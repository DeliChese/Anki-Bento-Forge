"""Provider-neutral adapter and safety checks for AI card responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .i18n import t
from .ai_providers import detect_provider


_TRUNCATION_REASONS = frozenset({
    "length", "max_tokens", "max_output_tokens", "content_filter_length",
    "incomplete",
})


@dataclass(frozen=True)
class AdaptedAiResponse:
    """The only response representation consumed by parsing/validation."""

    text: str
    structured_data: Any
    finish_reason: str
    truncated: bool
    usage: dict
    provider: str
    model: str


def enable_deepseek_json_output(payload: dict, cfg: dict) -> dict:
    """Enable native JSON and the benchmarked V4 card-generation mode."""
    if "api.deepseek.com" in (cfg.get("api_base") or "").lower():
        payload["response_format"] = {"type": "json_object"}
        if (cfg.get("model") or "").lower().startswith("deepseek-v4-"):
            mode = (cfg.get("thinking_mode") or "disabled").lower()
            if mode in ("enabled", "disabled"):
                payload["thinking"] = {"type": mode}
    return payload


def get_final_model_content(choice: dict) -> str:
    """Return final model content; reasoning traces are never card data."""
    if choice.get("finish_reason") == "length":
        raise RuntimeError(t("error_model_output_truncated"))

    message = choice["message"]
    content, structured = _message_content(message)
    if content.strip():
        return content
    if structured is not None:
        import json
        return json.dumps(structured, ensure_ascii=False)
    if (message.get("reasoning_content", "") or "").strip():
        raise RuntimeError(t("error_model_final_empty"))
    raise RuntimeError(t("error_model_empty"))


def _message_content(message: dict) -> tuple[str, Any]:
    structured = (
        message.get("parsed")
        if message.get("parsed") is not None
        else message.get("structured_content")
    )
    content = message.get("content", "")
    if isinstance(content, dict):
        return "", content
    if isinstance(content, str):
        return content, structured
    if isinstance(content, (list, tuple)):
        if content and all(
            isinstance(part, dict)
            and (part.get("type") in {"text", "output_text"} or "text" in part or "output_text" in part)
            for part in content
        ):
            texts = []
            for part in content:
                value = part.get("text") or part.get("output_text")
                if isinstance(value, str):
                    texts.append(value)
                if structured is None and part.get("json") is not None:
                    structured = part.get("json")
            return "".join(texts), structured
        return "", content
    return "", structured


def adapt_chat_completion_response(result: dict, cfg: dict) -> AdaptedAiResponse:
    """Normalize an OpenAI-compatible provider result without parsing cards."""
    choices = result.get("choices") if isinstance(result, dict) else None
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise RuntimeError(t("error_api_no_result", details="invalid response envelope"))
    choice = choices[0]
    message = choice.get("message")
    if not isinstance(message, dict):
        raise RuntimeError(t("error_model_empty"))
    text, structured = _message_content(message)
    if not text.strip() and structured is None:
        if str(message.get("reasoning_content") or "").strip():
            raise RuntimeError(t("error_model_final_empty"))
        raise RuntimeError(t("error_model_empty"))
    finish_reason = str(choice.get("finish_reason") or "").strip().lower()
    api_base = str(cfg.get("api_base") or "")
    return AdaptedAiResponse(
        text=text,
        structured_data=structured,
        finish_reason=finish_reason,
        truncated=finish_reason in _TRUNCATION_REASONS,
        usage=dict(result.get("usage") or {}),
        provider=detect_provider(api_base, str(cfg.get("model") or "")) or "custom",
        model=str(cfg.get("model") or ""),
    )


__all__ = [
    "AdaptedAiResponse", "adapt_chat_completion_response",
    "enable_deepseek_json_output", "get_final_model_content",
]
