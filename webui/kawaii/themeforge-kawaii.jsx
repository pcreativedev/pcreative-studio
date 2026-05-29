/* ===================== ThemeForge ♡ Kawaii ===================== */
const { useState, useEffect, useRef } = React;

/* agentes IA como mascotas kawaii */
const AGENTS = {
  claude:   { label: 'Claude-chan',  em: '🩵', color: '#7fb8ff' },
  codex:    { label: 'Codex-kun',    em: '💚', color: '#7fd9a8' },
  gemini:   { label: 'Gemini-chan',  em: '💛', color: '#ffcf5e' },
  opencode: { label: 'OpenCode',     em: '💜', color: '#c79bff' },
};

const STATUS = {
  live:     { label: 'live ♪',  em: '🌟', color: '#5fd8b4' },
  building: { label: 'forjando', em: '🔨', color: '#ff8fc7' },
  draft:    { label: 'borrador', em: '✏️', color: '#ffcf5e' },
  archived: { label: 'guardado', em: '📦', color: '#c4a8be' },
};

const PROJECTS = [
  { id: 'k-aurora', name: 'Aurora SaaS', jp: 'オーロラ', type: 'SaaS Landing', agent: 'claude', status: 'live', cost: 4.82, tags: ['next', 'tailwind'], commits: 47, updated: 'hace 3 min' },
  { id: 'k-nordic', name: 'Nordic Forge', jp: '北欧', type: 'Agencia creativa', agent: 'codex', status: 'building', cost: 2.10, tags: ['astro', 'gsap'], commits: 23, updated: 'hace 12 min' },
  { id: 'k-meridian', name: 'Meridian Shop', jp: '商店', type: 'E-commerce', agent: 'gemini', status: 'live', cost: 7.34, tags: ['shopify', 'remix'], commits: 89, updated: 'hace 1 h' },
  { id: 'k-flux', name: 'Flux Admin', jp: '管理', type: 'Dashboard', agent: 'opencode', status: 'draft', cost: 0.41, tags: ['laravel', 'vue'], commits: 8, updated: 'hace 5 h' },
  { id: 'k-zen', name: 'Zen Clinic', jp: '診療', type: 'Clínica · booking', agent: 'claude', status: 'live', cost: 3.95, tags: ['wp', 'acf'], commits: 34, updated: 'ayer' },
  { id: 'k-pixel', name: 'Pixel Arcade', jp: '遊技', type: 'Landing · game', agent: 'codex', status: 'archived', cost: 1.22, tags: ['tauri', 'react'], commits: 19, updated: 'hace 3 días' },
];

const STACKS = [
  { k: 'next', label: 'Next.js', jp: '次世代', em: '⚡' },
  { k: 'astro', label: 'Astro', jp: '星', em: '🚀' },
  { k: 'laravel', label: 'Laravel', jp: '帆', em: '🎀' },
  { k: 'wp', label: 'WordPress', jp: '出版', em: '📰' },
  { k: 'shopify', label: 'Hydrogen', jp: '商', em: '🛍️' },
  { k: 'tauri', label: 'Tauri', jp: '鳥', em: '🖥️' },
];

const NAV = [
  { id: 'gallery', em: '🖼️', label: 'Galería', jp: '制作' },
  { id: 'new', em: '✨', label: 'Nuevo', jp: '新規' },
  { id: 'cost', em: '💰', label: 'Coste IA', jp: '費用' },
  { id: 'compare', em: '⚔️', label: 'Comparar', jp: '比較' },
  { id: 'operator', em: '🚀', label: 'Operator', jp: '司令' },
  { id: 'market', em: '🌷', label: 'Market', jp: '市場' },
  { id: 'licensing', em: '🔑', label: 'Licencias', jp: '認可' },
  { id: 'settings', em: '🎨', label: 'Ajustes', jp: '設定' },
];

const MCP_SERVERS = [
  { id: 'filesystem', label: 'filesystem', always: true, em: '📁', desc: 'Acceso al proyecto' },
  { id: 'fetch', label: 'fetch', always: true, em: '🌐', desc: 'HTTP / scraping' },
  { id: 'memory', label: 'memory', always: true, em: '🧠', desc: 'Memoria del agente' },
  { id: 'github', label: 'github', always: true, em: '🐙', desc: 'Repos · PRs · push' },
  { id: 'themeforge', label: 'themeforge', always: true, em: '🌸', desc: '8 tools: create · zip · preflight…' },
  { id: 'playwright', label: 'playwright', em: '🎭', desc: 'Navegador automatizado' },
  { id: 'figma', label: 'figma-context', em: '🎨', desc: 'Lee diseños de Figma' },
  { id: 'shopify', label: 'shopify-dev', em: '🛍️', desc: 'GraphQL Admin/Storefront' },
  { id: 'postgres', label: 'postgres', em: '🐘', desc: 'Query a la DB' },
];

const DEPLOY_TARGETS = [
  { id: 'netlify', label: 'Netlify', em: '🩵' },
  { id: 'vercel', label: 'Vercel', em: '▲' },
  { id: 'cloudflare', label: 'Cloudflare', em: '🧡' },
  { id: 'surge', label: 'Surge', em: '💚' },
];

const PREFLIGHT = [
  { l: 'LICENSE presente', ok: true }, { l: 'documentation/ completa', ok: true },
  { l: 'Lighthouse ≥ 90', ok: true, n: '94 ♡' }, { l: 'Sin secretos (.env limpio)', ok: true },
  { l: 'Layout original (anti-copy)', ok: true }, { l: 'Imágenes con licencia', ok: false, n: '2 sin atribuir' },
  { l: 'Responsive 320→1920', ok: true },
];

/* ---- sparkles + burst ---- */
function startSparkles() {
  const box = document.getElementById('sparkles');
  if (!box || box.dataset.on) return;
  box.dataset.on = '1';
  const g = ['✨', '🌸', '⭐', '💖', '🩷', '🦋', '🍡', '🌟'];
  setInterval(() => {
    if (getComputedStyle(box).opacity === '0' || box.children.length > 24) return;
    const s = document.createElement('div');
    s.className = 'sp'; s.textContent = g[Math.floor(Math.random() * g.length)];
    s.style.left = Math.random() * 100 + 'vw';
    s.style.fontSize = (12 + Math.random() * 20) + 'px';
    const d = 7 + Math.random() * 8; s.style.animationDuration = d + 's';
    box.appendChild(s); setTimeout(() => s.remove(), d * 1000);
  }, 680);
}
function burst(e) {
  const h = document.createElement('div'); h.className = 'heart-burst';
  h.textContent = ['💖', '✨', '🌸', '🩷'][Math.floor(Math.random() * 4)];
  h.style.left = (e.clientX - 12) + 'px'; h.style.top = (e.clientY - 12) + 'px';
  document.body.appendChild(h); setTimeout(() => h.remove(), 900);
}
const Slot = ({ id, cls, radius = 18, ph }) => React.createElement('image-slot', { id, class: cls, shape: 'rounded', radius: String(radius), placeholder: ph });

