from __future__ import annotations

from typing import Any


US_EXCHANGE_CODES = {
    "ASE",
    "BATS",
    "NAS",
    "NCM",
    "NGM",
    "NMS",
    "NYQ",
    "PCX",
}

US_EXCHANGE_NAMES = {
    "NASDAQ",
    "NYSE",
    "NYSE AMERICAN",
    "NYSE ARCA",
    "CBOE BZX",
}


def normalize_exchange(value: Any) -> str:
    return str(value or "").strip().upper()


def is_us_listed_equity(symbol: str, exchange: str, exchange_display: str = "") -> bool:
    symbol = str(symbol or "").strip().upper()
    if not symbol:
        return False
    if "." in symbol:
        return False

    exchange_code = normalize_exchange(exchange)
    exchange_name = normalize_exchange(exchange_display)
    if exchange_code in US_EXCHANGE_CODES:
        return True
    return exchange_name in US_EXCHANGE_NAMES

