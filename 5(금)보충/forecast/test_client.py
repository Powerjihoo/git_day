import asyncio
import datetime
import json
import random
import websockets


async def send_data():
    uri = 'ws://localhost:1111/ws'  # FastAPI 서버의 WebSocket 엔드포인트 주소로 변경
    async with websockets.connect(uri) as websocket:
        while True:
            data = {
                'tagname': 'TagName3',  # TagName1, TagName2, TagName3 중 하나를 선택
                'values': round(random.random(), 2),  # 랜덤 데이터 생성
                'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'quality': 'good'
            }
            await websocket.send(json.dumps(data))
            print(f"Sent: {data['values']}")
            await asyncio.sleep(random.uniform(1, 10))

            response = await websocket.recv()
            print(f"Received: {response}")

# asyncio.get_event_loop().run_until_complete(send_data())  # 권장되지 않음
asyncio.run(send_data())  # 권장 방법
