project:
  name: "US Policy Industry Intelligence Platform"
  display_name: "美國政策產業趨勢與潛力公司分析系統"
  version: "1.0.0"
  description: >
    蒐集 White House 與 Federal Register 的政策文件，
    分析政策支持產業、法規落地程度、受益供應鏈與潛力公司，
    並透過評分模型產生產業與公司研究清單。
  language:
    frontend: "TypeScript"
    backend: "Python"
  locale:
    default: "zh-TW"
    timezone: "Asia/Taipei"

objectives:
  primary:
    - "自動蒐集 White House 政策文件"
    - "透過 Federal Register API 蒐集正式法規文件"
    - "辨識政策支持或限制的產業"
    - "比對 White House 政策與 Federal Register 法規"
    - "建立政策、產業、供應鏈與公司的關聯"
    - "產生產業趨勢分數"
    - "產生潛力公司研究分數"
    - "保留所有分析結果的原始資料來源"
  exclusions:
    - "系統不直接提供股票買賣指令"
    - "政策出現次數不直接等於公司投資價值"
    - "公司評分必須搭配財務與業務關聯資料"

architecture:
  style: "frontend-backend-separated"
  components:
    frontend:
      framework: "Next.js"
      version: "15+"
      language: "TypeScript"
      rendering:
        - "Server Components"
        - "Client Components"
        - "SSR"
      responsibilities:
        - "使用者登入"
        - "儀表板"
        - "政策文件查詢"
        - "產業趨勢分析"
        - "公司排名"
        - "分析工作管理"
        - "環境設定顯示"
        - "圖表與政策時間軸"

    backend:
      framework: "Django"
      api_framework: "Django REST Framework"
      language: "Python 3.12+"
      responsibilities:
        - "REST API"
        - "使用者與權限管理"
        - "政策資料管理"
        - "爬蟲任務管理"
        - "Federal Register API 整合"
        - "LLM 分析"
        - "產業分類"
        - "政策配對"
        - "公司評分"
        - "排程管理"

    worker:
      framework: "Celery"
      broker: "Redis"
      responsibilities:
        - "執行 White House 爬蟲"
        - "呼叫 Federal Register API"
        - "HTML 清理"
        - "政策文件分析"
        - "向量化"
        - "政策文件配對"
        - "重新計算產業與公司分數"

    scheduler:
      framework: "Celery Beat"
      responsibilities:
        - "定時啟動資料蒐集"
        - "定時重新分析"
        - "定時重新計算排名"

    database:
      relational:
        engine: "PostgreSQL"
        usage:
          - "政策文件"
          - "產業分類"
          - "公司資料"
          - "評分結果"
          - "爬蟲紀錄"
          - "分析工作紀錄"
      vector:
        engine: "Qdrant"
        usage:
          - "政策文件向量"
          - "White House 與 Federal Register 語意配對"
          - "產業與公司語意搜尋"

    cache:
      engine: "Redis"
      usage:
        - "Celery broker"
        - "API 快取"
        - "爬蟲鎖定"
        - "分析工作狀態"

system_flow:
  steps:
    - id: 1
      name: "資料蒐集"
      actions:
        - "依環境變數取得爬取日期範圍"
        - "爬取 White House 文件"
        - "呼叫 Federal Register API"
        - "保存原始 HTML 或 JSON"

    - id: 2
      name: "資料清理"
      actions:
        - "移除 HTML 導覽與頁尾"
        - "抽取標題、日期、文件類型與正文"
        - "產生文件 checksum"
        - "執行 URL 與內容去重"

    - id: 3
      name: "政策資訊抽取"
      actions:
        - "抽取政策產業"
        - "抽取政策工具"
        - "抽取執行機關"
        - "抽取金額與日期"
        - "抽取公司與地區"
        - "判斷政策正面或負面方向"

    - id: 4
      name: "政策文件配對"
      actions:
        - "依關鍵字比對"
        - "依政府機關比對"
        - "依文件日期比對"
        - "依向量相似度比對"
        - "建立 White House 與 Federal Register 關聯"

    - id: 5
      name: "產業與供應鏈分析"
      actions:
        - "將政策對應至標準產業分類"
        - "找出直接受益產業"
        - "找出間接受益供應鏈"
        - "找出可能受害產業"

    - id: 6
      name: "公司候選與評分"
      actions:
        - "依產業與產品找出公司"
        - "計算公司政策關聯度"
        - "加入財務與公司行動指標"
        - "產生公司潛力研究分數"

    - id: 7
      name: "前端呈現"
      actions:
        - "顯示產業排行榜"
        - "顯示政策時間軸"
        - "顯示公司排行榜"
        - "顯示政策來源與分析理由"

