from utils.database import Databases
from utils.logger import logger
import traceback
from psycopg2.errors import InFailedSqlTransaction


class CRUD(Databases):
    def insertDB(self, schema, table, colum, data):
        sql = " INSERT INTO {schema}.{table}({colum}) VALUES ('{data}') ;".format(
            schema=schema, table=table, colum=colum, data=data
        )
        try:
            self.cursor.execute(sql)
            self.db.commit()
        except Exception as e:
            print(" insert DB err ", e)

    def readDB(self, schema, table, sel_columns, whe_column, whe_arg, whe_condition):
        super().check_connection()
        if Databases.session_closed:
            super().__init__

        sql = " SELECT {sel_columns} FROM {schema}.{table} WHERE {whe_column} {whe_arg} {whe_condition} ".format(
            sel_columns=sel_columns,
            schema=schema,
            table=table,
            whe_column=whe_column,
            whe_arg=whe_arg,
            whe_condition=whe_condition,
        )
        try:
            self.cursor.execute(sql)
            result = self.cursor.fetchall()
            # TODO: self.db.close() (?)
        except InFailedSqlTransaction as err:
            logger.exception("Can not read database", err)
        except Exception as err:
            logger.exception("Unexpected error occur", err)

        return result

    def updateDB(
        self, schema, table, upd_column, upd_value, whe_column, whe_arg, whe_condition
    ):
        super().check_connection()
        if Databases.session_closed:
            super().__init__

        sql = " UPDATE {schema}.{table} SET {upd_column} = {upd_value} WHERE {whe_column} {whe_arg} {whe_condition} ".format(
            schema=schema,
            table=table,
            upd_column=upd_column,
            upd_value=upd_value,
            whe_column=whe_column,
            whe_arg=whe_arg,
            whe_condition=whe_condition,
        )
        try:
            self.cursor.execute(sql)
            # TODO: self.cursor.commit(?)
            self.db.commit()
        except Exception as err:
            logger.exception("Can not update database", err)
            traceback.print_exc()

    def deleteDB(self, schema, table, condition):
        sql = " delete from {schema}.{table} where {condition} ; ".format(
            schema=schema, table=table, condition=condition
        )
        try:
            self.cursor.execute(sql)
            self.db.commit()
        except Exception as e:
            print("delete DB err", e)

    def checkDB(self, schema, table):
        super().check_connection()
        if Databases.session_closed:
            super().__init__

        sql = f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{schema}' and table_name = '{table}'"
        # select table_name from information_schema.tables where table_schema = 'public'and table_name = 'model_info'
        try:
            self.cursor.execute(sql)
            hastable = bool(self.cursor.fetchall())
        except Exception as err:
            logger.exception("Can not check database", err)

        return hastable

