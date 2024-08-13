##inlux.py

import pandas as pd
from influxdb_client import InfluxDBClient

from utils.singleton import SingletonInstance


class InfluxConnector(metaclass=SingletonInstance):
    def __init__(self, url: str, token: str, org: str, bucket: str) -> None:
        self.client = InfluxDBClient(url=url, token=token, org=org)
        self.query_api = self.client.query_api()
        self.bucket = bucket

    def __create_query(self, tagnames: str | list[str], start: str, end: str):
        if isinstance(tagnames, str):
            tagnames = [tagnames]
        tag_conditions = " or ".join([f'r["tagName"] == "{tagname}"' for tagname in tagnames])
        query = f'''
            from(bucket: "{self.bucket}")
            |> range(start: {start}, stop: {end})
            |> filter(fn: (r) => {tag_conditions})
            |> keep(columns: ["_time", "_value", "tagName"])
        '''
        return query

    def __parse_influx_res(self, tables) -> pd.DataFrame:
        records = []
        for table in tables:
            for record in table.records:
                records.append({
                    "_time": record.get_time(),
                    "_value": record.get_value(),
                    "tagName": record.values.get("tagName")
                })
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame(records)
        return df

    def load_from_influx(self, tagnames: str | list[str], start: str, end: str, desired_len) -> pd.DataFrame:
        query = self.__create_query(tagnames, start, end)
        tables = self.query_api.query(query)
        df = self.__parse_influx_res(tables)
        if not df.empty:
            df['_time'] = pd.to_datetime(df['_time'], utc=True)
            df['_time'] = df['_time'].dt.tz_convert('Asia/Seoul')
            df.set_index('_time', inplace=True)
            resampled_df = df.resample('5S').bfill().dropna()
            resampled_df = resampled_df.iloc[:desired_len].reset_index()
            
            return resampled_df

        return pd.DataFrame()
