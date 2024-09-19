import datetime

import numpy as np
import pytz
from statsmodels.tsa.arima.model import ARIMA

import config
from influx import InfluxConnector
from utils.logger import logger  # 로거 추가

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
        # forecast 초기값 설정
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
        
        Parameters:
        - end_timestamp : 마지막 데이터의 타임스탬프(이 시점부터 미래예측시작)
        - step_size : 예측 단계 크기
        """
        forecast_timestamps = [(end_timestamp + 5 * i) for i in range(1, step_size + 1)]
        self.forecast_times = [
            datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
            for ts in forecast_timestamps
        ]

    def update_statistics(self, forecast_array: np.ndarray):
        """
        예측값에 대한 통계값 계산
        
        Parameters
        - forecast_array : 예측된 값의 배열
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
            self.model = ARIMA(values, order=(1, 2, 0)).fit()
            forecast = self.model.forecast(steps=step_size)  # 예측
            forecast_array[: len(forecast)] = forecast  # 예측 결과를 전달된 배열에 할당
            logger.info(f"Model training and forecasting successful for tagname={self.tagname}")
        except Exception as e:
            logger.error(f"Error during ARIMA model training and forecasting: {e}")

    def convert_to_utc(self, local_time_str: str) -> str:
        """
        로컬 시간을 UTC 시간으로 변환
        
        Parameters
        ----------
        local_time_str (str): 변환할 로컬 시간 문자열
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
        if np.isnan(self.values).all():
            df = self.influx_connector.load_from_influx(tagname=tag_name, start=model_info["start_date"], end="now()").iloc[: self.window_size].reset_index()
            if not df.empty:
                self.timestamps = (
                    (df["_time"].astype("int64") // 10**9).astype(np.uint64).values
                )
                self.values = df["_value"].astype(np.float32).values
                logger.info(f"Loaded initial data from InfluxDB for tagname={tag_name}")

        if timestamp - self.timestamps[-1] >= 5:
            nan_count = np.count_nonzero(np.isnan(self.values))
            if nan_count > 0:
                self.values[-nan_count] = values
                self.timestamps[-nan_count] = np.uint64(timestamp)
                logger.debug(f"Inserted new value {values} at position {nan_count} for tagname={tag_name}")
            else:
                self.values[:-1] = self.values[1:]
                self.values[-1] = values
                self.timestamps[:-1] = self.timestamps[1:]
                self.timestamps[-1] = np.uint64(timestamp)
                logger.debug(f"Updated oldest data and inserted new value {values} for tagname={tag_name}")

            filled_count = np.count_nonzero(~np.isnan(self.values))
            if filled_count >= self.window_size:
                self.train_predict(self.values, self.forecast, self.step_size)
                self.update_statistics(self.forecast)
                self.create_time(self.timestamps[-1], self.step_size)

                result = {
                    "tagname": tag_name,
                    "statistics": self.statistics,
                    "forecast": [
                        {
                            "value": self.forecast.tolist()[i],
                            "time": self.forecast_times[i],
                        }
                        for i in range(self.step_size)
                    ],
                }
                logger.info(f"Prediction successful for tagname={tag_name}")
            else:
                logger.warning(f"tagname={tag_name} - Filled count is {filled_count}. Not enough data to forecast.")
                return None
        else:
            logger.warning(f"tagname={tag_name} - Update ignored (time difference <= 5 seconds)")
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
        예측이 성공했을때 : {tagname:1, statistic:{--}, forecast:{[values,],[time,]} }
        예측이 실패했을때 : None
        """
        start_utc = self.convert_to_utc(start)
        end_utc = self.convert_to_utc(end)
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
                        "value": self.duration_trend.tolist()[i],
                        "time": self.forecast_times[i],
                    }
                    for i in range(self.duration_size)
                ],
            }
        else:
            print(f"tag: {tag_name} -  {start} ~ {end} 해당 구간에는 데이터가 없음")
            return None

        return result
