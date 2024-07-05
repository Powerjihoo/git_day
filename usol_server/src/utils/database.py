import sys
import traceback
from sqlite3 import OperationalError

import psycopg2
import pymysql
from config import settings
from psycopg2 import InterfaceError

from utils.logger import logger
from utils.scheme.singleton import SingletonInstance


class MariaDBConnector:
    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        name: str = "DB",
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.name = name
        self.conn = None
        self.get_connector()

    def get_connector(self):
        try:
            self.conn = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=0.5,
            )
            logger.debug(f"Database connection has been established ({self.name})")
        except pymysql.err.OperationalError:
            logger.error(
                f"Can not connect to database ({self.name}) host={self.host}, port={self.port}"
            )
            self.conn = None

    def select(self, sql):
        try:
            if not self.conn:
                self.get_connector()
            if self.conn:
                with self.conn.cursor() as cur:
                    logger.debug(f"Quering to {self.name}... {sql}")
                    cur.execute(sql)
                    result = cur.fetchall()
                    return result
        except (pymysql.err.OperationalError, pymysql.err.InterfaceError) as e:
            logger.error(f"Can not query to {self.name}", e)
            self.conn = None


class PGConnector(metaclass=SingletonInstance):
    session_closed = 0

    def __init__(self):
        self.connect_db()

    def __del__(self):
        self.db.close()
        self.cursor.close()

    def connect_db(self):
        try:
            self.db = psycopg2.connect(settings.POSTGRES_URL)
            self.check_connection()
            self.cursor = self.db.cursor()
            logger.debug("Database connection established")
        except Exception:
            logger.exception("Can not connect to database")
            print(settings.POSTGRES_URL)
            print(traceback.format_exc())
            sys.exit()

    def check_connection(self):
        PGConnector.session_closed = self.db.closed

    def execute(self, query, args=None):
        if args is None:
            args = {}
        try:
            self.cursor.execute(query, args)
            return self.cursor.fetchall()
        except OperationalError:
            logger.exception("Database session is closed unexpectedly")
        except InterfaceError:
            logger.debug("Database cursor was closed. try to reconnect to database...")
            self.connect_db()
            self.execute(self, query)

    def commit(self):
        self.cursor.commit()
        self.cursor.commit()
        self.cursor.commit()