environment_variables:
  application:
    DJANGO_ENV:
      default: "development"
      allowed:
        - "development"
        - "testing"
        - "production"

    DJANGO_SECRET_KEY:
      required: true
      sensitive: true

    DJANGO_DEBUG:
      default: "true"

    DJANGO_ALLOWED_HOSTS:
      default: "localhost,127.0.0.1"

    DJANGO_CORS_ALLOWED_ORIGINS:
      default: "http://localhost:3000"

    APP_TIMEZONE:
      default: "Asia/Taipei"

    APP_LANGUAGE:
      default: "zh-TW"

  crawl_date:
    CRAWL_DATE_MODE:
      default: "rolling_days"
      allowed:
        - "fixed_range"
        - "rolling_days"
      description: >
        fixed_range 使用 CRAWL_START_DATE 與 CRAWL_END_DATE。
        rolling_days 使用目前日期往前回溯 CRAWL_LOOKBACK_DAYS。

    CRAWL_START_DATE:
      default: "2026-01-01"
      format: "YYYY-MM-DD"
      description: "固定日期模式的爬取開始日期"

    CRAWL_END_DATE:
      default: "2026-06-29"
      format: "YYYY-MM-DD"
      description: >
        固定日期模式的爬取結束日期。
        若設定為空值，可由程式自動使用執行當日日期。

    CRAWL_LOOKBACK_DAYS:
      default: "30"
      type: "integer"
      description: "滾動日期模式每次往前回溯的天數"

    CRAWL_DATE_TIMEZONE:
      default: "America/New_York"
      description: "政策發布日期判斷所使用的時區"

    CRAWL_INCLUDE_TODAY:
      default: "true"

    CRAWL_FORCE_RECRAWL:
      default: "false"
      description: "是否忽略既有資料並重新爬取"

  crawl_schedule:
    CRAWL_SCHEDULE_ENABLED:
      default: "true"

    CRAWL_SCHEDULE_CRON:
      default: "0 7 * * *"
      description: "每天台北時間上午 7 點執行"

    POLICY_ANALYSIS_CRON:
      default: "30 7 * * *"

    SCORE_RECALCULATION_CRON:
      default: "0 8 * * *"

    CRAWL_BATCH_SIZE:
      default: "50"

    CRAWL_REQUEST_DELAY_SECONDS:
      default: "1.5"

    CRAWL_MAX_RETRIES:
      default: "3"

    CRAWL_REQUEST_TIMEOUT_SECONDS:
      default: "30"

  white_house:
    WHITE_HOUSE_BASE_URL:
      default: "https://www.whitehouse.gov"

    WHITE_HOUSE_SITEMAP_URL:
      default: "https://www.whitehouse.gov/sitemap_index.xml"

    WHITE_HOUSE_CRAWL_ENABLED:
      default: "true"

    WHITE_HOUSE_CRAWL_SECTIONS:
      default: >
        fact-sheets,
        presidential-actions,
        briefings-statements,
        releases

    WHITE_HOUSE_USER_AGENT:
      default: "PolicyResearchBot/1.0"

    WHITE_HOUSE_USE_PLAYWRIGHT:
      default: "false"

  federal_register:
    FEDERAL_REGISTER_API_BASE_URL:
      default: "https://www.federalregister.gov/api"

    FEDERAL_REGISTER_CRAWL_ENABLED:
      default: "true"

    FEDERAL_REGISTER_DOCUMENT_TYPES:
      default: "RULE,PRORULE,NOTICE,PRESDOCU"

    FEDERAL_REGISTER_PER_PAGE:
      default: "100"

    FEDERAL_REGISTER_MAX_PAGES:
      default: "100"

    FEDERAL_REGISTER_AGENCIES:
      default: ""
      description: "空白代表不限制政府機關"

  database:
    DATABASE_URL:
      required: true
      sensitive: true
      example: "postgresql://user:password@localhost:5432/policy_db"

    DB_CONN_MAX_AGE:
      default: "60"

  redis:
    REDIS_URL:
      required: true
      sensitive: true
      example: "redis://localhost:6379/0"

    CELERY_BROKER_URL:
      default_from: "REDIS_URL"

    CELERY_RESULT_BACKEND:
      default_from: "REDIS_URL"

  qdrant:
    QDRANT_URL:
      default: "http://localhost:6333"

    QDRANT_API_KEY:
      required: false
      sensitive: true

    QDRANT_COLLECTION_POLICY_DOCUMENTS:
      default: "policy_documents"

    QDRANT_COLLECTION_COMPANIES:
      default: "companies"

  ai:
    AI_PROVIDER:
      default: "gemini"
      allowed:
        - "openai"
        - "ollama"
        - "gemini"
        - "groq"

    AI_API_KEY:
      required_when: "AI_PROVIDER=openai"
      sensitive: true

    AI_MODEL:
      default: "gpt-5-mini"

    AI_BASE_URL:
      required: false

    EMBEDDING_PROVIDER:
      default: "ollama"

    EMBEDDING_MODEL:
      default: "nomic-embed-text:latest"

    AI_ANALYSIS_ENABLED:
      default: "true"

    AI_MAX_DOCUMENT_LENGTH:
      default: "60000"

    AI_TEMPERATURE:
      default: "0.1"

  frontend:
    NEXT_PUBLIC_API_BASE_URL:
      default: "http://localhost:8000/api"

    NEXT_PUBLIC_APP_NAME:
      default: "美國政策產業雷達"

    NEXT_PUBLIC_DEFAULT_LOCALE:
      default: "zh-TW"

    NEXT_PUBLIC_DEFAULT_TIMEZONE:
      default: "Asia/Taipei"

