import tempfile
import unittest
from pathlib import Path

from utils.DataApp import DataApp
from utils.io_workers import (ImageScanWorker, LabelExportWorker,
                              LabelImportWorker)


class IoWorkerTest(unittest.TestCase):
    def test_image_scan_filters_files_and_reports_progress(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / 'one.jpg').write_bytes(b'image')
            (folder / 'ignore.txt').write_text('x', encoding='utf-8')
            results = []
            progress = []
            worker = ImageScanWorker(folder=folder)
            worker.completed.connect(results.append)
            worker.progress.connect(
                lambda current, total, detail:
                progress.append((current, total, detail)))

            worker.run()

            self.assertEqual(
                [Path(path).name for path in results[0]['paths']],
                ['one.jpg'])
            self.assertEqual(progress[-1][:2], (2, 2))

    def test_label_import_converts_pose_prediction_in_background(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            source_folder = folder / 'source'
            destination_folder = folder / 'destination'
            source_folder.mkdir()
            source = source_folder / 'sample.txt'
            source.write_text(
                '0 0.5 0.5 0.4 0.6 0.4 0.4 0.9 0.6 0.4 0.3\n',
                encoding='utf-8')
            results = []
            worker = LabelImportWorker(
                destination_folder, {'sample'}, 'pose', (2, 3),
                sources=[source])
            worker.completed.connect(results.append)

            worker.run()

            self.assertEqual(len(results[0]['imported']), 1)
            self.assertEqual(results[0]['converted_rows'], 1)
            imported = DataApp(
                destination_folder / 'sample.txt',
                task='pose', kpt_shape=(2, 3))
            self.assertEqual(imported[0][-1], 1)

    def test_label_export_copies_nonempty_labels_and_reports_count(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            source_folder = folder / 'source'
            destination_folder = folder / 'destination'
            source_folder.mkdir()
            (source_folder / 'one.txt').write_text(
                '0 0.5 0.5 0.2 0.2', encoding='utf-8')
            (source_folder / 'empty.txt').write_text('', encoding='utf-8')
            results = []
            worker = LabelExportWorker(
                source_folder, {'one', 'empty'}, destination_folder)
            worker.completed.connect(results.append)

            worker.run()

            self.assertEqual(results[0]['exported'], 1)
            self.assertTrue((destination_folder / 'one.txt').is_file())
            self.assertFalse((destination_folder / 'empty.txt').exists())


if __name__ == '__main__':
    unittest.main()
