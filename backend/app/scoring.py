from __future__ import annotations

import math
import re
from collections import defaultdict

from .knowledge_base import COMPANIES, INDUSTRIES, POSITIVE_POLICY_TERMS, RISK_POLICY_TERMS
from .models import CompanyScore, IndustryScore, PolicyDocument


def count_terms(text: str, terms: list[str]) -> int:
    lower = text.lower()
    return sum(len(re.findall(rf"\b{re.escape(term.lower())}\b", lower)) for term in terms)


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def score_industries(policies: list[PolicyDocument]) -> list[IndustryScore]:
    results: list[IndustryScore] = []
    for industry in INDUSTRIES:
        evidence: list[PolicyDocument] = []
        positive = 0
        risk = 0
        keyword_hits = 0
        for policy in policies:
            text = f"{policy.title} {policy.summary} {policy.content}"
            hits = count_terms(text, industry["keywords"])
            if hits:
                evidence.append(policy)
                keyword_hits += hits
                positive += count_terms(text, POSITIVE_POLICY_TERMS)
                risk += count_terms(text, RISK_POLICY_TERMS)

        policy_count = len(evidence)
        source_diversity = len({p.source for p in evidence})
        implementation_bonus = sum(8 for p in evidence if p.source == "Federal Register")
        white_house_bonus = sum(6 for p in evidence if p.source == "White House")
        momentum = clamp((policy_count * 14) + (keyword_hits * 3) + (source_diversity * 8))
        score = clamp(
            momentum * 0.38
            + implementation_bonus
            + white_house_bonus
            + positive * 4
            - risk * 3
        )
        drivers = [p.title for p in sorted(evidence, key=lambda d: d.published_date, reverse=True)[:3]]
        results.append(
            IndustryScore(
                code=industry["code"],
                name=industry["name"],
                score=round(score, 2),
                momentum=round(momentum, 2),
                policy_count=policy_count,
                positive_signals=positive,
                risk_signals=risk,
                key_drivers=drivers,
                evidence_policy_ids=[p.id for p in evidence[:5]],
            )
        )
    return sorted(results, key=lambda item: item.score, reverse=True)


def rating(score: float) -> str:
    if score >= 85:
        return "高度潛力"
    if score >= 70:
        return "值得追蹤"
    if score >= 55:
        return "觀察名單"
    return "政策連動較弱"


def score_companies(
    policies: list[PolicyDocument],
    industries: list[IndustryScore],
) -> list[CompanyScore]:
    industry_map = {item.code: item for item in industries}
    policy_text_by_industry: dict[str, list[PolicyDocument]] = defaultdict(list)
    for policy in policies:
        text = f"{policy.title} {policy.summary} {policy.content}"
        for industry in INDUSTRIES:
            if count_terms(text, industry["keywords"]):
                policy_text_by_industry[industry["code"]].append(policy)

    results: list[CompanyScore] = []
    for company in COMPANIES:
        industry = industry_map[company["industry_code"]]
        docs = policy_text_by_industry.get(company["industry_code"], [])
        company_hits = 0
        evidence: list[str] = []
        for policy in docs:
            text = f"{policy.title} {policy.summary} {policy.content}"
            hits = count_terms(text, company["keywords"])
            company_hits += hits
            if hits and len(evidence) < 3:
                evidence.append(policy.title)

        relevance = clamp(45 + company_hits * 9)
        policy_strength = industry.score
        breadth_bonus = clamp(math.log1p(len(docs)) * 12, 0, 20)
        score = clamp(policy_strength * 0.52 + relevance * 0.32 + breadth_bonus - company["risk"] * 0.45)
        thesis = (
            f"{company['name']} 與「{industry.name}」政策主題高度相關；"
            f"目前政策動能 {industry.momentum:.0f}，相關政策 {industry.policy_count} 件。"
        )
        results.append(
            CompanyScore(
                ticker=company["ticker"],
                name=company["name"],
                exchange=company["exchange"],
                industry_code=company["industry_code"],
                industry_name=industry.name,
                score=round(score, 2),
                rating=rating(score),
                thesis=thesis,
                evidence=evidence or industry.key_drivers[:2],
            )
        )
    return sorted(results, key=lambda item: item.score, reverse=True)
