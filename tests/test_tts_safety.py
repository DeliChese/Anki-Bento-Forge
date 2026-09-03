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


def test_azure_settings_keep_key_out_of_profile_json(tmp_path):
    tts = _load_tts_module()
    keys = {}
    tts.get_user_data_path = lambda name: str(tmp_path / name)
    tts.save_api_key = lambda key, scope: keys.setdefault(scope, key) == key
    tts.load_api_key = lambda scope: keys.get(scope, "")

    assert tts.save_azure_tts_config("secret-key", "SoutheastAsia") is True
    saved = (tmp_path / "azure_tts.json").read_text(encoding="utf-8")
    assert "secret-key" not in saved
    assert tts.get_azure_tts_status() == {
        "enabled": True, "region": "southeastasia", "key_saved": True,
    }


def test_azure_tts_posts_escaped_ssml_and_publishes_atomically(tmp_path):
    tts = _load_tts_module()
    requested = {}

    class Response:
        def __enter__(self): return self
        def __exit__(self, *_args): return False
        def read(self, _size=-1): return b"azure-mp3"

    def urlopen(request, timeout):
        requested["request"] = request
        requested["timeout"] = timeout
        return Response()

    tts.get_tts_config = lambda: {"provider": "azure", "azure_region": "southeastasia"}
    tts.load_api_key = lambda _scope: "secret-key"
    tts._get_media_dir = lambda: str(tmp_path)
    tts.urllib.request.urlopen = urlopen

    tag = tts.get_audio_azure_tts("a < b & c", "en-US-JennyNeural", "en", rate="+0%")
    assert tag.startswith("[sound:anki_azure_")
    assert (tmp_path / tag[7:-1]).read_bytes() == b"azure-mp3"
    assert b"a &lt; b &amp; c" in requested["request"].data
    assert requested["request"].full_url.startswith("https://southeastasia.tts.speech.microsoft.com/")
    assert requested["request"].get_header("X-microsoft-outputformat") == tts._AZURE_TTS_OUTPUT_FORMAT
    assert requested["timeout"] == tts._AZURE_TTS_TIMEOUT_SECONDS


def test_azure_preview_does_not_change_local_usage_counter(tmp_path):
    tts = _load_tts_module()

    class Response:
        def __enter__(self): return self
        def __exit__(self, *_args): return False
        def read(self, _size=-1): return b"azure-mp3"

    recorded = []
    tts.get_tts_config = lambda: {"provider": "azure", "azure_region": "southeastasia"}
    tts.load_api_key = lambda _scope: "secret-key"
    tts._get_media_dir = lambda: str(tmp_path)
    tts.urllib.request.urlopen = lambda *_args, **_kwargs: Response()
    tts._record_azure_tts_usage = lambda *args, **kwargs: recorded.append((args, kwargs))

    assert tts.get_audio_azure_tts(
        "preview only", "en-US-JennyNeural", "en", track_usage=False,
    ).startswith("[sound:anki_azure_")
    assert recorded == []


def test_azure_voice_catalogue_filters_neural_voices_and_caches_without_key(tmp_path):
    tts = _load_tts_module()
    requested = {}

    class Response:
        def __enter__(self): return self
        def __exit__(self, *_args): return False
        def read(self, _size=-1):
            return (
                b'[{"ShortName":"ja-JP-NanamiNeural","DisplayName":"Nanami",'
                b'"Locale":"ja-JP","Gender":"Female","VoiceType":"Neural"},'
                b'{"ShortName":"ja-JP-OldStandard","DisplayName":"Old",'
                b'"Locale":"ja-JP","Gender":"Male","VoiceType":"Standard"},'
                b'{"ShortName":"en-US-JennyNeural","DisplayName":"Jenny",'
                b'"Locale":"en-US","Gender":"Female","VoiceType":"Neural"}]'
            )

    def urlopen(request, timeout):
        requested["request"] = request
        requested["timeout"] = timeout
        return Response()

    tts.get_user_data_path = lambda name: str(tmp_path / name)
    tts.get_tts_config = lambda: {"provider": "azure", "azure_region": "southeastasia"}
    tts.load_api_key = lambda _scope: "secret-key"
    tts.urllib.request.urlopen = urlopen

    assert tts.fetch_azure_voice_options("ja") == [{
        "id": "ja-JP-NanamiNeural", "name": "Nanami (ja-JP · Female)",
        "gender": "female", "locale": "ja-JP",
    }]
    assert tts.get_cached_azure_voice_options("ja")[0]["id"] == "ja-JP-NanamiNeural"
    cache = (tmp_path / "azure_tts_voices.json").read_text(encoding="utf-8")
    assert "secret-key" not in cache
    assert requested["request"].full_url.endswith("/cognitiveservices/voices/list")
    assert requested["request"].get_header("Ocp-apim-subscription-key") == "secret-key"
    assert requested["timeout"] == tts._AZURE_VOICE_LIST_TIMEOUT_SECONDS


def test_azure_usage_log_is_local_aggregate_only(tmp_path):
    tts = _load_tts_module()
    tts.get_user_data_path = lambda name: str(tmp_path / name)
    tts.time.strftime = lambda pattern: "2026-09-03" if pattern == "%Y-%m-%d" else "2026-09"

    tts._record_azure_tts_usage(12, success=True)
    tts._record_azure_tts_usage(5, success=False)
    tts._record_azure_tts_usage(cache_hit=True)

    summary = tts.get_azure_tts_usage_summary()
    assert summary["month_total"] == {
        "requests": 2, "characters": 17, "successes": 1,
        "successful_characters": 12, "failures": 1, "cache_hits": 1,
    }
    saved = (tmp_path / "azure_tts_usage.json").read_text(encoding="utf-8")
    assert "secret" not in saved
    assert "spoken text" not in saved
