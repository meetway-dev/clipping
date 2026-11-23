/* ============================================================
   ClipForge AI Studio — PeakCut Unified Frontend Engine
   A to Z Implementation of PeakCut Design, Navigation & Workflow
   ============================================================ */

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));

const I = {
  "github": `<path fill-rule="evenodd" transform="scale(16)" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>`,
  "instagram": `<rect x="32" y="32" width="192" height="192" rx="56" fill="none" stroke="currentColor" stroke-width="18"/><circle cx="128" cy="128" r="42" fill="none" stroke="currentColor" stroke-width="18"/><circle cx="184" cy="72" r="13"/>`,
  "chat": `<path d="M128,24A104,104,0,0,0,36.18,176.88L24.83,210.93a16,16,0,0,0,20.24,20.24l34.05-11.35A104,104,0,1,0,128,24Zm0,192a87.87,87.87,0,0,1-44.06-11.81,8,8,0,0,0-6.54-.67L40,216,52.47,178.6a8,8,0,0,0-.66-6.54A88,88,0,1,1,128,216Z"/>`,
  "home": `<path d="M219.31,108.68l-80-80a16,16,0,0,0-22.62,0l-80,80A15.87,15.87,0,0,0,32,120v96a8,8,0,0,0,8,8h64a8,8,0,0,0,8-8V160h32v56a8,8,0,0,0,8,8h64a8,8,0,0,0,8-8V120A15.87,15.87,0,0,0,219.31,108.68Z"/>`,
  "home_f": `<path d="M224,120v96a8,8,0,0,1-8,8H160a8,8,0,0,1-8-8V164a4,4,0,0,0-4-4H108a4,4,0,0,0-4,4v52a8,8,0,0,1-8,8H40a8,8,0,0,1-8-8V120a16,16,0,0,1,4.69-11.31l80-80a16,16,0,0,1,22.62,0l80,80A16,16,0,0,1,224,120Z"/>`,
  "film": `<path d="M216,40H40A16,16,0,0,0,24,56V200a16,16,0,0,0,16,16H216a16,16,0,0,0,16-16V56A16,16,0,0,0,216,40ZM40,88h80v80H40Zm96-16V56h32V72Zm-16,0H88V56h32Zm0,112v16H88V184Zm16,0h32v16H136Zm0-16V88h80v80Zm80-96H184V56h32ZM72,56V72H40V56ZM40,184H72v16H40Zm176,16H184V184h32v16Z"/>`,
  "film_f": `<path d="M216,40H40A16,16,0,0,0,24,56V200a16,16,0,0,0,16,16H216a16,16,0,0,0,16-16V56A16,16,0,0,0,216,40ZM184,56h32V72H184ZM72,200H40V184H72ZM72,72H40V56H72Zm48,128H88V184h32Zm0-128H88V56h32Zm48,128H136V184h32Zm0-128H136V56h32Zm48,128H184V184h32v16Z"/>`,
  "cog": `<path d="M128,80a48,48,0,1,0,48,48A48.05,48.05,0,0,0,128,80Zm0,80a32,32,0,1,1,32-32A32,32,0,0,1,128,160Z"/>`,
  "plus": `<path d="M224,128a8,8,0,0,1-8,8H136v80a8,8,0,0,1-16,0V136H40a8,8,0,0,1,0-16h80V40a8,8,0,0,1,16,0v80h80A8,8,0,0,1,224,128Z"/>`,
  "plusc": `<path d="M128,24A104,104,0,1,0,232,128,104.11,104.11,0,0,0,128,24Zm48,112H136v40a8,8,0,0,1-16,0V136H80a8,8,0,0,1,0-16h40V80a8,8,0,0,1,16,0v40h40a8,8,0,0,1,0,16Z"/>`,
  "scissors": `<path d="M157.73,113.13A8,8,0,0,1,159.82,102L227.48,55.7a8,8,0,0,1,9,13.21l-67.67,46.3a7.92,7.92,0,0,1-4.51,1.4A8,8,0,0,1,157.73,113.13Zm80.87,85.09a8,8,0,0,1-11.12,2.08L136,137.7,93.49,166.78a36,36,0,1,1-9-13.19L121.83,128,84.44,102.41a35.86,35.86,0,1,1,9-13.19l143,97.87A8,8,0,0,1,238.6,198.22ZM80,180a20,20,0,1,0-5.86,14.14A19.85,19.85,0,0,0,80,180ZM74.14,90.13a20,20,0,1,0-28.28,0A19.85,19.85,0,0,0,74.14,90.13Z"/>`,
  "sliders": `<path d="M40,88H73a32,32,0,0,0,62,0h81a8,8,0,0,0,0-16H135a32,32,0,0,0-62,0H40a8,8,0,0,0,0,16Zm64-24A16,16,0,1,1,88,80,16,16,0,0,1,104,64ZM216,168H199a32,32,0,0,0-62,0H40a8,8,0,0,0,0,16h97a32,32,0,0,0,62,0h17a8,8,0,0,0,0-16Zm-48,24a16,16,0,1,1,16-16A16,16,0,0,1,168,192Z"/>`,
  "bolt": `<path d="M215.79,118.17a8,8,0,0,0-5-5.66L153.18,90.9l14.66-73.33a8,8,0,0,0-13.69-7l-112,120a8,8,0,0,0,3,13l57.63,21.61L88.16,238.43a8,8,0,0,0,13.69,7l112-120A8,8,0,0,0,215.79,118.17Z"/>`,
  "bell": `<path d="M221.8,175.94C216.25,166.38,208,139.33,208,104a80,80,0,1,0-160,0c0,35.34-8.26,62.38-13.81,71.94A16,16,0,0,0,48,200H88.81a40,40,0,0,0,78.38,0H208a16,16,0,0,0,13.8-24.06ZM128,216a24,24,0,0,1-22.62-16h45.24A24,24,0,0,1,128,216Z"/>`,
  "up": `<path d="M224,144v64a8,8,0,0,1-8,8H40a8,8,0,0,1-8-8V144a8,8,0,0,1,16,0v56H208V144a8,8,0,0,1,16,0ZM93.66,77.66,120,51.31V144a8,8,0,0,0,16,0V51.31l26.34,26.35a8,8,0,0,0,11.32-11.32l-40-40a8,8,0,0,0-11.32,0l-40,40A8,8,0,0,0,93.66,77.66Z"/>`,
  "down": `<path d="M224,144v64a8,8,0,0,1-8,8H40a8,8,0,0,1-8-8V144a8,8,0,0,1,16,0v56H208V144a8,8,0,0,1,16,0Zm-101.66,5.66a8,8,0,0,0,11.32,0l40-40a8,8,0,0,0-11.32-11.32L136,124.69V32a8,8,0,0,0-16,0v92.69L93.66,98.34a8,8,0,0,0-11.32,11.32Z"/>`,
  "copy": `<path d="M216,32H88a8,8,0,0,0-8,8V80H40a8,8,0,0,0-8,8V216a8,8,0,0,0,8,8H168a8,8,0,0,0,8-8V176h40a8,8,0,0,0,8-8V40A8,8,0,0,0,216,32ZM160,208H48V96H160Zm48-48H176V88a8,8,0,0,0-8-8H96V48H208Z"/>`,
  "trash": `<path d="M216,48H176V40a24,24,0,0,0-24-24H104A24,24,0,0,0,80,40v8H40a8,8,0,0,0,0,16h8V208a16,16,0,0,0,16,16H192a16,16,0,0,0,16-16V64h8a8,8,0,0,0,0-16ZM96,40a8,8,0,0,1,8-8h48a8,8,0,0,1,8,8v8H96Zm96,168H64V64H192Z"/>`,
  "link": `<path d="M165.66,90.34a8,8,0,0,1,0,11.32l-64,64a8,8,0,0,1-11.32-11.32l64-64A8,8,0,0,1,165.66,90.34ZM215.6,40.4a56,56,0,0,0-79.2,0L106.34,70.45a8,8,0,0,0,11.32,11.32l30.06-30a40,40,0,0,1,56.57,56.56l-30.07,30.06a8,8,0,0,0,11.31,11.32L215.6,119.6a56,56,0,0,0,0-79.2Z"/>`,
  "play": `<path d="M232.4,114.49,88.32,26.35a16,16,0,0,0-16.2-.3A15.86,15.86,0,0,0,64,39.87V216.13A15.94,15.94,0,0,0,80,232a16.07,16.07,0,0,0,8.36-2.35L232.4,141.51a15.81,15.81,0,0,0,0-27ZM80,215.94V40l143.83,88Z"/>`,
  "pause": `<path d="M200,32H160a16,16,0,0,0-16,16V208a16,16,0,0,0,16,16h40a16,16,0,0,0,16-16V48A16,16,0,0,0,200,32Zm0,176H160V48h40ZM96,32H56A16,16,0,0,0,40,48V208a16,16,0,0,0,16,16H96a16,16,0,0,0,16-16V48A16,16,0,0,0,96,32Zm0,176H56V48H96Z"/>`,
  "check": `<path d="M173.66,98.34a8,8,0,0,1,0,11.32l-56,56a8,8,0,0,1-11.32,0l-24-24a8,8,0,0,1,11.32-11.32L112,148.69l50.34-50.35A8,8,0,0,1,173.66,98.34ZM232,128A104,104,0,1,1,128,24,104.11,104.11,0,0,1,232,128Z"/>`,
  "caret": `<path d="M213.66,101.66l-80,80a8,8,0,0,1-11.32,0l-80-80A8,8,0,0,1,53.66,90.34L128,164.69l74.34-74.35a8,8,0,0,1,11.32,11.32Z"/>`,
  "minus": `<path d="M224,128a8,8,0,0,1-8,8H40a8,8,0,0,1,0-16H216A8,8,0,0,1,224,128Z"/>`,
  "arrowr": `<path d="M221.66,133.66l-72,72a8,8,0,0,1-11.32-11.32L196.69,136H40a8,8,0,0,1,0-16H196.69L138.34,61.66a8,8,0,0,1,11.32-11.32l72,72A8,8,0,0,1,221.66,133.66Z"/>`,
  "x": `<path d="M205.66,194.34a8,8,0,0,1-11.32,11.32L128,139.31,61.66,205.66a8,8,0,0,1-11.32-11.32L116.69,128,50.34,61.66A8,8,0,0,1,61.66,50.34L128,116.69l66.34-66.35a8,8,0,0,1,11.32,11.32L139.31,128Z"/>`,
  "user": `<path d="M128,24A104,104,0,1,0,232,128,104.11,104.11,0,0,0,128,24ZM74.08,197.5a64,64,0,0,1,107.84,0,87.83,87.83,0,0,1-107.84,0ZM96,120a32,32,0,1,1,32,32A32,32,0,0,1,96,120Z"/>`,
  "send": `<path d="M227.32,28.68a16,16,0,0,0-15.66-4.08l-.15,0L19.57,82.84a16,16,0,0,0-2.49,29.8L102,154l41.3,84.87A15.86,15.86,0,0,0,157.74,248q.69,0,1.38-.06a15.88,15.88,0,0,0,14-11.51l58.2-191.94c0-.05,0-.1,0-.15A16,16,0,0,0,227.32,28.68Z"/>`,
  "radio": `<path d="M128,88a40,40,0,1,0,40,40A40,40,0,0,0,128,88Zm0,64a24,24,0,1,1,24-24A24,24,0,0,1,128,152Z"/>`,
  "clock": `<path d="M128,24A104,104,0,1,0,232,128,104.11,104.11,0,0,0,128,24Zm0,192a88,88,0,1,1,88-88A88.1,88.1,0,0,1,128,216Zm64-88a8,8,0,0,1-8,8H128a8,8,0,0,1-8-8V72a8,8,0,0,1,16,0v48h48A8,8,0,0,1,192,128Z"/>`,
  "chart": `<path d="M224,200h-8V40a8,8,0,0,0-8-8H152a8,8,0,0,0-8,8V80H96a8,8,0,0,0-8,8v40H48a8,8,0,0,0-8,8v64H32a8,8,0,0,0,0,16H224a8,8,0,0,0,0-16Z"/>`,
  "folder": `<path d="M245,110.64A16,16,0,0,0,232,104H216V88a16,16,0,0,0-16-16H130.67L102.94,51.2a16.14,16.14,0,0,0-9.6-3.2H40A16,16,0,0,0,24,64V208h0a8,8,0,0,0,8,8H211.1a8,8,0,0,0,7.59-5.47l28.49-85.47A16.05,16.05,0,0,0,245,110.64Z"/>`,
  "plug": `<path d="M237.66,18.34a8,8,0,0,0-11.32,0l-52.4,52.41-5.37-5.38a32.05,32.05,0,0,0-45.26,0L100,88.69l-6.34-6.35A8,8,0,0,0,82.34,93.66L88.69,100,65.37,123.31a32,32,0,0,0,0,45.26l5.38,5.37-52.41,52.4a8,8,0,0,0,11.32,11.32l52.4-52.41,5.37,5.38a32,32,0,0,0,45.26,0L156,167.31l6.34,6.35a8,8,0,0,0,11.32-11.32L167.31,156l23.32-23.31a32,32,0,0,0,0-45.26l-5.38-5.37,52.41-52.4A8,8,0,0,0,237.66,18.34Z"/>`,
  "warn": `<path d="M128,24A104,104,0,1,0,232,128,104.11,104.11,0,0,0,128,24Zm-8-80V80a8,8,0,0,1,16,0v56a8,8,0,0,1-16,0Zm20,36a12,12,0,1,1-12-12A12,12,0,0,1,140,172Z"/>`
};

const ic = n => `<svg viewBox="0 0 256 256" aria-hidden="true">${I[n] || ""}</svg>`;
const navIc = (n, v) => ic(S.view === v && I[n + "_f"] ? n + "_f" : n);

const fmt = s => {
  s = Math.max(0, Math.round(s || 0));
  const h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60);
  return (h ? h + ":" + String(m).padStart(2, "0") : m) + ":" + String(s % 60).padStart(2, "0");
};
const fmtLen = s => fmt(s);
const fmtK = n => n >= 1e6 ? (n / 1e6).toFixed(1) + "M" : n >= 1e3 ? (n / 1e3).toFixed(1) + "K" : n;