/* ---- Gallery ---- */
function ProjectCard({ p, onOpen }) {
  const [fav, setFav] = useState(p.status === 'live');
  const ag = AGENTS[p.agent], st = STATUS[p.status];
  return (
    <div className="pcard fade" style={{ opacity: p.status === 'archived' ? 0.7 : 1, cursor: 'pointer' }} onClick={() => onOpen(p)}>
      <span className="pstatus" style={{ color: st.color }}>{st.em} {st.label}</span>
      <span className="pjp">{p.jp}</span>
      <Slot id={p.id} cls="pcover" radius={20} ph="arrastra tu anime ♡" />
      <span className="pfav" onClick={(e) => { e.stopPropagation(); setFav(f => !f); burst(e); }}>{fav ? '💗' : '🤍'}</span>
      <div className="pbody">
        <div className="prow">
          <div><div className="pname">{p.name}</div><div className="ptype">{p.type}</div></div>
          <div className="pcost">${p.cost.toFixed(2)}</div>
        </div>
        <div className="ptags">{p.tags.map(t => <span key={t} className="tag">{t}</span>)}</div>
        <div className="pfoot">
          <span className="pagent" style={{ color: ag.color }}>{ag.em} {ag.label}</span>
          <span style={{ color: 'var(--tx-dim)', fontWeight: 600 }}>{p.commits} commits · {p.updated}</span>
        </div>
      </div>
    </div>
  );
}

function Gallery({ onOpen }) {
  const [f, setF] = useState('all');
  const fl = ['all', 'live', 'building', 'draft', 'archived'];
  const list = PROJECTS.filter(p => f === 'all' || p.status === f);
  return (
    <div className="page fade">
      <div className="stats">
        {[['🎀', '6', 'proyectos'], ['💸', '$19.84', 'cómputo IA'], ['🌟', '3', 'publicados'], ['🔨', '1', 'forjando ahora']].map(([e, n, l]) => (
          <div className="stat" key={l}><div className="em">{e}</div><div className="n">{n}</div><div className="l">{l}</div></div>
        ))}
      </div>
      <div className="filters">
        {fl.map(x => <button key={x} className={'fchip' + (f === x ? ' on' : '')} onClick={() => setF(x)}>{x === 'all' ? '✨ todos' : STATUS[x].em + ' ' + STATUS[x].label}</button>)}
      </div>
      <div className="grid">{list.map(p => <ProjectCard key={p.id} p={p} onOpen={onOpen} />)}</div>
    </div>
  );
}

/* ---- New project (vibe scaffolder kawaii) ---- */
function NewProject() {
  const [vibe, setVibe] = useState('');
  const [stack, setStack] = useState('next');
  const [agent, setAgent] = useState('claude');
  const [thinking, setThinking] = useState(false);
  const [done, setDone] = useState(false);
  const go = () => { setThinking(true); setDone(false); setTimeout(() => { setThinking(false); setDone(true); setStack('next'); }, 1300); };
  return (
    <div className="page fade" style={{ maxWidth: 920 }}>
      <h2 className="sec">✨ Vibe Scaffolder <span style={{ fontFamily: 'var(--jp)', fontSize: 14, color: 'var(--tx-dim)' }}>新規制作</span></h2>
      <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: 18 }}>
        <div className="panelc">
          <div style={{ fontWeight: 700, marginBottom: 10 }}>Cuéntame qué quieres crear 🌷</div>
          <textarea className="ta" value={vibe} onChange={e => setVibe(e.target.value)} placeholder='Ej: "Landing kawaii para cafetería de gatitos, pastel y redondito…"' />
          <button className="btn pri" style={{ marginTop: 14 }} onClick={go}>{thinking ? '✨ pensando…' : '✨ Pre-rellenar con IA'}</button>
          {thinking && <span style={{ marginLeft: 10, color: 'var(--accent)', fontWeight: 700 }}>{AGENTS[agent].em} analizando…</span>}
          {done && (
            <div className="fade" style={{ marginTop: 16, background: 'var(--bg2)', borderRadius: 16, padding: 14, fontSize: 13.5, lineHeight: 1.6 }}>
              <b>Prompt generado ♡</b><br />Build a production-ready landing usando <b style={{ color: 'var(--accent)' }}>Next.js</b>. {vibe || 'Diseño kawaii pastel, redondeado, mascota animada.'} Sistema de diseño coherente, accesible, imágenes del nicho, deploy-ready.
            </div>
          )}
        </div>
        <div className="panelc">
          <div style={{ fontWeight: 700, marginBottom: 10 }}>Agente IA 🐾</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            {Object.entries(AGENTS).map(([k, a]) => (
              <button key={k} className={'tile' + (agent === k ? ' on' : '')} onClick={() => setAgent(k)} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 18 }}>{a.em}</span><span style={{ fontSize: 13, fontWeight: 700 }}>{a.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
      <h2 className="sec" style={{ margin: '26px 0 14px' }}>🧱 Elige tu stack <span style={{ fontFamily: 'var(--jp)', fontSize: 14, color: 'var(--tx-dim)' }}>基盤</span></h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(140px,1fr))', gap: 10 }}>
        {STACKS.map(s => (
          <button key={s.k} className={'tile' + (stack === s.k ? ' on' : '')} onClick={() => setStack(s.k)}>
            <div style={{ fontSize: 22 }}>{s.em}</div>
            <div style={{ fontWeight: 700, fontSize: 14.5, marginTop: 4 }}>{s.label}</div>
            <div style={{ fontFamily: 'var(--jp)', fontSize: 11, color: 'var(--tx-dim)' }}>{s.jp}</div>
          </button>
        ))}
      </div>
      <div className="panelc" style={{ marginTop: 22, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontWeight: 600, color: 'var(--tx-dim)' }}><b style={{ color: 'var(--accent)' }}>{STACKS.find(s => s.k === stack).label}</b> · {AGENTS[agent].label} · ~$0.40</span>
        <button className="btn pri">🔨 ¡Forjar proyecto!</button>
      </div>
    </div>
  );
}

