import os
import shutil
import sys
import math
import yaml
from pathlib import Path

from PyQt5 import uic, QtGui
from PyQt5.QtCore import Qt, QEvent, QTimer, QSize
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (QMainWindow, QFileDialog, QListWidget, QMessageBox,
                             QColorDialog, QShortcut, QWidget, QVBoxLayout,
                             QPushButton, QButtonGroup, QSplitter,
                             QAbstractItemView, QSizePolicy, QMenu,
                             QWidgetAction, QLabel, QSlider, QHBoxLayout,
                             QApplication, QDialog, QDialogButtonBox,
                             QKeySequenceEdit, QActionGroup, QLineEdit,
                             QSpinBox, QComboBox)

from .CategoryApp import CategoryApp
from .tempCatewidget import CategoryApp as tempWidget
from .LabelApp import LabelApp
from .ImageApp import Image
from .DataApp import DataApp
from .thumbnailApp import thumbnailApp
from .modificationCls import modificationCls
from .common_fun import distance, root
from .class_styles import build_class_styles, normalize_class_style
from .industrial_theme import INDUSTRIAL_QSS
from .ui_icons import toolbar_icon
from .window_chrome import (AdjustableSplitter, BackgroundGlassPanel,
                            BackgroundViewportBinder, BackgroundWidget,
                            TitleBar)

root = root.parent

DEFAULT_SHORTCUTS = {
    'previous_image': ('上一张图片', 'Z'),
    'next_image': ('下一张图片', 'X'),
    'detect': ('执行检测', 'C'),
    'delete_box': ('删除标注', 'Delete'),
    'zoom_in': ('放大画布', '='),
    'zoom_out': ('缩小画布', '-'),
    'reset_view': ('重置画布', '0'),
    'save_labels': ('保存标签', 'Ctrl+S'),
}

COCO_KEYPOINT_NAMES = (
    '鼻子', '左眼', '右眼', '左耳', '右耳', '左肩', '右肩',
    '左肘', '右肘', '左腕', '右腕', '左髋', '右髋', '左膝',
    '右膝', '左踝', '右踝',
)
COCO_KEYPOINT_SKELETON = (
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
    (5, 11), (6, 12), (11, 12), (11, 13), (13, 15),
    (12, 14), (14, 16), (0, 1), (0, 2), (1, 3), (2, 4),
)


