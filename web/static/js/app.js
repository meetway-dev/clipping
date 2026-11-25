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
  "warn": `<path d="M128,24A104,104,0,1,0,232,128,104.11,104.11,0,0,0,128,24Zm-8-80V80a8,8,0,0,1,16,0v56a8,8,0,0,1-16,0Zm20,36a12,12,0,1,1-12-12A12,12,0,0,1,140,172Z"/>`,
  "cloud": `<path d="M192,96a64.07,64.07,0,0,0-58.67,38.67A48,48,0,0,0,88,128a48,48,0,0,0,0,96h104a64,64,0,0,0,0-128Z"/>`,
  "globe": `<path d="M128,24A104,104,0,1,0,232,128,104.11,104.11,0,0,0,128,24Zm87.67,96H175.87c-1.89-28.79-11.83-54.89-26.65-72.93A88.19,88.19,0,0,1,215.67,120ZM128,40.16c14.28,18.06,23.59,44,24.18,79.84H103.82C104.41,84.15,113.72,58.22,128,40.16ZM40.33,120A88.19,88.19,0,0,1,106.78,47.07C92,65.11,82,91.21,80.13,120ZM40.33,136H80.13c1.89,28.79,11.83,54.89,26.65,72.93A88.19,88.19,0,0,1,40.33,136Zm87.67,79.84c-14.28-18.06-23.59-44-24.18-79.84h48.36C151.59,171.85,142.28,197.78,128,215.84Zm21.22-7.07C164,190.89,174,164.79,175.87,136h39.8A88.19,88.19,0,0,1,149.22,208.77Z"/>`
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
  gdrive: { connected: false, email: "", folder_name: "ClipForge Clips", has_credentials: false },
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

function toast(msg, kind = "ok", title = "") {
  if (!msg) return;
  const container = $("#toasts");
  if (!container) return;

  const icons = {
    ok: "✓",
    bad: "✕",
    warn: "⚠️",
    info: "ℹ️",
    loading: "⏳"
  };

  const defaultTitles = {
    ok: "Success",
    bad: "Error",
    warn: "Attention",
    info: "Notice",
    loading: "Processing"
  };

  const t = document.createElement("div");
  t.className = `toast toast-${kind}`;
  t.setAttribute("role", "status");

  const toastTitle = title || defaultTitles[kind] || "Notification";
  const iconSymbol = icons[kind] || icons.ok;

  t.innerHTML = `
    <div class="toast-indicator">
      <span class="toast-indicator-icon">${iconSymbol}</span>
    </div>
    <div class="toast-content">
      <div class="toast-header">
        <span class="toast-title">${esc(toastTitle)}</span>
        <button type="button" class="toast-dismiss-btn" aria-label="Dismiss">&times;</button>
      </div>
      <div class="toast-msg">${esc(msg)}</div>
    </div>
    <div class="toast-progress"></div>
  `;

  // Dismiss button click
  t.querySelector(".toast-dismiss-btn")?.addEventListener("click", () => {
    t.classList.add("toast-leaving");
    setTimeout(() => t.remove(), 200);
  });

  container.append(t);

  // Auto-dismiss duration
  const dur = kind === "bad" ? 6500 : (kind === "loading" ? 12000 : 3600);
  const timer = setTimeout(() => {
    t.classList.add("toast-leaving");
    setTimeout(() => t.remove(), 250);
  }, dur);

  // Pause on hover
  t.addEventListener("mouseenter", () => {
    t.style.animationPlayState = "paused";
    clearTimeout(timer);
  });
}

function setStageLoading(active, msg = "Rendering with GPU NVENC...", sub = "Hardware Acceleration Active") {
  const frame = $("#stageCanvasFrame");
  if (!frame) return;
  let overlay = $("#stageLoadingOverlay");
  if (active) {
    if (!overlay) {
      overlay = document.createElement("div");
      overlay.id = "stageLoadingOverlay";
      overlay.className = "stage-loading-overlay";
      overlay.innerHTML = `
        <div class="stage-spinner-ring"></div>
        <div class="stage-loading-msg">${esc(msg)}</div>
        <div class="stage-loading-sub">${esc(sub)}</div>
      `;
      frame.appendChild(overlay);
    } else {
      const msgEl = overlay.querySelector(".stage-loading-msg");
      const subEl = overlay.querySelector(".stage-loading-sub");
      if (msgEl) msgEl.textContent = msg;
      if (subEl) subEl.textContent = sub;
      overlay.style.display = "flex";
    }
  } else if (overlay) {
    overlay.style.display = "none";
  }
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
    const gdPill = S.gdrive?.connected
      ? `<button type="button" class="gdrive-top-btn on" data-act="opengdrivetab" title="Google Drive: ${esc(S.gdrive.email || "")} (${esc(S.gdrive.folder_name || "ClipForge Clips")})">
          <span style="color:#007588;font-weight:900">▲</span> <span>${esc(S.gdrive.email ? S.gdrive.email.split("@")[0] : "Drive Connected")}</span>
         </button>`
      : `<button type="button" class="gdrive-top-btn" data-act="opengdrivetab" title="Connect Google Drive to sync clips to your mobile phone for TikTok">
          <span style="color:#007588;font-weight:900">▲</span> <span>Connect Drive</span>
         </button>`;
    act = `${gdPill}
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
const DRAFT = { link: null, file: null, busy: false, activeTab: "youtube" };

function drawAdd(variant) {
  const box = $("#add");
  if (!box) return;
  const isYt = DRAFT.activeTab === "youtube";

  box.innerHTML = `
    <form class="composer ${variant === "hero" ? "big" : "compact"}" id="addform">
      <!-- Minimalist Source Selector Tabs -->
      <div class="composer-source-tabs" role="tablist">
        <button type="button" class="source-tab ${isYt ? "active" : ""}" data-tab="youtube" role="tab" aria-selected="${isYt}">
          <span class="source-tab-icon">${ic("link")}</span>
          <span class="source-tab-label">YouTube / URL</span>
          <span class="source-tab-badge">Instant</span>
        </button>
        <button type="button" class="source-tab ${!isYt ? "active" : ""}" data-tab="upload" role="tab" aria-selected="${!isYt}">
          <span class="source-tab-icon">${ic("up")}</span>
          <span class="source-tab-label">Upload Video</span>
          <span class="source-tab-badge">MP4, MOV, MKV</span>
        </button>
      </div>

      <!-- Tab Content 1: YouTube / Web URL Stream Input -->
      <div class="composer-pane" id="pane_youtube" style="display: ${isYt ? "block" : "none"}">
        <div class="composer-input-wrap">
          <div class="composer-input-field">
            <span class="input-lens-icon">${ic("link")}</span>
            <input id="url" type="url" placeholder="Paste YouTube link (e.g. https://youtube.com/watch?v=...)" autocomplete="off" aria-label="Video link" value="${DRAFT.link?.url || ""}">
            ${DRAFT.link ? `<button type="button" class="input-clear-btn" data-act="clearlink" title="Clear link">${ic("x")}</button>` : ""}
          </div>
        </div>
      </div>

      <!-- Tab Content 2: Minimalist Drag & Drop Zone -->
      <div class="composer-pane" id="pane_upload" style="display: ${!isYt ? "block" : "none"}">
        <div class="minimal-dropzone" id="composerDropzone" data-act="pickfile">
          <div class="dropzone-glow-ring"></div>
          <div class="dropzone-body">
            <div class="dropzone-icon-bubble">${ic("up")}</div>
            <div class="dropzone-text-group">
              <span class="dropzone-main-text">Drag & drop your podcast or video file here</span>
              <span class="dropzone-sub-text">or <strong class="dropzone-highlight">click to browse</strong> from your computer</span>
            </div>
            <div class="dropzone-format-tags">
              <span>MP4</span><span>MOV</span><span>MKV</span><span>WEBM</span><span>Up to 4K</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Interactive File / Link Preview Card (Attachment) -->
      <div class="att" id="att"><div><div class="att-in" id="attIn"></div></div></div>

      <!-- Enhanced Composer Bottom Action Bar -->
      <div class="composer-bar">
        <div class="composer-quick-actions">
          <button type="button" class="chip opts-toggle-chip" data-act="toggleopts" aria-expanded="false" id="btn_toggle_options">
            ${ic("sliders")}
            <span>Studio Settings</span>
            <span class="chip-badge">AI Presets</span>
          </button>
          <span class="quick-summary-pill" id="composerQuickSummary">🔍 AI Viral Research Active · 60–90s complete thoughts · 5 clips</span>
        </div>

        <button class="btn primary make-clips-btn" id="goBtn" type="submit">
          <span class="btn-shine"></span>
          ${ic("scissors")}
          <span>Make clips</span>
        </button>
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
                  <input id="o_min" type="number" min="10" max="300" step="5" value="60"><i>s</i>
                  <button type="button" data-step="o_min" data-d="5">${ic("plus")}</button>
                </div>
              </div>
              <div class="nstep">
                <span>Longest</span>
                <div class="ctl">
                  <button type="button" data-step="o_maxlen" data-d="-5">${ic("minus")}</button>
                  <input id="o_maxlen" type="number" min="15" max="600" step="5" value="90"><i>s</i>
                  <button type="button" data-step="o_maxlen" data-d="5">${ic("plus")}</button>
                </div>
              </div>
            </div>

            <!-- Quick Duration Targets -->
            <div style="margin-top:10px;padding-top:8px;border-top:1px dashed var(--line)">
              <div style="font-size:11px;font-weight:700;color:var(--dim);margin-bottom:6px">Quick Duration Targets (AI prioritizes complete thoughts):</div>
              <div style="display:flex;gap:6px;flex-wrap:wrap">
                <button type="button" class="btn sm dur-preset-btn" data-act="setdurpreset" data-min="30" data-max="60" style="font-size:11px;padding:3px 8px">⚡ 30–60s (Quick)</button>
                <button type="button" class="btn sm dur-preset-btn on" data-act="setdurpreset" data-min="60" data-max="90" style="font-size:11px;padding:3px 8px;background:rgba(255,139,51,0.14);border:1px solid var(--brand);color:var(--brand);font-weight:800">🔥 60–90s (TikTok Sweet Spot)</button>
                <button type="button" class="btn sm dur-preset-btn" data-act="setdurpreset" data-min="60" data-max="180" style="font-size:11px;padding:3px 8px">🎙️ 60–180s (Deep Dive)</button>
                <button type="button" class="btn sm dur-preset-btn" data-act="setdurpreset" data-min="70" data-max="300" style="font-size:11px;padding:3px 8px">🎬 70–300s (Extended Story)</button>
              </div>
            </div>
          </div>

          <div class="ob wide">
            <label class="f">
              <span class="ot" style="margin:0">Headline banner text <span style="font-weight:400">(6–12 words recommended for top safe area)</span></span>
              <input id="o_hook" maxlength="140" autocomplete="off" placeholder="e.g. WHY 99% OF PEOPLE FAIL AT THIS (AND HOW TO FIX IT)">
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
            <div class="ob wide composer-preview-section" id="composer_preview_section">
              <div class="composer-preview-header">
                <div style="display:flex;align-items:center;gap:10px">
                  <div class="preview-icon-box">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="3" y="3" width="18" height="18" rx="3"/><path d="M3 9h18M3 15h18"/></svg>
                  </div>
                  <div>
                    <div style="display:flex;align-items:center;gap:8px">
                      <span style="font-size:14px;font-weight:800;color:var(--text);letter-spacing:-0.01em">Live TikTok 9:16 Layout & Safe Area Preview</span>
                      <span class="preview-live-badge"><span class="live-pulse-dot"></span>Real-Time Framing</span>
                    </div>
                    <div style="font-size:11.5px;color:var(--dim);margin-top:2px">Interact with live safe area padding, viral yellow hook position & TikTok overlay</div>
                  </div>
                </div>
                <div style="display:flex;gap:8px;align-items:center">
                  <button type="button" class="btn sm preview-tt-toggle-btn" data-act="togglecomposertiktok" id="btn_toggle_tiktok_ui">
                    <span class="tt-toggle-dot"></span>Toggle TikTok UI
                  </button>
                  <button type="button" class="btn sm preview-render-btn" data-act="rendercomposerframe">
                    ${ic("film")}📸 Render Exact Frame
                  </button>
                </div>
              </div>

              <div class="composer-preview-grid">
                <!-- 9:16 Smartphone Mockup Stage -->
                <div class="preview-stage-col">
                  <div class="tiktok-phone-mockup" id="composerPhoneMockup">
                    <div class="phone-dynamic-island"><span class="island-lens"></span><span class="island-mic"></span></div>
                    
                    <!-- Top Safe Area Overlay with Live Topic Headline Banner -->
                    <div class="safe-pad-zone top" id="composerPadTop" style="height:0%;display:none">
                      <div class="preview-banner-wrap" id="composerPreviewBanner">
                        <span class="preview-banner-viral-pill">THE 'OUTLIVE' METHOD: THE 3 EXERCISES YOU NEED</span>
                      </div>
                      <span class="pad-zone-tag" id="composerTagTop"><span class="tag-dot"></span>Top Safe Area: 0%</span>
                    </div>

                    <!-- Active Video Framing Center: Bounded by Top & Bottom Safe Areas -->
                    <div class="stage-active-center" id="composerActiveCenter" style="top:0%;height:100%">
                      <video id="composerVideo" autoplay muted loop playsinline style="display:none;width:100%;height:100%;object-fit:cover"></video>
                      <img id="composerImage" src="/brand/demo-clean.jpg" alt="Preview Frame" style="width:100%;height:100%;object-fit:cover">
                    </div>

                    <!-- Bottom Safe Area Overlay with Animated Captions Preview -->
                    <div class="safe-pad-zone bottom" id="composerPadBottom" style="height:0%;display:none">
                      <div class="preview-caption-wrap" id="composerPreviewCaptions">
                        <span class="preview-caption-chip">VIRAL <b style="color:#FFE500">&nbsp;CAPTIONS 🔥</b></span>
                      </div>
                      <span class="pad-zone-tag" id="composerTagBottom"><span class="tag-dot"></span>Bottom Safe Area: 0%</span>
                    </div>

                    <!-- Authentic TikTok Social UI Overlay -->
                    <div class="tiktok-social-overlay on" id="composerTikTokOverlay">
                      <div class="tt-top-header">
                        <span class="tt-live-pill"><span class="tt-live-dot"></span>LIVE</span>
                        <div class="tt-tabs">
                          <span class="tt-tab">Following</span>
                          <span class="tt-tab active">For You</span>
                        </div>
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
                        <div class="tt-creator-tag">@creator <span class="tt-verified">✓</span> • ClipForge Studio</div>
                        <div class="tt-caption-text">Watch how smart 9:16 safe area padding preserves full widescreen content! 🚀 #viral #podcast #shorts #fyp</div>
                        <div class="tt-sound-bar"><span>🎵</span> <marquee scrollamount="3">original sound - ClipForge Studio High Retention Voice</marquee></div>
                      </div>
                    </div>

                    <!-- Sleek Home Indicator Bar -->
                    <div class="phone-home-indicator"></div>
                  </div>
                </div>

                <!-- Controls & Real-Time Telemetry Column -->
                <div class="preview-controls-col">
                  <!-- Quick Padding Presets -->
                  <div class="preset-section">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                      <span class="preset-label">⚡ Quick Safe Area Presets:</span>
                      <span style="font-size:11px;color:var(--brand);font-weight:700">One-Click Optimal Padding</span>
                    </div>
                    <div class="preset-pills-row">
                      <button type="button" class="preset-pill on" data-act="setcomposerpad" data-top="0" data-bottom="0">
                        <span class="preset-title">0% Full 9:16</span>
                        <small>Max Zoom (31% kept)</small>
                      </button>
                      <button type="button" class="preset-pill" data-act="setcomposerpad" data-top="10" data-bottom="10">
                        <span class="preset-title">10% + 10%</span>
                        <small>80% Area (42% kept)</small>
                      </button>
                      <button type="button" class="preset-pill" data-act="setcomposerpad" data-top="15" data-bottom="15">
                        <span class="preset-title">15% + 15%</span>
                        <small>70% Area (47% kept)</small>
                      </button>
                      <button type="button" class="preset-pill star" data-act="setcomposerpad" data-top="20" data-bottom="20">
                        <span class="preset-title">20% + 20% <span class="badge-rec">RECOMMENDED</span></span>
                        <small>60% Area (+66% wider!)</small>
                      </button>
                      <button type="button" class="preset-pill" data-act="setcomposerpad" data-top="25" data-bottom="25">
                        <span class="preset-title">25% + 25%</span>
                        <small>50% Area (60% kept)</small>
                      </button>
                    </div>
                  </div>

                  <!-- Editable Top & Bottom Padding Sliders -->
                  <div class="pad-control-grid">
                    <div class="pad-control-row">
                      <div class="pad-label-row">
                        <div class="pad-label-left">
                          <span class="pad-icon-dot top"></span>
                          <span class="pad-label">Top Padding (Viral Hook Safe Zone)</span>
                        </div>
                        <div class="pad-val-box">
                          <input type="number" id="o_pad_top_num" class="pad-num-input" min="0" max="45" step="1" value="0">
                          <span class="pad-unit">%</span>
                        </div>
                      </div>
                      <input type="range" id="o_pad_top" class="pad-slider" min="0" max="45" step="1" value="0">
                    </div>

                    <div class="pad-control-row">
                      <div class="pad-label-row">
                        <div class="pad-label-left">
                          <span class="pad-icon-dot bottom"></span>
                          <span class="pad-label">Bottom Padding (Captions & TikTok UI Safe Zone)</span>
                        </div>
                        <div class="pad-val-box">
                          <input type="number" id="o_pad_bottom_num" class="pad-num-input" min="0" max="45" step="1" value="0">
                          <span class="pad-unit">%</span>
                        </div>
                      </div>
                      <input type="range" id="o_pad_bottom" class="pad-slider" min="0" max="45" step="1" value="0">
                    </div>
                  </div>

                  <!-- High-Tech Telemetry HUD Card -->
                  <div class="telemetry-card" id="composerTelemetry">
                    <div class="telem-header-row">
                      <div style="display:flex;align-items:center;gap:6px">
                        <span style="font-size:12px;color:var(--brand)">📐</span>
                        <span class="telem-title">Framing & Retention Telemetry</span>
                      </div>
                      <span class="telem-badge-opt standard" id="o_fov_status_badge">Standard 9:16 Crop</span>
                    </div>
                    
                    <div class="telem-gauge-wrap" title="Active Visible Video Area on Screen">
                      <div class="telem-gauge-bar" id="o_gauge_active_bar" style="width:100%"></div>
                    </div>

                    <div class="telem-metrics-grid">
                      <div class="telem-metric-item">
                        <span class="telem-k">Active Canvas</span>
                        <span class="telem-v" id="o_active_area_val"><strong style="color:var(--brand)">100%</strong> (1920px)</span>
                      </div>
                      <div class="telem-metric-item">
                        <span class="telem-k">Widescreen Kept</span>
                        <span class="telem-v" id="o_fov_val"><strong style="color:var(--brand-deep)">31.6%</strong> of original width</span>
                      </div>
                      <div class="telem-metric-item">
                        <span class="telem-k">Horizontal FOV Gain</span>
                        <span class="telem-v" id="o_zoom_gain_val">Standard 9:16 Cropping</span>
                      </div>
                      <div class="telem-metric-item">
                        <span class="telem-k">Safe Margins</span>
                        <span class="telem-v" id="o_pad_summary">Top: 0px • Bottom: 0px</span>
                      </div>
                    </div>
                  </div>

                  <!-- Interactive Tip on Widescreen Preservation -->
                  <div class="pad-explanation-box">
                    <div style="font-size:12px;font-weight:800;color:var(--brand-ink);display:flex;align-items:center;gap:6px">
                      <span style="color:var(--brand);font-size:14px">💡</span> Why Safe Area Padding Unlocks +66% More View:
                    </div>
                    <div style="font-size:11.5px;color:var(--dim);line-height:1.48;margin-top:5px">
                      Converting standard 16:9 widescreen to vertical 9:16 directly cuts off <b>68.4%</b> of the visible video. Setting <b>20% top & 20% bottom padding</b> reserves dedicated safe space for the <b>Top Viral Yellow Hook</b> and <b>TikTok Captions</b>, preserving <b>52.7%</b> of original widescreen width (<strong style="color:var(--good)">+66% wider visual field</strong>) with zero awkward facial zoom!
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
          <span>${esc(l.uploader || "YouTube Video")} · <b style="color:var(--brand)">AI Research &amp; Verification Ready</b></span>
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
          <span>${(f.size / (1024 * 1024)).toFixed(1)} MB · <b style="color:var(--brand)">AI Research &amp; Verification Ready</b></span>
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
  const videoSrc = (c.filename || c.output_file) ? `/media/${j.id}/${encodeURIComponent(c.filename)}` : "";
  const coversList = (c.covers && c.covers.length) ? c.covers : (c.cover ? [c.cover] : []);
  const activeCover = c.cover || (coversList.length ? coversList[0] : "");
  const thumbSrc = activeCover ? `/media/${j.id}/${encodeURIComponent(activeCover)}` : (c.filename ? `/media/${j.id}/${encodeURIComponent(c.filename.replace(/\.[^.]+$/, '.jpg'))}` : "");
  const folderName = c.folder_name || (c.topic ? c.topic.replace(/[^\w\s-]/g, '').trim().replace(/\s+/g, '_') : "");

  return `
    <article class="clip ${S.sel.has(key) ? "picked" : ""}">
      <button class="shot" data-act="openclip" ${a} aria-label="Open clip: ${esc(c.title || c.hook)}">
        ${thumbSrc ? `<img src="${thumbSrc}" alt="" loading="lazy">` : videoSrc ? `<video src="${videoSrc}#t=1" muted playsinline></video>` : `<span class="making">${c.status === "rendering" ? "Rendering vertical clip…" : "Ready"}</span>`}
        <span class="veil"><span>${ic("play")}</span></span>
        <span class="badge l ${scoreCls(c.virality_score || c.score || 90)}" title="AI Virality Score">${c.virality_score || c.score || 90}</span>
        <span class="badge r">${fmt(c.duration || (c.end - c.start) || 30)}</span>
        ${coversList.length > 1 ? `
          <div class="clip-thumb-bar" role="group" aria-label="Choose viral thumbnail variation" onclick="event.stopPropagation()">
            ${coversList.map((cov, idx) => {
              const cSrc = `/media/${j.id}/${encodeURIComponent(cov)}`;
              const isSel = (cov === activeCover) || (!activeCover && idx === 0);
              const archetypes = [
                { icon: "🤯", label: "Curiosity" },
                { icon: "⚠️", label: "Warning" },
                { icon: "🎯", label: "Authority" }
              ];
              const aMeta = archetypes[idx] || { icon: "🖼️", label: `Cover ${idx + 1}` };
              return `<button type="button" class="thumb-pill-btn ${isSel ? "active" : ""}" data-act="switchcardthumb" ${a} data-cov="${esc(cov)}" data-src="${cSrc}" title="${aMeta.label} Cover (${idx + 1} of ${coversList.length})">${aMeta.icon} <span class="pill-lbl">${aMeta.label}</span></button>`;
            }).join("")}
          </div>
        ` : ""}
      </button>
      <div class="clip-body">
        ${folderName ? `<div class="clip-folder-badge" title="Organized in dedicated folder: ${esc(folderName)}"><span class="f-icon">📁</span><span class="f-name">${esc(folderName)}</span></div>` : ""}
        <div class="hook">${esc(c.hook || c.title || "Viral Highlight")}</div>
        <div class="ttl">${esc(c.title || c.full_transcript || "")}</div>
        <div class="clip-foot">
          <label class="selck" title="Select clip"><input type="checkbox" data-sel="${key}" ${S.sel.has(key) ? "checked" : ""}></label>
          ${videoSrc ? `<a class="btn sm icon ghost" href="${videoSrc}" download title="Download MP4">${ic("down")}</a>` : ""}
          ${thumbSrc ? `<a class="btn sm icon ghost card-thumb-dl" href="${thumbSrc}" download="${esc(activeCover ? activeCover.split('/').pop() : (c.filename ? c.filename.replace(/\.[^.]+$/, '.jpg') : 'thumbnail.jpg'))}" title="Download TikTok Cover Thumbnail (1080x1920 JPG)" style="font-size:13px;line-height:1">🖼️</a>` : ""}
          <a class="btn sm ghost" href="/api/clips/${c.id}/download-zip" download title="Download Complete Clip Package (Folder with MP4, 3 Viral Covers, Clip Docs ZIP)" style="font-size:11px;font-weight:700;padding:0 7px;gap:3px;color:var(--brand)">📦 ZIP</a>
          <button type="button" class="btn sm icon ghost gdrive-card-btn" data-act="uploadgdrive" data-j="${j.id}" data-c="${c.id}" title="Upload to Google Drive (for mobile TikTok)">▲</button>
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
          ${!busy ? `<button class="btn sm highlight-editor-btn" data-act="openeditor" data-j="${j.id}" title="Open Interactive Timeline Multi-Clip Editor">🎬 Timeline Editor</button>` : ""}
          ${clips.length ? `<a class="btn sm ghost" href="/api/projects/${j.id}/download-docs" download title="Download Session Docs (.docx) with topics, titles & hashtags" style="font-size:11px;font-weight:600;padding:0 8px;gap:4px">📄 Docs</a>` : ""}
          ${clips.length ? `<a class="btn sm ghost" href="/api/projects/${j.id}/download-zip" download title="Download all clips organized in dedicated topic folders with 3 viral thumbnails & docs" style="font-size:11px;font-weight:700;padding:0 8px;gap:4px;color:var(--brand)">📦 ZIP All</a>` : ""}
          <button class="btn sm icon ghost" data-act="deljob" data-j="${j.id}" title="Delete project">${ic("trash")}</button>
          <label class="selck" title="Select project"><input type="checkbox" data-sel="j:${j.id}" ${S.sel.has("j:" + j.id) ? "checked" : ""}></label>
        </div>
      </div>

      ${busy ? pipelineTrackerHtml(j, progressPct) : ""}

      <!-- Expandable Executive Podcast Brief & Heatmap -->
      ${hasBrief && briefExpanded ? briefHtml(j) : ""}

      <!-- 9:16 Vertical Clip Cards -->
      ${clips.length ? `<div class="grid">${clips.map(c => clipHtml(j, c)).join("")}</div>` : ""}
    </section>`;
}

