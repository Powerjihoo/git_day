from enum import Enum

from fastapi import FastAPI


class ModelName(str, Enum):
    alxnet = 'alexnet'
    resnet = 'resnet'
    lenet = 'lenet'

app = FastAPI()


@app.get('/models/{model_name}')
async def get_model(model_name : ModelName):
    if model_name is ModelName.alxnet:
        return {"Model_name":model_name, 'message':'DL'}
    if model_name.value == 'lenet':
        return {'Modle_name':model_name, 'message':'image'}
    
    return {'Model_name',model_name, 'message','residual'}