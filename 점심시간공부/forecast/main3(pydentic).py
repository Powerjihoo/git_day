from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel, Field


class movie(BaseModel):
    mid:int
    genre:str
    rate : Union[int,float]
    tag : Optional[str] = None
    date : Optional[datetime] = None
    some_variable_list : List[int] = []

class user(BaseModel):
    uid:int
    name : str=Field(min_length=2, max_length=7)
    age : int=Field(gt=1, le=130)

tmp_movie_data = {
    'mid':'1',
    'genre':'action',
    'rate':1.5,
    'tag':None,
    'date':'2024-07-05 14:00:00'
}

tmp_user_data = {
    'uid':'100',
    'name':'jihoo',
    'age':'12'
}

tmp_movie = movie(**tmp_movie_data)
tmp_user = user(**tmp_user_data)
print(tmp_movie.json())
print(tmp_user.json())