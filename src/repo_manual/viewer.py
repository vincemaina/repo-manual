"""The browser viewer: a single, no-build static page that renders the committed manual as an
interactive site. It is a thin, read-only client over data the tool already emits:

* ``manual.json``        — the systems/pages tree (sidebar nav),
* ``index/symbols.json`` — the function/class drill-down + per-symbol line ranges,
* ``index/edges.json``   — the import/call graph,
* the narrated Markdown + Mermaid pages,
* the source files themselves — shown with syntax highlighting and jump-to-symbol line ranges.

No Python deps (stdlib ``http.server`` serves it); Markdown (marked), Mermaid, the graph (cytoscape), and
source highlighting (highlight.js) all render client-side via CDN libraries. Customisable because it's
plain HTML/CSS/JS. Navigation uses the History API, so browser Back/Forward move between pages.
"""

from __future__ import annotations

from repo_manual.config import ManualConfig

VIEWER_NAME = "index.html"


def write_viewer(config: ManualConfig) -> None:
    """Write the viewer page into the output dir. Served at ``/<output>/index.html`` from the repo root,
    so the viewer can fetch its data (``manual.json``, ``index/*.json``) and the source files it shows."""
    config.output_path.mkdir(parents=True, exist_ok=True)
    (config.output_path / VIEWER_NAME).write_text(_VIEWER_HTML)


