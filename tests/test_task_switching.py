import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from PyQt5.QtCore import QEvent, QPoint, Qt
from PyQt5.QtWidgets import (QApplication, QComboBox, QListWidget, QSpinBox,
                             QWidget)

from utils import mainWindow as main_window_module
from utils.LabelApp import LabelApp
from utils.mainWindow import MainWin
from utils.tempCatewidget import CategoryApp as CategoryPopup


class TaskSwitchingTest(unittest.TestCase):
    def test_selected_object_row_shows_its_own_delete_button(self):
        app = QApplication.instance() or QApplication([])
        deleted = []
        list_widget = QListWidget()
        main = SimpleNamespace(
            ui=SimpleNamespace(labelShow=list_widget),
            names={0: 'zero', 1: 'one'},
            img=SimpleNamespace(label_save=[
                [0, 1, 2, 3, 4], [1, 5, 6, 7, 8]]),
            is_choose_rect=False,
            is_choose_rect_index=None,
            deleteBox_=lambda index=None: deleted.append(index),
        )
        objects = LabelApp(main)

        objects.set_rect_box(0)

        self.assertFalse(objects._row_widgets[0].delete_button.isHidden())
        self.assertTrue(objects._row_widgets[1].delete_button.isHidden())

        objects.delete_row(1)

        self.assertEqual(deleted, [1])
        self.assertEqual(main.is_choose_rect_index, 1)
        app.processEvents()

    def test_category_picker_is_an_in_window_overlay(self):
        app = QApplication.instance() or QApplication([])
        host = QWidget()
        host.resize(800, 600)
        main = SimpleNamespace(
            window_shell=host,
            names={0: '0', 1: '1'},
            class_styles={},
            colors={},
            cls=0,
            change_label_name=False,
            temp_widget=None,
        )

        popup = CategoryPopup(main, QListWidget())

        self.assertIs(popup.parentWidget(), host)
        self.assertFalse(popup.isWindow())
        self.assertFalse(bool(popup.windowFlags() & Qt.Popup))
        popup.close()
        app.processEvents()

    def test_image_index_input_jumps_to_one_based_position(self):
        selected_rows = []
        scrolled_items = []

        class IndexInput:
            value = '4'

            def text(self):
                return self.value

            def setText(self, value):
                self.value = value

            def selectAll(self):
                pass

        queue = SimpleNamespace(
            item=lambda index: f'item-{index}',
            setCurrentRow=lambda index: selected_rows.append(index),
            scrollToItem=lambda item, _hint: scrolled_items.append(item),
        )
        thumbnail = SimpleNamespace(
            index=0,
            show_list=['1.jpg', '2.jpg', '3.jpg', '4.jpg', '5.jpg'],
            screen_list_widget=queue,
        )

        def jump(index):
            thumbnail.index = index

        thumbnail.up_dowm = jump
        window = SimpleNamespace(
            thumbnail_widget=thumbnail,
            image_index_input=IndexInput(),
            statusBar=lambda: SimpleNamespace(showMessage=lambda *args: None),
        )

        MainWin._jump_to_image_index(window)

        self.assertEqual(thumbnail.index, 3)
        self.assertEqual(selected_rows, [3])
        self.assertEqual(scrolled_items, ['item-3'])

    def test_image_index_input_rejects_out_of_range_position(self):
        messages = []

        class IndexInput:
            value = '99'

            def text(self):
                return self.value

            def setText(self, value):
                self.value = value

            def selectAll(self):
                pass

        thumbnail = SimpleNamespace(index=1, show_list=['1.jpg', '2.jpg'])
        field = IndexInput()
        window = SimpleNamespace(
            thumbnail_widget=thumbnail,
            image_index_input=field,
            statusBar=lambda: SimpleNamespace(
                showMessage=lambda message, _timeout: messages.append(message)),
        )

        MainWin._jump_to_image_index(window)

        self.assertEqual(field.value, '2')
        self.assertIn('1 - 2', messages[0])

    def test_failed_label_import_keeps_image_queue(self):
        queue_clears = []
        warnings = []
        window = SimpleNamespace(
            label_list=set(),
            label_list_only_name=set(),
            thumbnail_widget=None,
            ui=SimpleNamespace(
                thumbnailWidget=SimpleNamespace(
                    clear=lambda: queue_clears.append(True))),
            _finish_io_operation=lambda message: None,
        )

        with patch.object(
                main_window_module.QMessageBox, 'warning',
                side_effect=lambda _parent, title, message:
                warnings.append((title, message))):
            MainWin._label_import_completed(window, {
                'imported': [],
                'errors': ['sample.txt: 标签格式与当前任务不兼容'],
                'converted_rows': 0,
            })

        self.assertEqual(queue_clears, [])
        self.assertEqual(window.label_list, set())
        self.assertEqual(window.label_list_only_name, set())
        self.assertEqual(warnings, [
            ('部分标签导入失败',
             'sample.txt: 标签格式与当前任务不兼容')])

    def test_pose_prediction_import_writes_converted_training_label(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = main_window_module.Path(directory)
            source = folder / 'prediction.txt'
            destination = folder / 'imported.txt'
            source.write_text(
                '0 0.5 0.5 0.4 0.6 0.4 0.4 0.9 0.6 0.4 0.3\n',
                encoding='utf-8')
            window = SimpleNamespace(
                annotation_task='pose', kpt_shape=(2, 3))

            added = MainWin._merge_label_file(
                window, source, destination)
            imported = main_window_module.DataApp(
                destination, task='pose', kpt_shape=(2, 3))

            self.assertEqual(added, 1)
            self.assertEqual(imported[0][-6:], [
                0.4, 0.4, 2.0, 0.6, 0.4, 1.0])

    def test_category_popup_close_detaches_shared_reference(self):
        closed = []
        popup = SimpleNamespace(dismiss=lambda: closed.append(True))
        window = SimpleNamespace(temp_widget=popup)

        result = MainWin._close_category_popup(window)

        self.assertTrue(result)
        self.assertIsNone(window.temp_widget)
        self.assertEqual(closed, [True])

    def test_category_picker_reuses_existing_overlay(self):
        calls = []
        picker = SimpleNamespace(
            init=lambda: calls.append('init'),
            set_rect_cls=lambda cls, index: calls.append(
                ('select', cls, index)),
            show_at=lambda position: calls.append(('show', position)),
        )
        image = SimpleNamespace(label_save=[[2, 1, 2, 3, 4]])
        window = SimpleNamespace(
            img_is_load=True,
            img=image,
            annotation_task='detect',
            is_choose_rect=False,
            is_choose_rect_index=None,
            is_hover_move_allow=False,
            rect_save_current=None,
            cls=0,
            _category_picker=picker,
            temp_widget=None,
            move_xy=lambda index=None: calls.append(('move', index)),
            boxShowWidget=SimpleNamespace(
                set_rect_box=lambda index: calls.append(('box', index))),
            categoryShowWidget=SimpleNamespace(
                set_rect_cls=lambda cls, index: calls.append(
                    ('class', cls, index))),
            _close_category_popup=lambda invalidate_request=False: False,
        )

        shown = MainWin._show_annotation_category_picker(
            window, 0, QPoint(50, 60))

        self.assertTrue(shown)
        self.assertIs(window.temp_widget, picker)
        self.assertIn(('select', 2, 0), calls)
        self.assertIn(('show', QPoint(50, 60)), calls)

    def test_category_popup_closes_when_annotation_is_no_longer_valid(self):
        messages = []
        closed = []
        main = SimpleNamespace(
            is_choose_rect_index=None,
            img=SimpleNamespace(basedata=[]),
            statusBar=lambda: SimpleNamespace(
                showMessage=lambda message, _timeout=0: messages.append(message)),
        )
        popup = SimpleNamespace(
            main_window=main,
            dismiss=lambda deferred=False: closed.append(deferred),
        )

        CategoryPopup.changeLabel(popup, SimpleNamespace())

        self.assertEqual(closed, [True])
        self.assertIn('没有可调整类别的标注对象', messages[-1])

    def test_toolbar_width_includes_text_padding(self):
        self.assertEqual(MainWin._toolbar_control_width(82, 88), 106)
        self.assertEqual(MainWin._toolbar_control_width(40, 88), 88)

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

    def test_falsey_qt_image_is_reloaded_when_switching_pose_to_detect(self):
        class FalseyImage:
            label_save = []
            img_path = 'image.png'
            label_path = 'label.txt'

            def __bool__(self):
                return False

        old_image = FalseyImage()
        loaded = []
        actions = {
            name: SimpleNamespace(setChecked=lambda checked: None)
            for name in ('detect', 'segment', 'obb', 'pose')
        }
        window = SimpleNamespace(
            img_is_load=True,
            img=old_image,
            annotation_task='pose',
            task_actions=actions,
            task_button=SimpleNamespace(setText=lambda text: None),
            kpt_shape=(17, 3),
            boxShowWidget=SimpleNamespace(set_rect_box=lambda: None),
            statusBar=lambda: SimpleNamespace(showMessage=lambda *args: None),
            _sync_title_toolbar_widths=lambda button: None,
            _reset_task_interaction=lambda: None,
            _save_background_config=lambda **updates: None,
        )

        def init_image(image_path, label_path):
            loaded.append((image_path, label_path))
            window.img = SimpleNamespace(task=window.annotation_task)
            window.img_is_load = True
            return True

        window.init_image = init_image

        switched = MainWin.set_annotation_task(
            window, 'detect', persist=False, reload_image=True)

        self.assertTrue(switched)
        self.assertEqual(loaded, [('image.png', 'label.txt')])
        self.assertEqual(window.annotation_task, 'detect')
        self.assertEqual(window.img.task, 'detect')

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

    def test_segment_vertex_insert_uses_configurable_shortcut(self):
        inserted = []
        edge_hit = (2, 1, (30.0, 40.0))
        image = SimpleNamespace(
            segment_edge_hit_test=lambda *_args, **_kwargs: edge_hit)
        window = SimpleNamespace(
            img_is_load=True,
            annotation_task='segment',
            task_draft_points=[],
            mouse_pos=[30, 40],
            is_choose_rect=True,
            is_choose_rect_index=2,
            img=image,
            _insert_segment_vertex=lambda hit: inserted.append(hit) or True,
        )

        self.assertEqual(
            main_window_module.DEFAULT_SHORTCUTS['insert_segment_vertex'],
            ('插入分割点', 'I'))
        self.assertTrue(MainWin.insert_segment_vertex_at_cursor(window))
        self.assertEqual(inserted, [edge_hit])

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

    def test_cancel_pose_draft_discards_bbox_and_keypoints(self):
        messages = []
        redraws = []
        image = SimpleNamespace(label_save=[], only_index=True)
        empty_panel = SimpleNamespace(clear=lambda: None)
        window = SimpleNamespace(
            task_draft_points=[],
            task_pose_bbox=[10, 20, 110, 180],
            task_pose_points=[[30, 40, 2], [50, 60, 1]],
            task_drag=None,
            task_edit=None,
            is_add_box=False,
            is_update_label=False,
            is_first_add_box=True,
            is_first_update_label=True,
            detect_drag_original=None,
            detect_drag_start_org=None,
            mouse_left_press=False,
            mouse_save_temp=None,
            hand_flag=False,
            rect_save=None,
            rect_save_current=None,
            cross=False,
            hover=False,
            is_choose_rect=False,
            is_choose_rect_index=None,
            is_hover_move_allow=False,
            len_rect=0,
            annotation_task='pose',
            img=image,
            categoryShowWidget=empty_panel,
            boxShowWidget=empty_panel,
            _cancel_interaction_redraw=lambda: None,
            move_xy=lambda *args, **kwargs: redraws.append((args, kwargs)),
            setCursor=lambda cursor: None,
            statusBar=lambda: SimpleNamespace(
                showMessage=lambda message, _timeout=0: messages.append(message)),
        )

        cancelled = MainWin._cancel_current_annotation(window)

        self.assertTrue(cancelled)
        self.assertIsNone(window.task_pose_bbox)
        self.assertEqual(window.task_pose_points, [])
        self.assertFalse(window._ignore_left_release)
        self.assertFalse(image.only_index)
        self.assertEqual(len(redraws), 1)
        self.assertIn('已取消当前操作', messages[-1])

    def test_cancel_detect_draft_removes_only_unsaved_box(self):
        popped = []

        class DraftImage:
            def __init__(self):
                self.label_save = [[2, 10, 20, 100, 120]]
                self.only_index = True

            def pop(self, index):
                popped.append(index)
                self.label_save.pop(index)

        empty_panel = SimpleNamespace(clear=lambda: None)
        image = DraftImage()
        window = SimpleNamespace(
            task_draft_points=[], task_pose_bbox=None,
            task_pose_points=[], task_drag=None, task_edit=None,
            is_add_box=True, is_update_label=False,
            is_first_add_box=False, is_first_update_label=True,
            detect_drag_original=None, detect_drag_start_org=None,
            mouse_left_press=True, mouse_save_temp=(20, 30), hand_flag=False,
            rect_save=None, rect_save_current=[0, -1, image.label_save[0]],
            cross=False, hover=False, is_choose_rect=True,
            is_choose_rect_index=0, is_hover_move_allow=False,
            len_rect=1, annotation_task='detect', img=image,
            categoryShowWidget=empty_panel, boxShowWidget=empty_panel,
            _cancel_interaction_redraw=lambda: None,
            move_xy=lambda *args, **kwargs: None,
            setCursor=lambda cursor: None,
            statusBar=lambda: SimpleNamespace(showMessage=lambda *args: None),
        )

        cancelled = MainWin._cancel_current_annotation(window)

        self.assertTrue(cancelled)
        self.assertEqual(popped, [0])
        self.assertEqual(image.label_save, [])
        self.assertEqual(window.len_rect, 0)
        self.assertTrue(window._ignore_left_release)
        self.assertFalse(window.is_add_box)

    def test_escape_uses_shared_annotation_cancel(self):
        accepted = []
        event = SimpleNamespace(
            key=lambda: Qt.Key_Escape,
            accept=lambda: accepted.append(True),
        )
        window = SimpleNamespace(
            img_is_load=True,
            _cancel_current_annotation=lambda: True,
        )

        MainWin.keyPressEvent(window, event)

        self.assertEqual(accepted, [True])

    def test_pose_right_click_uses_shared_cancel_before_delete(self):
        actions = []
        event = SimpleNamespace(
            type=lambda: QEvent.MouseButtonPress,
            button=lambda: Qt.RightButton,
        )
        window = SimpleNamespace(
            label=object(), mouse_pos=None,
            _event_canvas_pos=lambda source, current_event: (30, 40),
            _cancel_interaction_redraw=lambda: actions.append('stop'),
            _cancel_current_annotation=lambda: actions.append('cancel') or True,
            is_choose_rect=True,
            deleteBox_=lambda: actions.append('delete'),
        )

        handled = MainWin._task_event_filter(window, event)

        self.assertTrue(handled)
        self.assertEqual(actions, ['stop', 'cancel'])

    def test_segment_blank_click_deselects_before_starting_new_polygon(self):
        actions = []
        messages = []
        event = SimpleNamespace(
            type=lambda: QEvent.MouseButtonPress,
            button=lambda: Qt.LeftButton,
            modifiers=lambda: Qt.NoModifier,
        )
        image = SimpleNamespace(
            task_hit_test=lambda x, y: (None, -1, -1),
            new_xy_to_org_xy=lambda point: point,
        )
        window = SimpleNamespace(
            label=object(), mouse_pos=None, annotation_task='segment',
            task_draft_points=[], is_choose_rect=True,
            is_choose_rect_index=2, img=image,
            _event_canvas_pos=lambda source, current_event: (30, 40),
            _cancel_interaction_redraw=lambda: None,
            _cancel_current_annotation=lambda: False,
            pos_in_org=lambda position: True,
            _clear_task_selection=lambda: actions.append('deselect'),
            move_xy=lambda *args, **kwargs: actions.append('redraw'),
            _redraw_task_draft=lambda **kwargs: actions.append('draft'),
            statusBar=lambda: SimpleNamespace(
                showMessage=lambda message, _timeout=0: messages.append(message)),
        )

        handled = MainWin._task_event_filter(window, event)

        self.assertTrue(handled)
        self.assertEqual(actions, ['deselect', 'redraw'])
        self.assertEqual(window.task_draft_points, [])
        self.assertIn('再次点击空白开始绘制', messages[-1])

        actions.clear()
        window.is_choose_rect = False
        MainWin._task_event_filter(window, event)

        self.assertEqual(window.task_draft_points, [(30, 40)])
        self.assertEqual(actions, ['deselect', 'draft'])

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
                _request_annotation_category_picker=(
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
            _request_annotation_category_picker=(
                lambda index, position: opened.append(
                    ('detect', index, position))),
        )
        MainWin.eventFilter(detect_window, label, event)

        self.assertEqual([entry[:2] for entry in opened], [
            ('segment', 2), ('obb', 2), ('pose', 2), ('detect', 2)])

    def test_category_picker_is_deferred_until_double_click_returns(self):
        callbacks = []
        opened = []
        image = SimpleNamespace(label_save=[[0, 1, 2, 3, 4]],
                                only_index=True)
        window = SimpleNamespace(
            _category_picker_request_id=0,
            _ignored_release_request_id=None,
            img=image,
            annotation_task='detect',
            mouse_left_press=True,
            is_add_box=False,
            is_update_label=True,
            task_edit=None,
            task_drag=None,
            detect_drag_original=[0, 1, 2, 3, 4],
            detect_drag_start_org=(1, 2),
            _cancel_interaction_redraw=lambda: None,
            _open_requested_category_picker=(
                lambda request, current_image, index, position:
                opened.append((request, current_image, index, position))),
            _expire_category_release_guard=lambda request: None,
        )

        with patch.object(
                main_window_module.QTimer, 'singleShot',
                side_effect=lambda _delay, callback: callbacks.append(callback)):
            handled = MainWin._request_annotation_category_picker(
                window, 0, QPoint(30, 40))

        self.assertTrue(handled)
        self.assertEqual(opened, [])
        self.assertTrue(window._ignore_left_release)
        self.assertFalse(window.mouse_left_press)
        self.assertFalse(window.is_update_label)
        self.assertFalse(image.only_index)
        self.assertEqual(len(callbacks), 2)

        callbacks[0]()

        self.assertEqual(opened[0][0:3], (1, image, 0))

    def test_detect_double_click_recovers_from_malformed_annotation(self):
        messages = []

        class DoubleClickEvent:
            @staticmethod
            def pos():
                return QPoint(30, 40)

        label = SimpleNamespace(
            mapToGlobal=lambda point: QPoint(point.x() + 100,
                                             point.y() + 200))
        window = SimpleNamespace(
            img=SimpleNamespace(
                label_save=[[0, 1, 2, 3, 4, 5]],
                hit_test=lambda x, y: ('rect', 0, -1)),
            is_choose_rect_index=None,
            temp_widget=None,
            mouse_left_press=True,
            is_add_box=True,
            is_update_label=True,
            _event_canvas_pos=lambda source, event: (30, 40),
            _show_annotation_category_picker=lambda index, position: None,
            statusBar=lambda: SimpleNamespace(
                showMessage=lambda message, _timeout=0:
                messages.append(message)),
        )

        handled = MainWin._handle_detect_double_click(
            window, label, DoubleClickEvent())

        self.assertTrue(handled)
        self.assertFalse(window.mouse_left_press)
        self.assertFalse(window.is_add_box)
        self.assertFalse(window.is_update_label)
        self.assertIn('DOUBLE CLICK RECOVERED', messages[-1])

    def test_interaction_redraw_coalesces_to_latest_pointer_frame(self):
        class FakeTimer:
            def __init__(self):
                self.active = False
                self.starts = 0

            def isActive(self):
                return self.active

            def start(self, _delay=None):
                self.active = True
                self.starts += 1

        timer = FakeTimer()
        window = SimpleNamespace(
            _pending_interaction_redraw=None,
            _interaction_redraw_timer=timer,
            _last_interaction_redraw_at=100.0,
            _interaction_frame_interval_ms=8.0,
            _flush_interaction_redraw=lambda: None,
        )

        with patch.object(
                main_window_module.time, 'perf_counter', return_value=100.001):
            MainWin._queue_interaction_redraw(
                window, 'task_drag', cursor=(10, 20))
            MainWin._queue_interaction_redraw(
                window, 'task_drag', cursor=(80, 90))

        self.assertEqual(timer.starts, 1)
        self.assertEqual(window._pending_interaction_redraw, (
            'task_drag', {'cursor': (80, 90)}))

    def test_first_interaction_frame_is_rendered_without_timer_delay(self):
        rendered = []

        class FakeTimer:
            @staticmethod
            def isActive():
                return False

            @staticmethod
            def start(_delay=None):
                raise AssertionError('首帧不应等待定时器')

        window = SimpleNamespace(
            _pending_interaction_redraw=None,
            _interaction_redraw_timer=FakeTimer(),
            _last_interaction_redraw_at=0.0,
            _interaction_frame_interval_ms=8.0,
            _flush_interaction_redraw=lambda: rendered.append(True),
        )

        MainWin._queue_interaction_redraw(window, 'detect_add')

        self.assertEqual(rendered, [True])

    def test_detect_drag_renders_dashed_draft_instead_of_solid_box(self):
        calls = []
        frame = object()

        class FakeImage:
            label_save = [[0, 10, 20, 110, 80]]

            @staticmethod
            def overlay_frame():
                return frame

            @staticmethod
            def label_show(index, **kwargs):
                calls.append(('labels', index, kwargs))

            @staticmethod
            def draw_task_draft(**kwargs):
                calls.append(('draft', kwargs))

        window = SimpleNamespace(
            img=FakeImage(),
            is_choose_rect_index=0,
            addBox=lambda redraw=True: calls.append(('add', redraw)),
            _interaction_frame=(
                lambda excluded_index=None: (
                    calls.append(('base', excluded_index)), frame)[1]),
            label=SimpleNamespace(
                setPixmap=lambda pixmap: calls.append(('commit', pixmap))),
        )

        MainWin._render_interaction_redraw(window, 'detect_add', {})

        self.assertEqual(calls[0], ('add', False))
        self.assertEqual(calls[1], ('base', 0))
        self.assertEqual(calls[2][0], 'draft')
        self.assertEqual(calls[2][1]['bbox'], [10, 20, 110, 80])
        self.assertIs(calls[-1][1], frame)


if __name__ == '__main__':
    unittest.main()
