from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import DATA_DIR


DATA_FILE = DATA_DIR / "state.json"


def load_state() -> dict[str, Any]:
    if not DATA_FILE.exists():
        return {"policies": [], "industries": [], "companies": [], "updated_at": None}
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def save_state(state: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
