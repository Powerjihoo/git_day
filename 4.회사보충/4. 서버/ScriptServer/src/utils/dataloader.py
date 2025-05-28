# utils.dataloader.py

import os
from datetime import timedelta

import pandas as pd
import pytz

from config import settings
from utils import exceptions as ex_util
from utils.influx_connector import InfluxConnector
from utils.logger import logging_time

TIMEZONE = pytz.timezone("Asia/Seoul")


class NotEnoughDataError(Exception):
    def __init__(self, message: str = "Not enough data to training model"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{__class__.__name__}: {self.message}"


influx_connector = InfluxConnector(
    host=settings.databases["influx"].host,
    port=settings.databases["influx"].port,
    username=settings.databases["influx"].username,
    password=settings.databases["influx"].password,
    database=settings.databases["influx"].database,
)


@logging_time
def load_from_pkl(filename: str, path: str) -> pd.DataFrame:
    file_path = os.path.join(path, filename)
    return pd.read_pickle(file_path)


@logging_time
def concat_pkl_data(path: str) -> pd.DataFrame:
    try:
        filenames = os.listdir(path)
        data_total = pd.DataFrame()
        for filename in filenames:
            data = DataLoader.load_from_pkl(filename, path)
            data_total = pd.concat([data_total, data])
        if not len(data_total):
            raise NotEnoughDataError
        return data_total
    except FileNotFoundError as err:
        raise ex_util.TrainDataNotFoundError from err


def save_df2pkl(data: pd.DataFrame, save_path: str, postfix: str) -> None:
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    filename = f"data_{postfix}"
    filepath = os.path.join(save_path, filename)
    data.to_pickle(filepath)


def convert_df_resample(
    df: pd.DataFrame, sampling_interval_seconds: int = 5, offset_hour: int = 0
) -> pd.DataFrame:
    sampling_interval = f"{sampling_interval_seconds}s"
    tagnames = df.tagname.unique().tolist()

    df.drop_duplicates(subset=["time", "tagname"], inplace=True)
    df.time = pd.to_datetime(df.time, errors="raise", format="mixed")
    df.time = df.time.dt.tz_convert(tz=TIMEZONE)

    df_resampled = pd.DataFrame()
    for idx, tagname in enumerate(tagnames):
        _df = df[df.tagname == tagname][["time", "value", "quality"]]
        _df.set_index("time", inplace=True)
        _df.columns = [tagname, f"{tagname}_status_code"]
        _df_sampled = _df.resample(sampling_interval).ffill().bfill().dropna()
        if idx > 0:
            df_resampled = df_resampled.join(_df_sampled)
        else:
            df_resampled = _df_sampled
    return df_resampled.ffill().bfill().dropna()


class DataLoader:
    @staticmethod
    def load_from_influx_raw(
        tagnames: str | list[str],
        start: str,
        end: str,
        offset_hour: int = 0,
    ) -> pd.DataFrame:
        _start = start + timedelta(hours=-offset_hour)
        _end = end + timedelta(hours=-offset_hour)
        df = influx_connector.load_from_influx(tagnames, _start, _end)
        df.time = pd.to_datetime(df.time, errors="raise", format="mixed")
        df.time = df.time.dt.tz_convert(tz=TIMEZONE)
        return df

    @staticmethod
    def load_from_influx_resampled(
        tagnames: str | list[str],
        start: str,
        end: str,
        sampling_interval_seconds: int = 5,
        offset_hour: int = 0,
    ) -> pd.DataFrame:
        _start = start + timedelta(hours=-offset_hour)
        _end = end + timedelta(hours=-offset_hour)
        df_data = influx_connector.load_from_influx(tagnames, _start, _end)
        if df_data.empty:
            return pd.DataFrame()
        df_data_resampled = convert_df_resample(
            df=df_data,
            sampling_interval_seconds=sampling_interval_seconds,
            offset_hour=offset_hour,
        )

        for tagname in df_data_resampled.columns[::2]:
            if tagname not in tagnames:
                raise ValueError(f"Could not load tag data {tagname=}")

        return df_data_resampled
