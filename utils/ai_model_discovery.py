"""Discover provider models without coupling network work to Qt/Anki.

Model catalogs are cached below the active profile. API keys are sent only in
request headers and are never included in the cache, URL, or log output.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
import urllib.request
from urllib.parse import urlparse, urlunparse

from .user_data import atomic_write_json, get_user_data_path, read_json

_CACHE_VERSION = 1
_CACHE_NAME = "ai_model_catalog.json"
_CACHE_TTL_SECONDS = 24 * 60 * 60
_MAX_RESPONSE_BYTES = 2 * 1024 * 1024
_CACHE_LOCK = threading.Lock()


def _normalized_base(api_base: str) -> str:
    return str(api_base or "").strip().rstrip("/")


def _catalog_key(provider: str, api_base: str) -> str:
    identity = f"{str(provider or '').strip().lower()}|{_normalized_base(api_base).lower()}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()[:32]


def _cache_document() -> dict:
    path = get_user_data_path(_CACHE_NAME)
    return read_json(
        path,
        {"version": _CACHE_VERSION, "catalogs": {}},
        lambda value: isinstance(value, dict) and isinstance(value.get("catalogs", {}), dict),
    )


def load_cached_models(provider: str, api_base: str) -> list[str]:
    entry = _cache_document().get("catalogs", {}).get(_catalog_key(provider, api_base), {})
    models = entry.get("models", []) if isinstance(entry, dict) else []
    return _normalize_model_ids(models)


def model_cache_is_fresh(provider: str, api_base: str) -> bool:
    entry = _cache_document().get("catalogs", {}).get(_catalog_key(provider, api_base), {})
    if not isinstance(entry, dict):
        return False
    try:
        return time.time() - float(entry.get("updated_at", 0)) < _CACHE_TTL_SECONDS
    except (TypeError, ValueError):
        return False


def save_cached_models(provider: str, api_base: str, models: list[str]) -> None:
    normalized = _normalize_model_ids(models)
    if not normalized:
        return
    with _CACHE_LOCK:
        document = _cache_document()
        catalogs = document.setdefault("catalogs", {})
        catalogs[_catalog_key(provider, api_base)] = {
            "provider": str(provider or "").strip().lower(),
            "api_base": _normalized_base(api_base),
            "updated_at": time.time(),
            "models": normalized,
        }
        document["version"] = _CACHE_VERSION
        atomic_write_json(get_user_data_path(_CACHE_NAME), document)


def _origin_with_path(api_base: str, path: str) -> str:
    parsed = urlparse(_normalized_base(api_base))
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("invalid API base URL")
    return urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))


def build_model_catalog_request(
    provider: str,
    api_base: str,
    api_key: str = "",
) -> tuple[str, dict[str, str]]:
    """Return the official catalog URL and authentication headers."""
    provider_id = str(provider or "").strip().lower()
    base = _normalized_base(api_base)
    parsed = urlparse(base)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("invalid API base URL")

    headers = {"Accept": "application/json", "User-Agent": "Bento-Forge"}
    key = str(api_key or "").strip()

    if provider_id == "ollama":
        return _origin_with_path(base, "/api/tags"), headers

    if provider_id == "gemini" and "generativelanguage.googleapis.com" in parsed.netloc.lower():
        if key:
            headers["x-goog-api-key"] = key
        return _origin_with_path(base, "/v1beta/models") + "?pageSize=1000", headers

    url = base + "/models"
    if provider_id == "anthropic" and "anthropic.com" in parsed.netloc.lower():
        if key:
            headers["x-api-key"] = key
        headers["anthropic-version"] = "2023-06-01"
    elif key:
        headers["Authorization"] = f"Bearer {key}"
    return url, headers


def _normalize_model_ids(models) -> list[str]:
    unique = {}
    for model in models or []:
        value = str(model or "").strip()
        if value.startswith("models/"):
            value = value[7:]
        if value:
            unique.setdefault(value.casefold(), value)
    return sorted(unique.values(), key=str.casefold)


def parse_model_catalog(payload: dict, provider: str = "") -> list[str]:
    """Parse OpenAI-compatible, Gemini, Ollama, and LM Studio catalogs."""
    if not isinstance(payload, dict):
        return []
    provider_id = str(provider or "").strip().lower()
    rows = payload.get("data")
    if not isinstance(rows, list):
        rows = payload.get("models")
    if not isinstance(rows, list):
        return []

    models = []
    for row in rows[:2000]:
        if isinstance(row, str):
            models.append(row)
            continue
        if not isinstance(row, dict):
            continue
        if str(row.get("type") or "").lower() in {"embedding", "embeddings"}:
            continue
        supported = row.get("supportedGenerationMethods") or row.get("supported_generation_methods")
        if provider_id == "gemini" and supported and "generateContent" not in supported:
            continue
        model_id = row.get("id") or row.get("model") or row.get("name") or row.get("key")
        if model_id:
            models.append(model_id)

    normalized = _normalize_model_ids(models)
    excluded_fragments = (
        "embedding", "moderation", "whisper", "transcri", "dall-e",
        "-tts", "tts-", "realtime", "image-generation",
    )
    return [
        model for model in normalized
        if not any(fragment in model.casefold() for fragment in excluded_fragments)
    ]


def fetch_provider_models(
    provider: str,
    api_base: str,
    api_key: str = "",
    *,
    timeout: int = 15,
) -> list[str]:
    """Fetch a bounded model catalog. Call from a background thread."""
    url, headers = build_model_catalog_request(provider, api_base, api_key)
    request = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read(_MAX_RESPONSE_BYTES + 1)
    if len(body) > _MAX_RESPONSE_BYTES:
        raise ValueError("model catalog response is too large")
    payload = json.loads(body.decode("utf-8"))
    return parse_model_catalog(payload, provider)
