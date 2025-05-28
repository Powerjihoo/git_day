import queue
import threading

from _protobuf.script_data_pb2 import FromIPCM
from api_client.apis.tagvalue import tagvalue_api
from dbinfo import exceptions as ex
from utils.logger import logger, logging_time
from utils.scheme.singleton import SingletonInstance


class ScriptTagValueQueue(dict, metaclass=SingletonInstance):
    """
    A singleton class for managing a queue of script tag values.

    This class extends the built-in dictionary to store script keys and their associated
    tag values in a thread-safe manner using a queue. It provides methods to initialize
    the queue with data from a database, update the data, and manage the queue for each
    script key.

    Methods:
        initialize() -> None:
            Initializes the queue with data loaded from the IPCM server.

        load_db_info() -> dict:
            Loads the current values from the database.

        update_data(script_key, model_tag_values) -> None:
            Updates the queue with new tag values for a given script key.

        _put(script_key: str, tag_values: dict) -> None:
            Adds tag values to the queue for a specific script key.

        _pop(script_key: str) -> None:
            Removes and returns the oldest item from the queue for a specific script key.

        __add_model(script_key: str) -> None:
            Adds a new queue for the specified script key.
    """

    def __init__(self):
        """
        Initializes the queue with data loaded from the IPCM server.

        This method fetches model data from the IPCM server and populates the queue
        with the retrieved values. It raises an error if the data loading fails.

        Raises:
            InitializingFailError: If unable to load tag value data from IPCM Server.
        """
        super().__init__()
        self._lock = threading.Lock()
        # self.initialize()

    @logging_time
    def initialize(self) -> None:
        try:
            # ! FIXME: 모델별 protobuf 데이터 받아서 initialize 필요
            message_pb = FromIPCM()
            message = self.load_db_info()
            message_pb.ParseFromString(message.value)

            for model_value in message_pb.model_data:
                self.update_data(
                    script_key=model_value.model_key, model_tag_values=model_value.data
                )

            logger.info(
                f"{'Initializing':12} | Model data loaded successfully num_model={len(message_pb)}"
            )
        except Exception as e:
            raise ex.InitializingFailError(
                message="Can not load tag value data from IPCM Server"
            ) from e

    @logging_time
    def load_db_info(self) -> dict:
        """
        Loads the current values from the database.

        Returns:
            dict: The current database model info data.
        """
        result = {}
        __data = tagvalue_api.get_current_values_all()
        if __data.status_code == 200:
            result = __data.json()
        return result

    def update_data(self, script_key, model_tag_values) -> None:
        """
        Updates the queue with new tag values for a given script key.

        Args:
            script_key (str): The key identifying the script.
            model_tag_values (dict): The tag values to be added to the queue.
        """
        self._put(script_key, model_tag_values)

    def _put(self, script_key: str, tag_values: dict) -> None:
        """
        Adds tag values to the queue for a specific script key.

        This method manages the queue's size and handles situations where the queue
        is full by removing the oldest item.

        Args:
            script_key (str): The key identifying the script.
            tag_values (dict): The tag values to be added to the queue.
        """
        try:
            self[script_key].put_nowait(tag_values)
        except KeyError:
            self.__add_model(script_key)
            self[script_key].put_nowait(tag_values)
        except queue.Full:
            self._pop(script_key)
            self[script_key].put_nowait(tag_values)
        except Exception as e:
            logger.warning(e)

    def _pop(self, script_key: str) -> None:
        """
        Removes and returns the oldest item from the queue for a specific script key.

        Args:
            script_key (str): The key identifying the script.

        Returns:
            The oldest tag value from the queue.
        """
        return self[script_key].get_nowait()

    def __add_model(self, script_key: str) -> None:
        """
        Adds a new queue for the specified script key.

        This method creates a new queue with a maximum size for the specified script key.

        Args:
            script_key (str): The key identifying the script.
        """
        self[script_key] = queue.Queue(maxsize=40)
