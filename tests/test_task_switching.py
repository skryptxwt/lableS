import unittest
from types import SimpleNamespace
from unittest.mock import patch

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


if __name__ == '__main__':
    unittest.main()
