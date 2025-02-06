"""
이 모듈은 디버그 세션을 관리하고 FastAPI를 사용하여 웹소켓 엔드포인트를 제공하는 기능을 포함합니다.

클래스:
    DebugSessionManager: 디버그 세션을 관리하는 클래스입니다. 세션 추가, 조회, 업데이트, 삭제 등의 기능을 제공합니다.

함수:
    websocket_endpoint: 웹소켓 엔드포인트를 정의하는 비동기 함수입니다. 주어진 세션 ID를 기반으로 웹소켓 연결을 처리합니다.

모듈 구조:
- calc.py: 디버그 세션 관리 클래스(DebugSessionManager)와 웹소켓 엔드포인트(websocket_endpoint)를 포함합니다.
- src/api_server/apis/routes/api.py: FastAPI 라우터를 설정하고 다양한 라우트를 포함합니다.
- src/api_server/apis/routes/calc.py: 웹소켓 엔드포인트를 정의합니다.

사용 예:
- DebugSessionManager를 사용하여 디버그 세션을 추가하거나 조회할 수 있습니다.
- 웹소켓 엔드포인트를 통해 Python 코드를 실시간 계산 결과를 응답할 수 있습니다.
"""

import asyncio
import datetime
import io
import math
import sys
import time
import traceback
from dataclasses import dataclass, field
from time import perf_counter

import numpy as np
import orjson
import pandas as pd
import pytz
from fastapi import APIRouter, Body, Response, WebSocket, WebSocketDisconnect, status
from orjson import OPT_SERIALIZE_NUMPY

from api_client.apis.tagvalue import tagvalue_api
from api_server import exceptions as ex_api
from api_server.apis.examples.calc import request_example, validation_example
from api_server.models.calctags import (
    RequestScriptCalc,
    ResponseScriptCalc,
    ResponseScriptCalcDebug,
    ResponseScriptExecutionTime,
    ScriptData,
    ScriptDataPlot,
    ScriptInputTagData,
    _ScriptInfo,
)
from custom_calc.customcalctag import CustomScript, CustomScriptManager
from utils.dataloader import DataLoader
from utils.logger import logger

router = APIRouter()
calc_manager = CustomScriptManager()

CLIENT_TIMEOUT = 600
TIMEZONE = pytz.timezone("Asia/Seoul")


def get_last_data(tagnames: list[str]) -> dict:
    res = tagvalue_api.get_current_value(tagnames=tagnames)
    _data = res.json()

    for tagname in tagnames:
        if not _data[tagname]:
            raise ValueError(f"No data {tagname}")

    data = {}
    for tagname, tag_data in _data.items():
        data[tagname] = ScriptInputTagData(
            timestamp=tag_data["timestamp"],
            value=tag_data["value"],
            status_code=tag_data["statusCodeEnum"],
        )

    return data


def convert_df2dict(
    df: pd.DataFrame, tagnames: list[str]
) -> list[dict[str, ScriptInputTagData]]:
    result_data = []
    for _, row in df.iterrows():
        _values = {}
        for tagname in tagnames:
            _values[tagname] = ScriptInputTagData(
                timestamp=row.name.value,
                value=row[tagname],
                status_code=row[f"{tagname}_status_code"],
            )
        result_data.append(_values)
    return result_data


