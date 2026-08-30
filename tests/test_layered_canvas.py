import os
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PyQt5.QtCore import QRect, Qt
from PyQt5.QtGui import QColor, QPixmap
from PyQt5.QtWidgets import QApplication

from utils.layered_canvas import LayeredCanvas


class LayeredCanvasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.canvas = LayeredCanvas()
        self.base = QPixmap(200, 120)
        self.base.fill(QColor('#d9e1e6'))
        self.base_key = self.base.cacheKey()
        self.canvas.set_static_layer(self.base)

    @staticmethod
    def _draw_red_rect(rect):
        def draw(painter):
            painter.fillRect(rect, QColor('#ef4444'))
        return draw

    def test_static_pixmap_is_not_copied_or_modified_by_pointer_updates(self):
        self.canvas.update_interaction(
            QRect(10, 10, 30, 20), self._draw_red_rect(QRect(10, 10, 30, 20)),
            padding=0)
        self.canvas.update_interaction(
            QRect(80, 30, 30, 20), self._draw_red_rect(QRect(80, 30, 30, 20)),
            padding=0)

        self.assertEqual(self.base.cacheKey(), self.base_key)
        self.assertEqual(self.canvas._static_layer.cacheKey(), self.base_key)

    def test_pointer_move_repaints_union_and_clears_previous_shape(self):
        old = QRect(10, 10, 30, 20)
        new = QRect(80, 30, 30, 20)
        self.canvas.update_interaction(
            old, self._draw_red_rect(old), padding=0)
        dirty = self.canvas.update_interaction(
            new, self._draw_red_rect(new), padding=0)

        self.assertEqual(dirty, old.united(new))
        image = self.canvas._interaction_layer.toImage()
        self.assertEqual(QColor(image.pixelColor(15, 15)).alpha(), 0)
        self.assertEqual(image.pixelColor(85, 35), QColor('#ef4444'))

    def test_clear_only_invalidates_current_interaction_bounds(self):
        bounds = QRect(20, 25, 40, 30)
        self.canvas.update_interaction(
            bounds, self._draw_red_rect(bounds), padding=0)

        self.assertEqual(self.canvas.clear_interaction(), bounds)
        self.assertTrue(self.canvas._interaction_bounds.isNull())
        self.assertEqual(
            self.canvas._interaction_layer.toImage().pixelColor(30, 30),
            QColor(Qt.transparent))


if __name__ == '__main__':
    unittest.main()
