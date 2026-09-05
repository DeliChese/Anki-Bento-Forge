"""
Integration tests — Mock Anki để test các luồng chính.
"""

import json
import importlib.util
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

    def test_card_creation_chat_uses_direct_generation_mode_without_source_parsing(self, monkeypatch):
        from workers import ai_workers

        calls = []
        monkeypatch.setattr(
            ai_workers,
            "extract_vocabulary_with_ai",
            lambda text, lang, instruction, **kwargs: (
                calls.append((text, lang, instruction, kwargs))
                or [{"front": "mua", "meaning": "buy"}]
            ),
        )
        worker = ai_workers.AiExtractThread(
            text="Tạo thẻ HSK 3 chủ đề đi chợ", lang="chinese",
            generation_request=True,
        )
        finished = []
        worker.finished.connect(finished.append)

        worker.run()

        assert len(calls) == 1
        assert calls[0][3]["generation_request"] is True
        assert "KHÔNG KÈM TÀI LIỆU NGUỒN" in calls[0][2]
        assert finished == [[{"front": "mua", "meaning": "buy"}]]

    def test_chinese_enumeration_is_recognized_as_all_fifteen_vocab_items(self):
        from workers.ai_workers import parse_explicit_vocabulary_items

        source = "我、你、您、他、她、它、我们、你们、他们、她们、大家、自己、别人、人家、谁"

        assert parse_explicit_vocabulary_items(source) == [
            "我", "你", "您", "他", "她", "它", "我们", "你们", "他们", "她们",
            "大家", "自己", "别人", "人家", "谁",
        ]

    def test_explicit_vocab_list_auto_expands_target_and_preserves_source_order(self, monkeypatch):
        from workers import ai_workers

        source_items = "我、你、您、他、她、它、我们、你们、他们、她们、大家、自己、别人、人家、谁".split("、")
        calls = []

        def fake_extract(text, lang, instruction, **kwargs):
            calls.append((text, instruction))
            return [{"simplified": item, "meaning": item} for item in reversed(source_items)]

        monkeypatch.setattr(ai_workers, "extract_vocabulary_with_ai", fake_extract)
        worker = ai_workers.AiExtractThread(
            text="、".join(source_items), lang="chinese", max_cards=5,
        )
        finished = []
        errors = []
        worker.finished.connect(finished.append)
        worker.error.connect(errors.append)

        worker.run()

        assert errors == []
        assert len(calls) == 1
        assert calls[0][0].splitlines() == source_items
        assert "ĐÚNG 15 thẻ" in calls[0][1]
        assert [card["simplified"] for card in finished[0]] == source_items

    def test_incomplete_explicit_vocab_result_is_rejected_instead_of_silently_previewed(
        self, monkeypatch,
    ):
        from workers import ai_workers

        monkeypatch.setattr(
            ai_workers,
            "extract_vocabulary_with_ai",
            lambda *args, **kwargs: [{"simplified": "我", "meaning": "tôi"}],
        )
        worker = ai_workers.AiExtractThread(text="我、你、他", lang="chinese")
        finished = []
        errors = []
        worker.finished.connect(finished.append)
        worker.error.connect(errors.append)

        worker.run()

        assert finished == []
        assert errors and "1/3" in errors[-1]
        assert "你" in errors[-1] and "他" in errors[-1]

    def test_topic_scope_filters_an_explicit_list_without_allowing_new_words(self, monkeypatch):
        from workers import ai_workers

        calls = []

        def fake_extract(text, lang, instruction, **kwargs):
            calls.append((text, instruction))
            return [
                {"simplified": "苹果", "meaning": "táo"},
                {"simplified": "香蕉", "meaning": "chuối"},
            ]

        monkeypatch.setattr(ai_workers, "extract_vocabulary_with_ai", fake_extract)
        worker = ai_workers.AiExtractThread(
            text="苹果、香蕉、学校", lang="chinese", max_cards=5,
            topic_scope="Ẩm thực",
        )
        finished, errors = [], []
        worker.finished.connect(finished.append)
        worker.error.connect(errors.append)

        worker.run()

        assert errors == []
        assert "CHỦ ĐỀ DO NGƯỜI HỌC KHÓA" in calls[0][1]
        assert [card["simplified"] for card in finished[0]] == ["苹果", "香蕉"]
        assert {card["topic"] for card in finished[0]} == {"Ẩm thực"}

    def test_topic_scope_rejects_words_outside_an_explicit_list(self, monkeypatch):
        from workers import ai_workers

        monkeypatch.setattr(
            ai_workers, "extract_vocabulary_with_ai",
            lambda *args, **kwargs: [{"simplified": "苹果", "meaning": "táo"},
                                      {"simplified": "医生", "meaning": "bác sĩ"}],
        )
        worker = ai_workers.AiExtractThread(
            text="苹果、香蕉", lang="chinese", topic_scope="Ẩm thực",
        )
        finished, errors = [], []
        worker.finished.connect(finished.append)
        worker.error.connect(errors.append)

        worker.run()

        assert finished == []
        assert errors

    def test_explicit_vocab_over_twenty_is_rejected_before_ai_call(self, monkeypatch):
        from workers import ai_workers

        calls = []
        monkeypatch.setattr(
            ai_workers,
            "extract_vocabulary_with_ai",
            lambda *args, **kwargs: calls.append((args, kwargs)),
        )
        worker = ai_workers.AiExtractThread(
            text="、".join(f"词{index}" for index in range(21)),
            lang="chinese",
        )
        errors = []
        worker.error.connect(errors.append)

        worker.run()

        assert calls == []
        assert errors and "21" in errors[-1] and "20" in errors[-1]

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


