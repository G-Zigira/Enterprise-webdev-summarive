const API = 'http://127.0.0.1:5001';

const PERIOD_LABEL = { morning:'Morning', afternoon:'Afternoon', evening:'Evening', night:'Night' };

const BOROUGH_COLOR = {
    Manhattan:      '#5b9bd5',
    Brooklyn:       '#6baa88',
    Queens:         '#c4a85a',
    Bronx:          '#c47870',
    'Staten Island':'#9580c8',
    EWR:            '#8b9cb0'
};

const gridColor = '#21262d';
const tickColor = '#6e7681';

let fareChart, fareDistChart;
let _whenData = [];

/* ── Navigation ── */
function show(name, btn) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.tab-nav button').forEach(b => b.classList.remove('active'));
    document.getElementById('section-' + name).classList.add('active');
    btn.classList.add('active');
    fareChart.resize();
    fareDistChart.resize();
}

/* ── API helper ── */
async function get(path) {
    const res = await fetch(API + path);
    if (!res.ok) throw new Error(res.status);
    return res.json();
}

function hourPeriod(h) {
    if (h >= 6  && h < 12) return 'morning';
    if (h >= 12 && h < 18) return 'afternoon';
    if (h >= 18 && h < 24) return 'evening';
    return 'night';
}

/* ── WHEN ── */
async function loadWhen() {
    try {
        const kpis = await get('/api/kpis');
        document.getElementById('s-total-trips').textContent = Number(kpis.total_trips).toLocaleString();
        document.getElementById('s-avg-fare').textContent    = '$' + kpis.avg_fare;
        document.getElementById('s-avg-tip').textContent     = kpis.avg_tip_pct + '%';
    } catch(e) {
        console.warn('KPIs:', e.message);
    }

    try {
        const hourly = await get('/api/hourly-volume');
        const peak   = hourly.reduce((a, b) => a.total_trips > b.total_trips ? a : b);
        const quiet  = hourly.reduce((a, b) => a.total_trips < b.total_trips ? a : b);
        document.getElementById('s-peak-hour').textContent  = String(peak.hour).padStart(2,'0')  + ':00';
        document.getElementById('s-quiet-hour').textContent = String(quiet.hour).padStart(2,'0') + ':00';
        _whenData = hourly;
        renderWhenTable(_whenData);
    } catch(e) {
        console.warn('Hourly volume:', e.message);
    }

    try {
        const fareByHour = await get('/api/fare-by-hour');
        fareChart.data.labels = fareByHour.map(h => h.hour + ':00');
        fareChart.data.datasets[0].data = fareByHour.map(h => h.avg_fare);
        fareChart.update();
    } catch(e) {
        console.warn('Fare by hour:', e.message);
    }
}

function renderWhenTable(data) {
    document.getElementById('tbody-when').innerHTML = data.map(h => `
        <tr>
            <td class="mono muted">${String(h.hour).padStart(2,'0')}:00</td>
            <td>${Number(h.avg_trips_per_day).toLocaleString()}</td>
            <td class="fare">$${h.avg_fare}</td>
            <td class="muted">${h.avg_speed_mph} mph</td>
            <td class="muted">${PERIOD_LABEL[hourPeriod(h.hour)]}</td>
        </tr>`).join('');
}

function filterWhen() {
    const p = document.getElementById('f-time').value;
    const data = p === 'all' ? _whenData : _whenData.filter(h => hourPeriod(h.hour) === p);
    renderWhenTable(data.length ? data : _whenData);
}

/* ── WHERE ── */
async function loadWhere() {
    try {
        const kpis = await get('/api/kpis');
        document.getElementById('s-avg-dist').textContent     = kpis.avg_distance_mi + ' mi';
        document.getElementById('s-active-zones').textContent = Number(kpis.active_zones).toLocaleString();
    } catch(e) {
        console.warn('KPIs (where):', e.message);
    }

    try {
        const boroughs = await get('/api/borough-summary');
        document.getElementById('s-top-borough').textContent = boroughs[0]?.borough || '—';
        renderLangBar(boroughs);
        renderBoroughTable(boroughs);
    } catch(e) {
        console.warn('Borough summary:', e.message);
    }

    loadZonesTable('');
}

function renderLangBar(boroughs) {
    document.getElementById('lang-bar').innerHTML = boroughs.map(b =>
        `<div class="lang-seg" style="width:${b.pct}%;background:${BOROUGH_COLOR[b.borough] || '#8b949e'}"></div>`
    ).join('');
    document.getElementById('lang-legend').innerHTML = boroughs.map(b =>
        `<div class="lang-item"><div class="lang-dot" style="background:${BOROUGH_COLOR[b.borough] || '#8b949e'}"></div>${b.borough} ${b.pct}%</div>`
    ).join('');
}

