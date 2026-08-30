import unittest

from utils.class_styles import (
    DEFAULT_BORDER, DEFAULT_BORDER_WIDTH, DEFAULT_HANDLE, DEFAULT_HANDLE_SIZE,
    DEFAULT_SELECTED_BORDER_EXTRA, DEFAULT_TEXT_POSITION, DEFAULT_TEXT_SIZE,
    build_class_styles, default_class_color, default_class_style,
    display_border, normalize_class_style, normalize_rgba,
    serialize_class_styles,
)


class ClassStylesTest(unittest.TestCase):
    def test_legacy_color_becomes_fill_and_opaque_border(self):
        style = normalize_class_style(None, [10, 20, 30, 45])

        self.assertEqual(style['fill'], (10, 20, 30, 45))
        self.assertEqual(style['border'], (10, 20, 30, DEFAULT_BORDER[3]))
        self.assertEqual(style['handle'], DEFAULT_HANDLE)
        self.assertEqual(style['handle_size'], DEFAULT_HANDLE_SIZE)
        self.assertEqual(style['border_width'], DEFAULT_BORDER_WIDTH)
        self.assertEqual(
            style['selected_border_extra'], DEFAULT_SELECTED_BORDER_EXTRA)
        self.assertEqual(style['text'], (10, 20, 30, 255))
        self.assertEqual(style['text_size'], DEFAULT_TEXT_SIZE)
        self.assertEqual(style['text_position'], DEFAULT_TEXT_POSITION)

    def test_border_and_fill_are_normalized_independently(self):
        style = normalize_class_style({
            'border': [1, 2, 3, 180],
            'fill': [4, 5, 6, 70],
            'handle': [7, 8, 9, 160],
            'handle_size': 14,
            'border_width': 5,
            'selected_border_extra': 4,
            'text': [10, 11, 12, 130],
            'text_size': 16,
            'text_position': 'inside_bottom_right',
        })

        self.assertEqual(style['border'], (1, 2, 3, 180))
        self.assertEqual(style['fill'], (4, 5, 6, 70))
        self.assertEqual(style['handle'], (7, 8, 9, 160))
        self.assertEqual(style['handle_size'], 14)
        self.assertEqual(style['border_width'], 5)
        self.assertEqual(style['selected_border_extra'], 4)
        self.assertEqual(style['text'], (10, 11, 12, 130))
        self.assertEqual(style['text_size'], 16)
        self.assertEqual(style['text_position'], 'inside_bottom_right')

    def test_build_supports_string_yaml_keys(self):
        styles = build_class_styles(
            {0: 'part'},
            {'0': {'border': [2, 3, 4, 200], 'fill': [5, 6, 7, 40]}},
            {'0': [8, 9, 10, 50]},
        )

        self.assertEqual(styles[0]['border'], (2, 3, 4, 200))
        self.assertEqual(styles[0]['fill'], (5, 6, 7, 40))

    def test_serialized_styles_are_yaml_safe_lists(self):
        serialized = serialize_class_styles({
            3: {
                'border': (1, 2, 3, 4),
                'border_width': 6,
                'selected_border_extra': 7,
                'fill': (5, 6, 7, 8),
                'handle': (9, 10, 11, 12),
                'handle_size': 16,
                'text': (13, 14, 15, 16),
                'text_size': 18,
                'text_position': 'outside_bottom_left',
            },
        })

        self.assertEqual(serialized[3]['border'], [1, 2, 3, 4])
        self.assertEqual(serialized[3]['fill'], [5, 6, 7, 8])
        self.assertEqual(serialized[3]['handle'], [9, 10, 11, 12])
        self.assertEqual(serialized[3]['handle_size'], 16)
        self.assertEqual(serialized[3]['border_width'], 6)
        self.assertEqual(serialized[3]['selected_border_extra'], 7)
        self.assertEqual(serialized[3]['text'], [13, 14, 15, 16])
        self.assertEqual(serialized[3]['text_size'], 18)
        self.assertEqual(serialized[3]['text_position'], 'outside_bottom_left')

    def test_invalid_dimensions_and_position_use_safe_values(self):
        style = normalize_class_style({
            'border_width': 99,
            'selected_border_extra': 99,
            'handle_size': 99,
            'text_size': 'invalid',
            'text_position': 'somewhere',
        })

        self.assertEqual(style['border_width'], 12)
        self.assertEqual(style['selected_border_extra'], 12)
        self.assertEqual(style['handle_size'], 20)
        self.assertEqual(style['text_size'], DEFAULT_TEXT_SIZE)
        self.assertEqual(style['text_position'], DEFAULT_TEXT_POSITION)

    def test_invalid_rgba_uses_default(self):
        self.assertEqual(
            normalize_rgba([999, 0, 0, 20], (1, 2, 3, 4)),
            (1, 2, 3, 4),
        )

    def test_selected_border_is_opaque_and_more_prominent(self):
        normal_color, normal_width = display_border((10, 20, 30, 80), 3)
        selected_color, selected_width = display_border(
            (10, 20, 30, 80), 3, selected=True)

        self.assertEqual(normal_color, (10, 20, 30, 80))
        self.assertEqual(normal_width, 3)
        self.assertEqual(selected_color, (10, 20, 30, 255))
        self.assertEqual(selected_width, 5)

    def test_selected_border_uses_configured_extra_width(self):
        selected_color, selected_width = display_border(
            (10, 20, 30, 80), 3, selected=True, selected_extra=6)

        self.assertEqual(selected_color, (10, 20, 30, 255))
        self.assertEqual(selected_width, 9)

    def test_each_default_class_has_a_stable_independent_color(self):
        colors = [default_class_color(class_id) for class_id in range(20)]

        self.assertEqual(colors, [
            default_class_color(class_id) for class_id in range(20)])
        self.assertEqual(len(colors), len(set(colors)))

    def test_default_class_style_derives_channels_from_its_own_color(self):
        color = default_class_color(7)
        style = default_class_style(7)

        self.assertEqual(style['border'], (*color, DEFAULT_BORDER[3]))
        self.assertEqual(style['fill'][:3], color)
        self.assertEqual(style['handle'], (*color, 255))
        self.assertEqual(style['handle_size'], DEFAULT_HANDLE_SIZE)
        self.assertEqual(style['text'][:3], color)
        self.assertEqual(style['border_width'], DEFAULT_BORDER_WIDTH)
        self.assertEqual(
            style['selected_border_extra'], DEFAULT_SELECTED_BORDER_EXTRA)
        self.assertEqual(style['text_size'], DEFAULT_TEXT_SIZE)
        self.assertEqual(style['text_position'], DEFAULT_TEXT_POSITION)


if __name__ == '__main__':
    unittest.main()
