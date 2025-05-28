import influxdb
import pandas as pd

from utils.logger import logger, logging_time
from utils.scheme.singleton import SingletonInstance


class InfluxConnector(metaclass=SingletonInstance):
    def __init__(
        self, host: str, port: int, username: str, password: str, database: str
    ) -> None:
        self.conn = influxdb.InfluxDBClient(
            host=host,
            port=port,
            username=username,
            password=password,
            database=database,
        )

    def __create_query(self, tagnames: str | list[str], start: str, end: str):
        if isinstance(tagnames, str):
            tagnames = [tagnames]
        tag_conditions = " OR ".join([f"tagname = '{tagname}'" for tagname in tagnames])
        query = f"SELECT * FROM rawvalue WHERE ({tag_conditions}) and time >= '{start}' and time <= '{end}'"  # noqa: E501
        return query

    def __parse_influx_res(
        self, influx_res: influxdb.resultset.ResultSet
    ) -> pd.DataFrame:
        series = influx_res.raw["series"]
        if not series:
            return pd.DataFrame()
        df = pd.DataFrame(series[0]["values"], columns=series[0]["columns"])
        return df

    @logging_time
    def load_from_influx(
        self,
        tagnames: str | list[str],
        start: str,
        end: str,
    ) -> influxdb.resultset.ResultSet:
        logger.debug(f"Loading data from influx... {start} ~ {end}")
        query = self.__create_query(tagnames, start, end)
        res = self.conn.query(query)
        df = self.__parse_influx_res(res)
        return df
