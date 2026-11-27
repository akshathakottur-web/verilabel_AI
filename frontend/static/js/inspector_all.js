(function () {
  const user = requireLogin(["inspector"]);
  if (!user) return;
  renderNavbar("inspector_all");

  const allMsg = document.getElementById("allMsg");

  // Make sure the helper files are really loaded.
  const needed = ["asList", "mk", "scanName", "scanScore", "scanVerdict", "verdictLabel", "scanRules", "ruleName",
    "ruleResult", "fmtDate", "statusClass", "isReviewed"];
  const missing = needed.filter(function (n) { return typeof window[n] !== "function"; });
  if (missing.length || typeof STATUS_LABELS === "undefined" || typeof InspectorUI === "undefined") {
    allMsg.textContent = "A script file is missing or old. Not found: " + missing.join(", ") +
      ". Check staff-api.js and inspector_common.js.";
    return;
  }

  const counts = document.getElementById("allCounts");
  const empty = document.getElementById("allEmpty");
  const wrap = document.getElementById("allWrap");
  const body = document.getElementById("allBody");
  let scans = [];
  let timer = null;

  function draw() {
    InspectorUI.renderCounts(counts, scans);
    empty.classList.toggle("hidden", scans.length > 0);
    wrap.classList.toggle("hidden", scans.length === 0);
    InspectorUI.renderScans(body, scans, { showOwner: true, redraw: draw, afterReview: load });
  }

  async function load() {
    if (timer) { clearTimeout(timer); timer = null; }
    // Real API: GET /api/inspector/scans/?scope=all gives a plain list of scan records.
    const res = await apiGet("inspectorAllScans");
    if (!res.ok) { allMsg.textContent = res.error; return; }
    allMsg.textContent = "";
    scans = asList(res.data, "scans");
    draw();
    const pending = scans.some(function (s) { return s.status === "queued" || s.status === "processing"; });
    if (pending) timer = setTimeout(load, 3000);
  }

  load();
})();