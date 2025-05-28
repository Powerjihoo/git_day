from typing import Any

from pydantic import BaseModel

from custom_calc.models import ScriptInputTagData

from .durations import DataParamsSingleDuration


class _ScriptOutputTags(BaseModel):
    tagname: str
    script: str


class _ScriptInfo(BaseModel):
    script_name: str
    initialization_code: str = None
    calculation_code: str
    input_tagnames: list[str]
    output_tags: list[_ScriptOutputTags]


class ScriptInfo(_ScriptInfo):
    script_id: int


class ScriptValidation(_ScriptInfo):
    data: list[dict[str, ScriptInputTagData]]


class ScriptData(BaseModel):
    script_id: int
    data: dict[str, ScriptInputTagData]


class ScriptDataPlot(BaseModel):
    script_id: int
    data_params: DataParamsSingleDuration


class RequestScriptCalc(BaseModel):
    script_id: int


class ResponseScriptCalc(BaseModel):
    script_id: int
    script_name: str
    input_data: list[_ScriptOutputTags]
    calc_result: dict[str, float]


class ResponseScriptCalcDebug(ResponseScriptCalc):
    calc_result_log: dict[str, Any]


class _ScriptExcutionTime(BaseModel):
    calc_result: dict[str, float]
    total_time: float
    calc_cnt: int
    mean_time: float


class ResponseScriptExecutionTime(BaseModel):
    script_id: int
    script_name: str
    message: str
    details: _ScriptExcutionTime = None
