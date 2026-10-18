from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class JobAnalyzeRequest(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)
    description: str = Field(min_length=50, max_length=20000)

    @field_validator("description")
    @classmethod
    def _enough_words(cls, v: str) -> str:
        if len(v.split()) < 10:
            raise ValueError("Job description must contain at least 10 words")
        return v.strip()


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    created_at: datetime
    raw_text: str
    analysis: dict[str, Any]


class JobSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    created_at: datetime
