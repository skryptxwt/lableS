# LabelS

基于 PyQt5 的 YOLO 工业视觉标注工具，支持图片浏览、手工标注、标签导入导出和 Ultralytics 模型辅助标注。

## 标注任务

顶部“任务”菜单可以切换四种 Ultralytics YOLO 标签格式：

- 检测：拖动绘制普通检测框；选中后可直接拖动框内部整体移动，四角和四边中点用于缩放。
- 实例分割：逐点单击绘制多边形，双击、右键或 `Enter` 闭合，`Backspace` 撤销顶点；选中已有多边形后，双击任意边线可插入新顶点，随后可拖动该顶点调整轮廓。
- OBB：拖动绘制旋转框，按住 `Shift` 拖动可锁定正方形；选中后可拖动框内部整体移动，拖动四角调整两个方向，拖动四边中点单独调整对应边，拖动框上方圆点旋转，或使用滚轮按 2° 调整（Shift + 滚轮按 0.25° 精调）。OBB 会始终保持直角和对边平行。
- 关键点：先拖动目标框，再依次标记关键点；左键表示可见，`Shift+左键` 表示遮挡，右键表示缺失。

任务菜单中的“关键点配置”可以设置 `kpt_shape`、关键点名称和骨架连接。不同任务的 `.txt` 标签结构不兼容，建议在导入图片或标签前先选择任务模式。

加载 Detect、Segment、OBB 或 Pose 模型后，工作台会识别模型任务；可在“加载模型”菜单中执行当前模型。

## 安装与启动

建议使用独立虚拟环境：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

类别名称、颜色和临时标签目录由 `Detection.yaml` 配置。运行期间产生的临时标签默认位于 `utils/temp_folder`，退出前请通过界面的保存功能导出正式标签。

## 测试

不依赖 GUI 的数据层测试可直接运行：

```powershell
python -m unittest discover -s tests -v
```
