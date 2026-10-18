import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_job_analyzer_dep
from app.database.session import get_db
from app.models import JobDescription, User
from app.schemas.job import JobAnalyzeRequest, JobOut, JobSummary
from app.services.job_analyzer import JobAnalyzer
from app.utils.text import clean_text

router = APIRouter(prefix="/jobs", tags=["Job descriptions"])
logger = logging.getLogger(__name__)


def _public(job: JobDescription) -> JobOut:
    out = JobOut.model_validate(job)
    out.analysis = {k: v for k, v in out.analysis.items() if not k.startswith("_")}
    return out


@router.post("/analyze", response_model=JobOut, status_code=status.HTTP_201_CREATED)
def analyze_job(payload: JobAnalyzeRequest, db: Session = Depends(get_db),
                user: User = Depends(get_current_user), analyzer: JobAnalyzer = Depends(get_job_analyzer_dep)):
    text = clean_text(payload.description)
    analysis = analyzer.analyze(text)
    job = JobDescription(user_id=user.id, title=(payload.title or "Untitled job").strip() or "Untitled job",
                         raw_text=text, analysis=analysis)
    db.add(job)
    db.commit()
    db.refresh(job)
    logger.info("Job description %s analysed", job.id)
    return _public(job)


@router.get("", response_model=list[JobSummary])
def list_jobs(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(select(JobDescription).where(JobDescription.user_id == user.id)
                      .order_by(JobDescription.created_at.desc())).all()


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    job = db.scalar(select(JobDescription).where(JobDescription.id == job_id, JobDescription.user_id == user.id))
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job description not found.")
    return _public(job)
