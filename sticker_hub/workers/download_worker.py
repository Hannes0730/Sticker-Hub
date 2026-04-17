from __future__ import annotations

from dataclasses import dataclass

import requests
from PySide6.QtCore import QObject, QRunnable, Signal

from sticker_hub.models import Sticker
from sticker_hub.services.cache_service import StickerCache
from sticker_hub.utils import build_thumbnail, detect_animation, detect_extension


@dataclass
class StickerPayload:
    sticker_id: str
    local_path: str
    animated: bool
    thumbnail: object


class DownloadSignals(QObject):
    ready = Signal(object)
    failed = Signal(str, str)


class DownloadWorker(QRunnable):
    def __init__(
        self,
        sticker: Sticker,
        cache: StickerCache,
        timeout_seconds: int = 20,
        thumbnail_size: tuple[int, int] = (168, 168),
    ):
        super().__init__()
        self.sticker = sticker
        self.cache = cache
        self.timeout_seconds = timeout_seconds
        self.thumbnail_size = thumbnail_size
        self.signals = DownloadSignals()

    def run(self) -> None:
        try:
            cached = self.cache.get(self.sticker.image_url)
            if cached:
                image_bytes = cached.path.read_bytes()
                qimage = build_thumbnail(image_bytes, self.thumbnail_size)
                self.signals.ready.emit(
                    StickerPayload(
                        sticker_id=self.sticker.sticker_id,
                        local_path=str(cached.path),
                        animated=cached.animated,
                        thumbnail=qimage,
                    )
                )
                return

            response = requests.get(self.sticker.image_url, timeout=self.timeout_seconds)
            response.raise_for_status()
            image_bytes = response.content

            animated = detect_animation(image_bytes)
            ext = detect_extension(self.sticker.image_url, response.headers.get("Content-Type"))
            local_path = self.cache.put(self.sticker.image_url, ext, image_bytes, animated)

            qimage = build_thumbnail(image_bytes, self.thumbnail_size)
            self.signals.ready.emit(
                StickerPayload(
                    sticker_id=self.sticker.sticker_id,
                    local_path=str(local_path),
                    animated=animated,
                    thumbnail=qimage,
                )
            )
        except Exception as exc:
            self.signals.failed.emit(self.sticker.sticker_id, str(exc))