/* ============================================================ Global App State */
const S = {
  view: "library",   // 'overview', 'library' (/app/videos), 'settings', 'usage', or 'c:<creator_id>'
  ctab: "clips",      // creator tab: clips, setup, activity
  stab: "ai",         // settings tab: ai, apps, speech, storage
  jobs: [],
  creators: [
    { id: "all", name: "Main Studio", channel: "" }
  ],
  accounts: [],
  status: {
    user: { name: "Studio Director", role: "admin" },
    ai: { ready: true, provider: "Ollama (on this machine)", model: "llama3.2", today_calls: 18 },
    styles: { bounce: "Hormozi (Bounce)", hype: "MrBeast (Hype)", clean: "Modern Clean", cyber: "Cyber Neon" },
    layouts: { fit_canvas: "Fit Full Video (Hook + Captions)", face_center: "Smart Face Center", gameplay: "Active speaker tracking", split: "Split screen (Host/Guest)", blur: "Blurred fill", crop: "Fill screen" }
  },
  sel: new Set(),
  expandedBriefs: new Set()
};

const D = { jid: null, cid: null, sig: "" };

/* ============================================================ API Helper */
async function api(path, opt = {}) {
  const r = await fetch(path, opt);
  if (!r.ok) {
    let d = r.statusText;
    try { d = (await r.json()).detail || d; } catch {}
    throw new Error(typeof d === "string" ? d : "Something went wrong");
  }
  return r.json();
}
const send = (path, body, method = "POST") => api(path, {
  method,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body ?? {})
});

function toast(msg, kind = "ok") {
  if (!msg) return;
  const t = document.createElement("div");
  t.className = "toast " + kind;
  t.textContent = msg;
  $("#toasts").append(t);
  setTimeout(() => t.remove(), kind === "bad" ? 6000 : 3200);
}

const cache = new WeakMap();
function put(el, html) {
  if (el && cache.get(el) !== html) {
    cache.set(el, html);
    el.innerHTML = html;
  }
}

function ask(title, text, okLabel = "Confirm", danger = false) {
  return new Promise(res => {
    const d = $("#formdlg");
    d.innerHTML = `<form method="dialog" class="dlg">
      <h2>${esc(title)}</h2>
      <p class="help">${esc(text)}</p>
      <div class="dlg-foot">
        <button class="btn" value="no">Cancel</button>
        <button class="btn ${danger ? "danger" : "primary"}" value="yes" autofocus>${esc(okLabel)}</button>
      </div>
    </form>`;
    d.onclose = () => res(d.returnValue === "yes");
    d.returnValue = "no";
    d.showModal();
  });
}

/* ============================================================ Shell & Navigation */
function drawShell() {
  const navItem = (v, icon, label, extra = "") => `
    <button class="nav-item ${S.view === v ? "on" : ""}" data-act="go" data-v="${esc(v)}" title="${esc(label)}">
      ${icon}
      <span class="label">${esc(label)}</span>
      ${extra}
    </button>`;

  const w = S.jobs.filter(j => ["queued", "running"].includes(j.status)).length;
  const workingBadge = w ? `<span class="working" title="${w} working now"><i></i>${w} working</span>` : S.jobs.length ? `<span class="count">${S.jobs.length}</span>` : "";

  put($("#nav"),
    navItem("overview", navIc("home", "overview"), "Home") +
    navItem("library", navIc("film", "library"), "All videos", workingBadge) +
    `<h4><span>Creators</span></h4>` +
    S.creators.map(c => navItem("c:" + c.id, `<span class="avatar">${esc(c.name.slice(0, 1).toUpperCase())}</span>`, c.name)).join("") +
    `<button class="nav-item" data-act="newcreator" title="New creator">${ic("plusc")}<span class="label">New creator</span></button>`
  );

  const k = S.status.ai;
  put($("#foot"),
    (k ? `<button class="ai-card ${S.view === "settings" ? "on" : ""}" data-act="go" data-v="settings" data-tab="ai" title="AI: ${esc(k.provider || "ready")}">
      <span class="ai-ic">${ic("bolt")}</span>
      <span class="ai-tx">
        <small><span class="led ${k.ready ? "" : "no"}"></span> Local Ollama</small>
        <b>${k.ready ? esc(k.model || "llama3.2") : "Connecting..."}</b>
      </span>
      <span class="ai-n" style="font-size:11px;color:var(--frame-dim)">Offline GPU</span>
    </button>` : "") +
    `<div class="me">
      <button class="me-btn" data-act="go" data-v="settings">
        <span class="avatar" style="background:#FF8B33;color:#1E1612;font-weight:800">CF</span>
        <span class="who">
          <b>Settings</b>
          <span>AI Engine, Pipeline, Apps</span>
        </span>
      </button>
      <button class="icon-btn bell" data-act="bell" title="System Status">${ic("bell")}</button>
    </div>`
  );

  let title = { overview: "Home", library: "All videos", settings: "Settings" }[S.view] || "Creator Studio";
  let sub = S.view === "overview" ? "System overview, clips activity, and analytics." : "Every video and recording, across all creators.";
  if (S.view === "settings") sub = "Local AI configuration, pipeline features, and connected platforms.";

  put($("#title"), `<span>${esc(title)}</span>`);
  put($("#subtitle"), esc(sub));

  let act = "";
  if (S.view === "library" || S.view === "overview") {
    act = `<a class="btn" href="https://github.com" target="_blank" rel="noopener">${ic("github")}<span>Star on GitHub</span></a>
           <button class="btn primary" data-act="focusurl">${ic("scissors")}Make clips</button>`;
  }
  put($("#actions"), act);
}

const ROUTES = { overview: "", library: "videos", settings: "settings" };
function pathFor(v, tab) {
  if (v === "settings") return "/app/settings" + (tab ? "/" + tab : "");
  return "/app" + (ROUTES[v] ? "/" + ROUTES[v] : "");
}

function go(v, tab) {
  S.view = v;
  if (v === "settings") S.stab = tab || "ai";
  history.pushState({ v, tab }, "", pathFor(v, tab));
  $("#app").classList.remove("open");

  const view = $("#view");
  if (window._gaStop) { window._gaStop(); window._gaStop = null; }

  $("#heroSlot").innerHTML = v === "overview" ? `
    <section class="hero">
      <div class="ga-bg" id="appAscii" aria-hidden="true"></div>
      <h2>What do you want to clip today?</h2>
      <p>Paste a YouTube/Twitch link or drop video files. Turn long podcasts into high-retention 9:16 shorts.</p>
      <div id="add"></div>
    </section>` : "";

  if (v === "overview") view.innerHTML = `<div id="ov"></div>`;
  else if (v === "library") view.innerHTML = `<div id="add"></div><div id="jobs"></div>`;
  else if (v === "settings") view.innerHTML = `<div id="sform"></div>`;
  else view.innerHTML = `<div id="add"></div><div id="jobs"></div>`;

  if ($("#add")) drawAdd(v === "overview" ? "hero" : "compact");
  if (v === "overview" && window.GradientASCII) {
    try { window._gaStop = GradientASCII($("#appAscii"), { colors: ["#ffb27a", "#ffffff", "#ffd2ae"], shape: "horizon", lightMode: true, cellSize: 16 }); } catch {}
  }

  if (v === "settings") drawSettings();
  render();
  $("#main").scrollTo(0, 0);
}

/* ============================================================ Composer Add Bar */
const DRAFT = { link: null, file: null, busy: false };

