from datetime import datetime
from typing import Literal

from pydantic import BaseModel

StatusLit = Literal["good", "limited", "missing", "info", "unknown"]
RatingLit = Literal["strong", "fair", "weak"]


class CoverageRowOut(BaseModel):
    key: str
    label: str
    status: StatusLit
    value: str
    why: str
    detail: str | None
    page: int | None
    source: Literal["document", "clause", "none"]


class CoverageSectionOut(BaseModel):
    key: str
    title: str
    subtitle: str
    rating: RatingLit | None
    items: list[CoverageRowOut]


class ScenarioOut(BaseModel):
    question: str
    item_key: str
    art: str
    status: StatusLit
    answer: str


class CoverageReportOut(BaseModel):
    available: bool
    policy_type: str
    demo: bool
    title: str | None = None
    rating: RatingLit | None
    scenarios: list[ScenarioOut]
    sections: list[CoverageSectionOut]
    counts: dict[str, int]
    note: str | None
    disclaimer: str


class RewardTaskOut(BaseModel):
    kind: str
    title: str
    coins: int
    route: str
    done: bool
    progress: str | None


class RewardHistoryOut(BaseModel):
    title: str
    coins: int
    created_at: datetime


class PerkOut(BaseModel):
    key: str
    title: str
    icon: str


class RewardsOut(BaseModel):
    balance: int
    tasks: list[RewardTaskOut]
    history: list[RewardHistoryOut]
    perks: list[PerkOut]
    note: str
