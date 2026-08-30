from pathlib import Path

import cv2
import math
import numpy as np
from PyQt5 import QtGui
from PyQt5.QtCore import QPointF, QRect, QRectF, Qt
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtGui import (QPixmap, QImage, QPainter, QColor, QFont, QPen,
                         QPolygonF)

from .common_fun import read_img
from .DataApp import DataApp
from .class_styles import display_border, normalize_class_style, normalize_rgba


def normalize_color(value, default=(0, 255, 0, 50)):
    """Backward-compatible color normalizer."""
    return normalize_rgba(value, default)


class Image(QMainWindow):

    TASK_MODES = {'detect': 0, 'segment': 1, 'pose': 2, 'obb': 3}

    @staticmethod
    def _enable_quality_rendering(painter):
        """Use the same sub-pixel antialiasing settings for every overlay."""
        painter.setRenderHints(
            QPainter.Antialiasing
            | QPainter.TextAntialiasing
            | QPainter.SmoothPixmapTransform,
            True)

    @staticmethod
    def _annotation_pen(color, width=1.0, style=Qt.SolidLine):
        """Create a smooth pen without sharp caps or jagged corner joins."""
        pen = QPen(QColor(*color))
        pen.setWidthF(max(0.8, float(width)))
        pen.setStyle(style)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        return pen

    @staticmethod
    def _annotation_font(pixel_size):
        """Create a clean CJK-capable font for on-canvas class labels."""
        font = QFont('Microsoft YaHei UI')
        font.setPixelSize(max(6, int(pixel_size)))
        font.setWeight(QFont.Medium)
        font.setHintingPreference(QFont.PreferVerticalHinting)
        font.setStyleStrategy(
            QFont.PreferAntialias | QFont.PreferQuality)
        return font

    def __init__(self, screen_label, img_path: str, label_path, mod=0,
                 parent=None, task=None, kpt_shape=(17, 3)):
        super().__init__()
        if not label_path:
            label_path = Path(parent.default_save_path) / f'{Path(img_path).stem}.txt'
            label_path.parent.mkdir(parents=True, exist_ok=True)
            label_path.touch(exist_ok=True)
        self.task = task or next(
            (name for name, value in self.TASK_MODES.items() if value == mod),
            'detect')
        self.mod = self.TASK_MODES[self.task]
        self.kpt_shape = tuple(kpt_shape)
        self.basedata = DataApp(
            label_path, task=self.task, kpt_shape=self.kpt_shape)
        self.img_path = img_path
        self.label_path = label_path
        self.org_img = read_img(img_path)  # 原始图像
        self.screen_label = screen_label  # 显示图像的label
        self.label_height = self.screen_label.size().height()  # label的高度
        self.label_width = self.screen_label.size().width()  # label的宽度

        self.org_width = self.org_img.shape[1]  # 原始图像的宽度
        self.org_height = self.org_img.shape[0]  # 原始图像的高度
        self.wheel_scale = 1  # 滚轮放大的倍数, 当前图片相对于label尺寸的缩放倍数
        self.center = None  # 当前图像的中心在label中的坐标
        self.label_save = list()  # 记录存储的label信息(真实坐标，不是base_data中的相对坐标，而是图像坐标）
        self.parent = parent
        self.is_trans = False
        self.only_index = False
        self.temp_img = None

        self.show_box_circle = True  # 是否显示矩形框的9个点
        self.show_other = True  # 是否显示其他的标签, True就是添加框的时候不显示其他的框
        self.show_box_fill = True  # 是否显示矩形框的填充
        self.show_box_text = True  # 是否显示矩形框的文字
        self.init()

    def init(self):
        self.center = (self.label_width // 2, self.label_height // 2)
        self.load_new_labels()
        self.show(scale=1)
        self.label_show()

    def resize_image(self, scale=1):
        """
        调整图像大小，填充黑色边框不改变图像的原始比例，缩放为窗口大小的scale倍
        """

        h, w = int(self.label_height * scale), int(self.label_width * scale)

        # 把图像按照原始的比例显示在Qt_label中
        scale_h = self.org_img.shape[0] / h
        scale_w = self.org_img.shape[1] / w

        scale_ = max(scale_w, scale_h)
        target_width = max(1, int(self.org_img.shape[1] / scale_))
        target_height = max(1, int(self.org_img.shape[0] / scale_))
        interpolation = (cv2.INTER_AREA
                         if target_width < self.org_width
                         or target_height < self.org_height
                         else cv2.INTER_CUBIC)
        zoom_img = cv2.resize(self.org_img,
                              (target_width, target_height),
                              interpolation=interpolation)
        back = np.zeros((h, w, 3), dtype=np.uint8)

        if scale_h >= scale_w:
            # 水平填充
            x1 = (back.shape[1] - zoom_img.shape[1]) // 2
            x2 = zoom_img.shape[1] + x1
            back[0:zoom_img.shape[0], x1: x2, :] = \
                zoom_img
        else:
            # 竖直填充
            y1 = (back.shape[0] - zoom_img.shape[0]) // 2
            y2 = zoom_img.shape[0] + y1
            back[y1:y2, 0:zoom_img.shape[1], :] = zoom_img
        zoom_img = back.astype(zoom_img.dtype)
        return cv2.resize(zoom_img, (w, h), interpolation=cv2.INTER_LINEAR)

    def img_transform(self, x, y, scale):
        """
        计算图像的缩放和平移，返回缩放后的图像
        """

        # 保存当前图像的中心在qt label中的坐标，以及当前的缩放倍数(相对于pyqt的label的尺寸)
        self.center = (x, y)
        self.wheel_scale = scale

        new_img = self.resize_image(scale)
        temp = np.zeros((self.label_height, self.label_width, 3), dtype=np.uint8)
        h, w, _ = new_img.shape
        x1, y1 = int(x - w / 2), int(y - h / 2)
        x2, y2 = int(x + w / 2), int(y + h / 2)
        x1, y1 = max(x1, 0), max(y1, 0)
        x2, y2 = min(x2, self.label_width), min(y2, self.label_height)
        temp[y1: y2, x1: x2, :] = new_img[y1 - y + (h + 1) // 2: y2 - y + (h + 1) // 2,
                                  x1 - x + (w + 1) // 2: x2 - x + (w + 1) // 2, :]

        return temp

    def show(self, x=None, y=None, scale=1.0):
        #  把图像显示在对应的qt label上面 但不显示其他信息

        if x is None or y is None:
            #  如果没有指定显示的位置，则默认显示在label的中心
            x, y = self.label_width // 2, self.label_height // 2

        if self.is_trans or self.temp_img is None:
            temp = self.img_transform(x, y, scale)
            self.temp_img = QPixmap.fromImage(QtGui.QImage(temp.data, self.label_width,
                                                           self.label_height, self.label_width * 3,
                                                           QImage.Format_RGB888).rgbSwapped())  # 加载图像
            self.is_trans = False
        self.screen_label.setPixmap(self.temp_img)

    def overlay_frame(self):
        """Return one writable base frame for a complete annotation pass."""
        if self.is_trans or self.temp_img is None:
            self.show(*self.center, scale=self.wheel_scale)
        # Keep the clone implicit; QPainter detaches it only when drawing.
        return QPixmap(self.temp_img)

    def add_rect(self, x1y1, x2y2, text, fill_color, border_color,
                 point_color, box_thickness=3, circle_radius=1,
                 text_size=8, is_show_nine_circle=True, is_over_striking=False,
                 text_color=None, text_position='outside_top_left',
                 painter=None) -> None:
        border_color, box_thickness = display_border(
            border_color, box_thickness, is_over_striking)

        pixmap = self.screen_label.pixmap()
        if pixmap is None:
            return
        owns_painter = painter is None
        if owns_painter:
            painter = QPainter(pixmap)
            self._enable_quality_rendering(painter)

        # 绘制矩形
        painter.setPen(self._annotation_pen(
            border_color, max(1, box_thickness)))
        brush_color = QColor(*fill_color)

        painter.setBrush(brush_color)

        if not self.show_box_fill:
            painter.setBrush(Qt.NoBrush)
        rect = QRectF(QPointF(*x1y1), QPointF(*x2y2)).normalized()
        painter.drawRect(rect)

        if is_show_nine_circle and self.show_box_circle:
            # 锚点是界面控件，保持屏幕像素大小，避免缩放图像后忽大忽小。
            radius = max(2.0, float(circle_radius) / 2)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(*point_color))
            for point in self.circle_nine(*x1y1, *x2y2):
                painter.drawEllipse(QPointF(*point), radius, radius)

        painter.setFont(self._annotation_font(text_size))
        if self.show_box_text:
            painter.setPen(QColor(*(text_color or border_color)))
            metrics = painter.fontMetrics()
            text_rect = self._label_text_rect(
                rect,
                metrics.horizontalAdvance(text) + 8,
                metrics.height() + 4,
                text_position,
                pixmap.rect(),
            )
            painter.drawText(text_rect, Qt.AlignCenter, text)

        if owns_painter:
            painter.end()
            # 单独绘制时立即提交；批量绘制由 label_show 统一提交。
            self.screen_label.setPixmap(pixmap)

    @staticmethod
    def _label_text_rect(rect, width, height, position, canvas_rect, margin=4):
        """Place a class name around a box while keeping it on the canvas."""
        width = min(max(1, int(width)), canvas_rect.width())
        height = min(max(1, int(height)), canvas_rect.height())
        right_aligned = position.endswith('right')
        inside = position.startswith('inside')
        bottom = 'bottom' in position

        x = rect.right() - width if right_aligned else rect.left()
        if inside:
            y = rect.bottom() - height - margin if bottom else rect.top() + margin
        else:
            y = rect.bottom() + margin if bottom else rect.top() - height - margin

        x = max(canvas_rect.left(), min(int(x), canvas_rect.right() - width + 1))
        y = max(canvas_rect.top(), min(int(y), canvas_rect.bottom() - height + 1))
        return QRect(x, y, width, height)

    def add_text(self, x1y1, text, text_color, text_size=12):
        # 图像上绘制文字
        pixmap = self.screen_label.pixmap()
        painter = QPainter(pixmap)
        self._enable_quality_rendering(painter)

        painter.setPen(QColor(*text_color))  # 设置画笔颜色为黑色

        # 使用drawText方法显示文本
        font = QFont("Arial", text_size)  # 设置字体和字号
        painter.setFont(font)
        painter.drawText(QPointF(*x1y1), text)

        painter.end()

        # 将绘制完成的QPixmap重新设置给QLabel
        self.screen_label.setPixmap(pixmap)

    def add_circle(self, x1y1, circle_color, circle_radius=5, is_ball=False):
        # 图像上绘制圆形
        pixmap = self.screen_label.pixmap()
        painter = QPainter(pixmap)
        self._enable_quality_rendering(painter)

        if is_ball:
            # 绘制圆形, 实心
            painter.setBrush(QColor(*circle_color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(*x1y1), circle_radius, circle_radius)
        else:
            # 绘制方点 使用setPen方法设置点的大小
            painter.setPen(self._annotation_pen(
                circle_color, circle_radius))
            painter.drawPoint(QPointF(*x1y1))

        painter.end()

        # 将绘制完成的QPixmap重新设置给QLabel
        self.screen_label.setPixmap(pixmap)

    def add_line(self, x1y1, x2y2, line_color, line_thickness=3):
        # 图像上绘制线
        pixmap = self.screen_label.pixmap()
        painter = QPainter(pixmap)
        self._enable_quality_rendering(painter)

        # 绘制线
        painter.setPen(self._annotation_pen(line_color, line_thickness))
        painter.drawLine(QPointF(*x1y1), QPointF(*x2y2))

        painter.end()

        # 将绘制完成的QPixmap重新设置给QLabel
        self.screen_label.setPixmap(pixmap)

    def load_new_labels(self):
        self.label_save = [
            self._annotation_from_normalized(raw_label)
            for raw_label in self.basedata]
        self.parent.len_rect = len(self.label_save)

    def _annotation_from_normalized(self, raw_label):
        cls = int(raw_label[0])
        values = raw_label[1:]
        if self.task == 'detect':
            x, y, w, h = values
            return [cls, (x - w / 2) * self.org_width,
                    (y - h / 2) * self.org_height,
                    (x + w / 2) * self.org_width,
                    (y + h / 2) * self.org_height]
        if self.task in ('segment', 'obb'):
            points = []
            for offset in range(0, len(values), 2):
                points.extend((values[offset] * self.org_width,
                               values[offset + 1] * self.org_height))
            label = [cls, *points]
            if self.task == 'obb':
                return self.fit_obb_label(
                    label, self.org_width, self.org_height)
            return label
        x, y, w, h = values[:4]
        converted = [cls, (x - w / 2) * self.org_width,
                     (y - h / 2) * self.org_height,
                     (x + w / 2) * self.org_width,
                     (y + h / 2) * self.org_height]
        dimensions = self.kpt_shape[1]
        for offset in range(4, len(values), dimensions):
            converted.extend((values[offset] * self.org_width,
                              values[offset + 1] * self.org_height))
            if dimensions == 3:
                converted.append(int(values[offset + 2]))
        return converted

    def label_show(self, index=None, pixmap=None, commit=True):
        if self.task != 'detect':
            self._label_show_task(index, pixmap=pixmap, commit=commit)
            return
        if self.only_index and index is not None and self.show_other:
            selected_index = self._normalized_index(index, len(self.label_save))
            if selected_index is None:
                return
            label = self.label_save[selected_index]
            cls, x1, y1, x2, y2 = label

            x1, y1 = self.org_xy_to_new_xy((x1, y1))  # 坐标变换, 从原始坐标转换为图像坐标
            x2, y2 = self.org_xy_to_new_xy((x2, y2))
            cls = int(cls)

            box_cls = self.parent.names[cls] if self.parent and self.parent.names.get(cls) else str(cls)

            style = normalize_class_style(
                self.parent.class_styles.get(cls) if self.parent else None,
                self.parent.colors.get(cls) if self.parent else None)

            # self.add_rect((x1, y1), (x2, y2), str(
            #     len(self.label_save) - 1 if index == -1 else index) + ':类别 :' + box_cls,
            #               box_color, (255, 0, 0, 200), (255, 0, 0, 200), 2,
            #               circle_radius=8, is_over_striking=True)

            target = pixmap or self.screen_label.pixmap()
            if target is None:
                return
            painter = QPainter(target)
            self._enable_quality_rendering(painter)
            try:
                self.add_rect(
                    (x1, y1), (x2, y2), box_cls,
                    style['fill'], style['border'],
                    style['handle'], style['border_width'],
                    circle_radius=style['handle_size'],
                    text_size=style['text_size'],
                    is_over_striking=True, text_color=style['text'],
                    text_position=style['text_position'], painter=painter)
            finally:
                painter.end()
            if commit:
                self.screen_label.setPixmap(target)
            return

        if self.mod == 0:
            # 普通检测模式
            # 减少循环内的重复计算和方法调用
            label_count = len(self.label_save)
            parent_names = self.parent.names if self.parent else None
            parent_colors = self.parent.colors if self.parent else None
            parent_styles = self.parent.class_styles if self.parent else None
            selected_index = self._normalized_index(index, label_count)
            target = pixmap or self.screen_label.pixmap()
            if target is None or not label_count:
                return

            # 一帧只创建一个 QPainter、只向 QLabel 提交一次。原实现每个框
            # 都 setPixmap，一旦框较多或大量重叠，MouseMove 会迅速堆积。
            painter = QPainter(target)
            self._enable_quality_rendering(painter)
            try:
                for label_index in self._paint_order(
                        label_count, selected_index):
                    label = self.label_save[label_index]
                    cls, x1, y1, x2, y2 = label
                    x1, y1 = self.org_xy_to_new_xy((x1, y1))
                    x2, y2 = self.org_xy_to_new_xy((x2, y2))
                    cls = int(cls)

                    box_cls = parent_names[cls] if parent_names and cls in parent_names else str(cls)
                    style = normalize_class_style(
                        parent_styles.get(cls) if parent_styles else None,
                        parent_colors.get(cls) if parent_colors else None)

                    self.add_rect(
                        (x1, y1), (x2, y2), f'{box_cls}',
                        style['fill'], style['border'], style['handle'],
                        style['border_width'],
                        circle_radius=style['handle_size'],
                        text_size=style['text_size'],
                        is_over_striking=selected_index == label_index,
                        text_color=style['text'],
                        text_position=style['text_position'], painter=painter)
            finally:
                painter.end()
            if commit:
                self.screen_label.setPixmap(target)

    def _class_style(self, class_id):
        class_id = int(class_id)
        parent = getattr(self, 'parent', None)
        styles = getattr(parent, 'class_styles', None)
        colors = getattr(parent, 'colors', None)
        return normalize_class_style(
            styles.get(class_id) if styles else None,
            colors.get(class_id) if colors else None)

    def _class_name(self, class_id):
        class_id = int(class_id)
        if self.parent and self.parent.names and class_id in self.parent.names:
            return self.parent.names[class_id]
        return str(class_id)

    def _label_show_task(self, index=None, pixmap=None, commit=True):
        label_count = len(self.label_save)
        selected_index = self._normalized_index(index, label_count)
        if self.only_index and self.show_other and selected_index is not None:
            order = [selected_index]
        else:
            order = self._paint_order(label_count, selected_index)
        target = pixmap or self.screen_label.pixmap()
        if target is None or not order:
            return
        painter = QPainter(target)
        self._enable_quality_rendering(painter)
        try:
            for label_index in order:
                label = self.label_save[label_index]
                style = self._class_style(label[0])
                selected = label_index == selected_index
                if self.task in ('segment', 'obb'):
                    points = [
                        QPointF(*self.org_xy_to_new_xy(label[offset:offset + 2]))
                        for offset in range(1, len(label), 2)
                    ]
                    self._paint_polygon(
                        painter, points, self._class_name(label[0]), style,
                        selected, rotated=self.task == 'obb')
                else:
                    self._paint_pose(painter, label, style, selected)
        finally:
            painter.end()
        if commit:
            self.screen_label.setPixmap(target)

    def _paint_polygon(self, painter, points, text, style, selected=False,
                       rotated=False):
        if len(points) < 2:
            return
        border, width = display_border(
            style['border'], style['border_width'], selected)
        painter.setPen(self._annotation_pen(border, width))
        painter.setBrush(
            QColor(*style['fill']) if self.show_box_fill else Qt.NoBrush)
        polygon = QPolygonF(points)
        painter.drawPolygon(polygon)

        if self.show_box_circle and selected:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(*style['handle']))
            handle_size = float(style['handle_size'])
            handle_radius = handle_size / 2
            corner_radius = min(2.5, handle_radius / 2)
            for point in points:
                painter.drawRoundedRect(
                    QRectF(point.x() - handle_radius,
                           point.y() - handle_radius,
                           handle_size, handle_size),
                    corner_radius, corner_radius)
            if rotated and len(points) == 4:
                edge_height = max(4.0, handle_size * 0.72)
                for edge in self.obb_edge_handles(points):
                    painter.drawRoundedRect(
                        QRectF(edge.x() - handle_radius,
                               edge.y() - edge_height / 2,
                               handle_size, edge_height),
                        corner_radius, corner_radius)
                handle = self.obb_rotation_handle(points)
                midpoint = QPointF(
                    (points[0].x() + points[1].x()) / 2,
                    (points[0].y() + points[1].y()) / 2)
                painter.setPen(self._annotation_pen(border, 1))
                painter.drawLine(midpoint, handle)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(handle, handle_radius, handle_radius)

        if self.show_box_text and points:
            painter.setFont(self._annotation_font(style['text_size']))
            painter.setPen(QColor(*style['text']))
            anchor = min(points, key=lambda point: (point.y(), point.x()))
            painter.drawText(
                QPointF(round(anchor.x()),
                        round(max(12, anchor.y() - 6))), text)

    def _paint_pose(self, painter, label, style, selected=False):
        cls, x1, y1, x2, y2, *raw_points = label
        corners = [
            QPointF(*self.org_xy_to_new_xy((x1, y1))),
            QPointF(*self.org_xy_to_new_xy((x2, y1))),
            QPointF(*self.org_xy_to_new_xy((x2, y2))),
            QPointF(*self.org_xy_to_new_xy((x1, y2))),
        ]
        self._paint_polygon(
            painter, corners, self._class_name(cls), style, selected)
        dimensions = self.kpt_shape[1]
        points = []
        for offset in range(0, len(raw_points), dimensions):
            visibility = int(raw_points[offset + 2]) if dimensions == 3 else 2
            point = QPointF(*self.org_xy_to_new_xy(
                raw_points[offset:offset + 2]))
            points.append((point, visibility))

        skeleton = getattr(self.parent, 'kpt_skeleton', ())
        if skeleton:
            painter.setPen(self._annotation_pen(style['border'], 2))
            for start, end in skeleton:
                if (start < len(points) and end < len(points)
                        and points[start][1] and points[end][1]):
                    painter.drawLine(points[start][0], points[end][0])

        for point, visibility in points:
            if visibility == 0:
                continue
            painter.setPen(self._annotation_pen(style['border'], 2))
            painter.setBrush(
                QColor(*style['handle']) if visibility == 2 else Qt.NoBrush)
            selected_radius = float(style['handle_size']) / 2
            radius = selected_radius if selected else max(2.0, selected_radius * .75)
            painter.drawEllipse(point, radius, radius)

    @staticmethod
    def obb_rotation_handle(points, distance=28):
        if len(points) != 4:
            return QPointF()
        midpoint = QPointF((points[0].x() + points[1].x()) / 2,
                           (points[0].y() + points[1].y()) / 2)
        center = QPointF(sum(point.x() for point in points) / 4,
                         sum(point.y() for point in points) / 4)
        dx, dy = midpoint.x() - center.x(), midpoint.y() - center.y()
        length = math.hypot(dx, dy) or 1.0
        return QPointF(midpoint.x() + dx / length * distance,
                       midpoint.y() + dy / length * distance)

    @staticmethod
    def obb_edge_handles(points):
        """Return the midpoint resize handle for every OBB edge."""
        if len(points) != 4:
            return []
        return [
            QPointF((point.x() + points[(index + 1) % 4].x()) / 2,
                    (point.y() + points[(index + 1) % 4].y()) / 2)
            for index, point in enumerate(points)
        ]

    @staticmethod
    def resize_obb_edge(label, edge_index, position, minimum_size=1.0):
        """Move one OBB edge while keeping its opposite edge fixed."""
        label = Image.canonicalize_obb_label(label)
        points = np.asarray(list(zip(label[1::2], label[2::2])),
                            dtype=np.float64)
        edge_index = int(edge_index) % 4
        next_index = (edge_index + 1) % 4
        opposite_start = (edge_index + 2) % 4
        opposite_end = (edge_index + 3) % 4
        selected_midpoint = (points[edge_index] + points[next_index]) / 2
        opposite_midpoint = (
            points[opposite_start] + points[opposite_end]) / 2
        axis = selected_midpoint - opposite_midpoint
        axis_length = float(np.linalg.norm(axis)) or 1.0
        axis /= axis_length
        requested = np.asarray(position, dtype=np.float64) - opposite_midpoint
        distance = max(float(np.dot(requested, axis)),
                       float(minimum_size))
        new_midpoint = opposite_midpoint + axis * distance
        half_edge = (points[next_index] - points[edge_index]) / 2
        points[edge_index] = new_midpoint - half_edge
        points[next_index] = new_midpoint + half_edge
        return [int(label[0]), *points.reshape(-1).tolist()]

    @staticmethod
    def rotate_obb_label(label, degrees):
        """Rotate a YOLO OBB label around its center, preserving its size."""
        label = Image.canonicalize_obb_label(label)
        points = [label[offset:offset + 2]
                  for offset in range(1, len(label), 2)]
        center_x = sum(point[0] for point in points) / 4
        center_y = sum(point[1] for point in points) / 4
        angle = math.radians(float(degrees))
        cosine, sine = math.cos(angle), math.sin(angle)
        rotated = []
        for point in points:
            px, py = point[0] - center_x, point[1] - center_y
            rotated.extend((center_x + px * cosine - py * sine,
                            center_y + px * sine + py * cosine))
        return [int(label[0]), *rotated]

    @staticmethod
    def canonicalize_obb_label(label):
        """Rebuild four ordered points as a true rectangle.

        Point-wise clipping can turn a rotated rectangle into an irregular
        quadrilateral.  Deriving two perpendicular local axes first keeps
        opposite sides parallel and every corner at 90 degrees.
        """
        if len(label) != 9:
            raise ValueError('OBB 标签必须包含类别和 4 个角点')
        points = np.asarray(list(zip(label[1::2], label[2::2])),
                            dtype=np.float64)
        center = points.mean(axis=0)
        axis_u = (points[1] - points[0]) + (points[2] - points[3])
        length_u = float(np.linalg.norm(axis_u))
        if length_u < 1e-9:
            axis_u = points[1] - points[0]
            length_u = float(np.linalg.norm(axis_u))
        if length_u < 1e-9:
            axis_u = np.asarray((1.0, 0.0))
            length_u = 1.0
        axis_u /= length_u
        axis_v = np.asarray((-axis_u[1], axis_u[0]))
        direction_v = (points[3] - points[0]) + (points[2] - points[1])
        if float(np.dot(axis_v, direction_v)) < 0:
            axis_v *= -1

        offsets = points - center
        half_width = max(
            float(np.mean(np.abs(offsets @ axis_u))), 0.5)
        half_height = max(
            float(np.mean(np.abs(offsets @ axis_v))), 0.5)
        corners = np.asarray((
            center - axis_u * half_width - axis_v * half_height,
            center + axis_u * half_width - axis_v * half_height,
            center + axis_u * half_width + axis_v * half_height,
            center - axis_u * half_width + axis_v * half_height,
        ))
        return [int(label[0]), *corners.reshape(-1).tolist()]

    @staticmethod
    def fit_obb_label(label, image_width, image_height):
        """Keep an OBB rectangular while fitting all corners in the image."""
        label = Image.canonicalize_obb_label(label)
        points = np.asarray(list(zip(label[1::2], label[2::2])),
                            dtype=np.float64)
        image_width = max(float(image_width), 1.0)
        image_height = max(float(image_height), 1.0)
        span = np.ptp(points, axis=0)
        scale = min(
            1.0,
            image_width / span[0] if span[0] > image_width else 1.0,
            image_height / span[1] if span[1] > image_height else 1.0,
        )
        if scale < 1.0:
            center = points.mean(axis=0)
            points = center + (points - center) * scale

        minimum = points.min(axis=0)
        maximum = points.max(axis=0)
        shift = np.zeros(2, dtype=np.float64)
        if minimum[0] < 0:
            shift[0] = -minimum[0]
        elif maximum[0] > image_width:
            shift[0] = image_width - maximum[0]
        if minimum[1] < 0:
            shift[1] = -minimum[1]
        elif maximum[1] > image_height:
            shift[1] = image_height - maximum[1]
        points += shift
        points[:, 0] = np.clip(points[:, 0], 0.0, image_width)
        points[:, 1] = np.clip(points[:, 1], 0.0, image_height)
        return [int(label[0]), *points.reshape(-1).tolist()]

    @staticmethod
    def obb_angle(label):
        if len(label) != 9:
            return 0.0
        angle = math.degrees(math.atan2(
            label[4] - label[2], label[3] - label[1]))
        return (angle + 180.0) % 360.0 - 180.0

    @staticmethod
    def _project_point_to_segment(point, start, end):
        """Return distance, projection and ratio for a finite line segment."""
        px, py = float(point[0]), float(point[1])
        x1, y1 = float(start[0]), float(start[1])
        x2, y2 = float(end[0]), float(end[1])
        dx, dy = x2 - x1, y2 - y1
        length_squared = dx * dx + dy * dy
        if length_squared <= 1e-12:
            projection = (x1, y1)
            return math.hypot(px - x1, py - y1), projection, 0.0
        ratio = max(0.0, min(1.0,
                            ((px - x1) * dx + (py - y1) * dy)
                            / length_squared))
        projection = (x1 + ratio * dx, y1 + ratio * dy)
        return (math.hypot(px - projection[0], py - projection[1]),
                projection, ratio)

    def segment_edge_hit_test(self, x, y, distance=12,
                              annotation_index=None, vertex_guard=10):
        """Find the closest editable segment edge and its projected point."""
        if self.task != 'segment':
            return None
        if annotation_index is None:
            indices = range(len(self.label_save) - 1, -1, -1)
        elif 0 <= annotation_index < len(self.label_save):
            indices = (annotation_index,)
        else:
            return None
        for label_index in indices:
            label = self.label_save[label_index]
            points = [self.org_xy_to_new_xy(label[offset:offset + 2])
                      for offset in range(1, len(label), 2)]
            best = None
            for edge_index, start in enumerate(points):
                end = points[(edge_index + 1) % len(points)]
                gap, projection, ratio = Image._project_point_to_segment(
                    (x, y), start, end)
                edge_length = math.dist(start, end)
                endpoint_gap = min(ratio, 1.0 - ratio) * edge_length
                if gap <= distance and endpoint_gap > vertex_guard:
                    candidate = (gap, label_index, edge_index, projection)
                    if best is None or candidate[0] < best[0]:
                        best = candidate
            if best is not None:
                return best[1], best[2], best[3]
        return None

    def task_hit_test(self, x, y, distance=10):
        """Return (kind, annotation index, control index) for non-box tasks."""
        for label_index in range(len(self.label_save) - 1, -1, -1):
            label = self.label_save[label_index]
            style = Image._class_style(self, label[0])
            handle_distance = max(
                float(distance), float(style['handle_size']) / 2 + 4)
            if self.task in ('segment', 'obb'):
                points = [
                    QPointF(*self.org_xy_to_new_xy(label[offset:offset + 2]))
                    for offset in range(1, len(label), 2)
                ]
                if self.task == 'obb':
                    rotation = self.obb_rotation_handle(points)
                    if math.hypot(
                            x - rotation.x(), y - rotation.y()) <= handle_distance:
                        return 'rotate', label_index, -1
                for point_index, point in enumerate(points):
                    if math.hypot(
                            x - point.x(), y - point.y()) <= handle_distance:
                        return 'vertex', label_index, point_index
                if self.task == 'segment':
                    for edge_index, start in enumerate(points):
                        end = points[(edge_index + 1) % len(points)]
                        gap, _projection, _ratio = (
                            Image._project_point_to_segment(
                                (x, y), (start.x(), start.y()),
                                (end.x(), end.y())))
                        if gap <= distance:
                            return 'shape', label_index, -1
                if self.task == 'obb':
                    for edge_index, point in enumerate(
                            self.obb_edge_handles(points)):
                        if math.hypot(
                                x - point.x(), y - point.y()) <= handle_distance:
                            return 'edge', label_index, edge_index
                if QPolygonF(points).containsPoint(
                        QPointF(x, y), Qt.OddEvenFill):
                    return 'shape', label_index, -1
            else:
                dimensions = self.kpt_shape[1]
                raw_points = label[5:]
                for point_index, offset in enumerate(
                        range(0, len(raw_points), dimensions)):
                    visibility = (int(raw_points[offset + 2])
                                  if dimensions == 3 else 2)
                    if visibility == 0:
                        continue
                    point = self.org_xy_to_new_xy(
                        raw_points[offset:offset + 2])
                    if math.hypot(
                            x - point[0], y - point[1]) <= handle_distance:
                        return 'keypoint', label_index, point_index
                p1 = self.org_xy_to_new_xy(label[1:3])
                p2 = self.org_xy_to_new_xy(label[3:5])
                bbox_points = (
                    p1, (p2[0], p1[1]), p2, (p1[0], p2[1]))
                for point_index, point in enumerate(bbox_points):
                    if math.hypot(
                            x - point[0], y - point[1]) <= handle_distance:
                        return 'bbox_vertex', label_index, point_index
                left, right = sorted((p1[0], p2[0]))
                top, bottom = sorted((p1[1], p2[1]))
                if left <= x <= right and top <= y <= bottom:
                    return 'shape', label_index, -1
        return None, -1, -1

    @staticmethod
    def _normalized_index(index, label_count):
        if index is None or isinstance(index, bool) or not label_count:
            return None
        try:
            index = int(index)
        except (TypeError, ValueError, OverflowError):
            return None
        if index < 0:
            index += label_count
        return index if 0 <= index < label_count else None

    @staticmethod
    def _paint_order(label_count, selected_index=None):
        """Paint oldest to newest, with an explicit selection on top."""
        order = list(range(label_count))
        if selected_index in order:
            order.remove(selected_index)
            order.append(selected_index)
        return order

    def new_xy_to_org_xy(self, xy):
        """
        坐标变换 将图像坐标转换为真实坐标
        """

        x, y = xy
        x = x - (self.center[0] - self.label_width / 2)
        y = y - (self.center[1] - self.label_height / 2)

        x = (x - self.label_width / 2) / self.wheel_scale + self.label_width / 2
        y = (y - self.label_height / 2) / self.wheel_scale + self.label_height / 2

        scale_x = self.org_img.shape[1] / self.label_width
        scale_y = self.org_img.shape[0] / self.label_height

        if scale_x > scale_y:
            scale = 1 / scale_x
            y = y - (self.label_height - self.org_img.shape[0] * scale) / 2
        else:
            scale = 1 / scale_y
            x = x - (self.label_width - self.org_img.shape[1] * scale) / 2

        x, y = x / scale, y / scale

        return x, y

    def org_xy_to_new_xy(self, xy):
        """
        坐标变换 将真实坐标转换为图像坐标
        """

        x, y = xy
        scale_x = self.org_width / self.label_width
        scale_y = self.org_height / self.label_height

        if scale_x > scale_y:
            # 说明是竖直填充
            scale = 1 / scale_x
            x, y = x * scale, y * scale

            y = (self.label_height - self.org_img.shape[0] * scale) / 2 + y
        else:
            # 说明是水平填充
            scale = 1 / scale_y
            x, y = x * scale, y * scale

            x = (self.label_width - self.org_img.shape[1] * scale) / 2 + x

        x = (x - self.label_width / 2) * self.wheel_scale + self.label_width / 2
        y = (y - self.label_height / 2) * self.wheel_scale + self.label_height / 2

        x = self.center[0] - self.label_width / 2 + x
        y = self.center[1] - self.label_height / 2 + y

        return x, y

    @staticmethod
    def circle_nine(x1, y1, x2, y2):
        """
        给定矩形的左上角和右下角坐标，返回 8 个缩放锚点。

        方法名为兼容旧调用保留；中心点已移除，框内区域用于整体拖动。
        """
        return [(x1, y1), (x2, y1), (x1, y2), (x2, y2),
                (x1, y1 + (y2 - y1) // 2),
                (x1 + (x2 - x1) // 2, y2),
                (x2, y2 - (y2 - y1) // 2),
                (x2 - (x2 - x1) // 2, y1)]

    @staticmethod
    def translate_detect_label(label, dx, dy, image_width, image_height):
        """Translate a detection box without shrinking it at image edges."""
        cls, x1, y1, x2, y2 = label
        x1, x2 = sorted((float(x1), float(x2)))
        y1, y2 = sorted((float(y1), float(y2)))
        dx = min(max(float(dx), -x1), float(image_width) - x2)
        dy = min(max(float(dy), -y1), float(image_height) - y2)
        return [int(cls), x1 + dx, y1 + dy, x2 + dx, y2 + dy]

    def is_in_circle(self, x, y, circle_distance=25):
        hit_type, index, point_index = self.hit_test(
            x, y, circle_distance)
        if hit_type == 'handle':
            return [True, index, point_index]
        return [False, -1, -1]

    def is_in_rect(self, x, y):
        hit_type, index, _point_index = self.hit_test(x, y)
        if hit_type == 'rect':
            return [True, index, -1]
        return [False, -1, -1]

    def _hit_test_indices(self):
        selected = getattr(self.parent, 'is_choose_rect_index', None)
        selected_first = (
            getattr(self.parent, 'is_hover_move_allow', False)
            and selected is not None
            and 0 <= selected < len(self.label_save)
        )
        order = list(range(len(self.label_save) - 1, -1, -1))
        if selected_first:
            order.remove(selected)
            order.insert(0, selected)
        return order

    def hit_test(self, x, y, circle_distance=15):
        """Hit the visually topmost box, where the latest box is on top."""
        for i in self._hit_test_indices():
            rect = self.label_save[i]
            style = Image._class_style(self, rect[0])
            handle_distance = max(
                float(circle_distance), float(style['handle_size']) / 2 + 4)
            x1y1 = self.org_xy_to_new_xy(rect[1:3])
            x2y2 = self.org_xy_to_new_xy(rect[3:5])
            for point_index, point in enumerate(self.circle_nine(
                    x1y1[0], x1y1[1], x2y2[0], x2y2[1])):
                if math.hypot(
                        x - point[0], y - point[1]) < handle_distance:
                    return 'handle', i, point_index
            left, right = sorted((x1y1[0], x2y2[0]))
            top, bottom = sorted((x1y1[1], x2y2[1]))
            if left <= x <= right and top <= y <= bottom:
                return 'rect', i, -1
        return None, -1, -1

    def pop(self, index):
        # 删除标签
        self.label_save.pop(index)
        self.basedata.pop(index)
        self.show(scale=self.wheel_scale)
        self.label_show()

    def append(self, label, redraw=True):
        # 添加标签
        if self.mod == 0:
            #  label为相对qt label的坐标
            cls, x1, y1, x2, y2 = label
            x1, y1 = self.new_xy_to_org_xy((x1, y1))  # 坐标变换, 从图像坐标转换为原始坐标
            x2, y2 = self.new_xy_to_org_xy((x2, y2))

            label = self._clamp_label([cls, x1, y1, x2, y2])
            cls, x1, y1, x2, y2 = label
            self.label_save.append(label)

            x, y, w, h = (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1
            x, y, w, h = x / self.org_width, y / self.org_height, w / self.org_width, h / self.org_height
            self.basedata.append([cls, x, y, w, h])
            if redraw:
                self.show(*self.center, scale=self.wheel_scale)
                # 新框拖动期间开启了 only_index，只绘制当前框即可，避免首帧
                # 把所有旧框重复绘制一遍。
                self.label_show(len(self.label_save) - 1)

    def insert(self, index, label):
        # 添加标签
        if self.mod == 0:
            #  label为相对qt label的坐标
            cls, x1, y1, x2, y2 = label
            x1, y1 = self.new_xy_to_org_xy((x1, y1))  # 坐标变换, 从图像坐标转换为原始坐标
            x2, y2 = self.new_xy_to_org_xy((x2, y2))

            label = self._clamp_label([cls, x1, y1, x2, y2])
            cls, x1, y1, x2, y2 = label
            self.label_save.insert(index, label)

            x, y, w, h = (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1
            x, y, w, h = x / self.org_width, y / self.org_height, w / self.org_width, h / self.org_height

            self.basedata.insert(index, [cls, x, y, w, h])
            self.show(*self.center, scale=self.wheel_scale)
            self.label_show()

    def change(self, index, label, redraw=True):
        # 修改标签
        if self.task != 'detect':
            self.change_annotation(index, label, redraw=redraw)
            return
        if self.mod == 0:
            label = self._clamp_label(label)
            self.label_save[index] = label
            #  label为相对qt label的坐标
            cls, x1, y1, x2, y2 = label
            x, y, w, h = (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1
            x, y, w, h = x / self.org_width, y / self.org_height, w / self.org_width, h / self.org_height
            self.basedata[index] = [cls, x, y, w, h]
            if redraw:
                self.show(*self.center, scale=self.wheel_scale)
                self.label_show(index)

    def _clamp_label(self, label):
        cls, x1, y1, x2, y2 = label
        x1, x2 = sorted((max(0.0, min(float(x1), self.org_width)),
                         max(0.0, min(float(x2), self.org_width))))
        y1, y2 = sorted((max(0.0, min(float(y1), self.org_height)),
                         max(0.0, min(float(y2), self.org_height))))
        return [int(cls), x1, y1, x2, y2]

    def _clamp_point(self, point):
        return (max(0.0, min(float(point[0]), self.org_width)),
                max(0.0, min(float(point[1]), self.org_height)))

    def _normalize_annotation(self, label):
        cls = int(label[0])
        if self.task == 'obb':
            fitted = self.fit_obb_label(
                label, self.org_width, self.org_height)
            coordinates = []
            for offset in range(1, len(fitted), 2):
                coordinates.extend((fitted[offset] / self.org_width,
                                    fitted[offset + 1] / self.org_height))
            return [cls, *coordinates]
        if self.task == 'segment':
            coordinates = []
            for offset in range(1, len(label), 2):
                x, y = self._clamp_point(label[offset:offset + 2])
                coordinates.extend((x / self.org_width, y / self.org_height))
            return [cls, *coordinates]
        if self.task == 'pose':
            cls, x1, y1, x2, y2, *raw_points = label
            x1, y1 = self._clamp_point((x1, y1))
            x2, y2 = self._clamp_point((x2, y2))
            x1, x2 = sorted((x1, x2))
            y1, y2 = sorted((y1, y2))
            normalized = [int(cls), (x1 + x2) / 2 / self.org_width,
                          (y1 + y2) / 2 / self.org_height,
                          (x2 - x1) / self.org_width,
                          (y2 - y1) / self.org_height]
            dimensions = self.kpt_shape[1]
            for offset in range(0, len(raw_points), dimensions):
                x, y = self._clamp_point(raw_points[offset:offset + 2])
                normalized.extend((x / self.org_width, y / self.org_height))
                if dimensions == 3:
                    normalized.append(int(raw_points[offset + 2]))
            return normalized
        raise ValueError(f'任务 {self.task} 不使用通用标注转换')

    def append_annotation(self, label):
        normalized = self._normalize_annotation(label)
        self.basedata.append(normalized)
        self.label_save.append(self._annotation_from_normalized(normalized))
        if self.parent:
            self.parent.len_rect = len(self.label_save)
        self.show(*self.center, scale=self.wheel_scale)
        self.label_show(len(self.label_save) - 1)
        return len(self.label_save) - 1

    def change_annotation(self, index, label, redraw=True):
        normalized = self._normalize_annotation(label)
        self.basedata[index] = normalized
        self.label_save[index] = self._annotation_from_normalized(normalized)
        if redraw:
            self.show(*self.center, scale=self.wheel_scale)
            self.label_show(index)

    def draw_task_draft(self, points=None, cursor=None, bbox=None,
                        pose_points=None, close_polygon=False, pixmap=None,
                        commit=True):
        """Draw an unsaved task annotation over the current canvas frame."""
        target = pixmap or self.screen_label.pixmap()
        if target is None:
            return
        painter = QPainter(target)
        self._enable_quality_rendering(painter)
        style = self._class_style(self.parent.cls if self.parent else 0)
        border, width = display_border(style['border'], 2, True)
        painter.setPen(self._annotation_pen(border, width, Qt.DashLine))
        painter.setBrush(QColor(*style['fill']))
        if points:
            canvas_points = [QPointF(*self.org_xy_to_new_xy(point))
                             for point in points]
            path_points = list(canvas_points)
            if cursor is not None:
                path_points.append(QPointF(*cursor))
            if len(path_points) >= 2:
                if close_polygon and len(canvas_points) >= 3:
                    painter.drawPolygon(QPolygonF(canvas_points))
                elif self.task == 'obb' and cursor is None and len(path_points) == 4:
                    painter.drawPolygon(QPolygonF(path_points))
                else:
                    painter.drawPolyline(QPolygonF(path_points))
            painter.setBrush(QColor(*style['handle']))
            handle_radius = float(style['handle_size']) / 2
            for point in canvas_points:
                painter.drawEllipse(point, handle_radius, handle_radius)
            if close_polygon and len(canvas_points) >= 3:
                painter.setBrush(Qt.NoBrush)
                painter.setPen(self._annotation_pen(border, max(2, width)))
                close_radius = max(9.0, handle_radius + 4)
                painter.drawEllipse(canvas_points[0], close_radius, close_radius)
        if bbox is not None:
            p1 = QPointF(*self.org_xy_to_new_xy(bbox[:2]))
            p2 = QPointF(*self.org_xy_to_new_xy(bbox[2:]))
            painter.drawRect(QRectF(p1, p2).normalized())
        if pose_points:
            painter.setBrush(QColor(*style['handle']))
            handle_radius = float(style['handle_size']) / 2
            for point in pose_points:
                canvas_point = QPointF(*self.org_xy_to_new_xy(point))
                painter.drawEllipse(canvas_point, handle_radius, handle_radius)
        painter.end()
        if commit:
            self.screen_label.setPixmap(target)

    def save(self):
        self.basedata.save()

    def __getitem__(self, item):
        return [self.label_save[item], self.basedata[item]]

    def __len__(self):
        return len(self.label_save)
