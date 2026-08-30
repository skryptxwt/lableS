import unittest
from types import SimpleNamespace

from utils.ImageApp import Image


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


if __name__ == '__main__':
    unittest.main()
