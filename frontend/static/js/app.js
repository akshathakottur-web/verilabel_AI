// Shared helpers for every page after login.

const NAV_BY_ROLE = {
  customer: [["upload", "Scan a label"], ["history", "History"]],
  inspector: [["inspector", "Batches"]],
  admin: [["admin_rules", "Rules"], ["admin_stats", "Statistics"]]
};

// Sends the visitor to the login page if not signed in, or home if the role is wrong.
function requireLogin(allowedRoles) {
  const s = getSession();
  if (!s) { window.location.href = CONFIG.PAGES.signin; return null; }
  if (allowedRoles && allowedRoles.indexOf(s.role) === -1) { goHomeForRole(s.role); return null; }
  return s;
}

function getQueryParam(name) {
  return new URLSearchParams(window.location.search).get(name);
}

function homeUrlForRole(role) {
  if (role === "inspector") return CONFIG.PAGES.inspector;
  if (role === "admin") return CONFIG.PAGES.admin_rules;
  return CONFIG.PAGES.upload;
}

function makeEl(tag, className, text) {
  const e = document.createElement(tag);
  if (className) e.className = className;
  if (text !== undefined) e.textContent = text;
  return e;
}

// Fills <div id="topbar"></div> with the logo, menu, user name and logout button.
function renderTopbar(activeKey) {
  const s = getSession();
  const host = document.getElementById("topbar");
  if (!host || !s) return;
  host.className = "topbar";
  host.textContent = "";

  const brand = makeEl("a", "brand");
  brand.href = homeUrlForRole(s.role);
  brand.innerHTML = '<span class="brand-mark"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12l5 5 9-10"/></svg></span>';
  brand.appendChild(document.createTextNode("Verilabel AI"));
  host.appendChild(brand);

  const nav = makeEl("nav", "nav");
  (NAV_BY_ROLE[s.role] || []).forEach(function (item) {
    const a = makeEl("a", item[0] === activeKey ? "active" : "", item[1]);
    a.href = CONFIG.PAGES[item[0]];
    nav.appendChild(a);
  });
  host.appendChild(nav);

  const chip = makeEl("div", "user-chip");
  chip.appendChild(makeEl("span", "", s.name || s.user_id));
  const out = makeEl("button", "link-btn", "Log out");
  out.type = "button";
  out.addEventListener("click", logout);
  chip.appendChild(out);
  host.appendChild(chip);
}