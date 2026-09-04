"""Compact AI request dedicated to one editable Reviewer example."""

from __future__ import annotations

import json
import time
from typing import Callable, Optional

from . import ai_extractor as core
from .ai_providers import get_provider


PROMPT_VERSION = 1
MAX_OUTPUT_TOKENS = 700


def get_review_example_api_config() -> dict:
    cfg = core.get_api_config()
    provider_id = str(cfg.get("review_example_provider") or "").strip()
    provider = get_provider(provider_id) if provider_id else None
    if provider:
        cfg["provider"] = provider_id
        cfg["api_base"] = str(provider["base"]).rstrip("/")
        cfg["api_key"] = core.get_api_key_for_provider(provider_id, cfg["api_base"])
    if override := str(cfg.get("review_example_model") or "").strip():
        cfg["model"] = override
    return cfg


def decode_payload(adapted) -> dict:
    value = adapted.structured_data
    if value is None:
        text = str(adapted.text or "").strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if len(lines) < 3 or lines[-1].strip() != "```":
                raise ValueError("malformed_json")
            text = "\n".join(lines[1:-1]).strip()
        decoder = json.JSONDecoder()
        try:
            value, end = decoder.raw_decode(text)
        except (TypeError, json.JSONDecodeError) as error:
            raise ValueError("malformed_json") from error
        if text[end:].strip():
            raise ValueError("ambiguous_json_payloads")
    if not isinstance(value, dict):
        raise ValueError("invalid_json_schema")
    result = {
        "text": str(value.get("sentence") or value.get("text") or "").strip()[:4_000],
        "reading": str(value.get("reading") or value.get("pronunciation") or "").strip()[:4_000],
        "translation": str(value.get("translation") or "").strip()[:4_000],
    }
    if not result["text"] or not result["translation"]:
        raise ValueError("invalid_json_schema")
    return result


def generate_review_example_with_ai(
    *, target: str, meaning: str, language: str, card_kind: str = "vocab",
    difficulty: str = "mixed", length: str = "medium", existing_examples=None,
    progress_callback: Optional[Callable[[str], None]] = None,
    should_abort: Optional[Callable[[], bool]] = None,
) -> dict:
    """Generate exactly one editable example with a compact, uncached request."""
    language = core.normalize_language(language)
    if card_kind == "vocabulary":
        card_kind = "vocab"
    card_kind = card_kind if card_kind in {"vocab", "grammar", "collocation"} else "vocab"
    difficulty = difficulty if difficulty in {"beginner", "intermediate", "advanced", "mixed"} else "mixed"
    length = length if length in {"short", "medium", "long"} else "medium"
    target = str(target or "").strip()[:500]
    meaning = str(meaning or "").strip()[:800]
    if not target:
        return {"error": "missing_target", "token_info": None}

    cfg = get_review_example_api_config()
    if not cfg.get("api_key") and "localhost" not in cfg.get("api_base", ""):
        return {"error": core.t("error_api_key_missing"), "token_info": None}
    prior = [
        str(item or "").strip()[:500]
        for item in list(existing_examples or [])[:8]
        if str(item or "").strip()
    ]
    request_data = {
        "language": language,
        "kind": card_kind,
        "target": target,
        "meaning": meaning,
        "difficulty": difficulty,
        "length": length,
        "avoid": prior,
    }
    system_prompt = (
        f"Bento Review Example v{PROMPT_VERSION}. Create one natural, pedagogically useful "
        "target-language example. Respect the requested difficulty and length, use the target exactly or "
        "a grammatically necessary inflection, and do not repeat the avoid list. Return one JSON object only: "
        '{"sentence":"...","reading":"...","translation":"Vietnamese..."}. '
        "reading must be kana for Japanese, pinyin with tone marks for Chinese, romanization for Korean, "
        "and IPA for English. No explanation or markdown."
    )
    user_prompt = json.dumps(request_data, ensure_ascii=False, separators=(",", ":"))

    policy = core.get_ai_session_policy()
    policy.configure(
        max_input_chars=cfg.get("session_max_input_chars", 90_000),
        max_tokens=cfg.get("session_max_tokens", 120_000),
        max_cost_usd=cfg.get("session_max_cost_usd", 2.0),
    )
    estimate = policy.estimate(
        text_chars=len(system_prompt) + len(user_prompt),
        model=cfg.get("model", ""),
        max_output_tokens=MAX_OUTPUT_TOKENS,
        chunk_size=max(1, len(user_prompt)),
    )
    blocked_reason = policy.check(estimate)
    if blocked_reason:
        return {
            "error": core.t("error_ai_budget_exceeded", reason=blocked_reason),
            "token_info": None,
        }

    payload = {
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.65,
        "max_tokens": min(int(cfg.get("max_tokens") or 8192), MAX_OUTPUT_TOKENS),
    }
    core._apply_reasoning_effort(payload, cfg)
    core.enable_deepseek_json_output(payload, cfg)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg['api_key']}",
    }
    if progress_callback:
        progress_callback(core.t("status_calling_model", model=cfg["model"]))
    started_at = time.time()
    started_monotonic = time.monotonic()
    try:
        body = core._http_post_json(
            f"{cfg['api_base'].rstrip('/')}/chat/completions",
            payload, headers, timeout=180,
            progress_callback=progress_callback, should_abort=should_abort,
        )
        response = json.loads(body)
        adapted = core.adapt_chat_completion_response(response, cfg)
        if adapted.truncated:
            raise RuntimeError(core.t("error_model_output_truncated"))
        result = decode_payload(adapted)
    except Exception as error:
        return {"error": str(error), "token_info": None}

    token_info = None
    usage = response.get("usage", {})
    if usage and usage.get("total_tokens"):
        token_info = core._calculate_cost(
            cfg["model"], usage.get("prompt_tokens", 0),
            usage.get("completion_tokens", 0), usage.get("cost"),
        )
        core._record_token_info(
            token_info,
            operation="review_example_generation",
            started_at=started_at,
            duration_seconds=time.monotonic() - started_monotonic,
            provider=adapted.provider,
        )
    result.update({"error": None, "token_info": token_info})
    return result
