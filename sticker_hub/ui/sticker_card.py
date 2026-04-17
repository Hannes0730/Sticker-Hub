from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageSequence
from PySide6.QtCore import QPoint, Qt, QMimeData, QUrl, Signal
from PySide6.QtCore import QTimer
from PySide6.QtGui import QDrag, QImage, QMovie, QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QMenu, QVBoxLayout

from sticker_hub.models import Sticker


class StickerCard(QFrame):
    left_clicked = Signal(str)
    copy_requested = Signal(str)
    save_requested = Signal(str)
    open_location_requested = Signal(str)
    favorite_toggled = Signal(str)

    def __init__(self, sticker: Sticker):
        super().__init__()
        self.sticker = sticker
        self.local_path: Path | None = None
        self.is_animated = False
        self.is_favorite = False
        self._drag_start = QPoint()
        self._base_pixmap: QPixmap | None = None
        self._movie: QMovie | None = None
        self._selected = False
        self._can_try_movie = False
        self._movie_failed = False
        self._fallback_timer = QTimer(self)
        self._fallback_timer.timeout.connect(self._advance_fallback_frame)
        self._fallback_frames: list[QPixmap] = []
        self._fallback_delays: list[int] = []
        self._fallback_idx = 0

        self.setObjectName("StickerCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(180, 180)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)

        self.preview = QLabel("Loading...")
        self.preview.setFixedSize(160, 160)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setObjectName("StickerPreview")

        layout.addWidget(self.preview)

    def set_thumbnail(self, pixmap: QPixmap, local_path: Path, animated: bool) -> None:
        self._stop_preview_animation()
        self._reset_animation_state()
        self.local_path = local_path
        self.is_animated = animated
        self._can_try_movie = animated or local_path.suffix.lower() in {".gif", ".webp"}
        self._base_pixmap = pixmap
        self.preview.setPixmap(self._fit_preview(pixmap))
        self.preview.setText("")

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)

        if selected:
            self._start_preview_animation()
        else:
            self._stop_preview_animation()

    def set_error(self, message: str) -> None:
        self.preview.setText("Failed")
        self.preview.setToolTip(message)

    def enterEvent(self, event) -> None:  # noqa: N802
        super().enterEvent(event)
        if not self._selected:
            self._start_preview_animation()

    def leaveEvent(self, event) -> None:  # noqa: N802
        super().leaveEvent(event)
        if not self._selected:
            self._stop_preview_animation()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.position().toPoint()
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if not self.local_path:
            return
        distance = (event.position().toPoint() - self._drag_start).manhattanLength()
        if distance < 8:
            return

        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(str(self.local_path))])

        drag = QDrag(self)
        drag.setMimeData(mime)
        if self._base_pixmap:
            drag.setPixmap(self._fit_preview(self._base_pixmap))
        drag.exec(Qt.DropAction.CopyAction)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        super().mouseReleaseEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            distance = (event.position().toPoint() - self._drag_start).manhattanLength()
            if distance < 8:
                self.left_clicked.emit(self.sticker.sticker_id)

    def _show_context_menu(self, global_pos) -> None:
        menu = QMenu(self)
        copy_action = menu.addAction("Copy")
        save_action = menu.addAction("Save As...")
        open_action = menu.addAction("Open File Location")
        favorite_action = menu.addAction("Remove Favorite" if self.is_favorite else "Add Favorite")

        selected = menu.exec(global_pos)
        if selected == copy_action:
            self.copy_requested.emit(self.sticker.sticker_id)
        elif selected == save_action:
            self.save_requested.emit(self.sticker.sticker_id)
        elif selected == open_action:
            self.open_location_requested.emit(self.sticker.sticker_id)
        elif selected == favorite_action:
            self.favorite_toggled.emit(self.sticker.sticker_id)

    def _start_preview_animation(self) -> None:
        if not self.local_path or not self._can_try_movie:
            return
        if self._movie_failed:
            self._start_fallback_animation()
            return
        if self._movie is None:
            self._movie = QMovie(str(self.local_path))
            if not self._movie.isValid():
                self._movie = None
                self._movie_failed = True
                self._start_fallback_animation()
                return
            self._movie.setScaledSize(self.preview.size())
        # QLabel loses the movie binding after setPixmap(); reattach on every start.
        if self.preview.movie() is not self._movie:
            self.preview.setMovie(self._movie)
        if self._movie and self._movie.state() != QMovie.MovieState.Running:
            self._movie.start()
            # frameCount() can be -1 (unknown) for valid animations, so only
            # degrade when a concrete single/empty frame count is reported.
            frame_count = self._movie.frameCount()
            if frame_count in {0, 1}:
                self._movie.stop()
                self._movie = None
                self._movie_failed = True
                self._start_fallback_animation()

    def _stop_preview_animation(self) -> None:
        if self._fallback_timer.isActive():
            self._fallback_timer.stop()
        if self._movie and self._movie.state() == QMovie.MovieState.Running:
            self._movie.stop()
        if self._base_pixmap:
            self.preview.setPixmap(self._fit_preview(self._base_pixmap))

    def _start_fallback_animation(self) -> None:
        if not self.local_path:
            return
        if not self._fallback_frames:
            self._load_fallback_frames()
        if len(self._fallback_frames) <= 1:
            return

        self._fallback_idx = 0
        self.preview.setPixmap(self._fallback_frames[0])
        self._fallback_timer.start(self._fallback_delays[0])

    def _load_fallback_frames(self) -> None:
        if not self.local_path:
            return
        try:
            with Image.open(self.local_path) as img:
                if not bool(getattr(img, "is_animated", False) and getattr(img, "n_frames", 1) > 1):
                    return

                frames: list[QPixmap] = []
                delays: list[int] = []
                for frame in ImageSequence.Iterator(img):
                    rgba = frame.convert("RGBA")
                    raw = rgba.tobytes("raw", "RGBA")
                    qimage = QImage(
                        raw,
                        rgba.width,
                        rgba.height,
                        QImage.Format.Format_RGBA8888,
                    ).copy()
                    pixmap = QPixmap.fromImage(qimage)
                    frames.append(self._fit_preview(pixmap))
                    delay = int(frame.info.get("duration", img.info.get("duration", 80)))
                    delays.append(max(20, delay))

                self._fallback_frames = frames
                self._fallback_delays = delays
        except Exception:
            self._fallback_frames = []
            self._fallback_delays = []

    def _advance_fallback_frame(self) -> None:
        if not self._fallback_frames:
            self._fallback_timer.stop()
            return

        self._fallback_idx = (self._fallback_idx + 1) % len(self._fallback_frames)
        self.preview.setPixmap(self._fallback_frames[self._fallback_idx])
        self._fallback_timer.start(self._fallback_delays[self._fallback_idx])

    def _reset_animation_state(self) -> None:
        if self._movie:
            self._movie.stop()
        self._movie = None
        self._movie_failed = False
        self._fallback_frames = []
        self._fallback_delays = []
        self._fallback_idx = 0

    def _fit_preview(self, pixmap: QPixmap) -> QPixmap:
        return pixmap.scaled(
            self.preview.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )


