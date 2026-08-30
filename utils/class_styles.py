from ast import literal_eval
import colorsys


DEFAULT_BORDER = (36, 155, 200, 230)
DEFAULT_FILL = (36, 155, 200, 50)
DEFAULT_HANDLE = (238, 68, 75, 230)
DEFAULT_BORDER_WIDTH = 2
DEFAULT_TEXT = (36, 155, 200, 255)
DEFAULT_TEXT_SIZE = 10
DEFAULT_TEXT_POSITION = 'outside_top_left'
TEXT_POSITIONS = (
    'outside_top_left', 'outside_top_right',
    'inside_top_left', 'inside_top_right',
    'inside_bottom_left', 'inside_bottom_right',
    'outside_bottom_left', 'outside_bottom_right',
)


def default_class_color(class_id):
    """Return a stable, visually separated RGB color for a class id."""
    try:
        class_id = max(0, int(class_id))
    except (TypeError, ValueError, OverflowError):
        class_id = 0
    # 黄金比例步进可避免相邻类别集中在同一色相区域。类别 0 从工业蓝开始。
    hue = (0.55 + class_id * 0.618033988749895) % 1.0
    saturation = 0.72
    value = 0.88
    return tuple(round(channel * 255) for channel in colorsys.hsv_to_rgb(
        hue, saturation, value))


def default_class_style(class_id):
    """Build the independent default palette entry for one class."""
    red, green, blue = default_class_color(class_id)
    return {
        'border': (red, green, blue, DEFAULT_BORDER[3]),
        'border_width': DEFAULT_BORDER_WIDTH,
        'fill': (red, green, blue, DEFAULT_FILL[3]),
        'handle': (red, green, blue, 255),
        'text': (red, green, blue, DEFAULT_TEXT[3]),
        'text_size': DEFAULT_TEXT_SIZE,
        'text_position': DEFAULT_TEXT_POSITION,
    }


def normalize_rgba(value, default):
    """Return a safe RGBA tuple from YAML-compatible values."""
    if value is None:
        return tuple(default)
    if isinstance(value, str):
        try:
            value = literal_eval(value)
        except (SyntaxError, ValueError):
            return tuple(default)
    if not isinstance(value, (list, tuple)) or len(value) not in (3, 4):
        return tuple(default)
    try:
        channels = tuple(int(channel) for channel in value)
    except (TypeError, ValueError):
        return tuple(default)
    if any(channel < 0 or channel > 255 for channel in channels):
        return tuple(default)
    if len(channels) == 3:
        return (*channels, int(default[3]))
    return channels


def mapping_value(mapping, class_id):
    if not isinstance(mapping, dict):
        return None
    if class_id in mapping:
        return mapping[class_id]
    return mapping.get(str(class_id))


def normalize_int(value, default, minimum, maximum):
    try:
        value = int(value)
    except (TypeError, ValueError, OverflowError):
        return int(default)
    return max(minimum, min(value, maximum))


def normalize_text_position(value):
    return value if value in TEXT_POSITIONS else DEFAULT_TEXT_POSITION


def display_border(border, width, selected=False):
    """Return the temporary border appearance for normal/selected rendering."""
    border = normalize_rgba(border, DEFAULT_BORDER)
    width = normalize_int(width, DEFAULT_BORDER_WIDTH, 1, 12)
    if not selected:
        return border, width
    return (*border[:3], 255), width + 2


def normalize_class_style(value=None, legacy_color=None):
    legacy_fill = normalize_rgba(legacy_color, DEFAULT_FILL)
    legacy_border = (*legacy_fill[:3], DEFAULT_BORDER[3])
    legacy_text = (*legacy_border[:3], DEFAULT_TEXT[3])
    if not isinstance(value, dict):
        return {
            'border': legacy_border,
            'border_width': DEFAULT_BORDER_WIDTH,
            'fill': legacy_fill,
            'handle': DEFAULT_HANDLE,
            'text': legacy_text,
            'text_size': DEFAULT_TEXT_SIZE,
            'text_position': DEFAULT_TEXT_POSITION,
        }
    border = normalize_rgba(value.get('border'), legacy_border)
    return {
        'border': border,
        'border_width': normalize_int(
            value.get('border_width'), DEFAULT_BORDER_WIDTH, 1, 12),
        'fill': normalize_rgba(value.get('fill'), legacy_fill),
        'handle': normalize_rgba(value.get('handle'), DEFAULT_HANDLE),
        'text': normalize_rgba(
            value.get('text'), (*border[:3], DEFAULT_TEXT[3])),
        'text_size': normalize_int(
            value.get('text_size'), DEFAULT_TEXT_SIZE, 6, 48),
        'text_position': normalize_text_position(value.get('text_position')),
    }


def build_class_styles(names, raw_styles=None, legacy_colors=None):
    styles = {}
    for raw_id in names or {}:
        class_id = int(raw_id)
        styles[class_id] = normalize_class_style(
            mapping_value(raw_styles, class_id),
            mapping_value(legacy_colors, class_id))
    return styles


def serialize_class_styles(styles):
    return {
        int(class_id): {
            'border': list(style['border']),
            'border_width': int(style['border_width']),
            'fill': list(style['fill']),
            'handle': list(style['handle']),
            'text': list(style['text']),
            'text_size': int(style['text_size']),
            'text_position': style['text_position'],
        }
        for class_id, style in styles.items()
    }
