// USE_MOCK true  = fake server in the browser (works without Member 1's backend)
// USE_MOCK false = real APIs. Then open the pages through Django, not the test server.
const CONFIG = {
  USE_MOCK: true,
  API_BASE: "", // empty = same website as the page

  // From contracts/API_CONTRACT.md. {id} is replaced by the scan or batch number.
  PATHS: {
    // Login and sign up
    signup: "/api/auth/signup/",
    signin: "/api/auth/signin/",
    me: "/api/auth/me/",

    // Scans
    upload: "/api/scans/",
    scans: "/api/scans/",
    myScans: "/api/scans/",
    scan: "/api/scans/{id}/",
    scanStatus: "/api/scans/{id}/",
    scanResult: "/api/scans/{id}/",

    // Report and alternatives
    report: "/api/scans/{id}/report/",
    alternatives: "/api/scans/{id}/alternatives/",

    // Inspector
    inspectorBatches: "/api/inspector/batches/",
    inspectorBatch: "/api/inspector/batches/{id}/",
    inspectorReview: "/api/inspector/scans/{id}/review/",

    // Admin
    adminRules: "/api/admin/rules/",
    adminRule: "/api/admin/rules/{id}/",
    adminHistory: "/api/admin/history/",
    adminStats: "/api/admin/stats/"
  },

  // Page addresses. Ask Member 1 for the real Django page URLs, then change ONLY these lines.
  PAGES: {
    signin: "/templates/signin.html",
    upload: "/templates/upload.html",
    progress: "/templates/progress.html",
    result: "/templates/result.html",
    history: "/templates/history.html",
    inspector: "/templates/inspector.html",
    admin_rules: "/templates/admin_rules.html",
        admin_history: "/templates/admin_history.html",
    admin_stats: "/templates/admin_stats.html"
  }
};