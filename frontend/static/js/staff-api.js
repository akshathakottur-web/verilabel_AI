// Helpers for the Inspector, Admin and History pages, plus their fake server (demo mode only).

// The 11 default rules, in the same shape as the real backend (compliance/default_rules.py).
const MOCK_DEFAULT_RULES = [
  { rule_id: "R01", name: "Name of the food", check_type: "field_found", field_key: "food_name", weight: 1, enabled: true },
  { rule_id: "R02", name: "List of ingredients", check_type: "field_found", field_key: "ingredients", weight: 1, enabled: true },
  { rule_id: "R03", name: "Nutrition information", check_type: "nutrition_values", field_key: "energy_kcal,protein_g,carbohydrate_g,total_fat_g", weight: 1, enabled: true },
  { rule_id: "R04", name: "Allergen declaration", check_type: "allergen_declared", field_key: "", weight: 1, enabled: true },
  { rule_id: "R05", name: "Veg / non-veg symbol", check_type: "field_found", field_key: "veg_nonveg_mark", weight: 1, enabled: true },
  { rule_id: "R06", name: "Net quantity", check_type: "field_found", field_key: "net_quantity", weight: 1, enabled: true },
  { rule_id: "R07", name: "Manufacturing date", check_type: "field_found", field_key: "manufacturing_date", weight: 1, enabled: true },
  { rule_id: "R08", name: "Expiry or best-before date", check_type: "field_found", field_key: "expiry_date", weight: 1, enabled: true },
  { rule_id: "R09", name: "FSSAI logo", check_type: "detection_found", field_key: "fssai_logo", weight: 1, enabled: true },
  { rule_id: "R10", name: "FSSAI licence number (14 digits)", check_type: "fssai_licence_14", field_key: "fssai_licence_number", weight: 1, enabled: true },
  { rule_id: "R11", name: "Manufacturer name and address", check_type: "field_found", field_key: "manufacturer_address", weight: 1, enabled: true }
];

function asList(data, key) {
  if (Array.isArray(data)) return data;
  if (data && Array.isArray(data[key])) return data[key];
  if (data && Array.isArray(data.results)) return data.results;
  return [];
}

function mk(tag, className, text) {
  const e = document.createElement(tag);
  if (className) e.className = className;
  if (text !== undefined) e.textContent = text;
  return e;
}

function fmtDate(value) {
  const d = new Date(value);
  return isNaN(d.getTime()) ? "" : d.toLocaleString("en-IN");
}

// Tolerant readers: they accept both the demo data and the real SCAN RECORD.
function scanName(s) {
  return s.product_name ||
    (s.extracted_fields && s.extracted_fields.food_name && s.extracted_fields.food_name.value) ||
    "Unknown product";
}
function scanScore(s) {
  if (s.score !== undefined && s.score !== null) return s.score;
  if (s.compliance_result && s.compliance_result.score !== undefined) return s.compliance_result.score;
  return null;
}
function scanVerdict(s) {
  return s.verdict || (s.compliance_result && s.compliance_result.verdict) || "";
}
function scanRules(s) {
  return s.rules ||
    (s.compliance_result && (s.compliance_result.rule_results || s.compliance_result.rules)) || [];
}
function ruleName(r) { return r.name || r.rule_name || "Rule"; }
function ruleResult(r) { return r.result || r.status || ""; }

const STATUS_LABELS = {
  queued: "Waiting", processing: "Checking", done: "Done",
  failed: "Failed", low_quality: "Photo too unclear"
};
function statusClass(status) {
  if (status === "done") return "good";
  if (status === "failed") return "bad";
  return "mid";
}

// ---------- Review information (who reviewed, and when) ----------
// Real record: review { status: "pending" | "reviewed", reviewed_by, reviewed_at }.
// Demo data: reviewed, reviewed_by, reviewed_at, review_note.
function isReviewed(s) {
  if (s.review && s.review.status) return s.review.status === "reviewed";
  return !!(s.reviewed || (s.review && s.review.reviewed));
}
function reviewLine(s) {
  const by = s.reviewed_by || (s.review && s.review.reviewed_by) || "";
  const at = s.reviewed_at || (s.review && s.review.reviewed_at) || "";
  let text = "";
  if (by) text = "by " + by;
  if (at) text += (text ? " on " : "On ") + fmtDate(at);
  return text || "Review details not available";
}
function reviewNote(s) {
  return s.review_note || (s.review && (s.review.review_note || s.review.note)) || "";
}

// Many photos at once (inspector). Contract: form field "images".
function apiUploadMany(files) {
  if (CONFIG.USE_MOCK) return mockRequest("POST", "uploadMany", { files: files });
  const form = new FormData();
  files.forEach(function (f) { form.append("images", f); });
  return realRequest("POST", "upload", { form: form });
}

