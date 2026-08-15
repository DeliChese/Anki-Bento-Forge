"""Persistent, privacy-safe AI usage history.

The history deliberately contains usage metadata only.  Prompt text, responses,
API keys and API URLs are never written to disk.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from .logger import get_logger
from .user_data import atomic_write_json, get_user_data_path, read_json

logger = get_logger()

_PATH = get_user_data_path("ai_usage_history.json")
_MAX_ENTRIES = 2_000
_LOCK = threading.RLock()


def _valid_document(value: Any) -> bool:
    return isinstance(value, dict) and isinstance(value.get("entries", []), list)


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return default


def _integer(value: Any) -> int:
    return int(_number(value))


def _load() -> Dict[str, List[dict]]:
    document = read_json(_PATH, {"version": 1, "entries": []}, _valid_document)
    entries = [entry for entry in document.get("entries", []) if isinstance(entry, dict)]
    return {"version": 1, "entries": entries[-_MAX_ENTRIES:]}


def record_usage(
    token_info: Dict[str, Any],
    *,
    operation: str,
    started_at: Optional[float] = None,
    duration_seconds: Optional[float] = None,
) -> None:
    """Append one provider-reported request to profile-scoped history."""
    if not isinstance(token_info, dict):
        return
    started = _number(started_at, time.time())
    duration = _number(duration_seconds)
    entry = {
        "timestamp": datetime.fromtimestamp(started).astimezone().isoformat(timespec="seconds"),
        "timestamp_unix": round(started, 3),
        "model": str(token_info.get("model") or "").strip() or "unknown",
        "operation": str(operation or "unknown").strip() or "unknown",
        "duration_seconds": round(duration, 3),
        "prompt_tokens": _integer(token_info.get("prompt_tokens")),
        "completion_tokens": _integer(token_info.get("completion_tokens")),
        "total_tokens": _integer(token_info.get("total_tokens")),
        "input_cost": round(_number(token_info.get("input_cost")), 8),
        "output_cost": round(_number(token_info.get("output_cost")), 8),
        "total_cost": round(_number(token_info.get("total_cost")), 8),
    }
    if entry["total_tokens"] <= 0:
        entry["total_tokens"] = entry["prompt_tokens"] + entry["completion_tokens"]

    with _LOCK:
        try:
            document = _load()
            document["entries"].append(entry)
            document["entries"] = document["entries"][-_MAX_ENTRIES:]
            atomic_write_json(_PATH, document)
        except Exception as error:
            logger.warning("Could not persist AI usage history: %s", error)


def get_usage_entries() -> List[dict]:
    """Return a newest-first copy of recorded usage metadata."""
    with _LOCK:
        return list(reversed(_load()["entries"]))


def clear_usage_history() -> None:
    """Remove only usage metadata after an explicit user action."""
    with _LOCK:
        try:
            atomic_write_json(_PATH, {"version": 1, "entries": []})
        except Exception as error:
            logger.warning("Could not clear AI usage history: %s", error)


def summarize_usage(entries: Optional[Iterable[Dict[str, Any]]] = None) -> dict:
    """Compute totals for the supplied (normally filtered) entries."""
    values = list(entries if entries is not None else get_usage_entries())
    return {
        "calls": len(values),
        "prompt_tokens": sum(_integer(item.get("prompt_tokens")) for item in values),
        "completion_tokens": sum(_integer(item.get("completion_tokens")) for item in values),
        "total_tokens": sum(_integer(item.get("total_tokens")) for item in values),
        "total_cost": round(sum(_number(item.get("total_cost")) for item in values), 8),
    }
