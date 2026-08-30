from PyQt5.QtCore import QThread, pyqtSignal
from .common_fun import root
root = root.parent


class loadModel(QThread):
    signal_model_loaded = pyqtSignal(object)
    signal_error = pyqtSignal(str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            from ultralytics import YOLO
            model = YOLO(self.file_path)
            model(str(root / "utils/material/warm_up.png"))  # 预热
            self.signal_model_loaded.emit(model)
        except Exception as exc:
            self.signal_error.emit(f'模型加载失败: {exc}')


class DetectModel(QThread):
    signal_detection_finished = pyqtSignal(object)
    signal_error = pyqtSignal(str)

    def __init__(self, model, image, confidence):
        super().__init__()
        self.model = model
        self.image = image
        self.confidence = confidence

    def run(self):
        try:
            result = self.model(self.image, conf=self.confidence)[0]
            boxes = result.boxes.xywhn.tolist()
            classes = result.boxes.cls.tolist()
            self.signal_detection_finished.emit((boxes, classes))
        except Exception as exc:
            self.signal_error.emit(f'检测失败: {exc}')