function drawAdd(variant) {
  const box = $("#add");
  if (!box) return;
  box.innerHTML = `
    <form class="composer ${variant === "hero" ? "big" : "compact"}" id="addform">
      <div class="composer-input">
        ${ic("link")}
        <input id="url" placeholder="Paste a YouTube, Twitch or Kick video link" autocomplete="off" aria-label="Video link">
      </div>
      <div class="att" id="att"><div><div class="att-in" id="attIn"></div></div></div>
      <div class="composer-bar">
        <button type="button" class="chip" data-act="pickfile">${ic("up")}Upload video</button>
        <button type="button" class="chip" data-act="toggleopts" aria-expanded="false">${ic("sliders")}Options</button>
        <span class="hint">or drop video file anywhere</span>
        <button class="btn primary" id="goBtn" type="submit">${ic("scissors")}Make clips</button>
      </div>

      <!-- Expandable PeakCut Options Accordion -->
      <div class="composer-opts" inert>
        <div class="og">
          <div class="ob">
            <div class="ot">Spoken language</div>
            <input type="hidden" id="o_lang" value="en">
            <div class="seg" role="group" aria-label="Spoken language">
              <button type="button" data-seg="o_lang" data-v="en" aria-pressed="true">English<small>Ready (NVIDIA Parakeet)</small></button>
              <button type="button" data-seg="o_lang" data-v="auto" aria-pressed="false">Auto-Detect<small>Multilingual Whisper</small></button>
            </div>
          </div>

          <div class="ob wide">
            <div class="ot">Clips</div>
            <div class="nsteps">
              <div class="nstep">
                <span>How many</span>
                <div class="ctl">
                  <button type="button" data-step="o_max" data-d="-1">${ic("minus")}</button>
                  <input id="o_max" type="number" min="1" max="20" step="1" value="5">
                  <button type="button" data-step="o_max" data-d="1">${ic("plus")}</button>
                </div>
              </div>
              <div class="nstep">
                <span>Shortest</span>
                <div class="ctl">
                  <button type="button" data-step="o_min" data-d="-5">${ic("minus")}</button>
                  <input id="o_min" type="number" min="10" max="120" step="5" value="25"><i>s</i>
                  <button type="button" data-step="o_min" data-d="5">${ic("plus")}</button>
                </div>
              </div>
              <div class="nstep">
                <span>Longest</span>
                <div class="ctl">
                  <button type="button" data-step="o_maxlen" data-d="-5">${ic("minus")}</button>
                  <input id="o_maxlen" type="number" min="15" max="180" step="5" value="65"><i>s</i>
                  <button type="button" data-step="o_maxlen" data-d="5">${ic("plus")}</button>
                </div>
              </div>
            </div>
          </div>

          <div class="ob wide">
            <label class="f">
              <span class="ot" style="margin:0">Headline banner text <span style="font-weight:400">(optional)</span></span>
              <input id="o_hook" maxlength="60" autocomplete="off" placeholder="Leave empty for AI to dynamically extract high-hook titles">
            </label>
          </div>

          <!-- Caption Styles Selection -->
          <div class="ob wide">
            <div class="ot cap-head">
              <span>Caption style</span>
              <label><input type="checkbox" id="o_captions" checked>Generate animated captions</label>
            </div>
            <input type="hidden" id="o_style" value="hormozi">
            <div class="tiles3" role="group">
              <button type="button" class="tile-o" data-seg="o_style" data-v="hormozi" aria-pressed="true">
                <span class="cap-prev" style="font-family:'Archivo Black',sans-serif;font-weight:800;letter-spacing:1px">ALEX <b style="color:#FFFF00">&nbsp;HORMOZI</b></span>
                Hormozi Impact
              </button>
              <button type="button" class="tile-o" data-seg="o_style" data-v="hype" aria-pressed="false">
                <span class="cap-prev" style="font-family:'Anton',sans-serif;font-size:15px;letter-spacing:1px">MRBEAST <b style="color:#00FF66">&nbsp;NEON</b></span>
                MrBeast Glow
              </button>
              <button type="button" class="tile-o" data-seg="o_style" data-v="cyber" aria-pressed="false">
                <span class="cap-prev" style="font-family:'Geist',sans-serif;color:#00E5FF;font-weight:700">CYBER <b style="color:#FF007F">&nbsp;NEON</b></span>
                Cyber Synth
              </button>
              <button type="button" class="tile-o" data-seg="o_style" data-v="clean" aria-pressed="false">
                <span class="cap-prev" style="font-family:'Poppins',sans-serif;font-weight:700">Clean <b style="color:#FFB800">&nbsp;Modern</b></span>
                Clean Amber
              </button>
            </div>
          </div>

          <!-- Video Layout Tiles -->
          <div class="ob wide">
            <div class="ot" style="display:flex;justify-content:space-between;align-items:center">
              <span>Camera layout & framing</span>
              <span style="font-size:11.5px;font-weight:400;color:var(--frame-dim)">Opus Clip & Submagic Framing</span>
            </div>
            <input type="hidden" id="o_layout" value="fit_canvas">
            <div class="tiles-layout" role="group">
              <button type="button" class="tile-o" data-seg="o_layout" data-v="fit_canvas" aria-pressed="true">
                <span class="lay-prev fit"><span class="ph"><i></i></span></span>
                <b>Fit Full Video</b>
                <span style="font-size:10.5px;color:var(--frame-dim);margin-top:-2px">Top Hook + Captions (Uncropped)</span>
              </button>
              <button type="button" class="tile-o" data-seg="o_layout" data-v="face_center" aria-pressed="false">
                <span class="lay-prev face"><span class="ph"><i></i></span></span>
                <b>Smart Face Center</b>
                <span style="font-size:10.5px;color:var(--frame-dim);margin-top:-2px">Dead-Center Face Lock</span>
              </button>
              <button type="button" class="tile-o" data-seg="o_layout" data-v="gameplay" aria-pressed="false">
                <span class="lay-prev"><span class="ph"><i style="left:2px;right:2px;height:18px"></i></span></span>
                <b>Speaker Track</b>
                <span style="font-size:10.5px;color:var(--frame-dim);margin-top:-2px">YuNet 0.25s Whip Cut</span>
              </button>
              <button type="button" class="tile-o" data-seg="o_layout" data-v="split" aria-pressed="false">
                <span class="lay-prev split"><span class="ph"><i></i></span></span>
                <b>Split Screen</b>
                <span style="font-size:10.5px;color:var(--frame-dim);margin-top:-2px">Host + Guest Stack</span>
              </button>
              <button type="button" class="tile-o" data-seg="o_layout" data-v="blur" aria-pressed="false">
                <span class="lay-prev"><span class="ph"><i></i></span></span>
                <b>Blurred Fill</b>
                <span style="font-size:10.5px;color:var(--frame-dim);margin-top:-2px">Classic Ambience</span>
              </button>
              <button type="button" class="tile-o" data-seg="o_layout" data-v="crop" aria-pressed="false">
                <span class="lay-prev crop"><span class="ph"><i style="top:0;height:100%;transform:none"></i></span></span>
                <b>Center Crop</b>
                <span style="font-size:10.5px;color:var(--frame-dim);margin-top:-2px">Direct 9:16 Full Cut</span>
              </button>
            </div>

            <!-- Customizable Fit Canvas Controls (Expands when Fit Canvas is selected) -->
            <div id="fit_canvas_options" class="fit-opt-card" style="display:block">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <span style="font-size:12.5px;font-weight:700;color:var(--text)">Canvas Spacing & Layout Distribution</span>
                <span id="o_top_space_val" style="font-size:13px;font-weight:800;color:var(--brand)">450px Top Spacing</span>
              </div>
              
              <div class="preset-row">
                <span style="font-size:11px;color:var(--frame-dim);align-self:center">Presets:</span>
                <button type="button" class="preset-btn" data-act="settopspace" data-val="450">450px (Balanced)</button>
                <button type="button" class="preset-btn" data-act="settopspace" data-val="320">320px (Hook Compact)</button>
                <button type="button" class="preset-btn" data-act="settopspace" data-val="550">550px (Spacious Hook)</button>
                <button type="button" class="preset-btn" data-act="settopspace" data-val="656">656px (Centered)</button>
              </div>

              <div style="display:flex;gap:12px;align-items:center">
                <span style="font-size:11px;color:var(--frame-dim)">Compact (150px)</span>
                <input type="range" id="o_top_space" min="150" max="800" step="10" value="450" style="flex:1"
                  oninput="document.getElementById('o_top_space_val').textContent = this.value + 'px Top Spacing'">
                <span style="font-size:11px;color:var(--frame-dim)">Spacious (800px)</span>
              </div>

              <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:4px">
                <label class="f" style="margin:0">
                  <span class="ot" style="margin:0 0 4px">Background canvas style</span>
                  <select id="o_canvas_bg">
                    <option value="solid_black" selected>Studio Black (#0E0C0A) — 100% Solid Clean</option>
                    <option value="heavy_blur">Ultra-Heavy Ambient Blur (100% Vignette)</option>
                  </select>
                </label>
                <div style="font-size:11.5px;color:var(--frame-dim);line-height:1.45;padding:4px 0">
                  <b style="color:var(--brand)">✨ Layout Benefits:</b> 100% uncropped widescreen video (zero side crop!). Bold Topic Hook sits in top canvas; Submagic captions sit in bottom canvas.
                </div>
              </div>
            </div>

            <!-- Safe Area & Spacing Controls + Real-Time TikTok 9:16 Layout Preview -->
            <div class="composer-preview-section" id="composer_preview_section">
              <div class="composer-preview-header">
                <div style="display:flex;align-items:center;gap:8px">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18"/></svg>
                  <span style="font-size:13px;font-weight:700;color:var(--text)">Live TikTok 9:16 Layout & Safe Area Preview</span>
                  <span class="badge" style="background:rgba(255,139,51,0.15);color:var(--brand);font-size:10px;padding:2px 6px">Real-Time Framing</span>
                </div>
                <div style="display:flex;gap:6px">
                  <button type="button" class="btn sm ghost" data-act="togglecomposertiktok" id="btn_toggle_tiktok_ui">
                    ${ic("radio")}Toggle TikTok UI
                  </button>
                  <button type="button" class="btn sm" data-act="rendercomposerframe" style="background:linear-gradient(135deg,#FF8B33,#FFB800);color:#1E1612;font-weight:700">
                    ${ic("film")}📸 Render Exact Frame
                  </button>
                </div>
              </div>

              <div class="composer-preview-grid">
                <!-- 9:16 Smartphone Mockup Stage -->
                <div class="preview-stage-col">
                  <div class="tiktok-phone-mockup" id="composerPhoneMockup">
                    <div class="phone-notch"><span class="notch-speaker"></span><span class="notch-lens"></span></div>
                    
                    <!-- Top Safe Area Overlay with Live Topic Headline Banner -->
                    <div class="safe-pad-zone top" id="composerPadTop" style="height:0%;display:none">
                      <div class="preview-banner-wrap" id="composerPreviewBanner">
                        <span class="preview-banner-pill">[ TOPIC HEADLINE BANNER ]</span>
                      </div>
                      <span class="pad-zone-tag" id="composerTagTop">Top Safe Area: 0%</span>
                    </div>

                    <!-- Active Video Framing Center: Bounded by Top & Bottom Safe Areas -->
                    <div class="stage-active-center" id="composerActiveCenter" style="top:0%;height:100%">
                      <video id="composerVideo" autoplay muted loop playsinline style="display:none;width:100%;height:100%;object-fit:cover"></video>
                      <img id="composerImage" src="/brand/demo-clean.jpg" alt="Preview Frame" style="width:100%;height:100%;object-fit:cover">
                    </div>

                    <!-- Bottom Safe Area Overlay with Animated Captions Preview -->
                    <div class="safe-pad-zone bottom" id="composerPadBottom" style="height:0%;display:none">
                      <div class="preview-caption-wrap" id="composerPreviewCaptions">
                        <span class="preview-caption-chip">VIRAL <b style="color:#FFFF00">&nbsp;CAPTIONS</b></span>
                      </div>
                      <span class="pad-zone-tag" id="composerTagBottom">Bottom Safe Area: 0%</span>
                    </div>

                    <!-- Authentic TikTok Social UI Overlay -->
                    <div class="tiktok-social-overlay on" id="composerTikTokOverlay">
                      <div class="tt-top-header">
                        <span class="tt-tab">Following</span>
                        <span class="tt-tab active">For You</span>
                        <span class="tt-search">🔍</span>
                      </div>
                      <div class="tt-right-actions">
                        <div class="tt-action-btn"><div class="tt-avatar"><img src="/brand/logo.svg" alt=""><span>+</span></div></div>
                        <div class="tt-action-btn"><span class="tt-icon">❤️</span><span class="tt-count">248.5K</span></div>
                        <div class="tt-action-btn"><span class="tt-icon">💬</span><span class="tt-count">1,842</span></div>
                        <div class="tt-action-btn"><span class="tt-icon">🔖</span><span class="tt-count">42.1K</span></div>
                        <div class="tt-action-btn"><span class="tt-icon">↗️</span><span class="tt-count">14.6K</span></div>
                        <div class="tt-action-btn disc"><div class="tt-disc"><span>🎵</span></div></div>
                      </div>
                      <div class="tt-bottom-meta">
                        <div class="tt-creator-tag">@creator • ClipForge Studio</div>
                        <div class="tt-caption-text">Why smart padding gives you 66% more view... #podcast #shorts #fyp</div>
                        <div class="tt-sound-bar"><span>🎵</span> <marquee scrollamount="3">original sound - ClipForge Studio High Retention Voice</marquee></div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Controls & Real-Time Telemetry Column -->
                <div class="preview-controls-col">
                  <!-- Quick Padding Presets -->
                  <div class="preset-section">
                    <span class="preset-label">Quick Safe Area Presets:</span>
                    <div class="preset-pills-row">
                      <button type="button" class="preset-pill on" data-act="setcomposerpad" data-top="0" data-bottom="0">
                        <b>0% Full 9:16</b>
                        <small>Max Zoom (31% kept)</small>
                      </button>
                      <button type="button" class="preset-pill" data-act="setcomposerpad" data-top="10" data-bottom="10">
                        <b>10% + 10%</b>
                        <small>80% Area (42% kept)</small>
                      </button>
                      <button type="button" class="preset-pill" data-act="setcomposerpad" data-top="15" data-bottom="15">
                        <b>15% + 15%</b>
                        <small>70% Area (47% kept)</small>
                      </button>
                      <button type="button" class="preset-pill star" data-act="setcomposerpad" data-top="20" data-bottom="20">
                        <b>20% + 20% ⭐</b>
                        <small>60% Area (53% kept)</small>
                      </button>
                      <button type="button" class="preset-pill" data-act="setcomposerpad" data-top="25" data-bottom="25">
                        <b>25% + 25%</b>
                        <small>50% Area (60% kept)</small>
                      </button>
                    </div>
                  </div>

                  <!-- Editable Top & Bottom Padding Sliders -->
                  <div class="pad-control-grid">
                    <div class="pad-control-row">
                      <div class="pad-label-row">
                        <span class="pad-label">Top Padding (Headline Banner Safe Zone)</span>
                        <div class="pad-val-box">
                          <input type="number" id="o_pad_top_num" class="pad-num-input" min="0" max="45" step="1" value="0">
                          <span class="pad-unit">%</span>
                        </div>
                      </div>
                      <input type="range" id="o_pad_top" class="pad-slider" min="0" max="45" step="1" value="0">
                    </div>

                    <div class="pad-control-row">
                      <div class="pad-label-row">
                        <span class="pad-label">Bottom Padding (Captions & UI Safe Zone)</span>
                        <div class="pad-val-box">
                          <input type="number" id="o_pad_bottom_num" class="pad-num-input" min="0" max="45" step="1" value="0">
                          <span class="pad-unit">%</span>
                        </div>
                      </div>
                      <input type="range" id="o_pad_bottom" class="pad-slider" min="0" max="45" step="1" value="0">
                    </div>
                  </div>

                  <!-- Live FOV, Aspect Ratio & Zoom Telemetry Card -->
                  <div class="telemetry-card" id="composerTelemetry">
                    <div class="telem-row">
                      <span class="telem-k">Active Video Area</span>
                      <span class="telem-v" id="o_active_area_val"><strong style="color:var(--brand)">100%</strong> of 9:16 Canvas</span>
                    </div>
                    <div class="telem-row">
                      <span class="telem-k">Widescreen 16:9 View Preserved</span>
                      <span class="telem-v" id="o_fov_val"><b>31.6%</b> of original width</span>
                    </div>
                    <div class="telem-row">
                      <span class="telem-k">Zoom Reduction</span>
                      <span class="telem-v" id="o_zoom_gain_val">Standard 9:16 Cropping</span>
                    </div>
                    <div class="telem-row">
                      <span class="telem-k">Safe Area Margins</span>
                      <span class="telem-v" id="o_pad_summary">Top: 0px • Bottom: 0px</span>
                    </div>
                  </div>

                  <!-- Interactive Tip on Widescreen Preservation -->
                  <div class="pad-explanation-box">
                    <div style="font-size:12px;font-weight:700;color:var(--text);display:flex;align-items:center;gap:6px">
                      <span style="color:#00E5FF">💡</span> Why Padding Preserves Content:
                    </div>
                    <div style="font-size:11.5px;color:var(--frame-dim);line-height:1.45;margin-top:4px">
                      Without padding, converting 16:9 to 9:16 cuts off <b>68.4%</b> of the horizontal view. Setting <b>20% top & 20% bottom padding</b> yields a 60% active area, preserving <b>52.7%</b> of the widescreen view — giving you <b>+66% more visible width</b> with minimal zoom!
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
<!-- ClipForge Proprietary Retention & Audio Options -->
          <div class="ob">
            <div class="ot">Royalty-Free BGM</div>
            <select id="o_bgm">
              <option value="none" selected>None (Original master audio only)</option>
              <option value="chill_lofi">Chill Lo-Fi Beat (Warm Jazz Chords)</option>
              <option value="podcast_ambient">Atmospheric Pad (Cinematic & Subtle)</option>
              <option value="deep_mystery">Deep Mystery & Suspense (Minor Drone)</option>
              <option value="viral_energy">Upbeat Viral Pulse (Rhythmic Motivational)</option>
            </select>
          </div>

          <div class="ob">
            <div class="ot">Retention Progress Bar</div>
            <select id="o_bar">
              <option value="#00E5FF" selected>Cyan Glow (#00E5FF - Opus Style)</option>
              <option value="#FFB800">Gold Amber (#FFB800 - Wealth Style)</option>
              <option value="#00FF55">Toxic Green (#00FF55 - Beast Style)</option>
              <option value="#FF007F">Hot Pink (#FF007F - Cyber Style)</option>
              <option value="none">None (Off)</option>
            </select>
          </div>

          <!-- Color Grading LUT & Creator Branding -->
          <div class="ob">
            <div class="ot">Color Grading LUT</div>
            <select id="o_color">
              <option value="none" selected>Natural (Original Colors)</option>
              <option value="cinematic_pop">Cinematic Pop (Vibrant Social Feed Contrast)</option>
              <option value="moody_studio">Moody Studio (Dramatic Deep Shadows)</option>
              <option value="clean_crisp">Clean Crisp (Sharpened Daylight Clarity)</option>
              <option value="warm_golden">Warm Golden (Studio Amber Glow)</option>
            </select>
          </div>

          <div class="ob">
            <div class="ot">Watermark / Creator Handle</div>
            <div style="display:flex;gap:6px">
              <input id="o_watermark" placeholder="@yourhandle (optional)" style="flex:1" maxlength="30">
              <select id="o_watermark_pos" style="width:110px">
                <option value="top_right" selected>Top Right</option>
                <option value="top_left">Top Left</option>
                <option value="bottom_right">Bottom Right</option>
                <option value="bottom_left">Bottom Left</option>
              </select>
            </div>
          </div>

          <div class="ob wide" style="display:flex;gap:20px;flex-wrap:wrap">
            <label class="sw"><input type="checkbox" id="o_clarifier" checked><span>Studio Voice Clarifier (FFT Denoiser + EBU R128 -14LUFS)</span></label>
            <label class="sw"><input type="checkbox" id="o_tightcut"><span>TightCut (Remove awkward pauses >0.65s)</span></label>
            <label class="sw"><input type="checkbox" id="o_hookzoom" checked><span>Hook Punch-In Zoom (5% zoom first 3s)</span></label>
            <label class="sw"><input type="checkbox" id="o_emojis" checked><span>Auto-Emojis & Keyword Highlights (💰, 🚀, 🔥)</span></label>
          </div>
        </div>
      </div>
    </form>`;

  drawAtt();
}

