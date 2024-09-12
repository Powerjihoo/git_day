##app.py

import datetime
import json

from fastapi import APIRouter, FastAPI, WebSocket
from pydantic import BaseModel

# import psycopg2
import config
from model import ARIMA_model

server_info = config.SERVER_CONFIG

# def fetch_db_data():
#     db = psycopg2.connect(host=server_info['postgre_host'], dbname=server_info['postgre_dbname'], user=server_info['postgre_user'], password=server_info['postgre_pw'], port=server_info['postgre_port'])
#     with db.cursor() as cursor:
#         cursor.execute("SELECT id FROM spot;")
#         result = cursor.fetchall()
#     db.close()
#     return result
# DB = fetch_db_data()

DB = [(1,), (2,)]  # Postgre연결후 위의 코드로 실행
arima_models = {item[0]: ARIMA_model(item[0]) for item in DB}

app = FastAPI()
router = APIRouter()

@router.websocket("/forecast")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            results = []

            for item in data:
                tag_name = item['tagname']
                values = item['values']
                timestamp_str = item['timestamp']
                timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").timestamp()
                print(f"Received: tagname={tag_name}, value={values}, timestamp={timestamp_str}")

                if tag_name in arima_models:
                    arima_model = arima_models[tag_name]
                    result = arima_model.update_data(values, tag_name, timestamp)
                    results.append(result)
                else:
                    print(f"알 수 없는 태그명으로 데이터 수신: {tag_name}")
            
            await websocket.send_text(json.dumps(results))

    except Exception as e:
        print(f"WebSocket 연결 오류: {str(e)}")
    finally:
        await websocket.close()




class DurationRequest(BaseModel):
    tagname: int
    start: str
    end: str

@app.post("/duration")
async def duration_forecast(request: DurationRequest):
    tag_name = request.tagname
    start = request.start
    end = request.end
    
    # 요청된 tagname에 해당하는 ARIMA 모델이 이미 생성되어 있는지 확인
    if tag_name in arima_models:
        arima_model = arima_models[tag_name]

        # duration_forecast 메서드 호출하여 예측 결과 얻기
        result = arima_model.duration_forecast(tag_name=tag_name, start=start, end=end)
        if result:
            return result
        else:
            return {"error": f"No data available for the given range: {start} to {end}"}
    else:
        print(f"알 수 없는 태그명으로 데이터 수신: {tag_name}")

app.include_router(router)