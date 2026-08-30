import unittest
from types import SimpleNamespace

import numpy as np

from utils.loadModeThread import DetectModel


class FakeModel:
    def __init__(self, task, result):
        self.task = task
        self.result = result

    def __call__(self, _image, conf=0.5):
        return [self.result]


def run_worker(task, result, kpt_shape=(17, 3)):
    worker = DetectModel(
        FakeModel(task, result), np.zeros((10, 10, 3), dtype=np.uint8),
        0.5, task=task, kpt_shape=kpt_shape)
    payloads = []
    errors = []
    worker.signal_detection_finished.connect(payloads.append)
    worker.signal_error.connect(errors.append)
    worker.run()
    if errors:
        raise AssertionError(errors[0])
    return payloads[0]


class InferenceTaskTest(unittest.TestCase):
    def test_detect_output(self):
        result = SimpleNamespace(
            boxes=SimpleNamespace(
                xywhn=np.array([[0.5, 0.5, 0.2, 0.3]]),
                cls=np.array([2])),
            masks=None, obb=None, keypoints=None)

        payload = run_worker('detect', result)

        self.assertEqual(payload['task'], 'detect')
        self.assertEqual(payload['annotations'], [[2, 0.5, 0.5, 0.2, 0.3]])

    def test_segment_output(self):
        result = SimpleNamespace(
            boxes=SimpleNamespace(cls=np.array([1])),
            masks=SimpleNamespace(xyn=[np.array(
                [[0.1, 0.2], [0.8, 0.2], [0.4, 0.9]])]),
            obb=None, keypoints=None)

        payload = run_worker('segment', result)

        self.assertEqual(payload['annotations'][0],
                         [1, 0.1, 0.2, 0.8, 0.2, 0.4, 0.9])

    def test_obb_output(self):
        result = SimpleNamespace(
            boxes=None, masks=None, keypoints=None,
            obb=SimpleNamespace(
                cls=np.array([3]),
                xyxyxyxyn=np.array([[[0.1, 0.1], [0.8, 0.2],
                                     [0.7, 0.8], [0.0, 0.7]]])))

        payload = run_worker('obb', result)

        self.assertEqual(len(payload['annotations'][0]), 9)
        self.assertEqual(payload['annotations'][0][0], 3)

    def test_obb_output_clamps_corners_to_normalized_image_bounds(self):
        result = SimpleNamespace(
            boxes=None, masks=None, keypoints=None,
            obb=SimpleNamespace(
                cls=np.array([3]),
                xyxyxyxyn=np.array([[[-0.08, 0.1], [1.06, 0.2],
                                     [0.7, 1.02], [0.0, -0.04]]])))

        payload = run_worker('obb', result)

        self.assertEqual(payload['annotations'][0],
                         [3, 0.0, 0.1, 1.0, 0.2,
                          0.7, 1.0, 0.0, 0.0])

    def test_pose_output_includes_visibility(self):
        result = SimpleNamespace(
            masks=None, obb=None,
            boxes=SimpleNamespace(
                xywhn=np.array([[0.5, 0.5, 0.4, 0.6]]),
                cls=np.array([0])),
            keypoints=SimpleNamespace(
                xyn=np.array([[[0.4, 0.3], [0.6, 0.4]]]),
                conf=np.array([[0.9, 0.3]])))

        payload = run_worker('pose', result, kpt_shape=(2, 3))

        self.assertEqual(payload['annotations'][0],
                         [0, 0.5, 0.5, 0.4, 0.6,
                          0.4, 0.3, 2, 0.6, 0.4, 1])


if __name__ == '__main__':
    unittest.main()
