##model.py

import datetime
import numpy as np

from statsmodels.tsa.arima.model import ARIMA

import config

server_info = config.SERVER_CONFIG

        
    def update_data(self, data, tag_name, timestamp):
        # 직전 timestamp가 현재 timestamp와 5초 이상 차이가 나면 업데이트
        if timestamp - self.timestamps[-1] >= 5:  
            # 만약 값이 없다면 InfluxDB에서 과거 데이터 불러오기
            if np.isnan(self.values).all():  # 모든 값이 NaN인 경우
                print("Fetching historical data from InfluxDB...")
                df = self.influx_connector.load_from_influx(tagnames=[self.tagname], start=model_info['start_date'], end="now()")
                if not df.empty:
                    self.timestamps = (df['_time'].astype('int64') // 10**9).astype(np.uint64)
                    self.values = df['_value'].astype(np.float32).values
                    print("Historical data loaded.")
                else:
                    print("No historical data available.")
                    return
    
    def train_predict(self):
        self.model = ARIMA(self.values, order=(1, 2, 1)).fit()
        forecast = self.model.forecast(steps=self.step_size)
        
        # 예측 결과가 self.forecast의 크기보다 크다면 크기를 조정
        if len(forecast) > len(self.forecast):
            self.forecast = np.full(shape=len(forecast), fill_value=np.nan, dtype=np.float32)

        # 예측값 업데이트
        self.forecast[:] = np.nan  # 이전 예측값 초기화
        self.forecast[:len(forecast)] = forecast  # 새 예측값 할당