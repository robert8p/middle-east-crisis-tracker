async function loadDashboard() {
  const response = await fetch('/api/dashboard');
  const data = await response.json();
  window.__dashboard = data;
  populateFilters(data.clusters);
  render(data);
}

function populateFilters(clusters) {
  const select = document.getElementById('filterEventType');
  const values = [...new Set(clusters.map(c => c.event_type))].sort();
  const existing = new Set([...select.options].map(o => o.value));
  for (const value of values) {
    if (!existing.has(value)) {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = value;
      select.appendChild(option);
    }
  }
}

function render(data) {
  document.getElementById('generatedAt').textContent = `Updated ${new Date(data.generated_at_utc).toLocaleString()}`;
  document.getElementById('clusterCount').textContent = `${data.stats.cluster_count} clusters`;
  document.getElementById('degradedCount').textContent = `${data.stats.degraded_sources} degraded sources`;
  document.getElementById('criticalCount').textContent = data.stats.critical_clusters;
  document.getElementById('shippingCount').textContent = data.stats.shipping_exposed_clusters;
  document.getElementById('situationLabel').textContent = data.situation.label;
  document.getElementById('situationRationale').textContent = data.situation.rationale;
  document.getElementById('situationConfidence').textContent = data.situation.confidence;

  renderWatchlist('scheduledWatch', 'Scheduled watch items', data.situation.watchlist_scheduled);
  renderWatchlist('inferredWatch', 'Inferred risk windows', data.situation.watchlist_inferred);
  renderTransmission(data.situation.market_transmission);
  renderSources(data.sources);
  renderClusters(filterClusters(data.clusters));
}

function filterClusters(clusters) {
  const eventType = document.getElementById('filterEventType').value;
  const confidence = document.getElementById('filterConfidence').value;
  const materiality = document.getElementById('filterMateriality').value;
  const exposure = document.getElementById('filterExposure').value;
  return clusters.filter(c => {
    if (eventType && c.event_type !== eventType) return false;
    if (confidence && c.confidence_band !== confidence) return false;
    if (materiality && c.materiality_band !== materiality) return false;
    if (exposure && !c.asset_exposure_tags.includes(exposure)) return false;
    return true;
  });
}

function humanizeEventType(value) {
  return (value || '').replace(/_/g, ' ').replace(/\w/g, ch => ch.toUpperCase());
}

function sourceCountLabel(count) {
  return `${count} source${count === 1 ? '' : 's'}`;
}

function badgeClass(type, value) {
  if (type === 'confidence') {
    if (value === 'High confidence') return 'conf-high';
    if (value === 'Moderate confidence') return 'conf-mid';
    if (value === 'Low confidence') return 'conf-low';
    return 'conf-unverified';
  }
  if (type === 'materiality') {
    if (value === 'Critical') return 'mat-critical';
    if (value === 'High') return 'mat-high';
    if (value === 'Medium') return 'mat-medium';
    return 'mat-low';
  }
  return '';
}

