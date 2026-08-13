"""Write privacy-safe, aggregate import reports to profile data."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from .user_data import atomic_write_json, get_user_data_path, prune_cache_dir


def build_import_report(report: Mapping, summary: Mapping) -> dict:
    """Return an aggregate report that excludes cards, prompts, and error text."""
    numeric = ("added", "updated", "audio_gen", "audio_failed", "errors")
    return {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "selection": {key: max(0, int(summary.get(key, 0))) for key in ("new", "updates")},
        "result": {key: max(0, int(report.get(key, 0))) for key in numeric},
        "cancelled": bool(report.get("cancelled", False)),
    }


def write_import_report(report: Mapping, summary: Mapping) -> str:
    """Persist an aggregate report and retain a bounded recent history."""
    report_dir = Path(get_user_data_path("reports"))
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = report_dir / f"import-{stamp}.json"
    atomic_write_json(str(path), build_import_report(report, summary))
    prune_cache_dir(str(report_dir), max_age_seconds=90 * 24 * 3600, max_bytes=512 * 1024, max_files=50)
    return str(path)