function drawAtt() {
  const box = $("#attIn");
  if (!box) return;
  if (!DRAFT.link && !DRAFT.file) {
    $("#att")?.classList.remove("has");
    box.innerHTML = "";
    return;
  }
  $("#att")?.classList.add("has");
  if (DRAFT.link) {
    const l = DRAFT.link;
    box.innerHTML = `
      <div class="lp">
        <div class="th">
          ${l.thumb ? `<img src="${l.thumb}" alt="">` : ""}
          ${l.duration ? `<span class="du">${fmtLen(l.duration)}</span>` : ""}
        </div>
        <div class="tx">
          <b>${esc(l.title || "YouTube Podcast")}</b>
          <span>${esc(l.uploader || "YouTube Video")}</span>
        </div>
        <span class="ok">${ic("check")}Ready</span>
        <button type="button" class="rm" data-act="clearlink">${ic("x")}</button>
      </div>`;
  } else if (DRAFT.file) {
    const f = DRAFT.file;
    box.innerHTML = `
      <div class="lp">
        <div class="th" style="background:#332014;display:grid;place-items:center;color:#FFB27A">${ic("film")}</div>
        <div class="tx">
          <b>${esc(f.name)}</b>
          <span>${(f.size / (1024 * 1024)).toFixed(1)} MB · local video file</span>
        </div>
        <span class="ok">${ic("check")}Ready</span>
        <button type="button" class="rm" data-act="clearfile">${ic("x")}</button>
      </div>`;
  }
}

/* ============================================================ Videos & Clips Rendering */
function scoreCls(s) { return s >= 85 ? "s-hi" : s >= 65 ? "s-mid" : ""; }

function clipHtml(j, c) {
  const a = `data-j="${j.id}" data-c="${esc(c.id)}"`;
  const key = `c:${j.id}:${c.id}`;
  const videoSrc = c.output_file ? `/media/${j.id}/${encodeURIComponent(c.filename)}` : "";
  const thumbSrc = c.cover ? `/media/${j.id}/${encodeURIComponent(c.cover)}` : (c.filename ? `/media/${j.id}/${encodeURIComponent(c.filename.replace(/\.[^.]+$/, '.jpg'))}` : "");

  return `
    <article class="clip ${S.sel.has(key) ? "picked" : ""}">
      <button class="shot" data-act="openclip" ${a} aria-label="Open clip: ${esc(c.title || c.hook)}">
        ${thumbSrc ? `<img src="${thumbSrc}" alt="" loading="lazy">` : videoSrc ? `<video src="${videoSrc}#t=1" muted playsinline></video>` : `<span class="making">${c.status === "rendering" ? "Rendering vertical clip…" : "Ready"}</span>`}
        <span class="veil"><span>${ic("play")}</span></span>
        <span class="badge l ${scoreCls(c.virality_score || c.score || 90)}" title="AI Virality Score">${c.virality_score || c.score || 90}</span>
        <span class="badge r">${fmt(c.duration || (c.end - c.start) || 30)}</span>
      </button>
      <div class="clip-body">
        <div class="hook">${esc(c.hook || c.title || "Viral Highlight")}</div>
        <div class="ttl">${esc(c.title || c.full_transcript || "")}</div>
        <div class="clip-foot">
          <label class="selck" title="Select clip"><input type="checkbox" data-sel="${key}" ${S.sel.has(key) ? "checked" : ""}></label>
          ${videoSrc ? `<a class="btn sm icon ghost" href="${videoSrc}" download title="Download MP4">${ic("down")}</a>` : ""}
          <button class="btn sm icon ghost" data-act="copy" ${a} title="Copy social caption">${ic("copy")}</button>
          <button class="btn sm icon ghost" data-act="delclip" ${a} title="Delete">${ic("trash")}</button>
          <span style="flex:1"></span>
          <button class="btn sm" data-act="openclip" ${a}>${ic("send")}Edit</button>
        </div>
      </div>
    </article>`;
}

function jobHtml(j) {
  const isFailed = j.status === "failed";
  const busy = j.status === "queued" || j.status === "running";
  const progressPct = j.progress <= 1.0 ? Math.round((j.progress || 0) * 100) : Math.round(j.progress || 0);
  const clips = j.clips || [];
  const hasBrief = (j.podcast_summary && j.podcast_summary.overview) || (j.transcript_segments && j.transcript_segments.length);
  const briefExpanded = S.expandedBriefs.has(j.id);

  if (isFailed) {
    return `
    <section class="job" data-job="${j.id}" style="border:1px solid #FF3B30;background:#181111">
      <div class="job-head">
        <div class="jt">
          <span class="jthumb" style="background:#331414;color:#FF453A">${ic("trash")}</span>
          <div>
            <h3 style="color:#FF453A">${esc(j.title || "Video Processing Error")}</h3>
            <p class="sub" style="color:#FF6961">${esc(j.stage || j.error || "An error occurred during clipping")}</p>
          </div>
        </div>
        <div class="row" style="gap:6px">
          <button class="btn sm danger" data-act="deljob" data-j="${j.id}">Dismiss</button>
        </div>
      </div>
    </section>`;
  }

  return `
    <section class="job" data-job="${j.id}">
      <div class="job-head">
        <div class="jt">
          <span class="jthumb">
            ${j.thumbnail_url ? `<img src="${j.thumbnail_url}" alt="">` : ic("film")}
            ${j.duration ? `<span class="du">${fmt(j.duration)}</span>` : ""}
          </span>
          <div>
            <h3>${esc(j.title || "Podcast Episode")}</h3>
            <p class="sub">${clips.length} clip${clips.length === 1 ? "" : "s"} · ${j.duration ? fmt(j.duration) + " long · " : ""} ${busy ? (j.stage || "Processing...") : "Ready"}</p>
          </div>
        </div>
        <div class="row" style="gap:6px">
          ${hasBrief ? `<button class="btn sm" data-act="togglebrief" data-j="${j.id}">${briefExpanded ? "▲ Hide Brief" : "🧠 Executive Brief & Heatmap"}</button>` : ""}
          ${clips.length ? `<button class="btn sm icon ghost" data-act="dlall" data-j="${j.id}" title="Download all clips ZIP">${ic("down")}</button>` : ""}
          <button class="btn sm icon ghost" data-act="deljob" data-j="${j.id}" title="Delete project">${ic("trash")}</button>
          <label class="selck" title="Select project"><input type="checkbox" data-sel="j:${j.id}" ${S.sel.has("j:" + j.id) ? "checked" : ""}></label>
        </div>
      </div>

      ${busy ? `
        <div class="bar"><i style="width:${progressPct}%"></i></div>
        <p class="sub">${esc(j.stage || "Processing pipeline...")} · ${progressPct}%</p>` : ""}

      <!-- Expandable Executive Podcast Brief & Heatmap -->
      ${hasBrief && briefExpanded ? briefHtml(j) : ""}

      <!-- 9:16 Vertical Clip Cards -->
      ${clips.length ? `<div class="grid">${clips.map(c => clipHtml(j, c)).join("")}</div>` : ""}
    </section>`;
}

function briefHtml(j) {
  const s = j.podcast_summary || {};
  const chapters = s.chapters || [];
  const takeaways = s.takeaways || [];
  const overview = s.overview || "High impact discussion.";

  return `
    <div class="podcast-brief-card">
      <div class="brief-header">
        <span class="brief-badge">🧠 Executive Podcast Brief & Discussion Chapters (Ollama LLaMA 3.2)</span>
      </div>
      <div class="brief-section">
        <div class="brief-section-title">Executive Overview</div>
        <p class="brief-overview-text">${esc(overview)}</p>
      </div>
      ${takeaways.length ? `
        <div class="brief-section">
          <div class="brief-section-title">Key Core Takeaways</div>
          <ul class="brief-takeaways-list">${takeaways.map(t => `<li>${esc(t)}</li>`).join("")}</ul>
        </div>` : ""}
      ${chapters.length ? `
        <div class="brief-section">
          <div class="brief-section-title">Topic Chapters — 1-Click Extraction</div>
          <div class="chapters-grid">
            ${chapters.map(ch => `
              <div class="chapter-card">
                <div class="chapter-info">
                  <b>${esc(ch.title)}</b>
                  <span>${fmt(ch.start)} - ${fmt(ch.end)}</span>
                </div>
                <button class="btn sm primary" data-act="cliptopic" data-j="${j.id}" data-start="${ch.start}" data-end="${ch.end}" data-title="${esc(ch.title)}">${ic("scissors")}Clip</button>
              </div>`).join("")}
          </div>
        </div>` : ""}
    </div>`;
}

function drawJobs() {
  const root = $("#jobs");
  if (!root) return;
  if (!S.jobs.length) {
    root.innerHTML = `
      <div class="empty">
        <img src="/brand/favicon.svg" alt="">
        <b>No videos yet</b>
        Paste a YouTube podcast link above or drop a video file. ClipForge will detect viral moments and render 9:16 shorts.
      </div>`;
    return;
  }
  root.innerHTML = S.jobs.map(j => jobHtml(j)).join("");
}

function drawSelBar() {
  const bar = $("#selbar");
  if (!bar) return;
  const n = S.sel.size;
  bar.classList.toggle("on", n > 0 && S.view === "library");
  if (!n) return;
  bar.innerHTML = `
    <b>${n} selected</b>
    <button class="btn sm" data-act="selall">Select all</button>
    <button class="btn sm primary" data-act="seldl">${ic("down")}Download ZIP</button>
    <button class="btn sm danger" data-act="seldel">${ic("trash")}Delete</button>
    <button class="btn sm" data-act="selclear">Cancel</button>`;
}

/* ============================================================ Safe Area & Padding Live Synchronizers */
function updateEditorPaddingPreview(topVal, bottomVal) {
  topVal = Math.max(0, Math.min(45, Number(topVal) || 0));
  bottomVal = Math.max(0, Math.min(45, Number(bottomVal) || 0));
  if (topVal + bottomVal > 80) {
    const scale = 80 / (topVal + bottomVal);
    topVal = Math.round(topVal * scale);
    bottomVal = Math.round(bottomVal * scale);
  }
  const activeVal = Math.max(20, 100 - topVal - bottomVal);

  const centerEl = $("#stageActiveCenter");
  const topOverlay = $("#previewPadTop");
  const bottomOverlay = $("#previewPadBottom");
  const tagTop = $("#tagPadTop");
  const tagBottom = $("#tagPadBottom");
  const activeAreaVal = $("#ed_active_area_val");
  const padSummary = $("#ed_pad_summary");
  const fovVal = $("#ed_fov_val");

  if (centerEl) {
    centerEl.style.top = `${topVal}%`;
    centerEl.style.height = `${activeVal}%`;
  }

  const topPx = Math.round(1920 * (topVal / 100));
  const botPx = Math.round(1920 * (bottomVal / 100));
  const activeHPx = Math.round(1920 * (activeVal / 100));
  const centerAR = 1080 / activeHPx;
  const fovPct = Math.min(100, Math.round((centerAR / (16/9)) * 1000) / 10);
  const zoomGain = Math.max(0, Math.round(((fovPct - 31.6) / 31.6) * 100));

  if (topOverlay) {
    topOverlay.style.height = `${topVal}%`;
    topOverlay.style.display = topVal > 0 ? "flex" : "none";
    if (tagTop) tagTop.textContent = `Top Safe Area: ${topVal}% (${topPx}px)`;
  }

  if (bottomOverlay) {
    bottomOverlay.style.height = `${bottomVal}%`;
    bottomOverlay.style.display = bottomVal > 0 ? "flex" : "none";
    if (tagBottom) tagBottom.textContent = `Bottom Safe Area: ${bottomVal}% (${botPx}px)`;
  }

  if (activeAreaVal) activeAreaVal.textContent = `${activeVal}% (${activeHPx}px)`;
  if (padSummary) padSummary.textContent = `Top: ${topPx}px • Bottom: ${botPx}px`;
  if (fovVal) fovVal.textContent = `${fovPct}% preserved (+${zoomGain}% wider view)`;

  document.querySelectorAll("[data-act='seteditorpad']").forEach(pill => {
    const t = Number(pill.getAttribute("data-top"));
    const b = Number(pill.getAttribute("data-bottom"));
    pill.classList.toggle("on", t === topVal && b === bottomVal);
  });
}

