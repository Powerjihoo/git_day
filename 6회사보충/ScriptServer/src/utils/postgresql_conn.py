import json
import threading
from typing import Dict, Optional

import pandas as pd
import psycopg2
import sqlalchemy
from psycopg2 import sql
from psycopg2.errors import UndefinedTable
from sqlalchemy.dialects.postgresql import insert

from utils.logger import logger
from utils.scheme.singleton import SingletonInstance


class PostgreSQLConnector(metaclass=SingletonInstance):
    connection = None
    cursor = None
    db_url = None

    def __init__(self, db_url=None):
        self._lock = threading.Lock()
        if db_url is not None:
            PostgreSQLConnector.db_url = db_url
            self.connect_database()

    def connect_database(self):
        if PostgreSQLConnector.connection is None or self.connection.closed:
            try:
                PostgreSQLConnector.connection = psycopg2.connect(
                    PostgreSQLConnector.db_url
                )
                PostgreSQLConnector.cursor = PostgreSQLConnector.connection.cursor()
            except Exception as e:
                logger.error(f"Error: Connection not established {e}")
            else:
                logger.debug("PostgreSQL Database connection created")

        self.connection = PostgreSQLConnector.connection
        self.cursor = PostgreSQLConnector.cursor

    def execute(self, sql_str: str) -> list:
        with self._lock:
            if self.connection.closed:
                self.connect_database()
            try:
                self.cursor.execute(sql_str)
                result = self.cursor.fetchall()
                return result
            except UndefinedTable as e:
                logger.exception(e)

    def insert(
        self,
        table: str,
        fields: list[str],
        params: list,
        returning_fields: str | list[str] = None,
    ) -> dict:
        with self._lock:
            if self.connection.closed:
                self.connect_database()
            # SQL query construction
            fields_identifiers = [sql.Identifier(field) for field in fields]
            placeholders = [sql.Placeholder() for _ in fields]

            query = sql.SQL("INSERT INTO {table} ({fields}) VALUES ({values})").format(
                table=sql.Identifier(table),
                fields=sql.SQL(", ").join(fields_identifiers),
                values=sql.SQL(", ").join(placeholders),
            )

            if returning_fields:
                if isinstance(returning_fields, str):
                    returning_fields = [returning_fields]
                returning_identifiers = [
                    sql.Identifier(field) for field in returning_fields
                ]
                query += sql.SQL(" RETURNING {returning_fields}").format(
                    returning_fields=sql.SQL(", ").join(returning_identifiers)
                )

            # Execute query
            self.cursor.execute(query, params)
            self.connection.commit()

            if returning_fields:
                result = self.cursor.fetchone()
                if result:
                    return dict(zip(returning_fields, result))

    def insert_many(
        self,
        table: str,
        fields: list[str],
        params_list: list[list],
        returning_fields: str | list[str] = None,
    ) -> list[dict]:
        with self._lock:
            if self.connection.closed:
                self.connect_database()

            # SQL query construction
            fields_identifiers = [sql.Identifier(field) for field in fields]
            placeholders = [sql.Placeholder() for _ in fields]

            values_placeholder = sql.SQL("({values})").format(
                values=sql.SQL(", ").join(placeholders)
            )
            values_placeholders = sql.SQL(", ").join(
                [values_placeholder] * len(params_list)
            )

            query = sql.SQL(
                "INSERT INTO {table} ({fields}) VALUES {values_placeholders}"
            ).format(
                table=sql.Identifier(table),
                fields=sql.SQL(", ").join(fields_identifiers),
                values_placeholders=values_placeholders,
            )

            if returning_fields:
                if isinstance(returning_fields, str):
                    returning_fields = [returning_fields]
                returning_identifiers = [
                    sql.Identifier(field) for field in returning_fields
                ]
                query += sql.SQL(" RETURNING {returning_fields}").format(
                    returning_fields=sql.SQL(", ").join(returning_identifiers)
                )

            # Execute query
            all_params = [param for value_set in params_list for param in value_set]
            self.cursor.execute(query, all_params)
            self.connection.commit()

            if returning_fields:
                result = self.cursor.fetchall()
                if result:
                    return [dict(zip(returning_fields, row)) for row in result]
                return []
            return []

    def insert_raw(self, sql_str: str) -> None:
        if self.connection.closed:
            self.connect_database()
        try:
            self.cursor.execute(sql_str)
            PostgreSQLConnector.connection.commit()
        except Exception as e:
            logger.exception(e)

    def delete(self, sql_str: str) -> None:
        if self.connection.closed:
            self.connect_database()
        try:
            self.cursor.execute(sql_str)
            PostgreSQLConnector.connection.commit()
        except Exception as e:
            logger.exception(e)

    def update(self, sql_str: str) -> None:
        if self.connection.closed:
            self.connect_database()
        try:
            self.cursor.execute(sql_str)
            PostgreSQLConnector.connection.commit()
        except Exception as e:
            logger.exception(e)

    def __load_table_data_by_sql(self, sql_str: str) -> list:
        result = self.execute(sql_str)
        return result

    def load_table_data(self, table: str, scheme: str = "public") -> list:
        _sql = f"SELECT * FROM {scheme}.{table}"
        result = self.execute(_sql)
        return result

    def load_table_columns(self, table: str, scheme: str = "public") -> list:
        _sql = f"SELECT column_name FROM information_schema.columns WHERE table_schema='{scheme}' AND table_name='{table}'"
        result = self.execute(_sql)
        return [i[0] for i in result]

    def load_table_as_df_by_sql(
        self, sql_str: str, table: str, scheme: str = "public", index_col: str = None
    ) -> pd.DataFrame:
        _data = self.__load_table_data_by_sql(sql_str)
        _columns = self.load_table_columns(table, scheme)
        result = pd.DataFrame(_data, columns=_columns)
        if index_col:
            result.set_index(index_col, drop=True, inplace=True)
        return result

    def load_table_as_df(
        self, table: str, scheme: str = "public", index_col: str = None
    ) -> pd.DataFrame:
        _data = self.load_table_data(table)
        _columns = self.load_table_columns(table, scheme)
        result = pd.DataFrame(_data, columns=_columns)
        if index_col:
            result.set_index(index_col, drop=True, inplace=True)
        return result

    def load_table_as_json(
        self, table: str, scheme: str = "public", index_col: str = None
    ) -> str:
        _data = self.load_table_data(table)
        _columns = self.load_table_columns(table, scheme)

        results = []
        for row in _data:
            results.append(dict(zip(_columns, row)))

        if index_col:
            _data.set_index(index_col, drop=True, inplace=True)
        return json.dumps(results, ensure_ascii=False)


