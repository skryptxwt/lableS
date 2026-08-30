import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from utils.DataApp import DataApp


class DataAppTest(unittest.TestCase):
    def test_parses_arbitrary_whitespace(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'labels.txt'
            path.write_text('0   0.5\t0.4  0.2 0.1\n', encoding='utf-8')

            labels = DataApp(path)

            self.assertEqual(labels[0], [0, 0.5, 0.4, 0.2, 0.1])

    def test_rejects_invalid_shape_and_coordinates(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'labels.txt'
            path.write_text('0 0.5 0.4 1.2 0.1\n', encoding='utf-8')

            with self.assertRaisesRegex(ValueError, r'\[0, 1\]'):
                DataApp(path)

    def test_save_is_round_trip_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'labels.txt'
            path.write_text('', encoding='utf-8')
            labels = DataApp(path)
            labels.append([2, 0.5, 0.4, 0.2, 0.1])

            labels.save()

            self.assertEqual(DataApp(path)[0], [2, 0.5, 0.4, 0.2, 0.1])
            self.assertEqual(list(Path(directory).glob('*.tmp')), [])

    def test_save_retries_temporary_windows_replace_denial(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'labels.txt'
            path.write_text('', encoding='utf-8')
            labels = DataApp(path)
            labels.append([0, 0.5, 0.5, 0.2, 0.2])

            with patch(
                    'utils.DataApp.os.replace',
                    side_effect=[PermissionError(5, '拒绝访问'), None]
                    ) as replace, patch(
                        'utils.DataApp.time.sleep') as sleep:
                labels.save()

            self.assertEqual(replace.call_count, 2)
            sleep.assert_called_once_with(0.015)
            self.assertEqual(list(Path(directory).glob('*.tmp')), [])

    def test_merge_deduplicates_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            first_path = Path(directory) / 'first.txt'
            second_path = Path(directory) / 'second.txt'
            first_path.write_text('0 0.5 0.5 0.2 0.2\n', encoding='utf-8')
            second_path.write_text(
                '0 0.5 0.5 0.2 0.2\n1 0.4 0.4 0.1 0.1\n', encoding='utf-8')
            first = DataApp(first_path)

            added = first.merge(DataApp(second_path))

            self.assertEqual(added, 1)
            self.assertEqual(len(first), 2)

    def test_segment_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'segment.txt'
            path.write_text('', encoding='utf-8')
            labels = DataApp(path, task='segment')
            polygon = [1, 0.1, 0.2, 0.7, 0.2, 0.6, 0.8]

            labels.append(polygon)
            labels.save()

            self.assertEqual(DataApp(path, task='segment')[0], polygon)

    def test_obb_requires_four_normalized_corners(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'obb.txt'
            path.write_text('', encoding='utf-8')
            labels = DataApp(path, task='obb')
            obb = [0, 0.2, 0.2, 0.8, 0.2, 0.8, 0.7, 0.2, 0.7]

            labels.append(obb)
            with self.assertRaisesRegex(ValueError, '9'):
                labels.append(obb[:-1])

    def test_pose_validates_configured_keypoint_shape(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'pose.txt'
            path.write_text('', encoding='utf-8')
            labels = DataApp(path, task='pose', kpt_shape=(2, 3))
            pose = [0, 0.5, 0.5, 0.4, 0.6,
                    0.4, 0.4, 2, 0.6, 0.4, 1]

            labels.append(pose)
            labels.save()
            self.assertEqual(
                DataApp(path, task='pose', kpt_shape=(2, 3))[0], pose)
            with self.assertRaisesRegex(ValueError, '可见性'):
                labels[0] = pose[:-1] + [3]

    def test_pose_prediction_confidence_converts_to_visibility_on_import(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'pose_prediction.txt'
            path.write_text(
                '0 0.5 0.5 0.4 0.6 0.4 0.4 0.9 0.6 0.4 0.3\n',
                encoding='utf-8')

            with self.assertRaisesRegex(ValueError, '可见性'):
                DataApp(path, task='pose', kpt_shape=(2, 3))

            labels = DataApp(
                path, task='pose', kpt_shape=(2, 3),
                accept_prediction_output=True)

            self.assertEqual(labels.normalized_prediction_rows, 1)
            self.assertEqual(labels[0], [
                0, 0.5, 0.5, 0.4, 0.6,
                0.4, 0.4, 2, 0.6, 0.4, 1])

    def test_pose_training_visibility_is_unchanged_in_compatible_import(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'pose_training.txt'
            path.write_text(
                '0 0.5 0.5 0.4 0.6 0.4 0.4 2 0.6 0.4 0\n',
                encoding='utf-8')

            labels = DataApp(
                path, task='pose', kpt_shape=(2, 3),
                accept_prediction_output=True)

            self.assertEqual(labels.normalized_prediction_rows, 0)
            self.assertEqual(labels[0][-3:], [0.6, 0.4, 0.0])


if __name__ == '__main__':
    unittest.main()
