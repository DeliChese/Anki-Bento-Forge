"""Profile-scoped persistence for AI Study Sessions.

The store owns conversation text, deterministic summaries, card artifacts and
small companion UI preferences.  It deliberately knows nothing about Anki,
Qt, credentials, HTTP or collection mutations.
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from .logger import get_logger, redact_sensitive
from .language_identity import CANONICAL_LANGUAGES, normalize_language, try_normalize_language
from .ai_output_validation import AI_OUTPUT_SCHEMA_VERSION, validate_ai_cards
from .ai_card_artifacts import (
    ARTIFACT_COMPATIBILITY_CURRENT, ARTIFACT_COMPATIBILITY_STALE,
)
from .user_data import atomic_write_json, get_user_data_path, read_json


logger = get_logger()

SESSION_SCHEMA_VERSION = 3
MESSAGE_TYPES = frozenset({"user", "assistant", "system_internal", "artifact_reference"})
MESSAGE_ROLES = frozenset({"user", "assistant", "system"})
WORKSPACE_MEMORY_KEYS = ("reviewer", "forge")
SUPPORTED_LANGUAGES = CANONICAL_LANGUAGES
DEFAULT_MAX_SESSIONS = 100
DEFAULT_MAX_MESSAGES = 500
DEFAULT_MAX_ARTIFACTS = 100
DEFAULT_MAX_STORE_BYTES = 15 * 1024 * 1024


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _identifier(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _clean_text(value: Any, limit: int) -> str:
    return str(redact_sensitive(str(value or "")))[:limit]


def _valid_document(value: Any) -> bool:
    return isinstance(value, dict) and isinstance(value.get("sessions", []), list)


def _serialized_size(value: Any) -> int:
    payload = json.dumps(value, ensure_ascii=False, indent=2)
    if os.linesep != "\n":
        payload = payload.replace("\n", os.linesep)
    return len(payload.encode("utf-8"))


def _referenced_source_ids(artifacts: list[dict]) -> set[str]:
    return {
        str(artifact.get("source_message_id") or "")
        for artifact in artifacts
        if artifact.get("source_message_id")
    }


def _pop_oldest_unreferenced_message(session: dict) -> bool:
    messages = session.get("messages") or []
    referenced = _referenced_source_ids(session.get("artifacts") or [])
    for index, message in enumerate(messages):
        if str(message.get("id") or "") not in referenced:
            messages.pop(index)
            return True
    return False


def _pop_oldest_artifact(session: dict) -> bool:
    artifacts = session.get("artifacts") or []
    if not artifacts:
        return False
    artifacts.pop(0)
    return True


def _prune_document_to_size(document: dict, max_bytes: int) -> None:
    """Prune deterministically without orphaning retained artifact provenance."""
    while _serialized_size(document) > max_bytes:
        message_pruned = False
        for session in document["sessions"]:
            if _pop_oldest_unreferenced_message(session):
                message_pruned = True
                break
        if message_pruned:
            continue

        artifact_pruned = False
        for session in document["sessions"]:
            if _pop_oldest_artifact(session):
                artifact_pruned = True
                break
        if artifact_pruned:
            continue

        if len(document["sessions"]) > 1:
            document["sessions"].pop(0)
            continue
        raise ValueError("study session store exceeds its bounded size")


def _bounded_session_items(
    messages: list[dict], artifacts: list[dict], *, max_messages: int, max_artifacts: int,
) -> tuple[list[dict], list[dict]]:
    """Apply count limits while protecting sources of every retained artifact."""
    retained_artifacts = list(artifacts[-max_artifacts:])
    while retained_artifacts:
        referenced = _referenced_source_ids(retained_artifacts)
        protected_count = sum(
            1 for message in messages if message.get("id") in referenced
        )
        if protected_count <= max_messages:
            break
        retained_artifacts.pop(0)

    referenced = _referenced_source_ids(retained_artifacts)
    protected = {
        index for index, message in enumerate(messages)
        if message.get("id") in referenced
    }
    remaining = max(0, max_messages - len(protected))
    kept = set(protected)
    for index in range(len(messages) - 1, -1, -1):
        if index in protected:
            continue
        if remaining <= 0:
            break
        kept.add(index)
        remaining -= 1
    return [message for index, message in enumerate(messages) if index in kept], retained_artifacts


def _message(value: Any) -> Optional[dict]:
    if not isinstance(value, dict):
        return None
    role = str(value.get("role") or "").strip().lower()
    kind = str(value.get("type") or role).strip().lower()
    if role not in MESSAGE_ROLES or kind not in MESSAGE_TYPES:
        return None
    content = _clean_text(value.get("content"), 50_000)
    if not content and kind != "artifact_reference":
        return None
    result = {
        "id": _clean_text(value.get("id"), 100) or _identifier("msg"),
        "role": role,
        "content": content,
        "created_at": _clean_text(value.get("created_at"), 64) or _now(),
        "type": kind,
    }
    snapshot = value.get("context_snapshot")
    if isinstance(snapshot, dict):
        result["context_snapshot"] = redact_sensitive(snapshot)
    artifact_id = _clean_text(value.get("artifact_id"), 100)
    if artifact_id:
        result["artifact_id"] = artifact_id
    return result


def _workspace_summaries(value: Any) -> dict:
    raw = value if isinstance(value, dict) else {}
    result = {}
    for workspace in WORKSPACE_MEMORY_KEYS:
        slot = raw.get(workspace)
        if not isinstance(slot, dict):
            slot = {}
        summary = _clean_text(slot.get("summary"), 8_000)
        result[workspace] = {
            "summary": summary,
            "summary_through_message_id": (
                _clean_text(slot.get("summary_through_message_id"), 100)
                if summary else ""
            ),
        }
    return result


def _clear_summaries(session: dict) -> None:
    session["summary"] = ""
    session["summary_through_message_id"] = ""
    session["workspace_summaries"] = _workspace_summaries({})


def _message_workspace(message: dict) -> str:
    snapshot = message.get("context_snapshot")
    if not isinstance(snapshot, dict):
        return ""
    workspace = str(snapshot.get("workspace") or "").strip().casefold()
    return workspace if workspace in WORKSPACE_MEMORY_KEYS else ""


def _artifact(value: Any) -> Optional[dict]:
    if not isinstance(value, dict) or not isinstance(value.get("cards"), list):
        return None
    try:
        schema_version = int(value.get("schema_version") or 0)
    except (TypeError, ValueError):
        return None
    kind = str(value.get("kind") or "").strip().lower()
    language = try_normalize_language(value.get("language"))
    if schema_version != AI_OUTPUT_SCHEMA_VERSION:
        return {
            "artifact_id": _clean_text(value.get("artifact_id"), 100) or _identifier("artifact"),
            "session_id": _clean_text(value.get("session_id"), 100),
            "created_at": _clean_text(value.get("created_at"), 64) or _now(),
            "language": language or "",
            "kind": kind if kind in {"vocab", "grammar"} else "",
            "schema_version": schema_version,
            "compatibility": ARTIFACT_COMPATIBILITY_STALE,
            "cards": redact_sensitive(value["cards"]),
            "source_message_id": _clean_text(value.get("source_message_id"), 100),
        }
    if kind not in {"vocab", "grammar"} or language is None:
        return None
    cards = [redact_sensitive(dict(card)) for card in value["cards"] if isinstance(card, dict)]
    if not cards:
        return None
    try:
        report = validate_ai_cards(
            cards, lang=language, kind=kind, require_example=True,
        )
    except ValueError:
        return None
    if report.invalid or report.duplicate_count or len(report.valid_cards) != len(cards):
        return None
    return {
        "artifact_id": _clean_text(value.get("artifact_id"), 100) or _identifier("artifact"),
        "session_id": _clean_text(value.get("session_id"), 100),
        "created_at": _clean_text(value.get("created_at"), 64) or _now(),
        "language": language,
        "kind": kind,
        "schema_version": schema_version,
        "compatibility": ARTIFACT_COMPATIBILITY_CURRENT,
        "cards": [dict(card) for card in report.valid_cards],
        "source_message_id": _clean_text(value.get("source_message_id"), 100),
    }


def _session(value: Any, *, max_messages: int, max_artifacts: int) -> Optional[dict]:
    if not isinstance(value, dict):
        return None
    language = try_normalize_language(value.get("language"))
    if language is None:
        return None
    session_id = _clean_text(value.get("id"), 100) or _identifier("session")
    messages = [item for item in (_message(item) for item in value.get("messages", [])) if item]
    message_ids = {item["id"] for item in messages}
    artifacts = [
        item for item in (_artifact(item) for item in value.get("artifacts", []))
        if item and item.get("source_message_id") in message_ids
    ]
    for artifact in artifacts:
        artifact["session_id"] = session_id
    messages, artifacts = _bounded_session_items(
        messages, artifacts, max_messages=max_messages, max_artifacts=max_artifacts,
    )
    deck_context = value.get("optional_deck_context")
    if not isinstance(deck_context, dict):
        deck_context = None
    summary = _clean_text(value.get("summary"), 8_000)
    return {
        "id": session_id,
        "title": _clean_text(value.get("title"), 160) or "Study Session",
        "language": language,
        "created_at": _clean_text(value.get("created_at"), 64) or _now(),
        "updated_at": _clean_text(value.get("updated_at"), 64) or _now(),
        "provider": _clean_text(value.get("provider"), 100),
        "model": _clean_text(value.get("model"), 200),
        "messages": messages,
        "summary": summary,
        "summary_through_message_id": _clean_text(
            value.get("summary_through_message_id"), 100,
        ),
        "workspace_summaries": _workspace_summaries(
            value.get("workspace_summaries")
        ),
        "artifacts": artifacts,
        "optional_deck_context": redact_sensitive(deck_context) if deck_context else None,
    }


class StudySessionStore:
    """Atomic bounded store. Every read resolves the active profile lazily."""

    def __init__(
        self,
        path: Optional[str] = None,
        *,
        max_sessions: int = DEFAULT_MAX_SESSIONS,
        max_messages: int = DEFAULT_MAX_MESSAGES,
        max_artifacts: int = DEFAULT_MAX_ARTIFACTS,
        max_bytes: int = DEFAULT_MAX_STORE_BYTES,
    ) -> None:
        self.path = path
        self.max_sessions = max(1, int(max_sessions))
        self.max_messages = max(10, int(max_messages))
        self.max_artifacts = max(1, int(max_artifacts))
        self.max_bytes = max(4_096, int(max_bytes))
        self._lock = threading.RLock()

    def _path(self) -> str:
        return self.path or get_user_data_path("ai_study_sessions.json")

    def _load(self) -> dict:
        raw = read_json(
            self._path(),
            {"schema_version": SESSION_SCHEMA_VERSION, "sessions": [], "ui_state": {}},
            _valid_document,
            max_bytes=self.max_bytes,
        )
        sessions = [
            item for item in (
                _session(value, max_messages=self.max_messages, max_artifacts=self.max_artifacts)
                for value in raw.get("sessions", [])
            ) if item
        ]
        sessions.sort(key=lambda item: item["updated_at"])
        ui_state = raw.get("ui_state") if isinstance(raw.get("ui_state"), dict) else {}
        return {
            "schema_version": SESSION_SCHEMA_VERSION,
            "sessions": sessions[-self.max_sessions:],
            "ui_state": redact_sensitive(ui_state),
        }

    def _save(self, document: dict) -> None:
        document["schema_version"] = SESSION_SCHEMA_VERSION
        document["sessions"] = document.get("sessions", [])[-self.max_sessions:]
        _prune_document_to_size(document, self.max_bytes)
        atomic_write_json(self._path(), document)

    def list_sessions(self) -> list[dict]:
        with self._lock:
            values = list(reversed(self._load()["sessions"]))
            return [
                {
                    "id": item["id"], "title": item["title"],
                    "language": item["language"], "created_at": item["created_at"],
                    "updated_at": item["updated_at"], "provider": item["provider"],
                    "model": item["model"], "message_count": len(item["messages"]),
                    "artifact_count": len(item["artifacts"]),
                }
                for item in values
            ]

    def create_session(
        self,
        *,
        language: str,
        title: str = "",
        provider: str = "",
        model: str = "",
        optional_deck_context: Optional[dict] = None,
    ) -> dict:
        with self._lock:
            document = self._load()
            now = _now()
            language = normalize_language(language)
            session = _session({
                "id": _identifier("session"),
                "title": title or "Study Session",
                "language": language,
                "created_at": now,
                "updated_at": now,
                "provider": provider,
                "model": model,
                "messages": [],
                "summary": "",
                "summary_through_message_id": "",
                "workspace_summaries": {},
                "artifacts": [],
                "optional_deck_context": optional_deck_context,
            }, max_messages=self.max_messages, max_artifacts=self.max_artifacts)
            document["sessions"].append(session)
            self._save(document)
            return dict(session)

    def get_session(self, session_id: str) -> Optional[dict]:
        with self._lock:
            for session in self._load()["sessions"]:
                if session["id"] == session_id:
                    return session
        return None

    def save_session(self, session: dict) -> dict:
        with self._lock:
            clean = _session(
                dict(session, updated_at=_now()),
                max_messages=self.max_messages,
                max_artifacts=self.max_artifacts,
            )
            if clean is None:
                raise ValueError("invalid study session")
            document = self._load()
            document["sessions"] = [
                item for item in document["sessions"] if item["id"] != clean["id"]
            ]
            document["sessions"].append(clean)
            self._save(document)
            return clean

    def rename_session(self, session_id: str, title: str) -> Optional[dict]:
        session = self.get_session(session_id)
        if session is None:
            return None
        session["title"] = _clean_text(title, 160) or session["title"]
        return self.save_session(session)

    def delete_session(self, session_id: str) -> bool:
        with self._lock:
            document = self._load()
            remaining = [item for item in document["sessions"] if item["id"] != session_id]
            if len(remaining) == len(document["sessions"]):
                return False
            document["sessions"] = remaining
            if document["ui_state"].get("last_session_id") == session_id:
                document["ui_state"].pop("last_session_id", None)
            self._save(document)
            return True

    def add_message(
        self,
        session_id: str,
        *,
        role: str,
        content: str,
        message_type: Optional[str] = None,
        context_snapshot: Optional[dict] = None,
        artifact_id: str = "",
    ) -> dict:
        session = self.get_session(session_id)
        if session is None:
            raise KeyError(session_id)
        value = _message({
            "id": _identifier("msg"), "role": role, "content": content,
            "created_at": _now(), "type": message_type or role,
            "context_snapshot": context_snapshot, "artifact_id": artifact_id,
        })
        if value is None:
            raise ValueError("invalid study-session message")
        session["messages"].append(value)
        self.save_session(session)
        return value

    def replace_latest_user_message(
        self,
        session_id: str,
        content: str,
        *,
        context_snapshot: Optional[dict] = None,
        workspace: Optional[str] = None,
    ) -> Optional[dict]:
        session = self.get_session(session_id)
        if session is None:
            return None
        index = next(
            (idx for idx in range(len(session["messages"]) - 1, -1, -1)
             if session["messages"][idx]["role"] == "user"),
            None,
        )
        if index is None:
            return None
        if workspace is not None:
            workspace = str(workspace).strip().casefold()
            if workspace not in WORKSPACE_MEMORY_KEYS:
                raise ValueError("unsupported AI workspace message mutation")
            if _message_workspace(session["messages"][index]) != workspace:
                return None
        session["messages"] = session["messages"][:index + 1]
        session["messages"][index]["content"] = _clean_text(content, 50_000)
        session["messages"][index]["created_at"] = _now()
        if isinstance(context_snapshot, dict):
            session["messages"][index]["context_snapshot"] = redact_sensitive(
                context_snapshot
            )
        else:
            session["messages"][index].pop("context_snapshot", None)
        _clear_summaries(session)
        return self.save_session(session)

    def delete_message(self, session_id: str, message_id: str) -> bool:
        session = self.get_session(session_id)
        if session is None:
            return False
        messages = [item for item in session["messages"] if item["id"] != message_id]
        if len(messages) == len(session["messages"]):
            return False
        session["messages"] = messages
        _clear_summaries(session)
        self.save_session(session)
        return True

    def delete_latest_user_turn(
        self, session_id: str, *, workspace: Optional[str] = None,
    ) -> bool:
        """Delete the latest learner message and every response derived from it."""
        session = self.get_session(session_id)
        if session is None:
            return False
        index = next(
            (idx for idx in range(len(session["messages"]) - 1, -1, -1)
             if session["messages"][idx]["role"] == "user"),
            None,
        )
        if index is None:
            return False
        if workspace is not None:
            workspace = str(workspace).strip().casefold()
            if workspace not in WORKSPACE_MEMORY_KEYS:
                raise ValueError("unsupported AI workspace message mutation")
            if _message_workspace(session["messages"][index]) != workspace:
                return False
        session["messages"] = session["messages"][:index]
        _clear_summaries(session)
        self.save_session(session)
        return True

    def update_summary(
        self,
        session_id: str,
        summary: str,
        summary_through_message_id: Optional[str] = None,
        *,
        workspace: Optional[str] = None,
    ) -> Optional[dict]:
        session = self.get_session(session_id)
        if session is None:
            return None
        clean_summary = _clean_text(summary, 8_000)
        clean_marker = (
            _clean_text(summary_through_message_id, 100)
            if summary_through_message_id is not None and clean_summary else ""
        )
        if workspace is not None:
            workspace = str(workspace).strip().casefold()
            if workspace not in WORKSPACE_MEMORY_KEYS:
                raise ValueError("unsupported AI workspace summary")
            session["workspace_summaries"][workspace] = {
                "summary": clean_summary,
                "summary_through_message_id": clean_marker,
            }
            return self.save_session(session)
        session["summary"] = clean_summary
        if summary_through_message_id is not None:
            session["summary_through_message_id"] = clean_marker
        if not session["summary"]:
            session["summary_through_message_id"] = ""
        return self.save_session(session)

    def add_artifact(self, session_id: str, artifact: dict) -> dict:
        session = self.get_session(session_id)
        if session is None:
            raise KeyError(session_id)
        clean = _artifact(dict(artifact, session_id=session_id))
        if clean is None:
            raise ValueError("invalid card artifact")
        source_message_id = clean.get("source_message_id")
        if not source_message_id or not any(
            item.get("id") == source_message_id for item in session["messages"]
        ):
            raise ValueError("card artifact source message does not exist")
        session["artifacts"].append(clean)
        self.save_session(session)
        return clean

    def get_artifact(self, session_id: str, artifact_id: str) -> Optional[dict]:
        session = self.get_session(session_id)
        if session:
            return next(
                (item for item in session["artifacts"] if item["artifact_id"] == artifact_id),
                None,
            )
        return None

    def get_ui_state(self) -> dict:
        with self._lock:
            return dict(self._load()["ui_state"])

    def update_ui_state(self, **changes: Any) -> dict:
        allowed = {
            "dock_side", "floating", "floating_x", "floating_y", "floating_width",
            "floating_height", "collapsed", "last_session_id", "always_on_top",
            "visible",
        }
        with self._lock:
            document = self._load()
            state = dict(document["ui_state"])
            state.update({key: redact_sensitive(value) for key, value in changes.items() if key in allowed})
            document["ui_state"] = state
            self._save(document)
            return dict(state)


__all__ = [
    "SESSION_SCHEMA_VERSION", "StudySessionStore", "MESSAGE_TYPES",
    "WORKSPACE_MEMORY_KEYS",
    "SUPPORTED_LANGUAGES",
]
