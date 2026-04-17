from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from PIL import Image, ImageSequence


@dataclass
class CacheEntry:
    path: Path
    animated: bool


class StickerCache:
    def __init__(self, app_name: str = "sticker_hub"):
        self.base_dir = Path(tempfile.gettempdir()) / app_name
        self.files_dir = self.base_dir / "stickers"
        self.send_dir = self.base_dir / "send"
        self.meta_file = self.base_dir / "index.json"
        self._lock = threading.Lock()
        self._index = self._load_index()

        self.files_dir.mkdir(parents=True, exist_ok=True)
        self.send_dir.mkdir(parents=True, exist_ok=True)

    def get(self, url: str) -> CacheEntry | None:
        with self._lock:
            item = self._index.get(url)
            if not item:
                return None

            path = self.files_dir / str(item["name"])
            if path.exists():
                return CacheEntry(path=path, animated=bool(item.get("animated", False)))

            return None

    def put(self, url: str, ext: str, image_bytes: bytes, animated: bool) -> Path:
        digest = sha256(url.encode("utf-8")).hexdigest()
        filename = f"{digest}{ext}"
        output = self.files_dir / filename
        output.write_bytes(image_bytes)

        with self._lock:
            self._index[url] = {"name": filename, "animated": animated}
            self._save_index()

        return output

    def create_send_copy(self, source: Path, preferred_ext: str = "original") -> tuple[Path, bool]:
        timestamp = int(time.time() * 1000)
        normalized_pref = preferred_ext.strip().lower()

        if normalized_pref in {"", "original", source.suffix.lower()}:
            send_file = self.send_dir / f"sticker_{timestamp}{source.suffix.lower()}"
            shutil.copy2(source, send_file)
            return send_file, True

        if normalized_pref not in {".gif", ".webp"}:
            send_file = self.send_dir / f"sticker_{timestamp}{source.suffix.lower()}"
            shutil.copy2(source, send_file)
            return send_file, False

        converted_path = self.send_dir / f"sticker_{timestamp}{normalized_pref}"
        try:
            self._convert_image(source, converted_path, normalized_pref)
            return converted_path, True
        except Exception:
            send_file = self.send_dir / f"sticker_{timestamp}{source.suffix.lower()}"
            shutil.copy2(source, send_file)
            return send_file, False

    def open_location(self, source: Path) -> None:
        if os.name == "nt":
            subprocess.Popen(["explorer", "/select,", str(source)])
            return

        subprocess.Popen(["xdg-open", str(source.parent)])

    def _load_index(self) -> dict[str, dict[str, object]]:
        if not self.meta_file.exists():
            return {}

        try:
            return json.loads(self.meta_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_index(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.meta_file.write_text(json.dumps(self._index, indent=2), encoding="utf-8")

    def _convert_image(self, source: Path, destination: Path, target_ext: str) -> None:
        with Image.open(source) as img:
            animated = bool(getattr(img, "is_animated", False) and getattr(img, "n_frames", 1) > 1)
            if target_ext == ".gif":
                self._save_as_gif(img, destination, animated)
            elif target_ext == ".webp":
                self._save_as_webp(img, destination, animated)
            else:
                raise ValueError(f"Unsupported target extension: {target_ext}")

    def _save_as_gif(self, image: Image.Image, destination: Path, animated: bool) -> None:
        if not animated:
            image.convert("RGBA").convert("P", palette=Image.Palette.ADAPTIVE).save(destination, format="GIF")
            return

        frames = [frame.convert("RGBA") for frame in ImageSequence.Iterator(image)]
        durations = [
            frame.info.get("duration", image.info.get("duration", 80))
            for frame in ImageSequence.Iterator(image)
        ]

        first = frames[0].convert("P", palette=Image.Palette.ADAPTIVE)
        rest = [frame.convert("P", palette=Image.Palette.ADAPTIVE) for frame in frames[1:]]
        first.save(
            destination,
            format="GIF",
            save_all=True,
            append_images=rest,
            loop=image.info.get("loop", 0),
            duration=durations,
            disposal=2,
            optimize=False,
        )

    def _save_as_webp(self, image: Image.Image, destination: Path, animated: bool) -> None:
        if not animated:
            image.convert("RGBA").save(
                destination,
                format="WEBP",
                lossless=True,
                quality=90,
                method=6,
            )
            return

        frames = [frame.convert("RGBA") for frame in ImageSequence.Iterator(image)]
        durations = [
            frame.info.get("duration", image.info.get("duration", 80))
            for frame in ImageSequence.Iterator(image)
        ]

        first = frames[0]
        first.save(
            destination,
            format="WEBP",
            save_all=True,
            append_images=frames[1:],
            duration=durations,
            loop=image.info.get("loop", 0),
            lossless=True,
            quality=90,
            method=6,
        )


