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

const PROJECTS = (typeof window !== 'undefined' && window.__TF_DATA__ && window.__TF_DATA__.projects && window.__TF_DATA__.projects.length) ? window.__TF_DATA__.projects : [
  { id: 'k-aurora', name: 'Aurora SaaS', jp: 'オーロラ', type: 'SaaS Landing', agent: 'claude', status: 'live', cost: 4.82, tags: ['next', 'tailwind'], commits: 47, updated: 'hace 3 min' },
  { id: 'k-nordic', name: 'Nordic Forge', jp: '北欧', type: 'Agencia creativa', agent: 'codex', status: 'building', cost: 2.10, tags: ['astro', 'gsap'], commits: 23, updated: 'hace 12 min' },
  { id: 'k-meridian', name: 'Meridian Shop', jp: '商店', type: 'E-commerce', agent: 'gemini', status: 'live', cost: 7.34, tags: ['shopify', 'remix'], commits: 89, updated: 'hace 1 h' },
  { id: 'k-flux', name: 'Flux Admin', jp: '管理', type: 'Dashboard', agent: 'opencode', status: 'draft', cost: 0.41, tags: ['laravel', 'vue'], commits: 8, updated: 'hace 5 h' },
  { id: 'k-zen', name: 'Zen Clinic', jp: '診療', type: 'Clínica · booking', agent: 'claude', status: 'live', cost: 3.95, tags: ['wp', 'acf'], commits: 34, updated: 'ayer' },
  { id: 'k-pixel', name: 'Pixel Arcade', jp: '遊技', type: 'Landing · game', agent: 'codex', status: 'archived', cost: 1.22, tags: ['tauri', 'react'], commits: 19, updated: 'hace 3 días' },
];

