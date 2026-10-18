"""Domain exceptions and the FastAPI handlers that turn them into clean JSON responses."""
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError, SQLAlchemyError

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code = 400
    detail = "Request could not be processed."

    def __init__(self, detail: str | None = None):
        super().__init__(detail or self.detail)
        self.detail = detail or self.detail


class UnsupportedFileError(AppError):
    status_code = 415
    detail = "Unsupported file format. Please upload PDF or DOCX."


class FileTooLargeError(AppError):
    status_code = 413
    detail = "File is too large."


class EmptyDocumentError(AppError):
    status_code = 422
    detail = "The document contains no extractable text."


class CorruptedDocumentError(AppError):
    status_code = 422
    detail = "The document appears to be corrupted or is not a valid file."


class ModelUnavailableError(AppError):
    status_code = 503
    detail = "The language model is not available right now. Please try again later."


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(OperationalError)
    async def _db_unavailable(_: Request, exc: OperationalError):
        logger.error("Database unavailable: %s", exc.__class__.__name__)
        return JSONResponse(status_code=503, content={"detail": "Database is unavailable. Please try again later."})

    @app.exception_handler(SQLAlchemyError)
    async def _db_error(_: Request, exc: SQLAlchemyError):
        logger.error("Database error: %s", exc.__class__.__name__)
        return JSONResponse(status_code=500, content={"detail": "A database error occurred."})

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception):
        # Stack trace goes to the server log only, never to the client.
        logger.exception("Unhandled error: %s", exc.__class__.__name__)
        return JSONResponse(status_code=500, content={"detail": "Internal server error."})
