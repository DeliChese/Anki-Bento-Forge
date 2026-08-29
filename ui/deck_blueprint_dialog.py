"""Independent AI Deck Blueprint editor.

The dialog owns no Factory widgets.  It builds an editable draft first and
performs collection mutation only after an explicit confirmation.
"""

from aqt import mw
from aqt.qt import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    Qt,
)
from aqt.utils import tooltip

from utils.anki_ops import run_collection, run_query
from utils.deck_blueprint import (
    create_blueprint_decks,
    deck_names_from_blueprint,
    parse_structured_source,
    sanitize_deck_segment,
)
from utils.i18n import t
from utils.logger import get_logger
from workers.deck_blueprint_worker import DeckBlueprintWorker


logger = get_logger()
_WORDS_ROLE = int(Qt.ItemDataRole.UserRole) + 1
_DESCRIPTION_ROLE = int(Qt.ItemDataRole.UserRole) + 2
_COMPACT_SOURCE_HEIGHT = 145
_EXPANDED_SOURCE_HEIGHT = 310


class DeckBlueprintDialog(QDialog):
    """Reviewable source-outline to parent/subdeck proposal workflow."""

    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.setWindowTitle(t("blueprint_title"))
        self.resize(1040, 760)
        self.setMinimumSize(780, 600)
        self._worker = None
        self._sections = []
        self._vocab_list = []
        self._organization = {"suggestion": "", "decks": []}
        self._source_expanded = False
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(8)

        title = QLabel(t("blueprint_intro"))
        title.setWordWrap(True)
        root.addWidget(title)

        controls = QHBoxLayout()
        controls.addWidget(QLabel(t("blueprint_language")))
        self.cbo_language = QComboBox()
        for lang in ("japanese", "chinese", "korean", "english"):
            self.cbo_language.addItem(t(f"lang_{lang}"), lang)
        controls.addWidget(self.cbo_language)
        controls.addStretch()
        self.btn_toggle_source = QPushButton(t("blueprint_expand_source"))
        self.btn_toggle_source.clicked.connect(self._toggle_source_height)
        controls.addWidget(self.btn_toggle_source)
        root.addLayout(controls)

        self.txt_source = QTextEdit()
        self.txt_source.setAcceptRichText(True)
        self.txt_source.setPlaceholderText(t("blueprint_source_placeholder"))
        self.txt_source.setMaximumHeight(_COMPACT_SOURCE_HEIGHT)
        self.txt_source.textChanged.connect(self._refresh_outline_preview)
        root.addWidget(self.txt_source)

        self.lbl_outline = QLabel(t("blueprint_outline_empty"))
        self.lbl_outline.setWordWrap(True)
        self.lbl_outline.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        root.addWidget(self.lbl_outline)

        instruction_row = QHBoxLayout()
        instruction_row.addWidget(QLabel(t("blueprint_instruction")))
        self.txt_instruction = QTextEdit()
        self.txt_instruction.setMaximumHeight(72)
        self.txt_instruction.setPlaceholderText(t("blueprint_instruction_placeholder"))
        instruction_row.addWidget(self.txt_instruction, 1)
        root.addLayout(instruction_row)

        main = QHBoxLayout()
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            t("blueprint_col_deck"), t("blueprint_col_words"), t("blueprint_col_description")
        ])
        self.tree.setColumnWidth(0, 300)
        self.tree.setColumnWidth(1, 80)
        self.tree.setAlternatingRowColors(True)
        self.tree.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.tree.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.tree.itemSelectionChanged.connect(self._show_selected_words)
        main.addWidget(self.tree, 3)

        details = QWidget()
        details_layout = QVBoxLayout(details)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.addWidget(QLabel(t("blueprint_words_title")))
        self.txt_words = QTextEdit()
        self.txt_words.setReadOnly(True)
        self.txt_words.setPlaceholderText(t("blueprint_words_empty"))
        details_layout.addWidget(self.txt_words, 1)
        main.addWidget(details, 1)
        root.addLayout(main, 1)

        tree_actions = QHBoxLayout()
        self.btn_add_parent = QPushButton(t("blueprint_add_parent"))
        self.btn_add_parent.clicked.connect(self._add_parent)
        tree_actions.addWidget(self.btn_add_parent)
        self.btn_add_sub = QPushButton(t("blueprint_add_sub"))
        self.btn_add_sub.clicked.connect(self._add_sub)
        tree_actions.addWidget(self.btn_add_sub)
        self.btn_remove = QPushButton(t("blueprint_remove_branch"))
        self.btn_remove.clicked.connect(self._remove_selected)
        tree_actions.addWidget(self.btn_remove)
        tree_actions.addStretch()
        root.addLayout(tree_actions)

        self.lbl_status = QLabel(t("blueprint_status_ready"))
        self.lbl_status.setWordWrap(True)
        root.addWidget(self.lbl_status)
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        root.addWidget(self.progress)

        buttons = QHBoxLayout()
        btn_close = QPushButton(t("btn_close"))
        btn_close.clicked.connect(self.reject)
        buttons.addWidget(btn_close)
        buttons.addStretch()
        self.btn_stop = QPushButton(t("btn_stop"))
        self.btn_stop.setVisible(False)
        self.btn_stop.clicked.connect(self._stop_worker)
        buttons.addWidget(self.btn_stop)
        self.btn_generate = QPushButton(t("blueprint_generate"))
        self.btn_generate.clicked.connect(self._start_generation)
        buttons.addWidget(self.btn_generate)
        self.btn_save = QPushButton(t("blueprint_save"))
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self._prepare_save)
        buttons.addWidget(self.btn_save)
        root.addLayout(buttons)

    def _toggle_source_height(self):
        self._source_expanded = not self._source_expanded
        self.txt_source.setMaximumHeight(
            _EXPANDED_SOURCE_HEIGHT if self._source_expanded else _COMPACT_SOURCE_HEIGHT
        )
        self.btn_toggle_source.setText(t(
            "blueprint_collapse_source" if self._source_expanded else "blueprint_expand_source"
        ))

    def _source_sections(self):
        return parse_structured_source(
            self.txt_source.toPlainText(),
            self.txt_source.toHtml(),
            unsectioned_title=t("blueprint_unsectioned"),
        )

    def _refresh_outline_preview(self):
        sections = self._source_sections()
        if not sections:
            self.lbl_outline.setText(t("blueprint_outline_empty"))
            return
        labels = [
            f"H{section['level']} · {' > '.join(section['path'])} ({section['word_count']})"
            for section in sections[:8]
        ]
        if len(sections) > 8:
            labels.append(t("blueprint_outline_more", count=len(sections) - 8))
        self.lbl_outline.setText(t(
            "blueprint_outline_detected", count=len(sections), outline="  |  ".join(labels)
        ))

    def _set_busy(self, busy):
        for widget in (
            self.txt_source, self.txt_instruction, self.cbo_language,
            self.btn_generate, self.btn_add_parent, self.btn_add_sub,
            self.btn_remove,
        ):
            widget.setEnabled(not busy)
        self.btn_save.setEnabled(not busy and self.tree.topLevelItemCount() > 0)
        self.btn_stop.setVisible(busy)
        self.progress.setVisible(busy)
        self.progress.setRange(0, 0 if busy else 100)

    def _start_generation(self):
        if not self.txt_source.toPlainText().strip():
            tooltip(t("blueprint_error_empty_source"))
            return
        if self._worker and self._worker.isRunning():
            return
        self._set_busy(True)
        self.lbl_status.setText(t("blueprint_status_starting"))
        self._worker = DeckBlueprintWorker(
            source_text=self.txt_source.toPlainText(),
            source_html=self.txt_source.toHtml(),
            lang=self.cbo_language.currentData(),
            custom_instruction=self.txt_instruction.toPlainText().strip(),
        )
        self._worker.progress.connect(self.lbl_status.setText)
        self._worker.outline_ready.connect(self._on_outline_ready)
        self._worker.blueprint_ready.connect(self._on_blueprint_ready)
        self._worker.error.connect(self._on_worker_error)
        self._worker.start()

    def _on_outline_ready(self, sections):
        self._sections = list(sections or ())

    def _on_blueprint_ready(self, organization, vocab_list, sections):
        self._organization = dict(organization or {})
        self._vocab_list = list(vocab_list or ())
        self._sections = list(sections or ())
        self._populate_tree(self._organization)
        self._set_busy(False)
        self.btn_save.setEnabled(bool(deck_names_from_blueprint(self._organization)))
        self.progress.setValue(100)
        self.lbl_status.setText(t(
            "blueprint_status_generated",
            decks=len(deck_names_from_blueprint(self._organization)),
            words=len(self._vocab_list),
        ))

    def _on_worker_error(self, error):
        self._set_busy(False)
        self.lbl_status.setText(t("blueprint_status_error", error=str(error)))

    def _stop_worker(self):
        if self._worker and self._worker.isRunning():
            self._worker.stop()
        self._set_busy(False)
        self.lbl_status.setText(t("blueprint_status_stopped"))

    def _editable_item(self, parent=None):
        item = QTreeWidgetItem(parent) if parent is not None else QTreeWidgetItem(self.tree)
        item.setFlags(
            item.flags()
            | Qt.ItemFlag.ItemIsEditable
            | Qt.ItemFlag.ItemIsDragEnabled
            | Qt.ItemFlag.ItemIsDropEnabled
        )
        return item

    def _populate_tree(self, organization):
        self.tree.clear()
        for parent_info in organization.get("decks", ()):
            parent = self._editable_item()
            parent.setText(0, str(parent_info.get("parent") or t("blueprint_default_parent")))
            parent.setData(0, _WORDS_ROLE, [])
            for sub_info in parent_info.get("sub_decks", ()):
                child = self._editable_item(parent)
                words = list(sub_info.get("words") or ())
                child.setText(0, str(sub_info.get("name") or t("blueprint_general")))
                child.setText(1, str(len(words)))
                child.setText(2, str(sub_info.get("description") or ""))
                child.setData(0, _WORDS_ROLE, words)
                child.setData(0, _DESCRIPTION_ROLE, str(sub_info.get("description") or ""))
        self.tree.expandAll()
        self.tree.resizeColumnToContents(1)

    def _selected_parent(self):
        item = self.tree.currentItem()
        if item is None:
            return None
        return item if item.parent() is None else item.parent()

    def _add_parent(self):
        name, ok = QInputDialog.getText(
            self, t("blueprint_add_parent"), t("blueprint_name_prompt")
        )
        if ok and sanitize_deck_segment(name):
            item = self._editable_item()
            item.setText(0, sanitize_deck_segment(name))
            item.setData(0, _WORDS_ROLE, [])
            self.tree.setCurrentItem(item)
            self.btn_save.setEnabled(True)

    def _add_sub(self):
        parent = self._selected_parent()
        if parent is None:
            tooltip(t("blueprint_select_parent"))
            return
        name, ok = QInputDialog.getText(
            self, t("blueprint_add_sub"), t("blueprint_name_prompt")
        )
        if ok and sanitize_deck_segment(name):
            item = self._editable_item(parent)
            item.setText(0, sanitize_deck_segment(name))
            item.setText(1, "0")
            item.setData(0, _WORDS_ROLE, [])
            parent.setExpanded(True)
            self.tree.setCurrentItem(item)

    def _remove_selected(self):
        item = self.tree.currentItem()
        if item is None:
            return
        parent = item.parent()
        if parent is None:
            self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(item))
        else:
            parent.removeChild(item)
        self.txt_words.clear()
        self.btn_save.setEnabled(self.tree.topLevelItemCount() > 0)

    def _show_selected_words(self):
        item = self.tree.currentItem()
        words = list(item.data(0, _WORDS_ROLE) or ()) if item is not None else []
        self.txt_words.setPlainText("\n".join(words))

    @staticmethod
    def _descendants(item):
        for index in range(item.childCount()):
            child = item.child(index)
            yield child
            yield from DeckBlueprintDialog._descendants(child)

    def _tree_to_blueprint(self):
        decks = []
        for index in range(self.tree.topLevelItemCount()):
            root = self.tree.topLevelItem(index)
            parent_name = sanitize_deck_segment(root.text(0), t("blueprint_default_parent"))
            sub_decks = []
            root_words = list(root.data(0, _WORDS_ROLE) or ())
            if root_words:
                sub_decks.append({
                    "name": t("blueprint_general"), "description": "",
                    "word_count": len(root_words), "words": root_words,
                })
            for child in self._descendants(root):
                words = list(child.data(0, _WORDS_ROLE) or ())
                description = str(child.text(2) or child.data(0, _DESCRIPTION_ROLE) or "")
                sub_decks.append({
                    "name": sanitize_deck_segment(child.text(0), t("blueprint_general")),
                    "description": description,
                    "word_count": len(words),
                    "words": words,
                })
            decks.append({"parent": parent_name, "sub_decks": sub_decks})
        return {"suggestion": self._organization.get("suggestion", ""), "decks": decks}

    def _prepare_save(self):
        blueprint = self._tree_to_blueprint()
        names = deck_names_from_blueprint(blueprint)
        if not names:
            tooltip(t("blueprint_error_empty_tree"))
            return
        self.btn_save.setEnabled(False)
        run_query(
            self,
            lambda col: list(col.decks.all_names()),
            lambda existing: self._confirm_save(blueprint, names, existing),
            self._on_save_error,
        )

    def _confirm_save(self, blueprint, names, existing_names):
        existing = {str(name) for name in existing_names or ()}
        new_count = sum(1 for name in names if name not in existing)
        reused_count = len(names) - new_count
        answer = QMessageBox.question(
            self,
            t("blueprint_save_confirm_title"),
            t(
                "blueprint_save_confirm",
                new=new_count,
                reused=reused_count,
                total=len(names),
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            self.btn_save.setEnabled(True)
            return
        self.lbl_status.setText(t("blueprint_status_saving"))
        run_collection(
            self,
            lambda col: create_blueprint_decks(col, blueprint),
            self._on_saved,
            self._on_save_error,
        )

    def _on_saved(self, result):
        mw.reset()
        self.btn_save.setEnabled(True)
        self.lbl_status.setText(t(
            "blueprint_status_saved",
            created=len(result.get("created", ())),
            reused=len(result.get("reused", ())),
        ))
        tooltip(t("blueprint_saved_tooltip", count=len(result.get("ids", {}))))

    def _on_save_error(self, error):
        logger.warning("Deck Blueprint save failed: %s", error)
        self.btn_save.setEnabled(True)
        self.lbl_status.setText(t("blueprint_status_error", error=str(error)))

    def reject(self):
        self._stop_worker()
        super().reject()