class TestAiPreviewLifecycle:
    @staticmethod
    def _load_preview_module():
        path = os.path.join(_addon_root, "ui", "ai_preview.py")
        spec = importlib.util.spec_from_file_location("ai_preview_lifecycle_test", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_quality_refresh_disconnects_before_table_teardown(self):
        bind_preview_quality_refresh = self._load_preview_module()._bind_preview_quality_refresh

        class FakeModel:
            def __init__(self):
                self.rowsRemoved = MockSignal()
                self.modelReset = MockSignal()

        class FakeTable:
            def __init__(self):
                self.itemChanged = MockSignal()
                self._model = FakeModel()

            def model(self):
                return self._model

        dialog = types.SimpleNamespace(finished=MockSignal())
        table = FakeTable()
        refreshes = []

        bind_preview_quality_refresh(
            dialog, table, lambda *_args: refreshes.append("refresh"),
        )
        assert refreshes == ["refresh"]

        table.itemChanged.emit()
        assert refreshes == ["refresh", "refresh"]

        dialog.finished.emit(0)
        table.itemChanged.emit()
        table.model().rowsRemoved.emit()
        table.model().modelReset.emit()

        assert refreshes == ["refresh", "refresh"]

    def test_deleted_qobject_runtime_error_deactivates_late_refresh(self):
        bind_preview_quality_refresh = self._load_preview_module()._bind_preview_quality_refresh

        class FakeModel:
            def __init__(self):
                self.rowsRemoved = MockSignal()
                self.modelReset = MockSignal()

        class FakeTable:
            def __init__(self):
                self.itemChanged = MockSignal()
                self._model = FakeModel()

            def model(self):
                return self._model

        dialog = types.SimpleNamespace(finished=MockSignal())
        table = FakeTable()
        calls = []

        def deleted_widget_callback(*_args):
            calls.append("attempt")
            raise RuntimeError("wrapped C/C++ object of type QTableWidget has been deleted")

        bind_preview_quality_refresh(dialog, table, deleted_widget_callback)
        table.model().modelReset.emit()

        assert calls == ["attempt"]

    def test_quality_refresh_ignores_synchronous_item_change_while_refreshing(self):
        bind_preview_quality_refresh = self._load_preview_module()._bind_preview_quality_refresh

        class FakeModel:
            def __init__(self):
                self.rowsRemoved = MockSignal()
                self.modelReset = MockSignal()

        class FakeTable:
            def __init__(self):
                self.itemChanged = MockSignal()
                self._model = FakeModel()

            def model(self):
                return self._model

        dialog = types.SimpleNamespace(finished=MockSignal())
        table = FakeTable()
        calls = []

        def refresh(*_args):
            calls.append("refresh")
            # Qt can emit itemChanged while the quality refresh assigns tooltips.
            table.itemChanged.emit()

        bind_preview_quality_refresh(dialog, table, refresh)
        assert calls == ["refresh"]

        table.model().modelReset.emit()
        assert calls == ["refresh", "refresh"]


class TestPhaseOneCollectionOperations:
    def test_prepare_audio_tasks_honors_example_3_and_4_switches(self):
        from utils.import_operations import prepare_audio_tasks

        cfg = {
            "lang_code": "en",
            "audio_fields": [
                ("Vocab Audio", "Front"),
                ("Example Audio", "Example"),
                ("Example2 Audio", "Example2"),
                ("Example3 Audio", "Example3"),
                ("Example4 Audio", "Example4"),
            ],
            "json_field_map": {
                "front": "Front", "example": "Example", "example_2": "Example2",
                "example_3": "Example3", "example_4": "Example4",
            },
        }
        batch = [{
            "item": {
                "front": "board", "example": "Board the train.",
                "example_2": "Board early.", "example_3": "Board at noon.",
                "example_4": "Board safely.",
            },
            "action": "add",
            "audio_enabled": (True, False, False, True, False),
        }]

        tasks = prepare_audio_tasks(MagicMock(), batch, cfg)

        assert [(task["key"], task["text"]) for task in tasks] == [
            ("0:Vocab Audio", "board"),
            ("0:Example3 Audio", "Board at noon."),
        ]

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
        progress = []
        report = import_operations.apply_import(
            FakeCollection(), [{"item": {"front": "test"}, "action": "add"}], cfg, 1,
            {"0:Audio": "[sound:test.mp3]"}, lambda: False,
            lambda current, total: progress.append((current, total)),
        )
        assert report["added"] == 1
        assert report["added_note_ids"] == [987]
        assert report["audio_gen"] == 1
        assert progress == [(1, 1)]

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
