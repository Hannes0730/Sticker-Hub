from __future__ import annotations

import shutil
from pathlib import Path

from PySide6.QtCore import QEvent, QMimeData, QSettings, QSignalBlocker, Qt, QTimer, QUrl
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QScroller

from sticker_hub.models import (
    Sticker,
    StickerCatalog,
    append_sticker_to_json,
    delete_category_from_json,
    delete_pack_from_json,
    get_catalog_db_status,
    load_catalog_from_json,
)
from sticker_hub.services import (
    StickerCache,
    StickerDownloadManager,
    check_for_update,
    resolve_sticker_urls,
    start_in_app_update,
    upgrade_sticker_urls_file,
)
from sticker_hub.ui.sticker_card import StickerCard
from sticker_hub.ui.sticker_grid import StickerGrid
from sticker_hub.utils import build_thumbnail


PREVIEW_QUALITY_SIZES: dict[str, tuple[int, int]] = {
    "performance": (168, 168),
    "high": (256, 256),
}

ANIMATION_BUDGET_INTERVAL_MS = 60

HIDDEN_NAV_CATEGORIES = {"Animated", "Favorite Packs", "Favorites Pack", "Imported"}
TOP_LEVEL_CATEGORIES = ["All", "Favorites", "Recent"]
ALL_PACKS_OPTION = "All Packs"