@router.post("/syntax_validation")
async def validate_code_syntax(
    request: _ScriptInfo = Body(None, examples=validation_example),
):
    """
    코드 구문 검증을 수행합니다.

    Args:
        request (CalcTagValidation): 검증할 코드가 포함된 요청 객체입니다.

    Returns:
        Response: 검증 결과를 포함한 응답 객체입니다.
    """
    try:
        custom_script = CustomScript(
            script_id=-1,
            script_name=request.script_name,
            initialization_code=request.initialization_code,
            calculation_code=request.calculation_code,
            input_tagnames=request.input_tagnames,
            output_tags=request.output_tags,
        )
        data = get_last_data(custom_script.input_tagnames)
        calc_result = custom_script.calc(data)
    except SyntaxError as e:
        raise ex_api.CodeSyntaxError(
            code=[request.initialization_code, request.calculation_code], message=e
        )
    except Exception as e:
        logger.error(e)
        raise ex_api.CodeSyntaxError(
            code=[request.initialization_code, request.calculation_code], message=e
        )

    result = {
        "message": "Success",
        "details": {
            "static_vars": custom_script.initialization_code,
            "code": custom_script.calculation_code,
            "calc_result": calc_result,
        },
    }

    return Response(content=orjson.dumps(result, option=OPT_SERIALIZE_NUMPY))


@router.post("")
async def calculate_script_once(
    request: RequestScriptCalc = Body(None, examples=request_example),
) -> ResponseScriptCalc:
    """
    계산을 수행합니다.

    Args:
        request (CalcTagData): 계산을 위한 요청 객체입니다.

    Returns:
        Response: 계산 결과를 포함한 응답 객체입니다.
    """

    try:
        custom_script: CustomScript = calc_manager[int(request.script_id)]
        current_time = datetime.datetime.now()
        data = get_last_data(custom_script.input_tagnames)

        s = perf_counter()
        calc_result = custom_script.calc(data)
        calc_time_taken = perf_counter() - s

        result = {
            "script_id": custom_script.script_id,
            "script_name": custom_script.script_name,
            "input_data": data,
            "calc_result": calc_result,
            "calc_at": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "calc_time_taken": calc_time_taken,
        }
    except Exception as e:
        logger.debug(e)
    return Response(content=orjson.dumps(result, option=OPT_SERIALIZE_NUMPY))


@router.post("/debug")
async def calculate_script_once_debug(
    request: RequestScriptCalc = Body(None, examples=request_example),
) -> ResponseScriptCalcDebug:
    """
    계산을 수행합니다.

    Args:
        request (CalcTagData): 계산을 위한 요청 객체입니다.

    Returns:
        Response: 계산 결과를 포함한 응답 객체입니다.
    """

    try:
        custom_script: CustomScript = calc_manager[int(request.script_id)]
        current_time = datetime.datetime.now()
        data = get_last_data(custom_script.input_tagnames)

        s = perf_counter()
        calc_result_log: pd.DataFrame = custom_script.debug_code(data)
        calc_time_taken = perf_counter() - s

        result = {
            "script_id": custom_script.script_id,
            "script_name": custom_script.script_name,
            "input_data": data,
            "calc_result": custom_script.result_output.copy(),
            "calc_result_log": calc_result_log.to_dict("records"),
            "calc_at": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "calc_time_taken": calc_time_taken,
        }
    except Exception as e:
        logger.debug(e)
    return Response(content=orjson.dumps(result, option=OPT_SERIALIZE_NUMPY))


@router.post("/excution_time")
async def test_script_calculation_execution_time(
    request: RequestScriptCalc = Body(None, examples=request_example),
) -> ResponseScriptExecutionTime:
    """
    계산 테스트를 수행합니다. 1초 동안 가능한 많은 계산을 수행하고, 총 계산 시간과 평균 계산 시간을 반환합니다.

    Args:
        request (CalcTagData): 계산을 위한 요청 객체입니다.

    Returns:
        Response: 계산 결과를 포함한 응답 객체입니다.
    """
    try:
        custom_script: CustomScript = calc_manager[int(request.script_id)]
        data = get_last_data(custom_script.input_tagnames)

        _counter = 0
        s = perf_counter()
        while perf_counter() - s <= 1.0 or _counter == 0:
            custom_script.calc(data)
            _counter += 1

        if _counter == 0:
            result = {
                "message": "Calculation time exceeded 1 second",
                "script_id": custom_script.script_id,
                "script_name": custom_script.script_name,
            }
        else:
            total_calc_time = perf_counter() - s
            mean_calc_time = total_calc_time / _counter

            result = {
                "message": "Success",
                "script_id": custom_script.script_id,
                "script_name": custom_script.script_name,
                "details": {
                    "value": custom_script.result_output,
                    "total_time": total_calc_time,
                    "calc_cnt": _counter,
                    "mean_time": mean_calc_time,
                },
            }
    except Exception as e:
        logger.exception(e)

    return Response(content=orjson.dumps(result, option=OPT_SERIALIZE_NUMPY))


