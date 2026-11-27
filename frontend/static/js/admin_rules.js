(function () {
  const user = requireLogin(["admin"]);
  if (!user) return;
  renderNavbar("admin_rules");

  // Check types and field names come from contracts/API_CONTRACT.md ("Admin rules").
  const TYPE_LABELS = {
    field_found: "A text item is found on the label",
    detection_found: "A symbol or table is detected in the photo",
    nutrition_values: "Nutrition values are present",
    allergen_declared: "An allergen declaration is present",
    fssai_licence_14: "The FSSAI licence number has 14 digits"
  };
  const FIELD_CHOICES = [
    ["food_name", "Name of the food"], ["ingredients", "List of ingredients"], ["nutrition", "Nutrition information"],
    ["allergens", "Allergens"], ["net_quantity", "Net quantity"], ["manufacturing_date", "Manufacturing date"],
    ["expiry_date", "Expiry or best-before date"], ["fssai_licence_number", "FSSAI licence number"],
    ["manufacturer_address", "Manufacturer name and address"], ["veg_nonveg_mark", "Veg / non-veg symbol"]
  ];
  const HINTS = {
    detection_found: "Type the detection class, for example fssai_logo. The allowed classes are listed in contracts/PIPELINE_CONTRACT.md.",
    nutrition_values: "Comma-separated nutrients from: energy_kcal, protein_g, carbohydrate_g, total_sugars_g, total_fat_g, saturated_fat_g, sodium_mg."
  };

  let rules = [];
  let editingId = null;

  const body = document.getElementById("rulesBody");
  const weightInfo = document.getElementById("weightInfo");
  const listMsg = document.getElementById("listMsg");
  const formTitle = document.getElementById("formTitle");
  const nameIn = document.getElementById("ruleName");
  const typeIn = document.getElementById("checkType");
  const selectBox = document.getElementById("fieldSelectBox");
  const selectIn = document.getElementById("fieldSelect");
  const textBox = document.getElementById("fieldTextBox");
  const textIn = document.getElementById("fieldText");
  const hint = document.getElementById("fieldHint");
  const weightIn = document.getElementById("ruleWeight");
  const enabledIn = document.getElementById("ruleEnabled");
  const saveBtn = document.getElementById("saveBtn");
  const cancelBtn = document.getElementById("cancelBtn");
  const formMsg = document.getElementById("formMsg");
  const okMsg = document.getElementById("okMsg");

  // Fill the two drop-down lists
  Object.keys(TYPE_LABELS).forEach(function (k) {
    const o = document.createElement("option");
    o.value = k; o.textContent = TYPE_LABELS[k];
    typeIn.appendChild(o);
  });
  FIELD_CHOICES.forEach(function (f) {
    const o = document.createElement("option");
    o.value = f[0]; o.textContent = f[1];
    selectIn.appendChild(o);
  });

  // Show only the detail box that the chosen check type needs
  function updateFieldBoxes() {
    const t = typeIn.value;
    selectBox.classList.toggle("hidden", t !== "field_found");
    textBox.classList.toggle("hidden", t !== "detection_found" && t !== "nutrition_values");
    hint.textContent = HINTS[t] || "";
  }
  typeIn.addEventListener("change", updateFieldBoxes);

  function fieldKeyFromForm() {
    const t = typeIn.value;
    if (t === "field_found") return selectIn.value;
    if (t === "detection_found" || t === "nutrition_values") return textIn.value.trim();
    return "";
  }

  function render() {
    body.textContent = "";
    let total = 0, on = 0;
    rules.forEach(function (r) {
      const tr = document.createElement("tr");
      [r.rule_id, r.name, TYPE_LABELS[r.check_type] || r.check_type, String(r.weight)].forEach(function (t) {
        const td = document.createElement("td");
        td.textContent = t;
        tr.appendChild(td);
      });
      if (r.field_key) {
        tr.children[2].appendChild(mk("div", "st-small", r.field_key));
      }
      const st = document.createElement("td");
      st.appendChild(mk("span", "st-badge " + (r.enabled ? "good" : "mid"), r.enabled ? "On" : "Off"));
      tr.appendChild(st);
      if (r.enabled) { total += Number(r.weight) || 0; on++; }

      const act = document.createElement("td");
      const edit = mk("button", "st-btn st-btn-light st-btn-small", "Edit");
      edit.type = "button";
      edit.setAttribute("aria-label", "Edit rule " + r.name);
      edit.addEventListener("click", function () { startEdit(r); });
      act.appendChild(edit);
      tr.appendChild(act);
      body.appendChild(tr);
    });
    weightInfo.textContent = rules.length + " rules, " + on + " switched on. Total weight of switched-on rules: " + total +
      ". A higher weight counts more in the compliance score.";
  }

  function resetForm() {
    editingId = null;
    nameIn.value = "";
    typeIn.value = "field_found";
    selectIn.value = FIELD_CHOICES[0][0];
    textIn.value = "";
    weightIn.value = "1";
    enabledIn.checked = true;
    formTitle.textContent = "Add a rule";
    saveBtn.textContent = "Add rule";
    cancelBtn.classList.add("hidden");
    formMsg.textContent = "";
    updateFieldBoxes();
  }

  function startEdit(r) {
    editingId = r.rule_id;
    nameIn.value = r.name || "";
    typeIn.value = TYPE_LABELS[r.check_type] ? r.check_type : "field_found";
    if (typeIn.value === "field_found") selectIn.value = r.field_key;
    else textIn.value = r.field_key || "";
    weightIn.value = r.weight;
    enabledIn.checked = !!r.enabled;
    formTitle.textContent = "Edit rule " + r.rule_id;
    saveBtn.textContent = "Save changes";
    cancelBtn.classList.remove("hidden");
    formMsg.textContent = "";
    okMsg.textContent = "";
    updateFieldBoxes();
    nameIn.focus();
  }

  cancelBtn.addEventListener("click", resetForm);

  saveBtn.addEventListener("click", async function () {
    formMsg.textContent = "";
    okMsg.textContent = "";
    const name = nameIn.value.trim();
    const weight = Number(weightIn.value);
    const fieldKey = fieldKeyFromForm();
    const needsKey = typeIn.value === "field_found" || typeIn.value === "detection_found" || typeIn.value === "nutrition_values";

    if (name === "") { formMsg.textContent = "Please enter a rule name."; return; }
    if (needsKey && fieldKey === "") { formMsg.textContent = "Please fill in the details for this check."; return; }
    if (!Number.isInteger(weight) || weight < 1 || weight > 10) {
      formMsg.textContent = "Weight must be a whole number from 1 to 10.";
      return;
    }

    const payload = { name: name, check_type: typeIn.value, field_key: fieldKey, weight: weight, enabled: enabledIn.checked };

    saveBtn.disabled = true;
    const res = editingId !== null
      ? await apiPut("adminRule", editingId, payload)
      : await apiPost("adminRules", payload);
    saveBtn.disabled = false;
    if (!res.ok) { formMsg.textContent = res.error; return; }

    okMsg.textContent = editingId !== null ? "Rule updated." : "Rule added.";
    resetForm();
    load();
  });

  async function load() {
    const res = await apiGet("adminRules");
    if (!res.ok) { listMsg.textContent = res.error; weightInfo.textContent = ""; return; }
    listMsg.textContent = "";
    rules = asList(res.data, "rules");
    render();
  }

  resetForm();
  load();
})();