function pipelineTrackerHtml(j, pct) {
  // Determine current active pipeline stage (1 to 5)
  let activeStep = j.step_index || 1;
  if (!j.step_index) {
    if (pct < 30) activeStep = 1;
    else if (pct < 45) activeStep = 2;
    else if (pct < 65) activeStep = 3;
    else if (pct < 85) activeStep = 4;
    else activeStep = 5;
  }

  const stages = [
    { num: 1, name: "Transcribe", label: "Whisper AI" },
    { num: 2, name: "AI Research", label: "Verify Viral Clips" },
    { num: 3, name: "Framing", label: "Safe Layout" },
    { num: 4, name: "Subtitles", label: "Kinetic ASS" },
    { num: 5, name: "Render & Covers", label: "NVENC / CPU" }
  ];

  const currentMsg = j.stage || j.status_message || "Processing video pipeline...";
  const detailMsg = j.step_detail || currentMsg;

  return `
    <div class="pipeline-tracker-card">
      <div class="pipeline-tracker-head">
        <div class="pipeline-tracker-title">
          <span class="pipeline-tracker-badge">
            <span class="pipeline-pulse-dot"></span>
            AI Studio Pipeline Active
          </span>
          <span style="font-size:12px;color:var(--dim);font-weight:600">Step ${activeStep} of 5: ${esc(stages[activeStep - 1]?.name || "Processing")}</span>
        </div>
        <div class="pipeline-tracker-pct">${pct}<span>%</span></div>
      </div>

      <!-- 5-Step Visual Stepper -->
      <div class="pipeline-stepper-grid">
        ${stages.map(s => {
          let state = "pending";
          let stateLabel = "Pending";
          if (s.num < activeStep || pct >= 100) {
            state = "done";
            stateLabel = "Done ✓";
          } else if (s.num === activeStep) {
            state = "active";
            stateLabel = "In Progress";
          }
          return `
            <div class="pipeline-step-node ${state}">
              <div class="step-node-header">
                <span class="step-node-num">${state === "done" ? "✓" : s.num}</span>
                <span class="step-node-state">${stateLabel}</span>
              </div>
              <span class="step-node-name">${s.name}</span>
            </div>
          `;
        }).join("")}
      </div>

      <!-- Master Glowing Rail Progress Bar -->
      <div class="pipeline-progress-rail">
        <div class="pipeline-progress-fill" style="width:${Math.max(3, Math.min(100, pct))}%"></div>
      </div>

      <!-- Live Activity & Sub-step Telemetry -->
      <div class="pipeline-activity-box">
        <div class="pipeline-activity-info">
          ${ic("bolt")}
          <span class="pipeline-activity-text">${esc(currentMsg)}</span>
        </div>
        <span class="pipeline-activity-detail">${esc(detailMsg !== currentMsg ? detailMsg : "")}</span>
      </div>
    </div>
  `;
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
    <button class="btn sm" data-act="selgdrive" style="background:rgba(0,229,255,0.15);border:1px solid rgba(0,229,255,0.5);color:#00E5FF;font-weight:700">
      <span style="font-weight:900">▲</span> Send to Drive (${n})
    </button>
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
    if (tagTop) tagTop.innerHTML = `<span class="tag-dot"></span>Top Safe Area: ${topVal}% (${topPx}px)`;
  }

  if (bottomOverlay) {
    bottomOverlay.style.height = `${bottomVal}%`;
    bottomOverlay.style.display = bottomVal > 0 ? "flex" : "none";
    if (tagBottom) tagBottom.innerHTML = `<span class="tag-dot"></span>Bottom Safe Area: ${bottomVal}% (${botPx}px)`;
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
    if (tagTop) tagTop.innerHTML = `<span class="tag-dot"></span>Top Safe Area: ${topVal}% (${topPx}px)`;
  }

  if (bottomOverlay) {
    bottomOverlay.style.height = `${bottomVal}%`;
    bottomOverlay.style.display = bottomVal > 0 ? "flex" : "none";
    if (tagBottom) tagBottom.innerHTML = `<span class="tag-dot"></span>Bottom Safe Area: ${bottomVal}% (${botPx}px)`;
  }

  if (activeAreaVal) activeAreaVal.innerHTML = `<strong style="color:var(--brand)">${activeVal}%</strong> (${activeHPx}px)`;
  if (padSummary) padSummary.textContent = `Top: ${topPx}px • Bottom: ${botPx}px`;
  if (fovVal) fovVal.innerHTML = `<strong style="color:var(--brand-deep)">${fovPct}%</strong> of widescreen kept`;
  if (zoomVal) {
    if (topVal === 0 && bottomVal === 0) {
      zoomVal.innerHTML = `<span style="color:var(--dim)">Standard 9:16 Cropping</span>`;
    } else {
      zoomVal.innerHTML = `<strong style="color:var(--good)">+${zoomGain}% Wider Field</strong> (Minimal Zoom)`;
    }
  }

  const gaugeBar = $("#o_gauge_active_bar");
  if (gaugeBar) gaugeBar.style.width = `${activeVal}%`;

  const statusBadge = $("#o_fov_status_badge");
  if (statusBadge) {
    if (topVal >= 15 && bottomVal >= 15) {
      statusBadge.textContent = "Optimal Widescreen (+66% FOV)";
      statusBadge.className = "telem-badge-opt optimal";
    } else if (topVal > 0 || bottomVal > 0) {
      statusBadge.textContent = "Balanced Framing";
      statusBadge.className = "telem-badge-opt balanced";
    } else {
      statusBadge.textContent = "Standard 9:16 Crop";
      statusBadge.className = "telem-badge-opt standard";
    }
  }

  const bannerEl = $("#composerPreviewBanner");
  const bannerInput = $("#o_hook");
  if (bannerEl) {
    let text = (bannerInput && bannerInput.value.trim()) ? bannerInput.value.trim().toUpperCase() : "THE REAL REASON 99% OF PEOPLE FAIL AT THIS HABIT";
    text = text.replace(/[\[\]]/g, "").trim();
    bannerEl.innerHTML = `<span class="preview-banner-viral-pill">${esc(text)}</span>`;
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
  const thumbSrc = c.cover ? `/media/${j.id}/${encodeURIComponent(c.cover)}` : (c.filename ? `/media/${j.id}/${encodeURIComponent(c.filename.replace(/\.[^.]+$/, '.jpg'))}` : "");
  const words = c.words || [];
  D.activeWords = JSON.parse(JSON.stringify(words));
  D.selectedWordIdx = null;

  const topPad = Math.max(0, Math.min(45, Number(c.top_padding || 0)));
  const bottomPad = Math.max(0, Math.min(45, Number(c.bottom_padding || 0)));
  const activeArea = Math.max(20, 100 - topPad - bottomPad);

  // Initialize Thumbnail Designer State for this clip
  D.thumbStyle = "hormozi";
  D.thumbColor = "#FFE600";
  D.thumbArch = "curiosity";
  D.thumbSec = Math.min((c.end || 30), (c.start || 0) + 1.2);

  const initTopicWords = (c.title || "SUCCESS").trim().toUpperCase().split(/\s+/);
  const defaultHl1 = "THE UNTOLD TRUTH";
  const defaultHl2 = ("ABOUT " + (initTopicWords[0] || "THIS")).slice(0, 20);
  const defaultCat = (initTopicWords[0] ? initTopicWords[0] + " PROTOCOL" : "PODCAST EXCLUSIVE").slice(0, 22);

  dlg.innerHTML = `
    <div class="editor">
      <!-- Left Stage: 9:16 Vertical Player & TikTok Cover Studio Switcher -->
      <div class="stage" id="stage">
        <div class="stage-mode-bar">
          <button type="button" class="stage-tab-btn active" id="btn_stage_video" data-act="switchstagemode" data-mode="video">
            ${ic("film")} Video Player
          </button>
          <button type="button" class="stage-tab-btn" id="btn_stage_thumb" data-act="switchstagemode" data-mode="thumb">
            🖼️ TikTok Cover Studio
          </button>
        </div>

        <div class="stage-canvas-frame" id="stageCanvasFrame">
          <!-- Video Player Mode -->
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

          <!-- TikTok Thumbnail Cover Studio Stage Overlay -->
          <div class="thumb-studio-stage" id="thumbStudioStage" style="display:none">
            <div class="thumb-preview-wrap">
              <img id="editorThumbImg" class="thumb-preview-img" src="${thumbSrc || ''}" alt="TikTok Cover Thumbnail">

              <!-- TikTok 3:4 Profile Grid Overlay Guide -->
              <div class="tiktok-grid-guide" id="ttGridGuide" style="display:flex">
                <span class="grid-guide-tag">📐 3:4 Profile Grid Safe Zone</span>
                <span class="grid-guide-tag">Centered on Profile</span>
              </div>

              <!-- Authentic TikTok UI Overlay (Likes, Comments, Disc) -->
              <div class="tiktok-mock-overlay" id="ttMockOverlay" style="display:flex">
                <div class="tt-mock-actions">
                  <div class="tt-mock-btn"><div class="tt-mock-icon">❤️</div><span class="tt-mock-count">142K</span></div>
                  <div class="tt-mock-btn"><div class="tt-mock-icon">💬</div><span class="tt-mock-count">2,410</span></div>
                  <div class="tt-mock-btn"><div class="tt-mock-icon">🔖</div><span class="tt-mock-count">18.5K</span></div>
                  <div class="tt-mock-btn"><div class="tt-mock-icon">↗️</div><span class="tt-mock-count">6,920</span></div>
                  <div class="tt-mock-disc"></div>
                </div>
                <div class="tt-mock-caption-zone">
                  <div class="tt-mock-user">@clipforge_podcast ✓</div>
                  <div class="tt-mock-desc">${esc(c.title || "Viral Podcast Highlight")} #podcast #viral</div>
                  <div class="tt-mock-sound">♫ Original Sound - Trending Podcast</div>
                </div>
              </div>
            </div>

            <!-- Frame Timestamp Scrubber -->
            <div class="thumb-scrubber-bar">
              <span style="font-size:11px;font-weight:700;color:var(--dim);white-space:nowrap">📸 Frame:</span>
              <input type="range" id="ed_thumb_sec" min="${c.start || 0}" max="${c.end || 30}" step="0.5" value="${D.thumbSec}" oninput="document.getElementById('ed_thumb_sec_val').textContent = Number(this.value).toFixed(1) + 's'; D.thumbSec = Number(this.value);">
              <span id="ed_thumb_sec_val" style="font-size:11px;font-weight:800;color:var(--brand);min-width:32px">${D.thumbSec.toFixed(1)}s</span>
              <button type="button" class="btn sm" data-act="grabthumbframe" data-c="${c.id}" style="padding:2px 8px;font-size:11px" title="Scrub & re-render cover with this speaker frame">Sample</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Panel: Streamlined Tabbed Inspector -->
      <div class="panel">
        <!-- Top Dialog Header -->
        <div class="modal-dialog-header">
          <div class="modal-header-meta">
            <span class="badge ${scoreCls(c.virality_score || 90)}" style="position:static">Score ${c.virality_score || 90} · High engagement hook</span>
            <h3 class="modal-clip-title">${esc(c.title || "Viral Clip")}</h3>
          </div>
          <button class="btn icon ghost modal-close-btn" data-act="closedlg" title="Close editor">${ic("x")}</button>
        </div>

        <!-- AI Video Edit Copilot -->
        <div class="ai-copilot-container">
          <div class="ai-copilot-header">
            <span class="ai-copilot-title">${ic("bolt")} AI Video Edit Copilot</span>
            <span class="ai-copilot-badge">Natural Language Re-Editor</span>
          </div>
          <div class="ai-copilot-input-row">
            <input id="ai_copilot_prompt" placeholder="Command AI: e.g. 'Make hook more aggressive', 'Focus on wealth', 'Hype style'..." />
            <button type="button" class="btn sm primary" data-act="runcopilot">${ic("bolt")} Apply Edit</button>
          </div>
          <div class="ai-copilot-quick-chips">
            <button type="button" class="copilot-chip" data-act="copilotpreset" data-preset="sharpen_hook">⚡ Sharpen Hook</button>
            <button type="button" class="copilot-chip" data-act="copilotpreset" data-preset="add_controversy">🔥 Add Controversy</button>
            <button type="button" class="copilot-chip" data-act="copilotpreset" data-preset="focus_wealth">💰 Focus on Wealth</button>
            <button type="button" class="copilot-chip" data-act="copilotpreset" data-preset="mrbeast_hype">⚡ MrBeast Subtitles</button>
            <button type="button" class="copilot-chip" data-act="copilotpreset" data-preset="clean_editorial">🎯 Clean Minimal</button>
          </div>
        </div>

        <!-- Clean Navigation Tabs for Edit Modal -->
        <div class="modal-subnav-tabs" role="tablist">
          <button type="button" class="modal-tab-btn active" data-modaltab="video" role="tab">
            ${ic("sliders")} Video & Framing
          </button>
          <button type="button" class="modal-tab-btn" data-modaltab="captions" role="tab">
            ${ic("chat")} Captions & Words
          </button>
          <button type="button" class="modal-tab-btn" data-modaltab="cover" role="tab">
            🖼️ Cover Studio
          </button>
          <button type="button" class="modal-tab-btn" data-modaltab="social" role="tab">
            ${ic("send")} Social Copy
          </button>
        </div>

        <!-- TAB 1: VIDEO & FRAMING -->
        <div class="modal-tab-pane active" id="pane_modaltab_video">
          <!-- Hook Text & Caption Style -->
          <div class="modal-field-group">
            <label class="f">Top Safe-Area Hook Banner (6–12 words recommended)
              <input id="ed_hook" value="${esc(c.hook || c.title || "")}" maxlength="140" placeholder="e.g. THE REAL REASON 99% OF PEOPLE FAIL AT THIS...">
            </label>
          </div>

          <div class="two">
            <label class="f">Caption Style
              <select id="ed_style">
                <option value="hormozi" ${c.subtitle_style === "hormozi" ? "selected" : ""}>Hormozi Impact (Yellow & White)</option>
                <option value="hype" ${c.subtitle_style === "hype" ? "selected" : ""}>MrBeast Neon (High Energy)</option>
                <option value="cyber" ${c.subtitle_style === "cyber" ? "selected" : ""}>Cyber Glow (Neon Cyan)</option>
                <option value="clean" ${c.subtitle_style === "clean" ? "selected" : ""}>Clean Amber (Editorial)</option>
              </select>
            </label>
            <label class="f">Camera Layout & Framing
              <select id="ed_layout" onchange="const fb=document.getElementById('ed_fit_options'); if(fb) fb.style.display=(this.value==='fit_canvas'?'block':'none'); const v=document.getElementById('editorVideo'); if(v) v.style.objectFit=(this.value==='fit_canvas'?'contain':'cover');">
                <option value="fit_canvas" ${c.layout_mode === "fit_canvas" ? "selected" : ""}>Fit Full Video (Zero Crop)</option>
                <option value="face_center" ${c.layout_mode === "face_center" ? "selected" : ""}>Smart Face Center</option>
                <option value="speaker_focus" ${c.layout_mode === "speaker_focus" ? "selected" : ""}>Active Speaker Tracking</option>
                <option value="split_screen" ${c.layout_mode === "split_screen" ? "selected" : ""}>Split-Screen (Host + Guest)</option>
                <option value="blur" ${c.layout_mode === "blur" ? "selected" : ""}>Blurred Ambient Fill</option>
                <option value="center_crop" ${c.layout_mode === "center_crop" ? "selected" : ""}>Center Crop (9:16)</option>
              </select>
            </label>
          </div>

          <!-- Safe Area & Spacing Controls in Clip Editor -->
          <div class="safe-area-panel" id="ed_safe_area_panel">
            <div class="safe-area-header">
              <div class="safe-area-title">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18"/></svg>
                <span>Safe Area & Padding</span>
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
                  <span class="preset-title">0% Full</span><small>Max Zoom</small>
                </button>
                <button type="button" class="preset-pill ${topPad===10&&bottomPad===10?'on':''}" data-act="seteditorpad" data-top="10" data-bottom="10">
                  <span class="preset-title">10% + 10%</span><small>80% Area</small>
                </button>
                <button type="button" class="preset-pill ${topPad===15&&bottomPad===15?'on':''}" data-act="seteditorpad" data-top="15" data-bottom="15">
                  <span class="preset-title">15% + 15%</span><small>70% Area</small>
                </button>
                <button type="button" class="preset-pill star ${topPad===20&&bottomPad===20?'on':''}" data-act="seteditorpad" data-top="20" data-bottom="20">
                  <span class="preset-title">20% + 20% <span class="badge-rec">RECOMMENDED</span></span><small>60% Area</small>
                </button>
                <button type="button" class="preset-pill ${topPad===25&&bottomPad===25?'on':''}" data-act="seteditorpad" data-top="25" data-bottom="25">
                  <span class="preset-title">25% + 25%</span><small>50% Area</small>
                </button>
              </div>
            </div>
            
            <div class="pad-control-grid">
              <div class="pad-control-row">
                <div class="pad-label-row">
                  <div class="pad-label-left">
                    <span class="pad-icon-dot top"></span>
                    <span class="pad-label">Top Padding (Hook Safe Area)</span>
                  </div>
                  <div class="pad-val-box">
                    <input type="number" id="ed_pad_top_num" class="pad-num-input" min="0" max="45" step="1" value="${topPad}">
                    <span class="pad-unit">%</span>
                  </div>
                </div>
                <input type="range" id="ed_pad_top" class="pad-slider" min="0" max="45" step="1" value="${topPad}">
              </div>

              <div class="pad-control-row">
                <div class="pad-label-row">
                  <div class="pad-label-left">
                    <span class="pad-icon-dot bottom"></span>
                    <span class="pad-label">Bottom Padding (Captions Safe Area)</span>
                  </div>
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

          <div id="ed_fit_options" style="display:${(c.layout_mode === 'fit_canvas' || !c.layout_mode) ? 'block' : 'none'};background:#201712;border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:10px;margin-bottom:8px;color:#F8F3EF">
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
            <label class="sw"><input type="checkbox" id="ed_clarifier" checked><span style="color:#EDE4DE">Studio Voice Clarifier (FFT Denoising & Broadcast Normalizer)</span></label>
          </div>

          <div class="two">
            <label class="f">Start (seconds)<input id="ed_start" type="number" step="0.5" value="${c.start || 0}"></label>
            <label class="f">End (seconds)<input id="ed_end" type="number" step="0.5" value="${c.end || 30}"></label>
          </div>
        </div>

        <!-- TAB 2: CAPTIONS & WORD KARAOKE -->
        <div class="modal-tab-pane" id="pane_modaltab_captions">
          <div class="row" style="justify-content:space-between;align-items:center;margin-bottom:8px">
            <span style="font-size:12px;font-weight:700;color:#F8F3EF">Interactive Word Karaoke</span>
            <span style="font-size:11px;color:#C8BCB4">Click any word to seek, correct, or color-tag</span>
          </div>

          <div class="karaoke-chips-flow" id="karaokeChips">
            ${words.length ? words.map((w, idx) => `
              <span class="word-chip ${w.color ? "hl-" + w.color : ""}" data-idx="${idx}" data-word="${esc(w.word)}" data-start="${w.start}" data-end="${w.end}">${esc(w.word)}</span>
            `).join("") : `<span class="sub" style="color:#C8BCB4">Click words in video to seek</span>`}
          </div>

          <!-- Word Inspector Card -->
          <div id="word_inspector" style="display:none;background:#201712;border:1px solid rgba(255,139,51,0.3);border-radius:8px;padding:12px;margin:10px 0;color:#F8F3EF">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
              <span style="font-size:12px;font-weight:700">Selected Word: <b id="inspect_word_label" style="color:var(--brand)"></b></span>
              <button type="button" class="btn sm ghost" onclick="document.getElementById('word_inspector').style.display='none'">✕</button>
            </div>
            <div style="display:flex;gap:6px;margin-bottom:8px">
              <input id="inspect_word_input" placeholder="Edit word text..." style="flex:1">
              <button type="button" class="btn sm primary" data-act="applywordedit">Save Word Text</button>
            </div>
            <div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center">
              <span style="font-size:11px;color:#C8BCB4">Color Tag:</span>
              <button type="button" class="btn sm ghost" data-act="tagwordcolor" data-color="gold" style="color:#FFB800">● Gold</button>
              <button type="button" class="btn sm ghost" data-act="tagwordcolor" data-color="green" style="color:#00FF55">● Green</button>
              <button type="button" class="btn sm ghost" data-act="tagwordcolor" data-color="coral" style="color:#FF3333">● Red</button>
              <button type="button" class="btn sm ghost" data-act="tagwordcolor" data-color="cyan" style="color:#00E5FF">● Cyan</button>
              <button type="button" class="btn sm ghost" data-act="tagwordcolor" data-color="none" style="color:#C8BCB4">✕ None</button>
              <span style="font-size:11px;color:#C8BCB4;margin-left:6px">Timeline:</span>
              <button type="button" class="btn sm ghost" data-act="setwordstart" style="color:#EDE4DE">Set Start Cut</button>
              <button type="button" class="btn sm ghost" data-act="setwordend" style="color:#EDE4DE">Set End Cut</button>
            </div>
          </div>
        </div>

        <!-- TAB 3: TIKTOK COVER STUDIO -->
        <div class="modal-tab-pane" id="pane_modaltab_cover">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <div>
              <h4 style="margin:0;font-size:13px;font-weight:700;color:#F8F3EF">Universal Editorial Cover Studio</h4>
              <p class="sub" style="font-size:11.5px;color:#C8BCB4">Real speaker photography + bold left-aligned typography</p>
            </div>
            <button type="button" class="btn sm" data-act="aithumbhooks" data-c="${c.id}" style="background:linear-gradient(135deg,#FF8B33,#FFB800);color:#1E1612;font-weight:700;font-size:11px">
              ${ic("bolt")}AI Hook Ideas
            </button>
          </div>

          <!-- Dropdown/Panel for AI Suggested Thumbnail Hooks -->
          <div id="ai_thumb_hooks_panel" style="display:none;background:#1E1510;border:1px solid rgba(255,139,51,0.3);border-radius:8px;padding:10px;margin-bottom:12px"></div>

          <!-- 3 Pre-Generated Viral Variations Gallery -->
          ${(() => {
            const modalCovers = (c.covers && c.covers.length) ? c.covers : (c.cover ? [c.cover] : []);
            if (!modalCovers.length) return "";
            return `
              <div class="covers-variation-gallery">
                <div class="covers-gallery-title-row">
                  <span class="gallery-title">🎯 3 Pre-Generated Viral Cover Variations</span>
                  <span class="gallery-subtitle">Choose the highest-CTR angle for TikTok. Click "Set Active" to select as primary cover.</span>
                </div>
                <div class="covers-cards-grid">
                  ${modalCovers.map((cov, idx) => {
                    const cSrc = `/media/${j.id}/${encodeURIComponent(cov)}`;
                    const isCurrent = (cov === (c.cover || modalCovers[0]));
                    const archetypes = [
                      { name: "Curiosity Loop", icon: "🤯", desc: "Golden hook ribbon, high psychological intrigue", accent: "#FFE600" },
                      { name: "Red Alert", icon: "⚠️", desc: "Urgent warning & mistake callout for urgency", accent: "#EF4444" },
                      { name: "Authority Blueprint", icon: "🎯", desc: "Cyan system blueprint & credible framework", accent: "#00E5FF" }
                    ];
                    const aInfo = archetypes[idx] || { name: `Cover ${idx + 1}`, icon: "🖼️", desc: "Viral generated thumbnail", accent: "#FFE600" };
                    return `
                      <div class="cover-card-box ${isCurrent ? 'is-active-cover' : ''}">
                        <div class="cover-card-preview">
                          <img src="${cSrc}" alt="${aInfo.name}" loading="lazy">
                          ${isCurrent ? `<span class="active-cover-pill">✓ ACTIVE</span>` : ""}
                        </div>
                        <div class="cover-card-meta">
                          <div class="cover-card-name" style="color:${aInfo.accent}">${aInfo.icon} ${aInfo.name}</div>
                          <div class="cover-card-desc">${aInfo.desc}</div>
                          <div class="cover-card-actions">
                            <button type="button" class="btn sm ${isCurrent ? 'ghost disabled' : 'primary-soft'}" data-act="setdefaultcover" data-c="${c.id}" data-cov="${esc(cov)}" data-src="${cSrc}">
                              ${isCurrent ? '✓ Active' : 'Set Active'}
                            </button>
                            <a class="btn sm icon ghost" href="${cSrc}" download="${esc(cov.split('/').pop())}" title="Download 1080x1920 JPG">🖼️</a>
                          </div>
                        </div>
                      </div>
                    `;
                  }).join("")}
                </div>
              </div>
            `;
          })()}

          <div style="font-size:12px;font-weight:700;color:var(--dim);margin:14px 0 8px 0;border-top:1px dashed var(--line);padding-top:10px">
            🎨 Custom Cover Fine-Tuner & Re-Generator:
          </div>

          <div class="hook-archetypes-row" style="margin-bottom:12px">
            <button type="button" class="hook-arch-pill on" data-act="setthumbarch" data-arch="curiosity">🤯 Curiosity Loop</button>
            <button type="button" class="hook-arch-pill" data-act="setthumbarch" data-arch="warning">⚠️ Warning / Mistake</button>
            <button type="button" class="hook-arch-pill" data-act="setthumbarch" data-arch="formula">📋 3-Rule Blueprint</button>
            <button type="button" class="hook-arch-pill" data-act="setthumbarch" data-arch="callout">🎯 Audience Callout</button>
          </div>

          <!-- Accent Color Swatches -->
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
            <span style="font-size:11.5px;font-weight:700">Keyword Highlight Accent Color</span>
            <span id="thumb_color_label" style="font-size:11px;font-weight:800;color:#FFE600">Neon Yellow</span>
          </div>
          <div class="color-swatches-row" style="margin-bottom:12px">
            <button type="button" class="color-swatch-btn on" data-act="setthumbcolor" data-color="#FFE600" data-name="Neon Yellow" style="background:#FFE600" title="Neon Yellow"></button>
            <button type="button" class="color-swatch-btn" data-act="setthumbcolor" data-color="#22C55E" data-name="Electric Green" style="background:#22C55E" title="Electric Green"></button>
            <button type="button" class="color-swatch-btn" data-act="setthumbcolor" data-color="#00E5FF" data-name="Electric Cyan" style="background:#00E5FF" title="Electric Cyan"></button>
            <button type="button" class="color-swatch-btn" data-act="setthumbcolor" data-color="#FF3B30" data-name="Crimson Red" style="background:#FF3B30" title="Crimson Red"></button>
            <button type="button" class="color-swatch-btn" data-act="setthumbcolor" data-color="#FFFFFF" data-name="Pure White" style="background:#FFFFFF" title="Pure White"></button>
          </div>

          <!-- Editable Headline & Text Fields -->
          <div class="two">
            <label class="f">Line 1 Hook (White)<input id="ed_thumb_hl1" value="${esc(defaultHl1)}" maxlength="22"></label>
            <label class="f">Line 2 Punch (Accent Ribbon)<input id="ed_thumb_hl2" value="${esc(defaultHl2)}" maxlength="22"></label>
          </div>
          <div class="two">
            <label class="f">Top Category Pill<input id="ed_thumb_cat" value="${esc(defaultCat)}" maxlength="24"></label>
            <label class="f">Speaker / Authority Name<input id="ed_thumb_sub" value="LONGEVITY PROTOCOL" maxlength="40"></label>
          </div>

          <div style="margin-top:12px">
            <button type="button" class="btn primary" style="width:100%" data-act="regen_thumb" data-c="${c.id}">
              ${ic("bolt")}⚡ Render High-Res TikTok Cover (1080x1920)
            </button>
          </div>
        </div>

        <!-- TAB 4: SOCIAL MEDIA POST COPY -->
        <div class="modal-tab-pane" id="pane_modaltab_social">
          <div class="row" style="justify-content:space-between;align-items:center;margin-bottom:12px">
            <div>
              <span style="font-size:12.5px;font-weight:800;color:#F8F3EF">Multi-Platform Publishing Kit</span>
              <div style="font-size:11px;color:#A89C94">TikTok · Instagram Reels · YouTube Shorts</div>
            </div>
            <button class="btn sm primary" data-act="gensocialkit">${ic("bolt")} Auto-Generate Social Kit</button>
          </div>

          <div id="social_kit_rendered_box" style="margin-bottom:12px"></div>

          <label class="f">Title<input id="ed_title" value="${esc(c.title || "")}"></label>
          <label class="f">Description<textarea id="ed_desc" rows="3">${esc(c.description || (c.social_kit?.youtube_shorts?.description) || "")}</textarea></label>
          <label class="f">Hashtags<input id="ed_tags" value="${esc((c.social_kit?.viral_hashtags || []).join(" "))}"></label>
        </div>

        <!-- Persistent Primary Action Footer -->
        <div class="modal-persistent-footer">
          <button class="btn primary reburn-clip-btn" data-act="remake">
            <span class="btn-shine"></span>
            ${ic("scissors")}
            <span>Save & Re-Burn Clip</span>
          </button>
          ${videoSrc ? `<a class="btn" id="ed_download_btn" href="${videoSrc}" download>${ic("down")}Download MP4</a>` : `<a class="btn" id="ed_download_btn" href="#" download style="display:none">${ic("down")}Download MP4</a>`}
          ${thumbSrc ? `<a class="btn" id="ed_thumb_btn" href="${thumbSrc}" download="${esc(c.filename ? c.filename.replace(/\.[^.]+$/, '.jpg') : 'thumbnail.jpg')}" title="Download TikTok Cover Thumbnail (1080x1920 JPG)">🖼️ Cover</a>` : ""}
          <a class="btn clip-zip-btn" href="/api/clips/${c.id}/download-zip" download title="Download Complete Clip Package (Folder with MP4, 3 Thumbnails, Clip Docs as ZIP)">📦 Clip ZIP</a>
          <button type="button" class="btn gdrive-upload-btn" data-act="uploadgdrive" data-j="${j.id}" data-c="${c.id}">
            <span style="font-weight:900">▲</span> Drive
          </button>
          <button class="btn" data-act="copydlg" title="Copy social caption">${ic("copy")}Copy</button>
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
    ["gdrive", "Google Drive", "cloud", "Sync clips to mobile for TikTok"],
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
        ${tab === "ai" ? aiSettingsHtml() : tab === "gdrive" ? gdriveSettingsHtml() : tab === "apps" ? appsSettingsHtml() : tab === "speech" ? speechSettingsHtml() : storageSettingsHtml()}
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

function gdriveSettingsHtml() {
  const g = S.gdrive || { connected: false, folder_name: "ClipForge Clips" };
  if (g.connected) {
    return `
    <section class="set-sec">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px">
        <div>
          <h2>Google Drive Cloud Sync</h2>
          <p class="help">Sync your viral clips directly to Google Drive. Download instantly on your mobile phone to post to TikTok!</p>
        </div>
        <span class="pill ok" style="font-size:12px;padding:4px 10px"><span style="color:#00E5FF;font-weight:900">▲</span> Connected</span>
      </div>

      <div class="gdrive-status-card" style="background:#191410;border:1px solid rgba(0,229,255,0.3);border-radius:12px;padding:20px;margin:16px 0">
        <div style="display:flex;align-items:center;gap:14px;margin-bottom:16px">
          <div style="width:48px;height:48px;border-radius:50%;background:rgba(0,229,255,0.15);display:flex;align-items:center;justify-content:center;font-size:24px;color:#00E5FF;font-weight:900">▲</div>
          <div>
            <div style="font-size:15px;font-weight:700;color:#F8F3EF">${esc(g.name || "Google Drive Account")}</div>
            <div style="font-size:12.5px;color:#C8BCB4">${esc(g.email || "")}</div>
          </div>
        </div>

        <div style="background:#110E0C;border-radius:8px;padding:12px 16px;margin-bottom:16px;display:flex;justify-content:space-between;align-items:center">
          <div>
            <span style="font-size:11px;text-transform:uppercase;color:#C8BCB4;font-weight:700;letter-spacing:0.04em">Destination Folder:</span>
            <div style="font-size:14px;font-weight:600;color:#00E5FF;margin-top:2px">📁 ${esc(g.folder_name || "ClipForge Clips")}</div>
          </div>
          <a href="https://drive.google.com" target="_blank" rel="noopener" class="btn sm" style="background:rgba(255,139,51,0.15);color:var(--brand);border:1px solid rgba(255,139,51,0.3)">Open Google Drive ↗</a>
        </div>

        <div class="row" style="gap:10px">
          <button type="button" class="btn sm danger" data-act="disconnectgdrive">Disconnect Account</button>
        </div>
      </div>

      <div class="pad-explanation-box" style="margin-top:16px">
        <div style="font-size:12px;font-weight:700;color:var(--text);display:flex;align-items:center;gap:6px">
          <span>📱</span> Mobile TikTok Upload Workflow:
        </div>
        <div style="font-size:11.5px;color:var(--dim);line-height:1.55;margin-top:4px">
          1. In ClipForge, click <b>▲ Upload to Google Drive</b> on any clip (or select multiple clips).<br>
          2. Open the <b>Google Drive</b> app on your phone.<br>
          3. Tap the video in your <b>ClipForge Clips</b> folder & select <b>"Save Video"</b> or <b>"Share to TikTok"</b>!
        </div>
      </div>
    </section>`;
  }

  return `
    <section class="set-sec">
      <h2>Connect Google Drive</h2>
      <p class="help">Connect Google Drive to upload clips with 1 click so you can download them directly on your phone and publish to TikTok!</p>

      <div class="gdrive-setup-card" style="background:#191410;border:1px solid rgba(0,229,255,0.3);border-radius:12px;padding:20px;margin:16px 0">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px">
          <span style="font-size:28px;color:#00E5FF">▲</span>
          <div>
            <div style="font-size:15px;font-weight:700;color:#F8F3EF">Google Cloud OAuth Setup</div>
            <div style="font-size:12px;color:#C8BCB4">Free personal Google Drive API access (takes ~2 minutes)</div>
          </div>
        </div>

        <div style="display:flex;flex-direction:column;gap:12px">
          <label class="f" style="color:#EDE4DE">Destination Drive Folder Name
            <input id="gd_folder" value="${esc(g.folder_name || "ClipForge Clips")}" placeholder="ClipForge Clips" style="background:#241A14;border:1px solid rgba(255,255,255,0.15);color:#FFFFFF">
          </label>

          <label class="f" style="color:#EDE4DE">Google OAuth Client ID
            <input id="gd_client_id" placeholder="e.g. 123456789-xxxx.apps.googleusercontent.com" value="${esc(g.client_id || "")}" style="background:#241A14;border:1px solid rgba(255,255,255,0.15);color:#FFFFFF">
          </label>

          <label class="f" style="color:#EDE4DE">Google OAuth Client Secret
            <input id="gd_client_secret" type="password" placeholder="e.g. GOCSPX-xxxx" style="background:#241A14;border:1px solid rgba(255,255,255,0.15);color:#FFFFFF">
          </label>

          <div class="row" style="margin-top:8px;gap:10px">
            <button type="button" class="btn primary" data-act="connectgdrive" style="background:linear-gradient(135deg,#00E5FF,#00B0FF);color:#0E0C0A;font-weight:700">
              <span style="font-weight:900">▲</span> Connect with Google Drive
            </button>
          </div>
        </div>
      </div>

      <div class="pad-explanation-box">
        <div style="font-size:12px;font-weight:700;color:var(--text);display:flex;align-items:center;gap:6px">
          <span>💡</span> Quick 3-Step Setup Instructions:
        </div>
        <div style="font-size:11.5px;color:var(--dim);line-height:1.55;margin-top:6px">
          1. Open <a href="https://console.cloud.google.com/apis/credentials" target="_blank" rel="noopener" style="color:#00E5FF;text-decoration:underline">Google Cloud Console</a> & enable the <b>Google Drive API</b>.<br>
          2. Click <b>Create Credentials</b> → <b>OAuth client ID</b> → Application type: <b>Web application</b>.<br>
          3. Under <b>Authorized redirect URIs</b>, enter:<br>
             <code style="background:#110E0C;padding:3px 8px;border-radius:4px;color:#FFB800;display:inline-block;margin:4px 0">http://localhost:8000/api/gdrive/callback</code><br>
          4. Copy your <b>Client ID</b> and <b>Client Secret</b> into the boxes above and click Connect!
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
  const hasBusyJobs = (S.jobs || []).some(j => j.status === "queued" || j.status === "running");
  const pollInterval = document.hidden ? 10000 : (hasBusyJobs ? 1000 : 3000);
  setTimeout(async () => {
    await tick();
    loop();
  }, pollInterval);
}

