# Implementation Log

## 2026-06-29

### Goal

根據 `design.md` 建立一個可執行的政策產業情報 MVP，用來爬取 White House 與 Federal Register 政策資料，分析產業動向，並找出有潛力的公司。

### Implemented Scope

- 建立一個不依賴外部套件的 Python 後端 MVP。
- 建立一個可由後端直接服務的前端 dashboard。
- 完成「政策資料取得 -> 產業政策動能評分 -> 候選公司評分 -> 前端呈現」的基本流程。
- 加入離線 fallback 樣本資料，避免網路不可用時整個流程無法測試。

### Backend

主要檔案：

- `backend/manage.py`
  - 提供 CLI 指令：
    - `python backend/manage.py analyze --lookback-days 30`
    - `python backend/manage.py analyze --offline --lookback-days 30`
    - `python backend/manage.py serve --host 127.0.0.1 --port 8000`

- `backend/app/api.py`
  - 使用 Python 標準函式庫 `http.server` 建立 API 與靜態檔案服務。
  - 服務 `frontend/index.html`、`frontend/styles.css`、`frontend/app.js`。
  - API endpoints：
    - `GET /api/health`
    - `GET /api/dashboard`
    - `GET /api/policies`
    - `GET /api/industries/ranking`
    - `GET /api/companies/ranking`
    - `POST /api/run-analysis?lookback_days=30`

- `backend/app/crawler.py`
  - 實作 Federal Register API 爬取。
  - 實作 White House 頁面連結與文字抽取。
  - 若線上爬取失敗，回傳內建 sample documents。

- `backend/app/scoring.py`
  - 實作產業分數計算。
  - 實作公司分數計算。
  - 分數來源包含：
    - 政策文件數量
    - 關鍵字命中
    - White House / Federal Register 來源差異
    - 正向政策訊號
    - 風險政策訊號
    - 公司風險扣分

- `backend/app/knowledge_base.py`
  - 定義追蹤產業 `INDUSTRIES`。
  - 定義候選公司 `COMPANIES`。
  - 目前候選公司數量為 10 家。
  - 前端顯示的「候選公司」數量來自這個清單經 API 回傳後的 `summary.companies`。

- `backend/app/pipeline.py`
  - 串接爬取、產業評分、公司評分與資料儲存。

- `backend/app/storage.py`
  - 將分析結果寫入 `backend/data/state.json`。

- `backend/app/models.py`
  - 定義 `PolicyDocument`、`IndustryScore`、`CompanyScore` dataclass。

### Frontend

主要檔案：

- `frontend/index.html`
  - Dashboard 主頁。

- `frontend/styles.css`
  - 儀表板樣式。
  - 包含摘要卡、產業排行、公司排行、政策證據列表。

- `frontend/app.js`
  - 呼叫後端 API。
  - 將 `/api/dashboard` 回傳資料渲染到前端。
  - 「重新分析」按鈕會呼叫 `POST /api/run-analysis?lookback_days=30`。

### Documentation

- `README.md`
  - 新增快速啟動方式、API 列表、資料來源與 MVP 說明。

- `.env.example`
  - 新增環境變數範例。

### Verification

已執行並通過：

```powershell
python -m compileall backend
```

```powershell
python backend/manage.py analyze --offline --lookback-days 30
```

離線分析結果：

```json
{
  "status": "ok",
  "policies": 5,
  "industries": 6,
  "companies": 10
}
```

本機服務驗證：

```text
GET http://127.0.0.1:8000/api/health
```

回傳：

```json
{"status":"ok","updated_at":"2026-06-29"}
```

首頁驗證：

```text
GET http://127.0.0.1:8000/
```

回傳 HTTP `200`。

### Local URL

前端與 API 共用同一個本機服務：

```text
http://127.0.0.1:8000/
```

### Current Limitations

- 目前是 MVP，尚未實作 `design.md` 中完整的 Django、Django REST Framework、Next.js、PostgreSQL、Redis、Celery、Qdrant 架構。
- AI/LLM 分析尚未接入，現在使用關鍵字與規則評分。
- White House 爬取目前是簡化版 HTML 文字抽取。
- 公司候選名單目前是靜態設定在 `backend/app/knowledge_base.py`。
- 尚未實作登入、權限、任務排程、後台管理與長期資料庫儲存。

### Useful Commands

離線重新分析：

```powershell
python backend/manage.py analyze --offline --lookback-days 30
```

線上重新分析：

```powershell
python backend/manage.py analyze --lookback-days 30
```

啟動服務：

```powershell
python backend/manage.py serve --host 127.0.0.1 --port 8000
```

瀏覽器開啟：

```text
http://127.0.0.1:8000/
```