const STACKS = (typeof window !== 'undefined' && window.__TF_DATA__ && window.__TF_DATA__.stacks && window.__TF_DATA__.stacks.length) ? window.__TF_DATA__.stacks.map(s => ({ k: s.key, label: s.label, jp: s.jp || '', em: '🌷', cat: s.cat })) : [
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

const MCP_SERVERS = (typeof window !== 'undefined' && window.__TF_DATA__ && window.__TF_DATA__.mcp && window.__TF_DATA__.mcp.length) ? window.__TF_DATA__.mcp.map(m => ({ id: m.id, label: m.label, always: m.always, em: m.always ? '💝' : '🎀', desc: m.desc, lic: m.lic })) : [
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
  const [projects, setProjects] = useState(PROJECTS);  // galería en vivo
  useEffect(() => {
    if (window.tfBridge && window.tfBridge.list_projects)
      window.tfBridge.list_projects().then(j => { try { const a = JSON.parse(j); if (Array.isArray(a)) setProjects(a); } catch (e) {} });
  }, []);
  const fl = ['all', 'live', 'building', 'draft', 'archived'];
  const list = projects.filter(p => f === 'all' || p.status === f);
  const liveN = projects.filter(p => p.status === 'live').length;
  const buildingN = projects.filter(p => p.status === 'building').length;
  const totalCost = projects.reduce((s, p) => s + (p.cost || 0), 0);
  return (
    <div className="page fade">
      <div className="stats">
        {[['🎀', String(projects.length), 'proyectos'], ['💸', '$' + totalCost.toFixed(2), 'cómputo IA'], ['🌟', String(liveN), 'publicados'], ['🔨', String(buildingN), 'forjando ahora']].map(([e, n, l]) => (
          <div className="stat" key={l}><div className="em">{e}</div><div className="n">{n}</div><div className="l">{l}</div></div>
        ))}
      </div>
      <div className="filters">
        {fl.map(x => <button key={x} className={'fchip' + (f === x ? ' on' : '')} onClick={() => setF(x)}>{x === 'all' ? '✨ todos' : STATUS[x].em + ' ' + STATUS[x].label}</button>)}
      </div>
      <div className="grid">{list.map(p => <ProjectCard key={p.id} p={p} onOpen={onOpen} />)}</div>
      {!list.length && <div style={{ color: 'var(--tx-dim)', fontWeight: 600, padding: 30, textAlign: 'center' }}>aún no hay proyectos — crea uno en «✨ Nuevo» ♡</div>}
    </div>
  );
}

/* ---- New project (vibe scaffolder kawaii · 4 modos + extras, paridad total) ---- */
const K_MODES = [
  { k: 'scratch', label: 'Desde cero', jp: '新規', em: '✨', desc: 'Scaffold oficial del stack + agente IA desde cero.' },
  { k: 'recreate', label: 'Recreate ref', jp: '再現', em: '🪄', desc: 'Carpeta / .zip / URL / Figma — la IA estudia y reimplementa.' },
  { k: 'adopt', label: 'Adopt local', jp: '採用', em: '📂', desc: 'Export de claude.ai/design, v0.dev o Figma Make.' },
  { k: 'repo', label: 'Existing repo', jp: '既存', em: '🐙', desc: 'Continúa un repo de GitHub existente.' },
];
const K_REF_KINDS = [['folder', 'Carpeta local'], ['zip', 'Archivo .zip'], ['url', 'URL de demo'], ['figma', 'Figma (frame)']];
function KToggle({ on, onClick }) {
  return <button onClick={onClick} style={{ cursor: 'pointer', width: 40, height: 23, borderRadius: 99, padding: 2, border: 'none', background: on ? 'var(--accent)' : 'rgba(0,0,0,0.12)', boxShadow: on ? '0 0 10px var(--accent)' : 'none', transition: 'all .18s' }}><span style={{ display: 'block', width: 19, height: 19, borderRadius: 99, background: '#fff', transform: on ? 'translateX(17px)' : 'none', transition: 'transform .18s' }} /></button>;
}
function KCheck({ label, sub, on, onToggle }) {
  return <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '11px 0', borderBottom: '2px dashed var(--line)' }}><div style={{ flex: 1 }}><div style={{ fontSize: 13.5, fontWeight: 700 }}>{label}</div>{sub && <div style={{ fontSize: 11.5, marginTop: 3, color: 'var(--tx-dim)', fontWeight: 600 }}>{sub}</div>}</div><KToggle on={on} onClick={onToggle} /></div>;
}
function NewProject({ onAnalyze, onLaunch }) {
  const [vibe, setVibe] = useState('');
  const [pname, setPname] = useState('');
  const [stack, setStack] = useState((typeof STACKS !== 'undefined' && STACKS[0]) ? STACKS[0].k : 'next');
  const [agent, setAgent] = useState('claude');
  const [type, setType] = useState('');  // vacío = «(Sin tipo específico)» → no impone formato Envato
  const [mode, setMode] = useState('scratch');
  const [refKind, setRefKind] = useState('folder');
  const [refVal, setRefVal] = useState('');
  const [repoId, setRepoId] = useState('');
  const [thinking, setThinking] = useState(false);
  const [done, setDone] = useState(false);
  const [genPrompt, setGenPrompt] = useState('');
  const [openCats, setOpenCats] = useState({});
  const [opts, setOpts] = useState({ autoskills: true, uipro: true, mcp: true, docs: true, postgres: false, licensing: false, licensing_gh: false, licensing_force: false });
  const tog = (k) => setOpts(o => ({ ...o, [k]: !o[k] }));
  const go = () => {
    setThinking(true); setDone(false);
    if (window.tfBridge && window.tfBridge.suggest_stack && (vibe || '').trim()) {
      const onRes = (j) => { let r = {}; try { r = JSON.parse(j); } catch (e) {}
        if (r.stack && STACKS.find(s => s.k === r.stack)) setStack(r.stack);
        if (r.template_type) setType(r.template_type);
        setGenPrompt(r.prompt || r.dev_prompt || ('Build: ' + vibe));
        setThinking(false); setDone(true);
        try { window.tfBridge.suggest_result.disconnect(onRes); } catch (e) {} };
      if (window.tfBridge.suggest_result && window.tfBridge.suggest_result.connect) window.tfBridge.suggest_result.connect(onRes);
      window.tfBridge.suggest_stack(vibe); return;
    }
    setTimeout(() => { setThinking(false); setDone(true); }, 1300);
  };
  const examine = () => {
    if (!window.tfBridge) return;
    const picker = refKind === 'zip' ? window.tfBridge.pick_file : window.tfBridge.pick_folder;
    if (!picker) return;
    picker().then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {} if (!r.path) return; setRefVal(r.path);
      if (window.tfBridge.detect_ref_stack) window.tfBridge.detect_ref_stack(r.path).then(dj => { let d = {}; try { d = JSON.parse(dj); } catch (e) {} if (d.stack && STACKS.find(s => s.k === d.stack)) setStack(d.stack); }); });
  };
  const forge = () => {
    if (mode === 'repo') {
      const rid = (repoId || '').trim();
      if (!rid || rid.indexOf('/') < 0) { alert('Indica el repo como owner/repo o una URL de GitHub. 🥺'); return; }
      const repoName = rid.replace(/\.git$/, '').replace(/\/$/, '').split('/').pop();
      onLaunch && onLaunch({ name: repoName, stack: 'none', agent, type, mode: 'existing', niche: vibe, existing_repo: rid, opts }); return;
    }
    const name = (pname || '').trim() || (vibe || '').trim().slice(0, 42) || type || 'Untitled Forge';
    if (!(pname || '').trim() && !confirm('Sin nombre — se usará «' + name + '». ¿Continuar? ♡')) return;
    onLaunch && onLaunch({ name, stack, agent, type, mode, niche: vibe, reference: refVal, reference_kind: refKind, opts });
  };
  const groups = {}; STACKS.forEach(s => { const c = s.cat || 'Otros'; (groups[c] = groups[c] || []).push(s); });
  const selCat = (STACKS.find(s => s.k === stack) || {}).cat;
  return (
    <div className="page fade" style={{ maxWidth: 980 }}>
      <h2 className="sec">✨ Vibe Scaffolder <span style={{ fontFamily: 'var(--jp)', fontSize: 14, color: 'var(--tx-dim)' }}>新規制作</span></h2>
      <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: 18 }}>
        <div className="panelc">
          <div style={{ fontWeight: 700, marginBottom: 10 }}>Cuéntame qué quieres crear 🌷</div>
          <textarea className="ta" value={vibe} onChange={e => setVibe(e.target.value)} placeholder='Ej: "Landing kawaii para cafetería de gatitos, pastel y redondito…"' />
          <button className="btn pri" style={{ marginTop: 14 }} onClick={go}>{thinking ? '✨ pensando…' : '✨ Pre-rellenar con IA'}</button>
          {thinking && <span style={{ marginLeft: 10, color: 'var(--accent)', fontWeight: 700 }}>{(AGENTS[agent] || {}).em} analizando…</span>}
          {done && (
            <div className="fade" style={{ marginTop: 16, background: 'var(--bg2)', borderRadius: 16, padding: 14, fontSize: 13.5, lineHeight: 1.6 }}>
              <b>Prompt generado ♡</b><br />{genPrompt || ('Build a production-ready ' + (type || 'producto') + ' usando ' + (STACKS.find(s => s.k === stack) || { label: stack }).label + '. ' + (vibe || 'Diseño kawaii pastel, redondeado, mascota animada.'))}
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
          <div style={{ fontWeight: 700, margin: '16px 0 8px' }}>Tipo de template 🎀</div>
          <input className="ta" value={type} onChange={e => setType(e.target.value)} placeholder="SaaS Landing · E-commerce · Dashboard…" style={{ minHeight: 0, height: 40, borderRadius: 14 }} />
        </div>
      </div>

      {/* MODO */}
      <h2 className="sec" style={{ margin: '26px 0 14px' }}>🌈 Modo <span style={{ fontFamily: 'var(--jp)', fontSize: 14, color: 'var(--tx-dim)' }}>方式</span></h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 10 }}>
        {K_MODES.map(m => (
          <button key={m.k} className={'tile' + (mode === m.k ? ' on' : '')} onClick={() => setMode(m.k)} style={{ textAlign: 'left', display: 'flex', gap: 12 }}>
            <span style={{ fontSize: 22 }}>{m.em}</span>
            <span><span style={{ fontWeight: 700, fontSize: 14 }}>{m.label} <span style={{ fontFamily: 'var(--jp)', fontSize: 11, color: 'var(--tx-dim)' }}>{m.jp}</span></span><br /><span style={{ fontSize: 12, color: 'var(--tx-dim)', fontWeight: 600, lineHeight: 1.5 }}>{m.desc}</span></span>
          </button>
        ))}
      </div>
      {(mode === 'recreate' || mode === 'adopt') && (
        <div className="panelc fade" style={{ marginTop: 12 }}>
          <div style={{ fontWeight: 700, marginBottom: 12 }}>Referencia 🔎 <span style={{ fontFamily: 'var(--jp)', fontSize: 12, color: 'var(--tx-dim)' }}>参照</span></div>
          {mode === 'recreate' && (
            <div style={{ display: 'flex', gap: 6, marginBottom: 12, flexWrap: 'wrap' }}>
              {K_REF_KINDS.map(([k, l]) => <button key={k} className={'fchip' + (refKind === k ? ' on' : '')} style={{ cursor: 'pointer' }} onClick={() => setRefKind(k)}>{l}</button>)}
            </div>
          )}
          <div style={{ display: 'flex', gap: 10 }}>
            <input className="ta" style={{ minHeight: 0, height: 40, flex: 1, borderRadius: 14 }} value={refVal} onChange={e => setRefVal(e.target.value)} placeholder={refKind === 'url' ? 'https://demo-template.com' : refKind === 'figma' ? 'figma.com/file/…?node-id=' : 'Ruta o examinar…'} />
            {refKind !== 'url' && refKind !== 'figma' && <button className="btn" onClick={examine}>📂 Examinar</button>}
          </div>
          <div style={{ marginTop: 12, display: 'flex', gap: 10, alignItems: 'center' }}>
            <button className="btn pri" onClick={() => { window.__tfRef = { value: refVal, kind: refKind }; onAnalyze && onAnalyze(); }}>🔎 Analizar con IA</button>
            <span style={{ fontSize: 11.5, color: 'var(--tx-dim)', fontWeight: 600 }}>{refKind === 'figma' ? 'Lee el frame vía MCP figma-context (es tu diseño). ♡' : 'Detecta stack + estudia layout/paleta/tipo, multi-turno. ♡'}</span>
          </div>
        </div>
      )}
      {mode === 'repo' && (
        <div className="panelc fade" style={{ marginTop: 12 }}>
          <div style={{ fontWeight: 700, marginBottom: 10 }}>Repositorio GitHub 🐙</div>
          <input className="ta" style={{ minHeight: 0, height: 40, borderRadius: 14 }} value={repoId} onChange={e => setRepoId(e.target.value)} placeholder="owner/repo o https://github.com/owner/repo" />
          <div style={{ fontSize: 11.5, marginTop: 8, color: 'var(--tx-dim)', fontWeight: 600 }}>No hace falta nombre: se usa el de la repo. gh repo clone con historial intacto. ♡</div>
        </div>
      )}

      {/* STACK (oculto en modo repo) */}
      {mode !== 'repo' && <>
      <h2 className="sec" style={{ margin: '26px 0 14px' }}>🧱 Elige tu stack <span style={{ fontFamily: 'var(--jp)', fontSize: 14, color: 'var(--tx-dim)' }}>基盤 · {STACKS.length}</span></h2>
      {Object.keys(groups).map(cat => {
        const open = openCats[cat] !== undefined ? openCats[cat] : (cat === selCat);
        return (
          <div key={cat} style={{ marginBottom: 10 }}>
            <button onClick={() => setOpenCats(o => ({ ...o, [cat]: !open }))} style={{ width: '100%', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8, background: 'var(--bg2)', border: 'none', borderRadius: 14, padding: '10px 14px', color: 'var(--tx-dim)', textAlign: 'left', fontWeight: 700 }}>
              <span style={{ color: 'var(--accent)', transform: open ? 'rotate(90deg)' : 'none', transition: 'transform .15s', display: 'inline-block', width: 12 }}>▸</span>
              <span style={{ fontSize: 12.5, letterSpacing: '.04em', flex: 1 }}>{cat}</span>
              <span className="tag">{groups[cat].length}</span>
              {groups[cat].some(s => s.k === stack) && <span style={{ width: 7, height: 7, borderRadius: 99, background: 'var(--accent)', boxShadow: '0 0 6px var(--accent)' }} />}
            </button>
            {open && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(150px,1fr))', gap: 10, padding: '10px 2px 4px' }}>
                {groups[cat].map(s => (
                  <button key={s.k} className={'tile' + (stack === s.k ? ' on' : '')} onClick={() => setStack(s.k)}>
                    <div style={{ fontSize: 22 }}>{s.em}</div>
                    <div style={{ fontWeight: 700, fontSize: 14.5, marginTop: 4 }}>{s.label}</div>
                    <div style={{ fontFamily: 'var(--jp)', fontSize: 11, color: 'var(--tx-dim)' }}>{s.jp}</div>
                  </button>
                ))}
              </div>
            )}
          </div>
        );
      })}
      <div className="panelc" style={{ marginTop: 14 }}>
        <div style={{ fontWeight: 700, marginBottom: 8 }}>Nombre del proyecto 🎀 <span style={{ fontFamily: 'var(--jp)', fontSize: 12, color: 'var(--tx-dim)' }}>名前</span></div>
        <input className="ta" value={pname} onChange={e => setPname(e.target.value)} placeholder="Ej: Aurora Dental · ~/Proyectos/themes/<slug>" style={{ minHeight: 0, height: 42, borderRadius: 14 }} />
      </div>
      </>}

      {/* SETUP + EXTRAS */}
      <h2 className="sec" style={{ margin: '26px 0 14px' }}>⚙️ Setup & Extras <span style={{ fontFamily: 'var(--jp)', fontSize: 14, color: 'var(--tx-dim)' }}>基礎</span></h2>
      <div className="panelc" style={{ padding: '6px 20px 14px' }}>
        <KCheck label="✨ npx autoskills" sub="auto-instala skills del stack (a11y/SEO/design) en .claude/skills/" on={opts.autoskills} onToggle={() => tog('autoskills')} />
        <KCheck label="💎 UI/UX Pro Max" sub="shadcn/ui · Aceternity · Magic UI + sistema de diseño" on={opts.uipro} onToggle={() => tog('uipro')} />
        <KCheck label="📡 Pre-configurar MCP servers" sub="genera .mcp.json (filesystem · github · playwright · figma · themeforge…)" on={opts.mcp} onToggle={() => tog('mcp')} />
        <KCheck label="📚 Documentación" sub="documentation/ con guía de instalación + changelog" on={opts.docs} onToggle={() => tog('docs')} />
        <KCheck label="🐘 PostgreSQL en Docker" sub="contenedor postgres:17 + DATABASE_URL en .env (requiere Docker)" on={opts.postgres} onToggle={() => tog('postgres')} />
        <KCheck label="🔑 Licencias (pcreative anti-nulled)" sub="verify-license + setup wizard según la familia del stack" on={opts.licensing} onToggle={() => tog('licensing')} />
        {opts.licensing && <div style={{ paddingLeft: 16, borderLeft: '3px solid var(--accent)', marginLeft: 6 }}>
          <KCheck label="└─ Crear repo gh <org>/<slug>" sub="gh repo create privado tras el scaffold (org en licensing.json)" on={opts.licensing_gh} onToggle={() => tog('licensing_gh')} />
          <KCheck label="└─ Forzar también en adopt / existing" sub="por defecto licensing solo corre en scratch/recreate" on={opts.licensing_force} onToggle={() => tog('licensing_force')} />
        </div>}
      </div>

      <div className="panelc" style={{ marginTop: 14, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontWeight: 600, color: 'var(--tx-dim)' }}><b style={{ color: 'var(--accent)' }}>{mode === 'repo' ? 'repo' : (STACKS.find(s => s.k === stack) || { label: stack }).label}</b> · {(K_MODES.find(m => m.k === mode) || { label: mode }).label} · {(AGENTS[agent] || { label: agent }).label}</span>
        <button className="btn pri" onClick={forge}>🔨 ¡Forjar proyecto!</button>
      </div>
    </div>
  );
}

