"""Local MeloTTS provider bridge for Bento Forge.

MeloTTS runs in its own Python 3.11 environment because Anki's interpreter is
not an appropriate host for PyTorch.  Requests never leave the computer: the
bridge starts a token-protected loopback worker and receives a WAV response.
"""

from __future__ import annotations

import hashlib
import json
import os
import atexit
import secrets
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request
from typing import Optional

from utils.logger import get_logger

logger = get_logger()

_MAX_AUDIO_BYTES = 32 * 1024 * 1024
_START_TIMEOUT_SECONDS = 60
_REQUEST_TIMEOUT_SECONDS = 240
_service_lock = threading.Lock()
_service_process: Optional[subprocess.Popen] = None
_service_port: Optional[int] = None
_service_token: Optional[str] = None


def _addon_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _runtime_python() -> str:
    return os.path.join(_addon_root(), "runtime", "melo-tts", "Scripts", "python.exe")


def _service_script() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "melo_service.py")


def is_melo_available() -> bool:
    """Return whether the separately installed local runtime is ready to start."""
    return os.path.isfile(_runtime_python()) and os.path.isfile(_service_script())


def _new_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _request(path: str, data: bytes = None, timeout: float = 5) -> bytes:
    if _service_port is None or _service_token is None:
        raise RuntimeError("MeloTTS service is not running")
    request = urllib.request.Request(
        f"http://127.0.0.1:{_service_port}{path}", data=data,
        method="POST" if data is not None else "GET",
    )
    request.add_header("X-Bento-Melo-Token", _service_token)
    if data is not None:
        request.add_header("Content-Type", "application/json; charset=utf-8")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(_MAX_AUDIO_BYTES + 1)


def _service_healthy() -> bool:
    try:
        return _request("/health") == b'{"ok":true}'
    except (OSError, urllib.error.URLError, urllib.error.HTTPError):
        return False


def _ensure_service() -> bool:
    global _service_process, _service_port, _service_token
    with _service_lock:
        if _service_process is not None and _service_process.poll() is None and _service_healthy():
            return True
        if not is_melo_available():
            logger.warning("MeloTTS local runtime is not installed")
            return False
        _service_port = _new_loopback_port()
        _service_token = secrets.token_urlsafe(32)
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        _service_process = subprocess.Popen(
            [_runtime_python(), _service_script(), "--port", str(_service_port), "--token", _service_token],
            cwd=_addon_root(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )
        deadline = time.monotonic() + _START_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            if _service_process.poll() is not None:
                break
            if _service_healthy():
                return True
            time.sleep(0.2)
        logger.warning("MeloTTS local service did not start")
        return False


def _stop_service() -> None:
    """Stop the child worker when Anki exits; no model process is left behind."""
    global _service_process, _service_port, _service_token
    with _service_lock:
        if _service_process is not None and _service_process.poll() is None:
            try:
                _service_process.terminate()
                _service_process.wait(timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                try:
                    _service_process.kill()
                except OSError:
                    pass
        _service_process = None
        _service_port = None
        _service_token = None


atexit.register(_stop_service)


def _rate_to_speed(rate: Optional[str]) -> float:
    try:
        percent = int(str(rate or "0%").replace("%", ""))
    except ValueError:
        percent = 0
    return max(0.25, min(4.0, 1.0 + percent / 100.0))


def get_audio_melo_tts(text: str, voice: str, lang: str, rate: Optional[str] = None,
                       cancel_event: Optional[threading.Event] = None) -> str:
    """Generate a local WAV and atomically publish it into Anki media."""
    if not text or not text.strip() or (cancel_event and cancel_event.is_set()) or not _ensure_service():
        return ""
    from .tts import (
        _audio_generation_lock, _cleanup_temporary_audio_files, _commit_audio_file,
        _discard_file, _get_media_dir, _strip_html, _temporary_audio_path,
    )

    clean_text = _strip_html(text)
    if not clean_text:
        return ""
    filename = "anki_melo_{}.wav".format(
        hashlib.md5(f"{voice}_{lang}_{rate}_{clean_text}".encode("utf-8")).hexdigest()
    )
    try:
        media_dir = _get_media_dir()
    except Exception:
        return ""
    filepath = os.path.join(media_dir, filename)
    _cleanup_temporary_audio_files(media_dir)
    if os.path.exists(filepath):
        return f"[sound:{filename}]"
    with _audio_generation_lock(f"melo:{filename}"):
        if os.path.exists(filepath):
            return f"[sound:{filename}]"
        temporary = _temporary_audio_path(filepath)
        try:
            if cancel_event and cancel_event.is_set():
                return ""
            payload = json.dumps({
                "text": clean_text, "lang": lang, "voice": voice,
                "speed": _rate_to_speed(rate),
            }, ensure_ascii=False).encode("utf-8")
            audio = _request("/synthesize", payload, timeout=_REQUEST_TIMEOUT_SECONDS)
            if cancel_event and cancel_event.is_set():
                return ""
            if len(audio) < 44 or len(audio) > _MAX_AUDIO_BYTES or audio[:4] != b"RIFF" or audio[8:12] != b"WAVE":
                raise ValueError("invalid MeloTTS audio")
            with open(temporary, "wb") as output:
                output.write(audio)
            if _commit_audio_file(temporary, filepath):
                return f"[sound:{filename}]"
        except Exception as error:
            logger.warning("MeloTTS local synthesis failed: %s", error)
        finally:
            _discard_file(temporary)
    return ""
