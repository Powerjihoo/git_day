import asyncio

from fastapi import FastAPI

app = FastAPI()

async def some_library(num:int,something:str):
    s = 0
    for i in range(num):
        print('something..:',something, i)
        #동기방식
        #time.sleep(1)
        await asyncio.sleep(1)  #await asyncio를 사용해 비동기로 사용한다
        s += int(something)
    return s

app = FastAPI()

@app.post('/')
async def read_results(something:str):
    s1 = await some_library(5,something)
    return {'data':'data','s1':s1}