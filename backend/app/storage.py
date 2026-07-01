from __future__ import annotations

import json
import re
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any

from .config import DATA_DIR, DEFAULT_COMPANIES, DEFAULT_INDUSTRIES, DEFAULT_LOOKBACK_DAYS, DEFAULT_POLICIES


DATA_FILE = DATA_DIR / "state.json"


def _backup_path(updated_at: str | None) -> Path:
    backup_date = updated_at or "unknown"
    backup_date = re.sub(r"[^0-9A-Za-z_-]+", "-", backup_date).strip("-") or "unknown"
    candidate = DATA_FILE.with_name(f"state-{backup_date}.json")
    index = 1
    while candidate.exists():
        candidate = DATA_FILE.with_name(f"state-{backup_date}-{index}.json")
        index += 1
    return candidate


def backup_state() -> Path | None:
    if not DATA_FILE.exists():
        return None
    try:
        current_state = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        current_state = {}
    target = _backup_path(current_state.get("updated_at"))
    shutil.copy2(DATA_FILE, target)
    return target


def _merge_company_items(companies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    related: dict[str, set[str]] = {}

    for item in companies:
        key = item.get("ticker") or item.get("name")
        if not key:
            continue
        key = str(key).strip().upper()
        existing = merged.get(key)
        if existing is None:
            existing = dict(item)
            merged[key] = existing
            related[key] = set(existing.get("related_industries") or [])
        else:
            if item.get("score", 0) > existing.get("score", 0):
                existing.update({
                    "score": item.get("score"),
                    "rating": item.get("rating"),
                    "industry_code": item.get("industry_code"),
                    "industry_name": item.get("industry_name"),
                })

            existing["evidence"] = list(dict.fromkeys([
                *existing.get("evidence", []),
                *item.get("evidence", []),
            ]))[:5]

        industry_name = item.get("industry_name")
        if industry_name:
            related[key].add(industry_name)
        for name in item.get("related_industries") or []:
            related[key].add(name)

    for key, item in merged.items():
        industries = sorted(related.get(key, set()))
        item["related_industries"] = industries
        if industries:
            item["thesis"] = (
                f"{item.get('name', item.get('ticker', 'Company'))} was generated from policy mentions. "
                f"Related policy industries: {', '.join(industries)}."
            )

    return sorted(merged.values(), key=lambda item: item.get("score", 0), reverse=True)


def normalize_state(state: dict[str, Any]) -> dict[str, Any]:
    if isinstance(state.get("companies"), list):
        state["companies"] = _merge_company_items(state["companies"])
    return state


def load_state() -> dict[str, Any]:
    if not DATA_FILE.exists():
        return {
            "policies": deepcopy(DEFAULT_POLICIES),
            "industries": deepcopy(DEFAULT_INDUSTRIES),
            "companies": deepcopy(DEFAULT_COMPANIES),
            "lookback_days": DEFAULT_LOOKBACK_DAYS,
            "updated_at": None,
        }
    state = normalize_state(json.loads(DATA_FILE.read_text(encoding="utf-8")))
    state["lookback_days"] = DEFAULT_LOOKBACK_DAYS
    return state


def save_state(state: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    backup_state()
    state = normalize_state(state)
    DATA_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
