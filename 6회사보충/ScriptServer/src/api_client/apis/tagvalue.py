# tagvalue.py

"""API for requesting influx data"""

from datetime import datetime
from typing import Any, List, Union

from pendulum import parse as pdl_parse

from api_client.apis.session import APISession
from utils import exceptions as ex_util
from utils.system import convert_unixtime2datetime

basepath = "/api/TagValue"


class TagValueAPI(APISession):
    def __init__(self):
        self.headers = {"Content-Type": "application/json-patch+json"}
        super().__init__()

    def get_historian_value_sampling(
        self, interval: int, start: int, end: int, tagnames: List[str]
    ) -> None:
        path = "/sampling"
        url = self.baseurl + basepath + path
        data = {
            "intervalSecond": str(interval),
            "start": self.formatting_datetime(start),
            "end": self.formatting_datetime(end),
            "tagNames": ",".join(tagnames) if isinstance(tagnames, list) else tagnames,
        }
        return self.request_post(url=url, data=str(data), headers=self.headers)

    def get_historian_value_archive(
        self, start: int, end: int, tagnames: Union[str, List[str]]
    ) -> None:
        if isinstance(tagnames, list):
            tagnames = ",".join(tagnames)
        path = f"/archive/{tagnames}/{self.formatting_datetime(start)}/{self.formatting_datetime(end)}"
        url = self.baseurl + basepath + path
        return self.request_get(url)

    def get_current_value_all(self) -> None:
        path = "/api/Python/Value/Realtime"
        url = self.baseurl + path
        return self.request_get(url)

    def get_current_value(self, tagnames: List[str]) -> dict:
        tagnames_str = ",".join(tagnames)
        path = f"/api/Python/Value/Realtime/{tagnames_str}"
        url = self.baseurl + path
        return self.request_get(url)

    def formatting_datetime(self, unknown_datetime: Any) -> str:
        if isinstance(unknown_datetime, (int, float)):
            return convert_unixtime2datetime(unknown_datetime)
        elif isinstance(unknown_datetime, str):
            return pdl_parse(unknown_datetime).strftime("%Y%m%d%H%M%S")
        elif isinstance(unknown_datetime, datetime):
            return unknown_datetime.strftime("%Y%m%d%H%M%S")
        else:
            raise ex_util.InvalidFormatError()


tagvalue_api = TagValueAPI()
