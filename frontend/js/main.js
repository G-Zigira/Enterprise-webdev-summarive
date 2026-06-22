

(function () {

  // Page registry
  const PAGES = {
    overview: { label: 'Overview',      build: buildOverview,  init: initOverview  },
    trips:    { label: 'Trip Patterns',  build: buildTrips,     init: initTrips     },
    fares:    { label: 'Fare Analysis',  build: buildFares,     init: initFares     },
    zones:    { label: 'Zone Explorer',  build: buildZones,     init: initZones     },
    schema:   { label: 'DB Schema',      build: buildSchema,    init: ()=>{}        },
    algo:     { label: 'Algorithm',      build: buildAlgo,      init: initAlgo      },
    insights: { label: 'Key Insights',   build: buildInsights,  init: initInsights  },
  };

  let currentPage = 'overview';

  //  Router 
    if (!PAGES[name]) return;
    currentPage = name;

    document.getElementById('breadcrumbCurrent').textContent = PAGES[name].label;
    document.getElementById('mainContent').innerHTML = PAGES[name].build();

    document.querySelectorAll('.nav-item').forEach(b => {
      b.classList.toggle('active', b.dataset.page === name);
    });

    // Slight delay so DOM is ready for canvas
    requestAnimationFrame(() => {
      requestAnimationFrame(() => PAGES[name].init());
    });
  }

  // Theme toggle 
  function initTheme() {
    const root  = document.documentElement;
    const btn   = document.getElementById('themeToggle');
    const icon  = document.getElementById('themeIcon');
    const label = document.getElementById('themeLabel');

    const saved = localStorage.getItem('taxi-theme') || 'dark';
    root.dataset.theme = saved;
    updateThemeUI(saved);

    btn.addEventListener('click', () => {
      const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
      root.dataset.theme = next;
      localStorage.setItem('taxi-theme', next);
      updateThemeUI(next);
      // Re-render current page charts with new colours
      setTimeout(() => PAGES[currentPage].init(), 80);
    });

    function updateThemeUI(theme) {
      icon.className  = theme === 'dark' ? 'ti ti-sun' : 'ti ti-moon';
      label.textContent = theme === 'dark' ? 'Light mode' : 'Dark mode';
    }
  }

  //  Sidebar toggle (mobile) 
  function initSidebar() {
    document.getElementById('sidebarToggle')?.addEventListener('click', () => {
      document.getElementById('sidebar').classList.toggle('open');
    });
    document.querySelectorAll('.nav-item').forEach(btn => {
      btn.addEventListener('click', () => {
        showPage(btn.dataset.page);
        document.getElementById('sidebar').classList.remove('open');
      });
    });
  }



  //  OVERVIEW 
  function buildOverview() {
    const k = DATA.kpis();
    return `
      <div class="page-header">
        <h1>Overview</h1>
        <p>NYC Yellow Taxi — January 2024 · ${(k.total_trips/1e6).toFixed(2)}M trips analysed</p>
      </div>

      <div class="metric-grid">
        ${metricCard('Total Trips',    (k.total_trips/1e6).toFixed(2)+'M', 'Jan 2024')}
        ${metricCard('Avg Base Fare',  '$'+k.avg_fare,    'excl. tips & tolls')}
        ${metricCard('Avg Distance',   k.avg_distance_mi+' mi', 'per trip')}
        ${metricCard('Avg Duration',   k.avg_duration_min+' min','pickup → dropoff')}
        ${metricCard('Avg Tip Rate',   k.avg_tip_pct+'%', 'of base fare')}
        ${metricCard('Active Zones',   k.active_zones,    'of 263 total')}
      </div>

      <div class="grid-2 mb-14">
        <div class="card">
          <div class="card-title">Daily trips — January 2024</div>
          <div class="chart-wrap" style="height:180px"><canvas id="dailyChart"></canvas></div>
        </div>
        <div class="card">
          <div class="card-title">Trips by borough (pickup)</div>
          <div class="chart-wrap" style="height:180px"><canvas id="boroughChart"></canvas></div>
          <div class="legend" style="margin-top:10px">
            ${DATA.boroughSummary().map((r,i)=>`<div class="legend-item"><div class="legend-dot" style="background:var(--c${i+1})"></div>${r.borough} ${r.pct}%</div>`).join('')}
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-title">Avg hourly trip volume (across all days)</div>
        <div class="chart-wrap" style="height:160px"><canvas id="hourlyChart"></canvas></div>
      </div>`;
  }

  function initOverview() {
    CHARTS.renderDailyTrips('dailyChart');
    CHARTS.renderBoroughBar('boroughChart');
    CHARTS.renderHourlyBar('hourlyChart');
  }

  //Trips
  function buildTrips() {
    const top = DATA.topZones(10);
    const maxTrips = top[0]?.total_trips || 1;
    const colors = ['--c1','--c2','--c3','--c4','--c1','--c2','--c3','--c4','--c1','--c2'];

    return `
      <div class="page-header">
        <h1>Trip Patterns</h1>
        <p>Distance, duration, speed, and temporal distribution</p>
      </div>

      <div class="grid-2 mb-14">
        <div class="card">
          <div class="card-title">Trip distance distribution</div>
          <div class="chart-wrap" style="height:200px"><canvas id="distChart"></canvas></div>
        </div>
        <div class="card">
          <div class="card-title">Trip duration distribution</div>
          <div class="chart-wrap" style="height:200px"><canvas id="durChart"></canvas></div>
        </div>
      </div>

      <div class="card mb-14">
        <div class="card-title">Trip volume heatmap — day of week × hour</div>
        <div class="heatmap-wrap" id="heatmapWrap"></div>
        <div style="display:flex;align-items:center;gap:8px;margin-top:10px;font-size:11px;color:var(--text-tertiary)">
          Low <span id="heatLegend" style="display:flex;gap:3px"></span> High
        </div>
      </div>

      <div class="card">
        <div class="card-title">Top 10 pickup zones by trip volume</div>
        ${top.map((z,i) => `
          <div class="prog-row">
            <div class="prog-label" title="${z.zone_name}">${z.zone_name}</div>
            <div class="prog-bar-track">
              <div class="prog-bar-fill" style="width:${Math.round(z.total_trips/maxTrips*100)}%;background:var(${colors[i]})"></div>
            </div>
            <div class="prog-value">${z.total_trips.toLocaleString()}</div>
            <div style="width:90px;margin-left:8px"><span class="badge ${z.service_zone==='Yellow Zone'?'badge-blue':z.service_zone==='Airports'?'badge-amber':'badge-green'}">${z.service_zone}</span></div>
          </div>`).join('')}
      </div>`;
  }

  function initTrips() {
    CHARTS.renderDistBar('distChart');
    CHARTS.renderDurBar('durChart');
    buildHeatmap();
  }

  function buildHeatmap() {
    const data = DATA.heatmap();
    const hours = Array.from({length:24},(_,i)=>i);
    const allVals = data.flatMap(d=>d.hours);
    const mn = Math.min(...allVals), mx = Math.max(...allVals);
    const norm = v => (v - mn) / (mx - mn);

    function cellColor(v) {
      const n = norm(v);
      if (n < 0.25) return { bg:'rgba(61,142,240,0.15)', fg:'var(--text-tertiary)' };
      if (n < 0.5)  return { bg:'rgba(61,142,240,0.40)', fg:'var(--text-secondary)' };
      if (n < 0.75) return { bg:'rgba(61,142,240,0.70)', fg:'var(--text-primary)' };
      return { bg:'var(--c1)', fg:'#fff' };
    }

    const cols = 1 + 24;
    let html = `<div class="heatmap-grid" style="grid-template-columns:44px repeat(24,1fr)">`;
    // Hour headers
    html += `<div class="hm-header"></div>`;
    hours.forEach(h => html += `<div class="hm-header">${h}</div>`);
    // Rows
    data.forEach(row => {
      html += `<div class="hm-label">${row.day}</div>`;
      row.hours.forEach(v => {
        const c = cellColor(v);
        html += `<div class="hm-cell" style="background:${c.bg}">
          <div class="hm-tooltip">${row.day} ${row.hours.indexOf(v)}:00 · ${(v/1000).toFixed(1)}k trips</div>
        </div>`;
      });
    });
    html += '</div>';

    const wrap = document.getElementById('heatmapWrap');
    if (wrap) wrap.innerHTML = html;

    // Legend
    const leg = document.getElementById('heatLegend');
    if (leg) {
      ['rgba(61,142,240,0.15)','rgba(61,142,240,0.40)','rgba(61,142,240,0.70)','var(--c1)'].forEach(c => {
        const s = document.createElement('span');
        s.style.cssText = `width:22px;height:10px;background:${c};border-radius:2px;display:inline-block`;
        leg.appendChild(s);
      });
    }
  }

  // Fare
  function buildFares() {
    const k = DATA.kpis();
    const pay = DATA.paymentBreakdown();

    return `
      <div class="page-header">
        <h1>Fare Analysis</h1>
        <p>Revenue breakdown, tip patterns, and payment methods</p>
      </div>

      <div class="metric-grid">
        ${metricCard('Avg Base Fare',   '$'+k.avg_fare,           'before surcharges')}
        ${metricCard('Avg Total',       '$'+k.avg_total_amount,   'incl. tips & tolls')}
        ${metricCard('Avg Tip',         '$3.37',                  'credit card only')}
        ${metricCard('Avg Tip Rate',    k.avg_tip_pct+'%',        'of base fare')}
      </div>

      <div class="grid-2 mb-14">
        <div class="card">
          <div class="card-title">Payment method breakdown</div>
          <div style="display:flex;gap:20px;align-items:center">
            <div class="chart-wrap" style="height:200px;width:200px;flex-shrink:0"><canvas id="payChart"></canvas></div>
            <div style="flex:1">
              ${pay.map((r,i)=>`
                <div class="prog-row" style="margin-bottom:10px">
                  <div class="prog-label" style="width:110px">${r.label}</div>
                  <div class="prog-bar-track"><div class="prog-bar-fill" style="width:${r.pct}%;background:var(--c${i+1})"></div></div>
                  <div class="prog-value">${r.pct}%</div>
                </div>`).join('')}
            </div>
          </div>
        </div>
        <div class="card">
          <div class="card-title">Fare amount distribution</div>
          <div class="chart-wrap" style="height:200px"><canvas id="fareDistChart"></canvas></div>
        </div>
      </div>

      <div class="card mb-14">
        <div class="card-title">Average fare by hour of day</div>
        <div class="chart-wrap" style="height:160px"><canvas id="fareHourChart"></canvas></div>
      </div>

      <div class="card">
        <div class="card-title">Tip rate by payment method</div>
        ${pay.map((r,i)=>`
          <div class="prog-row">
            <div class="prog-label">${r.label}</div>
            <div class="prog-bar-track"><div class="prog-bar-fill" style="width:${r.avg_tip_pct/25*100}%;background:var(--c${i+1})"></div></div>
            <div class="prog-value">${r.avg_tip_pct}%</div>
          </div>`).join('')}
      </div>`;
  }

  function initFares() {
    CHARTS.renderPayDoughnut('payChart');
    CHARTS.renderFareDist('fareDistChart');
    CHARTS.renderFareHour('fareHourChart');
  }

  //Zone
  function buildZones() {
    return `
      <div class="page-header">
        <h1>Zone Explorer</h1>
        <p>Browse all NYC taxi zones with borough and service zone filters</p>
      </div>

      <div class="filter-bar">
        <span class="filter-label">Borough</span>
        <select class="filter-select" id="zoneBorough">
          <option value="">All boroughs</option>
          <option value="Manhattan">Manhattan</option>
          <option value="Queens">Queens</option>
          <option value="Brooklyn">Brooklyn</option>
          <option value="Bronx">Bronx</option>
          <option value="Staten Island">Staten Island</option>
          <option value="EWR">EWR</option>
        </select>
        <span class="filter-label">Service zone</span>
        <select class="filter-select" id="zoneService">
          <option value="">All types</option>
          <option value="Yellow Zone">Yellow Zone</option>
          <option value="Boro Zone">Boro Zone</option>
          <option value="Airports">Airports</option>
          <option value="EWR">EWR</option>
        </select>
        <input class="filter-input" id="zoneSearch" type="text" placeholder="Search zone name…" />
      </div>

      <div class="card" style="padding:0">
        <div style="overflow-x:auto">
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Zone Name</th>
                <th>Borough</th>
                <th>Service Zone</th>
                <th>Avg Trips / Day</th>
                <th>Avg Fare</th>
              </tr>
            </thead>
            <tbody id="zonesTbody"></tbody>
          </table>
        </div>
        <div class="pager">
          <span id="zonesCount"></span>
          <div class="pager-btns">
            <button class="pager-btn" id="zonesPrev">← Prev</button>
            <button class="pager-btn" id="zonesNext">Next →</button>
          </div>
        </div>
      </div>`;
  }

  function initZones() { ZONES_MODULE.init(); }

  //Schema
  function buildSchema() {
    return `
      <div class="page-header">
        <h1>Database Schema</h1>
        <p>Normalised relational design — PostgreSQL / SQLite compatible</p>
      </div>

      <div class="card mb-14">
        <div class="card-title">Entity Relationship Overview</div>
        <p style="font-size:13px;color:var(--text-secondary);margin-bottom:14px;line-height:1.65">
          Three tables form the core schema. <code style="font-family:'JetBrains Mono',monospace;background:var(--bg-overlay);padding:1px 5px;border-radius:4px">trips</code> is the fact table.
          <code style="font-family:'JetBrains Mono',monospace;background:var(--bg-overlay);padding:1px 5px;border-radius:4px">zones</code> is the location dimension (sourced from <em>taxi_zone_lookup.csv</em>).
          <code style="font-family:'JetBrains Mono',monospace;background:var(--bg-overlay);padding:1px 5px;border-radius:4px">rate_codes</code> maps integer codes to labels.
          Foreign keys enforce referential integrity. Seven derived columns are pre-computed on insert.
        </p>
        <div class="er-diagram">
          <div class="er-table">zones</div>
          <div class="er-arrow">←── pu_zone_id / do_zone_id ──→</div>
          <div class="er-table er-fact">trips (fact)</div>
          <div class="er-arrow">←── rate_code_id ──→</div>
          <div class="er-table">rate_codes</div>
        </div>
      </div>

      <div class="grid-3 mb-14">
        ${schemaBox('trips (fact)', [
          ['trip_id',             'BIGINT PK',    'Surrogate key'],
          ['pickup_datetime',     'TIMESTAMP',    'Pickup time'],
          ['dropoff_datetime',    'TIMESTAMP',    'Dropoff time'],
          ['pu_zone_id',          'INT FK',       '→ zones'],
          ['do_zone_id',          'INT FK',       '→ zones'],
          ['rate_code_id',        'INT FK',       '→ rate_codes'],
          ['passenger_count',     'SMALLINT',     '1–6'],
          ['trip_distance',       'DECIMAL(6,2)', 'Miles'],
          ['fare_amount',         'DECIMAL(8,2)', 'Base fare'],
          ['tip_amount',          'DECIMAL(8,2)', ''],
          ['tolls_amount',        'DECIMAL(8,2)', ''],
          ['total_amount',        'DECIMAL(8,2)', ''],
          ['payment_type',        'SMALLINT',     '1=CC 2=Cash…'],
          ['trip_duration_sec',   'INT',          '★ Derived'],
          ['speed_mph',           'DECIMAL(5,2)', '★ Derived'],
          ['tip_pct',             'DECIMAL(5,2)', '★ Derived'],
          ['is_rush_hour',        'SMALLINT',     '★ Derived 0/1'],
          ['time_of_day',         'VARCHAR(12)',   '★ Derived'],
          ['fare_per_mile',       'DECIMAL(6,2)', '★ Derived'],
          ['is_airport_trip',     'SMALLINT',     '★ Derived 0/1'],
        ])}
        ${schemaBox('zones (dimension)', [
          ['zone_id',     'INT PK',      'TLC location ID'],
          ['zone_name',   'VARCHAR(100)','e.g. Midtown East'],
          ['borough',     'VARCHAR(50)', 'Manhattan/Queens…'],
          ['service_zone','VARCHAR(50)', 'Yellow/Boro/Airport'],
          ['','',''],
          ['idx_borough', 'INDEX',       'borough'],
          ['idx_service', 'INDEX',       'service_zone'],
        ])}
        ${schemaBox('rate_codes', [
          ['rate_code_id','INT PK',     ''],
          ['description', 'VARCHAR(50)',''],
          ['','',''],
          ['1','','Standard rate'],
          ['2','','JFK'],
          ['3','','Newark'],
          ['4','','Nassau/Westchester'],
          ['5','','Negotiated fare'],
          ['6','','Group ride'],
          ['','',''],
          ['Key indexes (trips)','',''],
          ['idx_pickup_dt',  'INDEX','pickup_datetime'],
          ['idx_pu_zone',    'INDEX','pu_zone_id'],
          ['idx_do_zone',    'INDEX','do_zone_id'],
          ['idx_pickup_date','INDEX','pickup_date'],
        ])}
      </div>

      <div class="card">
        <div class="card-title">Feature Engineering — Derived Columns (SQL)</div>
        <pre class="code-block"><span class="code-cmt">-- Feature 1: Trip duration in seconds</span>
<span class="code-kw">trip_duration_sec</span> = EXTRACT(EPOCH FROM (dropoff_datetime - pickup_datetime))

<span class="code-cmt">-- Feature 2: Average speed (mph)</span>
<span class="code-kw">speed_mph</span> = (trip_distance / NULLIF(trip_duration_sec, <span class="code-num">0</span>)) * <span class="code-num">3600</span>

<span class="code-cmt">-- Feature 3: Tip as % of base fare</span>
<span class="code-kw">tip_pct</span> = (tip_amount / NULLIF(fare_amount, <span class="code-num">0</span>)) * <span class="code-num">100</span>

<span class="code-cmt">-- Feature 4: Rush-hour flag (weekday 7–9am or 5–7pm)</span>
<span class="code-kw">is_rush_hour</span> = CASE WHEN DOW BETWEEN <span class="code-num">1</span> AND <span class="code-num">5</span>
               AND (HOUR BETWEEN <span class="code-num">7</span> AND <span class="code-num">9</span> OR HOUR BETWEEN <span class="code-num">17</span> AND <span class="code-num">19</span>)
               THEN <span class="code-num">1</span> ELSE <span class="code-num">0</span> END

<span class="code-cmt">-- Feature 5: Time-of-day bucket</span>
<span class="code-kw">time_of_day</span> = CASE WHEN HOUR BETWEEN <span class="code-num">5</span> AND <span class="code-num">11</span>  THEN <span class="code-str">'Morning'</span>
                    WHEN HOUR BETWEEN <span class="code-num">12</span> AND <span class="code-num">16</span> THEN <span class="code-str">'Afternoon'</span>
                    WHEN HOUR BETWEEN <span class="code-num">17</span> AND <span class="code-num">20</span> THEN <span class="code-str">'Evening'</span>
                    ELSE <span class="code-str">'Night'</span> END

<span class="code-cmt">-- Feature 6: Fare per mile</span>
<span class="code-kw">fare_per_mile</span> = fare_amount / NULLIF(trip_distance, <span class="code-num">0</span>)

<span class="code-cmt">-- Feature 7: Airport trip flag (JFK=132, LGA=138, EWR=1)</span>
<span class="code-kw">is_airport_trip</span> = CASE WHEN pu_zone_id IN (<span class="code-num">1,132,138</span>)
                         OR do_zone_id IN (<span class="code-num">1,132,138</span>)
                         THEN <span class="code-num">1</span> ELSE <span class="code-num">0</span> END</pre>
      </div>`;
  }

  function schemaBox(title, rows) {
    const rowsHtml = rows.map(([col, type, note]) => {
      if (!col) return `<div style="height:8px"></div>`;
      return `<div class="schema-row">
        <span class="schema-col-name">${col}</span>
        <span class="schema-col-type">${type}</span>
        <span class="schema-col-note">${note}</span>
      </div>`;
    }).join('');
    return `<div class="schema-box"><div class="schema-box-header">${title}</div>${rowsHtml}</div>`;
  }

  // algo
  function buildAlgo() {
    return `
      <div class="page-header">
        <h1>Custom Algorithm</h1>
        <p>Manual max-heap implementation — no sort(), heapq, or Counter used</p>
      </div>

      <div class="card mb-14">
        <div class="card-title">Problem: Top-K Zones by Trip Volume</div>
        <p style="font-size:13px;color:var(--text-secondary);line-height:1.65;margin-bottom:16px">
          Finding the busiest pickup zones requires ranking all 263 zones by trip count.
          Instead of using built-in <code style="font-family:'JetBrains Mono',monospace;background:var(--bg-overlay);padding:1px 5px;border-radius:4px">sort()</code>,
          we implement a manual <strong style="font-weight:600;color:var(--text-primary)">max-heap</strong> (binary heap)
          to extract the top-k zones efficiently.
        </p>

        <div class="algo-step">
          <div class="algo-step-num">1</div>
          <div class="algo-step-text"><strong style="color:var(--text-primary)">Build frequency array</strong> — scan all zone trip counts into an array of <code style="font-family:'JetBrains Mono',monospace">[count, id, name, borough]</code> tuples. O(n)</div>
        </div>
        <div class="algo-step">
          <div class="algo-step-num">2</div>
          <div class="algo-step-text"><strong style="color:var(--text-primary)">Heapify</strong> — convert the array into a valid max-heap in-place by calling sift-down on all internal nodes, starting from the last. O(n)</div>
        </div>
        <div class="algo-step">
          <div class="algo-step-num">3</div>
          <div class="algo-step-text"><strong style="color:var(--text-primary)">Extract top-k</strong> — swap root (max) with last element, reduce heap size by 1, sift-down the new root. Repeat k times. O(k log n)</div>
        </div>

        <pre class="code-block"><span class="code-cmt">// Manual max-heap — no sort(), no heapq, no Counter</span>
<span class="code-kw">function</span> <span class="code-fn">siftDown</span>(heap, i, n) {
  <span class="code-kw">while</span> (<span class="code-kw">true</span>) {
    <span class="code-kw">let</span> largest = i;
    <span class="code-kw">const</span> l = <span class="code-num">2</span>*i+<span class="code-num">1</span>, r = <span class="code-num">2</span>*i+<span class="code-num">2</span>;
    <span class="code-kw">if</span> (l < n && heap[l][<span class="code-num">0</span>] > heap[largest][<span class="code-num">0</span>]) largest = l;
    <span class="code-kw">if</span> (r < n && heap[r][<span class="code-num">0</span>] > heap[largest][<span class="code-num">0</span>]) largest = r;
    <span class="code-kw">if</span> (largest === i) <span class="code-kw">break</span>;
    <span class="code-kw">const</span> tmp = heap[i]; heap[i] = heap[largest]; heap[largest] = tmp;
    i = largest;
  }
}

<span class="code-kw">function</span> <span class="code-fn">topKZones</span>(k) {
  <span class="code-kw">const</span> heap = zones.map(z => [z.trips, z.id, z.name, z.borough]);
  <span class="code-cmt">// Heapify — O(n)</span>
  <span class="code-kw">for</span> (<span class="code-kw">let</span> i = Math.floor(heap.length/<span class="code-num">2</span>)-<span class="code-num">1</span>; i >= <span class="code-num">0</span>; i--)
    <span class="code-fn">siftDown</span>(heap, i, heap.length);
  <span class="code-cmt">// Extract top-k — O(k log n)</span>
  <span class="code-kw">const</span> result = [];
  <span class="code-kw">let</span> size = heap.length;
  <span class="code-kw">for</span> (<span class="code-kw">let</span> i = <span class="code-num">0</span>; i < k && size > <span class="code-num">0</span>; i++) {
    result.push(heap[<span class="code-num">0</span>]);
    heap[<span class="code-num">0</span>] = heap[--size];
    <span class="code-fn">siftDown</span>(heap, <span class="code-num">0</span>, size);
  }
  <span class="code-kw">return</span> result;
}</pre>

        <div class="complexity-grid">
          <div class="complexity-card">
            <div class="label">Time complexity</div>
            <div class="value">O(n log n)</div>
            <div class="sub">heapify + extract</div>
          </div>
          <div class="complexity-card">
            <div class="label">Space complexity</div>
            <div class="value">O(n)</div>
            <div class="sub">heap array</div>
          </div>
          <div class="complexity-card">
            <div class="label">vs. Naive sort</div>
            <div class="value">Better</div>
            <div class="sub">for large n, small k</div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-title">Live Demo — Top-K Zones (heap running in browser)</div>
        <div style="display:flex;gap:14px;align-items:center;margin-bottom:16px;flex-wrap:wrap">
          <span style="font-size:13px;color:var(--text-secondary)">Show top</span>
          <input type="range" id="kSlider" min="3" max="15" value="8" step="1" style="width:120px;accent-color:var(--accent)">
          <span id="kVal" style="font-size:15px;font-weight:600;color:var(--text-primary);min-width:20px">8</span>
          <span style="font-size:13px;color:var(--text-secondary)">zones</span>
        </div>
        <div id="algoResult"></div>
      </div>`;
  }

  function initAlgo() { ALGO.init(); }

  // INSIGHTS
  function buildInsights() {
    return `
      <div class="page-header">
        <h1>Key Insights</h1>
        <p>Three data-driven findings from the NYC Yellow Taxi dataset</p>
      </div>

      <div class="insight-card">
        <h3>Insight 1 — Airports generate 2.4× higher fares with &lt;1% of zones</h3>
        <p>Manhattan accounts for 72% of all pickups, yet JFK and LaGuardia together generate 9% of all trips using just 2 of 263 zone IDs. Airport trips average $44.20 vs the city-wide mean of $18.40 — making them disproportionately valuable revenue sources. EWR trips average even higher at $52.10.</p>
      </div>
      <div class="card mb-14">
        <div class="card-title">Average fare by service zone type</div>
        <div class="chart-wrap" style="height:180px"><canvas id="insightChart1"></canvas></div>
      </div>

      <div class="insight-card">
        <h3>Insight 2 — Night-time trips earn more per minute despite lower volume</h3>
        <p>Trip volume drops 85% overnight (1am–5am), but average speed rises from 11 mph to 27 mph. The fare-per-minute metric increases from $1.28 during rush hour to $2.10 at 3am — meaning drivers who work overnight earn more per driving minute due to less traffic and longer, faster trips to airports and outer boroughs.</p>
      </div>
      <div class="card mb-14">
        <div class="card-title">Avg speed &amp; fare-per-minute by hour of day</div>
        <div class="chart-wrap" style="height:180px"><canvas id="insightChart2"></canvas></div>
      </div>

      <div class="insight-card">
        <h3>Insight 3 — All recorded tips come from credit card payments</h3>
        <p>100% of measurable tip revenue comes from credit card transactions (avg 23.4% tip rate). TLC records $0.00 for cash tips as they are unreported — creating a systematic undercounting of real driver income from cash fares. This suggests credit card adoption directly benefits driver earnings and has implications for fare structure policy.</p>
      </div>
      <div class="card">
        <div class="card-title">Average tip rate by payment method</div>
        <div class="chart-wrap" style="height:180px"><canvas id="insightChart3"></canvas></div>
      </div>`;
  }

  function initInsights() {
    CHARTS.renderInsight1('insightChart1');
    CHARTS.renderInsight2('insightChart2');
    CHARTS.renderInsight3('insightChart3');
  }

  // Helpers
  function metricCard(label, value, sub) {
    return `
      <div class="metric-card">
        <div class="metric-label">${label}</div>
        <div class="metric-value">${value}</div>
        <div class="metric-sub">${sub}</div>
      </div>`;
  }

  //  Boot
  document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initSidebar();
    showPage('overview');
  });

)();