crawl_date_resolution:
  module: "apps.crawler.services.date_range"
  class_name: "CrawlDateRangeResolver"
  logic:
    fixed_range:
      start_date: "${CRAWL_START_DATE}"
      end_date: "${CRAWL_END_DATE:-today}"
    rolling_days:
      end_date: "today"
      start_date: "today - CRAWL_LOOKBACK_DAYS"
  validation:
    - "開始日期不得晚於結束日期"
    - "日期格式必須為 YYYY-MM-DD"
    - "CRAWL_LOOKBACK_DAYS 必須大於 0"
    - "日期範圍不得超過管理者設定的最大天數"
  maximum_range_days:
    default: 3650

crawl_sources:
  white_house:
    source_type: "web_crawler"
    base_url_env: "WHITE_HOUSE_BASE_URL"
    extraction:
      list_page:
        fields:
          - "detail_url"
          - "title"
          - "published_date"
          - "category"
      detail_page:
        fields:
          - "title"
          - "published_date"
          - "updated_date"
          - "document_type"
          - "content"
          - "author"
          - "canonical_url"
          - "metadata"
    sections:
      - key: "fact_sheets"
        path: "/fact-sheets/"
        document_type: "fact_sheet"

      - key: "presidential_actions"
        path: "/presidential-actions/"
        document_type: "presidential_action"

      - key: "briefings_statements"
        path: "/briefings-statements/"
        document_type: "briefing_statement"

      - key: "releases"
        path: "/releases/"
        document_type: "release"

    crawler_rules:
      respect_robots_txt: true
      store_raw_html: true
      deduplication:
        primary_key: "canonical_url"
        secondary_key: "content_checksum"
      retry:
        max_retries_env: "CRAWL_MAX_RETRIES"
      delay_seconds_env: "CRAWL_REQUEST_DELAY_SECONDS"

  federal_register:
    source_type: "rest_api"
    base_url_env: "FEDERAL_REGISTER_API_BASE_URL"
    endpoint: "/documents.json"
    parameters:
      per_page: "${FEDERAL_REGISTER_PER_PAGE}"
      order: "newest"
      conditions_publication_date_greater_than_or_equal_to: "${resolved_start_date}"
      conditions_publication_date_less_than_or_equal_to: "${resolved_end_date}"
      conditions_type:
        from_env: "FEDERAL_REGISTER_DOCUMENT_TYPES"
      conditions_agencies:
        from_env: "FEDERAL_REGISTER_AGENCIES"
    response_fields:
      - "document_number"
      - "title"
      - "type"
      - "abstract"
      - "publication_date"
      - "effective_on"
      - "agencies"
      - "html_url"
      - "pdf_url"
      - "raw_text_url"
      - "excerpts"
      - "citation"
      - "cfr_references"
      - "presidential_document_type"
      - "signing_date"
    crawler_rules:
      pagination: true
      max_pages_env: "FEDERAL_REGISTER_MAX_PAGES"
      store_raw_json: true
      deduplication:
        primary_key: "document_number"

backend_structure:
  root: "backend"
  folders:
    config:
      files:
        - "settings/base.py"
        - "settings/development.py"
        - "settings/production.py"
        - "urls.py"
        - "celery.py"

    apps:
      accounts:
        responsibilities:
          - "使用者"
          - "角色"
          - "權限"

      crawler:
        responsibilities:
          - "爬蟲來源設定"
          - "爬蟲工作"
          - "日期範圍解析"
          - "原始資料保存"

      policies:
        responsibilities:
          - "政策文件"
          - "政策分類"
          - "政策動作"
          - "政府機關"

      industries:
        responsibilities:
          - "產業分類"
          - "供應鏈關係"
          - "產業趨勢分數"

      companies:
        responsibilities:
          - "公司基本資料"
          - "公司產品"
          - "公司產業關係"
          - "公司財務資料"

      matching:
        responsibilities:
          - "White House 與 Federal Register 配對"
          - "文件向量相似度"
          - "人工確認"

      analytics:
        responsibilities:
          - "產業評分"
          - "公司評分"
          - "趨勢分析"
          - "分析快照"

      ai_analysis:
        responsibilities:
          - "政策文件結構化"
          - "產業抽取"
          - "公司抽取"
          - "政策正負面判斷"

      audit:
        responsibilities:
          - "使用者操作紀錄"
          - "資料修改紀錄"
          - "分析版本紀錄"