/* ---- Cost (kawaii donut + bars) ---- */
const COST = (typeof window !== 'undefined' && window.__TF_DATA__ && window.__TF_DATA__.cost && window.__TF_DATA__.cost.by_agent && window.__TF_DATA__.cost.by_agent.length) ? window.__TF_DATA__.cost.by_agent : [{ k: 'claude', v: 12.77 }, { k: 'gemini', v: 7.34 }, { k: 'codex', v: 3.32 }, { k: 'opencode', v: 1.63 }];
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

/* ---- Compare (terminales reales lado a lado) ---- */
function AgentPane({ k, url }) {
  const a = AGENTS[k] || { color: 'var(--accent)', em: '🐾', label: k };
  return (
    <div className="panelc" style={{ padding: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column', minHeight: 320 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px', borderBottom: '2px dashed var(--line)' }}>
        <span style={{ fontSize: 18 }}>{a.em}</span>
        <span style={{ fontSize: 13, fontWeight: 700 }}>{a.label}</span>
        {!url && <span style={{ marginLeft: 'auto', width: 7, height: 7, borderRadius: 99, background: a.color, boxShadow: `0 0 8px ${a.color}` }} />}
      </div>
      {url ? <iframe src={url} style={{ flex: 1, width: '100%', minHeight: 280, border: 'none', background: '#1b1020' }} />
        : <div style={{ padding: 16, flex: 1, color: 'var(--tx-dim)', fontWeight: 600 }}>esperando terminal real… ♡</div>}
    </div>
  );
}
function Compare() {
  const real = !!(window.tfBridge && window.tfBridge.compare);
  const [prompt, setPrompt] = useState('Crea una sección de pricing de 3 tiers con toggle anual');
  const [urls, setUrls] = useState({});
  const [providers, setProviders] = useState([]);
  useEffect(() => {
    if (!real || !window.tfBridge.compare_ready || !window.tfBridge.compare_ready.connect) return;
    const onReady = (j) => { let r = {}; try { r = JSON.parse(j); } catch (e) {} if (r.provider && r.url) setUrls(u => ({ ...u, [r.provider]: r.url })); };
    window.tfBridge.compare_ready.connect(onReady);
    return () => { try { window.tfBridge.compare_ready.disconnect(onReady); } catch (e) {} };
  }, []);
  const go = () => { if (!real || !prompt.trim()) return; setUrls({}); setProviders([]); window.tfBridge.compare(prompt).then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {} setProviders(r.providers || []); }); };
  const shownKeys = providers.length ? providers : Object.keys(AGENTS);
  return (
    <div className="page fade">
      <h2 className="sec">⚔️ Comparar agentes <span style={{ fontFamily: 'var(--jp)', fontSize: 14, color: 'var(--tx-dim)' }}>比較</span></h2>
      <div className="panelc" style={{ display: 'flex', gap: 10, marginBottom: 18 }}>
        <input className="ta" style={{ minHeight: 0, padding: '10px 14px', borderRadius: 99, flex: 1 }} value={prompt} onChange={e => setPrompt(e.target.value)} />
        <button className="btn pri" onClick={go}>{providers.length ? '↻ Re-run' : '▶ ¡Carrera!'}</button>
      </div>
      {!real && <div className="panelc" style={{ textAlign: 'center', color: 'var(--tx-dim)', fontWeight: 600, marginBottom: 16 }}>Compare no disponible (sin puente) 🥺</div>}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {shownKeys.map(k => <AgentPane key={k} k={k} url={urls[k]} />)}
      </div>
    </div>
  );
}

