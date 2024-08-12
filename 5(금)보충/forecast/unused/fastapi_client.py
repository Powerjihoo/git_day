import asyncio
import datetime
import json
import random

import websockets


async def send_data():
    url = 'ws://localhost:1111/forecast'
    async with websockets.connect(url) as websocket:
        while True:
            random_value = random.uniform(39, 41)
            
            data = {
                'tagname': 1,  # TagName1, TagName2, TagName3 중 하나를 선택
                'values': random_value,  # 랜덤 데이터 생성
                'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            await websocket.send(json.dumps(data))
            print(f"Sent({data['tagname']}) : {data['values']}")
            await asyncio.sleep(random.uniform(3, 7))

asyncio.get_event_loop().run_until_complete(send_data())
