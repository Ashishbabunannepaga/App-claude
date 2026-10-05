import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Language = Literal["en", "hi", "mr", "ta", "te", "kn", "bn", "gu", "ml"]


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    phone: str | None
    email: str | None
    full_name: str | None
    date_of_birth: date | None
    city: str | None
    state: str | None
    notify_renewals: bool
    notify_processing: bool
    preferred_language: str
    created_at: datetime
    deletion_requested_at: datetime | None


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=120)
    date_of_birth: date | None = None
    city: str | None = Field(None, max_length=80)
    state: str | None = Field(None, max_length=80)
    notify_renewals: bool | None = None
    notify_processing: bool | None = None
    preferred_language: Language | None = None