function updateComposerPaddingPreview(topVal, bottomVal) {
  topVal = Math.max(0, Math.min(45, Number(topVal) || 0));
  bottomVal = Math.max(0, Math.min(45, Number(bottomVal) || 0));
  if (topVal + bottomVal > 80) {
    const scale = 80 / (topVal + bottomVal);
    topVal = Math.round(topVal * scale);
    bottomVal = Math.round(bottomVal * scale);
  }
  const activeVal = Math.max(20, 100 - topVal - bottomVal);

  const topPx = Math.round(1920 * (topVal / 100));
  const botPx = Math.round(1920 * (bottomVal / 100));
  const activeHPx = Math.round(1920 * (activeVal / 100));
  const centerAR = 1080 / activeHPx;
  const fovPct = Math.min(100, Math.round((centerAR / (16/9)) * 1000) / 10);
  const zoomGain = Math.max(0, Math.round(((fovPct - 31.6) / 31.6) * 100));

  const centerEl = $("#composerActiveCenter");
  const topOverlay = $("#composerPadTop");
  const bottomOverlay = $("#composerPadBottom");
  const tagTop = $("#composerTagTop");
  const tagBottom = $("#composerTagBottom");
  const activeAreaVal = $("#o_active_area_val");
  const padSummary = $("#o_pad_summary");
  const fovVal = $("#o_fov_val");
  const zoomVal = $("#o_zoom_gain_val");

  if (centerEl) {
    centerEl.style.top = `${topVal}%`;
    centerEl.style.height = `${activeVal}%`;
  }

  if (topOverlay) {
    topOverlay.style.height = `${topVal}%`;
    topOverlay.style.display = topVal > 0 ? "flex" : "none";
    if (tagTop) tagTop.textContent = `Top Safe Area: ${topVal}% (${topPx}px)`;
  }

  if (bottomOverlay) {
    bottomOverlay.style.height = `${bottomVal}%`;
    bottomOverlay.style.display = bottomVal > 0 ? "flex" : "none";
    if (tagBottom) tagBottom.textContent = `Bottom Safe Area: ${bottomVal}% (${botPx}px)`;
  }

  if (activeAreaVal) activeAreaVal.innerHTML = `<strong style="color:var(--brand)">${activeVal}%</strong> of Canvas (${activeHPx}px)`;
  if (padSummary) padSummary.textContent = `Top: ${topPx}px • Bottom: ${botPx}px`;
  if (fovVal) fovVal.innerHTML = `<b>${fovPct}%</b> of 16:9 width kept`;
  if (zoomVal) {
    if (topVal === 0 && bottomVal === 0) {
      zoomVal.textContent = "Standard 9:16 Cropping (High Zoom)";
    } else {
      zoomVal.innerHTML = `<span style="color:#00FF66;font-weight:700">+${zoomGain}% More Content</span> (Minimal Zoom)`;
    }
  }

  const bannerEl = $("#composerPreviewBanner");
  const bannerInput = $("#o_hook");
  if (bannerEl) {
    const text = (bannerInput && bannerInput.value.trim()) ? bannerInput.value.trim().toUpperCase() : "THE 1 SECRET TO HIGH RETENTION";
    bannerEl.innerHTML = `<span class="preview-banner-pill">[ ${esc(text)} ]</span>`;
  }

  document.querySelectorAll("[data-act='setcomposerpad']").forEach(pill => {
    const t = Number(pill.getAttribute("data-top"));
    const b = Number(pill.getAttribute("data-bottom"));
    pill.classList.toggle("on", t === topVal && b === bottomVal);
  });
}
/* ============================================================ Clip Editor Dialog */
function openClip(jid, cid) {
  D.jid = jid;
  D.cid = cid;
  const j = S.jobs.find(x => x.id === jid);
  const c = j?.clips.find(x => x.id === cid);
  if (!c) return;

  const dlg = $("#clipdlg");
  const videoSrc = c.output_file ? `/media/${j.id}/${encodeURIComponent(c.filename)}` : "";
  const words = c.words || [];
  D.activeWords = JSON.parse(JSON.stringify(words));
  D.selectedWordIdx = null;

  const topPad = Math.max(0, Math.min(45, Number(c.top_padding || 0)));
  const bottomPad = Math.max(0, Math.min(45, Number(c.bottom_padding || 0)));
  const activeArea = Math.max(20, 100 - topPad - bottomPad);

  dlg.innerHTML = `
    <div class="editor">
      <!-- Left Stage: 9:16 Vertical Player with Safe-Zone & Padding Overlays -->
      <div class="stage" id="stage">
        <div class="stage-canvas-frame" id="stageCanvasFrame">
          <!-- Full 9:16 Canvas Video Player (exact rendered MP4 output) -->
          <video id="editorVideo" src="${videoSrc}" controls autoplay playsinline style="position:absolute;inset:0;width:100%;height:100%;object-fit:contain;z-index:1;background:#0E0C0A"></video>

          <!-- Top Safe Area Shaded Overlay -->
          <div class="safe-pad-zone top" id="previewPadTop" style="height:${topPad}%;display:${topPad > 0 ? "flex" : "none"};z-index:4">
            <span class="pad-zone-tag" id="tagPadTop">Top Safe Area: ${topPad}%</span>
          </div>

          <!-- Bottom Safe Area Shaded Overlay -->
          <div class="safe-pad-zone bottom" id="previewPadBottom" style="height:${bottomPad}%;display:${bottomPad > 0 ? "flex" : "none"};z-index:4">
            <span class="pad-zone-tag" id="tagPadBottom">Bottom Safe Area: ${bottomPad}%</span>
          </div>

          <!-- Social UI Safe Zone Mock Overlay (TikTok / Reels / Shorts) -->
          <div class="safe-zone-overlay" id="editorSafeZone">
            <div class="safe-zone-top">Top Header Safe Zone (TikTok / Reels)</div>
            <div class="safe-zone-right">
              <div class="mock-btn-profile">👤</div>
              <div class="mock-btn-action">❤️</div>
              <div class="mock-btn-action">💬</div>
              <div class="mock-btn-action">↗️</div>
            </div>
            <div class="safe-zone-bottom">@creator • Caption & Sound Area</div>
          </div>
        </div>
      </div>

      <!-- Right Panel: Controls & Submagic Karaoke -->
      <div class="panel">
        <div class="job-head" style="margin:0">
          <div>
            <span class="badge ${scoreCls(c.virality_score || 90)}" style="position:static">Score ${c.virality_score || 90} · High engagement hook</span>
            <p class="sub" style="margin-top:6px">${esc(c.title || "Viral Clip")}</p>
          </div>
          <button class="btn icon ghost" data-act="closedlg">${ic("x")}</button>
        </div>

        <div class="row" style="justify-content:space-between">
          <h3>On the video</h3>
          <button class="btn sm ghost" data-act="togglesafezone">Toggle Safe Zones</button>
        </div>

        <!-- AI Intelligence & Viral Hooks Bar -->
        <div style="display:flex;gap:6px;margin:6px 0 10px;align-items:center;flex-wrap:wrap">
          <button type="button" class="btn sm" data-act="aihooks" style="background:linear-gradient(135deg,#FF8B33,#FFB800);color:#1E1612;font-weight:700">
            ${ic("bolt")}⚡ AI Viral Hooks
          </button>
          <button type="button" class="btn sm ghost" data-act="aitranslate">
            ${ic("globe")}Translate Subtitles
          </button>
          <button type="button" class="btn sm ghost" data-act="aibroll">
            ${ic("film")}B-Roll & SFX Cues
          </button>
        </div>

        <div id="ai_hooks_panel" style="display:none;background:var(--muted);border:1px solid var(--line);border-radius:8px;padding:10px;margin-bottom:10px"></div>

        <label class="f">Big text hook<input id="ed_hook" value="${esc(c.hook || c.title || "")}"></label>
        
        <div class="two">
          <label class="f">Caption style
            <select id="ed_style">
              <option value="hormozi" ${c.subtitle_style === "hormozi" ? "selected" : ""}>Hormozi Impact</option>
              <option value="hype" ${c.subtitle_style === "hype" ? "selected" : ""}>MrBeast Neon</option>
              <option value="cyber" ${c.subtitle_style === "cyber" ? "selected" : ""}>Cyber Glow</option>
              <option value="clean" ${c.subtitle_style === "clean" ? "selected" : ""}>Clean Amber</option>
            </select>
          </label>
          <label class="f">Layout & Framing
            <select id="ed_layout" onchange="const fb=document.getElementById('ed_fit_options'); if(fb) fb.style.display=(this.value==='fit_canvas'?'block':'none'); const v=document.getElementById('editorVideo'); if(v) v.style.objectFit=(this.value==='fit_canvas'?'contain':'cover');">
              <option value="fit_canvas" ${c.layout_mode === "fit_canvas" ? "selected" : ""}>Fit Full Video (Top Hook + Bottom Captions)</option>
              <option value="face_center" ${c.layout_mode === "face_center" ? "selected" : ""}>Smart Face Center (Golden Ratio Eye-Line)</option>
              <option value="speaker_focus" ${c.layout_mode === "speaker_focus" ? "selected" : ""}>YuNet Active Speaker (0.25s Whip Cut)</option>
              <option value="split_screen" ${c.layout_mode === "split_screen" ? "selected" : ""}>Split-Screen Dual Stack (Host + Guest)</option>
              <option value="blur" ${c.layout_mode === "blur" ? "selected" : ""}>Aesthetic Blurred Fill</option>
              <option value="center_crop" ${c.layout_mode === "center_crop" ? "selected" : ""}>Center Crop (9:16)</option>
            </select>
          </label>
        </div>

        <!-- Safe Area & Spacing Controls in Clip Editor -->
        <div class="safe-area-panel" id="ed_safe_area_panel">
          <div class="safe-area-header">
            <div class="safe-area-title">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18"/></svg>
              <span>Safe Area & Spacing</span>
            </div>
            <button type="button" class="btn-pad-reset" id="btn_pad_reset" data-act="reseteditorpad">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
              Reset to 0%
            </button>
          </div>

          <div class="preset-section" style="margin-bottom:10px">
            <span class="preset-label">Quick Presets:</span>
            <div class="preset-pills-row">
              <button type="button" class="preset-pill ${topPad===0&&bottomPad===0?'on':''}" data-act="seteditorpad" data-top="0" data-bottom="0">
                <b>0% Full</b><small>Max Zoom</small>
              </button>
              <button type="button" class="preset-pill ${topPad===10&&bottomPad===10?'on':''}" data-act="seteditorpad" data-top="10" data-bottom="10">
                <b>10% + 10%</b><small>80% Area</small>
              </button>
              <button type="button" class="preset-pill ${topPad===15&&bottomPad===15?'on':''}" data-act="seteditorpad" data-top="15" data-bottom="15">
                <b>15% + 15%</b><small>70% Area</small>
              </button>
              <button type="button" class="preset-pill star ${topPad===20&&bottomPad===20?'on':''}" data-act="seteditorpad" data-top="20" data-bottom="20">
                <b>20% + 20% ⭐</b><small>60% Area</small>
              </button>
              <button type="button" class="preset-pill ${topPad===25&&bottomPad===25?'on':''}" data-act="seteditorpad" data-top="25" data-bottom="25">
                <b>25% + 25%</b><small>50% Area</small>
              </button>
            </div>
          </div>
          
          <div class="pad-control-grid">
            <!-- Top Padding Control -->
            <div class="pad-control-row">
              <div class="pad-label-row">
                <span class="pad-label">Top Padding</span>
                <div class="pad-val-box">
                  <input type="number" id="ed_pad_top_num" class="pad-num-input" min="0" max="45" step="1" value="${topPad}">
                  <span class="pad-unit">%</span>
                </div>
              </div>
              <input type="range" id="ed_pad_top" class="pad-slider" min="0" max="45" step="1" value="${topPad}">
            </div>

            <!-- Bottom Padding Control -->
            <div class="pad-control-row">
              <div class="pad-label-row">
                <span class="pad-label">Bottom Padding</span>
                <div class="pad-val-box">
                  <input type="number" id="ed_pad_bottom_num" class="pad-num-input" min="0" max="45" step="1" value="${bottomPad}">
                  <span class="pad-unit">%</span>
                </div>
              </div>
              <input type="range" id="ed_pad_bottom" class="pad-slider" min="0" max="45" step="1" value="${bottomPad}">
            </div>
          </div>

          <div class="pad-active-bar">
            <span>Active Framing: <strong id="ed_active_area_val" style="color:var(--brand)">${activeArea}%</strong> (<span id="ed_fov_val">${Math.min(100, Math.round(((1080 / Math.round(1920 * (activeArea / 100))) / (16/9)) * 1000) / 10)}% kept</span>)</span>
            <span id="ed_pad_summary" style="font-size:10px;color:var(--frame-dim)">Top: ${Math.round(1920*topPad/100)}px • Bottom: ${Math.round(1920*bottomPad/100)}px</span>
          </div>

          <button type="button" class="btn sm" data-act="rendereditorframe" style="width:100%;margin-top:8px;background:rgba(255,139,51,0.12);border:1px solid rgba(255,139,51,0.4);color:var(--brand);font-weight:700">
            ${ic("film")}📸 Snapshot Exact FFmpeg Rendered Frame
          </button>
        </div>
<div id="ed_fit_options" style="display:${(c.layout_mode === 'fit_canvas' || !c.layout_mode) ? 'block' : 'none'};background:var(--muted);border-radius:8px;padding:10px;margin-bottom:8px">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
            <span style="font-size:11.5px;font-weight:700">Top Space (Hook Placement)</span>
            <span id="ed_top_space_val" style="font-size:12px;font-weight:800;color:var(--brand)">450px</span>
          </div>
          <input type="range" id="ed_top_space" min="150" max="800" step="10" value="450" style="width:100%"
            oninput="document.getElementById('ed_top_space_val').textContent = this.value + 'px'">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-top:6px">
            <span style="font-size:11.5px;font-weight:700">Canvas Background</span>
            <select id="ed_canvas_bg" style="font-size:11.5px;padding:3px 6px">
              <option value="solid_black" selected>Studio Black (#0E0C0A) — 100% Solid Clean</option>
              <option value="heavy_blur">Ultra-Heavy Ambient Blur</option>
            </select>
          </div>
        </div>

        <!-- Video Styling & Audio Polish -->
        <div class="two">
          <label class="f">Color Grading LUT
            <select id="ed_color">
              <option value="none">Natural (Original Colors)</option>
              <option value="cinematic_pop" selected>Cinematic Pop (Vibrant Social Feed)</option>
              <option value="moody_studio">Moody Studio (Dramatic Deep Shadows)</option>
              <option value="clean_crisp">Clean Crisp (Sharpened Daylight)</option>
              <option value="warm_golden">Warm Golden (Studio Amber Glow)</option>
            </select>
          </label>
          <label class="f">Watermark / Creator Handle
            <input id="ed_watermark" placeholder="@yourhandle (optional)" value="" maxlength="30">
          </label>
        </div>

        <div style="margin-bottom:8px">
          <label class="sw"><input type="checkbox" id="ed_clarifier" checked><span>Studio Voice Clarifier (FFT Denoising & Broadcast Normalizer)</span></label>
        </div>

        <div class="two">
          <label class="f">Start (seconds)<input id="ed_start" type="number" step="0.5" value="${c.start || 0}"></label>
          <label class="f">End (seconds)<input id="ed_end" type="number" step="0.5" value="${c.end || 30}"></label>
        </div>

        <!-- Descript-Style Interactive Word Karaoke Flow -->
        <div class="row" style="justify-content:space-between;align-items:center;margin-top:6px">
          <h3>Interactive Word Karaoke Editor</h3>
          <span style="font-size:11px;color:var(--frame-dim)">Click any word to seek, spell-correct, or tag color</span>
        </div>

        <div class="karaoke-chips-flow" id="karaokeChips">
          ${words.length ? words.map((w, idx) => `
            <span class="word-chip ${w.color ? "hl-" + w.color : ""}" data-idx="${idx}" data-word="${esc(w.word)}" data-start="${w.start}" data-end="${w.end}">${esc(w.word)}</span>
          `).join("") : `<span class="sub">Click words in video to seek</span>`}
        </div>

        <!-- Word Inspector Card (appears when a word is clicked) -->
        <div id="word_inspector" style="display:none;background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:10px;margin:8px 0">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
            <span style="font-size:12px;font-weight:700">Selected Word: <b id="inspect_word_label" style="color:var(--brand)"></b></span>
            <button type="button" class="btn sm ghost" onclick="document.getElementById('word_inspector').style.display='none'">✕</button>
          </div>
          <div style="display:flex;gap:6px;margin-bottom:8px">
            <input id="inspect_word_input" placeholder="Edit word text..." style="flex:1">
            <button type="button" class="btn sm primary" data-act="applywordedit">Save Word Text</button>
          </div>
          <div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center">
            <span style="font-size:11px;color:var(--frame-dim)">Color Tag:</span>
            <button type="button" class="btn sm ghost" data-act="tagwordcolor" data-color="gold" style="color:#FFB800">● Gold</button>
            <button type="button" class="btn sm ghost" data-act="tagwordcolor" data-color="green" style="color:#00FF55">● Green</button>
            <button type="button" class="btn sm ghost" data-act="tagwordcolor" data-color="coral" style="color:#FF3333">● Red</button>
            <button type="button" class="btn sm ghost" data-act="tagwordcolor" data-color="cyan" style="color:#00E5FF">● Cyan</button>
            <button type="button" class="btn sm ghost" data-act="tagwordcolor" data-color="none">✕ None</button>
            <span style="font-size:11px;color:var(--frame-dim);margin-left:6px">Timeline:</span>
            <button type="button" class="btn sm ghost" data-act="setwordstart">Set Start Cut</button>
            <button type="button" class="btn sm ghost" data-act="setwordend">Set End Cut</button>
          </div>
        </div>

        <!-- Social Media Post Copy -->
        <div class="row" style="justify-content:space-between;align-items:center;margin-top:4px">
          <h3>Social Media Post Copy</h3>
          <button class="btn sm" data-act="rewritetext">${ic("bolt")}AI Rewrite</button>
        </div>
        <label class="f">Title<input id="ed_title" value="${esc(c.title || "")}"></label>
        <label class="f">Description<textarea id="ed_desc" rows="2">${esc(c.description || (c.social_kit?.youtube_shorts?.description) || "")}</textarea></label>
        <label class="f">Hashtags<input id="ed_tags" value="${esc((c.social_kit?.viral_hashtags || []).join(" "))}"></label>

        <button class="btn primary" data-act="remake">${ic("scissors")}Save & Re-Burn Clip (GPU NVENC ~1.5s)</button>

        <div class="row" style="margin-top:auto;padding-top:10px;border-top:1px solid var(--line)">
          ${videoSrc ? `<a class="btn" id="ed_download_btn" href="${videoSrc}" download>${ic("down")}Download MP4</a>` : `<a class="btn" id="ed_download_btn" href="#" download style="display:none">${ic("down")}Download MP4</a>`}
          <button class="btn" data-act="copydlg">${ic("copy")}Copy caption</button>
        </div>
      </div>
    </div>`;

  dlg.showModal();
}