database_models:
  Source:
    table: "sources"
    fields:
      id: "bigint primary key"
      code: "varchar(50) unique"
      name: "varchar(100)"
      source_type: "varchar(30)"
      base_url: "text"
      is_enabled: "boolean"
      created_at: "timestamp"
      updated_at: "timestamp"

  CrawlJob:
    table: "crawl_jobs"
    fields:
      id: "uuid primary key"
      source_id: "foreign key -> Source"
      date_mode: "varchar(20)"
      start_date: "date"
      end_date: "date"
      status: "varchar(20)"
      triggered_by: "varchar(20)"
      total_items: "integer"
      success_items: "integer"
      failed_items: "integer"
      skipped_items: "integer"
      started_at: "timestamp"
      completed_at: "timestamp"
      error_message: "text nullable"
      config_snapshot: "jsonb"
      created_at: "timestamp"

  PolicyDocument:
    table: "policy_documents"
    fields:
      id: "uuid primary key"
      source_id: "foreign key -> Source"
      external_id: "varchar(255) nullable"
      title: "text"
      slug: "varchar(500) nullable"
      document_type: "varchar(50)"
      publication_date: "date"
      effective_date: "date nullable"
      signing_date: "date nullable"
      canonical_url: "text"
      pdf_url: "text nullable"
      raw_text_url: "text nullable"
      summary: "text nullable"
      content: "text"
      raw_content: "jsonb nullable"
      content_checksum: "varchar(64)"
      language: "varchar(10)"
      crawl_job_id: "foreign key -> CrawlJob"
      analysis_status: "varchar(20)"
      created_at: "timestamp"
      updated_at: "timestamp"
    unique_constraints:
      - ["source_id", "external_id"]
      - ["source_id", "canonical_url"]

  GovernmentAgency:
    table: "government_agencies"
    fields:
      id: "bigint primary key"
      name: "varchar(255)"
      short_name: "varchar(100) nullable"
      federal_register_slug: "varchar(255) nullable"
      created_at: "timestamp"

  PolicyDocumentAgency:
    table: "policy_document_agencies"
    fields:
      policy_document_id: "foreign key -> PolicyDocument"
      agency_id: "foreign key -> GovernmentAgency"
      is_primary: "boolean"

  Industry:
    table: "industries"
    fields:
      id: "bigint primary key"
      code: "varchar(50) unique"
      name_zh_tw: "varchar(255)"
      name_en: "varchar(255)"
      parent_id: "self foreign key nullable"
      description: "text nullable"
      keywords: "jsonb"
      is_active: "boolean"
      created_at: "timestamp"
      updated_at: "timestamp"

  PolicyIndustrySignal:
    table: "policy_industry_signals"
    fields:
      id: "uuid primary key"
      policy_document_id: "foreign key -> PolicyDocument"
      industry_id: "foreign key -> Industry"
      signal_direction: "varchar(20)"
      signal_strength: "decimal(5,2)"
      relevance_score: "decimal(5,2)"
      confidence_score: "decimal(5,2)"
      policy_action: "varchar(100)"
      beneficiary_reason: "text"
      risk_reason: "text nullable"
      evidence: "jsonb"
      analysis_version: "varchar(50)"
      created_at: "timestamp"

  PolicyMatch:
    table: "policy_matches"
    fields:
      id: "uuid primary key"
      white_house_document_id: "foreign key -> PolicyDocument"
      federal_register_document_id: "foreign key -> PolicyDocument"
      keyword_score: "decimal(5,2)"
      agency_score: "decimal(5,2)"
      date_score: "decimal(5,2)"
      semantic_score: "decimal(5,2)"
      total_match_score: "decimal(5,2)"
      match_status: "varchar(20)"
      match_reason: "text"
      manually_verified: "boolean"
      created_at: "timestamp"
      updated_at: "timestamp"

  Company:
    table: "companies"
    fields:
      id: "uuid primary key"
      name: "varchar(255)"
      ticker: "varchar(30)"
      exchange: "varchar(50)"
      country: "varchar(100)"
      website: "text nullable"
      description: "text nullable"
      market_cap: "decimal nullable"
      is_active: "boolean"
      created_at: "timestamp"
      updated_at: "timestamp"
    unique_constraints:
      - ["ticker", "exchange"]

  CompanyIndustry:
    table: "company_industries"
    fields:
      company_id: "foreign key -> Company"
      industry_id: "foreign key -> Industry"
      relation_type: "varchar(30)"
      revenue_exposure_percent: "decimal(5,2) nullable"
      evidence: "jsonb nullable"

  CompanyPolicyScore:
    table: "company_policy_scores"
    fields:
      id: "uuid primary key"
      company_id: "foreign key -> Company"
      industry_id: "foreign key -> Industry"
      score_date: "date"
      white_house_support_score: "decimal(5,2)"
      federal_register_score: "decimal(5,2)"
      business_relevance_score: "decimal(5,2)"
      company_action_score: "decimal(5,2)"
      financial_growth_score: "decimal(5,2)"
      contract_subsidy_score: "decimal(5,2)"
      valuation_score: "decimal(5,2)"
      risk_score: "decimal(5,2)"
      total_score: "decimal(5,2)"
      score_details: "jsonb"
      created_at: "timestamp"
    unique_constraints:
      - ["company_id", "industry_id", "score_date"]

  IndustryTrendScore:
    table: "industry_trend_scores"
    fields:
      id: "uuid primary key"
      industry_id: "foreign key -> Industry"
      score_date: "date"
      white_house_document_count: "integer"
      federal_register_document_count: "integer"
      final_rule_count: "integer"
      proposed_rule_count: "integer"
      notice_count: "integer"
      positive_signal_count: "integer"
      negative_signal_count: "integer"
      momentum_30d: "decimal(6,2)"
      momentum_90d: "decimal(6,2)"
      total_score: "decimal(5,2)"
      score_details: "jsonb"
      created_at: "timestamp"

