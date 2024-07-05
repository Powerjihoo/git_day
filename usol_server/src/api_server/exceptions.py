from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from utils.logger import logger


class APIExeption(Exception):
    status_code: int
    code: str
    msg: str
    detail: str

    def __init__(
        self,
        *,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: str = "000000",
        msg: str = None,
        detail: str = None,
        ex: Exception = None,
    ):
        self.status_code = status_code
        self.code = code
        self.msg = msg
        self.detail = detail
        super().__init__(ex)


class WindEstimationError(Exception):
    def __init__(self, message="Can not estimate wind"):
        self.status_code = status.HTTP_406_NOT_ACCEPTABLE
        self.message = message
        logger.error(self.message)


class InvalidRequestBody(Exception):
    def __init__(self, message: str = "Invalid request body"):
        self.status_code = status.HTTP_406_NOT_ACCEPTABLE
        self.message = message
        logger.debug("Requested invalid body")


class CanNotUpdateModelAlarmSetting(Exception):
    def __init__(
        self,
        model_key: str,
        tagname: str = None,
        message: str = "Can not update model alarm setting",
    ):
        self.status_code = status.HTTP_406_NOT_ACCEPTABLE
        self.message = message
        self.model_key = model_key
        self.tagname = tagname
        logger.error(
            f"Requested model alarm setting could not be updated | model_key={self.model_key}, tagname={self.tagname}"
        )


class NoDataError(Exception):
    def __init__(self, target: str, message: str = "No data for requested target"):
        self.target = target
        self.status_code = status.HTTP_406_NOT_ACCEPTABLE
        self.message = message
        self.detail = {"target": self.target}
        logger.error(f"Could not find data for requested target {self.target}")


async def http_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=exc.status_code, content=str(exc.detail))


async def validation_exception_handler(request: Request, exc: Exception):
    logger.error(exc)
    return PlainTextResponse(status_code=400, content=str(exc))


async def wind_estimation_exception_handler(request: Request, exc: WindEstimationError):
    return JSONResponse(status_code=exc.status_code, content={"message": exc.message})


async def invalid_request_body(request: Request, exc: InvalidRequestBody):
    return JSONResponse(status_code=exc.status_code, content={"message": exc.message})


async def cannot_update_model_alarm_setting(
    request: Request, exc: CanNotUpdateModelAlarmSetting
):
    return JSONResponse(status_code=exc.status_code, content={"message": exc.message})


async def no_data_error(request: Request, exc: NoDataError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message, "detail": exc.detail},
    )


def add_exception_handlers(app):
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(WindEstimationError, wind_estimation_exception_handler)
    app.add_exception_handler(InvalidRequestBody, invalid_request_body)
    app.add_exception_handler(
        CanNotUpdateModelAlarmSetting, cannot_update_model_alarm_setting
    )
    app.add_exception_handler(NoDataError, no_data_error)