class MainWindow(QWidget):
    def __init__(self, catalog: StickerCatalog, cache: StickerCache, sticker_file: Path, app_version: str):
        super().__init__()
        self.catalog = catalog
        self.cache = cache
        self.sticker_file = sticker_file
        self.app_version = app_version.strip() or "dev"
        self.downloader = StickerDownloadManager(cache)
        self._settings = QSettings("StickerHub", "StickerHub")
        self._skipped_update_version = str(self._settings.value("updates/skipped_version", "") or "").strip()

        self.favorites: set[str] = set()
        self.recent: list[str] = []
        self.current_category = "All"
        self.current_pack = ALL_PACKS_OPTION
        self.selected_id: str | None = None

        self.cards_by_id: dict[str, StickerCard] = {}
        self.preview_quality = "high"
        self._animation_budget_timer = QTimer(self)
        self._animation_budget_timer.setSingleShot(True)
        self._animation_budget_timer.setInterval(ANIMATION_BUDGET_INTERVAL_MS)
        self._animation_budget_timer.timeout.connect(self._update_card_animation_budget)

        self.setWindowTitle(f"Sticker Hub v{self.app_version}")
        self.resize(1220, 760)

        self.downloader.set_thumbnail_size(PREVIEW_QUALITY_SIZES[self.preview_quality])

        root = QHBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        self.sidebar = QListWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(220)
        self.sidebar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        top_bar.setSpacing(8)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search stickers...")

        self.pack_filter = QComboBox()
        self.pack_filter.setObjectName("QualityModeCombo")
        self.pack_filter.setToolTip("Filter packs under the selected category.")
        self.pack_filter.setMinimumWidth(180)
        self.pack_filter.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.pack_filter.hide()

        self.delete_pack_button = QPushButton("Delete Pack")
        self.delete_pack_button.setObjectName("ImportButton")
        self.delete_pack_button.setToolTip("Delete the currently selected pack.")
        self.delete_pack_button.hide()

        self.import_button = QPushButton("Import URL")
        self.import_button.setObjectName("ImportButton")

        self.upgrade_urls_button = QPushButton("Upgrade URLs")
        self.upgrade_urls_button.setObjectName("ImportButton")
        self.upgrade_urls_button.setToolTip("Promote thumbnail-like links to preferred full-size URLs.")

        self.update_button = QPushButton("Check Updates")
        self.update_button.setObjectName("ImportButton")
        self.update_button.setToolTip("Check if a newer Sticker Hub version is available.")

        self.quality_mode = QComboBox()
        self.quality_mode.setObjectName("QualityModeCombo")
        self.quality_mode.addItem("Preview: Performance", "performance")
        self.quality_mode.addItem("Preview: High Quality", "high")
        self.quality_mode.setCurrentIndex(1)
        self.quality_mode.setToolTip("Controls preview thumbnail quality only. Sending uses original files.")

        self.copy_format = QComboBox()
        self.copy_format.setObjectName("CopyFormatCombo")
        self.copy_format.addItem("Copy: Original", "original")
        self.copy_format.addItem("Copy: GIF", ".gif")
        self.copy_format.addItem("Copy: WebP", ".webp")
        self.copy_format.setCurrentIndex(1)
        self.copy_format.setToolTip("Choose the format used when copying stickers.")

        self.version_badge = QLabel(f"v{self.app_version}")
        self.version_badge.setObjectName("StatusLabel")

        self.status = QLabel("Loading stickers...")
        self.status.setObjectName("StatusLabel")

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.grid_widget = StickerGrid()
        self.scroll.setWidget(self.grid_widget)
        self.scroll.viewport().installEventFilter(self)
        QScroller.grabGesture(self.scroll.viewport(), QScroller.LeftMouseButtonGesture)

        top_bar.addWidget(self.search, stretch=1)
        top_bar.addWidget(self.pack_filter)
        top_bar.addWidget(self.delete_pack_button)
        top_bar.addWidget(self.quality_mode)
        top_bar.addWidget(self.copy_format)
        top_bar.addWidget(self.import_button)
        top_bar.addWidget(self.upgrade_urls_button)
        top_bar.addWidget(self.update_button)
        top_bar.addWidget(self.version_badge)

        root.addWidget(self.sidebar)
        right_layout.addLayout(top_bar)
        right_layout.addWidget(self.scroll, stretch=1)
        right_layout.addWidget(self.status)
        root.addWidget(right, stretch=1)

        self._build_sidebar()
        self._create_cards()
        self._set_cards_window_active(self.isActiveWindow())

        self.sidebar.currentItemChanged.connect(self._on_category_changed)
        self.sidebar.customContextMenuRequested.connect(self._on_sidebar_context_menu)
        self.search.textChanged.connect(lambda _: self._apply_filters())
        self.pack_filter.currentIndexChanged.connect(self._on_pack_changed)
        self.pack_filter.customContextMenuRequested.connect(self._on_pack_context_menu)
        self.delete_pack_button.clicked.connect(self._delete_selected_pack)
        self.quality_mode.currentIndexChanged.connect(self._on_preview_quality_changed)
        self.import_button.clicked.connect(self._open_import_dialog)
        self.upgrade_urls_button.clicked.connect(self._upgrade_existing_urls)
        self.update_button.clicked.connect(lambda: self._check_for_updates(manual=True))
        self.downloader.sticker_ready.connect(self._on_sticker_ready)
        self.downloader.sticker_failed.connect(self._on_sticker_failed)
        self.scroll.verticalScrollBar().valueChanged.connect(lambda _: self._schedule_animation_budget_update())
        self.scroll.horizontalScrollBar().valueChanged.connect(lambda _: self._schedule_animation_budget_update())

        self._apply_filters()
        self._queue_visible_downloads()
        QTimer.singleShot(20, self._show_catalog_db_status)
        QTimer.singleShot(1400, lambda: self._check_for_updates(manual=False))

    def _show_catalog_db_status(self) -> None:
        status = get_catalog_db_status(self.sticker_file)
        if not bool(status.get("exists")):
            return

        table_count = int(status.get("table_count", 0) or 0)
        self.status.setText(f"Catalog DB: ready ({table_count} tables)")

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.grid_widget.update_layout_for_width(self.scroll.viewport().width())
        self._schedule_animation_budget_update()

    def eventFilter(self, watched: object, event: QEvent) -> bool:  # noqa: N802
        if watched is self.scroll.viewport() and event.type() == QEvent.Type.Resize:
            self.grid_widget.update_layout_for_width(self.scroll.viewport().width())
            self._schedule_animation_budget_update()
        return super().eventFilter(watched, event)

    def _schedule_animation_budget_update(self) -> None:
        if self._animation_budget_timer.isActive():
            self._animation_budget_timer.stop()
        self._animation_budget_timer.start()

    def _build_sidebar(self) -> None:
        with QSignalBlocker(self.sidebar):
            self.sidebar.clear()

            self._add_sidebar_group_header("Quick Access")
            for category in TOP_LEVEL_CATEGORIES:
                self._add_sidebar_entry(category)

            self._add_sidebar_group_header("Categories")
            for category in self._custom_pack_categories():
                self._add_sidebar_entry(category)

            if self.sidebar.count() > 0:
                selected_item = self._find_sidebar_item(self.current_category)
                if selected_item is None:
                    selected_item = self._find_sidebar_item("All")
                    self.current_category = "All"
                if selected_item is not None:
                    self.sidebar.setCurrentItem(selected_item)

        self._sync_pack_filter_for_category()

    def _add_sidebar_group_header(self, label: str) -> None:
        item = QListWidgetItem(label)
        item.setData(Qt.ItemDataRole.UserRole, "group_header")
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable & ~Qt.ItemFlag.ItemIsEnabled)

        header_font = QFont(item.font())
        header_font.setBold(True)
        item.setFont(header_font)
        self.sidebar.addItem(item)

    def _add_sidebar_entry(self, category: str) -> None:
        item = QListWidgetItem(category)
        item.setData(Qt.ItemDataRole.UserRole, "category")
        self.sidebar.addItem(item)

    def _find_sidebar_item(self, label: str) -> QListWidgetItem | None:
        for index in range(self.sidebar.count()):
            item = self.sidebar.item(index)
            if item.data(Qt.ItemDataRole.UserRole) != "category":
                continue
            if item.text() == label:
                return item
        return None

    def _custom_pack_categories(self) -> list[str]:
        parents = {
            sticker.parent_category.strip() or sticker.category.strip()
            for sticker in self.catalog.stickers
            if (sticker.parent_category.strip() or sticker.category.strip())
            not in set(TOP_LEVEL_CATEGORIES).union(HIDDEN_NAV_CATEGORIES)
        }
        return sorted(parents, key=str.casefold)

    def _packs_for_category(self, parent_category: str) -> list[str]:
        packs = {
            sticker.pack_name.strip()
            for sticker in self.catalog.stickers
            if sticker.parent_category == parent_category and sticker.pack_name.strip()
        }
        return sorted(packs, key=str.casefold)

    def _sync_pack_filter_for_category(self) -> None:
        packs = [] if self.current_category in TOP_LEVEL_CATEGORIES else self._packs_for_category(self.current_category)
        with QSignalBlocker(self.pack_filter):
            self.pack_filter.clear()
            if not packs:
                self.current_pack = ALL_PACKS_OPTION
                self.pack_filter.hide()
                self.delete_pack_button.hide()
                return

            self.pack_filter.addItem(ALL_PACKS_OPTION, ALL_PACKS_OPTION)
            for pack in packs:
                self.pack_filter.addItem(pack, pack)

            current_index = self.pack_filter.findData(self.current_pack)
            if current_index < 0:
                self.current_pack = ALL_PACKS_OPTION
                current_index = 0
            self.pack_filter.setCurrentIndex(current_index)
            self.pack_filter.show()
            self.delete_pack_button.show()

        self._sync_pack_delete_button_state()

    def _on_pack_changed(self, _index: int) -> None:
        self.current_pack = str(self.pack_filter.currentData() or ALL_PACKS_OPTION)
        self._sync_pack_delete_button_state()
        self._apply_filters()

    def _sync_pack_delete_button_state(self) -> None:
        can_delete = bool(self.current_pack and self.current_pack != ALL_PACKS_OPTION)
        self.delete_pack_button.setEnabled(can_delete)

    def _on_sidebar_context_menu(self, pos) -> None:
        item = self.sidebar.itemAt(pos)
        if not item or item.data(Qt.ItemDataRole.UserRole) != "category":
            return

        category = item.text()
        if category in TOP_LEVEL_CATEGORIES:
            return

        menu = QMenu(self)
        delete_action = menu.addAction(f"Delete category '{category}'")
        selected_action = menu.exec(self.sidebar.mapToGlobal(pos))
        if selected_action != delete_action:
            return

        confirm = QMessageBox.question(
            self,
            "Delete Category",
            f"Delete category '{category}' and all of its packs/stickers?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        if delete_category_from_json(self.sticker_file, category):
            self.status.setText(f"Deleted category '{category}'.")
            self._reload_catalog()
        else:
            self.status.setText(f"Unable to delete category '{category}'.")

    def _on_pack_context_menu(self, pos) -> None:
        if self.current_category in TOP_LEVEL_CATEGORIES:
            return

        selected_pack = str(self.pack_filter.currentData() or "").strip()
        if not selected_pack or selected_pack == ALL_PACKS_OPTION:
            return

        menu = QMenu(self)
        delete_action = menu.addAction(f"Delete pack '{selected_pack}'")
        selected_action = menu.exec(self.pack_filter.mapToGlobal(pos))
        if selected_action != delete_action:
            return

        self._delete_selected_pack()

    def _delete_selected_pack(self) -> None:
        selected_pack = str(self.pack_filter.currentData() or "").strip()
        if self.current_category in TOP_LEVEL_CATEGORIES:
            return
        if not selected_pack or selected_pack == ALL_PACKS_OPTION:
            return

        confirm = QMessageBox.question(
            self,
            "Delete Pack",
            f"Delete pack '{selected_pack}' under '{self.current_category}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        if delete_pack_from_json(self.sticker_file, self.current_category, selected_pack):
            self.current_pack = ALL_PACKS_OPTION
            self.status.setText(f"Deleted pack '{selected_pack}'.")
            self._reload_catalog()
        else:
            self.status.setText(f"Unable to delete pack '{selected_pack}'.")

    def _create_cards(self) -> None:
        self.cards_by_id = {}
        for sticker in self.catalog.stickers:
            card = StickerCard(sticker)
            card.setParent(self.grid_widget)
            card.left_clicked.connect(self._on_card_left_click)
            card.copy_requested.connect(self._on_copy_requested)
            card.save_requested.connect(self._on_save_requested)
            card.open_location_requested.connect(self._on_open_location_requested)
            card.favorite_toggled.connect(self._toggle_favorite)
            self.cards_by_id[sticker.sticker_id] = card

    def _set_cards_window_active(self, active: bool) -> None:
        for card in self.cards_by_id.values():
            card.set_window_active(active)
        self._schedule_animation_budget_update()

    def changeEvent(self, event) -> None:  # noqa: N802
        if event.type() == QEvent.Type.ActivationChange:
            self._set_cards_window_active(self.isActiveWindow())
        super().changeEvent(event)

    def _update_card_animation_budget(self) -> None:
        visible_cards = self.grid_widget.visible_cards()
        if not visible_cards:
            return

        if not self.isActiveWindow() or self.isMinimized():
            for card in visible_cards:
                card.set_animation_allowed(False)
            return
        for card in visible_cards:
            should_animate = card.isVisible() and bool(card.local_path) and card.is_animated
            card.set_animation_allowed(should_animate)

    def _on_category_changed(self, current: QListWidgetItem, _previous: QListWidgetItem) -> None:
        if not current:
            return
        if current.data(Qt.ItemDataRole.UserRole) != "category":
            fallback = self._find_sidebar_item(self.current_category) or self._find_sidebar_item("All")
            if fallback is not None and fallback is not current:
                self.sidebar.setCurrentItem(fallback)
            return
        self.current_category = current.text()
        self.current_pack = ALL_PACKS_OPTION
        self._sync_pack_filter_for_category()
        self._apply_filters()

    def _apply_filters(self) -> None:
        query = self.search.text()

        if self.current_category == "All":
            stickers = list(self.catalog.stickers)
        elif self.current_category == "Favorites":
            stickers = [
                self.catalog.by_id(sticker_id)
                for sticker_id in self.favorites
                if self.catalog.by_id(sticker_id)
            ]
        elif self.current_category == "Recent":
            stickers = [
                self.catalog.by_id(sticker_id)
                for sticker_id in self.recent
                if self.catalog.by_id(sticker_id)
            ]
        else:
            stickers = [
                sticker
                for sticker in self.catalog.stickers
                if (sticker.parent_category.strip() or sticker.category.strip()) == self.current_category
            ]
            if self.current_pack != ALL_PACKS_OPTION:
                stickers = [sticker for sticker in stickers if sticker.pack_name == self.current_pack]

        visible_cards = []
        for sticker in stickers:
            if not sticker:
                continue
            if query:
                probe = f"{sticker.label} {sticker.category}".lower()
                if query.strip().lower() not in probe:
                    continue
            card = self.cards_by_id.get(sticker.sticker_id)
            if card:
                visible_cards.append(card)

        self.grid_widget.set_cards(visible_cards)
        self.grid_widget.update_layout_for_width(self.scroll.viewport().width())
        self.status.setText(f"{len(visible_cards)} sticker(s)")
        self._schedule_animation_budget_update()
        self._queue_visible_downloads()

    def _queue_visible_downloads(self) -> None:
        for card in self.cards_by_id.values():
            if card.local_path:
                continue
            self.downloader.queue_download(card.sticker)

    def _on_sticker_ready(self, payload: object) -> None:
        card = self.cards_by_id.get(payload.sticker_id)
        if not card:
            return
        pixmap = QPixmap.fromImage(payload.thumbnail)
        card.set_thumbnail(pixmap, Path(payload.local_path), payload.animated)
        self._schedule_animation_budget_update()

    def _on_sticker_failed(self, sticker_id: str, message: str) -> None:
        card = self.cards_by_id.get(sticker_id)
        if card:
            card.set_error(message)

    def _on_preview_quality_changed(self, _index: int) -> None:
        selected = str(self.quality_mode.currentData() or "high")
        if selected not in PREVIEW_QUALITY_SIZES:
            selected = "high"
        if selected == self.preview_quality:
            return

        self.preview_quality = selected
        self.downloader.set_thumbnail_size(PREVIEW_QUALITY_SIZES[selected])
        self._refresh_loaded_previews()
        label = "High Quality" if selected == "high" else "Performance"
        self.status.setText(f"Preview mode: {label}")

    def _refresh_loaded_previews(self) -> None:
        size = PREVIEW_QUALITY_SIZES[self.preview_quality]
        for card in self.cards_by_id.values():
            if not card.local_path or not card.local_path.exists():
                continue

            try:
                qimage = build_thumbnail(card.local_path.read_bytes(), size=size)
                card.set_thumbnail(QPixmap.fromImage(qimage), card.local_path, card.is_animated)
            except Exception:
                continue

    def _on_card_left_click(self, sticker_id: str) -> None:
        self._set_selected(sticker_id)
        self._copy_sticker_to_send(sticker_id, set_clipboard=True)
        self._mark_recent(sticker_id)

    def _on_copy_requested(self, sticker_id: str) -> None:
        self._copy_sticker_to_send(sticker_id, set_clipboard=True)
        self._mark_recent(sticker_id)

    def _on_save_requested(self, sticker_id: str) -> None:
        card = self.cards_by_id.get(sticker_id)
        if not card or not card.local_path:
            return

        target, _ = QFileDialog.getSaveFileName(
            self,
            "Save Sticker",
            card.local_path.name,
            "Images (*.png *.jpg *.jpeg *.gif *.webp);;All Files (*)",
        )
        if not target:
            return

        shutil.copy2(card.local_path, target)

    def _on_open_location_requested(self, sticker_id: str) -> None:
        card = self.cards_by_id.get(sticker_id)
        if not card or not card.local_path:
            return
        self.cache.open_location(card.local_path)

    def _toggle_favorite(self, sticker_id: str) -> None:
        card = self.cards_by_id.get(sticker_id)
        if not card:
            # Guard against stale IDs from pre-reload card instances.
            self.favorites.discard(sticker_id)
            return

        if sticker_id in self.favorites:
            self.favorites.remove(sticker_id)
            card.is_favorite = False
        else:
            self.favorites.add(sticker_id)
            card.is_favorite = True

        if self.current_category == "Favorites":
            self._apply_filters()

    def _set_selected(self, sticker_id: str) -> None:
        if self.selected_id and self.selected_id in self.cards_by_id:
            self.cards_by_id[self.selected_id].set_selected(False)

        self.selected_id = sticker_id
        card = self.cards_by_id.get(sticker_id)
        if card:
            card.set_selected(True)

    def _copy_sticker_to_send(self, sticker_id: str, set_clipboard: bool) -> None:
        card = self.cards_by_id.get(sticker_id)
        if not card or not card.local_path:
            return

        selected_mode = str(self.copy_format.currentData())
        preferred_ext = selected_mode
        if preferred_ext not in {"original", ".gif", ".webp"}:
            preferred_ext = "original"

        send_file, applied_preference = self.cache.create_send_copy(card.local_path, preferred_ext=preferred_ext)
        if not set_clipboard:
            return

        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(str(send_file))])
        QApplication.clipboard().setMimeData(mime)


        if preferred_ext == "original":
            if applied_preference:
                self.status.setText(f"Copied: {send_file.name}")
            else:
                self.status.setText(f"Copied using original format ({send_file.suffix.upper()}).")
            self.status.setToolTip("")
            return

        if applied_preference:
            self.status.setText(f"Copied as {send_file.suffix.upper()}: {send_file.name}")
            if send_file.suffix.lower() == ".gif":
                self.status.setToolTip("GIF supports only 256 colors. Use WebP or Original for best quality.")
            else:
                self.status.setToolTip("")
        else:
            self.status.setText(f"Copied using original format ({send_file.suffix.upper()}).")
            self.status.setToolTip("")

    def _mark_recent(self, sticker_id: str) -> None:
        if sticker_id in self.recent:
            self.recent.remove(sticker_id)
        self.recent.insert(0, sticker_id)
        self.recent = self.recent[:40]

    def _open_import_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Import Stickers")

        form = QFormLayout(dialog)
        source_input = QLineEdit()
        source_input.setPlaceholderText("https://... (pack page or direct image URL)")

        category_input = QLineEdit()
        category_input.setPlaceholderText("Cats")

        pack_input = QLineEdit()
        pack_input.setPlaceholderText("Nailong Pack")

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        form.addRow("Source URL", source_input)
        form.addRow("Category", category_input)
        form.addRow("Pack Name", pack_input)
        form.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        source_url = source_input.text().strip()
        category = category_input.text().strip() or "Imported"
        pack_name = pack_input.text().strip() or "Imported Pack"
        if not source_url:
            QMessageBox.warning(self, "Import failed", "Please enter a source URL.")
            return

        self._import_from_url(source_url, category, pack_name)

    def _import_from_url(self, source_url: str, category: str, pack_name: str) -> None:
        self.import_button.setEnabled(False)
        self.upgrade_urls_button.setEnabled(False)
        self.status.setText("Importing stickers...")
        try:
            resolved_urls = resolve_sticker_urls(source_url)
            if not resolved_urls:
                QMessageBox.warning(
                    self,
                    "Import failed",
                    "No image URLs were found. Try a direct PNG/JPG/GIF/WebP link.",
                )
                return

            imported_count = 0
            skipped_count = 0
            for image_url in resolved_urls:
                was_added = append_sticker_to_json(
                    self.sticker_file,
                    category,
                    image_url,
                    "",
                    pack_name=pack_name,
                    pack_url=source_url,
                )
                if was_added:
                    imported_count += 1
                else:
                    skipped_count += 1

            self._reload_catalog()
            if skipped_count:
                self.status.setText(
                    f"Imported {imported_count} sticker(s), skipped {skipped_count} duplicate(s) in '{category} / {pack_name}'."
                )
            else:
                self.status.setText(f"Imported {imported_count} sticker(s) into '{category} / {pack_name}'.")
        except Exception as exc:
            QMessageBox.critical(self, "Import failed", str(exc))
            self.status.setText("Import failed.")
        finally:
            self.import_button.setEnabled(True)
            self.upgrade_urls_button.setEnabled(True)

    def _upgrade_existing_urls(self) -> None:
        self.import_button.setEnabled(False)
        self.upgrade_urls_button.setEnabled(False)
        self.status.setText("Upgrading existing sticker URLs...")
        try:
            stats = upgrade_sticker_urls_file(self.sticker_file)
            changed = stats["updated"] + stats["duplicates_removed"] + stats["invalid_skipped"]
            if changed:
                self._reload_catalog()
            self.status.setText(
                "URL upgrade complete: "
                f"updated {stats['updated']}, "
                f"duplicates removed {stats['duplicates_removed']}, "
                f"invalid skipped {stats['invalid_skipped']}."
            )
        except Exception as exc:
            QMessageBox.critical(self, "Upgrade failed", str(exc))
            self.status.setText("Upgrade failed.")
        finally:
            self.import_button.setEnabled(True)
            self.upgrade_urls_button.setEnabled(True)

    def _check_for_updates(self, manual: bool) -> None:
        self.update_button.setEnabled(False)
        if manual:
            self.status.setText("Checking for updates...")

        try:
            result = check_for_update(self.app_version)
        finally:
            self.update_button.setEnabled(True)

        if result.error:
            if manual:
                QMessageBox.warning(self, "Update Check", result.error)
            self.status.setText("Update check failed.")
            return

        if not result.update_available:
            if manual:
                QMessageBox.information(self, "Update Check", "You are already on the latest version.")
            self.status.setText("You are up to date.")
            return

        if not manual and result.latest_version == self._skipped_update_version:
            return

        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Information)
        dialog.setWindowTitle("Update available")
        dialog.setText(f"Version v{result.latest_version} is available.")
        dialog.setInformativeText("Install the new version now? The app will close and restart.")

        download_button = dialog.addButton("Install Now", QMessageBox.ButtonRole.AcceptRole)
        skip_button = dialog.addButton("Skip this version", QMessageBox.ButtonRole.DestructiveRole)
        dialog.addButton("Later", QMessageBox.ButtonRole.RejectRole)
        dialog.exec()

        clicked = dialog.clickedButton()
        if clicked == download_button:
            if not result.download_url:
                QMessageBox.warning(
                    self,
                    "Update available",
                    "No downloadable Windows asset was found for the latest release.",
                )
                self.status.setText("Update found, but no Windows download asset is available.")
                return

            self.update_button.setEnabled(False)
            self.status.setText("Downloading update...")

            def _progress(downloaded: int, total: int | None) -> None:
                if total and total > 0:
                    percent = int((downloaded / total) * 100)
                    self.status.setText(f"Downloading update... {percent}%")
                else:
                    mb = downloaded / (1024 * 1024)
                    self.status.setText(f"Downloading update... {mb:.1f} MB")
                QApplication.processEvents()

            install_result = start_in_app_update(
                result.download_url,
                result.asset_name,
                result.latest_version,
                progress_callback=_progress,
            )
            self.update_button.setEnabled(True)

            if not install_result.started:
                QMessageBox.warning(self, "Update failed", install_result.message)
                self.status.setText("Update failed.")
                return

            self.status.setText(install_result.message)
            QMessageBox.information(
                self,
                "Installing update",
                "Update downloaded. Sticker Hub will now close and relaunch automatically.",
            )
            QTimer.singleShot(180, QApplication.instance().quit)
            return

        if clicked == skip_button:
            self._skipped_update_version = result.latest_version
            self._settings.setValue("updates/skipped_version", self._skipped_update_version)
            self.status.setText(f"Skipped update v{result.latest_version}.")
            return

        self.status.setText("Update postponed.")

    def _reload_catalog(self) -> None:
        self.catalog = load_catalog_from_json(self.sticker_file)
        valid_ids = {sticker.sticker_id for sticker in self.catalog.stickers}
        self.favorites.intersection_update(valid_ids)
        self.recent = [sticker_id for sticker_id in self.recent if sticker_id in valid_ids]
        if self.selected_id and self.selected_id not in valid_ids:
            self.selected_id = None
        self._build_sidebar()
        self._create_cards()
        self._apply_filters()

