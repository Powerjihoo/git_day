import json
import math
from typing import Dict, Optional

import pandas as pd
import psycopg2
import sqlalchemy
from sqlalchemy.dialects.postgresql import insert

from utils.scheme.singleton import SingletonInstance


class PostgreSQLConnector(metaclass=SingletonInstance):
    # ! Need to threading LOCK????
    def __init__(self, db_url=None):
        self.conn = None
        self.db_url = db_url
        if self.db_url is not None:
            self.connect_database()
            if self.conn is None:
                raise ValueError(f"Can not connect to postgresql server {db_url}")

    def __repr__(self) -> str:
        return self.db_url

    def connect_database(self):
        if self.conn is None or self.conn.closed:
            try:
                self.conn = psycopg2.connect(self.db_url)
            except Exception as e:
                print(e)

    def get_page_count(self, table_name: str, num_rows: int) -> int:
        _sql = f"SELECT count(*) FROM {table_name}"
        result = self.execute_query(_sql)
        cnt_rows = result[0][0]
        cnt_page = math.ceil(cnt_rows / num_rows)
        return cnt_page

    def get_colnames(self, table_name: str) -> list[str]:
        try:
            with self.conn.cursor() as cur:
                query = f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'"
                cur.execute(query)
                result = [row[0] for row in cur.fetchall()]
                return result
        except (psycopg2.errors.InFailedSqlTransaction, psycopg2.errors.InterfaceError):
            print("exceptions....")
            if self.conn.closed:
                self.connect_database()
            self.conn.rollback()
            cur.execute(query)

    def get_primary_key_identifier(self, table_name: str) -> str:
        try:
            with self.conn.cursor() as cur:
                query = f"SELECT constraint_name FROM information_schema.table_constraints WHERE table_name = '{table_name}' and constraint_type = 'PRIMARY KEY';"
                cur.execute(query)
                result = cur.fetchall()
                if result:
                    return result[0][0]
                return None
        except (psycopg2.errors.InFailedSqlTransaction, psycopg2.errors.InterfaceError):
            if self.conn.closed:
                self.connect_database()
            print("exceptions....")
            self.conn.rollback()
            cur.execute(query)

    def get_primary_key_columns(self, constraint_name: str):
        try:
            with self.conn.cursor() as cur:
                query = f"SELECT column_name FROM information_schema.constraint_column_usage WHERE constraint_name='{constraint_name}'"
                cur.execute(query)
                result = [row[0] for row in cur.fetchall()]
                return result
        except (psycopg2.errors.InFailedSqlTransaction, psycopg2.errors.InterfaceError):
            if self.conn.closed:
                self.connect_database()
            print("exceptions....")
            self.conn.rollback()
            cur.execute(query)

    def upsert_data(
        self,
        data: pd.DataFrame,
        table_name: str,
        columns: list[str],
        unique_cols: list[str],
    ):
        # 데이터 일괄 처리 쿼리 생성
        column_str = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))
        conflict_str = ", ".join(
            [f"{col}=excluded.{col}" for col in columns if col not in unique_cols]
        )
        query = f"""
            INSERT INTO {table_name} ({column_str})
            VALUES ({placeholders})
            ON CONFLICT ({', '.join(unique_cols)}) DO UPDATE
            SET {conflict_str};
        """

        # 데이터 일괄 처리를 위한 리스트
        values = []
        for _, row in data.iterrows():
            row_values = []
            for col in columns:
                row_values.append(row[col])
            values.append(tuple(row_values))

        # 데이터 일괄 처리
        with self.conn:
            with self.conn.cursor() as cur:
                try:
                    cur.executemany(query, values)
                    self.conn.commit()
                except psycopg2.errors.InFailedSqlTransaction:
                    if self.conn.closed:
                        self.connect_database()
                    self.conn.rollback()
                    cur.executemany(query, values)
                    self.conn.commit()

    def insert_data(
        self, data: pd.DataFrame, table_name: str, column_map: dict[str, str]
    ):
        with self.conn:
            with self.conn.cursor() as cur:
                for _, row in data.iterrows():
                    column_string = ", ".join([f"{k}" for k in column_map.keys()])
                    value_string = ", ".join(
                        [f"'{row[column_map[k]]}'" for k in column_map.keys()]
                    )
                    query_string = f"""INSERT INTO {table_name} ({column_string})
                                    VALUES ({value_string});"""
                    try:
                        print(query_string)
                        cur.execute(query_string)
                        self.conn.commit()
                    except psycopg2.errors.UniqueViolation as e:
                        # If the row already exists in the database, do nothing and move on to the next row
                        pass

    def execute_update_many(self, query, data_list):
        try:
            with self.conn as conn:
                with conn.cursor() as cur:
                    cur.executemany(query, data_list)
                conn.commit()
        except (psycopg2.errors.InFailedSqlTransaction, psycopg2.errors.InterfaceError):
            print("exceptions....")
            if self.conn.closed:
                self.connect_database()
            self.conn.rollback()
            cur.execute(query)

    def execute_update(self, query: str):
        try:
            with self.conn:
                with self.conn.cursor() as cur:
                    cur.execute(query)
        except (psycopg2.errors.InFailedSqlTransaction, psycopg2.errors.InterfaceError):
            print("exceptions....")
            if self.conn.closed:
                self.connect_database()
            self.conn.rollback()
            cur.execute(query)

    def execute_query(self, query: str) -> None:
        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                result = cur.fetchall()
            return result
        except (
            psycopg2.errors.InFailedSqlTransaction,
            psycopg2.errors.InterfaceError,
            psycopg2.errors.AdminShutdown,
        ):
            print("exceptions....")
            if self.conn.closed:
                self.connect_database()
            self.conn.rollback()
            cur.execute(query)

    def load_table_columns(self, table: str, scheme: str = "public") -> list:
        _sql = f"SELECT column_name FROM information_schema.columns WHERE table_schema='{scheme}' AND table_name='{table}'"
        result = self.execute_query(_sql)
        return [i[0] for i in result]

    def load_table_data(
        self,
        table: str,
        num_rows: int = None,
        page_no: int = None,
        scheme: str = "public",
    ) -> list:
        _sql = f"SELECT * FROM {scheme}.{table}"
        if num_rows is not None and page_no is not None:
            offset = (page_no - 1) * num_rows
            _sql += f" OFFSET {offset} LIMIT {num_rows}"
        result = self.execute_query(_sql)
        return result

    def load_table_as_dict_by_sql(
        self, sql: str, table: str, columns: list[str] = None, scheme: str = "public"
    ) -> list[dict]:
        _data = self.execute_query(sql)
        if columns is None:
            _columns = self.load_table_columns(table, scheme)
        else:
            _columns = columns
        results = [dict(zip(_columns, row)) for row in _data]
        return results

    def load_table_as_df_by_sql(
        self, sql: str, table: str, scheme: str = "public", index_col: str = None
    ) -> pd.DataFrame:
        _data = self.execute_query(sql)
        _columns = self.load_table_columns(table, scheme)
        result = pd.DataFrame(_data, columns=_columns)
        if index_col:
            result.set_index(index_col, drop=True, inplace=True)
        return result

    def load_table_as_df(
        self,
        table: str,
        scheme: str = "public",
        index_col: str = None,
        num_rows: int = None,
        page_no: int = None,
    ) -> pd.DataFrame:
        _data = self.load_table_data(table, num_rows, page_no)
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
        results = [dict(zip(_columns, row)) for row in _data]

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
