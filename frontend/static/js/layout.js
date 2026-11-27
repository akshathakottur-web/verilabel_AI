// Top bar and "you must be logged in" check, shared by every page after sign in.

function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, function (c) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
  });
}

// Menu for each role. To add a page later, add one line here.
function navItemsFor(role) {
  const P = CONFIG.PAGES;
  if (role === "customer") {
    return [
      { id: "upload", label: "New scan", href: P.upload },
      { id: "history", label: "History", href: P.history }
    ];
  }
  if (role === "inspector") {
    return [
      { id: "inspector", label: "Batches", href: P.inspector },
      { id: "inspector_all", label: "All batches", href: P.inspector_all }
    ];
  }
  if (role === "admin") {
    return [
      { id: "admin_rules", label: "FSSAI rules", href: P.admin_rules },
      { id: "admin_stats", label: "Statistics", href: P.admin_stats },
      { id: "admin_history", label: "History", href: P.admin_history }
    ];
  }
  return [];
}

function homeUrlFor(role) {
  if (role === "inspector") return CONFIG.PAGES.inspector;
  if (role === "admin") return CONFIG.PAGES.admin_rules;
  return CONFIG.PAGES.upload;
}

// Call at the top of every page after sign in.
// Not signed in -> sign in page. Wrong role -> that person's own home page.
function requireLogin(allowedRoles) {
  const user = getSession();
  if (!user) {
    window.location.href = CONFIG.PAGES.signin;
    return null;
  }
  if (allowedRoles && allowedRoles.indexOf(user.role) === -1) {
    goHomeForRole(user.role);
    return null;
  }
  return user;
}

function renderNavbar(activeId) {
  const user = getSession();
  const holder = document.getElementById("navbar") || document.getElementById("topbar");
  if (!user || !holder) return;

  const home = homeUrlFor(user.role);
  // To show the Back button on the home page too, change the next line to: const onHome = false;
  const onHome = window.location.pathname === home;

  const links = navItemsFor(user.role).map(function (item) {
    const cls = item.id === activeId ? "active" : "";
    return '<a href="' + item.href + '" class="' + cls + '">' + escapeHtml(item.label) + "</a>";
  }).join("");

  // The Back button is hidden on a person's home page, where there is nowhere to go back to.
  holder.innerHTML =
    '<div class="nav-inner">' +
      (onHome ? "" : '<button id="backBtn" class="nav-back" type="button" aria-label="Go back">&larr; Back</button>') +
      '<span class="nav-brand">Verilabel AI</span>' +
      "<nav>" + links + "</nav>" +
      '<div class="nav-user"><span>' + escapeHtml(user.name || "") + "</span>" +
      '<button id="logoutBtn" type="button">Log out</button></div>' +
    "</div>";

  const back = document.getElementById("backBtn");
  if (back) {
    back.addEventListener("click", function () {
      if (window.history.length > 1 && document.referrer) window.history.back();
      else window.location.href = home;
    });
  }
  document.getElementById("logoutBtn").addEventListener("click", logout);
}

// Old helper names from yesterday's pages, kept so nothing breaks.
function getQueryParam(name) {
  return new URLSearchParams(window.location.search).get(name);
}
function renderTopbar(activeKey) {
  renderNavbar(activeKey);
}