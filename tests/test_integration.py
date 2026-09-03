"""
Integration tests — Mock Anki để test các luồng chính.
"""

import json
import sys
import os
import types
from unittest.mock import MagicMock
import pytest

# === Add addon root to path ===
_addon_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addon_root not in sys.path:
    sys.path.insert(0, _addon_root)

# === Mock Anki modules TRƯỚC KHI import bất kỳ module addon nào ===

# Mock PyQt5 signal mechanism
class MockSignal:
    def __init__(self, *types):
        self._slots = []
    def connect(self, slot):
        self._slots.append(slot)
    def emit(self, *args, **kwargs):
        for slot in self._slots:
            slot(*args, **kwargs)
    def disconnect(self, slot=None):
        if slot:
            self._slots.remove(slot)
        else:
            self._slots.clear()

# Mock aqt.qt (PyQt5 classes)
aqt_qt_mock = types.ModuleType("aqt.qt")
aqt_qt_mock.QThread = type("QThread", (object,), {
    "__init__": lambda self, parent=None: None,
    "start": lambda self: None,
    "isRunning": lambda self: False,
    "wait": lambda self, ms=0: None,
    "terminate": lambda self: None,
})
aqt_qt_mock.pyqtSignal = MockSignal
aqt_qt_mock.QDialog = type("QDialog", (object,), {"exec": lambda self: 1, "accept": lambda self: None, "reject": lambda self: None})
aqt_qt_mock.QVBoxLayout = lambda *a: MagicMock()
aqt_qt_mock.QHBoxLayout = lambda *a: MagicMock()
aqt_qt_mock.QGridLayout = lambda *a, **kw: MagicMock()
aqt_qt_mock.QLabel = lambda *a, **kw: MagicMock()
aqt_qt_mock.QPushButton = lambda *a, **kw: MagicMock()
aqt_qt_mock.QLineEdit = lambda *a, **kw: MagicMock()
aqt_qt_mock.QCheckBox = lambda *a, **kw: MagicMock()
aqt_qt_mock.QComboBox = lambda *a, **kw: MagicMock()
aqt_qt_mock.QDoubleSpinBox = lambda *a, **kw: MagicMock()
aqt_qt_mock.QSpinBox = lambda *a, **kw: MagicMock()
aqt_qt_mock.QGroupBox = lambda *a, **kw: MagicMock()
aqt_qt_mock.QTextBrowser = lambda *a, **kw: MagicMock()
aqt_qt_mock.QTableWidget = lambda *a, **kw: MagicMock()
aqt_qt_mock.QTableWidgetItem = lambda *a, **kw: MagicMock()
aqt_qt_mock.QScrollArea = lambda *a, **kw: MagicMock()
aqt_qt_mock.QWidget = lambda *a, **kw: MagicMock()
aqt_qt_mock.QApplication = MagicMock()
aqt_qt_mock.QFormLayout = lambda *a, **kw: MagicMock()
aqt_qt_mock.QMessageBox = MagicMock()
aqt_qt_mock.Qt = MagicMock()
aqt_qt_mock.QTimer = lambda *a, **kw: MagicMock()
aqt_qt_mock.QPlainTextEdit = lambda *a, **kw: MagicMock()
aqt_qt_mock.QProgressBar = lambda *a, **kw: MagicMock()
aqt_qt_mock.QListWidget = lambda *a, **kw: MagicMock()
aqt_qt_mock.QTextEdit = lambda *a, **kw: MagicMock()
aqt_qt_mock.QSlider = lambda *a, **kw: MagicMock()
aqt_qt_mock.QColorDialog = lambda *a, **kw: MagicMock()
aqt_qt_mock.QKeySequence = lambda *a, **kw: MagicMock()
aqt_qt_mock.QTreeWidget = lambda *a, **kw: MagicMock()
aqt_qt_mock.QTreeWidgetItem = lambda *a, **kw: MagicMock()
aqt_qt_mock.QInputDialog = MagicMock()
aqt_qt_mock.QMenu = lambda *a, **kw: MagicMock()
sys.modules["aqt.qt"] = aqt_qt_mock

# Mock aqt
aqt_mock = types.ModuleType("aqt")
aqt_mock.mw = MagicMock()
aqt_mock.mw.col = MagicMock()
aqt_mock.mw.col.media = MagicMock()
aqt_mock.mw.col.media.dir = lambda: "/tmp"
aqt_mock.mw.col.models = MagicMock()
aqt_mock.mw.col.decks = MagicMock()
aqt_mock.mw.app = MagicMock()
aqt_mock.gui_hooks = MagicMock()
sys.modules["aqt"] = aqt_mock
sys.modules["aqt.mw"] = aqt_mock.mw