function renderBoroughTable(boroughs) {
    const max = Math.max(...boroughs.map(b => b.trips));
    document.getElementById('tbody-borough').innerHTML = boroughs.map(b => `
        <div class="b-row">
            <div class="b-name">${b.borough}</div>
            <div><div class="b-bar-wrap"><div class="b-bar" style="width:${(b.trips / max * 100).toFixed(1)}%"></div></div></div>
            <div class="b-val">$${b.avg_fare}</div>
            <div class="b-val">${b.pct}%</div>
        </div>`).join('');
}

async function loadZonesTable(borough) {
    try {
        const qs  = borough ? `?borough=${encodeURIComponent(borough)}&per_page=15` : '?per_page=15';
        const res = await get('/api/zones' + qs);
        document.getElementById('tbody-where').innerHTML = (res.data || []).map(z => `
            <tr>
                <td><b>${z.zone_name}</b></td>
                <td class="muted">${z.borough}</td>
                <td>${Number(z.total_trips || 0).toLocaleString()}</td>
                <td class="fare">$${z.avg_fare ?? '—'}</td>
            </tr>`).join('');
    } catch(e) {
        console.warn('Zones:', e.message);
    }
}

function filterWhere() {
    const b = document.getElementById('f-borough').value;
    loadZonesTable(b === 'all' ? '' : b);
}

/* ── HOW MUCH ── */
async function loadHowMuch() {
    try {
        const payments = await get('/api/payment-breakdown');
        const max      = Math.max(...payments.map(p => p.trips));
        const card     = payments.find(p => p.label === 'Credit card');
        document.getElementById('s-card-pct').textContent = (card ? card.pct : '—') + '%';

        document.getElementById('payment-bars').innerHTML = payments.map(p => `
            <div class="pay-row">
                <div class="pay-name">${p.label}</div>
                <div class="pay-bar-bg"><div class="pay-bar-fill" style="width:${(p.trips / max * 100).toFixed(1)}%"></div></div>
                <div class="pay-num">${Number(p.trips).toLocaleString()}</div>
            </div>`).join('');

        document.getElementById('tbody-howmuch').innerHTML = payments.map(p => `
            <tr>
                <td><b>${p.label}</b></td>
                <td>${Number(p.trips).toLocaleString()}</td>
                <td class="muted">${p.pct}%</td>
                <td class="fare">$${p.avg_fare}</td>
                <td class="muted">${p.avg_tip_pct}%</td>
            </tr>`).join('');
    } catch(e) {
        console.warn('Payment breakdown:', e.message);
    }

    try {
        const fareDist = await get('/api/fare-distribution');
        fareDistChart.data.labels = fareDist.map(f => f.bucket);
        fareDistChart.data.datasets[0].data = fareDist.map(f => f.trips);
        fareDistChart.data.datasets[0].backgroundColor = fareDist.map((_, i) =>
            ['#6baa88','#5b9bd5','#c4a85a','#9580c8','#c47870','#8b9cb0','#d4b870'][i % 7]
        );
        fareDistChart.update();
    } catch(e) {
        console.warn('Fare distribution:', e.message);
    }
}

/* ── Charts (start empty — all data comes from API) ── */
fareChart = new Chart(document.getElementById('c-fare'), {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            data: [],
            borderColor: '#3fb950',
            backgroundColor: 'rgba(63,185,80,0.08)',
            fill: true,
            tension: 0.4,
            pointRadius: 2,
            pointBackgroundColor: '#3fb950',
        }]
    },
    options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
            x: { ticks: { color: tickColor, maxTicksLimit: 12 }, grid: { color: gridColor } },
            y: { ticks: { color: tickColor, callback: v => '$' + v }, grid: { color: gridColor } }
        }
    }
});

fareDistChart = new Chart(document.getElementById('c-faredist'), {
    type: 'bar',
    data: {
        labels: [],
        datasets: [{ data: [], backgroundColor: [], borderRadius: 4 }]
    },
    options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
            x: { ticks: { color: tickColor }, grid: { color: gridColor } },
            y: { ticks: { color: tickColor, callback: v => (v / 1000) + 'k' }, grid: { color: gridColor } }
        }
    }
});

/* ── Init ── */
loadWhen();
loadWhere();
loadHowMuch();
