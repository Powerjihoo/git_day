## inlux.py

import pandas as pd
from influxdb_client import InfluxDBClient

from utils.singleton import SingletonInstance


class InfluxConnector(metaclass=SingletonInstance):
    def __init__(self, url: str, token: str, org: str, bucket: str) -> None:
        self.client = InfluxDBClient(url=url, token=token, org=org)
        self.query_api = self.client.query_api()
        self.bucket = bucket


    # influxdb에서 데이터를 불러올 query로 작성
    def __create_query(self, tagname: int, start: str, end: str):
        query = f'''
            from(bucket: "{self.bucket}")
            |> range(start: {start}, stop: {end})
            |> filter(fn: (r) => r["tagName"] == "{tagname}")
            |> keep(columns: ["_time", "_value", "tagName"])
        '''
        return query

    # 데이터들을 불러온 후 DataFrame으로 변경
    def __parse_influx_res(self, tables) -> pd.DataFrame:
        records = []
        for table in tables:
            for record in table.records:
                records.append({
                    "_time": record.get_time(),
                    "_value": record.get_value(),
                    "tagName": record.values.get("tagName")
                })
        if records:
            return pd.DataFrame(records)
        else:
            return pd.DataFrame()

    # 불러온 데이터를 실시간으로 변경하고 60초 단위로 resampling
    def load_from_influx(self, tagname: int, start: str, end: str) -> pd.DataFrame:
        query = self.__create_query(tagname, start, end)
        tables = self.query_api.query(query)
        df = self.__parse_influx_res(tables)
        if not df.empty:
            df['_time'] = pd.to_datetime(df['_time'], utc=True)
            df['_time'] = df['_time'].dt.tz_convert('Asia/Seoul')
            df.set_index('_time', inplace=True)
            
            resampled_df = df.resample('60S').max().dropna() # bfill()
            return resampled_df
        else:
            return pd.DataFrame()