import ctypes
import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMessageBox
from utils import MainWin, root
from utils.window_chrome import IndustrialProxyStyle


APP_ICON_PATH = root / 'material' / 'app_icon.ico'


def set_windows_app_identity():
    """Give the script-hosted app its own Windows taskbar identity."""
    if not sys.platform.startswith('win'):
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            'LabelS.IndustrialVisionAnnotation')
    except (AttributeError, OSError):
        pass


if __name__ == '__main__':
    set_windows_app_identity()
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setApplicationName('LabelS')
    app.setApplicationDisplayName('LabelS')
    app.setWindowIcon(QIcon(str(APP_ICON_PATH)))
    app.setStyle(IndustrialProxyStyle('Fusion'))
    temp_folder = Path(root) / 'temp_folder'
    temp_files = list(temp_folder.glob('*.txt'))
    if temp_files:
        reply = QMessageBox.question(None, '删除确认', '是否删除上一次标注残留标签?', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            for path in temp_files:
                path.unlink()
    window = MainWin()
    window.show()
    sys.exit(app.exec_())
