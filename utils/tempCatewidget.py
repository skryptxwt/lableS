import logging
import yaml
from PyQt5 import uic
from PyQt5.QtCore import QRectF, QSize, Qt, QTimer
from PyQt5.QtGui import QColor, QIcon, QKeySequence, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (QAbstractItemView, QHBoxLayout, QLabel,
                             QListWidgetItem, QPushButton, QShortcut, QWidget)

from .class_styles import mapping_value, normalize_class_style
from .common_fun import CONFIG_PATH, root
from .industrial_theme import INDUSTRIAL_QSS


LOGGER = logging.getLogger('labels')


class CategoryApp(QWidget):
    def __init__(self, main_window, widget):
        # Keep the picker inside the existing application window.  A native
        # Qt.Popup starts a second Windows focus/activation loop; when it is
        # created from a canvas double-click that loop can deadlock with the
        # trailing mouse release.  A child overlay has the same appearance and
        # interaction without creating another native window.
        host = getattr(main_window, 'window_shell', main_window)
        super().__init__(host)
        self.label = None
        self.main_window = main_window
        self.listWidget = uic.loadUi(str(root / "qt_ui_file/temp_widget.ui"), self).clsShow
        self.categories = None
        self.category_entries = []
        self.index = None
        self.cls_index = None
        self.setWindowFlags(Qt.Widget)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName('categoryPopup')
        self._dismiss_pending = False

        popup_layout = self.layout()
        popup_layout.removeWidget(self.listWidget)
        popup_layout.setContentsMargins(10, 9, 10, 10)
        popup_layout.setHorizontalSpacing(0)
        popup_layout.setVerticalSpacing(7)

        self.header = QWidget(self)
        self.header.setObjectName('categoryPopupHeader')
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(4, 0, 2, 0)
        header_layout.setSpacing(8)
        self.title_label = QLabel('切换类别', self.header)
        self.title_label.setObjectName('categoryPopupTitle')
        self.current_badge = QLabel('', self.header)
        self.current_badge.setObjectName('categoryPopupCurrent')
        self.close_button = QPushButton('×', self.header)
        self.close_button.setObjectName('categoryPopupClose')
        self.close_button.setFixedSize(24, 24)
        self.close_button.setToolTip('关闭')
        self.close_button.clicked.connect(self.dismiss)
        self.escape_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.escape_shortcut.setContext(Qt.WidgetWithChildrenShortcut)
        self.escape_shortcut.activated.connect(self.dismiss)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.current_badge)
        header_layout.addWidget(self.close_button)
        popup_layout.addWidget(self.header, 0, 0)
        popup_layout.addWidget(self.listWidget, 1, 0)
        popup_layout.setRowStretch(1, 1)

        self.listWidget.setObjectName('categoryPopupList')
        # Discard the legacy inline stylesheet embedded in temp_widget.ui so
        # the popup-specific industrial theme can style the list consistently.
        self.listWidget.setStyleSheet('')
        self.listWidget.setMinimumSize(0, 0)
        self.listWidget.setMaximumSize(16777215, 16777215)
        self.listWidget.setIconSize(QSize(12, 12))
        self.listWidget.setSpacing(2)
        self.listWidget.setUniformItemSizes(True)
        self.listWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.listWidget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.listWidget.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.listWidget.itemClicked.connect(self.changeLabel)
        self.init()
        self.resize(224, 360)
        self.setMinimumSize(196, 220)
        self.setMaximumSize(300, 520)
        self.setStyleSheet(INDUSTRIAL_QSS)

    def init(self):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
        names = getattr(self.main_window, 'names', None) or data['names']
        if isinstance(names, dict):
            self.category_entries = sorted(
                ((int(class_id), str(name)) for class_id, name in names.items()),
                key=lambda entry: entry[0])
        else:
            self.category_entries = [
                (class_id, str(name)) for class_id, name in enumerate(names)]
        self.categories = [name for _class_id, name in self.category_entries]

    def _category_icon(self, class_id):
        styles = getattr(self.main_window, 'class_styles', None)
        colors = getattr(self.main_window, 'colors', None)
        style = normalize_class_style(
            mapping_value(styles, class_id), mapping_value(colors, class_id))
        color = QColor(*style['border'])
        color.setAlpha(255)
        pixmap = QPixmap(12, 12)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(1, 1, 10, 10)
        painter.end()
        return QIcon(pixmap)

    def set_rect_cls(self, cls_index=None, rect_index=None):
        self.index = rect_index
        self.cls_index = cls_index if rect_index is not None else self.main_window.cls
        self.listWidget.clear()
        selected_class = self.main_window.cls if cls_index is None else int(cls_index)
        selected_row = 0
        selected_name = str(selected_class)
        for row, (class_id, name) in enumerate(self.category_entries):
            item = QListWidgetItem(self._category_icon(class_id), name)
            item.setData(Qt.UserRole, class_id)
            item.setToolTip(f'类别 {class_id} · {name}')
            self.listWidget.addItem(item)
            if class_id == selected_class:
                selected_row = row
                selected_name = name
        self.listWidget.setCurrentRow(selected_row)
        current_item = self.listWidget.item(selected_row)
        if current_item is not None:
            self.listWidget.scrollToItem(
                current_item, QAbstractItemView.PositionAtCenter)
        self.current_badge.setText(f'当前  {selected_name}')
        self.main_window.cls = selected_class

    def clear(self):
        self.listWidget.clear()

    def changeLabel(self, item):
        """更改标签内容为点击的类别索引"""
        index = self.main_window.is_choose_rect_index

        image = getattr(self.main_window, 'img', None)
        label_save = getattr(image, 'label_save', ())
        basedata = getattr(image, 'basedata', ())
        if (image is None or index is None or index < 0
                or index >= len(label_save)
                or index >= len(basedata)):
            status_bar = getattr(self.main_window, 'statusBar', None)
            if callable(status_bar):
                status_bar().showMessage(
                    'CATEGORY  |  当前没有可调整类别的标注对象', 4000)
            self.dismiss(deferred=True)
            return
        try:
            class_data = item.data(Qt.UserRole)
            if class_data is None:
                raise ValueError('类别项缺少类别 ID')
            self.cls_index = int(class_data)
            class_name = mapping_value(
                self.main_window.names, self.cls_index) or str(self.cls_index)

            self.main_window.img.is_trans = False
            new_label = list(self.main_window.img.label_save[index])
            new_label[0] = self.cls_index
            self.main_window.img.change(index, new_label)
            self.main_window._save_annotations('CATEGORY CHANGE')

            self.main_window.cls = self.cls_index
            self.main_window.boxShowWidget.set_rect_box(index, class_name)
            self.main_window.categoryShowWidget.set_rect_cls(self.cls_index)
        except Exception:
            LOGGER.exception(
                'Category change failed | index=%s class=%s task=%s',
                index, getattr(self, 'cls_index', None),
                getattr(self.main_window, 'annotation_task', None))
            self.main_window.statusBar().showMessage(
                'CATEGORY CHANGE RECOVERED  |  修改失败，错误已写入日志',
                8000)
        finally:
            self.main_window.change_label_name = False
            # itemClicked is still executing here.  Defer hiding until Qt has
            # unwound the QListWidget signal stack; closing or deleting the
            # active event receiver here can access freed native state on
            # Windows.
            self.dismiss(deferred=True)

    def show_at(self, global_position):
        """Show beside the annotation as a clipped in-window overlay."""
        self._dismiss_pending = False
        host = self.parentWidget()
        position = (host.mapFromGlobal(global_position)
                    if host is not None else global_position)
        x = position.x() + 12
        y = position.y() + 12
        if host is not None:
            available = host.rect()
            x = min(max(x, available.left() + 8),
                    max(available.left() + 8,
                        available.right() - self.width() - 8))
            y = min(max(y, available.top() + 8),
                    max(available.top() + 8,
                        available.bottom() - self.height() - 8))
        self.move(x, y)
        LOGGER.info(
            'Category popup show | index=%s class=%s position=(%s, %s)',
            self.index, self.cls_index, x, y)
        # This is a child overlay, so show/raise never enters the Windows
        # top-level popup activation loop.
        self.show()
        self.raise_()
        QTimer.singleShot(0, self._focus_category_list)

    def _focus_category_list(self):
        if self.isVisible():
            self.listWidget.setFocus(Qt.OtherFocusReason)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.dismiss()
            return
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            item = self.listWidget.currentItem()
            if item is not None:
                self.changeLabel(item)
            return
        super().keyPressEvent(event)

    def dismiss(self, deferred=False):
        """Hide this reusable overlay outside the current item callback."""
        if deferred:
            if self._dismiss_pending:
                return
            self._dismiss_pending = True
            QTimer.singleShot(0, self.dismiss)
            return
        self._dismiss_pending = False
        LOGGER.info(
            'Category popup hide | index=%s class=%s',
            self.index, self.cls_index)
        self.main_window.change_label_name = False
        if getattr(self.main_window, 'temp_widget', None) is self:
            self.main_window.temp_widget = None
        self.hide()

    def closeEvent(self, event):
        LOGGER.info(
            'Category popup close | index=%s class=%s',
            self.index, self.cls_index)
        self.main_window.change_label_name = False
        if getattr(self.main_window, 'temp_widget', None) is self:
            self.main_window.temp_widget = None
        super().closeEvent(event)

    def focusOutEvent(self, event):
        # The canvas event filter, close button and Esc own dismissal.  Do not
        # close from focus callbacks: focus may legitimately move between the
        # list and close button inside this overlay.
        super().focusOutEvent(event)

    def paintEvent(self, event):
        # A translucent top-level QWidget is not guaranteed to paint its QSS
        # background on every Windows/Qt combination. Draw the rounded surface
        # explicitly so the header and list read as one floating panel.
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(QColor(117, 137, 150, 185), 1))
        painter.setBrush(QColor(247, 250, 252, 248))
        painter.drawRoundedRect(
            QRectF(self.rect()).adjusted(.5, .5, -.5, -.5), 10, 10)
        painter.end()
        super().paintEvent(event)
