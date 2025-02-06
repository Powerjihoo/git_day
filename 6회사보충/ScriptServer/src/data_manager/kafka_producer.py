import orjson
from kafka import KafkaProducer


def json_value_serializer(value):
    return orjson.dumps(value, option=orjson.OPT_SERIALIZE_NUMPY)


class MessageProducer:
    """
    A class for producing messages to a Kafka topic.

    Args:
        broker (str): The address of the Kafka broker.
        topic (str): The Kafka topic to which messages will be sent.

    Methods:
        send_message(msg):
            Sends a message to the specified Kafka topic.
    """

    def __init__(self, broker, topic):
        """
        Initializes the MessageProducer with the specified Kafka broker and topic.

        Args:
            broker (str): The address of the Kafka broker.
            topic (str): The Kafka topic to which messages will be sent.
        """
        self.broker = broker
        self.topic = topic
        self.producer = KafkaProducer(
            bootstrap_servers=self.broker,
            acks=0,
            api_version=(2, 5, 0),
            retries=3,
        )

    def send_message(self, msg):
        """
        Sends a message to the specified Kafka topic.

        This method attempts to send a message and waits for the response. If the message
        is sent successfully, it returns a success status. Otherwise, it raises an exception.

        Args:
            msg (Any): The message to send to the Kafka topic.

        Returns:
            dict: A dictionary containing the status code and error information.

        Raises:
            Exception: If sending the message fails.
        """
        try:
            future = self.producer.send(self.topic, msg)
            self.producer.flush()
            future.get(timeout=2)
            return {"status_code": 200, "error": None}
        except Exception as e:
            raise e