/* ---- Operator (Hermes real) ---- */
function Operator() {
  const op = (window.__TF_DATA__ && window.__TF_DATA__.operator) || {};
  const real = !!(window.tfBridge && window.tfBridge.launch_mission);
  const [missions, setMissions] = useState([]);  // misiones reales (vacío al inicio)
  const launch = () => {
    if (!real) return;
    if (!op.available) { alert('Instala Hermes Agent para usar el Operator. 🐾'); return; }
    const brief = prompt('Describe la misión (ej: «2 variantes Envato de landing dental, stack Astro»):');
    if (!brief) return;
    window.tfBridge.launch_mission(brief);
    setMissions(ms => [{ id: 'm' + ms.length, name: brief.slice(0, 60), agent: 'claude', st: 'corriendo', pct: 0, eta: 'Hermes…' }, ...ms]);
  };
  const running = missions.filter(m => m.pct < 100).length;
  return (
    <div className="page fade">
      <h2 className="sec">🚀 Mission Control <span style={{ fontFamily: 'var(--jp)', fontSize: 14, color: 'var(--tx-dim)' }}>司令室</span>
        <button className="btn pri" style={{ float: 'right' }} onClick={launch}>🐾 Lanzar misión</button></h2>
      <div className="stats" style={{ marginBottom: 22 }}>
        {[['🔨', String(running), 'activas'], ['📋', String(missions.length), 'total'], ['🩵', op.available ? (op.version || 'on') : 'off', 'hermes']].map(([e, n, l]) => (
          <div className="stat" key={l}><div className="em">{e}</div><div className="n">{n}</div><div className="l">{l}</div></div>
        ))}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {missions.length ? missions.map(m => {
          const a = AGENTS[m.agent] || { color: 'var(--accent)', em: '🐾' };
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
        }) : <div className="panelc" style={{ padding: 30, textAlign: 'center', color: 'var(--tx-dim)', fontWeight: 600 }}>aún no hay misiones — pulsa «Lanzar misión» {op.available ? '♡' : '(requiere Hermes)'}</div>}
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

      <h2 className="sec" style={{ margin: '26px 0 14px' }}>🔑 Credenciales <span style={{ fontFamily: 'var(--jp)', fontSize: 14, color: 'var(--tx-dim)' }}>鍵</span></h2>
      <div className="panelc" style={{ padding: '6px 18px 14px' }}>
        {((window.__TF_DATA__ && window.__TF_DATA__.creds) || [{ id: 'anthropic', label: 'Anthropic API key', configured: false }, { id: 'openrouter', label: 'OpenRouter key', configured: false }]).map(cr => (
          <div key={cr.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 0', borderBottom: '2px dashed var(--line)' }}>
            <span style={{ fontSize: 16, width: 18 }}>🔑</span>
            <div style={{ flex: 1 }}><div style={{ fontSize: 13.5, fontWeight: 700 }}>{cr.label}</div><div style={{ fontSize: 11.5, marginTop: 2, color: 'var(--tx-dim)', fontWeight: 600 }}>{cr.configured ? ('✓ configurada' + (cr.via === 'oauth' ? ' · OAuth/CLI login' : cr.via === 'gh-cli' ? ' · gh CLI' : ' · API key')) : 'sin configurar'}</div></div>
            <span style={{ width: 8, height: 8, borderRadius: 99, background: cr.configured ? 'var(--p3)' : 'var(--tx-dim)', boxShadow: cr.configured ? '0 0 8px var(--p3)' : 'none' }} />
            <button className="btn" style={{ padding: '6px 12px' }} onClick={() => { if (!(window.tfBridge && window.tfBridge.set_credential)) return; const v = prompt('Pega la ' + cr.label + ' (vacío para borrar):'); if (v === null) return; window.tfBridge.set_credential(cr.id, v).then(() => location.reload()); }}>✎ Editar</button>
          </div>
        ))}
        <div style={{ fontSize: 11.5, marginTop: 12, color: 'var(--tx-dim)', fontWeight: 600 }}>Las claves se guardan en ~/.config/themeforge/keys.json (chmod 0600) · nunca en el proyecto. ♡</div>
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
        <button className="btn pri" onClick={() => window.tfBridge && window.tfBridge.pixel_office_launch && window.tfBridge.pixel_office_launch().then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {} alert(r.ok ? (r.already ? 'Pixel Office ya está activo. ♡' : '🎮 Pixel Office lanzado. ♡') : ('Error: ' + (r.error || ''))); })}>🎮 Lanzar dashboard</button>
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
// Una terminal real por «kind» (agent/shell/hermes), filtrada por path+kind.
function TermFrame({ path, kind }) {
  const [url, setUrl] = useState(null); const [err, setErr] = useState(null);
  useEffect(() => {
    const B = window.tfBridge;
    if (!B || !path) return;
    const onReady = (j) => { let r = {}; try { r = JSON.parse(j); } catch (e) {} if (r.path === path && r.kind === kind) { if (r.url) setUrl(r.url); else if (r.error) setErr(r.error); } };
    if (B.terminal_ready && B.terminal_ready.connect) B.terminal_ready.connect(onReady);
    const fn = kind === 'agent' ? B.start_terminal : kind === 'shell' ? B.start_shell : kind === 'hermes' ? B.start_hermes : kind === 'setup' ? B.start_setup : null;
    if (fn) fn.call(B, path);
    return () => { try { B.terminal_ready.disconnect(onReady); } catch (e) {} };
  }, [path, kind]);
  if (!window.tfBridge || !path) return <KawaiiTerminal run={true} />;
  if (err) return <div style={{ flex: 1, padding: 14, color: 'var(--p3)', fontWeight: 600 }}>{kind}: {err} 🥺</div>;
  if (!url) return <div style={{ flex: 1, padding: 14, color: 'var(--tx-dim)', fontWeight: 600 }}>🖥️ iniciando {kind} (xterm · node-pty)… ♡</div>;
  return <iframe src={url} style={{ flex: 1, width: '100%', border: 'none', borderRadius: 16, background: '#1b1020', minHeight: 0 }} />;
}
// Pestaña «Office» — dashboard pixel-art ♡.
function OfficeFrame() {
  const [url, setUrl] = useState(null); const [msg, setMsg] = useState('✨ cargando Office… ♡');
  useEffect(() => {
    const B = window.tfBridge;
    if (!B || !B.pixel_office_url) { setMsg('Office no disponible 🥺'); return; }
    B.pixel_office_url().then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {} if (r.installed && r.url) setUrl(r.url); else setMsg('Pixel Office no instalado — Ajustes → Pixel Office ♡'); });
  }, []);
  if (!url) return <div style={{ flex: 1, padding: 14, color: 'var(--tx-dim)', fontWeight: 600 }}>{msg}</div>;
  return <iframe src={url} style={{ flex: 1, width: '100%', border: 'none', borderRadius: 16, background: '#1b1020', minHeight: 0 }} />;
}
// Pestañas encima del terminal (como en la app normal): Setup · Agente · Shell · Hermes · Office.
function RealTerm({ path, fresh }) {
  const op = (window.__TF_DATA__ && window.__TF_DATA__.operator) || {};
  const tabs = [];
  if (fresh) tabs.push(['setup', '⚙️ Setup']);
  tabs.push(['agent', '🩵 Agente'], ['shell', '🐚 Shell']);
  if (op.available) tabs.push(['hermes', '🚀 Hermes']);
  tabs.push(['office', '🎮 Office']);
  const first = fresh ? 'setup' : 'agent';
  const [active, setActive] = useState(first);
  const [seen, setSeen] = useState({ [first]: true });
  const open = (k) => { setActive(k); setSeen(s => ({ ...s, [k]: true })); };
  // Al terminar el setup → cambia solo a la pestaña Agente ♡.
  useEffect(() => {
    const B = window.tfBridge;
    if (!fresh || !B || !B.setup_done || !B.setup_done.connect) return;
    const onDone = (j) => { let r = {}; try { r = JSON.parse(j); } catch (e) {} if (r.path === path) { setSeen(s => ({ ...s, agent: true })); setActive('agent'); } };
    B.setup_done.connect(onDone);
    return () => { try { B.setup_done.disconnect(onDone); } catch (e) {} };
  }, [path, fresh]);
  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
      <div style={{ display: 'flex', gap: 5, marginBottom: 8, flexWrap: 'wrap' }}>
        {tabs.map(([k, l]) => <button key={k} className={'fchip' + (active === k ? ' on' : '')} onClick={() => open(k)}>{l}</button>)}
      </div>
      {tabs.map(([k]) => seen[k] ? (
        <div key={k} style={{ display: active === k ? 'flex' : 'none', flex: active === k ? 1 : 0, flexDirection: 'column', minHeight: 0 }}>
          {k === 'office' ? <OfficeFrame /> : <TermFrame path={path} kind={k} />}
        </div>
      ) : null)}
    </div>
  );
}
// Preview REAL con controles (Start / Stop / Reload / abrir en navegador) ♡.
function RealPreview({ path, narrow }) {
  const B = window.tfBridge;
  const [url, setUrl] = useState(null); const [err, setErr] = useState(null);
  const [status, setStatus] = useState('idle'); const [k, setK] = useState(0);
  const [log, setLog] = useState('');
  useEffect(() => {
    if (!B || !B.preview_ready || !B.preview_ready.connect) return;
    const onReady = (j) => { let r = {}; try { r = JSON.parse(j); } catch (e) {} if (r.path !== path) return;
      if (r.log !== undefined) { setLog(l => (l + r.log).slice(-4000)); return; }
      if (r.stopped) { setUrl(null); setStatus('stopped'); return; }
      if (r.url) { setUrl(r.url); setErr(null); setStatus('up'); } else if (r.error) { setErr(r.error); setStatus('error'); } };
    B.preview_ready.connect(onReady);
    return () => { try { B.preview_ready.disconnect(onReady); } catch (e) {} };
  }, [path]);
  const start = () => { if (B && B.start_preview && path) { setErr(null); setLog(''); setStatus('starting'); B.start_preview(path); } };
  const stop = () => { if (B && B.stop_preview && path) { B.stop_preview(path); setUrl(null); setStatus('stopped'); } };
  const reload = () => setK(x => x + 1);
  const openExt = () => { if (B && B.open_preview_external && path) B.open_preview_external(path); };
  const redetect = () => {
    if (!(B && B.refresh_profile && path)) return;
    B.refresh_profile(path).then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {}
      if (r.detected) { if (B.stop_preview) B.stop_preview(path); setUrl(null); setErr(null); setStatus('starting'); setTimeout(start, 500); }
      else alert('Aún sin preview detectable — ¿el setup terminó de instalar deps? (mira la pestaña Setup) 🥺'); });
  };
  useEffect(() => { if (B && path && status === 'idle') start(); }, [path]);
  const ctl = { fontSize: 11.5, padding: '5px 10px', borderRadius: 99 };
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '0 0 10px', flexWrap: 'wrap' }}>
        <button className="btn" style={ctl} onClick={start} disabled={status === 'up' || status === 'starting'}>▶ Start</button>
        <button className="btn" style={ctl} onClick={stop} disabled={status !== 'up'}>■ Stop</button>
        <button className="btn" style={ctl} onClick={reload} disabled={status !== 'up'}>↻ Reload</button>
        <button className="btn" style={ctl} onClick={openExt} disabled={status !== 'up'}>🗗 Navegador</button>
        <button className="btn" style={ctl} onClick={redetect}>🔄 Re-detectar</button>
        <input className="ta" readOnly value={url || ''} placeholder="URL del preview… ♡" style={{ minHeight: 0, padding: '5px 10px', flex: 1, fontSize: 11.5, borderRadius: 99, minWidth: 120 }} />
      </div>
      <div style={{ flex: 1, display: 'grid', placeItems: 'stretch', minHeight: 0, overflow: 'auto' }}>
        {!B || !path ? <Slot id={'pw'} cls="" radius={16} ph="preview de tu tema ♡" />
          : err ? <div style={{ color: 'var(--tx-dim)', fontWeight: 600, placeSelf: 'center' }}>preview: {err} 🥺</div>
          : status === 'stopped' ? <div style={{ color: 'var(--tx-dim)', fontWeight: 600, placeSelf: 'center' }}>■ preview detenido — pulsa ▶ Start ♡</div>
          : !url ? <div style={{ alignSelf: 'stretch', width: '100%', overflow: 'auto', fontFamily: 'var(--font)', fontSize: 11.5, color: 'var(--tx-dim)', fontWeight: 600, whiteSpace: 'pre-wrap', padding: 6 }}>{'✨ arrancando dev server (sondeando puerto)… ♡\n' + (log || '')}</div>
          : <iframe key={k} src={url} style={{ width: narrow ? 320 : '100%', maxWidth: '100%', height: '100%', minHeight: 280, border: 'none', borderRadius: 16, background: '#fff', justifySelf: 'center' }} />}
      </div>
    </div>
  );
}

