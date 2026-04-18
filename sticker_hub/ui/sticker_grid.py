from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QWidget

from sticker_hub.ui.sticker_card import StickerCard


class StickerGrid(QWidget):
    def __init__(self):
        super().__init__()
        self._cards: list[StickerCard] = []
        self._last_columns: int | None = None

        self.layout_grid = QGridLayout(self)
        self.layout_grid.setContentsMargins(8, 8, 8, 12)
        self.layout_grid.setHorizontalSpacing(12)
        self.layout_grid.setVerticalSpacing(12)
        self.layout_grid.setAlignment(Qt.AlignmentFlag.AlignTop)

    def set_cards(self, cards: list[StickerCard]) -> None:
        self._cards = cards
        # Force a rebuild when the visible card list changes.
        self._last_columns = None
        self.update_layout_for_width(self.width())

    def visible_cards(self) -> list[StickerCard]:
        return list(self._cards)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.update_layout_for_width(event.size().width())

    def update_layout_for_width(self, width: int) -> None:
        columns = self._compute_columns(width)
        if columns == self._last_columns:
            return
        self._rebuild_grid(columns)
        self._last_columns = columns

    def _compute_columns(self, width: int) -> int:
        if width <= 0:
            width = self.width()
        margins = self.layout_grid.contentsMargins()
        spacing = max(0, self.layout_grid.horizontalSpacing())
        available_width = max(1, width - margins.left() - margins.right())

        card_width = 180
        if self._cards:
            card_width = max(1, self._cards[0].sizeHint().width())

        # Fit as many cards as possible including inter-column spacing.
        return max(1, (available_width + spacing) // (card_width + spacing))

    def _rebuild_grid(self, columns: int) -> None:
        while self.layout_grid.count():
            item = self.layout_grid.takeAt(0)
            if item.widget():
                widget = item.widget()
                widget.hide()

        if not self._cards:
            return


        for idx, card in enumerate(self._cards):
            row = idx // columns
            col = idx % columns
            self.layout_grid.addWidget(card, row, col)
            card.setVisible(True)


