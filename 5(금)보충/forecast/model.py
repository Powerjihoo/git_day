##model.py

import datetime
import json

import numpy as np
from statsmodels.tsa.arima.model import ARIMA

import config
from influx import InfluxConnector

server_info = config.SERVER_CONFIG
model_info = config.MODEL_CONFIG['test_model']

class ARIMA_model:
    def __init__(self, tagname: str, window_size: int = model_info['window_size'], step_size: int = model_info['step_size']):
        self.tagname = tagname
        self.window_size = window_size
        self.step_size = step_size
        self.timestamps = np.zeros(shape=self.window_size, dtype=np.uint64)
        self.values = np.full(shape=self.window_size, fill_value=np.nan, dtype=np.float32)
        self.forecast = np.full(shape=self.window_size, fill_value=np.nan, dtype=np.float32)
        self.model = None

        # InfluxDB 연결 설정
        self.influx_connector = InfluxConnector(
            url=server_info['Influx_host'],
            token=server_info['Influx_token'],
            org=server_info['Influx_org'],
            bucket=server_info['Influx_bucket']
        )

    def __repr__(self):
        return f"[{self.__class__.__name__}] {self.tagname}"

    def update_data(self, data, tag_name, timestamp):
        # 시간 차이 체크
        if timestamp - self.timestamps[-1] >= 5:
            # 데이터 갱신
            self.values[:-1] = self.values[1:]
            self.values[-1] = data

            self.timestamps[:-1] = self.timestamps[1:]
            self.timestamps[-1] = np.uint64(timestamp)

            print(f"Updated value: {tag_name} : {self.values[-1]:.2f}")

            # 모든 값이 채워졌는지 확인
            if not np.isnan(self.values).any():
                # 데이터가 모두 채워졌을 때 예측 모델 훈련
                self.train_predict()
                self.update_statistics()

                # 미래 시간 생성
                last_timestamp = self.timestamps[-1]
                forecast_timestamps = [(last_timestamp + 5 * i) for i in range(1, self.step_size + 1)]
                forecast_times = [datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') for ts in forecast_timestamps]

                result = {
                    "tagname": tag_name,
                    "statistics": self.statistics,
                    "forecast": [
                        {"value": self.forecast.tolist()[i], "time": forecast_times[i]}
                        for i in range(len(self.forecast.tolist()))
                    ]
                }
            else:
                # 데이터가 채워지지 않은 경우
                result = {
                    "tagname": tag_name,
                    "Not_predict":'Zero None'}
        else:
            # 시간 차이가 5초 미만일 경우
            result = {
                    "tagname": tag_name,
                    "Not_predict":'Time None'}

        return result

    def train_predict(self):
        self.model = ARIMA(self.values, order=(1, 2, 0)).fit()
        forecast = self.model.forecast(steps=self.step_size)

        # 예측 결과가 self.forecast의 크기보다 크다면 크기를 조정
        if len(forecast) > len(self.forecast):
            self.forecast = np.full(shape=len(forecast), fill_value=np.nan, dtype=np.float32)

        # 예측값 업데이트
        self.forecast[:] = np.nan  # 이전 예측값 초기화
        self.forecast[:len(forecast)] = forecast  # 새 예측값 할당

    def update_statistics(self):
        forecast_values = [value for value in self.forecast if not np.isnan(value)]
        if len(forecast_values) > 0:
            forecast_values = np.array(forecast_values)
            self.statistics = {
                'max': round(float(forecast_values.max()), 2),
                'min': round(float(forecast_values.min()), 2),
                'mean': round(float(forecast_values.mean()), 2),
                'var': round(float(forecast_values.var()), 2),
                'std': round(float(forecast_values.std()), 2)
            }
        else:
            self.statistics = {
                'max': np.nan,
                'min': np.nan,
                'mean': np.nan,
                'var': np.nan,
                'std': np.nan
            }