// Log del setup/scaffold en vivo (señal progress) mientras se construye ♡.
function BuildLog({ lines }) {
  const box = useRef(null);
  useEffect(() => { if (box.current) box.current.scrollTop = box.current.scrollHeight; }, [lines]);
  return (
    <div ref={box} style={{ flex: 1, background: 'var(--bg2)', borderRadius: 16, padding: 14, fontFamily: 'var(--font)', fontSize: 12.5, lineHeight: 1.7, overflowY: 'auto', minHeight: 0, whiteSpace: 'pre-wrap', color: 'var(--tx-dim)', fontWeight: 600 }}>
      {(lines && lines.length) ? lines.join('') : '✨ esperando salida del scaffold… ♡'}
      <div style={{ color: 'var(--accent)' }}>▊ instalando (scaffold · autoskills · UI/UX Pro · MCP)… ♡</div>
    </div>
  );
}
// Barra de MCP servers REAL: lee el .mcp.json del proyecto; clic = activar/desactivar ♡.
function MCPBar({ path }) {
  const B = window.tfBridge;
  const [servers, setServers] = useState([]);
  const load = () => { if (B && B.read_mcp && path) B.read_mcp(path).then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {} if (r.servers) setServers(r.servers); }); };
  useEffect(load, [path]);
  const toggle = (id) => { if (!(B && B.toggle_mcp && path)) return; setServers(s => s.map(x => x.id === id ? { ...x, active: !x.active } : x)); B.toggle_mcp(path, id).then(load); };
  return (
    <div style={{ display: 'flex', gap: 6, marginBottom: 14, flexWrap: 'wrap', alignItems: 'center' }}>
      <span style={{ fontSize: 11.5, fontWeight: 700, color: 'var(--tx-dim)' }}>MCP ·</span>
      {(servers.length ? servers : MCP_SERVERS.map(m => ({ id: m.id, label: m.label, active: !!m.always, desc: m.desc }))).map(m => (
        <button key={m.id} className="tag" title={(m.active ? 'activo · ' : 'inactivo · ') + (m.desc || '')} onClick={() => toggle(m.id)}
          style={{ cursor: 'pointer', color: m.active ? 'var(--accent)' : 'var(--tx-dim)', opacity: m.active ? 1 : 0.55, fontWeight: 700 }}>
          {m.active ? '💝' : '🤍'} {m.label}
        </button>
      ))}
      <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--tx-dim)' }}>· clic = on/off ♡</span>
    </div>
  );
}
function ProjectWindow({ p, onBack, onDeploy, onBuild, onRef, buildLog }) {
  const [tab, setTab] = useState('desktop');
  const [pushed, setPushed] = useState(false);
  const building = p.status === 'building';
  const ag = AGENTS[p.agent] || { color: 'var(--accent)', em: '🐾', label: p.agent || 'agent' };
  const st = STATUS[p.status] || { color: 'var(--tx-dim)', em: '○', label: p.status || '' };
  const tabs = [['desktop', '🖥️ Desktop'], ['mobile', '📱 Mobile'], ['code', '💻 Code']];
  const B = window.tfBridge;
  const preflight = () => { if (B && B.run_preflight) { alert('🔎 Pre-flight… ♡'); B.run_preflight(p.path).then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {} alert('Pre-flight: ' + (r.verdict || r.status || (r.ok ? 'PASS ♡' : JSON.stringify(r).slice(0, 200)))); }); } else onBuild && onBuild(); };
  const buildzip = () => { if (B && B.build_zip) { alert('📦 Empaquetando ZIP… ♡'); B.build_zip(p.path).then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {} alert('ZIP: ' + (r.zip_path || r.zip || r.error || 'hecho ♡')); }); } else onBuild && onBuild(); };
  const push = () => { if (B && B.git_push) { B.git_push(p.path); setPushed(true); } else setPushed(true); };
  const deploy = () => { if (B && B.deploy_demo) { const pv = prompt('Deploy a (netlify/vercel/cloudflare/surge):', 'surge'); if (pv) B.deploy_demo(p.path, pv); } else onDeploy && onDeploy(); };
  const folder = () => { if (B && B.open_folder) B.open_folder(p.path); };
  const vscode = () => { if (B && B.open_vscode) B.open_vscode(p.path); };
  const extterm = () => { if (B && B.open_external_terminal) B.open_external_terminal(p.path); };
  const github = () => { if (B && B.github_create) { alert('🐙 GitHub: creando/empujando repo… mira el log ♡'); B.github_create(p.path); } };
  const operator = () => { window.tfNav && window.tfNav('operator'); };
  const newp = () => { window.tfNav && window.tfNav('new'); };
  const other = () => { window.tfNav && window.tfNav('gallery'); };
  return (
    <div className="page fade" style={{ height: '100%', display: 'flex', flexDirection: 'column', paddingBottom: 26 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14, flexWrap: 'wrap' }}>
        <button className="btn" onClick={onBack}>← Galería</button>
        <b style={{ fontSize: 19 }}>{p.name}</b><span style={{ fontFamily: 'var(--jp)', color: 'var(--tx-dim)' }}>{p.jp}</span>
        <span className="pstatus" style={{ position: 'static', color: st.color }}>{st.em} {st.label}</span>
        <div style={{ flex: 1 }} />
        <button className="btn" onClick={newp}>✨ Nuevo</button>
        <button className="btn" onClick={other}>📂 Abrir otro</button>
        <button className="btn" onClick={folder}>🗀 Folder</button>
        <button className="btn" onClick={vscode}>💻 VSCode</button>
        <button className="btn" onClick={extterm}>🖥️ Terminal ext.</button>
        <button className="btn" onClick={operator}>🚀 Operator</button>
        <button className="btn" onClick={preflight}>✅ Pre-flight</button>
        <button className="btn" onClick={buildzip}>📦 ZIP</button>
        <button className="btn" onClick={github}>🐙 GitHub</button>
        <button className={'btn' + (pushed ? '' : ' pri')} onClick={push}>{pushed ? '✓ Pushed' : '🐙 Push'}</button>
        <button className="btn pri" onClick={deploy}>🚀 Deploy</button>
      </div>
      {/* MCP chips reales */}
      <MCPBar path={p.path} />
      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: 16, minHeight: 0 }}>
        <div className="panelc" style={{ display: 'flex', flexDirection: 'column', padding: 14, minHeight: 0 }}>
          <div style={{ display: 'flex', gap: 6, marginBottom: 12 }}>
            {tabs.map(([k, l]) => <button key={k} className={'fchip' + (tab === k ? ' on' : '')} onClick={() => setTab(k)}>{l}</button>)}
            <span style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--tx-dim)', fontWeight: 600, alignSelf: 'center' }}>preview real ♡</span>
          </div>
          <div style={{ flex: 1, display: 'grid', placeItems: 'stretch', background: 'var(--bg2)', borderRadius: 18, padding: 0, minHeight: 0, overflow: 'auto' }}>
            <RealPreview path={p.path} narrow={tab === 'mobile'} />
          </div>
        </div>
        <div className="panelc" style={{ display: 'flex', flexDirection: 'column', padding: 14, minHeight: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
            <b>🖥️ Terminales</b>
            <span className="tag" style={{ marginLeft: 'auto' }}>{ag.em} {ag.label}</span>
          </div>
          <RealTerm path={p.path} fresh={p.fresh} />
        </div>
      </div>
    </div>
  );
}

