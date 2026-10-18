"""Orchestrates one resume-vs-job analysis and stores the result."""
import logging

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Analysis, JobDescription, Recommendation, Resume
from app.services.embedding_service import EmbeddingService
from app.services.matching_service import full_match
from app.services.quality_analyzer import analyze_quality
from app.services.recommendation_engine import generate_recommendations
from app.services.resume_service import resume_to_profile

logger = logging.getLogger(__name__)


def run_analysis(db: Session, user_id: int, resume: Resume, job: JobDescription,
                 embedder: EmbeddingService) -> Analysis:
    settings = get_settings()
    model_name = settings.embedding_model_name
    profile = resume_to_profile(resume)

    match = full_match(resume, job, profile, embedder, settings.coverage_threshold, model_name)

    # Quality analysis again, now aware of the job's missing required skills.
    quality = analyze_quality(profile, resume.raw_text, resume.page_count,
                              missing_required_skills=match["skills"]["skill_gaps"]["critical"])
    recs = generate_recommendations(profile, job.analysis, match, quality)

    updates = match["semantic"].pop("cache_updates")
    if "resume" in updates:
        resume.embeddings = updates["resume"]
    if "job" in updates:
        job.embedding = updates["job"]
        job.analysis = {**job.analysis, "_embedding_model": model_name}

    details = {
        "skills": match["skills"],
        "semantic": match["semantic"],
        "experience": match["experience"],
        "education": match["education"],
        "quality": quality,
        "component_scores": match["component_scores"],
        "weights": match["weights"],
        "score_explanation": (
            "Resume-Job Match Score = 40% skills + 30% semantic similarity + 15% experience relevance "
            "+ 10% education relevance + 5% resume structure. It is not a hiring probability."
        ),
    }
    analysis = Analysis(
        user_id=user_id, resume_id=resume.id, job_id=job.id,
        semantic_similarity=match["semantic"]["semantic_similarity"],
        skills_score=match["skills"]["skills_score"],
        semantic_score=match["semantic"]["semantic_score"],
        experience_score=match["experience"]["experience_score"],
        education_score=match["education"]["education_score"],
        structure_score=match["structure_score"],
        overall_score=match["overall_score"],
        quality_score=quality["quality_score"],
        details=details,
    )
    analysis.recommendations = [Recommendation(**r) for r in recs]
    try:
        db.add(analysis)
        db.add(resume)
        db.add(job)
        db.commit()
        db.refresh(analysis)
    except Exception:
        db.rollback()
        raise
    logger.info("Analysis %s stored (overall %.1f)", analysis.id, analysis.overall_score)
    return analysis
