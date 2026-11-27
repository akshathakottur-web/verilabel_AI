(function () {
  const user = requireLogin(["inspector"]);
  if (!user) return;
  renderNavbar("inspector");

  const detailCard = document.getElementById("detailCard");
  const detailMsg = document.getElementById("detailMsg");

  // Make sure the helper files are really loaded.
  const needed = ["asList", "mk", "scanName", "scanScore", "scanVerdict", "verdictLabel", "scanRules", "ruleName",
    "ruleResult", "fmtDate", "statusClass", "isReviewed", "reviewLine", "reviewNote"];
  const missing = needed.filter(function (n) { return typeof window[n] !== "function"; });
  if (missing.length || typeof STATUS_LABELS === "undefined" || typeof InspectorUI === "undefined") {
    detailCard.classList.remove("hidden");
    detailMsg.textContent = "A script file is missing or old. Not found: " + missing.join(", ") +
      ". Check staff-api.js and inspector_common.js.";
    return;
  }

  const MAX_FILES = 50;
  const MAX_MB = 10;
  const ALLOWED = ["image/jpeg", "image/png", "image/webp"];
  let chosen = [];
  let openId = null;
  let timer = null;
  let mineTimer = null;
  let mineScans = [];

  const filesInput = document.getElementById("filesInput");
  const fileList = document.getElementById("fileList");
  const batchBtn = document.getElementById("batchBtn");
  const batchMsg = document.getElementById("batchMsg");
  const batchBody = document.getElementById("batchBody");
  const batchWrap = document.getElementById("batchWrap");
  const batchEmpty = document.getElementById("batchEmpty");
  const listMsg = document.getElementById("listMsg");
  const detailTitle = document.getElementById("detailTitle");
  const detailBody = document.getElementById("detailBody");
  const summary = document.getElementById("detailSummary");
  const mineCounts = document.getElementById("mineCounts");
  const mineEmpty = document.getElementById("mineEmpty");
  const mineWrap = document.getElementById("mineWrap");
  const mineBody = document.getElementById("mineBody");
  const mineMsg = document.getElementById("mineMsg");

  function cell(tr, text) {
    const td = document.createElement("td");
    td.textContent = text;
    tr.appendChild(td);
    return td;
  }

  // After someone marks a scan as reviewed, everything on the page is refreshed.
  function refreshAll() {
    loadMine();
    loadBatches();
    if (openId) openBatch(openId);
  }

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
    const id = res.data.batch_id;
    chosen = [];
    renderFiles();
    await loadBatches();
    loadMine();
    if (id) openBatch(id);
  });

  // ----- My batches: all of this inspector's scans -----
  function drawMine() {
    InspectorUI.renderCounts(mineCounts, mineScans);
    mineEmpty.classList.toggle("hidden", mineScans.length > 0);
    mineWrap.classList.toggle("hidden", mineScans.length === 0);
    InspectorUI.renderScans(mineBody, mineScans, { redraw: drawMine, afterReview: refreshAll });
  }

  async function loadMine() {
    if (mineTimer) { clearTimeout(mineTimer); mineTimer = null; }
    const res = await apiGet("inspectorMyScans");
    if (!res.ok) { mineMsg.textContent = res.error; return; }
    mineMsg.textContent = "";
    mineScans = asList(res.data, "scans");
    drawMine();
    const pending = mineScans.some(function (s) { return s.status === "queued" || s.status === "processing"; });
    if (pending) mineTimer = setTimeout(loadMine, 3000);
  }

  // ----- list of batches -----
  // Real batch row: batch_id, created_at, created_by, total, done, in_progress, failed,
  // compliant, partial, non_compliant, reviewed.
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
      cell(tr, "#" + b.batch_id);
      cell(tr, fmtDate(b.created_at));
      cell(tr, String(b.total));
      cell(tr, String(b.compliant));
      cell(tr, String(b.non_compliant) + (b.partial ? " (+" + b.partial + " partial)" : ""));
      cell(tr, String(b.reviewed));
      const td = document.createElement("td");
      const open = mk("button", "st-btn st-btn-small", "Open");
      open.type = "button";
      open.addEventListener("click", function () { openBatch(b.batch_id); });
      td.appendChild(open);
      tr.appendChild(td);
      batchBody.appendChild(tr);
    });
  }

  // ----- one batch -----
  async function openBatch(id) {
    if (timer) { clearTimeout(timer); timer = null; }
    openId = id;
    detailCard.classList.remove("hidden");
    detailTitle.textContent = "Batch #" + id;
    summary.textContent = "Loading...";
    const res = await apiGet("inspectorBatch", id);
    if (!res.ok) { detailMsg.textContent = res.error; detailBody.textContent = ""; summary.textContent = ""; return; }
    detailMsg.textContent = "";
    const scans = asList(res.data, "scans");

    if (scans.length === 0) {
      detailBody.textContent = "";
      summary.textContent = "This batch has no photos.";
      return;
    }
    showBatch(scans);

    const pending = scans.some(function (s) { return s.status === "queued" || s.status === "processing"; });
    if (pending) {
      timer = setTimeout(function () { if (openId === id) openBatch(id); }, 3000);
    } else {
      loadBatches();
    }
    detailCard.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function count(scans, test) { return scans.filter(test).length; }

  function showBatch(scans) {
    const done = count(scans, function (s) { return s.status === "done"; });
    const unclear = count(scans, function (s) { return s.status === "low_quality"; });
    const failed = count(scans, function (s) { return s.status === "failed"; });
    const waiting = count(scans, function (s) { return s.status === "queued" || s.status === "processing"; });
    const reviewed = count(scans, function (s) { return isReviewed(s); });
    summary.textContent = scans.length + " photos: " + done + " checked, " + unclear + " too unclear, " +
      failed + " failed, " + waiting + " still being checked. " + reviewed + " reviewed.";
    try {
      InspectorUI.renderScans(detailBody, scans, {
        redraw: function () { showBatch(scans); },
        afterReview: refreshAll
      });
    } catch (err) {
      detailMsg.textContent = "Could not show the results: " + err.message;
      console.error(err);
    }
  }

  loadMine();
  loadBatches();
})();