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
    member_ids: list[uuid.UUID] | None = Field(None, max_length=20)

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


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    relation: str
    full_name: str
    date_of_birth: date | None


class NomineeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    family_member_id: uuid.UUID | None
    full_name: str
    relation: str
    share_percent: int
    date_of_birth: date | None
    phone: str | None
    appointee_name: str | None


class NomineeIn(BaseModel):
    family_member_id: uuid.UUID | None = None
    full_name: str = Field(min_length=1, max_length=120)
    relation: Literal["spouse", "child", "parent", "sibling", "other"]
    share_percent: int = Field(ge=1, le=100)
    date_of_birth: date | None = None
    phone: str | None = Field(None, max_length=20)
    appointee_name: str | None = Field(None, max_length=120)


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
    renewal_status: Literal["pending", "renewed", "not_renewing"]
    members: list[MemberOut]
    nominees: list[NomineeOut]
    created_at: datetime
    updated_at: datetime


class SummaryOut(BaseModel):
    headline: str
    key_points: list[str]
    watch_outs: list[str]
    disclaimer: str
    provider: str | None = None


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class Citation(BaseModel):
    page: int | None
    section: str | None
    excerpt: str


class RelatedClause(BaseModel):
    type: str
    title: str
    text: str
    page: int | None


class AnswerOut(BaseModel):
    id: uuid.UUID
    question: str
    answer: str
    answerable: bool
    confidence: Literal["high", "medium", "low"]
    citations: list[Citation]
    disclaimer: str
    provider: str | None = None
    related_clauses: list[RelatedClause] = []
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


class RenewalUpdate(BaseModel):
    renewal_status: Literal["pending", "renewed", "not_renewing"]


class HealthFinding(BaseModel):
    key: str
    label: str
    grade: Literal["strong", "attention", "not_covered"]
    detail: str


class HealthCheckOut(BaseModel):
    available: bool
    score: int | None
    strong: list[HealthFinding]
    attention: list[HealthFinding]
    not_covered: list[HealthFinding]
    not_mentioned: list[str]
    disclaimer: str


class ClauseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clause_type: str
    tags: list[str]
    title: str
    text: str
    page: int | None
    section: str | None


class InsightOut(BaseModel):
    id: str
    severity: Literal["high", "medium", "info"]
    category: str
    title: str
    detail: str
    action_label: str | None
    action_link: str | None
    policy_id: str | None


class InsightsOut(BaseModel):
    insights: list[InsightOut]
    disclaimer: str


class CompareRow(BaseModel):
    section: str
    label: str
    values: list[str | int | float | None]
    best_index: int | None


class CompareOut(BaseModel):
    policy_type: str
    policies: list[dict]
    rows: list[CompareRow]
    disclaimer: str
