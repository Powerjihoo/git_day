import datetime
import json

import numpy as np
import redis
from statsmodels.tsa.arima.model import ARIMA

import config

server_info = config.SERVER_CONFIG

# Redis 연결
redis_client = redis.Redis(host=server_info['redis_host'], port=server_info['redis_port'], db=server_info['redis_db'])

class ARIMA_model:
    def __init__(self, tagname: str, window_size: int = config.MODEL_CONFIG['test_model']['window_size'], step_size: int = config.MODEL_CONFIG['test_model']['step_size']):
        self.tagname = tagname
        self.window_size = window_size
        self.step_size = step_size
        self.timestamps = np.zeros(shape=self.window_size, dtype=np.uint64)
        self.values = np.full(shape=self.window_size, fill_value=np.nan, dtype=np.float32)
        self.forecast = np.full(shape=self.window_size, fill_value=np.nan, dtype=np.float32)
        self.model = None

    def __repr__(self):
        return f"[{self.__class__.__name__}] {self.tagname}"
    
    def update_data(self, data, timestamp):
        if not self.timestamps.any() or timestamp - self.timestamps[-1] >= 5: #timestamp가 비었거나 직전 timestamp와 5초이상 차이가 나면 업데이트
            self.values[:-1] = self.values[1:]
            self.timestamps[:-1] = self.timestamps[1:]
            self.values[-1] = data
            self.timestamps[-1] = timestamp
            print(f"updated_value : {self.values[-1]:.2f}")

            if not np.isnan(self.values).any():
                self.train_predict()
                    
            # 최근 window_size개의 time을 Redis에 저장
            recent_timestamps = [datetime.datetime.fromtimestamp(ts).strftime('%y-%m-%d %H:%M:%S') for ts in self.timestamps.tolist()]
            redis_key = f"{self.tagname}:recent_timestamps"
            redis_timestamp = json.dumps(recent_timestamps)
            redis_client.set(redis_key, redis_timestamp)

            # 최근 window_size개의 value를 Redis에 저장
            recent_values = [round(value, 2) for value in self.values.tolist()]
            redis_key = f"{self.tagname}:recent_values"
            redis_value = json.dumps(recent_values)
            redis_client.set(redis_key, redis_value)

            # window_size만큼의 데이터가 쌓이면 forecast시작 후 Redis에 저장
            forecast_values = [round(value, 2) for value in self.forecast.tolist()]
            redis_key = f"{self.tagname}:forecast"
            redis_forecast = json.dumps(forecast_values)
            redis_client.set(redis_key, redis_forecast)
        else:
            print("not updated(time <= 5)")
    
    def train_predict(self):
        self.model = ARIMA(self.values, order=(2, 1, 2)).fit()
        forecast = self.model.forecast(steps=self.step_size)
        self.forecast[:-5] = self.forecast[5:]
        self.forecast[-5:] = forecast[:]
