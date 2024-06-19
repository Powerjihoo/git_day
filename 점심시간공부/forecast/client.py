import asyncio
import websockets

async def hello():
    url = "ws://localhost:8766"
    async with websockets.connect(url) as websocket:
        name = input("이름기입: ")

        # 서버로 이름 보내기
        await websocket.send(name)
        print(f"Sent name: {name}")

asyncio.get_event_loop().run_until_complete(hello())
