"""
calctag.py

이 모듈은 FastAPI를 사용하여 커스텀 태그 스크립트를 관리하는 API 엔드포인트를 정의합니다.
여기에는 커스텀 태그 스크립트의 추가, 조회, 등록 및 해제 기능이 포함됩니다.

모듈 구성 요소:
- show: 전체 커스텀 태그 스크립트의 정보를 반환하는 엔드포인트.
- get_custom_tag_code: 특정 커스텀 태그 스크립트의 계산 코드를 반환하는 엔드포인트.
- add_script: 새로운 커스텀 태그 스크립트를 추가하는 엔드포인트.
- register: 커스텀 태그 스크립트를 등록하는 엔드포인트.
- unregister: 특정 커스텀 태그 스크립트를 등록 해제하는 엔드포인트.
"""

import orjson
from fastapi import APIRouter, Response, status

from api_server import exceptions as ex_api
from api_server.models.calctags import ScriptInfo, _ScriptInfo
from custom_calc.customcalctag import (
    CanNotFindTagError,
    CustomScript,
    CustomScriptManager,
)

router = APIRouter()
calc_manager = CustomScriptManager()


@router.get("/info", include_in_schema=False)
async def show():
    """
    전체 커스텀 태그 스크립트의 정보를 반환합니다.

    Returns:
        JSON 응답으로 각 커스텀 태그 스크립트의 세부 정보를 포함한 딕셔너리를 반환합니다.
    """
    result = {
        "message": "Success",
        "details": {
            str(k): {
                "script_name": v.script_name,
                "input_tagnames": v.input_tagnames,
                "initialization_code": v.initialization_code,
                "calculation_code": v.calculation_code,
                "output_tags": [
                    dict(_output_tag) for _output_tag in calc_manager[24]._output_tags
                ],
            }
            for k, v in calc_manager.items()
        },
    }

    return Response(content=orjson.dumps(result), status_code=status.HTTP_200_OK)


@router.get("/{tagname}", include_in_schema=False)
async def get_custom_tag_code(script_id: str):
    """
    특정 커스텀 태그 스크립트의 계산 코드를 반환합니다.

    Args:
        script_id (str): 커스텀 태그 스크립트의 ID.

    Returns:
        JSON 응답으로 스크립트 ID와 계산 코드를 포함한 딕셔너리를 반환합니다.
    """
    result = {
        "message": "Success",
        "details": {
            "script_id": script_id,
            "calculation_code": calc_manager[script_id].calculation_code,
        },
    }

    return Response(content=orjson.dumps(result), status_code=status.HTTP_200_OK)


@router.post("/add/{script_name}", include_in_schema=False)
async def add_script(custom_script: _ScriptInfo):
    """
    새로운 커스텀 태그 스크립트를 추가합니다.

    Args:
        custom_script (_CalcTag): 추가할 커스텀 태그 스크립트 객체.

    Returns:
        JSON 응답으로 성공 메시지와 추가된 스크립트의 세부 정보를 반환합니다.
    """
    script_id = calc_manager.save_custom_tag(custom_script)
    result = {
        "message": "Success",
        "details": {
            "script_id": script_id,
            "script_name": custom_script.script_name,
            "calculation_code": custom_script.calculation_code,
        },
    }
    return Response(content=orjson.dumps(result), status_code=status.HTTP_201_CREATED)


@router.post("/register/{script_id}")
async def register(request: ScriptInfo):
    """
    커스텀 태그 스크립트를 등록합니다.

    Args:
        request (CalcTag): 등록할 커스텀 태그 스크립트 객체.

    Returns:
        JSON 응답으로 성공 메시지와 등록된 스크립트의 세부 정보를 반환합니다.
    """
    try:
        new_custom_tag: CustomScript = calc_manager.create_custom_tag_obj(
            script_id=request.script_id,
            script_name=request.script_name,
            input_tagnames=request.input_tagnames,
            initialization_code=request.initialization_code,
            calculation_code=request.calculation_code,
            output_tags=request.output_tags,
        )
        calc_manager.register_calc_tag(custom_script=new_custom_tag, logging=True)

        result = {
            "message": "Success",
            "details": {
                "script_name": request.script_name,
                "calculation_code": request.calculation_code,
            },
        }
    except Exception as e:
        return Response(content=e.args[0], status_code=status.HTTP_400_BAD_REQUEST)

    return Response(content=orjson.dumps(result), status_code=status.HTTP_201_CREATED)


@router.delete("/register/{script_id}")
async def unregister(script_id: str):
    """
    특정 커스텀 태그 스크립트를 등록 해제합니다.

    Args:
        script_id (str): 등록 해제할 커스텀 태그 스크립트의 ID.

    Returns:
        상태 코드 204로 응답합니다.
    """
    try:
        calc_manager.unregister_calc_tag(script_id)

        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except CanNotFindTagError as e:
        raise ex_api.NotFoundScriptError(script_key=script_id, message=e.args[0])