_VIEWER_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>repo-manual</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
<style>
  :root { --bg:#0d1117; --panel:#161b22; --fg:#e6edf3; --muted:#8b949e; --accent:#58a6ff; --border:#30363d; --lh:20px; --pad:12px; }
  * { box-sizing:border-box; }
  body { margin:0; font:14px/1.6 -apple-system,Segoe UI,Roboto,sans-serif; background:var(--bg); color:var(--fg); }
  header { padding:10px 20px; border-bottom:1px solid var(--border); display:flex; gap:16px; align-items:center; }
  header h1 { font-size:15px; margin:0; }
  header .sum { color:var(--muted); font-size:12px; }
  header .toggle { margin-left:auto; display:flex; gap:4px; }
  header button { background:var(--panel); color:var(--fg); border:1px solid var(--border); padding:5px 12px; border-radius:6px; cursor:pointer; font-size:13px; }
  header button.on { background:#1f6feb33; color:var(--accent); border-color:var(--accent); }
  #layout { display:flex; height:calc(100vh - 48px); }
  nav { width:300px; min-width:260px; overflow:auto; border-right:1px solid var(--border); padding:10px; background:var(--panel); }
  nav .sec { color:var(--muted); text-transform:uppercase; font-size:11px; letter-spacing:.5px; margin:14px 6px 6px; }
  nav a { display:flex; justify-content:space-between; gap:8px; padding:6px 8px; border-radius:6px; color:var(--fg); text-decoration:none; cursor:pointer; }
  nav a:hover { background:#1f2630; }
  nav a.active { background:#1f6feb33; color:var(--accent); }
  .badge { font-size:12px; }
  main { flex:1; overflow:auto; padding:24px 36px; }
  main .page { max-width:900px; }
  main h1 { border-bottom:1px solid var(--border); padding-bottom:8px; }
  main pre { background:var(--panel); padding:12px; border-radius:8px; overflow:auto; }
  main :not(pre) > code { background:#1f2630; padding:1px 5px; border-radius:4px; }
  main table { border-collapse:collapse; width:100%; } main th,main td { border:1px solid var(--border); padding:6px 10px; text-align:left; }
  main a { color:var(--accent); }
  .mermaid { background:var(--panel); border-radius:8px; padding:12px; margin:12px 0; text-align:center; }
  blockquote { border-left:3px solid var(--accent); margin:12px 0; padding:4px 14px; color:var(--muted); }
  details.syms { margin-top:28px; border-top:1px solid var(--border); padding-top:12px; }
  details.syms summary { cursor:pointer; color:var(--muted); user-select:none; }
  .sym { padding:5px 0; border-bottom:1px solid #21262d; }
  .sym .nm { color:var(--accent); text-decoration:none; cursor:pointer; font-family:ui-monospace,monospace; }
  .sym .sig { color:var(--muted); font-family:ui-monospace,monospace; font-size:12px; }
  .sym .ln { color:var(--muted); font-size:12px; float:right; }
  /* graph view */
  #graphView { display:none; flex:1; position:relative; }
  #cy { width:100%; height:100%; }
  .gpanel { position:absolute; top:12px; left:12px; background:var(--panel); border:1px solid var(--border); border-radius:8px; padding:10px 12px; max-width:260px; z-index:5; }
  .gpanel h3 { margin:0 0 6px; font-size:12px; color:var(--muted); text-transform:uppercase; letter-spacing:.5px; }
  .gpanel button { font-size:12px; margin:2px 4px 2px 0; }
  .legend { font-size:12px; margin-top:8px; }
  .legend .row { display:flex; align-items:center; gap:6px; padding:1px 0; }
  .legend .sw { width:10px; height:10px; border-radius:2px; display:inline-block; }
  #ginfo { position:absolute; bottom:12px; left:12px; background:var(--panel); border:1px solid var(--border); border-radius:8px; padding:10px 12px; max-width:340px; z-index:5; display:none; }
  #ginfo .t { font-family:ui-monospace,monospace; color:var(--accent); word-break:break-all; }
  #ginfo .r { color:var(--muted); font-size:12px; }
  #ginfo a { color:var(--accent); cursor:pointer; }
  .hint { color:var(--muted); font-size:12px; }
  /* source view */
  #srcOverlay { display:none; position:fixed; inset:0; z-index:50; flex-direction:column; background:var(--bg); }
  .srcbar { display:flex; gap:12px; align-items:center; padding:10px 16px; border-bottom:1px solid var(--border); }
  .srcbar .t { font-family:ui-monospace,monospace; color:var(--accent); }
  .srcbar .sub { color:var(--muted); font-size:12px; }
  .srcbar .right { margin-left:auto; display:flex; gap:10px; align-items:center; }
  .srcbar a { color:var(--muted); font-size:12px; text-decoration:none; }
  .srcbar button { background:var(--panel); color:var(--fg); border:1px solid var(--border); border-radius:6px; cursor:pointer; padding:4px 10px; }
  #srcScroll { flex:1; overflow:auto; display:flex; background:var(--panel); }
  .srcgutter { margin:0; padding:var(--pad) 8px var(--pad) 14px; text-align:right; color:#6e7681; font:12.5px/var(--lh) ui-monospace,monospace; user-select:none; background:#0e131a; white-space:pre; }
  .srcgutter .hl { color:var(--accent); font-weight:600; }
  .srcmain { position:relative; flex:1; }
  #srcBand { display:none; position:absolute; left:0; right:0; background:#1f6feb22; border-left:2px solid var(--accent); pointer-events:none; }
  .srccode { margin:0; padding:var(--pad) 16px; font:12.5px/var(--lh) ui-monospace,monospace; }
  .srccode code.hljs { background:transparent !important; padding:0; }
</style>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/cytoscape@3/dist/cytoscape.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
</head>
<body>
<header>
  <h1>&#128216; <span id="title">repo-manual</span></h1>
  <span class="sum" id="sum"></span>
  <span class="toggle">
    <button id="btnManual" class="on" onclick="showManual()">&#128214; Manual</button>
    <button id="btnGraph" onclick="showGraph()">&#128376; Graph</button>
  </span>
</header>
<div id="layout">
  <nav id="nav"></nav>
  <main id="main"><div class="page">Loading&hellip;</div></main>
  <div id="graphView">
    <div class="gpanel">
      <h3>Graph</h3>
      <div>
        <button id="mImports" class="on" onclick="setMode('imports')">Imports (files)</button>
        <button id="mCalls" onclick="setMode('calls')">Calls (functions)</button>
      </div>
      <div><button onclick="relayout()">Re-layout</button><button onclick="clearHi()">Clear</button></div>
      <div class="hint">Click a node: blast radius (what it affects vs. depends on).</div>
      <div class="legend" id="legend"></div>
    </div>
    <div id="cy"></div>
    <div id="ginfo"></div>
  </div>
</div>
<div id="srcOverlay">
  <div class="srcbar">
    <span class="t" id="srcTitle"></span><span class="sub" id="srcSub"></span>
    <span class="right"><a id="srcRaw" target="_blank">raw &#8599;</a><button onclick="closeSource()">&#10005; close (Esc)</button></span>
  </div>
  <div id="srcScroll">
    <pre class="srcgutter" id="srcGutter"></pre>
    <div class="srcmain"><div id="srcBand"></div><pre class="srccode"><code id="srcCode"></code></pre></div>
  </div>
</div>
<script type="module">
import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
mermaid.initialize({ startOnLoad:false, theme:'dark', securityLevel:'loose' });

const $ = s => document.querySelector(s);
const BADGE = { fresh:'✅', stale:'⚠️', pending:'○' };
const PALETTE = ['#58a6ff','#3fb950','#d29922','#db61a2','#a371f7','#f78166','#56d4dd','#e3b341','#7ee787','#ffa657'];
const LH = 20, PAD = 12;  // must match --lh / --pad in CSS for the source highlight band

let MANUAL = null, PAGES = {}, SYMBOLS = [], SYMBYID = {}, FILES = [], EDGES = [];
let F2P = {}, PAGECOLOR = {}, CURRENT = null;
let cy = null, gmode = 'imports', graphBuilt = false;

// ---- source view (syntax-highlighted, jump-to-symbol) ----
function lang(file){
  const ext = file.split('.').pop();
  return { py:'python', ts:'typescript', tsx:'typescript', js:'javascript', jsx:'javascript',
           sql:'sql', go:'go', rs:'rust', java:'java', json:'json', md:'markdown' }[ext] || 'plaintext';
}
window.openSource = async (file, start, end) => {
  start = start || 0; end = end || start;
  const txt = await fetch('../' + file).then(r => r.text());
  const lines = txt.split('\n');
  $('#srcGutter').innerHTML = lines.map((_, i) => {
    const ln = i + 1; const hot = start && ln >= start && ln <= end;
    return '<span' + (hot ? ' class="hl"' : '') + '>' + ln + '</span>';
  }).join('\n');
  const code = $('#srcCode'); code.className = 'language-' + lang(file); code.textContent = txt;
  delete code.dataset.highlighted; hljs.highlightElement(code);
  const band = $('#srcBand');
  if (start){ band.style.display = 'block'; band.style.top = (PAD + (start - 1) * LH) + 'px';
    band.style.height = ((end - start + 1) * LH) + 'px'; } else band.style.display = 'none';
  $('#srcTitle').textContent = file; $('#srcSub').textContent = start ? ' :' + start + '-' + end : '';
  $('#srcRaw').href = '../' + file;
  $('#srcOverlay').style.display = 'flex';
  requestAnimationFrame(() => { $('#srcScroll').scrollTop = start ? Math.max(0, PAD + (start - 1) * LH - 90) : 0; });
};
window.closeSource = () => { $('#srcOverlay').style.display = 'none'; };
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeSource(); });

// intercept links to source files inside rendered Markdown so they open the highlighted view
function interceptSourceLinks(container){
  container.querySelectorAll('a[href]').forEach(a => {
    const m = /^(?:\.\.\/)+(.+\.(?:py|ts|tsx|js|jsx|sql|go|rs|java))(?:#L?(\d+))?$/.exec(a.getAttribute('href'));
    if (m) a.addEventListener('click', ev => { ev.preventDefault(); openSource(m[1], +m[2] || 0, +m[2] || 0); });
  });
}

// ---- manual view ----
function stripFront(md){
  if (md.startsWith('---')) { const e = md.indexOf('\n---', 3); if (e >= 0) return md.slice(md.indexOf('\n', e + 1) + 1); }
  return md;
}
async function renderPage(p){
  const md = await fetch('manual/' + p.section + '/' + p.id + '.md').then(r => r.text());
  const main = $('#main');
  const page = document.createElement('div'); page.className = 'page';
  page.innerHTML = marked.parse(stripFront(md));
  main.replaceChildren(page);
  page.querySelectorAll('code.language-mermaid').forEach(c => {
    const d = document.createElement('div'); d.className = 'mermaid'; d.textContent = c.textContent;
    c.closest('pre').replaceWith(d);
  });
  try { await mermaid.run({ nodes: page.querySelectorAll('.mermaid') }); } catch (e) {}
  interceptSourceLinks(page);

  const files = (p.relevant_files || []).map(f => f.path);
  const syms = SYMBOLS.filter(s => files.includes(s.file) && s.kind !== 'module');
  if (syms.length){
    const det = document.createElement('details'); det.className = 'syms'; det.open = syms.length <= 18;
    det.appendChild(Object.assign(document.createElement('summary'),
      { textContent: syms.length + ' functions / classes — click to view the source' }));
    syms.forEach(s => {
      const row = document.createElement('div'); row.className = 'sym';
      const a = document.createElement('a'); a.className = 'nm'; a.textContent = s.qualname;
      a.onclick = () => openSource(s.file, s.line_start, s.line_end);
      const sig = document.createElement('span'); sig.className = 'sig'; sig.textContent = s.signature || '';
      const ln = document.createElement('span'); ln.className = 'ln';
      ln.textContent = s.file.split('/').pop() + ':' + s.line_start + '-' + s.line_end;
      row.append(a, ' ', sig, ln); det.appendChild(row);
    });
    page.appendChild(det);
  }
  main.scrollTop = 0;
}
function markActive(id){
  document.querySelectorAll('nav a').forEach(a => a.classList.toggle('active', a.dataset.id === id));
}
// History-API routing: real Back/Forward between pages (the hash is the page id).
async function navTo(id, push){
  const p = PAGES[id]; if (!p) return;
  CURRENT = id; showManual(); markActive(id);
  if (push) history.pushState({ id }, '', '#' + id);
  await renderPage(p);
}
window.addEventListener('popstate', e => {
  closeSource();
  const id = (e.state && e.state.id) || location.hash.slice(1);
  if (PAGES[id]) navTo(id, false);
});

// ---- view toggle ----
window.showManual = () => {
  $('#nav').style.display = ''; $('#main').style.display = ''; $('#graphView').style.display = 'none';
  $('#btnManual').classList.add('on'); $('#btnGraph').classList.remove('on');
};
window.showGraph = () => {
  $('#nav').style.display = 'none'; $('#main').style.display = 'none'; $('#graphView').style.display = 'flex';
  $('#btnGraph').classList.add('on'); $('#btnManual').classList.remove('on');
  if (!graphBuilt) { buildGraph(); graphBuilt = true; }
};

// ---- graph ----
function pageIdForFile(file){
  const ps = F2P[file] || [];
  const sys = ps.find(x => x.section !== 'overview');
  return (sys || ps[0] || {}).id;
}
function elementsFor(mode){
  const els = [];
  if (mode === 'imports'){
    FILES.forEach(f => els.push({ data:{ id:f.path, label:f.path.split('/').pop(), color:PAGECOLOR[pageIdForFile(f.path)] || '#888' } }));
    EDGES.filter(e => e.kind === 'imports').forEach((e, i) => els.push({ data:{ id:'e'+i, source:e.src, target:e.dst } }));
  } else {
    const calls = EDGES.filter(e => e.kind === 'calls');
    const used = new Set(); calls.forEach(e => { used.add(e.src); used.add(e.dst); });
    used.forEach(id => { const s = SYMBYID[id]; if (s) els.push({ data:{ id, label:s.qualname, color:PAGECOLOR[pageIdForFile(s.file)] || '#888' } }); });
    calls.forEach((e, i) => els.push({ data:{ id:'c'+i, source:e.src, target:e.dst } }));
  }
  return els;
}
function layoutFor(mode){
  return mode === 'imports'
    ? { name:'breadthfirst', directed:true, spacingFactor:1.3, padding:30 }
    : { name:'cose', animate:false, nodeRepulsion:9000, idealEdgeLength:70, padding:30 };
}
function buildGraph(){
  cy = cytoscape({
    container: $('#cy'),
    elements: elementsFor(gmode),
    style: [
      { selector:'node', style:{ 'background-color':'data(color)', 'label':'data(label)', 'font-size':9,
        'color':'#c9d1d9', 'text-valign':'bottom', 'text-margin-y':3, 'width':18, 'height':18 } },
      { selector:'edge', style:{ 'width':1, 'line-color':'#3b424b', 'target-arrow-color':'#3b424b',
        'target-arrow-shape':'triangle', 'curve-style':'bezier', 'arrow-scale':0.8 } },
      { selector:'.faded', style:{ 'opacity':0.12 } },
      { selector:'node.root', style:{ 'border-width':3, 'border-color':'#fff', 'width':24, 'height':24 } },
      { selector:'.down', style:{ 'line-color':'#58a6ff', 'target-arrow-color':'#58a6ff' } },
      { selector:'node.down', style:{ 'border-width':2, 'border-color':'#58a6ff' } },
      { selector:'.up', style:{ 'line-color':'#f78166', 'target-arrow-color':'#f78166' } },
      { selector:'node.up', style:{ 'border-width':2, 'border-color':'#f78166' } },
    ],
    layout: layoutFor(gmode),
  });
  cy.on('tap', 'node', e => highlight(e.target));
  cy.on('tap', e => { if (e.target === cy) clearHi(); });
}
function highlight(n){
  cy.elements().addClass('faded');
  const down = n.successors(), up = n.predecessors();
  n.removeClass('faded').addClass('root');
  down.removeClass('faded').addClass('down');
  up.removeClass('faded').addClass('up');
  const isImp = gmode === 'imports';
  const info = $('#ginfo'); info.style.display = 'block';
  info.innerHTML = '<div class="t">' + n.data('label') + '</div>'
    + '<div class="r">' + (isImp ? 'imports' : 'calls') + ' ' + down.nodes().length
    + ' &middot; ' + (isImp ? 'imported by' : 'called by') + ' ' + up.nodes().length + ' <b>(blast radius)</b></div>'
    + '<div class="r"><a id="goPage">open page &rarr;</a> &nbsp; <a id="goSrc">view source &rarr;</a></div>';
  const sym = isImp ? null : SYMBYID[n.id()];
  const file = isImp ? n.id() : (sym || {}).file;
  const pid = pageIdForFile(file);
  $('#goPage').onclick = () => { if (PAGES[pid]) navTo(pid, true); };
  $('#goSrc').onclick = () => openSource(file, sym ? sym.line_start : 0, sym ? sym.line_end : 0);
}
window.clearHi = () => { if (cy) cy.elements().removeClass('faded root up down'); $('#ginfo').style.display = 'none'; };
window.relayout = () => { if (cy) cy.layout(layoutFor(gmode)).run(); };
window.setMode = (m) => {
  gmode = m; $('#mImports').classList.toggle('on', m === 'imports'); $('#mCalls').classList.toggle('on', m === 'calls');
  if (cy) cy.destroy(); buildGraph();
};

// ---- boot ----
async function boot(){
  MANUAL = await fetch('manual.json').then(r => r.json());
  PAGES = MANUAL.pages;
  SYMBOLS = await fetch('index/symbols.json').then(r => r.json()).then(d => d.symbols).catch(() => []);
  FILES = await fetch('index/files.json').then(r => r.json()).then(d => d.files).catch(() => []);
  EDGES = await fetch('index/edges.json').then(r => r.json()).then(d => d.edges).catch(() => []);
  SYMBOLS.forEach(s => SYMBYID[s.id] = s);

  let ci = 0;
  MANUAL.sections.forEach(sec => (sec.page_ids || []).forEach(id => {
    PAGECOLOR[id] = PALETTE[ci++ % PALETTE.length];
    const p = PAGES[id]; if (!p) return;
    (p.relevant_files || []).forEach(r => (F2P[r.path] = F2P[r.path] || []).push({ section:p.section, id }));
  }));

  const counts = { fresh:0, stale:0, pending:0 };
  Object.values(PAGES).forEach(p => counts[p.status] = (counts[p.status] || 0) + 1);
  $('#sum').textContent = counts.fresh + ' fresh · ' + counts.stale + ' stale · ' + counts.pending + ' pending';

  const nav = $('#nav'); let first = null;
  MANUAL.sections.forEach(sec => {
    const h = document.createElement('div'); h.className = 'sec'; h.textContent = sec.title; nav.appendChild(h);
    (sec.page_ids || []).forEach(id => {
      const p = PAGES[id]; if (!p) return;
      const a = document.createElement('a'); a.dataset.id = id;
      a.innerHTML = '<span>' + p.title + '</span><span class="badge">' + (BADGE[p.status] || '') + '</span>';
      a.onclick = () => navTo(id, true); nav.appendChild(a);
      if (!first) first = id;
    });
  });

  const legend = $('#legend');
  MANUAL.sections.forEach(sec => (sec.page_ids || []).forEach(id => {
    const p = PAGES[id]; if (!p || p.section === 'overview') return;
    const row = document.createElement('div'); row.className = 'row';
    row.innerHTML = '<span class="sw" style="background:' + (PAGECOLOR[id] || '#888') + '"></span>' + p.title;
    legend.appendChild(row);
  }));

  const startId = (location.hash.slice(1) && PAGES[location.hash.slice(1)]) ? location.hash.slice(1) : first;
  if (startId){ history.replaceState({ id:startId }, '', '#' + startId); navTo(startId, false); }
}
boot();
</script>
</body>
</html>
"""
