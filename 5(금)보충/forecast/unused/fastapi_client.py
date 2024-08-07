# client.py
import asyncio
import datetime
import json
import random

import websockets

value = [1,2,3,4,5,4,3,2,1]
index = 0
async def send_data():
    global index
    url = 'ws://localhost:1111/forecast'
    async with websockets.connect(url) as websocket:
        while True:
            data = {
                'tagname': 1,  # TagName1, TagName2, TagName3 중 하나를 선택
                'values': value[index],  # 랜덤 데이터 생성
                'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # ,'quality': 'good'    #####db에서 정상데이터만 불러서 쏴줄 예정이라 quailty는 없을예정
            }
            await websocket.send(json.dumps(data))
            print(f"Sent({data['tagname']}) : {data['values']}")
            index = (index + 1) % len(value)
            await asyncio.sleep(random.uniform(3,7))

asyncio.get_event_loop().run_until_complete(send_data())