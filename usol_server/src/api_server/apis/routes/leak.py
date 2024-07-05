from algorithm.leak_detection import dist_classifier, leak_classifier
from fastapi import APIRouter, Body

from api_server.apis.examples.leak import vib_data_example
from api_server.models.leak import VibData

router = APIRouter()


@router.post("/test")
async def classify_vib_data(data: list[VibData] = Body(examples=vib_data_example)):
    input_data = [_data.fft for _data in data]
    names = [_data.name for _data in data]
    leak_result = leak_classifier(input_data)
    dist_result = dist_classifier(leak_result, input_data)
    dist_result.insert(0, "names", names)
    return dist_result.to_dict("records")
