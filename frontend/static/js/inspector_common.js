// Shared by inspector.html and inspector_all.html.
// Builds the scan tables, the "Mark as reviewed" window and the "Reviewed by" window.
(function () {
  const me = getSession() || {};
  const expanded = {};
  let reviewScanId = null;
  let afterReview = null;

  const reviewModal = document.getElementById("reviewModal");
  const reviewText = document.getElementById("reviewText");
  const reviewMsg = document.getElementById("reviewMsg");
  const reviewOk = document.getElementById("reviewOk");
  const byModal = document.getElementById("byModal");

  function cell(tr, text) {
    const td = document.createElement("td");
    td.textContent = text;
    tr.appendChild(td);
    return td;
  }

  // The text shown under "Details".
  function detailText(s) {
    const box = mk("div");
    if (s.status === "low_quality") {
      const q = (s.compliance_result && s.compliance_result.image_quality_warning) || "The photo is too unclear.";
      box.appendChild(mk("p", "", "Photo problem: " + q));
      return box;
    }
    if (s.status === "failed") {
      box.appendChild(mk("p", "", "This photo could not be checked."));
      return box;
    }
    if (s.status !== "done") {
      box.appendChild(mk("p", "", "The result is not ready yet."));
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

  // Total, Reviewed and Not reviewed boxes.
  function renderCounts(box, scans) {
    const reviewed = scans.filter(function (s) { return isReviewed(s); }).length;
    box.textContent = "";
    [["Total scans", scans.length], ["Reviewed", reviewed], ["Not reviewed", scans.length - reviewed]].forEach(function (p) {
      const item = mk("div", "mini-stat");
      item.appendChild(mk("strong", "", String(p[1])));
      item.appendChild(mk("span", "", p[0]));
      box.appendChild(item);
    });
  }

  function isMine(s) {
    return !!(s.uploaded_by && s.uploaded_by.user_id === me.user_id);
  }

  // ----- "Reviewed by" window -----
  function showReviewedBy(s) {
    const r = s.review || {};
    document.getElementById("byName").textContent = r.reviewed_by || "-";
    document.getElementById("byNote").textContent = r.review_note || "-";
    document.getElementById("byDate").textContent = r.reviewed_at ? fmtDate(r.reviewed_at) : "-";
    byModal.classList.remove("hidden");
  }
  function closeBy() { byModal.classList.add("hidden"); }

  // ----- "Mark as reviewed" window -----
  function askReview(scanId, done) {
    reviewScanId = scanId;
    afterReview = done;
    reviewText.value = "";
    reviewMsg.textContent = "";
    reviewModal.classList.remove("hidden");
    reviewText.focus();
  }
  function closeReview() { reviewModal.classList.add("hidden"); reviewScanId = null; }

  document.getElementById("reviewCancel").addEventListener("click", closeReview);
  document.getElementById("byClose").addEventListener("click", closeBy);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") { closeReview(); closeBy(); }
  });

  reviewOk.addEventListener("click", async function () {
    const text = reviewText.value.trim();
    if (text.length < 3) { reviewMsg.textContent = "Please type your name and designation."; return; }
    if (text.length > 1000) { reviewMsg.textContent = "The text must be at most 1000 characters."; return; }
    reviewOk.disabled = true;
    // Real API: POST /api/inspector/scans/<id>/review/ with {"confirmation": "..."}
    const res = await apiPostId("inspectorReview", reviewScanId, { confirmation: text });
    reviewOk.disabled = false;
    if (!res.ok) { reviewMsg.textContent = res.error; return; }
    closeReview();
    if (afterReview) afterReview();
  });

  // ----- the scan table -----
  // opts: showOwner (adds the Uploaded by column), redraw (function), afterReview (function)
  function renderScans(tbody, scans, opts) {
    opts = opts || {};
    const colSpan = opts.showOwner ? 8 : 7;
    tbody.textContent = "";

    scans.forEach(function (s) {
      const tr = document.createElement("tr");
      cell(tr, scanName(s));
      if (opts.showOwner) cell(tr, (s.uploaded_by && s.uploaded_by.name) || "-");
      const score = scanScore(s);
      cell(tr, score === null ? "N/A" : score + "/100");
      cell(tr, verdictLabel(scanVerdict(s)));

      const st = document.createElement("td");
      st.appendChild(mk("span", "st-badge " + statusClass(s.status), STATUS_LABELS[s.status] || String(s.status)));
      tr.appendChild(st);

      // Review column
      const rv = document.createElement("td");
      if (isReviewed(s)) {
        rv.appendChild(mk("span", "st-badge good", "Reviewed"));
      } else if (s.status === "done" && isMine(s)) {
        const b = mk("button", "st-btn st-btn-small", "Mark as reviewed");
        b.type = "button";
        b.addEventListener("click", function () { askReview(s.scan_id, opts.afterReview); });
        rv.appendChild(b);
      } else if (s.status === "done") {
        rv.appendChild(mk("span", "st-badge mid", "Not reviewed"));
      } else {
        rv.textContent = "-";
      }
      tr.appendChild(rv);

      // "Reviewed by" button, between Review and Details
      const by = document.createElement("td");
      if (isReviewed(s)) {
        const bb = mk("button", "st-btn st-btn-light st-btn-small", "Reviewed by");
        bb.type = "button";
        bb.addEventListener("click", function () { showReviewedBy(s); });
        by.appendChild(bb);
      }
      tr.appendChild(by);

      // Details button
      const dt = document.createElement("td");
      const toggle = mk("button", "st-btn st-btn-light st-btn-small", expanded[s.scan_id] ? "Hide" : "Details");
      toggle.type = "button";
      toggle.addEventListener("click", function () {
        expanded[s.scan_id] = !expanded[s.scan_id];
        if (opts.redraw) opts.redraw();
      });
      dt.appendChild(toggle);
      tr.appendChild(dt);
      tbody.appendChild(tr);

      if (expanded[s.scan_id]) {
        const row = mk("tr", "st-detail");
        const td = document.createElement("td");
        td.colSpan = colSpan;
        td.appendChild(detailText(s));
        row.appendChild(td);
        tbody.appendChild(row);
      }
    });
  }

  window.InspectorUI = { renderScans: renderScans, renderCounts: renderCounts };
})();