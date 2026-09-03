"""
🎤 Japanese Text-to-Speech Providers — Các engine TTS

Hỗ trợ:
- edge-tts (Microsoft Edge TTS, online, chất lượng cao)
- gTTS (Google TTS, online, fallback)
- VoiceVox (local Japanese TTS)
"""

import asyncio
import html
import hashlib
import json
import os
import re
import threading
import time
import urllib.parse
import urllib.request
from collections import OrderedDict
from contextlib import contextmanager
from typing import Dict, Iterator, Optional

from utils.logger import get_logger, log_event
from utils.credentials import load_api_key, save_api_key
from utils.user_data import atomic_write_json, get_user_data_path, read_json

logger = get_logger()


# ═══════════════════════════════════════════════════════════
#  Dependency checks — never modify Anki's Python environment at runtime.
# ═══════════════════════════════════════════════════════════
_dependency_cache: Dict[str, bool] = {}
_dependency_cache_lock = threading.Lock()
_DEPENDENCIES = {
    "edge_tts": "edge-tts==7.2.7",
    "gtts": "gTTS==2.5.4",
}

# Network operations must be bounded even when a server is offline or stalls.
_CONNECT_TIMEOUT_SECONDS = 10
_READ_TIMEOUT_SECONDS = 30
_EDGE_TOTAL_TIMEOUT_SECONDS = 45

# VoiceVox query responses are a performance cache only.  Generated media is
# managed by Anki because it may be referenced by a note.
_MAX_VOICEVOX_QUERY_CACHE_ENTRIES = 64
_MAX_VOICEVOX_QUERY_CACHE_BYTES = 4 * 1024 * 1024
_MAX_VOICEVOX_QUERY_BYTES = 512 * 1024
_TEMP_FILE_MAX_AGE_SECONDS = 60 * 60
_TEMP_CLEANUP_INTERVAL_SECONDS = 15 * 60
_AZURE_TTS_CREDENTIAL_SCOPE = "azure-tts"
_AZURE_TTS_CONFIG_NAME = "azure_tts.json"
_AZURE_VOICE_CACHE_NAME = "azure_tts_voices.json"
_AZURE_USAGE_LOG_NAME = "azure_tts_usage.json"
_AZURE_TTS_TIMEOUT_SECONDS = 45
# Prefer the higher bitrate MP3; Anki then stores the finished file locally.
_AZURE_TTS_OUTPUT_FORMAT = "audio-24khz-96kbitrate-mono-mp3"
_AZURE_TTS_MAX_AUDIO_BYTES = 8 * 1024 * 1024
_AZURE_VOICE_LIST_TIMEOUT_SECONDS = 20
_AZURE_VOICE_LIST_MAX_BYTES = 2 * 1024 * 1024
_AZURE_VOICE_ID_RE = re.compile(r"[A-Za-z0-9-]{1,160}\Z")
_AZURE_USAGE_MAX_DAYS = 400
_AZURE_USAGE_MAX_BYTES = 256 * 1024
_AZURE_LOCALES = {
    "ja": ("ja-JP",),
    "zh": ("zh-CN", "zh-TW", "zh-HK"),
    "ko": ("ko-KR",),
}
_azure_usage_lock = threading.Lock()


def _normalize_azure_region(region: str) -> str:
    value = str(region or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9-]{2,64}", value):
        return ""
    return value


def get_tts_config() -> dict:
    """Read the non-secret TTS selection from profile-scoped data."""
    raw = read_json(
        get_user_data_path(_AZURE_TTS_CONFIG_NAME), {},
        lambda value: isinstance(value, dict), max_bytes=16 * 1024,
    )
    provider = "azure" if raw.get("provider") == "azure" else "edge"
    return {"provider": provider, "azure_region": _normalize_azure_region(raw.get("azure_region", ""))}


def get_azure_tts_status() -> dict:
    """Return UI-safe Azure configuration state without exposing the key."""
    config = get_tts_config()
    return {
        "enabled": config["provider"] == "azure",
        "region": config["azure_region"],
        "key_saved": bool(load_api_key(_AZURE_TTS_CREDENTIAL_SCOPE)),
    }


