"""Lifecycle coordinator for the UI-owned AI workers.

This module intentionally has no dependency on Anki, Qt, workers, or AI
configuration.  The dialog supplies worker factories and UI callbacks, while
this coordinator owns the cancellation token and worker references for one AI
workflow.  Keeping that boundary explicit makes cancellation behaviour
testable without an Anki runtime.
"""

from __future__ import annotations

import threading
from typing import Any, Callable, Optional


WorkerFactory = Callable[..., Any]
ProgressCallback = Callable[[str], None]
ExtractFinishedCallback = Callable[[list], None]
ChatFinishedCallback = Callable[[dict], None]
ErrorCallback = Callable[[str], None]


class AiWorkflowCoordinator:
    """Own cancellable AI worker lifecycle while leaving UI work to callers."""

    def __init__(self) -> None:
        self._cancel_event: Optional[threading.Event] = None
        self._extract_worker: Optional[Any] = None
        self._chat_worker: Optional[Any] = None

    @property
    def cancel_event(self) -> Optional[threading.Event]:
        return self._cancel_event

    @property
    def extract_worker(self) -> Optional[Any]:
        return self._extract_worker

    @property
    def chat_worker(self) -> Optional[Any]:
        return self._chat_worker

    def begin(self) -> threading.Event:
        """Start a new workflow and return its cancellation token."""
        self._cancel_event = threading.Event()
        return self._cancel_event

    def is_cancelled(self) -> bool:
        """Whether no workflow is active or its current token was cancelled."""
        return self._cancel_event is None or self._cancel_event.is_set()

    def start_extract(
        self,
        worker_factory: WorkerFactory,
        *,
        text: str,
        lang: str,
        custom_instruction: str,
        existing_words: list,
        grammar: bool,
        learning_mode: str = "language",
        on_progress: ProgressCallback,
        on_finished: ExtractFinishedCallback,
        on_error: ErrorCallback,
    ) -> Optional[Any]:
        """Build, wire, and start an extraction worker for the current token."""
        if self.is_cancelled():
            return None

        worker = worker_factory(
            text=text,
            lang=lang,
            custom_instruction=custom_instruction,
            existing_words=existing_words,
            grammar=grammar,
            learning_mode=learning_mode,
            cancel_event=self._cancel_event,
        )
        worker.progress.connect(on_progress)
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        self._extract_worker = worker
        worker.start()
        return worker

    def start_chat(
        self,
        worker_factory: WorkerFactory,
        *,
        message: str,
        lang: str,
        conversation_history: Optional[list],
        anki_context: Optional[dict],
        on_progress: ProgressCallback,
        on_finished: ChatFinishedCallback,
        on_error: ErrorCallback,
        card_kind: str = "vocab",
        card_mode: Optional[str] = None,
        study_session: Optional[dict] = None,
        use_card_context: bool = False,
        session_id: str = "",
        runtime_config: Optional[dict] = None,
        workspace: str = "reviewer",
        workspace_request=None,
    ) -> Optional[Any]:
        """Build, wire, and start a chat worker for the current token."""
        if self.is_cancelled():
            return None

        worker = worker_factory(
            message=message,
            lang=lang,
            conversation_history=conversation_history,
            anki_context=anki_context,
            card_kind=card_kind,
            card_mode=card_mode,
            study_session=study_session,
            use_card_context=use_card_context,
            session_id=session_id,
            runtime_config=runtime_config,
            workspace=workspace,
            workspace_request=workspace_request,
            cancel_event=self._cancel_event,
        )
        worker.progress.connect(on_progress)
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        self._chat_worker = worker
        worker.start()
        return worker

    def clear_extract_worker(self) -> None:
        self._extract_worker = None

    def clear_chat_worker(self) -> None:
        self._chat_worker = None

    def cancel(self) -> None:
        """Signal active workers to stop without waiting for their threads."""
        if self._cancel_event is not None:
            self._cancel_event.set()
        for worker in (self._chat_worker, self._extract_worker):
            if worker is not None and worker.isRunning():
                worker.stop()
