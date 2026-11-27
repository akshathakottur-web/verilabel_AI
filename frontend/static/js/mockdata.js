// Fake data used ONLY while CONFIG.USE_MOCK is true.
// The shape follows the real scan record (mocks/scan_record_sample.json).
// Lines marked LEGACY are old field names that the customer pages (upload, progress,
// result, history) still read. Remove them when those pages are redone.

// In the same order as the real default rules R01 to R11.
const RULE_NAMES = [
  "Name of the food",
  "List of ingredients",
  "Nutrition information",
  "Allergen declaration",
  "Veg / non-veg symbol",
  "Net quantity",
  "Manufacturing date",
  "Expiry or best-before date",
  "FSSAI logo",
  "FSSAI licence number (14 digits)",
  "Manufacturer name and address"
];

// The extracted field each rule looks at (R09 is a logo detection, so it has no field).
const RULE_FIELDS = [
  "food_name", "ingredients", "nutrition", "allergens", "veg_nonveg_mark",
  "net_quantity", "manufacturing_date", "expiry_date", null,
  "fssai_licence_number", "manufacturer_address"
];

function mockFieldValue(key, productName) {
  const values = {
    food_name: productName,
    ingredients: "Oats, edible vegetable oil, spices, salt",
    nutrition: { energy_kcal: 385, protein_g: 11, carbohydrate_g: 62, total_sugars_g: 3, total_fat_g: 8, saturated_fat_g: 2, sodium_mg: 620 },
    allergens: "Contains wheat",
    veg_nonveg_mark: "veg",
    net_quantity: "200 g",
    manufacturing_date: "10/2026",
    expiry_date: "Best before 9 months from packing",
    fssai_licence_number: "10012345678901",
    manufacturer_address: "Sample Foods Pvt Ltd, Bengaluru"
  };
  return values[key];
}

const MOCK_CUSTOMER = { user_id: "customer", name: "Customer", role: "customer" };

// Sets the real review object and the LEGACY top-level review fields together.
function markReviewed(rec, by, at, note) {
  rec.review = { status: "reviewed", reviewed_by: by, reviewed_at: at, review_note: note };
  rec.reviewed = true;          // LEGACY
  rec.reviewed_by = by;         // LEGACY
  rec.reviewed_at = at;         // LEGACY
  rec.review_note = note;       // LEGACY
}

function buildMockRecord(id, productName, failedRules, quality, owner) {
  const rules = RULE_NAMES.map(function (name, i) {
    const failed = failedRules.indexOf(name) !== -1;
    const status = failed ? "FAIL" : "PASS";
    return {
      rule_id: "R" + String(i + 1).padStart(2, "0"),
      name: name,
      status: status,
      result: status,           // LEGACY
      reason: failed ? "Not found on the label." : "Found on the label."
    };
  });

  const fields = {};
  RULE_FIELDS.forEach(function (key, i) {
    if (!key) return;
    const failed = failedRules.indexOf(RULE_NAMES[i]) !== -1;
    fields[key] = failed
      ? { found: false, value: null, confidence: 0 }
      : { found: true, value: mockFieldValue(key, productName), confidence: (key === "ingredients" && id % 3 === 0) ? 0.62 : 0.94 };
  });

  const passed = rules.filter(function (r) { return r.status === "PASS"; }).length;
  const score = Math.round((passed / rules.length) * 100);
  // Demo thresholds only. The real verdict comes from the backend.
  let code = "NON_COMPLIANT";
  let label = "Non-compliant";
  if (score >= 90) { code = "COMPLIANT"; label = "Compliant"; }
  else if (score >= 60) { code = "PARTIAL"; label = "Partially compliant"; }

  return {
    scan_id: id,
    id: id,                     // LEGACY (same number as scan_id)
    batch_id: null,
    status: "done",
    created_at: new Date().toISOString(),
    product_name: productName,
    score: score,
    image_url: null,
    uploaded_by: owner || MOCK_CUSTOMER,
    extracted_fields: fields,
    compliance_result: { image_quality_warning: null, rules: rules, score: score, verdict: code },
    review: { status: "pending", reviewed_by: null, reviewed_at: null, review_note: "" },
    // LEGACY fields read by the old customer pages:
    verdict: label,
    rules: rules,
    image_quality: quality || { status: "ok", reason: "" },
    reviewed: false,
    reviewed_by: "",
    reviewed_at: "",
    review_note: ""
  };
}

function seedMockScans() {
  const a = buildMockRecord(1, "Masala Oats", ["Allergen declaration", "Manufacturer name and address"]);
  a.created_at = "2026-11-20T10:15:00";
  markReviewed(a, "inspector1", "2026-11-24T14:32:00", "A. Kumar, Food Safety Officer");

  const b = buildMockRecord(2, "Salted Potato Chips", []);
  b.created_at = "2026-11-21T16:40:00";

  const c = {
    scan_id: 3, id: 3, batch_id: null, status: "low_quality",
    created_at: "2026-11-22T09:05:00",
    product_name: "Unreadable photo", score: null, image_url: null,
    uploaded_by: MOCK_CUSTOMER,
    extracted_fields: null,
    compliance_result: { image_quality_warning: "The photo is too blurry to read.", rules: [], score: null, verdict: null },
    review: { status: "pending", reviewed_by: null, reviewed_at: null, review_note: "" },
    // LEGACY
    verdict: "Could not check",
    rules: [],
    image_quality: { status: "too_low", reason: "The photo is too blurry to read." },
    reviewed: false, reviewed_by: "", reviewed_at: "", review_note: ""
  };
  return [c, b, a];
}

const MOCK_SCANS_KEY = "verilabel_mock_scans";

function loadMockScans() {
  try {
    const raw = localStorage.getItem(MOCK_SCANS_KEY);
    if (raw) {
      const list = JSON.parse(raw);
      // Only trust the saved list if it has the new shape (a numeric id and a review object).
      const good = Array.isArray(list) && list.every(function (s) {
        return s && typeof s.id === "number" && s.review && s.review.status;
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