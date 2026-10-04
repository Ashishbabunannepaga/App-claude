import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

PolicyTypeLit = Literal["health", "life", "motor", "other"]
FrequencyLit = Literal["annual", "half_yearly", "quarterly", "monthly", "single"]


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    error_code: str | None
    original_filename: str | None
    content_type: str
    size_bytes: int
    page_count: int | None
    extraction_method: str | None
    policy_id: uuid.UUID | None = None
    created_at: datetime


class SignedUrlOut(BaseModel):
    url: str
    expires_in: int


class PolicyFields(BaseModel):
    policy_type: PolicyTypeLit | None = None
    insurer: str | None = Field(None, max_length=120)
    plan_name: str | None = Field(None, max_length=200)
    policy_number: str | None = Field(None, max_length=80)
    start_date: date | None = None
    end_date: date | None = None
    premium: Decimal | None = Field(None, ge=0, max_digits=14, decimal_places=2)
    sum_insured: Decimal | None = Field(None, ge=0, max_digits=16, decimal_places=2)
    payment_frequency: FrequencyLit | None = None
    details: dict | None = None

    @model_validator(mode="after")
    def _dates(self) -> "PolicyFields":
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        return self


class PolicyCreate(PolicyFields):
    policy_type: PolicyTypeLit
    insurer: str = Field(min_length=1, max_length=120)


class PolicyUpdate(PolicyFields):
    pass


class PolicyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID | None
    policy_type: str
    insurer: str | None
    plan_name: str | None
    policy_number: str | None
    start_date: date | None
    end_date: date | None
    premium: Decimal | None
    sum_insured: Decimal | None
    payment_frequency: str | None
    verified: bool
    source: str
    extraction_confidence: float | None
    field_confidence: dict
    details: dict
    status: Literal["active", "expiring_soon", "expired", "unknown"]
    days_to_expiry: int | None
    created_at: datetime
    updated_at: datetime


class SummaryOut(BaseModel):
    headline: str
    key_points: list[str]
    watch_outs: list[str]
    disclaimer: str


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class Citation(BaseModel):
    page: int | None
    section: str | None
    excerpt: str


class AnswerOut(BaseModel):
    id: uuid.UUID
    question: str
    answer: str
    answerable: bool
    confidence: Literal["high", "medium", "low"]
    citations: list[Citation]
    disclaimer: str
    created_at: datetime


class RenewalItem(BaseModel):
    policy_id: uuid.UUID
    policy_type: str
    insurer: str | None
    end_date: date
    days_to_expiry: int


class PortfolioSummary(BaseModel):
    total_policies: int
    active_policies: int
    expiring_soon: int
    pending_verification: int
    total_annual_premium: Decimal
    health_cover: Decimal
    life_cover: Decimal
    by_type: dict[str, int]
    upcoming_renewals: list[RenewalItem]
