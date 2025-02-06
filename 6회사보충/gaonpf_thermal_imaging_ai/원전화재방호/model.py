## model.py
import datetime
import warnings

import numpy as np
import pytz
from statsmodels.tsa.arima.model import ARIMA

import config
from influx import InfluxConnector
from utils.logger import logger

warnings.filterwarnings('ignore')

server_info = config.SERVER_CONFIG
model_info = config.MODEL_CONFIG["test_model"]

class ARIMA_model:
    def __init__(
        self,
        tagname: int,                                       # 태그 이름 (ID)
        window_size: int = model_info["window_size"],       # model에 넣을 데이터 사이즈
        step_size: int = model_info["step_size"],           # 예측할 데이터 사이즈
        duration_size: int = model_info["duration_size"],   # 예측 기간 크기(Trend에 사용)
    ):
        # forecast 초기값 설정(list들은 nan값으로 채워넣기)
        self.tagname = tagname
        self.window_size = window_size
        self.step_size = step_size
        self.forecast = np.full(shape=self.step_size, fill_value=np.nan, dtype=np.float32)
        self.timestamps = np.zeros(shape=self.window_size, dtype=np.uint64)
        self.values = np.full(shape=self.window_size, fill_value=np.nan, dtype=np.float32)

        # duration 초기값 설정
        self.duration_size = duration_size
        self.duration_trend = np.full(shape=self.duration_size, fill_value=np.nan, dtype=np.float32)

        # InfluxDB 연결 설정
        self.influx_connector = InfluxConnector(
            url=server_info["Influx_host"],
            token=server_info["Influx_token"],
            org=server_info["Influx_org"],
            bucket=server_info["Influx_bucket"],
        )

    def __repr__(self) -> str:
        return f"[{self.__class__.__name__}] {self.tagname}"

    def create_time(self, end_timestamp: int, step_size: int):
        """
        미래에 대한 예측시간 생성
        
        Parameters
        ----------
        - end_timestamp : 마지막 데이터의 타임스탬프(이 시점부터 미래예측시작)
        - step_size : 예측 단계 크기
        """
        forecast_timestamps = [(end_timestamp + 60 * i) for i in range(1, step_size + 1)]
        self.forecast_times = [
            datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
            for ts in forecast_timestamps
        ]

    def update_statistics(self, forecast_array: np.ndarray):
        """
        예측값에 대한 통계값 계산
        """
        forecast_values = np.array(
            [value for value in forecast_array if not np.isnan(value)]
        )
        self.statistics = {
            "max": round(float(forecast_values.max()), 2),
            "min": round(float(forecast_values.min()), 2),
            "mean": round(float(forecast_values.mean()), 2),
            "var": round(float(forecast_values.var()), 2),
            "std": round(float(forecast_values.std()), 2),
        }

    def train_predict(self, values: np.ndarray, forecast_array: np.ndarray, step_size: int):
        """
        ARIMA 모델사용
    
        Parameters
        ----------
        values : 학습할 데이터
        forecast_array : 예측 결과를 저장할 배열
        step_size : 예측 단계 크기
        """
        try:
            self.model = ARIMA(values, order=(12, 2, 6)).fit()
            forecast = self.model.forecast(steps=step_size)  # 예측
            forecast_array[: len(forecast)] = forecast       # 예측 결과를 전달된 배열에 할당
        except Exception as e:
            logger.error(f"Error during ARIMA model training and forecasting: {e}")

    def convert_to_utc(self, local_time_str: str) -> str:
        """
        로컬 시간을 UTC 시간으로 변환
        """
        kst = pytz.timezone('Asia/Seoul')
        local_time = datetime.datetime.strptime(local_time_str, "%Y-%m-%d %H:%M:%S")
        local_time = kst.localize(local_time)
        utc_time = local_time.astimezone(pytz.UTC)
        return utc_time.isoformat()

    ########## forecast
    def update_data(self, values: float, tag_name: int, timestamp: int):
        """
        새 데이터를 업데이트하면서 예측을 수행합니다.
        
        Parameters
        ----------
        tag_name :  태그 이름 (ID).
        values :    새 데이터 값.
        timestamp : 새 데이터의 타임스탬프.

        Returns
        -------
        예측이 성공했을 때: {'tagname': 1, 'statistics': {...}, 'forecast': [{'value': ..., 'time': ...}, ...]}.
        예측이 실패했을 때: None.
        """
        # 데이터가 비어있을때(처음으로 시작했을때) InfluxDB에서 데이터 조회
        if np.isnan(self.values).all():
            df = self.influx_connector.load_from_influx(
                tagname=tag_name, start=model_info["start_date"], end="now()"
            ).iloc[: self.window_size].reset_index()
            
            # InfluxDB에서 불러온 데이터가 비어있다면 불러오지 못했다고 알림
            if df.empty:
                logger.info(f"Can't load data from InfluxDB for tagname = {tag_name}")
            else: 
                actual_size = len(df)
                # InfluxDB에서 불러온 데이터가 있다면 부족한 데이터 앞에 NaN으로 패딩하고 가져온 데이터를 뒤에 배치
                if actual_size < self.window_size:
                    padding_size = self.window_size - actual_size
                    padded_values = np.full(padding_size, np.nan, dtype=np.float32)
                    padded_timestamps = np.full(padding_size, np.nan, dtype=np.uint64)

                    self.values = np.concatenate(
                        [padded_values, df["_value"].astype(np.float32).values])
                    self.timestamps = np.concatenate(
                        [padded_timestamps, (df["_time"].astype("int64") // 10**9).astype(np.uint64).values])
                else:
                    # 데이터가 충분한 경우 그대로 사용
                    self.values = df["_value"].astype(np.float32).values
                    self.timestamps = (df["_time"].astype("int64") // 10**9).astype(np.uint64).values

                logger.info(f"Loaded initial data from InfluxDB for tagname = {tag_name}")

        # influxDB에서 데이터가 없었다면 새로운 값을 맨 마지막부터 추가하고 계속 업데이트하기
        nan_count = np.sum(np.isnan(self.values))
        if nan_count <= 0:
            self.values[-nan_count] = values
            self.timestamps[-nan_count] = np.uint64(timestamp)
        else:
            self.values[:-1] = self.values[1:]
            self.values[-1] = values
            self.timestamps[:-1] = self.timestamps[1:]
            self.timestamps[-1] = np.uint64(timestamp)

        # window_size가 다 채워지면 예측시작
        filled_count = np.sum(~np.isnan(self.values))
        if filled_count >= self.window_size:
            self.train_predict(self.values, self.forecast, self.step_size)
            self.update_statistics(self.forecast)
            self.create_time(self.timestamps[-1], self.step_size)

            result = {
                "tagname": tag_name,
                "statistics": self.statistics,
                "forecast": [
                    {
                        "v": round(self.forecast.tolist()[i],1),
                        "t": self.forecast_times[i],
                    }
                    for i in range(self.step_size)
                ],}
            logger.info(f"Prediction successful for tagname = {tag_name}")
        else:
            logger.warning(f"tagname = {tag_name} - Filled count is {filled_count}. Enough data count is {self.window_size}.")
            return None
        
        return result

    ########## trend
    def duration_forecast(self, tag_name: int, start: str, end: str):
        """
        특정기간에 대해 예측을 수행합니다.
        
        Parameters
        ----------
        tag_name (int): 태그 이름 (ID)
        start (str): 시작 시간
        end (str): 종료 시간
        
        Returns
        ----------
        예측이 성공했을 때: {'tagname': 1, 'statistics': {...}, 'forecast': [{'value': ..., 'time': ...}, ...]}.
        예측이 실패했을 때: None.
        """
        start_utc, end_utc = self.convert_to_utc(start), self.convert_to_utc(end)
        df = self.influx_connector.load_from_influx(tagname=tag_name, start=start_utc, end=end_utc).reset_index()
        if not df.empty:
            self.duration_values = df["_value"].astype(np.float32).values
            self.train_predict(self.duration_values, self.duration_trend, self.duration_size)
            self.update_statistics(self.duration_trend)
            end_timestamp = int(datetime.datetime.strptime(end, "%Y-%m-%d %H:%M:%S").timestamp())
            self.create_time(end_timestamp, self.duration_size)

            result = {
                "tagname": tag_name,
                "statistics": self.statistics,
                "forecast": [
                    {
                        "v": round(self.duration_trend.tolist()[i],1),
                        "t": self.forecast_times[i],
                    }
                    for i in range(self.duration_size)
                ],
            }
        else:
            return None

        return result