from copy import deepcopy
from pathlib import Path
import sys

import yaml
from PyQt5.QtCore import QRectF, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QCursor, QFont, QPainter, QPen
from PyQt5.QtWidgets import (
    QAbstractItemView, QColorDialog, QComboBox, QDesktopWidget, QHBoxLayout,
    QInputDialog, QLabel, QListWidget, QListWidgetItem, QMainWindow,
    QMessageBox, QPushButton, QSizePolicy, QSlider, QSpinBox, QVBoxLayout,
    QWidget,
)

from .class_styles import (
    DEFAULT_BORDER, DEFAULT_BORDER_WIDTH, DEFAULT_FILL, DEFAULT_HANDLE,
    DEFAULT_TEXT, DEFAULT_TEXT_POSITION, DEFAULT_TEXT_SIZE, build_class_styles,
    default_class_style, normalize_class_style, serialize_class_styles,
)
from .common_fun import root
from .industrial_theme import INDUSTRIAL_QSS
from .window_chrome import TitleBar

root = root.parent

TEXT_POSITION_LABELS = (
    ('框外左上', 'outside_top_left'),
    ('框外右上', 'outside_top_right'),
    ('框内左上', 'inside_top_left'),
    ('框内右上', 'inside_top_right'),
    ('框内左下', 'inside_bottom_left'),
    ('框内右下', 'inside_bottom_right'),
    ('框外左下', 'outside_bottom_left'),
    ('框外右下', 'outside_bottom_right'),
)


