from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from .config import YFINANCE_LOOKUP_ENABLED, YFINANCE_REQUEST_TIMEOUT_SECONDS
from .stock_filters import is_us_listed_equity


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
        symbol = quote.get("symbol")
        if (
            quote.get("quoteType") == "EQUITY"
            and symbol
            and is_us_listed_equity(
                symbol,
                quote.get("exchange", ""),
                quote.get("exchDisp", ""),
            )
        ):
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


def find_parent_company_via_wikidata(company_name: str) -> str | None:
    import urllib.request
    import urllib.parse
    import json

    try:
        # Step 1: Search Wikidata for the company entity
        query = urllib.parse.urlencode({
            "action": "wbsearchentities",
            "search": company_name,
            "language": "en",
            "format": "json"
        })
        url = f"https://www.wikidata.org/w/api.php?{query}"
        req = urllib.request.Request(url, headers={"User-Agent": "StockAIBot/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            results = data.get("search", [])
            if not results:
                return None
            entity_id = results[0]["id"]

        # Step 2: Get entity claims
        query2 = urllib.parse.urlencode({
            "action": "wbgetentities",
            "ids": entity_id,
            "languages": "en",
            "format": "json"
        })
        url2 = f"https://www.wikidata.org/w/api.php?{query2}"
        req2 = urllib.request.Request(url2, headers={"User-Agent": "StockAIBot/1.0"})
        with urllib.request.urlopen(req2, timeout=5) as response2:
            data2 = json.loads(response2.read().decode("utf-8"))
            entity = data2.get("entities", {}).get(entity_id, {})
            claims = entity.get("claims", {})
            
            # P749 is "parent organization"
            parent_claims = claims.get("P749", [])
            if not parent_claims:
                return None
                
            # Get all parent entity IDs
            parent_ids = []
            for claim in parent_claims:
                pid = claim.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id")
                if pid:
                    parent_ids.append(pid)

        if not parent_ids:
            return None

        # Step 3: Get parent names in bulk and check yfinance
        query3 = urllib.parse.urlencode({
            "action": "wbgetentities",
            "ids": "|".join(parent_ids),
            "languages": "en",
            "format": "json"
        })
        url3 = f"https://www.wikidata.org/w/api.php?{query3}"
        req3 = urllib.request.Request(url3, headers={"User-Agent": "StockAIBot/1.0"})
        with urllib.request.urlopen(req3, timeout=5) as response3:
            data3 = json.loads(response3.read().decode("utf-8"))
            entities = data3.get("entities", {})
            
            for pid in parent_ids:
                parent_entity = entities.get(pid, {})
                parent_name = parent_entity.get("labels", {}).get("en", {}).get("value")
                if parent_name:
                    # Check if this parent has a listed ticker
                    profile = lookup_stock_profile(parent_name)
                    if profile.ticker != "N/A":
                        return parent_name
            
            # Fallback to the first parent organization if none are listed
            fallback_entity = entities.get(parent_ids[0], {})
            return fallback_entity.get("labels", {}).get("en", {}).get("value")
    except Exception:
        return None


