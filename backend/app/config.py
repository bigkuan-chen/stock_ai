from __future__ import annotations

import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT_DIR / "frontend"
DATA_DIR = ROOT_DIR / "backend" / "data"

WHITE_HOUSE_BASE_URL = os.getenv("WHITE_HOUSE_BASE_URL", "https://www.whitehouse.gov")
FEDERAL_REGISTER_API_BASE_URL = os.getenv(
    "FEDERAL_REGISTER_API_BASE_URL",
    "https://www.federalregister.gov/api/v1",
)
REQUEST_TIMEOUT_SECONDS = int(os.getenv("CRAWL_REQUEST_TIMEOUT_SECONDS", "20"))
USER_AGENT = os.getenv("CRAWL_USER_AGENT", "PolicyResearchBot/1.0")
