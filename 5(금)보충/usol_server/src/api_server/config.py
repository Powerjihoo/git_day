import uvicorn
from config import settings
from fastapi import FastAPI
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles
from resources.constant import CONST
from resources.version import __version__
from starlette.middleware.cors import CORSMiddleware
from utils import exceptions as ex_util
from utils import system
from utils.logger import logger


def get_application() -> FastAPI:
    app = FastAPI(
        title=CONST.PROGRAM_NAME,
        version=__version__,
        default_response_class=ORJSONResponse,
    )
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", include_in_schema=False)
    async def root():
        return f"{CONST.PROGRAM_NAME}, {CONST.COMPANY_NAME}"

    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - Swagger",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url="/static/swagger-ui-bundle.js",
            swagger_css_url="/static/swagger-ui.css",
            swagger_favicon_url="/static/favicon_gaonpf.png",
        )

    @app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
    async def swagger_ui_redirect():
        return get_swagger_ui_oauth2_redirect_html()

    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - ReDoc",
            redoc_js_url="/static/redoc.standalone.js",
            redoc_favicon_url="/static/favicon_gaonpf.png",
        )

    logger.info(f"{CONST.PROGRAM_NAME} is starting...")

    return app


def get_uvicorn_logging_config():
    date_fmt = "%Y-%m-%d %H:%M:%S"
    _config = uvicorn.config.LOGGING_CONFIG

    _config["formatters"]["default"][
        "fmt"
    ] = "[%(asctime)s] %(levelprefix)s %(message)s"
    _config["formatters"]["default"]["datefmt"] = date_fmt
    _config["formatters"]["default"]["use_colors"] = True

    _config["formatters"]["access"][
        "fmt"
    ] = '[%(asctime)s] %(levelprefix)s "%(request_line)s" %(status_code)s - %(client_addr)s'
    _config["formatters"]["access"]["datefmt"] = date_fmt
    return _config


def get_api_ip():
    _ip = settings.APP_HOST
    if system.validate_ip_address(_ip):
        return _ip
    _ip = system.get_local_ip_address()
    if system.validate_ip_address(_ip):
        return _ip
    raise ex_util.InvalidIPAddressError(_ip)


def get_api_port():
    _port = settings.APP_PORT
    if system.validate_port_number(_port):
        return int(_port)
    _port = CONST.DEFAULT_PORT
    if system.validate_port_number(_port):
        return int(_port)
    raise ex_util.InvalidPortNumberError(_port)
