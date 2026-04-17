import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sticker_hub.models import load_catalog_from_json
from sticker_hub.paths import ensure_stickers_json
from sticker_hub.services import StickerCache


def main() -> int:
    catalog = load_catalog_from_json(ensure_stickers_json(PROJECT_ROOT / "stickers.json"))
    cache = StickerCache("sticker_hub_smoke")

    print(f"categories={len(catalog.categories)} stickers={len(catalog.stickers)}")
    print(f"cache_dir={cache.base_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