# Mock aqt.utils
aqt_utils_mock = types.ModuleType("aqt.utils")
aqt_utils_mock.showInfo = lambda *a: None
aqt_utils_mock.tooltip = lambda *a: None
aqt_utils_mock.qconnect = lambda f: f
aqt_utils_mock.askUser = lambda *a, **k: True
sys.modules["aqt.utils"] = aqt_utils_mock

# Mock anki
anki_mock = types.ModuleType("anki")
anki_notes_mock = types.ModuleType("anki.notes")
anki_notes_mock.Note = MagicMock()
sys.modules["anki"] = anki_mock
sys.modules["anki.notes"] = anki_notes_mock

# Mock audio package (for engine.py, tts.py)
audio_mock = types.ModuleType("audio")
audio_mock.__path__ = []
audio_mock.get_audio_multilang = lambda *a, **kw: ""
sys.modules["audio"] = audio_mock

audio_tts_mock = types.ModuleType("audio.tts")
audio_tts_mock._install_edge_tts = lambda: False
audio_tts_mock._install_gtts = lambda: False
audio_tts_mock.get_audio_edge_tts = lambda *a, **kw: ""
audio_tts_mock.get_audio_azure_tts = lambda *a, **kw: ""
audio_tts_mock.get_cached_azure_voice_options = lambda *a, **kw: []
audio_tts_mock.get_tts_config = lambda: {"provider": "edge"}
audio_tts_mock.get_audio_gtts = lambda *a, **kw: ""
sys.modules["audio.tts"] = audio_tts_mock
audio_mock.tts = audio_tts_mock

audio_engine_mock = types.ModuleType("audio.engine")
sys.modules["audio.engine"] = audio_engine_mock
audio_mock.engine = audio_engine_mock

# Load engine.py content into the mock module
_engine_path = os.path.join(_addon_root, "audio", "engine.py")
with open(_engine_path, "r", encoding="utf-8") as f:
    _engine_code = compile(f.read(), _engine_path, "exec")
    exec(_engine_code, audio_engine_mock.__dict__)


# === TESTS ===

class TestImportWorker:
    def test_init_stores_params(self):
        from workers.import_worker import ImportWorker
        tasks = [{"key": "0:Audio", "text": "test", "lang": "ja"}]
        worker = ImportWorker(tasks, speed=1.0)
        assert worker.audio_tasks == tasks
        assert worker.is_cancelled() is False

    def test_stop_sets_flag(self):
        from workers.import_worker import ImportWorker
        worker = ImportWorker([])
        worker.stop()
        assert worker.is_cancelled() is True

    def test_run_generates_tags_without_collection_access(self, monkeypatch):
        from workers import import_worker
        from workers.import_worker import ImportWorker

        class CaptureSignal:
            def __init__(self):
                self.value = None

            def emit(self, value):
                self.value = value

        monkeypatch.setattr(import_worker, "_generate_audio_safe", lambda *args: "[sound:test.mp3]")
        worker = ImportWorker([{"key": "0:Audio", "text": "test", "lang": "ja"}])
        finished = CaptureSignal()
        worker.finished = finished
        worker.run()

        assert finished.value["audio_tags"] == {"0:Audio": "[sound:test.mp3]"}


class TestAiExtractThread:
    def test_init_stores_params(self):
        from workers.ai_workers import AiExtractThread
        thread = AiExtractThread(text="hello", lang="japanese",
                                  custom_instruction="test", existing_words=["w1"])
        assert thread.text == "hello"
        assert thread.lang == "japanese"
        assert thread.existing_words == ["w1"]

    def test_default_params(self):
        from workers.ai_workers import AiExtractThread
        thread = AiExtractThread(text="test", lang="chinese")
        assert thread.custom_instruction == ""
        assert thread.existing_words == []

    def test_small_run_uses_one_direct_call_and_caps_preview_to_selected_target(self, monkeypatch):
        from workers import ai_workers

        calls = []
        monkeypatch.setattr(
            ai_workers,
            "extract_vocabulary_with_ai",
            lambda text, lang, instruction, **kwargs: (
                calls.append((text, lang, instruction, kwargs))
                or [{"front": str(index)} for index in range(25)]
            ),
        )
        worker = ai_workers.AiExtractThread(text="one short source", lang="english")
        finished = []
        worker.finished.connect(finished.append)

        worker.run()

        assert len(calls) == 1
        assert "tối đa 10 thẻ" in calls[0][2]
        assert len(finished[0]) == 10

    def test_large_source_is_rejected_before_any_ai_call(self, monkeypatch):
        from workers import ai_workers

        calls = []
        monkeypatch.setattr(
            ai_workers, "extract_vocabulary_with_ai",
            lambda *args, **kwargs: calls.append((args, kwargs)),
        )
        worker = ai_workers.AiExtractThread(
            text="x" * (ai_workers.SMALL_RUN_MAX_SOURCE_CHARS + 1),
            lang="english",
        )
        errors = []
        worker.error.connect(errors.append)

        worker.run()

        assert calls == []
        assert errors and str(ai_workers.SMALL_RUN_MAX_SOURCE_CHARS) in errors[0]


