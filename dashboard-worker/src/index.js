// ============================================================
// Mr. Oldverdict — Cloudflare Worker v1.1
// Dashboard + API for Modal pipeline
// ============================================================

const BEARER = 'mroldverdict_xK9mP1978';

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (request.method === 'OPTIONS') return cors(null, 204);

    if (url.pathname === '/health') {
      return cors({ status: 'ok', version: 'v1.1',
                    time: new Date().toISOString() });
    }

    if (url.pathname === '/' || url.pathname === '/dashboard') {
      return new Response(buildDashboard(), {
        headers: { 'content-type': 'text/html;charset=UTF-8',
                   'cache-control': 'no-store' }
      });
    }

    if (url.pathname === '/scripts') {
      try {
        const rows = await sbGet(env,
          'scripts?order=created_at.desc&limit=60' +
          '&select=id,setup,category,expression,published,published_at,created_at');
        return cors(rows);
      } catch (e) { return cors({ error: e.message }, 500); }
    }

    if (url.pathname === '/videos') {
      try {
        const rows = await sbGet(env,
          'videos?order=created_at.desc&limit=60' +
          '&select=id,script_id,video_url,voice_file_url,image_url,created_at,' +
          'scripts(setup,category,expression,published)');
        return cors(rows);
      } catch (e) { return cors({ error: e.message }, 500); }
    }

    if (url.pathname === '/topics') {
      try {
        const rows = await sbGet(env,
          'topics?order=engagement_score.desc&limit=100' +
          '&select=id,raw_topic,category,source,engagement_score,' +
          'blacklist_cleared,used,created_at');
        return cors(rows);
      } catch (e) { return cors({ error: e.message }, 500); }
    }

    if (url.pathname === '/stats') {
      try {
        const [scripts, videos, topics] = await Promise.all([
          sbGet(env, 'scripts?select=id,published,category'),
          sbGet(env, 'videos?select=id,video_url'),
          sbGet(env, 'topics?used=eq.false&select=id'),
        ]);
        return cors({
          total_scripts:    scripts.length,
          published:        scripts.filter(s => s.published).length,
          unpublished:      scripts.filter(s => !s.published).length,
          videos_assembled: videos.filter(v => v.video_url).length,
          topics_ready:     topics.length,
        });
      } catch (e) { return cors({ error: e.message }, 500); }
    }

    // ── DIAGNOSTICS — tells the dashboard what's configured ──
    if (url.pathname === '/diagnostics') {
      const supaOk = !!(env.SUPABASE_URL && env.SUPABASE_ANON_KEY);
      const modalOk = !!(env.MODAL_PIPELINE_URL);
      let supaTest = 'not_tested';
      if (supaOk) {
        try {
          const r = await sbGet(env, 'scripts?limit=1&select=id');
          supaTest = Array.isArray(r) ? 'ok' : 'error';
        } catch (e) { supaTest = 'error: ' + e.message.slice(0, 60); }
      }
      return cors({
        supabase_url_set:      !!env.SUPABASE_URL,
        supabase_key_set:      !!env.SUPABASE_ANON_KEY,
        supabase_svc_key_set:  !!env.SUPABASE_SERVICE_ROLE_KEY,
        modal_url_set:         !!env.MODAL_PIPELINE_URL,
        modal_url:             env.MODAL_PIPELINE_URL || 'NOT SET',
        supabase_test:         supaTest,
      });
    }

    if (url.pathname === '/run-pipeline' && request.method === 'POST') {
      const modalUrl = (env.MODAL_PIPELINE_URL || '').trim().replace(/\/$/, '');
      if (!modalUrl) return cors({ error: 'MODAL_PIPELINE_URL not set in Cloudflare env vars' }, 500);
      try {
        const r = await fetch(modalUrl + '/run-pipeline', {
          method: 'POST',
          headers: { 'Authorization': 'Bearer ' + BEARER,
                     'Content-Type': 'application/json' },
          signal: AbortSignal.timeout(30000)
        });
        const text = await r.text();
        return cors({ status: r.ok ? 'triggered' : 'error',
                      modal_status: r.status, body: text.slice(0, 300) });
      } catch (e) { return cors({ error: e.message }, 500); }
    }

    if (url.pathname === '/assemble' && request.method === 'POST') {
      const modalUrl = (env.MODAL_PIPELINE_URL || '').trim().replace(/\/$/, '');
      if (!modalUrl) return cors({ error: 'MODAL_PIPELINE_URL not set' }, 500);
      try {
        const body      = await request.json().catch(() => ({}));
        const script_id = body.script_id;
        if (!script_id) return cors({ error: 'script_id required' }, 400);
        const r = await fetch(modalUrl + '/assemble', {
          method: 'POST',
          headers: { 'Authorization': 'Bearer ' + BEARER,
                     'Content-Type': 'application/json' },
          body: JSON.stringify({ script_id }),
          signal: AbortSignal.timeout(30000)
        });
        const text = await r.text();
        return cors({ status: r.ok ? 'triggered' : 'error',
                      script_id, body: text.slice(0, 300) });
      } catch (e) { return cors({ error: e.message }, 500); }
    }

    if (url.pathname === '/publish' && request.method === 'POST') {
      const modalUrl = (env.MODAL_PIPELINE_URL || '').trim().replace(/\/$/, '');
      if (!modalUrl) return cors({ error: 'MODAL_PIPELINE_URL not set' }, 500);
      try {
        const body      = await request.json().catch(() => ({}));
        const script_id = body.script_id;
        if (!script_id) return cors({ error: 'script_id required' }, 400);
        const r = await fetch(modalUrl + '/publish', {
          method: 'POST',
          headers: { 'Authorization': 'Bearer ' + BEARER,
                     'Content-Type': 'application/json' },
          body: JSON.stringify({ script_id }),
          signal: AbortSignal.timeout(120000)
        });
        const text = await r.text();
        return cors({ status: r.ok ? 'published' : 'error',
                      script_id, body: text.slice(0, 300) });
      } catch (e) { return cors({ error: e.message }, 500); }
    }

    if (url.pathname === '/run-ingestion' && request.method === 'POST') {
      try {
        const r    = await fetch('https://ingestion.rkinfoarch.workers.dev/', {
          method: 'POST',
          headers: { 'Authorization': 'Bearer ' + BEARER },
          signal: AbortSignal.timeout(30000)
        });
        const text = await r.text();
        let result;
        try { result = JSON.parse(text); } catch (_) { result = text.slice(0, 300); }
        return cors({ status: r.ok ? 'triggered' : 'error',
                      http_status: r.status, result });
      } catch (e) { return cors({ error: e.message }, 500); }
    }

    if (url.pathname === '/test-modal') {
      const modalUrl = (env.MODAL_PIPELINE_URL || '').trim().replace(/\/$/, '');
      if (!modalUrl) return cors({ error: 'MODAL_PIPELINE_URL not set in Cloudflare env vars', ok: false });
      try {
        const r    = await fetch(modalUrl + '/', { signal: AbortSignal.timeout(15000) });
        const text = await r.text();
        return cors({ url: modalUrl, status: r.status,
                      response: text.slice(0, 400), ok: r.ok });
      } catch (e) {
        return cors({ url: modalUrl, error: e.message, ok: false });
      }
    }

    if (url.pathname === '/video-status') {
      const script_id = url.searchParams.get('script_id');
      if (!script_id) return cors({ error: 'script_id required' }, 400);
      try {
        const rows = await sbGet(env,
          'videos?script_id=eq.' + script_id +
          '&select=video_url,voice_file_url,image_url');
        if (rows.length && rows[0].video_url)
          return cors({ ready: true, video_url: rows[0].video_url });
        return cors({ ready: false });
      } catch (e) { return cors({ error: e.message }, 500); }
    }

    return cors({ error: 'route_not_found' }, 404);
  },

  async scheduled(event, env, ctx) {
    if (env.MODAL_PIPELINE_URL)
      fetch(env.MODAL_PIPELINE_URL + '/').catch(() => {});
  }
};

