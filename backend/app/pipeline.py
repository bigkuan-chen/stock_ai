from __future__ import annotations

import datetime
from zoneinfo import ZoneInfo
from django.db import transaction

from .config import DEFAULT_LOOKBACK_DAYS
from .crawler import crawl_all
from .models import AnalysisLog, News, Company, Industry
from .scoring import score_companies, score_industries
from .schemas import today_iso

TAIPEI_TZ = ZoneInfo("Asia/Taipei")


def run_analysis(lookback_days: int = DEFAULT_LOOKBACK_DAYS, offline: bool = False) -> dict:
    # 1. Run crawler and scoring logic
    policies = crawl_all(lookback_days=lookback_days, offline=offline)
    industries = score_industries(policies)
    companies = score_companies(policies, industries)

    run_at_str = datetime.datetime.now(TAIPEI_TZ).strftime("%Y-%m-%d %H:%M:%S")

    # 2. Persist to DB using Django ORM
    with transaction.atomic():
        analysis = AnalysisLog.objects.create(
            run_at=run_at_str,
            lookback_days=lookback_days
        )

        # Save News (Policy Documents)
        news_objs = [
            News(
                analysis=analysis,
                news_id=item.id,
                source=item.source,
                title=item.title,
                url=item.url,
                published_date=item.published_date,
                document_type=item.document_type,
                summary=item.summary,
                content=item.content,
                agencies=", ".join(item.agencies),
                run_at=run_at_str
            )
            for item in policies
        ]
        News.objects.bulk_create(news_objs)

        # Save Industries
        industry_objs = [
            Industry(
                analysis=analysis,
                code=item.code,
                name=item.name,
                score=item.score,
                momentum=item.momentum,
                policy_count=item.policy_count,
                positive_signals=item.positive_signals,
                risk_signals=item.risk_signals,
                key_drivers=", ".join(item.key_drivers),
                evidence_policy_ids=", ".join(item.evidence_policy_ids)
            )
            for item in industries
        ]
        Industry.objects.bulk_create(industry_objs)

        # Save Companies
        company_objs = [
            Company(
                analysis=analysis,
                ticker=item.ticker,
                name=item.name,
                exchange=item.exchange,
                industry_code=item.industry_code,
                industry_name=item.industry_name,
                score=item.score,
                rating=item.rating,
                thesis=item.thesis,
                evidence=", ".join(item.evidence),
                sector=item.sector,
                stock_industry=item.stock_industry,
                related_industries=", ".join(item.related_industries),
                run_at=run_at_str
            )
            for item in companies
        ]
        Company.objects.bulk_create(company_objs)

    return {
        "status": "ok",
        "policies": len(policies),
        "industries": len(industries),
        "companies": len(companies),
        "ana_id": analysis.ana_id,
        "run_at": run_at_str,
    }


def get_latest_state() -> dict:
    try:
        latest_analysis = AnalysisLog.objects.latest('ana_id')
    except AnalysisLog.DoesNotExist:
        # If no analysis exists, run a quick one offline to bootstrap
        res = run_analysis(lookback_days=DEFAULT_LOOKBACK_DAYS, offline=True)
        latest_analysis = AnalysisLog.objects.get(ana_id=res["ana_id"])

    policies = []
    for item in latest_analysis.news.all():
        policies.append({
            "id": item.news_id,
            "source": item.source,
            "title": item.title,
            "url": item.url,
            "published_date": item.published_date,
            "document_type": item.document_type,
            "summary": item.summary,
            "content": item.content,
            "agencies": [a.strip() for a in item.agencies.split(",") if a.strip()]
        })

    industries = []
    for item in latest_analysis.industries.all().order_by('-score'):
        industries.append({
            "code": item.code,
            "name": item.name,
            "score": item.score,
            "momentum": item.momentum,
            "policy_count": item.policy_count,
            "positive_signals": item.positive_signals,
            "risk_signals": item.risk_signals,
            "key_drivers": [d.strip() for d in item.key_drivers.split(",") if d.strip()],
            "evidence_policy_ids": [pid.strip() for pid in item.evidence_policy_ids.split(",") if pid.strip()]
        })

    companies = []
    for item in latest_analysis.companies.all().order_by('-score'):
        companies.append({
            "ticker": item.ticker,
            "name": item.name,
            "exchange": item.exchange,
            "industry_code": item.industry_code,
            "industry_name": item.industry_name,
            "score": item.score,
            "rating": item.rating,
            "thesis": item.thesis,
            "evidence": [e.strip() for e in item.evidence.split(",") if e.strip()],
            "sector": item.sector,
            "stock_industry": item.stock_industry,
            "related_industries": [ri.strip() for ri in item.related_industries.split(",") if ri.strip()]
        })

    return {
        "updated_at": latest_analysis.run_at,
        "lookback_days": latest_analysis.lookback_days,
        "policies": policies,
        "industries": industries,
        "companies": companies,
    }
