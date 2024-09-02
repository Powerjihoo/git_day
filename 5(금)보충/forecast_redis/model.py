##model.py

import datetime
import json

import numpy as np
import redis
from statsmodels.tsa.arima.model import ARIMA

import config
from influx import InfluxConnector

server_info = config.SERVER_CONFIG
model_info = config.MODEL_CONFIG['test_model']

# Redis 연결
redis_client = redis.Redis(host=server_info['redis_host'], port=server_info['redis_port'], db=server_info['redis_db'])

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
        # 직전 timestamp가 현재 timestamp와 5초 이상 차이가 나면 업데이트
        if timestamp - self.timestamps[-1] >= 5:  
            # # 만약 값이 없다면 InfluxDB에서 과거 데이터 불러오기
            # if np.isnan(self.values).all():  # 모든 값이 NaN인 경우
            #     print("Fetching historical data from InfluxDB...")
            #     df = self.influx_connector.load_from_influx(tagnames=[self.tagname], start=model_info['start_date'], end="now()", desired_len=self.window_size)
            #     if not df.empty:
            #         self.timestamps = (df['_time'].astype('int64') // 10**9).astype(np.uint64).values
            #         self.values = df['_value'].astype(np.float32).values
            #         print("Historical data loaded.")
            #     else:
            #         print("No historical data available.")
            #         return
                
            # 아래 부분은 timestamp가 5초 이상 차이가 날 때의 업데이트 로직입니다.
            self.values[:-1] = self.values[1:]
            self.values[-1] = data

            self.timestamps[:-1] = self.timestamps[1:]
            self.timestamps[-1] = np.uint64(timestamp)
            
            print(f"updated_value : {tag_name} : {self.values[-1]:.2f}")
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
            
            redis_key = f"{self.tagname}:alarm"
            if forecast_values[-1] > forecast_values[0]:
                redis_alarm = 'upper'
            elif forecast_values[-1] < forecast_values[0]:
                redis_alarm = 'lower'
            else:
                redis_alarm = 'same'
            redis_client.set(redis_key, redis_alarm)

            # 통계값 계산
            forecast_values = np.array(forecast_values)  # NumPy 배열로 변환

            statistics = {
                'max': forecast_values.max(),
                'min': forecast_values.min(),
                'mean': forecast_values.mean(),
                'var': forecast_values.var(),
                'std': forecast_values.std()
            }
            redis_key = f"{self.tagname}:statistics"
            redis_client.set(redis_key, json.dumps(statistics))  # JSON 문자열로 저장
        else:
            print(f"{tag_name} not updated(time <= 5)")

    
    def train_predict(self):
        self.model = ARIMA(self.values, order=(1, 2, 1)).fit()
        forecast = self.model.forecast(steps=self.step_size)
        
        # 예측 결과가 self.forecast의 크기보다 크다면 크기를 조정
        if len(forecast) > len(self.forecast):
            self.forecast = np.full(shape=len(forecast), fill_value=np.nan, dtype=np.float32)

        # 예측값 업데이트
        self.forecast[:] = np.nan  # 이전 예측값 초기화
        self.forecast[:len(forecast)] = forecast  # 새 예측값 할당