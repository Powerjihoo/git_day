import multiprocessing as mp
import os
import sys
import time

import loguru
from loguru._logger import Logger as _Logger

from config import settings
from resources.constant import CONST
from utils.scheme.singleton import SingletonInstance


class Logger(_Logger, metaclass=SingletonInstance):
    def __init__(self): ...

    def create_logger(
        self,
        log_dir: str,
        log_format_console: str,
        log_format_file: str,
        log_level_console: str = "DEBUG",
        log_level_file: str = "SUCCESS",
        *args,
        **kwargs,
    ) -> object:
        logger = loguru.logger
        logger.remove()
        logger.add(sys.stderr, level=log_level_console, format=log_format_console)
        logger.add(
            log_dir, level=log_level_file, format=log_format_file, *args, **kwargs
        )

        return logger


def handle_exception(exc_type, exc_value, exc_traceback):
    logger.opt(exception=(exc_type, exc_value, exc_traceback)).error(
        "Unhandled exception occur!!"
    )


def logging_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()

        logger.trace(
            f"Processing time: {func.__module__} | {func.__qualname__} -> "
            f"{(end_time - start_time):.6f}sec",
        )
        return result

    return wrapper


LOG_FORMAT_FILE = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS}|<level>{level: <8}| >> {message}</level>"
)
LOG_FORMAT_CONSOLE = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>|<level>{level: <8}| >> {message:<98}{module:>20}:{line:<4}| {function}</level>"

# Create logger
log_folder = CONST.LOG_PATH
app_name = f"{CONST.PROGRAM_NAME}_{settings.server_id}"
proc_name = mp.current_process().name
log_level_file = settings.log.level_file
log_level_console = settings.log.level_console


logger = Logger().create_logger(
    log_dir=f"{os.path.join(log_folder, proc_name, app_name)}.log",
    log_format_console=LOG_FORMAT_CONSOLE,
    log_format_file=LOG_FORMAT_FILE,
    log_level_console=log_level_console,
    log_level_file=log_level_file,
    rotation="00:00",
    retention="3 months",
    backtrace=True,
    diagnose=True,
)

sys.excepthook = handle_exception
