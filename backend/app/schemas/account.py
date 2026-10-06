import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Relation = Literal["self", "spouse", "child", "parent", "other"]


class MemberIn(BaseModel):
    relation: Relation
    full_name: str = Field(min_length=1, max_length=120)
    date_of_birth: date | None = None


class MemberUpdate(BaseModel):
    relation: Relation | None = None
    full_name: str | None = Field(None, min_length=1, max_length=120)
    date_of_birth: date | None = None


class DeviceIn(BaseModel):
    token: str = Field(min_length=10, max_length=512)
    platform: Literal["android", "ios"]


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: str
    title: str
    body: str
    deep_link: str | None
    policy_id: uuid.UUID | None
    created_at: datetime
    read_at: datetime | None


class SupportIn(BaseModel):
    category: Literal["question", "problem", "feedback", "privacy", "grievance", "expert_review"]
    message: str = Field(min_length=5, max_length=4000)