industry_taxonomy:
  initial_industries:
    - code: "AI_INFRASTRUCTURE"
      name_zh_tw: "AI 基礎設施"
      name_en: "AI Infrastructure"

    - code: "SEMICONDUCTORS"
      name_zh_tw: "半導體"
      name_en: "Semiconductors"

    - code: "DATA_CENTERS"
      name_zh_tw: "資料中心"
      name_en: "Data Centers"

    - code: "ELECTRIC_GRID"
      name_zh_tw: "電網與電力設備"
      name_en: "Electric Grid"

    - code: "NUCLEAR_ENERGY"
      name_zh_tw: "核能"
      name_en: "Nuclear Energy"

    - code: "NATURAL_GAS"
      name_zh_tw: "天然氣"
      name_en: "Natural Gas"

    - code: "CRITICAL_MINERALS"
      name_zh_tw: "關鍵礦物"
      name_en: "Critical Minerals"

    - code: "STEEL_ALUMINUM"
      name_zh_tw: "鋼鐵與鋁"
      name_en: "Steel and Aluminum"

    - code: "DEFENSE"
      name_zh_tw: "國防"
      name_en: "Defense"

    - code: "SHIPBUILDING"
      name_zh_tw: "造船與海事"
      name_en: "Shipbuilding"

    - code: "COMMERCIAL_SPACE"
      name_zh_tw: "商業太空"
      name_en: "Commercial Space"



policy_analysis_schema:
  output_format: "json"
  fields:
    document_summary:
      type: "string"

    industries:
      type: "array"
      items:
        industry_code: "string"
        direction:
          type: "string"
          allowed:
            - "positive"
            - "negative"
            - "mixed"
            - "neutral"
        relevance_score:
          type: "number"
          min: 0
          max: 100
        confidence_score:
          type: "number"
          min: 0
          max: 100
        reason: "string"
        evidence_quotes:
          type: "array"
          items: "string"

    policy_actions:
      type: "array"
      allowed_values:
        - "executive_order"
        - "fact_sheet"
        - "tariff"
        - "subsidy"
        - "tax_credit"
        - "government_procurement"
        - "investment"
        - "permit_acceleration"
        - "export_control"
        - "import_restriction"
        - "domestic_production"
        - "research_funding"
        - "investigation"
        - "final_rule"
        - "proposed_rule"
        - "notice"
        - "other"

    agencies:
      type: "array"
      items: "string"

    companies_mentioned:
      type: "array"
      items:
        company_name: "string"
        ticker: "string nullable"
        context: "string"

    monetary_amounts:
      type: "array"
      items:
        amount: "number"
        currency: "string"
        context: "string"

    geographic_scope:
      type: "array"
      items: "string"

    time_horizon:
      type: "string"
      allowed:
        - "immediate"
        - "short_term"
        - "medium_term"
        - "long_term"
        - "unknown"

    risk_flags:
      type: "array"
      items: "string"

policy_matching:
  candidate_filter:
    maximum_date_gap_days: 180
    require_shared_industry: true
    require_shared_keyword: false
  scoring:
    keyword_similarity:
      weight: 0.25
    agency_similarity:
      weight: 0.15
    publication_date_proximity:
      weight: 0.10
    industry_similarity:
      weight: 0.20
    vector_similarity:
      weight: 0.30
  thresholds:
    automatic_match: 80
    review_required: 60
    no_match_below: 60

industry_scoring:
  total_score: 100
  weights:
    white_house_policy_support: 20
    federal_register_implementation: 25
    recent_policy_momentum: 15
    policy_consistency: 10
    funding_and_procurement: 15
    company_action_signal: 10
    negative_policy_risk: 5

  federal_register_document_scores:
    presidential_document: 60
    notice: 45
    proposed_rule: 65
    interim_final_rule: 85
    final_rule: 100

  momentum_windows:
    - 30
    - 90
    - 180

company_scoring:
  total_score: 100
  weights:
    white_house_policy_support: 15
    federal_register_implementation: 20
    business_relevance: 15
    company_action: 15
    financial_growth: 15
    government_contract_or_subsidy: 10
    valuation: 5
    risk_adjustment: 5

  minimum_requirements:
    business_relevance_score: 60
    policy_support_score: 40
    financial_data_required: true
    active_company_required: true

  rating_levels:
    - min_score: 85
      label: "高度研究價值"

    - min_score: 70
      max_score: 84.99
      label: "值得深入研究"

    - min_score: 55
      max_score: 69.99
      label: "列入觀察"

    - min_score: 0
      max_score: 54.99
      label: "政策關聯不足"

api:
  base_path: "/api"
  authentication:
    type: "JWT"
    library: "djangorestframework-simplejwt"

  endpoints:
    auth:
      - method: "POST"
        path: "/auth/login/"
        description: "使用者登入"

      - method: "POST"
        path: "/auth/token/refresh/"
        description: "更新 JWT"

    crawl_jobs:
      - method: "GET"
        path: "/crawl-jobs/"
        description: "取得爬蟲工作列表"

      - method: "POST"
        path: "/crawl-jobs/"
        description: "手動建立爬蟲工作"
        request:
          source_codes:
            type: "array"
            example:
              - "WHITE_HOUSE"
              - "FEDERAL_REGISTER"
          date_mode:
            allowed:
              - "environment"
              - "fixed_range"
              - "rolling_days"
          start_date:
            type: "date nullable"
          end_date:
            type: "date nullable"
          lookback_days:
            type: "integer nullable"
          force_recrawl:
            type: "boolean"

      - method: "GET"
        path: "/crawl-jobs/{job_id}/"
        description: "取得工作狀態"

      - method: "POST"
        path: "/crawl-jobs/{job_id}/cancel/"
        description: "取消尚未完成的工作"

    policy_documents:
      - method: "GET"
        path: "/policy-documents/"
        filters:
          - "source"
          - "document_type"
          - "start_date"
          - "end_date"
          - "industry"
          - "agency"
          - "analysis_status"
          - "keyword"

      - method: "GET"
        path: "/policy-documents/{id}/"

      - method: "POST"
        path: "/policy-documents/{id}/reanalyze/"

    policy_matches:
      - method: "GET"
        path: "/policy-matches/"

      - method: "PATCH"
        path: "/policy-matches/{id}/verify/"
        description: "人工確認政策配對"

    industries:
      - method: "GET"
        path: "/industries/"

      - method: "GET"
        path: "/industries/ranking/"

      - method: "GET"
        path: "/industries/{id}/dashboard/"

      - method: "GET"
        path: "/industries/{id}/policy-timeline/"

      - method: "GET"
        path: "/industries/{id}/companies/"

    companies:
      - method: "GET"
        path: "/companies/"

      - method: "GET"
        path: "/companies/ranking/"

      - method: "GET"
        path: "/companies/{id}/"

      - method: "GET"
        path: "/companies/{id}/policy-evidence/"

    settings:
      - method: "GET"
        path: "/settings/crawl/"
        description: "顯示目前後端解析後的爬取設定"

      - method: "POST"
        path: "/settings/crawl/preview/"
        description: "預覽環境變數所產生的日期範圍"