/* ============================================================
   CapCut-Style Professional NLE Timeline Studio
   Replaces lines 1991–2626 in app.js
   ============================================================ */

const TL_STATE = {
  projectId: null,
  project: null,
  duration: 600,
  fps: 30,
  width: 1080,
  height: 1920,
  saveStatus: "Saved",
  isDirty: false,
  clipboard: null,
  tracks: [],
  clips: [],
  activeClipIdx: 0,
  activeTab: "cuts",
  zoom: 1.0,
  isPlaying: false,
  isLooping: false,
  showTikTokGuides: false,
  volume: 1.0,
  isMuted: false,
  dragTarget: null,
  _animFrame: null,
  _undoStack: [],
  _redoStack: []
};

function fmtTimecode(sec) {
  const s = Math.max(0, Number(sec) || 0);
  const m = Math.floor(s / 60);
  const remSec = (s % 60).toFixed(1);
  const padSec = Number(remSec) < 10 ? "0" + remSec : remSec;
  return `${m}:${padSec}`;
}

function secToFrames(sec, fps = TL_STATE.fps) {
  return Math.max(0, Math.round((Number(sec) || 0) * fps));
}

function framesToSec(frames, fps = TL_STATE.fps) {
  return Math.max(0, Number(frames) || 0) / fps;
}

