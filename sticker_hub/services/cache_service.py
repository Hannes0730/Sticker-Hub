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

    def create_send_copy(
        self,
        source: Path,
        preferred_ext: str = "original",
        upscale_factor: int = 1,
    ) -> tuple[Path, bool]:
        timestamp = int(time.time() * 1000)
        normalized_pref = preferred_ext.strip().lower()
        scale = max(1, int(upscale_factor))

        if normalized_pref in {"", "original", source.suffix.lower()}:
            send_file = self.send_dir / f"sticker_{timestamp}{source.suffix.lower()}"
            if scale == 1:
                shutil.copy2(source, send_file)
                return send_file, True

            try:
                self._convert_image(source, send_file, source.suffix.lower(), scale)
                return send_file, True
            except Exception:
                shutil.copy2(source, send_file)
                return send_file, False

        if normalized_pref not in {".gif", ".webp"}:
            send_file = self.send_dir / f"sticker_{timestamp}{source.suffix.lower()}"
            shutil.copy2(source, send_file)
            return send_file, False

        converted_path = self.send_dir / f"sticker_{timestamp}{normalized_pref}"
        try:
            self._convert_image(source, converted_path, normalized_pref, scale)
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

    def _convert_image(self, source: Path, destination: Path, target_ext: str, upscale_factor: int = 1) -> None:
        with Image.open(source) as img:
            animated = bool(getattr(img, "is_animated", False) and getattr(img, "n_frames", 1) > 1)
            if target_ext == ".gif":
                self._save_as_gif(img, destination, animated, upscale_factor)
            elif target_ext == ".webp":
                self._save_as_webp(img, destination, animated, upscale_factor)
            elif target_ext in {".png", ".jpg", ".jpeg"}:
                self._save_as_static(img, destination, target_ext, animated, upscale_factor)
            else:
                raise ValueError(f"Unsupported target extension: {target_ext}")

    def _save_as_static(
        self,
        image: Image.Image,
        destination: Path,
        target_ext: str,
        animated: bool,
        upscale_factor: int,
    ) -> None:
        if animated:
            # Static formats cannot preserve animation semantics here.
            raise ValueError("Animated image cannot be exported as static format with preserved motion")

        output = image.convert("RGBA")
        if upscale_factor > 1:
            output = self._resize_image(output, upscale_factor)

        if target_ext in {".jpg", ".jpeg"}:
            output.convert("RGB").save(destination, format="JPEG", quality=95, optimize=True)
            return

        output.save(destination, format="PNG", optimize=True)

    def _save_as_gif(self, image: Image.Image, destination: Path, animated: bool, upscale_factor: int) -> None:
        if not animated:
            output = image.convert("RGBA")
            if upscale_factor > 1:
                output = self._resize_image(output, upscale_factor)
            # GIF is limited to 256 colors; dithering helps reduce harsh banding.
            output.quantize(
                colors=256,
                method=Image.Quantize.FASTOCTREE,
                dither=Image.Dither.FLOYDSTEINBERG,
            ).save(destination, format="GIF")
            return

        frames: list[Image.Image] = []
        durations: list[int] = []
        for frame in ImageSequence.Iterator(image):
            rgba = frame.convert("RGBA")
            if upscale_factor > 1:
                rgba = self._resize_image(rgba, upscale_factor)
            frames.append(rgba)
            durations.append(int(frame.info.get("duration", image.info.get("duration", 80))))

        first = frames[0].quantize(
            colors=256,
            method=Image.Quantize.FASTOCTREE,
            dither=Image.Dither.FLOYDSTEINBERG,
        )
        rest = [
            frame.quantize(
                colors=256,
                method=Image.Quantize.FASTOCTREE,
                dither=Image.Dither.FLOYDSTEINBERG,
            )
            for frame in frames[1:]
        ]
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

    def _save_as_webp(self, image: Image.Image, destination: Path, animated: bool, upscale_factor: int) -> None:
        if not animated:
            output = image.convert("RGBA")
            if upscale_factor > 1:
                output = self._resize_image(output, upscale_factor)
            output.save(
                destination,
                format="WEBP",
                lossless=True,
                quality=90,
                method=6,
            )
            return

        frames: list[Image.Image] = []
        durations: list[int] = []
        for frame in ImageSequence.Iterator(image):
            rgba = frame.convert("RGBA")
            if upscale_factor > 1:
                rgba = self._resize_image(rgba, upscale_factor)
            frames.append(rgba)
            durations.append(int(frame.info.get("duration", image.info.get("duration", 80))))

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

    def _resize_image(self, image: Image.Image, upscale_factor: int) -> Image.Image:
        if upscale_factor <= 1:
            return image

        width, height = image.size
        return image.resize(
            (max(1, width * upscale_factor), max(1, height * upscale_factor)),
            Image.Resampling.LANCZOS,
        )


