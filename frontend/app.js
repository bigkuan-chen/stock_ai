const api = {
  dashboard: "/api/dashboard",
  run: "/api/run-analysis",
  status: "/api/analysis-status",
  getMacro: "/api/get-macro-data/",
  updateMacro: "/api/update-macro-data/",
};

const fmt = new Intl.NumberFormat("zh-TW", { maximumFractionDigits: 1 });
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function text(value) {
  return value === undefined || value === null || value === "" ? "-" : String(value);
}

function lookbackInput() {
  return document.querySelector("#lookbackDaysInput");
}

function currentLookbackDays() {
  const input = lookbackInput();
  if (!input) return 30; // Default fallback
  const value = Number.parseInt(input.value, 10);
  if (!Number.isFinite(value) || value < 1) {
    throw new Error("Lookback days 必須是大於 0 的整數");
  }
  return value;
}

function setSummary(data) {
  const policyCount = document.querySelector("#policyCount");
  const industryCount = document.querySelector("#industryCount");
  const companyCount = document.querySelector("#companyCount");
  const updatedAt = document.querySelector("#updatedAt");
  const input = lookbackInput();

  if (policyCount) policyCount.textContent = data.summary.policies;
  if (industryCount) industryCount.textContent = data.summary.industries;
  if (companyCount) companyCount.textContent = data.summary.companies;
  if (updatedAt) updatedAt.textContent = text(data.updated_at);
  if (input && !input.value && data.lookback_days) {
    input.value = data.lookback_days;
  }
}

function setStatus(message) {
  const status = document.querySelector("#analysisStatus");
  if (status) status.textContent = message;
}


function industryItem(item) {
  const drivers = item.key_drivers.slice(0, 3).map((driver) => `<span class="chip">${driver}</span>`).join("");
  return `
    <article class="item">
      <div class="row">
        <div>
          <div class="name">${item.name}</div>
          <div class="meta">Policies ${item.policy_count} | Positive ${item.positive_signals} | Risk ${item.risk_signals}</div>
        </div>
        <div class="score">${fmt.format(item.score)}</div>
      </div>
      <div class="bar" aria-hidden="true"><span style="--value: ${Math.max(item.score, 2)}%"></span></div>
      <div class="chips">${drivers}</div>
    </article>
  `;
}

function companyMeta(item) {
  const stockMeta = [item.exchange, item.sector, item.stock_industry]
    .filter((value) => value && value !== "N/A")
    .join(" | ");
  const related = Array.isArray(item.related_industries) && item.related_industries.length
    ? `Policy industries: ${item.related_industries.join(", ")}`
    : `Policy industry: ${item.industry_name}`;
  return stockMeta ? `${stockMeta} | ${related}` : related;
}

function companyItem(item) {
  return `
    <article class="item">
      <div class="row">
        <div>
          <div class="name">${item.ticker} | ${item.name}</div>
          <div class="meta">${companyMeta(item)}</div>
        </div>
        <div class="score">${fmt.format(item.score)}</div>
      </div>
      <p class="summary"><span class="rating">${item.rating}</span>${item.thesis}</p>
    </article>
  `;
}

function policyItem(item) {
  const title = item.url
    ? `<a class="policy-title" href="${item.url}" target="_blank" rel="noreferrer">${item.title}</a>`
    : `<span class="policy-title">${item.title}</span>`;
  return `
    <article class="item">
      ${title}
      <div class="meta">${item.source} | ${item.document_type} | ${item.published_date}</div>
      <p class="summary">${item.summary}</p>
    </article>
  `;
}

