import datetime
import json
import warnings

import numpy as np
import psycopg2
import redis
import uvicorn
from fastapi import FastAPI, WebSocket
from statsmodels.tsa.arima.model import ARIMA

import config

server_info = config.SERVER_CONFIG
model_info = config.MODEL_CONFIG['test_model']

warnings.filterwarnings('ignore')
# DB연결해서 데이터 ID값 불러오기
def fetch_db_data():
    db = psycopg2.connect(host=server_info['postgre_host'], dbname=server_info['postgre_dbname'], user=server_info['postgre_user'], password=server_info['postgre_pw'], port=server_info['postgre_port'])
    with db.cursor() as cursor:
        cursor.execute("SELECT id FROM spot;")
        result = cursor.fetchall()
    db.close()
    return result
DB = fetch_db_data()
# DB= [(20,), (21,), (22,)]

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

# ARIMA 모델 초기화
arima_models = {item[0]: ARIMA_model(item[0]) for item in DB}
app = FastAPI()

@app.websocket("/forecast")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
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
            else:
                print(f"알 수 없는 태그명으로 데이터 수신: {tag_name}")
            
    except Exception as e:
        print(f"WebSocket 연결 오류: {str(e)}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run(app, host=server_info['Fastapi_host'], port=server_info['Fastapi_port'])
