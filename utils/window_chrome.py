from PyQt5.QtCore import (QEasingCurve, QEvent, QObject, QPoint,
                          QPropertyAnimation, QRectF, Qt, QTimer, pyqtSignal)
from PyQt5.QtGui import (QColor, QLinearGradient, QPainter, QPainterPath,
                         QPen, QPixmap)
from PyQt5.QtWidgets import (QAbstractButton, QGraphicsOpacityEffect,
                             QHBoxLayout, QLabel, QProxyStyle, QSizePolicy,
                             QSlider, QSplitter, QSplitterHandle, QStyle,
                             QVBoxLayout, QWidget)


class HoverSlider(QWidget):
    """Compact value display that expands its slider only while hovered."""

    valueChanged = pyqtSignal(int)
    editingFinished = pyqtSignal()

    def __init__(self, caption, minimum, maximum, value, formatter=str, parent=None):
        super().__init__(parent)
        self.formatter = formatter
        self.setObjectName('hoverSliderControl')
        self.setFixedHeight(24)
        self.setFixedWidth(184)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(7, 0, 7, 0)
        layout.setSpacing(4)
        self.caption_label = QLabel(caption, self)
        self.caption_label.setObjectName('hoverSliderCaption')

        # The slot always keeps its width, so revealing the slider never
        # pushes the surrounding title-bar controls sideways.
        self.slider_slot = QWidget(self)
        self.slider_slot.setFixedWidth(90)
        slot_layout = QHBoxLayout(self.slider_slot)
        slot_layout.setContentsMargins(0, 0, 0, 0)
        self.slider = QSlider(Qt.Horizontal, self.slider_slot)
        self.slider.setProperty('compactHover', True)
        self.slider.setRange(minimum, maximum)
        self.slider.setFixedWidth(90)
        self.slider.setTracking(True)
        slot_layout.addWidget(self.slider)

        self.slider_opacity = QGraphicsOpacityEffect(self.slider)
        self.slider_opacity.setOpacity(0.0)
        self.slider.setGraphicsEffect(self.slider_opacity)
        self.slider.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.slider_animation = QPropertyAnimation(
            self.slider_opacity, b'opacity', self)
        self.slider_animation.setDuration(140)
        self.slider_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.slider_animation.finished.connect(self._animation_finished)

        self.value_label = QLabel(self)
        self.value_label.setObjectName('hoverSliderValue')
        self.value_label.setMinimumWidth(32)
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.caption_label)
        layout.addWidget(self.slider_slot)
        layout.addWidget(self.value_label)

        for widget in (
                self, self.caption_label, self.slider_slot,
                self.slider, self.value_label):
            widget.setMouseTracking(True)
            widget.installEventFilter(self)

        self.slider.valueChanged.connect(self._value_changed)
        self.slider.sliderReleased.connect(self.editingFinished)
        self.setValue(value)

    def value(self):
        return self.slider.value()

    def setValue(self, value):
        self.slider.setValue(value)
        self.value_label.setText(self.formatter(self.slider.value()))

    def _value_changed(self, value):
        self.value_label.setText(self.formatter(value))
        self.valueChanged.emit(value)

    def _expand(self):
        self.slider.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self._animate_slider(1.0)

    def _collapse_if_idle(self):
        widgets = (
            self, self.caption_label, self.slider_slot,
            self.slider, self.value_label,
        )
        if not any(widget.underMouse() for widget in widgets):
            self._animate_slider(0.0)

    def _animate_slider(self, opacity):
        if abs(self.slider_opacity.opacity() - opacity) < 0.01:
            return
        self.slider_animation.stop()
        self.slider_animation.setStartValue(self.slider_opacity.opacity())
        self.slider_animation.setEndValue(opacity)
        self.slider_animation.start()

    def _animation_finished(self):
        if self.slider_opacity.opacity() < 0.01:
            self.slider.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Enter:
            self._expand()
        elif event.type() == QEvent.Leave:
            QTimer.singleShot(140, self._collapse_if_idle)
        return super().eventFilter(watched, event)


