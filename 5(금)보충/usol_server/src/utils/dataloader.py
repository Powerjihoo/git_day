# utils.dataloader.py

import os
import shutil
from typing import Any, List, Union

import numpy as np
import pandas as pd
import requests
from pendulum import parse as pdl_parse

from api_client.apis.tagvalue import tagvalue_api
from utils import exceptions as ex_util
from utils.logger import logger, logging_time


class DataLoader:
    @staticmethod
    @logging_time
    def load_from_influx(
        tagnames: List[str],
        start: Any,
        end: Any,
        interval: int = 5,
        method: str = "archive",
    ) -> dict:
        logger.debug("Loading data from influxdb...")
        try:
            if method.casefold() == "archive":
                respond_data = tagvalue_api.get_historian_value_archive(
                    tagnames=tagnames, start=start, end=end,
                ).json()
            elif method.casefold() == "sampling":
                respond_data = tagvalue_api.get_historian_value_sampling(
                    tagnames=tagnames, start=start, end=end, interval=interval,
                ).json()
            else:
                raise ValueError("Invalid influx loading method")
            if not respond_data:
                raise ex_util.InfluxDataLoadError
            return respond_data
        except requests.exceptions.JSONDecodeError as err:
            raise ex_util.InfluxDataLoadError() from err
        except requests.exceptions.ConnectionError as err:
            raise ex_util.InfluxConnectionError() from err

    @staticmethod
    def convert_dict_to_df(
        data: Union[dict, List],
        tagnames: Union[List[str], str],
        has_timestamp: bool = True,
    ) -> pd.DataFrame:
        if not isinstance(tagnames, list):
            tagnames = [tagnames]

        try:
            data_df = pd.DataFrame()
            if isinstance(data, dict):
                if has_timestamp:
                    max_len = 0
                    for tagname, _data in data.items():
                        if len(_data) > max_len:
                            max_len = len(_data)
                            max_tagname = tagname
                    data_df["timestamp"] = pd.DataFrame.from_dict(data[max_tagname])[
                        "unixTimestamp"
                    ]
                for tagname in tagnames:
                    data_df[tagname] = pd.DataFrame.from_dict(data[tagname])["value"]
                    
            elif isinstance(data, List):
                if has_timestamp:
                    data_df["timestamp"] = pd.DataFrame(data[0]["valueList"])[
                        "unixTimestamp"
                    ]
                for idx, tagname in enumerate(tagnames):
                    data_df[tagname] = pd.DataFrame(data[idx]["valueList"])["value"]
                    
            else:
                raise ValueError("Invalid data type")

            data_df = data_df.fillna(method="ffill")
            return data_df
        
        except KeyError as err:
            raise ex_util.InfluxDataLoadError from err

    @staticmethod
    def convert_dict_to_df_resample(
        data: Union[dict, List], sampling_interval_seconds: int = 5, offset_hour:int=0
    ) -> pd.DataFrame:

        sampling_interval = f"{sampling_interval_seconds}S"
        df_dataset = pd.DataFrame
        try:
            if isinstance(data, dict):
                for tagname, tag_data in data.items():

                    values = tag_data

                    _df_data = pd.DataFrame(values, columns=["unixTimestamp", "value"])
                    _df_data.rename(columns={"value": tagname}, inplace=True)
                    _df_data["unixTimestamp"] = pd.to_datetime(
                        _df_data["unixTimestamp"], unit="ms", errors="raise"
                    ) + pd.offsets.Hour(offset_hour)
                    _df_data.set_index("unixTimestamp", inplace=True)
                    _df_data_sampled = _df_data.resample(sampling_interval).ffill()

                    try:
                        df_dataset = df_dataset.join(_df_data_sampled)
                    except TypeError:
                        df_dataset = _df_data_sampled
            elif isinstance(data, List):
                for tag_data in data:
                    tagname = tag_data["tagName"]
                    values = tag_data["valueList"]

                    _df_data = pd.DataFrame(values, columns=["unixTimestamp", "value"])
                    _df_data.rename(columns={"value": tagname}, inplace=True)
                    _df_data["unixTimestamp"] = pd.to_datetime(
                        _df_data["unixTimestamp"], unit="ms", errors="raise"
                    ) + pd.offsets.Hour(offset_hour)
                    _df_data.set_index("unixTimestamp", inplace=True)
                    _df_data_sampled = _df_data.resample(sampling_interval).ffill()

                    try:
                        df_dataset = df_dataset.join(_df_data_sampled)
                    except TypeError:
                        df_dataset = _df_data_sampled
            return df_dataset

        except KeyError as err:
            raise ex_util.InfluxDataLoadError from err



    @staticmethod
    @logging_time
    def load_from_csv(tagname: str, path: str = "D:data/KHNP") -> np.array:
        filename = f"{tagname}.csv"
        file_path = os.path.join(path, filename)
        data_org = pd.read_csv(file_path)
        return np.array(data_org)

    @staticmethod
    @logging_time
    def load_from_pkl(filename: str, path: str) -> pd.DataFrame:
        file_path = os.path.join(path, filename)
        return pd.read_pickle(file_path)

