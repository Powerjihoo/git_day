## app.py
import asyncio
import datetime
import json

import config
import psycopg2
from fastapi import APIRouter, FastAPI, WebSocket
from model import ARIMA_model
from pydantic import BaseModel
from utils.logger import logger

server_info = config.SERVER_CONFIG

# PostgreDB에서 객체정보 불러오기(tagname)
def fetch_db_data():
    db = psycopg2.connect(host=server_info['postgre_host'], dbname=server_info['postgre_dbname'], user=server_info['postgre_user'], password=server_info['postgre_pw'], port=server_info['postgre_port'])
    with db.cursor() as cursor:
        cursor.execute("SELECT id FROM spot;")
        result = cursor.fetchall()
    db.close()
    return result


# DB = [(1,), (2,), (3,),(4,), (5,), (6,),(7,), (8,), (9,),(10,), (11,), (12,),]  # Postgre연결되기전 임시 객체정보
DB = fetch_db_data()
arima_models = {item[0]: ARIMA_model(item[0]) for item in DB}

app = FastAPI()
router = APIRouter()

#forecast(실시간 예측)
@router.websocket("/forecast")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            results = []

            for item in data:
                tag_name: int = item['tagname']
                values = item['values']
                timestamp_str = item['timestamp']
                timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").timestamp()
                logger.info(f"Received: tagname = {tag_name}, value={values}, timestamp={timestamp_str}")

                if tag_name in arima_models:
                    arima_model = arima_models[tag_name]
                    result = arima_model.update_data(values, tag_name, timestamp)
                    results.append(result)
                else:
                    logger.warning(f"Unknown tagname received: {tag_name}, refreshing DB...")

                    # DB 조회를 비동기적으로 실행
                    loop = asyncio.get_running_loop()
                    new_db = await loop.run_in_executor(None, fetch_db_data)

                    if any(tag_name == row[0] for row in new_db):
                        logger.info(f"Tagname {tag_name} found in updated DB. Initializing ARIMA model...")
                        arima_models[tag_name] = ARIMA_model(tag_name)

                        # 새로 추가된 태그에 대해 예측 실행
                        arima_model = arima_models[tag_name]
                        result = arima_model.update_data(values, tag_name, timestamp)
                        results.append(result)
                    else:
                        logger.warning(f"Tagname {tag_name} is still missing after DB refresh.")

            
            await websocket.send_text(json.dumps(results))

    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
    finally:
        await websocket.close()

class DurationRequest(BaseModel):
    tagname: int
    start: str
    end: str


#trend(특정기간 예측)
@app.post("/duration")
async def duration_forecast(request: DurationRequest):
    tag_name = request.tagname
    start = request.start
    end = request.end
    
    if tag_name in arima_models:
        arima_model = arima_models[tag_name]
        result = arima_model.duration_forecast(tag_name=tag_name, start=start, end=end)
        if result:
            return result
        else:
            logger.warning(f"No data available for the given range: {start} to {end}")
            return {"error": f"No data available for the given range: {start} to {end}"}
    else:
        logger.warning(f"Unknown tagname received: {tag_name}, refreshing DB...")

        # DB 조회를 비동기적으로 실행
        loop = asyncio.get_running_loop()
        new_db = await loop.run_in_executor(None, fetch_db_data)

        if any(tag_name == row[0] for row in new_db):
            logger.info(f"Tagname {tag_name} found in updated DB. Initializing ARIMA model...")
            arima_models[tag_name] = ARIMA_model(tag_name)

            # 새로 추가된 태그에 대해 예측 실행
            arima_model = arima_models[tag_name]
            result = arima_model.duration_forecast(tag_name=tag_name, start=start, end=end)
            if result:
                return result
            else:
                logger.warning(f"No data available for the given range: {start} to {end}")
                return {"error": f"No data available for the given range: {start} to {end}"}
        else:
            logger.warning(f"Tagname {tag_name} is still missing after DB refresh.")

app.include_router(router)