from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from app.core.logging import logger


class AppError(Exception):
    def __init__(self, message: str, status_code: int = 500, detail: str = ""):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, resource: str):
        super().__init__(f"{resource} not found", status_code=404)


class ValidationError(AppError):
    def __init__(self, message: str):
        super().__init__(message, status_code=422)


class ProcessingError(AppError):
    def __init__(self, message: str):
        super().__init__(message, status_code=500)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    logger.warning(f"AppError [{exc.status_code}]: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "detail": exc.detail},
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )
