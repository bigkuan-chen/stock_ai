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
- `GET /api/stockcomps`

### 重新分析 (Re-analysis) API 規格

當其他專案需要觸發重新分析並確認進度時，可使用以下兩個 API。

#### 1. 觸發非同步分析 (Trigger Re-analysis)
- **方法**: `POST` (或 `GET`)
- **路徑**: `/api/run-analysis`
- **查詢參數 (Query Parameters)**:
  - `lookback_days` (整數，選填，預設為 `30` 或 `.env` 中 `CRAWL_LOOKBACK_DAYS` 的設定值): 回溯爬取天數。
  - `offline` (布林值，選填，預設為 `false`): 是否使用本機樣本作離線測試（不進行真實爬蟲）。
- **回傳狀態碼**: `202 Accepted`
- **回傳範例 (JSON)**:
  ```json
  {
    "status": "running",
    "started_at": 1712345678.9,
    "finished_at": null,
    "error": null,
    "lookback_days": 30,
    "offline": false
  }
  ```

#### 2. 查詢分析進度 (Query Analysis Status)
- **方法**: `GET`
- **路徑**: `/api/analysis-status`
- **回傳狀態碼**: `200 OK`
- **回傳範例 (JSON)**:
  - **進行中 (Running)**:
    ```json
    {
      "status": "running",
      "started_at": 1712345678.9,
      "finished_at": null,
      "error": null,
      "lookback_days": 30,
      "offline": false
    }
    ```
  - **完成 (Completed)**:
    ```json
    {
      "status": "completed",
      "started_at": 1712345678.9,
      "finished_at": 1712345710.2,
      "error": null,
      "lookback_days": 30,
      "offline": false,
      "summary": {
        "policies": 15,
        "industries": 5,
        "companies": 8
      }
    }
    ```
  - **失敗 (Failed)**:
    ```json
    {
      "status": "failed",
      "started_at": 1712345678.9,
      "finished_at": 1712345685.1,
      "error": "Error message details...",
      "lookback_days": 30,
      "offline": false
    }
    ```

#### 串接邏輯說明
1. 其他專案可發送 `POST` 請求到 `/api/run-analysis?lookback_days=30` 啟動背景分析。
2. 每隔 3~5 秒發送 `GET` 請求至 `/api/analysis-status`，檢查返回內容中的 `status` 欄位。
3. 當 `status` 為 `"completed"` 時，即表示分析完成，可再次讀取 `/api/dashboard` 以取得最新結果。

### 3. 取得最新上市公司清單 API (`/api/stockcomps`)

用於讓外部專案取得最新一期分析（`ana_id` 最大號）的上市公司資料。

- **方法**: `GET`
- **路徑**: `/api/stockcomps`
- **回傳狀態碼**: `200 OK`
- **回傳範例 (JSON)**:
  ```json
  [
    {
      "ticker": "GD",
      "name": "General Dynamics Corporation",
      "exchange": "NYSE",
      "industry_code": "defense_aerospace_military",
      "industry_name": "國防 / 航太 / 軍工",
      "sector": "Industrials"
    },
    {
      "ticker": "NNE",
      "name": "NANO Nuclear Energy Inc.",
      "exchange": "NASDAQ",
      "industry_code": "nuclear_uranium_smr",
      "industry_name": "核能 / 鈾 / SMR",
      "sector": "Industrials"
    }
  ]
  ```

---

## 部署與運行資訊 (Deployment Information)

本專案目前已部署於 GCP VM 上，並與原本監聽 Port 8000 的專案整合在同一個 Port 80 下運行。

### 1. 前端存取網址
- **網址**: `http://35.234.20.97/stock_ai/`
- *(註：請務必在結尾加上斜線 `/`，以確保 Nginx 路由正常匹配)*

### 2. 外部 API 呼叫網址
- **最新公司列表**: `http://35.234.20.97/api/stockcomps`
- **健康檢查**: `http://35.234.20.97/api/health`
- **觸發分析**: `http://35.234.20.97/api/run-analysis`
- **分析狀態**: `http://35.234.20.97/api/analysis-status`

## 總體經濟數據看板 (Macroeconomic Data Dashboard)

本專案新增了總體經濟數據看板，專門用於監控與分析美國的核心總體經濟指標。

### 1. 功能特點 (Features)
- **專屬頁面獨立路由**：在首頁 (`/`) 的頂端導覽列新增連結，可無縫導向至獨立看板頁面 `/macro.html`。
- **資料庫持久化儲存 (SQLite)**：
  - 資料庫使用專案的 SQLite (`stockai.db`)，建立名為 `macro_observations` 的資料表。
  - 設計防重寫限制 `unique_together = ('series_id', 'date')`，即使重複抓取相同日期的觀測值，亦會採更新/覆寫（Upsert）方式處理，避免資料庫膨脹與重疊。
- **台北時區時間對齊 (Asia/Taipei)**：
  - 資料表的更新時間標記 `fetched_at` 捨棄預設的 UTC 時區，改採台北時區 (`Asia/Taipei`) 的格式化時間字串寫入資料庫，維持與 `News` 及 `Company` 模型一致。
- **真實數據與備用模擬機制**：
  - 核心 FRED 指標（如 GDP、零售銷售額、失業率、非農就業 NFP、CPI、PPI、核心 PCE）皆由 St. Louis Fed 的 FRED API 官方端點即時對接取得。
  - **ADP 就業數據**：已串接 FRED 官方最新代碼 `ADPMNUSNERSA`，確保私人企業就業人數呈現真實數值。
  - **ISM 景氣指標**：由於 ISM 製造業與服務業 PMI 指標屬於 proprietary 版權限制數據，無法透過 FRED API 公開抓取，後端設有 Mock 機制自動產生擬真的 24 個月趨勢數據，防止 API 連線錯誤中斷頁面。
  - **全模擬模式**：當環境變數 `.env` 中沒有設定 `FRED_API_KEY` 時，程式會自動無縫切換至全數據 Mock 模式，在頁面上顯著標註「模擬數據」，以供開發者流暢測試。

### 2. API 規格說明 (API Specifications)

#### 1. 取得總體經濟數據 (Get Macro Data)
- **方法**: `GET`
- **路徑**: `/api/get-macro-data/`
- **行為**: 直接向 SQLite 中的 `macro_observations` 資料表進行查詢，依據日期由舊到新排序，動態重組前端所需的 JSON 結構。
- **回傳範例 (JSON)**:
  ```json
  {
    "growth": {
      "GDP": {
        "series_id": "GDPC1",
        "note": "BEA",
        "source": "BEA",
        "observations": [
          {"date": "2024-07-01", "value": 23478.57}
        ]
      }
    },
    "employment": { ... },
    "inflation": { ... },
    "updated_at": "2026-07-10 12:33:06",
    "is_mock": false
  }
  ```

#### 2. 強制手動更新數據 (Update Macro Data)
- **方法**: `POST`
- **路徑**: `/api/update-macro-data/`
- **行為**: 強制向 FRED API 抓取過去 730 天（2 年份）的各項指標數據，寫入 SQLite 資料庫並覆寫同步更新本機 `macro_data.json` 快取備用檔。

---

## Data Sources

- White House: `https://www.whitehouse.gov`
- Federal Register API: `https://www.federalregister.gov/api/v1/documents.json`
- FRED API (Federal Reserve Economic Data): `https://api.stlouisfed.org`

## Notes

This is an intentionally small MVP rather than the full production architecture in `design.md`. It keeps the same domain model and scoring concepts, but avoids required services such as PostgreSQL, Redis, Celery, Qdrant, and an LLM provider until the product workflow is validated.

