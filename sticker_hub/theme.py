DARK_THEME = """
QWidget {
    background: #1e2124;
    color: #dcddde;
    font-family: Segoe UI, Arial, sans-serif;
    font-size: 13px;
}
QLineEdit {
    background: #2b2d31;
    border: 1px solid #3f4147;
    border-radius: 8px;
    padding: 8px 10px;
    color: #f2f3f5;
}
QLineEdit:focus {
    border: 1px solid #5865f2;
}
QComboBox#CopyFormatCombo {
    background: #2b2d31;
    border: 1px solid #3f4147;
    border-radius: 8px;
    padding: 6px 10px;
    color: #f2f3f5;
}
QComboBox#CopyFormatCombo:hover {
    border: 1px solid #5865f2;
}
QComboBox#CopyFormatCombo QAbstractItemView {
    background: #2b2d31;
    border: 1px solid #3f4147;
    selection-background-color: #5865f2;
    color: #f2f3f5;
}
QPushButton#ImportButton {
    background: #5865f2;
    color: #ffffff;
    border: 1px solid #5865f2;
    border-radius: 8px;
    padding: 7px 12px;
    font-weight: 600;
}
QPushButton#ImportButton:hover {
    background: #6875f5;
}
QPushButton#ImportButton:disabled {
    background: #3b3f46;
    border: 1px solid #3b3f46;
    color: #aeb4bd;
}
QListWidget#Sidebar {
    background: #111214;
    border: 1px solid #2b2d31;
    border-radius: 10px;
    outline: none;
    padding: 8px;
}
QListWidget#Sidebar::item {
    margin: 2px;
    padding: 8px;
    border-radius: 8px;
}
QListWidget#Sidebar::item:selected {
    background: #5865f2;
    color: #ffffff;
}
QListWidget#Sidebar::item:hover {
    background: #3b3f46;
}
QScrollArea {
    border: 1px solid #2b2d31;
    border-radius: 10px;
    background: #17191c;
}
QFrame#StickerCard {
    background: #23262b;
    border: 1px solid #2d3138;
    border-radius: 12px;
}
QFrame#StickerCard:hover {
    border: 1px solid #5865f2;
    background: #2d3138;
}
QFrame#StickerCard[selected=\"true\"] {
    border: 1px solid #00b0f4;
}
QLabel#StickerPreview {
    background: #17191c;
    border-radius: 10px;
}
QLabel#StickerTitle {
    color: #f2f3f5;
    font-size: 12px;
}
QLabel#StatusLabel {
    color: #9ca3af;
    padding-left: 2px;
}
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 6px 2px 6px 2px;
}
QScrollBar::handle:vertical {
    background: #3b3f46;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #5865f2;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}
"""