function renderClusters(clusters) {
  const list = document.getElementById('clusterList');
  list.innerHTML = '';
  const template = document.getElementById('clusterTemplate');

  for (const cluster of clusters) {
    const node = template.content.cloneNode(true);
    node.querySelector('.event-type').textContent = humanizeEventType(cluster.event_type);
    const conf = node.querySelector('.confidence');
    conf.textContent = cluster.confidence_band;
    conf.classList.add(badgeClass('confidence', cluster.confidence_band));
    const mat = node.querySelector('.materiality');
    mat.textContent = cluster.materiality_band;
    mat.classList.add(badgeClass('materiality', cluster.materiality_band));
    node.querySelector('.cluster-title').textContent = cluster.canonical_title;
    node.querySelector('.cluster-summary').textContent = cluster.summary;
    node.querySelector('.why').textContent = cluster.why_it_matters;
    node.querySelector('.market').textContent = cluster.market_impact;
    node.querySelector('.uncertainty').textContent = cluster.uncertainty_notes;
    node.querySelector('.cluster-meta').textContent =
      `${sourceCountLabel(cluster.corroboration_count + 1)} • ${cluster.countries_involved.join(', ') || 'Region not explicit'} • ${cluster.actors_involved.join(', ') || 'Actors not explicit'}`;

    const tags = node.querySelector('.tags');
    [...cluster.locations, ...cluster.asset_exposure_tags].slice(0, 8).forEach(t => {
      const el = document.createElement('span');
      el.className = 'tag';
      el.textContent = t;
      tags.appendChild(el);
    });

    const evidence = node.querySelector('.evidence');
    const evidenceList = document.createElement('div');
    evidenceList.className = 'source-list';
    cluster.supporting_sources.forEach(s => {
      const item = document.createElement('div');
      item.className = 'source-item';
      const published = s.published_at_utc ? new Date(s.published_at_utc).toLocaleString() : 'Time unavailable';
      const strong = document.createElement('strong');
      strong.textContent = s.source;
      const title = document.createElement('div');
      title.textContent = s.title;
      const time = document.createElement('div');
      time.textContent = published;
      const linkWrap = document.createElement('div');
      const link = document.createElement('a');
      link.href = s.url;
      link.target = '_blank';
      link.rel = 'noreferrer';
      link.textContent = 'Open source';
      linkWrap.appendChild(link);
      item.appendChild(strong);
      item.appendChild(title);
      item.appendChild(time);
      item.appendChild(linkWrap);
      evidenceList.appendChild(item);
    });
    evidence.appendChild(evidenceList);
    const button = node.querySelector('.toggle-btn');
    button.addEventListener('click', () => evidence.classList.toggle('hidden'));

    list.appendChild(node);
  }
}

function renderWatchlist(containerId, title, items) {
  const container = document.getElementById(containerId);
  container.innerHTML = `<p class="mini-label">${title}</p>`;
  const list = document.createElement('div');
  list.className = 'watch-list';
  for (const item of items) {
    const el = document.createElement('div');
    el.className = 'watch-item';
    el.innerHTML = `<strong>${item.title}</strong><div>${item.why}</div>`;
    list.appendChild(el);
  }
  if (!items.length) {
    const empty = document.createElement('div');
    empty.className = 'watch-item';
    empty.textContent = 'No current items.';
    list.appendChild(empty);
  }
  container.appendChild(list);
}

function renderTransmission(items) {
  const container = document.getElementById('marketTransmission');
  const list = document.createElement('div');
  list.className = 'transmission-list';
  list.innerHTML = '';
  for (const item of items) {
    const el = document.createElement('div');
    el.className = 'transmission-item';
    el.innerHTML = `<strong>${item.channel}</strong><div>${item.note}</div>`;
    list.appendChild(el);
  }
  if (!items.length) {
    const empty = document.createElement('div');
    empty.className = 'transmission-item';
    empty.textContent = 'No elevated market transmission channels detected yet.';
    list.appendChild(empty);
  }
  container.innerHTML = '';
  container.appendChild(list);
}

function renderSources(sources) {
  const container = document.getElementById('sourceHealth');
  const list = document.createElement('div');
  list.className = 'source-list';
  for (const s of sources) {
    const el = document.createElement('div');
    el.className = 'source-item';
    const status = s.degraded ? 'Degraded' : 'OK';
    el.innerHTML = `<strong>${s.source_name}</strong><div>${status} • ${s.source_type}</div><div>${s.items_ingested_last_run} items • ${s.last_response_time_ms} ms</div>`;
    list.appendChild(el);
  }
  container.innerHTML = '';
  container.appendChild(list);
}

['filterEventType', 'filterConfidence', 'filterMateriality', 'filterExposure'].forEach(id => {
  document.addEventListener('change', (event) => {
    if (event.target && event.target.id === id && window.__dashboard) {
      renderClusters(filterClusters(window.__dashboard.clusters));
    }
  });
});

loadDashboard();
setInterval(loadDashboard, 60000);