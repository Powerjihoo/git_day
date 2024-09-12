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
        #초기 self값 설정
        self.tagname = tagname
        self.window_size = window_size
        self.step_size = step_size
        self.timestamps = np.zeros(shape=self.window_size, dtype=np.uint64)
        self.values = np.full(shape=self.window_size, fill_value=np.nan, dtype=np.float32)
        self.forecast = np.full(shape=self.step_size, fill_value=np.nan, dtype=np.float32)

        # InfluxDB 연결 설정
        self.influx_connector = InfluxConnector(
            url=server_info['Influx_host'],
            token=server_info['Influx_token'],
            org=server_info['Influx_org'],
            bucket=server_info['Influx_bucket']
        )

    def __repr__(self):
        return f"[{self.__class__.__name__}] {self.tagname}"

    def create_time(self):         #미래시간 생성
        forecast_timestamps = [(self.timestamps[-1] + 5 * i) for i in range(1, self.step_size + 1)]
        self.forecast_times = [datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') for ts in forecast_timestamps]

    def train_predict(self):       #ARIMA모델 예측
        self.model = ARIMA(self.values, order=(1, 2, 0)).fit()
        forecast = self.model.forecast(steps=self.step_size) # 예측
        self.forecast[:len(forecast)] = forecast  # 새 예측값 할당

    def update_statistics(self):   #예측값에 대한 통계값 생성
        forecast_values = np.array([value for value in self.forecast if not np.isnan(value)])
        self.statistics = {
            'max': round(float(forecast_values.max()), 2),
            'min': round(float(forecast_values.min()), 2),
            'mean': round(float(forecast_values.mean()), 2),
            'var': round(float(forecast_values.var()), 2),
            'std': round(float(forecast_values.std()), 2)
        }


    def update_data(self, values, tag_name, timestamp):
        # 처음으로 시작할때 만약 전체 데이터가 비어있다면 Influx에서 불러오기
        if np.isnan(self.values).all():
            print("Fetching historical data from InfluxDB...")
            df = self.influx_connector.load_from_influx(tagname=tag_name, start=model_info['start_date'], end="now()", desired_len=self.window_size)
            if not df.empty:
                self.timestamps[:len(df)] = (df['_time'].astype('int64') // 10**9).astype(np.uint64).values
                self.values[:len(df)] = df['_value'].astype(np.float32).values
                print("Historical data loaded.")
        
        # InfluxDB에서 데이터를 가져온 후에도 계속 새로운 값을 추가할 수 있도록 처리
        # 시간 차이 체크 (업데이트 되는 시간이 5초보다 짧을 경우 결과 반환 X)
        if timestamp - self.timestamps[-1] >= 5:
            # 아직 window_size만큼 데이터가 차지 않았을 경우 추가적으로 데이터를 쌓음
            nan_count = np.count_nonzero(np.isnan(self.values))
            if nan_count > 0:
                # 빈 공간이 있으면 그 위치에 새 값을 넣음
                self.values[-nan_count] = values
                self.timestamps[-nan_count] = np.uint64(timestamp)
            else:
                # 빈 공간이 없을 때는 기존 방식대로 가장 오래된 데이터를 제거하고 새 데이터를 추가
                self.values[:-1] = self.values[1:]
                self.values[-1] = values
                self.timestamps[:-1] = self.timestamps[1:]
                self.timestamps[-1] = np.uint64(timestamp)

            # 모든 값이 채워졌는지 확인(설정한 window_size만큼 채워져있을때부터 예측시작)
            filled_count = np.count_nonzero(~np.isnan(self.values))
            if filled_count >= self.window_size:
                self.train_predict()
                self.update_statistics()
                self.create_time()

                result = {
                    "tagname": tag_name,
                    "statistics": self.statistics,
                    "forecast": [
                        {"value": self.forecast.tolist()[i], "time": self.forecast_times[i]} for i in range(len(self.forecast.tolist()))]
                        }
            else:
                # 데이터가 채워지지 않은 경우 채워진 양을 출력하고 return으로 알려주기
                print(f"tag : {tag_name} filled_count = {filled_count} / {self.window_size}")
                return None
        else:
            # 시간 차이가 5초보다 짧을경우 return으로 알려주기
            print(f"tag : {tag_name} not updated(time <= 5)")
            return None
        
        return result