class MainWin(QMainWindow):
    # 总窗口
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QtGui.QIcon(str(
            Path(__file__).parent / 'material' / 'app_icon.ico')))

        # -———————————————————————————————— UI相关变量 ————————————————————————————————#

        # *** 从这里加载ui文件，搭建界面 ***
        self.ui = uic.loadUi(str(root / "utils/qt_ui_file/main.ui"), self)

        # *** 显示用的label, 主屏幕 ***
        self.label = self.ui.label
        self.label.installEventFilter(self)

        # *** 显示用的label, 用来显示当前图片的名字， 在最下方 ***
        self.current_label_name_show = self.ui.character_label  # 用来展示当前图片的名字

        # *** 显示当前文件夹下所有图片的名字,  变成缩略图 ***
        self.thumbnail_widget = None
        self.thumbnail_preview_size = 80

        self.temp_widget = None

        # *** 用来显示选中哪个框,用来切换框 ***
        self.boxShowWidget = LabelApp(self)

        # *** 如果鼠标选中了某个框, 用来显示和更新类别名 ***
        self.categoryShowWidget = CategoryApp(self)

        # *** UI界面上的按钮 ***
        self.arrows_button = self.ui.arrows  # 切换鼠标样式->箭头
        self.hand_button = self.ui.hand  # 切换鼠标样式->手
        self.open_folder = self.ui.openFolder  # 打开文件夹
        self.open_file = self.ui.openFile  # 打开文件
        self.imgUP = self.ui.imgUP  # 放大图片
        self.imgDOWN = self.ui.imgDOWN  # 缩小图片
        self.readFolderLabel = self.ui.readFolderLabel  # 读取文件夹的中的标签
        self.resetShowImg = self.ui.resetShowImg  # 重置图片显示
        self.save_label = self.ui.save  # 保存
        self.deleteBox = self.ui.deleteBox  # 删除选则的框
        self.cls_color = self.ui.cls_color  # 从轮盘中选则颜色, 并且更改当前类别的颜色
        self.renew_cls = self.ui.renewCls  # 修改类别名

        self.show_box_circle = self.ui.checkBox1  # 显示框和点
        self.show_other = self.ui.checkBox  # 显示其他类别的框和点
        self.show_box_fill = self.ui.checkBox2  # 显示框的填充
        self.show_box_text = self.ui.checkBox3  # 显示框的文字

        self.load_model = self.ui.load_model  # 导入模型
        self.detect = self.ui.detect  # 检测
        self.lineEdit = self.ui.lineEdit  # 检测置信度

        # —————————————————————————————   素材   ————————————————————————————#
        folder = QtGui.QPixmap(str(root / "utils/material/folder.png"))
        file = QtGui.QPixmap(str(root / "utils/material/file.png"))
        label = QtGui.QPixmap(str(root / "utils/material/label.png"))
        hand = QtGui.QPixmap(str(root / "utils/material/hand.png"))
        arrows = QtGui.QPixmap(str(root / "utils/material/arrow.png"))
        Down = QtGui.QPixmap(str(root / "utils/material/down.png"))
        Up = QtGui.QPixmap(str(root / "utils/material/Up.png"))
        reset = QtGui.QPixmap(str(root / "utils/material/reset.png"))
        export = QtGui.QPixmap(str(root / "utils/material/export.png"))
        color = QtGui.QPixmap(str(root / "utils/material/color.png"))

        self.open_folder.setIcon(QtGui.QIcon(folder.scaled(15, 15, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
        self.open_file.setIcon(QtGui.QIcon(file.scaled(15, 15, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
        self.readFolderLabel.setIcon(QtGui.QIcon(label.scaled(15, 15, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
        self.hand_button.setIcon(QtGui.QIcon(hand.scaled(15, 15, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
        self.arrows_button.setIcon(QtGui.QIcon(arrows.scaled(15, 15, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
        self.imgDOWN.setIcon(QtGui.QIcon(Down.scaled(15, 15, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
        self.imgUP.setIcon(QtGui.QIcon(Up.scaled(15, 15, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
        self.resetShowImg.setIcon(QtGui.QIcon(reset.scaled(15, 15, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
        self.save_label.setIcon(QtGui.QIcon(export.scaled(15, 15, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
        self.cls_color.setIcon(QtGui.QIcon(color.scaled(15, 15, Qt.KeepAspectRatio, Qt.SmoothTransformation)))

        # ————————————————————————————— 快捷键相关变量 ————————————————————————————#
        self.shortcut_bindings = {
            key: default for key, (_label, default) in DEFAULT_SHORTCUTS.items()
        }
        self.shortcuts = {}
        self.wheel_pan_enabled = True
        self.wheel_zoom_enabled = True
        self._create_shortcuts()

        # ———————————————————————————————— 信号槽 ————————————————————————————————#

        self.arrows_button.clicked.connect(self.arrows_button_)
        self.hand_button.clicked.connect(self.hand_button_)
        self.open_folder.clicked.connect(self.select_folder)
        self.open_file.clicked.connect(self.select_file)
        self.readFolderLabel.clicked.connect(self.readFolderLabel_)
        self.imgUP.clicked.connect(self.imgUp_)
        self.imgDOWN.clicked.connect(self.imgDown_)
        self.resetShowImg.clicked.connect(self.resetShowImg_)
        self.save_label.clicked.connect(self.save_)
        self.deleteBox.clicked.connect(self.deleteBox_)
        self.cls_color.clicked.connect(self.cls_color_)
        self.renew_cls.clicked.connect(self.renew_cls_)
        self.show_box_circle.stateChanged.connect(self.show_box_circle_)
        self.show_other.stateChanged.connect(self.show_other_)
        self.show_box_fill.stateChanged.connect(self.show_box_fill_)
        self.show_box_text.stateChanged.connect(self.show_box_text_)
        self.detect.clicked.connect(self.detect_)

        # ———————————————————————————————— 事件相关变量 ————————————————————————————————#

        self.mouse_left_press = False  # 鼠标左键按下
        self.mouse_right_press = False  # 鼠标右键按下
        self.mouse_pos = None  # 鼠标当前位置
        self.mouse_press_pos = None  # 鼠标按下的位置(左键按下的位置)
        self.move_pos_track = []  # 移动轨迹(用来绘制鼠标操作的移动轨迹，最多保存8个点)
        self.key_press = False  # 键盘按键是否按下了Ctrl

        # ———————————————————————————————— 按钮相关变量 ————————————————————————————————#

        self.hand = False  # 手型鼠标的标记
        self.temp_hand = False  # 临时手型鼠标的标记
        self.hand_flag = False  # 握紧手型鼠标的标记
        self.arrows = True  # 箭头鼠标的标记
        self.cross = False  # 十字鼠标的标记, 鼠标悬停在点上面的时候使用
        self.hover = False  # 悬停鼠标的标记

        # ———————————————————————————————— 图像相关变量 ————————————————————————————————#

        self.img_is_load = False  # 图片是否加载
        self.img = None  # 当前操作的图片
        self.annotation_task = 'detect'
        self.kpt_shape = (17, 3)
        self.keypoint_names = list(COCO_KEYPOINT_NAMES)
        self.kpt_skeleton = list(COCO_KEYPOINT_SKELETON)
        self.task_draft_points = []
        self.task_pose_bbox = None
        self.task_pose_points = []
        self.task_drag = None
        self.task_edit = None
        self.detect_drag_original = None
        self.detect_drag_start_org = None

        self.is_update_label = False  # 是否正在更新框的label
        self.is_update_label_save = None  # 保存更新框的label的信息 [box_index, img.label_save[index], img.basedata[index]]
        self.is_first_update_label = True  # 是否是第一次更新label

        self.is_add_box = False  # 是否在添加框
        self.is_first_add_box = True  # 是否是第一次更新label, 因为第一次添加框，后面都是修改框的label,用来区分是添加还是修改
        self.add_label_save = None  # 添加框的label的信息 [box_index, img.label_save[index], img.basedata[index]]

        self.is_open_folder = False  # 是否加载了了文件夹中的图片
        self.is_open_file = False  # 是否打加载了图片
        self.is_choose_rect = False  # 是否选择了框
        self.is_choose_rect_index = None  # 选择的框的索引
        self.is_choose_rect_over_striking = False  # 是否框已经加粗了

        self.is_hover_move_allow = False  # 是否可以移动框
        self.is_hover_move_rect = False  # 是否在移动框

        self.default_save_path = root / 'utils/temp_folder'  # 默认保存路径
        self.choose_save_path = None  # 选择的保存路径
        self.label_list = set()  # 第一次加载的时候, 要初始化本地标签文件到图片上, 存放所有标签全路径
        self.label_list_only_name = set()
        self.img_list = set()  # 存放所有图片全路径
        self.img_list_only_name = set()

        self.mouse_save_temp = None  # 临时记录显示的图片的中心在label中的位置
        self.circle_save = None  # 保存鼠标悬停的点的的信息 [box_index, circle_index, img.label_save[index], img.basedata[index]]
        self.rect_save = None  # 保存鼠标悬停的框的信息 [box_index, img.label_save[index], img.basedata[index]]
        self.rect_save_current = None  # 保存当前选中的框的信息 [box_index, img.label_save[index], img.basedata[index]]
        self.rect_save = None  # 保存鼠标悬停的框的信息 [box_index, img.label_save[index], img.basedata[index]]

        self.mouse_with_nine_circle = None  # 保存鼠标悬停的点的的信息 [box_index, circle_index, img.label_save[index], img.basedata[index]]
        self.mouse_with_box = None  # 保存鼠标悬停的框的信息 [box_index, img.label_save[index], img.basedata[index]]

        self.wheel_scale = 1  # 图片放大的倍数, 当前图片相对于label尺寸的缩放倍数
        self.cls = 0  # 当前类别, 新添加的标签默认使用上一次的标签名
        self.names = None  # 类别名字列表
        self.colors = dict()  # 类别颜色列表
        self.class_styles = dict()  # 每类独立的边框色与填充色

        self.len_rect = 0  # 当前图片已经添加的框的总数量

        self.label_height = self.label.size().height()  # label的高度
        self.label_width = self.label.size().width()  # label的宽度

        self.change_label_name = None

        self.yolov8_model = None
        self.conf = 0.5
        self.load_model_thread = None
        self.detect_thread = None
        self._detect_target = None
        self._background_initialized = False
        self._modification_window = None
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._refresh_after_resize)
        self._obb_save_timer = QTimer(self)
        self._obb_save_timer.setSingleShot(True)
        self._obb_save_timer.setInterval(240)
        self._obb_save_timer.timeout.connect(self._save_obb_wheel_change)
        # 高频 MouseMove 只保留最新一帧，避免整张画布重绘请求排队。
        # 8 ms 上限约为 120 FPS，既能保持跟手，也给事件循环留出时间。
        self._interaction_redraw_timer = QTimer(self)
        self._interaction_redraw_timer.setSingleShot(True)
        self._interaction_redraw_timer.setInterval(8)
        self._interaction_redraw_timer.timeout.connect(
            self._flush_interaction_redraw)
        self._pending_interaction_redraw = None

        # ———————————————————————————————— 初始化 ————————————————————————————————#
        self._apply_industrial_ui()
        self.init()

    def _apply_industrial_ui(self):
        """Apply one coherent, production-oriented visual system to the UI."""
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setWindowTitle('LabelS  |  Industrial Vision Annotation')
        self.setMinimumSize(1100, 720)
        self.resize(1400, 860)

        # The designer file contains per-widget legacy styles. Clearing them
        # lets the central theme remain the single source of truth.
        for widget in self.findChildren(QWidget):
            widget.setStyleSheet('')

        content_widget = self.takeCentralWidget()
        self.window_shell = BackgroundWidget(self)
        self.shell_layout = QVBoxLayout(self.window_shell)
        self.shell_layout.setContentsMargins(1, 1, 1, 0)
        self.shell_layout.setSpacing(0)
        self.title_bar = TitleBar(self)
        self.shell_layout.addWidget(self.title_bar)
        self.shell_layout.addWidget(content_widget, 1)
        self.setCentralWidget(self.window_shell)

        self.ui.gridLayout.setContentsMargins(8, 8, 8, 8)
        self.ui.gridLayout.setHorizontalSpacing(8)
        self.ui.gridLayout.setVerticalSpacing(6)
        self.ui.gridLayout_2.setSpacing(0)
        self.ui.gridLayout_3.setSpacing(0)
        self.ui.gridLayout_4.setSpacing(0)
        self.ui.gridLayout_6.setContentsMargins(6, 3, 6, 3)
        self.ui.gridLayout_6.setSpacing(4)
        self.ui.horizontalLayout_6.setContentsMargins(5, 4, 5, 4)
        self.ui.horizontalLayout_6.setSpacing(5)

        self.ui.horizontalGroupBox.setFixedHeight(34)
        self.ui.temp.setFixedHeight(34)
        self.ui.temp.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.label.setMinimumSize(600, 500)
        self.label.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setText('NO IMAGE LOADED\n\nOPEN A FILE OR DATASET TO START')
        self.current_label_name_show.setFixedHeight(28)
        self.current_label_name_show.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.ui.thumbnailWidget.setMinimumWidth(0)
        self.ui.thumbnailWidget.setMaximumWidth(16777215)
        self.ui.thumbnailWidget.setFrameShape(QListWidget.NoFrame)
        self.ui.label_2.setMinimumWidth(0)
        self.ui.label_2.setMaximumWidth(16777215)
        for widget in (self.ui.clsShow, self.ui.labelShow, self.ui.label_3, self.ui.label_5):
            widget.setMinimumWidth(210)
            widget.setMaximumWidth(210)
        for list_widget in (self.ui.labelShow, self.ui.clsShow):
            # Remove legacy Designer minimum heights (358/359 px). They make
            # the list overflow a resized inspector section and truncate its
            # effective scroll range.
            list_widget.setMinimumHeight(0)
            list_widget.setMaximumHeight(16777215)
            list_widget.setSizePolicy(
                QSizePolicy.Preferred, QSizePolicy.Expanding)
        for list_widget in (
                self.ui.thumbnailWidget, self.ui.labelShow, self.ui.clsShow):
            list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            list_widget.setAutoFillBackground(False)
        self.ui.thumbnailWidget.setVerticalScrollMode(
            QAbstractItemView.ScrollPerPixel)
        self.ui.labelShow.setVerticalScrollMode(
            QAbstractItemView.ScrollPerItem)
        self.ui.clsShow.setVerticalScrollMode(
            QAbstractItemView.ScrollPerItem)

        self.ui.thumbnailWidget.viewport().setObjectName(
            'transparentListViewport')
        self.ui.thumbnailWidget.viewport().setAutoFillBackground(False)
        self.ui.thumbnailWidget.viewport().setAttribute(
            Qt.WA_TranslucentBackground, True)

        self._right_viewport_binders = [
            BackgroundViewportBinder(
                self.window_shell, self.ui.thumbnailWidget.viewport(), self),
            BackgroundViewportBinder(
                self.window_shell, self.ui.labelShow.viewport(), self),
            BackgroundViewportBinder(
                self.window_shell, self.ui.clsShow.viewport(), self),
        ]

        section_titles = {
            self.ui.label_2: '图像队列',
            self.ui.label_3: '标注对象',
            self.ui.label_5: '类别属性',
        }
        for label, text in section_titles.items():
            label.setText(text)
            label.setProperty('role', 'sectionTitle')
            label.setFixedHeight(34)
            label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            label.setStyleSheet(
                'color: #263640; background: rgba(245, 248, 250, 168); border: 0; '
                'border-bottom: 1px solid rgba(122, 143, 154, 105); padding: 0 12px; '
                'font-size: 12px; font-weight: 600;')

        self.ui.renewCls.setText('类别管理')
        self.ui.load_model.setText('加载模型  ▾')
        self.ui.detect.setVisible(False)
        self.ui.save_5.setText('快捷键  ▾')
        self.ui.save_2.setVisible(False)  # 尚未接入的入口不在生产界面中展示
        self.background_button = QPushButton('窗口  ▾', self)
        self.background_button.setObjectName('backgroundButton')
        self.background_button.setFixedSize(62, 24)
        self.background_button.setProperty('toolbarControl', True)
        self.background_button.setToolTip('窗口与背景设置')
        self.background_button.clicked.connect(self.show_background_menu)
        self.ui.horizontalLayout_6.insertWidget(4, self.background_button, 0, Qt.AlignVCenter)

        self.task_button = QPushButton('任务：检测  ▾', self)
        self.task_button.setObjectName('taskButton')
        self.task_button.setFixedSize(88, 24)
        self.task_button.setProperty('toolbarControl', True)
        self.task_button.setToolTip('选择 YOLO 标注任务')
        self.task_button.clicked.connect(self.show_task_menu)
        self.task_menu = QMenu(self)
        self.task_menu.setObjectName('taskMenu')
        self.task_action_group = QActionGroup(self)
        self.task_action_group.setExclusive(True)
        self.task_actions = {}
        for task, label in (
                ('detect', '检测框'), ('segment', '实例分割'),
                ('obb', 'OBB 旋转框'), ('pose', '关键点')):
            action = self.task_menu.addAction(label)
            action.setCheckable(True)
            action.setData(task)
            action.triggered.connect(
                lambda _checked=False, value=task: self.set_annotation_task(value))
            self.task_action_group.addAction(action)
            self.task_actions[task] = action
        self.task_actions['detect'].setChecked(True)
        self.task_menu.addSeparator()
        self.keypoint_config_action = self.task_menu.addAction('关键点配置…')
        self.keypoint_config_action.triggered.connect(
            self.configure_keypoints)

        self.background_menu = QMenu(self)
        self.background_menu.setObjectName('backgroundMenu')
        self.background_import_action = self.background_menu.addAction(
            toolbar_icon('image'), '导入窗口背景')
        self.background_import_action.triggered.connect(
            self.choose_background_image)
        self.background_reset_action = self.background_menu.addAction(
            toolbar_icon('reset'), '还原窗口默认值')
        self.background_reset_action.triggered.connect(
            self.restore_default_window)
        self.background_menu.addSeparator()

        opacity_widget = QWidget(self.background_menu)
        opacity_widget.setObjectName('backgroundOpacityMenu')
        opacity_layout = QHBoxLayout(opacity_widget)
        opacity_layout.setContentsMargins(12, 5, 10, 7)
        opacity_layout.setSpacing(8)
        opacity_caption = QLabel('背景透明度', opacity_widget)
        self.background_opacity = QSlider(Qt.Horizontal, opacity_widget)
        self.background_opacity.setRange(0, 100)
        self.background_opacity.setValue(65)
        self.background_opacity.setFixedWidth(112)
        self.background_opacity.setProperty('menuSlider', True)
        self.background_opacity_value = QLabel('65%', opacity_widget)
        self.background_opacity_value.setObjectName('backgroundOpacityValue')
        self.background_opacity_value.setFixedWidth(34)
        opacity_layout.addWidget(opacity_caption)
        opacity_layout.addWidget(self.background_opacity)
        opacity_layout.addWidget(self.background_opacity_value)
        opacity_action = QWidgetAction(self.background_menu)
        opacity_action.setDefaultWidget(opacity_widget)
        self.background_menu.addAction(opacity_action)

        self.background_opacity.valueChanged.connect(self.update_background_opacity)
        self.background_opacity.valueChanged.connect(
            lambda value: self.background_opacity_value.setText(f'{value}%'))
        self.background_opacity.sliderReleased.connect(
            self.save_background_opacity)
        self.background_menu.aboutToHide.connect(
            self.save_background_opacity)

        thumbnail_widget = QWidget(self.background_menu)
        thumbnail_widget.setObjectName('thumbnailSizeMenu')
        thumbnail_layout = QHBoxLayout(thumbnail_widget)
        thumbnail_layout.setContentsMargins(12, 5, 10, 7)
        thumbnail_layout.setSpacing(8)
        thumbnail_caption = QLabel('预览图大小', thumbnail_widget)
        self.thumbnail_size_slider = QSlider(Qt.Horizontal, thumbnail_widget)
        self.thumbnail_size_slider.setRange(56, 128)
        self.thumbnail_size_slider.setValue(80)
        self.thumbnail_size_slider.setFixedWidth(112)
        self.thumbnail_size_slider.setProperty('menuSlider', True)
        self.thumbnail_size_value = QLabel('80 px', thumbnail_widget)
        self.thumbnail_size_value.setObjectName('thumbnailSizeValue')
        self.thumbnail_size_value.setFixedWidth(42)
        thumbnail_layout.addWidget(thumbnail_caption)
        thumbnail_layout.addWidget(self.thumbnail_size_slider)
        thumbnail_layout.addWidget(self.thumbnail_size_value)
        thumbnail_action = QWidgetAction(self.background_menu)
        thumbnail_action.setDefaultWidget(thumbnail_widget)
        self.background_menu.addAction(thumbnail_action)

        self.thumbnail_size_slider.valueChanged.connect(
            self.update_thumbnail_size)
        self.thumbnail_size_slider.valueChanged.connect(
            lambda value: self.thumbnail_size_value.setText(f'{value} px'))
        self.thumbnail_size_slider.sliderReleased.connect(
            self.save_thumbnail_size)
        self.background_menu.aboutToHide.connect(self.save_thumbnail_size)

        self.ui.label_4.setVisible(False)
        self.lineEdit.setVisible(False)
        self.load_model.setToolTip('模型与置信度设置')
        self.load_model.clicked.connect(self.show_model_menu)
        self.model_menu = QMenu(self)
        self.model_menu.setObjectName('modelMenu')
        self.model_import_action = self.model_menu.addAction(
            toolbar_icon('import'), '导入模型')
        self.model_import_action.triggered.connect(self.load_model_)
        self.model_run_action = self.model_menu.addAction(
            toolbar_icon('cursor'), '执行当前模型')
        self.model_run_action.triggered.connect(self.detect_)
        self.model_menu.addSeparator()

        confidence_widget = QWidget(self.model_menu)
        confidence_widget.setObjectName('modelConfidenceMenu')
        confidence_layout = QHBoxLayout(confidence_widget)
        confidence_layout.setContentsMargins(12, 5, 10, 7)
        confidence_layout.setSpacing(8)
        confidence_caption = QLabel('置信度', confidence_widget)
        self.confidence_control = QSlider(Qt.Horizontal, confidence_widget)
        self.confidence_control.setRange(0, 100)
        self.confidence_control.setValue(50)
        self.confidence_control.setFixedWidth(112)
        self.confidence_control.setProperty('menuSlider', True)
        self.confidence_value = QLabel('0.50', confidence_widget)
        self.confidence_value.setObjectName('modelConfidenceValue')
        self.confidence_value.setFixedWidth(36)
        confidence_layout.addWidget(confidence_caption)
        confidence_layout.addWidget(self.confidence_control)
        confidence_layout.addWidget(self.confidence_value)
        confidence_action = QWidgetAction(self.model_menu)
        confidence_action.setDefaultWidget(confidence_widget)
        self.model_menu.addAction(confidence_action)

        self.confidence_control.valueChanged.connect(self.update_confidence)
        self.confidence_control.valueChanged.connect(
            lambda value: self.confidence_value.setText(f'{value / 100:.2f}'))
        self.confidence_control.sliderReleased.connect(
            self.save_model_confidence)
        self.model_menu.aboutToHide.connect(self.save_model_confidence)

        self.show_box_circle.setText('锚点')
        self.show_box_circle.setToolTip('显示边框调整锚点')
        self.show_other.setText('聚焦')
        self.show_box_fill.setText('填充')
        self.show_box_text.setText('标签')
        self.deleteBox.hide()

        checkbox_widths = {
            self.show_other: 58,
            self.show_box_circle: 58,
            self.show_box_text: 58,
            self.show_box_fill: 58,
        }
        for checkbox, width in checkbox_widths.items():
            checkbox.setMinimumWidth(width)
            checkbox.setMaximumWidth(width)
            checkbox.setFixedHeight(28)

        # Keep the tool actions grouped on the left and pin all display
        # options to the far-right edge of the canvas toolbar.
        toolbar_grid = self.ui.gridLayout_6
        for column, width in ((1, 12), (13, 0)):
            item = toolbar_grid.itemAtPosition(0, column)
            if item is not None and item.spacerItem() is not None:
                item.spacerItem().changeSize(
                    width, 1, QSizePolicy.Fixed, QSizePolicy.Minimum)
        toolbar_grid.setColumnStretch(8, 1)
        toolbar_grid.invalidate()

        compact_buttons = (
            self.arrows_button, self.hand_button, self.open_folder, self.open_file,
            self.imgUP, self.imgDOWN, self.readFolderLabel, self.resetShowImg,
            self.save_label, self.cls_color,
        )
        for button in compact_buttons:
            button.setProperty('compact', True)
            button.setFixedSize(28, 28)
            button.setIconSize(QSize(13, 13))

        toolbar_icons = {
            self.open_file: 'image', self.open_folder: 'folder',
            self.readFolderLabel: 'import', self.save_label: 'export',
            self.arrows_button: 'cursor', self.hand_button: 'hand',
            self.imgUP: 'zoom_in', self.imgDOWN: 'zoom_out',
            self.resetShowImg: 'reset', self.cls_color: 'palette',
        }
        for button, icon_name in toolbar_icons.items():
            button.setIcon(toolbar_icon(icon_name))
            button.setIconSize(QSize(16, 16))
            button.setText('')
            button.setProperty('toolIcon', True)

        self.tool_mode_group = QButtonGroup(self)
        self.tool_mode_group.setExclusive(True)
        for button in (self.arrows_button, self.hand_button):
            button.setCheckable(True)
            self.tool_mode_group.addButton(button)
        self.arrows_button.setChecked(True)

        self.save_label.setProperty('role', 'primary')
        self.deleteBox.setProperty('role', 'danger')
        self._toolbar_min_widths = {
            self.ui.renewCls: 66,
            self.ui.load_model: 82,
            self.ui.save_5: 78,
            self.task_button: 88,
            self.background_button: 62,
        }
        for button in self._toolbar_min_widths:
            button.setFixedHeight(24)
            button.setProperty('toolbarControl', True)
            self.ui.horizontalLayout_6.setAlignment(button, Qt.AlignVCenter)

        self.title_bar.add_toolbar_widgets(
            self.ui.renewCls,
            self.task_button,
            self.ui.load_model,
            self.background_button,
            self.ui.save_5,
        )

        # Rebuild the workspace into one header row and one content row.  The
        # canvas toolbar now aligns with the image-queue heading, while the
        # right column uses a draggable vertical splitter.
        workspace_grid = self.ui.gridLayout
        workspace_grid.removeWidget(self.ui.horizontalGroupBox)
        workspace_grid.removeWidget(self.ui.label_2)
        workspace_grid.removeWidget(self.ui.thumbnailWidget)
        workspace_grid.removeItem(self.ui.gridLayout_2)
        workspace_grid.removeItem(self.ui.gridLayout_3)
        workspace_grid.removeItem(self.ui.gridLayout_4)
        self.ui.gridLayout_2.removeWidget(self.ui.temp)
        self.ui.gridLayout_2.removeWidget(self.label)
        self.ui.gridLayout_2.removeWidget(self.current_label_name_show)

        self.right_splitter = AdjustableSplitter(
            Qt.Vertical, self.ui.centralwidget,
            background_host=self.window_shell)
        self.right_splitter.setObjectName('rightSectionSplitter')
        self.right_splitter.setAttribute(Qt.WA_StyledBackground, True)
        self.right_splitter.setChildrenCollapsible(False)

        self.object_section = BackgroundGlassPanel(
            self.window_shell, self.right_splitter)
        self.object_section.setMinimumHeight(90)
        object_layout = QVBoxLayout(self.object_section)
        object_layout.setContentsMargins(0, 0, 0, 0)
        object_layout.setSpacing(0)
        object_layout.addWidget(self.ui.label_3)
        object_layout.addWidget(self.ui.labelShow, 1)

        self.class_section = BackgroundGlassPanel(
            self.window_shell, self.right_splitter)
        self.class_section.setMinimumHeight(90)
        class_layout = QVBoxLayout(self.class_section)
        class_layout.setContentsMargins(0, 0, 0, 0)
        class_layout.setSpacing(0)
        class_layout.addWidget(self.ui.label_5)
        class_layout.addWidget(self.ui.clsShow, 1)

        self.right_splitter.addWidget(self.object_section)
        self.right_splitter.addWidget(self.class_section)
        self.right_splitter.setStretchFactor(0, 1)
        self.right_splitter.setStretchFactor(1, 1)
        self.right_splitter.setSizes([420, 360])

        self.queue_section = BackgroundGlassPanel(
            self.window_shell, self.ui.centralwidget)
        self.queue_section.setObjectName('queueSection')
        self.queue_section.setMinimumWidth(212)
        self.queue_section.setMaximumWidth(520)
        queue_layout = QVBoxLayout(self.queue_section)
        queue_layout.setContentsMargins(0, 0, 0, 0)
        queue_layout.setSpacing(6)
        queue_layout.addWidget(self.ui.label_2)
        queue_layout.addWidget(self.ui.thumbnailWidget, 1)

        self.canvas_section = BackgroundGlassPanel(
            self.window_shell, self.ui.centralwidget,
            tint=QtGui.QColor(17, 22, 28, 205))
        self.canvas_section.setObjectName('canvasSection')
        canvas_layout = QVBoxLayout(self.canvas_section)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.setSpacing(6)

        self.canvas_toolbar_section = BackgroundGlassPanel(
            self.window_shell, self.canvas_section,
            tint=QtGui.QColor(249, 251, 252, 132))
        self.canvas_toolbar_section.setObjectName('canvasToolbarSurface')
        self.canvas_toolbar_section.setFixedHeight(34)
        toolbar_surface_layout = QVBoxLayout(self.canvas_toolbar_section)
        toolbar_surface_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_surface_layout.addWidget(self.ui.temp)

        self.canvas_status_section = BackgroundGlassPanel(
            self.window_shell, self.canvas_section,
            tint=QtGui.QColor(249, 251, 252, 178))
        self.canvas_status_section.setObjectName('canvasStatusSurface')
        self.canvas_status_section.setFixedHeight(28)
        status_surface_layout = QVBoxLayout(self.canvas_status_section)
        status_surface_layout.setContentsMargins(0, 0, 0, 0)
        status_surface_layout.addWidget(self.current_label_name_show)

        canvas_layout.addWidget(self.canvas_toolbar_section)
        canvas_layout.addWidget(self.label, 1)
        canvas_layout.addWidget(self.canvas_status_section)

        content_section = BackgroundGlassPanel(
            self.window_shell, self.ui.centralwidget,
            tint=QtGui.QColor(247, 249, 251, 28))
        content_section.setObjectName('workspaceContentSection')
        content_layout = QHBoxLayout(content_section)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)
        content_layout.addWidget(self.canvas_section, 1)
        content_layout.addWidget(self.right_splitter)

        self.workspace_splitter = AdjustableSplitter(
            Qt.Horizontal, self.ui.centralwidget,
            background_host=self.window_shell)
        self.workspace_splitter.setObjectName('workspaceSplitter')
        self.workspace_splitter.setChildrenCollapsible(False)
        self.workspace_splitter.addWidget(self.queue_section)
        self.workspace_splitter.addWidget(content_section)
        self.workspace_splitter.setStretchFactor(0, 0)
        self.workspace_splitter.setStretchFactor(1, 1)
        self.workspace_splitter.setSizes([236, 1100])

        workspace_grid.addWidget(self.workspace_splitter, 0, 0, 2, 3)
        workspace_grid.setRowStretch(0, 1)
        workspace_grid.setRowStretch(1, 0)
        workspace_grid.setColumnStretch(0, 1)
        workspace_grid.setColumnStretch(1, 0)
        workspace_grid.setColumnStretch(2, 0)
        self.ui.horizontalGroupBox.hide()
        self.ui.label_3.setFixedHeight(34)

        tooltips = {
            self.open_file: '打开图片文件', self.open_folder: '打开图片目录',
            self.readFolderLabel: '导入 YOLO 标签', self.save_label: '导出标签',
            self.arrows_button: '选择与编辑框', self.hand_button: '平移画布',
            self.imgUP: '放大画布', self.imgDOWN: '缩小画布',
            self.resetShowImg: '重置画布', self.cls_color: '设置类别颜色',
            self.deleteBox: '删除当前选中的标注框', self.detect: '使用当前模型检测当前图片',
            self.ui.save_5: '配置快捷键与鼠标滚轮操作',
        }
        for widget, tooltip in tooltips.items():
            widget.setToolTip(tooltip)

        self._build_shortcut_menu()
        self.ui.save_5.clicked.connect(self.show_shortcut_menu)
        self.setStyleSheet(INDUSTRIAL_QSS)
        self._sync_title_toolbar_widths()

        # The legacy .ui palette is black.  Using CSS ``transparent`` makes
        # Fusion composite that palette into a black tile on some backends,
        # so explicitly remove the toolbar controls' background painting.
        tool_button_style = (
            'QPushButton { background: none; border: none; } '
            'QPushButton:hover { background: #e3e8eb; border-radius: 5px; } '
            'QPushButton:pressed { background: #d4dce1; border-radius: 5px; } '
            'QPushButton:checked { background: #f7f9fa; '
            'border: 1px solid #a9b5bd; border-radius: 5px; }')
        for button in compact_buttons:
            button.setStyleSheet(tool_button_style)
            button.setAttribute(Qt.WA_StyledBackground, False)
        checkbox_style = (
            'QCheckBox { background: none; border: none; color: #31414b; } '
            'QCheckBox:hover { color: #172832; }')
        for checkbox in checkbox_widths:
            checkbox.setStyleSheet(checkbox_style)
            checkbox.setAttribute(Qt.WA_StyledBackground, False)

        # The Designer file gives these surfaces an opaque black palette.
        # They sit on panels which already paint the aligned window backdrop,
        # so keep the child widgets genuinely transparent on every Qt backend.
        for surface in (
                self.ui.temp, self.label, self.current_label_name_show):
            surface.setAutoFillBackground(False)
            surface.setAttribute(Qt.WA_StyledBackground, False)
            surface.setAttribute(Qt.WA_TranslucentBackground, True)
            palette = surface.palette()
            palette.setColor(
                QtGui.QPalette.Window, QtGui.QColor(0, 0, 0, 0))
            surface.setPalette(palette)
        self.ui.temp.setStyleSheet(
            'QGroupBox#temp { background: none; border: 0; }')
        self.label.setStyleSheet(
            'QLabel#label { background: none; '
            'border: 1px solid rgba(112, 125, 137, 180); '
            'border-radius: 5px; color: #82909b; }')
        self.current_label_name_show.setStyleSheet(
            'QLabel#character_label { background: none; border: 0; '
            'color: #53616c; padding: 0 12px; '
            'font-family: Consolas; font-size: 10px; }')
        for surface in (
                self.ui.temp, self.label, self.current_label_name_show):
            surface.setAttribute(Qt.WA_StyledBackground, False)
            palette = surface.palette()
            palette.setColor(
                QtGui.QPalette.Window, QtGui.QColor(0, 0, 0, 0))
            surface.setPalette(palette)
        inspector_style = (
            'QListWidget { color: #293840; background: transparent; '
            'border: 0; outline: 0; padding: 7px 6px; } '
            'QListWidget::item { color: #263942; '
            'background: qlineargradient(x1:0, y1:0, x2:1, y2:0, '
            'stop:0 rgba(250, 252, 253, 176), stop:1 rgba(231, 239, 243, 112)); '
            'border: 1px solid rgba(119, 143, 154, 58); '
            'border-radius: 6px; margin: 2px 0; padding: 4px 9px; } '
            'QListWidget::item:hover { color: #172b35; '
            'background: qlineargradient(x1:0, y1:0, x2:1, y2:0, '
            'stop:0 rgba(226, 240, 247, 225), stop:1 rgba(199, 226, 237, 174)); '
            'border: 1px solid rgba(59, 145, 178, 125); } '
            'QListWidget::item:selected { color: #14313e; font-weight: 600; '
            'background: qlineargradient(x1:0, y1:0, x2:1, y2:0, '
            'stop:0 rgba(157, 216, 237, 232), stop:1 rgba(205, 234, 244, 198)); '
            'border: 1px solid rgba(27, 139, 180, 185); '
            'border-left: 3px solid #168db8; }')
        for list_widget in (self.ui.labelShow, self.ui.clsShow):
            list_widget.setStyleSheet(inspector_style)
            list_widget.viewport().setStyleSheet(
                'background: transparent; border: 0;')
            list_widget.viewport().setAutoFillBackground(False)
            list_widget.viewport().setAttribute(
                Qt.WA_TranslucentBackground, True)
        self.statusBar().setSizeGripEnabled(False)
        self.statusBar().showMessage('SYSTEM READY  |  Z / X 切换图片  |  C 执行检测  |  Ctrl 临时平移')

    def show_background_menu(self):
        position = self.background_button.mapToGlobal(
            self.background_button.rect().bottomLeft())
        position.setY(position.y() + 5)
        self.background_menu.popup(position)

    @staticmethod
    def _toolbar_control_width(text_width, minimum_width, padding=24):
        """Keep title-bar text intact across fonts and display scaling."""
        return max(int(minimum_width), int(text_width) + int(padding))

    def _sync_title_toolbar_widths(self, button=None):
        buttons = ((button,) if button is not None
                   else tuple(self._toolbar_min_widths))
        for control in buttons:
            text_width = control.fontMetrics().horizontalAdvance(
                control.text())
            control.setFixedWidth(self._toolbar_control_width(
                text_width, self._toolbar_min_widths.get(control, 0)))

    def show_task_menu(self):
        position = self.task_button.mapToGlobal(
            self.task_button.rect().bottomLeft())
        position.setY(position.y() + 5)
        self.task_menu.popup(position)

    def set_annotation_task(self, task, persist=True, reload_image=True):
        labels = {
            'detect': '检测', 'segment': '分割',
            'obb': 'OBB', 'pose': '关键点',
        }
        if task not in labels:
            return False
        current_image = (self.img if self.img_is_load
                         and self.img is not None else None)
        previous_task = self.annotation_task
        if (reload_image and current_image is not None
                and current_image.label_save and task != self.annotation_task):
            self.task_actions[self.annotation_task].setChecked(True)
            self.statusBar().showMessage(
                'TASK SWITCH BLOCKED  |  当前图片已有标注；'
                '请先切换空白图片或清空当前标注', 6000)
            return False

        previous_image = (current_image.img_path
                          if current_image is not None else None)
        previous_label = (current_image.label_path
                          if current_image is not None else None)
        self.annotation_task = task
        self.task_button.setText(f'任务：{labels[task]}  ▾')
        self._sync_title_toolbar_widths(self.task_button)
        self.task_actions[task].setChecked(True)
        self._reset_task_interaction()
        if reload_image and previous_image is not None:
            if not self.init_image(previous_image, previous_label):
                self.annotation_task = previous_task
                self.img = current_image
                self.img_is_load = current_image is not None
                self.task_button.setText(
                    f'任务：{labels[previous_task]}  ▾')
                self._sync_title_toolbar_widths(self.task_button)
                self.task_actions[previous_task].setChecked(True)
                if current_image is not None:
                    current_image.show(
                        *current_image.center, scale=current_image.wheel_scale)
                    current_image.label_show()
                self.statusBar().showMessage(
                    'TASK SWITCH FAILED  |  已恢复原任务和当前图像', 7000)
                return False
            self.boxShowWidget.set_rect_box()
        if persist:
            self._save_background_config(
                annotation_task=task, kpt_shape=list(self.kpt_shape))
        hints = {
            'detect': '拖动绘制检测框；拖动框内部可整体移动',
            'segment': ('逐点单击绘制，单击起点、双击或 Enter 闭合；'
                        '右键取消，Ctrl+单击边线插入顶点'),
            'obb': '拖动绘制旋转框；边中点调单边，上方圆点或滚轮旋转',
            'pose': f'先拖动目标框，再依次标记 {self.kpt_shape[0]} 个关键点；右键记为缺失',
        }
        self.statusBar().showMessage(
            f'TASK {labels[task].upper()}  |  {hints[task]}'
            '  |  双击已有标注切换类别')
        return True

    def _reset_task_interaction(self):
        if hasattr(self, '_obb_save_timer'):
            self._obb_save_timer.stop()
        if hasattr(self, '_interaction_redraw_timer'):
            self._interaction_redraw_timer.stop()
        self._pending_interaction_redraw = None
        self.task_draft_points = []
        self.task_pose_bbox = None
        self.task_pose_points = []
        self.task_drag = None
        self.task_edit = None
        self.detect_drag_original = None
        self.detect_drag_start_org = None
        self.is_add_box = False
        self.is_update_label = False
        self.is_choose_rect = False
        self.is_choose_rect_index = None
        self.is_hover_move_allow = False
        self.mouse_left_press = False
        self.rect_save = None
        self.rect_save_current = None
        self.cross = False
        self.hover = False
        if self.img is not None:
            self.img.only_index = False

    def configure_keypoints(self):
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        dialog.setWindowTitle('关键点配置')
        dialog.setMinimumWidth(520)
        dialog.setStyleSheet(INDUSTRIAL_QSS)
        outer_layout = QVBoxLayout(dialog)
        outer_layout.setContentsMargins(1, 1, 1, 1)
        outer_layout.setSpacing(0)
        title_bar = TitleBar(dialog)
        title_bar.title_label.setText('关键点配置')
        title_bar.minimize_button.hide()
        title_bar.maximize_button.hide()
        outer_layout.addWidget(title_bar)
        content = QWidget(dialog)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(9)
        outer_layout.addWidget(content)

        shape_row = QWidget(dialog)
        shape_layout = QHBoxLayout(shape_row)
        shape_layout.setContentsMargins(0, 0, 0, 0)
        count_spin = QSpinBox(shape_row)
        count_spin.setRange(1, 100)
        count_spin.setValue(self.kpt_shape[0])
        dimensions_combo = QComboBox(shape_row)
        dimensions_combo.addItem('x, y', 2)
        dimensions_combo.addItem('x, y, 可见性', 3)
        dimensions_combo.setCurrentIndex(
            dimensions_combo.findData(self.kpt_shape[1]))
        shape_layout.addWidget(QLabel('关键点数量', shape_row))
        shape_layout.addWidget(count_spin)
        shape_layout.addSpacing(18)
        shape_layout.addWidget(QLabel('每点维度', shape_row))
        shape_layout.addWidget(dimensions_combo, 1)
        layout.addWidget(shape_row)

        layout.addWidget(QLabel('关键点名称（使用逗号分隔）', dialog))
        names_edit = QLineEdit(', '.join(self.keypoint_names), dialog)
        layout.addWidget(names_edit)
        layout.addWidget(QLabel('骨架连接（例如 0-1, 1-2）', dialog))
        skeleton_edit = QLineEdit(
            ', '.join(f'{start}-{end}' for start, end in self.kpt_skeleton),
            dialog)
        layout.addWidget(skeleton_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Cancel | QDialogButtonBox.Ok, parent=dialog)
        buttons.button(QDialogButtonBox.Ok).setText('确认')
        buttons.button(QDialogButtonBox.Cancel).setText('取消')
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec_() != QDialog.Accepted:
            return

        count = count_spin.value()
        dimensions = int(dimensions_combo.currentData())
        if (self.annotation_task == 'pose' and self.img_is_load
                and self.img.label_save
                and (count, dimensions) != self.kpt_shape):
            self.statusBar().showMessage(
                'POSE CONFIG BLOCKED  |  当前图片已有关键点标注；'
                '请在空白图片中修改关键点结构', 7000)
            return
        names = [name.strip() for name in names_edit.text().split(',')
                 if name.strip()]
        names = (names + [f'点 {index + 1}' for index in range(len(names), count)])[:count]
        skeleton = []
        for item in skeleton_edit.text().split(','):
            item = item.strip()
            if not item:
                continue
            try:
                start, end = (int(value.strip()) for value in item.split('-', 1))
            except (ValueError, TypeError):
                continue
            if 0 <= start < count and 0 <= end < count and start != end:
                skeleton.append((start, end))
        self.kpt_shape = (count, dimensions)
        self.keypoint_names = names
        self.kpt_skeleton = skeleton
        self._save_background_config(
            kpt_shape=list(self.kpt_shape),
            keypoint_names=list(self.keypoint_names),
            kpt_skeleton=[list(edge) for edge in self.kpt_skeleton])
        if self.annotation_task == 'pose' and self.img_is_load:
            self.init_image(self.img.img_path, self.img.label_path)
        self.statusBar().showMessage(
            f'POSE CONFIG  |  {count} KEYPOINTS × {dimensions} DIMENSIONS')

    def _pose_point_name(self, index):
        if 0 <= index < len(self.keypoint_names):
            return self.keypoint_names[index]
        return f'点 {index + 1}'

    def show_model_menu(self):
        position = self.load_model.mapToGlobal(
            self.load_model.rect().bottomLeft())
        position.setY(position.y() + 5)
        self.model_menu.popup(position)

    def choose_background_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, '选择工作台背景', '', '图片文件 (*.png *.jpg *.jpeg *.bmp *.webp)')
        if not file_path:
            return
        if not self.window_shell.set_background_image(file_path):
            QMessageBox.warning(self, '背景导入失败', '无法读取所选图片。')
            return
        self._save_background_config(background_image=file_path)
        self.statusBar().showMessage(f'BACKGROUND UPDATED  |  {Path(file_path).name}')

    def clear_background_image(self, _position=None):
        self.window_shell.set_background_image()
        self._save_background_config(background_image='')
        self.statusBar().showMessage('BACKGROUND CLEARED  |  已恢复默认中性底色')

    def restore_default_window(self):
        """Restore visual window defaults without touching annotation data."""
        self.window_shell.set_background_image()
        self.background_opacity.setValue(65)
        self.update_background_opacity(65)
        self.thumbnail_size_slider.setValue(80)
        self.update_thumbnail_size(80)
        if self.isMaximized() or self.isFullScreen():
            self.showNormal()

        screen = QApplication.screenAt(self.frameGeometry().center())
        if screen is None:
            screen = QApplication.primaryScreen()
        available = screen.availableGeometry()
        width = min(1400, max(1100, available.width() - 40))
        height = min(860, max(720, available.height() - 40))
        self.resize(width, height)
        target = available.center() - self.rect().center()
        self.move(target)
        self.right_splitter.setSizes([1, 1])
        self.workspace_splitter.setSizes([236, max(1, width - 250)])

        self._save_background_config(
            background_image='', background_opacity=65, thumbnail_size=80)
        self.statusBar().showMessage(
            'WINDOW RESET  |  背景、尺寸、位置及面板比例已恢复默认')

    def restore_default_background(self):
        """Compatibility alias for older callers."""
        self.restore_default_window()

    def update_background_opacity(self, value):
        self.window_shell.set_background_opacity(value / 100)

    def save_background_opacity(self):
        value = self.background_opacity.value()
        self._save_background_config(background_opacity=value)
        self.statusBar().showMessage(f'BACKGROUND OPACITY  |  {value}%')

    def update_thumbnail_size(self, value):
        self.thumbnail_preview_size = max(56, min(int(value), 128))
        if self.thumbnail_widget is not None:
            self.thumbnail_widget.set_thumbnail_size(
                self.thumbnail_preview_size)

    def save_thumbnail_size(self):
        value = self.thumbnail_size_slider.value()
        self._save_background_config(thumbnail_size=value)
        self.statusBar().showMessage(f'THUMBNAIL SIZE  |  {value} px')

    def update_confidence(self, value):
        self.conf = value / 100

    def save_model_confidence(self):
        value = self.confidence_control.value()
        self._save_background_config(detection_confidence=value)
        self.statusBar().showMessage(
            f'DETECTION CONFIDENCE  |  {value / 100:.2f}')

    @staticmethod
    def _save_background_config(**updates):
        config_path = root / 'Detection.yaml'
        with open(config_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file) or {}
        data.update(updates)
        with open(config_path, 'w', encoding='utf-8') as file:
            yaml.safe_dump(data, file, allow_unicode=True, sort_keys=False)

    def _create_shortcuts(self):
        callbacks = {
            'previous_image': self.handleShortcut1_,
            'next_image': self.handleShortcut2_,
            'detect': self.detect_,
            'delete_box': self.deleteBox_,
            'zoom_in': self.imgUp_,
            'zoom_out': self.imgDown_,
            'reset_view': self.resetShowImg_,
            'save_labels': self.save_,
        }
        for key, sequence in self.shortcut_bindings.items():
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.setContext(Qt.WindowShortcut)
            shortcut.activated.connect(callbacks[key])
            self.shortcuts[key] = shortcut

    def _build_shortcut_menu(self):
        self.shortcut_menu = QMenu(self)
        self.shortcut_menu.setObjectName('shortcutMenu')
        self.shortcut_actions = {}
        for key, (label, _default) in DEFAULT_SHORTCUTS.items():
            action = self.shortcut_menu.addAction(label)
            action.triggered.connect(
                lambda _checked=False, shortcut_key=key:
                self._edit_shortcut(shortcut_key))
            self.shortcut_actions[key] = action

        self.shortcut_menu.addSeparator()
        self.wheel_pan_action = self.shortcut_menu.addAction(
            '允许滚轮上下平移画布')
        self.wheel_pan_action.setCheckable(True)
        self.wheel_pan_action.setChecked(self.wheel_pan_enabled)
        self.wheel_zoom_action = self.shortcut_menu.addAction(
            '允许滚轮缩放图片')
        self.wheel_zoom_action.setCheckable(True)
        self.wheel_zoom_action.setChecked(self.wheel_zoom_enabled)
        self.wheel_pan_action.toggled.connect(self._wheel_options_changed)
        self.wheel_zoom_action.toggled.connect(self._wheel_options_changed)

        self.shortcut_menu.addSeparator()
        reset_action = self.shortcut_menu.addAction(
            toolbar_icon('reset'), '恢复默认快捷键')
        reset_action.triggered.connect(self.reset_shortcuts)
        self._refresh_shortcut_menu()

    def show_shortcut_menu(self):
        position = self.ui.save_5.mapToGlobal(
            self.ui.save_5.rect().bottomLeft())
        position.setY(position.y() + 5)
        self.shortcut_menu.popup(position)

    def _refresh_shortcut_menu(self):
        if not hasattr(self, 'shortcut_actions'):
            return
        for key, action in self.shortcut_actions.items():
            label = DEFAULT_SHORTCUTS[key][0]
            sequence = self.shortcut_bindings.get(key, '')
            action.setText(f'{label}\t{sequence or "已禁用"}')
        for action, checked in (
                (self.wheel_pan_action, self.wheel_pan_enabled),
                (self.wheel_zoom_action, self.wheel_zoom_enabled)):
            action.blockSignals(True)
            action.setChecked(checked)
            action.blockSignals(False)

    def _edit_shortcut(self, key):
        label = DEFAULT_SHORTCUTS[key][0]
        dialog = QDialog(self)
        dialog.setWindowTitle(f'设置快捷键 · {label}')
        dialog.setFixedWidth(360)
        dialog.setStyleSheet(INDUSTRIAL_QSS)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        prompt = QLabel(f'{label}：', dialog)
        editor = QKeySequenceEdit(
            QKeySequence(self.shortcut_bindings.get(key, '')), dialog)
        editor_row = QHBoxLayout()
        editor_row.setContentsMargins(0, 0, 0, 0)
        editor_row.setSpacing(8)
        disable_button = QPushButton('禁用此快捷键', dialog)
        disable_button.setFixedWidth(110)
        disable_button.clicked.connect(editor.clear)
        editor_row.addWidget(editor, 1)
        editor_row.addWidget(disable_button)
        hint = QLabel('清空按键可禁用此项；同一按键不能重复使用。', dialog)
        hint.setStyleSheet('color: #667780;')
        buttons = QDialogButtonBox(
            QDialogButtonBox.Cancel | QDialogButtonBox.Ok, parent=dialog)
        buttons.button(QDialogButtonBox.Cancel).setText('取消')
        buttons.button(QDialogButtonBox.Ok).setText('确认')
        buttons.button(QDialogButtonBox.Ok).setProperty('role', 'primary')
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(prompt)
        layout.addLayout(editor_row)
        layout.addWidget(hint)
        layout.addWidget(buttons)
        if dialog.exec_() != QDialog.Accepted:
            return

        sequence = editor.keySequence().toString(QKeySequence.PortableText)
        duplicate = next((
            other_key for other_key, other_sequence
            in self.shortcut_bindings.items()
            if other_key != key and sequence
            and other_sequence.casefold() == sequence.casefold()
        ), None)
        if duplicate is not None:
            QMessageBox.warning(
                self, '快捷键冲突',
                f'“{sequence}”已用于“{DEFAULT_SHORTCUTS[duplicate][0]}”。')
            return
        self.shortcut_bindings[key] = sequence
        self.shortcuts[key].setKey(QKeySequence(sequence))
        self.shortcuts[key].setEnabled(bool(sequence))
        self._refresh_shortcut_menu()
        self._save_shortcut_configuration()

    def _apply_shortcut_configuration(self, data):
        raw_bindings = data.get('shortcuts') or {}
        for key, (_label, default) in DEFAULT_SHORTCUTS.items():
            sequence = raw_bindings.get(key, default)
            if not isinstance(sequence, str):
                sequence = default
            self.shortcut_bindings[key] = sequence
            self.shortcuts[key].setKey(QKeySequence(sequence))
            self.shortcuts[key].setEnabled(bool(sequence))
        self.wheel_pan_enabled = bool(data.get('wheel_pan_enabled', True))
        self.wheel_zoom_enabled = bool(data.get('wheel_zoom_enabled', True))
        self._refresh_shortcut_menu()

    def _wheel_options_changed(self, _checked=False):
        self.wheel_pan_enabled = self.wheel_pan_action.isChecked()
        self.wheel_zoom_enabled = self.wheel_zoom_action.isChecked()
        self._save_shortcut_configuration()
        self.statusBar().showMessage(
            'MOUSE WHEEL  |  平移{}  ·  缩放{}'.format(
                '开启' if self.wheel_pan_enabled else '关闭',
                '开启' if self.wheel_zoom_enabled else '关闭'))

    def _save_shortcut_configuration(self):
        self._save_background_config(
            shortcuts=dict(self.shortcut_bindings),
            wheel_pan_enabled=self.wheel_pan_enabled,
            wheel_zoom_enabled=self.wheel_zoom_enabled)

    def reset_shortcuts(self):
        self.shortcut_bindings = {
            key: default for key, (_label, default) in DEFAULT_SHORTCUTS.items()
        }
        for key, sequence in self.shortcut_bindings.items():
            self.shortcuts[key].setKey(QKeySequence(sequence))
            self.shortcuts[key].setEnabled(True)
        self.wheel_pan_enabled = True
        self.wheel_zoom_enabled = True
        self._refresh_shortcut_menu()
        self._save_shortcut_configuration()
        self.statusBar().showMessage('SHORTCUTS RESET  |  已恢复默认按键与滚轮操作')

    def init(self, img_path=None):
        # 先加载本地的配置文件
        # names : 类别名字 list, colors : 类别颜色 list, cls : 默认类别 int, save_path : 默认保存路径 str
        with open(root / 'Detection.yaml', 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)

        if not self._background_initialized:
            self._background_initialized = True
            background_path = data.get('background_image')
            try:
                opacity = max(0, min(int(data.get('background_opacity', 65)), 100))
            except (TypeError, ValueError):
                opacity = 65
            self.background_opacity.setValue(opacity)
            self.update_background_opacity(opacity)
            try:
                confidence = max(
                    0, min(int(data.get('detection_confidence', 50)), 100))
            except (TypeError, ValueError):
                confidence = 50
            self.confidence_control.setValue(confidence)
            self.update_confidence(confidence)
            try:
                thumbnail_size = max(
                    56, min(int(data.get('thumbnail_size', 80)), 128))
            except (TypeError, ValueError):
                thumbnail_size = 80
            self.thumbnail_size_slider.setValue(thumbnail_size)
            self.update_thumbnail_size(thumbnail_size)
            self._apply_shortcut_configuration(data)
            raw_shape = data.get('kpt_shape', [17, 3])
            try:
                count, dimensions = int(raw_shape[0]), int(raw_shape[1])
                if count < 1 or dimensions not in (2, 3):
                    raise ValueError
                self.kpt_shape = (count, dimensions)
            except (TypeError, ValueError, IndexError):
                self.kpt_shape = (17, 3)
            configured_names = data.get('keypoint_names')
            if isinstance(configured_names, list):
                self.keypoint_names = [str(name) for name in configured_names]
            else:
                self.keypoint_names = list(COCO_KEYPOINT_NAMES)
            count = self.kpt_shape[0]
            self.keypoint_names = (
                self.keypoint_names
                + [f'点 {index + 1}' for index in range(
                    len(self.keypoint_names), count)])[:count]
            configured_skeleton = data.get('kpt_skeleton')
            if isinstance(configured_skeleton, list):
                self.kpt_skeleton = []
                for edge in configured_skeleton:
                    try:
                        start, end = int(edge[0]), int(edge[1])
                    except (TypeError, ValueError, IndexError):
                        continue
                    if 0 <= start < count and 0 <= end < count and start != end:
                        self.kpt_skeleton.append((start, end))
            else:
                self.kpt_skeleton = [
                    edge for edge in COCO_KEYPOINT_SKELETON
                    if edge[0] < count and edge[1] < count]
            self.set_annotation_task(
                data.get('annotation_task', 'detect'),
                persist=False, reload_image=False)
            if background_path and Path(background_path).is_file():
                self.window_shell.set_background_image(background_path)

        self.names = {
            int(key): str(value)
            for key, value in (data.get('names') or {}).items()
        }
        legacy_colors = data.get('colors') or {}
        self.class_styles = build_class_styles(
            self.names, data.get('class_styles'), legacy_colors)
        self.colors = {
            class_id: list(style['fill'])
            for class_id, style in self.class_styles.items()
        }
        self.cls = int(data['default_cls'])
        configured_save_path = data.get('save_path', 'temp_folder')
        if configured_save_path != 'temp_folder':
            configured_save_path = Path(configured_save_path).expanduser()
            self.default_save_path = configured_save_path if configured_save_path.is_absolute() else root / configured_save_path
        else:
            self.default_save_path = root / 'utils/temp_folder'
        self.default_save_path.mkdir(parents=True, exist_ok=True)

        self.wheel_scale = 1  # 滚轮放大的倍数, 当前图片相对于label尺寸的缩放倍数
        self.img_is_load = False  # 图片是否加载
        self.mouse_pos = [0, 0]  # 鼠标在label中的坐标
        self.mouse_save_temp = [0, 0]  # 鼠标在label中的坐标

        self.is_add_box, self.is_update_label, self.len_rect, self.is_choose_rect, self.rect_save, self.rect_save_current = False, False, 0, False, None, None
        self.mouse_press_pos, self.is_first_add_box = None, True
        self.is_choose_rect_index, self.is_choose_rect_over_striking = None, False
        self.cross, self.hover, self.hand, self.arrows, self.hand_flag, self.temp_hand = False, False, False, True, False, False
        if hasattr(self, 'tool_mode_group'):
            self._sync_tool_mode_buttons()
        self.mouse_press_pos, self.mouse_left_press, self.mouse_right_press = None, False, False
        self.detect_drag_original = None
        self.detect_drag_start_org = None

        self.label_list.clear()
        self.label_list_only_name.clear()
        for label_path in self.default_save_path.glob('*.txt'):
            self.label_list.add(str(label_path))
            self.label_list_only_name.add(label_path.stem)

        # 初始化图片, 如果有图片路径, 就加载图片
        if img_path is not None:
            img_name = Path(img_path).stem
            candidate = self.default_save_path / f'{img_name}.txt'
            p = candidate if candidate.exists() else None
            if self.init_image(img_path, p):
                self.categoryShowWidget.init()

    # 从本地加载图片，有标签就添加标签
    def init_image(self, img_path, label_path):
        try:
            image = Image(
                self.label, img_path, label_path, parent=self,
                task=self.annotation_task, kpt_shape=self.kpt_shape)
        except (OSError, ValueError) as exc:
            self.img_is_load = False
            self.img = None
            self.label.clear()
            self.label.setText(
                'LABEL FORMAT DOES NOT MATCH CURRENT TASK\n\n'
                'SWITCH TASK MODE OR USE A COMPATIBLE LABEL FILE')
            self.statusBar().showMessage(
                f'LABEL FORMAT ERROR  |  {exc}', 9000)
            return False
        self.img = image

        self.img.show_box_circle = self.show_box_circle.isChecked()
        self.img.show_other = self.show_other.isChecked()
        self.img.show_box_fill = self.show_box_fill.isChecked()
        self.img.show_box_text = self.show_box_text.isChecked()

        self.img_is_load = True
        self.statusBar().showMessage(
            f'IMAGE READY  |  {Path(img_path).name}  |  {len(self.img.label_save)} OBJECTS')
        return True

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.img_is_load and hasattr(self, '_resize_timer'):
            self._resize_timer.start(100)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.WindowStateChange and hasattr(self, 'title_bar'):
            maximized = self.isMaximized()
            self.shell_layout.setContentsMargins(0 if maximized else 1,
                                                 0 if maximized else 1,
                                                 0 if maximized else 1, 0)
            self.title_bar.maximize_button.update()

    def nativeEvent(self, event_type, message):
        """Restore native edge and corner resizing for the main window."""
        if sys.platform.startswith('win') and not self.isMaximized():
            from ctypes import wintypes

            native_message = wintypes.MSG.from_address(int(message))
            if native_message.message == 0x0084:  # WM_NCHITTEST
                hit = self._window_resize_hit_test(QtGui.QCursor.pos())
                if hit is not None:
                    return True, hit
        return super().nativeEvent(event_type, message)

    def _window_resize_hit_test(self, cursor, margin=7):
        """Return the Windows non-client hit code for a global cursor point."""
        frame = self.frameGeometry()
        on_left = frame.left() <= cursor.x() <= frame.left() + margin
        on_right = frame.right() - margin <= cursor.x() <= frame.right()
        on_top = frame.top() <= cursor.y() <= frame.top() + margin
        on_bottom = frame.bottom() - margin <= cursor.y() <= frame.bottom()

        if on_top and on_left:
            return 13  # HTTOPLEFT
        if on_top and on_right:
            return 14  # HTTOPRIGHT
        if on_bottom and on_left:
            return 16  # HTBOTTOMLEFT
        if on_bottom and on_right:
            return 17  # HTBOTTOMRIGHT
        if on_left:
            return 10  # HTLEFT
        if on_right:
            return 11  # HTRIGHT
        if on_top:
            return 12  # HTTOP
        if on_bottom:
            return 15  # HTBOTTOM
        return None

    def _refresh_after_resize(self):
        if not self.img_is_load:
            return
        self.label_height = self.label.size().height()
        self.label_width = self.label.size().width()
        self.img.label_height = self.label_height
        self.img.label_width = self.label_width
        self.img.center = (self.label_width // 2, self.label_height // 2)
        self.img.is_trans = True
        self.move_xy(index=self.is_choose_rect_index)

    # 事件过滤器, 用来处理鼠标事件
    def eventFilter(self, source, event):
        if self.change_label_name:
            return True
        task_mouse_events = (
            QEvent.MouseMove, QEvent.MouseButtonPress,
            QEvent.MouseButtonRelease, QEvent.MouseButtonDblClick,
        )
        if (self.img_is_load and self.annotation_task != 'detect'
                and source is self.label
                and event.type() in task_mouse_events):
            if (event.type() == QEvent.MouseButtonPress
                    and event.button() == Qt.MiddleButton):
                if self.arrows:
                    self.hand_button_()
                else:
                    self.arrows_button_()
                return True
            if (event.type() == QEvent.MouseButtonDblClick
                    and event.button() == Qt.LeftButton):
                return self._task_event_filter(event)
            if self.hand:
                return self._task_hand_event_filter(event)
            if self.arrows:
                return self._task_event_filter(event)
        if (self.img_is_load and self.annotation_task == 'detect'
                and source is self.label
                and event.type() == QEvent.MouseButtonDblClick
                and event.button() == Qt.LeftButton):
            position = self._event_canvas_pos(source, event)
            hit_type, index, _control = self.img.hit_test(*position)
            if hit_type is not None:
                self._show_annotation_category_picker(
                    index, source.mapToGlobal(event.pos()))
            return True
        # 鼠标移动事件
        if event.type() == QEvent.MouseMove:
            # Mouse events are local to their source widget.  Convert them to
            # label coordinates instead of applying the former hard-coded
            # 12 px Designer padding compensation.
            self.mouse_pos = list(self._event_canvas_pos(source, event))

            # 拉新框或调整旧框时，命中目标必须锁定为按下时的对象。
            # 否则重叠框会在 MouseMove 中不断抢占 rect_save_current，
            # 同时触发整层重绘，表现为抖动甚至界面假死。
            if not self.is_add_box and not self.is_update_label:
                self.get_cross_or_hover()
                self.mouse_hover_display()

            self.mouse_state()

            # 移动图像
            if self.hand and self.mouse_left_press:
                self.moveImage()

            # 更新label
            if self.is_update_label:
                self._queue_interaction_redraw('detect_update')

            # 添加框
            elif self.is_add_box:
                self._queue_interaction_redraw('detect_add')

        # ———————————————————————————————— 鼠标事件 ————————————————————————————————#

        # 点击左键
        if event.type() == QEvent.MouseButtonPress and event.type() != QEvent.MouseButtonDblClick:
            if event.button() == Qt.LeftButton:  # 鼠标左键按下, 双击也会触发
                if self.temp_widget is not None:
                    self.temp_widget.close()
                self.temp_widget = None

                if self.mouse_left_press is False and self.img_is_load:

                    self.mouse_left_press = True
                    self.mouse_press_pos = self._event_canvas_pos(
                        source, event, clamp=True)
                    self.mouse_pos = list(self.mouse_press_pos)
                    self._update_pointer_target(self.mouse_press_pos)
                    if (self.cross or self.hover) and self.rect_save_current:
                        self.cls = int(self.rect_save_current[2][0])
                    self.mouse_save_temp = self.mouse_press_pos

                    if self.arrows and self.cross and not self.is_add_box:
                        self.img.only_index = True
                        # 按下鼠标左键时，更新label
                        self.is_add_box = False
                        self.is_update_label = True
                        self.detect_drag_original = None
                        self.detect_drag_start_org = None

                    elif self.arrows and self.hover:
                        # 框内部既负责选中，也直接用于整体拖动；不再依赖中心锚点。
                        self.img.only_index = True
                        self.is_add_box = False
                        self.is_update_label = True
                        index = self.rect_save_current[0]
                        self.detect_drag_original = list(
                            self.img.label_save[index])
                        self.detect_drag_start_org = (
                            self.img.new_xy_to_org_xy(self.mouse_press_pos))
                        self.rect_save_current = [
                            index, -1, list(self.detect_drag_original)]
                        self.is_choose_rect_index = index
                        self.is_choose_rect = True
                        self.move_xy(index=self.is_choose_rect_index)

                    elif self.arrows and not self.is_update_label and self.pos_in_org(
                            self.mouse_press_pos):

                        self.img.only_index = True
                        # 按下鼠标左键时，添加框
                        # 清理上一个框的选择/悬停状态，确保松开时不会把旧框
                        # 当成刚创建的框处理。
                        self.is_choose_rect = False
                        self.is_choose_rect_index = None
                        self.is_choose_rect_over_striking = False
                        self.is_hover_move_allow = False
                        self.rect_save = None
                        self.rect_save_current = None
                        self.cross = False
                        self.hover = False
                        self.is_update_label = False
                        self.is_add_box = True

            if event.button() == Qt.RightButton:
                self.deleteBox_()

        # 释放
        if event.type() == QEvent.MouseButtonRelease:
            # 鼠标左键释放
            if event.button() == Qt.LeftButton:
                if not self.img_is_load:
                    return False

                if self.img_is_load:
                    self._interaction_redraw_timer.stop()
                    self._flush_interaction_redraw()
                    self.img.save()

                # is_first_add_box 为 False 才表示本次拖动真的创建了新框。
                # 仅按下/松开时不能检查、更不能删除最后一个旧框。
                if (self.is_add_box and not self.is_first_add_box
                        and self.is_choose_rect
                        and self.is_choose_rect_index is not None
                        and self.img.label_save):
                    x1y1 = self.img.org_xy_to_new_xy(self.img.label_save[-1][1:3])
                    x2y2 = self.img.org_xy_to_new_xy(self.img.label_save[-1][3:])
                    if distance(x1y1, x2y2) < 25:
                        self.deleteBox_(-1)
                        self.is_add_box = False

                release_pos = self._event_canvas_pos(source, event)
                if self.img_is_load and distance(
                        self.mouse_press_pos, release_pos) < 10:
                    self.mouse_pos = list(release_pos)
                    self._update_pointer_target(release_pos)
                    if not self.cross and not self.hover:
                        # 没有悬停在框上, 没有悬停在点上, 就取消选中框
                        self.is_choose_rect_index = None
                        self.is_choose_rect = False
                        self.is_hover_move_allow = False
                        self.rect_save_current = None
                        self.move_xy()
                        self.is_add_box = False

                    else:
                        self.is_choose_rect_index = self.rect_save_current[0]
                        self.is_choose_rect = True
                        self.move_xy(index=self.is_choose_rect_index)

                self.categoryShowWidget.clear()
                if self.is_choose_rect:
                    self.categoryShowWidget.set_rect_cls(self.cls)

                self.img.only_index = False
                self.is_update_label = False
                self.is_add_box = False
                self.mouse_left_press = False
                self.mouse_save_temp = None
                self.hand_flag = False
                self.detect_drag_original = None
                self.detect_drag_start_org = None

                self.rect_save = None
                self.is_first_add_box = True
                self.is_first_update_label = True

                if self.rect_save_current and not self.is_hover_move_allow:
                    index_ = self.rect_save_current[0] if self.rect_save_current else None

                    self.move_xy(index=index_)
                    self.categoryShowWidget.set_rect_cls(self.rect_save_current[2][0], 1)
                    self.boxShowWidget.set_rect_box(self.rect_save_current[0])
            else:
                return False

        return super().eventFilter(source, event)

    def _task_hand_event_filter(self, event):
        position = self._event_canvas_pos(self.label, event)
        self.mouse_pos = list(position)
        if (event.type() == QEvent.MouseButtonPress
                and event.button() == Qt.LeftButton):
            self.mouse_left_press = True
            self.mouse_save_temp = list(position)
            self.hand_flag = True
            self.setCursor(Qt.ClosedHandCursor)
        elif event.type() == QEvent.MouseMove and self.mouse_left_press:
            self.moveImage()
        elif (event.type() == QEvent.MouseButtonRelease
              and event.button() == Qt.LeftButton):
            self.mouse_left_press = False
            self.hand_flag = False
            self.setCursor(Qt.OpenHandCursor)
        return True

    def _task_event_filter(self, event):
        """Mouse interaction for segment, OBB and pose annotations."""
        position = self._event_canvas_pos(self.label, event)
        self.mouse_pos = list(position)

        if event.type() == QEvent.MouseButtonDblClick:
            if event.button() == Qt.LeftButton:
                if self.annotation_task == 'segment' and self.task_draft_points:
                    self._finish_segment()
                    return True
                hit = self.img.task_hit_test(*position)
                if hit[0] is not None:
                    global_pos = self.label.mapToGlobal(event.pos())
                    self._show_annotation_category_picker(hit[1], global_pos)
                return True

        if event.type() == QEvent.MouseButtonPress:
            self._cancel_interaction_redraw()
            if event.button() == Qt.RightButton:
                if self.annotation_task == 'segment' and self.task_draft_points:
                    self._cancel_segment_draft()
                elif self.annotation_task == 'pose' and self.task_pose_bbox:
                    self._append_pose_point(None, visibility=0)
                elif self.is_choose_rect:
                    self.deleteBox_()
                return True
            if event.button() != Qt.LeftButton or not self.pos_in_org(position):
                return True

            if self.annotation_task == 'segment':
                if self.task_draft_points:
                    if self._segment_can_close(position):
                        self._finish_segment()
                        return True
                    self.task_draft_points.append(
                        self.img.new_xy_to_org_xy(position))
                    self._redraw_task_draft(cursor=position)
                    return True
                if event.modifiers() & Qt.ControlModifier:
                    selected = (self.is_choose_rect_index
                                if self.is_choose_rect else None)
                    edge_hit = self.img.segment_edge_hit_test(
                        *position, annotation_index=selected)
                    if edge_hit is None and selected is not None:
                        edge_hit = self.img.segment_edge_hit_test(*position)
                    if edge_hit is not None:
                        self._insert_segment_vertex(edge_hit)
                        return True
                hit = self.img.task_hit_test(*position)
                if hit[0] is None:
                    self._clear_task_selection()
                    self.task_draft_points = [
                        self.img.new_xy_to_org_xy(position)]
                    self._redraw_task_draft(cursor=position)
                else:
                    self._begin_task_edit(hit, position)
                return True

            if self.annotation_task == 'pose' and self.task_pose_bbox:
                visibility = 1 if event.modifiers() & Qt.ShiftModifier else 2
                self._append_pose_point(position, visibility)
                return True

            hit = self.img.task_hit_test(*position)
            if hit[0] is not None:
                self._begin_task_edit(hit, position)
            else:
                self._clear_task_selection()
                self.task_drag = {
                    'start': tuple(position), 'current': tuple(position),
                    'square': False}
                self.mouse_left_press = True
            return True

        if event.type() == QEvent.MouseMove:
            if self.annotation_task == 'segment' and self.task_draft_points:
                can_close = self._segment_can_close(position)
                self.setCursor(Qt.PointingHandCursor if can_close
                               else Qt.CrossCursor)
                self._queue_interaction_redraw(
                    'task_draft', cursor=position,
                    close_polygon=can_close)
                return True
            if self.task_edit is not None and self.mouse_left_press:
                self._queue_interaction_redraw(
                    'task_edit', index=self.task_edit['index'],
                    position=tuple(position), modifiers=event.modifiers())
                return True
            if self.task_drag is not None and self.mouse_left_press:
                end = tuple(self.limit_xy(*position))
                square = bool(
                    self.annotation_task == 'obb'
                    and event.modifiers() & Qt.ShiftModifier)
                if square:
                    end = self._square_drag_end(
                        self.task_drag['start'], end)
                self.task_drag['current'] = end
                self.task_drag['square'] = square
                self._queue_interaction_redraw('task_drag')
                return True
            hit = self.img.task_hit_test(*position)
            edge_hit = None
            if self.annotation_task == 'segment':
                selected = (self.is_choose_rect_index
                            if self.is_choose_rect else None)
                edge_hit = self.img.segment_edge_hit_test(
                    *position, annotation_index=selected)
                if edge_hit is None and selected is not None:
                    edge_hit = self.img.segment_edge_hit_test(*position)
            self.setCursor(
                Qt.PointingHandCursor if edge_hit is not None
                else Qt.SizeAllCursor if hit[0] == 'shape'
                else Qt.CrossCursor if hit[0] in (
                    'vertex', 'edge', 'bbox_vertex', 'keypoint', 'rotate')
                else Qt.ArrowCursor)
            return True

        if event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
            self._interaction_redraw_timer.stop()
            self._flush_interaction_redraw()
            if self.task_edit is not None:
                self.img.save()
                self.task_edit = None
                self.mouse_left_press = False
                return True
            if self.task_drag is not None:
                start = self.task_drag['start']
                end = tuple(self.limit_xy(*position))
                if (self.annotation_task == 'obb'
                        and event.modifiers() & Qt.ShiftModifier):
                    end = self._square_drag_end(start, end)
                self.task_drag = None
                self.mouse_left_press = False
                if distance(start, end) < 12:
                    self._redraw_task_draft()
                    return True
                self._finish_task_box_drag(start, end)
                return True
        return True

    def _clear_task_selection(self):
        if self.img_is_load:
            self.img.only_index = False
        self.is_choose_rect = False
        self.is_choose_rect_index = None
        self.is_hover_move_allow = False
        self.rect_save_current = None
        self.boxShowWidget.clear()
        self.categoryShowWidget.clear()

    def _select_task_annotation(self, index):
        self.is_choose_rect = True
        self.is_choose_rect_index = index
        self.rect_save_current = [index, -1, self.img.label_save[index]]
        self.boxShowWidget.set_rect_box(index)
        self.categoryShowWidget.set_rect_cls(
            self.img.label_save[index][0], index)
        self.move_xy(index=index)

    def _show_annotation_category_picker(self, index, global_position):
        """Select an annotation and show the shared class picker beside it."""
        if not (self.img_is_load and 0 <= index < len(self.img.label_save)):
            return False
        if self.annotation_task == 'detect':
            self.is_choose_rect = True
            self.is_choose_rect_index = index
            self.is_hover_move_allow = True
            self.rect_save_current = [index, -1, self.img.label_save[index]]
            self.cls = int(self.img.label_save[index][0])
            self.move_xy(index=index)
            self.boxShowWidget.set_rect_box(index)
            self.categoryShowWidget.set_rect_cls(self.cls, index)
        else:
            self._select_task_annotation(index)
            self.cls = int(self.img.label_save[index][0])
        if self.temp_widget is not None:
            self.temp_widget.close()
        self.temp_widget = tempWidget(self, QListWidget())
        self.temp_widget.set_rect_cls(self.cls, index)
        self.temp_widget.show()
        self.temp_widget.move(global_position.x() + 12,
                              global_position.y() + 12)
        return True

    def _begin_task_edit(self, hit, position):
        kind, index, control = hit
        self._select_task_annotation(index)
        original = list(self.img.label_save[index])
        if self.annotation_task == 'obb':
            original = self.img.canonicalize_obb_label(original)
        self.task_edit = {
            'kind': kind, 'index': index, 'control': control,
            'start_canvas': tuple(position),
            'start_org': self.img.new_xy_to_org_xy(position),
            'original': original,
        }
        self.mouse_left_press = True

    def _update_task_edit(self, position, modifiers=Qt.NoModifier,
                          redraw=True):
        edit = self.task_edit
        label = list(edit['original'])
        current_org = self.img.new_xy_to_org_xy(position)
        dx = current_org[0] - edit['start_org'][0]
        dy = current_org[1] - edit['start_org'][1]
        kind = edit['kind']
        if kind == 'shape':
            if self.annotation_task == 'pose':
                dimensions = self.kpt_shape[1]
                for offset in (1, 3):
                    label[offset] += dx
                    label[offset + 1] += dy
                for offset in range(5, len(label), dimensions):
                    if dimensions == 3 and int(label[offset + 2]) == 0:
                        continue
                    label[offset] += dx
                    label[offset + 1] += dy
            else:
                for offset in range(1, len(label), 2):
                    label[offset] += dx
                    label[offset + 1] += dy
        elif kind == 'vertex':
            if self.annotation_task == 'obb':
                points = [label[offset:offset + 2]
                          for offset in range(1, len(label), 2)]
                corner = edit['control']
                opposite = (corner + 2) % 4
                next_corner = (corner + 1) % 4
                previous_corner = (corner - 1) % 4
                origin = points[opposite]

                def unit(point):
                    vx, vy = point[0] - origin[0], point[1] - origin[1]
                    length = math.hypot(vx, vy) or 1.0
                    return vx / length, vy / length

                axis_next = unit(points[next_corner])
                axis_previous = unit(points[previous_corner])
                delta = (current_org[0] - origin[0],
                         current_org[1] - origin[1])
                next_length = (delta[0] * axis_next[0]
                               + delta[1] * axis_next[1])
                previous_length = (delta[0] * axis_previous[0]
                                   + delta[1] * axis_previous[1])
                if modifiers & Qt.ShiftModifier:
                    side = max(abs(next_length), abs(previous_length))
                    next_length = math.copysign(side, next_length or 1.0)
                    previous_length = math.copysign(
                        side, previous_length or 1.0)
                points[next_corner] = [
                    origin[0] + axis_next[0] * next_length,
                    origin[1] + axis_next[1] * next_length]
                points[previous_corner] = [
                    origin[0] + axis_previous[0] * previous_length,
                    origin[1] + axis_previous[1] * previous_length]
                points[corner] = [
                    points[next_corner][0] + points[previous_corner][0] - origin[0],
                    points[next_corner][1] + points[previous_corner][1] - origin[1]]
                label = [label[0], *(value for point in points for value in point)]
            else:
                offset = 1 + edit['control'] * 2
                label[offset:offset + 2] = current_org
        elif kind == 'bbox_vertex':
            corner = edit['control']
            if corner == 0:
                label[1:3] = current_org
            elif corner == 1:
                label[3], label[2] = current_org
            elif corner == 2:
                label[3:5] = current_org
            else:
                label[1], label[4] = current_org
            label[1], label[3] = sorted((label[1], label[3]))
            label[2], label[4] = sorted((label[2], label[4]))
        elif kind == 'edge':
            label = self.img.resize_obb_edge(
                label, edit['control'], current_org)
        elif kind == 'keypoint':
            dimensions = self.kpt_shape[1]
            offset = 5 + edit['control'] * dimensions
            label[offset:offset + 2] = current_org
            if dimensions == 3 and label[offset + 2] == 0:
                label[offset + 2] = 2
        elif kind == 'rotate':
            points = [label[offset:offset + 2]
                      for offset in range(1, len(label), 2)]
            center_x = sum(point[0] for point in points) / 4
            center_y = sum(point[1] for point in points) / 4
            start_angle = math.atan2(
                edit['start_org'][1] - center_y,
                edit['start_org'][0] - center_x)
            current_angle = math.atan2(
                current_org[1] - center_y, current_org[0] - center_x)
            angle = current_angle - start_angle
            label = self.img.rotate_obb_label(
                label, math.degrees(angle))
        if redraw:
            self.img.change_annotation(edit['index'], label)
        else:
            self.img.change_annotation(edit['index'], label, redraw=False)
        self.rect_save_current = [edit['index'], -1,
                                  self.img.label_save[edit['index']]]

    def _finish_task_box_drag(self, start, end):
        x1, y1 = self.img.new_xy_to_org_xy(start)
        x2, y2 = self.img.new_xy_to_org_xy(end)
        x1, x2 = sorted((x1, x2))
        y1, y2 = sorted((y1, y2))
        if self.annotation_task == 'obb':
            label = [self.cls, x1, y1, x2, y1, x2, y2, x1, y2]
            index = self.img.append_annotation(label)
            self.img.save()
            self._select_task_annotation(index)
        else:
            self.task_pose_bbox = [x1, y1, x2, y2]
            self.task_pose_points = []
            self._redraw_task_draft()
            self.statusBar().showMessage(
                f'POSE  |  1 / {self.kpt_shape[0]}  '
                f'{self._pose_point_name(0)}  '
                '|  Shift+左键=遮挡，右键=缺失')

    @staticmethod
    def _square_drag_end(start, end):
        dx, dy = end[0] - start[0], end[1] - start[1]
        side = max(abs(dx), abs(dy))
        return (start[0] + math.copysign(side, dx or 1.0),
                start[1] + math.copysign(side, dy or 1.0))

    @staticmethod
    def _clean_segment_points(points, epsilon=1e-6):
        """Remove duplicate clicks without changing the polygon's shape."""
        cleaned = []
        for point in points:
            point = (float(point[0]), float(point[1]))
            if (not cleaned
                    or math.hypot(point[0] - cleaned[-1][0],
                                  point[1] - cleaned[-1][1]) > epsilon):
                cleaned.append(point)
        if (len(cleaned) > 1
                and math.hypot(cleaned[-1][0] - cleaned[0][0],
                               cleaned[-1][1] - cleaned[0][1]) <= epsilon):
            cleaned.pop()
        return cleaned

    def _segment_can_close(self, position, radius=14):
        """Return True when a valid draft is close enough to its first point."""
        if (not self.img_is_load or len(self.task_draft_points) < 3):
            return False
        first = self.img.org_xy_to_new_xy(self.task_draft_points[0])
        return distance(first, position) <= radius

    def _finish_segment(self):
        points = self._clean_segment_points(self.task_draft_points)
        if len(points) < 3:
            self.statusBar().showMessage('SEGMENT  |  至少需要 3 个顶点')
            return False
        twice_area = abs(sum(
            points[index][0] * points[(index + 1) % len(points)][1]
            - points[(index + 1) % len(points)][0] * points[index][1]
            for index in range(len(points))))
        if twice_area <= 2.0:
            self.statusBar().showMessage('SEGMENT  |  多边形面积过小，无法保存')
            return False
        label = [self.cls]
        for point in points:
            label.extend(point)
        index = None
        try:
            index = self.img.append_annotation(label)
            self.img.save()
        except (OSError, ValueError) as exc:
            if index is not None and index < len(self.img.label_save):
                self.img.pop(index)
            self.statusBar().showMessage(
                f'SEGMENT SAVE FAILED  |  {exc}', 9000)
            self._redraw_task_draft()
            return False
        self.task_draft_points = []
        self.setCursor(Qt.CrossCursor)
        self._select_task_annotation(index)
        self.statusBar().showMessage('SEGMENT  |  实例分割标注已保存')
        return True

    def _cancel_segment_draft(self):
        """Discard only the unfinished segment currently being drawn."""
        if not self.task_draft_points:
            return False
        self.task_draft_points = []
        self.setCursor(Qt.CrossCursor)
        self._redraw_task_draft()
        self.statusBar().showMessage('SEGMENT  |  已取消当前绘制')
        return True

    def _insert_segment_vertex(self, edge_hit):
        """Insert a projected vertex after the selected polygon edge."""
        index, edge_index, canvas_point = edge_hit
        if not (0 <= index < len(self.img.label_save)):
            return False
        original = list(self.img.label_save[index])
        point = self.img.new_xy_to_org_xy(canvas_point)
        insert_at = 1 + (edge_index + 1) * 2
        updated = [*original[:insert_at], point[0], point[1],
                   *original[insert_at:]]
        try:
            self.img.change_annotation(index, updated)
            self.img.save()
        except (OSError, ValueError) as exc:
            try:
                self.img.change_annotation(index, original)
            except (OSError, ValueError, IndexError):
                pass
            self.statusBar().showMessage(
                f'SEGMENT INSERT FAILED  |  {exc}', 9000)
            return False
        self._select_task_annotation(index)
        self.statusBar().showMessage(
            'SEGMENT  |  已插入新顶点；拖动该顶点可调整轮廓')
        return True

    def _append_pose_point(self, position, visibility=2):
        dimensions = self.kpt_shape[1]
        if position is None:
            point = (0.0, 0.0)
        else:
            point = self.img.new_xy_to_org_xy(position)
        entry = [point[0], point[1]]
        if dimensions == 3:
            entry.append(int(visibility))
        self.task_pose_points.append(entry)
        count = len(self.task_pose_points)
        if count >= self.kpt_shape[0]:
            label = [self.cls, *self.task_pose_bbox]
            for keypoint in self.task_pose_points:
                label.extend(keypoint)
            index = None
            try:
                index = self.img.append_annotation(label)
                self.img.save()
            except (OSError, ValueError) as exc:
                if index is not None and index < len(self.img.label_save):
                    self.img.pop(index)
                self.task_pose_points.pop()
                self.statusBar().showMessage(
                    f'POSE SAVE FAILED  |  {exc}', 9000)
                self._redraw_task_draft()
                return
            self.task_pose_bbox = None
            self.task_pose_points = []
            self._select_task_annotation(index)
            self.statusBar().showMessage('POSE  |  关键点标注已保存')
        else:
            self._redraw_task_draft()
            self.statusBar().showMessage(
                f'POSE  |  {count + 1} / {self.kpt_shape[0]}  '
                f'{self._pose_point_name(count)}  '
                '|  Shift+左键=遮挡，右键=缺失')

    def _redraw_task_drag(self):
        frame = self.img.overlay_frame()
        self.img.label_show(
            self.is_choose_rect_index, pixmap=frame, commit=False)
        start = self.img.new_xy_to_org_xy(self.task_drag['start'])
        end = self.img.new_xy_to_org_xy(self.task_drag['current'])
        x1, x2 = sorted((start[0], end[0]))
        y1, y2 = sorted((start[1], end[1]))
        if self.annotation_task == 'obb':
            self.img.draw_task_draft(
                points=[(x1, y1), (x2, y1), (x2, y2), (x1, y2)],
                pixmap=frame, commit=False)
        else:
            self.img.draw_task_draft(
                bbox=[x1, y1, x2, y2], pixmap=frame, commit=False)
        self.label.setPixmap(frame)

    def _queue_interaction_redraw(self, kind, **payload):
        """Coalesce high-frequency pointer updates into the newest frame."""
        self._pending_interaction_redraw = (kind, payload)
        if not self._interaction_redraw_timer.isActive():
            self._interaction_redraw_timer.start()

    def _cancel_interaction_redraw(self):
        self._interaction_redraw_timer.stop()
        self._pending_interaction_redraw = None

    def _flush_interaction_redraw(self):
        pending = self._pending_interaction_redraw
        self._pending_interaction_redraw = None
        if pending is None or not self.img_is_load:
            return
        kind, payload = pending
        if kind in ('detect_add', 'detect_update'):
            if kind == 'detect_add':
                self.addBox(redraw=False)
            else:
                self.updDatalabel(redraw=False)
            index = self.is_choose_rect_index
            if index is None:
                return
            frame = self.img.overlay_frame()
            self.img.label_show(index, pixmap=frame, commit=False)
            self.label.setPixmap(frame)
        elif kind == 'task_edit':
            if self.task_edit is None:
                return
            self._update_task_edit(
                payload['position'], payload['modifiers'], redraw=False)
            index = payload.get('index', self.is_choose_rect_index)
            frame = self.img.overlay_frame()
            self.img.label_show(index, pixmap=frame, commit=False)
            self.label.setPixmap(frame)
        elif kind == 'task_drag':
            if self.task_drag is not None:
                self._redraw_task_drag()
        elif kind == 'task_draft':
            self._redraw_task_draft(
                cursor=payload.get('cursor'),
                close_polygon=payload.get('close_polygon', False))

    def _redraw_task_draft(self, cursor=None, close_polygon=False):
        if not self.img_is_load:
            return
        frame = self.img.overlay_frame()
        self.img.label_show(
            self.is_choose_rect_index, pixmap=frame, commit=False)
        self.img.draw_task_draft(
            points=self.task_draft_points,
            cursor=cursor,
            close_polygon=close_polygon,
            bbox=self.task_pose_bbox,
            pose_points=[point[:2] for point in self.task_pose_points
                         if len(point) < 3 or point[2] != 0],
            pixmap=frame, commit=False)
        self.label.setPixmap(frame)

    # ———————————————————————————————— 键盘事件 ————————————————————————————————#

    def keyReleaseEvent(self, event):
        if self.temp_hand:
            self.key_press = False
            self.temp_hand = False
            self.arrows = True
            self.cross = False
            self.hand = False
            self._sync_tool_mode_buttons()

    def keyPressEvent(self, event):
        if self.img_is_load and self.annotation_task != 'detect':
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if self.annotation_task == 'segment' and self.task_draft_points:
                    self._finish_segment()
                    event.accept()
                    return
            if event.key() == Qt.Key_Backspace:
                if self.annotation_task == 'segment' and self.task_draft_points:
                    self.task_draft_points.pop()
                    self._redraw_task_draft()
                    event.accept()
                    return
                if self.annotation_task == 'pose' and self.task_pose_points:
                    self.task_pose_points.pop()
                    self._redraw_task_draft()
                    event.accept()
                    return
            if event.key() == Qt.Key_Escape:
                self._cancel_interaction_redraw()
                self.task_draft_points = []
                self.task_pose_bbox = None
                self.task_pose_points = []
                self.task_drag = None
                self.task_edit = None
                self.mouse_left_press = False
                self.move_xy(index=self.is_choose_rect_index)
                self.statusBar().showMessage('ANNOTATION CANCELLED')
                event.accept()
                return
        if self.img_is_load and event.modifiers() & Qt.ControlModifier:
            # Ctrl键被按下 event.modifiers()是一个int类型的值, 用来判断Ctrl键是否被按下
            self.temp_hand, self.key_press, self.hand = True, True, True
            self.cross, self.arrows = False, False
            self._sync_tool_mode_buttons()
        else:
            self.key_press = False

    # ———————————————————————————————— 鼠标滚轮事件 ————————————————————————————————#
    def wheelEvent(self, event):
        if (self.arrows and self.img_is_load
                and self.annotation_task == 'obb'
                and self.is_choose_rect
                and self.is_choose_rect_index is not None):
            delta = event.angleDelta().y()
            if not delta:
                event.ignore()
                return
            step = 0.25 if event.modifiers() & Qt.ShiftModifier else 2.0
            degrees = delta / 120.0 * step
            index = self.is_choose_rect_index
            label = self.img.rotate_obb_label(
                self.img.label_save[index], degrees)
            self.img.change_annotation(index, label)
            self.rect_save_current = [index, -1, self.img.label_save[index]]
            self._obb_save_timer.start()
            angle = self.img.obb_angle(self.img.label_save[index])
            self.statusBar().showMessage(
                f'OBB ROTATION  |  {angle:.2f}°  '
                '|  滚轮 2° / Shift+滚轮 0.25°')
            event.accept()
            return
        if self.arrows and self.img_is_load:
            if not self.wheel_pan_enabled:
                event.ignore()
                return
            self.img.is_trans = True
            self.move_xy(0, int(event.angleDelta().y() / 4))
            event.accept()
        elif self.hand and self.img_is_load:
            if not self.wheel_zoom_enabled:
                event.ignore()
                return
            self.hand_flag = False
            angle_delta = event.angleDelta().y() / 8  # 获取滚动距离
            if 0.2 <= self.wheel_scale <= 3:
                self.wheel_scale += round(angle_delta / 150, 2)
            else:
                self.wheel_scale = min(max(0.5, self.wheel_scale), 3)
            if self.wheel_scale < 0.1:
                self.wheel_scale = 0.2
            self.img.is_trans = True
            self.move_xy()
            event.accept()

    def _save_obb_wheel_change(self):
        if self.img_is_load and self.annotation_task == 'obb':
            self.img.save()

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            if self.arrows:
                self.hand = True
                self.arrows = False
                self.setCursor(Qt.OpenHandCursor)
            elif self.hand:
                self.hand = False
                self.arrows = True
                self.setCursor(Qt.ArrowCursor)
            self._sync_tool_mode_buttons()
        # 确保继续处理其他鼠标事件
        super().mousePressEvent(event)

    # ———————————————————————————————— 状态辅助函数 ————————————————————————————————#
    def mouse_state(self):
        # 鼠标样式
        if self.hand and self.hand_flag:
            self.setCursor(Qt.ClosedHandCursor)
        if self.hand and not self.hand_flag:
            self.setCursor(Qt.OpenHandCursor)
        if self.arrows and self.cross:
            self.setCursor(Qt.CrossCursor)
        if self.arrows and not self.cross:
            self.setCursor(Qt.ArrowCursor)
        if self.arrows and not self.cross and self.hover:
            self.setCursor(Qt.SizeAllCursor)

    # ———————————————————————————————— 辅助函数 ————————————————————————————————#

    def _event_canvas_pos(self, source, event, clamp=False):
        """Return a mouse-event position in the canvas label's coordinates."""
        point = event.pos()
        if source is not self.label:
            point = self.label.mapFrom(source, point)
        position = (point.x(), point.y())
        return self.limit_xy(*position) if clamp else position

    def limit_xy(self, x, y):
        # 限制x, y的范围 不要跑出qt label的范围
        x = max(min(x, self.label.size().width()), 0)
        y = max(min(y, self.label.size().height()), 0)
        return x, y

    def limit_center(self, x, y):
        # 限制x, y的范围 不要跑出加载的图像在label上的范围
        if x <= - self.img.label_width * self.wheel_scale // 2:
            x = - self.img.label_width * self.wheel_scale // 2 + 1
        if x >= self.img.label_width + self.img.label_width * self.wheel_scale // 2:
            x = self.img.label_width + self.img.label_width * self.wheel_scale // 2 - 1
        if y <= - self.img.label_height * self.wheel_scale // 2:
            y = - self.img.label_height * self.wheel_scale // 2 + 1
        if y >= self.img.label_height + self.img.label_height * self.wheel_scale // 2:
            y = self.img.label_height + self.img.label_height * self.wheel_scale // 2 - 1
        return int(x), int(y)

    def move_xy(self, bias_x=0, bias_y=0, index=None):
        if self.img_is_load:
            # 图片移动bias_x, bias_y个像素

            x = self.img.center[0] + bias_x
            y = self.img.center[1] + bias_y

            x, y = self.limit_center(x, y)

            self.img.show(int(x), int(y), scale=self.wheel_scale)  # 显示图片
            self.img.label_show(index)  # 显示标签

    def mouse_track(self):
        if self.img_is_load:
            if len(self.move_pos_track) < 8:
                self.move_pos_track.append(self.mouse_pos)
            else:
                self.move_pos_track.append(self.mouse_pos)
                self.move_pos_track.pop(0)
                for i in range(8):
                    self.img.add_circle(self.move_pos_track[7 - i], (100, 255, 255, 100 - i * 10), 5 - i // 2,
                                        is_ball=True)

    def get_cross_or_hover(self):
        if self.img_is_load:
            self._update_pointer_target(self.mouse_pos)

    def _update_pointer_target(self, position):
        hit_type, index, point_index = self.img.hit_test(
            *position, circle_distance=15)
        self.cross = hit_type == 'handle'
        self.hover = hit_type == 'rect'
        if hit_type is not None:
            self.rect_save = [index, point_index, self.img[index][0]]
            self.rect_save_current = self.rect_save
        elif not self.is_add_box and not self.is_update_label:
            self.rect_save = None

    def pos_in_org(self, pos):
        x, y = self.img.new_xy_to_org_xy(pos)
        return 0 < x < self.img.org_width and 0 < y < self.img.org_height

    def computer_new_label(self):
        pos = self.img.new_xy_to_org_xy(self.mouse_pos)
        circle_index = self.rect_save_current[1]
        if (circle_index == -1
                and self.detect_drag_original is not None
                and self.detect_drag_start_org is not None):
            dx = pos[0] - self.detect_drag_start_org[0]
            dy = pos[1] - self.detect_drag_start_org[1]
            return self.img.translate_detect_label(
                self.detect_drag_original, dx, dy,
                self.img.org_width, self.img.org_height)

        new_label = self.rect_save_current[2]

        self.computer_new_label_assist(new_label, circle_index, pos)

        x1, y1, x2, y2 = new_label[1:5]

        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])

        # TODO: 限制框的大小
        new_label[1:5] = x1, y1, x2, y2
        return new_label

    @staticmethod
    def computer_new_label_assist(new_label, index, pos):
        mapping = {
            0: lambda: new_label.__setitem__(slice(1, 3), pos),
            1: lambda: new_label.__setitem__(slice(2, 4), pos[::-1]),
            2: lambda: new_label.__setitem__(slice(1, None, 3), pos),
            3: lambda: new_label.__setitem__(slice(3, 5), pos),
            4: lambda: new_label.__setitem__(1, pos[0]),
            5: lambda: new_label.__setitem__(4, pos[1]),
            6: lambda: new_label.__setitem__(3, pos[0]),
            7: lambda: new_label.__setitem__(2, pos[1]),
        }

        return mapping[index]()

    def add_box(self, redraw=True):
        if self.is_first_add_box and self.pos_in_org(self.mouse_press_pos):
            self.is_first_add_box = False

            # Image.append 接收的是画布坐标并负责转换；这里不能先转换一次，
            # 否则首帧会被重复换算，随后又被 change 突然纠正。
            new_box = [self.cls, *self.mouse_press_pos,
                       *self.mouse_press_pos]
            if redraw:
                self.img.append(new_box)
            else:
                self.img.append(new_box, redraw=False)
            self.len_rect += 1
            self.is_choose_rect = True
            self.is_choose_rect_index = self.len_rect - 1
            self.rect_save_current = [self.len_rect - 1, -1, self.img.basedata[-1]]

            self.categoryShowWidget.set_rect_cls(self.rect_save_current[2][0], 1)
            self.boxShowWidget.set_rect_box(self.rect_save_current[0])

        elif not self.is_first_add_box and self.pos_in_org(self.mouse_pos):

            x1, y1 = self.mouse_press_pos
            x2, y2 = self.mouse_pos

            # 转换坐标
            x1, y1 = self.img.new_xy_to_org_xy((x1, y1))
            x2, y2 = self.img.new_xy_to_org_xy((x2, y2))

            # 调整坐标，确保(x1, y1)为左上角，(x2, y2)为右下角
            x1, x2 = sorted([x1, x2])
            y1, y2 = sorted([y1, y2])

            # 更新标签信息
            self.cls = self.img.label_save[-1][0]
            new_label = [self.cls, x1, y1, x2, y2]

            if redraw:
                self.img.change(-1, new_label)
            else:
                self.img.change(-1, new_label, redraw=False)
            self.rect_save_current = [self.len_rect - 1, -1, self.img.basedata[-1]]
            self.is_choose_rect_index = self.len_rect - 1

    # ———————————————————————————————— 槽函数 ————————————————————————————————#

    def hand_button_(self):
        self.hand = True
        self.arrows = False
        self.setCursor(Qt.OpenHandCursor)
        self._sync_tool_mode_buttons()

    def arrows_button_(self):
        self.hand = False
        self.arrows = True
        self.setCursor(Qt.ArrowCursor)
        self._sync_tool_mode_buttons()

    def _sync_tool_mode_buttons(self):
        self.arrows_button.setChecked(self.arrows)
        self.hand_button.setChecked(self.hand)

    def select_folder(self):
        # 选择获取文件夹路径
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", "/home", options=options)

        if os.path.isdir(folder) and os.path.exists(folder):
            img_path = [os.path.join(folder, i) for i in os.listdir(folder)]
            img_path = [i for i in img_path if i.lower().endswith(('.jpg', '.png', '.jpeg', '.bmp', '.tiff'))]
            self.reset_thumbnail(img_path)

            self.img_list = set(img_path)
            self.img_list_only_name = set([os.path.basename(i).split('.')[0] for i in img_path])
            if len(self.img_list):
                self.is_open_file = False
                self.is_open_folder = True

    def select_file(self):
        # 选择获取文件路径
        file_path, _ = QFileDialog.getOpenFileNames(None, "选择文件", "", "All Files (*);;Text Files (*.txt)")
        p = []
        for file_path in file_path:
            if os.path.isfile(file_path) and file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                self.is_open_file = True
                self.is_open_folder = False
                p += [file_path]
        self.img_list = set(p)
        self.img_list_only_name = set([os.path.basename(i).split('.')[0] for i in p])
        if len(p):
            self.reset_thumbnail(p)
            self.is_open_file = True
            self.is_open_folder = False

    def readFolderLabel_(self):
        txt_path_ = []
        folder = ''
        if self.is_open_folder:
            options = QFileDialog.Options()
            options |= QFileDialog.ShowDirsOnly
            folder = QFileDialog.getExistingDirectory(self, "Select Folder", "/home", options=options)

            if os.path.isdir(folder) and os.path.exists(folder):
                txt_path = [os.path.join(folder, i) for i in os.listdir(folder)]
                txt_path = [i for i in txt_path if i.lower().endswith('.txt')]
                txt_path_ = {Path(i).stem for i in txt_path}
            else:
                return

        elif self.is_open_file:
            file_path, _ = QFileDialog.getOpenFileNames(None, "选择文件", "", "All Files (*);;Text Files (*.txt)")
            txt_path = []
            txt_path_ = []
            folder = os.path.dirname(file_path[0]) if len(file_path) else None
            for file_path in file_path:
                if os.path.isfile(file_path) and file_path.endswith('.txt'):
                    self.ui.thumbnailWidget.clear()
                    txt_path += [file_path]
                    txt_path_ += [Path(file_path).stem]
            if not len(txt_path):
                return

        imported = 0
        for i in txt_path_:
            if i not in self.img_list_only_name:
                continue
            source = Path(folder) / f'{i}.txt'
            destination = self.default_save_path / f'{i}.txt'
            try:
                self._merge_label_file(source, destination)
            except (OSError, ValueError) as exc:
                QMessageBox.warning(self, '标签导入失败', str(exc))
                continue
            self.label_list.add(str(destination))
            self.label_list_only_name.add(i)
            imported += 1
        if imported:
            self.ui.thumbnailWidget.clear()
            self.thumbnail_widget.init()
            self.thumbnail_widget.screen_list_widget.setCurrentRow(self.thumbnail_widget.index)
            self.thumbnail_widget.update_header()
            self.init(img_path=self.thumbnail_widget.show_list[self.thumbnail_widget.index])
            self.statusBar().showMessage(f'LABEL IMPORT COMPLETE  |  {imported} FILES')

    def _merge_label_file(self, source, destination):
        incoming = DataApp(
            source, task=self.annotation_task, kpt_shape=self.kpt_shape)
        if not destination.exists():
            shutil.copy2(source, destination)
            return
        existing = DataApp(
            destination, task=self.annotation_task,
            kpt_shape=self.kpt_shape)
        existing.merge(incoming)
        existing.save()

    def imgUp_(self):
        if self.img_is_load:
            if self.wheel_scale <= 6:
                self.wheel_scale = self.wheel_scale * 1.5
            self.img.is_trans = True
            self.move_xy()

    def imgDown_(self):
        if self.img_is_load:
            if self.wheel_scale >= 0.2:
                self.wheel_scale = self.wheel_scale * 0.5
            self.img.is_trans = True
            self.move_xy()

    def resetShowImg_(self):
        if self.img_is_load:
            self.wheel_scale = 1
            self.img.is_trans = True
            self.img.show()
            self.img.label_show()

    def deleteBox_(self, index=False):
        if self.is_choose_rect and self.is_choose_rect_index is not None:
            self.img.pop(index if index else self.is_choose_rect_index)
            self.is_choose_rect_index = None
            self.is_choose_rect = False
            self.hover = False
            self.cross = False
            self.arrows = True
            self.is_hover_move_allow = False
            self.is_update_label = False
            self.is_add_box = False
            self.categoryShowWidget.clear()
            self.boxShowWidget.clear()
            self.len_rect -= 1

            self.move_xy()
            self.img.save()

    # ———————————————————————————————— 快捷键 ————————————————————————————————#
    def handleShortcut1_(self):
        if self.img_is_load:
            if self.thumbnail_widget.index > 0:
                index = self.thumbnail_widget.index - 1
                self.thumbnail_widget.up_dowm(index)
                self.thumbnail_widget.screen_list_widget.setCurrentRow(index)
                self.boxShowWidget.clear()
                self.move_xy()

    def handleShortcut2_(self):
        if self.img_is_load:
            if self.thumbnail_widget.index < len(self.thumbnail_widget.show_list) - 1:
                index = self.thumbnail_widget.index + 1
                self.thumbnail_widget.up_dowm(index)
                self.thumbnail_widget.screen_list_widget.setCurrentRow(index)
                self.boxShowWidget.clear()
                self.move_xy()

    def handleShortcut3_(self):
        if self.img_is_load:
            if self.thumbnail_widget.index > 0:
                index = 0
                self.thumbnail_widget.up_dowm(index)
                self.thumbnail_widget.screen_list_widget.setCurrentRow(index)

    def handleShortcut4_(self):
        if self.img_is_load:
            if self.thumbnail_widget.index < len(self.thumbnail_widget.show_list) - 1:
                index = len(self.thumbnail_widget.show_list) - 1
                self.thumbnail_widget.up_dowm(index)
                self.thumbnail_widget.screen_list_widget.setCurrentRow(index)

    def cls_color_(self):
        self._open_class_manager(self.cls)

    def renew_cls_(self):
        self._open_class_manager(self.cls)

    def _open_class_manager(self, selected_class=None):
        if (self._modification_window is not None
                and self._modification_window.isVisible()):
            self._modification_window.select_class(
                self.cls if selected_class is None else selected_class)
            if self._modification_window.isMinimized():
                self._modification_window.showNormal()
            self._modification_window.raise_()
            self._modification_window.activateWindow()
            return
        self._modification_window = modificationCls(
            self, self.cls if selected_class is None else selected_class)
        self._modification_window.configChanged.connect(
            self.apply_class_configuration)
        self._modification_window.destroyed.connect(
            lambda: setattr(self, '_modification_window', None))

    def apply_class_configuration(self, names, styles):
        """Apply editor changes immediately without resetting the workspace."""
        self.names = {int(key): str(value) for key, value in names.items()}
        self.class_styles = {
            int(class_id): normalize_class_style(style)
            for class_id, style in styles.items()
        }
        self.colors = {
            class_id: list(style['fill'])
            for class_id, style in self.class_styles.items()
        }
        if self.cls not in self.names:
            self.cls = min(self.names, default=0)

        self.categoryShowWidget.init()
        if not self.img_is_load:
            return

        selected_index = self.is_choose_rect_index
        self.boxShowWidget.set_rect_box(selected_index)
        if self.categoryShowWidget.listWidget.count():
            selected_class = (
                int(self.img.label_save[selected_index][0])
                if selected_index is not None
                and selected_index < len(self.img.label_save)
                else self.cls)
            self.categoryShowWidget.set_rect_cls(
                selected_class,
                selected_index if selected_index is not None else None)

        self.img.show(*self.img.center, scale=self.wheel_scale)
        self.img.label_show(selected_index)

    def show_box_circle_(self, state):
        if self.img_is_load:
            self.img.show_box_circle = True if state else False
            self.move_xy()

    def show_other_(self, state):
        if self.img_is_load:
            self.img.show_other = True if state else False
            self.move_xy()

    def show_box_fill_(self, state):
        if self.img_is_load:
            self.img.show_box_fill = True if state else False
            self.move_xy()

    def show_box_text_(self, state):
        if self.img_is_load:
            self.img.show_box_text = True if state else False
            self.move_xy()

    def load_model_(self):
        file_path, _ = QFileDialog.getOpenFileName(None, "选择文件", "", "All Files (*);;Text Files (*.txt)")
        if os.path.isfile(file_path) and len(file_path) and file_path.endswith('.pt'):
            res = QMessageBox.question(None, '加载模型', '请耐心等待？',
                                       QMessageBox.Yes | QMessageBox.No)
            if res == QMessageBox.Yes:
                from .loadModeThread import loadModel
                os.environ['YOLO_VERBOSE'] = str(False)
                self.load_model.setEnabled(False)
                self.statusBar().showMessage(f'MODEL LOADING  |  {Path(file_path).name}')
                self.load_model_thread = loadModel(file_path)
                self.load_model_thread.signal_model_loaded.connect(self._model_loaded)
                self.load_model_thread.signal_error.connect(self._worker_error)
                self.load_model_thread.finished.connect(lambda: self.load_model.setEnabled(True))
                self.load_model_thread.start()

    def _model_loaded(self, model):
        self.yolov8_model = model
        model_task = getattr(model, 'task', None)
        if model_task == 'pose':
            model_core = getattr(model, 'model', None)
            model_shape = getattr(model_core, 'kpt_shape', None)
            if model_shape is None and hasattr(model_core, 'yaml'):
                model_shape = model_core.yaml.get('kpt_shape')
            try:
                count, dimensions = int(model_shape[0]), int(model_shape[1])
                if count > 0 and dimensions in (2, 3):
                    self.kpt_shape = (count, dimensions)
                    self.keypoint_names = (
                        self.keypoint_names
                        + [f'点 {index + 1}' for index in range(
                            len(self.keypoint_names), count)])[:count]
                    self.kpt_skeleton = [
                        edge for edge in self.kpt_skeleton
                        if edge[0] < count and edge[1] < count]
                    self._save_background_config(
                        kpt_shape=list(self.kpt_shape),
                        keypoint_names=list(self.keypoint_names),
                        kpt_skeleton=[list(edge) for edge in self.kpt_skeleton])
            except (TypeError, ValueError, IndexError):
                pass
        if model_task in ('detect', 'segment', 'obb', 'pose'):
            self.set_annotation_task(model_task)
        self.statusBar().showMessage('MODEL READY  |  可以执行 AI 检测')
        self.show_prompt('模型加载完成')

    def show_prompt(self, res):
        QMessageBox.information(self, '', res)

    def _worker_error(self, message):
        self.statusBar().showMessage(f'ERROR  |  {message}')
        QMessageBox.critical(self, '错误', message)

    def detect_(self):
        if self.img_is_load:
            if self.yolov8_model is None:
                QMessageBox.question(None, '无效', '请先加载模型',
                                     QMessageBox.Yes | QMessageBox.No)
            else:
                self.conf = self.confidence_control.value() / 100
                if self.detect_thread is not None and self.detect_thread.isRunning():
                    return
                from .loadModeThread import DetectModel
                self.detect.setEnabled(False)
                self.statusBar().showMessage(
                    f'INFERENCE RUNNING  |  {Path(self.img.img_path).name}  |  CONF {self.conf:.2f}')
                self._detect_target = self.img
                self.detect_thread = DetectModel(
                    self.yolov8_model, self.img.org_img.copy(), self.conf,
                    task=self.annotation_task, kpt_shape=self.kpt_shape)
                self.detect_thread.signal_detection_finished.connect(self._detection_finished)
                self.detect_thread.signal_error.connect(self._worker_error)
                self.detect_thread.finished.connect(lambda: self.detect.setEnabled(True))
                self.detect_thread.start()

    def _detection_finished(self, detection):
        target = self._detect_target
        if target is None:
            return
        task = detection.get('task', self.annotation_task)
        annotations = detection.get('annotations', [])
        if task != self.annotation_task:
            self._worker_error(
                f'模型任务为 {task}，当前工作台任务为 {self.annotation_task}')
            return
        try:
            for annotation in annotations:
                target.basedata._validate(annotation)
        except (TypeError, ValueError) as exc:
            self._worker_error(f'模型输出与当前任务配置不兼容: {exc}')
            return
        for annotation in annotations:
            target.basedata.append(annotation)
        target.save()
        if self.img is target:
            target.label_save = []
            target.load_new_labels()
            self.move_xy()
            self.boxShowWidget.clear()
        self.statusBar().showMessage(
            f'INFERENCE COMPLETE  |  {Path(target.img_path).name}  |  {len(annotations)} OBJECTS ADDED')

    def save_(self):
        # 选择获取文件夹路径
        if self.is_open_file or self.is_open_folder:
            options = QFileDialog.Options()
            options |= QFileDialog.ShowDirsOnly
            folder = QFileDialog.getExistingDirectory(self, "Select Folder", "/home", options=options)
            if os.path.isdir(folder) and os.path.exists(folder):
                exported = 0
                for i in self.img_list_only_name:
                    p = os.path.join(self.default_save_path, i + '.txt')
                    if os.path.exists(p) and os.path.getsize(p) > 0:
                        shutil.copy(p, folder)
                        exported += 1
                self.statusBar().showMessage(f'EXPORT COMPLETE  |  {exported} LABEL FILES  |  {folder}')

    # 鼠标放到框上显示框的颜色加深， 不悬浮的时候颜色恢复
    def mouse_hover_display(self):
        if self.img_is_load and self.len_rect and (self.hover or self.cross) and not self.is_choose_rect:
            index_ = self.rect_save_current[0] if self.rect_save_current else None
            self.move_xy(index=index_)

            if not self.is_choose_rect and not self.is_add_box and not self.is_update_label \
                    and self.rect_save_current is not None:
                self.categoryShowWidget.set_rect_cls(self.rect_save_current[2][0])
                self.boxShowWidget.set_rect_box(self.rect_save_current[0])

        elif self.img_is_load and not self.is_choose_rect:
            self.categoryShowWidget.clear()
            self.boxShowWidget.clear()
            self.move_xy()

    # 鼠标点击框则算是选中框， 框加粗，保持常亮， 点击其他框或者点击空白处恢复
    def already_choose_rect_display(self):
        if self.img_is_load and self.arrows and self.is_choose_rect:
            self.move_xy(index=self.is_choose_rect_index)

            if not self.is_choose_rect_over_striking:
                self.categoryShowWidget.set_rect_cls(self.rect_save_current[2][0], 1)
                self.boxShowWidget.set_rect_box(self.rect_save_current[0])

                self.is_choose_rect_over_striking = True
        else:
            self.is_choose_rect_over_striking = False

    def moveImage(self):
        if self.hand and not self.hand_flag:
            self.hand_flag = True
        self.img.is_trans = True
        self.move_xy(self.mouse_pos[0] - self.mouse_save_temp[0], self.mouse_pos[1] - self.mouse_save_temp[1])
        self.mouse_track()
        self.mouse_save_temp = self.mouse_pos
        self.is_choose_rect_index = None
        self.is_choose_rect = False

    def updDatalabel(self, index=None, redraw=True):
        # TODO: 优化
        new_label = self.computer_new_label()

        if self.is_first_update_label:
            self.is_choose_rect = True

            self.categoryShowWidget.set_rect_cls(self.rect_save_current[2][0], 1)
            self.boxShowWidget.set_rect_box(self.rect_save_current[0])
            self.is_first_update_label = False

        self.rect_save_current[-1] = new_label  # 框索引, label
        self.rect_save = self.rect_save_current

        if redraw:
            self.img.change(self.rect_save_current[0], new_label)
        else:
            self.img.change(
                self.rect_save_current[0], new_label, redraw=False)

        self.is_choose_rect = True
        self.is_choose_rect_index = self.rect_save_current[0]

    def addBox(self, redraw=True):
        if self.pos_in_org(self.mouse_pos):
            self.add_box(redraw=redraw)
            self.rect_save_current = [len(self.img.label_save) - 1, -1, self.img.label_save[-1]]
            self.is_choose_rect = True
            self.is_choose_rect_index = len(self.img.label_save) - 1

    def reset_thumbnail(self, img_list):
        if self.thumbnail_widget is not None:
            self.thumbnail_widget.stop_loader()
        self.label.clear()
        self.ui.thumbnailWidget.clear()
        self.thumbnail_widget = thumbnailApp(self.ui.thumbnailWidget, self.current_label_name_show, self, img_list,
                                             self.label_list,
                                             size=(self.thumbnail_preview_size,
                                                   self.thumbnail_preview_size))
        self.thumbnail_widget.screen_list_widget.setDragDropMode(QListWidget.NoDragDrop)

        self.is_open_file = False
        self.is_choose_rect_index = None
        self.is_update_label = False
        self.is_add_box = False

        if self.img_is_load:
            self.len_rect = len(self.img.label_save)
            self.thumbnail_widget.screen_list_widget.setCurrentRow(0)
            self.thumbnail_widget.update_header()