def save_azure_tts_config(api_key: str, region: str, *, enabled: bool = True) -> bool:
    """Save Azure region plus its key in the OS credential store only."""
    normalized_region = _normalize_azure_region(region)
    if not normalized_region:
        return False
    supplied_key = str(api_key or "").strip()
    if supplied_key:
        if not save_api_key(supplied_key, _AZURE_TTS_CREDENTIAL_SCOPE):
            return False
    elif not load_api_key(_AZURE_TTS_CREDENTIAL_SCOPE):
        return False
    atomic_write_json(get_user_data_path(_AZURE_TTS_CONFIG_NAME), {
        "provider": "azure" if enabled else "edge",
        "azure_region": normalized_region,
    })
    return True


def use_edge_tts() -> None:
    """Switch back to keyless Edge Neural without deleting Azure credentials."""
    config = get_tts_config()
    atomic_write_json(get_user_data_path(_AZURE_TTS_CONFIG_NAME), {
        "provider": "edge", "azure_region": config["azure_region"],
    })


def _empty_azure_usage_day() -> dict:
    return {
        "requests": 0,
        "characters": 0,
        "successes": 0,
        "successful_characters": 0,
        "failures": 0,
        "cache_hits": 0,
    }


def _normalise_azure_usage_day(value: object) -> dict:
    source = value if isinstance(value, dict) else {}
    result = _empty_azure_usage_day()
    for key in result:
        try:
            result[key] = max(0, int(source.get(key, 0)))
        except (TypeError, ValueError):
            continue
    return result


