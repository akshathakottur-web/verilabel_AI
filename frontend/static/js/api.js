// One place for all server calls, so each page stays simple.
// Every call returns { ok: true, data } or { ok: false, error }.

function authHeaders() {
  const s = getSession();
  return s && s.token ? { "Authorization": "Token " + s.token } : {};
}

function buildUrl(pathKey, id) {
  const template = CONFIG.PATHS[pathKey];
  if (typeof template !== "string") throw new Error("Unknown API path: " + pathKey);
  const idText = (id === undefined || id === null) ? "" : encodeURIComponent(id);
  return CONFIG.API_BASE + template.replace("{id}", idText);
}

async function realRequest(method, pathKey, opts) {
  opts = opts || {};
  try {
    const headers = authHeaders();
    let body;
    if (opts.form) {
      body = opts.form; // the browser sets the content type for file uploads
    } else if (opts.body) {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(opts.body);
    }
    const res = await fetch(buildUrl(pathKey, opts.id), { method: method, headers: headers, body: body });

    if (opts.download) {
      if (!res.ok) return { ok: false, error: "Could not download the file." };
      const blob = await res.blob();
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = opts.filename || "download";
      document.body.appendChild(link);
      link.click();
      link.remove();
      return { ok: true, data: {} };
    }

    const data = await res.json().catch(function () { return {}; });
    if (!res.ok) {
      return { ok: false, error: data.error || data.detail || data.message || "Something went wrong. Please try again." };
    }
    return { ok: true, data: data };
  } catch (e) {
    return { ok: false, error: "Cannot reach the server. Check your internet or try later." };
  }
}

// ---------- Functions the pages call ----------
function apiPost(pathKey, body) {
  return CONFIG.USE_MOCK ? mockRequest("POST", pathKey, { body: body }) : realRequest("POST", pathKey, { body: body });
}
function apiPut(pathKey, id, body) {
  return CONFIG.USE_MOCK ? mockRequest("PUT", pathKey, { id: id, body: body }) : realRequest("PUT", pathKey, { id: id, body: body });
}
function apiGet(pathKey, id) {
  return CONFIG.USE_MOCK ? mockRequest("GET", pathKey, { id: id }) : realRequest("GET", pathKey, { id: id });
}
// Customer photo upload: form field "image" (see contracts/API_CONTRACT.md)
function apiUpload(file) {
  const form = new FormData();
  form.append("image", file);
  return CONFIG.USE_MOCK ? mockRequest("POST", "upload", { file: file }) : realRequest("POST", "upload", { form: form });
}
// Saves a file such as the PDF report
function apiDownload(pathKey, id, filename) {
  return CONFIG.USE_MOCK
    ? mockRequest("GET", pathKey, { id: id, download: true, filename: filename })
    : realRequest("GET", pathKey, { id: id, download: true, filename: filename });
}

// ---------- Fake server, used only while USE_MOCK is true ----------
function loadMockUsers() {
  let users = {};
  try { users = JSON.parse(localStorage.getItem("verilabel_mock_users")) || {}; } catch (e) { users = {}; }
  // DEMO ONLY. Real accounts come from Member 1's database.
  if (!users["admin"]) users["admin"] = { name: "Admin", role: "admin", password: "admin123" };
  if (!users["inspector1"]) users["inspector1"] = { name: "Inspector One", role: "inspector", password: "inspect123" };
  return users;
}

function mockRequest(method, pathKey, opts) {
  return new Promise(function (resolve) {
    setTimeout(function () {
      try { resolve(mockHandle(method, pathKey, opts || {})); }
      catch (e) { resolve({ ok: false, error: "Mock error: " + e.message }); }
    }, 400);
  });
}

function mockHandle(method, pathKey, opts) {
  // Inspector and Admin pages are answered by staff-api.js
  if (typeof mockStaffHandle === "function") {
    const staffResult = mockStaffHandle(method, pathKey, opts);
    if (staffResult) return staffResult;
  }

  // ----- accounts -----
  if (pathKey === "signup" || pathKey === "signin") {
    const users = loadMockUsers();
    const b = opts.body || {};
    if (pathKey === "signup") {
      if (users[b.user_id]) return { ok: false, error: "This ID is already taken." };
      users[b.user_id] = { name: b.name, role: b.role, password: b.password };
      localStorage.setItem("verilabel_mock_users", JSON.stringify(users));
      return { ok: true, data: { name: b.name, user_id: b.user_id, role: b.role } };
    }
    const u = users[b.user_id];
    if (!u || u.password !== b.password) return { ok: false, error: "Wrong ID or password." };
    return { ok: true, data: { token: "mock-token", user: { name: u.name, user_id: b.user_id, role: u.role } } };
  }

  const scans = loadMockScans();

  // ----- upload a photo -----
  if (pathKey === "upload") {
    const nextId = scans.reduce(function (m, s) {
      return (typeof s.id === "number" && s.id > m) ? s.id : m;
    }, 0) + 1;
    const name = opts.file && opts.file.name ? opts.file.name.replace(/\.[^.]+$/, "") : "Scanned product";
    const failed = RULE_NAMES.filter(function () { return Math.random() < 0.25; });
    const record = buildMockRecord(nextId, name, failed);
    record.started = Date.now();
    scans.unshift(record);
    saveMockScans(scans);
    return { ok: true, data: { scan_id: nextId, status: "queued" } };
  }

  // ----- list of this user's scans -----
  if (pathKey === "scans" || pathKey === "myScans") {
    return { ok: true, data: scans };
  }

  // ----- one scan (status and result are the same record, as in the contract) -----
  if (pathKey === "scan" || pathKey === "scanStatus" || pathKey === "scanResult" ||
      pathKey === "alternatives" || pathKey === "report") {
    const scan = scans.filter(function (s) { return String(s.id) === String(opts.id); })[0];
    if (!scan) return { ok: false, error: "Scan not found." };

    if (pathKey === "alternatives") return { ok: true, data: MOCK_ALTERNATIVES };

    if (pathKey === "report") {
      const text = "Verilabel AI sample report (demo mode)\n" +
        "Product: " + scan.product_name + "\nScore: " + scan.score + "\nVerdict: " + scan.verdict + "\n";
      const blob = new Blob([text], { type: "text/plain" });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = "verilabel-report-" + scan.id + ".txt";
      document.body.appendChild(link);
      link.click();
      link.remove();
      return { ok: true, data: {} };
    }

    let status = scan.status;
    if (scan.started) {
      const elapsed = Date.now() - scan.started;
      if (elapsed < 2000) status = "queued";
      else if (elapsed < 5000) status = "processing";
    }
    const copy = JSON.parse(JSON.stringify(scan));
    copy.status = status;
    return { ok: true, data: copy };
  }

  return { ok: false, error: "Mock not built yet for: " + pathKey };
}

// ---------- Login session (kept in the browser) ----------
function saveSession(session) { localStorage.setItem("verilabel_user", JSON.stringify(session)); }
function getSession() {
  const s = localStorage.getItem("verilabel_user");
  return s ? JSON.parse(s) : null;
}
function logout() {
  localStorage.removeItem("verilabel_user");
  window.location.href = CONFIG.PAGES.signin;
}
function goHomeForRole(role) {
  if (role === "inspector") window.location.href = CONFIG.PAGES.inspector;
  else if (role === "admin") window.location.href = CONFIG.PAGES.admin_rules;
  else window.location.href = CONFIG.PAGES.upload;
}