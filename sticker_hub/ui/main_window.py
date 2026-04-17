from __future__ import annotations

import shutil
from pathlib import Path

from PySide6.QtCore import QMimeData, Qt, QUrl
from PySide6.QtGui import QPixmap
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
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QScroller

from sticker_hub.models import Sticker, StickerCatalog, append_sticker_to_json, load_catalog_from_json
from sticker_hub.services import StickerCache, StickerDownloadManager, resolve_sticker_urls
from sticker_hub.ui.sticker_card import StickerCard
from sticker_hub.ui.sticker_grid import StickerGrid


class MainWindow(QWidget):
    def __init__(self, catalog: StickerCatalog, cache: StickerCache, sticker_file: Path, app_version: str):
        super().__init__()
        self.catalog = catalog
        self.cache = cache
        self.sticker_file = sticker_file
        self.app_version = app_version.strip() or "dev"
        self.downloader = StickerDownloadManager(cache)

        self.favorites: set[str] = set()
        self.recent: list[str] = []
        self.current_category = "All"
        self.selected_id: str | None = None

        self.cards_by_id: dict[str, StickerCard] = {}

        self.setWindowTitle(f"Sticker Board v{self.app_version}")
        self.resize(1220, 760)

        root = QHBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        self.sidebar = QListWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(220)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        top_bar.setSpacing(8)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search stickers...")

        self.import_button = QPushButton("Import URL")
        self.import_button.setObjectName("ImportButton")

        self.copy_format = QComboBox()
        self.copy_format.setObjectName("CopyFormatCombo")
        self.copy_format.addItem("Copy: Original", "original")
        self.copy_format.addItem("Copy: GIF", ".gif")
        self.copy_format.addItem("Copy: WebP", ".webp")
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
        QScroller.grabGesture(self.scroll.viewport(), QScroller.LeftMouseButtonGesture)

        top_bar.addWidget(self.search, stretch=1)
        top_bar.addWidget(self.copy_format)
        top_bar.addWidget(self.import_button)
        top_bar.addWidget(self.version_badge)

        root.addWidget(self.sidebar)
        right_layout.addLayout(top_bar)
        right_layout.addWidget(self.scroll, stretch=1)
        right_layout.addWidget(self.status)
        root.addWidget(right, stretch=1)

        self._build_sidebar()
        self._create_cards()

        self.sidebar.currentItemChanged.connect(self._on_category_changed)
        self.search.textChanged.connect(lambda _: self._apply_filters())
        self.import_button.clicked.connect(self._open_import_dialog)
        self.downloader.sticker_ready.connect(self._on_sticker_ready)
        self.downloader.sticker_failed.connect(self._on_sticker_failed)

        self._apply_filters()
        self._queue_visible_downloads()

    def _build_sidebar(self) -> None:
        self.sidebar.clear()
        for category in ["All", "Favorites", "Recent", *self.catalog.categories]:
            item = QListWidgetItem(category)
            self.sidebar.addItem(item)
        if self.sidebar.count() > 0:
            matching_items = self.sidebar.findItems(self.current_category, Qt.MatchFlag.MatchExactly)
            self.sidebar.setCurrentItem(matching_items[0] if matching_items else self.sidebar.item(0))

    def _create_cards(self) -> None:
        self.cards_by_id = {}
        for sticker in self.catalog.stickers:
            card = StickerCard(sticker)
            card.left_clicked.connect(self._on_card_left_click)
            card.copy_requested.connect(self._on_copy_requested)
            card.save_requested.connect(self._on_save_requested)
            card.open_location_requested.connect(self._on_open_location_requested)
            card.favorite_toggled.connect(self._toggle_favorite)
            self.cards_by_id[sticker.sticker_id] = card

    def _on_category_changed(self, current: QListWidgetItem, _previous: QListWidgetItem) -> None:
        if not current:
            return
        self.current_category = current.text()
        self._apply_filters()

    def _apply_filters(self) -> None:
        query = self.search.text()

        if self.current_category == "Favorites":
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
            selected_category = None if self.current_category == "All" else self.current_category
            stickers = self.catalog.filtered(selected_category, query)

        visible_cards = []
        for sticker in stickers:
            if not sticker:
                continue
            if query:
                probe = f"{sticker.label} {sticker.category}".lower()
                if query.strip().lower() not in probe:
                    continue
            visible_cards.append(self.cards_by_id[sticker.sticker_id])

        self.grid_widget.set_cards(visible_cards)
        self.status.setText(f"{len(visible_cards)} sticker(s)")
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

    def _on_sticker_failed(self, sticker_id: str, message: str) -> None:
        card = self.cards_by_id.get(sticker_id)
        if card:
            card.set_error(message)

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
        if sticker_id in self.favorites:
            self.favorites.remove(sticker_id)
            self.cards_by_id[sticker_id].is_favorite = False
        else:
            self.favorites.add(sticker_id)
            self.cards_by_id[sticker_id].is_favorite = True

        if self.current_category == "Favorites":
            self._apply_filters()

    def _set_selected(self, sticker_id: str) -> None:
        if self.selected_id and self.selected_id in self.cards_by_id:
            self.cards_by_id[self.selected_id].set_selected(False)

        self.selected_id = sticker_id
        if sticker_id in self.cards_by_id:
            self.cards_by_id[sticker_id].set_selected(True)

    def _copy_sticker_to_send(self, sticker_id: str, set_clipboard: bool) -> None:
        card = self.cards_by_id.get(sticker_id)
        if not card or not card.local_path:
            return

        preferred_ext = str(self.copy_format.currentData())
        send_file, applied_preference = self.cache.create_send_copy(card.local_path, preferred_ext=preferred_ext)
        if not set_clipboard:
            return

        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(str(send_file))])
        QApplication.clipboard().setMimeData(mime)

        if preferred_ext == "original":
            self.status.setText(f"Copied: {send_file.name}")
            return

        if applied_preference:
            self.status.setText(f"Copied as {send_file.suffix.upper()}: {send_file.name}")
        else:
            self.status.setText(f"Copied using original format ({send_file.suffix.upper()}).")

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
        category_input.setPlaceholderText("Imported")
        category_input.setText("Imported")

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        form.addRow("Source URL", source_input)
        form.addRow("Category", category_input)
        form.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        source_url = source_input.text().strip()
        category = category_input.text().strip() or "Imported"
        if not source_url:
            QMessageBox.warning(self, "Import failed", "Please enter a source URL.")
            return

        self._import_from_url(source_url, category)

    def _import_from_url(self, source_url: str, category: str) -> None:
        self.import_button.setEnabled(False)
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
                was_added = append_sticker_to_json(self.sticker_file, category, image_url, "")
                if was_added:
                    imported_count += 1
                else:
                    skipped_count += 1

            self._reload_catalog()
            if skipped_count:
                self.status.setText(
                    f"Imported {imported_count} sticker(s), skipped {skipped_count} duplicate(s) in '{category}'."
                )
            else:
                self.status.setText(f"Imported {imported_count} sticker(s) into '{category}'.")
        except Exception as exc:
            QMessageBox.critical(self, "Import failed", str(exc))
            self.status.setText("Import failed.")
        finally:
            self.import_button.setEnabled(True)

    def _reload_catalog(self) -> None:
        self.catalog = load_catalog_from_json(self.sticker_file)
        self.selected_id = None
        self._build_sidebar()
        self._create_cards()
        self._apply_filters()

