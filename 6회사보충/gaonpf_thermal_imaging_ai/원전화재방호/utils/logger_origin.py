import atexit
import os
import sys
import time
from functools import wraps

from loguru import logger as _Logger
from loguru import logger as _logger


class Logger:
    def __init__(self):
        self.logger = _logger

    def create_logger(
        self,
        log_dir: str,
        log_format_console: str,
        log_format_file: str,
        log_level_console: str = "DEBUG",
        log_level_file: str = "INFO",
        is_out_console: bool = True,
        *args,
        **kwargs,
    ) -> _Logger:
        self.logger.remove()  # 기존의 핸들러 제거
        if is_out_console:
            self.logger.add(sys.stderr, level=log_level_console, format=log_format_console)

        self.logger.add(
            log_dir, level=log_level_file, format=log_format_file, *args, **kwargs
        )
        atexit.register(self.logger.remove)

        return self.logger


def handle_exception(exc_type, exc_value, exc_traceback):
    _logger.opt(exception=(exc_type, exc_value, exc_traceback)).error(
        "Unhandled exception occurred!!"
    )


def logging_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        _logger.trace(
            f"Processing time: {func.__module__} | {func.__qualname__} -> {(end_time-start_time):.4f}sec\n"
        )
        return result

    return wrapper


LOG_FORMAT_FILE = "{time:YYYY-MM-DD HH:mm:ss}|<level>{level: <8}| >> {message}</level>"
LOG_FORMAT_CONSOLE = "<green>{time:YYYY-MM-DD HH:mm:ss}</green>|<level>{level: <9} >> {message:<109}{module:>20}:{line:<4}| {function}</level>"

# 로거 설정
log_folder = 'logs'  # 로그 파일이 저장될 폴더
app_name = 'application'  # 애플리케이션 이름

# 로그 폴더가 존재하지 않으면 생성
os.makedirs(log_folder, exist_ok=True)

logger = Logger().create_logger(
    log_dir=os.path.join(log_folder, f"{app_name}.log"),
    log_format_console=LOG_FORMAT_CONSOLE,
    log_format_file=LOG_FORMAT_FILE
)

sys.excepthook = handle_exception