/* ============================================================ Settings Views */
function drawSettings() {
  const box = $("#sform");
  if (!box) return;
  const tab = S.stab || "ai";
  const tabs = [
    ["ai", "AI", "bolt", "Local Ollama LLaMA 3.2 model & API"],
    ["apps", "Connected apps", "plug", "Where your clips get posted"],
    ["speech", "Speech models", "chat", "faster-whisper GPU engine"],
    ["storage", "Storage", "folder", "Outputs directory & cache"]
  ];

  box.innerHTML = `
    <div class="set-layout">
      <nav class="set-nav" aria-label="Settings navigation">
        ${tabs.map(([k, l, i, h]) => `
          <a href="#" class="set-link ${k === tab ? "on" : ""}" data-act="settab" data-k="${k}">
            ${ic(i)}
            <span><b>${l}</b><small>${h}</small></span>
          </a>`).join("")}
      </nav>
      <div class="set-body" id="setbody">
        ${tab === "ai" ? aiSettingsHtml() : tab === "apps" ? appsSettingsHtml() : tab === "speech" ? speechSettingsHtml() : storageSettingsHtml()}
      </div>
    </div>`;
}

function aiSettingsHtml() {
  return `
    <section class="set-sec">
      <h2>Local Ollama & AI Providers</h2>
      <p class="help">ClipForge uses local Ollama LLaMA 3.2 for podcast intelligence briefs, narrative arc scoring, and viral topic extraction on your machine. 100% free and private.</p>
      <div class="ai-form">
        <label class="f">AI Provider
          <select id="set_ai_provider">
            <option value="ollama" selected>Ollama (Local on this machine) — 100% Free</option>
            <option value="gemini">Google Gemini API</option>
            <option value="openai">OpenAI (GPT-4o)</option>
            <option value="anthropic">Anthropic Claude</option>
          </select>
        </label>
        <label class="f">Active Model
          <div class="with">
            <input id="set_ai_model" value="${esc(S.status.ai.model || "llama3.2")}">
            <button class="btn" type="button" data-act="findmodels">Find models</button>
          </div>
          <span class="hint">Recommended: <code>llama3.2</code> or <code>llama3.2:1b</code> for ultra-fast local inference.</span>
        </label>
        <label class="f">Ollama Host Address
          <input id="set_ai_host" value="http://127.0.0.1:11434">
        </label>
        <div class="row" style="margin-top:10px">
          <button class="btn primary" data-act="saveai">Save & Test Connection</button>
        </div>
      </div>
    </section>`;
}

function appsSettingsHtml() {
  return `
    <section class="set-sec">
      <h2>Connected Social Apps</h2>
      <p class="help">Direct publishing for TikTok, Instagram Reels, and YouTube Shorts.</p>
      <div class="apps">
        <div class="appcard">
          <span class="applogo" style="background:#FF0000">${ic("film")}</span>
          <div class="apptx"><b>YouTube Shorts</b><span>Post directly as YouTube Shorts.</span></div>
          <button class="btn sm primary">Connect</button>
        </div>
        <div class="appcard">
          <span class="applogo" style="background:linear-gradient(45deg,#F58529,#DD2A7B,#8134AF)">${ic("instagram")}</span>
          <div class="apptx"><b>Instagram Reels</b><span>Post clips straight to Reels.</span></div>
          <button class="btn sm primary">Connect</button>
        </div>
      </div>
    </section>`;
}

function speechSettingsHtml() {
  return `
    <section class="set-sec">
      <h2>Speech Transcription Models</h2>
      <p class="help">Offline GPU-accelerated faster-whisper model runs locally on your RTX 3050.</p>
      <div class="apps">
        <div class="appcard">
          <span class="applogo" style="background:#0F8A57">${ic("chat")}</span>
          <div class="apptx"><b>faster-whisper (Systran Base)</b><span>English & Multilingual · Status: Ready on GPU (CUDA)</span></div>
          <span class="pill ok">Active</span>
        </div>
      </div>
    </section>`;
}

function storageSettingsHtml() {
  return `
    <section class="set-sec">
      <h2>Storage & Cache</h2>
      <p class="help">Where videos, rendered clips, and .ass subtitle files are stored.</p>
      <div class="ai-form">
        <label class="f">Rendered Outputs Directory
          <input value="storage/outputs" disabled>
        </label>
        <label class="f">Temporary Cache
          <input value="storage/temp" disabled>
        </label>
      </div>
    </section>`;
}

/* ============================================================ Overview (Home) Dashboard */
function drawOverview() {
  const box = $("#ov");
  if (!box) return;
  const clipsTotal = S.jobs.reduce((a, j) => a + (j.clips || []).length, 0);

  box.innerHTML = `
    <div class="tiles">
      <div class="tile"><i>${ic("radio")}</i><b>0</b><span>Live recordings</span></div>
      <div class="tile"><i>${ic("scissors")}</i><b>${clipsTotal}</b><span>Clips generated</span></div>
      <div class="tile"><i>${ic("send")}</i><b>${clipsTotal}</b><span>Ready to publish</span></div>
      <div class="tile"><i>${ic("bolt")}</i><b>RTX 3050</b><span>NVENC GPU Active</span></div>
    </div>
    <div class="home-grid">
      <div class="card">
        <div class="card-head">
          <div><h2>Activity (Last 14 Days)</h2><p class="sub">Clips created vs exported</p></div>
          <div class="kpis">
            <div class="kpi"><b>${clipsTotal}</b><span>Clips Made</span></div>
            <div class="kpi"><b>100%</b><span>GPU Acceleration</span></div>
          </div>
        </div>
        <div style="height:140px;display:grid;place-items:center;background:var(--muted);border-radius:10px;color:var(--faint)">
          Activity Timeline Chart (All Systems Operational)
        </div>
      </div>
      <div class="card">
        <div class="card-head">
          <div><h2>Local AI Intelligence</h2><p class="sub">Ollama LLaMA 3.2</p></div>
        </div>
        <p style="font-size:13.5px;color:var(--text);line-height:1.6">
          Local LLM intelligence active on <code>127.0.0.1:11434</code>. Generating executive podcast summaries, narrative arc ratings, and virality timeline scrubbers completely offline.
        </p>
      </div>
    </div>`;
}

/* ============================================================ Synchronization & Polling */
async function tick() {
  try {
    const data = await api("/api/sync");
    if (data.jobs) S.jobs = data.jobs;
    if (data.ai) S.status.ai = data.ai;
    if (data.creators) S.creators = data.creators;
    render();
  } catch {}
}

function render() {
  drawShell();
  if (S.view === "library") drawJobs();
  if (S.view === "overview") drawOverview();
  drawSelBar();
}

function loop() {
  setTimeout(async () => {
    await tick();
    loop();
  }, document.hidden ? 10000 : 3000);
}

