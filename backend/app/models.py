from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any


@dataclass
class PolicyDocument:
    id: str
    source: str
    title: str
    url: str
    published_date: str
    document_type: str
    summary: str
    content: str
    agencies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IndustryScore:
    code: str
    name: str
    score: float
    momentum: float
    policy_count: int
    positive_signals: int
    risk_signals: int
    key_drivers: list[str]
    evidence_policy_ids: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CompanyScore:
    ticker: str
    name: str
    exchange: str
    industry_code: str
    industry_name: str
    score: float
    rating: str
    thesis: str
    evidence: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def today_iso() -> str:
    return date.today().isoformat()
