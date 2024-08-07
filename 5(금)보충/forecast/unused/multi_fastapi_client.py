import asyncio
import datetime
import json
import random

import websockets


async def send_data():
    uri = 'ws://localhost:1111/ws'
    async with websockets.connect(uri) as websocket:
        while True:
            data = [
                {
                    'tagname': 1,
                    'values': round(random.random(), 2),
                    'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                {
                    'tagname': 2,
                    'values': round(random.random(), 2),
                    'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                {
                    'tagname': 4,
                    'values': round(random.random(), 2),
                    'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            ]
            await websocket.send(json.dumps(data))
            print(f"Sent({data[0]['tagname']}) : {data[0]['values']}")
            print(f"Sent({data[1]['tagname']}) : {data[1]['values']}")
            print(f"Sent({data[2]['tagname']}) : {data[2]['values']}")
            await asyncio.sleep(random.uniform(3, 7))

asyncio.get_event_loop().run_until_complete(send_data())
