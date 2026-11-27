// Helpers for the Inspector, Admin and History pages, plus their fake server (demo mode only).
// The fake server returns the same shapes as the real Django API in dashboards/views.py.

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

// ---------- Readers for the real SCAN RECORD ----------
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
// The verdict CODE: "COMPLIANT", "PARTIAL", "NON_COMPLIANT" or "" when there is none.
function scanVerdict(s) {
  return (s.compliance_result && s.compliance_result.verdict) || "";
}
function verdictLabel(code) {
  if (code === "COMPLIANT") return "Compliant";
  if (code === "PARTIAL") return "Partially compliant";
  if (code === "NON_COMPLIANT") return "Non-compliant";
  return "Not available";
}
function verdictClass(code) {
  if (code === "COMPLIANT") return "good";
  if (code === "PARTIAL") return "mid";
  if (code === "NON_COMPLIANT") return "bad";
  return "";
}
function scanRules(s) {
  return (s.compliance_result && s.compliance_result.rules) || [];
}
function ruleName(r) { return r.name || "Rule"; }
function ruleResult(r) { return r.status || ""; }   // "PASS" or "FAIL"

const STATUS_LABELS = {
  queued: "Waiting", processing: "Checking", done: "Done",
  failed: "Failed", low_quality: "Photo too unclear"
};
function statusClass(status) {
  if (status === "done") return "good";
  if (status === "failed") return "bad";
  return "mid";
}

