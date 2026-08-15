"""Provider-neutral safety checks for structured AI card responses."""

from .i18n import t


def enable_deepseek_json_output(payload: dict, cfg: dict) -> dict:
    """Enable DeepSeek's native JSON mode for direct API calls."""
    if "api.deepseek.com" in (cfg.get("api_base") or "").lower():
        payload["response_format"] = {"type": "json_object"}
    return payload


def get_final_model_content(choice: dict) -> str:
    """Return final model content; reasoning traces are never card data."""
    if choice.get("finish_reason") == "length":
        raise RuntimeError(t("error_model_output_truncated"))

    message = choice["message"]
    content = message.get("content", "") or ""
    if content.strip():
        return content
    if (message.get("reasoning_content", "") or "").strip():
        raise RuntimeError(t("error_model_final_empty"))
    raise RuntimeError(t("error_model_empty"))
