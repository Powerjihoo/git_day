import argparse
import os
import sys
from typing import Optional

import yaml

from resources.constant import CONST

parser = argparse.ArgumentParser(prog=CONST.PROGRAM_NAME)
parser.add_argument("--config", type=str, help="config file path")
args = parser.parse_args()

if not (config_path := args.config):
    config_path = "script-server.yaml"


class ServerSettings:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def __repr__(self) -> str:
        return f"{__class__.__name__}(host={self.host}, port={self.port})"


class DatabaseSettings:
    def __init__(
        self,
        host: str,
        port: int,
        database: str = 0,
        username: str = None,
        password: str = None,
    ):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.db_url = f"dbname={self.database} user={self.username} host={self.host} password={self.password} port={self.port}"

    def __repr__(self) -> str:
        return (
            f"{__class__.__name__}("
            f"host={self.host}, port={self.port}, "
            f"database={self.database}, username={self.username}, password={self.password})"
        )


class LogSettings:
    def __init__(
        self,
        level_file: str,
        level_console: str,
        uvicorn_log_level: str,
        use_api_timing: bool,
        uvicorn_log_level_timing: str,
        logging_router: bool = False,
        logging_request_body: bool = False,
    ):
        self.level_file = level_file
        self.level_console = level_console
        self.uvicorn_log_level = uvicorn_log_level
        self.use_api_timing = use_api_timing
        self.uvicorn_log_level_timing = uvicorn_log_level_timing
        self.logging_router = logging_router
        self.logging_request_body = logging_request_body

    def __repr__(self) -> str:
        return (
            f"{__class__.__name__}("
            f"level_file={self.level_file}, level_console={self.level_console}, "
            f"uvicorn_log_level={self.uvicorn_log_level}, "
            f"use_api_timing={self.use_api_timing}, uvicorn_log_level_timing={self.uvicorn_log_level_timing})"
        )


class KafkaSettings:
    def __init__(
        self,
        brokers: list,
        topic_model_values: str,
        topic_pred_values: str,
        disable_consumer_group: bool = False,
    ):
        self.brokers = brokers
        self.topic_model_values = topic_model_values
        self.topic_pred_values = topic_pred_values
        self.disable_consumer_group = disable_consumer_group

    def __repr__(self) -> str:
        return (
            f"{__class__.__name__}("
            f"brokers={self.brokers}, topic_model_values={self.topic_model_values}, "
            f"topic_pred_values={self.topic_pred_values})"
        )


class DataSettings:
    def __init__(self, temp_folder_window: str, temp_folder_linux: str):
        if sys.platform.startswith("win"):
            self.temp_path = temp_folder_window
        else:
            self.temp_path = temp_folder_linux

    def __repr__(self) -> str:
        return f"{__class__.__name__}(model_path={self.temp_path}"


class SystemSettings:
    def __init__(self, enable_swagger: bool = False):
        self.enable_swagger = enable_swagger

    def __repr__(self) -> str:
        return f"{__class__.__name__}(target_gpu_device_no={self.target_gpu_device_no})"


class AppConfig:
    def __init__(
        self,
        server_id: str,
        servers: dict,
        databases: dict,
        log: LogSettings = None,
        data: DataSettings = None,
        system: SystemSettings = None,
        kafka: KafkaSettings = None,
    ):
        self.server_id = server_id
        self.servers = servers
        self.databases = databases
        self.log = log
        self.data = data
        self.system = system
        self.kafka = kafka

    def __repr__(self) -> str:
        return (
            f"{__class__.__name__}(servers={self.servers}, "
            f"databases={self.databases}, log={self.log}, data={self.data}, "
            f"gpu={self.system}, kafka={self.kafka})"
        )


def load_app_config_from_yaml(file_path: str) -> Optional[AppConfig]:
    try:
        print(f"Loading config file... {os.getcwd()}/{file_path}")
        with open(file_path, "r") as file:
            yaml_data = yaml.safe_load(file)
        server_id = yaml_data.get("server-id")
        servers = {
            server_name: ServerSettings(**settings)
            for server_name, settings in yaml_data.get("servers", {}).items()
        }
        databases = {
            db_name: DatabaseSettings(**settings)
            for db_name, settings in yaml_data.get("databases", {}).items()
        }
        log = LogSettings(**yaml_data.get("log", {}))
        data = DataSettings(**yaml_data.get("data", {}))
        system = SystemSettings(**yaml_data.get("system", {}))
        kafka = KafkaSettings(**yaml_data.get("kafka", {}))
        return AppConfig(
            server_id=server_id,
            servers=servers,
            databases=databases,
            log=log,
            data=data,
            system=system,
            kafka=kafka,
        )
    except Exception as e:
        print(f"Error loading YAML file: {e}")
        return None


settings = load_app_config_from_yaml(config_path)