async function loadDashboard() {
  const indList = document.querySelector("#industryList");
  const compList = document.querySelector("#companyList");
  const polList = document.querySelector("#policyList");
  
  if (!indList && !compList && !polList) return; // Exit if not on homepage
  
  const response = await fetch(api.dashboard);
  if (!response.ok) throw new Error("dashboard request failed");
  const data = await response.json();
  setSummary(data);
  
  if (indList) indList.innerHTML = data.top_industries.map(industryItem).join("");
  if (compList) compList.innerHTML = data.top_companies.map(companyItem).join("");
  if (polList) polList.innerHTML = data.recent_policies.map(policyItem).join("");
}

async function waitForAnalysis() {
  while (true) {
    await sleep(3000);
    const response = await fetch(api.status);
    if (!response.ok) throw new Error("analysis status request failed");
    const job = await response.json();
    if (job.status === "running") {
      setStatus(`分析中，lookback days: ${job.lookback_days || currentLookbackDays()}`);
      continue;
    }
    if (job.status === "failed") {
      throw new Error(job.error || "analysis failed");
    }
    return job;
  }
}

async function rerunAnalysis() {
  const button = document.querySelector("#refreshBtn");
  if (!button) return;
  const input = lookbackInput();
  const lookbackDays = currentLookbackDays();
  button.disabled = true;
  if (input) input.disabled = true;
  button.textContent = "分析中...";
  setStatus(`已開始背景分析，lookback days: ${lookbackDays}`);
  try {
    const params = new URLSearchParams({ lookback_days: String(lookbackDays) });
    const response = await fetch(`${api.run}?${params.toString()}`, { method: "POST" });
    if (!response.ok && response.status !== 202) throw new Error("analysis request failed");
    await waitForAnalysis();
    await loadDashboard();
    setStatus("分析完成");
  } catch (error) {
    setStatus(error.message);
  } finally {
    button.disabled = false;
    if (input) input.disabled = false;
    button.textContent = "重新分析";
  }
}

// Macroeconomic Dashboard Logic
function renderMacroData(data) {
  const statusEl = document.querySelector("#macroStatus");
  const gridEl = document.querySelector("#macroDataGrid");
  if (!statusEl || !gridEl) return;
  
  if (!data || Object.keys(data).length === 0 || (!data.growth && !data.employment && !data.inflation)) {
    statusEl.textContent = "尚未有快取資料，請點擊右方按鈕更新獲取最新數據。";
    statusEl.style.display = "block";
    gridEl.style.display = "none";
    return;
  }
  
  statusEl.style.display = "none";
  gridEl.style.display = "grid";
  
  const DISPLAY_NAMES = {
    GDP: "GDP 實質國內生產毛額",
    Retail_Sales: "零售銷售額",
    ISM_Manufacturing_PMI: "ISM 製造業 PMI",
    ISM_Services_PMI: "ISM 服務業 PMI",
    NFP: "非農就業人口 (NFP)",
    Initial_Jobless_Claims: "每週初領失業金人數",
    Unemployment_Rate: "失業率",
    ADP_Employment: "ADP 就業人數 (小非農)",
    CPI: "CPI 消費者物價指數",
    Core_CPI: "核心 CPI 物價指數",
    PPI: "PPI 生產者物價指數",
    Core_PCE: "核心 PCE 物價指數"
  };
  
  const categories = {
    growth: "經濟成長與景氣 (Growth)",
    employment: "就業市場 (Employment)",
    inflation: "通貨膨脹 (Inflation)"
  };
  
  let html = "";
  for (const [key, label] of Object.entries(categories)) {
    const metrics = data[key] || {};
    let itemHtml = "";
    
    for (const [metricName, info] of Object.entries(metrics)) {
      const obs = info.observations || [];
      const latestObs = obs.length > 0 ? obs[obs.length - 1] : null;
      
      let valStr = "-";
      if (latestObs) {
        valStr = fmt.format(latestObs.value);
        if (metricName === "Unemployment_Rate") {
          valStr += "%";
        }
      }
      
      const dateStr = latestObs ? latestObs.date : "N/A";
      const displayName = DISPLAY_NAMES[metricName] || metricName.replace(/_/g, " ");
      const seriesId = info.series_id || info.source || "";
      const note = info.note || "";
      
      itemHtml += `
        <div class="macro-indicator-item">
          <div class="macro-indicator-details">
            <span class="macro-indicator-name">${displayName}</span>
            <span class="macro-indicator-meta">${seriesId} | ${note}</span>
          </div>
          <div class="macro-indicator-value-container">
            <div class="macro-indicator-value">${valStr}</div>
            <div class="macro-indicator-date">${dateStr}</div>
          </div>
        </div>
      `;
    }
    
    html += `
      <div class="macro-category">
        <h3 class="macro-category-title" style="margin: 0 0 10px; font-size: 15px; font-weight: 800; color: var(--accent); border-bottom: 1px solid var(--line); padding-bottom: 6px;">${label}</h3>
        <div class="macro-indicator-list">
          ${itemHtml || '<p class="meta">無指標資料</p>'}
        </div>
      </div>
    `;
  }
  
  const updateTime = data.updated_at || "未知";
  const sourceLabel = data.is_mock ? " (模擬數據，金鑰未設定)" : "";
  html += `
    <div style="grid-column: 1 / -1; text-align: right; font-size: 12px; color: var(--muted); margin-top: 6px;">
      最後更新時間：${updateTime}${sourceLabel}
    </div>
  `;
  
  gridEl.innerHTML = html;
}