function buildEditorProject() {
  return {
    projectId: TL_STATE.projectId,
    title: document.getElementById("ccProjectTitle")?.value || TL_STATE.project?.title || "Untitled Project",
    fps: TL_STATE.fps,
    width: TL_STATE.width,
    height: TL_STATE.height,
    durationFrames: secToFrames(TL_STATE.duration),
    tracks: TL_STATE.tracks,
    clips: TL_STATE.clips,
    settings: {
      aspectRatio: `${TL_STATE.width}:${TL_STATE.height}`,
      resolution: `${TL_STATE.width}x${TL_STATE.height}`
    }
  };
}

function ccMarkDirty() {
  TL_STATE.isDirty = true;
  TL_STATE.saveStatus = "Unsaved changes";
  const status = document.getElementById("ccSaveStatus");
  if (status) status.textContent = TL_STATE.saveStatus;
  clearTimeout(TL_STATE._autosaveTimer);
  TL_STATE._autosaveTimer = setTimeout(ccSaveEditorProject, 1200);
}

async function ccSaveEditorProject(manual = false) {
  if (!TL_STATE.projectId) return;
  TL_STATE.saveStatus = "Saving...";
  const status = document.getElementById("ccSaveStatus");
  if (status) status.textContent = TL_STATE.saveStatus;
  try {
    const project = buildEditorProject();
    const res = await api(`/api/projects/${TL_STATE.projectId}/editor-state`, {
      method: "POST",
      body: JSON.stringify({ editor_project: project, title: project.title })
    });
    if (!res || res.status !== "success") throw new Error("Save failed");
    TL_STATE.isDirty = false;
    TL_STATE.saveStatus = "Saved";
    if (status) status.textContent = TL_STATE.saveStatus;
    if (manual) toast("Project saved", "ok");
  } catch (err) {
    TL_STATE.saveStatus = "Save failed";
    if (status) status.textContent = TL_STATE.saveStatus;
    if (manual) toast(err.message || "Failed to save project", "bad");
  }
}

function ccSaveUndo() {
  TL_STATE._undoStack.push(JSON.stringify(TL_STATE.clips));
  if (TL_STATE._undoStack.length > 100) TL_STATE._undoStack.shift();
  TL_STATE._redoStack = [];
  ccMarkDirty();
}

async function openTimelineEditor(projectId) {
  try {
    toast("Loading CapCut Studio...", "loading", "Timeline Studio");
    const proj = await api(`/api/projects/${projectId}`);
    if (!proj) { toast("Project could not be loaded", "bad"); return; }

    TL_STATE.projectId = projectId;
    TL_STATE.project = proj;
    TL_STATE.duration = Math.max(10.0, Number(proj.duration || 600));
    const saved = proj.editor_project;
    TL_STATE.fps = Number(saved?.fps || 30);
    TL_STATE.width = Number(saved?.width || 1080);
    TL_STATE.height = Number(saved?.height || 1920);
    TL_STATE.activeTab = "cuts";
    TL_STATE.zoom = 1.0;
    TL_STATE.isPlaying = false;
    TL_STATE.isLooping = false;
    TL_STATE.showTikTokGuides = false;
    TL_STATE._undoStack = [];
    TL_STATE._redoStack = [];

    if (saved?.tracks) {
      TL_STATE.tracks = saved.tracks;
      const savedClips = saved.clips || [];
      TL_STATE.clips = savedClips.length ? savedClips.map((c, i) => ({
        ...c,
        id: c.id || `clip_${i + 1}`,
        start: Math.max(0, Number(c.start ?? c.sourceInSec ?? 0)),
        end: Math.min(TL_STATE.duration, Number(c.end ?? (c.sourceInSec || 0) + (c.durationSec || 30))),
        title: c.title || c.topic || c.name || `Clip ${i + 1}`,
        hook: c.hook || c.title || ""
      })) : [];
    } else {
      TL_STATE.tracks = [
        { id: "video-main", type: "video", name: "Main Video", order: 0, visible: true, muted: false, locked: false, clips: [] },
        { id: "captions", type: "caption", name: "Captions", order: 1, visible: true, muted: false, locked: false, clips: [] },
        { id: "hooks", type: "text", name: "Hooks", order: 2, visible: true, muted: false, locked: false, clips: [] },
        { id: "audio", type: "audio", name: "Voice", order: 3, visible: true, muted: false, locked: false, clips: [] }
      ];
    }

    if ((!saved?.tracks || !TL_STATE.clips.length) && proj.clips && proj.clips.length > 0) {
      TL_STATE.clips = proj.clips.map((c, i) => ({
        id: c.id || `clip_${i + 1}`,
        start: Math.max(0, Number(c.start !== undefined ? c.start : (c.start_sec !== undefined ? c.start_sec : (i * 60)))),
        end: Math.min(TL_STATE.duration, Number(c.end !== undefined ? c.end : (c.end_sec !== undefined ? c.end_sec : ((i * 60) + 45)))),
        title: c.title || c.topic || `Clip ${i + 1}`,
        hook: c.hook || c.title || "",
        subtitle_style: c.subtitle_style || "hormozi",
        layout_mode: c.layout_mode || "speaker_focus",
        top_padding: Number(c.top_padding || 0),
        bottom_padding: Number(c.bottom_padding || 0),
        canvas_top_space: Number(c.canvas_top_space || 450),
        virality_score: Number(c.virality_score || 92)
      }));
    } else {
      TL_STATE.clips = [{
        id: "clip_1", start: 0, end: Math.min(60, TL_STATE.duration),
        title: "Viral Highlight 1", hook: "PODCAST HIGHLIGHT",
        subtitle_style: "hormozi", layout_mode: "speaker_focus",
        top_padding: 0, bottom_padding: 0, canvas_top_space: 450, virality_score: 92
      }];
    }

    TL_STATE.activeClipIdx = 0;
    renderCapCutStudio();

    const dlg = $("#timelinedlg");
    if (dlg) dlg.showModal();
  } catch (err) {
    console.error("Timeline Editor Error:", err);
    toast("Error loading timeline editor: " + (err.message || err), "bad");
  }
}

