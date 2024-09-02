##model.py

import datetime

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

    def __repr__(self):
        return f"[{self.__class__.__name__}] {self.tagname}"

    def update_data(self, data, tag_name, timestamp):
        # # 처음 데이터를 확인하고 만약 전체 데이터가 비어있다면 Influx에서 불러오기
        # if np.isnan(self.values).all():
        #     print("Fetching historical data from InfluxDB...")
        #     df = self.influx_connector.load_from_influx(tagnames=[self.tagname], start=model_info['start_date'], end="now()", desired_len=self.window_size)
        #     if not df.empty:
        #         self.timestamps = (df['_time'].astype('int64') // 10**9).astype(np.uint64).values
        #         self.values = df['_value'].astype(np.float32).values
        #         print("Historical data loaded.")
        #     else:
        #         print("No historical data available.")
        #         return  # 데이터가 없으면 함수 종료하기
            
        # 시간 차이 체크 (업데이트 되는 시간이 5초보다 짧을경우 결과 반환 X)
        if timestamp - self.timestamps[-1] >= 5:
            self.values[:-1] = self.values[1:]
            self.values[-1] = data
            self.timestamps[:-1] = self.timestamps[1:]
            self.timestamps[-1] = np.uint64(timestamp)
            print(f"Updated value: {tag_name} : {self.values[-1]:.2f}")

            # 모든 값이 채워졌는지 확인(설정한 window_size만큼 채워져있을때부터 예측시작)
            if not np.isnan(self.values).any():
                self.train_predict()
                self.update_statistics()

                # 미래 시간 생성(step_size만큼)
                forecast_timestamps = [(self.timestamps[-1] + 5 * i) for i in range(1, self.step_size + 1)]
                forecast_times = [datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') for ts in forecast_timestamps]

                result = {
                    "tagname": tag_name,
                    "statistics": self.statistics,
                    "forecast": [
                        {"value": self.forecast.tolist()[i], "time": forecast_times[i]}
                        for i in range(len(self.forecast.tolist()))
                    ]}
            else:
                # 데이터가 채워지지 않은 경우 return으로 알려주기
                print(f"{tag_name} data is not enough")
                result = {
                    "tagname": tag_name,
                    "nan_error":f"Data is not enought windsow_size = {self.values.shape[0]}, nan_count = {np.isnan(self.values).sum()}"}
        else:
            # 시간 차이가 5초보다 짧을경우 return으로 알려주기
            print(f"{tag_name} not updated(time <= 5)")
            result = {
                    "tagname": tag_name,
                    "time_error":'Time difference is less than 5 seconds'}

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
        forecast_values = np.array([value for value in self.forecast if not np.isnan(value)])
        forecast_values = np.array(forecast_values)
        self.statistics = {
            'max': round(float(forecast_values.max()), 2),
            'min': round(float(forecast_values.min()), 2),
            'mean': round(float(forecast_values.mean()), 2),
            'var': round(float(forecast_values.var()), 2),
            'std': round(float(forecast_values.std()), 2)
        }

