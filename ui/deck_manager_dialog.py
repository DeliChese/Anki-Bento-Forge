"""
🗂️ Deck Manager Dialog — UI quản lý Parent/Sub Decks ngay trong add-on.

Tree view hiển thị cấu trúc deck từ Anki collection. Cho phép:
- Tạo Parent Deck mới
- Tạo Sub Deck bên trong deck đang chọn
- Đổi tên deck
- Xóa deck (kèm sub deck + thẻ)
- Làm mới tức thì (mọi thao tác đều gọi refresh_anki để UI ngoài Anki cập nhật)
"""

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTreeWidget, QTreeWidgetItem, QInputDialog,
    QMessageBox, QAbstractItemView, Qt,
)
from aqt.utils import tooltip

from utils.deck_manager import (
    get_deck_tree, create_deck, rename_deck, delete_decks,
    collapse_selected_deck_names, refresh_anki,
)
from utils.i18n import t


class DeckManagerDialog(QDialog):
    """Dialog quản lý deck parent/sub với cập nhật tức thì."""

    def __init__(self, parent=None, blueprint_source=None):
        super().__init__(parent)
        self._blueprint_source = (
            dict(blueprint_source) if isinstance(blueprint_source, dict) else {}
        )
        self.setWindowTitle(t("deck_manage_title"))
        self.setMinimumSize(520, 520)
        self.resize(620, 600)
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowMinMaxButtonsHint
            | Qt.WindowType.WindowMaximizeButtonHint
        )
        self._setup_ui()
        self._reload_tree()

    # ── UI ────────────────────────────────────────────────
    def _setup_ui(self):
        vl = QVBoxLayout(self)

        header = QHBoxLayout()
        header_copy = QLabel(
            f"<h3>{t('deck_manage_header')}</h3>"
            f"<p style='color:#555;font-size:11px;'>{t('deck_manage_desc')}</p>"
        )
        header_copy.setWordWrap(True)
        header.addWidget(header_copy, 1)
        self.btn_blueprint = QPushButton(t("deck_center_open_blueprint"))
        self.btn_blueprint.setProperty("class", "info")
        self.btn_blueprint.setToolTip(t("deck_center_open_blueprint_tip"))
        self.btn_blueprint.clicked.connect(self._open_blueprint)
        header.addWidget(self.btn_blueprint)
        vl.addLayout(header)

        # Tree view
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([t("deck_col_name"), t("deck_col_cards")])
        self.tree.setColumnWidth(0, 320)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)
        self.tree.itemChanged.connect(self._on_checked_items_changed)
        vl.addWidget(self.tree, 1)

        selection_row = QHBoxLayout()
        self.btn_select_all = QPushButton(t("deck_select_all"))
        self.btn_select_all.setToolTip(t("deck_select_all_tip"))
        self.btn_select_all.clicked.connect(lambda: self._set_all_checked(True))
        selection_row.addWidget(self.btn_select_all)
        self.btn_clear_selection = QPushButton(t("deck_clear_selection"))
        self.btn_clear_selection.setToolTip(t("deck_clear_selection_tip"))
        self.btn_clear_selection.clicked.connect(lambda: self._set_all_checked(False))
        selection_row.addWidget(self.btn_clear_selection)
        selection_row.addStretch()
        vl.addLayout(selection_row)

        # Buttons
        btn_row = QHBoxLayout()

        self.btn_add_parent = QPushButton(t("deck_add_parent"))
        self.btn_add_parent.setToolTip(t("deck_add_parent_prompt"))
        self.btn_add_parent.clicked.connect(self._add_parent)
        btn_row.addWidget(self.btn_add_parent)

        self.btn_add_sub = QPushButton(t("deck_add_sub"))
        self.btn_add_sub.setToolTip(t("deck_add_sub_tip"))
        self.btn_add_sub.clicked.connect(self._add_sub)
        btn_row.addWidget(self.btn_add_sub)

        self.btn_rename = QPushButton(t("deck_rename"))
        self.btn_rename.setToolTip(t("deck_rename_prompt"))
        self.btn_rename.clicked.connect(self._rename)
        btn_row.addWidget(self.btn_rename)

        self.btn_delete = QPushButton(t("deck_delete"))
        self.btn_delete.setToolTip(t("deck_delete_title"))
        self.btn_delete.clicked.connect(self._delete)
        btn_row.addWidget(self.btn_delete)

        self.btn_refresh = QPushButton(t("deck_refresh"))
        self.btn_refresh.setToolTip(t("deck_refresh"))
        self.btn_refresh.clicked.connect(self._reload_tree)
        btn_row.addWidget(self.btn_refresh)

        vl.addLayout(btn_row)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color:#27ae60;font-size:11px;")
        vl.addWidget(self.lbl_status)

    # ── Tree helpers ─────────────────────────────────────
    def _reload_tree(self):
        """Tải lại cây deck từ Anki collection."""
        self.tree.clear()
        tree = get_deck_tree()
        for node in tree:
            item = self._add_tree_node(None, node)
            # Item gốc phải được thêm vào tree bằng addTopLevelItem
            self.tree.addTopLevelItem(item)
        self.tree.expandAll()
        self.lbl_status.setText(t("deck_count_parents", count=len(tree)))

    def _add_tree_node(self, parent_item, node):
        item = QTreeWidgetItem(parent_item)
        # Hiển thị segment cuối cùng (sau "::") để tree gọn gàng,
        # nhưng lưu tên đầy đủ trong UserRole để thao tác chính xác.
        display_name = node["name"].split("::")[-1]
        item.setText(0, display_name)
        item.setText(1, str(node["card_count"]))
        item.setData(0, Qt.ItemDataRole.UserRole, node["name"])
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(0, Qt.CheckState.Unchecked)
        for child in node.get("children", []):
            self._add_tree_node(item, child)
        return item

    def _selected_deck_name(self):
        """Return the active deck for single-deck actions."""
        item = self.tree.currentItem()
        if item is None:
            return None
        return item.data(0, Qt.ItemDataRole.UserRole)

    def _iter_tree_items(self):
        def walk(item):
            yield item
            for index in range(item.childCount()):
                yield from walk(item.child(index))

        for index in range(self.tree.topLevelItemCount()):
            yield from walk(self.tree.topLevelItem(index))

    def _checked_deck_names(self):
        return [
            item.data(0, Qt.ItemDataRole.UserRole)
            for item in self._iter_tree_items()
            if item.checkState(0) == Qt.CheckState.Checked
        ]

    def _set_all_checked(self, checked):
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        self.tree.blockSignals(True)
        for item in self._iter_tree_items():
            item.setCheckState(0, state)
        self.tree.blockSignals(False)
        self._on_checked_items_changed()

    def _on_checked_items_changed(self, *_args):
        count = len(self._checked_deck_names())
        if count:
            self.lbl_status.setText(t("deck_selected_count", count=count))

    # ── Actions ──────────────────────────────────────────
    def _open_blueprint(self):
        """Open the review-first AI planner from the single Deck Center entry."""
        from ui.deck_blueprint_dialog import DeckBlueprintDialog

        dialog = DeckBlueprintDialog(
            self,
            initial_source=self._blueprint_source.get("text", ""),
            initial_language=self._blueprint_source.get("language", ""),
            source_files=self._blueprint_source.get("files", ()),
        )
        dialog.exec()
        self._reload_tree()

    def _add_parent(self):
        name, ok = QInputDialog.getText(
            self, t("deck_add_parent_title"), t("deck_add_parent_prompt")
        )
        if not ok or not name.strip():
            return
        deck_id = create_deck(name.strip())
        if deck_id is not None:
            refresh_anki()
            self._reload_tree()
            tooltip(t("deck_created", name=name.strip()))
        else:
            QMessageBox.warning(self, t("deck_add_parent_title"), t("deck_create_failed"))

    def _add_sub(self):
        parent_name = self._selected_deck_name()
        if not parent_name:
            tooltip(t("deck_select_first"))
            return
        name, ok = QInputDialog.getText(
            self, t("deck_add_sub_title"),
            t("deck_add_sub_prompt", parent=parent_name),
        )
        if not ok or not name.strip():
            return
        full_name = f"{parent_name}::{name.strip()}"
        deck_id = create_deck(full_name)
        if deck_id is not None:
            refresh_anki()
            self._reload_tree()
            tooltip(t("deck_created", name=full_name))
        else:
            QMessageBox.warning(self, t("deck_add_sub_title"), t("deck_create_failed"))

    def _rename(self):
        old_name = self._selected_deck_name()
        if not old_name:
            tooltip(t("deck_select_first"))
            return
        new_name, ok = QInputDialog.getText(
            self, t("deck_rename_title"), t("deck_rename_prompt"), text=old_name
        )
        if not ok or not new_name.strip():
            return
        if rename_deck(old_name, new_name.strip()):
            refresh_anki()
            self._reload_tree()
            tooltip(t("deck_renamed", old=old_name, new=new_name.strip()))
        else:
            QMessageBox.warning(self, t("deck_rename_title"), t("deck_rename_failed"))

    def _delete(self):
        checked_names = self._checked_deck_names()
        names = checked_names or [self._selected_deck_name()]
        roots = collapse_selected_deck_names(names)
        if not roots:
            tooltip(t("deck_select_first"))
            return
        if len(roots) == 1:
            message = t("deck_delete_confirm", name=roots[0])
        else:
            message = t("deck_delete_many_confirm", count=len(roots))
        ret = QMessageBox.question(
            self, t("deck_delete_title"),
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ret != QMessageBox.StandardButton.Yes:
            return
        deleted = delete_decks(roots)
        if deleted:
            refresh_anki()
            self._reload_tree()
            if len(deleted) == 1:
                tooltip(t("deck_deleted", name=deleted[0]))
            else:
                tooltip(t("deck_deleted_many", count=len(deleted)))
        else:
            QMessageBox.warning(self, t("deck_delete_title"), t("deck_delete_failed"))

    def _on_context_menu(self, pos):
        """Menu chuột phải nhanh."""
        from aqt.qt import QMenu
        menu = QMenu(self)
        menu.addAction(t("deck_add_sub"), self._add_sub)
        menu.addAction(t("deck_rename"), self._rename)
        menu.addAction(t("deck_delete"), self._delete)
        menu.exec(self.tree.viewport().mapToGlobal(pos))