function sbh(env) {
  return {
    apikey:         env.SUPABASE_ANON_KEY,
    Authorization:  'Bearer ' + (env.SUPABASE_SERVICE_ROLE_KEY || env.SUPABASE_ANON_KEY),
    'Content-Type': 'application/json'
  };
}
async function sbGet(env, ep) {
  const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + ep, { headers: sbh(env) });
  if (!r.ok) throw new Error('Supabase ' + r.status + ': ' + ep.slice(0, 40));
  return r.json();
}
function cors(data, status) {
  return new Response(JSON.stringify(data, null, 2), {
    status: status || 200,
    headers: {
      'content-type':                'application/json',
      'Access-Control-Allow-Origin':  '*',
      'Access-Control-Allow-Headers': '*',
      'Access-Control-Allow-Methods': 'GET,POST,OPTIONS,PATCH'
    }
  });
}

// ============================================================
// DASHBOARD
// ============================================================
function buildDashboard() {
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Mr. Oldverdict</title>
<link href="https://fonts.googleapis.com/css2?family=IM+Fell+English:ital@0;1&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#f5f0e8;
  --surface:#fffdf7;
  --surface2:#f0ebe0;
  --border:rgba(100,80,50,0.12);
  --border2:rgba(100,80,50,0.22);
  --text:#2a2218;
  --muted:#8a7a60;
  --gold:#9a6820;
  --gold-light:#c8960a;
  --green:#2e6e2e;
  --red:#8a2e20;
  --blue:#2a5080;
  --purple:#5a3888;
  --font:'IM Fell English',serif;
  --mono:'DM Mono',monospace;
}
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%}
body{background:var(--bg);color:var(--text);font-family:var(--font);
  display:flex;flex-direction:column;overflow:hidden}

