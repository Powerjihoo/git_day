import datetime
import json

from fastapi import FastAPI, WebSocket

import config
from model import ARIMA_model

server_info = config.SERVER_CONFIG

# DB에서 ID를 불러오는 함수
def fetch_db_data():
    import psycopg2
    db = psycopg2.connect(host=server_info['postgre_host'], dbname=server_info['postgre_dbname'], user=server_info['postgre_user'], password=server_info['postgre_pw'], port=server_info['postgre_port'])
    with db.cursor() as cursor:
        cursor.execute("SELECT id FROM spot;")
        result = cursor.fetchall()
    db.close()
    return result

# ARIMA 모델 초기화
DB = fetch_db_data()
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
