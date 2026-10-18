import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, get_embedder
from app.database.session import get_db
from app.models import Analysis, JobDescription, Resume, User
from app.schemas.analysis import AnalysisOut, AnalysisSummary, MatchRequest
from app.services.analysis_service import run_analysis
from app.services.embedding_service import EmbeddingService

router = APIRouter(prefix="/matching", tags=["Matching"])
logger = logging.getLogger(__name__)


def to_out(a: Analysis) -> AnalysisOut:
    out = AnalysisOut.model_validate(a)
    out.component_scores = a.details.get("component_scores", {})
    out.weights = a.details.get("weights", {})
    out.resume_name = a.resume.original_filename
    out.job_title = a.job.title
    return out


@router.post("/analyze", response_model=AnalysisOut, status_code=status.HTTP_201_CREATED)
def analyze_match(payload: MatchRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user),
                  embedder: EmbeddingService = Depends(get_embedder)):
    resume = db.scalar(select(Resume).where(Resume.id == payload.resume_id, Resume.user_id == user.id).options(
        selectinload(Resume.skills), selectinload(Resume.education), selectinload(Resume.experience),
        selectinload(Resume.projects), selectinload(Resume.certifications)))
    job = db.scalar(select(JobDescription).where(JobDescription.id == payload.job_id,
                                                 JobDescription.user_id == user.id))
    if resume is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Resume not found.")
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job description not found.")
    analysis = run_analysis(db, user.id, resume, job, embedder)
    return to_out(analysis)


@router.get("", response_model=list[AnalysisSummary])
def list_analyses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(Analysis).where(Analysis.user_id == user.id).order_by(Analysis.created_at.desc())
                      .options(selectinload(Analysis.resume), selectinload(Analysis.job))).all()
    return [AnalysisSummary(id=a.id, resume_id=a.resume_id, job_id=a.job_id, resume_name=a.resume.original_filename,
                            job_title=a.job.title, overall_score=a.overall_score,
                            semantic_similarity=a.semantic_similarity, quality_score=a.quality_score,
                            created_at=a.created_at) for a in rows]


@router.get("/{analysis_id}", response_model=AnalysisOut)
def get_analysis(analysis_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    a = db.scalar(select(Analysis).where(Analysis.id == analysis_id, Analysis.user_id == user.id).options(
        selectinload(Analysis.recommendations), selectinload(Analysis.resume), selectinload(Analysis.job)))
    if a is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Analysis not found.")
    return to_out(a)
