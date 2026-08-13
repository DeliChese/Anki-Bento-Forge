"""Safety invariants for optional TTS providers.

Load the provider module directly so these tests remain independent from Anki
and from test modules that replace ``audio.tts`` with a lightweight mock.
"""

import importlib.util
import os
import threading
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[1]


def _load_tts_module():
    spec = importlib.util.spec_from_file_location("bento_tts_safety", _ROOT / "audio" / "tts.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_dependency_install_commands_are_pinned_and_explicit():
    tts = _load_tts_module()

    assert tts.get_tts_install_command("edge_tts") == "python -m pip install edge-tts==7.2.7"
    assert tts.get_tts_install_command("gtts") == "python -m pip install gTTS==2.5.4"


def test_audio_commit_is_atomic_and_rejects_empty_files(tmp_path):
    tts = _load_tts_module()
    output = tmp_path / "audio.mp3"
    temporary = tmp_path / "audio.mp3.tmp"
    temporary.write_bytes(b"audio")

    assert tts._commit_audio_file(str(temporary), str(output)) is True
    assert output.read_bytes() == b"audio"
    assert not temporary.exists()

    empty = tmp_path / "empty.tmp"
    empty.touch()
    assert tts._commit_audio_file(str(empty), str(output)) is False
    assert output.read_bytes() == b"audio"


def test_cancelled_edge_request_never_imports_or_publishes_audio(tmp_path):
    tts = _load_tts_module()
    cancelled = threading.Event()
    cancelled.set()
    tts._get_media_dir = lambda: str(tmp_path)

    assert tts.get_audio_edge_tts("テスト", "ja-JP-NanamiNeural", cancel_event=cancelled) == ""
    assert list(tmp_path.iterdir()) == []


def test_voicevox_query_cache_has_entry_and_byte_bounds():
    tts = _load_tts_module()
    tts._MAX_VOICEVOX_QUERY_CACHE_ENTRIES = 2
    tts._MAX_VOICEVOX_QUERY_CACHE_BYTES = 6
    tts._MAX_VOICEVOX_QUERY_BYTES = 4

    tts._cache_voicevox_query("one", b"111")
    tts._cache_voicevox_query("two", b"222")
    tts._cache_voicevox_query("three", b"333")

    assert tts._get_cached_voicevox_query("one") is None
    assert len(tts._audio_query_cache) == 2
    assert tts._audio_query_cache_bytes <= 6


def test_cleanup_only_removes_stale_bento_temporary_files(tmp_path):
    tts = _load_tts_module()
    stale_temp = tmp_path / "anki_edge_old.mp3.1.1.tmp"
    card_media = tmp_path / "anki_edge_card.mp3"
    unrelated = tmp_path / "other.tmp"
    stale_temp.write_bytes(b"partial")
    card_media.write_bytes(b"audio")
    unrelated.write_bytes(b"keep")
    old_timestamp = 1
    os.utime(stale_temp, (old_timestamp, old_timestamp))
    tts._last_temp_cleanup = 0

    tts._cleanup_temporary_audio_files(str(tmp_path))

    assert not stale_temp.exists()
    assert card_media.exists()
    assert unrelated.exists()