class TestPhaseOneCollectionOperations:
    def test_apply_import_reports_audio_and_created_note(self, monkeypatch):
        from utils import import_operations

        class FakeNote(dict):
            def __init__(self, *args):
                super().__init__()
                self.id = 0
                self.flushed = False

            def flush(self):
                self.flushed = True

        class FakeCollection:
            def __init__(self):
                self.models = MagicMock()
                self.models.by_name.return_value = {"name": "TestModel"}
                self.added = []

            def add_note(self, note, _deck_id):
                note.id = 987
                self.added.append(note)

        monkeypatch.setattr(import_operations, "Note", FakeNote)
        cfg = {
            "lang_code": "ja", "audio_fields": [("Audio", "Front")],
            "json_field_map": {"front": "Front"}, "all_fields": ["Front", "Audio"],
            "model_name": "TestModel", "front_field": "Front", "detect_key": "front",
        }
        report = import_operations.apply_import(
            FakeCollection(), [{"item": {"front": "test"}, "action": "add"}], cfg, 1,
            {"0:Audio": "[sound:test.mp3]"}, lambda: False,
        )
        assert report["added"] == 1
        assert report["added_note_ids"] == [987]
        assert report["audio_gen"] == 1

    def test_cancelled_import_does_not_mutate_collection(self, monkeypatch):
        from utils import import_operations

        collection = MagicMock()
        report = import_operations.apply_import(
            collection, [{"item": {"front": "test"}, "action": "add"}],
            {"audio_fields": [], "json_field_map": {}, "all_fields": [],
             "model_name": "Test", "front_field": "Front", "detect_key": "front"},
            1, {}, lambda: True,
        )
        assert report["cancelled"] is True
        collection.add_note.assert_not_called()

    def test_backoff_wait_is_cancelable(self):
        from utils.ai_extractor import _abortable_wait

        with pytest.raises(RuntimeError, match="Đã hủy"):
            _abortable_wait(5, lambda: True)


class TestDeckScanWorker:
    def test_init_stores_params(self):
        from workers.deck_scan_worker import DeckScanWorker
        worker = DeckScanWorker(model_name="Test", deck_id=456, front_field="Front")
        assert worker.model_name == "Test"
        assert worker.deck_id == 456


class TestSpeedToEdgeRate:
    def test_normal(self):
        from audio.engine import speed_to_edge_rate
        assert speed_to_edge_rate(1.0) == "+0%"

    def test_clamped(self):
        from audio.engine import speed_to_edge_rate
        assert speed_to_edge_rate(0.0) == "-50%"
        assert speed_to_edge_rate(5.0) == "+100%"


class TestSafeParseJsonIntegration:
    def test_ai_output_japanese(self):
        from utils.json_parser import safe_parse_json
        result = safe_parse_json('[{"front":"t1","meaning":"m1"},{"front":"t2","meaning":"m2"}]')
        assert len(result) == 2

    def test_ai_output_chinese(self):
        from utils.json_parser import safe_parse_json
        result = safe_parse_json('[{"simplified":"xuexi","meaning":"hoc tap"}]')
        assert len(result) == 1


class TestVoiceOptions:
    def test_audio_never_silently_falls_back_to_gtts(self, monkeypatch):
        import audio.engine as engine

        monkeypatch.setattr(engine, "_install_edge_tts", lambda: True)
        monkeypatch.setattr(engine, "get_audio_edge_tts", lambda *args, **kwargs: "")
        assert engine.get_audio_multilang("hello", "en") == ""

    def test_audio_routes_to_official_azure_when_selected(self, monkeypatch):
        import audio.engine as engine

        monkeypatch.setattr(engine, "get_tts_config", lambda: {"provider": "azure"})
        monkeypatch.setattr(engine, "get_audio_azure_tts", lambda *args, **kwargs: "[sound:azure.mp3]")
        assert engine.get_audio_multilang("hello", "en") == "[sound:azure.mp3]"

    def test_japanese_has_nanami(self):
        from audio.engine import get_voice_options
        voices = get_voice_options("ja")
        ids = [v["id"] for v in voices]
        assert "ja-JP-NanamiNeural" in ids

    def test_chinese_multi_region(self):
        from audio.engine import get_voice_options
        voices = get_voice_options("zh")
        ids = [v["id"] for v in voices]
        cn = [i for i in ids if "CN" in i]
        tw = [i for i in ids if "TW" in i]
        assert len(cn) >= 1
        assert len(tw) >= 1
