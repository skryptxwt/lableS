from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage

from .common_fun import read_img, resize_img


class ImageLoader(QThread):
    signal_image_loaded = pyqtSignal(QImage, int)
    signal_progress = pyqtSignal(int, int, str)
    signal_completed = pyqtSignal(int, int)

    def __init__(self, image_paths, preview_size=160):
        super().__init__()
        self.image_paths = image_paths
        self.preview_size = max(80, int(preview_size))

    def run(self):
        total = len(self.image_paths)
        errors = 0
        for index, path in enumerate(self.image_paths):
            if self.isInterruptionRequested():
                return
            try:
                image = self.load_image(path)
                self.signal_image_loaded.emit(image, index)
            except Exception:
                # A corrupt/unsupported image must not terminate the worker
                # before it can report completion and release the busy UI.
                errors += 1
            self.signal_progress.emit(index + 1, total, str(path))
        self.signal_completed.emit(total, errors)

    def load_image(self, file):
        image_data = read_img(file)
        s = self.preview_size
        temp = resize_img(image_data, (s, s))

        # QPixmap is a GUI resource and must stay on the main thread. QImage
        # is reentrant, and copy() detaches it from the temporary NumPy buffer.
        return QImage(
            temp.data, s, s, s * 3,
            QImage.Format_RGB888).rgbSwapped().copy()