async function loadMacroDashboard() {
  const statusEl = document.querySelector("#macroStatus");
  const gridEl = document.querySelector("#macroDataGrid");
  if (!statusEl || !gridEl) return;
  
  try {
    const response = await fetch(api.getMacro);
    if (!response.ok) {
      if (response.status === 404) {
        statusEl.textContent = "尚未有快取資料，請點擊右方按鈕手動更新。";
        statusEl.style.display = "block";
        gridEl.style.display = "none";
        return;
      }
      throw new Error("無法取得總體經濟數據");
    }
    const data = await response.json();
    renderMacroData(data);
  } catch (error) {
    statusEl.textContent = `載入失敗: ${error.message}`;
    statusEl.style.display = "block";
    gridEl.style.display = "none";
  }
}

async function triggerUpdateMacro() {
  const updateBtn = document.querySelector("#updateMacroBtn");
  const statusEl = document.querySelector("#macroStatus");
  const gridEl = document.querySelector("#macroDataGrid");
  if (!updateBtn || !statusEl || !gridEl) return;
  
  updateBtn.disabled = true;
  updateBtn.textContent = "更新中...";
  statusEl.textContent = "正在向 FRED API 抓取並分析最新數據，請稍候...";
  statusEl.style.display = "block";
  gridEl.style.display = "none";
  
  try {
    const response = await fetch(api.updateMacro, { method: "POST" });
    if (!response.ok) throw new Error("更新 API 回傳錯誤");
    const resData = await response.json();
    if (resData.data) {
      renderMacroData(resData.data);
      alert("總體經濟數據更新成功！");
    } else {
      throw new Error(resData.message || "更新失敗");
    }
  } catch (error) {
    alert(`更新失敗: ${error.message}`);
    await loadMacroDashboard();
  } finally {
    updateBtn.disabled = false;
    updateBtn.textContent = "手動更新最新數據";
  }
}

const refreshBtn = document.querySelector("#refreshBtn");
if (refreshBtn) refreshBtn.addEventListener("click", rerunAnalysis);

const updateMacroBtn = document.querySelector("#updateMacroBtn");
if (updateMacroBtn) updateMacroBtn.addEventListener("click", triggerUpdateMacro);

loadDashboard().catch((error) => {
  const main = document.querySelector("main");
  if (main) {
    main.insertAdjacentHTML(
      "afterbegin",
      `<section class="panel"><strong>載入失敗</strong><p class="summary">${error.message}</p></section>`,
    );
  }
});

loadMacroDashboard();
