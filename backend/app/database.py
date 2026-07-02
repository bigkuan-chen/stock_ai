from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from .config import DB_DIR, DB_FILE
from .storage import normalize_state


TAIPEI_TZ = ZoneInfo("Asia/Taipei")
RUN_AT_FORMAT = "%Y-%m-%d %H:%M:%S"


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 5000;

CREATE TABLE IF NOT EXISTS analysis_log (
    ana_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at        TEXT NOT NULL,
    lookback_days INTEGER NOT NULL CHECK (lookback_days > 0),

    CONSTRAINT uq_analysis_log_run_at
        UNIQUE (run_at),
    CONSTRAINT uq_analysis_log_ana_run
        UNIQUE (ana_id, run_at)
);

CREATE TABLE IF NOT EXISTS news (
    ana_id         INTEGER NOT NULL,
    id             TEXT NOT NULL,
    source         TEXT NOT NULL,
    title          TEXT NOT NULL,
    url            TEXT NOT NULL,
    published_date TEXT,
    document_type  TEXT,
    summary        TEXT NOT NULL DEFAULT '',
    content        TEXT NOT NULL DEFAULT '',
    agencies       TEXT NOT NULL DEFAULT '',
    run_at         TEXT NOT NULL,

    CONSTRAINT pk_news
        PRIMARY KEY (ana_id, id),

    CONSTRAINT fk_news_analysis
        FOREIGN KEY (ana_id, run_at)
        REFERENCES analysis_log (ana_id, run_at)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS companies (
    ana_id              INTEGER NOT NULL,
    ticker              TEXT NOT NULL,
    name                TEXT NOT NULL,
    exchange            TEXT,
    industry_code       TEXT,
    industry_name       TEXT,
    score               REAL,
    rating              TEXT,
    thesis              TEXT NOT NULL DEFAULT '',
    evidence            TEXT NOT NULL DEFAULT '',
    sector              TEXT,
    stock_industry      TEXT,
    related_industries  TEXT NOT NULL DEFAULT '',
    run_at              TEXT NOT NULL,

    CONSTRAINT pk_companies
        PRIMARY KEY (ana_id, ticker),

    CONSTRAINT fk_companies_analysis
        FOREIGN KEY (ana_id, run_at)
        REFERENCES analysis_log (ana_id, run_at)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_analysis_log_run_at
    ON analysis_log (run_at);

CREATE INDEX IF NOT EXISTS idx_news_run_at
    ON news (run_at);
CREATE INDEX IF NOT EXISTS idx_news_source
    ON news (source);
CREATE INDEX IF NOT EXISTS idx_news_published_date
    ON news (published_date);
CREATE INDEX IF NOT EXISTS idx_news_document_type
    ON news (document_type);
CREATE INDEX IF NOT EXISTS idx_news_url
    ON news (url);

CREATE INDEX IF NOT EXISTS idx_companies_run_at
    ON companies (run_at);
CREATE INDEX IF NOT EXISTS idx_companies_ticker
    ON companies (ticker);
CREATE INDEX IF NOT EXISTS idx_companies_industry_code
    ON companies (industry_code);
CREATE INDEX IF NOT EXISTS idx_companies_industry_name
    ON companies (industry_name);
CREATE INDEX IF NOT EXISTS idx_companies_sector
    ON companies (sector);
CREATE INDEX IF NOT EXISTS idx_companies_stock_industry
    ON companies (stock_industry);
CREATE INDEX IF NOT EXISTS idx_companies_rating
    ON companies (rating);
CREATE INDEX IF NOT EXISTS idx_companies_score
    ON companies (score DESC);
"""


def array_text(value: Any) -> str:
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return value.strip()
        value = parsed
    if not isinstance(value, list):
        return ""
    return ", ".join(str(item).strip() for item in value if str(item).strip())


def nullable_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def required_text(value: Any, field_name: str) -> str:
    text = nullable_text(value)
    if text is None:
        raise ValueError(f"{field_name} is required")
    return text


def valid_date_or_none(value: Any) -> str | None:
    text = nullable_text(value)
    if text is None:
        return None
    try:
        datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        return None
    return text


def run_at_now() -> str:
    return datetime.now(TAIPEI_TZ).strftime(RUN_AT_FORMAT)


def ensure_unique_run_at(conn: sqlite3.Connection, run_at: str) -> str:
    current = datetime.strptime(run_at, RUN_AT_FORMAT)
    while True:
        exists = conn.execute(
            "SELECT 1 FROM analysis_log WHERE run_at = ? LIMIT 1",
            (current.strftime(RUN_AT_FORMAT),),
        ).fetchone()
        if not exists:
            return current.strftime(RUN_AT_FORMAT)
        current += timedelta(seconds=1)


def connect() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    return conn


def initialize_database(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    migrate_json_array_schema(conn)


def schema_sql(conn: sqlite3.Connection, table: str) -> str:
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone()
    return row[0] if row and row[0] else ""


def migrate_json_array_schema(conn: sqlite3.Connection) -> None:
    table_sql = "\n".join([schema_sql(conn, "news"), schema_sql(conn, "companies")])
    if "json_valid" not in table_sql:
        return

    analysis_rows = conn.execute(
        "SELECT ana_id, run_at, lookback_days FROM analysis_log ORDER BY ana_id"
    ).fetchall()
    news_rows = conn.execute(
        """
        SELECT ana_id, id, source, title, url, published_date, document_type,
               summary, content, agencies, run_at
        FROM news
        ORDER BY ana_id, id
        """
    ).fetchall()
    company_rows = conn.execute(
        """
        SELECT ana_id, ticker, name, exchange, industry_code, industry_name,
               score, rating, thesis, evidence, sector, stock_industry,
               related_industries, run_at
        FROM companies
        ORDER BY ana_id, ticker
        """
    ).fetchall()

    conn.execute("PRAGMA foreign_keys = OFF;")
    conn.executescript(
        """
        DROP INDEX IF EXISTS idx_analysis_log_run_at;
        DROP INDEX IF EXISTS idx_news_run_at;
        DROP INDEX IF EXISTS idx_news_source;
        DROP INDEX IF EXISTS idx_news_published_date;
        DROP INDEX IF EXISTS idx_news_document_type;
        DROP INDEX IF EXISTS idx_news_url;
        DROP INDEX IF EXISTS idx_companies_run_at;
        DROP INDEX IF EXISTS idx_companies_ticker;
        DROP INDEX IF EXISTS idx_companies_industry_code;
        DROP INDEX IF EXISTS idx_companies_industry_name;
        DROP INDEX IF EXISTS idx_companies_sector;
        DROP INDEX IF EXISTS idx_companies_stock_industry;
        DROP INDEX IF EXISTS idx_companies_rating;
        DROP INDEX IF EXISTS idx_companies_score;

        ALTER TABLE analysis_log RENAME TO analysis_log_old;
        ALTER TABLE news RENAME TO news_old;
        ALTER TABLE companies RENAME TO companies_old;
        """
    )
    conn.executescript(SCHEMA_SQL)
    conn.executemany(
        "INSERT INTO analysis_log (ana_id, run_at, lookback_days) VALUES (?, ?, ?)",
        analysis_rows,
    )
    conn.executemany(
        """
        INSERT INTO news (
            ana_id, id, source, title, url, published_date, document_type,
            summary, content, agencies, run_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (*row[:9], array_text(row[9]), row[10])
            for row in news_rows
        ],
    )
    conn.executemany(
        """
        INSERT INTO companies (
            ana_id, ticker, name, exchange, industry_code, industry_name,
            score, rating, thesis, evidence, sector, stock_industry,
            related_industries, run_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (*row[:9], array_text(row[9]), row[10], row[11], array_text(row[12]), row[13])
            for row in company_rows
        ],
    )
    conn.executescript(
        """
        DROP TABLE companies_old;
        DROP TABLE news_old;
        DROP TABLE analysis_log_old;
        """
    )
    conn.execute("PRAGMA foreign_keys = ON;")


def insert_news(conn: sqlite3.Connection, ana_id: int, run_at: str, policies: list[dict[str, Any]]) -> None:
    rows = []
    for policy in policies:
        rows.append((
            ana_id,
            required_text(policy.get("id"), "policy.id"),
            required_text(policy.get("source"), "policy.source"),
            required_text(policy.get("title"), "policy.title"),
            required_text(policy.get("url"), "policy.url"),
            valid_date_or_none(policy.get("published_date")),
            nullable_text(policy.get("document_type")),
            str(policy.get("summary") or ""),
            str(policy.get("content") or ""),
            array_text(policy.get("agencies")),
            run_at,
        ))
    conn.executemany(
        """
        INSERT INTO news (
            ana_id, id, source, title, url, published_date, document_type,
            summary, content, agencies, run_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def insert_companies(conn: sqlite3.Connection, ana_id: int, run_at: str, companies: list[dict[str, Any]]) -> None:
    rows = []
    for company in companies:
        ticker = required_text(company.get("ticker"), "company.ticker").upper()
        rows.append((
            ana_id,
            ticker,
            required_text(company.get("name"), "company.name"),
            nullable_text(company.get("exchange")),
            nullable_text(company.get("industry_code")),
            nullable_text(company.get("industry_name")),
            company.get("score"),
            nullable_text(company.get("rating")),
            str(company.get("thesis") or ""),
            array_text(company.get("evidence")),
            nullable_text(company.get("sector")),
            nullable_text(company.get("stock_industry")),
            array_text(company.get("related_industries")),
            run_at,
        ))
    conn.executemany(
        """
        INSERT INTO companies (
            ana_id, ticker, name, exchange, industry_code, industry_name,
            score, rating, thesis, evidence, sector, stock_industry,
            related_industries, run_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def save_analysis_to_db(state: dict[str, Any]) -> dict[str, Any]:
    state = normalize_state(state)
    lookback_days = int(state.get("lookback_days") or 0)
    if lookback_days <= 0:
        raise ValueError("lookback_days must be greater than 0")
    policies = state.get("policies") or []
    companies = state.get("companies") or []
    if not isinstance(policies, list):
        raise ValueError("policies must be a list")
    if not isinstance(companies, list):
        raise ValueError("companies must be a list")

    conn = connect()
    try:
        initialize_database(conn)
        run_at = ensure_unique_run_at(conn, run_at_now())
        conn.execute("BEGIN IMMEDIATE;")
        cursor = conn.execute(
            "INSERT INTO analysis_log (run_at, lookback_days) VALUES (?, ?)",
            (run_at, lookback_days),
        )
        ana_id = int(cursor.lastrowid)
        insert_news(conn, ana_id, run_at, policies)
        insert_companies(conn, ana_id, run_at, companies)
        conn.commit()
        return {
            "ana_id": ana_id,
            "run_at": run_at,
            "lookback_days": lookback_days,
            "news": len(policies),
            "companies": len(companies),
            "database": str(DB_FILE),
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
