# US Policy Industry Intelligence Platform

This repository implements an MVP for `design.md`: it crawls policy signals from the White House and Federal Register, maps them to industries, scores industries and companies, and exposes a dashboard API plus a lightweight frontend.

## Quick Start

```powershell
python backend/manage.py analyze --lookback-days 30
python backend/manage.py serve --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000/
```

The backend uses live sources when network access is available. If crawling fails, it falls back to bundled sample documents so the scoring flow remains testable.

## API

- `GET /api/health`
- `GET /api/dashboard`
- `GET /api/policies`
- `GET /api/industries/ranking`
- `GET /api/companies/ranking`
- `POST /api/run-analysis?lookback_days=30`

## Data Sources

- White House: `https://www.whitehouse.gov`
- Federal Register API: `https://www.federalregister.gov/api/v1/documents.json`

## Notes

This is an intentionally small MVP rather than the full production architecture in `design.md`. It keeps the same domain model and scoring concepts, but avoids required services such as PostgreSQL, Redis, Celery, Qdrant, and an LLM provider until the product workflow is validated.
