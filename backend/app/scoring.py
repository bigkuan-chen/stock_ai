from __future__ import annotations

import math
import re
from collections import defaultdict

from .config import YFINANCE_LOOKUP_LIMIT
from .knowledge_base import INDUSTRIES, POSITIVE_POLICY_TERMS, RISK_POLICY_TERMS
from .market_data import lookup_stock_profile
from .schemas import CompanyScore, IndustryScore, PolicyDocument


POLICY_STOCK_FALLBACKS = {
    "defense_aerospace_military": ("Industrials", "Aerospace & Defense"),
    "ai_datacenter_power": ("Technology", "AI, Data Centers & Power Infrastructure"),
    "semiconductors": ("Technology", "Semiconductors"),
    "critical_minerals_rare_earth": ("Basic Materials", "Other Industrial Metals & Minerals"),
    "nuclear_uranium_smr": ("Utilities", "Nuclear Utilities"),
    "traditional_energy_lng_oil": ("Energy", "Oil & Gas Integration"),
    "ev_battery_charging": ("Consumer Cyclical", "Auto Manufacturers"),
    "pharma_reshoring": ("Healthcare", "Drug Manufacturers"),
}


def stock_classification_with_fallback(
    sector: str,
    stock_industry: str,
    industry_code: str,
    industry_name: str,
) -> tuple[str, str]:
    fallback_sector, fallback_industry = POLICY_STOCK_FALLBACKS.get(
        industry_code,
        ("N/A", industry_name),
    )
    if not sector or sector == "N/A":
        sector = fallback_sector
    if not stock_industry or stock_industry == "N/A":
        stock_industry = fallback_industry
    return sector, stock_industry


def count_terms(text: str, terms: list[str]) -> int:
    lower = text.lower()
    return sum(len(re.findall(rf"\b{re.escape(term.lower())}\b", lower)) for term in terms)


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def policy_text(policy: PolicyDocument) -> str:
    return f"{policy.title} {policy.summary} {policy.content}"


def score_industries(policies: list[PolicyDocument]) -> list[IndustryScore]:
    results: list[IndustryScore] = []
    for industry in INDUSTRIES:
        evidence: list[PolicyDocument] = []
        positive = 0
        risk = 0
        keyword_hits = 0
        for policy in policies:
            text = policy_text(policy)
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
        return "strong"
    if score >= 70:
        return "positive"
    if score >= 55:
        return "watch"
    return "low"


