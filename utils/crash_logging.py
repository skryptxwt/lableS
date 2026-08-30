"""Persistent diagnostics for failures raised from Qt callbacks."""

import faulthandler
import logging
import os
import sys
import tempfile
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOGGER_NAME = 'labels'
_LOG_DIRECTORY = None
_FAULT_STREAM = None


def _candidate_log_directories():
    local_app_data = os.environ.get('LOCALAPPDATA')
    if local_app_data:
        yield Path(local_app_data) / 'LabelS' / 'logs'
    yield Path(tempfile.gettempdir()) / 'LabelS' / 'logs'


def _prepare_log_directory():
    global _LOG_DIRECTORY
    if _LOG_DIRECTORY is not None:
        return _LOG_DIRECTORY
    for directory in _candidate_log_directories():
        try:
            directory.mkdir(parents=True, exist_ok=True)
            _LOG_DIRECTORY = directory
            return directory
        except OSError:
            continue
    return None


def log_file_path():
    directory = _prepare_log_directory()
    return directory / 'labels.log' if directory is not None else None


def _write_unhandled(exc_type, exc_value, exc_traceback, context):
    logging.getLogger(LOGGER_NAME).critical(
        'Unhandled exception in %s', context,
        exc_info=(exc_type, exc_value, exc_traceback))


def configure_crash_logging():
    """Install rotating Python logs and a fatal native crash trace."""
    global _FAULT_STREAM
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    path = log_file_path()
    if path is not None and not any(
            isinstance(handler, RotatingFileHandler)
            and Path(handler.baseFilename) == path
            for handler in logger.handlers):
        handler = RotatingFileHandler(
            path, maxBytes=2 * 1024 * 1024, backupCount=4,
            encoding='utf-8')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)s | %(threadName)s | %(message)s'))
        logger.addHandler(handler)

    def exception_hook(exc_type, exc_value, exc_traceback):
        _write_unhandled(
            exc_type, exc_value, exc_traceback, 'Python main thread')

    sys.excepthook = exception_hook

    if hasattr(threading, 'excepthook'):
        def thread_exception_hook(args):
            _write_unhandled(
                args.exc_type, args.exc_value, args.exc_traceback,
                f'worker thread {args.thread.name}')
        threading.excepthook = thread_exception_hook

    if path is not None and _FAULT_STREAM is None:
        try:
            _FAULT_STREAM = (path.parent / 'fatal.log').open(
                'a', encoding='utf-8', buffering=1)
            faulthandler.enable(_FAULT_STREAM, all_threads=True)
        except (OSError, RuntimeError):
            _FAULT_STREAM = None

    logger.info('LabelS diagnostics initialized')
    return path


def log_qt_exception(receiver, event):
    receiver_name = type(receiver).__name__ if receiver is not None else 'None'
    try:
        event_type = int(event.type()) if event is not None else -1
    except (AttributeError, TypeError, ValueError):
        event_type = -1
    logging.getLogger(LOGGER_NAME).exception(
        'Qt callback failed | receiver=%s event=%s',
        receiver_name, event_type)
