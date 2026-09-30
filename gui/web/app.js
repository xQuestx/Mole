'use strict';

(() => {
  const paths = {
    overview: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    sparkles: '<path d="m12 3 2.6 6.4L21 12l-6.4 2.6L12 21l-2.6-6.4L3 12l6.4-2.6L12 3Z"/><path d="m20 2 .7 1.8L22.5 4.5l-1.8.7L20 7l-.7-1.8-1.8-.7 1.8-.7L20 2Z"/>',
    apps: '<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><path d="M14 17.5h7m-3.5-3.5v7"/>',
    pie: '<path d="M10 3a9 9 0 1 0 11 11H10V3Z"/><path d="M14 2v8h8a9 9 0 0 0-8-8Z"/>',
    sliders: '<path d="M4 6h6m4 0h6M4 12h10m4 0h2M4 18h2m4 0h10"/><circle cx="12" cy="6" r="2"/><circle cx="16" cy="12" r="2"/><circle cx="8" cy="18" r="2"/>',
    code: '<path d="m8 6-6 6 6 6m8-12 6 6-6 6m-3-15-2 18"/>',
    package: '<path d="m12 3 9 5-9 5-9-5 9-5Zm9 5v9l-9 5-9-5V8m9 5v9M7.5 5.5l9 5v4"/>',
    activity: '<path d="M2 12h4l3-8 6 16 3-8h4"/>',
    history: '<path d="M3 11a9 9 0 1 1 2 7M3 4v7h7m2-4v5l3 2"/>',
    fingerprint: '<path d="M5 8a8 8 0 0 1 14 0M3 13v-2m18 2v-2M7 15v-4a5 5 0 0 1 10 0v2M5 13v3l-1 3m15-4v2l-1 4M9 21l2-4v-6a1 1 0 0 1 2 0v7l-1 4m3-7v3l-1 4M7 18l-1 3"/>',
    terminal: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="m7 8 4 4-4 4m7 0h3"/>',
    refresh: '<path d="M20 7a8 8 0 0 0-14-2L3 8m0-5v5h5M4 17a8 8 0 0 0 14 2l3-3m0 5v-5h-5"/>',
    trash: '<path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7m4-7v7"/>',
    help: '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 0 1 5 0c0 2-2.5 2-2.5 4m0 3h.01"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10h.01"/>',
    shield: '<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6l8-3Z"/><path d="m8 12 3 3 5-6"/>',
    laptop: '<rect x="5" y="3" width="14" height="13" rx="1.5"/><path d="m5 16-3 4h20l-3-4M10 18h4"/>',
    drive: '<rect x="3" y="4" width="18" height="16" rx="3"/><path d="M3 14h18m-4 3h.01m-4 0h.01"/>',
    arrow: '<path d="M5 12h14m-5-5 5 5-5 5"/>',
    external: '<path d="M8 4H4v16h16v-4M13 3h8v8m0-8L10 14"/>',
    chevron: '<path d="m9 5 7 7-7 7"/>',
    down: '<path d="m6 9 6 6 6-6"/>',
    up: '<path d="m6 15 6-6 6 6"/>',
    folder: '<path d="M3 6h6l2 2h10v11H3V6Z"/>',
    file: '<path d="M5 3h9l5 5v13H5V3Zm9 0v5h5M8 12h8m-8 4h6"/>',
    image: '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8" cy="8" r="1.5"/><path d="m3 17 6-6 4 4 3-3 5 5"/>',
    music: '<path d="M9 18V5l11-2v13M9 5l11-2"/><ellipse cx="6" cy="18" rx="3" ry="2"/><ellipse cx="17" cy="16" rx="3" ry="2"/>',
    film: '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M7 3v18M17 3v18M3 8h4m-4 8h4M17 8h4m-4 8h4"/>',
    archive: '<rect x="3" y="3" width="18" height="5" rx="1"/><path d="M5 8v13h14V8M9 12h6"/>',
    search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
    lock: '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3m-4 5v2"/>',
    home: '<path d="m3 10 9-7 9 7v11h-7v-7h-4v7H3V10Z"/>',
    copy: '<rect x="8" y="8" width="13" height="13" rx="2"/><path d="M16 8V3H3v13h5"/>',
    check: '<path d="m5 12 4 4L19 6"/>',
    close: '<path d="m6 6 12 12M6 18 18 6"/>',
    menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
    warning: '<path d="m12 3 10 18H2L12 3Zm0 6v5m0 3h.01"/>',
    link: '<path d="m9 15 6-6m-7 8-2 2a4 4 0 0 1-6-6l5-5a4 4 0 0 1 6 0m2-1 2-2a4 4 0 0 1 6 6l-5 5a4 4 0 0 1-6 0"/>',
  };
  const icon = name => `<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.file}</svg>`;
  const escape = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[char]));
  const $ = selector => document.querySelector(selector);
  const main = $('#main');
  const dialog = $('#action-dialog');
  const app = { state: null, view: 'overview', generation: 0, configs: new Map(), command: null, commandGeneration: 0, commandTimer: null,
    browser: { path: '', parent: null, entries: [], partial: false, loading: false, error: '', search: '', sort: 'size', order: -1, generation: 0, selected: new Set(), type: 'all', minSize: '', olderDays: '', filterDrafts: { minSize: '', olderDays: '' }, filterErrors: {}, offset: 0, nextOffset: null, totalVisible: null, totalFiltered: null, sampledAt: null, filterTimer: null, retryAfterJob: null },
    reports: new Map(), reportFilters: { apps: { query: '', sort: 'name' }, history: { query: '', command: '', outcome: '', since: '' } },
    measurements: new Map(), previews: new Map(), recentMoves: [], job: null, jobContext: null, activityView: null, jobTimer: null, jobGeneration: 0, jobPollSequence: 0, jobStarting: false, dialogBusy: false, dialogOperation: null, dialogGeneration: 0, pendingFocus: null };
  let token = '';
  let postQueue = Promise.resolve();
  let browseQueue = Promise.resolve();
  const fragmentToken = new URLSearchParams(location.hash.slice(1)).get('token');
  if (fragmentToken) {
    token = fragmentToken;
    try { sessionStorage.setItem('mole-session-token', token); }
    catch (_) { /* The current session retains its token in memory. */ }
    finally { history.replaceState(null, '', location.pathname + location.search); }
  } else {
    try { token = sessionStorage.getItem('mole-session-token') || ''; }
    catch (_) { /* Reopen the launcher URL if browser storage is unavailable. */ }
  }

  async function request(url, data, timeout = 100000) {
    if (!token) throw new Error('Reopen the full local URL printed by the Mole launcher to connect this browser.');
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeout);
    try {
      const response = await fetch(url, { method: data === undefined ? 'GET' : 'POST', cache: 'no-store', credentials: 'omit',
        headers: { 'X-Mole-Token': token, ...(data === undefined ? {} : { 'Content-Type': 'application/json' }) },
        ...(data === undefined ? {} : { body: JSON.stringify(data) }), signal: controller.signal });
      const body = await response.json();
      if (!response.ok) { const error = new Error(body.error || `Mole could not complete this request (${response.status}).`); error.status = response.status; throw error; }
      return body;
    } catch (error) {
      if (error.name === 'AbortError') throw new Error('The request timed out. Refresh to check the current state before trying again.');
      if (error instanceof TypeError) throw new Error('The local Mole server is unavailable. Restart the launcher, then reopen its full URL.');
      throw error;
    } finally { clearTimeout(timer); }
  }
  function api(url, data, timeout) {
    if (data === undefined) return request(url, data, timeout);
    const result = postQueue.then(() => request(url, data, timeout));
    postQueue = result.catch(() => {});
    return result;
  }
  function bytes(value, digits = 1) {
    if (!Number.isFinite(value) || value < 0) return 'Unknown';
    if (value < 1000) return `${value} B`;
    const units = ['KB', 'MB', 'GB', 'TB', 'PB'];
    let size = value / 1000, unit = 0;
    while (size >= 1000 && unit < units.length - 1) { size /= 1000; unit++; }
    return `${size.toLocaleString(undefined, { maximumFractionDigits: digits })} ${units[unit]}`;
  }
  function date(value) {
    const d = new Date(typeof value === 'number' ? value * 1000 : value);
    return Number.isNaN(d.getTime()) ? 'Unknown' : d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
  }
  function readableTime(value) {
    const d = new Date(value * 1000);
    return Number.isNaN(d.getTime()) ? 'Unknown' : d.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' });
  }
  function toast(message, error = false) {
    const node = document.createElement('div');
    node.className = `toast${error ? ' error' : ''}`;
    node.innerHTML = `${icon(error ? 'warning' : 'check')}<span>${escape(message)}</span><button aria-label="Dismiss notification">${icon('close')}</button>`;
    node.querySelector('button').addEventListener('click', () => node.remove());
    $('#toast-stack').append(node);
    if (!error) setTimeout(() => node.remove(), 6500);
    while ($('#toast-stack').children.length > 3) $('#toast-stack').firstElementChild.remove();
  }
  function connection(connected) {
    $('#connection-dot').className = `connection-dot ${connected ? 'connected' : 'offline'}`;
    $('#connection-label').textContent = connected ? 'Connected locally' : 'Connection unavailable';
  }
  function setMachine() {
    $('#machine-name').textContent = app.state.host || 'Your Mac';
    $('#machine-os').textContent = app.state.os || app.state.system || 'System unavailable';
    $('#version').textContent = `v${app.state.version}`;
    connection(true);
  }
  function navigation() {
    const groups = new Map();
    for (const item of app.state.catalog) {
      if (!groups.has(item.group)) groups.set(item.group, []);
      groups.get(item.group).push(item);
    }
    $('#navigation').innerHTML = `<button class="nav-item active" data-view="overview" aria-current="page">${icon('overview')}<span>Overview</span></button><button class="nav-item" data-view="recovery">${icon('trash')}<span>Trash & recovery</span></button>` +
      [...groups].map(([name, items]) => `<div class="nav-group"><p class="nav-group-label">${escape(name)}</p>${items.map(item => `<button class="nav-item" data-view="${escape(item.id)}">${icon(item.icon)}<span>${escape(item.name)}</span></button>`).join('')}</div>`).join('');
  }
  function storage() {
    const disk = app.state.disk;
    const percent = Number.isFinite(disk.used) && disk.total > 0 ? Math.min(100, Math.max(0, disk.used / disk.total * 100)) : null;
    const low = percent !== null && (disk.free / disk.total < .1);
    const space = bytes(disk.free).split(' ');
    const usedText = percent === null ? 'Unknown' : `${percent.toFixed(0)}%`;
    const offset = percent === null ? 0 : 464.956 * (1 - percent / 100);
    return `<div class="storage-panel"><div class="storage-main"><div class="storage-topline"><span class="storage-label">${icon('drive')}Your home volume</span><span class="live-tag">Live disk snapshot</span></div>
      <div class="space-number">${escape(space[0])} <small>${escape(space.slice(1).join(' '))}</small></div><p class="space-caption">available for what comes next</p>
      <div class="disk-track" role="meter" aria-label="Storage used" aria-valuemin="0" aria-valuemax="100" ${percent === null ? '' : `aria-valuenow="${percent.toFixed(1)}"`} aria-valuetext="${escape(bytes(disk.used))} used of ${escape(bytes(disk.total))}"><div class="disk-used" style="width:${percent || 0}%"></div></div>
      <div class="disk-legend"><span><i class="legend-dot"></i><b>${escape(bytes(disk.used))}</b> used</span><span><i class="legend-dot free"></i><b>${escape(bytes(disk.total))}</b> total</span></div></div>
      <div class="storage-visual"><div class="disk-orbit"><svg viewBox="0 0 172 172" aria-hidden="true"><circle class="orbit-track" cx="86" cy="86" r="74" fill="none" stroke-width="9"/><circle class="orbit-used" cx="86" cy="86" r="74" fill="none" stroke-width="9" stroke-linecap="round" stroke-dasharray="464.956" stroke-dashoffset="${offset}"/></svg><div class="orbit-center"><strong>${usedText}</strong><span>space in use</span></div></div></div></div>
      <div class="storage-footnote${low ? ' low-space' : ''}"><span>${icon(low ? 'warning' : 'info')}${low ? 'Your disk is running low. Start with a cleanup preview.' : 'Measured from the volume containing your home folder.'}</span><span>Updated ${escape(readableTime(app.state.sampled_at))}</span></div>`;
  }
  function overview() {
    main.innerHTML = `<div class="view-enter"><section class="hero"><div><span class="eyebrow"><i class="eyebrow-dot"></i>A small ritual for your Mac</span><h1>A little care.<br><em>A lighter Mac.</em></h1><p>More room for your work. Less of what’s in the way.</p></div><div class="hero-stamp"><span class="stamp-ring">${icon('shield')}</span><span>Thoughtful care.<br>Always your call.</span></div></section>
      <section id="storage-zone" aria-label="Disk storage">${storage()}</section>
      <div class="section-heading"><div><h2>Where would you like to start?</h2><p>A few good ways to give your Mac some breathing room.</p></div></div>
      <section class="quick-grid" aria-label="Quick tasks">${[
        ['clean', 'sparkles', 'A fresh start', 'Review caches, logs, and leftovers.', 'Preview before you clean'],
        ['uninstall', 'apps', 'A little less clutter', 'Remove apps you’ve outgrown.', 'Review apps in Terminal'],
        ['purge', 'code', 'Room to build', 'Clear rebuildable project artifacts.', 'Keep the work you made'],
      ].map(([id, symbol, name, desc, note]) => `<button class="quick-card" data-view="${id}"><div class="quick-card-top"><span class="quick-icon">${icon(symbol)}</span><span class="quick-arrow">${icon('external')}</span></div><h3>${name}</h3><p>${desc}</p><div class="quick-card-bottom">${icon('shield')}${note}</div></button>`).join('')}</section>
      <div class="section-heading"><div><h2>A closer look at your files</h2><p>Browse what’s here. Choose what’s ready to go.</p></div><button class="text-button" data-view="analyze">Explore files ${icon('arrow')}</button></div>
      ${browserShell(true)}<p class="quiet-note">${icon('shield')}Personal items move to Trash after review. Mole checks protection rules before each move.</p>${recoveryShell(true)}</div>`;
    renderBrowser(); renderRecovery();
    if (!app.browser.path && !app.browser.loading) loadBrowse(defaultPath());
  }
  function defaultPath() { return app.state.locations.find(path => path === `${app.state.home}/Downloads`) || app.state.home; }
  function labelForPath(path) { return path === app.state.home ? 'Home' : path.split('/').filter(Boolean).at(-1); }
  function browserShell(compact = false) {
    const order = ['Downloads', 'Desktop', 'Documents', 'Pictures', 'Movies', 'Music', 'Home'];
    const locations = [...app.state.locations].sort((a, b) => order.indexOf(labelForPath(a)) - order.indexOf(labelForPath(b)));
    const browser = app.browser;
    return `<section class="browser-panel" aria-label="Home folder browser" data-compact="${compact}"><div class="browser-toolbar"><div class="location-tabs" aria-label="Personal folders">${locations.map(path => `<button class="location-tab" data-browse-path="${escape(path)}">${escape(labelForPath(path))}</button>`).join('')}</div><div class="browser-tools"><label class="search-box">${icon('search')}<input id="file-search" type="search" placeholder="Find a file…" aria-label="Filter files in this folder" value="${escape(browser.search)}"></label><button class="icon-button" id="refresh-folder" title="Refresh folder" aria-label="Refresh folder">${icon('refresh')}</button></div></div>
      ${compact ? '' : `<div class="browser-filter-bar"><label class="browser-filter"><span>Type</span><select id="file-type-filter" aria-label="Filter by file type">${[['all', 'All items'], ['file', 'Files'], ['folder', 'Folders'], ['image', 'Images'], ['video', 'Videos'], ['audio', 'Audio'], ['archive', 'Archives'], ['installer', 'Installers'], ['document', 'Documents']].map(([value, label]) => `<option value="${value}" ${browser.type === value ? 'selected' : ''}>${label}</option>`).join('')}</select></label><label class="browser-filter"><span>Min file size</span><div class="filter-unit"><input id="file-size-filter" type="number" min="0" max="1000000000" step="any" value="${escape(browser.filterDrafts.minSize)}" placeholder="Any" aria-label="Minimum file size in MB" aria-describedby="file-filter-error"><span>MB</span></div></label><label class="browser-filter"><span>Older than</span><div class="filter-unit"><input id="file-age-filter" type="number" min="0" max="36500" step="1" value="${escape(browser.filterDrafts.olderDays)}" placeholder="Any" aria-label="Modified more than this many days ago" aria-describedby="file-filter-error"><span>days</span></div></label><button class="text-button" id="clear-file-filters">Clear filters</button></div><p id="file-filter-error" class="report-error" role="alert" hidden></p>`}
      <div class="breadcrumbs" id="breadcrumbs"></div><div id="browser-content"></div><div id="selection-bar"></div><div class="browser-footer"><span class="browser-summary" id="browser-summary"></span>${compact ? `<button class="text-button" data-view="analyze">View all files ${icon('arrow')}</button>` : '<div class="pagination" id="file-pagination"></div>'}</div></section>${compact ? '' : '<p class="keyboard-help"><span><kbd>Cmd/Ctrl F</kbd> Find files</span><span><kbd>Alt ↑</kbd> Parent folder</span><span>Hidden items are excluded.</span></p>'}`;
  }
  function selectedEntries() { return app.browser.entries.filter(entry => app.browser.selected.has(entry.id)); }
  const previewExtensions = new Set(['png', 'jpg', 'jpeg', 'gif', 'webp', 'heic', 'heif', 'tif', 'tiff', 'bmp', 'pdf']);
  function previewSupported(entry) { return !entry.directory && !entry.symlink && previewExtensions.has(entry.name.split('.').at(-1).toLowerCase()); }
  function measuredEntry(path) {
    return app.measurements.get(app.browser.path)?.entries?.find(entry => entry.path === path);
  }
  function sizeCell(entry) {
    if (entry.symlink) return '<span class="file-sub-label">Link</span>';
    if (!entry.directory) return escape(bytes(entry.size));
    const measured = measuredEntry(entry.path);
    if (!measured) return '<span class="file-sub-label">Not measured</span>';
    if (completeSize(measured)) return `<span title="Measured snapshot, ${escape(readableTime(app.measurements.get(app.browser.path).sampled_at))}">${escape(bytes(measured.size))}</span>`;
    return measured.scan_status === 'partial' && Number.isFinite(measured.size) && measured.size > 0 ? `<span title="Incomplete measurement; this is a lower bound">${escape(bytes(measured.size))}+</span>` : '<span class="file-sub-label">Unavailable</span>';
  }
  function fileIcon(entry) {
    if (entry.directory) return 'folder';
    if (entry.symlink) return 'link';
    const ext = entry.name.split('.').at(-1).toLowerCase();
    if (['png', 'jpg', 'jpeg', 'gif', 'heic', 'webp', 'svg', 'avif'].includes(ext)) return 'image';
    if (['mp3', 'wav', 'aif', 'm4a', 'flac'].includes(ext)) return 'music';
    if (['mov', 'mp4', 'mkv', 'avi'].includes(ext)) return 'film';
    if (['zip', 'tar', 'gz', 'dmg', 'pkg', 'iso', 'xip'].includes(ext)) return 'archive';
    return 'file';
  }
  function renderBrowser() {
    const container = $('#browser-content');
    if (!container) return;
    const browser = app.browser;
    const compact = $('.browser-panel').dataset.compact === 'true';
    document.querySelectorAll('.location-tab').forEach(button => { const active = browser.path === button.dataset.browsePath || browser.path.startsWith(button.dataset.browsePath + '/'); button.classList.toggle('active', active && button.dataset.browsePath !== app.state.home || browser.path === app.state.home && button.dataset.browsePath === app.state.home); });
    const pieces = browser.path ? browser.path.slice(app.state.home.length).split('/').filter(Boolean) : [];
    const crumbs = [{ label: 'Home', path: app.state.home }];
    for (let i = 0; i < pieces.length; i++) crumbs.push({ label: pieces[i], path: app.state.home + '/' + pieces.slice(0, i + 1).join('/') });
    $('#breadcrumbs').innerHTML = icon('folder') + crumbs.map((crumb, i) => `${i ? '<span>/</span>' : ''}<button data-browse-path="${escape(crumb.path)}" ${i === crumbs.length - 1 ? 'aria-current="location"' : ''}>${escape(crumb.label)}</button>`).join('') + `<button class="icon-button up-button" data-parent-folder ${browser.parent ? '' : 'disabled'} aria-label="Go to parent folder" title="Go to parent folder">${icon('up')}</button>`;
    $('#refresh-folder').disabled = browser.loading || app.dialogBusy;
    if ($('#file-type-filter')) $('#file-type-filter').value = browser.type;
    if ($('#file-size-filter')) { $('#file-size-filter').disabled = browser.type === 'folder'; if (document.activeElement !== $('#file-size-filter')) $('#file-size-filter').value = browser.filterDrafts.minSize; }
    if ($('#file-age-filter') && document.activeElement !== $('#file-age-filter')) $('#file-age-filter').value = browser.filterDrafts.olderDays;
    renderFilterErrors();
    if ($('#file-pagination')) $('#file-pagination').innerHTML = `<button class="button secondary small" data-page-offset="${Math.max(0, browser.offset - 200)}" ${browser.loading || browser.offset === 0 ? 'disabled' : ''}>Previous</button><button class="button secondary small" data-page-offset="${browser.nextOffset ?? 0}" ${browser.loading || browser.nextOffset === null ? 'disabled' : ''}>Next</button>`;
    if (browser.loading) { container.innerHTML = '<div class="table-empty"><span class="loading-orbit small" aria-hidden="true"></span><p>Reading this folder…</p></div>'; $('#browser-summary').textContent = 'Reading filtered files'; $('#selection-bar').innerHTML = ''; return; }
    if (browser.error) { container.innerHTML = `<div class="table-empty">${icon('warning')}<p>${escape(browser.error)}</p><p>Try another personal folder or use the Terminal disk explorer.</p></div>`; $('#browser-summary').textContent = 'Folder unavailable'; $('#selection-bar').innerHTML = ''; return; }
    const rows = compact ? browser.entries.slice(0, 6) : browser.entries;
    const arrow = key => browser.sort === key ? icon(browser.order === 1 ? 'up' : 'down') : '';
    if (!rows.length) container.innerHTML = `<div class="table-empty">${icon('folder')}<p>${browser.search || browser.type !== 'all' || browser.minSize || browser.olderDays ? 'No visible items match these filters.' : 'No visible items in this folder.'}</p><p>Choose another folder or clear the filters.</p></div>`;
    else container.innerHTML = `<div class="file-table-wrap${compact ? ' compact' : ''}"><table class="file-table"><thead><tr><th class="select-cell"><span class="sr-only">Select</span></th><th aria-sort="${browser.sort === 'name' ? browser.order === 1 ? 'ascending' : 'descending' : 'none'}"><button data-sort="name">Name ${arrow('name')}</button></th><th class="file-size-cell" aria-sort="${browser.sort === 'size' ? browser.order === 1 ? 'ascending' : 'descending' : 'none'}"><button data-sort="size" title="Sort by listed file size; folder totals require measurement">File size ${arrow('size')}</button></th><th class="file-date-cell" aria-sort="${browser.sort === 'modified' ? browser.order === 1 ? 'ascending' : 'descending' : 'none'}"><button data-sort="modified">Modified ${arrow('modified')}</button></th><th class="file-actions-cell"><span class="sr-only">File actions</span></th></tr></thead><tbody>${rows.map(entry => {
      const selected = browser.selected.has(entry.id);
      const disabled = !entry.eligible || (browser.selected.size >= 5 && !selected) || app.dialogBusy || jobRunning();
      const why = !entry.eligible ? 'Browse only. This item cannot be selected for GUI Trash review.' : disabled ? 'Review up to five items when no other task is running.' : 'Select for Trash review';
      return `<tr${selected ? ' class="selected"' : ''}><td class="select-cell"><label class="file-selection-label" title="${why}"><input class="file-checkbox" type="checkbox" data-select-id="${escape(entry.id)}" aria-label="Select ${escape(entry.name)} for review" ${selected ? 'checked' : ''} ${disabled ? 'disabled' : ''}></label></td><td><button class="file-name" ${entry.directory ? 'data-browse-path="' + escape(entry.path) + '"' : 'data-file-detail="' + escape(entry.id) + '"'} title="${entry.directory ? 'Open' : 'Details for'} ${escape(entry.path)}"><span class="file-type-icon${entry.directory ? ' folder' : ''}">${icon(fileIcon(entry))}</span><span class="file-title">${escape(entry.name)}</span>${!entry.eligible ? `<span class="file-lock" title="Browse only">${icon('lock')}</span>` : ''}</button></td><td class="file-size-cell">${sizeCell(entry)}</td><td class="file-date-cell">${escape(date(entry.modified))}</td><td class="file-actions-cell"><div class="file-row-actions"><button class="icon-button" data-native-action="reveal" data-entry-id="${escape(entry.id)}" aria-label="Reveal ${escape(entry.name)} in Finder" title="Reveal in Finder" ${entry.symlink ? 'disabled' : ''}>${icon('folder')}</button><button class="icon-button" data-native-action="preview" data-entry-id="${escape(entry.id)}" aria-label="Preview ${escape(entry.name)}" title="${previewSupported(entry) ? 'Open in Preview' : 'Preview supports images and PDF files'}" ${previewSupported(entry) ? '' : 'disabled'}>${icon('image')}</button></div></td></tr>`;
    }).join('')}</tbody></table></div>`;
    if (browser.partial) container.insertAdjacentHTML('beforeend', '<div class="partial-note">This listing is incomplete. Loaded rows are a partial sample; full counts and later pages are unavailable. Narrow the folder or use Terminal for a complete scan.</div>');
    const end = browser.offset + rows.length;
    const range = rows.length ? `${browser.offset + 1}–${end}` : '0';
    const count = browser.partial || browser.totalFiltered === null ? `${rows.length} loaded visible rows · incomplete` : `${range} of ${browser.totalFiltered} matching visible items`;
    $('#browser-summary').innerHTML = `${icon('info')}<span>${escape(count)}${browser.totalVisible !== null && !browser.partial ? ` · ${browser.totalVisible} total visible` : ''}${app.measurements.has(browser.path) ? ' · folder sizes are a snapshot' : ''}</span>`;
    renderSelection();
  }
  function renderBrowserPreservingFocus() {
    const focused = document.activeElement;
    const inBrowser = focused?.closest('.browser-panel');
    const attributes = ['data-select-id', 'data-file-detail', 'data-entry-id', 'data-native-action', 'data-sort', 'data-browse-path'];
    const selector = inBrowser ? focused.id ? '#' + CSS.escape(focused.id) : attributes.filter(key => focused.hasAttribute(key)).map(key => `[${key}="${CSS.escape(focused.getAttribute(key))}"]`).join('') : '';
    renderBrowser();
    if (selector && document.activeElement !== focused) document.querySelector(selector)?.focus({ preventScroll: true });
  }
  function renderSelection() {
    const container = $('#selection-bar');
    if (!container) return;
    const selected = selectedEntries();
    if (!selected.length) { container.innerHTML = ''; return; }
    const knownBytes = selected.reduce((sum, entry) => sum + (entry.size ?? 0), 0);
    const unknown = selected.some(entry => entry.size === null);
    const details = unknown ? 'Folder sizes have not been measured.' : `${bytes(knownBytes)} in selected files · up to 5 items`;
    container.innerHTML = `<div class="selection-bar"><div class="selection-copy"><strong>${selected.length} ${selected.length === 1 ? 'item' : 'items'} selected for review</strong><span>${details}</span></div><div class="selection-actions"><button class="text-button" id="clear-selection" ${app.dialogBusy || jobRunning() ? 'disabled' : ''}>Clear</button><button class="button small" id="review-trash" ${app.dialogBusy || jobRunning() ? 'disabled' : ''}>${icon('trash')}Review Trash</button></div></div>`;
  }
  async function loadBrowse(path, options = {}) {
    const browser = app.browser;
    clearTimeout(browser.filterTimer);
    const generation = ++browser.generation;
    const preserveFilters = options.preserveFilters && path === browser.path;
    if (!preserveFilters) { browser.search = ''; browser.type = 'all'; browser.minSize = ''; browser.olderDays = ''; browser.filterDrafts = { minSize: '', olderDays: '' }; browser.filterErrors = {}; }
    browser.path = path; browser.offset = options.offset || 0; browser.loading = true; browser.error = ''; browser.retryAfterJob = null; browser.selected.clear();
    if ($('#file-search')) $('#file-search').value = browser.search;
    renderBrowser(); renderMeasurement();
    const query = new URLSearchParams({ path, offset: String(browser.offset), q: browser.search, type: browser.type, sort: browser.sort, order: browser.order === 1 ? 'asc' : 'desc' });
    if (browser.minSize) query.set('min_size', String(Math.floor(Number(browser.minSize) * 1000000)));
    if (browser.olderDays) query.set('older_days', String(Number(browser.olderDays)));
    try {
      const pending = browseQueue.then(() => generation === browser.generation ? api('/api/browse?' + query) : null);
      browseQueue = pending.catch(() => null);
      const result = await pending;
      if (!result || generation !== browser.generation) return;
      browser.path = result.path; browser.parent = result.parent; browser.entries = result.entries; browser.partial = !!result.partial;
      browser.offset = result.offset ?? browser.offset; browser.nextOffset = result.next_offset ?? null;
      browser.totalVisible = Number.isFinite(result.total_visible) ? result.total_visible : null;
      browser.totalFiltered = Number.isFinite(result.total_filtered) ? result.total_filtered : null;
      browser.sampledAt = result.sampled_at;
    } catch (error) { if (generation === browser.generation) { browser.entries = []; browser.error = error.message; if (error.status === 409) browser.retryAfterJob = { path, offset: browser.offset }; browser.nextOffset = null; browser.parent = path !== app.state.home ? path.slice(0, path.lastIndexOf('/')) : null; } }
    finally { if (generation === browser.generation) { browser.loading = false; renderBrowser(); renderMeasurement(); if (options.focus && $('#file-search')) $('#file-search').focus({ preventScroll: true }); } }
  }
  function normalizeFileFilter(key, value) {
    const text = String(value).trim();
    if (!text) return '';
    const number = Number(text);
    const maximum = key === 'olderDays' ? 36500 : 1000000000;
    if (!Number.isFinite(number) || number < 0 || number > maximum || key === 'olderDays' && !Number.isInteger(number)) {
      throw new Error(key === 'olderDays' ? 'Older than must be a whole number from 0 to 36,500 days.' : 'Minimum file size must be a number from 0 to 1,000,000,000 MB.');
    }
    return String(number);
  }
  function renderFilterErrors() {
    const node = $('#file-filter-error');
    if (!node) return;
    const errors = Object.values(app.browser.filterErrors).filter(Boolean);
    node.hidden = !errors.length;
    const message = errors.length ? errors.join(' ') + ' Invalid values are not applied; the last valid filters remain in use.' : '';
    if (node.textContent !== message) node.textContent = message;
    for (const [key, id] of [['minSize', 'file-size-filter'], ['olderDays', 'file-age-filter']]) {
      document.getElementById(id)?.setAttribute('aria-invalid', String(!!app.browser.filterErrors[key]));
    }
  }
  function updateFileFilterDraft(key, input) {
    const browser = app.browser;
    browser.filterDrafts[key] = input.value;
    try {
      if (input.validity.badInput) throw new Error(key === 'olderDays' ? 'Enter a whole number of days.' : 'Enter a nonnegative file size in MB.');
      const value = normalizeFileFilter(key, input.value);
      browser.filterErrors[key] = '';
      if (browser[key] !== value) { browser[key] = value; filterBrowse(true); }
    } catch (error) { browser.filterErrors[key] = error.message; }
    renderFilterErrors();
  }
  function filterBrowse(delayed = false) {
    const browser = app.browser;
    clearTimeout(browser.filterTimer); ++browser.generation;
    browser.selected.clear(); browser.loading = true; renderBrowser();
    browser.filterTimer = setTimeout(() => loadBrowse(browser.path, { preserveFilters: true }), delayed ? 300 : 0);
  }
  function fileDetails(id) {
    const entry = app.browser.entries.find(row => row.id === id);
    if (!entry) return;
    openDialog(fileIcon(entry), `<h2 id="dialog-title">${escape(entry.name)}</h2><p id="dialog-description">Metadata from the folder listing.</p><ul class="dialog-paths"><li>${escape(entry.path)}</li><li>${entry.directory ? 'Folder' : entry.symlink ? 'Symbolic link' : 'File'} · ${entry.directory ? 'Recursive size requires measurement' : escape(bytes(entry.size))}</li><li>Modified ${escape(date(entry.modified))}</li><li>${entry.eligible ? 'Eligible for Mole’s Trash review' : 'Browse only · GUI Trash review unavailable'}</li></ul>`, [{ label: 'Close', style: 'secondary', action: closeDialog }, { label: 'Reveal in Finder', action: () => nativeAction('reveal', id), disabled: entry.symlink }, { label: 'Open in Preview', action: () => nativeAction('preview', id), disabled: !previewSupported(entry) }]);
  }
  function configFor(item) {
    if (!app.configs.has(item.id)) app.configs.set(item.id, { flags: new Set(item.flags.filter(flag => flag[3]).map(flag => flag[0])), fields: Object.fromEntries((item.fields || []).map(field => [field.key, field.type === 'select' ? field.values[0][0] : ''])) });
    return app.configs.get(item.id);
  }
  function payloadFor(item) {
    const config = configFor(item);
    return { command: item.id, flags: [...config.flags], fields: Object.fromEntries(Object.entries(config.fields).filter(([key, value]) => value.trim() && (key !== 'interval' || config.flags.has('watch')))) };
  }
  function flagRow(flag, config) {
    const [key, name, note] = flag;
    const danger = key === 'permanent' || key === 'yes';
    return `<label class="option-row${danger ? ' destructive' : ''}"><span class="option-copy"><strong>${escape(name)}</strong><small>${escape(note)}</small></span><code class="option-code">--${escape(key)}</code><span class="switch"><input type="checkbox" data-flag="${escape(key)}" ${config.flags.has(key) ? 'checked' : ''}><span class="switch-track"></span></span></label>`;
  }
  function fieldControl(field, config) {
    const value = config.fields[field.key] || '';
    const id = 'field-' + field.key;
    let control;
    if (field.type === 'select') control = `<select id="${escape(id)}" data-field="${escape(field.key)}">${field.values.map(([key, label]) => `<option value="${escape(key)}" ${value === key ? 'selected' : ''}>${escape(label)}</option>`).join('')}</select>`;
    else if (field.type === 'apps') control = `<textarea id="${escape(id)}" data-field="${escape(field.key)}" maxlength="4096" spellcheck="false" placeholder="${escape(field.placeholder)}">${escape(value)}</textarea>`;
    else control = `<input id="${escape(id)}" data-field="${escape(field.key)}" type="${field.type === 'number' ? 'number' : 'text'}" ${field.type === 'number' ? `min="${field.min}" max="${field.max}" step="${field.key === 'limit' ? 1 : 'any'}"` : 'maxlength="4096"'} value="${escape(value)}" placeholder="${escape(field.placeholder || '')}" spellcheck="false" ${field.key === 'interval' && !config.flags.has('watch') ? 'disabled' : ''}>`;
    return `<div class="field"><label for="${escape(id)}">${escape(field.label)}</label>${control}${field.hint ? `<small>${escape(field.hint)}</small>` : ''}</div>`;
  }
  function commandView(item) {
    const config = configFor(item);
    const flags = [...item.flags];
    if (!flags.some(flag => flag[0] === 'debug')) flags.push(['debug', 'Detailed logs', 'Include Mole’s diagnostic information.']);
    if (!['update', 'remove', 'help', 'version'].includes(item.id)) flags.push(['help', 'Command help', 'Print usage for this command without running the task.']);
    main.innerHTML = `<div class="view-enter"><header class="command-header"><span class="command-header-icon">${icon(item.icon)}${escape(item.group)}</span><h1>${escape(item.name)}<span style="color:var(--moss)">.</span></h1><p>${escape(item.description)}</p></header>
      ${['status', 'history', 'uninstall'].includes(item.id) ? reportShell(item.id === 'uninstall' ? 'apps' : item.id) : ''}
      ${['clean', 'uninstall'].includes(item.id) ? previewShell(item.id) : ''}
      ${item.id === 'analyze' ? `${measurementShell()}${browserShell()}<p class="quiet-note">${icon('info')}Use Measure folder for recursive sizes. Measurements are snapshots within Mole’s scan rules.</p><div class="section-heading"><div><h2>Take it further in Terminal</h2><p>Explore complete directory sizes and other volumes with Mole.</p></div></div>` : ''}
      <div class="command-layout"><form class="options-panel" id="command-form"><div class="options-heading"><h2>Make it your own</h2><span>mo ${escape(item.id)}</span></div>${flags.map(flag => flagRow(flag, config)).join('')}${(item.fields || []).length ? `<div class="fields">${item.fields.map(field => fieldControl(field, config)).join('')}</div>` : ''}</form>
      <aside class="command-side" aria-label="Command preview"><div class="command-card"><div class="command-card-header">${icon('terminal')}Your command</div><div class="command-mode" id="command-mode"></div><pre class="command-preview" id="command-preview">Preparing command…</pre><div class="command-controls"><button class="button" id="launch-command" disabled>${icon('terminal')}Open in Terminal</button><button class="button secondary" id="copy-command" disabled>${icon('copy')}Copy command</button><p class="command-explanation">Review the command here.<br>Mole handles the next steps in Terminal.</p></div></div><div class="command-note">${icon('shield')}<p>${escape(item.note)}</p><div id="command-warning"></div></div></aside></div></div>`;
    $('#command-form').addEventListener('submit', event => event.preventDefault());
    renderCommandWarning(item);
    if (['clean', 'uninstall'].includes(item.id)) renderPreview(item.id);
    if (item.id === 'analyze') { renderMeasurement(); renderBrowser(); if (!app.browser.path && !app.browser.loading) loadBrowse(defaultPath()); }
    if (['status', 'history', 'uninstall'].includes(item.id)) renderReport(item.id === 'uninstall' ? 'apps' : item.id);
    generateCommand(item);
  }
  function renderCommandWarning(item) {
    const config = configFor(item);
    const help = config.flags.has('help') || item.id === 'help' || item.id === 'version';
    const manager = config.flags.has('whitelist') || config.flags.has('paths');
    const preview = config.flags.has('dry-run') && !manager && !help;
    const changes = !preview && !help && !['analyze', 'status', 'history'].includes(item.id) && !(item.id === 'uninstall' && config.flags.has('list')) && !(item.id === 'touchid' && config.fields.action === 'status') && !(item.id === 'completion' && config.fields.shell);
    const interactiveExplorer = item.id === 'analyze' && !config.flags.has('json');
    const mode = help ? 'Help & information' : manager ? 'Opens an editable manager' : preview ? 'Preview only · no cleanup changes' : interactiveExplorer ? 'Interactive disk explorer' : changes ? 'Runs with changes enabled' : 'Read-only command';
    $('#command-mode').textContent = mode;
    $('#command-mode').className = `command-mode${changes ? ' changes-enabled' : ''}`;
    const danger = !help && !manager && !preview && (config.flags.has('permanent') || ['clean', 'purge', 'installer'].includes(item.id));
    const unattended = !help && !manager && config.flags.has('yes') && !preview;
    $('#command-warning').innerHTML = danger || unattended ? `<div class="warning-note">${icon('warning')}${danger ? 'This command may permanently remove selected items. Review the complete plan in Terminal.' : 'Unattended cleanup skips interactive selection. Review eligible targets with Preview only first.'}</div>` : '';
  }
  function generateCommand(item, delayed = false) {
    clearTimeout(app.commandTimer);
    const generation = ++app.commandGeneration;
    app.command = null;
    if ($('#launch-command')) { $('#launch-command').disabled = true; $('#copy-command').disabled = true; }
    const run = async () => {
      if (generation !== app.commandGeneration || app.view !== item.id) return;
      const preview = $('#command-preview');
      preview.textContent = 'Preparing command…'; preview.classList.remove('command-error');
      try {
        const result = await api('/api/command', payloadFor(item));
        if (generation !== app.commandGeneration || app.view !== item.id) return;
        app.command = result.command;
        $('#command-preview').textContent = result.command;
        $('#launch-command').disabled = app.dialogBusy || jobRunning();
        $('#copy-command').disabled = false;
      } catch (error) {
        if (generation !== app.commandGeneration || app.view !== item.id) return;
        $('#command-preview').textContent = error.message;
        $('#command-preview').classList.add('command-error');
      }
    };
    app.commandTimer = setTimeout(run, delayed ? 180 : 0);
  }
  function navigate(id) {
    if (!app.state || !['overview', 'recovery'].includes(id) && !app.state.catalog.some(item => item.id === id)) return;
    app.view = id; app.generation++; app.commandGeneration++; clearTimeout(app.commandTimer);
    setNavOpen(false);
    document.querySelectorAll('.nav-item').forEach(button => { const active = button.dataset.view === id; button.classList.toggle('active', active); if (active) button.setAttribute('aria-current', 'page'); else button.removeAttribute('aria-current'); });
    const item = app.state.catalog.find(item => item.id === id);
    $('#view-label').textContent = item?.name || (id === 'recovery' ? 'Trash & recovery' : 'Overview');
    document.title = `${item?.name || (id === 'recovery' ? 'Trash & recovery' : 'Overview')} · Mole`;
    if (id === 'overview') overview(); else if (id === 'recovery') recoveryView(); else commandView(item);
    renderJob();
    window.scrollTo({ top: 0 });
    main.focus({ preventScroll: true });
  }
  function reportShell(kind) {
    const name = { status: 'Your Mac, right now', history: 'Recorded activity', apps: 'Your installed apps' }[kind];
    const note = { status: 'A one-time snapshot from Mole. Refresh when you need it.', history: 'Actual outcomes from Mole’s operation log. Filters apply to loaded records.', apps: 'Search installed apps, then choose exact uninstall names.' }[kind];
    const filter = app.reportFilters[kind];
    const filters = kind === 'apps' ? `<div class="report-filter-bar"><label class="search-box">${icon('search')}<input id="app-search" type="search" value="${escape(filter.query)}" placeholder="Find an app…" aria-label="Search app names and bundle identifiers"></label><label class="browser-filter"><span>Sort</span><select id="app-sort" aria-label="Sort app inventory">${[['name', 'Name'], ['size-desc', 'Reported size · largest first'], ['size-asc', 'Reported size · smallest first']].map(([value, label]) => `<option value="${value}" ${filter.sort === value ? 'selected' : ''}>${label}</option>`).join('')}</select></label></div>` : kind === 'history' ? `<div class="report-filter-bar"><label class="search-box">${icon('search')}<input id="history-search" type="search" value="${escape(filter.query)}" placeholder="Find recorded activity…" aria-label="Search loaded activity"></label><label class="browser-filter"><span>Command</span><select id="history-command" aria-label="Filter activity by command"><option value="">All commands</option></select></label><label class="browser-filter"><span>Outcome</span><select id="history-outcome" aria-label="Filter activity by outcome">${[['', 'All outcomes'], ['trashed', 'Trashed'], ['removed', 'Removed'], ['skipped', 'Skipped'], ['failed', 'Failed'], ['rebuilt', 'Rebuilt']].map(([value, label]) => `<option value="${value}" ${filter.outcome === value ? 'selected' : ''}>${label}</option>`).join('')}</select></label><label class="browser-filter"><span>Since</span><input type="date" id="history-since" value="${escape(filter.since)}" aria-label="Show activity since date"></label></div>` : '';
    return `<section class="report-panel" aria-label="${name}"><div class="report-heading"><div><h2>${name}</h2><p>${note}</p></div><button class="button secondary small" data-report="${kind}">${icon('refresh')}${kind === 'status' ? 'Refresh health' : kind === 'history' ? 'Load history' : 'List apps'}</button></div>${filters}<div id="report-content" aria-live="polite"></div></section>`;
  }
  function reportedSize(value) {
    if (typeof value !== 'string') return null;
    const match = value.trim().match(/^([\d.,]+)\s*(B|K|KB|KiB|M|MB|MiB|G|GB|GiB|T|TB|TiB)$/i);
    if (!match) return null;
    const number = Number(match[1].replaceAll(',', ''));
    const unit = match[2].toLowerCase();
    const power = unit === 'b' ? 0 : { k: 1, m: 2, g: 3, t: 4 }[unit[0]];
    return Number.isFinite(number) && power !== undefined ? number * (unit.includes('i') ? 1024 : 1000) ** power : null;
  }
  // Forensic statuses come from mole_delete; session totals come from history.sh.
  // An unfamiliar status stays visible verbatim and receives no guessed outcome.
  function fileActionOutcome(entry) {
    const status = String(entry.status || '').toLowerCase();
    const mode = String(entry.mode || '').toLowerCase();
    const action = String(entry.action || '').toUpperCase();
    if (action === 'TRASH_ATTEMPT') return null;
    if (action === 'TRASH_UNCONFIRMED' || ['trash-unconfirmed', 'trash_unconfirmed', 'unconfirmed'].includes(status)) return 'failed';
    if (['ok', 'success', 'trashed', 'removed'].includes(status)) return mode === 'trash' ? 'trashed' : ['permanent', 'delete'].includes(mode) ? 'removed' : null;
    if (['error', 'timed-out', 'interrupted', 'trash-failed', 'invalid-mode', 'failed'].includes(status)) return 'failed';
    if (['rejected', 'mutable-parent', 'identity-changed', 'ownership-unverified', 'app-reappeared', 'privacy-denied', 'sudo-blocked-test-mode', 'skipped'].includes(status)) return 'skipped';
    return null;
  }
  function historyMatches(entry, session, filter) {
    const text = [entry.command, entry.path, entry.mode, entry.status, entry.action, ...(entry.actions ? Object.keys(entry.actions).filter(key => entry.actions[key] > 0) : [])].filter(Boolean).join(' ').toLocaleLowerCase();
    if (filter.query && !text.includes(filter.query.toLocaleLowerCase())) return false;
    if (filter.command && (session ? entry.command !== filter.command : true)) return false;
    if (filter.since) { const timestamp = new Date(session ? entry.started_at : entry.timestamp).getTime(); if (!Number.isFinite(timestamp) || timestamp < new Date(filter.since + 'T00:00:00').getTime()) return false; }
    if (filter.outcome) {
      if (session) { if (!(entry.actions?.[filter.outcome] > 0 || filter.outcome === 'failed' && entry.failed_tasks > 0)) return false; }
      else if (fileActionOutcome(entry) !== filter.outcome) return false;
    }
    return true;
  }
  function reportView(kind) { return kind === 'apps' ? 'uninstall' : kind; }
  function renderReport(kind) {
    if (app.view !== reportView(kind) || !$('#report-content')) return;
    const record = app.reports.get(kind);
    const content = $('#report-content');
    const button = document.querySelector('[data-report]');
    button.disabled = !!record?.loading || jobRunning();
    if (record?.loading) { content.innerHTML = '<div class="report-empty"><span class="loading-orbit" aria-hidden="true"></span><div><p>Collecting a snapshot…</p><small>Mole is reading current data. This may take a moment.</small></div></div>'; return; }
    if (record?.error && !record?.data) { content.innerHTML = `<div class="report-error">${escape(record.error)}</div><p class="quiet-note">${icon('info')}Open this command in Terminal for details.</p>`; return; }
    if (!record?.data) { content.innerHTML = `<div class="report-empty">${icon(kind === 'status' ? 'activity' : kind === 'history' ? 'history' : 'apps')}<div><p>${kind === 'status' ? 'Your health snapshot is ready when you are.' : kind === 'history' ? 'See the work Mole has actually completed.' : 'Find exact app names for the command below.'}</p><small>${kind === 'status' ? 'Choose Refresh health to measure current usage.' : 'Use the button above to read your local data.'}</small></div></div>`; return; }
    const data = record.data;
    let html = record.error ? `<div class="report-error">${escape(record.error)} · Showing the previous completed snapshot.</div>` : '';
    if (kind === 'status') {
      const metric = (name, value, note) => `<div class="report-metric"><span>${escape(name)}</span><strong>${escape(value)}</strong><small>${escape(note)}</small></div>`;
      const percent = value => Number.isFinite(value) ? `${Math.round(value)}%` : 'Unknown';
      html += `<div class="report-metrics">${metric('CPU usage', percent(data.cpu?.usage), 'At collection time')}${metric('Memory used', percent(data.memory?.used_percent), data.memory ? `${bytes(data.memory.used)} of ${bytes(data.memory.total)}` : 'Unavailable')}${metric('Health score', Number.isFinite(data.health_score) && data.health_score >= 0 && data.health_score <= 100 ? `${data.health_score}/100` : 'Unknown', data.health_score_msg || 'No score reported')}${metric('Uptime', data.uptime || 'Unknown', 'Since the last restart')}</div>`;
      if (data.collected_at) html += `<p class="quiet-note">${icon('info')}Snapshot from ${escape(new Date(data.collected_at).toLocaleString())}.</p>`;
    } else if (kind === 'history') {
      const filter = app.reportFilters.history;
      const allSessions = Array.isArray(data.sessions) ? data.sessions : [];
      const allDeletions = Array.isArray(data.deletions) ? data.deletions : [];
      const commands = [...new Set(allSessions.map(entry => entry.command).filter(Boolean))].sort();
      const commandSelect = $('#history-command');
      if (commandSelect) { const signature = JSON.stringify(commands); if (commandSelect.dataset.options !== signature) { commandSelect.innerHTML = '<option value="">All commands</option>' + commands.map(command => `<option value="${escape(command)}">${escape(command)}</option>`).join(''); commandSelect.dataset.options = signature; } commandSelect.value = filter.command; }
      const sessions = allSessions.filter(entry => historyMatches(entry, true, filter));
      const deletions = allDeletions.filter(entry => historyMatches(entry, false, filter));
      html += `<p class="report-scope">${sessions.length} of ${allSessions.length} loaded sessions · ${deletions.length} of ${allDeletions.length} loaded file actions. Filters cover the latest ${escape(data.limit || Math.max(allSessions.length, allDeletions.length))} available records per log.</p>${filter.command ? '<p class="quiet-note">File actions have no command identity and are omitted by this command filter.</p>' : ''}`;
      if (!Array.isArray(data.sessions) && !Array.isArray(data.deletions)) html += '<div class="report-empty"><p>This report has no session or file-action rows. View the JSON report for details.</p></div>';
      else if (!sessions.length && !deletions.length) html += '<div class="report-empty"><p>No loaded records match these filters.</p></div>';
      if (sessions.length) html += `<div class="history-list"><h3 class="report-section-label">Recent sessions</h3>${sessions.map(entry => {
        const actionCounts = entry.actions ? Object.entries(entry.actions).filter(([, count]) => count > 0).map(([action, count]) => `${count} ${action}`) : [];
        if (entry.failed_tasks > 0) actionCounts.push(`${entry.failed_tasks} ${entry.failed_tasks === 1 ? 'task failure' : 'task failures'}`);
        const counts = actionCounts.join(' · ');
        const outcome = entry.ended_at ? 'Completion recorded' : 'No completion recorded';
        return `<div class="history-item">${icon('history')}<div><strong>mo ${escape(entry.command || 'operation')}</strong><small>${escape(counts || 'No outcomes recorded')} · ${escape(outcome)}</small><small>${escape(entry.operation_count ?? 'Unknown')} logged operations</small></div><time>${escape(entry.started_at || 'Time unavailable')}</time></div>`;
      }).join('')}</div>`;
      if (deletions.length) html += `<div class="history-list"><h3 class="report-section-label">Recent file actions</h3>${deletions.map(entry => `<div class="history-item">${icon(entry.mode === 'TRASH' || entry.mode === 'trash' ? 'trash' : 'file')}<div><strong>${escape(entry.path?.split('/').at(-1) || 'File operation')}</strong><small>${escape(entry.path || 'Path unavailable')}</small><small>${escape(entry.mode || 'Mode unavailable')} · ${escape(entry.status || entry.action || 'Outcome unavailable')}</small></div><time>${escape(entry.timestamp || 'Time unavailable')}</time></div>`).join('')}</div>`;
    } else if (kind === 'apps') {
      const source = Array.isArray(data) ? data : Array.isArray(data.apps) ? data.apps : null;
      const filter = app.reportFilters.apps;
      const entries = source ? source.filter(entry => [entry.name, entry.bundle_id, entry.uninstall_name, entry.path, entry.source].filter(Boolean).join(' ').toLocaleLowerCase().includes(filter.query.toLocaleLowerCase())).sort((a, b) => {
        if (filter.sort.startsWith('size')) { const left = reportedSize(a.size), right = reportedSize(b.size); if (left === null && right !== null) return 1; if (right === null && left !== null) return -1; if (left !== null && right !== null && left !== right) return (left - right) * (filter.sort === 'size-desc' ? -1 : 1); }
        return String(a.name || '').localeCompare(String(b.name || ''), undefined, { numeric: true });
      }) : null;
      const selectedNames = new Set(configFor(app.state.catalog.find(item => item.id === 'uninstall')).fields.apps.split('\n').map(name => name.trim()).filter(Boolean));
      if (entries && !entries.length) html += '<div class="report-empty"><p>No loaded applications match this search.</p></div>';
      else if (entries) html += `<p class="quiet-note">${icon('info')}${entries.length} of ${source.length} loaded apps. Choose exact names, then review the uninstall command in Terminal.</p><div class="app-inventory">${entries.map(entry => {
        const name = entry.name || entry.uninstall_name;
        const selected = selectedNames.has(name);
        return `<div class="app-inventory-row${selected ? ' chosen' : ''}"><span class="app-inventory-icon">${icon('apps')}</span><div class="app-inventory-info"><strong>${escape(entry.name || 'Unnamed app')}</strong><small>${escape(entry.bundle_id || 'Bundle ID unavailable')} · ${escape(entry.source || 'App')}</small></div><span class="app-inventory-size">${escape(typeof entry.size === 'string' && entry.size ? entry.size : 'Unknown')}</span><button class="button secondary small" data-app-name="${escape(name || '')}" aria-pressed="${selected}" ${name ? '' : 'disabled'}>${selected ? 'Added' : 'Choose'}</button></div>`;
      }).join('')}</div>`;
    }
    if (record.sampled_at) html += `<p class="report-scope">Completed snapshot · ${escape(readableTime(record.sampled_at))}</p>`;
    html += `<details class="report-raw"${!html ? ' open' : ''}><summary>View complete JSON report</summary><pre>${escape(JSON.stringify(data, null, 2))}</pre></details>`;
    content.innerHTML = html;
  }
  async function loadReport(kind) {
    await startJob({ kind: 'report', report: kind }, { type: 'report', key: kind, title: { status: 'System health snapshot', history: 'Activity history', apps: 'Installed app inventory' }[kind] });
  }
  function jobRunning() { return app.jobStarting || ['running', 'unknown'].includes(app.job?.status); }
  function elapsed(value) {
    if (!Number.isFinite(value) || value < 0) return '—';
    const seconds = Math.floor(value);
    return seconds < 60 ? `${seconds}s` : `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
  }
  function renderJob() {
    let host = $('#job-host');
    if (!host) { host = document.createElement('div'); host.id = 'job-host'; host.className = 'job-host'; main.before(host); }
    if (!app.job && !app.jobStarting) { host.hidden = true; return; }
    host.hidden = false;
    const focusedAction = host.contains(document.activeElement) ? document.activeElement.id : '';
    const job = app.job || { id: 'starting', status: 'running', stage: 'Starting your request…', elapsed_seconds: 0 };
    const active = ['running', 'unknown'].includes(job.status);
    const title = app.jobContext?.title || 'Mole task';
    const previousKey = host.dataset.jobKey;
    const key = String(job.id);
    if (previousKey !== key) {
      host.dataset.jobKey = key; delete host.dataset.actionKey;
      host.innerHTML = `<section class="job-panel" aria-label="Current Mole task"><div class="job-heading"><span class="job-icon">${icon(active ? 'activity' : job.status === 'completed' ? 'check' : 'info')}</span><div><strong>${escape(title)}</strong><p class="job-stage" id="job-stage" role="status"></p></div><div class="job-time"><span>Elapsed</span><strong id="job-elapsed"></strong></div><div class="job-actions">${active ? '<button class="button secondary small" id="cancel-job">Cancel task</button>' : '<button class="icon-button" id="dismiss-job" aria-label="Dismiss completed task">' + icon('close') + '</button>'}${job.status === 'unknown' ? '<button class="button secondary small" id="check-job">Check status</button>' : ''}</div></div><div id="job-progress"></div><div id="job-activity-host" hidden></div><p class="job-error" id="job-error" hidden></p></section>`;
    }
    const actionKey = `${job.status}:${app.jobStarting}`;
    const actionsChanged = host.dataset.actionKey !== actionKey;
    if (actionsChanged) {
      host.dataset.actionKey = actionKey;
      host.querySelector('.job-actions').innerHTML = active ? '<button class="button secondary small" id="cancel-job">Cancel task</button>' + (job.status === 'unknown' ? '<button class="button secondary small" id="check-job">Check status</button>' : '') : '<button class="icon-button" id="dismiss-job" aria-label="Dismiss completed task">' + icon('close') + '</button>';
      host.querySelector('.job-icon').innerHTML = icon(active ? 'activity' : job.status === 'completed' ? 'check' : 'info');
    }
    host.querySelector('.job-panel').dataset.state = job.status;
    const stage = job.stage || job.status;
    if ($('#job-stage').textContent !== stage) $('#job-stage').textContent = stage;
    $('#job-elapsed').textContent = elapsed(job.elapsed_seconds);
    const progress = job.progress;
    if (progress && Number.isFinite(progress.done) && Number.isFinite(progress.total) && progress.total > 0 && progress.done >= 0 && progress.done <= progress.total) {
      $('#job-progress').innerHTML = `<div class="job-progress"><progress max="${progress.total}" value="${progress.done}" aria-label="Measured task progress"></progress><span>${escape(progress.done)} / ${escape(progress.total)} ${escape(progress.unit || 'items')}</span></div>`;
    } else $('#job-progress').innerHTML = '';
    $('#job-error').hidden = !job.error;
    $('#job-error').textContent = job.error || '';
    if (focusedAction && (previousKey !== key || actionsChanged) && document.activeElement.id !== focusedAction) (document.getElementById(focusedAction) || $('#dismiss-job'))?.focus({ preventScroll: true });
    if ($('#cancel-job')) $('#cancel-job').disabled = app.jobStarting || !!job.cancelling;
    document.querySelectorAll('[data-report], [data-start-preview], #measure-folder').forEach(button => { button.disabled = jobRunning(); });
    if ($('#review-trash')) $('#review-trash').disabled = jobRunning() || app.dialogBusy;
    if ($('#launch-command')) $('#launch-command').disabled = !app.command || jobRunning() || app.dialogBusy;
    renderPreviewActivity(job);
  }
  function retainPreviewActivity(snapshot, previous) {
    const stopped = ['completed', 'cancelled', 'failed'].includes(snapshot.status);
    if (snapshot.kind === 'preview' && previous?.id === snapshot.id && Array.isArray(previous.activity?.lines) && (!Array.isArray(snapshot.activity?.lines) || stopped && !snapshot.activity.lines.length && previous.activity.lines.length)) {
      return { ...snapshot, activity: previous.activity };
    }
    return snapshot;
  }
  function readableActivityLine(line) {
    return line.replace(/\u001b\][^\u0007]*(?:\u0007|\u001b\\)/g, '').replace(/\u001b\[[0-?]*[ -/]*[@-~]/g, '').split('\r').at(-1).replace(/[\u0000-\u0008\u000b-\u001f\u007f]/g, '');
  }
  function nearActivityBottom(log) { return log.scrollHeight - log.scrollTop - log.clientHeight <= 28; }
  function renderPreviewActivity(job, jumpToLatest = false) {
    const host = $('#job-activity-host');
    if (!host) return;
    const preview = job.kind === 'preview' || app.jobContext?.type === 'preview';
    host.hidden = !preview;
    if (!preview) return;
    if (!app.activityView || app.activityView.id !== String(job.id)) {
      app.activityView = { id: String(job.id), receivedKey: '', renderedKey: '', changedAt: Number.isFinite(job.elapsed_seconds) ? job.elapsed_seconds : 0, following: true };
      host.innerHTML = `<section class="job-activity" aria-labelledby="job-activity-title"><div class="job-activity-heading"><div><span class="job-activity-dot" aria-hidden="true"></span><h3 id="job-activity-title">Live preview activity</h3></div><span class="job-activity-status" id="job-activity-status"></span></div><div class="job-activity-latest"><span>Latest output</span><p id="job-activity-latest"></p></div><div class="job-activity-toolbar"><span id="job-activity-meta"></span><button class="text-button" id="job-activity-latest-button" aria-label="Scroll to latest preview output" hidden>Latest ${icon('down')}</button></div><div class="job-activity-log" id="job-activity-log" role="region" aria-label="Recent preview output" aria-describedby="job-activity-note" tabindex="0" hidden><pre id="job-activity-lines" aria-live="off"></pre></div><p class="job-activity-note" id="job-activity-note">This is read-only preview output. To apply changes, use your reviewed Terminal command.</p></section>`;
      $('#job-activity-log').addEventListener('scroll', () => {
        const view = app.activityView;
        const log = $('#job-activity-log');
        if (!view || !log || view.id !== String(app.job?.id)) return;
        const following = nearActivityBottom(log);
        if (following !== view.following) renderPreviewActivity(app.job, following);
      });
      $('#job-activity-latest-button').addEventListener('click', () => { if (app.job) renderPreviewActivity(app.job, true); });
    }
    const view = app.activityView;
    const lines = Array.isArray(job.activity?.lines) ? job.activity.lines.filter(line => typeof line === 'string').slice(-120).map(readableActivityLine) : [];
    const total = Number.isSafeInteger(job.activity?.total_lines) && job.activity.total_lines >= lines.length ? job.activity.total_lines : null;
    const truncated = !!job.activity?.truncated;
    const receivedKey = JSON.stringify([lines, total, truncated]);
    if (view.receivedKey !== receivedKey) {
      view.receivedKey = receivedKey;
      view.changedAt = Number.isFinite(job.elapsed_seconds) ? job.elapsed_seconds : view.changedAt;
    }
    const log = $('#job-activity-log');
    const selection = window.getSelection();
    const selectingOutput = selection && !selection.isCollapsed && (log.contains(selection.anchorNode) || log.contains(selection.focusNode));
    const following = jumpToLatest || nearActivityBottom(log) && !selectingOutput;
    view.following = following;
    if (following && view.renderedKey !== receivedKey) {
      const output = $('#job-activity-lines');
      lines.forEach((line, index) => {
        let row = output.children[index];
        if (!row) { row = document.createElement('span'); row.className = 'job-activity-line'; output.append(row); }
        if (row.textContent !== line) row.textContent = line;
      });
      while (output.children.length > lines.length) output.lastElementChild.remove();
      view.renderedKey = receivedKey;
      log.hidden = !lines.length;
      log.scrollTop = log.scrollHeight;
    }
    const waiting = !lines.some(line => line.trim());
    const quiet = job.status === 'running' && Number.isFinite(job.elapsed_seconds) && job.elapsed_seconds - view.changedAt >= 12;
    const status = job.status === 'unknown' ? 'Connection interrupted · last received output' : job.status === 'cancelled' ? 'Cancelled · output retained' : job.status === 'failed' ? 'Stopped · output retained' : job.status === 'completed' ? 'Preview finished' : quiet ? 'Still running · no new reported output recently' : 'Preview running';
    if ($('#job-activity-status').textContent !== status) $('#job-activity-status').textContent = status;
    let latest = '';
    for (let index = lines.length - 1; index >= 0; index--) if (lines[index].trim()) { latest = lines[index]; break; }
    if (waiting) latest = ['completed', 'failed', 'cancelled'].includes(job.status) ? 'No readable preview output was reported.' : job.status === 'unknown' ? 'No preview output was received before the connection was interrupted.' : 'Waiting for the first preview output. Filesystem checks may be quiet for a while.';
    if ($('#job-activity-latest').textContent !== latest) $('#job-activity-latest').textContent = latest;
    $('#job-activity-latest').title = waiting ? '' : latest;
    host.dataset.waiting = String(waiting);
    const pending = view.renderedKey !== receivedKey;
    const meta = following ? total === null ? 'Recent reported output' : `${lines.length} of ${total} reported lines${truncated ? ' · some output omitted' : ''}` : pending ? 'Reading earlier output · new output available' : 'Reading earlier output';
    if ($('#job-activity-meta').textContent !== meta) $('#job-activity-meta').textContent = meta;
    $('#job-activity-latest-button').hidden = !lines.length && !$('#job-activity-lines').children.length;
    $('#job-activity-latest-button').classList.toggle('has-new-output', pending && !following);
  }
  async function startJob(payload, context) {
    if (jobRunning()) { toast('Let the current task finish, or cancel it before starting another.', true); return; }
    const generation = ++app.jobGeneration;
    app.jobStarting = true; app.job = null; app.jobContext = context;
    if (context.type === 'report') { const record = app.reports.get(context.key) || {}; app.reports.set(context.key, { ...record, loading: true, error: '' }); renderReport(context.key); }
    if (context.type === 'preview') { const record = app.previews.get(context.key) || {}; app.previews.set(context.key, { ...record, loading: true, error: '' }); renderPreview(context.key); }
    renderJob(); renderBrowser();
    $('#job-host')?.scrollIntoView({ block: 'nearest', behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
    try {
      const accepted = await api('/api/jobs', payload);
      if (generation !== app.jobGeneration) return;
      app.jobStarting = false;
      app.job = { id: accepted.id, kind: payload.kind, status: 'running', stage: 'Preparing the task…', elapsed_seconds: 0, progress: null };
      renderJob();
      await pollJob(accepted.id, generation);
    } catch (error) {
      if (generation !== app.jobGeneration) return;
      app.jobStarting = false;
      if (await recoverActiveJob()) return;
      app.job = { id: 'failed-' + generation, status: 'failed', stage: 'Could not start the task', error: error.message, elapsed_seconds: 0 };
      applyJobResult(app.job); renderJob();
    }
  }
  async function pollJob(id, generation = app.jobGeneration) {
    clearTimeout(app.jobTimer);
    const sequence = ++app.jobPollSequence;
    try {
      const snapshot = await request('/api/jobs/' + encodeURIComponent(id), undefined, 12000);
      if (generation !== app.jobGeneration || sequence !== app.jobPollSequence || app.job?.id !== id) return;
      app.job = retainPreviewActivity(snapshot, app.job); renderJob();
      if (snapshot.status === 'running') app.jobTimer = setTimeout(() => pollJob(id, generation), 1100);
      else { applyJobResult(snapshot); renderJob(); }
    } catch (error) {
      if (generation !== app.jobGeneration || sequence !== app.jobPollSequence || app.job?.id !== id) return;
      let message = error.message;
      if (error.status === 404) {
        const recovered = await recoverActiveJob();
        if (recovered) return;
        if (generation !== app.jobGeneration || sequence !== app.jobPollSequence || app.job?.id !== id) return;
        if (recovered === false) {
          app.job = { ...app.job, status: 'failed', stage: 'Result expired or unavailable', error: 'No active task remains. This result could not be verified. Start a new task for a fresh result.' };
          applyJobResult(app.job); renderJob();
          return;
        }
        message = app.lastRecoveryError || message;
      }
      app.job = { ...app.job, status: 'unknown', stage: 'Connection interrupted · task outcome unknown', error: message };
      renderJob();
    }
  }
  async function recoverActiveJob() {
    app.lastRecoveryError = '';
    try {
      const response = await request('/api/jobs', undefined, 12000);
      const snapshot = response.active;
      if (!snapshot || snapshot.status !== 'running') return false;
      clearTimeout(app.jobTimer);
      const generation = ++app.jobGeneration;
      const context = snapshot.request || snapshot.context || {};
      app.job = retainPreviewActivity(snapshot, app.job); app.jobStarting = false;
      app.jobContext = context.kind === 'report' ? { type: 'report', key: context.report, title: { status: 'System health snapshot', history: 'Activity history', apps: 'Installed app inventory' }[context.report] || 'Read-only report' } : context.kind === 'analyze' ? { type: 'measure', path: context.path, title: 'Measuring ' + labelForPath(context.path || '') } : context.kind === 'preview' ? { type: 'preview', key: context.command, apps: context.apps || [], title: context.command === 'uninstall' ? 'Uninstall preview' : 'Cleanup preview' } : { title: 'Current Mole task' };
      renderJob(); renderBrowser();
      pollJob(snapshot.id, generation);
      return true;
    } catch (error) { app.lastRecoveryError = error.message; return null; }
  }
  function applyJobResult(job) {
    const context = app.jobContext;
    const complete = job.status === 'completed';
    const error = job.error || (job.status === 'cancelled' ? 'Task cancelled. No completed result was returned.' : 'The task could not complete.');
    if (context?.type === 'report') {
      const previous = app.reports.get(context.key) || {};
      app.reports.set(context.key, { ...previous, loading: false, error: complete ? '' : error, ...(complete ? { data: job.result, sampled_at: job.sampled_at || job.result?.sampled_at || Date.now() / 1000 } : {}) });
      renderReport(context.key);
    } else if (context?.type === 'measure') {
      if (complete && job.result) {
        app.measurements.delete(context.path); app.measurements.set(context.path, job.result);
        while (app.measurements.size > 10) app.measurements.delete(app.measurements.keys().next().value);
      }
      renderMeasurement();
    } else if (context?.type === 'preview') {
      const previous = app.previews.get(context.key) || {};
      app.previews.set(context.key, { ...previous, loading: false, error: complete ? '' : error, ...(complete ? { data: job.result, apps: context.apps || [] } : {}) });
      renderPreview(context.key);
    }
    renderRecovery(); renderBrowserPreservingFocus();
    const retry = app.browser.retryAfterJob;
    if (retry && retry.path === app.browser.path && !jobRunning()) loadBrowse(retry.path, { preserveFilters: true, offset: retry.offset });
  }
  async function cancelJob() {
    if (!app.job?.id || !jobRunning() || app.jobStarting) return;
    const id = app.job.id, generation = app.jobGeneration;
    clearTimeout(app.jobTimer); ++app.jobPollSequence;
    app.job.cancelling = true; renderJob();
    try {
      await request('/api/jobs/' + encodeURIComponent(id) + '/cancel', {}, 12000);
      if (generation === app.jobGeneration) await pollJob(id, generation);
    } catch (error) { if (generation === app.jobGeneration) { app.job.cancelling = false; app.job.status = 'unknown'; app.job.stage = 'Cancellation not confirmed'; app.job.error = error.message; renderJob(); } }
  }
  function measurementShell() {
    return `<section class="measurement-panel" aria-label="Folder measurements"><div class="measurement-heading"><div><h2>See where the space goes</h2><p>Measure this folder, then step inside the larger pieces.</p></div><button class="button small" id="measure-folder">${icon('pie')}Measure folder</button></div><div id="measurement-content"></div></section>`;
  }
  function completeSize(entry) { return entry.scan_status === 'complete' && Number.isFinite(entry.size) && entry.size >= 0; }
  function treemap(items, x = 0, y = 0, width = 100, height = 100) {
    if (items.length === 1) return [{ ...items[0], x, y, width, height }];
    const total = items.reduce((sum, entry) => sum + entry.size, 0);
    let index = 1, left = items[0].size;
    while (index < items.length - 1 && Math.abs(total / 2 - (left + items[index].size)) < Math.abs(total / 2 - left)) left += items[index++].size;
    const ratio = left / total;
    return width >= height ? [...treemap(items.slice(0, index), x, y, width * ratio, height), ...treemap(items.slice(index), x + width * ratio, y, width * (1 - ratio), height)] : [...treemap(items.slice(0, index), x, y, width, height * ratio), ...treemap(items.slice(index), x, y + height * ratio, width, height * (1 - ratio))];
  }
  function renderMeasurement() {
    const content = $('#measurement-content');
    if (!content) return;
    const measurement = app.measurements.get(app.browser.path);
    $('#measure-folder').disabled = jobRunning();
    if (!measurement) { content.innerHTML = `<div class="measurement-empty">${icon('folder')}<p>Folder sizes are measured on your request.<br><span>No recursive scan has run for this folder yet.</span></p></div>`; return; }
    const entries = Array.isArray(measurement.entries) ? measurement.entries : [];
    const known = entries.filter(completeSize).sort((a, b) => b.size - a.size);
    const positive = known.filter(entry => entry.size > 0);
    const measured = known.reduce((sum, entry) => sum + entry.size, 0);
    const unknown = entries.filter(entry => !completeSize(entry));
    const tiles = positive.slice(0, 12);
    if (positive.length > 12) tiles.push({ name: 'Other measured items', size: positive.slice(12).reduce((sum, entry) => sum + entry.size, 0), aggregate: true });
    const chart = tiles.length ? treemap(tiles).map((entry, index) => {
      const label = `${entry.name}: ${bytes(entry.size)}, ${(entry.size / measured * 100).toFixed(1)}% of measured entries`;
      const tag = entry.aggregate ? 'div' : 'button';
      return `<${tag} class="disk-map-tile${entry.aggregate ? ' aggregate' : ''}" ${entry.aggregate ? '' : `${entry.is_dir ? 'data-map-path' : 'data-map-file'}="${escape(entry.path)}" aria-label="${escape(label)}"`} style="left:${entry.x}%;top:${entry.y}%;width:${entry.width}%;height:${entry.height}%;--tile-weight:${entry.size / measured};--tile-tone:${index % 5}" title="${escape(label)}"><span class="disk-map-label">${escape(entry.name)}</span><span class="disk-map-size">${escape(bytes(entry.size))}</span></${tag}>`;
    }).join('') : '';
    content.innerHTML = `<div class="measurement-summary"><div><strong>${escape(bytes(measured))}</strong><span>in ${known.length} completely measured entries</span></div><span>${measurement.scan_status === 'complete' ? 'Measured snapshot' : 'Incomplete scan'} · ${escape(readableTime(measurement.sampled_at))}</span></div>${chart ? `<div class="disk-map" aria-label="Proportional sizes within this folder">${chart}</div>` : '<p class="quiet-note">No positive, complete entry sizes were returned.</p>'}<p class="quiet-note">${icon('info')}Tiles share the measured entries above, not your whole disk. Folder tiles start a new read-only scan.</p>${unknown.length ? `<details class="measurement-unknown" open><summary>${unknown.length} ${unknown.length === 1 ? 'entry is' : 'entries are'} incomplete or unavailable</summary><ul>${unknown.map(entry => `<li><span>${escape(entry.name)}</span><span>${entry.scan_status === 'partial' && Number.isFinite(entry.size) && entry.size > 0 ? `${escape(bytes(entry.size))}+ · partial` : 'Size unavailable'}</span></li>`).join('')}</ul></details>` : ''}${known.some(entry => entry.size === 0) ? `<p class="quiet-note">${known.filter(entry => entry.size === 0).length} completely measured entries contain 0 bytes.</p>` : ''}`;
  }
  async function measureFolder(path = app.browser.path || defaultPath(), drill = false) {
    if (jobRunning()) { toast('Finish or cancel the current task before measuring another folder.', true); return; }
    if (drill) await loadBrowse(path);
    await startJob({ kind: 'analyze', path }, { type: 'measure', path, title: 'Measuring ' + labelForPath(path) });
  }
  function previewShell(command) {
    return `<section class="cleanup-preview-panel" aria-label="Cleanup preview"><div class="measurement-heading"><div><h2>${command === 'clean' ? 'A look before you clean' : 'Review selected apps'}</h2><p>${command === 'clean' ? 'A read-only dry-run of Mole’s standard cleanup.' : 'Choose exact app names, then inspect a forced dry-run.'}</p></div><button class="button small" data-start-preview="${command}">${icon('search')}${command === 'clean' ? 'Preview cleanup' : 'Preview selected apps'}</button></div><div id="cleanup-preview-content"></div></section>`;
  }
  function renderPreview(command) {
    const content = $('#cleanup-preview-content');
    if (!content || app.view !== command) return;
    const record = app.previews.get(command);
    document.querySelector('[data-start-preview]').disabled = jobRunning();
    if (!record?.data && !record?.loading && !record?.error) { content.innerHTML = '<p class="quiet-note">' + icon('shield') + 'A preview inspects targets. It never authorizes a later removal.</p>'; return; }
    const data = record?.data;
    let html = record?.loading ? '<p class="quiet-note">' + icon('activity') + 'The preview is running. Its stage and cancellation control are above.</p>' : '';
    if (record?.error) html += `<p class="report-error">${escape(record.error)}</p>`;
    if (data) {
      if (record.loading || record.error) html += '<p class="preview-previous">Previous completed preview · the current task produced no new completed result.</p>';
      const candidates = Array.isArray(data.candidates) ? data.candidates : [];
      html += `<div class="preview-summary"><strong>${escape(data.command || 'Mole dry-run')}</strong><span>Snapshot ${escape(readableTime(data.sampled_at))}</span></div><p class="quiet-note">${icon('info')}${escape(data.scope_note || 'This preview is a limited, unprivileged inspection. Read the transcript for retained items and skipped checks.')}</p>${record.apps?.length ? `<p class="preview-apps">Previewed names: ${escape(record.apps.join(', '))}</p>` : ''}${candidates.length ? `<div class="preview-candidates">${candidates.map(candidate => `<div class="preview-candidate"><span>${icon('file')}</span><div><strong class="${candidate.path ? '' : 'preview-raw-line'}">${escape(candidate.path || candidate.raw_line || 'Unparsed preview row')}</strong><small>${escape(candidate.section || '')}${candidate.note ? ' · ' + escape(candidate.note) : ''}</small></div><span class="preview-size">${escape(candidate.path ? candidate.size_label || 'Size not reported' : '')}</span></div>`).join('')}</div>` : '<p class="quiet-note">No structured candidate paths were reported. Inspect the transcript for the complete preview outcome.</p>'}<p class="quiet-note">${icon('shield')}This is a read-only report, not a GUI deletion plan. Run changes through the reviewed Terminal command.</p><details class="report-raw"><summary>Read full preview transcript</summary><pre>${escape(data.output || 'No transcript returned.')}</pre></details>${typeof data.preview_report === 'string' && data.preview_report ? `<details class="report-raw"><summary>Read raw preview listing</summary><pre>${escape(data.preview_report)}</pre></details>` : ''}`;
    }
    content.innerHTML = html;
  }
  async function previewCleanup(command) {
    const names = command === 'uninstall' ? configFor(app.state.catalog.find(item => item.id === 'uninstall')).fields.apps.split('\n').map(name => name.trim()).filter(Boolean) : [];
    if (command === 'uninstall' && !names.length) { toast('Choose at least one exact app name before previewing uninstall.', true); $('#field-apps')?.focus(); return; }
    await startJob({ kind: 'preview', command, ...(command === 'uninstall' ? { apps: names } : {}) }, { type: 'preview', key: command, apps: names, title: command === 'clean' ? 'Cleanup preview' : 'Uninstall preview' });
  }
  function recoveryShell(compact = false) {
    return `<section class="recovery-panel" aria-label="Trash recovery" data-recovery-compact="${compact}"><div class="measurement-heading"><div><h2>A second chance, in Trash</h2><p>Your reviewed file moves stay recoverable until Trash is emptied.</p></div><button class="button secondary small" data-open-trash>${icon('trash')}Open Trash</button></div><div id="recovery-content"></div></section>`;
  }
  function renderRecovery() {
    const content = $('#recovery-content');
    if (!content) return;
    const compact = $('.recovery-panel').dataset.recoveryCompact === 'true';
    const history = app.reports.get('history')?.data;
    const logged = Array.isArray(history?.deletions) ? history.deletions.filter(entry => entry.mode === 'trash' && entry.status === 'ok' && typeof entry.path === 'string').map(entry => ({ path: entry.path, time: new Date(entry.timestamp).getTime() / 1000, logged: true })).filter(entry => Number.isFinite(entry.time)) : [];
    const seen = new Set();
    const moves = [...app.recentMoves, ...logged].sort((a, b) => b.time - a.time).filter(move => { if (seen.has(move.path)) return false; seen.add(move.path); return true; }).slice(0, compact ? 3 : 20);
    content.innerHTML = `<p class="quiet-note">${icon('info')}In Finder’s Trash, select an item, then choose File → Put Back when available. You can also drag it to a folder. Mole does not promise automatic undo.</p>${moves.length ? `<h3 class="report-section-label">Confirmed Trash moves${logged.length ? ' · session and loaded logs' : ' · this GUI session'}</h3><div class="recovery-items">${moves.map(move => `<div class="history-item">${icon('trash')}<div><strong>${escape(move.path.split('/').at(-1))}</strong><small>${escape(move.path)}</small></div><time>${escape(move.logged ? date(move.time) + ' · ' + readableTime(move.time) : readableTime(move.time))}</time></div>`).join('')}</div>` : '<p class="recovery-empty">No successful Trash moves are loaded yet.</p>'}${compact ? '<button class="text-button" data-view="recovery">Recovery details ' + icon('arrow') + '</button>' : `<div class="recovery-actions"><button class="button secondary small" data-report="history" ${jobRunning() ? 'disabled' : ''}>${icon('history')}Load recent Trash activity</button><button class="text-button" data-view="history">Browse recorded activity ${icon('arrow')}</button></div>`}<p class="quiet-note">These are recorded moves, not proof that items remain in Trash. Use Finder to check what is still available.</p>`;
  }
  function recoveryView() {
    main.innerHTML = `<div class="view-enter"><header class="command-header"><span class="command-header-icon">${icon('trash')}Your files</span><h1>Room to reconsider.</h1><p>Restore personal items through your Mac’s Trash.</p></header>${recoveryShell()}<p class="quiet-note">${icon('shield')}Permanent CLI cleanup does not enter Trash and cannot be restored here.</p></div>`;
    renderRecovery();
  }
  async function nativeAction(action, id) {
    try { await api('/api/file-action', { action, ...(id ? { id } : {}) }); toast(action === 'trash' ? 'Opened your Mac’s Trash.' : action === 'reveal' ? 'Revealed in Finder.' : 'Opened in Preview.'); }
    catch (error) { toast(error.message, true); }
  }
  const mobileDrawer = window.matchMedia('(max-width: 720px)');
  function setNavOpen(open) {
    const expanded = open && mobileDrawer.matches;
    document.body.classList.toggle('nav-open', expanded);
    $('#sidebar-scrim').hidden = !expanded;
    $('#menu-button').setAttribute('aria-expanded', String(expanded));
    $('#sidebar').inert = mobileDrawer.matches && !expanded;
    $('#sidebar').setAttribute('aria-hidden', String(mobileDrawer.matches && !expanded));
    $('.main-shell').inert = expanded;
    if (expanded) $('#navigation .active')?.focus();
  }
  mobileDrawer.addEventListener('change', () => setNavOpen(false));
  function openDialog(type, content, actions) {
    if (app.dialogBusy) return;
    app.dialogGeneration++;
    if (!dialog.open) app.pendingFocus = document.activeElement;
    $('#dialog-icon').className = `dialog-icon${type === 'trash' ? ' danger' : ''}`;
    $('#dialog-icon').innerHTML = icon(type);
    $('#dialog-content').innerHTML = content;
    $('#dialog-actions').replaceChildren();
    for (const { label, style, action, disabled } of actions) {
      const button = document.createElement('button'); button.className = `button${style ? ' ' + style : ''}`; button.textContent = label; button.disabled = !!disabled; button.dataset.initiallyDisabled = String(!!disabled); button.addEventListener('click', action); $('#dialog-actions').append(button);
    }
    if (!dialog.open) dialog.showModal();
    $('#dialog-actions button')?.focus();
  }
  function closeDialog() { if (!app.dialogBusy) dialog.close(); }
  function dialogBusy(busy) {
    app.dialogBusy = busy;
    $('#dialog-close').disabled = busy;
    $('#dialog-actions').querySelectorAll('button').forEach(button => { button.disabled = busy || button.dataset.initiallyDisabled === 'true'; });
  }
  function beginDialogOperation(kind) {
    const operation = { kind, generation: app.dialogGeneration };
    app.dialogOperation = operation;
    dialogBusy(true); renderBrowserPreservingFocus(); renderJob();
    return operation;
  }
  function finishDialogOperation(operation) {
    if (app.dialogOperation !== operation) return false;
    app.dialogOperation = null;
    dialogBusy(false); renderBrowserPreservingFocus(); renderJob();
    return true;
  }
  function dialogFailure(error) {
    dialogBusy(false);
    if (!dialog.open) { openDialog('warning', `<h2 id="dialog-title">Review the result</h2><p id="dialog-description">${escape(error.message)}</p>`, [{ label: 'Close', style: 'secondary', action: closeDialog }]); return; }
    $('.dialog-progress')?.remove();
    const errorNode = document.createElement('div'); errorNode.className = 'dialog-error'; errorNode.setAttribute('role', 'alert'); errorNode.textContent = error.message;
    $('#dialog-content').append(errorNode);
    $('#dialog-actions').innerHTML = '<button class="button secondary" id="finish-dialog">Close</button>';
    $('#finish-dialog').addEventListener('click', closeDialog); $('#finish-dialog').focus();
  }
  function launchDialog() {
    if (!app.command || jobRunning()) return;
    const item = app.state.catalog.find(command => command.id === app.view);
    const payload = payloadFor(item);
    const canonical = app.command;
    const mode = $('#command-mode').textContent;
    const modeClass = $('#command-mode').className;
    openDialog('terminal', `<h2 id="dialog-title">Run in Terminal?</h2><p id="dialog-description">Opening Terminal starts this command. Commands with changes enabled may apply changes immediately.</p><div class="${escape(modeClass)}">${escape(mode)}</div><pre class="dialog-command">${escape(canonical)}</pre><p>${escape(item.note)}</p><p class="dialog-small">Actual outcomes appear in Terminal and Mole’s activity log.</p>`, [
      { label: 'Cancel', style: 'secondary', action: closeDialog },
      { label: 'Open in Terminal', action: async () => { const operation = beginDialogOperation('launch'); try { await api('/api/launch', payload); if (!finishDialogOperation(operation)) return; dialog.close(); toast('Opened in Terminal. Check its output.'); } catch (error) { if (finishDialogOperation(operation)) dialogFailure(error); } } },
    ]);
  }
  async function reviewTrash() {
    const ids = [...app.browser.selected];
    if (!ids.length || ids.length > 5 || jobRunning() || app.dialogBusy) return;
    openDialog('trash', '<h2 id="dialog-title">Review your selection</h2><p id="dialog-description">Mole is checking these items against its protection rules.</p><div class="dialog-progress"><span class="loading-orbit" aria-hidden="true"></span>Preparing the exact Trash plan…</div>', [{ label: 'Checking selection…', disabled: true }]);
    const operation = beginDialogOperation('plan');
    const generation = operation.generation;
    try {
      const plan = await api('/api/plan', { ids }, 210000);
      if (app.dialogOperation !== operation) return;
      const visible = dialog.open && generation === app.dialogGeneration;
      finishDialogOperation(operation);
      if (!visible) return;
      openDialog('trash', `<h2 id="dialog-title">Move to Trash?</h2><p id="dialog-description">Review these ${plan.paths.length === 1 ? 'exact item' : `${plan.paths.length} exact items`}. Only the paths below will be submitted to Mole.</p><ul class="dialog-paths">${plan.paths.map(path => `<li>${escape(path)}</li>`).join('')}</ul><p class="dialog-small">Items can be restored from Trash. Moving them does not free disk space until Trash is emptied. This review expires after two minutes.</p>`, [
        { label: 'Keep items', style: 'secondary', action: closeDialog },
        { label: `Move ${plan.paths.length === 1 ? 'item' : `${plan.paths.length} items`} to Trash`, style: 'danger', action: () => executeTrash(plan.receipt) },
      ]);
    } catch (error) { const visible = dialog.open && generation === app.dialogGeneration; if (finishDialogOperation(operation) && visible) dialogFailure(error); }
  }
  async function executeTrash(receipt) {
    app.measurements.clear(); renderMeasurement();
    const operation = beginDialogOperation('trash');
    $('#dialog-actions').lastElementChild.textContent = 'Moving to Trash…';
    try {
      const result = await api('/api/trash', { receipt }, 210000);
      if (!finishDialogOperation(operation)) return;
      const completed = result.completed || [];
      app.recentMoves.unshift(...completed.map(path => ({ path, time: Date.now() / 1000 })));
      app.recentMoves = app.recentMoves.slice(0, 20);
      app.measurements.clear();
      const remaining = result.remaining || [];
      const unconfirmed = result.unconfirmed || [];
      const notAttempted = result.not_attempted || [];
      const content = `<h2 id="dialog-title">${result.error ? 'Review the result' : 'Moved to Trash'}</h2><p id="dialog-description">${completed.length ? `Mole confirmed ${completed.length} ${completed.length === 1 ? 'item' : 'items'} moved to Trash.` : 'Mole did not confirm any items moved.'}</p>${completed.length ? `<ul class="dialog-paths">${completed.map(path => `<li>${escape(path)}</li>`).join('')}</ul>` : ''}${result.error ? `<div class="dialog-error">${escape(result.error)}</div>` : `<div class="dialog-result">${icon('check')}You can restore these items from your Mac’s Trash.</div>`}${unconfirmed.length ? `<p class="dialog-small">Move outcome unconfirmed. Check this folder and Trash before retrying.</p><ul class="dialog-paths">${unconfirmed.map(path => `<li>${escape(path)}</li>`).join('')}</ul>` : ''}${notAttempted.length ? `<p class="dialog-small">The Trash helper was not started for these paths.</p><ul class="dialog-paths">${notAttempted.map(path => `<li>${escape(path)}</li>`).join('')}</ul>` : ''}${remaining.length && !unconfirmed.length && !notAttempted.length ? `<p class="dialog-small">Refresh the folder and check Trash for these remaining items.</p><ul class="dialog-paths">${remaining.map(path => `<li>${escape(path)}</li>`).join('')}</ul>` : ''}<p class="dialog-small">Space is still occupied while items are in Trash.</p>`;
      openDialog(result.error ? 'warning' : 'check', content, [{ label: 'Done', action: closeDialog }]);
      app.browser.selected.clear();
      await loadBrowse(app.browser.path);
      await refreshState(false); renderRecovery(); renderMeasurement();
    } catch (error) { if (finishDialogOperation(operation)) { dialogFailure(new Error(error.message + ' No move outcome could be confirmed from this response. Check the folder and Trash before retrying.')); app.browser.selected.clear(); renderBrowser(); } }
  }
  async function copyCommand() {
    if (!app.command) return;
    try {
      await navigator.clipboard.writeText(app.command); toast('Command copied.');
    } catch (_) {
      const node = $('#command-preview'); const range = document.createRange(); range.selectNodeContents(node); const selection = window.getSelection(); selection.removeAllRanges(); selection.addRange(range); toast('Select the command and use ⌘C to copy it.');
    }
  }
  async function refreshState(notify = true) {
    const button = $('#refresh-state'); button.disabled = true;
    try { app.state = await api('/api/state'); setMachine(); if ($('#storage-zone')) $('#storage-zone').innerHTML = storage(); if (notify) toast('Disk information refreshed.'); }
    catch (error) { connection(false); if (notify) toast(error.message, true); }
    finally { button.disabled = false; }
  }
  async function initialize() {
    main.innerHTML = '<div class="initial-state"><span class="loading-orbit" aria-hidden="true"></span><p>Getting to know your Mac…</p></div>';
    try { app.state = await api('/api/state'); setMachine(); navigation(); navigate('overview'); await recoverActiveJob(); }
    catch (error) { connection(false); main.innerHTML = `<div class="error-panel">${icon('warning')}<h1>Let’s reconnect.</h1><p>${escape(error.message)}</p><p>The Mole launcher prints a local URL for this session. Open that full URL in this browser to reconnect.</p><button class="button secondary" id="retry-connect">${icon('refresh')}Try again</button></div>`; $('#retry-connect').addEventListener('click', initialize); }
  }

  document.addEventListener('click', event => {
    const view = event.target.closest('[data-view]');
    if (view) { event.preventDefault(); navigate(view.dataset.view); return; }
    const browse = event.target.closest('[data-browse-path]');
    if (browse && !app.dialogBusy) { loadBrowse(browse.dataset.browsePath, { focus: true }); return; }
    const page = event.target.closest('[data-page-offset]');
    if (page) { loadBrowse(app.browser.path, { preserveFilters: true, offset: Number(page.dataset.pageOffset), focus: true }); return; }
    const fileDetail = event.target.closest('[data-file-detail]');
    if (fileDetail) { fileDetails(fileDetail.dataset.fileDetail); return; }
    const native = event.target.closest('[data-native-action]');
    if (native) { nativeAction(native.dataset.nativeAction, native.dataset.entryId); return; }
    const mapPath = event.target.closest('[data-map-path]');
    if (mapPath) { measureFolder(mapPath.dataset.mapPath, true); return; }
    const mapFile = event.target.closest('[data-map-file]');
    if (mapFile) { const path = mapFile.dataset.mapFile; loadBrowse(path.slice(0, path.lastIndexOf('/'))); return; }
    const preview = event.target.closest('[data-start-preview]');
    if (preview) { previewCleanup(preview.dataset.startPreview); return; }
    if (event.target.closest('[data-open-trash]')) { nativeAction('trash'); return; }
    const appName = event.target.closest('[data-app-name]');
    if (appName) {
      const item = app.state.catalog.find(command => command.id === 'uninstall');
      const config = configFor(item);
      const names = config.fields.apps.split('\n').map(name => name.trim()).filter(Boolean);
      const name = appName.dataset.appName;
      if (names.includes(name)) config.fields.apps = names.filter(value => value !== name).join('\n');
      else if (names.length < 50) config.fields.apps = [...names, name].join('\n');
      else { toast('Review up to 50 exact app names per Terminal command.', true); return; }
      $('#field-apps').value = config.fields.apps;
      renderReport('apps'); generateCommand(item);
      const refreshedButton = [...document.querySelectorAll('[data-app-name]')].find(button => button.dataset.appName === name); refreshedButton?.focus({ preventScroll: true });
      return;
    }
    const sort = event.target.closest('[data-sort]');
    if (sort) { const key = sort.dataset.sort; app.browser.order = app.browser.sort === key ? -app.browser.order : key === 'name' ? 1 : -1; app.browser.sort = key; loadBrowse(app.browser.path, { preserveFilters: true }); return; }
    const report = event.target.closest('[data-report]');
    if (report) { loadReport(report.dataset.report); return; }
    const button = event.target.closest('button');
    if (!button) return;
    if (button.id === 'measure-folder') measureFolder();
    if (button.id === 'cancel-job') cancelJob();
    if (button.id === 'check-job' && app.job) pollJob(app.job.id);
    if (button.id === 'dismiss-job') { app.job = null; app.jobContext = null; renderJob(); }
    if (button.id === 'refresh-folder') { app.measurements.clear(); loadBrowse(app.browser.path || defaultPath(), { preserveFilters: true }); }
    if (button.id === 'clear-file-filters') loadBrowse(app.browser.path);
    if (button.hasAttribute('data-parent-folder') && app.browser.parent) loadBrowse(app.browser.parent);
    if (button.id === 'clear-selection') { app.browser.selected.clear(); renderBrowser(); }
    if (button.id === 'review-trash') reviewTrash();
    if (button.id === 'copy-command') copyCommand();
    if (button.id === 'launch-command') launchDialog();
  });
  document.addEventListener('input', event => {
    if (event.target.id === 'file-search') { app.browser.search = event.target.value; filterBrowse(true); return; }
    if (event.target.id === 'app-search') { app.reportFilters.apps.query = event.target.value; renderReport('apps'); return; }
    if (event.target.id === 'history-search') { app.reportFilters.history.query = event.target.value; renderReport('history'); return; }
    if (event.target.id === 'file-size-filter') { updateFileFilterDraft('minSize', event.target); return; }
    if (event.target.id === 'file-age-filter') { updateFileFilterDraft('olderDays', event.target); return; }
    if (event.target.matches('[data-field]')) {
      const item = app.state.catalog.find(command => command.id === app.view); configFor(item).fields[event.target.dataset.field] = event.target.value;
      if (item.id === 'uninstall' && event.target.dataset.field === 'apps') renderReport('apps');
      renderCommandWarning(item); generateCommand(item, true);
    }
  });
  document.addEventListener('change', event => {
    if (['file-size-filter', 'file-age-filter'].includes(event.target.id)) { updateFileFilterDraft(event.target.id === 'file-size-filter' ? 'minSize' : 'olderDays', event.target); return; }
    if (event.target.id === 'app-sort') { app.reportFilters.apps.sort = event.target.value; renderReport('apps'); return; }
    const historyFields = { 'history-command': 'command', 'history-outcome': 'outcome', 'history-since': 'since' };
    if (historyFields[event.target.id]) { app.reportFilters.history[historyFields[event.target.id]] = event.target.value; renderReport('history'); return; }
    if (event.target.id === 'file-type-filter') { app.browser.type = event.target.value; if (app.browser.type === 'folder') { app.browser.minSize = ''; app.browser.filterDrafts.minSize = ''; app.browser.filterErrors.minSize = ''; } filterBrowse(); return; }
    if (event.target.matches('[data-field]')) {
      const item = app.state.catalog.find(command => command.id === app.view);
      const config = configFor(item);
      if (config.fields[event.target.dataset.field] === event.target.value) return;
      config.fields[event.target.dataset.field] = event.target.value;
      if (item.id === 'uninstall' && event.target.dataset.field === 'apps') renderReport('apps');
      renderCommandWarning(item); generateCommand(item, true);
    }
    if (event.target.matches('[data-select-id]')) {
      const id = event.target.dataset.selectId;
      if (event.target.checked && app.browser.selected.size < 5) app.browser.selected.add(id); else app.browser.selected.delete(id);
      renderBrowser();
      const checkbox = document.querySelector(`[data-select-id="${CSS.escape(id)}"]`); checkbox?.focus();
    }
    if (event.target.matches('[data-flag]')) {
      const item = app.state.catalog.find(command => command.id === app.view); const config = configFor(item); const key = event.target.dataset.flag;
      if (event.target.checked) config.flags.add(key); else config.flags.delete(key);
      if ($('#field-interval')) $('#field-interval').disabled = !config.flags.has('watch');
      renderCommandWarning(item); generateCommand(item);
    }
  });
  $('#machine-icon').innerHTML = icon('laptop');
  $('#menu-button').innerHTML = icon('menu');
  $('#refresh-state').innerHTML = icon('refresh');
  $('#private-label').innerHTML = `${icon('lock')}<span>Only on this Mac</span>`;
  $('#dialog-close').innerHTML = icon('close');
  $('#menu-button').addEventListener('click', () => setNavOpen(!document.body.classList.contains('nav-open')));
  $('#sidebar-scrim').addEventListener('click', () => { setNavOpen(false); $('#menu-button').focus(); });
  $('#refresh-state').addEventListener('click', () => refreshState());
  $('#dialog-close').addEventListener('click', closeDialog);
  dialog.addEventListener('cancel', event => { if (app.dialogBusy) event.preventDefault(); });
  dialog.addEventListener('close', () => {
    if (dialog.open) return; // A queued close event must not invalidate a newer modal.
    app.dialogGeneration++;
    const operation = app.dialogOperation;
    if (operation?.kind === 'plan') finishDialogOperation(operation);
    else if (operation) {
      renderBrowserPreservingFocus(); renderJob();
      toast(operation.kind === 'trash' ? 'The confirmed Trash request is still running. Closing its dialog does not cancel moves.' : 'The confirmed Terminal handoff is still running.');
    } else dialogBusy(false);
    const focus = app.pendingFocus?.isConnected ? app.pendingFocus : app.pendingFocus?.id ? document.getElementById(app.pendingFocus.id) : null;
    if (focus) focus.focus({ preventScroll: true }); else main.focus({ preventScroll: true });
    app.pendingFocus = null;
  });
  document.addEventListener('keydown', event => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'f' && !dialog.open) { const search = $('#file-search') || $('#app-search') || $('#history-search'); if (search) { event.preventDefault(); setNavOpen(false); search.focus(); search.select(); } }
    if (event.altKey && event.key === 'ArrowUp' && !dialog.open && $('#browser-content') && app.browser.parent && !event.target.matches('input, textarea, select')) { event.preventDefault(); loadBrowse(app.browser.parent, { focus: true }); }
    if (event.key === 'Tab' && document.body.classList.contains('nav-open')) {
      const focusable = [...$('#sidebar').querySelectorAll('a[href], button:not(:disabled)')];
      const first = focusable[0], last = focusable.at(-1);
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
    if (event.key === 'Escape' && !dialog.open && !document.body.classList.contains('nav-open') && ['file-search', 'app-search', 'history-search'].includes(event.target.id) && event.target.value) { event.preventDefault(); event.target.value = ''; event.target.dispatchEvent(new Event('input', { bubbles: true })); }
    if (event.key === 'Escape' && !dialog.open && document.body.classList.contains('nav-open')) { setNavOpen(false); $('#menu-button').focus(); } });
  setNavOpen(false);
  initialize();
})();