/* ---- Market (analizador real con IA) ---- */
function Market() {
  const [q, setQ] = useState('');
  const [done, setDone] = useState(false);
  const [load, setLoad] = useState(false);
  const [md, setMd] = useState('');
  const real = !!(window.tfBridge && window.tfBridge.analyze_market);
  useEffect(() => {
    if (!real || !window.tfBridge.market_result || !window.tfBridge.market_result.connect) return;
    const onRes = (j) => { let r = {}; try { r = JSON.parse(j); } catch (e) {} setLoad(false); setMd(r.error ? ('⚠ ' + r.error) : (r.markdown || '')); setDone(true); };
    window.tfBridge.market_result.connect(onRes);
    return () => { try { window.tfBridge.market_result.disconnect(onRes); } catch (e) {} };
  }, []);
  const go = (kind) => { if (!real) return; setLoad(true); setDone(false); setMd(''); window.tfBridge.analyze_market(kind || q); };
  return (
    <div className="page fade">
      <h2 className="sec">🌷 Market Analyzer <span style={{ fontFamily: 'var(--jp)', fontSize: 14, color: 'var(--tx-dim)' }}>市場分析</span></h2>
      <div className="panelc" style={{ display: 'flex', gap: 10, marginBottom: 14 }}>
        <input className="ta" style={{ minHeight: 0, padding: '11px 16px', borderRadius: 99 }} value={q} onChange={e => setQ(e.target.value)} placeholder='Nicho a investigar — ej: "café de gatitos" 🐱' />
        <button className="btn pri" onClick={() => go()}>{load ? '🔎 buscando…' : '🔎 Analizar'}</button>
      </div>
      {real && <div style={{ display: 'flex', gap: 8, marginBottom: 18, flexWrap: 'wrap' }}>
        {[['@general', 'Mercado 2026'], ['@stacks', 'Stacks'], ['@prediction', 'Predicción 2027']].map(([k, l]) => <button key={k} className="tag" style={{ cursor: 'pointer' }} onClick={() => go(k)}>{l}</button>)}
        {done && md && <button className="tag" style={{ cursor: 'pointer', marginLeft: 'auto', color: 'var(--accent)' }} onClick={() => window.tfNav && window.tfNav('new')}>✨ Crear proyecto desde análisis</button>}
      </div>}
      {load && <div className="panelc" style={{ textAlign: 'center', color: 'var(--accent)', fontWeight: 700 }}>✨ analizando mercado con IA (OpenRouter) — puede tardar… ✨</div>}
      {done && md && <div className="panelc fade"><pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: 13, lineHeight: 1.7, color: 'var(--tx)', margin: 0 }}>{md}</pre></div>}
      {!done && !load && <div className="panelc" style={{ textAlign: 'center', color: 'var(--tx-dim)', fontWeight: 600 }}>introduce un nicho para empezar 🌸</div>}
    </div>
  );
}