@router.post("/plot")
async def calculate_script_multiple_point(request: ScriptDataPlot = Body(None)):
    """
    calc_plot 엔드포인트는 주어진 요청 데이터에 대해 계산을 수행합니다.

    Args:
        request (list[dict]): 계산을 위한 데이터 목록.

    Returns:
        Response: 계산 결과를 포함한 응답 객체입니다.
    """

    custom_script: CustomScript = calc_manager[request.script_id]
    output_tagnames = [tag.tagname for tag in custom_script._output_tags]

    df_data = DataLoader.load_from_influx_raw(
        tagnames=custom_script.input_tagnames,
        start=request.data_params.duration_start,
        end=request.data_params.duration_end,
        offset_hour=9,
    )

    input_data = {tagname: {} for tagname in custom_script.input_tagnames}
    for tagname in custom_script.input_tagnames:
        df_data_tag = df_data[df_data.tagname == tagname]
        input_data[tagname]["x"] = df_data_tag.time.apply(lambda x:x.value).values
        input_data[tagname]["y"] = df_data_tag.value.values
        
    test_result = {tagname: {"x": [], "y": []} for tagname in output_tagnames}
    script_input_data = {
        tagname: ScriptInputTagData(-1, np.nan, 0)
        for tagname in custom_script.input_tagnames
    }

    for _, row in df_data.iterrows():
        script_input_data[row.tagname] = ScriptInputTagData(
            timestamp=row.time.value, value=row.value, status_code=row.quality
        )
        custom_script.calc(script_input_data)
        _result = custom_script.result_output.copy()
        for tagname in output_tagnames:
            if math.isnan(_result[tagname]):
                continue
            test_result[tagname]["x"].append(
                np.max([tag_data.timestamp for tag_data in script_input_data.values()])
            )
            test_result[tagname]["y"].append(_result[tagname])

    first_timestamp = (
        pd.to_datetime(request.data_params.duration_start)
        .tz_localize(tz=TIMEZONE)
        .value
    )
    last_timestamp = (
        pd.to_datetime(request.data_params.duration_end).tz_localize(tz=TIMEZONE).value
    )
    for tagname in list(test_result.keys()):
        if not test_result[tagname]["x"][0] == first_timestamp:
            firstvalue = test_result[tagname]["y"][0]
            test_result[tagname]["x"].insert(0, first_timestamp)
            test_result[tagname]["y"].insert(0, firstvalue)

        if not test_result[tagname]["x"][-1] == last_timestamp:
            lastvalue = test_result[tagname]["y"][-1]
            test_result[tagname]["x"].append(last_timestamp)
            test_result[tagname]["y"].append(lastvalue)

    plot_result = {
        "data_input": input_data,
        "data_output": test_result,
    }

    return Response(content=orjson.dumps(plot_result, option=OPT_SERIALIZE_NUMPY))


