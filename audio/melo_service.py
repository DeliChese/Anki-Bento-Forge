"""Loopback-only MeloTTS worker, executed by the dedicated Python 3.11 runtime.

This module deliberately has no Anki imports.  It receives requests only from
the add-on process on 127.0.0.1 and keeps loaded language models in memory.
"""

from __future__ import annotations

import argparse
import hmac
import json
import os
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


_ADDON_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MELO_SOURCE = os.path.join(_ADDON_ROOT, "runtime", "MeloTTS")
if _MELO_SOURCE not in sys.path:
    # This must precede this script's ``audio`` directory, whose melo.py bridge
    # would otherwise shadow the third-party ``melo`` package.
    sys.path.insert(0, _MELO_SOURCE)
if _ADDON_ROOT not in sys.path:
    sys.path.insert(0, _ADDON_ROOT)


_MAX_REQUEST_BYTES = 128 * 1024
_MAX_AUDIO_BYTES = 32 * 1024 * 1024
_LANGUAGES = {"ja": "JP", "zh": "ZH", "ko": "KR", "en": "EN"}
_VOICES = {
    "ja": {"JP"},
    "zh": {"ZH"},
    "ko": {"KR"},
    "en": {"EN-US", "EN-BR", "EN_INDIA", "EN-AU", "EN-Default"},
}


class MeloServer(ThreadingHTTPServer):
    """Server state shared by authenticated request handlers."""

    daemon_threads = True

    def __init__(self, address, token: str):
        super().__init__(address, MeloHandler)
        self.token = token
        self.models = {}
        self.model_lock = threading.Lock()

    def get_model(self, lang: str):
        with self.model_lock:
            model = self.models.get(lang)
            if model is None:
                import torch
                from melo.api import TTS

                device = "cuda:0" if torch.cuda.is_available() else "cpu"
                model = TTS(language=_LANGUAGES[lang], device=device)
                self.models[lang] = model
            return model


class MeloHandler(BaseHTTPRequestHandler):
    server: MeloServer

    def log_message(self, _format, *_args):
        """Do not emit card text to a console log."""

    def _authorized(self) -> bool:
        supplied = self.headers.get("X-Bento-Melo-Token", "")
        return hmac.compare_digest(supplied, self.server.token)

    def _send(self, status: int, body: bytes, content_type: str = "application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path != "/health" or not self._authorized():
            self._send(403, b'{"ok":false}')
            return
        self._send(200, b'{"ok":true}')

    def do_POST(self):
        if self.path != "/synthesize" or not self._authorized():
            self._send(403, b'{"ok":false}')
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size <= 0 or size > _MAX_REQUEST_BYTES:
                raise ValueError("invalid request size")
            payload = json.loads(self.rfile.read(size).decode("utf-8"))
            text = str(payload.get("text", "")).strip()
            lang = str(payload.get("lang", ""))
            voice = str(payload.get("voice", ""))
            speed = float(payload.get("speed", 1.0))
            if not text or len(text) > 12_000 or lang not in _LANGUAGES:
                raise ValueError("invalid text or language")
            if voice not in _VOICES[lang] or not 0.25 <= speed <= 4.0:
                raise ValueError("invalid voice or speed")

            temporary = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            temporary.close()
            try:
                model = self.server.get_model(lang)
                speaker_id = model.hps.data.spk2id[voice]
                model.tts_to_file(text, speaker_id, temporary.name, speed=speed)
                with open(temporary.name, "rb") as audio:
                    body = audio.read(_MAX_AUDIO_BYTES + 1)
                if len(body) < 44 or len(body) > _MAX_AUDIO_BYTES or body[:4] != b"RIFF" or body[8:12] != b"WAVE":
                    raise ValueError("invalid generated audio")
                self._send(200, body, "audio/wav")
            finally:
                try:
                    os.remove(temporary.name)
                except OSError:
                    pass
        except Exception as error:
            # Keep user text and implementation details out of the response.
            self._send(500, ('{"ok":false,"error":"' + type(error).__name__ + '"}').encode("ascii"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535 or len(args.token) < 32:
        raise SystemExit("invalid loopback configuration")
    MeloServer(("127.0.0.1", args.port), args.token).serve_forever()


if __name__ == "__main__":
    main()
