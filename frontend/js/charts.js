/**
 * charts.js — Chart.js wrapper utilities
 * All charts use CSS variable colours and share consistent axis/grid styling.
 */

const CHARTS = (() => {

  // ── Chart registry — destroy before re-render ─────────────────────────
  const registry = {};

  function destroy(id) {
    if (registry[id]) { registry[id].destroy(); delete registry[id]; }
  }

  // ── Shared defaults ───────────────────────────────────────────────────
  function getCSSVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  function gridColor()  { return getCSSVar('--border-subtle') || 'rgba(255,255,255,0.06)'; }
  function textColor()  { return getCSSVar('--text-tertiary')  || '#5a6070'; }
  function getColors()  {
    return ['--c1','--c2','--c3','--c4','--c5','--c6'].map(c => getCSSVar(c));
  }

  const BASE_SCALES = () => ({
    x: {
      ticks:  { color: textColor(), font: { size: 11, family: 'Inter' } },
      grid:   { color: gridColor() },
      border: { color: 'transparent' },
    },
    y: {
      ticks:  { color: textColor(), font: { size: 11, family: 'Inter' } },
      grid:   { color: gridColor() },
      border: { color: 'transparent' },
    }
  });

  const BASE_OPTS = () => ({
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 500, easing: 'easeOutQuart' },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: getCSSVar('--bg-elevated') || '#1a1e25',
        titleColor:  getCSSVar('--text-primary')   || '#e8eaed',
        bodyColor:   getCSSVar('--text-secondary')  || '#8b9098',
        borderColor: getCSSVar('--border-default')  || 'rgba(255,255,255,0.1)',
        borderWidth: 1,
        padding: 10,
        cornerRadius: 8,
        titleFont: { family: 'Inter', weight: '500', size: 12 },
        bodyFont:  { family: 'Inter', size: 12 },
      }
    }
  });

  // ── Factory ───────────────────────────────────────────────────────────
  function make(id, type, labels, datasets, extraOpts = {}) {
    destroy(id);
    const canvas = document.getElementById(id);
    if (!canvas) return null;
    const chart = new Chart(canvas, {
      type,
      data: { labels, datasets },
      options: deepMerge(BASE_OPTS(), extraOpts),
    });
    registry[id] = chart;
    return chart;
  }

  function deepMerge(target, source) {
    const out = { ...target };
    for (const key of Object.keys(source)) {
      if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
        out[key] = deepMerge(target[key] || {}, source[key]);
      } else {
        out[key] = source[key];
      }
    }
    return out;
  }

  // ── Specific chart builders ───────────────────────────────────────────

  function line(id, labels, data, color, opts = {}) {
    const c = color || getColors()[0];
    return make(id, 'line', labels, [{
      data,
      borderColor: c,
      backgroundColor: c + '18',
      borderWidth: 2,
      pointRadius: 2,
      pointHoverRadius: 4,
      fill: true,
      tension: 0.38,
    }], deepMerge({ scales: BASE_SCALES() }, opts));
  }

  function multiLine(id, labels, series, opts = {}) {
    const colors = getColors();
    const datasets = series.map((s, i) => ({
      label: s.label,
      data: s.data,
      borderColor: s.color || colors[i],
      backgroundColor: (s.color || colors[i]) + '12',
      borderWidth: 2,
      pointRadius: 2,
      pointHoverRadius: 4,
      fill: false,
      tension: 0.38,
      borderDash: s.dash || [],
      yAxisID: s.yAxisID || 'y',
    }));
    return make(id, 'line', labels, datasets, deepMerge({ scales: BASE_SCALES() }, opts));
  }

  function bar(id, labels, data, colors, opts = {}) {
    const palette = getColors();
    const bg = Array.isArray(colors) ? colors
      : (data.map((_, i) => (colors || palette[0])));
    return make(id, 'bar', labels, [{
      data,
      backgroundColor: bg,
      borderRadius: 5,
      borderSkipped: false,
    }], deepMerge({ scales: BASE_SCALES() }, opts));
  }

  function doughnut(id, labels, data, opts = {}) {
    const colors = getColors();
    return make(id, 'doughnut', labels, [{
      data,
      backgroundColor: colors.slice(0, data.length),
      borderWidth: 0,
      hoverOffset: 6,
    }], deepMerge({ cutout: '65%', plugins: { legend: { display: false } } }, opts));
  }

  // ── Daily trip line (overview) ─────────────────────────────────────────
  function renderDailyTrips(canvasId) {
    const rows  = DATA.dailyTrips();
    const labels = rows.map(r => r.pickup_date.slice(5));   // MM-DD
    const values = rows.map(r => r.trips);
    const c = getCSSVar('--c1');
    return line(canvasId, labels, values, c, {
      scales: {
        ...BASE_SCALES(),
        y: { ...BASE_SCALES().y, ticks: { ...BASE_SCALES().y.ticks, callback: v => (v/1000).toFixed(0)+'k' } },
        x: { ...BASE_SCALES().x, ticks: { ...BASE_SCALES().x.ticks, maxTicksLimit: 10 } },
      },
      plugins: { ...BASE_OPTS().plugins, tooltip: { ...BASE_OPTS().plugins.tooltip, callbacks: {
        label: ctx => `${(ctx.parsed.y/1000).toFixed(1)}k trips`
      }}}
    });
  }

  // ── Borough bar ────────────────────────────────────────────────────────
  function renderBoroughBar(canvasId) {
    const rows = DATA.boroughSummary();
    const labels = rows.map(r => r.borough);
    const values = rows.map(r => r.pct);
    const colors = getColors();
    return bar(canvasId, labels, values, colors, {
      scales: {
        ...BASE_SCALES(),
        y: { ...BASE_SCALES().y, ticks: { ...BASE_SCALES().y.ticks, callback: v => v+'%' } },
      }
    });
  }

  // ── Hourly volume bar ─────────────────────────────────────────────────
  function renderHourlyBar(canvasId) {
    const rows = DATA.hourlyVolume();
    const labels = rows.map(r => r.hour + ':00');
    const values = rows.map(r => r.avg_trips_per_day);
    const accent = getCSSVar('--c1');
    const dim    = accent + '55';
    const bg = values.map(v => v > 1200 ? accent : dim);
    return bar(canvasId, labels, values, bg, {
      scales: {
        ...BASE_SCALES(),
        y: { ...BASE_SCALES().y, ticks: { ...BASE_SCALES().y.ticks, callback: v => (v/1000).toFixed(1)+'k' } },
        x: { ...BASE_SCALES().x, ticks: { ...BASE_SCALES().x.ticks, maxTicksLimit: 12 } },
      }
    });
  }

  // ── Distance histogram ─────────────────────────────────────────────────
  function renderDistBar(canvasId) {
    const rows = DATA.distanceDist();
    return bar(canvasId, rows.map(r=>r.bucket), rows.map(r=>r.pct), getCSSVar('--c2'), {
      scales: { ...BASE_SCALES(), y: { ...BASE_SCALES().y, ticks: { ...BASE_SCALES().y.ticks, callback: v => v+'%' } } }
    });
  }

  // ── Duration histogram ─────────────────────────────────────────────────
  function renderDurBar(canvasId) {
    const data  = [8,22,26,19,14,7,4];
    const lbls  = ['0–5 min','5–10','10–15','15–20','20–30','30–45','45+'];
    return bar(canvasId, lbls, data, getCSSVar('--c5'), {
      scales: { ...BASE_SCALES(), y: { ...BASE_SCALES().y, ticks: { ...BASE_SCALES().y.ticks, callback: v => v+'%' } } }
    });
  }

  // ── Payment doughnut ───────────────────────────────────────────────────
  function renderPayDoughnut(canvasId) {
    const rows = DATA.paymentBreakdown();
    return doughnut(canvasId, rows.map(r=>r.label), rows.map(r=>r.pct));
  }

  // ── Fare distribution bar ──────────────────────────────────────────────
  function renderFareDist(canvasId) {
    const rows = DATA.fareDistribution();
    return bar(canvasId, rows.map(r=>r.bucket), rows.map(r=>r.pct), getCSSVar('--c3'), {
      scales: { ...BASE_SCALES(), y: { ...BASE_SCALES().y, ticks: { ...BASE_SCALES().y.ticks, callback: v => v+'%' } } }
    });
  }

  // ── Fare by hour ───────────────────────────────────────────────────────
  function renderFareHour(canvasId) {
    const rows = DATA.fareByHour();
    const labels = rows.map(r => r.hour+':00');
    return line(canvasId, labels, rows.map(r=>r.avg_fare), getCSSVar('--c3'), {
      scales: {
        ...BASE_SCALES(),
        y: { ...BASE_SCALES().y, ticks: { ...BASE_SCALES().y.ticks, callback: v => '$'+v.toFixed(0) } },
        x: { ...BASE_SCALES().x, ticks: { ...BASE_SCALES().x.ticks, maxTicksLimit: 8 } },
      }
    });
  }

  // ── Insight 1: avg fare by service zone ───────────────────────────────
  function renderInsight1(canvasId) {
    const rows = DATA.insightAirport();
    const colors = getColors();
    return bar(canvasId, rows.map(r=>r.service_zone), rows.map(r=>r.avg_fare),
      rows.map((_,i) => colors[i]), {
      scales: { ...BASE_SCALES(), y: { ...BASE_SCALES().y, ticks: { ...BASE_SCALES().y.ticks, callback: v => '$'+v } } }
    });
  }

  // ── Insight 2: speed + fare/min dual axis ─────────────────────────────
  function renderInsight2(canvasId) {
    const rows = DATA.insightNight();
    const labels = rows.map(r => r.hour+':00');
    return multiLine(canvasId, labels, [
      { label:'Avg speed (mph)', data: rows.map(r=>r.avg_speed), color: getCSSVar('--c1'), yAxisID:'y' },
      { label:'Fare/min ($)',    data: rows.map(r=>r.fare_per_min), color: getCSSVar('--c3'), yAxisID:'y2', dash:[4,3] },
    ], {
      scales: {
        x: BASE_SCALES().x,
        y:  { ...BASE_SCALES().y, position:'left',  ticks:{ ...BASE_SCALES().y.ticks, callback: v => v.toFixed(0)+' mph' } },
        y2: { ...BASE_SCALES().y, position:'right', grid:{ display:false }, ticks:{ ...BASE_SCALES().y.ticks, callback: v => '$'+v.toFixed(2) } },
      },
      plugins: { ...BASE_OPTS().plugins, legend: { display: true,
        labels: { color: textColor(), font:{ size:11, family:'Inter' }, boxWidth:10, boxHeight:10 }
      }}
    });
  }

  // ── Insight 3: tip rate by payment ────────────────────────────────────
  function renderInsight3(canvasId) {
    const rows = DATA.insightTips();
    const colors = [getCSSVar('--c1'), getCSSVar('--text-tertiary'), getCSSVar('--c2'), getCSSVar('--c4')];
    return bar(canvasId, rows.map(r=>r.label), rows.map(r=>r.avg_tip_pct), colors, {
      scales: {
        ...BASE_SCALES(),
        y: { ...BASE_SCALES().y, max:30, ticks:{ ...BASE_SCALES().y.ticks, callback: v => v+'%' } }
      }
    });
  }

  return {
    destroy, getColors, getCSSVar,
    line, multiLine, bar, doughnut,
    renderDailyTrips, renderBoroughBar, renderHourlyBar,
    renderDistBar, renderDurBar,
    renderPayDoughnut, renderFareDist, renderFareHour,
    renderInsight1, renderInsight2, renderInsight3,
  };
})();
