(function () {
  const user = requireLogin(["admin"]);
  if (!user) return;
  renderNavbar("admin_history");

  let all = [];
  let view = "total"; // "reviewed", "not" or "total"

  const tabs = {
    reviewed: document.getElementById("tabReviewed"),
    not: document.getElementById("tabNot"),
    total: document.getElementById("tabTotal")
  };
  const titles = { reviewed: "Reviewed", not: "Not reviewed", total: "Total scanned labels" };
  const body = document.getElementById("historyBody");
  const emptyBox = document.getElementById("emptyBox");
  const tableWrap = document.getElementById("tableWrap");

  function reviewText(sc) {
    if (!sc.reviewed) return "Not reviewed";
    const note = sc.review_note ? sc.review_note + " - " : "";
    return note + reviewLine(sc);
  }

  function pick() {
    if (view === "reviewed") return all.filter(function (s) { return s.reviewed; });
    if (view === "not") return all.filter(function (s) { return !s.reviewed; });
    return all;
  }

  function render() {
    Object.keys(tabs).forEach(function (k) {
      tabs[k].classList.toggle("active", k === view);
      tabs[k].setAttribute("aria-pressed", k === view ? "true" : "false");
    });
    document.getElementById("listTitle").textContent = titles[view];

    const list = pick();
    body.textContent = "";
    emptyBox.classList.toggle("hidden", list.length > 0);
    tableWrap.classList.toggle("hidden", list.length === 0);

    list.forEach(function (sc) {
      const tr = document.createElement("tr");
      [
        fmtDate(sc.created_at),
        sc.product_name || "Unknown product",
        (sc.score === null || sc.score === undefined) ? "N/A" : sc.score + "/100"
      ].forEach(function (t) {
        const td = document.createElement("td");
        td.textContent = t;
        tr.appendChild(td);
      });
      const st = document.createElement("td");
      st.appendChild(mk("span", "st-badge " + statusClass(sc.status), STATUS_LABELS[sc.status] || String(sc.status)));
      tr.appendChild(st);
      const rv = document.createElement("td");
      rv.textContent = reviewText(sc);
      tr.appendChild(rv);
      body.appendChild(tr);
    });
  }

  Object.keys(tabs).forEach(function (k) {
    tabs[k].addEventListener("click", function () { view = k; render(); });
  });

  async function load() {
    const res = await apiGet("adminHistory");
    if (!res.ok) { document.getElementById("msg").textContent = res.error; return; }
    all = asList(res.data, "scans").slice().sort(function (a, b) {
      return new Date(b.created_at) - new Date(a.created_at);
    });
    document.getElementById("nReviewed").textContent = all.filter(function (s) { return s.reviewed; }).length;
    document.getElementById("nNot").textContent = all.filter(function (s) { return !s.reviewed; }).length;
    document.getElementById("nTotal").textContent = all.length;
    render();
  }
  load();
})();