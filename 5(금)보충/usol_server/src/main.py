import uvicorn
from api_server import config as api_config
from api_server import exceptions as ex_api
from api_server.apis.routes.api import router as api_router
from api_server.middleware.timing import add_timing_middleware
from config import settings
from utils.logger import logger

LOG_LEVELS: dict[str, int] = {
    "critical": logger.critical,
    "error": logger.error,
    "warning": logger.warning,
    "info": logger.info,
    "debug": logger.debug,
}


app = api_config.get_application()
app.include_router(api_router)

exclude_timing = []
if settings.USE_API_LOG_TIMING:
    add_timing_middleware(
        app,
        record=LOG_LEVELS.get(settings.LOG_LEVEL_UVICORN_TIMING, logger.debug),
        prefix="app",
        exclude=exclude_timing,
    )
ex_api.add_exception_handlers(app)


def run_api_server():
    uvicorn.run(
        app,
        host=api_config.get_api_ip(),
        port=api_config.get_api_port(),
        log_config=api_config.get_uvicorn_logging_config(),
        log_level=(settings.LOG_LEVEL_UVICORN).lower(),
    )


if __name__ == "__main__":
    run_api_server()
