from pydantic import BaseModel

class ResponseBase(BaseModel):
    message:str = "Success"
    details:dict = {}