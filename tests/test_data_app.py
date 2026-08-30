import tempfile
import unittest
from pathlib import Path

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


if __name__ == '__main__':
    unittest.main()
