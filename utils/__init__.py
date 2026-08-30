from pathlib import Path

root = Path(__file__).parent


def __getattr__(name):
    """Delay importing the Qt application until it is actually requested."""
    if name == 'MainWin':
        from .mainWindow import MainWin
        return MainWin
    raise AttributeError(name)

__all__ = ['MainWin', 'root']
