import ctypes
import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMessageBox
from utils import MainWin, root
from utils.crash_logging import configure_crash_logging, log_qt_exception
from utils.window_chrome import IndustrialProxyStyle


APP_ICON_PATH = root / 'material' / 'app_icon.ico'


class SafeApplication(QApplication):
    """Keep Python exceptions in Qt callbacks from terminating the process."""

    def notify(self, receiver, event):
        try:
            return super().notify(receiver, event)
        except Exception:
            log_qt_exception(receiver, event)
            window = self.activeWindow()
            if window is not None and hasattr(window, 'statusBar'):
                try:
                    window.statusBar().showMessage(
                        '操作发生异常，程序已恢复；详细信息已写入日志', 8000)
                except Exception:
                    pass
            return False


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
    configure_crash_logging()
    set_windows_app_identity()
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = SafeApplication(sys.argv)
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
