from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget


class LabelApp(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.listWidget = self.main_window.ui.labelShow
        self.categories = None
        self.index = None
        self.listWidget.itemClicked.connect(self.changeLabel)
        self.listWidget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def set_rect_box(self, box_cls_index=None, is_choose=None):
        context = []

        if is_choose is not None:
            self.listWidget.item(self.main_window.is_choose_rect_index).setText(
                f'{self.main_window.is_choose_rect_index} : {is_choose}')
            return
        for i, label in enumerate(self.main_window.img.label_save):
            context.append(f' {i+1} : {self.main_window.names[label[0]]}')
        self.listWidget.clear()
        self.listWidget.addItems(context)
        # 默认选择第一个类别，并更改QLabel为对应的索引
        if box_cls_index is not None:
            self.listWidget.setCurrentRow(box_cls_index)

    def clear(self):
        self.set_rect_box()
        self.listWidget.clearSelection()

    def changeLabel(self, item):
        """更改标签内容为点击的类别索引"""
        currentIndex = self.listWidget.currentRow()
        self.main_window.rect_save_current = [currentIndex, -1, self.main_window.img.label_save[currentIndex]]
        self.main_window.img.only_index = True
        self.main_window.is_choose_rect = True
        self.main_window.is_hover_move_allow = True
        self.main_window.is_choose_rect_index = currentIndex
        self.main_window.img.is_trans = False

        self.main_window.move_xy(index=currentIndex)
        self.main_window.categoryShowWidget.set_rect_cls(self.main_window.img.label_save[currentIndex][0], currentIndex)
        self.set_rect_box(currentIndex)
        self.index = currentIndex
        self.main_window.is_choose_rect_index = currentIndex
