import json
import threading
from contextlib import suppress
import pandas as pd
import pymssql
import sqlalchemy

from utils.logger import logger, logging_time
from utils.scheme.singleton import SingletonInstance


class MSSQLConnector:
    def __init__(
        self,
        host: str,
        database: str,
        username: str,
        password: str,
        port: int = 1433,
        charset="UTF-8",
    ):
        self.host = host
        self.database = database
        self.username = username
        self.password = password
        self.port = port
        self.charset = charset
        self.connect()

    def connect(self):
        try:
            self.conn = pymssql.connect(
                host=self.host,
                database=self.database,
                user=self.username,
                password=self.password,
                port=self.port,
                charset=self.charset,
                login_timeout=3,
            )
        except Exception as e:
            logger.error(e)
            self.conn = None

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def execute_query(self, sql: str, params: tuple = ()):
        if self.conn is None:
            self.connect()
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, params)
            self.conn.commit()
            return True
        except pymssql.Error as e:
            logger.error(e)
            self.conn.rollback()
            return False
        except Exception as e:
            logger.error(e)
            self.connect()
        finally:
            with suppress(Exception):
                cursor.close()

    def insert_data(self, table: str, data: dict):
        columns = ", ".join(data.keys())
        values = ", ".join([f"'{value}'" for value in data.values()])
        sql = f"INSERT INTO {table} ({columns}) VALUES ({values})"
        return self.execute_query(sql)

    def update_data(self, table: str, data: dict, condition: str = ""):
        set_clause = ", ".join(
            [f"{column} = '{value}'" for column, value in data.items()]
        )
        sql = f"UPDATE {table} SET {set_clause}"
        if condition:
            sql += f" WHERE {condition}"
        return self.execute_query(sql)

    def select_data(self, table: str, columns: str = "*", condition: str = ""):
        sql = f"SELECT {columns} FROM {table}"
        if condition:
            sql += f" WHERE {condition}"
        cursor = self.conn.cursor(as_dict=True)
        cursor.execute(sql)
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def delete_data(self, table: str, condition: str = ""):
        sql = f"DELETE FROM {table}"
        if condition:
            sql += f" WHERE {condition}"
        return self.execute_query(sql)


class MSSQLConnector_old(object):
    connection = None
    cursor = None
    db_url = None

    def __init__(
        self,
        host: str = None,
        user: str = None,
        password: str = None,
        database: str = None,
        port=1433,
    ):
        self._lock = threading.Lock()
        if host is not None:
            MSSQLConnector_old.host = host
            if user is not None:
                MSSQLConnector_old.user = user
            if password is not None:
                MSSQLConnector_old.password = password
            if database is not None:
                MSSQLConnector_old.database = database
            if port is not None:
                MSSQLConnector_old.port = port
            self.connect_database()

    def connect_database(self):
        if MSSQLConnector_old.connection is None or not self.connection._conn.connected:
            try:
                MSSQLConnector_old.connection = pymssql.connect(
                    host=MSSQLConnector_old.host,
                    user=MSSQLConnector_old.user,
                    password=MSSQLConnector_old.password,
                    database=MSSQLConnector_old.database,
                    port=MSSQLConnector_old.port,
                    charset="EUC-KR",
                    login_timeout=5,
                )
                MSSQLConnector_old.cursor = MSSQLConnector_old.connection.cursor()
            except Exception as e:
                logger.error(f"Error: Connection not established {e}")
            else:
                logger.debug("MSSQL Database connection created")

        self.connection = MSSQLConnector_old.connection
        self.cursor = MSSQLConnector_old.cursor

    def insert(self, sql: str) -> bool:
        with self._lock:
            if self.connection is None or not self.connection._conn.connected:
                self.connect_database()
            try:
                self.cursor.execute(sql)
                MSSQLConnector_old.connection.commit()
                return True
            except Exception as e:
                logger.error(e)
                return False

    def execute(self, sql: str) -> list:
        with self._lock:
            if self.connection is None or not self.connection._conn.connected:
                self.connect_database()
            try:
                self.cursor.execute(sql)
                result = self.cursor.fetchall()
                return result
            except Exception as e:
                logger.exception(e)

    def delete(self, sql: str) -> None:
        with self._lock:
            if self.connection is None or not self.connection._conn.connected:
                self.connect_database()
            try:
                self.cursor.execute(sql)
                MSSQLConnector_old.connection.commit()
            except Exception as e:
                logger.exception(e)

    def update(self, sql: str) -> None:
        with self._lock:
            if self.connection is None or not self.connection._conn.connected:
                self.connect_database()
            try:
                self.cursor.execute(sql)
                MSSQLConnector_old.connection.commit()
            except Exception as e:
                logger.exception(e)

    def load_table_data(self, table: str, scheme: str = "dbo") -> list:
        _sql = f"SELECT * FROM {scheme}.{table}"
        result = self.execute(_sql)
        if result:
            return result
        else:
            None

    def load_table_columns(self, table: str, scheme: str = "dbo") -> list:
        _sql = f"SELECT column_name FROM information_schema.columns WHERE table_schema='{scheme}' AND table_name='{table}'"
        result = self.execute(_sql)
        if result:
            return [i[0] for i in result]
        else:
            None

    def load_table_as_df(
        self, table: str, scheme: str = "dbo", index_col: str = None
    ) -> pd.DataFrame:
        _data = self.load_table_data(table)
        _columns = self.load_table_columns(table, scheme)
        result = pd.DataFrame(_data, columns=_columns)
        if index_col:
            result.set_index(index_col, drop=True, inplace=True)
        return result

    def load_table_as_json(
        self, table: str, scheme: str = "dbo", index_col: str = None
    ):
        _data = self.load_table_data(table)
        _columns = self.load_table_columns(table, scheme)

        results = []
        for row in _data:
            results.append(dict(zip(_columns, row)))

        if index_col:
            _data.set_index(index_col, drop=True, inplace=True)
        return json.dumps(results, ensure_ascii=False)

    def upsert_df(self, df: pd.DataFrame, table: str, scheme: str = "dbo") -> None:
        ...


class MSSQLEngine(metaclass=SingletonInstance):
    def __init__(self, user, password, db, host, port):
        self.conn = self.connect(
            user,
            password,
            db,
            host,
            port,
        )

    def connect(self, user, password, db, host, port=1433):
        url = f"mssql+pymssql://{user}:{password}@{host}:{port}/{db}"
        return sqlalchemy.create_engine(url, echo=True)
