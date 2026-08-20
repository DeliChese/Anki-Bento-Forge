"""Tests for the Anki-independent AI worker lifecycle coordinator."""

import ast
from pathlib import Path

from utils.ai_workflow import AiWorkflowCoordinator


class _Signal:
    def __init__(self):
        self.callback = None

    def connect(self, callback):
        self.callback = callback

    def emit(self, value):
        self.callback(value)


class _Worker:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.progress = _Signal()
        self.finished = _Signal()
        self.error = _Signal()
        self.started = False
        self.stopped = False
        self.running = True

    def start(self):
        self.started = True

    def isRunning(self):
        return self.running

    def stop(self):
        self.stopped = True


def test_workflow_module_keeps_anki_and_qt_out_of_the_lifecycle_seam():
    import utils.ai_workflow as workflow

    source = Path(workflow.__file__).read_text(encoding="utf-8")
    imported_roots = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    assert imported_roots.isdisjoint({"aqt", "anki", "PyQt5", "PyQt6", "workers"})


def test_extract_worker_uses_current_token_and_forwards_signals():
    coordinator = AiWorkflowCoordinator()
    token = coordinator.begin()
    progress, finished, errors = [], [], []

    worker = coordinator.start_extract(
        _Worker,
        text="source",
        lang="japanese",
        custom_instruction="keep examples short",
        existing_words=["already known"],
        grammar=False,
        on_progress=progress.append,
        on_finished=finished.append,
        on_error=errors.append,
    )

    assert worker is coordinator.extract_worker
    assert worker.started
    assert worker.kwargs["cancel_event"] is token
    assert worker.kwargs["existing_words"] == ["already known"]
    assert worker.kwargs["learning_mode"] == "language"
    worker.progress.emit("working")
    worker.finished.emit([{"word": "猫"}])
    worker.error.emit("unused")
    assert progress == ["working"]
    assert finished == [[{"word": "猫"}]]
    assert errors == ["unused"]


def test_extract_worker_forwards_explicit_knowledge_mode():
    coordinator = AiWorkflowCoordinator()
    coordinator.begin()
    worker = coordinator.start_extract(
        _Worker,
        text="source", lang="english", custom_instruction="", existing_words=[],
        grammar=False, learning_mode="knowledge",
        on_progress=lambda _message: None,
        on_finished=lambda _result: None,
        on_error=lambda _message: None,
    )
    assert worker.kwargs["learning_mode"] == "knowledge"


def test_chat_worker_uses_current_token_and_can_be_cleared():
    coordinator = AiWorkflowCoordinator()
    token = coordinator.begin()
    progress, finished, errors = [], [], []

    worker = coordinator.start_chat(
        _Worker,
        message="help me study",
        lang="korean",
        conversation_history=[{"role": "user", "content": "earlier"}],
        anki_context={"cards": 2},
        card_kind="grammar",
        on_progress=progress.append,
        on_finished=finished.append,
        on_error=errors.append,
    )

    assert worker is coordinator.chat_worker
    assert worker.started
    assert worker.kwargs["cancel_event"] is token
    assert worker.kwargs["anki_context"] == {"cards": 2}
    assert worker.kwargs["card_kind"] == "grammar"
    coordinator.clear_chat_worker()
    assert coordinator.chat_worker is None


def test_cancel_signals_active_workers_without_blocking():
    coordinator = AiWorkflowCoordinator()
    token = coordinator.begin()
    extract = coordinator.start_extract(
        _Worker,
        text="source",
        lang="chinese",
        custom_instruction="",
        existing_words=[],
        grammar=False,
        on_progress=lambda _message: None,
        on_finished=lambda _result: None,
        on_error=lambda _message: None,
    )
    chat = coordinator.start_chat(
        _Worker,
        message="help",
        lang="chinese",
        conversation_history=None,
        anki_context=None,
        on_progress=lambda _message: None,
        on_finished=lambda _result: None,
        on_error=lambda _message: None,
    )

    coordinator.cancel()

    assert token.is_set()
    assert extract.stopped
    assert chat.stopped
    assert coordinator.is_cancelled()
    assert coordinator.start_extract(
        _Worker,
        text="new work",
        lang="chinese",
        custom_instruction="",
        existing_words=[],
        grammar=False,
        on_progress=lambda _message: None,
        on_finished=lambda _result: None,
        on_error=lambda _message: None,
    ) is None
