import unittest
import math
from types import SimpleNamespace
from PyQt5.QtCore import QPointF, Qt

from utils.ImageApp import Image
from utils.mainWindow import MainWin


class FakeImage:
    circle_nine = staticmethod(Image.circle_nine)
    _hit_test_indices = Image._hit_test_indices
    hit_test = Image.hit_test

    def __init__(self, labels, selected=None, selected_only=False):
        self.label_save = labels
        self.parent = SimpleNamespace(
            is_choose_rect_index=selected,
            is_hover_move_allow=selected_only,
        )

    @staticmethod
    def org_xy_to_new_xy(point):
        return point


class ImageLayeringTest(unittest.TestCase):
    def assertObbIsRectangle(self, label, places=6):
        points = list(zip(label[1::2], label[2::2]))
        edges = [
            (points[(index + 1) % 4][0] - point[0],
             points[(index + 1) % 4][1] - point[1])
            for index, point in enumerate(points)
        ]
        self.assertAlmostEqual(
            edges[0][0] * edges[1][0] + edges[0][1] * edges[1][1],
            0.0, places=places)
        self.assertAlmostEqual(edges[0][0], -edges[2][0], places=places)
        self.assertAlmostEqual(edges[0][1], -edges[2][1], places=places)
        self.assertAlmostEqual(edges[1][0], -edges[3][0], places=places)
        self.assertAlmostEqual(edges[1][1], -edges[3][1], places=places)

    def test_paint_order_places_latest_box_last(self):
        self.assertEqual(Image._paint_order(3), [0, 1, 2])

    def test_selected_box_is_painted_on_top(self):
        self.assertEqual(Image._paint_order(3, 0), [1, 2, 0])

    def test_overlap_hit_prefers_latest_box(self):
        image = FakeImage([
            [0, 10, 10, 120, 120],
            [1, 50, 50, 160, 160],
        ])
        self.assertEqual(image.hit_test(80, 80), ('rect', 1, -1))

    def test_box_boundary_is_clickable(self):
        image = FakeImage([[0, 50, 50, 160, 160]])
        self.assertEqual(image.hit_test(50, 80), ('rect', 0, -1))

    def test_explicit_list_selection_is_prioritized(self):
        image = FakeImage([
            [0, 10, 10, 120, 120],
            [1, 50, 50, 160, 160],
        ], selected=0, selected_only=True)
        self.assertEqual(image.hit_test(80, 80), ('rect', 0, -1))

    def test_explicit_selection_falls_through_to_other_boxes(self):
        image = FakeImage([
            [0, 10, 10, 120, 120],
            [1, 150, 50, 260, 160],
        ], selected=0, selected_only=True)
        self.assertEqual(image.hit_test(180, 80), ('rect', 1, -1))

    def test_obb_rotation_handle_is_outside_top_edge(self):
        points = [QPointF(10, 20), QPointF(110, 20),
                  QPointF(110, 80), QPointF(10, 80)]

        handle = Image.obb_rotation_handle(points)

        self.assertAlmostEqual(handle.x(), 60)
        self.assertLess(handle.y(), 20)

    def test_rotate_obb_preserves_center_and_edge_lengths(self):
        label = [0, 10, 20, 110, 20, 110, 80, 10, 80]

        rotated = Image.rotate_obb_label(label, 90)
        points = list(zip(rotated[1::2], rotated[2::2]))
        center = (sum(point[0] for point in points) / 4,
                  sum(point[1] for point in points) / 4)
        first_edge = math.dist(points[0], points[1])
        second_edge = math.dist(points[1], points[2])

        self.assertEqual(rotated[0], 0)
        self.assertAlmostEqual(center[0], 60)
        self.assertAlmostEqual(center[1], 50)
        self.assertAlmostEqual(first_edge, 100)
        self.assertAlmostEqual(second_edge, 60)
        self.assertAlmostEqual(Image.obb_angle(rotated), 90)

    def test_rotate_obb_supports_fine_wheel_increment(self):
        label = [0, 10, 20, 110, 20, 110, 80, 10, 80]

        rotated = Image.rotate_obb_label(label, 0.25)

        self.assertAlmostEqual(Image.obb_angle(rotated), 0.25)

    def test_irregular_obb_is_rebuilt_as_a_rectangle(self):
        irregular = [
            3, 420, 133, 756, 451, 545, 589, 209, 357,
        ]

        repaired = Image.canonicalize_obb_label(irregular)

        self.assertObbIsRectangle(repaired)

    def test_rotated_obb_fits_image_without_clipping_individual_corners(self):
        label = [0, 50, 100, 450, 100, 450, 300, 50, 300]
        rotated = Image.rotate_obb_label(label, 45)

        fitted = Image.fit_obb_label(rotated, 500, 400)

        self.assertObbIsRectangle(fitted)
        self.assertTrue(all(0 <= x <= 500 for x in fitted[1::2]))
        self.assertTrue(all(0 <= y <= 400 for y in fitted[2::2]))

    def test_shift_drag_locks_obb_to_square(self):
        end = MainWin._square_drag_end((10, 20), (80, 50))

        self.assertEqual(end, (80.0, 90.0))

    def test_selected_obb_rotates_with_mouse_wheel(self):
        class WheelImage:
            rotate_obb_label = staticmethod(Image.rotate_obb_label)
            obb_angle = staticmethod(Image.obb_angle)

            def __init__(self):
                self.label_save = [
                    [0, 10, 20, 110, 20, 110, 80, 10, 80]
                ]

            def change_annotation(self, index, label):
                self.label_save[index] = label

        class WheelEvent:
            accepted = False

            @staticmethod
            def angleDelta():
                return SimpleNamespace(y=lambda: 120)

            @staticmethod
            def modifiers():
                return Qt.NoModifier

            def accept(self):
                self.accepted = True

        timer = SimpleNamespace(start=lambda: None)
        status = SimpleNamespace(showMessage=lambda _message: None)
        window = SimpleNamespace(
            arrows=True,
            img_is_load=True,
            annotation_task='obb',
            is_choose_rect=True,
            is_choose_rect_index=0,
            img=WheelImage(),
            rect_save_current=None,
            _obb_save_timer=timer,
            statusBar=lambda: status,
        )
        event = WheelEvent()

        MainWin.wheelEvent(window, event)

        self.assertTrue(event.accepted)
        self.assertAlmostEqual(Image.obb_angle(window.img.label_save[0]), 2)

    def test_task_hit_test_prefers_latest_overlapping_polygon(self):
        image = SimpleNamespace(
            task='segment',
            label_save=[
                [0, 10, 10, 100, 10, 100, 100, 10, 100],
                [1, 40, 40, 130, 40, 130, 130, 40, 130],
            ],
            org_xy_to_new_xy=lambda point: point,
        )

        self.assertEqual(
            Image.task_hit_test(image, 70, 70), ('shape', 1, -1))


if __name__ == '__main__':
    unittest.main()