class HoverSliderPopup(QWidget):
    """Slider panel shown below a title-bar action on hover."""

    valueChanged = pyqtSignal(int)
    editingFinished = pyqtSignal()

    def __init__(self, caption, minimum, maximum, value,
                 formatter=str, parent=None):
        super().__init__(parent)
        self.formatter = formatter
        self.anchor = None
        self.setObjectName('hoverSliderPopup')
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedSize(190, 52)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 7)
        layout.setSpacing(3)

        header = QWidget(self)
        header.setObjectName('sliderPopupHeader')
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        self.caption_label = QLabel(caption, header)
        self.caption_label.setObjectName('sliderPopupCaption')
        self.value_label = QLabel(header)
        self.value_label.setObjectName('sliderPopupValue')
        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header_layout.addWidget(self.caption_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.value_label)

        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setProperty('popupSlider', True)
        self.slider.setRange(minimum, maximum)
        self.slider.setTracking(True)
        layout.addWidget(header)
        layout.addWidget(self.slider)

        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.setInterval(180)
        self.hide_timer.timeout.connect(self._hide_if_idle)
        self.wheel_finish_timer = QTimer(self)
        self.wheel_finish_timer.setSingleShot(True)
        self.wheel_finish_timer.setInterval(260)
        self.wheel_finish_timer.timeout.connect(self.editingFinished)

        for widget in (header, self.caption_label, self.value_label, self.slider):
            widget.setMouseTracking(True)
            widget.installEventFilter(self)

        self.slider.valueChanged.connect(self._value_changed)
        self.slider.sliderReleased.connect(self.editingFinished)
        self.setValue(value)
        self.hide()

    def attach_to(self, anchor):
        self.anchor = anchor
        anchor.setMouseTracking(True)
        anchor.installEventFilter(self)

    def value(self):
        return self.slider.value()

    def setValue(self, value):
        self.slider.setValue(value)
        self.value_label.setText(self.formatter(self.slider.value()))

    def _value_changed(self, value):
        self.value_label.setText(self.formatter(value))
        self.valueChanged.emit(value)

    def _show_below_anchor(self):
        if self.anchor is None:
            return
        parent = self.parentWidget()
        position = self.anchor.mapTo(
            parent, QPoint(0, self.anchor.height() + 5))
        maximum_x = max(0, parent.width() - self.width() - 6)
        position.setX(max(6, min(position.x(), maximum_x)))
        self.move(position)
        self.show()
        self.raise_()

    def _schedule_hide(self):
        self.hide_timer.start()

    def _hide_if_idle(self):
        widgets = [self, self.anchor, *self.findChildren(QWidget)]
        if not any(widget is not None and widget.underMouse()
                   for widget in widgets):
            self.hide()

    def _adjust_from_wheel(self, event):
        delta = event.angleDelta().y()
        if not delta:
            return False
        direction = 1 if delta > 0 else -1
        steps = max(1, abs(delta) // 120)
        self.slider.setValue(
            self.slider.value() + direction * steps)
        self.wheel_finish_timer.start()
        event.accept()
        return True

    def enterEvent(self, event):
        self.hide_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._schedule_hide()
        super().leaveEvent(event)

    def wheelEvent(self, event):
        if not self._adjust_from_wheel(event):
            super().wheelEvent(event)

    def eventFilter(self, watched, event):
        if watched is self.anchor:
            if event.type() == QEvent.Enter:
                self.hide_timer.stop()
                self._show_below_anchor()
            elif event.type() == QEvent.Leave:
                self._schedule_hide()
            elif event.type() == QEvent.MouseButtonPress:
                self.hide()
            elif event.type() == QEvent.Wheel:
                self._show_below_anchor()
                return self._adjust_from_wheel(event)
        else:
            if event.type() == QEvent.Enter:
                self.hide_timer.stop()
            elif event.type() == QEvent.Leave:
                self._schedule_hide()
            elif event.type() == QEvent.Wheel:
                return self._adjust_from_wheel(event)
        return super().eventFilter(watched, event)


class BackgroundWidget(QWidget):
    """Window shell that renders a cover-scaled user background image."""

    backgroundChanged = pyqtSignal()
    DEFAULT_BACKGROUND_COLOR = QColor('#e8ecef')

    def __init__(self, parent=None):
        super().__init__(parent)
        self._background = QPixmap()
        self._background_opacity = 0.65
        self.setObjectName('windowShell')

    def set_background_image(self, path=None):
        pixmap = QPixmap(str(path)) if path else QPixmap()
        if path and pixmap.isNull():
            return False
        self._background = pixmap
        self.update()
        self.backgroundChanged.emit()
        return True

    def set_background_opacity(self, opacity):
        self._background_opacity = max(0.0, min(float(opacity), 1.0))
        self.update()
        self.backgroundChanged.emit()

    def draw_background_for(self, painter, target):
        """Draw the shell background aligned to a descendant widget."""
        painter.fillRect(target.rect(), self.DEFAULT_BACKGROUND_COLOR)
        if self._background.isNull():
            return
        scaled = self._background.scaled(
            self.size(), Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation)
        image_x = (self.width() - scaled.width()) // 2
        image_y = (self.height() - scaled.height()) // 2
        target_origin = target.mapTo(self, QPoint(0, 0))
        painter.setOpacity(self._background_opacity)
        painter.drawPixmap(
            image_x - target_origin.x(),
            image_y - target_origin.y(),
            scaled)
        painter.setOpacity(1.0)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.DEFAULT_BACKGROUND_COLOR)
        if not self._background.isNull():
            scaled = self._background.scaled(
                self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.setOpacity(self._background_opacity)
            painter.drawPixmap(x, y, scaled)
            painter.setOpacity(1.0)


class BackgroundGlassPanel(QWidget):
    """Panel that redraws the window backdrop before applying a glass tint."""

    def __init__(self, background_host, parent=None, tint=None):
        super().__init__(parent)
        self.background_host = background_host
        self.tint = QColor(tint) if tint is not None else QColor(247, 249, 251, 34)
        self.setObjectName('rightSectionPanel')
        self.setAutoFillBackground(False)
        self.background_host.backgroundChanged.connect(self.update)

    def paintEvent(self, event):
        painter = QPainter(self)
        self.background_host.draw_background_for(painter, self)
        painter.fillRect(self.rect(), self.tint)
        if self.property('panelFrame'):
            frame_pen = QPen(QColor(105, 126, 139, 135))
            frame_pen.setWidthF(1.0)
            painter.setPen(frame_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(QRectF(self.rect()).adjusted(.5, .5, -.5, -.5))
        painter.end()


class BackgroundViewportBinder(QObject):
    """Paint the aligned window background underneath an item view."""

    def __init__(self, background_host, viewport, parent=None):
        super().__init__(parent or viewport)
        self.background_host = background_host
        self.viewport = viewport
        self.viewport.setObjectName('backgroundListViewport')
        self.viewport.setAutoFillBackground(False)
        self.viewport.setAttribute(Qt.WA_TranslucentBackground, True)
        self.viewport.setStyleSheet('background: transparent; border: 0;')
        self.viewport.installEventFilter(self)
        self.background_host.backgroundChanged.connect(self.refresh)
        QTimer.singleShot(0, self.refresh)

    def refresh(self):
        self.viewport.update()

    def eventFilter(self, watched, event):
        if watched is self.viewport:
            if event.type() == QEvent.Paint:
                painter = QPainter(self.viewport)
                self.background_host.draw_background_for(
                    painter, self.viewport)
                painter.fillRect(
                    self.viewport.rect(), QColor(247, 249, 251, 38))
                painter.end()
            elif event.type() in (QEvent.Resize, QEvent.Show):
                QTimer.singleShot(0, self.refresh)
        return super().eventFilter(watched, event)


class IndustrialSplitterHandle(QSplitterHandle):
    """Large, visible hit target for resizing stacked inspector panels."""

    def __init__(self, orientation, parent, background_host=None):
        super().__init__(orientation, parent)
        self.background_host = background_host
        self.hovered = False
        self.setCursor(
            Qt.SplitVCursor if orientation == Qt.Vertical else Qt.SplitHCursor)
        self.setMouseTracking(True)

    def enterEvent(self, event):
        self.hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered = False
        self.update()
        super().leaveEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.splitter().setSizes([1, 1])
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        if self.background_host is not None:
            self.background_host.draw_background_for(painter, self)
            painter.fillRect(
                self.rect(), QColor(247, 249, 251, 42))
        else:
            painter.fillRect(self.rect(), QColor('#e1e7eb'))
        if self.hovered:
            painter.fillRect(self.rect(), QColor(37, 155, 200, 24))

        # Keep a continuous divider visible over both light and image-backed
        # panels.  The wider handle remains an easy resize target, while this
        # slim line provides the visual boundary that the old short grip did
        # not communicate on its own.
        splitter_name = self.splitter().objectName()
        is_queue_boundary = splitter_name == 'workspaceSplitter'
        divider_thickness = 3 if is_queue_boundary else 1
        divider_color = (QColor(37, 155, 200, 225) if self.hovered
                         else QColor(53, 73, 84, 245)
                         if is_queue_boundary
                         else QColor(101, 122, 134, 145))
        if self.orientation() == Qt.Vertical:
            divider = QRectF(
                0, (self.height() - divider_thickness) / 2,
                self.width(), divider_thickness)
        else:
            # The queue resize handle deliberately remains wide and easy to
            # grab, but its visible divider belongs against the queue panel.
            # Drawing it in the middle of the handle left a conspicuous gap
            # beside the queue heading and content.
            divider_x = (0 if is_queue_boundary
                         else (self.width() - divider_thickness) / 2)
            divider = QRectF(
                divider_x, 0,
                divider_thickness, self.height())
        painter.fillRect(divider, divider_color)

        if self.orientation() == Qt.Vertical:
            grip_width = min(38, max(18, self.width() - 12))
            grip = QRectF(
                (self.width() - grip_width) / 2,
                (self.height() - 3) / 2,
                grip_width,
                3)
        else:
            grip_height = min(38, max(18, self.height() - 12))
            grip_x = (0 if is_queue_boundary
                      else (self.width() - 3) / 2)
            grip = QRectF(
                grip_x,
                (self.height() - grip_height) / 2,
                3,
                grip_height)
        painter.setPen(Qt.NoPen)
        painter.setBrush(
            QColor('#249bc8') if self.hovered else QColor('#758792'))
        painter.drawRoundedRect(grip, 1.5, 1.5)


class AdjustableSplitter(QSplitter):
    def __init__(self, orientation, parent=None, background_host=None):
        super().__init__(orientation, parent)
        self.background_host = background_host
        self.setHandleWidth(14)
        self.setOpaqueResize(True)

    def createHandle(self):
        return IndustrialSplitterHandle(
            self.orientation(), self, self.background_host)


class WindowControlButton(QAbstractButton):
    """Frameless-window control whose glyph is drawn at runtime."""

    def __init__(self, control, parent=None):
        super().__init__(parent)
        self.control = control
        self.hovered = False
        self.setFixedSize(40, 34)
        self.setFocusPolicy(Qt.NoFocus)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip({
            'minimize': '最小化', 'maximize': '最大化 / 还原', 'close': '关闭'
        }[control])

    def enterEvent(self, event):
        self.hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        if self.hovered:
            background = QColor('#d55252') if self.control == 'close' else QColor('#e4e9ed')
            painter.fillRect(self.rect(), background)

        color = QColor('#ffffff') if self.hovered and self.control == 'close' else QColor('#46515c')
        pen = QPen(color, 1.35)
        pen.setCapStyle(Qt.SquareCap)
        pen.setJoinStyle(Qt.MiterJoin)
        painter.setPen(pen)

        center_x = self.width() / 2
        center_y = self.height() / 2
        if self.control == 'minimize':
            painter.drawLine(QPoint(int(center_x - 4), int(center_y + 3)),
                             QPoint(int(center_x + 4), int(center_y + 3)))
        elif self.control == 'close':
            painter.drawLine(QPoint(int(center_x - 4), int(center_y - 4)),
                             QPoint(int(center_x + 4), int(center_y + 4)))
            painter.drawLine(QPoint(int(center_x + 4), int(center_y - 4)),
                             QPoint(int(center_x - 4), int(center_y + 4)))
        elif self.window().isMaximized():
            painter.drawRect(QRectF(center_x - 3, center_y - 4, 8, 7))
            painter.drawLine(QPoint(int(center_x - 5), int(center_y - 2)),
                             QPoint(int(center_x - 5), int(center_y + 4)))
            painter.drawLine(QPoint(int(center_x - 5), int(center_y + 4)),
                             QPoint(int(center_x + 1), int(center_y + 4)))
        else:
            painter.drawRect(QRectF(center_x - 4, center_y - 4, 8, 8))


class TitleBar(QWidget):
    def __init__(self, window):
        super().__init__(window)
        self.host_window = window
        self.drag_offset = None
        self.setObjectName('titleBar')
        self.setFixedHeight(36)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 0, 0, 0)
        self.layout.setSpacing(0)

        self.title_label = QLabel('LabelS')
        self.title_label.setObjectName('windowTitleLabel')
        self.title_label.setMinimumWidth(48)
        self.title_label.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.layout.addWidget(self.title_label)
        self.layout.addSpacing(18)

        self.toolbar = QWidget(self)
        self.toolbar.setObjectName('titleToolbar')
        self.toolbar_layout = QHBoxLayout(self.toolbar)
        self.toolbar_layout.setContentsMargins(0, 0, 0, 0)
        self.toolbar_layout.setSpacing(5)
        self.layout.addWidget(self.toolbar, 0, Qt.AlignVCenter)
        self.layout.addStretch(1)

        self.minimize_button = WindowControlButton('minimize', self)
        self.maximize_button = WindowControlButton('maximize', self)
        self.close_button = WindowControlButton('close', self)
        self.minimize_button.clicked.connect(window.showMinimized)
        self.maximize_button.clicked.connect(self.toggle_maximize)
        self.close_button.clicked.connect(window.close)
        self.layout.addWidget(self.minimize_button)
        self.layout.addWidget(self.maximize_button)
        self.layout.addWidget(self.close_button)

    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor('#dfe6e9'))
        gradient.setColorAt(1.0, QColor('#d2dce1'))
        painter.fillRect(self.rect(), gradient)
        painter.setPen(QColor('#aebbc2'))
        painter.drawLine(0, self.height() - 1,
                         self.width(), self.height() - 1)
        super().paintEvent(event)

    def add_toolbar_widgets(self, *widgets):
        """Place primary workspace controls in the native title-bar row."""
        for widget in widgets:
            self.toolbar_layout.addWidget(widget, 0, Qt.AlignVCenter)

    def toggle_maximize(self):
        if self.host_window.isMaximized():
            self.host_window.showNormal()
        else:
            self.host_window.showMaximized()
        self.maximize_button.update()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle_maximize()
            event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_offset = event.globalPos() - self.host_window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.drag_offset is not None:
            if self.host_window.isMaximized():
                ratio = event.pos().x() / max(1, self.width())
                self.host_window.showNormal()
                self.drag_offset = QPoint(int(self.host_window.width() * ratio), self.height() // 2)
            self.host_window.move(event.globalPos() - self.drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_offset = None
        super().mouseReleaseEvent(event)


class IndustrialProxyStyle(QProxyStyle):
    """Draw a consistent checkbox icon instead of using the platform glyph."""

    def pixelMetric(self, metric, option=None, widget=None):
        if metric in (QStyle.PM_IndicatorWidth, QStyle.PM_IndicatorHeight):
            return 14
        return super().pixelMetric(metric, option, widget)

    def drawPrimitive(self, element, option, painter, widget=None):
        if element != QStyle.PE_IndicatorCheckBox:
            return super().drawPrimitive(element, option, painter, widget)

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = QRectF(option.rect).adjusted(1, 1, -1, -1)
        enabled = bool(option.state & QStyle.State_Enabled)
        checked = bool(option.state & QStyle.State_On)
        hovered = bool(option.state & QStyle.State_MouseOver)

        if checked:
            fill = QColor('#159ec5') if enabled else QColor('#71818a')
            border = QColor('#70d5ee') if hovered else QColor('#38b9dc')
        else:
            fill = QColor('#ffffff') if enabled else QColor('#e2e7eb')
            border = QColor('#71808c') if hovered else QColor('#9aa6af')
        painter.setPen(QPen(border, 1))
        painter.setBrush(fill)
        painter.drawRoundedRect(rect, 2.5, 2.5)

        if checked:
            pen = QPen(QColor('#ffffff'), 2.0)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            path = QPainterPath()
            path.moveTo(rect.left() + 3.2, rect.center().y())
            path.lineTo(rect.left() + 6.2, rect.bottom() - 3.3)
            path.lineTo(rect.right() - 2.8, rect.top() + 3.5)
            painter.drawPath(path)

        painter.restore()
