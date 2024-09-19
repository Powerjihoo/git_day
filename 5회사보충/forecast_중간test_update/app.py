import datetime
import json
import zlib  # 또는 gzip

from fastapi import APIRouter, FastAPI, WebSocket
from pydantic import BaseModel

import config
from model import ARIMA_model
from utils.logger import logger

server_info = config.SERVER_CONFIG

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
                tag_name: int = item['tagname']
                values = item['values']
                timestamp_str = item['timestamp']
                timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").timestamp()
                logger.info(f"Received: tagname={tag_name}, value={values}, timestamp={timestamp_str}")

                if tag_name in arima_models:
                    arima_model = arima_models[tag_name]
                    result = arima_model.update_data(values, tag_name, timestamp)
                    results.append(result)
                else:
                    logger.warning(f"Unknown tagname received: {tag_name}")

            # JSON 인코딩 및 압축
            compressed_results = zlib.compress(json.dumps(results).encode())
            await websocket.send_bytes(compressed_results)

    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
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
    
    # Check if the ARIMA model for the requested tagname is already created
    if tag_name in arima_models:
        arima_model = arima_models[tag_name]

        # Call the duration_forecast method to get prediction results
        result = arima_model.duration_forecast(tag_name=tag_name, start=start, end=end)
        if result:
            return result
        else:
            logger.warning(f"No data available for the given range: {start} to {end}")
            return {"error": f"No data available for the given range: {start} to {end}"}
    else:
        logger.warning(f"Unknown tagname received: {tag_name}")

app.include_router(router)
