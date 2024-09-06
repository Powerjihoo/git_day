import atexit as _atexit
import multiprocessing as mp
import os
import sys
import time
from functools import wraps

from loguru._logger import Core as _Core
from loguru._logger import Logger as _Logger

from utils.singleton import SingletonInstance


class Logger(_Logger, metaclass=SingletonInstance):
    def __init__(self):
        ...

    def create_logger(
        self,
        log_dir: str,
        log_format_console: str,
        log_format_file: str,
        log_level_console: str = "DEBUG",
        log_level_file: str = "SUCCESS",
        is_out_consol: bool = True,
        *args,
        **kwargs,
    ) -> object:
        logger = _Logger(
            core=_Core(),
            exception=None,
            depth=0,
            record=False,
            lazy=False,
            colors=False,
            raw=False,
            capture=True,
            patcher=None,
            extra={},
        )
        if is_out_consol:
            logger.add(sys.stderr, level=log_level_console, format=log_format_console)

        logger.add(
            log_dir, level=log_level_file, format=log_format_file, *args, **kwargs
        )
        _atexit.register(logger.remove)

        return logger


def handle_exception(exc_type, exc_value, exc_traceback):
    logger.opt(exception=(exc_type, exc_value, exc_traceback)).error(
        "Unhandled exception occur!!"
    )


def logging_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        logger.trace(
            f"Processing time: {func.__module__} | {func.__qualname__} -> {(end_time-start_time):.4f}sec\n"
        )
        return result

    return wrapper


LOG_FORMAT_FILE = "{time:YYYY-MM-DD HH:mm:ss}|<level>{level: <8}| >> {message}</level>"
LOG_FORMAT_CONSOLE = "<green>{time:YYYY-MM-DD HH:mm:ss}</green>|<level>{level: <9} >> {message:<109}{module:>20}:{line:<4}| {function}</level>"

import config

LOG_INFO = config.LOG_CONFIG
# Create logger
log_folder = LOG_INFO.LOG_PATH
app_name = LOG_INFO.PROGRAM_NAME


logger = Logger().create_logger(
    log_dir=f"{os.path.join(log_folder, app_name)}.log",
)

sys.excepthook = handle_exception