@router.post("/plot/debug")
async def calculate_script_multiple_point_debug(request: ScriptDataPlot = Body(None)):
    """
    엔드포인트는 디버깅 모드에서 계산을 수행합니다.

    Args:
        request (CalcTagData): 디버깅을 위한 데이터.

    Returns:
        Response: 디버깅 결과를 포함한 응답 객체입니다.
    """

    custom_script: CustomScript = calc_manager[request.script_id]
    output_tagnames = [tag.tagname for tag in custom_script._output_tags]

    df_data = DataLoader.load_from_influx_raw(
        tagnames=custom_script.input_tagnames,
        start=request.data_params.duration_start,
        end=request.data_params.duration_end,
        offset_hour=9,
    )

    input_data = {tagname: {} for tagname in custom_script.input_tagnames}
    for tagname in custom_script.input_tagnames:
        df_data_tag = df_data[df_data.tagname == tagname]
        input_data[tagname]["x"] = df_data_tag.time.apply(lambda x:x.value).values
        input_data[tagname]["y"] = df_data_tag.value.values
        
    test_result = {tagname: {"x": [], "y": []} for tagname in output_tagnames}
    script_input_data = {
        tagname: ScriptInputTagData(-1, np.nan, 0)
        for tagname in custom_script.input_tagnames
    }

    calc_result_logs = []
    for _, row in df_data.iterrows():
        script_input_data[row.tagname] = ScriptInputTagData(
            timestamp=row.time.value, value=row.value, status_code=row.quality
        )
        calc_result_log: pd.DataFrame = custom_script.debug_code(script_input_data)
        calc_result_logs.append(calc_result_log.to_dict("records"))
        _result = custom_script.result_output.copy()
        for tagname in output_tagnames:
            if math.isnan(_result[tagname]):
                continue
            test_result[tagname]["x"].append(
                np.max([tag_data.timestamp for tag_data in script_input_data.values()])
            )
            test_result[tagname]["y"].append(_result[tagname])

    first_timestamp = (
        pd.to_datetime(request.data_params.duration_start)
        .tz_localize(tz=TIMEZONE)
        .value
    )
    last_timestamp = (
        pd.to_datetime(request.data_params.duration_end).tz_localize(tz=TIMEZONE).value
    )
    for tagname in list(test_result.keys()):
        if not test_result[tagname]["x"][0] == first_timestamp:
            firstvalue = test_result[tagname]["y"][0]
            test_result[tagname]["x"].insert(0, first_timestamp)
            test_result[tagname]["y"].insert(0, firstvalue)

        if not test_result[tagname]["x"][-1] == last_timestamp:
            lastvalue = test_result[tagname]["y"][-1]
            test_result[tagname]["x"].append(last_timestamp)
            test_result[tagname]["y"].append(lastvalue)

    debug_result = {
        "data_input": input_data,
        "data_output": test_result,
        "debug_logs": calc_result_logs,
    }

    return Response(content=orjson.dumps(debug_result, option=OPT_SERIALIZE_NUMPY))


@dataclass
class DebugSession:
    """
    디버그 세션 정보를 담고 있는 클래스입니다.

    Attributes:
        session_id (str): 세션 ID.
        variables (dict): 세션 변수.
        last_activate (float): 마지막 활성화 시간.
    """

    session_id: str
    variables: dict = field(default_factory=dict)
    last_activate: float = time.time()


class DebugSessionManager(dict):
    """
    디버그 세션을 관리하는 클래스입니다.
    """

    def __add_session(self, session_id: str) -> None:
        """
        새로운 디버그 세션을 추가합니다.

        Args:
            session_id (str): 세션 ID.
        """
        self[session_id] = DebugSession(session_id=session_id)
        logger.info(f"New debug session added {session_id=}")

    def get_session(self, session_id: str) -> DebugSession:
        """
        세션 ID로 디버그 세션을 가져옵니다.

        Args:
            session_id (str): 세션 ID.

        Returns:
            DebugSession: 디버그 세션 객체.
        """
        if session_id not in self:
            self.__add_session(session_id=session_id)
        return self.get(session_id)

    def update_session_variables(self, session_id: str, data: dict) -> None:
        """
        세션 변수들을 업데이트합니다.

        Args:
            session_id (str): 세션 ID.
            data (dict): 업데이트할 변수 데이터.
        """
        session: DebugSession = self[session_id]
        session.variables = data

    def update_session_last_activate(self, session_id: str, data: float) -> None:
        """
        세션의 마지막 활성화 시간을 업데이트합니다.

        Args:
            session_id (str): 세션 ID.
            data (float): 마지막 활성화 시간.
        """
        session: DebugSession = self[session_id]
        session.last_activate = data

    def remove_session(self, session_id: str) -> None:
        """
        세션을 제거합니다.

        Args:
            session_id (str): 세션 ID.
        """
        if session_id in self:
            del self[session_id]
            logger.info(f"Inactive debug session removed {session_id=}")