// A POST that also needs an id in the address (for example, marking a scan as reviewed).
function apiPostId(pathKey, id, body) {
  return CONFIG.USE_MOCK
    ? mockRequest("POST", pathKey, { id: id, body: body })
    : realRequest("POST", pathKey, { id: id, body: body });
}

// ---------- Fake server for inspector and admin ----------
const STAFF_KEY = "verilabel_mock_staff";

function seedStaffState() {
  const names = ["Masala Oats", "Salted Chips", "Fruit Drink", "Instant Noodles"];
  const fails = [
    ["Allergen declaration"],
    [],
    ["Manufacturer address", "FSSAI logo", "Net quantity", "Veg / non-veg mark", "Allergen declaration"],
    ["FSSAI licence number", "Allergen declaration"]
  ];
  const scans = names.map(function (n, i) {
    const r = buildMockRecord(100 + i, n, fails[i]);
    r.created_at = "2026-11-23T11:0" + i + ":00";
    return r;
  });
  scans[0].reviewed = true;
  scans[0].reviewed_by = "Inspector One";
  scans[0].reviewed_at = "2026-11-24T14:32:00";
  scans[0].review_note = "A. Kumar, Food Safety Officer";

  return {
    next_scan: 200, next_batch: 2, next_rule: MOCK_DEFAULT_RULES.length + 1,
    batches: [{ id: 1, created_at: "2026-11-23T11:00:00", scans: scans }],
    rules: JSON.parse(JSON.stringify(MOCK_DEFAULT_RULES))
  };
}

function loadStaffState() {
  try {
    const raw = localStorage.getItem(STAFF_KEY);
    if (raw) {
      const st = JSON.parse(raw);
      // Old saved demo data (without rule_id) is thrown away and rebuilt.
      if (st && Array.isArray(st.batches) && Array.isArray(st.rules) && st.rules[0] && st.rules[0].rule_id) return st;
    }
  } catch (e) { /* use the seed */ }
  return seedStaffState();
}
function saveStaffState(st) {
  try { localStorage.setItem(STAFF_KEY, JSON.stringify(st)); } catch (e) { /* ignore */ }
}

function withStatus(scan) {
  const copy = JSON.parse(JSON.stringify(scan));
  if (copy.started) {
    const elapsed = Date.now() - copy.started;
    if (elapsed < 2000) copy.status = "queued";
    else if (elapsed < 5000) copy.status = "processing";
  }
  return copy;
}

function allMockScans(st) {
  let all = [];
  st.batches.forEach(function (b) { all = all.concat(b.scans.map(withStatus)); });
  return all.concat(loadMockScans());
}

// Same checks as compliance/services.py, so errors look the same in demo and real mode.
function cleanMockRule(b) {
  const TYPES = ["field_found", "detection_found", "nutrition_values", "allergen_declared", "fssai_licence_14"];
  const name = String(b.name || "").trim();
  if (!name || name.length > 200) return { error: "The rule name is required and must be at most 200 characters." };
  if (TYPES.indexOf(b.check_type) === -1) return { error: "check_type must be one of: " + TYPES.join(", ") };
  const w = parseInt(b.weight, 10);
  if (!(w >= 1 && w <= 10)) return { error: "weight must be a whole number from 1 to 10." };
  if (typeof b.enabled !== "boolean") return { error: "enabled must be true or false." };
  return { value: { name: name, check_type: b.check_type, field_key: String(b.field_key || "").trim(), weight: w, enabled: b.enabled } };
}

