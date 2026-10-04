from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Error with a stable machine-readable code and a user-safe message."""

    status_code = 400

    def __init__(self, code: str, message: str, status_code: int | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class NotFound(AppError):
    def __init__(self, what: str = "Resource"):
        super().__init__("not_found", f"{what} not found", 404)


class Unauthorized(AppError):
    def __init__(self, message: str = "Authentication required"):
        super().__init__("unauthorized", message, 401)


class RateLimited(AppError):
    def __init__(self, message: str = "Too many requests. Please try again later."):
        super().__init__("rate_limited", message, 429)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        fields = {".".join(str(p) for p in e["loc"][1:]): e["msg"] for e in exc.errors()}
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Please check the highlighted fields",
                    "fields": fields,
                }
            },
        )
