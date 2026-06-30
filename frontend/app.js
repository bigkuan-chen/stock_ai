const api = {
  dashboard: "/api/dashboard",
  run: "/api/run-analysis",
};

const fmt = new Intl.NumberFormat("zh-TW", { maximumFractionDigits: 1 });

function text(value) {
  return value === undefined || value === null || value === "" ? "-" : String(value);
}

function setSummary(data) {
  document.querySelector("#policyCount").textContent = data.summary.policies;
  document.querySelector("#industryCount").textContent = data.summary.industries;
  document.querySelector("#companyCount").textContent = data.summary.companies;
  document.querySelector("#updatedAt").textContent = text(data.updated_at);
}

function industryItem(item) {
  const drivers = item.key_drivers.slice(0, 3).map((driver) => `<span class="chip">${driver}</span>`).join("");
  return `
    <article class="item">
      <div class="row">
        <div>
          <div class="name">${item.name}</div>
          <div class="meta">政策 ${item.policy_count} 件 · 正向訊號 ${item.positive_signals} · 風險 ${item.risk_signals}</div>
        </div>
        <div class="score">${fmt.format(item.score)}</div>
      </div>
      <div class="bar" aria-hidden="true"><span style="--value: ${Math.max(item.score, 2)}%"></span></div>
      <div class="chips">${drivers}</div>
    </article>
  `;
}

function companyItem(item) {
  return `
    <article class="item">
      <div class="row">
        <div>
          <div class="name">${item.ticker} · ${item.name}</div>
          <div class="meta">${item.exchange} · ${item.industry_name}</div>
        </div>
        <div class="score">${fmt.format(item.score)}</div>
      </div>
      <p class="summary"><span class="rating">${item.rating}</span>：${item.thesis}</p>
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
      <div class="meta">${item.source} · ${item.document_type} · ${item.published_date}</div>
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

async function rerunAnalysis() {
  const button = document.querySelector("#refreshBtn");
  button.disabled = true;
  button.textContent = "分析中";
  try {
    await fetch(api.run, { method: "POST" });
    await loadDashboard();
  } finally {
    button.disabled = false;
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