frontend_structure:
  root: "frontend"
  app_router:
    routes:
      "/":
        page: "Dashboard"
        access: "authenticated"

      "/login":
        page: "Login"

      "/policies":
        page: "PolicyDocumentList"

      "/policies/[id]":
        page: "PolicyDocumentDetail"

      "/industries":
        page: "IndustryRanking"

      "/industries/[id]":
        page: "IndustryDashboard"

      "/companies":
        page: "CompanyRanking"

      "/companies/[id]":
        page: "CompanyDetail"

      "/matches":
        page: "PolicyMatchReview"

      "/crawl-jobs":
        page: "CrawlJobManagement"

      "/settings":
        page: "SystemSettings"

  folders:
    - "app"
    - "components"
    - "features"
    - "hooks"
    - "lib"
    - "services"
    - "stores"
    - "types"
    - "utils"

  state_management:
    server_state: "TanStack Query"
    client_state: "Zustand"

  styling:
    framework: "Tailwind CSS"
    component_library: "shadcn/ui"

  charts:
    library: "Apache ECharts"
    chart_types:
      - "政策時間軸"
      - "產業趨勢折線圖"
      - "政策文件類型分布"
      - "公司評分雷達圖"
      - "產業與供應鏈關聯圖"

frontend_pages:
  dashboard:
    components:
      - "DateRangeSummaryCard"
      - "CrawlerStatusCard"
      - "TopIndustryRanking"
      - "TopCompanyRanking"
      - "RecentPolicyDocuments"
      - "PolicySignalTrendChart"
      - "SourceDocumentCountChart"

  crawl_job_management:
    fields:
      - "來源"
      - "日期模式"
      - "開始日期"
      - "結束日期"
      - "回溯天數"
      - "強制重新爬取"
    functions:
      - "使用環境變數執行"
      - "自訂日期執行"
      - "查看執行進度"
      - "查看錯誤訊息"
      - "重新執行失敗工作"

  policy_detail:
    sections:
      - "基本資料"
      - "原始文件連結"
      - "政策摘要"
      - "產業訊號"
      - "受益產業"
      - "負面影響"
      - "政府機關"
      - "關聯公司"
      - "Federal Register 對應文件"
      - "AI 分析證據"

  industry_dashboard:
    sections:
      - "產業總分"
      - "30 日與 90 日動能"
      - "White House 政策數"
      - "Federal Register 文件數"
      - "政策時間軸"
      - "受益供應鏈"
      - "風險供應鏈"
      - "候選公司排行榜"

  company_detail:
    sections:
      - "公司基本資料"
      - "總評分"
      - "各項評分"
      - "受益政策"
      - "政策證據"
      - "業務關聯"
      - "財務資料"
      - "政策風險"

celery_tasks:
  crawler:
    - name: "crawl_white_house"
      queue: "crawler"
      arguments:
        - "crawl_job_id"
        - "start_date"
        - "end_date"

    - name: "crawl_federal_register"
      queue: "crawler"
      arguments:
        - "crawl_job_id"
        - "start_date"
        - "end_date"

    - name: "normalize_policy_document"
      queue: "document_processing"

  analysis:
    - name: "analyze_policy_document"
      queue: "ai"

    - name: "generate_policy_embedding"
      queue: "embedding"

    - name: "match_policy_documents"
      queue: "matching"

    - name: "calculate_industry_scores"
      queue: "analytics"

    - name: "calculate_company_scores"
      queue: "analytics"

  workflow:
    policy_collection_pipeline:
      sequence:
        - "resolve_crawl_date_range"
        - "create_crawl_job"
        - "crawl_white_house"
        - "crawl_federal_register"
        - "normalize_policy_documents"
        - "analyze_policy_documents"
        - "generate_embeddings"
        - "match_policy_documents"
        - "calculate_industry_scores"
        - "calculate_company_scores"
        - "complete_crawl_job"

