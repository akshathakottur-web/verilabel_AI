// Shows a warning bar at the top of every page while the fake server is on.
(function () {
  if (typeof CONFIG === "undefined" || !CONFIG.USE_MOCK) return;
  const bar = document.createElement("div");
  bar.setAttribute("role", "status");
  bar.textContent = "Demo mode: results are sample data, not read from your photo.";
  bar.style.cssText =
    "background:#fff4d6;color:#7a5600;text-align:center;padding:8px 12px;" +
    "font:600 0.9rem Poppins,Arial,sans-serif;position:sticky;top:0;z-index:900;";
  document.body.insertBefore(bar, document.body.firstChild);
})();