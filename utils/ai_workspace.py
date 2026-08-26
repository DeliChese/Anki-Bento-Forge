"""Pure request-scoped policy for Reviewer and Forge AI workspaces."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping, Optional

from .ai_context_manager import (
    card_context_system_message, has_usable_card_context, minimal_card_context,
)
from .language_identity import normalize_language
from .logger import redact_sensitive


WORKSPACES = frozenset({"reviewer", "forge"})


@dataclass(frozen=True)
class WorkspacePolicy:
    """Immutable UI and context capabilities for one workspace."""

    workspace: str
    title_key: str
    subtitle_key: str
    input_placeholder_key: str
    input_accessible_key: str
    quick_actions: tuple[tuple[str, str], ...]
    allows_card_context: bool
    allows_source_context: bool
    allows_card_mode: bool
    shows_route_strip: bool


@dataclass(frozen=True)
class WorkspaceRequestContext:
    """Exact provenance for one AI request, never for a whole session."""

    workspace: str
    language: str
    learning_mode: str
    lane: str
    source_text: str
    user_instruction: str
    card_context_items: tuple[tuple[str, object], ...]
    use_card_context: bool
    request_token: str

    @property
    def card_context(self) -> dict:
        return dict(self.card_context_items)

    @property
    def source_attached(self) -> bool:
        return bool(self.source_text)

    def to_snapshot(self) -> dict:
        """Return bounded optional message metadata compatible with schema v1."""
        snapshot = {
            "workspace": self.workspace,
            "language": self.language,
            "learning_mode": self.learning_mode,
            "lane": self.lane,
            "source_text": self.source_text,
            "source_chars": len(self.source_text),
            "source_attached": self.source_attached,
            "user_instruction": self.user_instruction,
            "use_card_context": self.use_card_context,
            "request_token": self.request_token,
        }
        if self.card_context_items:
            snapshot["card_context"] = self.card_context
        return redact_sensitive(snapshot)


_REVIEWER_ACTIONS = (
    ("study_quick_explain", "study_prompt_explain"),
    ("study_quick_hint", "study_prompt_hint"),
    ("study_quick_contrast", "study_prompt_contrast"),
    ("study_quick_usage", "study_prompt_usage"),
    ("study_quick_example", "study_prompt_example"),
    ("study_quick_check", "study_prompt_check"),
)

_FORGE_ACTIONS = (
    ("study_forge_quick_analyze", "study_forge_prompt_analyze"),
    ("study_forge_quick_contrast", "study_forge_prompt_contrast"),
    ("study_forge_quick_examples", "study_forge_prompt_examples"),
    ("study_forge_quick_quality", "study_forge_prompt_quality"),
)


_GRAMMAR_ROUTE_CUES = (
    "grammar", "grammatical", "ngữ pháp", "cấu trúc", "mẫu câu", "pattern",
    "文法", "语法", "語法", "문법", "어미", "助詞", "particle", "conjugation",
)
_VOCAB_ROUTE_CUES = (
    "vocabulary", "vocab", "từ vựng", "từ mới", "word", "words", "collocation",
    "単語", "語彙", "词汇", "詞彙", "生词", "生詞", "어휘", "단어",
)


def route_forge_lane(source_text: str, instruction: str = "", fallback: str = "vocab") -> str:
    """Route the next AI production request without making an extra AI call.

    Explicit user intent wins.  When the request is neutral, retain the lane
    supplied by the calling Factory so opening the unified Workshop never
    silently changes the user's current draft.
    """
    fallback = str(fallback or "vocab").strip().casefold()
    if fallback not in {"vocab", "grammar"}:
        fallback = "vocab"
    instruction_text = str(instruction or "").casefold()
    source = str(source_text or "").casefold()

    def score(text: str, cues: tuple[str, ...]) -> int:
        return sum(1 for cue in cues if cue in text)

    instruction_grammar = score(instruction_text, _GRAMMAR_ROUTE_CUES)
    instruction_vocab = score(instruction_text, _VOCAB_ROUTE_CUES)
    if instruction_grammar != instruction_vocab:
        return "grammar" if instruction_grammar > instruction_vocab else "vocab"

    combined = f"{instruction_text}\n{source}"
    grammar_score = score(source, _GRAMMAR_ROUTE_CUES)
    vocab_score = score(source, _VOCAB_ROUTE_CUES)
    # Formula-like targets are useful grammar evidence, but only when no
    # explicit vocabulary request is present.
    if re.search(r"(?:^|\s)[~〜～]|(?:^|\s)[nva]\s*\+|\b(?:tense|clause|syntax)\b", combined):
        grammar_score += 1
    if grammar_score == vocab_score:
        return fallback
    return "grammar" if grammar_score > vocab_score else "vocab"

_POLICIES = {
    "reviewer": WorkspacePolicy(
        workspace="reviewer",
        title_key="study_reviewer_title",
        subtitle_key="study_reviewer_subtitle",
        input_placeholder_key="study_reviewer_input_placeholder",
        input_accessible_key="study_reviewer_input_accessible",
        quick_actions=_REVIEWER_ACTIONS,
        allows_card_context=True,
        allows_source_context=False,
        allows_card_mode=False,
        shows_route_strip=False,
    ),
    "forge": WorkspacePolicy(
        workspace="forge",
        title_key="study_forge_title",
        subtitle_key="study_forge_subtitle",
        input_placeholder_key="study_forge_input_placeholder",
        input_accessible_key="study_forge_input_accessible",
        quick_actions=_FORGE_ACTIONS,
        allows_card_context=False,
        allows_source_context=True,
        allows_card_mode=True,
        shows_route_strip=True,
    ),
}


def resolve_workspace(value: str) -> str:
    workspace = str(value or "").strip().casefold()
    if workspace not in WORKSPACES:
        raise ValueError("unsupported AI workspace")
    return workspace


def get_workspace_policy(workspace: str) -> WorkspacePolicy:
    return _POLICIES[resolve_workspace(workspace)]


def validate_workspace_card_mode(workspace: str, card_mode: Optional[str]) -> Optional[str]:
    """Allow importable card output only on the Forge production surface."""
    workspace = resolve_workspace(workspace)
    mode = None if card_mode is None else str(card_mode).strip().casefold()
    if mode not in {None, "vocab", "grammar"}:
        raise ValueError("unsupported study-session card mode")
    if mode is not None and not get_workspace_policy(workspace).allows_card_mode:
        raise ValueError("Reviewer workspace does not allow Card Mode")
    return mode


def validate_workspace_request(
    workspace: str,
    language: str,
    context,
) -> str:
    """Validate optional request provenance at the shared AI boundary."""
    workspace = resolve_workspace(workspace)
    if context is None:
        return workspace
    if not isinstance(context, WorkspaceRequestContext):
        raise ValueError("invalid workspace request context")
    if context.workspace != workspace:
        raise ValueError("workspace request ownership mismatch")
    if context.language != normalize_language(language):
        raise ValueError("workspace request language mismatch")
    return workspace


def build_workspace_request_context(
    *,
    workspace: str,
    language: str,
    user_instruction: str,
    request_token: str,
    learning_mode: str = "language",
    lane: str = "vocab",
    source_text: str = "",
    card_context: Optional[Mapping] = None,
    use_card_context: bool = False,
) -> WorkspaceRequestContext:
    """Build a fail-closed immutable context snapshot for one request."""
    workspace = resolve_workspace(workspace)
    language = normalize_language(language)
    token = str(request_token or "").strip()
    if not token:
        raise ValueError("request token is required")
    instruction = str(redact_sensitive(user_instruction or "")).strip()[:50_000]

    if workspace == "reviewer":
        filtered = minimal_card_context(
            card_context,
            include_answer=str((card_context or {}).get("side") or "question") == "answer",
        ) if use_card_context else {}
        if not has_usable_card_context(filtered):
            filtered = {}
        return WorkspaceRequestContext(
            workspace=workspace,
            language=language,
            learning_mode="language",
            lane="",
            source_text="",
            user_instruction=instruction,
            card_context_items=tuple(filtered.items()),
            use_card_context=bool(filtered),
            request_token=token,
        )

    learning_mode = str(learning_mode or "language").strip().casefold()
    if learning_mode not in {"language", "knowledge"}:
        raise ValueError("unsupported Forge learning mode")
    if learning_mode == "knowledge":
        lane = "knowledge"
    else:
        lane = str(lane or "").strip().casefold()
        if lane not in {"vocab", "grammar"}:
            raise ValueError("unsupported Forge language lane")
    source = str(redact_sensitive(source_text or "")).strip()[:50_000]
    return WorkspaceRequestContext(
        workspace=workspace,
        language=language,
        learning_mode=learning_mode,
        lane=lane,
        source_text=source,
        user_instruction=instruction,
        card_context_items=(),
        use_card_context=False,
        request_token=token,
    )


def workspace_context_message(context: WorkspaceRequestContext) -> dict:
    """Describe only context explicitly owned by this request."""
    if context.workspace == "reviewer":
        if not context.use_card_context:
            content = "REVIEWER REQUEST CONTEXT: no current-card context was attached."
        else:
            content = card_context_system_message(context.card_context)["content"]
    else:
        lines = [
            "FORGE REQUEST CONTEXT (use only this explicitly supplied production context):",
            f"language: {context.language}",
            f"workflow: {context.learning_mode}",
            f"lane: {context.lane}",
            "current_card: none",
        ]
        if context.source_text:
            lines.extend(("SOURCE:", context.source_text))
        else:
            lines.append("SOURCE: none attached")
        content = "\n".join(lines)
    return {"role": "system", "content": content}


__all__ = [
    "WORKSPACES", "WorkspacePolicy", "WorkspaceRequestContext",
    "build_workspace_request_context", "get_workspace_policy", "resolve_workspace",
    "route_forge_lane",
    "validate_workspace_card_mode", "validate_workspace_request",
    "workspace_context_message",
]