def _read_azure_usage_days() -> dict:
    raw = read_json(
        get_user_data_path(_AZURE_USAGE_LOG_NAME), {},
        lambda value: isinstance(value, dict), max_bytes=_AZURE_USAGE_MAX_BYTES,
    )
    source_days = raw.get("days", {})
    if not isinstance(source_days, dict):
        return {}
    return {
        day: _normalise_azure_usage_day(values)
        for day, values in source_days.items()
        if isinstance(day, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", day)
    }


def _record_azure_tts_usage(characters: int = 0, *, success: Optional[bool] = None,
                            cache_hit: bool = False) -> None:
    """Persist local Azure request counters without retaining text or credentials."""
    count = max(0, int(characters or 0))
    day = time.strftime("%Y-%m-%d")
    with _azure_usage_lock:
        try:
            days = _read_azure_usage_days()
            entry = _normalise_azure_usage_day(days.get(day))
            if cache_hit:
                entry["cache_hits"] += 1
            elif success is not None:
                entry["requests"] += 1
                entry["characters"] += count
                if success:
                    entry["successes"] += 1
                    entry["successful_characters"] += count
                else:
                    entry["failures"] += 1
            days[day] = entry
            retained_days = dict(sorted(days.items())[-_AZURE_USAGE_MAX_DAYS:])
            atomic_write_json(get_user_data_path(_AZURE_USAGE_LOG_NAME), {
                "version": 1,
                "days": retained_days,
            })
        except Exception as error:
            # Usage accounting must never prevent a card from receiving audio.
            logger.warning("Could not record local Azure Speech usage: %s", error)


def get_azure_tts_usage_summary(*, max_days: int = 90) -> dict:
    """Return UI-safe local estimates; Azure Portal remains billing authority."""
    with _azure_usage_lock:
        days = _read_azure_usage_days()
    rows = []
    for day, values in sorted(days.items(), reverse=True)[:max(1, min(int(max_days), _AZURE_USAGE_MAX_DAYS))]:
        rows.append({"date": day, **_normalise_azure_usage_day(values)})

    def totals(entries):
        result = _empty_azure_usage_day()
        for entry in entries:
            for key in result:
                result[key] += entry[key]
        return result

    month = time.strftime("%Y-%m")
    return {
        "month": month,
        "month_total": totals(entry for entry in rows if entry["date"].startswith(month)),
        "all_time_total": totals(_normalise_azure_usage_day(entry) for entry in days.values()),
        "days": rows,
    }


def _normalize_azure_voice(record: object) -> Optional[dict]:
    """Keep only the UI-safe fields needed from Azure's voice catalogue."""
    if not isinstance(record, dict):
        return None
    voice_id = str(record.get("ShortName") or record.get("Name") or record.get("id") or "").strip()
    locale = str(record.get("Locale") or record.get("locale") or "").strip()
    display_name = str(record.get("DisplayName") or record.get("display_name") or voice_id).strip()
    gender = str(record.get("Gender") or record.get("gender") or "").strip().lower()
    voice_type = str(record.get("VoiceType") or "").strip().lower()
    if (
        not _AZURE_VOICE_ID_RE.fullmatch(voice_id)
        or not re.fullmatch(r"[a-z]{2,3}-[A-Z]{2,4}", locale)
        or not display_name
        or len(display_name) > 120
    ):
        return None
    # The endpoint normally returns Neural voices only.  Keep the suffix check
    # for older responses which omit VoiceType.
    if voice_type and voice_type != "neural":
        return None
    if not voice_type and not voice_id.endswith("Neural"):
        return None
    return {
        "id": voice_id,
        "display_name": display_name,
        "locale": locale,
        "gender": "female" if gender == "female" else "male" if gender == "male" else "unknown",
    }


def _voice_options_for_language(records: object, lang: str) -> list:
    """Filter official Azure voices to the learning languages Bento Forge supports."""
    wanted_locales = _AZURE_LOCALES.get(lang, ())
    options = []
    seen = set()
    for record in records if isinstance(records, list) else ():
        voice = _normalize_azure_voice(record)
        if voice is None:
            continue
        locale = voice["locale"]
        if lang == "en":
            matches_language = locale.startswith("en-")
        else:
            matches_language = locale in wanted_locales
        if not matches_language or voice["id"] in seen:
            continue
        seen.add(voice["id"])
        gender_label = {"female": "Female", "male": "Male"}.get(voice["gender"], "Voice")
        options.append({
            "id": voice["id"],
            "name": f"{voice['display_name']} ({locale} · {gender_label})",
            "gender": voice["gender"],
            "locale": locale,
        })

    preferred = {
        "ja": ("ja-JP",),
        "zh": ("zh-CN", "zh-TW", "zh-HK"),
        "ko": ("ko-KR",),
        "en": ("en-US", "en-GB"),
    }.get(lang, ())
    return sorted(
        options,
        key=lambda voice: (
            voice["locale"] not in preferred,
            preferred.index(voice["locale"]) if voice["locale"] in preferred else len(preferred),
            voice["locale"], voice["name"].casefold(),
        ),
    )


def get_cached_azure_voice_options(lang: str) -> list:
    """Read the last verified Azure voice list without any network request."""
    config = get_tts_config()
    region = config.get("azure_region", "")
    if not region:
        return []
    raw = read_json(
        get_user_data_path(_AZURE_VOICE_CACHE_NAME), {},
        lambda value: isinstance(value, dict), max_bytes=_AZURE_VOICE_LIST_MAX_BYTES,
    )
    if raw.get("region") != region:
        return []
    return _voice_options_for_language(raw.get("voices"), lang)


def fetch_azure_voice_options(lang: str) -> list:
    """Fetch and cache official Neural voices for the configured Azure region.

    This is deliberately called by a worker, never by the Qt UI thread.
    Credentials remain in the request header and are never written to the cache.
    """
    config = get_tts_config()
    region = config.get("azure_region", "")
    api_key = load_api_key(_AZURE_TTS_CREDENTIAL_SCOPE) or ""
    if not region or not api_key:
        raise RuntimeError("Azure Speech region or credential is unavailable")
    request = urllib.request.Request(
        f"https://{region}.tts.speech.microsoft.com/cognitiveservices/voices/list",
        headers={
            "Ocp-Apim-Subscription-Key": api_key,
            "User-Agent": "BentoForge-Anki",
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=_AZURE_VOICE_LIST_TIMEOUT_SECONDS) as response:
        payload = response.read(_AZURE_VOICE_LIST_MAX_BYTES + 1)
    if len(payload) > _AZURE_VOICE_LIST_MAX_BYTES:
        raise ValueError("Azure Speech voice list exceeds the safety limit")
    try:
        records = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Azure Speech returned an invalid voice list") from error
    if not isinstance(records, list):
        raise ValueError("Azure Speech returned an invalid voice list")
    safe_records = [voice for item in records if (voice := _normalize_azure_voice(item))]
    atomic_write_json(get_user_data_path(_AZURE_VOICE_CACHE_NAME), {
        "region": region,
        "saved_at": int(time.time()),
        "voices": safe_records,
    })
    return _voice_options_for_language(safe_records, lang)


def _check_library_available(name: str) -> bool:
    """Return whether a TTS module is installed, without attempting installation."""
    with _dependency_cache_lock:
        if name in _dependency_cache:
            return _dependency_cache[name]
        try:
            __import__(name)
            _dependency_cache[name] = True
            return True
        except ImportError:
            _dependency_cache[name] = False
            return False


# ═══════════════════════════════════════════════════════════
#  Dependency status and user-actionable installation instructions
# ═══════════════════════════════════════════════════════════
def get_tts_dependency_status() -> Dict[str, bool]:
    """Return installed status for optional TTS providers."""
    return {module: _check_library_available(module) for module in _DEPENDENCIES}


def get_tts_install_command(module_name: str) -> str:
    """Return the pinned command the user may run in their chosen environment."""
    requirement = _DEPENDENCIES.get(module_name)
    if requirement is None:
        raise ValueError(f"Unknown TTS dependency: {module_name}")
    return f"python -m pip install {requirement}"


def _report_missing_dependency(module_name: str) -> None:
    log_event(
        "TTS_DEPENDENCY_MISSING",
        "show_explicit_install_instruction",
        install_command=get_tts_install_command(module_name),
        provider=module_name,
    )


# Compatibility names retained for callers/tests.  These used to install a
# package silently; now they only perform the dependency check.
def _install_edge_tts() -> bool:
    available = _check_library_available("edge_tts")
    if not available:
        _report_missing_dependency("edge_tts")
    return available


def _install_gtts() -> bool:
    available = _check_library_available("gtts")
    if not available:
        _report_missing_dependency("gtts")
    return available


# ═══════════════════════════════════════════════════════════
#  Cache, per-key generation locks, and temporary-file cleanup
# ═══════════════════════════════════════════════════════════
_audio_query_cache: "OrderedDict[str, bytes]" = OrderedDict()
_audio_query_cache_bytes = 0
_audio_query_cache_lock = threading.Lock()
_audio_generation_locks: Dict[str, list] = {}
_audio_generation_locks_lock = threading.Lock()
_last_temp_cleanup = 0.0
_temp_cleanup_lock = threading.Lock()

# Event loop cho Edge TTS — mỗi thread có loop riêng (thread-safe cho ThreadPoolExecutor)
_edge_loop_local = threading.local()


@contextmanager
def _audio_generation_lock(cache_key: str) -> Iterator[None]:
    """Serialize writers for one cache key without retaining locks forever."""
    with _audio_generation_locks_lock:
        entry = _audio_generation_locks.get(cache_key)
        if entry is None:
            entry = [threading.Lock(), 0]
            _audio_generation_locks[cache_key] = entry
        entry[1] += 1
    try:
        with entry[0]:
            yield
    finally:
        with _audio_generation_locks_lock:
            entry[1] -= 1
            if entry[1] == 0 and _audio_generation_locks.get(cache_key) is entry:
                del _audio_generation_locks[cache_key]


def _temporary_audio_path(filepath: str) -> str:
    return f"{filepath}.{os.getpid()}.{threading.get_ident()}.tmp"


def _discard_file(path: str) -> None:
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass
    except OSError:
        logger.debug("Could not remove temporary TTS file")


def _commit_audio_file(temporary_path: str, filepath: str) -> bool:
    """Atomically publish a non-empty audio file after a successful request."""
    try:
        if os.path.getsize(temporary_path) <= 0:
            _discard_file(temporary_path)
            return False
        os.replace(temporary_path, filepath)
        return True
    except OSError:
        _discard_file(temporary_path)
        return False


def _cleanup_temporary_audio_files(media_dir: str) -> None:
    """Remove only stale Bento Forge temporary files; never delete card media."""
    global _last_temp_cleanup
    now = time.monotonic()
    with _temp_cleanup_lock:
        # ``0`` is the startup/test sentinel, not a real monotonic timestamp.
        # A short-lived process can have ``now < interval`` and must still make
        # its first cleanup pass.
        if (
            _last_temp_cleanup > 0
            and now - _last_temp_cleanup < _TEMP_CLEANUP_INTERVAL_SECONDS
        ):
            return
        _last_temp_cleanup = now
    try:
        cutoff = time.time() - _TEMP_FILE_MAX_AGE_SECONDS
        for name in os.listdir(media_dir):
            if not name.startswith("anki_") or not name.endswith(".tmp"):
                continue
            path = os.path.join(media_dir, name)
            try:
                if os.path.isfile(path) and os.path.getmtime(path) < cutoff:
                    os.unlink(path)
            except OSError:
                continue
    except OSError:
        logger.debug("Could not clean temporary TTS files")


def _get_cached_voicevox_query(cache_key: str) -> Optional[bytes]:
    with _audio_query_cache_lock:
        data = _audio_query_cache.get(cache_key)
        if data is not None:
            _audio_query_cache.move_to_end(cache_key)
        return data


def _cache_voicevox_query(cache_key: str, query_data: bytes) -> None:
    global _audio_query_cache_bytes
    if len(query_data) > _MAX_VOICEVOX_QUERY_BYTES:
        return
    with _audio_query_cache_lock:
        previous = _audio_query_cache.pop(cache_key, None)
        if previous is not None:
            _audio_query_cache_bytes -= len(previous)
        _audio_query_cache[cache_key] = query_data
        _audio_query_cache_bytes += len(query_data)
        while (
            len(_audio_query_cache) > _MAX_VOICEVOX_QUERY_CACHE_ENTRIES
            or _audio_query_cache_bytes > _MAX_VOICEVOX_QUERY_CACHE_BYTES
        ):
            _, evicted = _audio_query_cache.popitem(last=False)
            _audio_query_cache_bytes -= len(evicted)


def _get_edge_loop():
    """Lấy event loop cho thread hiện tại (mỗi thread có loop riêng, lazy singleton)."""
    import asyncio
    loop = getattr(_edge_loop_local, "loop", None)
    if loop is None or loop.is_closed():
        loop = asyncio.new_event_loop()
        _edge_loop_local.loop = loop
    return loop


def _get_media_dir() -> str:
    """Lấy thư mục media của Anki — import aqt lazy để tránh lỗi khi test."""
    from aqt import mw
    return mw.col.media.dir()


_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    """Loại bỏ thẻ HTML (vd <b>…</b> dùng để highlight pattern) trước khi TTS.

    Giữ nguyên nội dung bên trong thẻ — chỉ bỏ tag + decode entity HTML
    (< & ...) để giọng đọc không phát âm "b"/"pi" ở cuối câu ví dụ.
    """
    if not text:
        return text
    cleaned = _HTML_TAG_RE.sub("", text)
    cleaned = html.unescape(cleaned)
    return cleaned.strip()


# ═══════════════════════════════════════════════════════════
#  Edge TTS Provider
# ═══════════════════════════════════════════════════════════
async def _await_edge_generation(awaitable, cancel_event: Optional[threading.Event]) -> None:
    """Bound Edge TTS and let a queued worker abandon it promptly."""
    task = asyncio.ensure_future(awaitable)
    deadline = time.monotonic() + _EDGE_TOTAL_TIMEOUT_SECONDS
    try:
        while not task.done():
            if cancel_event is not None and cancel_event.is_set():
                task.cancel()
                raise asyncio.CancelledError()
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                task.cancel()
                raise TimeoutError("Edge TTS timed out")
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=min(0.2, remaining))
            except asyncio.TimeoutError:
                continue
        await task
    finally:
        if not task.done():
            task.cancel()


def _run_edge_generation(awaitable, cancel_event: Optional[threading.Event]) -> None:
    loop = _get_edge_loop()
    coroutine = _await_edge_generation(awaitable, cancel_event)
    if loop.is_running():
        temporary_loop = asyncio.new_event_loop()
        try:
            temporary_loop.run_until_complete(coroutine)
        finally:
            temporary_loop.close()
    else:
        loop.run_until_complete(coroutine)


def get_audio_edge_tts(
    text: str,
    voice: str,
    lang: str = "ja",
    rate: str = None,
    cancel_event: Optional[threading.Event] = None,
) -> Optional[str]:
    """Create Edge audio with a bounded request and atomic media publication."""
    if not text or not text.strip():
        return ""

    text = _strip_html(text)
    if not text:
        return ""

    rate_suffix = f"_{rate}" if rate else ""
    filename = f"anki_edge_{hashlib.md5(f'{voice}_{lang}_{text}{rate_suffix}'.encode('utf-8')).hexdigest()}.mp3"
    try:
        media_dir = _get_media_dir()
    except Exception:
        return ""
    filepath = os.path.join(media_dir, filename)
    _cleanup_temporary_audio_files(media_dir)

    if os.path.exists(filepath):
        return f"[sound:{filename}]"

    cache_key = f"edge:{filename}"
    with _audio_generation_lock(cache_key):
        if os.path.exists(filepath):
            return f"[sound:{filename}]"
        temporary_path = _temporary_audio_path(filepath)
        try:
            if cancel_event is not None and cancel_event.is_set():
                return ""
            import edge_tts

            communicate = edge_tts.Communicate(text, voice, rate=rate) if rate else edge_tts.Communicate(text, voice)
            _run_edge_generation(communicate.save(temporary_path), cancel_event)
            if _commit_audio_file(temporary_path, filepath):
                return f"[sound:{filename}]"
        except asyncio.CancelledError:
            _discard_file(temporary_path)
            return ""
        except Exception as error:
            _discard_file(temporary_path)
            logger.warning("Edge Neural TTS failed; audio skipped instead of using gTTS fallback: %s", error)
            return ""

    return ""


def get_audio_azure_tts(
    text: str,
    voice: str,
    lang: str = "ja",
    rate: str = None,
    cancel_event: Optional[threading.Event] = None,
    track_usage: bool = True,
) -> Optional[str]:
    """Create official Azure Neural audio with an atomic media publication."""
    if not text or not text.strip() or (cancel_event is not None and cancel_event.is_set()):
        return ""
    config = get_tts_config()
    region = config.get("azure_region", "")
    api_key = load_api_key(_AZURE_TTS_CREDENTIAL_SCOPE) or ""
    if not region or not api_key:
        logger.warning("Azure Speech TTS is selected but its region or credential is unavailable")
        return ""
    text = _strip_html(text)
    if not text:
        return ""

    rate_suffix = f"_{rate}" if rate else ""
    digest = hashlib.md5(f"{region}_{voice}_{lang}_{text}{rate_suffix}".encode("utf-8")).hexdigest()
    filename = f"anki_azure_{digest}.mp3"
    try:
        media_dir = _get_media_dir()
    except Exception:
        return ""
    filepath = os.path.join(media_dir, filename)
    _cleanup_temporary_audio_files(media_dir)
    if os.path.exists(filepath):
        if track_usage:
            _record_azure_tts_usage(cache_hit=True)
        return f"[sound:{filename}]"

    cache_key = f"azure:{filename}"
    with _audio_generation_lock(cache_key):
        if os.path.exists(filepath):
            if track_usage:
                _record_azure_tts_usage(cache_hit=True)
            return f"[sound:{filename}]"
        temporary_path = _temporary_audio_path(filepath)
        request_started = False
        request_accounted = False
        try:
            if cancel_event is not None and cancel_event.is_set():
                return ""
            locale = {"ja": "ja-JP", "zh": "zh-CN", "ko": "ko-KR", "en": "en-US"}.get(lang, "en-US")
            prosody = f'<prosody rate="{html.escape(rate, quote=True)}">{html.escape(text)}</prosody>' if rate else html.escape(text)
            ssml = (
                f'<speak version="1.0" xml:lang="{locale}">'
                f'<voice name="{html.escape(voice, quote=True)}">{prosody}</voice></speak>'
            ).encode("utf-8")
            request = urllib.request.Request(
                f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1",
                data=ssml,
                headers={
                    "Ocp-Apim-Subscription-Key": api_key,
                    "Content-Type": "application/ssml+xml",
                    "X-Microsoft-OutputFormat": _AZURE_TTS_OUTPUT_FORMAT,
                    "User-Agent": "BentoForge-Anki",
                },
                method="POST",
            )
            request_started = True
            with urllib.request.urlopen(request, timeout=_AZURE_TTS_TIMEOUT_SECONDS) as response:
                audio = response.read(_AZURE_TTS_MAX_AUDIO_BYTES + 1)
            if len(audio) > _AZURE_TTS_MAX_AUDIO_BYTES:
                raise ValueError("Azure Speech audio response exceeds the safety limit")
            if track_usage:
                _record_azure_tts_usage(len(text), success=True)
            request_accounted = True
            if cancel_event is not None and cancel_event.is_set():
                return ""
            with open(temporary_path, "wb") as handle:
                handle.write(audio)
            if _commit_audio_file(temporary_path, filepath):
                return f"[sound:{filename}]"
        except Exception as error:
            _discard_file(temporary_path)
            if track_usage and request_started and not request_accounted:
                _record_azure_tts_usage(len(text), success=False)
            logger.warning("Azure Speech TTS failed; audio skipped: %s", error)
            return ""

    return ""


# ═══════════════════════════════════════════════════════════
#  Google TTS Provider
# ═══════════════════════════════════════════════════════════
def get_audio_gtts(text: str, lang: str = "ja", cancel_event: Optional[threading.Event] = None) -> Optional[str]:
    """Create gTTS audio with bounded network timeouts and atomic output."""
    if not text or not text.strip():
        return ""

    text = _strip_html(text)
    if not text:
        return ""

    filename = f"anki_gtts_{hashlib.md5(f'{lang}_{text}'.encode('utf-8')).hexdigest()}.mp3"
    try:
        media_dir = _get_media_dir()
    except Exception:
        return ""
    filepath = os.path.join(media_dir, filename)
    _cleanup_temporary_audio_files(media_dir)

    if os.path.exists(filepath):
        return f"[sound:{filename}]"

    with _audio_generation_lock(f"gtts:{filename}"):
        if os.path.exists(filepath):
            return f"[sound:{filename}]"
        temporary_path = _temporary_audio_path(filepath)
        try:
            if cancel_event is not None and cancel_event.is_set():
                return ""
            from gtts import gTTS

            lang_map = {"ja": "ja", "zh": "zh-CN"}
            tts_lang = lang_map.get(lang, lang)
            tts = gTTS(
                text=text,
                lang=tts_lang,
                slow=False,
                timeout=(_CONNECT_TIMEOUT_SECONDS, _READ_TIMEOUT_SECONDS),
            )
            tts.save(temporary_path)
            if cancel_event is not None and cancel_event.is_set():
                _discard_file(temporary_path)
                return ""
            if _commit_audio_file(temporary_path, filepath):
                return f"[sound:{filename}]"
        except Exception as error:
            _discard_file(temporary_path)
            logger.warning("gTTS failed: %s", error)

    return ""


# ═══════════════════════════════════════════════════════════
#  VoiceVox Provider (Japanese)
# ═══════════════════════════════════════════════════════════
def get_audio_voicevox(
    text: str,
    speaker_id: int = 3,
    cancel_event: Optional[threading.Event] = None,
) -> Optional[str]:
    """Create VoiceVox audio with bounded HTTP calls and atomic output."""
    if not text or not text.strip():
        return ""

    text = _strip_html(text)
    if not text:
        return ""

    cache_key = f"{text}_{speaker_id}"
    filename = f"anki_vv_{hashlib.md5(cache_key.encode('utf-8')).hexdigest()}.wav"
    try:
        media_dir = _get_media_dir()
    except Exception:
        return ""
    filepath = os.path.join(media_dir, filename)
    _cleanup_temporary_audio_files(media_dir)

    if os.path.exists(filepath):
        return f"[sound:{filename}]"

    with _audio_generation_lock(f"voicevox:{filename}"):
        if os.path.exists(filepath):
            return f"[sound:{filename}]"
        temporary_path = _temporary_audio_path(filepath)
        try:
            if cancel_event is not None and cancel_event.is_set():
                return ""
            host = "http://127.0.0.1:50021"
            query_data = _get_cached_voicevox_query(cache_key)
            if query_data is None:
                query_url = f"{host}/audio_query?text={urllib.parse.quote(text)}&speaker={speaker_id}"
                req_query = urllib.request.Request(query_url, method="POST")
                with urllib.request.urlopen(req_query, timeout=_CONNECT_TIMEOUT_SECONDS) as response:
                    query_data = response.read(_MAX_VOICEVOX_QUERY_BYTES + 1)
                if len(query_data) > _MAX_VOICEVOX_QUERY_BYTES:
                    raise ValueError("VoiceVox query response exceeds size limit")
                _cache_voicevox_query(cache_key, query_data)

            if cancel_event is not None and cancel_event.is_set():
                return ""
            synth_url = f"{host}/synthesis?speaker={speaker_id}"
            request = urllib.request.Request(synth_url, data=query_data, method="POST")
            request.add_header("Content-Type", "application/json")
            cancelled = False
            with urllib.request.urlopen(request, timeout=_READ_TIMEOUT_SECONDS) as response, open(temporary_path, "wb") as output:
                while True:
                    if cancel_event is not None and cancel_event.is_set():
                        cancelled = True
                        break
                    chunk = response.read(64 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
            if cancelled:
                _discard_file(temporary_path)
                return ""
            if _commit_audio_file(temporary_path, filepath):
                return f"[sound:{filename}]"
        except Exception as error:
            _discard_file(temporary_path)
            logger.debug("VoiceVox failed: %s", error)

    return ""
