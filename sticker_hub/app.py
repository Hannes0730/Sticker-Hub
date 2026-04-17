from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QRect
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication

from sticker_hub.models import load_catalog_from_json
from sticker_hub.paths import get_asset_path
from sticker_hub.services import StickerCache
from sticker_hub.theme import DARK_THEME
from sticker_hub.ui.main_window import MainWindow
from sticker_hub.version import get_app_version


def _load_runtime_icon() -> QIcon:
    icon_path = get_asset_path("icon.png")
    pixmap = QPixmap(str(icon_path))
    if pixmap.isNull():
        return QIcon()

    width = pixmap.width()
    height = pixmap.height()
    if width == height:
        return QIcon(pixmap)

    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    cropped = pixmap.copy(QRect(left, top, side, side))
    return QIcon(cropped)


def run_app(sticker_file: Path) -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME)

    runtime_icon = _load_runtime_icon()
    if not runtime_icon.isNull():
        app.setWindowIcon(runtime_icon)

    catalog = load_catalog_from_json(sticker_file)
    cache = StickerCache()
    app_version = get_app_version()

    window = MainWindow(catalog, cache, sticker_file, app_version=app_version)
    if not runtime_icon.isNull():
        window.setWindowIcon(runtime_icon)
    window.show()

    return app.exec()
