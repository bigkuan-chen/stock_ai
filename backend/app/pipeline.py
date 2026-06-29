from __future__ import annotations

from .crawler import crawl_all
from .models import today_iso
from .scoring import score_companies, score_industries
from .storage import load_state, save_state


def run_analysis(lookback_days: int = 30, offline: bool = False) -> dict:
    policies = crawl_all(lookback_days=lookback_days, offline=offline)
    industries = score_industries(policies)
    companies = score_companies(policies, industries)
    state = {
        "updated_at": today_iso(),
        "lookback_days": lookback_days,
        "policies": [item.to_dict() for item in policies],
        "industries": [item.to_dict() for item in industries],
        "companies": [item.to_dict() for item in companies],
    }
    save_state(state)
    return state


def get_or_create_state() -> dict:
    state = load_state()
    if state.get("policies"):
        return state
    return run_analysis(lookback_days=30, offline=False)
