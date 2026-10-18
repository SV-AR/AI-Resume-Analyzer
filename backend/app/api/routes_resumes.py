import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, get_resume_processor
from app.core.config import get_settings
from app.core.exceptions import FileTooLargeError
from app.database.session import get_db
from app.models import Resume, ResumeSkill, User
from app.schemas.resume import ResumeDetail, ResumeSummary
from app.services.document_processor import process_document, validate_upload
from app.services.nlp_processor import ResumeNLPProcessor
from app.services.resume_service import create_resume, delete_resume_file

router = APIRouter(prefix="/resumes", tags=["Resumes"])
logger = logging.getLogger(__name__)


def to_detail(resume: Resume) -> ResumeDetail:
    d = ResumeDetail.model_validate(resume)
    d.sections_detected = list(resume.sections.keys())
    return d


def _owned_resume(db: Session, user: User, resume_id: int) -> Resume:
    resume = db.scalar(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == user.id).options(
            selectinload(Resume.skills), selectinload(Resume.education), selectinload(Resume.experience),
            selectinload(Resume.projects), selectinload(Resume.certifications))
    )
    if resume is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Resume not found.")
    return resume


@router.post("/upload", response_model=ResumeDetail, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    processor: ResumeNLPProcessor = Depends(get_resume_processor),
):
    settings = get_settings()
    # Read in chunks so an oversized upload is rejected without loading it all into memory.
    chunks, size = [], 0
    while chunk := await file.read(1024 * 256):
        size += len(chunk)
        if size > settings.max_upload_bytes:
            raise FileTooLargeError(f"File is too large. Maximum size is {settings.max_upload_mb} MB.")
        chunks.append(chunk)
    data = b"".join(chunks)

    file_type = validate_upload(file.filename or "", file.content_type, data, settings.max_upload_bytes)
    doc = process_document(data, file_type)
    resume = create_resume(db, user.id, file.filename or "resume", file_type, data, doc, processor)
    return to_detail(resume)


@router.get("", response_model=list[ResumeSummary])
def list_resumes(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    counts = dict(db.execute(
        select(ResumeSkill.resume_id, func.count(ResumeSkill.id)).join(Resume).where(Resume.user_id == user.id)
        .group_by(ResumeSkill.resume_id)).all())
    resumes = db.scalars(select(Resume).where(Resume.user_id == user.id).order_by(Resume.created_at.desc())).all()
    return [
        ResumeSummary(
            id=r.id, original_filename=r.original_filename, file_type=r.file_type, page_count=r.page_count,
            word_count=r.word_count, quality_score=r.quality_score, created_at=r.created_at,
            skill_count=counts.get(r.id, 0), candidate_name=(r.personal_information or {}).get("name"),
        ) for r in resumes
    ]


@router.get("/{resume_id}", response_model=ResumeDetail)
def get_resume(resume_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return to_detail(_owned_resume(db, user, resume_id))


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(resume_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    resume = _owned_resume(db, user, resume_id)
    delete_resume_file(resume)
    db.delete(resume)
    db.commit()
