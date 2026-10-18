"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging

settings = get_settings()
setup_logging(settings.log_level)
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Starting %s (environment=%s)", settings.app_name, settings.environment)
    if settings.preload_models:
        from app.api.deps import get_resume_processor
        from app.services.embedding_service import get_embedding_service

        get_resume_processor()  # loads spaCy + skill matcher once
        try:
            get_embedding_service().encoder.load()
        except Exception:  # logged inside; the API still starts and /api/health reports the problem
            logger.error("Embedding model could not be preloaded; it will be retried on first use")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Resume analysis and resume-job matching with spaCy and Sentence Transformers. "
                "Scores are similarity measures, not hiring predictions.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)
register_exception_handlers(app)


@app.exception_handler(RequestValidationError)
async def validation_handler(_, exc: RequestValidationError):
    errors = [{"field": ".".join(str(p) for p in e["loc"] if p != "body"), "message": e["msg"]} for e in exc.errors()]
    msg = "; ".join(f"{e['field']}: {e['message']}" if e["field"] else e["message"] for e in errors)
    return JSONResponse(status_code=422, content={"detail": msg, "errors": errors})


app.include_router(api_router)
