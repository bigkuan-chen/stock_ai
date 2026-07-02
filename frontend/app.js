const api = {
  dashboard: "/api/dashboard",
  run: "/api/run-analysis",
  status: "/api/analysis-status",
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
  const value = Number.parseInt(lookbackInput().value, 10);
  if (!Number.isFinite(value) || value < 1) {
    throw new Error("Lookback days 必須是大於 0 的整數");
  }
  return value;
}

function setSummary(data) {
  document.querySelector("#policyCount").textContent = data.summary.policies;
  document.querySelector("#industryCount").textContent = data.summary.industries;
  document.querySelector("#companyCount").textContent = data.summary.companies;
  document.querySelector("#updatedAt").textContent = text(data.updated_at);
  if (!lookbackInput().value && data.lookback_days) {
    lookbackInput().value = data.lookback_days;
  }
}

function setStatus(message) {
  document.querySelector("#analysisStatus").textContent = message;
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
  const response = await fetch(api.dashboard);
  if (!response.ok) throw new Error("dashboard request failed");
  const data = await response.json();
  setSummary(data);
  document.querySelector("#industryList").innerHTML = data.top_industries.map(industryItem).join("");
  document.querySelector("#companyList").innerHTML = data.top_companies.map(companyItem).join("");
  document.querySelector("#policyList").innerHTML = data.recent_policies.map(policyItem).join("");
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
  const input = lookbackInput();
  const lookbackDays = currentLookbackDays();
  button.disabled = true;
  input.disabled = true;
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
    input.disabled = false;
    button.textContent = "重新分析";
  }
}

document.querySelector("#refreshBtn").addEventListener("click", rerunAnalysis);
loadDashboard().catch((error) => {
  document.querySelector("main").insertAdjacentHTML(
    "afterbegin",
    `<section class="panel"><strong>載入失敗</strong><p class="summary">${error.message}</p></section>`,
  );
});
