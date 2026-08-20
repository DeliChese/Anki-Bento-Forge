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
from .user_data import atomic_write_json, get_user_data_path, read_json


logger = get_logger()

SESSION_SCHEMA_VERSION = 2
MESSAGE_TYPES = frozenset({"user", "assistant", "system_internal", "artifact_reference"})
MESSAGE_ROLES = frozenset({"user", "assistant", "system"})
SUPPORTED_LANGUAGES = frozenset({"japanese", "chinese", "korean", "english"})
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


def _artifact(value: Any) -> Optional[dict]:
    if not isinstance(value, dict) or not isinstance(value.get("cards"), list):
        return None
    kind = str(value.get("kind") or "").strip().lower()
    language = str(value.get("language") or "").strip().lower()
    if kind not in {"vocab", "grammar"} or language not in SUPPORTED_LANGUAGES:
        return None
    cards = [redact_sensitive(dict(card)) for card in value["cards"] if isinstance(card, dict)]
    if not cards:
        return None
    try:
        schema_version = max(1, int(value.get("schema_version") or 1))
    except (TypeError, ValueError):
        schema_version = 1
    return {
        "artifact_id": _clean_text(value.get("artifact_id"), 100) or _identifier("artifact"),
        "session_id": _clean_text(value.get("session_id"), 100),
        "created_at": _clean_text(value.get("created_at"), 64) or _now(),
        "language": language,
        "kind": kind,
        "schema_version": schema_version,
        "cards": cards,
        "source_message_id": _clean_text(value.get("source_message_id"), 100),
    }


def _session(value: Any, *, max_messages: int, max_artifacts: int) -> Optional[dict]:
    if not isinstance(value, dict):
        return None
    language = str(value.get("language") or "japanese").strip().lower()
    if language not in SUPPORTED_LANGUAGES:
        language = "japanese"
    session_id = _clean_text(value.get("id"), 100) or _identifier("session")
    messages = [item for item in (_message(item) for item in value.get("messages", [])) if item]
    artifacts = [item for item in (_artifact(item) for item in value.get("artifacts", [])) if item]
    for artifact in artifacts:
        artifact["session_id"] = session_id
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
        "messages": messages[-max_messages:],
        "summary": summary,
        "summary_through_message_id": _clean_text(
            value.get("summary_through_message_id"), 100,
        ),
        "artifacts": artifacts[-max_artifacts:],
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
        while _serialized_size(document) > self.max_bytes:
            pruned = False
            for session in document["sessions"]:
                if session.get("messages"):
                    session["messages"].pop(0)
                    pruned = True
                    break
                if session.get("artifacts"):
                    session["artifacts"].pop(0)
                    pruned = True
                    break
            if not pruned and len(document["sessions"]) > 1:
                document["sessions"].pop(0)
                pruned = True
            if not pruned:
                raise ValueError("study session store exceeds its bounded size")
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
        language: str = "japanese",
        title: str = "",
        provider: str = "",
        model: str = "",
        optional_deck_context: Optional[dict] = None,
    ) -> dict:
        with self._lock:
            document = self._load()
            now = _now()
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

    def replace_latest_user_message(self, session_id: str, content: str) -> Optional[dict]:
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
        session["messages"] = session["messages"][:index + 1]
        session["messages"][index]["content"] = _clean_text(content, 50_000)
        session["messages"][index]["created_at"] = _now()
        session["summary"] = ""
        session["summary_through_message_id"] = ""
        return self.save_session(session)

    def delete_message(self, session_id: str, message_id: str) -> bool:
        session = self.get_session(session_id)
        if session is None:
            return False
        messages = [item for item in session["messages"] if item["id"] != message_id]
        if len(messages) == len(session["messages"]):
            return False
        session["messages"] = messages
        session["summary"] = ""
        session["summary_through_message_id"] = ""
        self.save_session(session)
        return True

    def delete_latest_user_turn(self, session_id: str) -> bool:
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
        session["messages"] = session["messages"][:index]
        session["summary"] = ""
        session["summary_through_message_id"] = ""
        self.save_session(session)
        return True

    def update_summary(
        self,
        session_id: str,
        summary: str,
        summary_through_message_id: Optional[str] = None,
    ) -> Optional[dict]:
        session = self.get_session(session_id)
        if session is None:
            return None
        session["summary"] = _clean_text(summary, 8_000)
        if summary_through_message_id is not None:
            session["summary_through_message_id"] = _clean_text(
                summary_through_message_id, 100,
            )
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
    "SUPPORTED_LANGUAGES",
]
