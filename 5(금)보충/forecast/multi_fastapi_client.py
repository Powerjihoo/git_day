import asyncio
import datetime
import json
import random

import websockets


async def send_data():
    uri = 'ws://localhost:1113/forecast'
    inc = 0.005
    async with websockets.connect(uri) as websocket:
        while True:
            random_value1 = random.uniform(36, 38)+inc
            random_value2 = random.uniform(36, 38)-inc
            inc+=0.005
            data = [
                {
                    'tagname': 1,
                    'values': random_value1,
                    'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                {
                    'tagname': 2,
                    'values': random_value2,
                    'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            ]
            await websocket.send(json.dumps(data))
            print(f"Sent({data[0]['tagname']}) : {data[0]['values']}")
            print(f"Sent({data[1]['tagname']}) : {data[1]['values']}")
            await asyncio.sleep(random.uniform(3, 7))

asyncio.get_event_loop().run_until_complete(send_data())


