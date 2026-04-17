from __future__ import annotations

import os
import shutil
from pathlib import Path

APP_DIR_NAME = "StickerHub"


def get_data_dir() -> Path:
    override = os.getenv("STICKER_HUB_DATA_DIR", "").strip()
    if override:
        return Path(override).expanduser()

    documents_dir = Path.home() / "Documents"
    if not documents_dir.exists():
        documents_dir = Path.home()
    return documents_dir / APP_DIR_NAME


def get_stickers_json_path() -> Path:
    return get_data_dir() / "stickers.json"


def ensure_stickers_json(default_source: Path | None = None) -> Path:
    target = get_stickers_json_path()
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists():
        return target

    if default_source and default_source.exists():
        shutil.copy2(default_source, target)
    else:
        target.write_text("{}\n", encoding="utf-8")

    return target

