from pathlib import Path
import sys

from sticker_hub import run_app
from sticker_hub.paths import ensure_stickers_json


def _find_default_stickers_source() -> Path | None:
    candidates: list[Path] = []

    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(meipass) / "stickers.json")
        candidates.append(Path(sys.executable).resolve().parent / "stickers.json")
    else:
        candidates.append(Path(__file__).resolve().parent / "stickers.json")

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def main() -> int:
    sticker_path = ensure_stickers_json(_find_default_stickers_source())
    return run_app(sticker_path)


if __name__ == "__main__":
    raise SystemExit(main())
