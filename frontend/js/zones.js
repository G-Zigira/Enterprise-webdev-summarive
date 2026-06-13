/**
 * zones.js — Zone Explorer page logic
 * Filterable, sortable, paginated zone table.
 */

const ZONES_MODULE = (() => {

  let currentPage = 1;
  let perPage     = 15;
  let sortKey     = 'total_trips';
  let sortDir     = 'desc';
  let filters     = { borough: '', service: '', search: '' };

  const SERVICE_BADGE = {
    'Yellow Zone': 'badge-blue',
    'Boro Zone':   'badge-green',
    'Airports':    'badge-amber',
    'EWR':         'badge-red',
  };

  function getFilters() {
    filters.borough = document.getElementById('zoneBorough')?.value || '';
    filters.service = document.getElementById('zoneService')?.value  || '';
    filters.search  = document.getElementById('zoneSearch')?.value   || '';
  }

  function render() {
    getFilters();
    const result = DATA.zones({ ...filters, page: currentPage, per_page: perPage });
    renderTable(result.data);
    renderPager(result.total);
  }

  function renderTable(rows) {
    const tbody = document.getElementById('zonesTbody');
    if (!tbody) return;

    if (rows.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:24px;color:var(--text-tertiary)">No zones match your filters.</td></tr>`;
      return;
    }

    tbody.innerHTML = rows.map(z => {
      const badgeClass = SERVICE_BADGE[z.service_zone] || 'badge-green';
      const trips = (z.total_trips || 0).toLocaleString();
      const fare  = z.avg_fare ? '$' + z.avg_fare.toFixed(2) : '—';
      return `
        <tr>
          <td style="color:var(--text-tertiary);font-family:'JetBrains Mono',monospace;font-size:12px">${z.zone_id}</td>
          <td style="font-weight:500">${z.zone_name}</td>
          <td>${z.borough}</td>
          <td><span class="badge ${badgeClass}">${z.service_zone}</span></td>
          <td style="font-variant-numeric:tabular-nums">${trips}</td>
          <td style="font-variant-numeric:tabular-nums">${fare}</td>
        </tr>`;
    }).join('');
  }

  function renderPager(total) {
    const totalPages = Math.ceil(total / perPage);
    const start = (currentPage - 1) * perPage + 1;
    const end   = Math.min(currentPage * perPage, total);

    const countEl = document.getElementById('zonesCount');
    if (countEl) countEl.textContent = `Showing ${start}–${end} of ${total} zones`;

    const prevBtn = document.getElementById('zonesPrev');
    const nextBtn = document.getElementById('zonesNext');
    if (prevBtn) prevBtn.disabled = currentPage <= 1;
    if (nextBtn) nextBtn.disabled = currentPage >= totalPages;
  }

  function init() {
    // Filter controls
    ['zoneBorough','zoneService'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.addEventListener('change', () => { currentPage = 1; render(); });
    });

    const searchEl = document.getElementById('zoneSearch');
    if (searchEl) {
      let debounce;
      searchEl.addEventListener('input', () => {
        clearTimeout(debounce);
        debounce = setTimeout(() => { currentPage = 1; render(); }, 220);
      });
    }

    // Pager buttons
    const prevBtn = document.getElementById('zonesPrev');
    const nextBtn = document.getElementById('zonesNext');
    if (prevBtn) prevBtn.addEventListener('click', () => { currentPage--; render(); });
    if (nextBtn) nextBtn.addEventListener('click', () => { currentPage++; render(); });

    render();
  }

  return { init, render };
})();