/* ---- Cost (kawaii donut + bars) ---- */
const COST = [{ k: 'claude', v: 12.77 }, { k: 'gemini', v: 7.34 }, { k: 'codex', v: 3.32 }, { k: 'opencode', v: 1.63 }];
function Cost() {
  const total = COST.reduce((s, d) => s + d.v, 0);
  const days = Array.from({ length: 14 }, (_, i) => 0.3 + Math.abs(Math.sin(i / 2)) * 1.4 + (i > 10 ? 0.6 : 0));
  const max = Math.max(...days);
  let acc = 0, C = 2 * Math.PI * 70;
  return (
    <div className="page fade">
      <h2 className="sec">💰 Coste de IA <span style={{ fontFamily: 'var(--jp)', fontSize: 14, color: 'var(--tx-dim)' }}>費用追跡</span></h2>
      <div className="stats" style={{ marginBottom: 22 }}>
        {[['💖', '$' + total.toFixed(2), 'total'], ['🌸', '$8.42', 'este mes'], ['🎀', '$3.94', 'media/proyecto'], ['✨', '421K', 'tokens/$']].map(([e, n, l]) => (
          <div className="stat" key={l}><div className="em">{e}</div><div className="n">{n}</div><div className="l">{l}</div></div>
        ))}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 18 }}>
        <div className="panelc" style={{ textAlign: 'center' }}>
          <div style={{ fontWeight: 700, marginBottom: 10 }}>Por mascota 🐾</div>
          <svg viewBox="0 0 180 180" style={{ width: 180, height: 180 }}>
            <circle cx="90" cy="90" r="70" fill="none" stroke="var(--bg2)" strokeWidth="20" />
            {COST.map(d => {
              const frac = d.v / total, dash = C * frac;
              const el = <circle key={d.k} cx="90" cy="90" r="70" fill="none" stroke={AGENTS[d.k].color} strokeWidth="20" strokeLinecap="round" strokeDasharray={`${dash - 4} ${C}`} strokeDashoffset={-C * acc} transform="rotate(-90 90 90)" />;
              acc += frac; return el;
            })}
            <text x="90" y="96" textAnchor="middle" style={{ fontFamily: 'var(--cute)', fontSize: 22, fill: 'var(--accent)' }}>${total.toFixed(0)}</text>
          </svg>
          <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 7 }}>
            {COST.map(d => (
              <div key={d.k} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, fontWeight: 600 }}>
                <span>{AGENTS[d.k].em}</span><span style={{ flex: 1, textAlign: 'left' }}>{AGENTS[d.k].label}</span><span style={{ color: 'var(--accent)' }}>${d.v.toFixed(2)}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="panelc">
          <div style={{ fontWeight: 700, marginBottom: 16 }}>Gasto diario 🌈</div>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8, height: 180 }}>
            {days.map((v, i) => (
              <div key={i} style={{ flex: 1, height: (v / max * 100) + '%', borderRadius: '99px 99px 6px 6px', background: i > 10 ? 'linear-gradient(var(--accent2),var(--accent))' : 'linear-gradient(var(--accent),var(--accent2))' }} title={'$' + v.toFixed(2)} />
            ))}
          </div>
          <div style={{ textAlign: 'center', marginTop: 10, color: 'var(--tx-dim)', fontWeight: 600, fontSize: 12.5 }}>últimos 14 días ♡</div>
        </div>
      </div>
    </div>
  );
}

