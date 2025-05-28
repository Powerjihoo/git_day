from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
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


class InvalidRequestBody(Exception):
    def __init__(self, message: str = "Invalid request body"):
        self.status_code = status.HTTP_406_NOT_ACCEPTABLE
        self.message = message
        logger.debug("Requested invalid body")


class NotFoundScriptError(Exception):
    def __init__(
        self, script_key: str, message: str = "Can not find requested tagname"
    ):
        self.script_key = script_key
        self.status_code = status.HTTP_406_NOT_ACCEPTABLE
        self.message = message
        self.detail = {"tagname": self.script_key}
        logger.error(f"{self.message} | tagname={self.script_key}")


class CodeSyntaxError(Exception):
    def __init__(self, code: str | list[str], message: str = "Code syntex error"):
        self.code = code
        self.status_code = status.HTTP_406_NOT_ACCEPTABLE
        self.message = message
        self.detail = {"code": self.code}
        if isinstance(self.code, str):
            _code = self.code
        else:
            _code = "\n".join(self.code)
        logger.error(f"{self.message}\n{_code}")


async def http_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=exc.status_code, content=str(exc.detail))


async def validation_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )


async def invalid_request_body(request: Request, exc: InvalidRequestBody):
    return JSONResponse(status_code=exc.status_code, content={"message": exc.message})


async def not_found_tagname_exception_handler(
    request: Request, exc: NotFoundScriptError
):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message, "detail": exc.detail},
    )


async def code_syntax_error(request: Request, exc: CodeSyntaxError):
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder({"message": str(exc.message), "details": exc.detail}),
    )


def add_exception_handlers(app):
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(InvalidRequestBody, invalid_request_body)
    app.add_exception_handler(NotFoundScriptError, not_found_tagname_exception_handler)
    app.add_exception_handler(CodeSyntaxError, code_syntax_error)
