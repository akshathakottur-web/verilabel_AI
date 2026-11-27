(function () {
  const user = requireLogin(["admin"]);
  if (!user) return;
  renderNavbar("admin_stats");

  const NS = "http://www.w3.org/2000/svg";

  function svgEl(name, attrs, text) {
    const e = document.createElementNS(NS, name);
    Object.keys(attrs || {}).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    if (text !== undefined) e.textContent = text;
    return e;
  }

  function noData(box) {
    box.textContent = "";
    box.appendChild(mk("p", "st-muted", "No data yet."));
  }

  // Vertical bars: items = [{ label, value }]
  function columnChart(box, items, description) {
    box.textContent = "";
    const max = Math.max.apply(null, items.map(function (i) { return i.value; }).concat([0]));
    if (items.length === 0 || max === 0) return noData(box);

    const W = 600, H = 230, pad = 30;
    const svg = svgEl("svg", { viewBox: "0 0 " + W + " " + H, role: "img", "aria-label": description });
    const slot = (W - pad * 2) / items.length;
    const bw = slot * 0.6;
    items.forEach(function (it, i) {
      const h = (H - pad * 2) * it.value / max;
      const x = pad + i * slot + (slot - bw) / 2;
      svg.appendChild(svgEl("rect", { x: x, y: H - pad - h, width: bw, height: h, rx: 4, fill: "#5b9c87" }));
      if (it.value > 0) {
        svg.appendChild(svgEl("text", { x: x + bw / 2, y: H - pad - h - 5, "text-anchor": "middle", "font-size": 12, fill: "#14302a" }, String(it.value)));
      }
      if (i % 2 === 0) {
        svg.appendChild(svgEl("text", { x: x + bw / 2, y: H - 10, "text-anchor": "middle", "font-size": 11, fill: "#4d6b62" }, it.label));
      }
    });
    box.appendChild(svg);
  }

  // Donut: parts = [{ label, value, color }]
  function donut(box, parts) {
    box.textContent = "";
    const total = parts.reduce(function (a, p) { return a + p.value; }, 0);
    if (total === 0) return noData(box);

    const R = 54, C = 2 * Math.PI * R;
    const svg = svgEl("svg", { viewBox: "0 0 150 150", role: "img", "aria-label": "Compliance overview donut chart", style: "max-width:220px;display:block;margin:0 auto" });
    const g = svgEl("g", { transform: "rotate(-90 75 75)", fill: "none", "stroke-width": 22 });
    let offset = 0;
    parts.forEach(function (p) {
      const len = C * p.value / total;
      g.appendChild(svgEl("circle", { cx: 75, cy: 75, r: R, stroke: p.color, "stroke-dasharray": len + " " + C, "stroke-dashoffset": -offset }));
      offset += len;
    });
    svg.appendChild(g);
    box.appendChild(svg);

    const legend = mk("div", "st-legend");
    parts.forEach(function (p) {
      const item = mk("span");
      const sw = mk("span", "st-swatch");
      sw.style.background = p.color;
      item.appendChild(sw);
      item.appendChild(document.createTextNode(p.label + ": " + p.value + " (" + Math.round(p.value / total * 100) + "%)"));
      legend.appendChild(item);
    });
    box.appendChild(legend);
  }

  // Horizontal bars: items = [{ name, count }]
  function barList(box, items) {
    box.textContent = "";
    if (!items.length) return noData(box);
    const max = Math.max.apply(null, items.map(function (i) { return i.count; })) || 1;
    items.forEach(function (it) {
      const row = mk("div", "st-bar-row");
      const top = mk("div", "st-bar-top");
      top.appendChild(mk("span", "", it.name));
      top.appendChild(mk("strong", "", String(it.count)));
      row.appendChild(top);
      const track = mk("div", "st-bar-track");
      const fill = mk("div", "st-bar-fill");
      fill.style.width = Math.round(it.count / max * 100) + "%";
      track.appendChild(fill);
      row.appendChild(track);
      box.appendChild(row);
    });
  }

  function shortDay(iso) {
    const d = new Date(iso + "T00:00:00");
    return isNaN(d.getTime()) ? iso : d.getDate() + "/" + (d.getMonth() + 1);
  }

  // The last 14 days, including days with no scans (the API only sends days that have scans).
  function fillDays(perDay) {
    const counts = {};
    (perDay || []).forEach(function (d) { counts[d.date] = d.count; });
    const items = [];
    for (let i = 13; i >= 0; i--) {
      const d = new Date(); d.setDate(d.getDate() - i);
      const iso = d.toISOString().slice(0, 10);
      items.push({ label: shortDay(iso), value: counts[iso] || 0 });
    }
    return items;
  }

  // Text for the "Reviewed" column.
  function reviewText(sc) {
    if (!isReviewed(sc)) return "Not reviewed";
    const note = reviewNote(sc) ? reviewNote(sc) + " - " : "";
    return note + reviewLine(sc);
  }

  function show(id, value) {
    document.getElementById(id).textContent = (value === undefined || value === null) ? "-" : value;
  }

  async function load() {
    const msg = document.getElementById("msg");
    // Real API: GET /api/admin/stats/. All the numbers come from the database, so they
    // always match the History page.
    const res = await apiGet("adminStats");
    if (!res.ok) { msg.textContent = res.error; return; }
    const s = res.data;

    const vc = s.verdict_counts || {};
    const sum = (vc.COMPLIANT || 0) + (vc.PARTIAL || 0) + (vc.NON_COMPLIANT || 0);

    show("sTotal", s.total_scanned);
    show("sReviewed", s.reviewed);
    show("sNot", s.not_reviewed);
    show("sAvg", (s.average_score === null || s.average_score === undefined) ? null : s.average_score + "/100");
    show("sGood", sum ? Math.round((vc.COMPLIANT || 0) / sum * 100) + "%" : null);

    columnChart(document.getElementById("dayChart"), fillDays(s.scans_per_day), "Scans per day for the last 14 days");
    donut(document.getElementById("donutChart"), [
      { label: "Compliant", value: vc.COMPLIANT || 0, color: "#1b6b4a" },
      { label: "Partial", value: vc.PARTIAL || 0, color: "#e8890c" },
      { label: "Non-compliant", value: vc.NON_COMPLIANT || 0, color: "#c62d22" }
    ]);
    barList(document.getElementById("failBox"), (s.most_failed_rules || []).map(function (r) {
      return { name: r.name, count: r.failures };
    }));
    barList(document.getElementById("topBox"), (s.top_products || []).map(function (p) {
      return { name: p.product_name, count: p.count };
    }));

    const body = document.getElementById("historyBody");
    body.textContent = "";
    (s.recent_scans || []).forEach(function (sc) {
      const tr = document.createElement("tr");
      const score = scanScore(sc);
      [
        fmtDate(sc.created_at),
        scanName(sc),
        score === null ? "N/A" : score + "/100"
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
  load();
})();