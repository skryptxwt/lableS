import unittest
from types import SimpleNamespace
from unittest.mock import patch

from PyQt5.QtCore import QEvent, QPoint, Qt
from PyQt5.QtWidgets import QComboBox, QSpinBox

from utils import mainWindow as main_window_module
from utils.mainWindow import MainWin


class TaskSwitchingTest(unittest.TestCase):
    def test_existing_labels_block_switch_without_native_dialog(self):
        messages = []
        action = SimpleNamespace(setChecked=lambda checked: None)
        window = SimpleNamespace(
            img_is_load=True,
            img=SimpleNamespace(label_save=[[0, 1, 1, 2, 1, 2, 2, 1, 2]]),
            annotation_task='obb',
            task_actions={'obb': action},
            statusBar=lambda: SimpleNamespace(
                showMessage=lambda message, _timeout=0: messages.append(message)),
        )

        with patch('utils.mainWindow.QMessageBox.warning',
                   side_effect=AssertionError('不应打开原生模态警告框')):
            switched = MainWin.set_annotation_task(window, 'detect')

        self.assertFalse(switched)
        self.assertEqual(window.annotation_task, 'obb')
        self.assertIn('TASK SWITCH BLOCKED', messages[-1])

    def test_reset_task_interaction_clears_transient_mouse_state(self):
        stopped = []
        image = SimpleNamespace(only_index=True)
        window = SimpleNamespace(
            _obb_save_timer=SimpleNamespace(stop=lambda: stopped.append(True)),
            task_draft_points=[(1, 2)],
            task_pose_bbox=[1, 2, 3, 4],
            task_pose_points=[[1, 2]],
            task_drag={'start': (1, 2)},
            task_edit={'kind': 'edge'},
            detect_drag_original=[0, 1, 2, 3, 4],
            detect_drag_start_org=(1, 2),
            is_add_box=True,
            is_update_label=True,
            is_choose_rect=True,
            is_choose_rect_index=0,
            is_hover_move_allow=True,
            mouse_left_press=True,
            rect_save=[0],
            rect_save_current=[0],
            cross=True,
            hover=True,
            img=image,
        )

        MainWin._reset_task_interaction(window)

        self.assertEqual(stopped, [True])
        self.assertFalse(window.mouse_left_press)
        self.assertIsNone(window.task_edit)
        self.assertIsNone(window.rect_save_current)
        self.assertFalse(image.only_index)

    def test_keypoint_dialog_widget_dependencies_are_imported(self):
        self.assertIs(main_window_module.QSpinBox, QSpinBox)
        self.assertIs(main_window_module.QComboBox, QComboBox)

    def test_incompatible_label_reports_status_without_native_dialog(self):
        messages = []
        label = SimpleNamespace(
            clear=lambda: None,
            setText=lambda text: None,
        )
        window = SimpleNamespace(
            label=label,
            annotation_task='pose',
            kpt_shape=(17, 3),
            img_is_load=True,
            img=object(),
            statusBar=lambda: SimpleNamespace(
                showMessage=lambda message, _timeout=0: messages.append(message)),
        )

        with patch('utils.mainWindow.Image',
                   side_effect=ValueError('pose 标签字段数量错误')):
            with patch('utils.mainWindow.QMessageBox.warning',
                       side_effect=AssertionError('不应打开原生模态警告框')):
                loaded = MainWin.init_image(window, 'image.png', 'label.txt')

        self.assertFalse(loaded)
        self.assertFalse(window.img_is_load)
        self.assertIsNone(window.img)
        self.assertIn('LABEL FORMAT ERROR', messages[-1])

    def test_pose_save_failure_rolls_back_last_point_and_annotation(self):
        messages = []

        class FailingImage:
            def __init__(self):
                self.label_save = []

            @staticmethod
            def new_xy_to_org_xy(position):
                return position

            def append_annotation(self, label):
                self.label_save.append(label)
                return len(self.label_save) - 1

            @staticmethod
            def save():
                raise PermissionError('标签文件正在使用')

            def pop(self, index):
                self.label_save.pop(index)

        window = SimpleNamespace(
            kpt_shape=(2, 3),
            task_pose_bbox=[10, 10, 100, 100],
            task_pose_points=[[20, 20, 2]],
            cls=0,
            img=FailingImage(),
            statusBar=lambda: SimpleNamespace(
                showMessage=lambda message, _timeout=0: messages.append(message)),
            _redraw_task_draft=lambda: None,
        )

        MainWin._append_pose_point(window, (30, 30), visibility=2)

        self.assertEqual(window.task_pose_points, [[20, 20, 2]])
        self.assertEqual(window.img.label_save, [])
        self.assertIn('POSE SAVE FAILED', messages[-1])

    def test_segment_closes_only_near_first_point_after_three_vertices(self):
        image = SimpleNamespace(org_xy_to_new_xy=lambda point: point)
        window = SimpleNamespace(
            img_is_load=True,
            img=image,
            task_draft_points=[(20, 20), (80, 20), (80, 80)],
        )

        self.assertTrue(MainWin._segment_can_close(window, (29, 25)))
        self.assertFalse(MainWin._segment_can_close(window, (40, 40)))
        window.task_draft_points.pop()
        self.assertFalse(MainWin._segment_can_close(window, (20, 20)))

    def test_segment_cleanup_removes_adjacent_and_closing_duplicates(self):
        points = [(10, 10), (10, 10), (40, 10), (40, 40), (10, 10)]

        cleaned = MainWin._clean_segment_points(points)

        self.assertEqual(cleaned, [(10.0, 10.0), (40.0, 10.0),
                                   (40.0, 40.0)])

    def test_segment_save_failure_keeps_draft_and_rolls_back_annotation(self):
        messages = []

        class FailingImage:
            def __init__(self):
                self.label_save = []

            def append_annotation(self, label):
                self.label_save.append(label)
                return len(self.label_save) - 1

            @staticmethod
            def save():
                raise PermissionError('标签文件正在使用')

            def pop(self, index):
                self.label_save.pop(index)

        original = [(10, 10), (80, 10), (80, 80)]
        window = SimpleNamespace(
            task_draft_points=list(original),
            cls=2,
            img=FailingImage(),
            _clean_segment_points=MainWin._clean_segment_points,
            statusBar=lambda: SimpleNamespace(
                showMessage=lambda message, _timeout=0: messages.append(message)),
            _redraw_task_draft=lambda: None,
        )

        saved = MainWin._finish_segment(window)

        self.assertFalse(saved)
        self.assertEqual(window.task_draft_points, original)
        self.assertEqual(window.img.label_save, [])
        self.assertIn('SEGMENT SAVE FAILED', messages[-1])

    def test_segment_vertex_is_inserted_after_hit_edge(self):
        messages = []

        class EditableImage:
            def __init__(self):
                self.label_save = [
                    [3, 10, 10, 90, 10, 90, 90, 10, 90]
                ]

            @staticmethod
            def new_xy_to_org_xy(point):
                return point

            def change_annotation(self, index, label):
                self.label_save[index] = list(label)

            @staticmethod
            def save():
                pass

        image = EditableImage()
        window = SimpleNamespace(
            img=image,
            statusBar=lambda: SimpleNamespace(
                showMessage=lambda message, _timeout=0: messages.append(message)),
            _select_task_annotation=lambda index: None,
        )

        inserted = MainWin._insert_segment_vertex(
            window, (0, 1, (90.0, 50.0)))

        self.assertTrue(inserted)
        self.assertEqual(image.label_save[0], [
            3, 10, 10, 90, 10, 90.0, 50.0, 90, 90, 10, 90])
        self.assertIn('已插入新顶点', messages[-1])

    def test_cancel_segment_draft_discards_only_unsaved_points(self):
        messages = []
        redraws = []
        cursors = []
        window = SimpleNamespace(
            task_draft_points=[(10, 10), (80, 10), (80, 80)],
            setCursor=lambda cursor: cursors.append(cursor),
            _redraw_task_draft=lambda: redraws.append(True),
            statusBar=lambda: SimpleNamespace(
                showMessage=lambda message, _timeout=0: messages.append(message)),
        )

        cancelled = MainWin._cancel_segment_draft(window)

        self.assertTrue(cancelled)
        self.assertEqual(window.task_draft_points, [])
        self.assertEqual(redraws, [True])
        self.assertEqual(cursors, [Qt.CrossCursor])
        self.assertIn('已取消当前绘制', messages[-1])

    def test_double_click_opens_category_picker_for_every_task(self):
        opened = []

        class DoubleClickEvent:
            @staticmethod
            def type():
                return QEvent.MouseButtonDblClick

            @staticmethod
            def button():
                return Qt.LeftButton

            @staticmethod
            def pos():
                return QPoint(30, 40)

        label = SimpleNamespace(
            mapToGlobal=lambda point: QPoint(point.x() + 100,
                                             point.y() + 200))
        image = SimpleNamespace(
            task_hit_test=lambda x, y: ('shape', 2, -1),
            hit_test=lambda x, y: ('rect', 2, -1),
        )
        event = DoubleClickEvent()
        for task in ('segment', 'obb', 'pose'):
            window = SimpleNamespace(
                annotation_task=task,
                task_draft_points=[],
                label=label,
                img=image,
                mouse_pos=None,
                _event_canvas_pos=lambda source, current_event: (30, 40),
                _show_annotation_category_picker=(
                    lambda index, position, current=task:
                    opened.append((current, index, position))),
            )
            MainWin._task_event_filter(window, event)

        detect_window = SimpleNamespace(
            change_label_name=False,
            img_is_load=True,
            annotation_task='detect',
            label=label,
            img=image,
            _event_canvas_pos=lambda source, current_event: (30, 40),
            _show_annotation_category_picker=(
                lambda index, position: opened.append(
                    ('detect', index, position))),
        )
        MainWin.eventFilter(detect_window, label, event)

        self.assertEqual([entry[:2] for entry in opened], [
            ('segment', 2), ('obb', 2), ('pose', 2), ('detect', 2)])


if __name__ == '__main__':
    unittest.main()
