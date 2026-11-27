(function () {
  const user = requireLogin(["customer"]);
  if (!user) return;
  renderNavbar("history");

  function cell(tr, text) {
    const td = document.createElement("td");
    td.textContent = text;
    tr.appendChild(td);
    return td;
  }

  async function load() {
    const loading = document.getElementById("loading");
    const res = await apiGet("scans");
    loading.classList.add("hidden");
    if (!res.ok) { document.getElementById("msg").textContent = res.error; return; }

    const list = asList(res.data, "scans").slice().sort(function (a, b) {
      return new Date(b.created_at) - new Date(a.created_at);
    });

    if (list.length === 0) {
      document.getElementById("emptyBox").classList.remove("hidden");
      return;
    }

    document.getElementById("tableWrap").classList.remove("hidden");
    const body = document.getElementById("historyBody");
    list.forEach(function (s) {
      const tr = document.createElement("tr");
      cell(tr, fmtDate(s.created_at));
      cell(tr, scanName(s));
      const score = scanScore(s);
      cell(tr, score === null ? "N/A" : score + "/100");

      const st = document.createElement("td");
      st.appendChild(mk("span", "st-badge " + statusClass(s.status), STATUS_LABELS[s.status] || s.status));
      tr.appendChild(st);

      const rv = document.createElement("td");
      if (isReviewed(s)) {
        rv.appendChild(mk("span", "st-badge good", "Reviewed"));
        rv.appendChild(mk("div", "st-small", reviewLine(s)));
        const note = reviewNote(s);
        if (note) rv.appendChild(mk("div", "st-small", note));
      } else {
        rv.appendChild(mk("span", "st-small", "Not reviewed yet"));
      }
      tr.appendChild(rv);

      const link = document.createElement("td");
      const a = mk("a", "", "View");
      // Both names are passed, because older pages read ?scan= and newer ones ?id=
      a.href = CONFIG.PAGES.result + "?id=" + encodeURIComponent(s.id) + "&scan=" + encodeURIComponent(s.id);
      link.appendChild(a);
      tr.appendChild(link);
      body.appendChild(tr);
    });
  }
  load();
})();