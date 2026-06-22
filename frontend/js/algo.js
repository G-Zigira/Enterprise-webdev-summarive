
const ALGO = (() => {

  // Manual max-heap (array-backed)
  // Each element: [count, zone_id, zone_name, borough]

  function siftDown(heap, i, n) {
    while (true) {
      let largest = i;
      const l = 2 * i + 1;
      const r = 2 * i + 2;
      if (l < n && heap[l][0] > heap[largest][0]) largest = l;
      if (r < n && heap[r][0] > heap[largest][0]) largest = r;
      if (largest === i) break;
      // Manual swap — no destructuring to keep it explicit
      const tmp = heap[i];
      heap[i] = heap[largest];
      heap[largest] = tmp;
      i = largest;
    }
  }

  function heapify(arr) {
    // Build max-heap in O(n) — start from last internal node
    for (let i = Math.floor(arr.length / 2) - 1; i >= 0; i--) {
      siftDown(arr, i, arr.length);
    }
  }

  function extractMax(heap, size) {
    const max = heap[0];
    heap[0] = heap[size - 1];
    siftDown(heap, 0, size - 1);
    return max;
  }

  /**
   * topKZones(k)
   * Returns the top-k zones by simulated trip count using a manual max-heap.
   * Time:  O(n log n) to heapify + O(k log n) to extract
   * Space: O(n) for the heap array
   */
  function topKZones(k) {
    // Step 1: Build frequency array from DATA (simulates scanning trip records)
    const zones = DATA.topZones(999); // get all zones
    const heap  = zones.map(z => [z.total_trips, z.zone_id, z.zone_name, z.borough]);

    // Step 2: Heapify — O(n)
    heapify(heap);

    // Step 3: Extract top-k — O(k log n)
    const result = [];
    let size = heap.length;
    for (let i = 0; i < k && size > 0; i++) {
      result.push(extractMax(heap, size));
      size--;
    }
    return result;
  }

  // Render live demo 
  const BOROUGH_COLORS = {
    'Manhattan':    'var(--c1)',
    'Queens':       'var(--c2)',
    'Brooklyn':     'var(--c3)',
    'Bronx':        'var(--c4)',
    'Staten Island':'var(--c5)',
    'EWR':          'var(--c6)',
  };

  function render() {
    const slider = document.getElementById('kSlider');
    const kLabel = document.getElementById('kVal');
    const container = document.getElementById('algoResult');
    if (!slider || !container) return;

    const k = parseInt(slider.value);
    if (kLabel) kLabel.textContent = k;

    const results = topKZones(k);
    const max = results[0]?.[0] || 1;

    container.innerHTML = results.map((r, idx) => {
      const [count, , name, borough] = r;
      const pct = Math.round(count / max * 100);
      const color = BOROUGH_COLORS[borough] || 'var(--c1)';
      return `
        <div class="prog-row" style="margin-bottom:11px">
          <div style="width:26px;font-size:12px;color:var(--text-tertiary);font-weight:500;flex-shrink:0">#${idx+1}</div>
          <div class="prog-label">${name}</div>
          <div class="prog-bar-track" style="flex:1">
            <div class="prog-bar-fill" style="width:${pct}%;background:${color}"></div>
          </div>
          <div class="prog-value">${count.toLocaleString()}</div>
          <div style="width:80px;margin-left:8px;flex-shrink:0">
            <span class="badge badge-blue" style="font-size:10px">${borough}</span>
          </div>
        </div>`;
    }).join('');
  }

  function init() {
    const slider = document.getElementById('kSlider');
    if (slider) slider.addEventListener('input', render);
    render();
  }

  return { init, render, topKZones };
})();
