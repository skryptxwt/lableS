from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QListWidgetItem, QPushButton,
                             QWidget)

from .ui_icons import toolbar_icon


class _ObjectRow(QWidget):
    """One annotation row with a contextual delete action at the right."""

    def __init__(self, owner, index, text):
        super().__init__(owner.listWidget)
        self.owner = owner
        self.index = index
        self.setObjectName('annotationObjectRow')
        layout = QHBoxLayout(self)
        layout.setContentsMargins(9, 0, 4, 0)
        layout.setSpacing(5)

        self.caption = QLabel(text, self)
        self.caption.setObjectName('annotationObjectCaption')
        self.caption.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.delete_button = QPushButton('', self)
        self.delete_button.setObjectName('annotationRowDelete')
        self.delete_button.setFixedSize(22, 22)
        self.delete_button.setIcon(
            toolbar_icon('delete', size=16, color='#78868f'))
        self.delete_button.setIconSize(QSize(12, 12))
        self.delete_button.setToolTip(f'删除标注对象 {index + 1}')
        self.delete_button.hide()
        self.delete_button.clicked.connect(
            lambda _checked=False: self.owner.delete_row(self.index))

        layout.addWidget(self.caption, 1)
        layout.addWidget(self.delete_button, 0, Qt.AlignVCenter)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.owner.select_row(self.index)
            event.accept()
            return
        super().mousePressEvent(event)


class LabelApp(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.listWidget = self.main_window.ui.labelShow
        self.categories = None
        self.index = None
        self._row_widgets = {}
        self.listWidget.itemClicked.connect(self.changeLabel)
        self.listWidget.currentRowChanged.connect(
            self._update_delete_visibility)
        self.listWidget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def _class_name(self, class_id):
        names = self.main_window.names or {}
        class_id = int(class_id)
        return str(names.get(class_id, class_id))

    def set_rect_box(self, box_cls_index=None, is_choose=None):
        if is_choose is not None:
            try:
                selected = int(box_cls_index)
            except (TypeError, ValueError, OverflowError):
                return
            self.set_rect_box(selected)
            return

        image = getattr(self.main_window, 'img', None)
        labels = getattr(image, 'label_save', ())
        selected = None
        if box_cls_index is not None:
            try:
                candidate = int(box_cls_index)
                if 0 <= candidate < len(labels):
                    selected = candidate
            except (TypeError, ValueError, OverflowError):
                pass

        self.listWidget.blockSignals(True)
        try:
            self.listWidget.clear()
            self._row_widgets = {}
            for index, label in enumerate(labels):
                item = QListWidgetItem(self.listWidget)
                item.setSizeHint(QSize(0, 28))
                row = _ObjectRow(
                    self, index,
                    f'{index + 1} : {self._class_name(label[0])}')
                self.listWidget.setItemWidget(item, row)
                self._row_widgets[index] = row
            self.listWidget.setCurrentRow(
                selected if selected is not None else -1)
        finally:
            self.listWidget.blockSignals(False)
        self._update_delete_visibility(
            selected if selected is not None else -1)

    def clear(self):
        self.set_rect_box()
        self.listWidget.clearSelection()
        self.listWidget.setCurrentRow(-1)
        self._update_delete_visibility(-1)

    def _update_delete_visibility(self, current_row):
        for index, row in self._row_widgets.items():
            row.delete_button.setVisible(index == current_row)

    def select_row(self, index):
        item = self.listWidget.item(index)
        if item is None:
            return
        self.listWidget.setCurrentRow(index)
        self.changeLabel(item)

    def delete_row(self, index):
        image = getattr(self.main_window, 'img', None)
        if image is None or not 0 <= index < len(image.label_save):
            return
        self.listWidget.setCurrentRow(index)
        self.main_window.is_choose_rect = True
        self.main_window.is_choose_rect_index = index
        self.main_window.deleteBox_(index)

    def changeLabel(self, item):
        """Select the annotation represented by the clicked row."""
        current_index = self.listWidget.row(item)
        if current_index < 0:
            return
        labels = self.main_window.img.label_save
        if current_index >= len(labels):
            return
        self.main_window.rect_save_current = [
            current_index, -1, labels[current_index]]
        self.main_window.img.only_index = True
        self.main_window.is_choose_rect = True
        self.main_window.is_hover_move_allow = True
        self.main_window.is_choose_rect_index = current_index
        self.main_window.img.is_trans = False

        self.main_window.move_xy(index=current_index)
        self.main_window.categoryShowWidget.set_rect_cls(
            labels[current_index][0], current_index)
        self.listWidget.setCurrentRow(current_index)
        self._update_delete_visibility(current_index)
        self.index = current_index
