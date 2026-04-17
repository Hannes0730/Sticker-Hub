from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QWidget

from sticker_hub.ui.sticker_card import StickerCard


class StickerGrid(QWidget):
    def __init__(self):
        super().__init__()
        self._cards: list[StickerCard] = []

        self.layout_grid = QGridLayout(self)
        self.layout_grid.setContentsMargins(8, 8, 8, 12)
        self.layout_grid.setHorizontalSpacing(12)
        self.layout_grid.setVerticalSpacing(12)
        self.layout_grid.setAlignment(Qt.AlignmentFlag.AlignTop)

    def set_cards(self, cards: list[StickerCard]) -> None:
        self._cards = cards
        self._rebuild_grid()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._rebuild_grid()

    def _rebuild_grid(self) -> None:
        while self.layout_grid.count():
            item = self.layout_grid.takeAt(0)
            if item.widget():
                item.widget().setParent(self)

        if not self._cards:
            return

        cell_width = 192
        columns = max(1, self.width() // cell_width)

        for idx, card in enumerate(self._cards):
            row = idx // columns
            col = idx % columns
            self.layout_grid.addWidget(card, row, col)


