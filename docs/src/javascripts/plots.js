// Plotly plots for the Assessment spaced-repetition formulas.
// Theme-aware (Material CSS vars), survives instant navigation (document$).
(function () {
  const PALETTE = ["#56b4e9", "#e69f00", "#009e73"]; // Okabe–Ito: sky blue, orange, green
  const FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif";

  function colors() {
    const dark = document.body.getAttribute("data-md-color-scheme") === "slate";
    const cs = getComputedStyle(document.body);
    return {
      fg: cs.getPropertyValue("--md-default-fg-color").trim() || (dark ? "#e6e6e6" : "#333"),
      grid: dark ? "rgba(255,255,255,0.13)" : "rgba(0,0,0,0.12)",
      line: dark ? "rgba(255,255,255,0.34)" : "rgba(0,0,0,0.28)",
    };
  }

  function linspace(a, b, n) {
    const o = [];
    for (let i = 0; i < n; i++) o.push(a + (b - a) * i / (n - 1));
    return o;
  }

  function recall() {
    const x = linspace(0, 12, 120);
    const traces = [1, 3, 9].map((h, i) => ({
      x, y: x.map(d => Math.pow(2, -d / h)),
      mode: "lines", name: "h = " + h, line: { color: PALETTE[i], width: 2.5, shape: "spline" },
    }));
    const layout = {
      xaxis: { title: "Δ, days", range: [0, 12] },
      yaxis: { title: "p", range: [0, 1] },
      shapes: [{ type: "line", x0: 0, x1: 12, y0: 0.5, y1: 0.5, line: { dash: "dot", width: 1.5 } }],
    };
    return { traces, layout };
  }

  function halflife() {
    const n = [0, 1, 2, 3, 4, 5, 6];
    const traces = [{
      x: n, y: n.map(k => Math.pow(2.5, k)), mode: "lines+markers", name: "h₀·EFⁿ",
      line: { color: PALETTE[0], width: 2.5 }, marker: { color: PALETTE[0], size: 8 },
    }];
    const layout = { showlegend: false, xaxis: { title: "n", dtick: 1 }, yaxis: { title: "h, days", rangemode: "tozero" } };
    return { traces, layout };
  }

  function softmax() {
    const f = [0.9, 0.7, 0.5, 0.3, 0.1];
    const labels = f.map(v => "f = " + v);
    const traces = [1, 3].map((beta, i) => {
      const w = f.map(v => Math.pow(v, beta));
      const Z = w.reduce((a, c) => a + c, 0);
      return { x: labels, y: w.map(v => v / Z), type: "bar", name: "β = " + beta, marker: { color: PALETTE[i] } };
    });
    const layout = { barmode: "group", bargap: 0.28, xaxis: { title: "candidate" }, yaxis: { title: "P(i)", rangemode: "tozero" } };
    return { traces, layout };
  }

  const BUILDERS = { recall, halflife, softmax };

  function render(div) {
    const build = BUILDERS[div.getAttribute("data-plot")];
    if (!build || !window.Plotly) return;
    const c = colors();
    const { traces, layout } = build();
    [layout.xaxis, layout.yaxis].forEach(ax => {
      ax.gridcolor = c.grid; ax.linecolor = c.line; ax.zeroline = false;
      ax.tickcolor = c.line;
      ax.title = { text: ax.title, font: { size: 13, color: c.fg } };
      ax.tickfont = { size: 11, color: c.fg };
    });
    (layout.shapes || []).forEach(s => { s.line.color = c.line; });
    const full = Object.assign({
      margin: { l: 54, r: 18, t: 18, b: 48 },
      paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
      font: { family: FONT, color: c.fg, size: 12 },
      hovermode: "x unified",
      hoverlabel: { font: { family: FONT, size: 12 } },
      showlegend: true,
      legend: { orientation: "h", y: 1.14, x: 1, xanchor: "right", font: { size: 12, color: c.fg } },
    }, layout);
    Plotly.react(div, traces, full, { responsive: true, displayModeBar: false });
  }

  function renderAll() { document.querySelectorAll("div[data-plot]").forEach(render); }

  // Wait for the Plotly CDN script before rendering (retry up to ~5s).
  function boot() {
    if (window.Plotly) return renderAll();
    let tries = 0;
    const t = setInterval(() => {
      if (window.Plotly || ++tries > 50) { clearInterval(t); renderAll(); }
    }, 100);
  }

  // Render on this page load.
  if (document.readyState !== "loading") boot();
  else document.addEventListener("DOMContentLoaded", boot);

  // Re-render on light/dark toggle.
  new MutationObserver(renderAll).observe(document.body,
    { attributes: true, attributeFilter: ["data-md-color-scheme"] });

  // Re-render on Material instant navigation, if that ever gets enabled.
  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(boot);
  }
})();

// demo self-check: recall at Δ=h must be 0.5, growth at n=0 must be h0
console.assert(Math.abs(Math.pow(2, -3 / 3) - 0.5) < 1e-9, "recall(h)=0.5");
console.assert(Math.pow(2.5, 0) === 1, "halflife(0)=h0");
