from sqlite3 import OperationalError
import sys
import traceback

import psycopg2
from psycopg2 import InterfaceError
from config import settings
from utils.logger import logger
from utils.scheme.singleton import SingletonInstance


class Databases(metaclass=SingletonInstance):

    session_closed = 0

    def __init__(self):
        self.connect_db()

    def __del__(self):
        self.db.close()
        self.cursor.close()

    def connect_db(self):
        try:
            self.db = psycopg2.connect(settings.DATABASE_URL)
            self.check_connection()
            self.cursor = self.db.cursor()
            logger.debug("Database connection established")
        except Exception:
            logger.exception("Can not connect to database")
            print(settings.DATABASE_URL)
            print(traceback.format_exc())
            sys.exit()

    def check_connection(self):
        Databases.session_closed = self.db.closed

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
