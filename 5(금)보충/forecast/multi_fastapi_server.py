import datetime
import json
import warnings

import numpy as np
import redis
import uvicorn
from fastapi import FastAPI, WebSocket
from statsmodels.tsa.arima.model import ARIMA

warnings.filterwarnings('ignore')

# Redis 연결
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# 예시 DB 데이터
DB = [
    {
        "tagname": "TagName1",
        "description": "TEMP"
    },
    {
        "tagname": "TagName2",
        "description": "PRESS"
    },
    {
        "tagname": "TagName3",
        "description": "FLOW"
    }
]

class ARIMA_model:
    def __init__(self, tagname: str, window_size: int = 5):
        self.tagname = tagname
        self.window_size = window_size
        self.timestamps = np.zeros(shape=self.window_size, dtype=np.uint64)
        self.values = np.full(shape=self.window_size, fill_value=np.nan, dtype=np.float32)
        self.forecast = np.full(shape=self.window_size, fill_value=np.nan, dtype=np.float32)
        self.model = None

    def __repr__(self):
        return f"[{self.__class__.__name__}] {self.tagname}"
    
    def update_data(self, tag_name, data, timestamp):
        if not self.timestamps.any() or timestamp - self.timestamps[-1] >= 5:
            self.values[:-1] = self.values[1:]
            self.timestamps[:-1] = self.timestamps[1:]
            self.values[-1] = data
            self.timestamps[-1] = timestamp
            print(f"updated_value : {tag_name} : {self.values[-1]:.2f}")

            if not np.isnan(self.values).any():
                self.train_predict()
                    
            # 최근 window_size개의 데이터를 Redis에 저장
            recent_values = [round(value, 2) for value in self.values.tolist()]
            redis_key = f"{self.tagname}:recent_values"
            redis_value = json.dumps(recent_values)
            redis_client.set(redis_key, redis_value)

            # time
            recent_timestamps = [datetime.datetime.fromtimestamp(ts).strftime('%y-%m-%d %H:%M:%S') if ts != 0 else 'nan' for ts in self.timestamps.tolist()]
            redis_key = f"{self.tagname}:recent_timestamps"
            redis_timestamp = json.dumps(recent_timestamps)
            redis_client.set(redis_key, redis_timestamp)

            # forecast
            forecast_values = [round(value, 2) for value in self.forecast.tolist()]
            redis_key = f"{self.tagname}:forecast"
            redis_forecast = json.dumps(forecast_values)
            redis_client.set(redis_key, redis_forecast)
        else:
            print(f"{tag_name} not updated(time <= 5)")
    
    def train_predict(self):
        self.model = ARIMA(self.values, order=(1, 1, 1)).fit()
        forecast = self.model.forecast(steps=self.window_size)
        self.forecast[:-1] = self.forecast[1:]
        self.forecast[-1] = forecast[0]

# ARIMA 모델 초기화
arima_models = {item["tagname"]: ARIMA_model(item["tagname"]) for item in DB}

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            for item in data:
                tag_name = item['tagname']
                value = item['values']
                timestamp_str = item['timestamp']
                timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").timestamp()
                
                if tag_name in arima_models:
                    arima_model = arima_models[tag_name]
                    arima_model.update_data(tag_name, value, timestamp)
                else:
                    print(f"알 수 없는 태그명으로 데이터 수신: {tag_name}")
            
    except Exception as e:
        print(f"WebSocket 연결 오류: {str(e)}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=1111)
