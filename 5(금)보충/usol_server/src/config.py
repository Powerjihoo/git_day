# import toml
import sys
import traceback

import tomllib
from munch import DefaultMunch
from resources.constant import CONST
from utils.scheme.singleton import SingletonInstance

# * Read configuration file from config.toml


def load_config(file_path):
    with open(file_path, "rb") as f:
        return tomllib.load(f)


class Settings(metaclass=SingletonInstance):
    try:
        __config = load_config(CONST.CONFIG_PATH)
        config = DefaultMunch.fromDict(__config)

        setting_servers = config.servers
        APP_HOST: str = setting_servers.Algorithm.get("host", "0.0.0.0")
        APP_PORT: int = setting_servers.Algorithm.get("port", 51000)

        setting_log = config.log
        LOG_LEVEL_FILE: str = setting_log.get("level_file", "INFO")
        LOG_LEVEL_CONSOLE: str = setting_log.get("level_console", "DEBUG")
        USE_API_LOG_TIMING: bool = setting_log.get("use_api_timing", True)
        LOG_LEVEL_UVICORN: str = setting_log.get("uvicorn_log_level", "info")
        LOG_LEVEL_UVICORN_TIMING: str = setting_log.get(
            "uvicorn_log_level_timing", "info"
        )

        setting_directory = config.directory
        MODEL_PATH_1: str = setting_directory.get("model_path_1")
        MODEL_PATH_2: str = setting_directory.get("model_path_2")
        MODEL_PATH_3: str = setting_directory.get("model_path_3")
        MODEL_PATH_4: str = setting_directory.get("model_path_4")

    except Exception:
        print(f"Failed to strat {CONST.PROGRAM_NAME} due to config error")
        print(traceback.format_exc())
        sys.exit()


settings = Settings()
