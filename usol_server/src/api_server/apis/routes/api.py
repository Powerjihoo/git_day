from fastapi import APIRouter

from api_server.apis.routes import leak

router = APIRouter()
router.include_router(leak.router, tags=["leak"], prefix="/leak")
