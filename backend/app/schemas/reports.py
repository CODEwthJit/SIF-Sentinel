"""
Pydantic Schemas for Report Entities
Phase 9.1 — SIH26165
"""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class ReportCreate(BaseModel):
    narrative: str = Field(
        ...,
        description="Safety / Incident report narrative text to be analyzed for SIF precursors.",
        examples=["An employee was working on a roof approximately 28 feet above ground when the scaffold collapsed and the employee fell."]
    )

    @field_validator("narrative")
    @classmethod
    def validate_narrative_not_empty(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("Narrative must be a string.")
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Narrative cannot be empty or whitespace-only.")
        return cleaned


class ReportOut(BaseModel):
    id: int
    narrative: str
    created_at: datetime

    model_config = {"from_attributes": True}
