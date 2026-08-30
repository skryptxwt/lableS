import unittest
import math
from types import SimpleNamespace
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QImage

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
    def test_draft_respects_disabled_fill_option(self):
        canvas = QImage(100, 100, QImage.Format_ARGB32)
        canvas.fill(Qt.transparent)
        style = {
            'border': (20, 180, 220, 255),
            'fill': (40, 190, 90, 180),
            'handle': (240, 60, 70, 255),
            'handle_size': 6,
        }
        image = SimpleNamespace(
            screen_label=SimpleNamespace(pixmap=lambda: canvas),
            parent=SimpleNamespace(cls=0),
            task='detect',
            show_box_fill=False,
            _class_style=lambda _cls: style,
            _enable_quality_rendering=Image._enable_quality_rendering,
            _annotation_pen=Image._annotation_pen,
            org_xy_to_new_xy=lambda point: point,
        )

        Image.draw_task_draft(
            image, bbox=[10, 10, 80, 80], pixmap=canvas, commit=False)

        self.assertEqual(canvas.pixelColor(45, 45).alpha(), 0)
        self.assertGreater(canvas.pixelColor(10, 10).alpha(), 0)

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

    def test_annotation_pen_uses_round_subpixel_strokes(self):
        pen = Image._annotation_pen((20, 120, 220, 255), 2.5)

        self.assertAlmostEqual(pen.widthF(), 2.5)
        self.assertEqual(pen.capStyle(), Qt.RoundCap)
        self.assertEqual(pen.joinStyle(), Qt.RoundJoin)

    def test_annotation_font_uses_quality_cjk_rendering(self):
        font = Image._annotation_font(13)

        self.assertEqual(font.family(), 'Microsoft YaHei UI')
        self.assertEqual(font.pixelSize(), 13)
        self.assertEqual(font.weight(), font.Medium)
        self.assertTrue(font.styleStrategy() & font.PreferAntialias)
        self.assertTrue(font.styleStrategy() & font.PreferQuality)

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

    def test_detection_center_is_not_a_resize_handle(self):
        image = FakeImage([[0, 10, 10, 110, 110]])

        self.assertEqual(len(Image.circle_nine(10, 10, 110, 110)), 8)
        self.assertEqual(image.hit_test(60, 60), ('rect', 0, -1))

    def test_detection_box_translation_preserves_size_at_boundary(self):
        moved = Image.translate_detect_label(
            [0, 10, 20, 110, 80], 100, -50, 150, 100)

        self.assertEqual(moved, [0, 50, 0, 150, 60])

    def test_detection_interior_drag_uses_press_offset(self):
        image = SimpleNamespace(
            org_width=200,
            org_height=120,
            new_xy_to_org_xy=lambda point: point,
            translate_detect_label=Image.translate_detect_label,
        )
        window = SimpleNamespace(
            img=image,
            mouse_pos=(80, 70),
            rect_save_current=[0, -1, [0, 10, 20, 110, 80]],
            detect_drag_original=[0, 10, 20, 110, 80],
            detect_drag_start_org=(60, 50),
        )

        moved = MainWin.computer_new_label(window)

        self.assertEqual(moved, [0, 30, 40, 130, 100])

    def test_detection_data_can_update_without_immediate_canvas_redraw(self):
        image = SimpleNamespace(
            task='detect',
            mod=0,
            org_width=200,
            org_height=120,
            label_save=[[0, 10, 20, 110, 80]],
            basedata=[[0, .3, .4, .5, .5]],
            show=lambda *_args, **_kwargs: self.fail(
                'coalesced update must not redraw immediately'),
            label_show=lambda *_args, **_kwargs: self.fail(
                'coalesced update must not redraw immediately'),
        )
        image._clamp_label = lambda label: Image._clamp_label(image, label)

        Image.change(image, 0, [0, 30, 40, 130, 100], redraw=False)

        self.assertEqual(image.label_save[0], [0, 30.0, 40.0, 130.0, 100.0])
        self.assertEqual(image.basedata[0], [0, .4, 7 / 12, .5, .5])

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

    def test_obb_has_four_edge_midpoint_handles(self):
        points = [QPointF(10, 20), QPointF(110, 20),
                  QPointF(110, 80), QPointF(10, 80)]

        handles = Image.obb_edge_handles(points)

        self.assertEqual(len(handles), 4)
        self.assertEqual([(point.x(), point.y()) for point in handles], [
            (60.0, 20.0), (110.0, 50.0),
            (60.0, 80.0), (10.0, 50.0),
        ])

    def test_obb_drag_preview_is_explicitly_closed(self):
        self.assertTrue(Image.draft_is_closed(
            'obb', 4, cursor=None, closed_shape=True))
        # A transient task-state change must not make the fourth edge vanish.
        self.assertTrue(Image.draft_is_closed(
            'detect', 4, cursor=None, closed_shape=True))
        self.assertFalse(Image.draft_is_closed(
            'segment', 4, cursor=(30, 30)))

    def test_obb_edge_handle_resizes_only_its_axis(self):
        label = [0, 10, 20, 110, 20, 110, 80, 10, 80]

        resized = Image.resize_obb_edge(label, 0, (60, 0))

        self.assertObbIsRectangle(resized)
        self.assertEqual(resized, [
            0, 10.0, 0.0, 110.0, 0.0,
            110.0, 80.0, 10.0, 80.0,
        ])

    def test_obb_edge_midpoint_is_hit_before_shape(self):
        image = SimpleNamespace(
            task='obb',
            label_save=[[0, 10, 20, 110, 20, 110, 80, 10, 80]],
            org_xy_to_new_xy=lambda point: point,
            obb_rotation_handle=Image.obb_rotation_handle,
            obb_edge_handles=Image.obb_edge_handles,
        )

        self.assertEqual(
            Image.task_hit_test(image, 110, 50), ('edge', 0, 1))

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

    def test_segment_edge_hit_projects_to_edge_and_preserves_order(self):
        image = SimpleNamespace(
            task='segment',
            label_save=[[0, 10, 10, 110, 10, 110, 80, 10, 80]],
            org_xy_to_new_xy=lambda point: point,
        )

        hit = Image.segment_edge_hit_test(image, 65, 14)

        self.assertEqual(hit[:2], (0, 0))
        self.assertEqual(hit[2], (65.0, 10.0))

    def test_segment_edge_hit_does_not_duplicate_near_vertex(self):
        image = SimpleNamespace(
            task='segment',
            label_save=[[0, 10, 10, 110, 10, 110, 80, 10, 80]],
            org_xy_to_new_xy=lambda point: point,
        )

        self.assertIsNone(Image.segment_edge_hit_test(image, 13, 12))


if __name__ == '__main__':
    unittest.main()
