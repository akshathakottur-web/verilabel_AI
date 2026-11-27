(function () {
  const user = requireLogin(["inspector"]);
  if (!user) return;
  renderNavbar("inspector");
  console.log("inspector_page.js loaded");

  const detailCard = document.getElementById("detailCard");
  const detailMsg = document.getElementById("detailMsg");

  // Make sure the helper file is really loaded.
  const needed = ["asList", "mk", "scanName", "scanScore", "scanVerdict", "scanRules", "ruleName", "ruleResult", "fmtDate", "statusClass"];
  const missing = needed.filter(function (n) { return typeof window[n] !== "function"; });
  if (missing.length || typeof STATUS_LABELS === "undefined") {
    detailCard.classList.remove("hidden");
    detailMsg.textContent = "staff-api.js is missing or old. Not found: " + missing.join(", ") + ". Replace staff-api.js with the latest version.";
    return;
  }

  // Safe fallbacks for the review helpers
  if (typeof isReviewed !== "function") {
    window.isReviewed = function (s) { return !!(s.reviewed || (s.review && s.review.reviewed)); };
  }
  if (typeof reviewLine !== "function") {
    window.reviewLine = function (s) {
      const by = s.reviewed_by || "";
      const at = s.reviewed_at || "";
      let text = by ? "by " + by : "";
      if (at) text += (text ? " on " : "On ") + fmtDate(at);
      return text || "Review details not available";
    };
  }

  const MAX_FILES = 50;
  const MAX_MB = 10;
  const ALLOWED = ["image/jpeg", "image/png", "image/webp"];
  let chosen = [];
  let openId = null;
  let timer = null;
  let reviewScanId = null;
  const expanded = {};

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
  const modal = document.getElementById("reviewModal");
  const reviewText = document.getElementById("reviewText");
  const reviewMsg = document.getElementById("reviewMsg");
  const reviewOk = document.getElementById("reviewOk");
  const summary = document.getElementById("detailSummary");

  function cell(tr, text) {
    const td = document.createElement("td");
    td.textContent = text;
    tr.appendChild(td);
    return td;
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
      renderDetail(scans);
    } catch (err) {
      detailMsg.textContent = "Could not show the results: " + err.message;
      console.error(err);
    }
  }

  function detailText(s) {
    const box = mk("div");
    if (s.status === "low_quality") {
      const q = (s.image_quality && s.image_quality.reason) ||
        (s.compliance_result && s.compliance_result.image_quality_warning) || "The photo is too unclear.";
      box.appendChild(mk("p", "", "Photo problem: " + q));
      return box;
    }
    const failedRules = scanRules(s).filter(function (r) { return ruleResult(r) === "FAIL"; });
    if (failedRules.length === 0) { box.appendChild(mk("p", "", "No missing items.")); return box; }
    box.appendChild(mk("strong", "", "Missing or failed:"));
    const ul = mk("ul", "st-list");
    failedRules.forEach(function (r) { ul.appendChild(mk("li", "", ruleName(r) + (r.reason ? ": " + r.reason : ""))); });
    box.appendChild(ul);
    return box;
  }

  function renderDetail(scans) {
    detailBody.textContent = "";
    scans.forEach(function (s) {
      const tr = document.createElement("tr");
      cell(tr, scanName(s));
      const score = scanScore(s);
      cell(tr, score === null ? "N/A" : score + "/100");
      cell(tr, scanVerdict(s));

      const st = document.createElement("td");
      st.appendChild(mk("span", "st-badge " + statusClass(s.status), STATUS_LABELS[s.status] || String(s.status)));
      tr.appendChild(st);

      const rv = document.createElement("td");
      if (isReviewed(s)) {
        rv.appendChild(mk("span", "st-badge good", "Reviewed"));
                const who = (typeof reviewNote === "function") ? reviewNote(s) : (s.review_note || "");
        if (who) rv.appendChild(mk("div", "", who));
        rv.appendChild(mk("div", "st-small", reviewLine(s)));
      } else if (s.status === "done" || s.status === "low_quality") {
        const b = mk("button", "st-btn st-btn-small", "Mark as reviewed");
        b.type = "button";
        b.addEventListener("click", function () { openReview(s.id); });
        rv.appendChild(b);
      } else {
        rv.textContent = "-";
      }
      tr.appendChild(rv);

      const dt = document.createElement("td");
      const toggle = mk("button", "st-btn st-btn-light st-btn-small", expanded[s.id] ? "Hide" : "Details");
      toggle.type = "button";
      toggle.addEventListener("click", function () { expanded[s.id] = !expanded[s.id]; showBatch(scans); });
      dt.appendChild(toggle);
      tr.appendChild(dt);
      detailBody.appendChild(tr);

      if (expanded[s.id]) {
        const row = mk("tr", "st-detail");
        const td = document.createElement("td");
        td.colSpan = 6;
        td.appendChild(detailText(s));
        row.appendChild(td);
        detailBody.appendChild(row);
      }
    });
  }

  // ----- mark as reviewed -----
  function openReview(id) {
    reviewScanId = id;
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
    // ASSUMED field name "confirmation". Confirm it when we write the real API.
    const res = await apiPostId("inspectorReview", reviewScanId, { confirmation: text });
    reviewOk.disabled = false;
    if (!res.ok) { reviewMsg.textContent = res.error; return; }
    closeReview();
    openBatch(openId);
  });

  loadBatches();
})();