import asyncio
import datetime
import json
import random
import websockets

async def send_data():
    uri = 'ws://localhost:1111'
    async with websockets.connect(uri) as websocket:
        while True:
            data = [
                {
                    'tagname': 'TagName1',
                    'values': round(random.random(), 2),
                    'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'quality': 'good'
                },
                {
                    'tagname': 'TagName2',
                    'values': round(random.random(), 2),
                    'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'quality': 'good'
                },
                {
                    'tagname': 'TagName3',
                    'values': round(random.random(), 2),
                    'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'quality': 'good'
                }
            ]
            await websocket.send(json.dumps(data))
            response = await websocket.recv()
            print(f"Received: {response}")
            await asyncio.sleep(random.uniform(1, 10))

asyncio.get_event_loop().run_until_complete(send_data())