security:
  authentication:
    method: "JWT"
    access_token_minutes: 30
    refresh_token_days: 7

  authorization:
    roles:
      admin:
        permissions:
          - "manage_users"
          - "manage_settings"
          - "run_crawler"
          - "edit_industries"
          - "edit_companies"
          - "verify_policy_matches"

      analyst:
        permissions:
          - "view_dashboard"
          - "run_crawler"
          - "verify_policy_matches"
          - "edit_analysis"

      viewer:
        permissions:
          - "view_dashboard"
          - "view_policies"
          - "view_industries"
          - "view_companies"

  crawler_security:
    - "限制可爬取網域"
    - "驗證重新導向後的網域"
    - "設定請求逾時"
    - "限制回應內容大小"
    - "避免 SSRF"
    - "遵守 robots.txt"
    - "保留來源 URL"

  secrets:
    rules:
      - "Secret 不得提交至 Git"
      - "前端不得存放 Django Secret Key"
      - "AI API Key 只能存在後端"
      - "PostgreSQL 密碼只能存在後端"
      - "Qdrant API Key 只能存在後端"

logging:
  format: "json"
  levels:
    development: "DEBUG"
    production: "INFO"
  fields:
    - "timestamp"
    - "level"
    - "module"
    - "crawl_job_id"
    - "policy_document_id"
    - "task_id"
    - "message"
    - "exception"
  retention_days: 90

monitoring:
  health_checks:
    - path: "/health/"
      checks:
        - "django"
        - "postgresql"
        - "redis"
        - "qdrant"

    - path: "/health/ready/"
      checks:
        - "database_migrations"
        - "celery_worker"
        - "required_environment_variables"

  metrics:
    - "crawl_job_success_rate"
    - "crawl_document_count"
    - "crawl_failure_count"
    - "average_document_processing_time"
    - "ai_analysis_failure_rate"
    - "policy_match_count"
    - "api_response_time"

testing:
  backend:
    framework: "pytest"
    libraries:
      - "pytest-django"
      - "factory-boy"
      - "responses"
    test_types:
      - "unit"
      - "integration"
      - "api"
      - "crawler_parser"
      - "date_range_resolver"
      - "scoring"

  frontend:
    framework:
      unit: "Vitest"
      component: "React Testing Library"
      end_to_end: "Playwright"

  required_test_cases:
    - "固定日期模式正確解析"
    - "結束日期空白時使用當日"
    - "滾動日期模式正確回溯"
    - "開始日期晚於結束日期時拒絕執行"
    - "重複 URL 不重複新增"
    - "相同 checksum 不重複新增"
    - "Federal Register API 分頁正確"
    - "爬蟲工作失敗後可重新執行"
    - "Final Rule 分數高於 Proposed Rule"
    - "負面政策正確降低公司分數"

deployment:
  development:
    orchestration: "Docker Compose"
    services:
      - "frontend"
      - "backend"
      - "celery_worker"
      - "celery_beat"
      - "postgres"
      - "redis"
      - "qdrant"

  production:
    frontend:
      platform: "Vercel"
      environment_variables:
        - "NEXT_PUBLIC_API_BASE_URL"
        - "NEXT_PUBLIC_APP_NAME"

    backend:
      platform_options:
        - "GCP Cloud Run"
        - "Render"
      process:
        web: "gunicorn config.wsgi:application"
        worker: "celery -A config worker -l info"
        beat: "celery -A config beat -l info"

    database:
      platform_options:
        - "GCP Cloud SQL PostgreSQL"
        - "Neon"
        - "Supabase PostgreSQL"

    redis:
      platform_options:
        - "GCP Memorystore"
        - "Upstash Redis"
        - "Render Redis"

    qdrant:
      platform_options:
        - "Qdrant Cloud"
        - "GCP VM Docker"

docker_compose:
  services:
    frontend:
      build: "./frontend"
      ports:
        - "3000:3000"
      environment:
        NEXT_PUBLIC_API_BASE_URL: "http://localhost:8000/api"
      depends_on:
        - "backend"

    backend:
      build: "./backend"
      command: "python manage.py runserver 0.0.0.0:8000"
      ports:
        - "8000:8000"
      env_file:
        - ".env"
      depends_on:
        - "postgres"
        - "redis"
        - "qdrant"

    celery_worker:
      build: "./backend"
      command: "celery -A config worker -l info"
      env_file:
        - ".env"
      depends_on:
        - "backend"
        - "redis"
        - "postgres"

    celery_beat:
      build: "./backend"
      command: "celery -A config beat -l info"
      env_file:
        - ".env"
      depends_on:
        - "backend"
        - "redis"
        - "postgres"

    postgres:
      image: "postgres:16"
      environment:
        POSTGRES_DB: "policy_db"
        POSTGRES_USER: "policy_user"
        POSTGRES_PASSWORD: "policy_password"
      ports:
        - "5432:5432"
      volumes:
        - "postgres_data:/var/lib/postgresql/data"

    redis:
      image: "redis:7-alpine"
      ports:
        - "6379:6379"

    qdrant:
      image: "qdrant/qdrant:latest"
      ports:
        - "6333:6333"
        - "6334:6334"
      volumes:
        - "qdrant_data:/qdrant/storage"

  volumes:
    postgres_data: {}
    qdrant_data: {}

