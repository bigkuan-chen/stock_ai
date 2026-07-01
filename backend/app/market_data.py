from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from .config import YFINANCE_LOOKUP_ENABLED, YFINANCE_REQUEST_TIMEOUT_SECONDS


@dataclass(frozen=True)
class StockProfile:
    ticker: str
    exchange: str
    sector: str
    industry: str
    name: str


def empty_profile(name: str) -> StockProfile:
    return StockProfile(ticker="N/A", exchange="N/A", sector="N/A", industry="N/A", name=name)


def _import_yfinance() -> Any | None:
    try:
        import yfinance as yf
    except ImportError:
        return None
    return yf


def _best_quote(quotes: list[dict[str, Any]]) -> dict[str, Any] | None:
    for quote in quotes:
        if quote.get("quoteType") == "EQUITY" and quote.get("symbol"):
            return quote
    return None


@lru_cache(maxsize=1024)
def lookup_stock_profile(company_name: str) -> StockProfile:
    if not YFINANCE_LOOKUP_ENABLED:
        return empty_profile(company_name)

    yf = _import_yfinance()
    if yf is None:
        return empty_profile(company_name)

    try:
        search = yf.Search(company_name, max_results=5, timeout=YFINANCE_REQUEST_TIMEOUT_SECONDS)
        quote = _best_quote(getattr(search, "quotes", []) or [])
        if not quote:
            return empty_profile(company_name)

        ticker = quote.get("symbol") or "N/A"
        quote_name = quote.get("longname") or quote.get("shortname") or company_name
        exchange = (
            quote.get("exchDisp")
            or quote.get("exchange")
            or "N/A"
        )
        return StockProfile(
            ticker=ticker,
            exchange=exchange,
            sector=quote.get("sectorDisp") or quote.get("sector") or "N/A",
            industry=quote.get("industryDisp") or quote.get("industry") or "N/A",
            name=quote_name,
        )
    except Exception:
        return empty_profile(company_name)
