from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from PySide6.QtGui import QImage


def build_thumbnail(image_bytes: bytes, size: tuple[int, int] = (168, 168)) -> QImage:
    with Image.open(io.BytesIO(image_bytes)) as img:
        img = img.convert("RGBA")
        img.thumbnail(size, Image.Resampling.LANCZOS)
        raw = img.tobytes("raw", "RGBA")
        qimage = QImage(raw, img.width, img.height, QImage.Format.Format_RGBA8888)
        return qimage.copy()


def detect_animation(image_bytes: bytes) -> bool:
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            return bool(getattr(img, "is_animated", False) and getattr(img, "n_frames", 1) > 1)
    except UnidentifiedImageError:
        return False


def detect_extension(url: str, content_type: str | None) -> str:
    suffix = Path(url).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
        return suffix

    if not content_type:
        return ".bin"

    mapping = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/gif": ".gif",
        "image/webp": ".webp",
    }
    for key, ext in mapping.items():
        if content_type.startswith(key):
            return ext

    return ".bin"