/* ---- Sub-inspector panels ---- */
function renderSubInspector(tab) {
  const clip = TL_STATE.clips[TL_STATE.activeClipIdx];
  if (!clip && tab === "cuts") return `<div class="cc-insp-empty">No clips yet. Add a clip below.</div>`;

  if (tab === "cuts") {
    const dur = Math.max(0, clip.end - clip.start).toFixed(1);
    return `
    <div class="cc-insp-section">
      <div class="cc-insp-label">📋 Clip ${TL_STATE.activeClipIdx + 1} of ${TL_STATE.clips.length}</div>
      <input class="cc-insp-title-input" data-field="title" value="${esc(clip.title)}" placeholder="Clip title…" />
    </div>
    <div class="cc-insp-section">
      <div class="cc-insp-label">⏱ Start Time</div>
      <div class="cc-bound-row">
        <button class="cc-bound-btn" data-act="cc_adj_bound" data-type="start" data-delta="-5">-5s</button>
        <button class="cc-bound-btn" data-act="cc_adj_bound" data-type="start" data-delta="-1">-1s</button>
        <span class="cc-timecode-pill">${fmtTimecode(clip.start)}</span>
        <button class="cc-bound-btn" data-act="cc_adj_bound" data-type="start" data-delta="1">+1s</button>
        <button class="cc-bound-btn" data-act="cc_adj_bound" data-type="start" data-delta="5">+5s</button>
      </div>
      <button class="cc-ph-set-btn" data-act="cc_set_bound_playhead" data-type="start">⏱ Set to Playhead</button>
    </div>
    <div class="cc-insp-section">
      <div class="cc-insp-label">⏱ End Time</div>
      <div class="cc-bound-row">
        <button class="cc-bound-btn" data-act="cc_adj_bound" data-type="end" data-delta="-5">-5s</button>
        <button class="cc-bound-btn" data-act="cc_adj_bound" data-type="end" data-delta="-1">-1s</button>
        <span class="cc-timecode-pill">${fmtTimecode(clip.end)}</span>
        <button class="cc-bound-btn" data-act="cc_adj_bound" data-type="end" data-delta="1">+1s</button>
        <button class="cc-bound-btn" data-act="cc_adj_bound" data-type="end" data-delta="5">+5s</button>
      </div>
      <button class="cc-ph-set-btn" data-act="cc_set_bound_playhead" data-type="end">⏱ Set to Playhead</button>
    </div>
    <div class="cc-insp-section">
      <div class="cc-insp-label">📊 Duration: <strong style="color:#00e5ff">${dur}s</strong>
        <span class="cc-viral-badge" style="background:${clip.virality_score>=85?'#ff4444':'#f97316'}">${clip.virality_score}% Viral</span>
      </div>
    </div>
    <div class="cc-insp-section" style="margin-top:auto;display:flex;gap:8px">
      <button class="cc-insp-add-btn" data-act="cc_add_clip">＋ Add Clip</button>
      <button class="cc-insp-del-btn" data-act="cc_del_clip">🗑 Remove</button>
    </div>`;
  }

  if (tab === "captions") {
    const ss = clip ? clip.subtitle_style : "hormozi";
    return `
    <div class="cc-insp-section">
      <div class="cc-insp-label">💬 Caption Style</div>
      ${["hormozi","mrbeast","cyber","clean"].map(s => `
        <label class="cc-style-chip ${ss===s?'active':''}">
          <input type="radio" name="subtitle_style" value="${s}" ${ss===s?'checked':''} data-field="subtitle_style" style="display:none">
          ${s.charAt(0).toUpperCase()+s.slice(1)}
        </label>`).join('')}
    </div>
    <div class="cc-insp-section">
      <div class="cc-insp-label">🔤 Word Case</div>
      <select class="cc-select" data-field="word_case">
        <option value="upper">UPPER CASE</option>
        <option value="title">Title Case</option>
        <option value="lower">lower case</option>
      </select>
    </div>
    <div class="cc-insp-section">
      <div class="cc-insp-label">😄 Inject Emojis</div>
      <label class="cc-toggle"><input type="checkbox" data-field="inject_emojis"> <span>Auto-add emojis</span></label>
    </div>
    <div class="cc-caption-preview">
      <span style="font-weight:900;font-size:20px;text-transform:uppercase;color:#fff;text-shadow:2px 2px 0 #000">CAPTION PREVIEW</span>
    </div>`;
  }

  if (tab === "hooks") {
    const hook = clip ? clip.hook : "";
    const hookStyle = clip ? (clip.hook_style || "yellow") : "yellow";
    return `
    <div class="cc-insp-section">
      <div class="cc-insp-label">🎯 Hook Banner Text</div>
      <textarea class="cc-textarea" data-field="hook" rows="3" placeholder="Enter hook text…">${esc(hook)}</textarea>
    </div>
    <div class="cc-insp-section">
      <div class="cc-insp-label">🎨 Banner Style</div>
      ${["yellow","red","cyan","minimal"].map(s => `
        <label class="cc-style-chip hook-style-${s} ${hookStyle===s?'active':''}">
          <input type="radio" name="hook_style" value="${s}" ${hookStyle===s?'checked':''} data-field="hook_style" style="display:none">
          ${s.charAt(0).toUpperCase()+s.slice(1)}
        </label>`).join('')}
    </div>
    <div class="cc-insp-section">
      <div class="cc-insp-label">🔤 Font Weight</div>
      <label class="cc-toggle"><input type="checkbox" data-field="hook_bold" ${clip&&clip.hook_bold?'checked':''}> <span>Bold text</span></label>
    </div>
    <div class="cc-hook-preview" style="background:${hookStyle==='yellow'?'#FFD700':hookStyle==='red'?'#ff4444':hookStyle==='cyan'?'#00e5ff':'rgba(0,0,0,0.6)'};color:${hookStyle==='yellow'||hookStyle==='cyan'?'#000':'#fff'};padding:8px;border-radius:6px;text-align:center;font-weight:900;font-size:14px;margin-top:8px">
      ${esc(hook || "HOOK BANNER PREVIEW")}
    </div>`;
  }

  if (tab === "framing") {
    const lm = clip ? clip.layout_mode : "speaker_focus";
    const tp = clip ? clip.top_padding : 0;
    const bp = clip ? clip.bottom_padding : 0;
    const cts = clip ? clip.canvas_top_space : 450;
    return `
    <div class="cc-insp-section">
      <div class="cc-insp-label">🎥 Layout Mode</div>
      <select class="cc-select" data-field="layout_mode">
        ${["speaker_focus","split_screen","full_frame","talking_head"].map(m =>
          `<option value="${m}" ${lm===m?'selected':''}>${m.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase())}</option>`).join('')}
      </select>
    </div>
    <div class="cc-insp-section">
      <div class="cc-insp-label">⬆ Top Padding: <span id="ccTopPadNum">${tp}</span>%</div>
      <input type="range" class="cc-slider" data-field="top_padding" min="0" max="40" step="1" value="${tp}">
    </div>
    <div class="cc-insp-section">
      <div class="cc-insp-label">⬇ Bottom Padding: <span id="ccBotPadNum">${bp}</span>%</div>
      <input type="range" class="cc-slider" data-field="bottom_padding" min="0" max="40" step="1" value="${bp}">
    </div>
    <div class="cc-insp-section">
      <div class="cc-insp-label">📐 Canvas Top Space: <span id="ccCtsNum">${cts}</span>px</div>
      <input type="range" class="cc-slider" data-field="canvas_top_space" min="200" max="700" step="10" value="${cts}">
    </div>`;
  }

  if (tab === "audio") {
    return `
    <div class="cc-insp-section">
      <div class="cc-insp-label">🔊 Volume</div>
      <input type="range" class="cc-slider" id="ccVolSlider" min="0" max="1" step="0.05" value="${TL_STATE.volume}">
    </div>
    <div class="cc-insp-section">
      <div class="cc-insp-label">🎙 Voice Clarifier</div>
      <label class="cc-toggle"><input type="checkbox" id="ccVoiceClarify"> <span>Enhance speech clarity</span></label>
    </div>
    <div class="cc-insp-section">
      <div class="cc-insp-label">🎵 Background Music</div>
      <label class="cc-toggle"><input type="checkbox" id="ccBgMusic"> <span>Add lo-fi background</span></label>
    </div>
    <div class="cc-insp-section">
      <div class="cc-insp-label">🔇 Mute Preview</div>
      <label class="cc-toggle"><input type="checkbox" id="ccMuteToggle" ${TL_STATE.isMuted?'checked':''}> <span>Mute video preview</span></label>
    </div>`;
  }

  if (tab === "covers") {
    return `
    <div class="cc-insp-section">
      <div class="cc-insp-label">🖼 Thumbnail Color</div>
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        ${["#ff4444","#ff9800","#4caf50","#2196f3","#9c27b0","#FFD700"].map(col =>
          `<div class="cc-color-swatch" style="background:${col}" data-act="cc_cover_color" data-color="${col}"></div>`).join('')}
      </div>
    </div>
    <div class="cc-insp-section">
      <div class="cc-insp-label">💧 Watermark Text</div>
      <input class="cc-insp-title-input" data-field="watermark" placeholder="@YourHandle" value="">
    </div>
    <div class="cc-insp-section">
      <div class="cc-insp-label">📸 Cover Frames (3 auto-generated per clip)</div>
      <div style="font-size:11px;color:#888">Applied after re-render</div>
    </div>`;
  }

  return "";
}

/* ---- Tracks HTML ---- */
function buildTracksHtml() {
  const dur = TL_STATE.duration;
  const zoom = TL_STATE.zoom;
  const pxPerSec = 60 * zoom;
  const totalW = Math.max(800, dur * pxPerSec + 60);

  // Ruler
  const tickStep = zoom < 0.5 ? 60 : zoom < 1 ? 30 : zoom < 2 ? 15 : 10;
  let rulerHtml = "";
  for (let t = 0; t <= dur; t += tickStep) {
    const x = t * pxPerSec;
    rulerHtml += `<div class="cc-ruler-tick" style="left:${x}px"><span>${fmtTimecode(t)}</span></div>`;
  }

  // Video clips
  let videoTrackHtml = "";
  TL_STATE.clips.forEach((c, i) => {
    const x = c.start * pxPerSec;
    const w = Math.max(2, (c.end - c.start) * pxPerSec);
    const isActive = i === TL_STATE.activeClipIdx;
    videoTrackHtml += `
      <div class="cc-video-clip ${isActive ? 'active' : ''}" data-act="cc_select_clip" data-idx="${i}"
           style="left:${x}px;width:${w}px" title="${esc(c.title)}">
        <div class="cc-clip-trim-handle left" data-act="cc_trim" data-idx="${i}" data-side="start"></div>
        <span class="cc-clip-label">${esc(c.title)}</span>
        <span class="cc-clip-dur">${(c.end - c.start).toFixed(1)}s</span>
        <div class="cc-clip-trim-handle right" data-act="cc_trim" data-idx="${i}" data-side="end"></div>
      </div>`;
  });

  // Caption track items
  let captionTrackHtml = "";
  TL_STATE.clips.forEach((c, i) => {
    const x = c.start * pxPerSec;
    const w = Math.max(2, (c.end - c.start) * pxPerSec);
    captionTrackHtml += `
      <div class="cc-caption-item" style="left:${x}px;width:${w}px" data-act="cc_select_clip" data-idx="${i}">
        <span class="cc-caption-label">${esc(c.subtitle_style || "hormozi")}</span>
      </div>`;
  });

  // Hook track items
  let hookTrackHtml = "";
  TL_STATE.clips.forEach((c, i) => {
    if (!c.hook) return;
    const x = c.start * pxPerSec;
    const w = Math.max(2, Math.min((c.end - c.start) * pxPerSec * 0.4, 120));
    hookTrackHtml += `
      <div class="cc-hook-item" style="left:${x}px;width:${w}px" data-act="cc_select_clip" data-idx="${i}">
        <span>${esc(c.hook.substring(0, 20))}</span>
      </div>`;
  });

  return { rulerHtml, videoTrackHtml, captionTrackHtml, hookTrackHtml, totalW, pxPerSec };
}

/* ---- Main render ---- */
function renderCapCutStudio() {
  const dlg = $("#timelinedlg");
  if (!dlg) return;

  const proj = TL_STATE.project || {};
  const clip = TL_STATE.clips[TL_STATE.activeClipIdx];
  const { rulerHtml, videoTrackHtml, captionTrackHtml, hookTrackHtml, totalW } = buildTracksHtml();
  const inspHtml = renderSubInspector(TL_STATE.activeTab);

  const tabs = [
    { id: "cuts",     icon: "✂️", label: "Cuts" },
    { id: "captions", icon: "💬", label: "Captions" },
    { id: "hooks",    icon: "🎯", label: "Hooks" },
    { id: "framing",  icon: "🎥", label: "Framing" },
    { id: "audio",    icon: "🔊", label: "Audio" },
    { id: "covers",   icon: "🖼️", label: "Covers" }
  ];

  dlg.innerHTML = `
  <div class="cc-studio-root">
    <!-- TOP BAR -->
    <div class="cc-topbar">
      <div class="cc-topbar-left">
        <span class="cc-logo-badge">🎬 CapForge</span>
        <input class="cc-project-title-input" id="ccProjectTitle" value="${esc(proj.title || 'Untitled Project')}" placeholder="Project title…">
        <span class="cc-dur-pill">${fmtTimecode(TL_STATE.duration)}</span>
        <span class="cc-save-status" id="ccSaveStatus">${TL_STATE.saveStatus}</span>
      </div>
      <div class="cc-topbar-tools">
        <button class="cc-tool-btn" data-act="cc_split" title="Split at playhead">✂️ Split</button>
        <button class="cc-tool-btn" data-act="cc_del_clip" title="Delete active clip">🗑 Delete</button>
        <button class="cc-tool-btn ${TL_STATE.isLooping ? 'active' : ''}" data-act="cc_loop" title="Loop">🔁 Loop</button>
        <button class="cc-tool-btn ${TL_STATE.showTikTokGuides ? 'active' : ''}" data-act="cc_tiktok_guides" title="TikTok Safe Zones">📐 Guides</button>
      </div>
      <div class="cc-topbar-right">
        <span class="cc-dur-pill">${TL_STATE.width}×${TL_STATE.height} · ${TL_STATE.fps} fps</span>
        <button class="cc-tool-btn" data-act="cc_save" title="Save project (Ctrl+S)">💾 Save</button>
        <button class="cc-apply-btn" data-act="cc_apply">🚀 Apply & Re-render</button>
        <button class="cc-close-btn" data-act="closetimeline">✕</button>
      </div>
    </div>

    <!-- MAIN WORKSPACE -->
    <div class="cc-main-workspace">

      <!-- LEFT NAV DOCK -->
      <div class="cc-nav-dock">
        ${tabs.map(t => `
          <button class="cc-dock-btn ${TL_STATE.activeTab === t.id ? 'active' : ''}"
                  data-act="cc_dock" data-tab="${t.id}" title="${t.label}">
            <span class="cc-dock-icon">${t.icon}</span>
            <span class="cc-dock-label">${t.label}</span>
          </button>`).join('')}
      </div>

      <!-- SUB-INSPECTOR -->
      <div class="cc-sub-inspector" id="ccInspector">
        ${inspHtml}
      </div>

      <!-- CENTER CANVAS (Phone Preview) -->
      <div class="cc-center-canvas">
        <div class="cc-preview-phone-frame">
          <video id="ccVideo"
            src="/api/projects/${TL_STATE.projectId}/source-video"
            preload="metadata"
            style="width:100%;height:100%;object-fit:cover;border-radius:inherit"
            playsinline></video>

          <!-- Hook Banner Overlay -->
          <div class="cc-overlay-banner" id="ccBannerOverlay" style="${clip && clip.hook ? '' : 'display:none'}">
            ${clip ? esc(clip.hook) : ''}
          </div>

          <!-- Subtitle Overlay -->
          <div class="cc-overlay-subtitle" id="ccSubtitleOverlay">
            <span class="cc-sub-word">SUBTITLE PREVIEW</span>
          </div>

          <!-- TikTok Guides -->
          <div class="cc-tiktok-guides" id="ccTikTokGuides" style="${TL_STATE.showTikTokGuides ? '' : 'display:none'}">
            <div class="cc-guide-line" style="top:8%"></div>
            <div class="cc-guide-line" style="top:14%"></div>
            <div class="cc-guide-line" style="bottom:20%"></div>
            <div class="cc-guide-label" style="top:8%">Safe zone top</div>
            <div class="cc-guide-label" style="bottom:20%">Comments area</div>
          </div>
        </div>

        <!-- Transport Bar -->
        <div class="cc-transport-bar">
          <button class="cc-transport-btn" data-act="cc_step" data-sec="-5" title="Back 5s">⏮</button>
          <button class="cc-transport-btn" data-act="cc_step" data-sec="-1" title="Back 1s">◀</button>
          <button class="cc-transport-btn cc-play-btn" id="ccPlayBtn" data-act="cc_playpause" title="Play/Pause">▶</button>
          <button class="cc-transport-btn" data-act="cc_step" data-sec="1" title="Fwd 1s">▶</button>
          <button class="cc-transport-btn" data-act="cc_step" data-sec="5" title="Fwd 5s">⏭</button>
          <span class="cc-timecode-display" id="ccTimecodeDisplay">0:00.0</span>
          <div class="cc-speed-group">
            ${[0.5, 1, 1.5, 2].map(r => `<button class="cc-speed-btn ${r===1?'active':''}" data-act="cc_speed" data-rate="${r}">${r}x</button>`).join('')}
          </div>
          <button class="cc-transport-btn ${TL_STATE.isMuted ? 'active' : ''}" data-act="cc_mute" title="Mute">🔇</button>
        </div>
      </div>
    </div>

    <!-- TIMELINE SECTION -->
    <div class="cc-timeline-section">
      <!-- Timeline Toolbar -->
      <div class="cc-tl-toolbar">
        <button class="cc-tl-tool-btn" data-act="cc_zoom" data-delta="-0.25" title="Zoom out">🔍−</button>
        <input type="range" id="ccZoomSlider" min="0.2" max="6" step="0.1" value="${TL_STATE.zoom}" style="width:80px;accent-color:#00e5ff">
        <button class="cc-tl-tool-btn" data-act="cc_zoom" data-delta="0.25" title="Zoom in">🔍+</button>
        <div class="cc-tl-sep"></div>
        <button class="cc-tl-tool-btn" data-act="cc_add_clip" title="Add Clip">＋ Clip</button>
        <button class="cc-tl-tool-btn" data-act="cc_split" title="Split at playhead">✂️ Split</button>
        <button class="cc-tl-tool-btn" data-act="cc_del_clip" title="Delete">🗑</button>
        <div class="cc-tl-sep"></div>
        <button class="cc-tl-tool-btn" data-act="cc_undo" title="Undo">↩</button>
        <button class="cc-tl-tool-btn" data-act="cc_redo" title="Redo">↪</button>
        <span style="margin-left:auto;font-size:11px;color:#888">${TL_STATE.clips.length} clip${TL_STATE.clips.length===1?'':'s'} · ${fmtTimecode(TL_STATE.duration)} source</span>
      </div>

      <!-- Tracks Layout -->
      <div class="cc-tracks-layout">
        <!-- Track Headers -->
        <div class="cc-track-headers">
          <div class="cc-track-header-cell" style="height:24px;border-bottom:1px solid #333">⏱ Ruler</div>
          <div class="cc-track-header-cell">🎬 Video</div>
          <div class="cc-track-header-cell">💬 Captions</div>
          <div class="cc-track-header-cell">🎯 Hooks</div>
        </div>

        <!-- Tracks Viewport -->
        <div class="cc-tracks-viewport" id="ccTracksViewport">
          <div class="cc-track-scroll-inner" style="width:${totalW}px">
            <!-- Ruler -->
            <div class="cc-ruler-track" style="width:${totalW}px">
              ${rulerHtml}
            </div>
            <!-- Video Track Lane -->
            <div class="cc-track-lane" id="ccVideoTrack" style="width:${totalW}px">
              ${videoTrackHtml}
            </div>
            <!-- Caption Track Lane -->
            <div class="cc-track-lane cc-caption-lane" style="width:${totalW}px">
              ${captionTrackHtml}
            </div>
            <!-- Hook Track Lane -->
            <div class="cc-track-lane cc-hook-lane" style="width:${totalW}px">
              ${hookTrackHtml}
            </div>
            <!-- Playhead -->
            <div class="cc-playhead-line" id="ccPlayhead" style="left:0px">
              <div class="cc-playhead-head" id="ccPlayheadHead">▼</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Status Bar -->
      <div class="cc-status-bar">
        <span>🎬 ${TL_STATE.clips.length} clips</span>
        <span>⏱ ${fmtTimecode(TL_STATE.duration)} source</span>
        <span style="color:#4caf50">⚡ GPU NVENC Active</span>
        <span style="margin-left:auto;color:#00e5ff">CapForge Studio v2.0</span>
      </div>
    </div>

    <!-- Loading Overlay -->
    <div class="cc-loading-overlay" id="ccLoadingOverlay" style="display:none">
      <div class="cc-spinner"></div>
      <div style="color:#fff;margin-top:16px;font-size:16px">Re-rendering clips with GPU…</div>
      <div style="color:#888;font-size:12px;margin-top:4px">This may take a minute. Please wait.</div>
    </div>
  </div>`;

  attachCapCutEvents();
}