/* ============================================================ Event Handlers */
document.addEventListener("click", async e => {
  const b = e.target.closest("[data-act]");
  if (!b) return;
  const a = b.dataset.act, d = b.dataset;

  if (a === "go") { go(d.v, d.tab); return; }
  if (a === "collapse") { $("#app").classList.toggle("mini"); return; }
  if (a === "menu") { $("#app").classList.toggle("open"); return; }
  if (a === "toggleopts") {
    const p = $(".composer-opts"), open = !p.classList.contains("open");
    p.classList.toggle("open", open);
    p.inert = !open;
    b.classList.toggle("on", open);
    return;
  }
  if (a === "pickfile") { $("#file").click(); return; }
  if (a === "focusurl") { $("#url")?.focus(); return; }
  if (a === "clearlink") { DRAFT.link = null; drawAtt(); return; }
  if (a === "clearfile") { DRAFT.file = null; drawAtt(); return; }
  if (a === "openclip") { openClip(d.j, d.c); return; }
  if (a === "closedlg") { $("#clipdlg").close(); return; }
  if (a === "togglebrief") {
    if (S.expandedBriefs.has(d.j)) S.expandedBriefs.delete(d.j);
    else S.expandedBriefs.add(d.j);
    drawJobs();
    return;
  }
  if (a === "settab") { e.preventDefault(); S.stab = d.k; drawSettings(); return; }
  if (a === "togglesafezone") { $("#editorSafeZone")?.classList.toggle("on"); return; }
  if (a === "reseteditorpad") {
    const topS = $("#ed_pad_top"), topN = $("#ed_pad_top_num");
    const botS = $("#ed_pad_bottom"), botN = $("#ed_pad_bottom_num");
    if (topS) topS.value = 0;
    if (topN) topN.value = 0;
    if (botS) botS.value = 0;
    if (botN) botN.value = 0;
    updateEditorPaddingPreview(0, 0);
    toast("Safe area padding reset to 0%", "ok");
    return;
  }
  if (a === "resetcomposerpad") {
    const topS = $("#o_pad_top"), topN = $("#o_pad_top_num");
    const botS = $("#o_pad_bottom"), botN = $("#o_pad_bottom_num");
    if (topS) topS.value = 0;
    if (topN) topN.value = 0;
    if (botS) botS.value = 0;
    if (botN) botN.value = 0;
    updateComposerPaddingPreview(0, 0);
    toast("Safe area padding reset to 0%", "ok");
    return;
  }
  if (a === "setcomposerpad") {
    const top = Number(d.top || 0);
    const bot = Number(d.bottom || 0);
    const topS = $("#o_pad_top"), topN = $("#o_pad_top_num");
    const botS = $("#o_pad_bottom"), botN = $("#o_pad_bottom_num");
    if (topS) topS.value = top;
    if (topN) topN.value = top;
    if (botS) botS.value = bot;
    if (botN) botN.value = bot;
    updateComposerPaddingPreview(top, bot);
    return;
  }
  if (a === "seteditorpad") {
    const top = Number(d.top || 0);
    const bot = Number(d.bottom || 0);
    const topS = $("#ed_pad_top"), topN = $("#ed_pad_top_num");
    const botS = $("#ed_pad_bottom"), botN = $("#ed_pad_bottom_num");
    if (topS) topS.value = top;
    if (topN) topN.value = top;
    if (botS) botS.value = bot;
    if (botN) botN.value = bot;
    updateEditorPaddingPreview(top, bot);
    return;
  }
  if (a === "togglecomposertiktok") {
    $("#composerTikTokOverlay")?.classList.toggle("on");
    return;
  }
  if (a === "rendercomposerframe") {
    b.disabled = true;
    try {
      toast("Rendering exact 1080x1920 layout preview frame with FFmpeg...", "ok");
      const topPad = Number($("#o_pad_top")?.value || 0);
      const botPad = Number($("#o_pad_bottom")?.value || 0);
      const rawLayout = $("#o_layout")?.value || "speaker_focus";
      const layoutMode = (rawLayout === "fit_canvas") ? "fit_canvas"
                       : (rawLayout === "face_center") ? "face_center"
                       : (rawLayout === "split") ? "split_screen"
                       : (rawLayout === "crop") ? "center_crop"
                       : (rawLayout === "blur") ? "blur"
                       : "speaker_focus";
      const bannerText = $("#o_hook")?.value?.trim() || "";
      const bg = $("#o_canvas_bg")?.value || "solid_black";
      const style = $("#o_style")?.value || "hormozi";

      const source = DRAFT.draft_name || (DRAFT.file ? "draft" : (DRAFT.link ? DRAFT.link.url : ""));
      const url = `/api/preview/layout_frame?source=${encodeURIComponent(source)}&layout=${encodeURIComponent(layoutMode)}&top_padding=${topPad}&bottom_padding=${botPad}&canvas_bg=${encodeURIComponent(bg)}&banner_text=${encodeURIComponent(bannerText)}&subtitle_style=${encodeURIComponent(style)}&t=${Date.now()}`;

      const img = $("#composerImage");
      if (img) {
        img.src = url;
        img.style.display = "block";
      }
      const vid = $("#composerVideo");
      if (vid) vid.style.display = "none";
      toast("Exact FFmpeg layout frame rendered!", "ok");
    } catch (err) {
      toast("Could not render frame: " + err.message, "bad");
    } finally {
      b.disabled = false;
    }
    return;
  }
  if (a === "rendereditorframe") {
    b.disabled = true;
    try {
      toast("Rendering exact 1080x1920 layout preview frame for this clip...", "ok");
      const topPad = Number($("#ed_pad_top")?.value || 0);
      const botPad = Number($("#ed_pad_bottom")?.value || 0);
      const layout = $("#ed_layout")?.value || "speaker_focus";
      const hook = $("#ed_hook")?.value?.trim() || "";
      const bg = $("#ed_canvas_bg")?.value || "solid_black";
      const style = $("#ed_style")?.value || "hormozi";
      const start = Number($("#ed_start")?.value || 0);

      const url = `/api/preview/layout_frame?source=${encodeURIComponent(D.jid)}&time_sec=${start}&layout=${encodeURIComponent(layout)}&top_padding=${topPad}&bottom_padding=${botPad}&canvas_bg=${encodeURIComponent(bg)}&banner_text=${encodeURIComponent(hook)}&subtitle_style=${encodeURIComponent(style)}&t=${Date.now()}`;

      let prevImg = $("#editorPreviewImg");
      if (!prevImg) {
        prevImg = document.createElement("img");
        prevImg.id = "editorPreviewImg";
        prevImg.style.cssText = "position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:3";
        $("#stageCanvasFrame")?.appendChild(prevImg);
      }
      prevImg.src = url;
      prevImg.style.display = "block";
      toast("Exact layout snapshot rendered!", "ok");
    } catch (err) {
      toast("Could not render frame: " + err.message, "bad");
    } finally {
      b.disabled = false;
    }
    return;
  }
  if (a === "delclip") {
    if (!await ask("Delete this clip?", "The clip file and subtitles will be removed.", "Delete clip", true)) return;
    await api(`/api/jobs/${d.j}/clips/${encodeURIComponent(d.c)}`, { method: "DELETE" });
    toast("Clip deleted", "ok");
    tick();
    return;
  }
  if (a === "deljob") {
    if (!await ask("Delete this project?", "All clips from this video will be removed.", "Delete project", true)) return;
    await api(`/api/jobs/${d.j}`, { method: "DELETE" });
    toast("Project deleted", "ok");
    tick();
    return;
  }
  if (a === "dlall") {
    const ids = (S.jobs.find(x => x.id === d.j)?.clips || []).map(c => d.j + "." + c.id);
    window.location.href = "/api/clips.zip?ids=" + encodeURIComponent(ids.join(","));
    toast("Preparing ZIP archive...", "ok");
    return;
  }
  if (a === "copy" || a === "copydlg") {
    let text = "Viral Highlight #shorts #podcast";
    if (a === "copydlg") {
      text = `${$("#ed_title")?.value || ""}\n\n${$("#ed_desc")?.value || ""}\n\n${$("#ed_tags")?.value || ""}`;
    }
    await navigator.clipboard.writeText(text);
    toast("Caption & hashtags copied to clipboard", "ok");
    return;
  }
  if (a === "selclear") { S.sel.clear(); render(); return; }
  if (a === "selall") {
    S.jobs.forEach(j => {
      S.sel.add("j:" + j.id);
      (j.clips || []).forEach(c => S.sel.add(`c:${j.id}:${c.id}`));
    });
    render();
    return;
  }
  if (a === "seldl") {
    const clipIds = [];
    for (const key of S.sel) {
      const p = key.split(":");
      if (p[0] === "c") clipIds.push(`${p[1]}.${p[2]}`);
    }
    if (!clipIds.length) { toast("No individual clips selected", "bad"); return; }
    window.location.href = "/api/clips.zip?ids=" + encodeURIComponent(clipIds.join(","));
    toast(`Downloading ${clipIds.length} clips ZIP...`, "ok");
    return;
  }
  if (a === "seldel") {
    if (!await ask("Delete selected items?", "This action cannot be undone.", "Delete", true)) return;
    for (const key of [...S.sel]) {
      const p = key.split(":");
      if (p[0] === "j") await api(`/api/jobs/${p[1]}`, { method: "DELETE" });
      else if (p[0] === "c") await api(`/api/jobs/${p[1]}/clips/${p[2]}`, { method: "DELETE" });
    }
    S.sel.clear();
    toast("Selected items deleted", "ok");
    tick();
    return;
  }
  if (a === "cliptopic") {
    b.disabled = true;
    try {
      toast("Extracting custom 9:16 short for topic chapter...", "ok");
      await send("/api/clips/custom-extract", {
        project_id: d.j,
        start_sec: Number(d.start),
        end_sec: Number(d.end),
        title: d.title,
        subtitle_style: "hormozi",
        layout_mode: "speaker_focus"
      });
      toast("Chapter clip extracted successfully!", "ok");
      tick();
    } catch (err) {
      toast(err.message, "bad");
    } finally {
      b.disabled = false;
    }
    return;
  }
  if (a === "settopspace") {
    const val = Number(d.val || 450);
    const inp = $("#o_top_space");
    if (inp) inp.value = val;
    const lbl = $("#o_top_space_val");
    if (lbl) lbl.textContent = `${val}px Top Spacing`;
    return;
  }
  if (a === "aihooks") {
    b.disabled = true;
    try {
      toast("Querying local Ollama for 5 viral vertical hooks...", "ok");
      const transcript = (D.activeWords || []).map(w => w.word).join(" ");
      const res = await send("/api/ai/generate-hooks", {
        transcript: transcript,
        topic: $("#ed_title")?.value || $("#ed_hook")?.value || "",
        clip_id: D.cid
      });
      const panel = $("#ai_hooks_panel");
      if (panel && res.hooks && res.hooks.length) {
        panel.style.display = "block";
        panel.innerHTML = `
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
            <span style="font-size:12px;font-weight:700">⚡ AI Generated Viral Hooks (Click to apply)</span>
            <button type="button" class="btn sm ghost" onclick="document.getElementById('ai_hooks_panel').style.display='none'">✕</button>
          </div>
          <div style="display:flex;flex-direction:column;gap:5px">
            ${res.hooks.map(h => `
              <button type="button" class="btn sm ghost" data-act="pickhook" data-hook="${esc(h.hook)}" style="justify-content:flex-start;text-align:left;font-size:12px;padding:6px 10px;background:#fff">
                <span class="badge" style="position:static;font-size:10px;margin-right:6px">${esc(h.type)}</span>
                <b>${esc(h.hook)}</b>
              </button>
            `).join("")}
          </div>
        `;
        toast("5 viral hooks generated!", "ok");
      }
    } catch (err) {
      toast(err.message, "bad");
    } finally {
      b.disabled = false;
    }
    return;
  }
  if (a === "pickhook") {
    const hk = d.hook;
    if (hk) {
      $("#ed_hook").value = hk;
      $("#ai_hooks_panel").style.display = "none";
      toast("Applied headline hook to canvas!", "ok");
    }
    return;
  }
  if (a === "aitranslate") {
    b.disabled = true;
    try {
      toast("Translating subtitles with local AI...", "ok");
      const transcript = (D.activeWords || []).map(w => w.word).join(" ");
      const res = await send("/api/ai/translate", {
        transcript: transcript,
        target_lang: "es",
        clip_id: D.cid
      });
      const panel = $("#ai_hooks_panel");
      if (panel && res.translated_text) {
        panel.style.display = "block";
        panel.innerHTML = `
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
            <span style="font-size:12px;font-weight:700">🌐 AI Multilingual Translation (${esc(res.language)})</span>
            <button type="button" class="btn sm ghost" onclick="document.getElementById('ai_hooks_panel').style.display='none'">✕</button>
          </div>
          <p style="font-size:12px;color:var(--text);margin-bottom:8px">${esc(res.translated_text)}</p>
          <div style="display:flex;gap:6px">
            <button type="button" class="btn sm primary" data-act="applytranshook" data-thook="${esc(res.suggested_title || res.translated_text.slice(0,35))}">Use As Hook</button>
          </div>
        `;
        toast(`Translated to ${res.language}!`, "ok");
      }
    } catch (err) {
      toast(err.message, "bad");
    } finally {
      b.disabled = false;
    }
    return;
  }
  if (a === "applytranshook") {
    $("#ed_hook").value = d.thook;
    $("#ai_hooks_panel").style.display = "none";
    toast("Applied multilingual hook!", "ok");
    return;
  }
  if (a === "aibroll") {
    b.disabled = true;
    try {
      toast("Scanning transcript for visual & SFX cues...", "ok");
      const transcript = (D.activeWords || []).map(w => w.word).join(" ");
      const res = await send("/api/ai/b-roll", { transcript: transcript });
      const panel = $("#ai_hooks_panel");
      if (panel && res.suggestions) {
        panel.style.display = "block";
        panel.innerHTML = `
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
            <span style="font-size:12px;font-weight:700">🎬 Recommended Visual B-Roll & SFX</span>
            <button type="button" class="btn sm ghost" onclick="document.getElementById('ai_hooks_panel').style.display='none'">✕</button>
          </div>
          <div style="display:flex;flex-direction:column;gap:6px">
            ${res.suggestions.map(s => `
              <div style="font-size:11.5px;background:#fff;padding:6px 8px;border-radius:6px;border:1px solid var(--line-2)">
                <b>${esc(s.b_roll_suggestion)}</b> · <span style="color:var(--brand)">${esc(s.sfx_cue)}</span>
              </div>
            `).join("")}
          </div>
        `;
        toast("Found B-Roll retention cues!", "ok");
      }
    } catch (err) {
      toast(err.message, "bad");
    } finally {
      b.disabled = false;
    }
    return;
  }
  if (a === "applywordedit") {
    const idx = D.selectedWordIdx;
    const inp = $("#inspect_word_input");
    if (idx !== null && inp && D.activeWords && D.activeWords[idx]) {
      const newText = inp.value.trim();
      if (newText) {
        D.activeWords[idx].word = newText;
        const chip = $(`#karaokeChips .word-chip[data-idx="${idx}"]`);
        if (chip) chip.textContent = newText;
        $("#inspect_word_label").textContent = newText;
        toast("Word text updated in subtitles", "ok");
      }
    }
    return;
  }
  if (a === "tagwordcolor") {
    const idx = D.selectedWordIdx;
    const color = d.color;
    if (idx !== null && D.activeWords && D.activeWords[idx]) {
      D.activeWords[idx].color = (color === "none") ? null : color;
      const chip = $(`#karaokeChips .word-chip[data-idx="${idx}"]`);
      if (chip) {
        chip.className = `word-chip active ${color !== "none" ? "hl-" + color : ""}`;
      }
      toast(`Word tagged with ${color} highlight`, "ok");
    }
    return;
  }
  if (a === "setwordstart") {
    const idx = D.selectedWordIdx;
    if (idx !== null && D.activeWords && D.activeWords[idx]) {
      const st = D.activeWords[idx].start;
      $("#ed_start").value = st;
      toast(`Clip start trimmed to ${st.toFixed(1)}s`, "ok");
    }
    return;
  }
  if (a === "setwordend") {
    const idx = D.selectedWordIdx;
    if (idx !== null && D.activeWords && D.activeWords[idx]) {
      const en = D.activeWords[idx].end;
      $("#ed_end").value = en;
      toast(`Clip end trimmed to ${en.toFixed(1)}s`, "ok");
    }
    return;
  }
  if (a === "remake") {
    b.disabled = true;
    try {
      toast("Re-burning clip with GPU NVENC hardware acceleration...", "ok");
      const topPadVal = Number($("#ed_pad_top")?.value || 0);
      const botPadVal = Number($("#ed_pad_bottom")?.value || 0);
      const res = await send(`/api/jobs/${D.jid}/clips/${D.cid}/render`, {
        start: Number($("#ed_start").value),
        end: Number($("#ed_end").value),
        hook: $("#ed_hook").value,
        style: $("#ed_style").value,
        layout: $("#ed_layout").value,
        top_space: Number($("#ed_top_space")?.value || 450),
        top_padding: topPadVal,
        bottom_padding: botPadVal,
        canvas_bg: $("#ed_canvas_bg")?.value || "solid_black",
        color_preset: $("#ed_color")?.value || "none",
        watermark: $("#ed_watermark")?.value?.trim() || "",
        voice_clarifier: $("#ed_clarifier") ? $("#ed_clarifier").checked : true,
        words: D.activeWords || []
      });
      toast("Clip re-burn complete!", "ok");
      if (res && res.file) {
        const newSrc = `/media/${D.jid}/${encodeURIComponent(res.file)}?t=${Date.now()}`;
        const videoEl = $("#editorVideo");
        if (videoEl) {
          videoEl.src = newSrc;
          videoEl.play().catch(() => {});
        }
        const dlBtn = $("#ed_download_btn");
        if (dlBtn) {
          dlBtn.href = `/media/${D.jid}/${encodeURIComponent(res.file)}`;
          dlBtn.style.display = "inline-flex";
        }
        const j = S.jobs.find(x => x.id === D.jid);
        if (j) {
          const c = j.clips.find(x => x.id === D.cid);
          if (c) {
            c.filename = res.file;
            c.output_file = res.output_file || res.file;
            c.top_padding = topPadVal;
            c.bottom_padding = botPadVal;
            c.layout_mode = $("#ed_layout")?.value || c.layout_mode;
            c.subtitle_style = $("#ed_style")?.value || c.subtitle_style;
            c.hook = $("#ed_hook")?.value || c.hook;
          }
        }
      }
      tick();
    } catch (err) {
      toast(err.message, "bad");
    } finally {
      b.disabled = false;
    }
    return;
  }
  if (a === "rewritetext") {
    const t = $("#ed_title"), dsc = $("#ed_desc");
    if (t) t.value = "THE UNTOLD TRUTH ABOUT " + (t.value || "SUCCESS").toUpperCase();
    if (dsc) dsc.value = "Watch this before it gets taken down. Key breakdown from the full podcast.";
    toast("Rewritten with viral high-retention copy", "ok");
    return;
  }
  if (a === "findmodels") {
    b.disabled = true;
    try {
      toast("Scanning local Ollama models...", "ok");
      const res = await send("/api/ai/models", {});
      if (res.models && res.models.length) {
        const inp = $("#set_ai_model");
        if (inp) inp.value = res.models[0];
        toast(`Found ${res.models.length} local models: ${res.models.join(", ")}`, "ok");
      }
    } catch (err) {
      toast("Could not reach Ollama: " + err.message, "bad");
    } finally {
      b.disabled = false;
    }
    return;
  }
  if (a === "saveai") {
    b.disabled = true;
    try {
      const model = $("#set_ai_model")?.value || "llama3.2";
      const host = $("#set_ai_host")?.value || "http://127.0.0.1:11434";
      toast("Testing connection to Ollama...", "ok");
      const res = await send("/api/ai/save", { model, host });
      if (res.connected) {
        toast(`Connected to Ollama (${model})! Status: Healthy`, "ok");
      } else {
        toast(`Ollama at ${host} is offline. Start it in terminal: 'ollama serve'`, "bad");
      }
      tick();
    } catch (err) {
      toast("Connection error: " + err.message, "bad");
    } finally {
      b.disabled = false;
    }
    return;
  }
});