class ClassStylePreview(QWidget):
    """Live sample canvas for the selected annotation class."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.class_name = '类别预览'
        self.border = DEFAULT_BORDER
        self.border_width = DEFAULT_BORDER_WIDTH
        self.fill = DEFAULT_FILL
        self.handle = DEFAULT_HANDLE
        self.text = DEFAULT_TEXT
        self.text_size = DEFAULT_TEXT_SIZE
        self.text_position = DEFAULT_TEXT_POSITION
        self.setObjectName('classStylePreview')
        self.setMinimumHeight(230)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_preview(self, name, style):
        self.class_name = name
        self.border = tuple(style['border'])
        self.border_width = style['border_width']
        self.fill = tuple(style['fill'])
        self.handle = tuple(style['handle'])
        self.text = tuple(style['text'])
        self.text_size = style['text_size']
        self.text_position = style['text_position']
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor('#e8edf0'))

        painter.setPen(QPen(QColor(129, 145, 155, 35), 1))
        for x in range(0, self.width(), 24):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), 24):
            painter.drawLine(0, y, self.width(), y)

        sample = QRectF(
            max(32, self.width() * 0.15),
            max(48, self.height() * 0.22),
            max(120, self.width() * 0.70),
            max(90, self.height() * 0.56),
        )
        painter.setBrush(QColor(*self.fill))
        painter.setPen(QPen(QColor(*self.border), self.border_width))
        painter.drawRoundedRect(sample, 3, 3)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(*self.handle))
        points = (
            sample.topLeft(), sample.topRight(), sample.bottomLeft(),
            sample.bottomRight(),
            sample.center(),
            type(sample.topLeft())(sample.center().x(), sample.top()),
            type(sample.topLeft())(sample.center().x(), sample.bottom()),
            type(sample.topLeft())(sample.left(), sample.center().y()),
            type(sample.topLeft())(sample.right(), sample.center().y()),
        )
        for point in points:
            painter.drawRoundedRect(
                QRectF(point.x() - 4, point.y() - 4, 8, 8), 1.5, 1.5)

        text_font = QFont('Arial')
        text_font.setPixelSize(self.text_size)
        text_font.setBold(True)
        painter.setFont(text_font)
        painter.setPen(QColor(*self.text))
        text_height = painter.fontMetrics().height() + 4
        inside = self.text_position.startswith('inside')
        right = self.text_position.endswith('right')
        bottom = 'bottom' in self.text_position
        margin = 6
        if inside:
            text_y = (sample.bottom() - text_height - margin if bottom
                      else sample.top() + margin)
        else:
            text_y = (sample.bottom() + margin if bottom
                      else sample.top() - text_height - margin)
        text_rect = QRectF(
            sample.left() + margin,
            text_y,
            max(10, sample.width() - margin * 2),
            text_height,
        )
        alignment = (Qt.AlignRight if right else Qt.AlignLeft) | Qt.AlignVCenter
        painter.drawText(text_rect, alignment, self.class_name)


class StyleControl(QWidget):
    colorChanged = pyqtSignal(QColor)
    opacityChanged = pyqtSignal(int)
    opacityEditingFinished = pyqtSignal()

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.color = QColor('#249bc8')
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        title_label = QLabel(title, self)
        title_label.setObjectName('styleControlTitle')
        title_label.setFixedWidth(66)
        self.color_button = QPushButton('选择颜色', self)
        self.color_button.setFixedWidth(88)
        self.color_button.clicked.connect(self._choose_color)
        self.opacity_slider = QSlider(Qt.Horizontal, self)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setProperty('menuSlider', True)
        self.opacity_value = QLabel('100%', self)
        self.opacity_value.setFixedWidth(38)
        self.opacity_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.opacity_slider.valueChanged.connect(self._opacity_changed)
        self.opacity_slider.sliderReleased.connect(
            self.opacityEditingFinished.emit)

        layout.addWidget(title_label)
        layout.addWidget(self.color_button)
        layout.addWidget(self.opacity_slider, 1)
        layout.addWidget(self.opacity_value)

    def set_rgba(self, rgba):
        self.color = QColor(*rgba[:3])
        self.opacity_slider.blockSignals(True)
        self.opacity_slider.setValue(round(rgba[3] * 100 / 255))
        self.opacity_slider.blockSignals(False)
        self.opacity_value.setText(f'{self.opacity_slider.value()}%')
        self._update_swatch()

    def rgba(self):
        alpha = round(self.opacity_slider.value() * 255 / 100)
        return self.color.red(), self.color.green(), self.color.blue(), alpha

    def _choose_color(self):
        color = QColorDialog.getColor(self.color, self, '选择颜色')
        if not color.isValid():
            return
        self.color = color
        self._update_swatch()
        self.colorChanged.emit(color)

    def _update_swatch(self):
        foreground = '#ffffff' if self.color.lightness() < 140 else '#1e2930'
        self.color_button.setStyleSheet(
            f'background: {self.color.name()}; color: {foreground}; '
            'border: 1px solid #82919a; border-radius: 4px;')

    def _opacity_changed(self, value):
        self.opacity_value.setText(f'{value}%')
        self.opacityChanged.emit(value)


class modificationCls(QMainWindow):
    configChanged = pyqtSignal(dict, dict)

    def __init__(self, main_window=None, selected_class=None):
        # Keep this as an independent top-level window so a minimized editor
        # remains available from the Windows taskbar.
        super().__init__(None)
        self.main_window = main_window
        self.selected_class = selected_class
        self.names = {}
        self.styles = {}
        self._loading = False
        self._accepted = False
        self._load_config()
        self._original_names = deepcopy(self.names)
        self._original_styles = deepcopy(self.styles)
        self.initUI()

    def _load_config(self):
        with open(root / 'Detection.yaml', 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file) or {}
        self.names = {
            int(key): str(value)
            for key, value in (data.get('names') or {}).items()
        }
        self.styles = build_class_styles(
            self.names, data.get('class_styles'), data.get('colors'))
        configured_save_path = data.get('save_path', 'temp_folder')
        if configured_save_path == 'temp_folder':
            self.save_path = root / 'utils/temp_folder'
        else:
            path = Path(configured_save_path).expanduser()
            self.save_path = path if path.is_absolute() else root / path

    def initUI(self):
        self.resize(820, 650)
        self.setMinimumSize(720, 570)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        screen = QDesktopWidget().availableGeometry(self)
        self.move(
            screen.center().x() - self.width() // 2,
            screen.center().y() - self.height() // 2,
        )
        self.setWindowTitle('类别样式')
        self.setAttribute(Qt.WA_DeleteOnClose, True)

        shell = QWidget(self)
        shell.setObjectName('windowShell')
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(1, 1, 1, 1)
        shell_layout.setSpacing(0)
        self.title_bar = TitleBar(self)
        self.title_bar.title_label.setText('类别样式')
        shell_layout.addWidget(self.title_bar)

        central = QWidget(shell)
        central.setObjectName('centralwidget')
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)
        shell_layout.addWidget(central, 1)
        self.setCentralWidget(shell)

        left = QWidget(central)
        left.setFixedWidth(220)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(7)
        heading = QLabel('类别', left)
        heading.setProperty('role', 'sectionTitle')
        heading.setFixedHeight(34)
        self.listWidget = QListWidget(left)
        self.listWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.listWidget.currentItemChanged.connect(self._selection_changed)
        left_layout.addWidget(heading)
        left_layout.addWidget(self.listWidget, 1)

        button_row = QHBoxLayout()
        self.btnAdd = QPushButton('添加', left)
        self.btnModify = QPushButton('重命名', left)
        self.btnDelete = QPushButton('删除', left)
        self.btnDelete.setProperty('role', 'danger')
        self.btnAdd.clicked.connect(self.addItem)
        self.btnModify.clicked.connect(self.modifyItem)
        self.btnDelete.clicked.connect(self.deleteItem)
        button_row.addWidget(self.btnAdd)
        button_row.addWidget(self.btnModify)
        button_row.addWidget(self.btnDelete)
        left_layout.addLayout(button_row)
        self.btnReset = QPushButton('全部类别恢复默认值', left)
        self.btnReset.setToolTip('恢复通用尺寸设置，并为每个类别重新分配专属颜色')
        self.btnReset.setToolTip('将全部类别的标注样式恢复为默认值')
        self.btnReset.clicked.connect(self.resetAllStyles)
        left_layout.addWidget(self.btnReset)

        right = QWidget(central)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        preview_heading = QLabel('样式预览', right)
        preview_heading.setProperty('role', 'sectionTitle')
        preview_heading.setFixedHeight(34)
        self.preview = ClassStylePreview(right)
        self.border_control = StyleControl('边框', right)
        self.fill_control = StyleControl('内部填充', right)
        self.handle_control = StyleControl('锚点', right)
        self.text_control = StyleControl('类别文字', right)

        geometry_row = QWidget(right)
        geometry_layout = QHBoxLayout(geometry_row)
        geometry_layout.setContentsMargins(0, 0, 0, 0)
        geometry_layout.setSpacing(8)
        border_width_label = QLabel('边框粗细', geometry_row)
        border_width_label.setObjectName('styleOptionTitle')
        border_width_label.setFixedWidth(66)
        self.border_width_spin = QSpinBox(geometry_row)
        self.border_width_spin.setRange(1, 12)
        self.border_width_spin.setSuffix(' px')
        self.border_width_spin.setFixedWidth(92)
        text_size_label = QLabel('文字大小', geometry_row)
        text_size_label.setObjectName('styleOptionTitle')
        self.text_size_spin = QSpinBox(geometry_row)
        self.text_size_spin.setRange(6, 48)
        self.text_size_spin.setSuffix(' px')
        self.text_size_spin.setFixedWidth(92)
        position_label = QLabel('文字位置', geometry_row)
        position_label.setObjectName('styleOptionTitle')
        self.text_position_combo = QComboBox(geometry_row)
        for label, value in TEXT_POSITION_LABELS:
            self.text_position_combo.addItem(label, value)
        geometry_layout.addWidget(border_width_label)
        geometry_layout.addWidget(self.border_width_spin)
        geometry_layout.addSpacing(8)
        geometry_layout.addWidget(text_size_label)
        geometry_layout.addWidget(self.text_size_spin)
        geometry_layout.addSpacing(8)
        geometry_layout.addWidget(position_label)
        geometry_layout.addWidget(self.text_position_combo, 1)

        common_geometry_row = QWidget(right)
        common_geometry_layout = QHBoxLayout(common_geometry_row)
        common_geometry_layout.setContentsMargins(0, 0, 0, 0)
        common_geometry_layout.setSpacing(8)
        common_geometry_note = QLabel(
            '统一边框粗细、文字大小和位置', common_geometry_row)
        common_geometry_note.setStyleSheet('color: #53646e; padding-left: 2px;')
        self.btnApplyGeometryAll = QPushButton(
            '应用到全部类别', common_geometry_row)
        self.btnApplyGeometryAll.setFixedWidth(126)
        self.btnApplyGeometryAll.setToolTip(
            '把当前边框粗细、文字大小和文字位置应用到全部类别；颜色保持独立')
        self.btnApplyGeometryAll.clicked.connect(self.applyGeometryToAll)
        common_geometry_layout.addWidget(common_geometry_note)
        common_geometry_layout.addStretch(1)
        common_geometry_layout.addWidget(self.btnApplyGeometryAll)
        self.border_control.colorChanged.connect(self._style_changed)
        self.fill_control.colorChanged.connect(self._style_changed)
        self.handle_control.colorChanged.connect(self._style_changed)
        self.text_control.colorChanged.connect(self._style_changed)
        self.border_control.opacityChanged.connect(self._style_changed)
        self.fill_control.opacityChanged.connect(self._style_changed)
        self.handle_control.opacityChanged.connect(self._style_changed)
        self.text_control.opacityChanged.connect(self._style_changed)
        self.border_width_spin.valueChanged.connect(self._style_changed)
        self.text_size_spin.valueChanged.connect(self._style_changed)
        self.text_position_combo.currentIndexChanged.connect(self._style_changed)
        self.hint = QLabel('修改会实时预览；确认后保存，取消或关闭将撤销。', right)
        self.hint.setStyleSheet('color: #667780; padding: 2px;')
        right_layout.addWidget(preview_heading)
        right_layout.addWidget(self.preview, 1)
        right_layout.addWidget(self.border_control)
        right_layout.addWidget(self.fill_control)
        right_layout.addWidget(self.handle_control)
        right_layout.addWidget(self.text_control)
        right_layout.addWidget(geometry_row)
        right_layout.addWidget(common_geometry_row)
        right_layout.addWidget(self.hint)

        action_row = QHBoxLayout()
        action_row.addStretch(1)
        self.btnCancel = QPushButton('取消', right)
        self.btnConfirm = QPushButton('确认', right)
        self.btnConfirm.setProperty('role', 'primary')
        self.btnCancel.setFixedWidth(86)
        self.btnConfirm.setFixedWidth(86)
        self.btnCancel.clicked.connect(self.cancelChanges)
        self.btnConfirm.clicked.connect(self.confirmChanges)
        action_row.addWidget(self.btnCancel)
        action_row.addWidget(self.btnConfirm)
        right_layout.addLayout(action_row)

        root_layout.addWidget(left)
        root_layout.addWidget(right, 1)

        self._rebuild_list(self.selected_class)
        self.setStyleSheet(INDUSTRIAL_QSS)
        self.show()

    def select_class(self, class_id):
        for row in range(self.listWidget.count()):
            item = self.listWidget.item(row)
            if item.data(Qt.UserRole) == int(class_id):
                self.listWidget.setCurrentRow(row)
                return

    def _rebuild_list(self, selected_id=None):
        self.listWidget.blockSignals(True)
        self.listWidget.clear()
        selected_row = 0
        for row, class_id in enumerate(sorted(self.names)):
            item = QListWidgetItem(f'{class_id}   {self.names[class_id]}')
            item.setData(Qt.UserRole, class_id)
            self.listWidget.addItem(item)
            if selected_id is not None and class_id == int(selected_id):
                selected_row = row
        self.listWidget.blockSignals(False)
        if self.listWidget.count():
            self.listWidget.setCurrentRow(selected_row)
            self._load_selected_style()

    def _current_class_id(self):
        item = self.listWidget.currentItem()
        return item.data(Qt.UserRole) if item is not None else None

    def _selection_changed(self, current, _previous):
        if current is not None:
            self._load_selected_style()

    def _load_selected_style(self):
        class_id = self._current_class_id()
        if class_id is None:
            return
        self._loading = True
        style = self.styles[class_id]
        self.border_control.set_rgba(style['border'])
        self.fill_control.set_rgba(style['fill'])
        self.handle_control.set_rgba(style['handle'])
        self.text_control.set_rgba(style['text'])
        self.border_width_spin.setValue(style['border_width'])
        self.text_size_spin.setValue(style['text_size'])
        position_index = self.text_position_combo.findData(style['text_position'])
        self.text_position_combo.setCurrentIndex(max(0, position_index))
        self.preview.set_preview(self.names[class_id], style)
        self._loading = False

    def _style_changed(self, _value=None):
        if self._loading:
            return
        class_id = self._current_class_id()
        if class_id is None:
            return
        self.styles[class_id] = {
            'border': self.border_control.rgba(),
            'border_width': self.border_width_spin.value(),
            'fill': self.fill_control.rgba(),
            'handle': self.handle_control.rgba(),
            'text': self.text_control.rgba(),
            'text_size': self.text_size_spin.value(),
            'text_position': self.text_position_combo.currentData(),
        }
        self.preview.set_preview(self.names[class_id], self.styles[class_id])
        self.configChanged.emit(dict(self.names), dict(self.styles))

    def _persist(self):
        with open(root / 'Detection.yaml', 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file) or {}
        data['names'] = dict(self.names)
        data['class_styles'] = serialize_class_styles(self.styles)
        data['colors'] = {
            class_id: list(style['fill'])
            for class_id, style in self.styles.items()
        }
        with open(root / 'Detection.yaml', 'w', encoding='utf-8') as file:
            yaml.safe_dump(data, file, allow_unicode=True, sort_keys=False)

    def _notify_preview(self):
        self.configChanged.emit(dict(self.names), dict(self.styles))

    def resetAllStyles(self):
        if not self.styles:
            return
        self.styles = {
            class_id: default_class_style(class_id)
            for class_id in self.names
        }
        self._load_selected_style()
        self._notify_preview()
        self.hint.setText(
            '已为全部类别恢复独立默认配色；点击“确认”保存，取消可撤销。')

    def applyGeometryToAll(self):
        """Share geometry/text layout settings without changing class colors."""
        if not self.styles:
            return
        shared_values = {
            'border_width': self.border_width_spin.value(),
            'text_size': self.text_size_spin.value(),
            'text_position': self.text_position_combo.currentData(),
        }
        for class_id, style in tuple(self.styles.items()):
            updated = normalize_class_style(style)
            updated.update(shared_values)
            self.styles[class_id] = updated
        self._load_selected_style()
        self._notify_preview()
        self.hint.setText(
            '已将边框粗细、文字大小和位置应用到全部类别；颜色保持独立。')

    def resetCurrentStyle(self):
        """Compatibility alias: reset now intentionally applies to all classes."""
        self.resetAllStyles()

    def confirmChanges(self):
        self._persist()
        self._accepted = True
        self.configChanged.emit(dict(self.names), dict(self.styles))
        self.close()

    def cancelChanges(self):
        self.close()

    def addItem(self):
        name, ok = QInputDialog.getText(self, '新增类别', '类别名称：')
        name = name.strip()
        if not ok or not name:
            return
        if name in self.names.values():
            QMessageBox.warning(self, '名称重复', '该类别名称已经存在。')
            return
        class_id = max(self.names, default=-1) + 1
        self.names[class_id] = name
        self.styles[class_id] = default_class_style(class_id)
        self._rebuild_list(class_id)
        self._notify_preview()

    def modifyItem(self):
        class_id = self._current_class_id()
        if class_id is None:
            return
        name, ok = QInputDialog.getText(
            self, '重命名类别', '类别名称：',
            text=self.names[class_id])
        name = name.strip()
        if not ok or not name or name == self.names[class_id]:
            return
        if name in self.names.values():
            QMessageBox.warning(self, '名称重复', '该类别名称已经存在。')
            return
        self.names[class_id] = name
        self._rebuild_list(class_id)
        self._notify_preview()

    def deleteItem(self):
        class_id = self._current_class_id()
        if class_id is None:
            return
        class_ids = sorted(self.names)
        if len(class_ids) == 1:
            QMessageBox.warning(self, '无法删除', '至少需要保留一个类别。')
            return
        if class_id != class_ids[-1]:
            QMessageBox.warning(self, '无法删除', '为避免类别 ID 错位，只能删除最后一个类别。')
            return
        if self._class_is_used(class_id):
            QMessageBox.warning(self, '无法删除', '当前标注数据仍在使用该类别。')
            return
        reply = QMessageBox.question(
            self, '删除类别', f'确定删除“{self.names[class_id]}”吗？',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self.names.pop(class_id, None)
        self.styles.pop(class_id, None)
        self._rebuild_list(max(self.names))
        self._notify_preview()

    def _class_is_used(self, class_id):
        if self.main_window is not None and self.main_window.img_is_load:
            if any(int(label[0]) == class_id
                   for label in self.main_window.img.label_save):
                return True
        for label_path in self.save_path.glob('*.txt'):
            try:
                with open(label_path, encoding='utf-8') as file:
                    for line in file:
                        fields = line.split()
                        if fields and int(float(fields[0])) == class_id:
                            return True
            except (OSError, ValueError, OverflowError):
                continue
        return False

    def closeEvent(self, event):
        if not self._accepted:
            self.configChanged.emit(
                deepcopy(self._original_names),
                deepcopy(self._original_styles),
            )
        super().closeEvent(event)

    def nativeEvent(self, event_type, message):
        """Restore native edge/corner resizing for the frameless window."""
        if sys.platform.startswith('win') and not self.isMaximized():
            from ctypes import wintypes

            native_message = wintypes.MSG.from_address(int(message))
            if native_message.message == 0x0084:  # WM_NCHITTEST
                frame = self.frameGeometry()
                cursor = QCursor.pos()
                margin = 7
                on_left = frame.left() <= cursor.x() <= frame.left() + margin
                on_right = frame.right() - margin <= cursor.x() <= frame.right()
                on_top = frame.top() <= cursor.y() <= frame.top() + margin
                on_bottom = frame.bottom() - margin <= cursor.y() <= frame.bottom()

                if on_top and on_left:
                    return True, 13  # HTTOPLEFT
                if on_top and on_right:
                    return True, 14  # HTTOPRIGHT
                if on_bottom and on_left:
                    return True, 16  # HTBOTTOMLEFT
                if on_bottom and on_right:
                    return True, 17  # HTBOTTOMRIGHT
                if on_left:
                    return True, 10  # HTLEFT
                if on_right:
                    return True, 11  # HTRIGHT
                if on_top:
                    return True, 12  # HTTOP
                if on_bottom:
                    return True, 15  # HTBOTTOM
        return super().nativeEvent(event_type, message)
