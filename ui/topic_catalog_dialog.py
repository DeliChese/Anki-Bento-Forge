"""Small CRUD dialog for one language's learner-owned topic catalog."""

from __future__ import annotations

from aqt.qt import (
    QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QPushButton, QVBoxLayout,
)
from aqt.utils import tooltip

from utils.i18n import t
from utils.topic_catalog import TopicCatalogError, TopicCatalogStore, normalize_topic


class TopicCatalogDialog(QDialog):
    """Edit only the catalog for the language supplied by the Factory."""

    def __init__(self, *, store: TopicCatalogStore, language: str,
                 language_label: str, parent=None):
        super().__init__(parent)
        self._store = store
        self._language = language
        self.setWindowTitle(t("topic_catalog_title"))
        self.setMinimumSize(420, 330)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(t("topic_catalog_language", language=language_label)))
        layout.addWidget(QLabel(t("topic_catalog_list_label")))

        self.list_widget = QListWidget()
        self.list_widget.currentTextChanged.connect(self._select_topic)
        layout.addWidget(self.list_widget, 1)

        input_row = QHBoxLayout()
        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText(t("topic_catalog_placeholder"))
        input_row.addWidget(self.topic_input, 1)
        self.add_button = QPushButton(t("topic_catalog_add"))
        self.add_button.clicked.connect(self._add_topic)
        input_row.addWidget(self.add_button)
        layout.addLayout(input_row)

        actions = QHBoxLayout()
        self.update_button = QPushButton(t("topic_catalog_update"))
        self.update_button.clicked.connect(self._update_topic)
        actions.addWidget(self.update_button)
        self.delete_button = QPushButton(t("topic_catalog_delete"))
        self.delete_button.clicked.connect(self._delete_topic)
        actions.addWidget(self.delete_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
        self._reload()

    def _topics(self) -> list[str]:
        return [self.list_widget.item(index).text() for index in range(self.list_widget.count())]

    def _reload(self, selected: str = "") -> None:
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for topic in self._store.topics_for(self._language):
            self.list_widget.addItem(topic)
        self.list_widget.blockSignals(False)
        wanted = selected.casefold()
        for index in range(self.list_widget.count()):
            if self.list_widget.item(index).text().casefold() == wanted:
                self.list_widget.setCurrentRow(index)
                break
        self._set_action_state()

    def _select_topic(self, topic: str) -> None:
        self.topic_input.setText(topic)
        self._set_action_state()

    def _set_action_state(self) -> None:
        has_selected = self.list_widget.currentRow() >= 0
        self.update_button.setEnabled(has_selected)
        self.delete_button.setEnabled(has_selected)

    def _candidate(self) -> str:
        try:
            return normalize_topic(self.topic_input.text())
        except TopicCatalogError:
            tooltip(t("topic_catalog_invalid"))
            return ""

    def _save(self, topics: list[str], selected: str = "") -> None:
        try:
            self._store.replace_topics(self._language, topics)
        except TopicCatalogError as error:
            tooltip(t("topic_catalog_error", error=str(error)))
            return
        self._reload(selected)

    def _add_topic(self) -> None:
        topic = self._candidate()
        if not topic:
            return
        if any(existing.casefold() == topic.casefold() for existing in self._topics()):
            tooltip(t("topic_catalog_duplicate"))
            return
        self._save([*self._topics(), topic], topic)

    def _update_topic(self) -> None:
        index = self.list_widget.currentRow()
        topic = self._candidate()
        if index < 0 or not topic:
            return
        topics = self._topics()
        if any(
            existing.casefold() == topic.casefold() and position != index
            for position, existing in enumerate(topics)
        ):
            tooltip(t("topic_catalog_duplicate"))
            return
        topics[index] = topic
        self._save(topics, topic)

    def _delete_topic(self) -> None:
        index = self.list_widget.currentRow()
        if index < 0:
            return
        topics = self._topics()
        del topics[index]
        self.topic_input.clear()
        self._save(topics)


__all__ = ["TopicCatalogDialog"]
