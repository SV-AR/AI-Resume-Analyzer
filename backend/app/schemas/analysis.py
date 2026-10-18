from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class MatchRequest(BaseModel):
    resume_id: int
    job_id: int


class RecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    category: str
    priority: str
    title: str
    message: str
    reason: str


class AnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    resume_id: int
    job_id: int
    created_at: datetime
    resume_name: str = ""
    job_title: str = ""
    # Semantic similarity = raw cosine similarity (0..1); NOT a probability of being hired.
    semantic_similarity: float
    overall_score: float
    quality_score: float
    component_scores: dict[str, float] = {}
    weights: dict[str, float] = {}
    details: dict[str, Any]
    recommendations: list[RecommendationOut]
    disclaimer: str = (
        "The match score reflects semantic similarity and skill overlap between this resume and this job "
        "description. It is not a prediction of hiring probability or ATS ranking."
    )


class AnalysisSummary(BaseModel):
    id: int
    resume_id: int
    job_id: int
    resume_name: str
    job_title: str
    overall_score: float
    semantic_similarity: float
    quality_score: float
    created_at: datetime
