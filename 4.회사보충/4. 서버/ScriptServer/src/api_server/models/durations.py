from datetime import datetime, timedelta

from pendulum import parse as pdl_parse
from pydantic import BaseModel, Field, conint, conlist, constr, field_validator

from utils.system import regex_date_validation

DURATION_ERROR_MESSAGE = "duration_end must be greater than duration_start"


class _Duration(BaseModel):
    start: str
    end: str

    def __init__(self, **data):
        if "start" in data:
            data["start"] = datetime.fromisoformat(data["start"])
        if "end" in data:
            data["end"] = datetime.fromisoformat(data["end"])
        super().__init__(**data)


class DataParamsMultipleDuration(BaseModel):
    sampling_interval_seconds: conint(ge=1, le=8640000) = 5
    durations: conlist(_Duration, min_length=1)

    @field_validator("durations")
    def check_duration(cls, values):
        start, end = values.data.start, values.data.end
        if start >= end or not start or not end:
            values.start, values.end = values.end, values.start
        return values


class DataParamsSingleDuration(BaseModel):
    duration_start: datetime = Field(description="Start of the duration")
    duration_end: datetime = Field(description="End of the duration")
    sampling_interval_seconds: conint(ge=1, le=8640000) = 1

    def __init__(self, **data):
        if "duration_start" in data:
            data["duration_start"] = datetime.fromisoformat(data["duration_start"])
        if "duration_end" in data:
            data["duration_end"] = datetime.fromisoformat(data["duration_end"])
        super().__init__(**data)


class DataParamsDefaultDuration(BaseModel):
    duration_start: constr(pattern=regex_date_validation())
    duration_end: constr(pattern=regex_date_validation())

    @field_validator("duration_end")
    def check_duration(cls, v, values):
        start, end = values.data["duration_start"], v
        if start >= end or not start or not end:
            raise ValueError(DURATION_ERROR_MESSAGE)
        return v


def split_durations(
    start: datetime, end: datetime, split_duration_days: int
) -> list[_Duration]:
    """
    Calculate split durations between start and end dates.

    Args:
        start (datetime): Start datetime.
        end (datetime): End datetime.
        split_duration_days (int): Duration(days) to split the range.

    Returns:
        list[Durations]: List of Durations objects representing the split durations.
    """

    if isinstance(start, str):
        start = pdl_parse(start)
    if isinstance(end, str):
        end = pdl_parse(end)

    result = []
    current_duration_start = start
    current_duration_end = start + timedelta(days=split_duration_days)

    while current_duration_end <= end:
        result.append(
            _Duration(
                start=current_duration_start.format("YYYY-MM-DD HH:mm:ss"),
                end=current_duration_end.format("YYYY-MM-DD HH:mm:ss"),
            )
        )
        current_duration_start = current_duration_end
        current_duration_end += timedelta(days=split_duration_days)

    # Handle the remaining duration
    if current_duration_start < end:
        result.append(
            _Duration(
                start=current_duration_start.format("YYYY-MM-DD HH:mm:ss"),
                end=end.format("YYYY-MM-DD HH:mm:ss"),
            )
        )

    return result
