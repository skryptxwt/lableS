import os.path

from PyQt5.QtCore import QSize, Qt, QTimer
from PyQt5.QtWidgets import QMainWindow, QListView, QListWidget, QListWidgetItem
from PyQt5.QtGui import QPixmap, QIcon
from .thumbnaiThread import ImageLoader


class thumbnailApp(QMainWindow):

    def __init__(self, screen_list_widget, screen_label, main_window,
                 show_img_list, show_label_list,
                 size: (int, int) = (80, 80), paths_validated=False):
        super().__init__()

        self.image_loader = None  # 加载本地图片的线程
        self._load_generation = 0
        self.main_window = main_window  # 父窗口
        self.screen_list_widget = screen_list_widget  # 用来显示缩略图的部件

        self.thumbnail_size = QSize(*size)
        self.screen_list_widget.setDragDropMode(QListWidget.NoDragDrop)
        self.screen_list_widget.itemClicked.connect(self.on_item_clicked)
        self.screen_label = screen_label  # 显示缩略图对应名字的label

        self.show_list = show_img_list  # 显示的图片路径
        self.paths_validated = bool(paths_validated)
        self.show_list_temp = []  # 保留不是全路径的图片名字
        self.show_list_current = 0  # 一次最多加载20张图片

        self.show_label = show_label_list  # 显示的标签路径
        self.show_label_temp = []  # 保留不是全路径的标签名字

        self.index = 0

        self.screen_list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.init()

    def init(self):
        self.stop_loader()
        self._load_generation += 1
        self.screen_list_widget.setViewMode(QListWidget.IconMode)
        self.screen_list_widget.setIconSize(self.thumbnail_size)
        self.screen_list_widget.setResizeMode(QListWidget.Adjust)
        self.screen_list_widget.setFlow(QListView.LeftToRight)
        self.screen_list_widget.setWrapping(True)
        self.screen_list_widget.setMovement(QListView.Static)
        self.screen_list_widget.setUniformItemSizes(True)
        self.screen_list_widget.setWordWrap(False)
        self.screen_list_widget.setSpacing(4)
        self.set_thumbnail_size(self.thumbnail_size.width())
        self.path_init()
        self.load_label_img()

    def set_thumbnail_size(self, size):
        size = max(56, min(int(size), 128))
        self.thumbnail_size = QSize(size, size)
        self.screen_list_widget.setIconSize(self.thumbnail_size)
        self.screen_list_widget.setGridSize(QSize(size + 24, size + 36))
        self.screen_list_widget.doItemsLayout()

    def path_init(self):
        if not self.paths_validated:
            self.show_list = [
                path for path in self.show_list
                if os.path.exists(path) and os.path.isfile(path)
                and path.lower().endswith(
                    ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'))]
        self.show_list_temp = self.show_list.copy()
        self.show_list_temp = [os.path.basename(path) for path in self.show_list_temp]

    def load_label_img(self):

        default_pixmap = QPixmap(self.thumbnail_size)
        default_pixmap.fill(Qt.white)

        if self.show_label is not None:
            self.show_label_temp = [os.path.basename(path) for path in self.show_label]

        if len(self.show_list_temp) > 0:
            self.update_header()
            self.main_window.init(self.show_list[0])
            self._placeholder_pixmap = default_pixmap
            self._placeholder_index = 0
            generation = self._load_generation
            QTimer.singleShot(
                0, lambda: self._populate_placeholder_batch(generation))
        else:
            self.main_window._thumbnail_loading_finished(0, 0)

    def _populate_placeholder_batch(self, generation, batch_size=64):
        if generation != self._load_generation:
            return
        total = len(self.show_list)
        stop = min(self._placeholder_index + batch_size, total)
        for index in range(self._placeholder_index, stop):
            item = QListWidgetItem(
                QIcon(self._placeholder_pixmap), str(index + 1))
            item.setData(Qt.UserRole, index)
            self.screen_list_widget.addItem(item)
        self._placeholder_index = stop
        self.main_window._update_io_progress(
            stop, total, '正在建立图像队列')
        if stop < total:
            QTimer.singleShot(
                0, lambda: self._populate_placeholder_batch(generation))
            return
        self.image_loader = ImageLoader(self.show_list, 160)
        self.image_loader.signal_image_loaded.connect(
            self.update_image, Qt.QueuedConnection)
        self.image_loader.signal_progress.connect(
            self.main_window._thumbnail_loading_progress,
            Qt.QueuedConnection)
        self.image_loader.signal_completed.connect(
            self.main_window._thumbnail_loading_finished,
            Qt.QueuedConnection)
        self.image_loader.start()

    def update_image(self, image, index):
        item = self.screen_list_widget.item(index)
        if item is not None:
            item.setIcon(QIcon(QPixmap.fromImage(image)))

    def stop_loader(self):
        self._load_generation += 1
        if self.image_loader is not None and self.image_loader.isRunning():
            self.image_loader.requestInterruption()
            self.image_loader.wait(1500)

    def on_item_clicked(self, item):
        # 获取项目的文本
        index = item.data(Qt.UserRole)
        if index is None:
            index = int(item.text()) - 1
        if self.index is not None and self.index != int(index):
            self.index = int(index)
            self.main_window.boxShowWidget.clear()
            self.update_header()
            self.main_window.init(self.show_list[self.index])

    def up_dowm(self, index):
        # 获取项目的文本
        if self.index is not None and self.index != int(index):
            self.index = int(index)
            self.main_window.boxShowWidget.clear()
            self.update_header()
            self.main_window.init(self.show_list[self.index])

    def update_header(self):
        if not self.show_list_temp:
            self.screen_label.setText('NO IMAGE LOADED')
            if hasattr(self.main_window, 'update_image_position_status'):
                self.main_window.update_image_position_status(0, 0, '')
            return
        text = self.show_list_temp[self.index]
        if hasattr(self.main_window, 'update_image_position_status'):
            self.main_window.update_image_position_status(
                self.index, len(self.show_list_temp), text)
        else:
            self.screen_label.setText(
                f'{self.index + 1} / {len(self.show_list_temp)}   ·   {text}')
        self.screen_label.setAlignment(Qt.AlignCenter)
