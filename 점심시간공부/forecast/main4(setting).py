from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class DataInput(BaseModel):
    name : str


class PredictOutput(BaseModel):
    prob:float
    prediction:int


@app.post('/pydantic',response_model=PredictOutput)
def pydantic_post(data_request:DataInput):
    return {'prob':0.1, 'prediction':0aa}