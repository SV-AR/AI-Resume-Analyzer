from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models import Analysis, JobDescription, Resume, User

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Aggregated numbers for the dashboard in a handful of queries."""
    resume_count = db.scalar(select(func.count(Resume.id)).where(Resume.user_id == user.id)) or 0
    job_count = db.scalar(select(func.count(JobDescription.id)).where(JobDescription.user_id == user.id)) or 0
    analyses = db.scalars(select(Analysis).where(Analysis.user_id == user.id).order_by(Analysis.created_at.desc())
                          .options(selectinload(Analysis.resume), selectinload(Analysis.job))).all()
    latest_resume = db.scalar(select(Resume).where(Resume.user_id == user.id).order_by(Resume.created_at.desc())
                              .options(selectinload(Resume.skills)))

    missing_counter: Counter = Counter()
    for a in analyses:
        missing_counter.update(a.details.get("skills", {}).get("missing_skills", []))

    latest = analyses[0] if analyses else None
    category_counts = Counter(s.category for s in latest_resume.skills) if latest_resume else Counter()
    return {
        "counts": {"resumes": resume_count, "jobs": job_count, "analyses": len(analyses)},
        "latest_resume": None if not latest_resume else {
            "id": latest_resume.id, "name": latest_resume.original_filename,
            "quality_score": latest_resume.quality_score, "skill_count": len(latest_resume.skills)},
        "latest_analysis": None if not latest else {
            "id": latest.id, "job_title": latest.job.title, "resume_name": latest.resume.original_filename,
            "overall_score": latest.overall_score, "semantic_similarity": latest.semantic_similarity,
            "quality_score": latest.quality_score, "component_scores": latest.details.get("component_scores", {}),
            "matched_skills": latest.details.get("skills", {}).get("matched_skills", []),
            "missing_skills": latest.details.get("skills", {}).get("missing_skills", []),
            "additional_skills": latest.details.get("skills", {}).get("additional_skills", []),
            "skill_gaps": latest.details.get("skills", {}).get("skill_gaps", {}),
            "issues": latest.details.get("quality", {}).get("issues", []),
            "recommendation_count": len(latest.recommendations),
        },
        "skills_by_category": [{"category": k, "count": v} for k, v in category_counts.most_common()],
        "top_missing_skills": [{"skill": k, "count": v} for k, v in missing_counter.most_common(8)],
        "history": [{"id": a.id, "job_title": a.job.title, "resume_name": a.resume.original_filename,
                     "overall_score": a.overall_score, "semantic_similarity": a.semantic_similarity,
                     "created_at": a.created_at.isoformat()} for a in reversed(analyses[:20])],
        "disclaimer": "Scores describe resume-job similarity and are not hiring probabilities.",
    }