/* ---- Event attachment ---- */
function attachCapCutEvents() {
  /* Video timeupdate → playhead + timecode */
  const vid = document.getElementById("ccVideo");
  if (vid) {
    vid.volume = TL_STATE.volume;
    vid.muted = TL_STATE.isMuted;
    vid.loop = TL_STATE.isLooping;

    vid.addEventListener("timeupdate", () => {
      const t = vid.currentTime;
      const pxPerSec = 60 * TL_STATE.zoom;
      const ph = document.getElementById("ccPlayhead");
      if (ph) ph.style.left = (t * pxPerSec) + "px";
      const tc = document.getElementById("ccTimecodeDisplay");
      if (tc) tc.textContent = fmtTimecode(t);
    });

    vid.addEventListener("play", () => {
      TL_STATE.isPlaying = true;
      const btn = document.getElementById("ccPlayBtn");
      if (btn) btn.textContent = "⏸";
    });
    vid.addEventListener("pause", () => {
      TL_STATE.isPlaying = false;
      const btn = document.getElementById("ccPlayBtn");
      if (btn) btn.textContent = "▶";
    });
    vid.addEventListener("ended", () => {
      if (!TL_STATE.isLooping) vid.currentTime = 0;
    });
  }

  /* Zoom slider */
  const zoomSlider = document.getElementById("ccZoomSlider");
  if (zoomSlider) {
    zoomSlider.addEventListener("input", () => {
      TL_STATE.zoom = parseFloat(zoomSlider.value);
      ccRefreshTracks();
    });
  }

  /* Tracks viewport click → seek */
  const viewport = document.getElementById("ccTracksViewport");
  if (viewport) {
    viewport.addEventListener("click", (e) => {
      if (e.target.closest("[data-act]")) return;
      const rect = viewport.getBoundingClientRect();
      const scrollLeft = viewport.scrollLeft;
      const relX = e.clientX - rect.left + scrollLeft;
      const pxPerSec = 60 * TL_STATE.zoom;
      const seekTime = Math.max(0, Math.min(TL_STATE.duration, relX / pxPerSec));
      const v = document.getElementById("ccVideo");
      if (v) v.currentTime = seekTime;
    });

    /* Trim handle drag */
    viewport.addEventListener("pointerdown", (e) => {
      const handle = e.target.closest(".cc-clip-trim-handle");
      if (handle) {
        e.preventDefault();
        const idx = parseInt(handle.closest("[data-idx]").dataset.idx);
        const side = handle.dataset.side;
        ccSaveUndo();
        TL_STATE.dragTarget = { type: "trim", idx, side };
      } else {
        const clipEl = e.target.closest(".cc-video-clip");
        if (!clipEl) return;
        e.preventDefault();
        const idx = parseInt(clipEl.dataset.idx);
        const clip = TL_STATE.clips[idx];
        if (!clip) return;
        ccSaveUndo();
        TL_STATE.dragTarget = { type: "move", idx, originStart: clip.start, originEnd: clip.end, grabX: e.clientX };
        ccSelectClip(idx);
      }
      viewport.setPointerCapture(e.pointerId);
    });

    viewport.addEventListener("pointermove", (e) => {
      if (!TL_STATE.dragTarget) return;
      const rect = viewport.getBoundingClientRect();
      const scrollLeft = viewport.scrollLeft;
      const relX = e.clientX - rect.left + scrollLeft;
      const pxPerSec = 60 * TL_STATE.zoom;
      const t = Math.max(0, Math.min(TL_STATE.duration, relX / pxPerSec));
      const { type, idx, side } = TL_STATE.dragTarget;
      if (type === "trim") {
        const c = TL_STATE.clips[idx];
        if (!c) return;
        if (side === "start") {
          c.start = framesToSec(secToFrames(Math.min(t, c.end - 3)));
        } else {
          c.end = framesToSec(secToFrames(Math.max(t, c.start + 3)));
        }
        ccRefreshTracks();
      } else if (type === "move") {
        const c = TL_STATE.clips[idx];
        if (!c) return;
        const deltaSec = (e.clientX - TL_STATE.dragTarget.grabX) / (60 * TL_STATE.zoom);
        const duration = TL_STATE.dragTarget.originEnd - TL_STATE.dragTarget.originStart;
        const newStart = framesToSec(secToFrames(Math.max(0, Math.min(TL_STATE.duration - duration, TL_STATE.dragTarget.originStart + deltaSec))));
        c.start = newStart;
        c.end = newStart + duration;
        ccRefreshTracks();
      }
    });

    viewport.addEventListener("pointerup", () => {
      if (TL_STATE.dragTarget) {
        TL_STATE.dragTarget = null;
        ccRefreshInspector();
      }
    });
  }

  /* Inspector live inputs */
  const inspector = document.getElementById("ccInspector");
  if (inspector) {
    inspector.addEventListener("input", (e) => {
      const field = e.target.dataset.field;
      if (!field) return;
      const clip = TL_STATE.clips[TL_STATE.activeClipIdx];
      if (!clip) return;
      const val = e.target.type === "checkbox" ? e.target.checked : (e.target.type === "range" ? parseFloat(e.target.value) : e.target.value);
      clip[field] = val;
      ccMarkDirty();

      /* Live number display for sliders */
      if (field === "top_padding") {
        const el = document.getElementById("ccTopPadNum");
        if (el) el.textContent = val;
      }
      if (field === "bottom_padding") {
        const el = document.getElementById("ccBotPadNum");
        if (el) el.textContent = val;
      }
      if (field === "canvas_top_space") {
        const el = document.getElementById("ccCtsNum");
        if (el) el.textContent = val;
      }

      /* Live banner update */
      if (field === "hook") {
        const banner = document.getElementById("ccBannerOverlay");
        if (banner) {
          banner.style.display = val ? "" : "none";
          banner.textContent = val;
        }
      }
    });

    inspector.addEventListener("change", (e) => {
      const field = e.target.dataset.field;
      if (!field) return;
      const clip = TL_STATE.clips[TL_STATE.activeClipIdx];
      if (!clip) return;
      const val = e.target.type === "checkbox" ? e.target.checked : e.target.value;
      clip[field] = val;
      /* Refresh style chips */
      if (field === "subtitle_style" || field === "hook_style") {
        ccRefreshInspector();
      }
    });

    /* Volume slider live */
    inspector.addEventListener("input", (e) => {
      if (e.target.id === "ccVolSlider") {
        TL_STATE.volume = parseFloat(e.target.value);
        const v = document.getElementById("ccVideo");
        if (v) v.volume = TL_STATE.volume;
      }
      if (e.target.id === "ccMuteToggle") {
        TL_STATE.isMuted = e.target.checked;
        const v = document.getElementById("ccVideo");
        if (v) v.muted = TL_STATE.isMuted;
      }
    });
  }

  /* Playhead drag */
  const phHead = document.getElementById("ccPlayheadHead");
  if (phHead && viewport) {
    phHead.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      TL_STATE.dragTarget = { type: "playhead" };
      viewport.setPointerCapture(e.pointerId);
    });
  }
}

/* ---- Partial refresh helpers ---- */
function ccRefreshTracks() {
  const { rulerHtml, videoTrackHtml, captionTrackHtml, hookTrackHtml, totalW } = buildTracksHtml();
  const ruler = document.querySelector(".cc-ruler-track");
  const videoTrack = document.getElementById("ccVideoTrack");
  const captionTrack = document.querySelector(".cc-caption-lane");
  const hookTrack = document.querySelector(".cc-hook-lane");
  const scrollInner = document.querySelector(".cc-track-scroll-inner");

  if (scrollInner) scrollInner.style.width = totalW + "px";
  if (ruler) { ruler.innerHTML = rulerHtml; ruler.style.width = totalW + "px"; }
  if (videoTrack) { videoTrack.innerHTML = videoTrackHtml; videoTrack.style.width = totalW + "px"; }
  if (captionTrack) { captionTrack.innerHTML = captionTrackHtml; captionTrack.style.width = totalW + "px"; }
  if (hookTrack) { hookTrack.innerHTML = hookTrackHtml; hookTrack.style.width = totalW + "px"; }

  /* Update playhead position */
  const v = document.getElementById("ccVideo");
  if (v) {
    const pxPerSec = 60 * TL_STATE.zoom;
    const ph = document.getElementById("ccPlayhead");
    if (ph) ph.style.left = (v.currentTime * pxPerSec) + "px";
  }
}

function ccRefreshInspector() {
  const insp = document.getElementById("ccInspector");
  if (insp) {
    insp.innerHTML = renderSubInspector(TL_STATE.activeTab);
    /* Re-attach inspector events by calling attachCapCutEvents which is idempotent for inspector */
    const inspector = document.getElementById("ccInspector");
    if (inspector) {
      inspector.addEventListener("input", (e) => {
        const field = e.target.dataset.field;
        if (!field) return;
        const clip = TL_STATE.clips[TL_STATE.activeClipIdx];
        if (!clip) return;
        const val = e.target.type === "checkbox" ? e.target.checked : (e.target.type === "range" ? parseFloat(e.target.value) : e.target.value);
        clip[field] = val;
        if (field === "top_padding") { const el = document.getElementById("ccTopPadNum"); if (el) el.textContent = val; }
        if (field === "bottom_padding") { const el = document.getElementById("ccBotPadNum"); if (el) el.textContent = val; }
        if (field === "canvas_top_space") { const el = document.getElementById("ccCtsNum"); if (el) el.textContent = val; }
        if (field === "hook") { const b = document.getElementById("ccBannerOverlay"); if (b) { b.style.display = val ? "" : "none"; b.textContent = val; } }
      });
      inspector.addEventListener("change", (e) => {
        const field = e.target.dataset.field;
        if (!field) return;
        const clip = TL_STATE.clips[TL_STATE.activeClipIdx];
        if (!clip) return;
        clip[field] = e.target.type === "checkbox" ? e.target.checked : e.target.value;
        ccMarkDirty();
        if (field === "subtitle_style" || field === "hook_style") ccRefreshInspector();
      });
    }
  }
}

function ccSelectClip(idx) {
  if (idx < 0 || idx >= TL_STATE.clips.length) return;
  TL_STATE.activeClipIdx = idx;
  const clip = TL_STATE.clips[idx];
  const v = document.getElementById("ccVideo");
  if (v && clip) v.currentTime = clip.start;
  /* Update banner */
  const banner = document.getElementById("ccBannerOverlay");
  if (banner && clip) {
    banner.style.display = clip.hook ? "" : "none";
    banner.textContent = clip.hook || "";
  }
  ccRefreshTracks();
  ccRefreshInspector();
}

function ccSplitAtPlayhead() {
  const v = document.getElementById("ccVideo");
  if (!v) return;
  const t = v.currentTime;
  const clip = TL_STATE.clips[TL_STATE.activeClipIdx];
  if (!clip) return;
  if (t <= clip.start + 2 || t >= clip.end - 2) {
    toast("Playhead must be at least 2s inside the clip to split", "bad");
    return;
  }
  ccSaveUndo();
  t = framesToSec(secToFrames(t));
  const newClip = {
    ...clip,
    id: `clip_${Date.now()}`,
    start: t,
    end: clip.end,
    title: clip.title + " (B)"
  };
  clip.end = t;
  TL_STATE.clips.splice(TL_STATE.activeClipIdx + 1, 0, newClip);
  toast("Clip split at " + fmtTimecode(t), "ok");
  ccRefreshTracks();
  ccRefreshInspector();
}

function ccDeleteActiveClip() {
  if (TL_STATE.clips.length <= 1) {
    toast("Cannot delete the only clip", "bad");
    return;
  }
  ccSaveUndo();
  TL_STATE.clips.splice(TL_STATE.activeClipIdx, 1);
  TL_STATE.activeClipIdx = Math.min(TL_STATE.activeClipIdx, TL_STATE.clips.length - 1);
  toast("Clip removed", "ok");
  ccRefreshTracks();
  ccRefreshInspector();
}

function ccAddClipAtPlayhead() {
  const v = document.getElementById("ccVideo");
  const t = v ? v.currentTime : 0;
  ccSaveUndo();
  const newStart = Math.max(0, t);
  const newEnd = Math.min(TL_STATE.duration, newStart + 45);
  TL_STATE.clips.push({
    id: `clip_${Date.now()}`,
    start: newStart,
    end: newEnd,
    title: `Clip ${TL_STATE.clips.length + 1}`,
    hook: "",
    subtitle_style: "hormozi",
    layout_mode: "speaker_focus",
    top_padding: 0,
    bottom_padding: 0,
    canvas_top_space: 450,
    virality_score: 85
  });
  TL_STATE.activeClipIdx = TL_STATE.clips.length - 1;
  toast("New clip added", "ok");
  ccRefreshTracks();
  ccRefreshInspector();
}

function ccAdjBound(type, delta) {
  const clip = TL_STATE.clips[TL_STATE.activeClipIdx];
  if (!clip) return;
  ccSaveUndo();
  const d = Number(delta);
  if (type === "start") {
    clip.start = Math.max(0, Math.min(clip.end - 3, clip.start + d));
  } else {
    clip.end = Math.max(clip.start + 3, Math.min(TL_STATE.duration, clip.end + d));
  }
  ccRefreshTracks();
  ccRefreshInspector();
}

function ccSetBoundToPlayhead(type) {
  const clip = TL_STATE.clips[TL_STATE.activeClipIdx];
  const v = document.getElementById("ccVideo");
  if (!clip || !v) return;
  ccSaveUndo();
  const t = v.currentTime;
  if (type === "start") {
    clip.start = Math.max(0, Math.min(clip.end - 3, t));
  } else {
    clip.end = Math.max(clip.start + 3, Math.min(TL_STATE.duration, t));
  }
  toast(`Clip ${type} set to ${fmtTimecode(t)}`, "ok");
  ccRefreshTracks();
  ccRefreshInspector();
}

async function applyCapCutEdits() {
  if (!TL_STATE.clips || TL_STATE.clips.length === 0) {
    toast("Please add at least 1 clip before applying", "bad");
    return;
  }
  for (let i = 0; i < TL_STATE.clips.length; i++) {
    const c = TL_STATE.clips[i];
    if (c.end <= c.start || (c.end - c.start) < 3.0) {
      toast(`Clip ${i + 1} duration must be at least 3 seconds`, "bad");
      ccSelectClip(i);
      return;
    }
  }

  const overlay = document.getElementById("ccLoadingOverlay");
  if (overlay) overlay.style.display = "flex";

  try {
    toast("Re-rendering clips with AI Safe Framing & Kinetic Subtitles…", "loading", "Studio");
    const res = await api(`/api/projects/${TL_STATE.projectId}/apply-timeline-edits`, {
      method: "POST",
      body: JSON.stringify({
        clips: TL_STATE.clips,
        editor_project: buildEditorProject()
      })
    });

    if (res && res.status === "success") {
      toast("✨ All timeline clips re-rendered successfully!", "ok", "Studio Complete");
      await tick();
      const dlg = $("#timelinedlg");
      if (dlg) dlg.close();
      const v = document.getElementById("ccVideo");
      if (v) v.pause();
      render();
    } else {
      throw new Error(res?.detail || "Failed to apply timeline edits");
    }
  } catch (err) {
    console.error("Apply CapCut Edits Error:", err);
    toast("Rendering error: " + (err.message || err), "bad");
    if (overlay) overlay.style.display = "none";
  }
}

/* ---- Undo/Redo ---- */
function ccUndo() {
  if (!TL_STATE._undoStack.length) { toast("Nothing to undo", "bad"); return; }
  TL_STATE._redoStack.push(JSON.stringify(TL_STATE.clips));
  TL_STATE.clips = JSON.parse(TL_STATE._undoStack.pop());
  TL_STATE.activeClipIdx = Math.min(TL_STATE.activeClipIdx, TL_STATE.clips.length - 1);
  ccRefreshTracks();
  ccRefreshInspector();
  toast("Undo", "ok");
}

function ccRedo() {
  if (!TL_STATE._redoStack.length) { toast("Nothing to redo", "bad"); return; }
  TL_STATE._undoStack.push(JSON.stringify(TL_STATE.clips));
  TL_STATE.clips = JSON.parse(TL_STATE._redoStack.pop());
  TL_STATE.activeClipIdx = Math.min(TL_STATE.activeClipIdx, TL_STATE.clips.length - 1);
  ccRefreshTracks();
  ccRefreshInspector();
  toast("Redo", "ok");
}

