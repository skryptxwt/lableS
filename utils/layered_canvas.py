"""Experimental canvas that separates static and interactive painting.

The production editor currently composes every interaction frame into a full
QPixmap.  This widget keeps the static frame untouched and reuses one
transparent interaction layer.  Pointer updates clear and repaint only the
union of the previous and current annotation bounds.
"""

from PyQt5.QtCore import QRect, QSize, Qt
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtWidgets import QWidget


class LayeredCanvas(QWidget):
    """Two-layer canvas prototype with dirty-region interaction updates."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._static_layer = QPixmap()
        self._interaction_layer = QPixmap()
        self._interaction_bounds = QRect()
        self._last_dirty_rect = QRect()
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)

    def sizeHint(self):
        if not self._static_layer.isNull():
            return self._static_layer.size()
        return QSize(640, 480)

    @property
    def last_dirty_rect(self):
        """Return the most recently scheduled interaction repaint rectangle."""
        return QRect(self._last_dirty_rect)

    def set_static_layer(self, pixmap):
        """Replace the static frame without copying it for later interactions."""
        self._static_layer = pixmap
        if (self._interaction_layer.isNull()
                or self._interaction_layer.size() != pixmap.size()
                or (self._interaction_layer.devicePixelRatio()
                    != pixmap.devicePixelRatio())):
            self._interaction_layer = QPixmap(pixmap.size())
            self._interaction_layer.setDevicePixelRatio(
                pixmap.devicePixelRatio())
            self._interaction_layer.fill(Qt.transparent)
            self._interaction_bounds = QRect()
        self.updateGeometry()
        self.update()

    def update_interaction(self, bounds, draw, padding=3):
        """Redraw one interaction object and update only its changed region.

        ``draw`` receives a QPainter targeting the reusable transparent layer.
        ``bounds`` must contain the complete current interaction geometry.
        """
        if self._interaction_layer.isNull():
            return QRect()

        current = QRect(bounds).normalized().adjusted(
            -padding, -padding, padding, padding)
        current = current.intersected(self._interaction_layer.rect())
        dirty = (self._interaction_bounds.united(current)
                 if not self._interaction_bounds.isNull() else current)

        painter = QPainter(self._interaction_layer)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(dirty, Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.setClipRect(current)
        draw(painter)
        painter.end()

        self._interaction_bounds = current
        self._last_dirty_rect = dirty
        if not dirty.isNull():
            self.update(dirty)
        return QRect(dirty)

    def clear_interaction(self):
        """Clear the current interaction object using its previous dirty area."""
        dirty = QRect(self._interaction_bounds)
        if not self._interaction_layer.isNull() and not dirty.isNull():
            painter = QPainter(self._interaction_layer)
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.fillRect(dirty, Qt.transparent)
            painter.end()
            self.update(dirty)
        self._interaction_bounds = QRect()
        self._last_dirty_rect = dirty
        return dirty

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setClipRegion(event.region())
        if not self._static_layer.isNull():
            painter.drawPixmap(0, 0, self._static_layer)
        if not self._interaction_layer.isNull():
            painter.drawPixmap(0, 0, self._interaction_layer)
        painter.end()
