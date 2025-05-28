import time

import orjson
from google import protobuf
from kafka import KafkaConsumer

from _protobuf.script_data_pb2 import FromIPCM
from config import settings
from dbinfo.tag_value import ScriptTagValueQueue
from resources.constant import CONST
from utils.logger import logger, logging_time

from .models import ScriptDataFromKafka

script_tag_value_queue = ScriptTagValueQueue()


class StreamDataCollector:
    """
    A class for collecting and processing streaming data from a Kafka topic.

    Args:
        broker (str): The address of the Kafka broker.
        topic (str): The Kafka topic to consume messages from.

    Methods:
        receive_message() -> None:
            Polls messages from the Kafka topic and processes them.

        receive_message_raw() -> None:
            Polls raw messages from the Kafka topic and processes them.

        close() -> None:
            Closes the Kafka consumer connection.
    """

    def __init__(self, broker, topic):
        """
        Initializes the StreamDataCollector with the specified Kafka broker and topic.

        Args:
            broker (str): The address of the Kafka broker.
            topic (str): The Kafka topic to consume messages from.
        """
        self.broker = broker
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=self.broker,
            client_id=f"{CONST.PROGRAM_NAME}_{settings.server_id}",
            group_id=f"{CONST.PROGRAM_NAME}_{settings.server_id}"
            if not settings.kafka.disable_consumer_group
            else None,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            consumer_timeout_ms=1000,
            max_poll_records=1,
            session_timeout_ms=300000,
            max_poll_interval_ms=600000,
            heartbeat_interval_ms=10000,
            fetch_min_bytes=0,
            fetch_max_wait_ms=250,
        )

    def receive_message(self) -> None:
        """
        Polls messages from the Kafka topic and processes them.

        This method retrieves messages, parses them using Protocol Buffers, and updates the
        script tag value queue with the extracted data. It handles decoding errors and logs
        exceptions if they occur.

        Returns:
            None
        """
        # logger.trace("polling start")
        res = self.consumer.poll(timeout_ms=0)
        # logger.trace("polling end")
        if not res:
            time.sleep(0.5)
            return
        logger.trace("Get message")
        message_pb = FromIPCM()
        for messages in res.values():
            try:
                for message in messages:
                    message_pb.ParseFromString(message.value)
                    logger.trace(
                        f"  => Model data in message from IPCM: {len(message_pb.script_data)}"
                    )

                    for model_value in message_pb.script_data:
                        try:
                            script_tag_value_queue.update_data(
                                model_value.script_key, model_value.data
                            )
                        except Exception as e:
                            logger.error(e)
            except protobuf.message.DecodeError:
                continue
            except Exception as e:
                logger.exception(e)

    @logging_time
    def receive_message_raw(self) -> None:
        """
        Polls raw messages from the Kafka topic and processes them.

        This method retrieves messages, decodes them using JSON, and updates the script
        tag value queue with the extracted data. It handles decoding errors and logs
        exceptions if they occur.

        Returns:
            None
        """
        res = self.consumer.poll(timeout_ms=0)
        if not res:
            time.sleep(0.5)
            return
        logger.trace("Get message")
        for messages in res.values():
            try:
                for message in messages:
                    logger.trace(
                        f"  => Model data in message from IPCM: {len(message)}"
                    )

                    script_data_list = [
                        ScriptDataFromKafka.from_dict(script_data)
                        for script_data in orjson.loads(message.value)
                    ]

                    for script_data in script_data_list:
                        try:
                            script_tag_value_queue.update_data(
                                script_data.script_key, script_data.data
                            )
                        except Exception as e:
                            logger.error(e)
            except protobuf.message.DecodeError:
                continue
            except Exception as e:
                logger.exception(e)

    def close(self):
        self.consumer.close()
