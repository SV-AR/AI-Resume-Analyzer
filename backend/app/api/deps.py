"""Shared FastAPI dependencies."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database.session import get_db
from app.models import User
from app.services.embedding_service import EmbeddingService, get_embedding_service
from app.services.job_analyzer import JobAnalyzer
from app.services.nlp_processor import ResumeNLPProcessor

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

_processor: ResumeNLPProcessor | None = None
_job_analyzer: JobAnalyzer | None = None


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    sub = decode_access_token(token)
    if sub is None or not sub.isdigit():
        raise credentials_error
    user = db.get(User, int(sub))
    if user is None or not user.is_active:
        raise credentials_error
    return user


def get_resume_processor() -> ResumeNLPProcessor:
    """Created once; shares the cached spaCy pipeline and skill matcher."""
    global _processor
    if _processor is None:
        _processor = ResumeNLPProcessor()
    return _processor


def get_job_analyzer_dep() -> JobAnalyzer:
    global _job_analyzer
    if _job_analyzer is None:
        _job_analyzer = JobAnalyzer()
    return _job_analyzer


def get_embedder() -> EmbeddingService:
    return get_embedding_service()
