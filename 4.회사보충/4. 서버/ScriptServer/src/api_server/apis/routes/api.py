"""
이 모듈은 FastAPI 라우터를 설정합니다.
각 라우터는 다른 엔드포인트를 처리합니다.
"""

from fastapi import APIRouter

from api_server.apis.routes import calc, script, system

router = APIRouter()
router.include_router(script.router, tags=["script"], prefix="/script")
router.include_router(calc.router, tags=["calc"], prefix="/calc")
router.include_router(system.router, tags=["system"], prefix="/system")