/* ---- Compare ---- */
function Compare() {
  const [run, setRun] = useState(false);
  const outs = {
    claude: ['🩵 analizando ♡', 'export function Pricing()', '✓ 1.2s · best girl ⭐'],
    codex: ['💚 tokenizando…', 'const Pricing = () =>', '✓ 1.6s'],
    gemini: ['💛 planeando…', 'function PricingGrid()', '✓ 1.4s'],
    opencode: ['💜 cargando local…', 'export const Pricing', '✓ 3.1s'],
  };
  return (
    <div className="page fade">
      <h2 className="sec">⚔️ Comparar agentes <span style={{ fontFamily: 'var(--jp)', fontSize: 14, color: 'var(--tx-dim)' }}>比較</span></h2>
      <div className="panelc" style={{ display: 'flex', gap: 10, marginBottom: 18 }}>
        <input className="ta" style={{ minHeight: 0, padding: '10px 14px', borderRadius: 99 }} defaultValue="Crea una sección de pricing de 3 tiers con toggle anual" />
        <button className="btn pri" onClick={() => { setRun(false); setTimeout(() => setRun(true), 50); }}>▶ ¡Carrera!</button>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {Object.entries(AGENTS).map(([k, a]) => (
          <div className="panelc" key={k} style={{ padding: 16 }}>
            <div style={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}><span style={{ fontSize: 18 }}>{a.em}</span> {a.label}</div>
            <div style={{ background: 'var(--bg2)', borderRadius: 14, padding: 12, fontSize: 12.5, lineHeight: 1.9, minHeight: 80, fontFamily: 'var(--font)', color: 'var(--tx-dim)' }}>
              {run ? outs[k].map((l, i) => <div key={i} style={{ color: l.startsWith('✓') ? a.color : 'var(--tx-dim)', fontWeight: l.startsWith('✓') ? 700 : 500 }}>{l}</div>) : <span>esperando carrera… ♡</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ---- Operator ---- */
const MISSIONS = [
  { id: 'o1', name: 'Aurora · hero + pricing', agent: 'claude', st: 'corriendo', pct: 68, eta: '2m 10s' },
  { id: 'o2', name: 'Nordic · case studies', agent: 'codex', st: 'corriendo', pct: 34, eta: '5m 40s' },
  { id: 'o3', name: 'Meridian · checkout', agent: 'gemini', st: 'en cola', pct: 0, eta: '—' },
  { id: 'o4', name: 'Zen · booking widget', agent: 'claude', st: 'listo ♡', pct: 100, eta: '✓' },
];
function Operator() {
  return (
    <div className="page fade">
      <h2 className="sec">🚀 Mission Control <span style={{ fontFamily: 'var(--jp)', fontSize: 14, color: 'var(--tx-dim)' }}>司令室</span></h2>
      <div className="stats" style={{ marginBottom: 22 }}>
        {[['🔨', '2', 'activas'], ['⏳', '1', 'en cola'], ['🌟', '12', 'hoy'], ['💸', '$8.40', 'coste hoy']].map(([e, n, l]) => (
          <div className="stat" key={l}><div className="em">{e}</div><div className="n">{n}</div><div className="l">{l}</div></div>
        ))}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {MISSIONS.map(m => {
          const a = AGENTS[m.agent];
          return (
            <div className="panelc" key={m.id} style={{ padding: '16px 20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ fontSize: 18 }}>{a.em}</span>
                <b style={{ flex: 1 }}>{m.name}</b>
                <span style={{ fontWeight: 700, color: m.pct === 100 ? 'var(--p3)' : 'var(--accent)' }}>{m.st}</span>
                <span style={{ color: 'var(--tx-dim)', fontWeight: 600, width: 56, textAlign: 'right' }}>{m.eta}</span>
              </div>
              <div className="bar2" style={{ marginTop: 11 }}><i style={{ width: m.pct + '%', background: m.pct === 100 ? 'var(--p3)' : 'linear-gradient(90deg,var(--accent),var(--accent2))' }} /></div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ---- Settings (themes) ---- */
// Temas REALES de ThemeForge inyectados por el shell (prototipos + packs + clásicos).
const THEMES = ((typeof window !== 'undefined' && window.__TF_DATA__ && window.__TF_DATA__.themes) || [
  { k: 'kawaii', label: 'Kawaii 🌸', acc: '#ff8fc7', acc2: '#b9a3ff', bg: '#fff5fa', proto: true, web: true },
]);
function Settings() {
  const [th, setTh] = useState((window.__TF_DATA__ && window.__TF_DATA__.current_theme) || 'kawaii');
  const applyTheme = (t) => {
    setTh(t.k);
    if (t.proto) { if (window.tfBridge && window.tfBridge.use_web_theme) window.tfBridge.use_web_theme(t.k); }
    else if (t.web) { if (window.tfApplyTheme && t.vars) window.tfApplyTheme(t.vars); if (window.tfBridge && window.tfBridge.set_theme) window.tfBridge.set_theme(t.k); }
    else if (window.tfBridge && window.tfBridge.switch_to_classic) { if (confirm('Tema clásico «' + t.label + '» (UI nativa). ThemeForge se reiniciará. ¿Continuar?')) window.tfBridge.switch_to_classic(t.k); }
  };
  return (
    <div className="page fade" style={{ maxWidth: 820 }}>
      <h2 className="sec">🎨 Temas de la app <span style={{ fontFamily: 'var(--jp)', fontSize: 14, color: 'var(--tx-dim)' }}>テーマ</span></h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 14 }}>
        {THEMES.map(t => (
          <button key={t.k} className={'tile' + (th === t.k ? ' on' : '')} onClick={() => applyTheme(t)} style={{ padding: 0, overflow: 'hidden', position: 'relative' }}>
            {t.proto && <span style={{ position: 'absolute', top: 5, right: 5, fontSize: 9, padding: '2px 6px', borderRadius: 99, background: 'rgba(255,143,199,0.2)', color: 'var(--accent)' }}>診⟳</span>}
            {t.web === false && <span style={{ position: 'absolute', top: 5, right: 5, fontSize: 9, padding: '2px 6px', borderRadius: 99, background: 'rgba(255,176,0,0.2)', color: '#d99a00' }}>古典↻</span>}
            <div style={{ height: 64, background: t.bg, padding: 10, display: 'flex', gap: 6, alignItems: 'flex-start' }}>
              <span style={{ width: 18, height: 18, borderRadius: 99, background: t.acc, boxShadow: `0 0 8px ${t.acc}` }} />
              <span style={{ width: 18, height: 18, borderRadius: 99, background: t.acc2 }} />
            </div>
            <div style={{ padding: '10px 12px', fontWeight: 700, fontSize: 14 }}>{t.label}</div>
          </button>
        ))}
      </div>
      <div className="panelc" style={{ marginTop: 20 }}>
        <div style={{ fontWeight: 700, marginBottom: 8 }}>Mascota de la app 🐱</div>
        <div style={{ display: 'flex', gap: 14, alignItems: 'center' }}>
          <Slot id="mascot" cls="" radius={20} ph="tu mascota anime ♡" />
          <span style={{ color: 'var(--tx-dim)', fontWeight: 600, fontSize: 13.5 }}>Arrastra una imagen para tu mascota — te saludará en cada arranque. (◕ᴗ◕✿)</span>
        </div>
      </div>

      <h2 className="sec" style={{ margin: '26px 0 14px' }}>📡 MCP servers <span style={{ fontFamily: 'var(--jp)', fontSize: 14, color: 'var(--tx-dim)' }}>接続</span></h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(220px,1fr))', gap: 12 }}>
        {MCP_SERVERS.map(m => (
          <div className="panelc" key={m.id} style={{ padding: 15 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><span style={{ fontSize: 17 }}>{m.em}</span><b style={{ flex: 1, fontSize: 14 }}>{m.label}</b>{m.always && <span className="tag" style={{ color: 'var(--accent)' }}>always</span>}</div>
            <div style={{ color: 'var(--tx-dim)', fontWeight: 600, fontSize: 12.5, marginTop: 8, lineHeight: 1.5 }}>{m.desc}</div>
          </div>
        ))}
      </div>

      <h2 className="sec" style={{ margin: '26px 0 14px' }}>🎮 Pixel Office <span style={{ fontFamily: 'var(--jp)', fontSize: 14, color: 'var(--tx-dim)' }}>可視化</span></h2>
      <div className="panelc" style={{ textAlign: 'center' }}>
        <div style={{ color: 'var(--tx-dim)', fontWeight: 600, fontSize: 13.5, maxWidth: 480, margin: '0 auto 16px', lineHeight: 1.6 }}>Visualizador pixel-art que muestra tus sesiones de IA como mascotas en una oficina virtual. ♡</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(8,1fr)', gap: 4, maxWidth: 280, margin: '0 auto 18px' }}>
          {Array.from({ length: 24 }, (_, i) => { const a = [9, 12, 18].includes(i); const cols = ['#7fb8ff', '#7fd9a8', '#ffcf5e']; return <div key={i} style={{ aspectRatio: '1', borderRadius: 6, background: a ? cols[i % 3] : 'var(--bg2)', boxShadow: a ? `0 0 8px ${cols[i % 3]}` : 'none' }} />; })}
        </div>
        <button className="btn pri">🎮 Lanzar dashboard</button>
      </div>
      <style>{`#mascot{width:120px;height:120px;flex-shrink:0;}`}</style>
    </div>
  );
}

/* ---- Project Window (preview + terminal kawaii) ---- */
const TERM_K = [
  { c: 'var(--accent)', s: '$ themeforge agent --task "build hero + features" ♡' },
  { c: '#7fb8ff', s: '🩵 Claude-chan · session forge-7f2a' },
  { c: 'var(--tx-dim)', s: '⟳ leyendo CLAUDE.md … contexto cargado' },
  { c: '#7fd9a8', s: '✓ creado Hero.tsx (+148 −0) 🌸' },
  { c: '#7fd9a8', s: '✓ creado FeatureBento.tsx (+212 −0)' },
  { c: 'var(--tx-dim)', s: '⟳ tipando … tsc — 0 errores ♪' },
  { c: 'var(--accent2)', s: '◤ ¡tarea completa! preview actualizado ✨' },
];
function KawaiiTerminal({ run }) {
  const [n, setN] = useState(0);
  const box = useRef(null);
  useEffect(() => {
    if (!run) { setN(0); return; }
    setN(0); let i = 0;
    const t = setInterval(() => { i++; setN(i); if (i >= TERM_K.length) clearInterval(t); }, 480);
    return () => clearInterval(t);
  }, [run]);
  useEffect(() => { if (box.current) box.current.scrollTop = box.current.scrollHeight; }, [n]);
  return (
    <div ref={box} style={{ background: 'var(--bg2)', borderRadius: 18, padding: 14, fontFamily: 'var(--font)', fontSize: 13, lineHeight: 1.85, flex: 1, overflowY: 'auto', minHeight: 0 }}>
      {TERM_K.slice(0, n).map((l, i) => <div key={i} style={{ color: l.c, fontWeight: 600 }}>{l.s}</div>)}
      {run && n < TERM_K.length && <span style={{ color: 'var(--accent)' }}>▊</span>}
      {!run && <span style={{ color: 'var(--tx-dim)' }}>terminal lista ♡ — pulsa ▶</span>}
    </div>
  );
}
function ProjectWindow({ p, onBack, onDeploy, onBuild, onRef }) {
  const [tab, setTab] = useState('desktop');
  const [run, setRun] = useState(false);
  const [pushed, setPushed] = useState(false);
  const ag = AGENTS[p.agent], st = STATUS[p.status];
  useEffect(() => { const t = setTimeout(() => setRun(true), 500); return () => clearTimeout(t); }, []);
  const tabs = [['desktop', '🖥️ Desktop'], ['mobile', '📱 Mobile'], ['code', '💻 Code']];
  return (
    <div className="page fade" style={{ height: '100%', display: 'flex', flexDirection: 'column', paddingBottom: 26 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
        <button className="btn" onClick={onBack}>← Galería</button>
        <b style={{ fontSize: 19 }}>{p.name}</b><span style={{ fontFamily: 'var(--jp)', color: 'var(--tx-dim)' }}>{p.jp}</span>
        <span className="pstatus" style={{ position: 'static', color: st.color }}>{st.em} {st.label}</span>
        <div style={{ flex: 1 }} />
        <button className="btn" onClick={onBuild}>✅ Pre-flight</button>
        <button className={'btn' + (pushed ? '' : ' pri')} onClick={() => setPushed(true)}>{pushed ? '✓ Pushed 🐙' : '🐙 Push'}</button>
        <button className="btn pri" onClick={onDeploy}>🚀 Deploy</button>
      </div>
      {/* MCP chips */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 14, flexWrap: 'wrap', alignItems: 'center' }}>
        <span style={{ fontSize: 11.5, fontWeight: 700, color: 'var(--tx-dim)' }}>MCP ·</span>
        {MCP_SERVERS.slice(0, 7).map(m => <span key={m.id} className="tag" style={{ color: m.always ? 'var(--accent)' : 'var(--tx-dim)' }}>{m.em} {m.label}</span>)}
      </div>
      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: 16, minHeight: 0 }}>
        <div className="panelc" style={{ display: 'flex', flexDirection: 'column', padding: 14, minHeight: 0 }}>
          <div style={{ display: 'flex', gap: 6, marginBottom: 12 }}>
            {tabs.map(([k, l]) => <button key={k} className={'fchip' + (tab === k ? ' on' : '')} onClick={() => setTab(k)}>{l}</button>)}
            <span style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--tx-dim)', fontWeight: 600, alignSelf: 'center' }}>localhost:5173 ♡</span>
          </div>
          <div style={{ flex: 1, display: 'grid', placeItems: 'center', background: 'var(--bg2)', borderRadius: 18, padding: 16, minHeight: 0, overflow: 'auto' }}>
            <Slot id={'pw-' + p.id} cls="" radius={16} ph="preview de tu tema ♡ (arrastra un anime)" />
          </div>
        </div>
        <div className="panelc" style={{ display: 'flex', flexDirection: 'column', padding: 14, minHeight: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
            <b>🖥️ Terminal del agente</b>
            <span className="tag" style={{ marginLeft: 'auto' }}>{ag.em} {ag.label}</span>
          </div>
          <KawaiiTerminal run={run} />
          <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
            <input className="ta" style={{ minHeight: 0, padding: '9px 14px', borderRadius: 99, flex: 1 }} placeholder="responder al agente… ♡" />
            <button className="btn pri" onClick={() => { setRun(false); setTimeout(() => setRun(true), 60); }}>▶</button>
          </div>
        </div>
      </div>
      <style>{`#pw-${p.id}{width:100%;height:${tab === 'mobile' ? '320px' : '300px'};max-width:${tab === 'mobile' ? '280px' : 'none'};}`}</style>
    </div>
  );
}

/* ---- Market ---- */
function Market() {
  const [q, setQ] = useState('');
  const [done, setDone] = useState(false);
  const [load, setLoad] = useState(false);
  const go = () => { setLoad(true); setDone(false); setTimeout(() => { setLoad(false); setDone(true); }, 1200); };
  const rows = [['Dental clinic landing', '$39', '★4.8', '1,240', 'alta'], ['Booking + calendar', '$49', '★4.9', '2,100', 'alta'], ['Multipurpose business', '$29', '★4.4', '8,400', 'saturada']];
  return (
    <div className="page fade">
      <h2 className="sec">🌷 Market Analyzer <span style={{ fontFamily: 'var(--jp)', fontSize: 14, color: 'var(--tx-dim)' }}>市場分析</span></h2>
      <div className="panelc" style={{ display: 'flex', gap: 10, marginBottom: 18 }}>
        <input className="ta" style={{ minHeight: 0, padding: '11px 16px', borderRadius: 99 }} value={q} onChange={e => setQ(e.target.value)} placeholder='Nicho a investigar — ej: "café de gatitos" 🐱' />
        <button className="btn pri" onClick={go}>{load ? '🔎 buscando…' : '🔎 Analizar'}</button>
      </div>
      {load && <div className="panelc" style={{ textAlign: 'center', color: 'var(--accent)', fontWeight: 700 }}>✨ consultando ThemeForest · Creative Market · Gumroad… ✨</div>}
      {done && (
        <div className="fade" style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: 16 }}>
          <div className="panelc" style={{ padding: 0, overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13.5 }}>
              <thead><tr style={{ background: 'var(--bg2)' }}>{['Template', 'Precio', 'Rating', 'Ventas', 'Competencia'].map((h, i) => <th key={h} style={{ textAlign: i === 0 ? 'left' : 'right', padding: '12px 16px', color: 'var(--tx-dim)', fontWeight: 700 }}>{h}</th>)}</tr></thead>
              <tbody>{rows.map((r, i) => <tr key={i} style={{ borderTop: '2px dashed var(--line)' }}>
                <td style={{ padding: '12px 16px', fontWeight: 600 }}>{r[0]}</td>
                <td style={{ textAlign: 'right', padding: '12px 16px', color: 'var(--p3)', fontWeight: 700 }}>{r[1]}</td>
                <td style={{ textAlign: 'right', padding: '12px 16px', color: 'var(--p4)', fontWeight: 700 }}>{r[2]}</td>
                <td style={{ textAlign: 'right', padding: '12px 16px', color: 'var(--tx-dim)', fontWeight: 600 }}>{r[3]}</td>
                <td style={{ textAlign: 'right', padding: '12px 16px' }}><span className="tag" style={{ color: r[4] === 'alta' ? 'var(--p3)' : 'var(--accent)' }}>{r[4]}</span></td>
              </tr>)}</tbody>
            </table>
          </div>
          <div className="panelc" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--tx-dim)' }}>VEREDICTO ♡</div>
            <div style={{ fontFamily: 'var(--cute)', fontSize: 30, color: 'var(--p3)', margin: '8px 0' }}>¡FORJAR! 🔨</div>
            <div style={{ fontSize: 13, color: 'var(--tx-dim)', fontWeight: 600, lineHeight: 1.6 }}>Demanda alta, sweet-spot <b style={{ color: 'var(--accent)' }}>$45–55</b>. Diferénciate con booking integrado.</div>
          </div>
        </div>
      )}
      {!done && !load && <div className="panelc" style={{ textAlign: 'center', color: 'var(--tx-dim)', fontWeight: 600 }}>introduce un nicho para empezar 🌸</div>}
    </div>
  );
}

/* ---- Licensing ---- */
function Licensing() {
  const [pr, setPr] = useState('lemon');
  const provs = [['lemon', 'Lemon Squeezy', '🍋'], ['polar', 'Polar', '🐻‍❄️'], ['paddle', 'Paddle', '🚣'], ['custom', 'Custom', '🌟']];
  return (
    <div className="page fade" style={{ maxWidth: 900 }}>
      <h2 className="sec">🔑 Licencias <span style={{ fontFamily: 'var(--jp)', fontSize: 14, color: 'var(--tx-dim)' }}>認可</span></h2>
      <div className="panelc" style={{ marginBottom: 18 }}>
        <div style={{ fontWeight: 700, marginBottom: 12 }}>Proveedor 💝</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 10 }}>
          {provs.map(([k, l, e]) => <button key={k} className={'tile' + (pr === k ? ' on' : '')} onClick={() => setPr(k)} style={{ textAlign: 'center' }}><div style={{ fontSize: 24 }}>{e}</div><div style={{ fontWeight: 700, fontSize: 13.5, marginTop: 6 }}>{l}</div></button>)}
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div className="panelc">
          <div style={{ fontWeight: 700, marginBottom: 12 }}>Config ⚙️</div>
          {[['Store ID', 'store_8f2a9c'], ['Product ID', 'prod_kawaii_01'], ['API key', '••••••••3f7a']].map(([l, v]) => (
            <div key={l} style={{ marginBottom: 11 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--tx-dim)', marginBottom: 4 }}>{l}</div>
              <div style={{ background: 'var(--bg2)', borderRadius: 12, padding: '9px 13px', fontWeight: 600, fontSize: 13 }}>{v}</div>
            </div>
          ))}
          <button className="btn pri" style={{ marginTop: 6 }}>💝 Cablear en proyecto</button>
        </div>
        <div className="panelc">
          <div style={{ fontWeight: 700, marginBottom: 12 }}>Validador · license.ts 🌸</div>
          <div style={{ background: 'var(--bg2)', borderRadius: 14, padding: 14, fontSize: 12.5, lineHeight: 1.8, fontFamily: 'var(--font)', color: 'var(--tx-dim)' }}>
            <div><b style={{ color: 'var(--accent2)' }}>export async function</b> <b style={{ color: 'var(--p3)' }}>validate</b>(key) {'{'}</div>
            <div>&nbsp;&nbsp;<b style={{ color: 'var(--accent2)' }}>const</b> r = await fetch(API);</div>
            <div>&nbsp;&nbsp;<b style={{ color: 'var(--accent2)' }}>return</b> r.valid; {'}'}</div>
          </div>
          <div style={{ marginTop: 12, color: 'var(--p3)', fontWeight: 700, fontSize: 13 }}>✓ Validación activa · 256-bit ♡</div>
        </div>
      </div>
    </div>
  );
}

/* ---- Modals ---- */
function Modal({ title, jp, onClose, children, w = 560 }) {
  useEffect(() => { const h = e => e.key === 'Escape' && onClose(); window.addEventListener('keydown', h); return () => window.removeEventListener('keydown', h); }, []);
  return (
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, zIndex: 300, background: 'rgba(107,74,94,0.32)', backdropFilter: 'blur(5px)', display: 'grid', placeItems: 'center', padding: 24 }}>
      <div className="panelc fade" onClick={e => e.stopPropagation()} style={{ width: `min(${w}px,94vw)`, maxHeight: '86vh', overflowY: 'auto' }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
          <div><div style={{ fontFamily: 'var(--cute)', fontSize: 19 }}>{title}</div><div style={{ fontFamily: 'var(--jp)', fontSize: 12, color: 'var(--tx-dim)' }}>{jp}</div></div>
          <button className="btn" style={{ marginLeft: 'auto', padding: '6px 12px' }} onClick={onClose}>✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}
function DeployModal({ onClose }) {
  const [t, setT] = useState('netlify'); const [phase, setPhase] = useState('idle'); const [log, setLog] = useState([]);
  const go = () => { setPhase('go'); setLog([]); const steps = ['⟳ npm run build …', '✓ build OK · 1.2 MB 🌸', `⟳ subiendo a ${t} …`, '✓ ¡desplegado! ✨', '◤ LIVE ♡']; let i = 0; const tick = () => { if (i >= steps.length) { setPhase('done'); return; } setLog(l => [...l, steps[i]]); i++; setTimeout(tick, 550); }; tick(); };
  return (
    <Modal title="🚀 Deploy demo" jp="展開" onClose={onClose}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 16 }}>
        {DEPLOY_TARGETS.map(d => <button key={d.id} className={'tile' + (t === d.id ? ' on' : '')} disabled={phase !== 'idle'} onClick={() => setT(d.id)} style={{ display: 'flex', alignItems: 'center', gap: 8 }}><span style={{ fontSize: 18 }}>{d.em}</span><b style={{ fontSize: 14 }}>{d.label}</b></button>)}
      </div>
      {phase === 'idle' ? <button className="btn pri" style={{ width: '100%', justifyContent: 'center' }} onClick={go}>🚀 Deploy a {DEPLOY_TARGETS.find(d => d.id === t).label}</button>
        : <div style={{ background: 'var(--bg2)', borderRadius: 14, padding: 14, fontWeight: 600, fontSize: 13, lineHeight: 1.9, minHeight: 110 }}>{log.map((l, i) => <div key={i} style={{ color: l.startsWith('✓') || l.startsWith('◤') ? 'var(--p3)' : 'var(--tx-dim)' }}>{l}</div>)}{phase === 'done' && <div style={{ color: 'var(--accent)', marginTop: 8 }}>→ https://{t}-aurora.app ♡</div>}</div>}
    </Modal>
  );
}
function BuildModal({ onClose }) {
  const [zip, setZip] = useState(false);
  const ok = PREFLIGHT.filter(p => p.ok).length;
  return (
    <Modal title="✅ Pre-flight & ZIP" jp="出荷検査" onClose={onClose}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}><span style={{ color: 'var(--tx-dim)', fontWeight: 600 }}>Checklist marketplace</span><span className="tag" style={{ color: 'var(--p3)' }}>{ok}/{PREFLIGHT.length} OK ♡</span></div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 7, marginBottom: 16 }}>
        {PREFLIGHT.map((c, i) => <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 9, background: 'var(--bg2)', borderRadius: 12, padding: '9px 13px', fontWeight: 600, fontSize: 13.5 }}><span>{c.ok ? '💚' : '💛'}</span><span style={{ flex: 1 }}>{c.l}</span>{c.n && <span style={{ color: 'var(--tx-dim)', fontSize: 12 }}>{c.n}</span>}</div>)}
      </div>
      {!zip ? <button className="btn pri" style={{ width: '100%', justifyContent: 'center' }} onClick={() => setZip(true)}>📦 Build ZIP para marketplace</button>
        : <div className="fade" style={{ background: 'var(--bg2)', borderRadius: 14, padding: 16 }}><b style={{ color: 'var(--p3)' }}>💚 aurora-kawaii.zip</b><div style={{ color: 'var(--tx-dim)', fontWeight: 600, fontSize: 13, marginTop: 8 }}>312 archivos · 8.4 MB → <b style={{ color: 'var(--accent)' }}>2.1 MB</b> (75% ♡)<br /><span style={{ fontSize: 11.5 }}>excluye node_modules · .env · context/ · reference/</span></div><button className="btn" style={{ marginTop: 12 }}>⬇ Descargar</button></div>}
    </Modal>
  );
}
function RefModal({ onClose }) {
  const [n, setN] = useState(0); const [done, setDone] = useState(false);
  const lines = [{ c: '#7fb8ff', s: '🩵 Analizando referencia · Claude-chan' }, { c: 'var(--tx-dim)', s: 'Detectado: Next.js 14 + Tailwind + shadcn/ui' }, { c: 'var(--tx-dim)', s: 'Layout: hero split · bento 6 · pricing 3-tier' }, { c: 'var(--p4)', s: '⚠ imágenes propietarias → reemplazar por anime ♡' }, { c: 'var(--accent)', s: '¿Mantengo el pricing o propongo algo original?' }];
  useEffect(() => { if (n >= lines.length) { setDone(true); return; } const t = setTimeout(() => setN(n + 1), 420); return () => clearTimeout(t); }, [n]);
  return (
    <Modal title="🔎 Análisis de referencia" jp="参照分析" onClose={onClose} w={620}>
      <div style={{ background: 'var(--bg2)', borderRadius: 14, padding: 14, fontWeight: 600, fontSize: 13, lineHeight: 1.9, minHeight: 140 }}>
        {lines.slice(0, n).map((l, i) => <div key={i} style={{ color: l.c }}>{l.s}</div>)}
        {!done && <span style={{ color: 'var(--accent)' }}>▊ streaming…</span>}
      </div>
      <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
        <input className="ta" style={{ minHeight: 0, padding: '9px 14px', borderRadius: 99, flex: 1 }} placeholder="responder… ♡" disabled={!done} />
        <button className="btn pri" onClick={onClose}>💾 Guardar</button>
      </div>
    </Modal>
  );
}

/* ---- Command palette ---- */
function Palette({ open, onClose, onNav, onOpenProject }) {
  const [q, setQ] = useState(''); const [sel, setSel] = useState(0); const inp = useRef(null);
  const actions = [
    ...NAV.map(n => ({ id: n.id, label: 'Ir a ' + n.label, em: n.em, kind: 'nav' })),
    ...PROJECTS.map(p => ({ id: p.id, label: 'Abrir · ' + p.name, em: '📂', kind: 'proj', p })),
    { id: 'deploy', label: 'Deploy demo', em: '🚀', kind: 'cmd' }, { id: 'zip', label: 'Build ZIP', em: '📦', kind: 'cmd' },
  ];
  const f = actions.filter(a => a.label.toLowerCase().includes(q.toLowerCase()));
  useEffect(() => { if (open) { setQ(''); setSel(0); setTimeout(() => inp.current?.focus(), 30); } }, [open]);
  useEffect(() => { setSel(0); }, [q]);
  const run = a => { if (!a) return; if (a.kind === 'proj') onOpenProject(a.p); else onNav(a.id); onClose(); };
  if (!open) return null;
  return (
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, zIndex: 320, background: 'rgba(107,74,94,0.3)', backdropFilter: 'blur(5px)', display: 'grid', placeItems: 'start center', paddingTop: '12vh' }}>
      <div className="panelc fade" onClick={e => e.stopPropagation()} style={{ width: 'min(560px,92vw)', padding: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', borderBottom: '2px dashed var(--line)', marginBottom: 8 }}>
          <span style={{ fontSize: 18 }}>🔍</span>
          <input ref={inp} value={q} onChange={e => setQ(e.target.value)} onKeyDown={e => { if (e.key === 'ArrowDown') { e.preventDefault(); setSel(s => Math.min(f.length - 1, s + 1)); } else if (e.key === 'ArrowUp') { e.preventDefault(); setSel(s => Math.max(0, s - 1)); } else if (e.key === 'Enter') run(f[sel]); }} placeholder="Buscar acciones, proyectos… ♡" style={{ flex: 1, border: 'none', background: 'none', outline: 'none', fontFamily: 'var(--font)', fontSize: 15, color: 'var(--tx)' }} />
          <span className="tag">ESC</span>
        </div>
        <div style={{ maxHeight: 340, overflowY: 'auto' }}>
          {f.map((a, i) => <div key={a.id + a.kind} onMouseEnter={() => setSel(i)} onClick={() => run(a)} style={{ display: 'flex', alignItems: 'center', gap: 11, padding: '10px 13px', borderRadius: 14, cursor: 'pointer', background: i === sel ? 'linear-gradient(135deg,var(--accent),var(--accent2))' : 'transparent', color: i === sel ? '#fff' : 'var(--tx)', fontWeight: 600 }}><span style={{ fontSize: 16 }}>{a.em}</span>{a.label}</div>)}
          {f.length === 0 && <div style={{ padding: 24, textAlign: 'center', color: 'var(--tx-dim)', fontWeight: 600 }}>sin coincidencias 🥺</div>}
        </div>
      </div>
    </div>
  );
}

/* ---- App shell ---- */
const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "palette": ["#ff8fc7", "#b9a3ff"],
  "dark": false,
  "sparkles": true
}/*EDITMODE-END*/;

const PALETTES = {
  'Sakura 🌸': ['#ff8fc7', '#b9a3ff'],
  'Lavanda 💜': ['#b9a3ff', '#8fb8ff'],
  'Matcha 🍵': ['#7fc99a', '#cfe6a8'],
  'Durazno 🍑': ['#ff9e7d', '#ffd36e'],
  'Cielo 🩵': ['#7fd4ff', '#b9a3ff'],
};

/* ---- Intro kawaii (boot) ---- */
function KawaiiBoot({ onDone }) {
  const steps = [
    { s: 'despertando a las mascotas IA', e: '🐾' },
    { s: 'esponjando los cojines pastel', e: '🌸' },
    { s: 'cargando sparkles mágicos', e: '✨' },
    { s: 'calentando la forja kawaii', e: '🔨' },
    { s: 'preparando el té matcha', e: '🍵' },
    { s: '¡todo listo! ♡', e: '💖' },
  ];
  const [n, setN] = useState(0);
  const [fade, setFade] = useState(false);
  useEffect(() => {
    if (n < steps.length) {
      const t = setTimeout(() => setN(n + 1), n === 0 ? 280 : 360 + Math.random() * 160);
      return () => clearTimeout(t);
    }
    const a = setTimeout(() => setFade(true), 520);
    const b = setTimeout(onDone, 1080);
    return () => { clearTimeout(a); clearTimeout(b); };
  }, [n]);
  const pct = Math.round((n / steps.length) * 100);
  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 900, display: 'grid', placeItems: 'center',
      background: 'radial-gradient(circle at 30% 20%,#ffeaf4,#fff5fa 60%)',
      transition: 'opacity .5s ease', opacity: fade ? 0 : 1, pointerEvents: fade ? 'none' : 'auto',
    }}>
      <div style={{ textAlign: 'center', position: 'relative', zIndex: 2, width: 'min(420px,86vw)' }}>
        <div style={{ fontSize: 78, animation: 'bounce 1.4s ease-in-out infinite', filter: 'drop-shadow(0 8px 18px rgba(255,143,199,.5))' }}>🌸</div>
        <div style={{ fontFamily: 'var(--cute)', fontSize: 32, color: 'var(--accent)', marginTop: 6, textShadow: '2px 2px 0 #fff,3px 3px 0 var(--line)' }}>ThemeForge</div>
        <div style={{ fontFamily: 'var(--jp)', color: 'var(--tx-dim)', letterSpacing: '.36em', fontSize: 13, marginTop: 4 }}>かわいいビルダー</div>
        {/* loading line */}
        <div style={{ minHeight: 26, marginTop: 26, fontWeight: 700, color: 'var(--tx)', fontSize: 15 }}>
          {n < steps.length
            ? <span className="fade" key={n}>{steps[n].e} {steps[n].s}<span style={{ animation: 'blinkk 1s infinite' }}> …</span></span>
            : <span>{steps[steps.length - 1].e} {steps[steps.length - 1].s}</span>}
        </div>
        {/* progress bar */}
        <div style={{ height: 12, background: '#ffffff', border: '2px solid var(--line)', borderRadius: 99, marginTop: 18, overflow: 'hidden', boxShadow: 'var(--shadow)' }}>
          <div style={{ height: '100%', width: pct + '%', borderRadius: 99, background: 'linear-gradient(90deg,var(--accent),var(--accent2))', transition: 'width .4s cubic-bezier(.3,1.4,.5,1)' }} />
        </div>
        <div style={{ marginTop: 8, fontFamily: 'var(--font)', fontWeight: 700, color: 'var(--tx-dim)', fontSize: 13 }}>{pct}% ♡</div>
        {/* mascotas peeking */}
        <div style={{ marginTop: 22, display: 'flex', gap: 14, justifyContent: 'center' }}>
          {Object.values(AGENTS).map((a, i) => (
            <span key={i} style={{ fontSize: 24, animation: `bounce 1.4s ease-in-out ${i * 0.15}s infinite` }}>{a.em}</span>
          ))}
        </div>
      </div>
      <style>{`
        @keyframes bounce{0%,100%{transform:translateY(0)}50%{transform:translateY(-12px)}}
        @keyframes blinkk{0%,49%{opacity:1}50%,100%{opacity:.2}}
      `}</style>
    </div>
  );
}

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [booted, setBooted] = useState(false);
  const [route, setRoute] = useState('gallery');
  const [project, setProject] = useState(null);
  const [modal, setModal] = useState(null);
  const [palette, setPalette] = useState(false);
  useEffect(() => {
    const r = document.documentElement.style;
    const [a, b] = Array.isArray(t.palette) ? t.palette : ['#ff8fc7', '#b9a3ff'];
    r.setProperty('--accent', a); r.setProperty('--accent2', b);
    r.setProperty('--sparkle', t.sparkles ? '1' : '0');
    document.body.classList.toggle('dark', t.dark);
  }, [t]);
  useEffect(() => { startSparkles(); }, []);
  useEffect(() => {
    const h = e => { if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); setPalette(o => !o); } };
    window.addEventListener('keydown', h); return () => window.removeEventListener('keydown', h);
  }, []);

  const nav = (id) => { setProject(null); setRoute(id); };
  const openProject = (p) => { setProject(p); setRoute('project'); };
  const titles = { gallery: '🖼️ Galería de proyectos', new: '✨ Nuevo proyecto', cost: '💰 Coste de IA', compare: '⚔️ Comparar agentes', operator: '🚀 Mission Control', market: '🌷 Market Analyzer', licensing: '🔑 Licencias', settings: '🎨 Ajustes', project: '📂 ' + (project ? project.name : '') };

  return (
    <div className="app">
      {!booted && <KawaiiBoot onDone={() => setBooted(true)} />}
      <div className="side">
        <div className="brand">🌸 ThemeForge<small>かわいいビルダー · kawaii</small></div>
        <div className="nav">
          {NAV.map(n => (
            <button key={n.id} className={'navi' + (route === n.id ? ' on' : '')} onClick={() => nav(n.id)}>
              <span className="ico">{n.em}</span> {n.label} <span className="jp">{n.jp}</span>
            </button>
          ))}
        </div>
        <div className="agents">
          <div className="lbl">Mascotas IA</div>
          {Object.entries(AGENTS).map(([k, a], i) => (
            <div className="agrow" key={k}><span className="em">{a.em}</span> {a.label}<span className="dot" style={{ background: i < 2 ? a.color : 'var(--line)', boxShadow: i < 2 ? `0 0 6px ${a.color}` : 'none' }} /></div>
          ))}
        </div>
      </div>

      <div className="main">
        <div className="bar">
          <h1 className="h1">{titles[route]}</h1>
          <div className="search" onClick={() => setPalette(true)} style={{ cursor: 'pointer' }}>🔍 <input placeholder="Buscar…  ⌘K" readOnly style={{ cursor: 'pointer' }} /></div>
          <button className="btn pri" onClick={() => nav('new')}>✨ Nuevo</button>
        </div>
        {route === 'gallery' && <Gallery onOpen={openProject} />}
        {route === 'new' && <NewProject />}
        {route === 'cost' && <Cost />}
        {route === 'compare' && <Compare />}
        {route === 'operator' && <Operator />}
        {route === 'market' && <Market />}
        {route === 'licensing' && <Licensing />}
        {route === 'settings' && <Settings />}
        {route === 'project' && <ProjectWindow p={project || PROJECTS[0]} onBack={() => nav('gallery')} onDeploy={() => setModal('deploy')} onBuild={() => setModal('build')} onRef={() => setModal('ref')} />}
      </div>

      {modal === 'deploy' && <DeployModal onClose={() => setModal(null)} />}
      {modal === 'build' && <BuildModal onClose={() => setModal(null)} />}
      {modal === 'ref' && <RefModal onClose={() => setModal(null)} />}
      <Palette open={palette} onClose={() => setPalette(false)} onNav={nav} onOpenProject={openProject} />

      <TweaksPanel title="Tweaks">
        <TweakSection label="Colores ♡" />
        <TweakColor label="Paleta" value={t.palette} options={Object.values(PALETTES)} onChange={v => setTweak('palette', v)} />
        <TweakToggle label="Modo noche 🌙" value={t.dark} onChange={v => setTweak('dark', v)} />
        <TweakSection label="Magia ✨" />
        <TweakToggle label="Sparkles flotantes" value={t.sparkles} onChange={v => setTweak('sparkles', v)} />
      </TweaksPanel>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
