from __future__ import annotations

import os
import shutil
import sys
import tempfile
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

#test
def get_cache_dir() -> Path:
    override = os.getenv("STICKER_HUB_CACHE_DIR", "").strip()
    if override:
        return Path(override).expanduser()

    return Path(tempfile.gettempdir()) / APP_DIR_NAME


def get_stickers_json_path() -> Path:
    return get_data_dir() / "stickers.json"


def get_catalog_db_path() -> Path:
    return get_data_dir() / "stickers.db"


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


def get_asset_path(asset_name: str) -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", "")
        if meipass:
            return Path(meipass) / "assets" / asset_name
        return Path(sys.executable).resolve().parent / "assets" / asset_name

    project_root = Path(__file__).resolve().parents[1]
    return project_root / "assets" / asset_name


