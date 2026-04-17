from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from sticker_hub.models import load_catalog_from_json
from sticker_hub.services import StickerCache
from sticker_hub.theme import DARK_THEME
from sticker_hub.ui.main_window import MainWindow


def run_app(sticker_file: Path) -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME)

    catalog = load_catalog_from_json(sticker_file)
    cache = StickerCache()

    window = MainWindow(catalog, cache, sticker_file)
    window.show()

    return app.exec()

