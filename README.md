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

## Data Sources

- White House: `https://www.whitehouse.gov`
- Federal Register API: `https://www.federalregister.gov/api/v1/documents.json`

## Notes

This is an intentionally small MVP rather than the full production architecture in `design.md`. It keeps the same domain model and scoring concepts, but avoids required services such as PostgreSQL, Redis, Celery, Qdrant, and an LLM provider until the product workflow is validated.
