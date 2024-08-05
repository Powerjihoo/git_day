import uvicorn
from api_server import config as api_config
from api_server.apis.routes.api import router as api_router
from config import settings

app = api_config.get_application()
app.include_router(api_router)

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
