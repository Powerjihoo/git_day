import asyncio
import datetime
import json
import warnings

import numpy as np
import websockets
from statsmodels.tsa.arima.model import ARIMA

warnings.filterwarnings('ignore')

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
        self.timestamps = np.zeros(shape=[1, self.window_size], dtype=np.uint64)
        self.values = np.full(shape=[1, self.window_size], fill_value=np.nan, dtype=np.float32)
        self.model = None

    def __repr__(self):
        return f"[{self.__class__.__name__}] {self.tagname}"
    
    def update_data(self, data, timestamp):
        if timestamp - self.timestamps[-1][-1] >= 5:
            self.values[-1][0:-1] = self.values[-1][1:]
            self.timestamps[-1][0:-1] = self.timestamps[-1][1:]
            self.values[-1][-1] = data
            self.timestamps[-1][-1] = timestamp
            print("updated")
            if np.count_nonzero(~np.isnan(self.values)) == self.window_size:
                self.train_predict()
        else:
            print("not updated")
    
    def train_predict(self):
        # nan 값을 제외한 실제 데이터로 모델을 학습
        valid_indices = ~np.isnan(self.values[-1])
        data_to_train = self.values[-1][valid_indices]
        self.model = ARIMA(data_to_train, order=(1, 1, 1)).fit()
        print(f"Model trained for {self.tagname}")

    def predict(self):
        if self.model is not None:
            forecast = self.model.forecast(steps=1)
            return [round(value, 2) for value in forecast]
        else:
            return []

async def handle_client(websocket, path):
    print('server start')
    async for message in websocket:
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
        else:
            response = {
                'tagname': tag_name,
                'error': 'Model not found for this tagname. No model created.',
                'formatted_time': timestamp_str
            }
            print(f"Received data for unknown tagname: {tag_name}")
        
        await websocket.send(json.dumps(response))

# ARIMA 모델 초기화
arima_models = {item["tagname"]: ARIMA_model(item["tagname"]) for item in DB}

start_server = websockets.serve(handle_client, 'localhost', 1111)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()