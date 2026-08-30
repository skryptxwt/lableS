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

    def __init__(self, model, image, confidence, task='detect', kpt_shape=(17, 3)):
        super().__init__()
        self.model = model
        self.image = image
        self.confidence = confidence
        self.task = task
        self.kpt_shape = tuple(kpt_shape)

    def run(self):
        try:
            result = self.model(self.image, conf=self.confidence)[0]
            task = getattr(self.model, 'task', None) or self.task
            annotations = []
            if task == 'segment' and result.masks is not None:
                classes = result.boxes.cls.tolist()
                for class_id, polygon in zip(classes, result.masks.xyn):
                    annotations.append([
                        int(class_id),
                        *(float(value) for point in polygon.tolist()
                          for value in point),
                    ])
            elif task == 'obb' and result.obb is not None:
                classes = result.obb.cls.tolist()
                for class_id, corners in zip(
                        classes, result.obb.xyxyxyxyn.tolist()):
                    annotations.append([
                        int(class_id),
                        *(float(value) for point in corners for value in point),
                    ])
            elif task == 'pose' and result.keypoints is not None:
                boxes = result.boxes.xywhn.tolist()
                classes = result.boxes.cls.tolist()
                points = result.keypoints.xyn.tolist()
                confidences = (result.keypoints.conf.tolist()
                               if result.keypoints.conf is not None else None)
                dimensions = self.kpt_shape[1]
                for item_index, (class_id, box, keypoints) in enumerate(
                        zip(classes, boxes, points)):
                    annotation = [int(class_id), *map(float, box)]
                    for point_index, point in enumerate(keypoints):
                        annotation.extend((float(point[0]), float(point[1])))
                        if dimensions == 3:
                            confidence = (confidences[item_index][point_index]
                                          if confidences is not None else 1.0)
                            annotation.append(2 if confidence >= 0.5 else 1)
                    annotations.append(annotation)
            else:
                boxes = result.boxes.xywhn.tolist()
                classes = result.boxes.cls.tolist()
                annotations = [
                    [int(class_id), *map(float, box)]
                    for class_id, box in zip(classes, boxes)
                ]
                task = 'detect'
            self.signal_detection_finished.emit({
                'task': task, 'annotations': annotations})
        except Exception as exc:
            self.signal_error.emit(f'检测失败: {exc}')


