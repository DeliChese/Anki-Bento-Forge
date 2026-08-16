"""Persistent cache for AI extraction results.

This module owns cache key construction, bounded directory maintenance, TTL
checks, persistence, and clearing.  Provider/config and prompt decisions are
injected by ``ai_extractor`` so this layer stays independent of AI workflows,
Anki, and UI modules.
"""

import hashlib
import os
import time
from typing import Callable, Optional

from .user_data import (
    atomic_write_json,
    clear_cache_dir,
    migrate_legacy_directory,
    prune_cache_dir,
    read_json,
)


DEFAULT_PROMPT_VERSION = 15
DEFAULT_MAX_BYTES = 25 * 1024 * 1024
DEFAULT_MAX_FILES = 200
DEFAULT_TTL_SECONDS = 7 * 24 * 3600
OPENROUTER_TTL_SECONDS = 14 * 24 * 3600


def build_cache_key(
    text: str,
    lang: str,
    instruction: str,
    existing_hash: str,
    *,
    kind: str = "vocab",
    prompt_version: int = DEFAULT_PROMPT_VERSION,
    prompt_signature: str = "",
) -> str:
    """Return the stable key used by legacy and current AI result caches."""
    raw = (
        f"{prompt_version}|{prompt_signature}|{kind}|{lang}|"
        f"{instruction}|{existing_hash}|{text}"
    )
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def ensure_cache_dir(
    cache_dir: str,
    legacy_cache_dir: str,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
    max_files: int = DEFAULT_MAX_FILES,
) -> None:
    """Migrate, create, and bound the result cache directory."""
    migrate_legacy_directory(legacy_cache_dir, cache_dir)
    os.makedirs(cache_dir, exist_ok=True)
    prune_cache_dir(
        cache_dir,
        max_age_seconds=OPENROUTER_TTL_SECONDS,
        max_bytes=max_bytes,
        max_files=max_files,
    )


def get_cached_result(
    text: str,
    lang: str,
    instruction: str,
    existing_hash: str,
    *,
    cache_dir: str,
    legacy_cache_dir: str,
    prompt_signature: str,
    is_openrouter: Callable[[], bool],
    kind: str = "vocab",
    prompt_version: int = DEFAULT_PROMPT_VERSION,
    max_bytes: int = DEFAULT_MAX_BYTES,
    max_files: int = DEFAULT_MAX_FILES,
    now: Callable[[], float] = time.time,
) -> Optional[list]:
    """Return an unexpired cached result, or ``None`` on miss/corruption."""
    ensure_cache_dir(
        cache_dir,
        legacy_cache_dir,
        max_bytes=max_bytes,
        max_files=max_files,
    )
    key = build_cache_key(
        text,
        lang,
        instruction,
        existing_hash,
        kind=kind,
        prompt_version=prompt_version,
        prompt_signature=prompt_signature,
    )
    cache_file = os.path.join(cache_dir, f"ai_{key}.json")
    if not os.path.exists(cache_file):
        return None
    try:
        data = read_json(cache_file, {}, lambda value: isinstance(value, dict))
        ttl = OPENROUTER_TTL_SECONDS if is_openrouter() else DEFAULT_TTL_SECONDS
        if now() - data.get("_cached_at", 0) < ttl:
            return data.get("vocab", [])
    except Exception:
        pass
    return None


def set_cached_result(
    text: str,
    lang: str,
    instruction: str,
    existing_hash: str,
    vocab_list: list,
    *,
    cache_dir: str,
    legacy_cache_dir: str,
    prompt_signature: str,
    kind: str = "vocab",
    prompt_version: int = DEFAULT_PROMPT_VERSION,
    max_bytes: int = DEFAULT_MAX_BYTES,
    max_files: int = DEFAULT_MAX_FILES,
) -> None:
    """Persist an AI result while preserving the established cache schema."""
    ensure_cache_dir(
        cache_dir,
        legacy_cache_dir,
        max_bytes=max_bytes,
        max_files=max_files,
    )
    key = build_cache_key(
        text,
        lang,
        instruction,
        existing_hash,
        kind=kind,
        prompt_version=prompt_version,
        prompt_signature=prompt_signature,
    )
    cache_file = os.path.join(cache_dir, f"ai_{key}.json")
    try:
        atomic_write_json(
            cache_file,
            {
                "vocab": vocab_list,
                "_kind": kind,
                "_cached_at": time.time(),
                "_lang": lang,
            },
        )
    except Exception:
        pass


def clear_result_cache(cache_dir: str) -> None:
    """Clear only AI cache data, never persistent profile state."""
    if os.path.exists(cache_dir):
        clear_cache_dir(cache_dir)
