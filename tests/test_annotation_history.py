import unittest
from types import SimpleNamespace

from PyQt5.QtGui import QKeySequence

from utils.annotation_history import AnnotationHistory
from utils.mainWindow import DEFAULT_SHORTCUTS
from utils.mainWindow import MainWin


class AnnotationHistoryTests(unittest.TestCase):
    def test_undo_redo_and_new_branch(self):
        history = AnnotationHistory(limit=8)
        key = ('image.jpg', 'detect')
        initial = [[0, 0.5, 0.5, 0.2, 0.2]]
        moved = [[0, 0.6, 0.5, 0.2, 0.2]]
        deleted = []
        history.activate(key, initial)
        history.record(key, moved, '移动标注')
        history.record(key, deleted, '删除标注')

        self.assertEqual(history.undo(key), (moved, '删除标注'))
        self.assertEqual(history.undo(key), (initial, '移动标注'))
        self.assertEqual(history.redo(key), (moved, '移动标注'))

        replacement = [[2, 0.4, 0.4, 0.1, 0.1]]
        history.record(key, replacement, '新建标注')
        self.assertFalse(history.can_redo(key))
        self.assertEqual(history.undo(key), (moved, '新建标注'))

    def test_equal_states_are_not_recorded(self):
        history = AnnotationHistory()
        key = ('image.jpg', 'segment')
        rows = [[1, 0.1, 0.1, 0.9, 0.1, 0.5, 0.8]]
        history.activate(key, rows)

        self.assertFalse(history.record(key, rows, '无变化'))
        self.assertFalse(history.can_undo(key))

    def test_history_is_independent_per_image_and_task(self):
        history = AnnotationHistory()
        detect_key = ('same.jpg', 'detect')
        obb_key = ('same.jpg', 'obb')
        history.activate(detect_key, [])
        history.activate(obb_key, [])
        history.record(detect_key, [[0, 0.5, 0.5, 0.2, 0.2]], '检测框')

        self.assertTrue(history.can_undo(detect_key))
        self.assertFalse(history.can_undo(obb_key))

    def test_limit_discards_oldest_states(self):
        history = AnnotationHistory(limit=3)
        key = ('image.jpg', 'detect')
        history.activate(key, [])
        for index in range(4):
            history.record(
                key, [[index, 0.5, 0.5, 0.2, 0.2]], f'操作 {index}')

        self.assertIsNotNone(history.undo(key))
        self.assertIsNotNone(history.undo(key))
        self.assertIsNone(history.undo(key))

    def test_default_undo_redo_are_configurable_modifier_combinations(self):
        self.assertEqual(DEFAULT_SHORTCUTS['undo'][1], 'Ctrl+Z')
        self.assertEqual(DEFAULT_SHORTCUTS['redo'][1], 'Ctrl+Y')
        self.assertFalse(QKeySequence('Ctrl+Z').isEmpty())
        self.assertFalse(QKeySequence('Ctrl+Shift+Z').isEmpty())
        self.assertEqual(
            QKeySequence('Ctrl+Alt+Shift+R').toString(
                QKeySequence.PortableText),
            'Ctrl+Alt+Shift+R')

    def test_window_undo_redo_restores_and_persists_annotation_rows(self):
        class FakeData:
            def __init__(self, rows):
                self.data = [list(row) for row in rows]

            def __iter__(self):
                return iter(self.data)

            @staticmethod
            def _validate(_row):
                pass

        class FakeImage:
            def __init__(self, rows):
                self.img_path = 'image.jpg'
                self.task = 'detect'
                self.basedata = FakeData(rows)
                self.label_save = [list(row) for row in rows]
                self.only_index = False
                self.saved = []

            @staticmethod
            def _annotation_from_normalized(row):
                return list(row)

            def save(self):
                self.saved.append([list(row) for row in self.basedata])

        class Harness:
            _annotation_history_key = staticmethod(
                MainWin._annotation_history_key)
            _annotation_history_rows = staticmethod(
                MainWin._annotation_history_rows)
            _record_annotation_history = MainWin._record_annotation_history
            _restore_annotation_history = MainWin._restore_annotation_history
            undo_annotation = MainWin.undo_annotation
            redo_annotation = MainWin.redo_annotation

        initial = [[0, 0.5, 0.5, 0.2, 0.2]]
        moved = [[0, 0.6, 0.5, 0.2, 0.2]]
        window = Harness()
        window.img = FakeImage(initial)
        window.img_is_load = True
        window.annotation_history = AnnotationHistory()
        key = window._annotation_history_key(window.img)
        window.annotation_history.activate(key, initial)
        window.img.basedata.data = [list(row) for row in moved]
        window.img.label_save = [list(row) for row in moved]
        window._record_annotation_history('TASK EDIT')
        messages = []
        window.statusBar = lambda: SimpleNamespace(
            showMessage=lambda message, _timeout=0: messages.append(message))
        window._cancel_current_annotation = lambda: False
        window._obb_save_timer = SimpleNamespace(isActive=lambda: False)
        window._cancel_interaction_redraw = lambda: None
        window._clear_task_selection = lambda: None
        window.move_xy = lambda: None

        self.assertTrue(window.undo_annotation())
        self.assertEqual(window.img.basedata.data, initial)
        self.assertEqual(window.img.saved[-1], initial)
        self.assertIn('已撤销', messages[-1])

        self.assertTrue(window.redo_annotation())
        self.assertEqual(window.img.basedata.data, moved)
        self.assertEqual(window.img.saved[-1], moved)
        self.assertIn('已恢复', messages[-1])

    def test_reopening_image_keeps_history_after_save_precision_rounding(self):
        history = AnnotationHistory()

        class ImageState:
            img_path = 'same-image.jpg'
            task = 'detect'

            def __init__(self, rows):
                self.basedata = rows

        before = ImageState([[0, 0.123456, 0.5, 0.2, 0.2]])
        key = MainWin._annotation_history_key(before)
        history.activate(key, MainWin._annotation_history_rows(before))
        after = ImageState([[0, 0.654321, 0.5, 0.2, 0.2]])
        history.record(
            key, MainWin._annotation_history_rows(after), '移动标注')

        # DataApp.save() writes detect coordinates with three decimals.  A
        # newly constructed Image therefore loads these rounded values.
        reopened = ImageState([[0, 0.654, 0.5, 0.2, 0.2]])
        history.activate(key, MainWin._annotation_history_rows(reopened))

        self.assertTrue(history.can_undo(key))
        rows, action = history.undo(key)
        self.assertEqual(rows[0][1], 0.123)
        self.assertEqual(action, '移动标注')


if __name__ == '__main__':
    unittest.main()
