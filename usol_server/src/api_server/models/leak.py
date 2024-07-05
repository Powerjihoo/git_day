from pydantic import BaseModel, conlist


class VibData(BaseModel):
    name: str
    fft: conlist(float, min_length=513, max_length=513)
