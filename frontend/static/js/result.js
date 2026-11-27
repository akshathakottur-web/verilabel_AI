(function () {
  const user = requireLogin(["customer"]);
  if (!user) return;
  renderNavbar("");

  const id = new URLSearchParams(window.location.search).get("id");
  const msg = document.getElementById("msg");
  const loading = document.getElementById("loading");

  function cell(row, text) {
    const td = document.createElement("td");
    td.textContent = text;
    row.appendChild(td);
    return td;
  }
  function item(listEl, text) {
    const li = document.createElement("li");
    li.textContent = text;
    listEl.appendChild(li);
  }

  function render(r) {
    // The real field names come from mocks/scan_record_sample.json. Fix them here if they differ.
    const rules = r.rules || (r.compliance && r.compliance.rules) || [];
    const score = (r.score !== undefined && r.score !== null) ? r.score
      : (r.compliance ? r.compliance.score : null);
    const verdict = r.verdict || (r.compliance && r.compliance.verdict) || "";
    const quality = r.image_quality || {};

    loading.classList.add("hidden");
    document.getElementById("resultBox").classList.remove("hidden");

    document.getElementById("productName").textContent = r.product_name || "Unknown product";
    document.getElementById("verdict").textContent = verdict;
    const hasScore = score !== null && score !== undefined;
    document.getElementById("score").textContent = hasScore ? String(score) : "N/A";
    if (hasScore) {
      document.getElementById("ring").setAttribute("stroke-dasharray", (score / 100 * 326.7) + " 327");
    }

    if (quality.status === "too_low") {
      const banner = document.getElementById("qualityBanner");
      banner.textContent = "Warning: " + (quality.reason || "The photo quality is too low.") + " Please take a clearer photo and try again.";
      banner.classList.remove("hidden");
    }

    const body = document.getElementById("rulesBody");
    rules.forEach(function (rule) {
      const row = document.createElement("tr");
      cell(row, rule.name);
      const td = document.createElement("td");
      const badge = document.createElement("span");
      badge.className = "badge " + (rule.result === "PASS" ? "pass" : "fail");
      badge.textContent = rule.result;
      td.appendChild(badge);
      row.appendChild(td);
      cell(row, rule.reason || "");
      body.appendChild(row);
    });

    const list = document.getElementById("missingList");
    const failed = rules.filter(function (x) { return x.result === "FAIL"; });
    if (rules.length === 0) item(list, "No items could be checked for this photo.");
    else if (failed.length === 0) item(list, "No missing items. Everything mandatory was found.");
    else failed.forEach(function (x) { item(list, x.name + ": " + (x.reason || "")); });
  }

  async function loadAlternatives() {
    const box = document.getElementById("altBox");
    const res = await apiGet("alternatives", id);
    box.textContent = "";
    const data = res.ok ? res.data : [];
    const list = Array.isArray(data) ? data : (data.alternatives || []);
    if (!res.ok || list.length === 0) {
      const p = document.createElement("p");
      p.className = "up-muted";
      p.textContent = "No alternatives available for this product.";
      box.appendChild(p);
      return;
    }
    list.forEach(function (a) {
      const div = document.createElement("div");
      div.className = "alt-item";
      const strong = document.createElement("strong");
      strong.textContent = a.name;
      div.appendChild(strong);
      div.appendChild(document.createTextNode(" (" + (a.category || "") + "): " + (a.why || "")));
      box.appendChild(div);
    });
  }

  document.getElementById("pdfBtn").addEventListener("click", async function () {
    const out = document.getElementById("pdfMsg");
    out.textContent = "";
    const res = await apiDownload("report", id, "verilabel-report-" + id + ".pdf");
    if (!res.ok) out.textContent = res.error;
  });

  async function load() {
    if (!id) { loading.classList.add("hidden"); msg.textContent = "No scan found. Please upload a photo first."; return; }
    const res = await apiGet("scan", id);
    if (!res.ok) { loading.classList.add("hidden"); msg.textContent = res.error; return; }
    render(res.data);
    loadAlternatives();
  }
  load();
})();