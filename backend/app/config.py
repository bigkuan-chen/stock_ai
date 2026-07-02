from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT_DIR / "frontend"
DATA_DIR = ROOT_DIR / "backend" / "data"
DB_DIR = ROOT_DIR / "db"
DB_FILE = DB_DIR / "stockai.db"


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ[key.strip()] = value.strip().strip('"').strip("'")


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        os.environ[name] = str(default)
        return default
    try:
        return int(value)
    except ValueError:
        os.environ[name] = str(default)
        return default


def _env_json_list(name: str) -> list[Any]:
    value = os.getenv(name)
    if not value:
        os.environ[name] = "[]"
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        os.environ[name] = "[]"
        return []
    if not isinstance(parsed, list):
        os.environ[name] = "[]"
        return []
    return parsed


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        os.environ[name] = "true" if default else "false"
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_csv(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if value is None:
        os.environ[name] = ",".join(default)
        return default
    items = [item.strip() for item in value.split(",") if item.strip()]
    if not items:
        os.environ[name] = ",".join(default)
        return default
    return items


_load_dotenv(ROOT_DIR / ".env")

WHITE_HOUSE_BASE_URL = os.getenv("WHITE_HOUSE_BASE_URL", "https://www.whitehouse.gov")
FEDERAL_REGISTER_API_BASE_URL = os.getenv(
    "FEDERAL_REGISTER_API_BASE_URL",
    "https://www.federalregister.gov/api/v1",
)
FEDERAL_REGISTER_DOCUMENT_TYPES = _env_csv("FEDERAL_REGISTER_DOCUMENT_TYPES", ["RULE", "PRESDOCU"])
DEFAULT_LOOKBACK_DAYS = _env_int("CRAWL_LOOKBACK_DAYS", 30)
DEFAULT_POLICIES = _env_json_list("DEFAULT_POLICIES")
DEFAULT_INDUSTRIES = _env_json_list("DEFAULT_INDUSTRIES")
DEFAULT_COMPANIES = _env_json_list("DEFAULT_COMPANIES")
TOP_INDUSTRIES_LIMIT = _env_int("TOP_INDUSTRIES_LIMIT", 5)
TOP_COMPANIES_LIMIT = _env_int("TOP_COMPANIES_LIMIT", 8)
RECENT_POLICIES_LIMIT = _env_int("RECENT_POLICIES_LIMIT", 10)
REQUEST_TIMEOUT_SECONDS = _env_int("CRAWL_REQUEST_TIMEOUT_SECONDS", 20)
USER_AGENT = os.getenv("CRAWL_USER_AGENT", "PolicyResearchBot/1.0")
YFINANCE_LOOKUP_ENABLED = _env_bool("YFINANCE_LOOKUP_ENABLED", True)
YFINANCE_LOOKUP_LIMIT = _env_int("YFINANCE_LOOKUP_LIMIT", 30)
YFINANCE_REQUEST_TIMEOUT_SECONDS = _env_int("YFINANCE_REQUEST_TIMEOUT_SECONDS", 5)