def generated_ticker(name: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", name.upper())
    if not words:
        return "N/A"
    if len(words) == 1:
        return words[0][:8]
    return "".join(word[0] for word in words)[:8]


def extract_company_mentions(text: str) -> list[str]:
    suffixes = (
        "Inc",
        "Incorporated",
        "Corporation",
        "Corp",
        "Company",
        "Co",
        "LLC",
        "Ltd",
        "Limited",
        "PLC",
        "Holdings",
        "Group",
        "Technologies",
        "Systems",
        "Energy",
        "Aerospace",
        "Pharmaceuticals",
        "Biotech",
        "Semiconductor",
        "Manufacturing",
    )
    suffix_pattern = "|".join(re.escape(suffix) for suffix in suffixes)
    pattern = re.compile(
        rf"\b([A-Z][A-Za-z0-9&.,'-]*(?:\s+[A-Z][A-Za-z0-9&.,'-]*){{0,6}}\s+"
        rf"(?:{suffix_pattern})\.?)\b"
    )
    names: list[str] = []
    seen: set[str] = set()
    for match in pattern.finditer(text):
        name = re.sub(r"\s+", " ", match.group(1)).strip(" ,.;:")
        key = name.lower()
        if key not in seen:
            names.append(name)
            seen.add(key)
    return names


def policies_by_industry(policies: list[PolicyDocument]) -> dict[str, list[PolicyDocument]]:
    grouped: dict[str, list[PolicyDocument]] = defaultdict(list)
    for policy in policies:
        text = policy_text(policy)
        for industry in INDUSTRIES:
            if count_terms(text, industry["keywords"]):
                grouped[industry["code"]].append(policy)
    return grouped


def merge_company_results(results: list[CompanyScore]) -> list[CompanyScore]:
    merged: dict[str, CompanyScore] = {}
    related: dict[str, set[str]] = defaultdict(set)

    for item in results:
        existing = merged.get(item.ticker)
        related[item.ticker].add(item.industry_name)
        if existing is None:
            merged[item.ticker] = item
            continue

        existing.evidence = list(dict.fromkeys([*existing.evidence, *item.evidence]))[:5]
        if item.score > existing.score:
            existing.score = item.score
            existing.rating = item.rating
            existing.industry_code = item.industry_code
            existing.industry_name = item.industry_name

    for ticker, item in merged.items():
        item.related_industries = sorted(related[ticker])
        industries = ", ".join(item.related_industries)
        item.thesis = (
            f"{item.name} was generated from policy mentions. "
            f"Related policy industries: {industries}."
        )

    return sorted(merged.values(), key=lambda item: item.score, reverse=True)


def score_companies(
    policies: list[PolicyDocument],
    industries: list[IndustryScore],
) -> list[CompanyScore]:
    grouped = policies_by_industry(policies)
    candidates: list[tuple[float, str, IndustryScore, list[PolicyDocument]]] = []

    for industry in industries:
        docs = grouped.get(industry.code, [])
        company_evidence: dict[str, list[PolicyDocument]] = defaultdict(list)
        for policy in docs:
            for company_name in extract_company_mentions(policy_text(policy)):
                company_evidence[company_name].append(policy)

        for company_name, evidence_docs in company_evidence.items():
            company_hits = len(evidence_docs)
            relevance = clamp(40 + company_hits * 12)
            breadth_bonus = clamp(math.log1p(company_hits) * 12, 0, 20)
            score = clamp(industry.score * 0.6 + relevance * 0.3 + breadth_bonus)
            candidates.append((score, company_name, industry, evidence_docs))

    candidates.sort(key=lambda item: item[0], reverse=True)
    results: list[CompanyScore] = []
    for index, (score, company_name, industry, evidence_docs) in enumerate(candidates):
        if YFINANCE_LOOKUP_LIMIT > 0 and index >= YFINANCE_LOOKUP_LIMIT:
            break
        stock = lookup_stock_profile(company_name)
        subsidiary_trigger = None

        if stock.ticker == "N/A":
            from .models import SubsidiaryMapping
            from .market_data import find_parent_company_via_wikidata

            normalized_name = company_name.lower().strip()
            db_mapping = SubsidiaryMapping.objects.filter(subsidiary_name=normalized_name).first()

            if db_mapping:
                parent_name = db_mapping.parent_company_name
                parent_stock = lookup_stock_profile(parent_name)
                if parent_stock.ticker != "N/A":
                    stock = parent_stock
                    subsidiary_trigger = company_name
            else:
                parent_name = find_parent_company_via_wikidata(company_name)
                if parent_name:
                    parent_stock = lookup_stock_profile(parent_name)
                    if parent_stock.ticker != "N/A":
                        stock = parent_stock
                        subsidiary_trigger = company_name
                        try:
                            SubsidiaryMapping.objects.create(
                                subsidiary_name=normalized_name,
                                parent_company_name=parent_name
                            )
                        except Exception:
                            pass

        if stock.ticker == "N/A":
            continue

        if subsidiary_trigger:
            thesis = (
                f"{stock.name} (via subsidiary {subsidiary_trigger}) was generated from policy mentions in the "
                f"{industry.name} industry. It appeared in {len(evidence_docs)} related policy item(s)."
            )
        else:
            thesis = (
                f"{stock.name} was generated from policy mentions in the "
                f"{industry.name} industry. It appeared in {len(evidence_docs)} related policy item(s)."
            )
        sector, stock_industry = stock_classification_with_fallback(
            stock.sector,
            stock.industry,
            industry.code,
            industry.name,
        )
        results.append(
            CompanyScore(
                ticker=stock.ticker,
                name=stock.name,
                exchange=stock.exchange,
                industry_code=industry.code,
                industry_name=industry.name,
                score=round(score, 2),
                rating=rating(score),
                thesis=thesis,
                evidence=[policy.title for policy in evidence_docs[:3]],
                sector=sector,
                stock_industry=stock_industry,
                related_industries=[industry.name],
            )
        )

    return merge_company_results(results)
