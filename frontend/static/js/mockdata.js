// Fake data used ONLY while CONFIG.USE_MOCK is true.
// When Member 1's real API is connected, the field names must match
// mocks/scan_record_sample.json. Fix them here and in the pages if they differ.

const RULE_NAMES = [
  "Name of the food",
  "List of ingredients",
  "Nutrition information",
  "Allergen declaration",
  "Net quantity",
  "Manufacturing date",
  "Best before / expiry date",
  "FSSAI licence number",
  "Manufacturer address",
  "Veg / non-veg mark",
  "FSSAI logo"
];

function buildMockRecord(id, productName, failedRules, quality) {
  const rules = RULE_NAMES.map(function (name, i) {
    const failed = failedRules.indexOf(name) !== -1;
    return {
      rule_id: i + 1,
      name: name,
      result: failed ? "FAIL" : "PASS",
      reason: failed ? "Not found on the label." : "Found on the label."
    };
  });
  const passed = rules.filter(function (r) { return r.result === "PASS"; }).length;
  const score = Math.round((passed / rules.length) * 100);
  let verdict = "Non-compliant";
  if (score >= 90) verdict = "Compliant";
  else if (score >= 60) verdict = "Partially compliant";
  return {
    id: id,
    scan_id: id,
    status: "done",
    created_at: new Date().toISOString(),
    product_name: productName,
    score: score,
    verdict: verdict,
    image_quality: quality || { status: "ok", reason: "" },
    rules: rules,
    reviewed: false,
    reviewed_by: "",
    reviewed_at: "",
    review_note: ""
  };
}

function seedMockScans() {
  const a = buildMockRecord(1, "Masala Oats", ["Allergen declaration", "Manufacturer address"]);
  a.created_at = "2026-11-20T10:15:00";
  a.reviewed = true;
  a.reviewed_by = "Inspector One";
  a.reviewed_at = "2026-11-24T14:32:00";
  a.review_note = "A. Kumar, Food Safety Officer";

  const b = buildMockRecord(2, "Salted Potato Chips", []);
  b.created_at = "2026-11-21T16:40:00";

  const c = {
    id: 3, scan_id: 3, status: "low_quality", created_at: "2026-11-22T09:05:00",
    product_name: "Unreadable photo", score: null, verdict: "Could not check",
    image_quality: { status: "too_low", reason: "The photo is too blurry to read." },
    rules: [], reviewed: false, reviewed_by: "", reviewed_at: "", review_note: ""
  };
  return [c, b, a];
}

const MOCK_SCANS_KEY = "verilabel_mock_scans";

function loadMockScans() {
  try {
    const raw = localStorage.getItem(MOCK_SCANS_KEY);
    if (raw) {
      const list = JSON.parse(raw);
      // Only trust the saved list if every scan has a numeric id.
      const good = Array.isArray(list) && list.every(function (s) {
        return s && typeof s.id === "number" && s.rules !== undefined;
      });
      if (good) return list;
    }
  } catch (e) { /* fall through to the seed */ }
  return seedMockScans();
}

function saveMockScans(scans) {
  try { localStorage.setItem(MOCK_SCANS_KEY, JSON.stringify(scans)); } catch (e) { /* ignore */ }
}

const MOCK_ALTERNATIVES = [
  { name: "Baked Millet Chips", category: "Snacks", why: "Lower salt and saturated fat." },
  { name: "Plain Rolled Oats", category: "Breakfast", why: "Lower sugar and no added flavouring." },
  { name: "Roasted Chana", category: "Snacks", why: "More protein and less saturated fat." }
];