.topbar{
  position:relative;z-index:10;display:flex;align-items:center;
  justify-content:space-between;padding:0 24px;height:52px;
  border-bottom:1px solid var(--border2);
  background:var(--surface);flex-shrink:0;
}
.logo{font-size:1.1rem;color:var(--gold);letter-spacing:0.02em}
.logo-sub{font-family:var(--mono);font-size:.52rem;color:var(--muted);
  letter-spacing:.15em;text-transform:uppercase;margin-top:1px}
.topbar-nav{display:flex;align-items:center;gap:2px}
.nav-btn{
  padding:5px 14px;border-radius:5px;border:none;
  background:transparent;font-family:var(--font);font-size:.82rem;
  color:var(--muted);cursor:pointer;transition:all .15s;
}
.nav-btn:hover{color:var(--text)}
.nav-btn.active{color:var(--gold);border-bottom:2px solid var(--gold)}
.topbar-right{font-family:var(--mono);font-size:.58rem;color:var(--muted)}

.pages{flex:1;overflow:hidden}
.page{display:none;height:100%;overflow-y:auto;padding:22px}
.page.active{display:block}
.page::-webkit-scrollbar{width:4px}
.page::-webkit-scrollbar-thumb{background:var(--border2);border-radius:2px}

/* Connection banner */
.conn-banner{
  display:flex;gap:8px;align-items:center;flex-wrap:wrap;
  padding:8px 14px;border-radius:6px;margin-bottom:16px;
  font-family:var(--mono);font-size:.62rem;
  background:var(--surface2);border:1px solid var(--border2);
}
.conn-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.conn-ok{background:var(--green)}
.conn-err{background:var(--red)}
.conn-unk{background:var(--muted)}
.conn-item{display:flex;align-items:center;gap:5px;color:var(--muted)}

/* Stats */
.stats{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:18px}
.stat{
  background:var(--surface);border:1px solid var(--border2);
  border-radius:7px;padding:14px 16px;
}
.stat-val{font-size:2rem;color:var(--gold);
  letter-spacing:-0.02em;line-height:1;margin-bottom:3px}
.stat-lbl{font-family:var(--mono);font-size:.56rem;color:var(--muted);
  text-transform:uppercase;letter-spacing:.08em}