document.addEventListener("input", (e) => {
  if (e.target?.id === "ccProjectTitle") ccMarkDirty();
});

document.addEventListener("keydown", (e) => {
  const dlg = document.getElementById("timelinedlg");
  if (!dlg || !dlg.open) return;
  const tag = e.target?.tagName?.toLowerCase();
  const isTyping = tag === "input" || tag === "textarea" || e.target?.isContentEditable;
  if (isTyping) {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") {
      e.preventDefault();
      ccSaveEditorProject(true);
    }
    return;
  }

  if (e.code === "Space") {
    e.preventDefault();
    document.querySelector("[data-act='cc_playpause']")?.click();
  } else if (e.key.toLowerCase() === "s" && !e.ctrlKey && !e.metaKey) {
    e.preventDefault();
    ccSplitAtPlayhead();
  } else if (e.key === "Delete" || e.key === "Backspace") {
    e.preventDefault();
    ccDeleteActiveClip();
  } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") {
    e.preventDefault();
    e.shiftKey ? ccRedo() : ccUndo();
  } else if ((e.ctrlKey || e.metaKey) && e.key.toLower() === "y") {
    e.preventDefault();
    ccRedo();
  } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") {
    e.preventDefault();
    ccSaveEditorProject(true);
  } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "c") {
    const clip = TL_STATE.clips[TL_STATE.activeClipIdx];
    if (clip) TL_STATE.clipboard = JSON.parse(JSON.stringify(clip));
  } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "v" && TL_STATE.clipboard) {
    e.preventDefault();
    ccSaveUndo();
    const copy = JSON.parse(JSON.stringify(TL_STATE.clipboard));
    copy.id = `clip_${Date.now()}`;
    copy.start = Math.min(TL_STATE.duration - 3, copy.start + (copy.end - copy.start));
    copy.end = Math.min(TL_STATE.duration, copy.start + (TL_STATE.clipboard.end - TL_STATE.clipboard.start));
    TL_STATE.clips.push(copy);
    TL_STATE.activeClipIdx = TL_STATE.clips.length - 1;
    ccRefreshTracks();
    ccRefreshInspector();
  } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "d") {
    e.preventDefault();
    const clip = TL_STATE.clips[TL_STATE.activeClipIdx];
    if (clip) {
      ccSaveUndo();
      const copy = JSON.parse(JSON.stringify(clip));
      copy.id = `clip_${Date.now()}`;
      copy.start = Math.min(TL_STATE.duration - 3, copy.start + (copy.end - copy.start));
      copy.end = Math.min(TL_STATE.duration, copy.start + (clip.end - clip.start));
      TL_STATE.clips.push(copy);
      TL_STATE.activeClipIdx = TL_STATE.clips.length - 1;
      ccRefreshTracks();
      ccRefreshInspector();
    }
  } else if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
    const v = document.getElementById("ccVideo");
    if (!v) return;
    e.preventDefault();
    const delta = e.shiftKey ? 5 : 1 / TL_STATE.fps;
    v.currentTime = Math.max(0, Math.min(TL_STATE.duration, v.currentTime + (e.key === "ArrowRight" ? delta : -delta)));
  }
});

