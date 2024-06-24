# server.py
import asyncio
import datetime
import json
import warnings

import numpy as np
import redis
import uvicorn
from fastapi import FastAPI, WebSocket
from statsmodels.tsa.arima.model import ARIMA

warnings.filterwarnings('ignore')

# Redis 클라이언트 초기화
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
        self.model = None
        self.initialize_redis()

    def initialize_redis(self):
        # Redis에서 기존 데이터 초기화
        redis_client.delete(f"{self.tagname}:recent_values")
        redis_client.delete(f"{self.tagname}:forecast")

        # 초기 NaN 값을 Redis에 저장
        redis_key = f"{self.tagname}:recent_values"
        redis_value = json.dumps(self.values.tolist())
        redis_client.set(redis_key, redis_value)
        redis_client.set(f"{self.tagname}:forecast", json.dumps("데이터가 부족해서 예측불가"))

    def __repr__(self):
        return f"[{self.__class__.__name__}] {self.tagname}"
    
    def update_data(self, data, timestamp):
        if not self.timestamps.any() or timestamp - self.timestamps[-1] >= 5:
            self.values[:-1] = self.values[1:]
            self.timestamps[:-1] = self.timestamps[1:]
            self.values[-1] = data
            self.timestamps[-1] = timestamp
            print("updated")

            if np.count_nonzero(~np.isnan(self.values)) >= self.window_size:
                self.train_predict()
                
            # 최근 window_size개의 데이터를 Redis에 저장
            recent_values = [round(value, 2) if not np.isnan(value) else 'nan' for value in self.values.tolist()]
            redis_key = f"{self.tagname}:recent_values"
            redis_value = json.dumps(recent_values)
            redis_client.set(redis_key, redis_value)
        else:
            print("not updated")
    
    def train_predict(self):
        data_to_train = self.values[~np.isnan(self.values)]
        if len(data_to_train) >= self.window_size:
            self.model = ARIMA(data_to_train, order=(1, 1, 1)).fit()
            print(f"Model trained for {self.tagname}")

            # 예측값을 Redis에 저장
            forecast = self.predict()
            if forecast:
                redis_key = f"{self.tagname}:forecast"
                redis_value = json.dumps(forecast)
                redis_client.set(redis_key, redis_value)
        else:
            print("Not enough data to train the model")

    def predict(self):
        if self.model is not None:
            forecast = self.model.forecast(steps=1)
            return [round(value, 2) for value in forecast]
        else:
            return []

# ARIMA 모델 초기화
arima_models = {item["tagname"]: ARIMA_model(item["tagname"]) for item in DB}

app = FastAPI()

async def send_forecast_periodically(websocket: WebSocket):
    while True:
        await asyncio.sleep(5)  # 5초마다 예측값을 전송
        for tagname, arima_model in arima_models.items():
            redis_key = f"{tagname}:forecast"
            forecast = redis_client.get(redis_key)
            if forecast:
                forecast = json.loads(forecast)
                recent_values = redis_client.get(f"{tagname}:recent_values")
                if recent_values:
                    recent_values = json.loads(recent_values)
                else:
                    recent_values = [float('nan')] * arima_model.window_size
                response = {
                    'tagname': tagname,
                    'recent_values': recent_values,
                    'forecast': forecast,
                    'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                await websocket.send_text(json.dumps(response))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print('WebSocket client connected')
    try:
        # 백그라운드 작업 시작
        asyncio.create_task(send_forecast_periodically(websocket))
        
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            tag_name = data['tagname']
            value = data['values']
            timestamp_str = data['timestamp']
            timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").timestamp()
            
            if tag_name in arima_models:
                arima_model = arima_models[tag_name]
                arima_model.update_data(value, timestamp)
                
                response = {
                    'tagname': tag_name,
                    'real_value': value,
                    'forecast': arima_model.predict(),
                    'formatted_time': timestamp_str
                }
                # Redis에 데이터 저장
                redis_key = f"{tag_name}:{timestamp_str}"
                redis_value = json.dumps(response)
                redis_client.set(redis_key, redis_value)
            else:
                response = {
                    'tagname': tag_name,
                    'error': '해당 태그명에 대한 모델을 찾을 수 없습니다. 모델이 생성되지 않았습니다.',
                    'formatted_time': timestamp_str
                }
                print(f"알 수 없는 태그명으로 데이터 수신: {tag_name}")
            
            await websocket.send_text(json.dumps(response))
    except Exception as e:
        print(f"WebSocket 연결 오류: {str(e)}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=1111)