env_example: |
  # Django
  DJANGO_ENV=development
  DJANGO_SECRET_KEY=change-me
  DJANGO_DEBUG=true
  DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
  DJANGO_CORS_ALLOWED_ORIGINS=http://localhost:3000

  # Crawl date mode
  # fixed_range 或 rolling_days
  CRAWL_DATE_MODE=rolling_days

  # fixed_range 模式使用
  CRAWL_START_DATE=2026-01-01
  CRAWL_END_DATE=2026-06-29

  # rolling_days 模式使用
  CRAWL_LOOKBACK_DAYS=30

  CRAWL_DATE_TIMEZONE=America/New_York
  CRAWL_INCLUDE_TODAY=true
  CRAWL_FORCE_RECRAWL=false

  # Schedule
  CRAWL_SCHEDULE_ENABLED=true
  CRAWL_SCHEDULE_CRON=0 7 * * *
  POLICY_ANALYSIS_CRON=30 7 * * *
  SCORE_RECALCULATION_CRON=0 8 * * *

  # Crawler
  CRAWL_BATCH_SIZE=50
  CRAWL_REQUEST_DELAY_SECONDS=1.5
  CRAWL_MAX_RETRIES=3
  CRAWL_REQUEST_TIMEOUT_SECONDS=30

  # White House
  WHITE_HOUSE_BASE_URL=https://www.whitehouse.gov
  WHITE_HOUSE_SITEMAP_URL=https://www.whitehouse.gov/sitemap_index.xml
  WHITE_HOUSE_CRAWL_ENABLED=true
  WHITE_HOUSE_CRAWL_SECTIONS=fact-sheets,presidential-actions,briefings-statements,releases
  WHITE_HOUSE_USER_AGENT=PolicyResearchBot/1.0
  WHITE_HOUSE_USE_PLAYWRIGHT=false

  # Federal Register
  FEDERAL_REGISTER_API_BASE_URL=https://www.federalregister.gov/api
  FEDERAL_REGISTER_CRAWL_ENABLED=true
  FEDERAL_REGISTER_DOCUMENT_TYPES=RULE,PRORULE,NOTICE,PRESDOCU
  FEDERAL_REGISTER_PER_PAGE=100
  FEDERAL_REGISTER_MAX_PAGES=100
  FEDERAL_REGISTER_AGENCIES=

  # PostgreSQL
  DATABASE_URL=postgresql://policy_user:policy_password@postgres:5432/policy_db

  # Redis and Celery
  REDIS_URL=redis://redis:6379/0
  CELERY_BROKER_URL=redis://redis:6379/0
  CELERY_RESULT_BACKEND=redis://redis:6379/0

  # Qdrant
  QDRANT_URL=http://qdrant:6333
  QDRANT_API_KEY=
  QDRANT_COLLECTION_POLICY_DOCUMENTS=policy_documents
  QDRANT_COLLECTION_COMPANIES=companies

  # AI
  AI_PROVIDER=openai
  AI_API_KEY=
  AI_MODEL=gpt-5-mini
  EMBEDDING_PROVIDER=openai
  EMBEDDING_MODEL=text-embedding-3-small
  AI_ANALYSIS_ENABLED=true
  AI_MAX_DOCUMENT_LENGTH=60000
  AI_TEMPERATURE=0.1

  # Frontend
  NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
  NEXT_PUBLIC_APP_NAME=美國政策產業雷達
  NEXT_PUBLIC_DEFAULT_LOCALE=zh-TW
  NEXT_PUBLIC_DEFAULT_TIMEZONE=Asia/Taipei

management_commands:
  - command: >
      python manage.py crawl_policies
      --use-env-dates
    description: "依環境變數日期執行所有來源爬蟲"

  - command: >
      python manage.py crawl_policies
      --source white_house
      --start-date 2026-01-01
      --end-date 2026-06-29
    description: "手動指定 White House 爬取日期"

  - command: >
      python manage.py crawl_policies
      --source federal_register
      --lookback-days 90
    description: "手動回溯 90 天"

  - command: >
      python manage.py analyze_pending_policies
    description: "分析尚未處理的政策文件"

  - command: >
      python manage.py match_policy_documents
    description: "配對 White House 與 Federal Register 文件"

  - command: >
      python manage.py recalculate_scores
    description: "重新計算產業與公司分數"

acceptance_criteria:
  phase_1:
    name: "政策資料蒐集 MVP"
    requirements:
      - "可以從環境變數讀取爬取日期"
      - "支援固定日期與回溯天數模式"
      - "可以爬取 White House 四類政策文件"
      - "可以取得 Federal Register 四類文件"
      - "可以保存原始資料與正文"
      - "可以依 URL、文件編號與 checksum 去重"
      - "Next.js 可以查看政策文件列表"
      - "可以從前端手動啟動爬蟲工作"

  phase_2:
    name: "AI 政策分析"
    requirements:
      - "可以抽取產業、政策動作與政府機關"
      - "可以判斷正面、負面與混合政策"
      - "可以產生政策摘要"
      - "可以比對 White House 與 Federal Register 文件"
      - "可以人工確認配對結果"

  phase_3:
    name: "公司與產業排名"
    requirements:
      - "可以建立產業與供應鏈分類"
      - "可以建立公司與產業關係"
      - "可以產生產業趨勢分數"
      - "可以產生公司政策關聯分數"
      - "前端可顯示產業與公司排行榜"
      - "每個分數必須顯示計算依據與政策來源"