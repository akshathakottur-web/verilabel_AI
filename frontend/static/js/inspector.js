(function () {
  const user = requireLogin(["inspector"]);
  if (!user) return;
  renderNavbar("inspector");

  const MAX_FILES = 50;
  const MAX_MB = 10;
  const ALLOWED = ["image/jpeg", "image/png", "image/webp"];
  let chosen = [];
  let openId = null;
  let timer = null;
  let reviewScanId = null;
  let reviewKind = "batch";
  let customerFilter = "pending";
  let customerList = [];
  const expanded = {};

  const tabBatches = document.getElementById("tabBatches");
  const tabCustomers = document.getElementById("tabCustomers");
  const batchSection = document.getElementById("batchSection");
  const customerSection = document.getElementById("customerSection");

  const filesInput = document.getElementById("filesInput");
  const fileList = document.getElementById("fileList");
  const batchBtn = document.getElementById("batchBtn");
  const batchMsg = document.getElementById("batchMsg");
  const batchBody = document.getElementById("batchBody");
  const batchWrap = document.getElementById("batchWrap");
  const batchEmpty = document.getElementById("batchEmpty");
  const listMsg = document.getElementById("listMsg");
  const detailCard = document.getElementById("detailCard");
  const detailTitle = document.getElementById("detailTitle");
  const detailBody = document.getElementById("detailBody");
  const detailMsg = document.getElementById("detailMsg");

  const customerBody = document.getElementById("customerBody");
  const customerWrap = document.getElementById("customerWrap");
  const customerEmpty = document.getElementById("customerEmpty");
  const customerMsg = document.getElementById("customerMsg");
  const filterButtons = {
    pending: document.getElementById("filterPending"),
    reviewed: document.getElementById("filterReviewed"),
    all: document.getElementById("filterAll")
  };

  const modal = document.getElementById("reviewModal");
  const reviewText = document.getElementById("reviewText");
  const reviewMsg = document.getElementById("reviewMsg");
  const reviewOk = document.getElementById("reviewOk");

  function cell(tr, text) {
    const td = document.createElement("td");
    td.textContent = text;
    tr.appendChild(td);
    return td;
  }

  function verdictCell(s) {
    const td = document.createElement("td");
    const v = scanVerdict(s);
    td.appendChild(mk("span", "st-badge " + verdictClass(v), verdictLabel(v)));
    return td;
  }

  // The review column: "Reviewed" details, or the button, or a dash.
  function reviewCell(s, kind) {
    const td = document.createElement("td");
    if (isReviewed(s)) {
      td.appendChild(mk("span", "st-badge good", "Reviewed"));
      td.appendChild(mk("div", "st-small", reviewLine(s)));
      const note = reviewNote(s);
      if (note) td.appendChild(mk("div", "st-small", "Confirmed: " + note));
    } else if (s.status === "done") {
      const b = mk("button", "st-btn st-btn-small", "Mark as reviewed");
      b.type = "button";
      b.addEventListener("click", function () { openReview(scanId(s), kind); });
      td.appendChild(b);
    } else {
      td.textContent = "-";
    }
    return td;
  }

  function detailText(s) {
    const box = mk("div");
    if (s.status === "low_quality") {
      const q = (s.image_quality && s.image_quality.reason) ||
        (s.compliance_result && s.compliance_result.image_quality_warning) || "The photo is too unclear.";
      box.appendChild(mk("p", "", "Photo problem: " + q));
      return box;
    }
    const failed = scanRules(s).filter(function (r) { return ruleResult(r) === "FAIL"; });
    if (failed.length === 0) { box.appendChild(mk("p", "", "No missing items.")); return box; }
    box.appendChild(mk("strong", "", "Missing or failed:"));
    const ul = mk("ul", "st-list");
    failed.forEach(function (r) { ul.appendChild(mk("li", "", ruleName(r) + (r.reason ? ": " + r.reason : ""))); });
    box.appendChild(ul);
    return box;
  }

  // ----- tabs -----
  function showTab(name) {
    const customers = name === "customers";
    batchSection.classList.toggle("hidden", customers);
    customerSection.classList.toggle("hidden", !customers);
    tabBatches.className = "st-btn" + (customers ? " st-btn-light" : "");
    tabCustomers.className = "st-btn" + (customers ? "" : " st-btn-light");
    tabBatches.setAttribute("aria-selected", customers ? "false" : "true");
    tabCustomers.setAttribute("aria-selected", customers ? "true" : "false");
    if (customers) loadCustomerScans();
  }
  tabBatches.addEventListener("click", function () { showTab("batches"); });
  tabCustomers.addEventListener("click", function () { showTab("customers"); });

  // ----- choosing photos -----
  function renderFiles() {
    fileList.textContent = "";
    chosen.forEach(function (f, i) {
      const li = mk("li");
      li.appendChild(mk("span", "", f.name));
      const rm = mk("button", "st-btn st-btn-light st-btn-small", "Remove");
      rm.type = "button";
      rm.setAttribute("aria-label", "Remove " + f.name);
      rm.addEventListener("click", function () { chosen.splice(i, 1); renderFiles(); });
      li.appendChild(rm);
      fileList.appendChild(li);
    });
    batchBtn.disabled = chosen.length === 0;
  }

  document.getElementById("pickBtn").addEventListener("click", function () { filesInput.click(); });

  filesInput.addEventListener("change", function (e) {
    const problems = [];
    Array.prototype.forEach.call(e.target.files, function (f) {
      if (ALLOWED.indexOf(f.type) === -1) { problems.push(f.name + " is not a JPG, PNG or WEBP image."); return; }
      if (f.size > MAX_MB * 1024 * 1024) { problems.push(f.name + " is larger than " + MAX_MB + " MB."); return; }
      if (chosen.length >= MAX_FILES) { problems.push("Only " + MAX_FILES + " photos are allowed per batch."); return; }
      const dup = chosen.some(function (c) { return c.name === f.name && c.size === f.size; });
      if (!dup) chosen.push(f);
    });
    filesInput.value = "";
    batchMsg.textContent = problems.slice(0, 3).join(" ");
    renderFiles();
  });

  batchBtn.addEventListener("click", async function () {
    batchMsg.textContent = "";
    batchBtn.disabled = true;
    batchBtn.textContent = "Uploading...";
    const res = await apiUploadMany(chosen);
    batchBtn.textContent = "Check all labels";
    if (!res.ok) { batchBtn.disabled = false; batchMsg.textContent = res.error; return; }
    const id = res.data.batch_id || res.data.id;
    chosen = [];
    renderFiles();
    await loadBatches();
    if (id) openBatch(id);
  });

  // ----- list of batches -----
  async function loadBatches() {
    const res = await apiGet("inspectorBatches");
    if (!res.ok) { listMsg.textContent = res.error; return; }
    listMsg.textContent = "";
    const list = asList(res.data, "batches");
    batchBody.textContent = "";
    batchEmpty.classList.toggle("hidden", list.length > 0);
    batchWrap.classList.toggle("hidden", list.length === 0);
    list.forEach(function (b) {
      const tr = document.createElement("tr");
      cell(tr, "#" + b.id);
      cell(tr, fmtDate(b.created_at));
      cell(tr, String(b.total));
      cell(tr, String(b.compliant));
      cell(tr, String(b.non_compliant));
      cell(tr, String(b.reviewed));
      const td = document.createElement("td");
      const open = mk("button", "st-btn st-btn-small", "Open");
      open.type = "button";
      open.addEventListener("click", function () { openBatch(b.id); });
      td.appendChild(open);
      tr.appendChild(td);
      batchBody.appendChild(tr);
    });
  }

  // ----- one batch -----
  async function openBatch(id) {
    if (timer) { clearTimeout(timer); timer = null; }
    openId = id;
    const res = await apiGet("inspectorBatch", id);
    detailCard.classList.remove("hidden");
    if (!res.ok) { detailMsg.textContent = res.error; return; }
    detailMsg.textContent = "";
    const scans = asList(res.data, "scans");
    detailTitle.textContent = "Batch #" + id;
    renderDetail(scans);
    const pending = scans.some(function (s) { return s.status === "queued" || s.status === "processing"; });
    if (pending) {
      timer = setTimeout(function () { if (openId === id) openBatch(id); }, 3000);
    } else {
      loadBatches();
    }
  }

  function renderDetail(scans) {
    detailBody.textContent = "";
    scans.forEach(function (s) {
      const sid = s.id(s);
      const tr = document.createElement("tr");
      cell(tr, scanName(s));
      const score = scanScore(s);
      cell(tr, score === null ? "N/A" : score + "/100");
      tr.appendChild(verdictCell(s));

      const st = document.createElement("td");
      st.appendChild(mk("span", "st-badge " + statusClass(s.status), STATUS_LABELS[s.status] || s.status));
      tr.appendChild(st);

      tr.appendChild(reviewCell(s, "batch"));

      const dt = document.createElement("td");
      const toggle = mk("button", "st-btn st-btn-light st-btn-small", expanded[sid] ? "Hide" : "Details");
      toggle.type = "button";
      toggle.addEventListener("click", function () { expanded[sid] = !expanded[sid]; renderDetail(scans); });
      dt.appendChild(toggle);
      tr.appendChild(dt);
      detailBody.appendChild(tr);

      if (expanded[sid]) {
        const row = mk("tr", "st-detail");
        const td = document.createElement("td");
        td.colSpan = 6;
        td.appendChild(detailText(s));
        row.appendChild(td);
        detailBody.appendChild(row);
      }
    });
  }

  // ----- customer scans -----
  function setFilter(name) {
    customerFilter = name;
    Object.keys(filterButtons).forEach(function (k) {
      filterButtons[k].className = "st-btn" + (k === name ? "" : " st-btn-light");
    });
    loadCustomerScans();
  }
  filterButtons.pending.addEventListener("click", function () { setFilter("pending"); });
  filterButtons.reviewed.addEventListener("click", function () { setFilter("reviewed"); });
  filterButtons.all.addEventListener("click", function () { setFilter("all"); });

  async function loadCustomerScans() {
    const res = await apiCustomerScans(customerFilter === "all" ? "" : customerFilter);
    if (!res.ok) { customerMsg.textContent = res.error; return; }
    customerMsg.textContent = "";
    customerList = asList(res.data, "scans");
    renderCustomers();
  }

  function renderCustomers() {
    customerBody.textContent = "";
    customerEmpty.classList.toggle("hidden", customerList.length > 0);
    customerWrap.classList.toggle("hidden", customerList.length === 0);
    customerList.forEach(function (s) {
      const sid = scanId(s);
      const tr = document.createElement("tr");
      cell(tr, uploaderName(s));
      cell(tr, scanName(s));
      const score = scanScore(s);
      cell(tr, score === null ? "N/A" : score + "/100");
      tr.appendChild(verdictCell(s));
      cell(tr, fmtDate(s.created_at));
      tr.appendChild(reviewCell(s, "customer"));

      const dt = document.createElement("td");
      const toggle = mk("button", "st-btn st-btn-light st-btn-small", expanded[sid] ? "Hide" : "Details");
      toggle.type = "button";
      toggle.addEventListener("click", function () { expanded[sid] = !expanded[sid]; renderCustomers(); });
      dt.appendChild(toggle);
      tr.appendChild(dt);
      customerBody.appendChild(tr);

      if (expanded[sid]) {
        const row = mk("tr", "st-detail");
        const td = document.createElement("td");
        td.colSpan = 7;
        td.appendChild(detailText(s));
        row.appendChild(td);
        customerBody.appendChild(row);
      }
    });
  }

  // ----- mark as reviewed -----
  function openReview(scanIdValue, kind) {
    reviewScanId = scanIdValue;
    reviewKind = kind;
    reviewText.value = "";
    reviewMsg.textContent = "";
    modal.classList.remove("hidden");
    reviewText.focus();
  }
  function closeReview() { modal.classList.add("hidden"); reviewScanId = null; }

  document.getElementById("reviewCancel").addEventListener("click", closeReview);
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") closeReview(); });

  reviewOk.addEventListener("click", async function () {
    const text = reviewText.value.trim();
    if (text.length < 3) { reviewMsg.textContent = "Please type your name and designation."; return; }
    reviewOk.disabled = true;
    // Member 1's contract: body {"confirmation": "text"}. Errors come back as 400 {"error": "message"}.
    const res = await apiPostId("inspectorReview", reviewScanId, { confirmation: text });
    reviewOk.disabled = false;
    if (!res.ok) { reviewMsg.textContent = res.error; return; }
    const kind = reviewKind;
    closeReview();
    if (kind === "customer") loadCustomerScans();
    else openBatch(openId);
  });

  loadBatches();
})();