debug_session_manager = DebugSessionManager()


@router.post("/debug/{session_id}/activate")
async def activate_debug_console(
    session_id: str,
    request: ScriptData = Body(None, examples=request_example),
):
    """
    디버그 콘솔을 활성화

    Args:
        session_id (str): 세션 ID
        request (CalcTagData): 디버깅을 위한 데이터

    Returns:
        Response: 상태 코드 204를 반환
    """
    try:
        debug_session = debug_session_manager.get_session(session_id=session_id)
        _session_temp_variables = debug_session.variables

        custom_script: CustomScript = calc_manager[request.script_id]
        exec(
            custom_script.calculation_code,
            CustomScript.allowed_builtins
            | {"self": custom_script, "Value": request.data},
            _session_temp_variables,
        )
    except Exception as e:
        logger.debug(e)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/debug/{session_id}/deactivate")
async def deactivate_debug_console(
    session_id: str,
):
    """
    디버그 콘솔 비활성화

    Args:
        session_id (str): 세션 ID

    Returns:
        Response: 상태 코드 204를 반환
    """
    debug_session_manager.remove_session(session_id=session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.websocket("/debug/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    디버그 웹소켓 엔드포인트를 처리합니다.

    Args:
        websocket (WebSocket): 웹소켓 객체.
        session_id (str): 세션 ID.
    """
    await websocket.accept()
    logger.info(f"Client {session_id} connected")
    debug_session = debug_session_manager.get_session(session_id=session_id)
    _session_temp_variables = debug_session.variables

    try:
        while True:
            try:
                debug_session_manager.update_session_last_activate(
                    session_id=session_id, data=time.time()
                )

                code = (await websocket.receive_text()).strip()
                logger.trace(f"Received code from client {session_id}: {code}")

                old_stdout = sys.stdout
                old_stderr = sys.stderr
                new_stdout = io.StringIO()
                new_stderr = io.StringIO()
                sys.stdout = new_stdout
                sys.stderr = new_stderr
                try:
                    exec(code, _session_temp_variables)
                    result = new_stdout.getvalue()

                    try:
                        expression_result = eval(code, {}, _session_temp_variables)
                        result += (
                            f"{expression_result}"
                            if expression_result is not None
                            else ""
                        )
                    except Exception:
                        pass
                    error = new_stderr.getvalue()
                    if error:
                        result += "\nErrors:\n" + error
                except Exception as e:
                    result = f"[Exception] {e.__repr__()}"
                finally:
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr

                await websocket.send_text(result.strip())
            except WebSocketDisconnect:
                logger.info(f"Client {session_id} disconnected")
                break
            except Exception as e:
                logger.error(f"Error handling client {session_id}: {str(e)}")
                await websocket.send_text(f"Error: {str(e)}\n{traceback.format_exc()}")

    finally:
        if websocket.client_state != WebSocketDisconnect:
            try:
                await websocket.close()
            except Exception as e:
                logger.warning(
                    f"Error closing websocket for client {session_id}: {str(e)}"
                )


async def cleanup_debug_sessions(interval: float = 5.0):
    """
    비활성 디버그 세션을 정리하는 함수

    Args:
        interval (float): 정리 주기 (초)
    """
    while True:
        current_time = time.time()
        for session_id in list(debug_session_manager.keys()):
            session: DebugSession = debug_session_manager[session_id]
            if current_time - session.last_activate > CLIENT_TIMEOUT:
                debug_session_manager.remove_session(session_id=session_id)
        await asyncio.sleep(interval)