// ---------- Review information ----------
// Real record: review { status: "pending" | "reviewed", reviewed_by, reviewed_at, review_note }
function isReviewed(s) {
  return !!(s.review && s.review.status === "reviewed");
}
function reviewLine(s) {
  const r = s.review || {};
  let text = "";
  if (r.reviewed_by) text = "by " + r.reviewed_by;
  if (r.reviewed_at) text += (text ? " on " : "On ") + fmtDate(r.reviewed_at);
  return text || "Review details not available";
}
function reviewNote(s) {
  return (s.review && s.review.review_note) || "";
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
const STAFF_VERSION = 2;

function makeMockBatch(batchId, firstScanId, owner, day, names, fails) {
  const scans = names.map(function (n, i) {
    const r = buildMockRecord(firstScanId + i, n, fails[i], null, owner);
    r.batch_id = batchId;
    r.created_at = day + "T11:0" + i + ":00";
    return r;
  });
  return { id: batchId, created_at: day + "T11:00:00", scans: scans };
}

function seedStaffState() {
  const inspectorOne = { user_id: "inspector1", name: "Inspector One", role: "inspector" };
  const inspectorTwo = { user_id: "inspector2", name: "Inspector Two", role: "inspector" };

  const batch1 = makeMockBatch(1, 100, inspectorOne, "2026-11-23",
    ["Masala Oats", "Salted Chips", "Fruit Drink", "Instant Noodles"],
    [
      ["Allergen declaration"],
      [],
      ["Manufacturer name and address", "FSSAI logo", "Net quantity", "Veg / non-veg symbol", "Allergen declaration"],
      ["FSSAI licence number (14 digits)", "Allergen declaration"]
    ]);
  markReviewed(batch1.scans[0], "inspector1", "2026-11-24T14:32:00", "A. Kumar, Food Safety Officer");

  const batch2 = makeMockBatch(2, 110, inspectorTwo, "2026-11-25",
    ["Chocolate Spread", "Fruit Jam", "Cream Biscuits"],
    [
      ["FSSAI logo"],
      [],
      ["Allergen declaration", "Net quantity"]
    ]);
  markReviewed(batch2.scans[1], "inspector2", "2026-11-26T10:20:00", "R. Nair, Food Analyst");

  return {
    version: STAFF_VERSION,
    next_scan: 200, next_batch: 3, next_rule: MOCK_DEFAULT_RULES.length + 1,
    batches: [batch2, batch1],
    rules: JSON.parse(JSON.stringify(MOCK_DEFAULT_RULES))
  };
}

function loadStaffState() {
  try {
    const raw = localStorage.getItem(STAFF_KEY);
    if (raw) {
      const st = JSON.parse(raw);
      // Old saved demo data (old shape or old version) is thrown away and rebuilt.
      const rulesOk = st && Array.isArray(st.rules) && st.rules[0] && st.rules[0].rule_id;
      const scansOk = st && Array.isArray(st.batches) && st.batches.every(function (b) {
        return b.scans.every(function (s) { return s.review && s.review.status && s.compliance_result !== undefined; });
      });
      if (rulesOk && scansOk && st.version === STAFF_VERSION) return st;
    }
  } catch (e) { /* use the seed */ }
  return seedStaffState();
}
function saveStaffState(st) {
  try { localStorage.setItem(STAFF_KEY, JSON.stringify(st)); } catch (e) { /* ignore */ }
}

// A scan that was just uploaded moves from queued to processing to done.
// While it is not done it has no score and no result, like the real API.
function withStatus(scan) {
  const copy = JSON.parse(JSON.stringify(scan));
  if (copy.started) {
    const elapsed = Date.now() - copy.started;
    if (elapsed < 2000) copy.status = "queued";
    else if (elapsed < 5000) copy.status = "processing";
    if (copy.status !== "done") {
      copy.score = null;
      copy.compliance_result = null;
      copy.extracted_fields = null;
    }
  }
  return copy;
}

function allMockScans(st) {
  let all = [];
  st.batches.forEach(function (b) { all = all.concat(b.scans.map(withStatus)); });
  return all.concat(loadMockScans());
}

function newestFirst(list) {
  return list.slice().sort(function (a, b) { return new Date(b.created_at) - new Date(a.created_at); });
}

function batchOwnerId(b) {
  return (b.scans[0] && b.scans[0].uploaded_by && b.scans[0].uploaded_by.user_id) || "";
}

// Like the real API: an inspector sees their own batches, an admin sees all.
function visibleMockBatches(st) {
  const me = getSession() || {};
  if (me.role === "admin") return st.batches;
  return st.batches.filter(function (b) { return batchOwnerId(b) === me.user_id; });
}

// One batch row, same fields as the real API.
function mockBatchRow(b) {
  const scans = b.scans.map(withStatus);
  function count(test) { return scans.filter(test).length; }
  const owner = (b.scans[0] && b.scans[0].uploaded_by) || { user_id: "inspector1", name: "Inspector One" };
  return {
    batch_id: b.id,
    created_at: b.created_at,
    created_by: { user_id: owner.user_id, name: owner.name },
    total: scans.length,
    done: count(function (s) { return s.status === "done"; }),
    in_progress: count(function (s) { return s.status === "queued" || s.status === "processing"; }),
    failed: count(function (s) { return s.status === "failed" || s.status === "low_quality"; }),
    compliant: count(function (s) { return scanVerdict(s) === "COMPLIANT"; }),
    partial: count(function (s) { return scanVerdict(s) === "PARTIAL"; }),
    non_compliant: count(function (s) { return scanVerdict(s) === "NON_COMPLIANT"; }),
    reviewed: count(function (s) { return isReviewed(s); })
  };
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
    const me = getSession() || {};
    const owner = { user_id: me.user_id || "inspector1", name: me.name || "Inspector One", role: "inspector" };
    const batch = { id: st.next_batch++, created_at: new Date().toISOString(), scans: [] };
    files.forEach(function (f) {
      const failed = RULE_NAMES.filter(function () { return Math.random() < 0.25; });
      const rec = buildMockRecord(st.next_scan++, f.name.replace(/\.[^.]+$/, ""), failed, null, owner);
      rec.batch_id = batch.id;
      rec.started = Date.now();
      batch.scans.push(rec);
    });
    st.batches.unshift(batch);
    saveStaffState(st);
    return { ok: true, data: { batch_id: batch.id, scans: batch.scans.map(function (s) { return { scan_id: s.scan_id, status: "queued" }; }) } };
  }

  if (key === "inspectorBatches") {
    return { ok: true, data: visibleMockBatches(st).map(mockBatchRow) };
  }

  if (key === "inspectorBatch") {
    const b = visibleMockBatches(st).filter(function (x) { return String(x.id) === String(opts.id); })[0];
    if (!b) return { ok: false, error: "Batch not found." };
    const data = mockBatchRow(b);
    data.scans = b.scans.map(withStatus);
    return { ok: true, data: data };
  }

  // Real API: GET /api/inspector/scans/?scope=mine or ?scope=all (a plain list, newest first)
  if (key === "inspectorMyScans" || key === "inspectorAllScans") {
    const meId = (getSession() || {}).user_id;
    let list = [];
    st.batches.forEach(function (b) { list = list.concat(b.scans.map(withStatus)); });
    if (key === "inspectorMyScans") {
      list = list.filter(function (s) { return s.uploaded_by && s.uploaded_by.user_id === meId; });
    }
    return { ok: true, data: newestFirst(list) };
  }

  if (key === "inspectorReview") {
    // Works for your own batch scans and for customer scans, like the real API.
    let found = null;
    let customerScans = null;
    st.batches.forEach(function (b) {
      b.scans.forEach(function (s) { if (String(s.scan_id) === String(opts.id)) found = s; });
    });
    if (!found) {
      customerScans = loadMockScans();
      found = customerScans.filter(function (s) { return String(s.scan_id) === String(opts.id); })[0] || null;
    }
    if (!found) return { ok: false, error: "Scan not found." };

    // A colleague's scan cannot be opened by another inspector (can_view_scan).
    const me = getSession() || {};
    if (found.uploaded_by && found.uploaded_by.role === "inspector" &&
        me.role !== "admin" && found.uploaded_by.user_id !== me.user_id) {
      return { ok: false, error: "Scan not found." };
    }

    const text = String((opts.body || {}).confirmation || "").trim();
    if (withStatus(found).status !== "done") return { ok: false, error: 'Only a finished scan (status "done") can be reviewed.' };
    if (isReviewed(found)) return { ok: false, error: "This scan has already been reviewed." };
    if (!text) return { ok: false, error: "Please type the confirmation text." };
    if (text.length > 1000) return { ok: false, error: "The confirmation text must be at most 1000 characters." };

    markReviewed(found, me.user_id || "inspector1", new Date().toISOString(), text);
    if (customerScans) saveMockScans(customerScans); else saveStaffState(st);
    return { ok: true, data: withStatus(found) };
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

  // Real API: a plain list of scan records, newest first.
  if (key === "adminHistory") {
    return { ok: true, data: newestFirst(allMockScans(st)) };
  }

  if (key === "adminStats") {
    const everything = allMockScans(st);
    const checked = everything.filter(function (s) { return scanScore(s) !== null; });
    const scores = checked.map(scanScore);
    const avg = scores.length ? Math.round(scores.reduce(function (a, b) { return a + b; }, 0) / scores.length) : null;

    const verdictCounts = { COMPLIANT: 0, PARTIAL: 0, NON_COMPLIANT: 0 };
    checked.forEach(function (s) {
      const v = scanVerdict(s);
      if (verdictCounts[v] !== undefined) verdictCounts[v] += 1;
    });

    const statusCounts = {};
    everything.forEach(function (s) { statusCounts[s.status] = (statusCounts[s.status] || 0) + 1; });

    // Only days that have scans, like the real API. The page fills in the empty days.
    const days = {};
    const today = new Date();
    for (let i = 13; i >= 0; i--) {
      const d = new Date(today); d.setDate(d.getDate() - i);
      days[d.toISOString().slice(0, 10)] = 0;
    }
    everything.forEach(function (s) {
      const day = String(s.created_at).slice(0, 10);
      if (days[day] !== undefined) days[day] += 1;
    });
    const perDay = Object.keys(days).filter(function (d) { return days[d] > 0; })
      .map(function (d) { return { date: d, count: days[d] }; });

    const productCounts = {};
    everything.forEach(function (s) {
      if (!s.product_name) return;
      productCounts[s.product_name] = (productCounts[s.product_name] || 0) + 1;
    });
    const topProducts = Object.keys(productCounts)
      .map(function (n) { return { product_name: n, count: productCounts[n] }; })
      .sort(function (a, b) { return b.count - a.count || a.product_name.localeCompare(b.product_name); })
      .slice(0, 5);

    const failures = {};
    everything.filter(function (s) { return s.status === "done"; }).forEach(function (s) {
      scanRules(s).forEach(function (r) {
        if (ruleResult(r) !== "FAIL") return;
        if (!failures[r.rule_id]) failures[r.rule_id] = { rule_id: r.rule_id, name: ruleName(r), failures: 0 };
        failures[r.rule_id].failures += 1;
      });
    });
    const mostFailed = Object.keys(failures).map(function (k) { return failures[k]; })
      .sort(function (a, b) { return b.failures - a.failures; }).slice(0, 5);

    const reviewedCount = everything.filter(function (s) { return isReviewed(s); }).length;
    return { ok: true, data: {
      total_scanned: everything.length,
      reviewed: reviewedCount,
      not_reviewed: everything.length - reviewedCount,
      checked: checked.length,
      average_score: avg,
      fully_compliant: verdictCounts.COMPLIANT,
      verdict_counts: verdictCounts,
      status_counts: statusCounts,
      scans_per_day: perDay,
      top_products: topProducts,
      most_failed_rules: mostFailed,
      recent_scans: newestFirst(everything).slice(0, 10)
    } };
  }

  return null;
}