/* ---- Licensing (sistema real anti-nulled pcreative) ---- */
function Licensing() {
  const real = !!(window.tfBridge && window.tfBridge.licensing_status);
  const [st, setSt] = useState(null);
  const [sub, setSub] = useState('lic');
  const [np, setNp] = useState(''); const [ne, setNe] = useState(''); const [nt, setNt] = useState('regular');
  const [prods, setProds] = useState(null); const [gum, setGum] = useState(null); const [tools, setTools] = useState('');
  const api = (p, m, b) => window.tfBridge.licensing_api(p, m || 'GET', b ? JSON.stringify(b) : '').then(j => { try { return JSON.parse(j); } catch (e) { return {}; } });
  const refresh = () => { if (real) window.tfBridge.licensing_status().then(j => { try { setSt(JSON.parse(j)); } catch (e) {} }); };
  useEffect(() => { refresh(); }, []);
  const create = () => { if (!np.trim()) return; window.tfBridge.licensing_create(np, ne, nt).then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {} alert(r.ok ? ('✓ Licencia ♡: ' + (r.key || '')) : ('Error: ' + (r.error || r.code))); refresh(); }); };
  if (!real) return <div className="page fade"><div className="panelc">Licensing no disponible (sin puente). 🥺</div></div>;
  return (
    <div className="page fade" style={{ maxWidth: 980 }}>
      <h2 className="sec">🔑 Licencias <span style={{ fontFamily: 'var(--jp)', fontSize: 14, color: 'var(--tx-dim)' }}>認可</span></h2>
      <div className="panelc" style={{ marginBottom: 14, display: 'flex', alignItems: 'center', gap: 12, fontSize: 13.5, fontWeight: 600 }}>
        <span style={{ width: 11, height: 11, borderRadius: 99, background: st ? (st.reachable ? 'var(--p3)' : (st.configured ? '#ffcf5e' : 'var(--tx-dim)')) : 'var(--tx-dim)' }} />
        <span>{!st ? 'consultando… ♡' : !st.configured ? 'Sin backend (config en licensing.json)' : st.reachable ? ('Backend OK ✓ · ' + (st.licenses || []).length + ' licencias · ' + (st.products || []).length + ' productos') : 'Configurado pero no responde 🥺'}</span>
        <button className="btn" style={{ marginLeft: 'auto' }} onClick={refresh}>↻</button>
      </div>
      <div style={{ display: 'flex', gap: 8, marginBottom: 14, flexWrap: 'wrap' }}>
        {[['lic', 'Licencias'], ['prod', 'Productos'], ['gum', 'Gumroad'], ['tools', 'Tools']].map(([k, l]) => (
          <button key={k} className={'fchip' + (sub === k ? ' on' : '')} style={{ cursor: 'pointer' }} onClick={() => { setSub(k); if (k === 'prod' && !prods) api('/api/products/versions').then(r => setProds(r.data)); if (k === 'gum' && !gum) api('/api/gumroad').then(r => setGum(r.data)); }}>{l}</button>
        ))}
      </div>
      {sub === 'lic' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 16 }}>
          <div className="panelc" style={{ padding: 0, overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead><tr style={{ background: 'var(--bg2)' }}>{['Key', 'Producto', 'Tipo', 'Estado'].map(h => <th key={h} style={{ textAlign: 'left', padding: '11px 14px', color: 'var(--tx-dim)', fontWeight: 700 }}>{h}</th>)}</tr></thead>
              <tbody>{(st && st.licenses && st.licenses.length) ? st.licenses.map((l, i) => <tr key={i} style={{ borderTop: '2px dashed var(--line)' }}><td style={{ padding: '9px 14px', color: 'var(--accent)', fontWeight: 600 }}>{l.key}</td><td style={{ padding: '9px 14px' }}>{l.product}</td><td style={{ padding: '9px 14px', color: 'var(--tx-dim)' }}>{l.type}</td><td style={{ padding: '9px 14px' }}>{l.status}</td></tr>) : <tr><td colSpan={4} style={{ padding: 22, textAlign: 'center', color: 'var(--tx-dim)', fontWeight: 600 }}>aún no hay licencias ♡</td></tr>}</tbody>
            </table>
          </div>
          <div className="panelc">
            <div style={{ fontWeight: 700, marginBottom: 12 }}>Crear licencia 💝 <span style={{ fontFamily: 'var(--jp)', fontSize: 12, color: 'var(--tx-dim)' }}>発行</span></div>
            <input className="ta" style={{ minHeight: 0, height: 40, marginBottom: 8, borderRadius: 12 }} value={np} onChange={e => setNp(e.target.value)} placeholder="producto (slug)" />
            <input className="ta" style={{ minHeight: 0, height: 40, marginBottom: 8, borderRadius: 12 }} value={ne} onChange={e => setNe(e.target.value)} placeholder="email comprador" />
            <select className="ta" style={{ minHeight: 0, height: 40, marginBottom: 10, borderRadius: 12 }} value={nt} onChange={e => setNt(e.target.value)}><option value="regular">regular</option><option value="extended">extended</option></select>
            <button className="btn pri" onClick={create}>🔑 Crear licencia</button>
          </div>
        </div>
      )}
      {sub === 'prod' && <div className="panelc"><div style={{ display: 'flex', marginBottom: 10 }}><b style={{ flex: 1 }}>Productos / Versiones</b><button className="btn" onClick={() => api('/api/products/versions').then(r => setProds(r.data))}>↻</button></div><pre style={{ whiteSpace: 'pre-wrap', fontSize: 12.5, color: 'var(--tx-dim)', margin: 0, fontWeight: 600 }}>{prods ? ((prods.products || []).map(p => '🌸 ' + p.id + ' · ' + (p.currentVersion || '—') + ' · ' + p.repo).join('\n') || '(sin productos)') : 'cargando… ♡'}</pre></div>}
      {sub === 'gum' && <div className="panelc"><div style={{ display: 'flex', marginBottom: 10 }}><b style={{ flex: 1 }}>Ventas Gumroad</b><button className="btn" onClick={() => api('/api/gumroad').then(r => setGum(r.data))}>↻</button></div><pre style={{ whiteSpace: 'pre-wrap', fontSize: 12, color: 'var(--tx-dim)', margin: 0 }}>{gum ? JSON.stringify(gum, null, 2) : 'cargando… ♡'}</pre></div>}
      {sub === 'tools' && <div className="panelc"><div style={{ display: 'flex', gap: 8, marginBottom: 10 }}><button className="btn" onClick={() => api('/api/integrations/status').then(r => setTools(JSON.stringify(r.data, null, 2)))}>Estado integraciones</button></div><pre style={{ whiteSpace: 'pre-wrap', fontSize: 12, color: 'var(--tx-dim)', margin: 0, minHeight: 50 }}>{tools || '// resultado'}</pre></div>}
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
// Análisis de referencia REAL (reference_analyzer + IA, streaming por reference_progress).
function RefModal({ onClose }) {
  const real = !!(window.tfBridge && window.tfBridge.analyze_reference);
  const [lines, setLines] = useState([]);
  const [status, setStatus] = useState('⏳ iniciando… ♡');
  const [done, setDone] = useState(false);
  const boxRef = useRef(null);
  useEffect(() => {
    if (!real) { setDone(true); setStatus('sin puente 🥺'); return; }
    const ref = (window.__tfRef && window.__tfRef.value) || prompt('Ruta de la referencia a analizar (carpeta o .zip):') || '';
    if (!ref) { setDone(true); return; }
    const kind = (window.__tfRef && window.__tfRef.kind) || 'folder';
    const onProg = (j) => { let r = {}; try { r = JSON.parse(j); } catch (e) {}
      if (r.status) setStatus(r.status);
      if (r.text !== undefined) setLines(ls => [...ls, r.text]);
      if (r.done) { if (r.error) setLines(ls => [...ls, '\n⚠ ' + r.error]); setStatus(r.error ? '⚠ error' : '✓ Análisis IA listo — se inyectará en CLAUDE.md al crear el proyecto. ♡'); setDone(true); } };
    if (window.tfBridge.reference_progress && window.tfBridge.reference_progress.connect) window.tfBridge.reference_progress.connect(onProg);
    window.tfBridge.analyze_reference(ref, kind);
    return () => { try { window.tfBridge.reference_progress.disconnect(onProg); } catch (e) {} };
  }, []);
  useEffect(() => { if (boxRef.current) boxRef.current.scrollTop = boxRef.current.scrollHeight; }, [lines]);
  return (
    <Modal title="🔎 Análisis de referencia" jp="参照分析" onClose={onClose} w={820}>
      <div ref={boxRef} style={{ background: 'var(--bg2)', borderRadius: 14, padding: 14, fontWeight: 600, fontSize: 13, lineHeight: 1.8, maxHeight: '52vh', overflowY: 'auto' }}>
        <div style={{ color: 'var(--tx-dim)', whiteSpace: 'pre-wrap' }}>{lines.join('')}</div>
        {!done && <div style={{ color: 'var(--accent)', marginTop: 8 }}>▊ {status}</div>}
      </div>
      {done && <div style={{ marginTop: 12, padding: '10px 14px', borderRadius: 14, background: 'rgba(95,216,180,0.16)', color: 'var(--p3)', fontWeight: 700, fontSize: 12.5 }}>✓ Análisis IA listo — se inyectará en CLAUDE.md al crear el proyecto (modo recreate). ♡</div>}
      <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
        <button className="btn pri" style={{ marginLeft: 'auto' }} onClick={onClose}>💾 Guardar</button>
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
  const [buildLog, setBuildLog] = useState([]);
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
  useEffect(() => { window.tfNav = nav; }, []);
  const openProject = (p) => { setProject(p); };  // ventana/modal aparte (no reemplaza la galería) ♡
  // Crear proyecto REAL: abre el proyecto en una VENTANA/MODAL aparte (como la
  // ProjectWindow nativa) con el SETUP en vivo; al terminar pasa a la IA ♡.
  const launch = (cfg) => {
    window.__tfLastAgent = cfg.agent;
    if (!(window.tfBridge && window.tfBridge.create_project)) {
      setProject({ ...cfg, id: cfg.name, status: 'live', fresh: true, jp: '制作' }); return;
    }
    if (!window.__tfWired) {
      window.__tfWired = true;
      if (window.tfBridge.build_done && window.tfBridge.build_done.connect)
        window.tfBridge.build_done.connect((j) => { let r = {}; try { r = JSON.parse(j); } catch (e) {}
          setProject(prev => ({ ...(prev || {}), id: r.slug || (prev && prev.id), name: r.name || (prev && prev.name), path: r.path || (prev && prev.path), agent: window.__tfLastAgent || 'claude', status: r.ok ? 'live' : 'draft', fresh: r.fresh || (prev && prev.fresh), jp: '制作' })); });
    }
    window.tfBridge.create_project(JSON.stringify(cfg)).then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {}
      if (r && r.ok && r.path) { setProject({ id: r.slug, name: cfg.name, path: r.path, agent: cfg.agent, status: 'live', fresh: true, jp: '制作' }); }
      else if (r && r.ok === false) alert('Error al crear: ' + (r.error || '')); });
  };
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
        {route === 'new' && <NewProject onAnalyze={() => setModal('ref')} onLaunch={launch} />}
        {route === 'cost' && <Cost />}
        {route === 'compare' && <Compare />}
        {route === 'operator' && <Operator />}
        {route === 'market' && <Market />}
        {route === 'licensing' && <Licensing />}
        {route === 'settings' && <Settings />}
      </div>

      {/* Proyecto en VENTANA/MODAL aparte (como la ProjectWindow nativa) ♡ */}
      {project && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 600, background: 'var(--bg, #fff5fa)', display: 'flex', flexDirection: 'column', padding: 20, overflow: 'auto' }}>
          <ProjectWindow p={project} onBack={() => setProject(null)} onDeploy={() => setModal('deploy')} onBuild={() => setModal('build')} onRef={() => setModal('ref')} buildLog={buildLog} />
        </div>
      )}

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