/* Actions */
.actions{display:flex;gap:8px;margin-bottom:18px;flex-wrap:wrap}
.btn{
  display:inline-flex;align-items:center;gap:5px;
  padding:7px 16px;border-radius:5px;border:none;
  font-family:var(--font);font-size:.82rem;cursor:pointer;
  transition:all .15s;white-space:nowrap;
}
.btn:disabled{opacity:.4;cursor:not-allowed}
.btn-gold{background:var(--gold);color:#fff}
.btn-gold:hover:not(:disabled){background:var(--gold-light)}
.btn-ghost{
  background:var(--surface);color:var(--text);
  border:1px solid var(--border2);
}
.btn-ghost:hover:not(:disabled){border-color:var(--gold);color:var(--gold)}
.btn-red{background:rgba(138,46,32,.08);color:var(--red);border:1px solid rgba(138,46,32,.2)}
.btn-red:hover:not(:disabled){background:rgba(138,46,32,.15)}
.btn-green{background:rgba(46,110,46,.08);color:var(--green);border:1px solid rgba(46,110,46,.2)}
.btn-green:hover:not(:disabled){background:rgba(46,110,46,.15)}

/* Layout */
.two-col{display:grid;grid-template-columns:1fr 290px;gap:14px;align-items:start}
.panel{
  background:var(--surface);border:1px solid var(--border2);
  border-radius:7px;overflow:hidden;margin-bottom:14px;
}
.panel-head{
  padding:10px 16px;border-bottom:1px solid var(--border);
  display:flex;align-items:center;justify-content:space-between;
  background:var(--surface2);
}
.panel-title{font-size:.62rem;font-family:var(--mono);
  text-transform:uppercase;letter-spacing:.12em;color:var(--muted)}
.panel-sub{font-family:var(--mono);font-size:.58rem;color:var(--muted)}

/* Tabs */
.tabs{display:flex;gap:2px;padding:7px 12px;border-bottom:1px solid var(--border);
  background:var(--surface2)}
.tab{
  padding:4px 12px;border-radius:4px;border:1px solid transparent;
  background:transparent;font-family:var(--mono);font-size:.63rem;
  color:var(--muted);cursor:pointer;transition:all .12s;
}
.tab:hover{color:var(--text);background:var(--bg)}
.tab.active{color:var(--gold);border-color:var(--border2);background:var(--surface)}

/* Script rows */
.script-row{
  display:grid;grid-template-columns:1fr 100px 90px 60px 60px;
  gap:8px;padding:10px 16px;border-bottom:1px solid var(--border);
  align-items:center;transition:background .1s;
}
.script-row:hover{background:var(--surface2)}
.script-row:last-child{border-bottom:none}
.script-setup{font-size:.82rem;color:var(--text);line-height:1.35;margin-bottom:2px}
.script-meta{
  font-family:var(--mono);font-size:.58rem;color:var(--muted);
  display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin-top:2px;
}

/* Badges */
.badge{
  display:inline-flex;align-items:center;
  padding:2px 7px;border-radius:3px;
  font-family:var(--mono);font-size:.58rem;
}
.b-pub{background:rgba(46,110,46,.1);color:var(--green);border:1px solid rgba(46,110,46,.2)}
.b-unpub{background:rgba(138,138,138,.1);color:var(--muted);border:1px solid var(--border2)}
.b-assembled{background:rgba(42,80,128,.1);color:var(--blue);border:1px solid rgba(42,80,128,.2)}
.b-noassembly{background:rgba(138,46,32,.06);color:var(--red);border:1px solid rgba(138,46,32,.15)}

.cat-badge{
  font-family:var(--mono);font-size:.58rem;padding:1px 6px;
  border-radius:3px;
}
.expr-dot{
  width:6px;height:6px;border-radius:50%;
  display:inline-block;margin-right:3px;flex-shrink:0;
}
.time-cell{font-family:var(--mono);font-size:.58rem;color:var(--muted);text-align:right}
.action-cell{display:flex;gap:4px;justify-content:flex-end}
.mini-btn{
  padding:3px 9px;border-radius:3px;border:1px solid var(--border2);
  background:transparent;font-family:var(--mono);font-size:.57rem;
  color:var(--muted);cursor:pointer;transition:all .12s;
}
.mini-btn:hover{border-color:var(--gold);color:var(--gold)}
.mini-btn:disabled{opacity:.35;cursor:not-allowed}
.mini-btn.pub{border-color:rgba(46,110,46,.3);color:var(--green)}
.mini-btn.pub:hover{background:rgba(46,110,46,.08)}

/* Topic rows */
.topic-row{
  padding:10px 16px;border-bottom:1px solid var(--border);transition:background .1s;
}
.topic-row:hover{background:var(--surface2)}
.topic-row:last-child{border-bottom:none}
.topic-text{font-size:.8rem;color:var(--text);margin-bottom:3px;line-height:1.35}
.topic-foot{display:flex;align-items:center;justify-content:space-between}
.score-pill{font-family:var(--mono);font-size:.58rem;padding:2px 6px;border-radius:3px;}
.sc-hi{background:rgba(46,110,46,.1);color:var(--green)}
.sc-lo{background:rgba(138,46,32,.08);color:var(--red)}

/* Debug box */
.debug-box{
  border-radius:5px;padding:9px 13px;
  font-family:var(--mono);font-size:.63rem;
  line-height:1.8;margin-bottom:14px;
  border:1px solid var(--border2);background:var(--surface);
  color:var(--text);
}
.dg{color:var(--green);font-weight:500}
.dr{color:var(--red);font-weight:500}
.dk{color:var(--gold);font-weight:500}
.dm{color:var(--muted)}

/* Empty */
.empty{padding:32px 20px;text-align:center;
  color:var(--muted);font-family:var(--mono);font-size:.68rem;line-height:1.9}

@media(max-width:800px){
  .stats{grid-template-columns:repeat(3,1fr)}
  .two-col{grid-template-columns:1fr}
  .script-row{grid-template-columns:1fr 80px 70px}
}
</style>
</head>
<body>
<div class="topbar">
  <div>
    <div class="logo">Mr. Oldverdict</div>
    <div class="logo-sub">Been watching since before.</div>
  </div>
  <nav class="topbar-nav">
    <button class="nav-btn active" onclick="showPage('home',this)">Home</button>
    <button class="nav-btn"        onclick="showPage('scripts',this)">Scripts</button>
    <button class="nav-btn"        onclick="showPage('topics',this)">Topics</button>
  </nav>
  <div class="topbar-right" id="last-updated">Loading...</div>
</div>

<div class="pages">

<!-- HOME -->
<div class="page active" id="page-home">
  <div class="conn-banner" id="conn-banner">
    <div class="conn-item"><div class="conn-dot conn-unk"></div>Checking connections...</div>
  </div>
  <div class="stats">
    <div class="stat"><div class="stat-val" id="s-scripts">-</div><div class="stat-lbl">Scripts</div></div>
    <div class="stat"><div class="stat-val" id="s-published">-</div><div class="stat-lbl">Published</div></div>
    <div class="stat"><div class="stat-val" id="s-unpub">-</div><div class="stat-lbl">Unpublished</div></div>
    <div class="stat"><div class="stat-val" id="s-assembled">-</div><div class="stat-lbl">Assembled</div></div>
    <div class="stat"><div class="stat-val" id="s-topics">-</div><div class="stat-lbl">Topics Ready</div></div>
  </div>
  <div class="actions">
    <button class="btn btn-gold"  id="b-pipeline" onclick="doRunPipeline()">&#9654; Run Pipeline</button>
    <button class="btn btn-ghost" id="b-ingest"   onclick="doRunIngestion()">&#8595; Pull Topics</button>
    <button class="btn btn-ghost" id="b-modal"    onclick="doTestModal()">&#9711; Test Modal</button>
  </div>
  <div id="debug-home"></div>
  <div class="two-col">
    <div>
      <div class="panel">
        <div class="panel-head">
          <span class="panel-title">Recent Scripts</span>
          <span class="panel-sub" id="home-ref"></span>
        </div>
        <div class="tabs">
          <button class="tab active" data-tab="all"   onclick="switchTab('all',this)">All</button>
          <button class="tab"        data-tab="ready" onclick="switchTab('ready',this)">Ready to Publish</button>
          <button class="tab"        data-tab="pub"   onclick="switchTab('pub',this)">Published</button>
        </div>
        <div id="home-scripts"></div>
      </div>
    </div>
    <div>
      <div class="panel">
        <div class="panel-head"><span class="panel-title">Topics Queue</span></div>
        <div id="home-topics"></div>
      </div>
    </div>
  </div>
</div>

<!-- SCRIPTS -->
<div class="page" id="page-scripts">
  <div class="actions" style="margin-bottom:14px">
    <button class="btn btn-ghost" id="bs-all"  onclick="filterScripts('all')">All</button>
    <button class="btn btn-gold"  id="bs-rdy"  onclick="filterScripts('ready')">Ready to Publish</button>
    <button class="btn btn-ghost" id="bs-pub"  onclick="filterScripts('pub')">Published</button>
  </div>
  <div id="debug-scripts"></div>
  <div class="panel">
    <div class="panel-head">
      <span class="panel-title">Scripts</span>
      <span class="panel-sub" id="scripts-count">-</span>
    </div>
    <div id="scripts-list"></div>
  </div>
</div>

<!-- TOPICS -->
<div class="page" id="page-topics">
  <div class="actions">
    <button class="btn btn-ghost" id="bt-all"   onclick="filterTopics('all')">All</button>
    <button class="btn btn-gold"  id="bt-ready" onclick="filterTopics('ready')">Ready</button>
    <button class="btn btn-ghost" id="bt-used"  onclick="filterTopics('used')">Used</button>
    <button class="btn btn-ghost" id="b-ingest2" onclick="doRunIngestion()">&#8595; Pull Topics</button>
  </div>
  <div id="debug-topics"></div>
  <div class="panel">
    <div class="panel-head">
      <span class="panel-title">Topics</span>
      <span class="panel-sub" id="topics-count">-</span>
    </div>
    <div id="topics-list"></div>
  </div>
</div>

</div>

<script>
var CATS={
  A:{label:'Modern Behavior',color:'#9a6820'},
  B:{label:'Work & Ambition',color:'#6b6820'},
  C:{label:'Relationships',  color:'#882050'},
  D:{label:'Time & Meaning', color:'#5a3888'},
  E:{label:'Value Reversal', color:'#2e6e2e'}
};
var EXPR={
  flat_observation:    {label:'Flat',    color:'#8a7a60'},
  slight_raise:        {label:'Raise',   color:'#2a5080'},
  mid_line_delivery:   {label:'Mid',     color:'#6b6820'},
  quiet_concern:       {label:'Concern', color:'#5a3888'},
  precise_destruction: {label:'Precise', color:'#8a3820'},
  faint_amusement:     {label:'Amused',  color:'#2e6e2e'}
};

var allScripts=[], allVideos=[], allTopics=[];
var activeTab='all', scriptFilter='ready', topicFilter='ready', currentPage='home';

function ago(iso){
  var s=Math.floor((Date.now()-new Date(iso))/1000);
  if(s<60)return s+'s';
  if(s<3600)return Math.floor(s/60)+'m';
  if(s<86400)return Math.floor(s/3600)+'h';
  return Math.floor(s/86400)+'d';
}
function showDebug(id,html,isErr){
  var el=document.getElementById(id); if(!el)return;
  el.innerHTML='<div class="debug-box" style="'+(isErr?'border-color:rgba(138,46,32,.3);background:rgba(138,46,32,.04)':'')+'">'+html+'</div>';
}
function catBadge(cat){
  var c=CATS[cat]||{label:cat||'?',color:'var(--muted)'};
  return '<span class="cat-badge" style="color:'+c.color+';background:'+c.color+'18;border:1px solid '+c.color+'30">'+cat+'</span>';
}
function exprBadge(expr){
  var e=EXPR[expr||'flat_observation']||{label:'?',color:'var(--muted)'};
  return '<span><span class="expr-dot" style="background:'+e.color+'"></span>'
    +'<span style="font-family:var(--mono);font-size:.56rem;color:'+e.color+'">'+e.label+'</span></span>';
}

function showPage(name,btn){
  document.querySelectorAll('.page').forEach(function(p){p.classList.remove('active');});
  document.querySelectorAll('.nav-btn').forEach(function(b){b.classList.remove('active');});
  document.getElementById('page-'+name).classList.add('active');
  btn.classList.add('active'); currentPage=name;
  if(name==='scripts') renderScriptsPage();
  if(name==='topics')  renderTopicsPage();
}
function switchTab(tab,btn){
  activeTab=tab;
  document.querySelectorAll('.tab').forEach(function(t){t.classList.remove('active');});
  btn.classList.add('active');
  renderHomeScripts();
}

/* ── Connection diagnostics ── */
async function checkConnections(){
  var banner=document.getElementById('conn-banner'); if(!banner)return;
  try{
    var r=await fetch('/diagnostics'); var d=await r.json();
    var items=[];
    items.push('<div class="conn-item"><div class="conn-dot '+(d.supabase_url_set?'conn-ok':'conn-err')+'"></div>'
      +'Supabase URL '+(d.supabase_url_set?'set':'MISSING')+'</div>');
    items.push('<div class="conn-item"><div class="conn-dot '+(d.supabase_key_set?'conn-ok':'conn-err')+'"></div>'
      +'Anon key '+(d.supabase_key_set?'set':'MISSING')+'</div>');
    items.push('<div class="conn-item"><div class="conn-dot '+(d.supabase_svc_key_set?'conn-ok':'conn-err')+'"></div>'
      +'Service key '+(d.supabase_svc_key_set?'set':'MISSING')+'</div>');
    items.push('<div class="conn-item"><div class="conn-dot '+(d.modal_url_set?'conn-ok':'conn-err')+'"></div>'
      +'Modal URL '+(d.modal_url_set?'set':'MISSING — deploy pipeline.py first')+'</div>');
    var testOk=d.supabase_test==='ok';
    items.push('<div class="conn-item"><div class="conn-dot '+(testOk?'conn-ok':'conn-err')+'"></div>'
      +'DB query: '+d.supabase_test+'</div>');
    banner.innerHTML=items.join('');
  }catch(e){
    banner.innerHTML='<div class="conn-item"><div class="conn-dot conn-err"></div>Diagnostics failed: '+e.message+'</div>';
  }
}

/* ── Data loading ── */
async function loadStats(){
  try{
    var r=await fetch('/stats'); var d=await r.json();
    if(d.error){showDebug('debug-home','<span class="dr">Stats error: '+d.error+'</span>',true);return;}
    document.getElementById('s-scripts').textContent=d.total_scripts||0;
    document.getElementById('s-published').textContent=d.published||0;
    document.getElementById('s-unpub').textContent=d.unpublished||0;
    document.getElementById('s-assembled').textContent=d.videos_assembled||0;
    document.getElementById('s-topics').textContent=d.topics_ready||0;
    document.getElementById('last-updated').textContent='Updated '+new Date().toLocaleTimeString();
  }catch(e){showDebug('debug-home','<span class="dr">Failed to load stats: '+e.message+'</span>',true);}
}
async function loadScripts(){
  try{
    var r=await fetch('/scripts'); var d=await r.json();
    if(d.error){showDebug('debug-home','<span class="dr">Scripts error: '+d.error+'</span>',true);return;}
    allScripts=d; renderHomeScripts(); renderScriptsPage();
  }catch(e){showDebug('debug-home','<span class="dr">Failed to load scripts: '+e.message+'</span>',true);}
}
async function loadVideos(){
  try{
    var r=await fetch('/videos'); var d=await r.json();
    if(!d.error) allVideos=d;
  }catch(e){}
}
async function loadTopics(){
  try{
    var r=await fetch('/topics'); var d=await r.json();
    if(d.error){return;}
    allTopics=d; renderHomeTopics(); renderTopicsPage();
  }catch(e){}
}

function getVideo(sid){return allVideos.find(function(v){return v.script_id===sid;});}
function hasVideo(sid){var v=getVideo(sid);return v&&v.video_url;}

/* ── Rendering ── */
function renderHomeScripts(){
  var el=document.getElementById('home-scripts'); if(!el)return;
  var rows=allScripts;
  if(activeTab==='ready') rows=rows.filter(function(s){return !s.published&&hasVideo(s.id);});
  if(activeTab==='pub')   rows=rows.filter(function(s){return s.published;});
  document.getElementById('home-ref').textContent=rows.length+' shown';
  if(!rows.length){el.innerHTML='<div class="empty">Nothing here yet.</div>';return;}
  el.innerHTML=rows.slice(0,15).map(scriptRow).join('');
}
function filterScripts(f){
  scriptFilter=f;
  ['all','rdy','pub'].forEach(function(k){
    var btn=document.getElementById('bs-'+k); if(!btn)return;
    btn.className='btn '+(
      (k==='all'&&f==='all')||(k==='rdy'&&f==='ready')||(k==='pub'&&f==='pub')
      ?'btn-gold':'btn-ghost');
  });
  renderScriptsPage();
}
function renderScriptsPage(){
  var rows=allScripts;
  if(scriptFilter==='ready') rows=rows.filter(function(s){return !s.published&&hasVideo(s.id);});
  if(scriptFilter==='pub')   rows=rows.filter(function(s){return s.published;});
  document.getElementById('scripts-count').textContent=rows.length+' scripts';
  var el=document.getElementById('scripts-list'); if(!el)return;
  if(!rows.length){el.innerHTML='<div class="empty">Nothing here.</div>';return;}
  el.innerHTML=rows.map(scriptRow).join('');
}
function scriptRow(s){
  var assembled=hasVideo(s.id);
  var pubBadge=s.published
    ?'<span class="badge b-pub">Published</span>'
    :(assembled
      ?'<span class="badge b-assembled">Assembled</span>'
      :'<span class="badge b-noassembly">No video</span>');
  var assBtn=assembled?''
    :'<button class="mini-btn" data-id="'+s.id+'" onclick="doAssemble(this.dataset.id,this)">Assemble</button>';
  var pubBtn=(!s.published&&assembled)
    ?'<button class="mini-btn pub" data-id="'+s.id+'" onclick="doPublish(this.dataset.id,this)">Publish</button>'
    :'';
  return '<div class="script-row">'
    +'<div><div class="script-setup">'+(s.setup||'Untitled')+'</div>'
    +'<div class="script-meta">'
    +(s.category?catBadge(s.category):'')
    +(s.expression?exprBadge(s.expression):'')
    +'</div></div>'
    +'<div>'+pubBadge+'</div>'
    +'<div class="time-cell">'+(s.created_at?ago(s.created_at)+' ago':'')+'</div>'
    +'<div class="action-cell">'+assBtn+'</div>'
    +'<div class="action-cell">'+pubBtn+'</div>'
    +'</div>';
}
function renderHomeTopics(){
  var ready=allTopics.filter(function(t){return !t.used;});
  var el=document.getElementById('home-topics'); if(!el)return;
  if(!ready.length){
    el.innerHTML='<div class="empty">Queue empty.<br>Click Pull Topics.</div>'; return;
  }
  el.innerHTML=ready.slice(0,8).map(function(t){
    var cat=CATS[t.category]||{label:t.category||'?',color:'var(--muted)'};
    return '<div class="topic-row">'
      +'<div class="topic-text">'+(t.raw_topic||'Untitled')+'</div>'
      +'<div class="topic-foot">'
      +'<span class="score-pill '+(t.engagement_score>=70?'sc-hi':'sc-lo')+'">'+(t.engagement_score||0)+'</span>'
      +'<span style="font-family:var(--mono);font-size:.58rem;color:'+cat.color+'">'+cat.label+'</span>'
      +'</div></div>';
  }).join('');
}
function filterTopics(f){
  topicFilter=f;
  ['all','ready','used'].forEach(function(k){
    var btn=document.getElementById('bt-'+k); if(btn)btn.className='btn '+(k===f?'btn-gold':'btn-ghost');
  });
  renderTopicsPage();
}
function renderTopicsPage(){
  var topics=allTopics;
  if(topicFilter==='ready') topics=topics.filter(function(t){return !t.used;});
  if(topicFilter==='used')  topics=topics.filter(function(t){return t.used;});
  document.getElementById('topics-count').textContent=topics.length+' topics';
  var el=document.getElementById('topics-list'); if(!el)return;
  if(!topics.length){el.innerHTML='<div class="empty">No topics.</div>';return;}
  el.innerHTML=topics.map(function(t){
    var cat=CATS[t.category]||{label:t.category||'?',color:'var(--muted)'};
    return '<div class="topic-row">'
      +'<div class="topic-text">'+(t.raw_topic||'Untitled')+'</div>'
      +'<div class="topic-foot">'
      +'<span class="score-pill '+(t.engagement_score>=70?'sc-hi':'sc-lo')+'">'+(t.engagement_score||0)+'</span>'
      +'<span style="display:flex;gap:8px;align-items:center">'
      +'<span style="font-family:var(--mono);font-size:.58rem;color:'+cat.color+'">'+cat.label+'</span>'
      +'<span style="font-family:var(--mono);font-size:.55rem;color:var(--muted)">'+(t.used?'Used':'Ready')+'</span>'
      +'</span></div></div>';
  }).join('');
}

/* ── Actions ── */
async function doRunPipeline(){
  var btn=document.getElementById('b-pipeline');
  btn.disabled=true; btn.textContent='Running...';
  showDebug('debug-home','<span class="dm">Triggering pipeline...</span>');
  try{
    var r=await fetch('/run-pipeline',{method:'POST'});
    var d=await r.json();
    if(d.error) throw new Error(d.error);
    showDebug('debug-home','<span class="dg">&#10003; Pipeline triggered.</span> Modal responded: '+JSON.stringify(d.body||d.status).slice(0,80));
    setTimeout(function(){loadStats();loadScripts();loadVideos();},6000);
  }catch(e){showDebug('debug-home','<span class="dr">&#10007; '+e.message+'</span>',true);}
  finally{btn.disabled=false;btn.innerHTML='&#9654; Run Pipeline';}
}
async function doRunIngestion(){
  var btns=[document.getElementById('b-ingest'),document.getElementById('b-ingest2')];
  btns.forEach(function(b){if(b)b.disabled=true;});
  showDebug('debug-home','<span class="dm">Pulling topics from Reddit...</span>');
  try{
    var r=await fetch('/run-ingestion',{method:'POST'});
    var d=await r.json();
    if(d.error) throw new Error(d.error);
    showDebug('debug-home','<span class="dg">&#10003; Ingestion triggered.</span>');
    setTimeout(loadTopics,5000);
  }catch(e){
    showDebug('debug-home','<span class="dr">&#10007; '+e.message+'</span>',true);
    showDebug('debug-topics','<span class="dr">&#10007; '+e.message+'</span>',true);
  }
  finally{btns.forEach(function(b){if(b)b.disabled=false;});}
}
async function doTestModal(){
  var btn=document.getElementById('b-modal'); btn.disabled=true; btn.textContent='Testing...';
  showDebug('debug-home','<span class="dm">Testing Modal connection...</span>');
  try{
    var r=await fetch('/test-modal'); var d=await r.json();
    if(d.error&&!d.url) throw new Error(d.error);
    showDebug('debug-home',
      '<span class="dk">'+d.url+'</span><br>'
      +'<span class="'+(d.ok?'dg':'dr')+'">HTTP '+d.status+' '+(d.ok?'&#10003; OK':'&#10007; FAILED')+'</span>'
      +(d.response?'<br><span class="dm">'+d.response.slice(0,120)+'</span>':'')
      +(d.error?'<br><span class="dr">'+d.error+'</span>':''),
      !d.ok);
  }catch(e){showDebug('debug-home','<span class="dr">&#10007; '+e.message+'</span>',true);}
  finally{btn.disabled=false;btn.innerHTML='&#9711; Test Modal';}
}
async function doAssemble(scriptId,btn){
  btn.disabled=true; btn.textContent='...';
  try{
    var r=await fetch('/assemble',{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({script_id:scriptId})});
    var d=await r.json();
    if(d.error) throw new Error(d.error);
    showDebug('debug-scripts','<span class="dg">&#10003; Assembly triggered for '+scriptId.slice(0,8)+'...</span>');
    setTimeout(function(){loadVideos();renderScriptsPage();},8000);
  }catch(e){
    showDebug('debug-scripts','<span class="dr">&#10007; '+e.message+'</span>',true);
    btn.disabled=false; btn.textContent='Assemble';
  }
}
async function doPublish(scriptId,btn){
  if(!confirm('Publish to YouTube?'))return;
  btn.disabled=true; btn.textContent='...';
  try{
    var r=await fetch('/publish',{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({script_id:scriptId})});
    var d=await r.json();
    if(d.error) throw new Error(d.error);
    showDebug('debug-scripts','<span class="dg">&#10003; Published to YouTube.</span>');
    setTimeout(function(){loadScripts();loadVideos();loadStats();},3000);
  }catch(e){
    showDebug('debug-scripts','<span class="dr">&#10007; '+e.message+'</span>',true);
    btn.disabled=false; btn.textContent='Publish';
  }
}

/* ── Init ── */
async function loadAll(){
  await checkConnections();
  await Promise.all([loadStats(),loadScripts(),loadVideos(),loadTopics()]);
}
loadAll();
setInterval(function(){loadStats();loadScripts();loadVideos();loadTopics();},30000);
</script>
</body>
</html>`;
}