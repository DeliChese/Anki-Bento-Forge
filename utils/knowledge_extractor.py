"""Strict AI extraction for V18 Knowledge cards.

This module performs network work only.  It has no Anki/Qt dependency and
accepts already-serialized duplicate keys from the UI's QueryOp.
"""

from __future__ import annotations

import hashlib
import json
from typing import Callable, Iterable, List, Optional

from .ai_extractor import (
    _ai_cache_get,
    _ai_cache_set,
    _apply_reasoning_effort,
    _check_truncated_output,
    ensure_ai_session_budget,
    get_api_config,
)
from .ai_http_client import post_json
from .ai_response_guard import enable_deepseek_json_output, get_final_model_content
from .i18n import t
from .knowledge_model import knowledge_duplicate_key
from .knowledge_schema import parse_knowledge_cards
from .prompt_config import get_knowledge_system_prompt


def _existing_hash(keys: Iterable[str]) -> str:
    raw = "\n".join(sorted({str(key).strip() for key in keys if str(key).strip()}))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def extract_knowledge_with_ai(
    text: str,
    custom_instruction: str = "",
    existing_keys: Optional[List[str]] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
    force_refresh: bool = False,
    should_abort: Optional[Callable[[], bool]] = None,
) -> list:
    """Extract a complete, strictly validated Knowledge JSON array."""
    existing_keys = list(existing_keys or [])
    existing_hash = _existing_hash(existing_keys)
    if should_abort and should_abort():
        raise RuntimeError(t("error_cancelled_by_user"))
    if not force_refresh:
        cached = _ai_cache_get(text, "knowledge", custom_instruction, existing_hash, kind="knowledge")
        if cached is not None:
            # Cache entries were validated before persistence.
            cards = parse_knowledge_cards(json.dumps(cached, ensure_ascii=False))
            if progress_callback:
                progress_callback(t("status_cache_knowledge", count=len(cards)))
            return cards

    cfg = get_api_config()
    if not cfg.get("api_key") and "localhost" not in cfg.get("api_base", ""):
        raise ValueError(t("error_api_key_missing"))
    max_chars = cfg.get("max_chars", 45000)
    if len(text) > max_chars:
        text = text[:max_chars]

    user_message = "Create Knowledge cards only from the source material below."
    user_message += "\n\nSOURCE MATERIAL:\n" + text
    if existing_keys:
        user_message += "\n\nDUPLICATE KEYS TO EXCLUDE:\n" + "\n".join(existing_keys[:400])
    if custom_instruction.strip():
        user_message += "\n\nADDITIONAL REQUIREMENT:\n" + custom_instruction.strip()
    payload = {
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": get_knowledge_system_prompt()},
            {"role": "user", "content": user_message},
        ],
        "temperature": cfg.get("temperature", 0.3),
        "max_tokens": cfg.get("max_tokens", 8192),
    }
    _apply_reasoning_effort(payload, cfg)
    enable_deepseek_json_output(payload, cfg)
    if progress_callback:
        progress_callback(t("status_calling_model", model=cfg["model"]))
    timeout = 600 if "reasoner" in cfg.get("model", "") else 300
    body = post_json(
        cfg["api_base"].rstrip("/") + "/chat/completions",
        payload,
        {"Content-Type": "application/json", "Authorization": f"Bearer {cfg['api_key']}"},
        timeout=timeout,
        progress_callback=progress_callback,
        should_abort=should_abort,
    )
    result = json.loads(body)
    if not result.get("choices"):
        raise RuntimeError(t("error_api_no_result", details=body[:500]))
    content = get_final_model_content(result["choices"][0])
    _check_truncated_output(content, progress_callback)
    cards = parse_knowledge_cards(content)

    blocked = set(existing_keys)
    unique = []
    seen = set()
    for card in cards:
        key = knowledge_duplicate_key(card)
        if key not in blocked and key not in seen:
            seen.add(key)
            unique.append(card)
    if unique:
        _ai_cache_set(text, "knowledge", custom_instruction, existing_hash, unique, kind="knowledge")
    if progress_callback:
        progress_callback(t("status_new_knowledge", count=len(unique)))
    return unique


def extract_knowledge_long_text(
    text: str,
    custom_instruction: str = "",
    existing_keys: Optional[List[str]] = None,
    chunk_size: Optional[int] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
    force_refresh: bool = False,
    should_abort: Optional[Callable[[], bool]] = None,
) -> list:
    """Extract Knowledge from long text; any invalid chunk rejects the run."""
    ensure_ai_session_budget(text)
    chunk_size = chunk_size or get_api_config().get("chunk_size", 8000)
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)] or [""]
    all_cards = []
    keys = list(existing_keys or [])
    seen = set(keys)
    for index, chunk in enumerate(chunks):
        if should_abort and should_abort():
            raise RuntimeError(t("error_cancelled_by_user"))
        if progress_callback and len(chunks) > 1:
            progress_callback(t("status_chunk", current=index + 1, total=len(chunks)))
        cards = extract_knowledge_with_ai(
            chunk,
            custom_instruction,
            existing_keys=keys,
            progress_callback=progress_callback,
            force_refresh=force_refresh,
            should_abort=should_abort,
        )
        for card in cards:
            key = knowledge_duplicate_key(card)
            if key not in seen:
                seen.add(key)
                keys.append(key)
                all_cards.append(card)
    return all_cards