class PostgreSQLEngine(metaclass=SingletonInstance):
    def __init__(self, user, password, db, host, port):
        self.conn = self.connect(
            user,
            password,
            db,
            host,
            port,
        )
        self.meta: sqlalchemy.MetaData = sqlalchemy.MetaData(self.conn)
        self.create_upsert_method(None)

    def connect(self, user, password, db, host, port=5432):
        url = "postgresql://{}:{}@{}:{}/{}".format(user, password, host, port, db)
        return sqlalchemy.create_engine(url, client_encoding="utf8")

    def create_upsert_method(self, extra_update_fields: Optional[Dict[str, str]]):
        """
        Create upsert method that satisfied the pandas's to_sql API.
        """

        def method(table, conn, keys, data_iter):
            # select table that data is being inserted to (from pandas's context)
            sql_table = sqlalchemy.Table(table.name, self.meta, autoload=True)

            # list of dictionaries {col_name: value} of data to insert
            values_to_insert = [dict(zip(keys, data)) for data in data_iter]

            # create insert statement using postgresql dialect.
            # For other dialects, please refer to https://docs.sqlalchemy.org/en/14/dialects/
            insert_stmt = sqlalchemy.dialects.postgresql.insert(
                sql_table, values_to_insert
            )

            # create update statement for excluded fields on conflict
            update_stmt = {exc_k.key: exc_k for exc_k in insert_stmt.excluded}
            if extra_update_fields:
                update_stmt.update(extra_update_fields)

            # create upsert statement.
            upsert_stmt = insert_stmt.on_conflict_do_update(
                index_elements=sql_table.primary_key.columns,  # index elements are primary keys of a table
                set_=update_stmt,  # the SET part of an INSERT statement
            )

            # execute upsert statement
            conn.execute(upsert_stmt)

        self.upsert_method = method


def psql_upsert(table, conn, keys, data_iter, pk_name):
    for row in data_iter:
        data = dict(zip(keys, row))
        insert_st = insert(table.table).values(**data)
        upsert_st = insert_st.on_conflict_do_update(constraint=pk_name, set_=data)
        conn.execute(upsert_st)