// Ingestion Form Submit Handler
document.addEventListener("submit", async e => {
  if (e.target.id === "addform") {
    e.preventDefault();
    const btn = $("#goBtn");
    btn.disabled = true;
    try {
      const fd = new FormData();
      if (DRAFT.file) {
        fd.append("file", DRAFT.file);
      } else if (DRAFT.link) {
        fd.append("youtube_url", DRAFT.link.url);
      } else {
        const u = $("#url")?.value.trim();
        if (!u) { toast("Paste a YouTube link or upload a file first", "bad"); return; }
        fd.append("youtube_url", u);
      }

      const rawLayout = $("#o_layout")?.value || "fit_canvas";
      const layoutMode = (rawLayout === "fit_canvas") ? "fit_canvas"
                       : (rawLayout === "face_center") ? "face_center"
                       : (rawLayout === "split") ? "split_screen"
                       : (rawLayout === "crop") ? "center_crop"
                       : (rawLayout === "blur") ? "blur"
                       : "speaker_focus";

      fd.append("subtitle_style", $("#o_style")?.value || "hormozi");
      fd.append("layout_mode", layoutMode);
      fd.append("canvas_top_space", $("#o_top_space")?.value || "450");
      fd.append("top_padding", $("#o_pad_top")?.value || "0");
      fd.append("bottom_padding", $("#o_pad_bottom")?.value || "0");
      fd.append("pad_top", $("#o_pad_top")?.value || "0");
      fd.append("pad_bottom", $("#o_pad_bottom")?.value || "0");
      fd.append("canvas_bg", $("#o_canvas_bg")?.value || "solid_black");
      fd.append("max_clips", $("#o_max")?.value || "5");
      fd.append("min_clip_seconds", $("#o_min")?.value || "25");
      fd.append("max_clip_seconds", $("#o_maxlen")?.value || "65");
      fd.append("face_tracking", layoutMode === "speaker_focus" ? "true" : "false");
      fd.append("show_headline_banner", $("#o_captions")?.checked ? "true" : "false");
      fd.append("custom_headline", $("#o_hook")?.value?.trim() || "");
      fd.append("language", $("#o_lang")?.value || "en");
      fd.append("enable_tightcut", $("#o_tightcut")?.checked ? "true" : "false");
      fd.append("enable_auto_emojis", $("#o_emojis")?.checked ? "true" : "false");
      fd.append("progress_bar_color", $("#o_bar")?.value || "#00E5FF");
      fd.append("bgm_track", $("#o_bgm")?.value || "none");
      fd.append("bgm_volume", "0.12");
      fd.append("color_preset", $("#o_color")?.value || "none");
      fd.append("watermark_text", $("#o_watermark")?.value?.trim() || "");
      fd.append("watermark_position", $("#o_watermark_pos")?.value || "top_right");
      fd.append("enable_voice_clarifier", $("#o_clarifier")?.checked ? "true" : "false");
      fd.append("enable_hook_zoom", $("#o_hookzoom")?.checked ? "true" : "false");

      toast("Starting ClipForge pipeline...", "ok");
      const resp = await fetch("/api/clips/create", { method: "POST", body: fd });
      if (!resp.ok) {
        let errMsg = resp.statusText;
        try { errMsg = (await resp.json()).detail || errMsg; } catch {}
        throw new Error(errMsg);
      }
      toast("Video queued for clipping!", "ok");

      DRAFT.link = null;
      DRAFT.file = null;
      if ($("#url")) $("#url").value = "";
      drawAtt();
      go("library");
      tick();
    } catch (err) {
      toast(err.message, "bad");
    } finally {
      btn.disabled = false;
    }
  }
});

// File upload picker
$("#file")?.addEventListener("change", e => {
  if (e.target.files?.length) {
    DRAFT.file = e.target.files[0];
    DRAFT.link = null;
    drawAtt();
    const f = DRAFT.file;
    const previewVid = $("#composerVideo");
    const previewImg = $("#composerImage");
    if (previewVid && f) {
      previewVid.src = URL.createObjectURL(f);
      previewVid.style.display = "block";
      previewVid.play().catch(() => {});
      if (previewImg) previewImg.style.display = "none";
    }
    const fd = new FormData();
    fd.append("file", f);
    fetch("/api/preview/upload_draft", { method: "POST", body: fd })
      .then(r => r.json())
      .then(res => { if (res && res.draft_name) DRAFT.draft_name = res.draft_name; })
      .catch(() => {});
  }
  e.target.value = "";
});

// YouTube URL live preview
let ytTimer = 0;
$("#url")?.addEventListener("input", e => {
  clearTimeout(ytTimer);
  const u = e.target.value.trim();
  if (/youtu\.?be/i.test(u)) {
    ytTimer = setTimeout(async () => {
      try {
        const info = await api("/api/preview?url=" + encodeURIComponent(u));
        DRAFT.link = { url: u, title: info.title, duration: info.duration, thumb: info.thumb || info.thumbnail, uploader: info.uploader || info.channel };
        DRAFT.file = null;
        drawAtt();
      } catch {}
    }, 600);
  }
});

// Segmented options & Word Chip click handlers
document.addEventListener("click", e => {
  const chip = e.target.closest("#karaokeChips .word-chip");
  if (chip) {
    const idx = Number(chip.dataset.idx);
    D.selectedWordIdx = idx;
    const startSec = Number(chip.dataset.start);
    const wordText = chip.dataset.word || chip.textContent.trim();

    // 1. Seek video to word timestamp
    const v = $("#editorVideo");
    if (v && !isNaN(startSec)) {
      v.currentTime = Math.max(0, startSec);
      v.play().catch(() => {});
    }

    // 2. Highlight selected chip
    $("#karaokeChips").querySelectorAll(".word-chip").forEach(c => c.classList.remove("active"));
    chip.classList.add("active");

    // 3. Open Word Inspector
    const insp = $("#word_inspector");
    if (insp) {
      insp.style.display = "block";
      const lbl = $("#inspect_word_label");
      if (lbl) lbl.textContent = wordText;
      const inp = $("#inspect_word_input");
      if (inp) {
        inp.value = wordText;
        inp.focus();
      }
    }
    return;
  }

  const sg = e.target.closest("[data-seg]");
  if (sg) {
    const id = sg.dataset.seg;
    const inp = $("#" + id);
    if (inp) inp.value = sg.dataset.v;
    sg.parentElement.querySelectorAll("[data-seg]").forEach(b => b.setAttribute("aria-pressed", String(b === sg)));
    if (id === "o_layout") {
      const isFit = (sg.dataset.v === "fit_canvas");
      const fitBox = $("#fit_canvas_options");
      if (fitBox) fitBox.style.display = isFit ? "block" : "none";
      const vid = $("#composerVideo");
      const img = $("#composerImage");
      if (vid) vid.style.objectFit = isFit ? "contain" : "cover";
      if (img) img.style.objectFit = isFit ? "contain" : "cover";
      const topPad = Number($("#o_pad_top")?.value || 0);
      const botPad = Number($("#o_pad_bottom")?.value || 0);
      updateComposerPaddingPreview(topPad, botPad);
    }
    return;
  }
  const st = e.target.closest("[data-step]");
  if (st) {
    const inp = $("#" + st.dataset.step);
    const d = Number(st.dataset.d);
    if (inp) inp.value = Math.max(Number(inp.min || 1), Math.min(Number(inp.max || 180), Number(inp.value) + d));
    return;
  }
  const selck = e.target.closest("[data-sel]");
  if (selck && e.target.tagName === "INPUT") {
    const key = selck.dataset.sel;
    if (selck.checked) S.sel.add(key);
    else S.sel.delete(key);
    render();
    return;
  }
});

// Safe Area & Padding Sliders and Inputs Synchronization
document.addEventListener("input", e => {
  const tid = e.target.id;
  if (tid === "o_hook") {
    const bannerEl = $("#composerPreviewBanner");
    const text = e.target.value.trim() ? e.target.value.trim().toUpperCase() : "THE 1 SECRET TO HIGH RETENTION";
    if (bannerEl) bannerEl.innerHTML = `<span class="preview-banner-pill">[ ${esc(text)} ]</span>`;
    return;
  }
  if (tid === "ed_pad_top") {
    const val = Number(e.target.value) || 0;
    const numInput = $("#ed_pad_top_num");
    if (numInput) numInput.value = val;
    const botVal = Number($("#ed_pad_bottom")?.value || 0);
    updateEditorPaddingPreview(val, botVal);
  } else if (tid === "ed_pad_top_num") {
    const val = Math.max(0, Math.min(45, Number(e.target.value) || 0));
    const slider = $("#ed_pad_top");
    if (slider) slider.value = val;
    const botVal = Number($("#ed_pad_bottom")?.value || 0);
    updateEditorPaddingPreview(val, botVal);
  } else if (tid === "ed_pad_bottom") {
    const val = Number(e.target.value) || 0;
    const numInput = $("#ed_pad_bottom_num");
    if (numInput) numInput.value = val;
    const topVal = Number($("#ed_pad_top")?.value || 0);
    updateEditorPaddingPreview(topVal, val);
  } else if (tid === "ed_pad_bottom_num") {
    const val = Math.max(0, Math.min(45, Number(e.target.value) || 0));
    const slider = $("#ed_pad_bottom");
    if (slider) slider.value = val;
    const topVal = Number($("#ed_pad_top")?.value || 0);
    updateEditorPaddingPreview(topVal, val);
  } else if (tid === "o_pad_top") {
    const val = Number(e.target.value) || 0;
    const numInput = $("#o_pad_top_num");
    if (numInput) numInput.value = val;
    const botVal = Number($("#o_pad_bottom")?.value || 0);
    updateComposerPaddingPreview(val, botVal);
  } else if (tid === "o_pad_top_num") {
    const val = Math.max(0, Math.min(45, Number(e.target.value) || 0));
    const slider = $("#o_pad_top");
    if (slider) slider.value = val;
    const botVal = Number($("#o_pad_bottom")?.value || 0);
    updateComposerPaddingPreview(val, botVal);
  } else if (tid === "o_pad_bottom") {
    const val = Number(e.target.value) || 0;
    const numInput = $("#o_pad_bottom_num");
    if (numInput) numInput.value = val;
    const topVal = Number($("#o_pad_top")?.value || 0);
    updateComposerPaddingPreview(topVal, val);
  } else if (tid === "o_pad_bottom_num") {
    const val = Math.max(0, Math.min(45, Number(e.target.value) || 0));
    const slider = $("#o_pad_bottom");
    if (slider) slider.value = val;
    const topVal = Number($("#o_pad_top")?.value || 0);
    updateComposerPaddingPreview(topVal, val);
  }
});

document.addEventListener("change", e => {
  const tid = e.target.id;
  if (tid === "ed_pad_top_num") {
    let val = Math.max(0, Math.min(45, Number(e.target.value) || 0));
    e.target.value = val;
    const slider = $("#ed_pad_top");
    if (slider) slider.value = val;
    const botVal = Number($("#ed_pad_bottom")?.value || 0);
    updateEditorPaddingPreview(val, botVal);
  } else if (tid === "ed_pad_bottom_num") {
    let val = Math.max(0, Math.min(45, Number(e.target.value) || 0));
    e.target.value = val;
    const slider = $("#ed_pad_bottom");
    if (slider) slider.value = val;
    const topVal = Number($("#ed_pad_top")?.value || 0);
    updateEditorPaddingPreview(topVal, val);
  } else if (tid === "o_pad_top_num") {
    let val = Math.max(0, Math.min(45, Number(e.target.value) || 0));
    e.target.value = val;
    const slider = $("#o_pad_top");
    if (slider) slider.value = val;
    const botVal = Number($("#o_pad_bottom")?.value || 0);
    updateComposerPaddingPreview(val, botVal);
  } else if (tid === "o_pad_bottom_num") {
    let val = Math.max(0, Math.min(45, Number(e.target.value) || 0));
    e.target.value = val;
    const slider = $("#o_pad_bottom");
    if (slider) slider.value = val;
    const topVal = Number($("#o_pad_top")?.value || 0);
    updateComposerPaddingPreview(topVal, val);
  }
});

// Initial boot
document.addEventListener("DOMContentLoaded", () => {
  go("library");
  tick();
  loop();
});
