# LabelS

基于 PyQt5 的 YOLO 检测框标注工具，支持图片浏览、手工标注、标签导入导出和 Ultralytics 模型辅助检测。

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

