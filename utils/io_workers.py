"""Background workers for image, label and export file operations."""

import os
import shutil
from pathlib import Path

from PyQt5.QtCore import QThread, pyqtSignal

from .DataApp import DataApp


IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif'}


def merge_label_file(source, destination, task, kpt_shape):
    """Merge one label file and normalize supported prediction output."""
    source = Path(source)
    destination = Path(destination)
    incoming = DataApp(
        source, task=task, kpt_shape=kpt_shape,
        accept_prediction_output=True)
    if not destination.exists():
        incoming.label_path = destination
        incoming.save()
        return len(incoming), incoming.normalized_prediction_rows
    existing = DataApp(destination, task=task, kpt_shape=kpt_shape)
    added = existing.merge(incoming)
    existing.save()
    return added, incoming.normalized_prediction_rows


class ImageScanWorker(QThread):
    progress = pyqtSignal(int, int, str)
    completed = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, paths=None, folder=None, parent=None):
        super().__init__(parent)
        self.paths = list(paths or ())
        self.folder = Path(folder) if folder else None

    def run(self):
        try:
            candidates = self.paths
            if self.folder is not None:
                self.progress.emit(0, 0, '正在扫描图片目录')
                candidates = [
                    entry.path for entry in os.scandir(self.folder)
                    if entry.is_file(follow_symlinks=False)
                ]
                candidates.sort(key=lambda path: Path(path).name.casefold())
            valid = []
            total = len(candidates)
            for current, value in enumerate(candidates, start=1):
                if self.isInterruptionRequested():
                    return
                path = Path(value)
                if path.suffix.lower() in IMAGE_EXTENSIONS and path.is_file():
                    valid.append(str(path))
                self.progress.emit(current, total, path.name)
            self.completed.emit({
                'paths': valid,
                'skipped': total - len(valid),
            })
        except (OSError, ValueError) as exc:
            self.failed.emit(f'图片导入失败: {exc}')


class LabelImportWorker(QThread):
    progress = pyqtSignal(int, int, str)
    completed = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, destination_folder, image_stems, task, kpt_shape,
                 sources=None, folder=None, parent=None):
        super().__init__(parent)
        self.destination_folder = Path(destination_folder)
        self.image_stems = set(image_stems)
        self.task = task
        self.kpt_shape = tuple(kpt_shape)
        self.sources = [Path(path) for path in (sources or ())]
        self.folder = Path(folder) if folder else None

    def run(self):
        try:
            sources = self.sources
            if self.folder is not None:
                self.progress.emit(0, 0, '正在扫描标签目录')
                sources = sorted(
                    (Path(entry.path) for entry in os.scandir(self.folder)
                     if entry.is_file(follow_symlinks=False)
                     and Path(entry.name).suffix.lower() == '.txt'),
                    key=lambda path: path.name.casefold())
            sources = [
                path for path in sources
                if path.suffix.lower() == '.txt'
                and path.stem in self.image_stems
            ]
            imported = []
            errors = []
            converted_rows = 0
            total = len(sources)
            for current, source in enumerate(sources, start=1):
                if self.isInterruptionRequested():
                    return
                destination = self.destination_folder / source.name
                try:
                    _added, converted = merge_label_file(
                        source, destination, self.task, self.kpt_shape)
                    imported.append(str(destination))
                    converted_rows += converted
                except (OSError, TypeError, ValueError) as exc:
                    errors.append(f'{source.name}: {exc}')
                self.progress.emit(current, total, source.name)
            self.completed.emit({
                'imported': imported,
                'errors': errors,
                'converted_rows': converted_rows,
                'matched': total,
            })
        except (OSError, ValueError) as exc:
            self.failed.emit(f'标签导入失败: {exc}')


class LabelExportWorker(QThread):
    progress = pyqtSignal(int, int, str)
    completed = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, source_folder, image_stems, destination_folder,
                 parent=None):
        super().__init__(parent)
        self.source_folder = Path(source_folder)
        self.image_stems = sorted(set(image_stems), key=str.casefold)
        self.destination_folder = Path(destination_folder)

    def run(self):
        try:
            self.destination_folder.mkdir(parents=True, exist_ok=True)
            exported = 0
            errors = []
            total = len(self.image_stems)
            for current, stem in enumerate(self.image_stems, start=1):
                if self.isInterruptionRequested():
                    return
                source = self.source_folder / f'{stem}.txt'
                destination = self.destination_folder / source.name
                try:
                    if source.is_file() and source.stat().st_size > 0:
                        if source.resolve() != destination.resolve():
                            shutil.copy2(source, destination)
                        exported += 1
                except OSError as exc:
                    errors.append(f'{source.name}: {exc}')
                self.progress.emit(current, total, source.name)
            self.completed.emit({
                'exported': exported,
                'errors': errors,
                'folder': str(self.destination_folder),
            })
        except OSError as exc:
            self.failed.emit(f'标签导出失败: {exc}')
