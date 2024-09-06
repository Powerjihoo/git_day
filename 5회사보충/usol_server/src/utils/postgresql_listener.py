import asyncio
from typing import Optional

import asyncpg

if __name__ == "__main__":
    import os
    import sys

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from abc import ABC, abstractmethod

from config import settings

from utils.logger import logger


class PostgresListener(ABC):
    """A class for listening to PostgreSQL database notifications."""

    def __init__(
        self,
        dsn: str,
        channels: str | list[str] = [],
        timeout: Optional[int] = 5,
        connection_check_interval: Optional[int] = 1,
    ) -> None:
        """
        _summary_

        Args:
            dsn (str): The data source name string to connect to the database
                        ex) postgres://{USER}:{PASSWORD}@{HOST}:{PORT}/{DANAME}
            channels (str | list[str], optional): The channel to listen for notification on. Defaults to [].
            timeout (Optional[int], optional): The timeout value for database connections,in seconds.. Defaults to 5.

        Attributes:
            dsn (str): The Data Source Name string to connect to the database.
            channel (str): The channel to listen for notifications on.
            connection (Optional[asyncpg.Connection]): The connection to the database.
            timeout (int): The timeout value for database connections, in seconds.
        """
        self.dsn = dsn
        self.channels = channels

        self.connection: Optional[asyncpg.Connection] = None
        self.timeout = timeout
        self.connection_check_interval = connection_check_interval

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(channels: {self.channels}"

    async def __connect_db(self, initialize: bool = False) -> None:
        """
        A coroutine that connects to the PostgreSQL database.

        If a connection error occurs, the coroutine will retry after a 5-second delay.

        """
        while True:
            try:
                self.connection = await asyncpg.connect(
                    dsn=self.dsn, timeout=self.timeout
                )
                logger.debug(f"Connected to database: {self}")
                break
            except (asyncpg.PostgresConnectionError, asyncio.CancelledError):
                logger.error("Failed to connect to database, retrying in 5 seconds...")
                await asyncio.sleep(5)
            except ConnectionRefusedError:
                logger.error("Connection refused, retrying in 5 seconds...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error("Can not connect to postgres listener", e)
                if initialize:
                    import os

                    logger.exception(
                        "Please check the postgresql database listener setting", e
                    )
                    os._exit(0)

    async def __add_listeners(self, channels: str | list[str]) -> None:
        """
        A coroutine that add listener with specific channel name(s)

        Args:
            channels (str | list[str]): channel name
        """
        if isinstance(channels, str):
            channels = [channels]
        if isinstance(channels, list):
            for channel in channels:
                await self.connection.add_listener(channel, self.handle_notify)

    @abstractmethod
    async def handle_notify(
        self, conn: asyncpg.Connection, pid: int, channel: str, payload: str
    ) -> None:
        """
        A coroutine that handles a PostgreSQL database notification.

        Args:
            conn (asyncpg.Connection): The connection to the database.
            pid (int): The process ID of the PostgreSQL server process that sent the notification.
            channel (str): The name of the channel that the notification was sent on.
            payload (str): The payload of the notification.

        """
        raise NotImplementedError

    async def listen(self) -> None:
        """
        A coroutine that listens for notifications on the specified channel.

        If the database connection is closed, the coroutine will attempt to reconnect.

        """
        await self.__connect_db(initialize=True)
        await self.__add_listeners(self.channels)

        while True:
            if self.connection.is_closed():
                logger.error("Database connection closed, attempting to reconnect...")
                await self.__connect_db()
                await self.__add_listeners(self.channels)
            await asyncio.sleep(self.connection_check_interval)

    async def run(self):
        await self.listen()


if __name__ == "__main__":
    listener = PostgresListener(
        dsn=settings.DB_SOURCE_NAME,
        channels=["my_table_insert"],
    )
    asyncio.run(listener.run())
    asyncio.sleep(5)
