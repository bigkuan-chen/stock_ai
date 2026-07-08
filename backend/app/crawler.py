from __future__ import annotations

import hashlib
import json
import re
import urllib.parse
import urllib.request
from datetime import date, timedelta
from html.parser import HTMLParser
from typing import Any

from .config import (
    FEDERAL_REGISTER_API_BASE_URL,
    FEDERAL_REGISTER_DOCUMENT_TYPES,
    REQUEST_TIMEOUT_SECONDS,
    USER_AGENT,
    WHITE_HOUSE_BASE_URL,
)
from .schemas import PolicyDocument


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip = False

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text and not self._skip:
            self.parts.append(text)

    def text(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self.parts)).strip()


class LinkExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        attr = dict(attrs)
        href = attr.get("href")
        if href:
            self.links.append(href)


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return response.read().decode("utf-8", errors="replace")


def stable_id(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def federal_register_document(item: dict[str, Any], fallback_date: str) -> PolicyDocument:
    agencies = [a.get("name", "") for a in item.get("agencies", []) if a.get("name")]
    title = item.get("title") or "Untitled Federal Register document"
    abstract = item.get("abstract") or ""
    return PolicyDocument(
        id=stable_id("federal_register", item.get("document_number", title)),
        source="Federal Register",
        title=title,
        url=item.get("html_url") or item.get("pdf_url") or "",
        published_date=item.get("publication_date") or fallback_date,
        document_type=item.get("type") or "document",
        summary=abstract,
        content=" ".join([title, abstract, item.get("citation", ""), " ".join(agencies)]),
        agencies=agencies,
    )


def crawl_federal_register(lookback_days: int) -> list[PolicyDocument]:
    start = date.today() - timedelta(days=lookback_days)
    end = date.today()
    docs: list[PolicyDocument] = []
    seen: set[str] = set()

    current = end
    while current >= start:
        current_iso = current.isoformat()
        params = {
            "order": "newest",
            "per_page": 1000,
            "conditions[publication_date][is]": current_iso,
            "conditions[type][]": FEDERAL_REGISTER_DOCUMENT_TYPES,
        }
        query = urllib.parse.urlencode(params, doseq=True)
        url = f"{FEDERAL_REGISTER_API_BASE_URL}/documents.json?{query}"
        while url:
            data = json.loads(fetch_text(url))
            for item in data.get("results", []):
                doc = federal_register_document(item, current_iso)
                if doc.id in seen:
                    continue
                seen.add(doc.id)
                docs.append(doc)
            url = data.get("next_page_url")
        current -= timedelta(days=1)
    return docs


def crawl_white_house(lookback_days: int) -> list[PolicyDocument]:
    del lookback_days
    sections = ["/fact-sheets/", "/presidential-actions/", "/briefing-room/"]
    urls: list[str] = []
    for section in sections:
        html = fetch_text(urllib.parse.urljoin(WHITE_HOUSE_BASE_URL, section))
        parser = LinkExtractor()
        parser.feed(html)
        for href in parser.links:
            full_url = urllib.parse.urljoin(WHITE_HOUSE_BASE_URL, href)
            if WHITE_HOUSE_BASE_URL in full_url and any(s in full_url for s in sections):
                urls.append(full_url.split("#")[0])

    docs: list[PolicyDocument] = []
    for url in sorted(set(urls)):
        try:
            html = fetch_text(url)
        except Exception:
            continue
        extractor = TextExtractor()
        extractor.feed(html)
        text = extractor.text()
        if len(text) < 300:
            continue
        title = text[:140].split(" | ")[0].strip()
        docs.append(
            PolicyDocument(
                id=stable_id("white_house", url),
                source="White House",
                title=title,
                url=url,
                published_date=date.today().isoformat(),
                document_type="white_house_release",
                summary=text[:500],
                content=text[:8000],
                agencies=[],
            )
        )
    return docs


def sample_documents() -> list[PolicyDocument]:
    samples: list[dict[str, Any]] = [
        {
            "source": "White House",
            "title": "Fact Sheet: Investing in domestic semiconductor manufacturing and AI infrastructure",
            "document_type": "fact_sheet",
            "content": "The Administration announces funding, grants, and procurement support for domestic semiconductor manufacturing, AI compute, cybersecurity, data centers, and resilient supply chains.",
        },
        {
            "source": "Federal Register",
            "title": "Department of Energy notice for grid modernization and clean energy transmission funding",
            "document_type": "NOTICE",
            "content": "DOE announces investment grants for clean energy, transmission, grid modernization, renewable energy, battery storage, and permitting acceleration.",
        },
        {
            "source": "Federal Register",
            "title": "Defense procurement rule for aerospace supply chain resilience",
            "document_type": "RULE",
            "content": "The Department of Defense issues a final rule supporting defense procurement, aerospace manufacturing, missile systems, shipbuilding, drones, and national security supply chains.",
        },
        {
            "source": "White House",
            "title": "Executive action to accelerate infrastructure permitting and broadband deployment",
            "document_type": "presidential_action",
            "content": "The policy accelerates permitting and investment for infrastructure, construction, water systems, broadband, transportation, bridges, rail, and highways.",
        },
        {
            "source": "Federal Register",
            "title": "FDA notice on pharmaceutical manufacturing and public health supply chains",
            "document_type": "NOTICE",
            "content": "FDA seeks comments on pharmaceutical manufacturing, medical devices, drug supply chain resilience, public health, and biotech innovation.",
        },
    ]
    today = date.today().isoformat()
    return [
        PolicyDocument(
            id=stable_id("sample", item["title"]),
            source=item["source"],
            title=item["title"],
            url="",
            published_date=today,
            document_type=item["document_type"],
            summary=item["content"][:260],
            content=item["content"],
            agencies=[],
        )
        for item in samples
    ]


def crawl_all(lookback_days: int, offline: bool = False) -> list[PolicyDocument]:
    if offline:
        return sample_documents()
    docs: list[PolicyDocument] = []
    for crawler in (crawl_federal_register, crawl_white_house):
        try:
            docs.extend(crawler(lookback_days))
        except Exception:
            pass
    return docs or sample_documents()