// Returns a result, or null if the request is not for the staff pages.
function mockStaffHandle(method, key, opts) {
  const st = loadStaffState();

  if (key === "uploadMany") {
    const files = opts.files || [];
    if (!files.length) return { ok: false, error: "Please choose at least one photo." };
    const batch = { id: st.next_batch++, created_at: new Date().toISOString(), scans: [] };
    files.forEach(function (f) {
      const failed = RULE_NAMES.filter(function () { return Math.random() < 0.25; });
      const rec = buildMockRecord(st.next_scan++, f.name.replace(/\.[^.]+$/, ""), failed);
      rec.started = Date.now();
      batch.scans.push(rec);
    });
    st.batches.unshift(batch);
    saveStaffState(st);
    return { ok: true, data: { batch_id: batch.id, scans: batch.scans.map(function (s) { return { scan_id: s.id, status: "queued" }; }) } };
  }

  if (key === "inspectorBatches") {
    return { ok: true, data: st.batches.map(function (b) {
      const scans = b.scans.map(withStatus);
      const done = scans.filter(function (s) { return s.status === "done"; });
      return {
        id: b.id, created_at: b.created_at, total: scans.length,
        compliant: done.filter(function (s) { return s.verdict === "Compliant"; }).length,
        non_compliant: done.filter(function (s) { return s.verdict !== "Compliant"; }).length,
        reviewed: scans.filter(function (s) { return isReviewed(s); }).length
      };
    }) };
  }

  if (key === "inspectorBatch") {
    const b = st.batches.filter(function (x) { return String(x.id) === String(opts.id); })[0];
    if (!b) return { ok: false, error: "Batch not found." };
    return { ok: true, data: { id: b.id, created_at: b.created_at, scans: b.scans.map(withStatus) } };
  }

  if (key === "inspectorReview") {
    const text = ((opts.body || {}).confirmation || "").trim();
    if (text.length < 3) return { ok: false, error: "Please type your confirmation (at least 3 characters)." };
    let found = null;
    st.batches.forEach(function (b) {
      b.scans.forEach(function (s) { if (String(s.id) === String(opts.id)) found = s; });
    });
    if (!found) return { ok: false, error: "Scan not found." };
    if (found.reviewed) return { ok: false, error: "This scan has already been reviewed." };
    found.reviewed = true;
    found.reviewed_at = new Date().toISOString();
    found.review_note = text;
    found.reviewed_by = (getSession() || {}).name || "Inspector";
    saveStaffState(st);
    return { ok: true, data: { scan_id: found.id, reviewed: true } };
  }

  if (key === "adminRules") {
    if (method === "POST") {
      const c = cleanMockRule(opts.body || {});
      if (c.error) return { ok: false, error: c.error };
      const id = "R" + String(st.next_rule++).padStart(2, "0");
      const rule = Object.assign({ rule_id: id }, c.value);
      st.rules.push(rule);
      saveStaffState(st);
      return { ok: true, data: rule };
    }
    return { ok: true, data: st.rules };
  }

  if (key === "adminRule") {
    const rule = st.rules.filter(function (r) { return r.rule_id === String(opts.id); })[0];
    if (!rule) return { ok: false, error: "Rule " + opts.id + " was not found." };
    const c = cleanMockRule(opts.body || {});
    if (c.error) return { ok: false, error: c.error };
    Object.assign(rule, c.value);
    saveStaffState(st);
    return { ok: true, data: rule };
  }

  if (key === "adminHistory") {
    const all = allMockScans(st);
    const counts = {};
    all.forEach(function (s) {
      if (s.status !== "done") return;
      const n = scanName(s);
      counts[n] = (counts[n] || 0) + 1;
    });
    const top = Object.keys(counts).map(function (n) { return { name: n, count: counts[n] }; })
      .sort(function (a, b) { return b.count - a.count; }).slice(0, 5);
    const scans = all.map(function (s) {
      return {
        id: s.id, product_name: scanName(s), created_at: s.created_at, score: scanScore(s),
        status: s.status, verdict: scanVerdict(s),
        reviewed: isReviewed(s), reviewed_by: s.reviewed_by || "", reviewed_at: s.reviewed_at || "",
        review_note: s.review_note || ""
      };
    }).sort(function (a, b) { return new Date(b.created_at) - new Date(a.created_at); });
    return { ok: true, data: { scans: scans, top_products: top } };
  }

  if (key === "adminStats") {
    const everything = allMockScans(st);
    const all = everything.filter(function (s) { return s.status === "done" && scanScore(s) !== null; });
    const scores = all.map(scanScore);
    const avg = scores.length ? Math.round(scores.reduce(function (a, b) { return a + b; }, 0) / scores.length) : 0;
    const perDay = [];
    for (let i = 13; i >= 0; i--) {
      const d = new Date(); d.setDate(d.getDate() - i);
      const day = d.toISOString().slice(0, 10);
      perDay.push({ date: day, count: all.filter(function (s) { return String(s.created_at).slice(0, 10) === day; }).length });
    }
    const failCounts = {};
    all.forEach(function (s) {
      scanRules(s).forEach(function (r) {
        if (ruleResult(r) === "FAIL") failCounts[ruleName(r)] = (failCounts[ruleName(r)] || 0) + 1;
      });
    });
    return { ok: true, data: {
      total_scans: everything.length,
      checked_scans: all.length,
      reviewed: everything.filter(function (s) { return isReviewed(s); }).length,
      not_reviewed: everything.filter(function (s) { return !isReviewed(s); }).length,
      average_score: avg,
      scans_per_day: perDay,
      compliance_breakdown: {
        compliant: scores.filter(function (x) { return x >= 90; }).length,
        partial: scores.filter(function (x) { return x >= 60 && x < 90; }).length,
        non_compliant: scores.filter(function (x) { return x < 60; }).length
      },
      most_failed_rules: Object.keys(failCounts).map(function (n) { return { name: n, count: failCounts[n] }; })
        .sort(function (a, b) { return b.count - a.count; }).slice(0, 5)
    } };
  }

  return null;
}