from fastapi import APIRouter, Response, status

router = APIRouter()


@router.get(
    "/health_status",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Check API Server is running",
    include_in_schema=False,
)
async def check_health_status():
    """
    API 서버가 실행 중인지 확인합니다.
    """
    return Response(status_code=status.HTTP_204_NO_CONTENT)
