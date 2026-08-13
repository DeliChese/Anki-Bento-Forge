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
import os
import re
import threading
import time
import urllib.parse
import urllib.request
from collections import OrderedDict
from contextlib import contextmanager
from typing import Dict, Iterator, Optional

from utils.logger import get_logger

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
    logger.warning(
        "Optional TTS dependency '%s' is unavailable. Install it explicitly with: %s",
        module_name,
        get_tts_install_command(module_name),
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
        if now - _last_temp_cleanup < _TEMP_CLEANUP_INTERVAL_SECONDS:
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
            logger.warning("Edge TTS failed; trying gTTS fallback: %s", error)
            return get_audio_gtts(text, lang, cancel_event=cancel_event)

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
