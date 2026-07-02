```yaml
project:
  name: "StockAI JSON to SQLite Importer"
  version: "1.0.0"
  description: >
    將系統爬文及公司分析結果 JSON 匯入 SQLite3。
    每次匯入建立一筆 analysis_log，並使用相同的 ana_id 與 run_at
    關聯該次分析的 news 與 companies 資料。

database:
  engine: "SQLite3"
  path: "db/stockai.db"
  encoding: "UTF-8"

  startup:
    create_directory_if_missing: true
    create_database_if_missing: true
    enable_foreign_keys: true
    journal_mode: "WAL"
    synchronous: "NORMAL"
    busy_timeout_ms: 5000

  connection_pragmas:
    - "PRAGMA foreign_keys = ON;"
    - "PRAGMA journal_mode = WAL;"
    - "PRAGMA synchronous = NORMAL;"
    - "PRAGMA busy_timeout = 5000;"

datetime:
  field_name: "run_at"
  format: "%Y-%m-%d %H:%M:%S"
  example: "2026-07-02 20:35:18"
  timezone: "Asia/Taipei"

  generation_rule: >
    匯入程式開始執行時，只產生一次 run_at。
    analysis_log、news、companies 必須共用相同的 run_at，
    不得在逐筆新增資料時重新取得目前時間。

  source_rule:
    run_at:
      source: "由匯入程式產生"
      do_not_use: "JSON.updated_at"
      reason: >
        JSON.updated_at 只有日期，無法區分同一天內的多次分析執行。
    lookback_days:
      source: "JSON.lookback_days"

json_input:
  expected_structure:
    updated_at:
      type: "string"
      required: false
      format: "YYYY-MM-DD"
      usage: "來源資料更新日期，暫不直接存入資料表"

    lookback_days:
      type: "integer"
      required: true
      minimum: 1
      target:
        table: "analysis_log"
        column: "lookback_days"

    policies:
      type: "array"
      required: false
      default: []
      target_table: "news"

      item_fields:
        id:
          type: "string"
          required: true
        source:
          type: "string"
          required: true
        title:
          type: "string"
          required: true
        url:
          type: "string"
          required: true
        published_date:
          type: "string"
          required: false
          format: "YYYY-MM-DD"
        document_type:
          type: "string"
          required: false
        summary:
          type: "string"
          required: false
          default: ""
        content:
          type: "string"
          required: false
          default: ""
        agencies:
          type: "array[string]"
          required: false
          default: []
          storage: "JSON encoded TEXT"

    companies:
      type: "array"
      required: false
      default: []
      target_table: "companies"

      item_fields:
        ticker:
          type: "string"
          required: true
        name:
          type: "string"
          required: true
        exchange:
          type: "string"
          required: false
        industry_code:
          type: "string"
          required: false
        industry_name:
          type: "string"
          required: false
        score:
          type: "number"
          required: false
        rating:
          type: "string"
          required: false
        thesis:
          type: "string"
          required: false
          default: ""
        evidence:
          type: "array[string]"
          required: false
          default: []
          storage: "JSON encoded TEXT"
        sector:
          type: "string"
          required: false
        stock_industry:
          type: "string"
          required: false
        related_industries:
          type: "array[string]"
          required: false
          default: []
          storage: "JSON encoded TEXT"

tables:
  analysis_log:
    description: "記錄每一次分析與匯入批次。"

    primary_key:
      columns:
        - "ana_id"
      strategy: "INTEGER PRIMARY KEY AUTOINCREMENT"

    unique_constraints:
      - columns:
          - "run_at"
        reason: "每次分析執行時間必須唯一"

    columns:
      ana_id:
        sql_type: "INTEGER"
        nullable: false
        primary_key: true
        autoincrement: true

      run_at:
        sql_type: "TEXT"
        nullable: false
        unique: true
        format: "YYYY-MM-DD HH:MM:SS"

      lookback_days:
        sql_type: "INTEGER"
        nullable: false
        check: "lookback_days > 0"

    indexes:
      - name: "idx_analysis_log_run_at"
        columns:
          - "run_at"
        unique: true

  news:
    description: "保存本次分析取得的政策、新聞與研究文件。"

    primary_key:
      type: "composite"
      columns:
        - "ana_id"
        - "id"

    columns:
      ana_id:
        sql_type: "INTEGER"
        nullable: false

      id:
        sql_type: "TEXT"
        nullable: false

      source:
        sql_type: "TEXT"
        nullable: false

      title:
        sql_type: "TEXT"
        nullable: false

      url:
        sql_type: "TEXT"
        nullable: false

      published_date:
        sql_type: "TEXT"
        nullable: true
        format: "YYYY-MM-DD"

      document_type:
        sql_type: "TEXT"
        nullable: true

      summary:
        sql_type: "TEXT"
        nullable: false
        default: "''"

      content:
        sql_type: "TEXT"
        nullable: false
        default: "''"

      agencies:
        sql_type: "TEXT"
        nullable: false
        default: "'[]'"
        content_type: "JSON array"

      run_at:
        sql_type: "TEXT"
        nullable: false
        format: "YYYY-MM-DD HH:MM:SS"

    foreign_keys:
      - columns:
          - "ana_id"
          - "run_at"
        references:
          table: "analysis_log"
          columns:
            - "ana_id"
            - "run_at"
        on_update: "CASCADE"
        on_delete: "CASCADE"

    indexes:
      - name: "idx_news_run_at"
        columns:
          - "run_at"

      - name: "idx_news_source"
        columns:
          - "source"

      - name: "idx_news_published_date"
        columns:
          - "published_date"

      - name: "idx_news_document_type"
        columns:
          - "document_type"

      - name: "idx_news_url"
        columns:
          - "url"

  companies:
    description: "保存每次分析產生的公司評分與研究證據。"

    primary_key:
      type: "composite"
      columns:
        - "ana_id"
        - "ticker"

    columns:
      ana_id:
        sql_type: "INTEGER"
        nullable: false

      ticker:
        sql_type: "TEXT"
        nullable: false
        normalization: "trim and uppercase"

      name:
        sql_type: "TEXT"
        nullable: false

      exchange:
        sql_type: "TEXT"
        nullable: true

      industry_code:
        sql_type: "TEXT"
        nullable: true

      industry_name:
        sql_type: "TEXT"
        nullable: true

      score:
        sql_type: "REAL"
        nullable: true

      rating:
        sql_type: "TEXT"
        nullable: true

      thesis:
        sql_type: "TEXT"
        nullable: false
        default: "''"

      evidence:
        sql_type: "TEXT"
        nullable: false
        default: "'[]'"
        content_type: "JSON array"

      sector:
        sql_type: "TEXT"
        nullable: true

      stock_industry:
        sql_type: "TEXT"
        nullable: true

      related_industries:
        sql_type: "TEXT"
        nullable: false
        default: "'[]'"
        content_type: "JSON array"

      run_at:
        sql_type: "TEXT"
        nullable: false
        format: "YYYY-MM-DD HH:MM:SS"

    foreign_keys:
      - columns:
          - "ana_id"
          - "run_at"
        references:
          table: "analysis_log"
          columns:
            - "ana_id"
            - "run_at"
        on_update: "CASCADE"
        on_delete: "CASCADE"

    indexes:
      - name: "idx_companies_run_at"
        columns:
          - "run_at"

      - name: "idx_companies_ticker"
        columns:
          - "ticker"

      - name: "idx_companies_industry_code"
        columns:
          - "industry_code"

      - name: "idx_companies_industry_name"
        columns:
          - "industry_name"

      - name: "idx_companies_sector"
        columns:
          - "sector"

      - name: "idx_companies_stock_industry"
        columns:
          - "stock_industry"

      - name: "idx_companies_rating"
        columns:
          - "rating"

      - name: "idx_companies_score"
        columns:
          - "score"

table_schema_sql: |
  PRAGMA foreign_keys = ON;
  PRAGMA journal_mode = WAL;
  PRAGMA synchronous = NORMAL;
  PRAGMA busy_timeout = 5000;

  CREATE TABLE IF NOT EXISTS analysis_log (
      ana_id        INTEGER PRIMARY KEY AUTOINCREMENT,
      run_at        TEXT NOT NULL,
      lookback_days INTEGER NOT NULL CHECK (lookback_days > 0),

      CONSTRAINT uq_analysis_log_run_at
          UNIQUE (run_at)
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
      agencies       TEXT NOT NULL DEFAULT '[]'
                     CHECK (json_valid(agencies)),
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
      evidence            TEXT NOT NULL DEFAULT '[]'
                          CHECK (json_valid(evidence)),
      sector              TEXT,
      stock_industry      TEXT,
      related_industries  TEXT NOT NULL DEFAULT '[]'
                          CHECK (json_valid(related_industries)),
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

json_to_database_mapping:
  analysis_log:
    ana_id:
      source: "SQLite 自動產生"
    run_at:
      source: "匯入程式在 transaction 開始前產生一次"
    lookback_days:
      source: "$.lookback_days"

  news:
    source_array: "$.policies[*]"
    fields:
      ana_id: "$generated.ana_id"
      id: "$.id"
      source: "$.source"
      title: "$.title"
      url: "$.url"
      published_date: "$.published_date"
      document_type: "$.document_type"
      summary: "$.summary"
      content: "$.content"
      agencies: "json.dumps($.agencies, ensure_ascii=false)"
      run_at: "$generated.run_at"

  companies:
    source_array: "$.companies[*]"
    fields:
      ana_id: "$generated.ana_id"
      ticker: "upper(trim($.ticker))"
      name: "$.name"
      exchange: "$.exchange"
      industry_code: "$.industry_code"
      industry_name: "$.industry_name"
      score: "$.score"
      rating: "$.rating"
      thesis: "$.thesis"
      evidence: "json.dumps($.evidence, ensure_ascii=false)"
      sector: "$.sector"
      stock_industry: "$.stock_industry"
      related_industries: >
        json.dumps($.related_industries, ensure_ascii=false)
      run_at: "$generated.run_at"

import_process:
  transaction_mode: "IMMEDIATE"

  steps:
    - step: 1
      name: "建立資料庫目錄"
      action: >
        若 db 目錄不存在，建立 db 目錄。

    - step: 2
      name: "讀取 JSON"
      action: >
        使用 UTF-8 讀取 JSON，解析 updated_at、lookback_days、
        policies 與 companies。

    - step: 3
      name: "驗證必要欄位"
      validations:
        - "lookback_days 必須存在且為大於 0 的整數"
        - "policies 必須是陣列；缺少時使用空陣列"
        - "companies 必須是陣列；缺少時使用空陣列"
        - "每筆 policy.id 不得為空"
        - "每筆 policy.source 不得為空"
        - "每筆 policy.title 不得為空"
        - "每筆 policy.url 不得為空"
        - "每筆 company.ticker 不得為空"
        - "每筆 company.name 不得為空"

    - step: 4
      name: "產生統一執行時間"
      action: >
        以 Asia/Taipei 時區取得目前時間，
        格式化為 YYYY-MM-DD HH:MM:SS，
        只執行一次並保存至 run_at 變數。

    - step: 5
      name: "避免同秒執行時間衝突"
      action: >
        查詢 analysis_log 是否已存在相同 run_at。
        若存在，等待至下一秒或重新產生新的 run_at。
      reason: >
        run_at 精確到秒，同一秒內若同時啟動兩個分析，
        UNIQUE(run_at) 會阻止重複批次時間。

    - step: 6
      name: "開始交易"
      sql: "BEGIN IMMEDIATE;"

    - step: 7
      name: "新增 analysis_log"
      sql: |
        INSERT INTO analysis_log (
            run_at,
            lookback_days
        )
        VALUES (?, ?);
      parameters:
        - "run_at"
        - "json.lookback_days"
      generated_value:
        ana_id: "cursor.lastrowid"

    - step: 8
      name: "新增 news"
      iteration: "$.policies[*]"
      sql: |
        INSERT INTO news (
            ana_id,
            id,
            source,
            title,
            url,
            published_date,
            document_type,
            summary,
            content,
            agencies,
            run_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
      parameters:
        - "ana_id"
        - "policy.id"
        - "policy.source"
        - "policy.title"
        - "policy.url"
        - "policy.published_date"
        - "policy.document_type"
        - "policy.summary or ''"
        - "policy.content or ''"
        - "JSON encoded policy.agencies or []"
        - "run_at"

    - step: 9
      name: "新增 companies"
      iteration: "$.companies[*]"
      sql: |
        INSERT INTO companies (
            ana_id,
            ticker,
            name,
            exchange,
            industry_code,
            industry_name,
            score,
            rating,
            thesis,
            evidence,
            sector,
            stock_industry,
            related_industries,
            run_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
      parameters:
        - "ana_id"
        - "uppercase company.ticker"
        - "company.name"
        - "company.exchange"
        - "company.industry_code"
        - "company.industry_name"
        - "company.score"
        - "company.rating"
        - "company.thesis or ''"
        - "JSON encoded company.evidence or []"
        - "company.sector"
        - "company.stock_industry"
        - "JSON encoded company.related_industries or []"
        - "run_at"

    - step: 10
      name: "提交交易"
      sql: "COMMIT;"

    - step: 11
      name: "錯誤回復"
      on_error:
        sql: "ROLLBACK;"
        behavior: >
          analysis_log、news、companies 任一新增失敗，
          整批資料全部取消，不留下不完整的分析批次。

duplicate_policy:
  within_same_analysis:
    news:
      conflict_key:
        - "ana_id"
        - "id"
      behavior: "reject"
      reason: "同一分析批次不應出現重複文件 id"

    companies:
      conflict_key:
        - "ana_id"
        - "ticker"
      behavior: "reject"
      reason: "同一分析批次每個 ticker 只能有一筆結果"

  across_different_analyses:
    behavior: "allow"
    reason: >
      相同 news.id 或 company.ticker 可存在於不同 ana_id，
      以便保留每次分析的歷史快照。

data_normalization:
  ticker:
    operations:
      - "去除前後空白"
      - "轉為大寫"

  nullable_strings:
    behavior: >
      非必要欄位缺少時存 NULL；
      summary、content、thesis 缺少時存空字串。

  json_arrays:
    fields:
      - "news.agencies"
      - "companies.evidence"
      - "companies.related_industries"
    encoding:
      function: "json.dumps"
      ensure_ascii: false
    empty_value: "[]"

  published_date:
    accepted_format: "YYYY-MM-DD"
    invalid_behavior: "存 NULL 並記錄 validation warning"

query_examples:
  latest_analysis:
    description: "取得最新一次分析紀錄"
    sql: |
      SELECT
          ana_id,
          run_at,
          lookback_days
      FROM analysis_log
      ORDER BY ana_id DESC
      LIMIT 1;

  latest_companies:
    description: "取得最新一次分析的公司排名"
    sql: |
      SELECT
          c.*
      FROM companies AS c
      WHERE c.ana_id = (
          SELECT MAX(ana_id)
          FROM analysis_log
      )
      ORDER BY c.score DESC;

  latest_news:
    description: "取得最新一次分析的新聞與政策資料"
    sql: |
      SELECT
          n.*
      FROM news AS n
      WHERE n.ana_id = (
          SELECT MAX(ana_id)
          FROM analysis_log
      )
      ORDER BY n.published_date DESC, n.id;

  company_history:
    description: "查詢單一股票歷次分析分數"
    parameters:
      ticker: "VRT"
    sql: |
      SELECT
          c.ana_id,
          c.run_at,
          c.ticker,
          c.name,
          c.score,
          c.rating,
          c.thesis
      FROM companies AS c
      WHERE c.ticker = UPPER(?)
      ORDER BY c.ana_id DESC;

  parse_company_evidence:
    description: "利用 SQLite JSON1 展開 evidence 陣列"
    sql: |
      SELECT
          c.ticker,
          c.name,
          e.value AS evidence_item
      FROM companies AS c
      JOIN json_each(c.evidence) AS e
      WHERE c.ana_id = ?;

  parse_news_agencies:
    description: "利用 SQLite JSON1 展開 agencies 陣列"
    sql: |
      SELECT
          n.id,
          n.title,
          a.value AS agency
      FROM news AS n
      JOIN json_each(n.agencies) AS a
      WHERE n.ana_id = ?;

acceptance_criteria:
  - id: "AC-001"
    requirement: "資料庫檔案建立於 db/stockai.db"

  - id: "AC-002"
    requirement: >
      每次匯入只新增一筆 analysis_log，
      並由 SQLite 自動產生 ana_id。

  - id: "AC-003"
    requirement: >
      同一批次的 analysis_log、news、companies.run_at
      必須完全相同，精確到秒。

  - id: "AC-004"
    requirement: >
      news 使用 (ana_id, id) 作為複合主鍵。

  - id: "AC-005"
    requirement: >
      companies 使用 (ana_id, ticker) 作為複合主鍵。

  - id: "AC-006"
    requirement: >
      相同 ticker 可出現在不同 ana_id，
      用於保留歷史分析結果。

  - id: "AC-007"
    requirement: >
      agencies、evidence、related_industries
      必須保存為合法 JSON array 字串。

  - id: "AC-008"
    requirement: >
      任一資料新增失敗時，整個分析批次必須 rollback。

  - id: "AC-009"
    requirement: >
      刪除 analysis_log 時，對應的 news 與 companies
      必須透過 ON DELETE CASCADE 一併刪除。

  - id: "AC-010"
    requirement: >
      系統必須支援同一天執行多次分析，
      每次產生不同 ana_id 與 run_at。

