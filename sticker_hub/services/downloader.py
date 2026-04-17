from __future__ import annotations

from PySide6.QtCore import QObject, QThreadPool, Signal

from sticker_hub.models import Sticker
from sticker_hub.services.cache_service import StickerCache
from sticker_hub.workers.download_worker import DownloadWorker


class StickerDownloadManager(QObject):
    sticker_ready = Signal(object)
    sticker_failed = Signal(str, str)

    def __init__(self, cache: StickerCache, parent: QObject | None = None):
        super().__init__(parent)
        self.cache = cache
        self._pool = QThreadPool.globalInstance()
        self._pool.setMaxThreadCount(max(self._pool.maxThreadCount(), 6))
        self._inflight: set[str] = set()
        self._thumbnail_size: tuple[int, int] = (168, 168)

    def set_thumbnail_size(self, size: tuple[int, int]) -> None:
        self._thumbnail_size = size

    def queue_download(self, sticker: Sticker) -> None:
        if sticker.sticker_id in self._inflight:
            return

        self._inflight.add(sticker.sticker_id)
        worker = DownloadWorker(sticker, self.cache, thumbnail_size=self._thumbnail_size)
        worker.signals.ready.connect(self._handle_ready)
        worker.signals.failed.connect(self._handle_failed)
        self._pool.start(worker)

    def _handle_ready(self, payload: object) -> None:
        sticker_id = getattr(payload, "sticker_id", "")
        self._inflight.discard(sticker_id)
        self.sticker_ready.emit(payload)

    def _handle_failed(self, sticker_id: str, message: str) -> None:
        self._inflight.discard(sticker_id)
        self.sticker_failed.emit(sticker_id, message)