/* ============================================================ Event Handlers */
document.addEventListener("click", async e => {
  const b = e.target.closest("[data-act]");
  if (!b) return;
  const a = b.dataset.act, d = b.dataset;

  if (a === "go") { go(d.v, d.tab); return; }
  if (a === "bell") { toast("ClipForge Studio active. GPU NVENC engine and offline Ollama AI operational.", "ok", "System Status"); return; }
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
  if (a === "openeditor") { openTimelineEditor(d.j); return; }
  if (a === "closetimeline") {
    const dlg = $("#timelinedlg");
    if (dlg) dlg.close();
    const v = document.getElementById("ccVideo");
    if (v) v.pause();
    return;
  }
  if (a === "cc_playpause") {
    const v = document.getElementById("ccVideo");
    if (v) { if (v.paused) v.play(); else v.pause(); }
    return;
  }
  if (a === "cc_step") {
    const v = document.getElementById("ccVideo");
    if (v) v.currentTime = Math.max(0, Math.min(TL_STATE.duration, (v.currentTime || 0) + Number(d.sec || 0)));
    return;
  }
  if (a === "cc_speed") {
    const rate = Number(d.rate || 1);
    const v = document.getElementById("ccVideo");
    if (v) v.playbackRate = rate;
    document.querySelectorAll("[data-act='cc_speed']").forEach(btn => {
      btn.classList.toggle("active", Number(btn.dataset.rate) === rate);
    });
    return;
  }
  if (a === "cc_loop") {
    TL_STATE.isLooping = !TL_STATE.isLooping;
    const v = document.getElementById("ccVideo");
    if (v) v.loop = TL_STATE.isLooping;
    b.classList.toggle("active", TL_STATE.isLooping);
    return;
  }
  if (a === "cc_mute") {
    TL_STATE.isMuted = !TL_STATE.isMuted;
    const v = document.getElementById("ccVideo");
    if (v) v.muted = TL_STATE.isMuted;
    b.classList.toggle("active", TL_STATE.isMuted);
    return;
  }
  if (a === "cc_tiktok_guides") {
    TL_STATE.showTikTokGuides = !TL_STATE.showTikTokGuides;
    const guides = document.getElementById("ccTikTokGuides");
    if (guides) guides.style.display = TL_STATE.showTikTokGuides ? "" : "none";
    b.classList.toggle("active", TL_STATE.showTikTokGuides);
    return;
  }
  if (a === "cc_zoom") {
    TL_STATE.zoom = Math.max(0.2, Math.min(8.0, TL_STATE.zoom + Number(d.delta || 0)));
    const slider = document.getElementById("ccZoomSlider");
    if (slider) slider.value = TL_STATE.zoom;
    ccRefreshTracks();
    return;
  }
  if (a === "cc_dock") {
    TL_STATE.activeTab = d.tab;
    document.querySelectorAll(".cc-dock-btn").forEach(btn => btn.classList.toggle("active", btn.dataset.tab === d.tab));
    ccRefreshInspector();
    return;
  }
  if (a === "cc_select_clip") {
    ccSelectClip(Number(d.idx));
    return;
  }
  if (a === "cc_del_clip") {
    e.stopPropagation();
    ccDeleteActiveClip();
    return;
  }
  if (a === "cc_add_clip") {
    ccAddClipAtPlayhead();
    return;
  }
  if (a === "cc_split") {
    ccSplitAtPlayhead();
    return;
  }
  if (a === "cc_set_bound_playhead") {
    ccSetBoundToPlayhead(d.type);
    return;
  }
  if (a === "cc_adj_bound") {
    ccAdjBound(d.type, d.delta);
    return;
  }
  if (a === "cc_apply") {
    applyCapCutEdits();
    return;
  }
  if (a === "cc_save") {
    ccSaveEditorProject(true);
    return;
  }
  if (a === "cc_undo") {
    ccUndo();
    return;
  }
  if (a === "cc_redo") {
    ccRedo();
    return;
  }
  if (a === "cc_cover_color") {
    const clip = TL_STATE.clips[TL_STATE.activeClipIdx];
    if (clip) { clip.cover_color = d.color; toast("Cover color set", "ok"); }
    return;
  }
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
    setStageLoading(true, "Sampling FFmpeg Layout Frame...", "Exact 1080x1920 Snapshot");
    try {
      toast("Rendering exact 1080x1920 layout preview frame for this clip...", "loading", "Rendering Preview");
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
      toast("Exact layout snapshot rendered!", "ok", "Snapshot Ready");
    } catch (err) {
      toast("Could not render frame: " + err.message, "bad", "Preview Error");
    } finally {
      b.disabled = false;
      setStageLoading(false);
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
  if (a === "switchcardthumb") {
    const card = b.closest(".clip");
    if (card) {
      const img = card.querySelector(".shot img");
      if (img && d.src) {
        img.src = d.src;
      }
      card.querySelectorAll(".thumb-pill-btn").forEach(btn => {
        btn.classList.toggle("active", btn === b);
      });
      const dlLink = card.querySelector(".card-thumb-dl");
      if (dlLink && d.src) {
        dlLink.href = d.src;
        if (d.cov) dlLink.download = d.cov.split('/').pop();
      }
    }
    return;
  }
  if (a === "setdefaultcover") {
    const cid = d.c || D.cid;
    const cov = d.cov;
    const src = d.src;
    if (!cid || !cov) return;
    b.disabled = true;
    try {
      toast("Updating active TikTok cover...", "loading", "Cover Studio");
      const res = await send(`/api/clips/${cid}/set-cover`, { cover: cov });
      if (res && res.status === "success") {
        toast("✨ Active cover thumbnail set!", "ok", "Cover Updated");
        for (const job of S.jobs) {
          const cl = (job.clips || []).find(x => x.id === cid);
          if (cl) {
            cl.cover = cov;
          }
        }
        const stageImg = $("#editorThumbImg");
        if (stageImg && src) stageImg.src = src;
        const thumbBtn = $("#ed_thumb_btn");
        if (thumbBtn && src) {
          thumbBtn.href = src;
          thumbBtn.download = cov.split('/').pop();
        }
        const cardImg = document.querySelector(`button[data-c="${cid}"] img`);
        if (cardImg && src) cardImg.src = src;
        const card = cardImg?.closest(".clip");
        if (card) {
          card.querySelectorAll(".thumb-pill-btn").forEach(btn => {
            btn.classList.toggle("active", btn.dataset.cov === cov);
          });
          const dlLink = card.querySelector(".card-thumb-dl");
          if (dlLink && src) {
            dlLink.href = src;
            dlLink.download = cov.split('/').pop();
          }
        }
        const pane = $("#pane_modaltab_cover");
        if (pane) {
          pane.querySelectorAll(".cover-card-box").forEach(box => {
            const btn = box.querySelector('[data-act="setdefaultcover"]');
            const isActive = btn && btn.dataset.cov === cov;
            box.classList.toggle("is-active-cover", isActive);
            let pill = box.querySelector(".active-cover-pill");
            if (isActive) {
              if (!pill) {
                pill = document.createElement("span");
                pill.className = "active-cover-pill";
                pill.textContent = "✓ ACTIVE";
                box.querySelector(".cover-card-preview")?.appendChild(pill);
              }
            } else if (pill) {
              pill.remove();
            }
            if (btn) {
              btn.className = `btn sm ${isActive ? 'ghost disabled' : 'primary-soft'}`;
              btn.textContent = isActive ? '✓ Active' : 'Set Active';
            }
          });
        }
      }
    } catch (err) {
      toast("Error setting cover: " + (err.message || err), "bad", "Cover Studio");
    } finally {
      b.disabled = false;
    }
    return;
  }
  if (a === "dlall") {
    const ids = (S.jobs.find(x => x.id === d.j)?.clips || []).map(c => d.j + "." + c.id);
    window.location.href = "/api/clips.zip?ids=" + encodeURIComponent(ids.join(","));
    toast("Preparing ZIP archive with clips & docs file...", "ok");
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
      if (p[0] === "c") {
        clipIds.push(`${p[1]}.${p[2]}`);
      } else if (p[0] === "j") {
        const job = S.jobs.find(x => x.id === p[1]);
        if (job && job.clips) {
          job.clips.forEach(c => clipIds.push(`${job.id}.${c.id}`));
        }
      }
    }
    if (!clipIds.length) { toast("No clips selected", "bad"); return; }
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
  if (a === "opengdrivetab") {
    go("settings", "gdrive");
    drawSettings();
    return;
  }
  if (a === "connectgdrive") {
    const cid = $("#gd_client_id")?.value?.trim() || "";
    const sec = $("#gd_client_secret")?.value?.trim() || "";
    const folder = $("#gd_folder")?.value?.trim() || "ClipForge Clips";
    b.disabled = true;
    try {
      toast("Saving Google Drive settings...", "ok");
      const cfgRes = await send("/api/gdrive/configure", {
        client_id: cid,
        client_secret: sec,
        folder_name: folder
      });
      if (cfgRes?.auth_url) {
        toast("Opening Google authentication...", "ok");
        window.open(cfgRes.auth_url, "gdrive_auth", "width=560,height=680");
        const pollTimer = setInterval(async () => {
          try {
            const st = await api("/api/gdrive/status");
            if (st && st.connected) {
              clearInterval(pollTimer);
              S.gdrive = st;
              toast("⚡ Google Drive connected successfully! Ready to sync clips to your phone.", "ok");
              drawSettings();
              rTopBar();
            }
          } catch {}
        }, 1800);
        setTimeout(() => clearInterval(pollTimer), 120000);
      } else {
        toast("Please provide both Google OAuth Client ID and Secret to connect.", "bad");
      }
    } catch (err) {
      toast(err.message, "bad");
    } finally {
      b.disabled = false;
    }
    return;
  }
  if (a === "disconnectgdrive") {
    if (!await ask("Disconnect Google Drive?", "Cloud syncing will be paused until you reconnect.", "Disconnect", true)) return;
    b.disabled = true;
    try {
      await api("/api/gdrive/disconnect", { method: "POST" });
      S.gdrive = { connected: false, email: "", folder_name: "ClipForge Clips", has_credentials: false };
      toast("Google Drive disconnected.", "ok");
      drawSettings();
      rTopBar();
    } catch (err) {
      toast(err.message, "bad");
    } finally {
      b.disabled = false;
    }
    return;
  }
  if (a === "uploadgdrive") {
    b.disabled = true;
    try {
      const st = await api("/api/gdrive/status");
      S.gdrive = st || S.gdrive;
      if (!st || !st.connected) {
        if (await ask("Connect Google Drive", "Google Drive is not connected yet. Connect it now to upload clips directly to your phone for TikTok?", "Connect Drive")) {
          go("settings", "gdrive");
          drawSettings();
        }
        return;
      }
      toast(`Uploading clip to Google Drive (${st.folder_name || "ClipForge Clips"})...`, "ok");
      const res = await send("/api/gdrive/upload", { cid: d.c, jid: d.j, clip_id: d.c });
      if (res && res.status === "success" && res.results?.[0]) {
        const item = res.results[0];
        toast(`✅ Uploaded "${item.title}" to Google Drive (${res.folder_name})! Ready on your phone for TikTok.`, "ok");
      } else {
        throw new Error(res?.results?.[0]?.error || "Upload failed. Check server logs.");
      }
    } catch (err) {
      toast("Drive upload: " + err.message, "bad");
    } finally {
      b.disabled = false;
    }
    return;
  }
  if (a === "selgdrive") {
    b.disabled = true;
    try {
      const st = await api("/api/gdrive/status");
      S.gdrive = st || S.gdrive;
      if (!st || !st.connected) {
        if (await ask("Connect Google Drive", "Connect Google Drive to upload your selected clips to your mobile phone for TikTok.", "Connect Drive")) {
          go("settings", "gdrive");
          drawSettings();
        }
        return;
      }
      const clipIds = [];
      for (const key of S.sel) {
        const p = key.split(":");
        if (p[0] === "c") clipIds.push(p[2]);
        else if (p[0] === "j") {
          const j = S.jobs.find(x => x.id === p[1]);
          if (j && j.clips) clipIds.push(...j.clips.map(c => c.id));
        }
      }
      if (!clipIds.length) {
        toast("No clips selected to upload.", "bad");
        return;
      }
      toast(`Uploading ${clipIds.length} clips to Google Drive (${st.folder_name})...`, "ok");
      const res = await send("/api/gdrive/upload", { clip_ids: clipIds });
      if (res && res.uploaded_count > 0) {
        toast(`✅ Uploaded ${res.uploaded_count} clips to Google Drive (${res.folder_name})! Ready on your phone for TikTok.`, "ok");
      } else {
        throw new Error(res?.results?.[0]?.error || "Upload failed for selected clips.");
      }
    } catch (err) {
      toast("Drive batch upload: " + err.message, "bad");
    } finally {
      b.disabled = false;
    }
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
  if (a === "setdurpreset") {
    const minVal = Number(d.min);
    const maxVal = Number(d.max);
    if ($("#o_min")) $("#o_min").value = minVal;
    if ($("#o_maxlen")) $("#o_maxlen").value = maxVal;
    document.querySelectorAll(".dur-preset-btn").forEach(btn => {
      const isThis = Number(btn.getAttribute("data-min")) === minVal && Number(btn.getAttribute("data-max")) === maxVal;
      btn.classList.toggle("on", isThis);
      btn.style.background = isThis ? "rgba(255,139,51,0.14)" : "";
      btn.style.borderColor = isThis ? "var(--brand)" : "";
      btn.style.color = isThis ? "var(--brand)" : "";
      btn.style.fontWeight = isThis ? "800" : "500";
    });
    toast(`Duration set: ${minVal}s to ${maxVal}s (AI prioritizes complete thoughts in 60–90s sweet spot)`, "ok");
    return;
  }
  if (a === "switchstagemode") {
    const mode = d.mode;
    const v = $("#editorVideo");
    const ts = $("#thumbStudioStage");
    const tc = $("#thumbStudioControls");
    const vc = $("#videoControlsSection");
    const bV = $("#btn_stage_video");
    const bT = $("#btn_stage_thumb");
    const safeZone = $("#editorSafeZone");
    const padTop = $("#previewPadTop");
    const padBot = $("#previewPadBottom");

    if (mode === "thumb") {
      if (v) { v.pause(); v.style.display = "none"; }
      if (safeZone) safeZone.style.display = "none";
      if (padTop) padTop.style.display = "none";
      if (padBot) padBot.style.display = "none";
      if (ts) ts.style.display = "flex";
      if (tc) tc.style.display = "block";
      if (vc) vc.style.display = "none";
      if (bV) bV.classList.remove("active");
      if (bT) bT.classList.add("active");
    } else {
      if (v) v.style.display = "block";
      if (ts) ts.style.display = "none";
      if (tc) tc.style.display = "none";
      if (vc) vc.style.display = "block";
      if (bV) bV.classList.add("active");
      if (bT) bT.classList.remove("active");
    }
    return;
  }
  if (a === "togglettguide") {
    const gg = $("#ttGridGuide");
    const mo = $("#ttMockOverlay");
    if (gg && mo) {
      const isVisible = gg.style.display !== "none";
      gg.style.display = isVisible ? "none" : "flex";
      mo.style.display = isVisible ? "none" : "flex";
      toast(isVisible ? "TikTok 3:4 profile grid & UI hidden" : "TikTok 3:4 profile grid & UI visible", "ok");
    }
    return;
  }
  if (a === "setthumbstyle") {
    D.thumbStyle = d.style;
    document.querySelectorAll(".thumb-style-card").forEach(c => {
      c.classList.toggle("on", c.getAttribute("data-style") === d.style);
    });
    toast(`Selected ${d.style.replace('_', ' ').toUpperCase()} style. Click Render to apply.`, "ok");
    return;
  }
  if (a === "setthumbcolor") {
    D.thumbColor = d.color;
    document.querySelectorAll(".color-swatch-btn").forEach(s => {
      s.classList.toggle("on", s.getAttribute("data-color") === d.color);
    });
    const lbl = $("#thumb_color_label");
    if (lbl) {
      lbl.textContent = d.name || d.color;
      lbl.style.color = d.color;
    }
    toast(`Accent color set to ${d.name || d.color}`, "ok");
    return;
  }
  if (a === "setthumbarch") {
    D.thumbArch = d.arch;
    document.querySelectorAll(".hook-arch-pill").forEach(p => {
      p.classList.toggle("on", p.getAttribute("data-arch") === d.arch);
    });
    const topic = ($("#ed_title")?.value || "SUCCESS").trim().toUpperCase();
    const words = topic.split(/\s+/);
    const core = words[0] || "THIS";
    const hl1Inp = $("#ed_thumb_hl1");
    const hl2Inp = $("#ed_thumb_hl2");
    const subInp = $("#ed_thumb_sub");

    if (d.arch === "warning") {
      if (hl1Inp) hl1Inp.value = "STOP MAKING THIS";
      if (hl2Inp) hl2Inp.value = `${core} MISTAKE`.slice(0, 20);
      if (subInp) subInp.value = "Why 99% of people fail at this";
    } else if (d.arch === "formula") {
      if (hl1Inp) hl1Inp.value = "THE 3 RULES OF";
      if (hl2Inp) hl2Inp.value = `${core} MASTERY`.slice(0, 20);
      if (subInp) subInp.value = "The step-by-step formula";
    } else if (d.arch === "callout") {
      if (hl1Inp) hl1Inp.value = "IF YOU WANT";
      if (hl2Inp) hl2Inp.value = `REAL ${core}`.slice(0, 20);
      if (subInp) subInp.value = "Watch before this gets deleted";
    } else {
      if (hl1Inp) hl1Inp.value = "THE UNTOLD TRUTH";
      if (hl2Inp) hl2Inp.value = `ABOUT ${core}`.slice(0, 20);
      if (subInp) subInp.value = "What 99% of people miss";
    }
    toast(`Applied ${d.arch.toUpperCase()} hook template!`, "ok");
    return;
  }
  if (a === "aithumbhooks") {
    b.disabled = true;
    try {
      toast("Querying AI for 4 viral TikTok thumbnail hook archetypes...", "ok");
      const cid = d.c || D.cid;
      const res = await send(`/api/clips/${cid}/thumbnail/generate-hooks`, {
        topic: $("#ed_title")?.value || $("#ed_hook")?.value || "",
        hook: $("#ed_desc")?.value || $("#ed_hook")?.value || ""
      });
      const panel = $("#ai_thumb_hooks_panel");
      if (panel && res.hooks && res.hooks.length) {
        panel.style.display = "block";
        panel.innerHTML = `
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
            <span style="font-size:12px;font-weight:700;color:var(--brand)">⚡ AI TikTok Hook Formulas</span>
            <button type="button" class="btn sm ghost" onclick="document.getElementById('ai_thumb_hooks_panel').style.display='none'">✕</button>
          </div>
          <div style="display:flex;flex-direction:column;gap:6px">
            ${res.hooks.map(h => `
              <button type="button" class="btn sm ghost" data-act="applythumbhook"
                data-cat="${esc(h.category || '')}"
                data-hl1="${esc(h.headline_1 || '')}"
                data-hl2="${esc(h.headline_2 || '')}"
                data-sub="${esc(h.subheadline || '')}"
                style="justify-content:flex-start;text-align:left;font-size:11.5px;padding:8px 10px;background:#241A14;border:1px solid rgba(255,255,255,0.12);border-radius:6px;flex-direction:column;align-items:flex-start;gap:2px">
                <div style="display:flex;justify-content:space-between;width:100%">
                  <span style="font-size:10px;font-weight:800;color:var(--brand)">${esc(h.label || h.archetype)}</span>
                  <span style="font-size:9.5px;color:var(--frame-dim)">[Click to apply]</span>
                </div>
                <div style="font-size:12px;font-weight:900;color:#F8F3EF">${esc(h.headline_1)} <span style="color:#FFE600">${esc(h.headline_2)}</span></div>
                <div style="font-size:10.5px;color:#C8BCB4">${esc(h.subheadline)}</div>
              </button>
            `).join("")}
          </div>
        `;
        toast("Loaded 4 viral TikTok thumbnail hooks!", "ok");
      }
    } catch(err) {
      toast("Error generating thumbnail hooks: " + (err.message || err), "bad");
    } finally {
      b.disabled = false;
    }
    return;
  }
  if (a === "applythumbhook") {
    if ($("#ed_thumb_cat")) $("#ed_thumb_cat").value = d.cat || "";
    if ($("#ed_thumb_hl1")) $("#ed_thumb_hl1").value = d.hl1 || "";
    if ($("#ed_thumb_hl2")) $("#ed_thumb_hl2").value = d.hl2 || "";
    if ($("#ed_thumb_sub")) $("#ed_thumb_sub").value = d.sub || "";
    const p = $("#ai_thumb_hooks_panel");
    if (p) p.style.display = "none";
    toast("Hook loaded! Click 'Render Cover' to apply.", "ok");
    return;
  }
  if (a === "grabthumbframe") {
    D.thumbSec = Number($("#ed_thumb_sec")?.value || 1.2);
    toast(`Sampling video frame at ${D.thumbSec.toFixed(1)}s...`, "ok");
    a = "regen_thumb";
  }
  if (a === "regen_thumb") {
    b.disabled = true;
    b.classList.add("loading");
    setStageLoading(true, "Designing Editorial Cover (1080x1920)...", "Real Face Extraction & Typography");
    try {
      toast("Designing high-res AI editorial cover (1080x1920)...", "loading", "Cover Studio");
      const cid = d.c || D.cid;
      const res = await send(`/api/clips/${cid}/thumbnail/regenerate`, {
        topic: $("#ed_title")?.value || "",
        hook: $("#ed_desc")?.value || $("#ed_hook")?.value || "",
        category: $("#ed_thumb_cat")?.value || "",
        headline_1: $("#ed_thumb_hl1")?.value || "",
        headline_2: $("#ed_thumb_hl2")?.value || "",
        subheadline: $("#ed_thumb_sub")?.value || "",
        style: D.thumbStyle || "hormozi",
        accent_color: D.thumbColor || "#FFE600",
        archetype: D.thumbArch || "curiosity",
        timestamp_sec: D.thumbSec || Number($("#ed_thumb_sec")?.value || 1.2)
      });
      if (res && res.thumbnail_url) {
        toast("✨ Professional TikTok cover thumbnail rendered!", "ok", "Cover Ready");
        const img = $("#editorThumbImg");
        if (img) {
          img.src = res.thumbnail_url;
        }
        const thumbBtn = $("#ed_thumb_btn");
        if (thumbBtn) {
          thumbBtn.href = res.thumbnail_url;
          thumbBtn.style.display = "inline-flex";
        }
        const ts = $("#thumbStudioStage");
        const tc = $("#thumbStudioControls");
        const v = $("#editorVideo");
        const vc = $("#videoControlsSection");
        const bV = $("#btn_stage_video");
        const bT = $("#btn_stage_thumb");
        if (ts && ts.style.display === "none") {
          if (v) { v.pause(); v.style.display = "none"; }
          ts.style.display = "flex";
          if (tc) tc.style.display = "block";
          if (vc) vc.style.display = "none";
          if (bV) bV.classList.remove("active");
          if (bT) bT.classList.add("active");
        }
        const cardImg = document.querySelector(`button[data-c="${cid}"] img`);
        if (cardImg) {
          cardImg.src = res.thumbnail_url;
        }
      }
    } catch(err) {
      toast("Error generating thumbnail: " + (err.message || err), "bad", "Studio Error");
    } finally {
      b.disabled = false;
      b.classList.remove("loading");
      setStageLoading(false);
    }
    return;
  }
  if (a === "remake") {
    b.disabled = true;
    b.classList.add("loading");
    setStageLoading(true, "Re-burning Vertical Clip...", "GPU NVENC Hardware Acceleration");
    try {
      toast("Re-burning vertical clip with GPU NVENC hardware acceleration...", "loading", "Rendering Clip");
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
      toast("✨ Clip re-burn complete and ready to export!", "ok", "Render Ready");
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
      toast("Render failed: " + (err.message || err), "bad", "Render Error");
    } finally {
      b.disabled = false;
      b.classList.remove("loading");
      setStageLoading(false);
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
  if (a === "runcopilot" || a === "copilotpreset") {
    let instruction = "";
    if (a === "copilotpreset") {
      const p = d.preset;
      const presets = {
        sharpen_hook: "Sharpen the hook for peak curiosity and scroll-stopping retention",
        add_controversy: "Make headline and hook controversial to spark comment debates",
        focus_wealth: "Re-angle headline and hook towards wealth, business, and financial success",
        mrbeast_hype: "Use high energy MrBeast neon subtitles and fast paced headline",
        clean_editorial: "Use clean minimal editorial caption style with balanced contrast"
      };
      instruction = presets[p] || p;
      if ($("#ai_copilot_prompt")) $("#ai_copilot_prompt").value = instruction;
    } else {
      instruction = $("#ai_copilot_prompt")?.value?.trim() || "";
    }
    if (!instruction) {
      toast("Please enter an edit instruction or choose a preset chip.", "info");
      return;
    }

    b.disabled = true;
    toast("AI Video Copilot analyzing clip and applying edits...", "loading", "AI Copilot");
    try {
      const res = await send("/api/ai/edit-copilot", {
        clip_id: D.cid,
        instruction,
        current_state: {
          title: $("#ed_title")?.value || "",
          hook: $("#ed_hook")?.value || "",
          subtitle_style: $("#ed_style")?.value || "hormozi",
          layout_mode: $("#ed_layout")?.value || "fit_canvas"
        }
      });
      if (res && res.edits) {
        const ed = res.edits;
        if (ed.updated_title && $("#ed_title")) $("#ed_title").value = ed.updated_title;
        if (ed.updated_hook && $("#ed_hook")) $("#ed_hook").value = ed.updated_hook;
        if (ed.suggested_subtitle_style && $("#ed_style")) $("#ed_style").value = ed.suggested_subtitle_style;
        if (ed.suggested_layout && $("#ed_layout")) $("#ed_layout").value = ed.suggested_layout;
        if (ed.hashtags && $("#ed_tags")) $("#ed_tags").value = ed.hashtags.join(" ");

        toast(`✨ AI Copilot: ${ed.explanation || 'Applied optimizations'}`, "ok", "Edit Applied");
      }
    } catch (err) {
      toast("Copilot error: " + (err.message || err), "bad", "AI Copilot");
    } finally {
      b.disabled = false;
    }
    return;
  }
  if (a === "gensocialkit") {
    b.disabled = true;
    toast("Generating multi-platform publishing kit (TikTok, Reels, Shorts)...", "loading", "Social Kit");
    try {
      const res = await send("/api/ai/social-kit", {
        clip_id: D.cid,
        title: $("#ed_title")?.value || "",
        hook: $("#ed_hook")?.value || "",
        transcript: D.activeWords ? D.activeWords.map(w => w.word).join(" ") : ""
      });
      const box = $("#social_kit_rendered_box");
      if (box && res.social_kit) {
        const sk = res.social_kit;
        box.innerHTML = `
          <div class="social-platform-card">
            <div class="social-card-head">
              <h4>📱 TikTok Post</h4>
              <button type="button" class="btn sm" data-act="copysocialtext" data-text="${esc(sk.tiktok?.caption + '\n\n' + (sk.tiktok?.hashtags || []).join(' '))}">${ic("copy")} Copy</button>
            </div>
            <div class="social-text-block">${esc(sk.tiktok?.caption || "")}\n\n${esc((sk.tiktok?.hashtags || []).join(" "))}</div>
            <div style="font-size:11px;color:#A89C94"><b>SEO Keywords:</b> ${esc((sk.tiktok?.seo_keywords || []).join(", "))}</div>
          </div>

          <div class="social-platform-card">
            <div class="social-card-head">
              <h4>📸 Instagram Reels</h4>
              <button type="button" class="btn sm" data-act="copysocialtext" data-text="${esc(sk.instagram?.caption)}">${ic("copy")} Copy</button>
            </div>
            <div class="social-text-block">${esc(sk.instagram?.caption || "")}</div>
          </div>

          <div class="social-platform-card">
            <div class="social-card-head">
              <h4>🔴 YouTube Shorts</h4>
              <button type="button" class="btn sm" data-act="copysocialtext" data-text="${esc(sk.youtube_shorts?.title + '\n\n' + sk.youtube_shorts?.description)}">${ic("copy")} Copy</button>
            </div>
            <div class="social-text-block"><b>${esc(sk.youtube_shorts?.title || "")}</b>\n\n${esc(sk.youtube_shorts?.description || "")}</div>
          </div>
        `;
        toast("Generated publishing copy for all 3 platforms!", "ok", "Social Kit Ready");
      }
    } catch (err) {
      toast("Error generating social kit: " + (err.message || err), "bad");
    } finally {
      b.disabled = false;
    }
    return;
  }
  if (a === "copysocialtext") {
    await navigator.clipboard.writeText(d.text);
    toast("Copied post text to clipboard!", "ok");
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

// Handle source tabs (YouTube vs Upload)
document.addEventListener("click", e => {
  const tabBtn = e.target.closest(".source-tab");
  if (tabBtn) {
    const targetTab = tabBtn.dataset.tab;
    DRAFT.activeTab = targetTab;
    document.querySelectorAll(".source-tab").forEach(b => {
      const active = b.dataset.tab === targetTab;
      b.classList.toggle("active", active);
      b.setAttribute("aria-selected", active);
    });
    const paneYt = $("#pane_youtube");
    const paneUp = $("#pane_upload");
    if (paneYt) paneYt.style.display = targetTab === "youtube" ? "block" : "none";
    if (paneUp) paneUp.style.display = targetTab === "upload" ? "block" : "none";
    if (targetTab === "youtube") {
      setTimeout(() => $("#url")?.focus(), 50);
    }
  }

  // Handle clip editor modal subnav tabs (Video & Framing, Captions & Words, Cover Studio, Social Copy)
  const modalTabBtn = e.target.closest(".modal-tab-btn");
  if (modalTabBtn) {
    const target = modalTabBtn.dataset.modaltab;
    document.querySelectorAll(".modal-tab-btn").forEach(b => {
      const active = b.dataset.modaltab === target;
      b.classList.toggle("active", active);
      b.setAttribute("aria-selected", active);
    });
    document.querySelectorAll(".modal-tab-pane").forEach(p => {
      p.classList.toggle("active", p.id === `pane_modaltab_${target}`);
    });
    // Auto switch stage mode based on tab
    if (target === "cover") {
      const btnThumb = $("#btn_stage_thumb");
      if (btnThumb && !btnThumb.classList.contains("active")) {
        btnThumb.click();
      }
    } else if (target === "video" || target === "captions") {
      const btnVid = $("#btn_stage_video");
      if (btnVid && !btnVid.classList.contains("active")) {
        btnVid.click();
      }
    }
  }
});

// Drag and drop video files directly onto composer or dropzone
document.addEventListener("dragover", e => {
  e.preventDefault();
  const c = $("#addform");
  if (c && e.dataTransfer?.types?.includes("Files")) {
    c.classList.add("over");
  }
});

document.addEventListener("dragleave", e => {
  const c = $("#addform");
  if (c && !c.contains(e.relatedTarget)) {
    c.classList.remove("over");
  }
});

document.addEventListener("drop", e => {
  const c = $("#addform");
  if (c) c.classList.remove("over");
  if (e.dataTransfer?.files?.length) {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f.type.startsWith("video/") || f.name.match(/\.(mp4|mov|mkv|avi|webm|flv|wmv)$/i)) {
      DRAFT.file = f;
      DRAFT.link = null;
      DRAFT.activeTab = "upload";
      drawAdd();
      drawAtt();
      toast(`Loaded video file: ${f.name} (${(f.size / (1024 * 1024)).toFixed(1)} MB)`, "ok");
    } else {
      toast("Please drop a valid video file (MP4, MOV, MKV, etc.)", "bad");
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
    const text = e.target.value.trim() ? e.target.value.trim().toUpperCase() : "THE REAL REASON 99% OF PEOPLE FAIL AT THIS HABIT";
    if (bannerEl) bannerEl.innerHTML = `<span class="preview-banner-viral-pill">${esc(text)}</span>`;
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

// Google Drive OAuth Popup Listener
window.addEventListener("message", e => {
  if (e.data === "gdrive_connected") {
    api("/api/gdrive/status").then(st => {
      if (st) {
        S.gdrive = st;
        toast("⚡ Google Drive connected successfully!", "ok");
        drawSettings();
        rTopBar();
      }
    });
  }
});

// Initial boot
document.addEventListener("DOMContentLoaded", () => {
  go("library");
  tick();
  loop();
  api("/api/gdrive/status").then(st => {
    if (st) {
      S.gdrive = st;
      rTopBar();
    }
  }).catch(() => {});
});
