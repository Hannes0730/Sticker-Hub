from __future__ import annotations

from pathlib import Path

from sticker_hub.models import load_catalog_from_json
from sticker_hub.paths import ensure_stickers_json, get_catalog_db_path


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    source_json = project_root / "stickers.json"
    sticker_json = ensure_stickers_json(source_json if source_json.exists() else None)

    catalog = load_catalog_from_json(sticker_json)
    db_path = get_catalog_db_path()

    print(f"json_cache={sticker_json}")
    print(f"sqlite_db={db_path}")
    print(f"categories={len(catalog.categories)} stickers={len(catalog.stickers)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

