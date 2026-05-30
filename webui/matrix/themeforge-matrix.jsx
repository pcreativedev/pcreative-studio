/* ===================== ThemeForge // MATRIX ===================== */
const { useState, useEffect, useRef } = React;

/* agentes IA como daemons */
const AGENTS = {
  claude:   { label: 'claude',   em: '◈', color: '#00ff66', pid: 'd4e2' },
  codex:    { label: 'codex',    em: '◇', color: '#00d9ff', pid: '7a1c' },
  gemini:   { label: 'gemini',   em: '◆', color: '#ffb000', pid: '9f3b' },
  opencode: { label: 'opencode', em: '◉', color: '#b46fff', pid: 'c5e8' },
};

const STATUS = {
  live:     { label: 'online',   em: '●', color: '#00ff41' },
  building: { label: 'compilando', em: '▶', color: '#ffb000' },
  draft:    { label: 'borrador', em: '◌', color: '#00d9ff' },
  archived: { label: 'archivado', em: '▣', color: '#3f7d54' },
};

const PROJECTS = (typeof window !== 'undefined' && window.__TF_DATA__ && window.__TF_DATA__.projects && window.__TF_DATA__.projects.length) ? window.__TF_DATA__.projects : [
  { id: 'm-aurora', name: 'Aurora SaaS', jp: 'オーロラ', type: 'SaaS Landing', agent: 'claude', status: 'live', cost: 4.82, tags: ['next', 'tailwind'], commits: 47, updated: 'hace 3 min' },
  { id: 'm-nordic', name: 'Nordic Forge', jp: '北欧', type: 'Agencia creativa', agent: 'codex', status: 'building', cost: 2.10, tags: ['astro', 'gsap'], commits: 23, updated: 'hace 12 min' },
  { id: 'm-meridian', name: 'Meridian Shop', jp: '商店', type: 'E-commerce', agent: 'gemini', status: 'live', cost: 7.34, tags: ['shopify', 'remix'], commits: 89, updated: 'hace 1 h' },
  { id: 'm-flux', name: 'Flux Admin', jp: '管理', type: 'Dashboard', agent: 'opencode', status: 'draft', cost: 0.41, tags: ['laravel', 'vue'], commits: 8, updated: 'hace 5 h' },
  { id: 'm-zen', name: 'Zen Clinic', jp: '診療', type: 'Clínica · booking', agent: 'claude', status: 'live', cost: 3.95, tags: ['wp', 'acf'], commits: 34, updated: 'ayer' },
  { id: 'm-pixel', name: 'Pixel Arcade', jp: '遊技', type: 'Landing · game', agent: 'codex', status: 'archived', cost: 1.22, tags: ['tauri', 'react'], commits: 19, updated: 'hace 3 días' },
];

const STACKS = (typeof window !== 'undefined' && window.__TF_DATA__ && window.__TF_DATA__.stacks && window.__TF_DATA__.stacks.length) ? window.__TF_DATA__.stacks.map(s => ({ k: s.key, label: s.label, jp: s.jp || '', em: '◆', cat: s.cat })) : [
  { k: 'next', label: 'Next.js', jp: '次世代', em: '▲' },
  { k: 'astro', label: 'Astro', jp: '星', em: '✦' },
  { k: 'laravel', label: 'Laravel', jp: '帆', em: '◣' },
  { k: 'wp', label: 'WordPress', jp: '出版', em: 'W' },
  { k: 'shopify', label: 'Hydrogen', jp: '商', em: '⬡' },
  { k: 'tauri', label: 'Tauri', jp: '鳥', em: '◈' },
];

const NAV = [
  { id: 'gallery', em: '▤', label: 'Galería', jp: '制作' },
  { id: 'new', em: '+', label: 'Nuevo', jp: '新規' },
  { id: 'cost', em: '$', label: 'Coste IA', jp: '費用' },
  { id: 'compare', em: '⇄', label: 'Comparar', jp: '比較' },
  { id: 'operator', em: '⌬', label: 'Operator', jp: '司令' },
  { id: 'market', em: '⊞', label: 'Market', jp: '市場' },
  { id: 'licensing', em: '⚿', label: 'Licencias', jp: '認可' },
  { id: 'settings', em: '⚙', label: 'Ajustes', jp: '設定' },
];

const MCP_SERVERS = (typeof window !== 'undefined' && window.__TF_DATA__ && window.__TF_DATA__.mcp && window.__TF_DATA__.mcp.length) ? window.__TF_DATA__.mcp.map(m => ({ id: m.id, label: m.label, always: m.always, em: m.always ? '▮' : '◇', desc: m.desc, lic: m.lic })) : [
  { id: 'filesystem', label: 'filesystem', always: true, em: '▮', desc: 'Acceso al proyecto' },
  { id: 'fetch', label: 'fetch', always: true, em: '⇆', desc: 'HTTP / scraping' },
  { id: 'memory', label: 'memory', always: true, em: '⊟', desc: 'Memoria del agente' },
  { id: 'github', label: 'github', always: true, em: '⎇', desc: 'Repos · PRs · push' },
  { id: 'themeforge', label: 'themeforge', always: true, em: '鍛', desc: '8 tools: create · zip · preflight…' },
  { id: 'playwright', label: 'playwright', em: '◐', desc: 'Navegador automatizado' },
  { id: 'figma', label: 'figma-context', em: '◓', desc: 'Lee diseños de Figma' },
  { id: 'shopify', label: 'shopify-dev', em: '⬡', desc: 'GraphQL Admin/Storefront' },
  { id: 'postgres', label: 'postgres', em: '⊞', desc: 'Query a la DB' },
];

const DEPLOY_TARGETS = [
  { id: 'netlify', label: 'Netlify', em: '◆' },
  { id: 'vercel', label: 'Vercel', em: '▲' },
  { id: 'cloudflare', label: 'Cloudflare', em: '◉' },
  { id: 'surge', label: 'Surge', em: '⌁' },
];

const PREFLIGHT = [
  { l: 'LICENSE presente', ok: true }, { l: 'documentation/ completa', ok: true },
  { l: 'Lighthouse >= 90', ok: true, n: '94' }, { l: 'Sin secretos (.env limpio)', ok: true },
  { l: 'Layout original (anti-copy)', ok: true }, { l: 'Imágenes con licencia', ok: false, n: '2 sin atribuir' },
  { l: 'Responsive 320->1920', ok: true },
];

/* ---- digital rain ---- */
function startRain() {
  const c = document.getElementById('rain');
  if (!c || c.dataset.on) return;
  c.dataset.on = '1';
  const ctx = c.getContext('2d');
  const fontSize = 16;
  const chars = 'アァカサタナハマヤャラワガザダバパイィキシチニヒミリヰギジヂビピウゥクスツヌフムユュルグズブヅプエェケセテネヘメレヱゲゼデベペオォコソトノホモヨョロヲゴゾドボポヴッン0123456789'.split('');
  let cols = 0, drops = [];
  function resize() {
    c.width = window.innerWidth; c.height = window.innerHeight;
    cols = Math.floor(c.width / fontSize);
    drops = Array(cols).fill(0).map(() => Math.random() * -60);
  }
  resize(); window.addEventListener('resize', resize);
  setInterval(() => {
    ctx.fillStyle = 'rgba(4,8,4,0.10)';
    ctx.fillRect(0, 0, c.width, c.height);
    ctx.font = fontSize + "px 'Share Tech Mono', monospace";
    for (let i = 0; i < cols; i++) {
      const y = drops[i] * fontSize, x = i * fontSize;
      ctx.fillStyle = '#c8ffd4';
      ctx.fillText(chars[(Math.random() * chars.length) | 0], x, y);
      ctx.fillStyle = 'rgba(0,255,65,0.55)';
      ctx.fillText(chars[(Math.random() * chars.length) | 0], x, y - fontSize * 3);
      if (y > c.height && Math.random() > 0.975) drops[i] = 0;
      drops[i]++;
    }
  }, 55);
}
function burst(e) {
  const h = document.createElement('div'); h.className = 'burstfx';
  h.textContent = ['+1', '◈', '01', '▲', 'ACK'][Math.floor(Math.random() * 5)];
  h.style.left = (e.clientX - 8) + 'px'; h.style.top = (e.clientY - 8) + 'px';
  document.body.appendChild(h); setTimeout(() => h.remove(), 800);
}
const Slot = ({ id, cls, radius = 4, ph }) => React.createElement('image-slot', { id, class: cls, shape: 'rounded', radius: String(radius), placeholder: ph });

/* ---- Gallery ---- */
function gop(slug, op, arg) {  // operación real de galería (favorito/tags/archivar/eliminar)
  const B = window.tfBridge;
  if (!B || !B.gallery_op) return Promise.resolve({});
  return B.gallery_op(slug, op, arg || '').then(j => { try { return JSON.parse(j); } catch (e) { return {}; } });
}
function ProjectCard({ p, onOpen, onChanged, archived }) {
  const ag = AGENTS[p.agent] || { color: 'var(--accent)', em: '◆', label: p.agent }, st = STATUS[p.status] || { color: 'var(--tx-dim)', em: '○', label: p.status };
  const act = (e, op, arg) => { e.stopPropagation(); gop(p.id, op, arg).then(() => onChanged && onChanged()); };
  return (
    <div className="pcard fade" style={{ opacity: archived ? 0.65 : 1, cursor: 'pointer' }} onClick={() => onOpen(p)}>
      <span className="pstatus" style={{ color: st.color }}>{st.em} {st.label}</span>
      <span className="pjp">{p.jp}</span>
      <Slot id={p.id} cls="pcover" radius={3} ph="// arrastra screenshot" />
      <span className="pfav" title="favorito" onClick={(e) => { act(e, 'favorite'); burst(e); }}>{p.fav ? '★' : '☆'}</span>
      <div className="pbody">
        <div className="prow">
          <div><div className="pname">{p.name}</div><div className="ptype">{p.type}</div></div>
          <div className="pcost">${(p.cost || 0).toFixed(2)}</div>
        </div>
        <div className="ptags">{(p.tags || []).map(t => <span key={t} className="tag">{t}</span>)}</div>
        <div className="pfoot">
          <span className="pagent" style={{ color: ag.color }}>{ag.em} {ag.label}</span>
          <span style={{ color: 'var(--tx-dim)' }}>{p.commits} commits · {p.updated}</span>
        </div>
        <div style={{ display: 'flex', gap: 6, marginTop: 8, flexWrap: 'wrap' }} onClick={e => e.stopPropagation()}>
          <button className="tag" style={{ cursor: 'pointer' }} title="editar tags" onClick={(e) => { const v = prompt('Tags (separados por coma):', (p.tags || []).join(', ')); if (v !== null) act(e, 'tags', v); }}>🏷️ tags</button>
          {archived
            ? <button className="tag" style={{ cursor: 'pointer' }} title="restaurar" onClick={(e) => act(e, 'unarchive')}>♻ restaurar</button>
            : <button className="tag" style={{ cursor: 'pointer' }} title="archivar" onClick={(e) => act(e, 'archive')}>📦 archivar</button>}
          <button className="tag" style={{ cursor: 'pointer', color: 'var(--p3)', borderColor: 'var(--p3)' }} title="eliminar" onClick={(e) => { if (confirm('¿Eliminar «' + p.name + '» PARA SIEMPRE? (carpeta + contenedor)')) act(e, 'delete'); }}>🗑️</button>
        </div>
      </div>
    </div>
  );
}

function Gallery({ onOpen }) {
  const [f, setF] = useState('all');
  const [projects, setProjects] = useState(PROJECTS);  // galería en vivo
  const [arch, setArch] = useState([]);                // archivados
  const [showArch, setShowArch] = useState(false);
  const [favOnly, setFavOnly] = useState(false);
  const [q, setQ] = useState('');
  const load = () => {
    const B = window.tfBridge;
    if (B && B.list_projects) B.list_projects().then(j => { try { const a = JSON.parse(j); if (Array.isArray(a)) setProjects(a); } catch (e) {} });
    if (B && B.list_archived) B.list_archived().then(j => { try { const a = JSON.parse(j); if (Array.isArray(a)) setArch(a); } catch (e) {} });
  };
  useEffect(load, []);
  const fl = ['all', 'live', 'building', 'draft'];
  const base = showArch ? arch : projects;
  const ql = q.trim().toLowerCase();
  const list = base.filter(p => (showArch || f === 'all' || p.status === f) && (!favOnly || p.fav)
    && (!ql || (p.name + ' ' + (p.stack || '') + ' ' + (p.tags || []).join(' ')).toLowerCase().includes(ql)));
  const liveN = projects.filter(p => p.status === 'live').length;
  const buildingN = projects.filter(p => p.status === 'building').length;
  const totalCost = projects.reduce((s, p) => s + (p.cost || 0), 0);
  return (
    <div className="page fade">
      <div className="stats">
        {[['◫', String(projects.length), 'proyectos'], ['$', totalCost.toFixed(2), 'cómputo IA'], ['●', String(liveN), 'desplegados'], ['▶', String(buildingN), 'compilando']].map(([e, n, l]) => (
          <div className="stat" key={l}><div className="em">{e}</div><div className="n">{n}</div><div className="l">{l}</div></div>
        ))}
      </div>
      <div className="filters" style={{ alignItems: 'center', flexWrap: 'wrap' }}>
        <input className="ta" value={q} onChange={e => setQ(e.target.value)} placeholder="🔍 filtrar (nombre/stack/tag)…" style={{ minHeight: 0, padding: '6px 12px', width: 220, fontSize: 12 }} />
        {!showArch && fl.map(x => <button key={x} className={'fchip' + (f === x ? ' on' : '')} onClick={() => setF(x)}>{x === 'all' ? '> todos' : (STATUS[x].em + ' ' + STATUS[x].label)}</button>)}
        <button className={'fchip' + (favOnly ? ' on' : '')} onClick={() => setFavOnly(v => !v)}>★ favoritos</button>
        <button className={'fchip' + (showArch ? ' on' : '')} onClick={() => setShowArch(v => !v)}>📦 archivados</button>
        <button className="fchip" onClick={load}>↻</button>
      </div>
      <div className="grid">{list.map(p => <ProjectCard key={p.id} p={p} onOpen={onOpen} onChanged={load} archived={showArch} />)}</div>
      {!list.length && <div style={{ color: 'var(--tx-dim)', fontFamily: 'var(--term)', padding: 30, textAlign: 'center' }}>// {showArch ? 'sin proyectos archivados' : 'sin proyectos — crea uno en «+ Nuevo»'}</div>}
    </div>
  );
}

/* ---- New project (vibe scaffolder · 4 modos + extras, paridad con el normal) ---- */
const M_MODES = [
  { k: 'scratch', label: 'Desde cero', jp: '新規', desc: 'Scaffold oficial del stack + agente IA desde cero.' },
  { k: 'recreate', label: 'Recreate ref', jp: '再現', desc: 'Carpeta / .zip / URL / Figma — la IA estudia y reimplementa.' },
  { k: 'adopt', label: 'Adopt local', jp: '採用', desc: 'Export de claude.ai/design, v0.dev o Figma Make.' },
  { k: 'repo', label: 'Existing repo', jp: '既存', desc: 'Continúa un repo de GitHub existente.' },
];
const M_REF_KINDS = [['folder', 'Carpeta local'], ['zip', 'Archivo .zip'], ['url', 'URL de demo'], ['figma', 'Figma (frame)']];
function MToggle({ on, onClick }) {
  return <button onClick={onClick} style={{ cursor: 'pointer', width: 38, height: 22, borderRadius: 99, padding: 2, border: 'none', background: on ? 'var(--accent)' : 'rgba(255,255,255,0.12)', boxShadow: on ? '0 0 10px var(--accent)' : 'none', transition: 'all .18s' }}><span style={{ display: 'block', width: 18, height: 18, borderRadius: 99, background: on ? '#040804' : '#7d8f80', transform: on ? 'translateX(16px)' : 'none', transition: 'transform .18s' }} /></button>;
}
function MCheck({ label, sub, on, onToggle }) {
  return <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '11px 0', borderBottom: '1px solid var(--line)' }}><div style={{ flex: 1 }}><div style={{ fontSize: 13.5, fontFamily: 'var(--term)' }}>{label}</div>{sub && <div style={{ fontSize: 11.5, marginTop: 3, color: 'var(--tx-dim)', fontFamily: 'var(--term)' }}>{sub}</div>}</div><MToggle on={on} onClick={onToggle} /></div>;
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
      if (!rid || rid.indexOf('/') < 0) { alert('Indica el repo como owner/repo o una URL de GitHub.'); return; }
      const repoName = rid.replace(/\.git$/, '').replace(/\/$/, '').split('/').pop();
      onLaunch && onLaunch({ name: repoName, stack: 'none', agent, type, mode: 'existing', niche: vibe, existing_repo: rid, opts }); return;
    }
    const name = (pname || '').trim() || (vibe || '').trim().slice(0, 42) || type || 'Untitled Forge';
    if (!(pname || '').trim() && !confirm('Sin nombre — se usará «' + name + '». ¿Continuar?')) return;
    onLaunch && onLaunch({ name, stack, agent, type, mode, niche: vibe, reference: refVal, reference_kind: refKind, opts });
  };
  const groups = {}; STACKS.forEach(s => { const c = s.cat || 'Otros'; (groups[c] = groups[c] || []).push(s); });
  const selCat = (STACKS.find(s => s.k === stack) || {}).cat;
  return (
    <div className="page fade" style={{ maxWidth: 980 }}>
      <h2 className="sec">{'>'} Vibe Scaffolder <span style={{ fontFamily: 'var(--term)', fontSize: 13, color: 'var(--tx-dim)' }}>新規制作</span></h2>
      <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: 16 }}>
        <div className="panelc">
          <div style={{ fontWeight: 600, marginBottom: 10, fontFamily: 'var(--term)' }}>$ describe el objetivo</div>
          <textarea className="ta" value={vibe} onChange={e => setVibe(e.target.value)} placeholder='Ej: "Landing premium para clínica dental en Madrid, paleta cálida…"' />
          <button className="btn pri" style={{ marginTop: 14 }} onClick={go}>{thinking ? '> procesando…' : '> Pre-rellenar con IA'}</button>
          {thinking && <span style={{ marginLeft: 10, color: 'var(--accent)', fontFamily: 'var(--term)' }}>{(AGENTS[agent] || {}).em} analizando…</span>}
          {done && (
            <div className="fade" style={{ marginTop: 16, background: 'var(--bg)', border: '1px solid var(--line)', borderRadius: 4, padding: 14, fontSize: 13, lineHeight: 1.65, fontFamily: 'var(--term)' }}>
              <b style={{ color: 'var(--accent)' }}>[ prompt generado ]</b><br />{genPrompt || ('Build a production-ready ' + (type || 'producto') + ' usando ' + (STACKS.find(s => s.k === stack) || { label: stack }).label + '. ' + (vibe || 'Estética coherente, accesible, imágenes del nicho, deploy-ready.'))}
            </div>
          )}
        </div>
        <div className="panelc">
          <div style={{ fontWeight: 600, marginBottom: 10, fontFamily: 'var(--term)' }}>daemon IA</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            {Object.entries(AGENTS).map(([k, a]) => (
              <button key={k} className={'tile' + (agent === k ? ' on' : '')} onClick={() => setAgent(k)} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 16, color: a.color }}>{a.em}</span><span style={{ fontSize: 13, fontWeight: 600, fontFamily: 'var(--term)' }}>{a.label}</span>
              </button>
            ))}
          </div>
          <div style={{ fontWeight: 600, margin: '16px 0 8px', fontFamily: 'var(--term)' }}>tipo de template 種類</div>
          <input className="ta" value={type} onChange={e => setType(e.target.value)} placeholder="SaaS Landing · E-commerce · Dashboard…" style={{ minHeight: 0, height: 38 }} />
        </div>
      </div>

      {/* MODO */}
      <h2 className="sec" style={{ margin: '26px 0 14px' }}>{'~'} Modo <span style={{ fontFamily: 'var(--term)', fontSize: 13, color: 'var(--tx-dim)' }}>方式</span></h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 10 }}>
        {M_MODES.map(m => (
          <button key={m.k} className={'tile' + (mode === m.k ? ' on' : '')} onClick={() => setMode(m.k)} style={{ textAlign: 'left' }}>
            <div style={{ fontWeight: 600, fontSize: 14 }}>{m.label} <span style={{ fontFamily: 'var(--term)', fontSize: 11, color: 'var(--tx-dim)' }}>{m.jp}</span></div>
            <div style={{ fontSize: 12, marginTop: 4, color: 'var(--tx-dim)', fontFamily: 'var(--term)', lineHeight: 1.5 }}>{m.desc}</div>
          </button>
        ))}
      </div>
      {(mode === 'recreate' || mode === 'adopt') && (
        <div className="panelc fade" style={{ marginTop: 12 }}>
          <div style={{ fontWeight: 600, marginBottom: 12, fontFamily: 'var(--term)' }}>referencia 参照</div>
          {mode === 'recreate' && (
            <div style={{ display: 'flex', gap: 6, marginBottom: 12, flexWrap: 'wrap' }}>
              {M_REF_KINDS.map(([k, l]) => <button key={k} className="tag" style={{ cursor: 'pointer', color: refKind === k ? 'var(--accent)' : 'var(--tx-dim)', borderColor: refKind === k ? 'var(--accent)' : 'var(--line)' }} onClick={() => setRefKind(k)}>{l}</button>)}
            </div>
          )}
          <div style={{ display: 'flex', gap: 10 }}>
            <input className="ta" style={{ minHeight: 0, height: 38, flex: 1 }} value={refVal} onChange={e => setRefVal(e.target.value)} placeholder={refKind === 'url' ? 'https://demo-template.com' : refKind === 'figma' ? 'figma.com/file/…?node-id=' : 'Ruta o examinar…'} />
            {refKind !== 'url' && refKind !== 'figma' && <button className="btn" onClick={examine}>📂 Examinar</button>}
          </div>
          <div style={{ marginTop: 12, display: 'flex', gap: 10, alignItems: 'center' }}>
            <button className="btn pri" onClick={() => { window.__tfRef = { value: refVal, kind: refKind }; onAnalyze && onAnalyze(); }}>{'>'} Analizar con IA</button>
            <span style={{ fontSize: 11.5, color: 'var(--tx-dim)', fontFamily: 'var(--term)' }}>{refKind === 'figma' ? 'Lee el frame vía MCP figma-context (es tu diseño).' : 'Detecta stack + estudia layout/paleta/tipo, multi-turno.'}</span>
          </div>
        </div>
      )}
      {mode === 'repo' && (
        <div className="panelc fade" style={{ marginTop: 12 }}>
          <div style={{ fontWeight: 600, marginBottom: 10, fontFamily: 'var(--term)' }}>repositorio github</div>
          <input className="ta" style={{ minHeight: 0, height: 38 }} value={repoId} onChange={e => setRepoId(e.target.value)} placeholder="owner/repo o https://github.com/owner/repo" />
          <div style={{ fontSize: 11, marginTop: 8, color: 'var(--tx-dim)', fontFamily: 'var(--term)' }}>No hace falta nombre: se usa el de la repo. gh repo clone con historial intacto.</div>
        </div>
      )}

      {/* STACK (oculto en modo repo, que no usa stack) */}
      {mode !== 'repo' && <>
      <h2 className="sec" style={{ margin: '26px 0 14px' }}>{'#'} Stack <span style={{ fontFamily: 'var(--term)', fontSize: 13, color: 'var(--tx-dim)' }}>基盤 · {STACKS.length}</span></h2>
      {Object.keys(groups).map(cat => {
        const open = openCats[cat] !== undefined ? openCats[cat] : (cat === selCat);
        return (
          <div key={cat} style={{ marginBottom: 10 }}>
            <button onClick={() => setOpenCats(o => ({ ...o, [cat]: !open }))} style={{ width: '100%', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8, background: 'var(--bg)', border: '1px solid var(--line)', borderRadius: 4, padding: '9px 12px', color: 'var(--tx-dim)', textAlign: 'left' }}>
              <span style={{ color: 'var(--accent)', transform: open ? 'rotate(90deg)' : 'none', transition: 'transform .15s', display: 'inline-block', width: 12 }}>▸</span>
              <span style={{ fontFamily: 'var(--term)', fontSize: 11, letterSpacing: '.06em', textTransform: 'uppercase', flex: 1 }}>{cat}</span>
              <span className="tag">{groups[cat].length}</span>
              {groups[cat].some(s => s.k === stack) && <span style={{ width: 6, height: 6, borderRadius: 99, background: 'var(--accent)', boxShadow: '0 0 6px var(--accent)' }} />}
            </button>
            {open && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(150px,1fr))', gap: 10, padding: '10px 2px 4px' }}>
                {groups[cat].map(s => (
                  <button key={s.k} className={'tile' + (stack === s.k ? ' on' : '')} onClick={() => setStack(s.k)}>
                    <div style={{ fontSize: 20, fontFamily: 'var(--term)', color: 'var(--accent)' }}>{s.em}</div>
                    <div style={{ fontWeight: 600, fontSize: 14, marginTop: 4 }}>{s.label}</div>
                    <div style={{ fontFamily: 'var(--term)', fontSize: 11, color: 'var(--tx-dim)' }}>{s.jp}</div>
                  </button>
                ))}
              </div>
            )}
          </div>
        );
      })}
      <div className="panelc" style={{ marginTop: 14 }}>
        <div style={{ fontWeight: 600, marginBottom: 8, fontFamily: 'var(--term)' }}>$ nombre del proyecto <span style={{ color: 'var(--tx-dim)' }}>名前</span></div>
        <input className="ta" value={pname} onChange={e => setPname(e.target.value)} placeholder="Ej: Aurora Dental · ~/Proyectos/themes/<slug>" style={{ minHeight: 0, height: 40 }} />
      </div>
      </>}

      {/* SETUP + EXTRAS */}
      <h2 className="sec" style={{ margin: '26px 0 14px' }}>{'='} Setup & Extras <span style={{ fontFamily: 'var(--term)', fontSize: 13, color: 'var(--tx-dim)' }}>基礎</span></h2>
      <div className="panelc" style={{ padding: '6px 20px 14px' }}>
        <MCheck label="npx autoskills 技能" sub="auto-instala skills del stack (a11y/SEO/design) en .claude/skills/" on={opts.autoskills} onToggle={() => tog('autoskills')} />
        <MCheck label="UI/UX Pro Max 高級UI" sub="shadcn/ui · Aceternity · Magic UI + sistema de diseño" on={opts.uipro} onToggle={() => tog('uipro')} />
        <MCheck label="Pre-configurar MCP servers 接続" sub="genera .mcp.json (filesystem · github · playwright · figma · themeforge…)" on={opts.mcp} onToggle={() => tog('mcp')} />
        <MCheck label="Documentación 文書" sub="documentation/ con guía de instalación + changelog" on={opts.docs} onToggle={() => tog('docs')} />
        <MCheck label="🐘 PostgreSQL en Docker DB" sub="contenedor postgres:17 + DATABASE_URL en .env (requiere Docker)" on={opts.postgres} onToggle={() => tog('postgres')} />
        <MCheck label="🔑 Licencias (pcreative anti-nulled) 認可" sub="verify-license + setup wizard según la familia del stack" on={opts.licensing} onToggle={() => tog('licensing')} />
        {opts.licensing && <div style={{ paddingLeft: 16, borderLeft: '2px solid var(--accent)', marginLeft: 6 }}>
          <MCheck label="└─ Crear repo gh <org>/<slug>" sub="gh repo create privado tras el scaffold (org en licensing.json)" on={opts.licensing_gh} onToggle={() => tog('licensing_gh')} />
          <MCheck label="└─ Forzar también en adopt / existing 強制" sub="por defecto licensing solo corre en scratch/recreate" on={opts.licensing_force} onToggle={() => tog('licensing_force')} />
        </div>}
      </div>

      <div className="panelc" style={{ marginTop: 14, display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontFamily: 'var(--term)', borderColor: 'var(--accent)' }}>
        <span style={{ color: 'var(--tx-dim)' }}><b style={{ color: 'var(--accent)' }}>{mode === 'repo' ? 'repo' : (STACKS.find(s => s.k === stack) || { label: stack }).label}</b> · {(M_MODES.find(m => m.k === mode) || { label: mode }).label} · {(AGENTS[agent] || { label: agent }).label}</span>
        <button className="btn pri" onClick={forge}>▶ Forjar proyecto</button>
      </div>
    </div>
  );
}

/* ---- Cost ---- */
const COST = (typeof window !== 'undefined' && window.__TF_DATA__ && window.__TF_DATA__.cost && window.__TF_DATA__.cost.by_agent && window.__TF_DATA__.cost.by_agent.length) ? window.__TF_DATA__.cost.by_agent : [{ k: 'claude', v: 12.77 }, { k: 'gemini', v: 7.34 }, { k: 'codex', v: 3.32 }, { k: 'opencode', v: 1.63 }];
function Cost() {
  const B = window.tfBridge;
  const [data, setData] = useState((window.__TF_DATA__ && window.__TF_DATA__.cost) || {});
  const rescan = () => { if (B && B.cost_data) B.cost_data().then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {} if (!r.error) setData(r); }); };
  const by = (data.by_agent && data.by_agent.length) ? data.by_agent : COST;
  const total = (data.total != null) ? data.total : by.reduce((s, d) => s + d.v, 0);
  const days = (data.days && data.days.length) ? data.days : Array.from({ length: 30 }, () => 0);
  const max = Math.max(0.01, ...days);
  const models = data.models || [];
  let acc = 0; const C = 2 * Math.PI * 70;
  return (
    <div className="page fade">
      <h2 className="sec">$ Coste de IA <span style={{ fontFamily: 'var(--term)', fontSize: 13, color: 'var(--tx-dim)' }}>費用追跡</span><button className="btn" style={{ float: 'right', padding: '4px 10px' }} onClick={rescan}>↻ Re-scan</button></h2>
      <div className="stats" style={{ marginBottom: 22 }}>
        {[['Σ', '$' + total.toFixed(2), 'total'], ['◴', '$' + (data.month != null ? data.month.toFixed(2) : '0.00'), 'este mes'], ['⊟', String(models.length), 'modelos'], ['⚡', String(data.tokens || '—'), 'tokens']].map(([e, n, l]) => (
          <div className="stat" key={l}><div className="em">{e}</div><div className="n">{n}</div><div className="l">{l}</div></div>
        ))}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 16 }}>
        <div className="panelc" style={{ textAlign: 'center' }}>
          <div style={{ fontWeight: 600, marginBottom: 10, fontFamily: 'var(--term)' }}>por daemon</div>
          <svg viewBox="0 0 180 180" style={{ width: 180, height: 180 }}>
            <circle cx="90" cy="90" r="70" fill="none" stroke="var(--bg)" strokeWidth="18" />
            {by.map(d => {
              const ag = AGENTS[d.k] || { color: 'var(--accent)' };
              const frac = total ? d.v / total : 0, dash = C * frac;
              const el = <circle key={d.k} cx="90" cy="90" r="70" fill="none" stroke={ag.color} strokeWidth="18" strokeDasharray={`${dash - 3} ${C}`} strokeDashoffset={-C * acc} transform="rotate(-90 90 90)" style={{ filter: `drop-shadow(0 0 4px ${ag.color})` }} />;
              acc += frac; return el;
            })}
            <text x="90" y="98" textAnchor="middle" style={{ fontFamily: 'var(--display)', fontSize: 30, fill: 'var(--accent)' }}>${total.toFixed(0)}</text>
          </svg>
          <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 7 }}>
            {by.map(d => { const ag = AGENTS[d.k] || { color: 'var(--accent)', em: '◆', label: d.k }; return (
              <div key={d.k} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5, fontFamily: 'var(--term)' }}>
                <span style={{ color: ag.color }}>{ag.em}</span><span style={{ flex: 1, textAlign: 'left' }}>{ag.label}</span><span style={{ color: 'var(--accent)' }}>${d.v.toFixed(2)}</span>
              </div>); })}
            {!by.length && <span style={{ color: 'var(--tx-dim)', fontFamily: 'var(--term)', fontSize: 12 }}>sin gasto registrado</span>}
          </div>
        </div>
        <div className="panelc">
          <div style={{ fontWeight: 600, marginBottom: 16, fontFamily: 'var(--term)' }}>gasto · últimos 30 días</div>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 3, height: 160 }}>
            {days.map((v, i) => (
              <div key={i} style={{ flex: 1, height: Math.max(2, (v / max * 100)) + '%', borderRadius: '2px 2px 0 0', background: 'linear-gradient(var(--accent),var(--accent2))', boxShadow: '0 0 6px rgba(0,255,65,0.4)' }} title={'$' + v.toFixed(2)} />
            ))}
          </div>
        </div>
      </div>
      <h2 className="sec" style={{ margin: '24px 0 12px' }}>⊟ Por modelo <span style={{ fontFamily: 'var(--term)', fontSize: 13, color: 'var(--tx-dim)' }}>模型</span></h2>
      <div className="panelc" style={{ padding: 0, overflow: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12.5, fontFamily: 'var(--term)' }}>
          <thead><tr style={{ background: 'var(--bg)' }}>{['Modelo', 'Daemon', 'Sesiones', 'In', 'Out', 'Precio', 'Coste'].map(h => <th key={h} style={{ textAlign: 'left', padding: '9px 12px', color: 'var(--tx-dim)', borderBottom: '1px solid var(--line)' }}>{h}</th>)}</tr></thead>
          <tbody>{models.length ? models.map((m, i) => <tr key={i} style={{ borderTop: '1px solid var(--line)' }}>
            <td style={{ padding: '8px 12px', color: 'var(--tx)' }}>{m.model}</td><td style={{ padding: '8px 12px', color: (AGENTS[m.agent] || {}).color || 'var(--tx-dim)' }}>{m.agent}</td>
            <td style={{ padding: '8px 12px' }}>{m.sessions}</td><td style={{ padding: '8px 12px', color: 'var(--tx-dim)' }}>{m.input}</td><td style={{ padding: '8px 12px', color: 'var(--tx-dim)' }}>{m.output}</td>
            <td style={{ padding: '8px 12px', color: 'var(--tx-dim)' }}>{m.rate}</td><td style={{ padding: '8px 12px', color: 'var(--accent)' }}>${m.cost.toFixed(2)}</td>
          </tr>) : <tr><td colSpan={7} style={{ padding: 22, textAlign: 'center', color: 'var(--tx-dim)' }}>// sin sesiones de IA registradas todavía</td></tr>}</tbody>
        </table>
      </div>
    </div>
  );
}

/* ---- Compare (terminales reales lado a lado) ---- */
function AgentPane({ k, url }) {
  const a = AGENTS[k] || { color: 'var(--accent)', em: '◆', label: k };
  return (
    <div className="panelc" style={{ padding: 0, overflow: 'hidden', borderColor: url ? a.color : 'var(--line)', display: 'flex', flexDirection: 'column', minHeight: 320 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px', borderBottom: '1px solid var(--line)', fontFamily: 'var(--term)' }}>
        <span style={{ color: a.color, fontSize: 15 }}>{a.em}</span>
        <span style={{ fontSize: 12.5, fontWeight: 600 }}>{a.label}</span>
        {!url && <span style={{ marginLeft: 'auto', width: 6, height: 6, borderRadius: 99, background: a.color, boxShadow: `0 0 8px ${a.color}` }} />}
      </div>
      {url ? <iframe src={url} style={{ flex: 1, width: '100%', minHeight: 280, border: 'none', background: '#040804' }} />
        : <div style={{ padding: 16, flex: 1, color: 'var(--tx-dim)', fontFamily: 'var(--term)' }}>// esperando terminal real…</div>}
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
  const [sel, setSel] = useState(Object.keys(AGENTS));
  const toggle = (k) => setSel(s => s.includes(k) ? s.filter(x => x !== k) : [...s, k]);
  const go = () => { if (!real || !prompt.trim()) return; setUrls({}); setProviders([]); window.tfBridge.compare(prompt).then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {} setProviders(r.providers || []); }); };
  const clear = () => { setUrls({}); setProviders([]); };
  const shownKeys = (providers.length ? providers : Object.keys(AGENTS)).filter(k => sel.includes(k));
  return (
    <div className="page fade">
      <h2 className="sec">⇄ Comparar agentes <span style={{ fontFamily: 'var(--term)', fontSize: 13, color: 'var(--tx-dim)' }}>比較</span></h2>
      <div className="panelc" style={{ display: 'flex', gap: 10, marginBottom: 12 }}>
        <input className="ta" style={{ minHeight: 0, padding: '11px 14px', flex: 1 }} value={prompt} onChange={e => setPrompt(e.target.value)} />
        <button className="btn pri" onClick={go}>{providers.length ? '↻ Re-run' : '▶ Ejecutar'}</button>
        <button className="btn" onClick={clear}>🧹 Limpiar</button>
      </div>
      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
        {Object.entries(AGENTS).map(([k, a]) => <button key={k} className={'tag' + (sel.includes(k) ? ' on' : '')} style={{ cursor: 'pointer', color: sel.includes(k) ? a.color : 'var(--tx-dim)', borderColor: sel.includes(k) ? a.color : 'var(--line)' }} onClick={() => toggle(k)}>{sel.includes(k) ? '☑' : '☐'} {a.em} {a.label}</button>)}
      </div>
      {!real && <div className="panelc" style={{ textAlign: 'center', color: 'var(--tx-dim)', fontFamily: 'var(--term)', marginBottom: 16 }}>// compare no disponible (sin puente)</div>}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {shownKeys.map(k => <AgentPane key={k} k={k} url={urls[k]} />)}
      </div>
    </div>
  );
}

/* ---- Operator (Hermes: Mission Control completo, 12 pestañas) ---- */
const PHASES = ['Plan', 'Crear', 'Build', 'QA', 'Empaquetar'];

/* ── helpers de puente ───────────────────────────────────────── */
function callB(name) {
  var args = Array.prototype.slice.call(arguments, 1);
  var B = window.tfBridge;
  if (!B || !B[name]) return Promise.resolve({ ok: false, error: 'sin puente' });
  try { return B[name].apply(B, args).then(function(j) { try { return JSON.parse(j); } catch (e) { return { ok: false, error: 'json' }; } }); }
  catch (e) { return Promise.resolve({ ok: false, error: '' + e }); }
}
function useHermesEvent(handler, deps) {
  useEffect(function() {
    var B = window.tfBridge;
    if (!B || !B.hermes_event || !B.hermes_event.connect) return;
    var cb = function(j) { var r = {}; try { r = JSON.parse(j); } catch (e) {} handler(r); };
    B.hermes_event.connect(cb);
    return function() { try { B.hermes_event.disconnect(cb); } catch (e) {} };
  }, deps || []);
}
var MX_FLD = { background: 'var(--bg)', border: '1px solid var(--line)', borderRadius: 4, padding: '6px 9px', color: 'var(--tx)', fontFamily: 'var(--term)', fontSize: 12, outline: 'none' };
var MX_SBTN = { cursor: 'pointer', padding: '6px 12px', borderRadius: 4, fontSize: 12, fontFamily: 'var(--term)', background: 'rgba(0,255,65,0.10)', border: '1px solid rgba(0,255,65,0.35)', color: 'var(--accent)' };
var MX_GBTN = { cursor: 'pointer', padding: '6px 12px', borderRadius: 4, fontSize: 12, fontFamily: 'var(--term)', background: 'transparent', border: '1px solid var(--line)', color: 'var(--tx-dim)' };
function MxOut({ text }) {
  if (!text) return null;
  return <div className="panelc" style={{ padding: 12, marginTop: 12, fontSize: 11, fontFamily: 'var(--term)', color: 'var(--tx-dim)', whiteSpace: 'pre-wrap', maxHeight: 260, overflow: 'auto' }}>{text}</div>;
}
function MxSec({ title, children }) {
  return <div className="panelc" style={{ padding: 16, marginBottom: 16 }}>
    <div style={{ fontFamily: 'var(--term)', fontSize: 11, letterSpacing: '.06em', textTransform: 'uppercase', color: 'var(--accent)', marginBottom: 12 }}>{title}</div>
    {children}
  </div>;
}

/* ── 🔌 Proveedor ─────────────────────────────────────────────── */
function ProviderTab() {
  var [data, setData] = useState(null);
  var [key, setKey] = useState('');
  var [model, setModel] = useState('');
  var [sel, setSel] = useState('');
  var [out, setOut] = useState('');
  var [login, setLogin] = useState(false);
  var load = function() { callB('hermes_providers').then(function(r) { if (r.ok) { setData(r); var cur = r.current_provider || (r.providers[0] && r.providers[0].key); setSel(cur); setModel(r.current_model || ''); } }); };
  useEffect(function() { load(); }, []);
  useHermesEvent(function(r) { if (r.op === 'test_brain' && r.done) setOut(function(o) { return o + '\n' + (r.out || (r.ok ? 'OK' : 'fallo')); }); });
  if (!data) return <div style={{ padding: 20, fontFamily: 'var(--term)', color: 'var(--tx-dim)' }}>// cargando proveedores…</div>;
  var spec = data.providers.find(function(p) { return p.key === sel; }) || data.providers[0];
  return <div>
    <MxSec title="ESTADO ACTUAL · 現状">
      <div style={{ fontFamily: 'var(--term)', fontSize: 12.5 }}>cerebro: <b style={{ color: 'var(--accent)' }}>{data.current_provider || '—'}</b> · <b>{data.current_model || '—'}</b></div>
    </MxSec>
    <MxSec title="CONFIGURAR CEREBRO · 頭脳">
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
        <label style={{ fontFamily: 'var(--term)', fontSize: 12, color: 'var(--tx-dim)' }}>proveedor{' '}
          <select value={sel} onChange={function(e) { setSel(e.target.value); setModel(''); }} style={MX_FLD}>
            {data.providers.map(function(p) { return <option key={p.key} value={p.key}>{p.label}{p.has_auth ? ' ✓' : ''}</option>; })}
          </select></label>
        <label style={{ fontFamily: 'var(--term)', fontSize: 12, color: 'var(--tx-dim)' }}>modelo{' '}
          <input list="np-models" value={model} onChange={function(e) { setModel(e.target.value); }} placeholder="modelo…" style={{ ...MX_FLD, width: 220 }} />
          <datalist id="np-models">{(spec.models || []).map(function(m) { return <option key={m} value={m} />; })}</datalist></label>
      </div>
      <div style={{ fontSize: 11.5, marginTop: 8, lineHeight: 1.5, color: 'var(--tx-dim)', fontFamily: 'var(--term)' }}>{spec.note}</div>
      <div style={{ display: 'flex', gap: 10, marginTop: 12, flexWrap: 'wrap', alignItems: 'center' }}>
        {spec.auth === 'api'
          ? <><input type="password" value={key} onChange={function(e) { setKey(e.target.value); }} placeholder={'API key de ' + spec.key} style={{ ...MX_FLD, width: 260 }} />
            <button style={MX_GBTN} onClick={function() { callB('hermes_save_key', spec.key, key).then(function(r) { setOut(function(o) { return o + '\n' + (r.out || (r.ok ? 'key guardada' : r.error)); }); setKey(''); load(); }); }}>Guardar key</button></>
          : <button style={MX_GBTN} onClick={function() { setLogin(true); callB('hermes_login', spec.key); }}>🔐 Login OAuth</button>}
        <button style={MX_SBTN} onClick={function() { callB('hermes_set_model', spec.key, model).then(function(r) { setOut(function(o) { return o + '\n' + (r.out || (r.ok ? 'modelo aplicado' : r.error)); }); load(); }); }}>Usar este modelo</button>
        <button style={MX_GBTN} onClick={function() { setOut(function(o) { return o + '\n▶ probando…'; }); callB('hermes_test_brain'); }}>Probar</button>
        <button style={MX_GBTN} onClick={load}>↻</button>
      </div>
    </MxSec>
    {login && <HermesFrame kind="hermes-login" onStart={function() {}} />}
    <MxOut text={out} />
  </div>;
}

/* ── 🎨 Imágenes (Runware) ────────────────────────────────────── */
function ImagesTab() {
  var [st, setSt] = useState(null);
  var [key, setKey] = useState('');
  var [arch, setArch] = useState('');
  var [q, setQ] = useState('');
  var [models, setModels] = useState([]);
  var [air, setAir] = useState('');
  var [prompt, setPrompt] = useState('matrix digital rain, glitch terminal');
  var [img, setImg] = useState('');
  var [out, setOut] = useState('');
  var load = function() { callB('runware_status').then(setSt); };
  useEffect(function() { load(); }, []);
  useHermesEvent(function(r) {
    if (r.op === 'runware_search' && r.done) { setModels(r.models || []); setOut(function(o) { return o + '\n' + (r.ok ? (r.models || []).length + ' modelos' : r.error); }); }
    if (r.op === 'runware_test' && r.done) { if (r.url) setImg(r.url); setOut(function(o) { return o + '\n' + (r.ok ? '✓ imagen generada' : '✗ ' + r.error); }); }
  });
  if (!st) return <div style={{ padding: 20, fontFamily: 'var(--term)', color: 'var(--tx-dim)' }}>// cargando…</div>;
  if (!st.ok) return <div className="panelc" style={{ padding: 20, fontFamily: 'var(--term)', color: '#ffb000' }}>// Runware no disponible: {st.error}</div>;
  return <div>
    <MxSec title="API KEY RUNWARE · 鍵">
      <div style={{ fontFamily: 'var(--term)', fontSize: 12, color: st.has_key ? '#00d9ff' : 'var(--tx-dim)' }}>● {st.has_key ? 'key configurada' : 'sin key'}</div>
      <div style={{ display: 'flex', gap: 10, marginTop: 10 }}>
        <input type="password" value={key} onChange={function(e) { setKey(e.target.value); }} placeholder="RUNWARE_API_KEY" style={{ ...MX_FLD, width: 280 }} />
        <button style={MX_GBTN} onClick={function() { callB('runware_save_key', key).then(function() { setKey(''); load(); }); }}>Guardar</button>
      </div>
    </MxSec>
    <MxSec title="BUSCAR MODELO · 検索">
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
        <select value={arch} onChange={function(e) { setArch(e.target.value); }} style={MX_FLD}><option value="">arquitectura…</option>{(st.architectures || []).map(function(a) { return <option key={a} value={a}>{a}</option>; })}</select>
        <input value={q} onChange={function(e) { setQ(e.target.value); }} placeholder="ej: flux realistic" style={{ ...MX_FLD, width: 220 }} />
        <button style={MX_SBTN} onClick={function() { setOut(function(o) { return o + '\n▶ buscando…'; }); callB('runware_search', q, arch); }}>Buscar</button>
      </div>
      {models.length > 0 && <div className="panelc" style={{ marginTop: 10, maxHeight: 180, overflow: 'auto', padding: 6 }}>
        {models.map(function(m) { return <div key={m.air} onClick={function() { setAir(m.air); }} style={{ cursor: 'pointer', padding: '6px 8px', borderRadius: 4, fontSize: 11.5, fontFamily: 'var(--term)', background: air === m.air ? 'rgba(0,255,65,0.12)' : 'transparent' }}>
          <span>{m.name}</span> <span style={{ color: 'var(--tx-dim)' }}>· {m.architecture}</span></div>; })}
      </div>}
      <div style={{ display: 'flex', gap: 10, marginTop: 10, alignItems: 'center' }}>
        <span style={{ fontFamily: 'var(--term)', fontSize: 11, color: 'var(--tx-dim)' }}>defecto: {st.default || '—'}{air ? ' → ' + air : ''}</span>
        <button style={MX_GBTN} disabled={!air} onClick={function() { callB('runware_set_default', air).then(load); }}>Usar por defecto</button>
      </div>
    </MxSec>
    <MxSec title="PROBAR GENERACIÓN · 試">
      <div style={{ display: 'flex', gap: 10 }}>
        <input value={prompt} onChange={function(e) { setPrompt(e.target.value); }} style={{ ...MX_FLD, flex: 1 }} />
        <button style={MX_SBTN} onClick={function() { setOut(function(o) { return o + '\n▶ generando…'; }); callB('runware_test', prompt, air); }}>Probar</button>
      </div>
      {img && <img src={img} alt="" style={{ marginTop: 12, maxWidth: '100%', borderRadius: 4, border: '1px solid var(--line)' }} />}
    </MxSec>
    <MxOut text={out} />
  </div>;
}

/* ── 🤖 Agentes (skills) ──────────────────────────────────────── */
function AgentsTab() {
  var [skills, setSkills] = useState([]);
  var [webonly, setWebonly] = useState(false);
  var [detail, setDetail] = useState('');
  var [q, setQ] = useState('');
  var [iid, setIid] = useState('');
  var [out, setOut] = useState('');
  var [pack, setPack] = useState(null);
  var [picked, setPicked] = useState({});
  var load = function() { callB('hermes_skills', webonly).then(function(r) { if (r.ok) setSkills(r.skills); }); };
  useEffect(function() { load(); }, [webonly]);
  useHermesEvent(function(r) {
    if (r.op === 'skills_search' && r.done) setOut(function(o) { return o + '\n' + (r.out || ''); });
    if (r.op === 'install_skill') { if (r.line) setOut(function(o) { return (o + r.line).slice(-6000); }); if (r.done) { setOut(function(o) { return o + '\n■ instalación terminada'; }); load(); } }
    if (r.op === 'install_pack') { if (r.line) setOut(function(o) { return (o + r.line).slice(-6000); }); if (r.done) { setOut(function(o) { return o + '\n■ pack instalado'; }); load(); } }
  });
  var openPack = function() { callB('hermes_skill_pack').then(function(r) { setPack(r.groups || []); var p = {}; (r.groups || []).forEach(function(g) { g.items.forEach(function(it) { p[it.id] = true; }); }); setPicked(p); }); };
  return <div>
    <MxSec title="AGENTES INSTALADOS · 代理">
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center', marginBottom: 10 }}>
        <label style={{ fontFamily: 'var(--term)', fontSize: 12, color: 'var(--tx-dim)' }}><input type="checkbox" checked={webonly} onChange={function(e) { setWebonly(e.target.checked); }} /> solo web/diseño</label>
        <input value={q} onChange={function(e) { setQ(e.target.value); }} placeholder="buscar en el registro…" style={{ ...MX_FLD, width: 220 }} />
        <button style={MX_GBTN} onClick={function() { setOut(function(o) { return o + '\n▶ buscando «' + q + '»…'; }); callB('hermes_skills_search', q); }}>Buscar registro</button>
        <button style={MX_GBTN} onClick={function() { callB('hermes_seed_web_agents').then(function(r) { setOut(function(o) { return o + '\n' + (r.ok ? 'sembrados: ' + (r.names || []).join(', ') : r.error); }); load(); }); }}>Sembrar web</button>
        <button style={MX_GBTN} onClick={openPack}>📦 Pack web</button>
        <button style={MX_GBTN} onClick={load}>↻</button>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <div className="panelc" style={{ maxHeight: 240, overflow: 'auto', padding: 6 }}>
          {skills.length ? skills.map(function(s) { return <div key={s.path} onClick={function() { callB('hermes_skill_detail', s.path).then(function(r) { setDetail(r.text || ''); }); }} style={{ cursor: 'pointer', padding: '7px 9px', borderRadius: 4, fontSize: 12, fontFamily: 'var(--term)' }}>
            {s.tf ? '⭐ ' : ''}<b>{s.name}</b><div style={{ fontSize: 10.5, color: 'var(--tx-dim)' }}>{s.category}</div></div>; })
            : <div style={{ padding: 16, fontFamily: 'var(--term)', color: 'var(--tx-dim)' }}>// sin skills</div>}
        </div>
        <div className="panelc" style={{ maxHeight: 240, overflow: 'auto', padding: 10, fontSize: 10.5, fontFamily: 'var(--term)', whiteSpace: 'pre-wrap', color: 'var(--tx-dim)' }}>{detail || '// selecciona un agente'}</div>
      </div>
      <div style={{ display: 'flex', gap: 10, marginTop: 10 }}>
        <input value={iid} onChange={function(e) { setIid(e.target.value); }} placeholder="id/url a instalar — ej: official/devops/docker" style={{ ...MX_FLD, flex: 1 }} />
        <button style={MX_SBTN} onClick={function() { setOut(function(o) { return o + '\n▶ instalando…'; }); callB('hermes_install_skill', iid); }}>Instalar</button>
      </div>
    </MxSec>
    {pack && <MxSec title="PACK CURADO · 束">
      <div style={{ maxHeight: 220, overflow: 'auto' }}>
        {pack.map(function(g) { return <div key={g.domain} style={{ marginBottom: 8 }}>
          <div style={{ fontFamily: 'var(--term)', fontSize: 11, color: 'var(--accent)' }}>{g.domain}</div>
          {g.items.map(function(it) { return <label key={it.id} style={{ display: 'block', fontFamily: 'var(--term)', fontSize: 11.5, padding: '2px 0' }}>
            <input type="checkbox" checked={!!picked[it.id]} onChange={function(e) { setPicked(function(p) { var np = Object.assign({}, p); np[it.id] = e.target.checked; return np; }); }} /> {it.label}</label>; })}
        </div>; })}
      </div>
      <button style={MX_SBTN} onClick={function() { var ids = Object.keys(picked).filter(function(k) { return picked[k]; }).join(','); setOut(function(o) { return o + '\n▶ instalando pack…'; }); callB('hermes_install_pack', ids); setPack(null); }}>📥 Instalar seleccionadas</button>
    </MxSec>}
    <MxOut text={out} />
  </div>;
}

/* ── ➕ Crear agente ──────────────────────────────────────────── */
function CreateTab() {
  var [name, setName] = useState('');
  var [stacks, setStacks] = useState('');
  var [spec, setSpec] = useState('');
  var [body, setBody] = useState('');
  var [out, setOut] = useState('');
  useHermesEvent(function(r) { if (r.op === 'draft_skill' && r.done) { if (r.ok && r.out) setBody(r.out); setOut(function(o) { return o + '\n' + (r.ok ? '✓ redactado' : '✗ ' + (r.out || '')); }); } });
  return <div>
    <MxSec title="NUEVO AGENTE · 新規">
      <div style={{ display: 'grid', gap: 10 }}>
        <input value={name} onChange={function(e) { setName(e.target.value); }} placeholder="nombre — ej: shopify-pro" style={MX_FLD} />
        <input value={stacks} onChange={function(e) { setStacks(e.target.value); }} placeholder="stacks base (separados por coma)" style={MX_FLD} />
        <input value={spec} onChange={function(e) { setSpec(e.target.value); }} placeholder="especialidad — qué hace y cuándo usarlo" style={MX_FLD} />
      </div>
      <div style={{ display: 'flex', gap: 10, marginTop: 10 }}>
        <button style={MX_GBTN} onClick={function() { callB('hermes_skill_template', name, stacks, spec).then(function(r) { if (r.ok) setBody(r.template); }); }}>Plantilla</button>
        <button style={MX_GBTN} onClick={function() { setOut(function(o) { return o + '\n▶ Hermes redactando…'; }); callB('hermes_skill_draft_ai', name, stacks, spec); }}>Redactar con IA</button>
        <button style={MX_SBTN} onClick={function() { callB('hermes_skill_save', name, body).then(function(r) { setOut(function(o) { return o + '\n' + (r.ok ? '✓ guardado en ' + r.path : '✗ ' + r.error); }); }); }}>Guardar skill</button>
      </div>
    </MxSec>
    <textarea value={body} onChange={function(e) { setBody(e.target.value); }} placeholder="El SKILL.md aparecerá aquí (editable)…" style={{ ...MX_FLD, width: '100%', minHeight: 280, fontSize: 11.5, lineHeight: 1.5 }} />
    <MxOut text={out} />
  </div>;
}

/* ── 🧠 Memoria ───────────────────────────────────────────────── */
function MxMemFile({ label, value, max, onSave }) {
  var [v, setV] = useState(value || '');
  var [msg, setMsg] = useState('');
  return <div className="panelc" style={{ padding: 12, flex: 1 }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <div style={{ fontFamily: 'var(--term)', fontSize: 11, letterSpacing: '.06em', textTransform: 'uppercase', color: 'var(--accent)' }}>{label}</div>
      <span style={{ fontFamily: 'var(--term)', fontSize: 10.5, color: v.length > max ? '#ffb000' : 'var(--tx-dim)' }}>{v.length}/{max}</span>
    </div>
    <textarea value={v} onChange={function(e) { setV(e.target.value); }} style={{ ...MX_FLD, width: '100%', minHeight: 160, marginTop: 8, fontSize: 11.5 }} />
    <button style={{ ...MX_GBTN, marginTop: 8 }} onClick={function() { onSave(v).then(function(r) { setMsg(r.ok ? '✓ guardado' : '✗ ' + r.error); setTimeout(function() { setMsg(''); }, 2000); }); }}>Guardar {msg}</button>
  </div>;
}
function MemoryTab() {
  var [d, setD] = useState(null);
  var [note, setNote] = useState('');
  var load = function() { callB('hermes_memory').then(setD); };
  useEffect(function() { load(); }, []);
  if (!d) return <div style={{ padding: 20, fontFamily: 'var(--term)', color: 'var(--tx-dim)' }}>// cargando memoria…</div>;
  if (!d.ok) return <div className="panelc" style={{ padding: 20, fontFamily: 'var(--term)', color: '#ffb000' }}>// {d.error}</div>;
  var lim = d.limits || {};
  return <div>
    <div style={{ display: 'flex', gap: 14, marginBottom: 16, flexWrap: 'wrap' }}>
      <MxMemFile label="MEMORY.md · エージェント" value={d.memory} max={lim['MEMORY.md'] || 2200} onSave={function(v) { return callB('hermes_memory_save', 'MEMORY.md', v); }} />
      <MxMemFile label="USER.md · 利用者" value={d.user} max={lim['USER.md'] || 1375} onSave={function(v) { return callB('hermes_memory_save', 'USER.md', v); }} />
    </div>
    <MxSec title="NOTAS POR PROYECTO · 案件">
      <div style={{ display: 'grid', gridTemplateColumns: '240px 1fr', gap: 12 }}>
        <div className="panelc" style={{ maxHeight: 200, overflow: 'auto', padding: 6 }}>
          {(d.projects || []).length ? d.projects.map(function(p) { return <div key={p.path} onClick={function() { callB('hermes_project_note', p.path).then(function(r) { setNote(r.text || ''); }); }} style={{ cursor: 'pointer', padding: '6px 8px', borderRadius: 4, fontSize: 12, fontFamily: 'var(--term)' }}>{p.name}</div>; })
            : <div style={{ padding: 12, fontFamily: 'var(--term)', color: 'var(--tx-dim)' }}>// sin .hermes.md</div>}
        </div>
        <div className="panelc" style={{ maxHeight: 200, overflow: 'auto', padding: 10, fontSize: 10.5, fontFamily: 'var(--term)', whiteSpace: 'pre-wrap', color: 'var(--tx-dim)' }}>{note || '// selecciona un proyecto'}</div>
      </div>
    </MxSec>
    <MxSec title="SESIONES · 履歴"><div style={{ fontFamily: 'var(--term)', fontSize: 11, whiteSpace: 'pre-wrap', color: 'var(--tx-dim)' }}>{d.sessions || '—'}</div></MxSec>
  </div>;
}

/* ── 📊 Kanban ────────────────────────────────────────────────── */
function KanbanTab() {
  var [boards, setBoards] = useState([]);
  var [board, setBoard] = useState('');
  var [tasks, setTasks] = useState([]);
  var [nt, setNt] = useState({ title: '', body: '', priority: '', skill: '' });
  var [out, setOut] = useState('');
  useEffect(function() { callB('kanban_boards').then(function(r) { if (r.ok) { setBoards(r.boards); if (r.boards[0]) setBoard(r.boards[0]); } }); }, []);
  var loadTasks = function(b) { callB('kanban_tasks', b || board).then(function(r) { if (r.ok) setTasks(r.tasks); }); };
  useEffect(function() { if (board) loadTasks(board); }, [board]);
  useHermesEvent(function(r) { if (r.op === 'kanban_dispatch') { if (r.line) setOut(function(o) { return (o + r.line).slice(-6000); }); if (r.done) { setOut(function(o) { return o + '\n■ dispatch terminado'; }); loadTasks(); } } });
  return <div>
    <MxSec title="TABLERO · 板">
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
        <select value={board} onChange={function(e) { setBoard(e.target.value); }} style={MX_FLD}>{boards.length ? boards.map(function(b) { return <option key={b} value={b}>{b}</option>; }) : <option value="">(sin tableros)</option>}</select>
        <button style={MX_SBTN} onClick={function() { setOut(function(o) { return o + '\n▶ dispatch…'; }); callB('kanban_dispatch', board); }}>▶ Dispatch</button>
        <button style={MX_GBTN} onClick={function() { loadTasks(); }}>↻</button>
      </div>
      <div className="panelc" style={{ marginTop: 10, padding: 0, overflow: 'hidden' }}>
        {tasks.length ? tasks.map(function(t) { return <div key={t.id} style={{ display: 'flex', gap: 10, padding: '8px 12px', borderBottom: '1px solid var(--line)', fontSize: 12, fontFamily: 'var(--term)' }}>
          <span style={{ width: 60, color: 'var(--tx-dim)' }}>{t.id}</span>
          <span style={{ flex: 1 }}>{t.title}</span>
          <span style={{ color: 'var(--accent)' }}>{t.status}</span>
          <span style={{ width: 90, textAlign: 'right', color: 'var(--tx-dim)' }}>{t.assignee}</span>
          <span style={{ width: 60, textAlign: 'right', color: 'var(--tx-dim)' }}>{t.priority}</span>
        </div>; }) : <div style={{ padding: 16, fontFamily: 'var(--term)', color: 'var(--tx-dim)' }}>// sin tareas</div>}
      </div>
    </MxSec>
    <MxSec title="NUEVA TAREA · 新規">
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <input value={nt.title} onChange={function(e) { setNt(Object.assign({}, nt, { title: e.target.value })); }} placeholder="título" style={MX_FLD} />
        <select value={nt.priority} onChange={function(e) { setNt(Object.assign({}, nt, { priority: e.target.value })); }} style={MX_FLD}><option value="">prioridad…</option>{['low', 'medium', 'high', 'urgent'].map(function(p) { return <option key={p} value={p}>{p}</option>; })}</select>
        <input value={nt.skill} onChange={function(e) { setNt(Object.assign({}, nt, { skill: e.target.value })); }} placeholder="skill (opcional)" style={MX_FLD} />
        <input value={nt.body} onChange={function(e) { setNt(Object.assign({}, nt, { body: e.target.value })); }} placeholder="detalle (opcional)" style={MX_FLD} />
      </div>
      <button style={{ ...MX_SBTN, marginTop: 10 }} onClick={function() { callB('kanban_create', board, nt.title, nt.body, nt.priority, nt.skill).then(function(r) { setOut(function(o) { return o + '\n' + (r.ok ? '✓ creada' : '✗ ' + (r.out || r.error)); }); setNt({ title: '', body: '', priority: '', skill: '' }); loadTasks(); }); }}>Crear tarea</button>
    </MxSec>
    <MxOut text={out} />
  </div>;
}

/* ── ⏰ Cron ──────────────────────────────────────────────────── */
function CronTab() {
  var [jobs, setJobs] = useState([]);
  var [sel, setSel] = useState('');
  var [f, setF] = useState({ schedule: '', prompt: '', skill: '', deliver: 'local', name: '' });
  var [out, setOut] = useState('');
  var load = function() { callB('cron_jobs').then(function(r) { if (r.ok) setJobs(r.jobs); }); };
  useEffect(function() { load(); }, []);
  var op = function(a) { if (!sel) return; if (a === 'remove' && !confirm('¿Eliminar el job?')) return; callB('cron_op', a, sel).then(function(r) { setOut(function(o) { return o + '\n' + (r.ok ? '✓ ' + a : '✗ ' + r.out); }); load(); }); };
  return <div>
    <MxSec title="MISIONES PROGRAMADAS · 予定">
      <div className="panelc" style={{ padding: 0, overflow: 'hidden' }}>
        {jobs.length ? jobs.map(function(j) { return <div key={j.id} onClick={function() { setSel(j.id); }} style={{ cursor: 'pointer', display: 'flex', gap: 10, padding: '8px 12px', borderBottom: '1px solid var(--line)', fontSize: 12, fontFamily: 'var(--term)', background: sel === j.id ? 'rgba(0,255,65,0.10)' : 'transparent' }}>
          <span>{j.paused ? '⏸' : '▶'}</span>
          <span style={{ width: 120 }}>{j.schedule}</span>
          <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{j.name || j.prompt}</span>
          <span style={{ width: 120, textAlign: 'right', color: 'var(--tx-dim)' }}>{j.next}</span>
        </div>; }) : <div style={{ padding: 16, fontFamily: 'var(--term)', color: 'var(--tx-dim)' }}>// sin jobs</div>}
      </div>
      <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
        <button style={MX_GBTN} onClick={function() { op('pause'); }}>⏸ Pausar</button>
        <button style={MX_GBTN} onClick={function() { op('resume'); }}>▶ Reanudar</button>
        <button style={MX_GBTN} onClick={function() { op('run'); }}>⚡ Ejecutar</button>
        <button style={{ ...MX_GBTN, color: '#ffb000' }} onClick={function() { op('remove'); }}>🗑 Eliminar</button>
        <button style={{ ...MX_GBTN, marginLeft: 'auto' }} onClick={load}>↻</button>
      </div>
    </MxSec>
    <MxSec title="PROGRAMAR · 設定">
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <input value={f.schedule} onChange={function(e) { setF(Object.assign({}, f, { schedule: e.target.value })); }} placeholder="cuándo — every 1d · 30m · 0 9 * * 1-5" style={MX_FLD} />
        <input value={f.name} onChange={function(e) { setF(Object.assign({}, f, { name: e.target.value })); }} placeholder="nombre (opcional)" style={MX_FLD} />
        <input value={f.skill} onChange={function(e) { setF(Object.assign({}, f, { skill: e.target.value })); }} placeholder="skill — ej: themeforge-operator" style={MX_FLD} />
        <select value={f.deliver} onChange={function(e) { setF(Object.assign({}, f, { deliver: e.target.value })); }} style={MX_FLD}>{['local', 'origin', 'telegram', 'discord', 'slack', 'email', 'all'].map(function(d) { return <option key={d} value={d}>{d}</option>; })}</select>
      </div>
      <textarea value={f.prompt} onChange={function(e) { setF(Object.assign({}, f, { prompt: e.target.value })); }} placeholder="tarea / prompt…" style={{ ...MX_FLD, width: '100%', minHeight: 70, marginTop: 10 }} />
      <button style={{ ...MX_SBTN, marginTop: 10 }} onClick={function() { callB('cron_create', f.schedule, f.prompt, f.skill, f.deliver, f.name).then(function(r) { setOut(function(o) { return o + '\n' + (r.ok ? '✓ programada' : '✗ ' + (r.out || r.error)); }); if (r.ok) setF({ schedule: '', prompt: '', skill: '', deliver: 'local', name: '' }); load(); }); }}>Programar</button>
    </MxSec>
    <MxOut text={out} />
  </div>;
}

/* ── 📲 Remoto (gateway) ──────────────────────────────────────── */
function RemoteTab() {
  var [plats, setPlats] = useState([]);
  var [plat, setPlat] = useState('');
  var [target, setTarget] = useState('');
  var [msg, setMsg] = useState('');
  var [pcode, setPcode] = useState({ plat: '', code: '' });
  var [out, setOut] = useState('');
  var [setup, setSetup] = useState(false);
  useEffect(function() { callB('gateway_platforms').then(function(r) { if (r.ok) { setPlats(r.platforms); if (r.platforms[0]) setPlat(r.platforms[0].key); } }); }, []);
  useHermesEvent(function(r) { if (r.op === 'gateway_send' && r.done) setOut(function(o) { return o + '\n' + (r.ok ? '✓ enviado' : '✗ ' + r.out); }); });
  var run = function(slot) {
    var args = Array.prototype.slice.call(arguments, 1);
    return callB.apply(null, [slot].concat(args)).then(function(r) { setOut(function(o) { return (o + '\n' + (r.out || (r.ok ? 'ok' : r.error))).slice(-6000); }); });
  };
  var hint = (plats.find(function(p) { return p.key === plat; }) || {}).hint;
  return <div>
    <MxSec title="SERVICIO GATEWAY · 接続">
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <button style={MX_SBTN} onClick={function() { setSetup(true); }}>⚙ Configurar plataformas</button>
        <button style={MX_GBTN} onClick={function() { run('gateway_op', 'status'); }}>Estado</button>
        <button style={MX_GBTN} onClick={function() { run('gateway_op', 'install'); }}>Instalar servicio</button>
        <button style={MX_GBTN} onClick={function() { run('gateway_op', 'start'); }}>Arrancar</button>
        <button style={MX_GBTN} onClick={function() { run('gateway_op', 'stop'); }}>Parar</button>
      </div>
      {setup && <HermesFrame kind="hermes-gateway" onStart={function() { callB('gateway_setup'); }} />}
    </MxSec>
    <MxSec title="ENVIAR MENSAJE · 送信">
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
        <select value={plat} onChange={function(e) { setPlat(e.target.value); }} style={MX_FLD}>{plats.map(function(p) { return <option key={p.key} value={p.key}>{p.key}</option>; })}</select>
        <button style={MX_GBTN} onClick={function() { run('gateway_targets'); }}>Ver targets</button>
      </div>
      <div style={{ fontSize: 11, marginTop: 6, color: 'var(--tx-dim)', fontFamily: 'var(--term)' }}>{hint}</div>
      <div style={{ display: 'flex', gap: 10, marginTop: 10 }}>
        <input value={target} onChange={function(e) { setTarget(e.target.value); }} placeholder="destino — telegram · discord:#ops · slack:#eng" style={{ ...MX_FLD, width: 240 }} />
        <input value={msg} onChange={function(e) { setMsg(e.target.value); }} placeholder="mensaje de prueba" style={{ ...MX_FLD, flex: 1 }} />
        <button style={MX_SBTN} onClick={function() { setOut(function(o) { return o + '\n▶ enviando…'; }); callB('gateway_send', target, msg); }}>Enviar</button>
      </div>
    </MxSec>
    <MxSec title="PAIRING · 承認">
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
        <button style={MX_GBTN} onClick={function() { run('pairing_list'); }}>Ver pairings</button>
        <input value={pcode.plat} onChange={function(e) { setPcode(Object.assign({}, pcode, { plat: e.target.value })); }} placeholder="plataforma" style={{ ...MX_FLD, width: 120 }} />
        <input value={pcode.code} onChange={function(e) { setPcode(Object.assign({}, pcode, { code: e.target.value })); }} placeholder="código" style={{ ...MX_FLD, width: 120 }} />
        <button style={MX_SBTN} onClick={function() { run('pairing_approve', pcode.plat, pcode.code); }}>Aprobar</button>
      </div>
    </MxSec>
    <MxOut text={out} />
  </div>;
}

/* ── 🛡️ Avanzado ──────────────────────────────────────────────── */
function AdvancedTab() {
  var [sec, setSec] = useState({ backend: 'local', mode: 'smart' });
  var [out, setOut] = useState('');
  var [fb, setFb] = useState(false);
  useEffect(function() { callB('hermes_security').then(function(r) { if (r.ok) setSec({ backend: r.backend, mode: r.mode }); }); }, []);
  useHermesEvent(function(r) { if (r.op === 'insights' && r.done) setOut(function(o) { return o + '\n' + (r.out || ''); }); });
  var run = function(slot) {
    var args = Array.prototype.slice.call(arguments, 1);
    return callB.apply(null, [slot].concat(args)).then(function(r) { setOut(function(o) { return (o + '\n' + (r.out || (r.ok ? 'ok' : r.error))).slice(-6000); }); });
  };
  return <div>
    <MxSec title="AISLAMIENTO &amp; SEGURIDAD · 隔離">
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
        <label style={{ fontFamily: 'var(--term)', fontSize: 12, color: 'var(--tx-dim)' }}>backend{' '}
          <select value={sec.backend} onChange={function(e) { setSec(Object.assign({}, sec, { backend: e.target.value })); }} style={MX_FLD}>{['local', 'docker', 'ssh', 'modal', 'daytona', 'singularity'].map(function(b) { return <option key={b} value={b}>{b}</option>; })}</select></label>
        <label style={{ fontFamily: 'var(--term)', fontSize: 12, color: 'var(--tx-dim)' }}>aprobaciones{' '}
          <select value={sec.mode} onChange={function(e) { setSec(Object.assign({}, sec, { mode: e.target.value })); }} style={MX_FLD}>{['manual', 'smart', 'off'].map(function(m) { return <option key={m} value={m}>{m}</option>; })}</select></label>
        <button style={MX_SBTN} onClick={function() { run('hermes_security_apply', sec.backend, sec.mode); }}>Aplicar seguridad</button>
      </div>
    </MxSec>
    <MxSec title="PORTAL DE HERRAMIENTAS · 道具">
      <div style={{ display: 'flex', gap: 8 }}>
        <button style={MX_GBTN} onClick={function() { run('hermes_portal', 'status'); }}>Estado del portal</button>
        <button style={MX_GBTN} onClick={function() { run('hermes_portal', 'tools'); }}>Herramientas</button>
      </div>
    </MxSec>
    <MxSec title="PERFIL &amp; BUNDLE · 束">
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <button style={MX_GBTN} onClick={function() { run('hermes_profile_create'); }}>Crear perfil themeforge</button>
        <button style={MX_GBTN} onClick={function() { run('hermes_bundle_create'); }}>Crear bundle /themeforge</button>
        <button style={MX_GBTN} onClick={function() { run('hermes_profile_list'); }}>Listar perfiles</button>
      </div>
    </MxSec>
    <MxSec title="COSTE &amp; FALLBACK · 費用">
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <button style={MX_GBTN} onClick={function() { setOut(function(o) { return o + '\n▶ insights…'; }); callB('hermes_insights', 30); }}>Insights (30d)</button>
        <button style={MX_GBTN} onClick={function() { run('hermes_fallback_list'); }}>Ver fallback</button>
        <button style={MX_GBTN} onClick={function() { setFb(true); }}>Añadir fallback</button>
      </div>
      {fb && <HermesFrame kind="hermes-fallback" onStart={function() { callB('hermes_fallback_add'); }} />}
    </MxSec>
    <MxOut text={out} />
  </div>;
}

/* ── iframe del Chat/Admin de Hermes ─────────────────────────── */
const HMARKERS = [['plan', 0], ['scaffold', 1], ['creando', 1], ['create_project', 1], ['building', 2], ['run_agent_build', 2], ['preflight', 3], ['qa', 3], ['build_zip', 4], ['.zip', 4], ['packaged', 4]];
const HTABS = [
  ['mision', '🎯 Misión'], ['proveedor', '🔌 Proveedor'], ['imagenes', '🎨 Imágenes'],
  ['agentes', '🤖 Agentes'], ['crear', '➕ Crear'], ['memoria', '🧠 Memoria'],
  ['kanban', '📊 Kanban'], ['cron', '⏰ Cron'], ['remoto', '📲 Remoto'],
  ['avanzado', '🛡️ Avanzado'], ['chat', '💬 Chat'], ['admin', '⚙ Admin'],
];
// iframe del Chat/Admin de Hermes (terminal_ready filtrado por kind).
function HermesFrame({ kind, start, onStart }) {
  var [url, setUrl] = useState(null); var [err, setErr] = useState(null);
  useEffect(function() {
    var B = window.tfBridge;
    if (!B || !B.terminal_ready || !B.terminal_ready.connect) { setErr('sin puente'); return; }
    var onReady = function(j) { var r = {}; try { r = JSON.parse(j); } catch (e) {} if (r.kind === kind) { if (r.url) setUrl(r.url); else if (r.error) setErr(r.error); } };
    B.terminal_ready.connect(onReady);
    if (onStart) onStart(); else if (B[start]) B[start]();
    return function() { try { B.terminal_ready.disconnect(onReady); } catch (e) {} };
  }, [kind]);
  if (err) return <div className="panelc" style={{ color: 'var(--p3)', fontFamily: 'var(--term)' }}>// {err}</div>;
  if (!url) return <div className="panelc" style={{ color: 'var(--tx-dim)', fontFamily: 'var(--term)' }}>// iniciando {kind === 'hermes-admin' ? 'dashboard' : kind}…</div>;
  return <iframe src={url} style={{ width: '100%', height: '68vh', border: '1px solid var(--line)', borderRadius: 4, background: '#040804' }} />;
}
function Operator() {
  var op = (window.__TF_DATA__ && window.__TF_DATA__.operator) || {};
  var real = !!(window.tfBridge && window.tfBridge.launch_mission);
  var [missions, setMissions] = useState([]);
  var [power, setPower] = useState(!!op.available);
  var [tab, setTab] = useState('mision');
  var [hs, setHs] = useState({ available: op.available, version: op.version });
  var [brief, setBrief] = useState('');
  var [variants, setVariants] = useState(1);
  var [prov, setProv] = useState('codex');
  var [log, setLog] = useState('');
  var refreshHs = function() { var B = window.tfBridge; if (B && B.hermes_status) B.hermes_status().then(function(j) { var r = {}; try { r = JSON.parse(j); } catch (e) {} setHs(r); }); };
  useEffect(function() {
    refreshHs();
    var B = window.tfBridge;
    if (!B || !B.progress || !B.progress.connect) return;
    var onLog = function(line) { setLog(function(l) { return (l + line).slice(-6000); }); setMissions(function(ms) { return ms.map(function(m, i) { if (i !== 0) return m; var ph = m.phase || 0; var low = ('' + line).toLowerCase(); HMARKERS.forEach(function(mk_idx) { var mk = mk_idx[0], idx = mk_idx[1]; if (low.indexOf(mk) >= 0 && idx > ph) ph = idx; }); var done = /terminada \(exit/.test(line); return Object.assign({}, m, { phase: done ? 4 : ph, pct: done ? 100 : Math.max(m.pct, 15 + ph * 20), st: done ? 'listo' : m.st }); }); }); };
    B.progress.connect(onLog);
    return function() { try { B.progress.disconnect(onLog); } catch (e) {} };
  }, []);
  var launch = function() {
    if (!real || !power) return;
    if (!hs.available && !op.available) { alert('Instala Hermes Agent para usar el Operator.'); return; }
    if (!brief.trim()) { alert('Escribe el brief de la misión.'); return; }
    setLog('');
    if (window.tfBridge.launch_mission_opts) window.tfBridge.launch_mission_opts(brief, prov, variants);
    else window.tfBridge.launch_mission(brief);
    setMissions(function(ms) { return [{ id: 'm' + ms.length, name: brief.slice(0, 60), agent: prov, st: 'corriendo', pct: 10, phase: 0, eta: variants + 'x' }].concat(ms); });
  };
  var running = missions.filter(function(m) { return m.pct < 100; }).length;
  var chip = function(ok, l) { return <span style={{ fontFamily: 'var(--term)', color: ok == null ? 'var(--tx-dim)' : (ok ? 'var(--accent)' : 'var(--p3)') }}>● {l}</span>; };
  var off = <div className="panelc" style={{ color: 'var(--tx-dim)', fontFamily: 'var(--term)', padding: 20 }}>// enciende Hermes para usar esta pestaña</div>;
  return (
    <div className="page fade">
      <h2 className="sec">⌬ Mission Control <span style={{ fontFamily: 'var(--term)', fontSize: 13, color: 'var(--tx-dim)' }}>司令室</span>
        <button className="btn" style={{ float: 'right', color: power ? 'var(--accent)' : 'var(--p3)', borderColor: power ? 'var(--accent)' : 'var(--p3)' }} onClick={function() { setPower(function(p) { return !p; }); }} disabled={!hs.available}>⏻ {power ? 'Hermes ON' : 'Hermes OFF'}</button></h2>
      <div className="panelc" style={{ display: 'flex', gap: 16, alignItems: 'center', marginBottom: 14, fontFamily: 'var(--term)', fontSize: 12.5, flexWrap: 'wrap' }}>
        {chip(hs.available, hs.available ? ('Hermes ' + (hs.version || '')) : 'Hermes no instalado')}
        {chip(hs.mcp, hs.mcp ? 'MCP themeforge' : 'MCP sin registrar')}
        {chip(hs.provider || hs.model ? true : null, (hs.provider || hs.model) ? ((hs.provider || '?') + ' · ' + (hs.model || '?')) : 'modelo sin configurar')}
        <button className="btn" style={{ marginLeft: 'auto', padding: '4px 10px' }} onClick={refreshHs}>↻</button>
      </div>
      <div style={{ display: 'flex', gap: 6, marginBottom: 16, flexWrap: 'wrap' }}>
        {HTABS.map(function(kl) { var k = kl[0], l = kl[1]; return <button key={k} className={'fchip' + (tab === k ? ' on' : '')} onClick={function() { setTab(k); }}>{l}</button>; })}
      </div>

      {tab === 'proveedor' && <ProviderTab />}
      {tab === 'imagenes' && <ImagesTab />}
      {tab === 'agentes' && <AgentsTab />}
      {tab === 'crear' && <CreateTab />}
      {tab === 'memoria' && <MemoryTab />}
      {tab === 'kanban' && (power ? <KanbanTab /> : off)}
      {tab === 'cron' && <CronTab />}
      {tab === 'remoto' && <RemoteTab />}
      {tab === 'avanzado' && <AdvancedTab />}
      {tab === 'chat' && (power ? <HermesFrame kind="hermes-chat" start="start_hermes_chat" /> : off)}
      {tab === 'admin' && (power ? <HermesFrame kind="hermes-admin" start="hermes_admin" /> : off)}

      {tab === 'mision' && <>
        <div className="panelc" style={{ marginBottom: 14 }}>
          <textarea className="ta" value={brief} onChange={function(e) { setBrief(e.target.value); }} placeholder='Brief de la misión — ej: "landing Envato para clínica dental, stack Astro"' />
          <div style={{ display: 'flex', gap: 10, marginTop: 10, alignItems: 'center', flexWrap: 'wrap', fontFamily: 'var(--term)', fontSize: 12.5 }}>
            <label>variantes <input type="number" min={1} max={6} value={variants} onChange={function(e) { setVariants(+e.target.value); }} className="ta" style={{ minHeight: 0, width: 56, padding: '5px 8px' }} /></label>
            <label>agente <select className="ta" value={prov} onChange={function(e) { setProv(e.target.value); }} style={{ minHeight: 0, padding: '5px 8px' }}>{['codex', 'opencode', 'claude-api', 'gemini'].map(function(p) { return <option key={p} value={p}>{p}</option>; })}</select></label>
            <button className="btn pri" style={{ marginLeft: 'auto' }} onClick={launch} disabled={!power}>▶ Lanzar misión</button>
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 11 }}>
          {missions.map(function(m) {
            var a = AGENTS[m.agent] || { color: 'var(--accent)', em: '◆' };
            return (
              <div className="panelc" key={m.id} style={{ padding: '15px 20px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontFamily: 'var(--term)' }}>
                  <span style={{ fontSize: 15, color: a.color }}>{a.em}</span>
                  <b style={{ flex: 1 }}>{m.name}</b>
                  <span style={{ color: m.pct === 100 ? 'var(--accent)' : 'var(--p3)' }}>{m.st}</span>
                  <span style={{ color: 'var(--tx-dim)', width: 56, textAlign: 'right' }}>{m.eta}</span>
                </div>
                <div style={{ display: 'flex', gap: 6, marginTop: 10, fontFamily: 'var(--term)', fontSize: 11 }}>
                  {PHASES.map(function(ph, i) { return <span key={ph} style={{ color: i <= (m.phase || 0) ? 'var(--accent)' : 'var(--tx-dim)' }}>{i <= (m.phase || 0) ? '●' : '○'} {ph}</span>; })}
                </div>
                <div className="bar2" style={{ marginTop: 10 }}><i style={{ width: m.pct + '%' }} /></div>
              </div>
            );
          })}
        </div>
        {log && <div className="panelc" style={{ marginTop: 14, fontFamily: 'var(--term)', fontSize: 12, color: 'var(--tx-dim)', whiteSpace: 'pre-wrap', maxHeight: 240, overflow: 'auto' }}>{log}</div>}
        {!missions.length && <div className="panelc" style={{ textAlign: 'center', padding: 30, color: 'var(--tx-dim)', fontFamily: 'var(--term)' }}>// sin misiones activas — pulsa ▶ Lanzar misión</div>}
      </>}
    </div>
  );
}

/* ---- Settings ---- */
// Temas REALES de ThemeForge (prototipos web + packs recolor + clásicos),
// inyectados por el shell. Fallback mínimo si se abre suelto.
const THEMES = ((typeof window !== 'undefined' && window.__TF_DATA__ && window.__TF_DATA__.themes) || [
  { k: 'matrix', label: 'Matrix', acc: '#00ff41', acc2: '#008f11', bg: '#040804', proto: true, web: true },
]);
// Sistema + Setup + Skills + Shortcuts (datos/diálogos reales del bridge).
function SysAndSetup() {
  const B = window.tfBridge;
  const [sys, setSys] = useState(null);
  const [skills, setSkills] = useState([]);
  const loadSys = () => { if (B && B.system_status) B.system_status().then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {} setSys(r.sections || []); }); };
  useEffect(() => { loadSys(); if (B && B.list_stack_skills) B.list_stack_skills().then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {} setSkills(r.stacks || []); }); }, []);
  const call = (m, arg) => { if (B && B[m]) (arg !== undefined ? B[m](arg) : B[m]()); };
  const setupBtns = [['open_credentials', '🔑 Credenciales (login/keys)'], ['open_dependency_wizard', '🔧 Dependencias'], ['open_onboarding', '🧙 Onboarding'], ['open_theme_editor', '🎨 Theme editor'], ['open_figma_import', '📥 Import Figma']];
  return (
    <div>
      <h2 className="sec" style={{ margin: '8px 0 14px' }}>⌬ Estado del sistema <span style={{ fontFamily: 'var(--term)', fontSize: 13, color: 'var(--tx-dim)' }}>状態</span><button className="btn" style={{ float: 'right', padding: '4px 10px' }} onClick={loadSys}>↻</button></h2>
      <div className="panelc" style={{ fontFamily: 'var(--term)', fontSize: 12.5 }}>
        {!sys ? <span style={{ color: 'var(--tx-dim)' }}>detectando…</span> : sys.map(sec => (
          <div key={sec.title} style={{ marginBottom: 10 }}>
            <div style={{ color: 'var(--accent)', fontSize: 11, letterSpacing: '.08em', textTransform: 'uppercase', marginBottom: 4 }}>{sec.title}</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {sec.items.map(it => <span key={it.name} title={it.detail} style={{ color: it.ok ? 'var(--accent)' : 'var(--tx-dim)' }}>{it.ok ? '●' : '○'} {it.name}</span>)}
            </div>
          </div>
        ))}
      </div>
      <h2 className="sec" style={{ margin: '26px 0 14px' }}>⚙ Setup & herramientas <span style={{ fontFamily: 'var(--term)', fontSize: 13, color: 'var(--tx-dim)' }}>道具</span></h2>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {setupBtns.map(([m, l]) => <button key={m} className="btn" onClick={() => call(m)}>{l}</button>)}
      </div>
      {skills.length > 0 && <>
        <h2 className="sec" style={{ margin: '26px 0 14px' }}>技 Skills por stack <span style={{ fontFamily: 'var(--term)', fontSize: 13, color: 'var(--tx-dim)' }}>技能</span></h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(260px,1fr))', gap: 12 }}>
          {skills.map(s => <div className="panelc" key={s.key} style={{ padding: 14 }}><b style={{ fontFamily: 'var(--term)', fontSize: 13 }}>{s.label}</b><div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 8 }}>{s.skills.map(k => <span key={k} className="tag">{k}</span>)}</div></div>)}
        </div>
      </>}
      <h2 className="sec" style={{ margin: '26px 0 14px' }}>↗ Atajos <span style={{ fontFamily: 'var(--term)', fontSize: 13, color: 'var(--tx-dim)' }}>近道</span></h2>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {[['themeforge', '📁 Carpeta ThemeForge'], ['context', '📚 context/'], ['stacks', '📝 Editar stacks.py']].map(([k, l]) => <button key={k} className="btn" onClick={() => call('open_shortcut', k)}>{l}</button>)}
      </div>
    </div>
  );
}
function Settings() {
  const [th, setTh] = useState((window.__TF_DATA__ && window.__TF_DATA__.current_theme) || 'matrix');
  const applyTheme = (t) => {
    setTh(t.k);
    if (t.proto) {                         // diseño web completo → recarga el shell
      if (window.tfBridge && window.tfBridge.use_web_theme) window.tfBridge.use_web_theme(t.k);
    } else if (t.web) {                    // pack recolor → CSS vars en vivo
      if (window.tfApplyTheme && t.vars) window.tfApplyTheme(t.vars);
      if (window.tfBridge && window.tfBridge.set_theme) window.tfBridge.set_theme(t.k);
    } else if (window.tfBridge && window.tfBridge.switch_to_classic) {  // clásico → reinicia
      if (confirm('Tema clásico «' + t.label + '» (UI nativa). ThemeForge se reiniciará. ¿Continuar?')) window.tfBridge.switch_to_classic(t.k);
    }
  };
  return (
    <div className="page fade" style={{ maxWidth: 820 }}>
      <h2 className="sec">⚙ Temas de la app <span style={{ fontFamily: 'var(--term)', fontSize: 13, color: 'var(--tx-dim)' }}>テーマ</span></h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 14 }}>
        {THEMES.map(t => (
          <button key={t.k} className={'tile' + (th === t.k ? ' on' : '')} onClick={() => applyTheme(t)} style={{ padding: 0, overflow: 'hidden', position: 'relative' }}>
            {t.proto && <span style={{ position: 'absolute', top: 5, right: 5, fontSize: 8.5, padding: '2px 5px', borderRadius: 5, background: 'rgba(0,255,65,0.18)', color: 'var(--accent)', fontFamily: 'var(--term)' }}>診⟳</span>}
            {t.web === false && <span style={{ position: 'absolute', top: 5, right: 5, fontSize: 8.5, padding: '2px 5px', borderRadius: 5, background: 'rgba(255,176,0,0.18)', color: '#ffb000', fontFamily: 'var(--term)' }}>古典↻</span>}
            <div style={{ height: 64, background: t.bg, padding: 10, display: 'flex', gap: 6, alignItems: 'flex-start' }}>
              <span style={{ width: 18, height: 18, borderRadius: 3, background: t.acc, boxShadow: `0 0 8px ${t.acc}` }} />
              <span style={{ width: 18, height: 18, borderRadius: 3, background: t.acc2 }} />
            </div>
            <div style={{ padding: '10px 12px', fontWeight: 600, fontSize: 14, fontFamily: 'var(--term)' }}>{t.label}</div>
          </button>
        ))}
      </div>
      <div className="panelc" style={{ marginTop: 20 }}>
        <div style={{ fontWeight: 600, marginBottom: 8, fontFamily: 'var(--term)' }}>avatar del operador</div>
        <div style={{ display: 'flex', gap: 14, alignItems: 'center' }}>
          <Slot id="mascot" cls="" radius={4} ph="// arrastra avatar" />
          <span style={{ color: 'var(--tx-dim)', fontFamily: 'var(--term)', fontSize: 13 }}>Arrastra una imagen para tu avatar de operador — aparecerá en cada arranque del sistema.</span>
        </div>
      </div>

      <SysAndSetup />

      <h2 className="sec" style={{ margin: '26px 0 14px' }}>⚿ Credenciales <span style={{ fontFamily: 'var(--term)', fontSize: 13, color: 'var(--tx-dim)' }}>鍵</span></h2>
      <div className="panelc" style={{ padding: '6px 18px 14px' }}>
        {((window.__TF_DATA__ && window.__TF_DATA__.creds) || [{ id: 'anthropic', label: 'Anthropic API key', configured: false }, { id: 'openrouter', label: 'OpenRouter key', configured: false }]).map(cr => (
          <div key={cr.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 0', borderBottom: '1px solid var(--line)', fontFamily: 'var(--term)' }}>
            <span style={{ color: 'var(--accent)', fontSize: 14, width: 16 }}>◈</span>
            <div style={{ flex: 1 }}><div style={{ fontSize: 13.5 }}>{cr.label}</div><div style={{ fontSize: 11, marginTop: 2, color: 'var(--tx-dim)' }}>{cr.configured ? ('✓ configurada' + (cr.via === 'oauth' ? ' · OAuth/CLI login' : cr.via === 'gh-cli' ? ' · gh CLI' : ' · API key')) : 'sin configurar'}</div></div>
            <span style={{ width: 7, height: 7, borderRadius: 99, background: cr.configured ? 'var(--accent)' : 'var(--tx-dim)', boxShadow: cr.configured ? '0 0 8px var(--accent)' : 'none' }} />
            <button className="btn" style={{ padding: '6px 10px' }} onClick={() => { if (!(window.tfBridge && window.tfBridge.set_credential)) return; const v = prompt('Pega la ' + cr.label + ' (vacío para borrar):'); if (v === null) return; window.tfBridge.set_credential(cr.id, v).then(() => location.reload()); }}>✎ Editar</button>
          </div>
        ))}
        <div style={{ fontSize: 11, marginTop: 12, color: 'var(--tx-dim)', fontFamily: 'var(--term)' }}>Las claves se guardan en ~/.config/themeforge/keys.json (chmod 0600) · nunca en el proyecto.</div>
      </div>

      <h2 className="sec" style={{ margin: '26px 0 14px' }}>⇆ MCP servers <span style={{ fontFamily: 'var(--term)', fontSize: 13, color: 'var(--tx-dim)' }}>接続</span></h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(220px,1fr))', gap: 12 }}>
        {MCP_SERVERS.map(m => (
          <div className="panelc" key={m.id} style={{ padding: 15 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontFamily: 'var(--term)' }}><span style={{ fontSize: 15, color: 'var(--accent)' }}>{m.em}</span><b style={{ flex: 1, fontSize: 13.5 }}>{m.label}</b>{m.always && <span className="tag" style={{ color: 'var(--accent)', borderColor: 'var(--accent)' }}>always</span>}</div>
            <div style={{ color: 'var(--tx-dim)', fontFamily: 'var(--term)', fontSize: 12, marginTop: 8, lineHeight: 1.5 }}>{m.desc}</div>
          </div>
        ))}
      </div>

      <h2 className="sec" style={{ margin: '26px 0 14px' }}>⌗ Pixel Office <span style={{ fontFamily: 'var(--term)', fontSize: 13, color: 'var(--tx-dim)' }}>可視化</span></h2>
      <div className="panelc" style={{ textAlign: 'center' }}>
        <div style={{ color: 'var(--tx-dim)', fontFamily: 'var(--term)', fontSize: 13, maxWidth: 480, margin: '0 auto 16px', lineHeight: 1.6 }}>Visualizador pixel-art que muestra tus sesiones de IA como avatares en una oficina virtual.</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(8,1fr)', gap: 4, maxWidth: 280, margin: '0 auto 18px' }}>
          {Array.from({ length: 24 }, (_, i) => { const a = [9, 12, 18].includes(i); const cols = ['#00ff66', '#00d9ff', '#ffb000']; return <div key={i} style={{ aspectRatio: '1', borderRadius: 3, background: a ? cols[i % 3] : 'var(--bg)', border: '1px solid var(--line)', boxShadow: a ? `0 0 8px ${cols[i % 3]}` : 'none' }} />; })}
        </div>
        <button className="btn pri" onClick={() => window.tfBridge && window.tfBridge.pixel_office_launch && window.tfBridge.pixel_office_launch().then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {} alert(r.ok ? (r.already ? 'Pixel Office ya está activo.' : '▶ Pixel Office lanzado.') : ('Error: ' + (r.error || ''))); })}>▶ Lanzar dashboard</button>
      </div>
      <style>{`#mascot{width:120px;height:120px;flex-shrink:0;}`}</style>
    </div>
  );
}

/* ---- Project Window (preview + terminal) ---- */
const TERM_K = [
  { c: 'var(--accent)', s: '$ themeforge agent --task "build hero + features"' },
  { c: '#00ff66', s: '◈ claude · session forge-7f2a · pid d4e2' },
  { c: 'var(--tx-dim)', s: '> leyendo CLAUDE.md … contexto cargado' },
  { c: 'var(--accent)', s: '[OK] creado Hero.tsx (+148 −0)' },
  { c: 'var(--accent)', s: '[OK] creado FeatureBento.tsx (+212 −0)' },
  { c: 'var(--tx-dim)', s: '> tipando … tsc — 0 errores' },
  { c: 'var(--p3)', s: '◤ tarea completa · preview actualizado' },
];
// Una terminal real (xterm+node-pty) por «kind» (agent/shell/hermes), filtrada
// por path+kind en terminal_ready. Conserva sesión aunque se cambie de pestaña.
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
  if (!window.tfBridge || !path) return <MatrixTerminal run={true} />;
  if (err) return <div style={{ flex: 1, padding: 14, fontFamily: 'var(--term)', color: 'var(--p3)' }}>// {kind}: {err}</div>;
  if (!url) return <div style={{ flex: 1, padding: 14, fontFamily: 'var(--term)', color: 'var(--tx-dim)' }}>// iniciando {kind} (xterm · node-pty)…</div>;
  return <iframe src={url} style={{ flex: 1, width: '100%', border: '1px solid var(--line)', borderRadius: 4, background: '#040804', minHeight: 0 }} />;
}
// Pestaña «Office» — dashboard pixel-art (visualizador de sesiones IA).
function OfficeFrame() {
  const [url, setUrl] = useState(null); const [msg, setMsg] = useState('// cargando Office…');
  useEffect(() => {
    const B = window.tfBridge;
    if (!B || !B.pixel_office_url) { setMsg('// Office no disponible'); return; }
    B.pixel_office_url().then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {} if (r.installed && r.url) setUrl(r.url); else setMsg('// Pixel Office no instalado — Ajustes → Pixel Office'); });
  }, []);
  if (!url) return <div style={{ flex: 1, padding: 14, fontFamily: 'var(--term)', color: 'var(--tx-dim)' }}>{msg}</div>;
  return <iframe src={url} style={{ flex: 1, width: '100%', border: '1px solid var(--line)', borderRadius: 4, background: '#040804', minHeight: 0 }} />;
}
// Pestañas encima del terminal (como en la app normal): Setup · Agente · Shell · Hermes · Office.
function RealTerm({ path, fresh }) {
  const op = (window.__TF_DATA__ && window.__TF_DATA__.operator) || {};
  const tabs = [];
  if (fresh) tabs.push(['setup', '⚙ Setup']);
  tabs.push(['agent', '◈ Agente'], ['shell', '▮ Shell']);
  if (op.available) tabs.push(['hermes', '🚀 Hermes']);
  tabs.push(['office', '🎮 Office']);
  const first = fresh ? 'setup' : 'agent';
  const [active, setActive] = useState(first);
  const [seen, setSeen] = useState({ [first]: true });
  const open = (k) => { setActive(k); setSeen(s => ({ ...s, [k]: true })); };
  // Al terminar el setup → cambia solo a la pestaña Agente.
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

function MatrixTerminal({ run }) {
  const [n, setN] = useState(0);
  const box = useRef(null);
  useEffect(() => {
    if (!run) { setN(0); return; }
    setN(0); let i = 0;
    const t = setInterval(() => { i++; setN(i); if (i >= TERM_K.length) clearInterval(t); }, 460);
    return () => clearInterval(t);
  }, [run]);
  useEffect(() => { if (box.current) box.current.scrollTop = box.current.scrollHeight; }, [n]);
  return (
    <div ref={box} style={{ background: 'var(--bg)', border: '1px solid var(--line)', borderRadius: 4, padding: 14, fontFamily: 'var(--term)', fontSize: 13, lineHeight: 1.85, flex: 1, overflowY: 'auto', minHeight: 0 }}>
      {TERM_K.slice(0, n).map((l, i) => <div key={i} style={{ color: l.c }}>{l.s}</div>)}
      {run && n < TERM_K.length && <span style={{ color: 'var(--accent)' }}>▊</span>}
      {!run && <span style={{ color: 'var(--tx-dim)' }}>terminal lista — pulsa ▶</span>}
    </div>
  );
}
// Preview REAL: controles + sub-proyectos (mono-repo) + viewport + screenshot,
// igual que la barra de preview de la ProjectWindow nativa.
const VPORTS = [['📱', 360], ['📋', 768], ['💻', 1280], ['🖥', 1920], ['⛶', 0]];
function RealPreview({ path, fresh }) {
  const B = window.tfBridge;
  const [activePath, setActivePath] = useState(path);
  const [subs, setSubs] = useState([]);
  const [waitSetup, setWaitSetup] = useState(!!fresh);  // proyecto nuevo: espera al setup
  const [url, setUrl] = useState(null); const [err, setErr] = useState(null);
  const [status, setStatus] = useState('idle'); const [k, setK] = useState(0);
  const [log, setLog] = useState(''); const [vw, setVw] = useState(0);
  useEffect(() => { if (B && B.list_subprojects && path) B.list_subprojects(path).then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {} setSubs((r.subprojects || []).filter(s => s.has_preview)); }); }, [path]);
  useEffect(() => {
    if (!B || !B.preview_ready || !B.preview_ready.connect) return;
    const onReady = (j) => { let r = {}; try { r = JSON.parse(j); } catch (e) {} if (r.path !== activePath) return;
      if (r.log !== undefined) { setLog(l => (l + r.log).slice(-4000)); return; }
      if (r.stopped) { setUrl(null); setStatus('stopped'); return; }
      if (r.url) { setUrl(r.url); setErr(null); setStatus('up'); } else if (r.error) { setErr(r.error); setStatus('error'); } };
    B.preview_ready.connect(onReady);
    return () => { try { B.preview_ready.disconnect(onReady); } catch (e) {} };
  }, [activePath]);
  const start = () => { if (B && B.start_preview && activePath) { setErr(null); setLog(''); setStatus('starting'); B.start_preview(activePath); } };
  const stop = () => { if (B && B.stop_preview && activePath) { B.stop_preview(activePath); setUrl(null); setStatus('stopped'); } };
  const reload = () => setK(x => x + 1);
  const openExt = () => { if (B && B.open_preview_external && activePath) B.open_preview_external(activePath); };
  const shot = () => { if (B && B.screenshot_preview && activePath) B.screenshot_preview(activePath).then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {} alert(r.ok ? ('📸 captura: ' + r.file) : ('Error: ' + (r.error || ''))); }); };
  const switchSub = (sp) => { if (status === 'up' && B.stop_preview) B.stop_preview(activePath); setUrl(null); setErr(null); setStatus('idle'); setActivePath(sp); };
  const redetect = () => {
    if (!(B && B.refresh_profile && activePath)) return;
    B.refresh_profile(activePath).then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {}
      if (r.detected) { if (B.stop_preview) B.stop_preview(activePath); setUrl(null); setErr(null); setStatus('starting'); setTimeout(start, 500); }
      else alert('Aún sin preview detectable — ¿el setup terminó de instalar deps? (mira la pestaña Setup)'); });
  };
  // No auto-arrancar mientras el setup (npm install) del proyecto nuevo corre;
  // al terminar (setup_done) arranca solo.
  useEffect(() => { if (B && activePath && status === 'idle' && !waitSetup) start(); }, [activePath, waitSetup]);
  useEffect(() => {
    if (!fresh || !B || !B.setup_done || !B.setup_done.connect) return;
    const onDone = (j) => { let r = {}; try { r = JSON.parse(j); } catch (e) {} if (r.path === activePath) setWaitSetup(false); };
    B.setup_done.connect(onDone);
    return () => { try { B.setup_done.disconnect(onDone); } catch (e) {} };
  }, [activePath, fresh]);
  const ctl = { fontFamily: 'var(--term)', fontSize: 11.5, padding: '5px 9px' };
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '0 0 8px', flexWrap: 'wrap' }}>
        <button className="btn" style={ctl} onClick={start} disabled={status === 'up' || status === 'starting'}>▶ Start</button>
        <button className="btn" style={ctl} onClick={stop} disabled={status !== 'up'}>■ Stop</button>
        <button className="btn" style={ctl} onClick={reload} disabled={status !== 'up'}>↻</button>
        <button className="btn" style={ctl} onClick={openExt} disabled={status !== 'up'}>🗗</button>
        <button className="btn" style={ctl} onClick={shot} disabled={status !== 'up'}>📸</button>
        <button className="btn" style={ctl} onClick={redetect}>🔄</button>
        {subs.length > 1 && <select className="ta" value={activePath} onChange={e => switchSub(e.target.value)} style={{ minHeight: 0, padding: '5px 8px', fontSize: 11, ...ctl }}>{subs.map(s => <option key={s.path} value={s.path}>{s.name}{s.ref ? ' (ref)' : ''}</option>)}</select>}
        <input className="ta" readOnly value={url || ''} placeholder="URL…" style={{ minHeight: 0, padding: '5px 9px', flex: 1, fontSize: 11.5, minWidth: 90 }} />
        {VPORTS.map(([e, w]) => <button key={w} className={'btn' + (vw === w ? ' pri' : '')} style={{ ...ctl, padding: '5px 7px' }} title={w ? w + 'px' : 'full'} onClick={() => setVw(w)}>{e}</button>)}
      </div>
      <div style={{ flex: 1, display: 'grid', placeItems: 'stretch', minHeight: 0, overflow: 'auto' }}>
        {!B || !activePath ? <div style={{ color: 'var(--tx-dim)', fontFamily: 'var(--term)', placeSelf: 'center' }}>// sin preview</div>
          : err ? <div style={{ color: 'var(--p3)', fontFamily: 'var(--term)', placeSelf: 'center' }}>// preview: {err}</div>
          : status === 'stopped' ? <div style={{ color: 'var(--tx-dim)', fontFamily: 'var(--term)', placeSelf: 'center' }}>■ preview detenido — pulsa ▶ Start</div>
          : (waitSetup && status === 'idle') ? <div style={{ color: 'var(--tx-dim)', fontFamily: 'var(--term)', placeSelf: 'center', textAlign: 'center', padding: 20 }}>⏳ esperando a que termine el setup (npm install)…<br /><span style={{ fontSize: 11 }}>arrancará solo al acabar · o pulsa ▶ Start</span></div>
          : !url ? <div style={{ alignSelf: 'stretch', width: '100%', overflow: 'auto', fontFamily: 'var(--term)', fontSize: 11.5, color: 'var(--tx-dim)', whiteSpace: 'pre-wrap', padding: 4 }}>{'> arrancando dev server (sondeando puerto)…\n' + (log || '')}</div>
          : <iframe key={k} src={url} style={{ width: vw ? vw : '100%', maxWidth: '100%', height: '100%', minHeight: 280, border: 'none', borderRadius: 4, background: '#fff', justifySelf: 'center' }} />}
      </div>
    </div>
  );
}

// Log del setup/scaffold en vivo (señal progress) mientras se construye.
function BuildLog({ lines }) {
  const box = useRef(null);
  useEffect(() => { if (box.current) box.current.scrollTop = box.current.scrollHeight; }, [lines]);
  return (
    <div ref={box} style={{ flex: 1, background: 'var(--bg)', border: '1px solid var(--line)', borderRadius: 4, padding: 14, fontFamily: 'var(--term)', fontSize: 12.5, lineHeight: 1.7, overflowY: 'auto', minHeight: 0, whiteSpace: 'pre-wrap', color: 'var(--tx-dim)' }}>
      {(lines && lines.length) ? lines.join('') : '> esperando salida del scaffold…'}
      <div style={{ color: 'var(--accent)' }}>▊ instalando (scaffold · autoskills · UI/UX Pro · MCP)…</div>
    </div>
  );
}
// Barra de MCP servers REAL: lee el .mcp.json del proyecto; clic = activar/desactivar.
function MCPBar({ path }) {
  const B = window.tfBridge;
  const [servers, setServers] = useState([]);
  const load = () => { if (B && B.read_mcp && path) B.read_mcp(path).then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {} if (r.servers) setServers(r.servers); }); };
  useEffect(load, [path]);
  const toggle = (id) => { if (!(B && B.toggle_mcp && path)) return; setServers(s => s.map(x => x.id === id ? { ...x, active: !x.active } : x)); B.toggle_mcp(path, id).then(load); };
  return (
    <div style={{ display: 'flex', gap: 6, marginBottom: 14, flexWrap: 'wrap', alignItems: 'center' }}>
      <span style={{ fontSize: 11, fontFamily: 'var(--term)', color: 'var(--tx-dim)' }}>MCP ·</span>
      {(servers.length ? servers : MCP_SERVERS.map(m => ({ id: m.id, label: m.label, active: !!m.always, desc: m.desc }))).map(m => (
        <button key={m.id} className="tag" title={(m.active ? 'activo · ' : 'inactivo · ') + (m.desc || '')} onClick={() => toggle(m.id)}
          style={{ cursor: 'pointer', color: m.active ? 'var(--accent)' : 'var(--tx-dim)', borderColor: m.active ? 'var(--accent)' : 'var(--line)', opacity: m.active ? 1 : 0.55 }}>
          {m.active ? '●' : '○'} {m.label}
        </button>
      ))}
      <span style={{ fontSize: 10.5, fontFamily: 'var(--term)', color: 'var(--tx-dim)' }}>· clic = on/off (.mcp.json)</span>
    </div>
  );
}
function ProjectWindow({ p, onBack, onDeploy, onBuild, buildLog }) {
  const [tab, setTab] = useState('desktop');
  const [pushed, setPushed] = useState(false);
  const building = p.status === 'building';
  const ag = AGENTS[p.agent] || { color: 'var(--accent)', em: '◆', label: p.agent || 'agent' };
  const st = STATUS[p.status] || { color: 'var(--tx-dim)', em: '○', label: p.status || '' };
  const tabs = [['desktop', '▭ Desktop'], ['mobile', '▯ Mobile'], ['code', '⌗ Code']];
  const B = window.tfBridge;
  const preflight = () => { if (B && B.run_preflight) { alert('⟳ Pre-flight…'); B.run_preflight(p.path).then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {} alert('Pre-flight: ' + (r.verdict || r.status || (r.ok ? 'PASS' : JSON.stringify(r).slice(0, 200)))); }); } else onBuild && onBuild(); };
  const buildzip = () => { if (B && B.build_zip) { alert('⟳ Empaquetando ZIP…'); B.build_zip(p.path).then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {} alert('ZIP: ' + (r.zip_path || r.zip || r.error || 'hecho')); }); } };
  const push = () => { if (B && B.git_push) { B.git_push(p.path); setPushed(true); } else setPushed(true); };
  const deploy = () => { if (B && B.deploy_demo) { const pv = prompt('Deploy a (netlify/vercel/cloudflare/surge):', 'surge'); if (pv) B.deploy_demo(p.path, pv); } else onDeploy && onDeploy(); };
  const folder = () => { if (B && B.open_folder) B.open_folder(p.path); };
  const vscode = () => { if (B && B.open_vscode) B.open_vscode(p.path); };
  const extterm = () => { if (B && B.open_external_terminal) B.open_external_terminal(p.path); };
  const github = () => { if (B && B.github_create) { alert('⎇ GitHub: creando/empujando repo… mira la terminal de setup'); B.github_create(p.path); } };
  const operator = () => { window.tfNav && window.tfNav('operator'); };
  const newp = () => { window.tfNav && window.tfNav('new'); };
  const other = () => { window.tfNav && window.tfNav('gallery'); };
  return (
    <div className="page fade" style={{ height: '100%', display: 'flex', flexDirection: 'column', paddingBottom: 26 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14, flexWrap: 'wrap' }}>
        <button className="btn" onClick={onBack}>← Galería</button>
        <b style={{ fontSize: 18, fontFamily: 'var(--display)' }}>{p.name}</b><span style={{ fontFamily: 'var(--term)', color: 'var(--tx-dim)' }}>{p.jp}</span>
        <span className="pstatus" style={{ position: 'static', color: st.color }}>{st.em} {st.label}</span>
        <div style={{ flex: 1 }} />
        <button className="btn" onClick={newp}>＋ Nuevo</button>
        <button className="btn" onClick={other}>📂 Abrir otro</button>
        <button className="btn" onClick={folder}>🗀 Folder</button>
        <button className="btn" onClick={vscode}>⌨ VSCode</button>
        <button className="btn" onClick={extterm}>▮ Terminal ext.</button>
        <button className="btn" onClick={operator}>⌬ Operator</button>
        <button className="btn" onClick={preflight}>✓ Pre-flight</button>
        <button className="btn" onClick={buildzip}>⊞ ZIP</button>
        <button className="btn" onClick={github}>⎇ GitHub</button>
        <button className={'btn' + (pushed ? '' : ' pri')} onClick={push}>{pushed ? '✓ Pushed' : '⎇ Push'}</button>
        <button className="btn pri" onClick={deploy}>▶ Deploy</button>
      </div>
      <MCPBar path={p.path} />
      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: 16, minHeight: 0 }}>
        <div className="panelc" style={{ display: 'flex', flexDirection: 'column', padding: 14, minHeight: 0 }}>
          <div style={{ display: 'flex', gap: 6, marginBottom: 12 }}>
            {tabs.map(([k, l]) => <button key={k} className={'fchip' + (tab === k ? ' on' : '')} onClick={() => setTab(k)}>{l}</button>)}
            <span style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--tx-dim)', fontFamily: 'var(--term)', alignSelf: 'center' }}>localhost:5173</span>
          </div>
          <div style={{ flex: 1, display: 'grid', placeItems: 'stretch', background: 'var(--bg)', border: '1px solid var(--line)', borderRadius: 4, padding: 0, minHeight: 0, overflow: 'auto' }}>
            <RealPreview path={p.path} fresh={p.fresh} narrow={tab === 'mobile'} />
          </div>
        </div>
        <div className="panelc" style={{ display: 'flex', flexDirection: 'column', padding: 14, minHeight: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10, fontFamily: 'var(--term)' }}>
            <b>⌗ Terminales</b>
            <span className="tag" style={{ marginLeft: 'auto', color: ag.color, borderColor: ag.color }}>{ag.em} {ag.label}</span>
          </div>
          <RealTerm path={p.path} fresh={p.fresh} />
        </div>
      </div>
    </div>
  );
}

/* ---- Market ---- */
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
  const niche = () => { const v = prompt('Nicho concreto a investigar:'); if (v) go(v); };
  const market = () => { const v = prompt('Marketplace (ThemeForest / CodeCanyon / Gumroad…):'); if (v) go('marketplace: ' + v); };
  const cmp = () => { const a = prompt('Nicho A:'); if (!a) return; const b = prompt('Nicho B:'); if (!b) return; go('compara estos 2 nichos: ' + a + ' vs ' + b); };
  const copy = () => { try { navigator.clipboard.writeText(md); } catch (e) {} };
  const exportMd = () => { if (window.tfBridge && window.tfBridge.market_export) window.tfBridge.market_export(md); };
  return (
    <div className="page fade">
      <h2 className="sec">⊞ Market Analyzer <span style={{ fontFamily: 'var(--term)', fontSize: 13, color: 'var(--tx-dim)' }}>市場分析</span></h2>
      <div className="panelc" style={{ display: 'flex', gap: 10, marginBottom: 14 }}>
        <input className="ta" style={{ minHeight: 0, padding: '11px 16px' }} value={q} onChange={e => setQ(e.target.value)} placeholder='Nicho a investigar — ej: "clínica dental"' />
        <button className="btn pri" onClick={() => go()}>{load ? '> analizando…' : '> Analizar'}</button>
      </div>
      {real && <div style={{ display: 'flex', gap: 8, marginBottom: 18, flexWrap: 'wrap', fontFamily: 'var(--term)' }}>
        {[['@general', 'Mercado 2026'], ['@stacks', 'Stacks'], ['@prediction', 'Predicción 2027']].map(([k, l]) => <button key={k} className="tag" style={{ cursor: 'pointer' }} onClick={() => go(k)}>{l}</button>)}
        <button className="tag" style={{ cursor: 'pointer' }} onClick={niche}>🎯 Nicho</button>
        <button className="tag" style={{ cursor: 'pointer' }} onClick={market}>🏪 Marketplace</button>
        <button className="tag" style={{ cursor: 'pointer' }} onClick={cmp}>⚖ Comparar 2</button>
        {done && md && <>
          <button className="tag" style={{ cursor: 'pointer' }} onClick={copy}>📋 Copiar</button>
          <button className="tag" style={{ cursor: 'pointer' }} onClick={exportMd}>💾 Exportar</button>
          <button className="tag" style={{ cursor: 'pointer', marginLeft: 'auto', color: 'var(--accent)' }} onClick={() => window.tfNav && window.tfNav('new')}>▶ Crear proyecto desde análisis</button>
        </>}
      </div>}
      {load && <div className="panelc" style={{ textAlign: 'center', color: 'var(--accent)', fontFamily: 'var(--term)' }}>{'>'} analizando mercado con IA (OpenRouter) — puede tardar…</div>}
      {done && md && <div className="panelc fade"><pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontFamily: 'var(--term)', fontSize: 13, lineHeight: 1.7, color: 'var(--tx)', margin: 0 }}>{md}</pre></div>}
      {!done && !load && <div className="panelc" style={{ textAlign: 'center', color: 'var(--tx-dim)', fontFamily: 'var(--term)' }}>introduce un nicho para empezar</div>}
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
  const create = () => { if (!np.trim()) return; window.tfBridge.licensing_create(np, ne, nt).then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {} alert(r.ok ? ('✓ Licencia: ' + (r.key || '')) : ('Error: ' + (r.error || r.code))); refresh(); }); };
  if (!real) return <div className="page fade"><div className="panelc">Licensing no disponible (sin puente).</div></div>;
  return (
    <div className="page fade" style={{ maxWidth: 980 }}>
      <h2 className="sec">⚿ Licencias <span style={{ fontFamily: 'var(--term)', fontSize: 13, color: 'var(--tx-dim)' }}>認可</span></h2>
      <div className="panelc" style={{ marginBottom: 14, display: 'flex', alignItems: 'center', gap: 12, fontFamily: 'var(--term)', fontSize: 13 }}>
        <span style={{ width: 9, height: 9, borderRadius: 99, background: st ? (st.reachable ? 'var(--accent)' : (st.configured ? '#ffb000' : 'var(--tx-dim)')) : 'var(--tx-dim)' }} />
        <span>{!st ? 'consultando…' : !st.configured ? 'Sin backend (config en licensing.json)' : st.reachable ? ('Backend OK · ' + (st.licenses || []).length + ' licencias · ' + (st.products || []).length + ' productos') : 'Configurado pero no responde'}</span>
        <button className="btn" style={{ marginLeft: 'auto' }} onClick={refresh}>↻</button>
      </div>
      <div style={{ display: 'flex', gap: 8, marginBottom: 14, flexWrap: 'wrap' }}>
        {[['lic', 'Licencias'], ['prod', 'Productos'], ['gum', 'Gumroad'], ['tools', 'Tools']].map(([k, l]) => (
          <button key={k} className={'tag' + (sub === k ? ' on' : '')} style={{ cursor: 'pointer', color: sub === k ? 'var(--accent)' : 'var(--tx-dim)' }} onClick={() => { setSub(k); if (k === 'prod' && !prods) api('/api/products/versions').then(r => setProds(r.data)); if (k === 'gum' && !gum) api('/api/gumroad').then(r => setGum(r.data)); }}>{l}</button>
        ))}
      </div>
      {sub === 'lic' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 16 }}>
          <div className="panelc" style={{ padding: 0, overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12.5, fontFamily: 'var(--term)' }}>
              <thead><tr style={{ background: 'var(--bg)' }}>{['Key', 'Producto', 'Tipo', 'Estado'].map(h => <th key={h} style={{ textAlign: 'left', padding: '10px 14px', color: 'var(--tx-dim)', borderBottom: '1px solid var(--line)' }}>{h}</th>)}</tr></thead>
              <tbody>{(st && st.licenses && st.licenses.length) ? st.licenses.map((l, i) => <tr key={i} style={{ borderTop: '1px solid var(--line)' }}><td style={{ padding: '9px 14px', color: 'var(--accent)' }}>{l.key}</td><td style={{ padding: '9px 14px' }}>{l.product}</td><td style={{ padding: '9px 14px', color: 'var(--tx-dim)' }}>{l.type}</td><td style={{ padding: '9px 14px' }}>{l.status}</td></tr>) : <tr><td colSpan={4} style={{ padding: 22, textAlign: 'center', color: 'var(--tx-dim)' }}>// sin licencias</td></tr>}</tbody>
            </table>
          </div>
          <div className="panelc">
            <div style={{ fontWeight: 600, marginBottom: 12, fontFamily: 'var(--term)' }}>crear licencia 発行</div>
            <input className="ta" style={{ minHeight: 0, height: 38, marginBottom: 8 }} value={np} onChange={e => setNp(e.target.value)} placeholder="producto (slug)" />
            <input className="ta" style={{ minHeight: 0, height: 38, marginBottom: 8 }} value={ne} onChange={e => setNe(e.target.value)} placeholder="email comprador" />
            <select className="ta" style={{ minHeight: 0, height: 38, marginBottom: 10 }} value={nt} onChange={e => setNt(e.target.value)}><option value="regular">regular</option><option value="extended">extended</option></select>
            <button className="btn pri" onClick={create}>⚿ Crear licencia</button>
          </div>
        </div>
      )}
      {sub === 'prod' && <div className="panelc"><div style={{ display: 'flex', marginBottom: 10 }}><b style={{ flex: 1, fontFamily: 'var(--term)' }}>Productos / Versiones</b><button className="btn" onClick={() => api('/api/products/versions').then(r => setProds(r.data))}>↻</button></div><pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'var(--term)', fontSize: 12, color: 'var(--tx-dim)', margin: 0 }}>{prods ? ((prods.products || []).map(p => '• ' + p.id + ' · ' + (p.currentVersion || '—') + ' · ' + p.repo).join('\n') || '(sin productos)') : '// cargando…'}</pre></div>}
      {sub === 'gum' && <div className="panelc"><div style={{ display: 'flex', marginBottom: 10 }}><b style={{ flex: 1, fontFamily: 'var(--term)' }}>Ventas Gumroad</b><button className="btn" onClick={() => api('/api/gumroad').then(r => setGum(r.data))}>↻</button></div><pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'var(--term)', fontSize: 12, color: 'var(--tx-dim)', margin: 0 }}>{gum ? JSON.stringify(gum, null, 2) : '// cargando…'}</pre></div>}
      {sub === 'tools' && <div className="panelc"><div style={{ display: 'flex', gap: 8, marginBottom: 10 }}><button className="btn" onClick={() => api('/api/integrations/status').then(r => setTools(JSON.stringify(r.data, null, 2)))}>Estado integraciones</button></div><pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'var(--term)', fontSize: 12, color: 'var(--tx-dim)', margin: 0, minHeight: 50 }}>{tools || '// resultado'}</pre></div>}
    </div>
  );
}

/* ---- Modals ---- */
function Modal({ title, jp, onClose, children, w = 560 }) {
  useEffect(() => { const h = e => e.key === 'Escape' && onClose(); window.addEventListener('keydown', h); return () => window.removeEventListener('keydown', h); }, []);
  return (
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, zIndex: 300, background: 'rgba(0,8,2,0.6)', backdropFilter: 'blur(4px)', display: 'grid', placeItems: 'center', padding: 24 }}>
      <div className="panelc fade" onClick={e => e.stopPropagation()} style={{ width: `min(${w}px,94vw)`, maxHeight: '86vh', overflowY: 'auto', boxShadow: 'var(--glow),0 20px 50px -10px rgba(0,0,0,.8)' }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
          <div><div style={{ fontFamily: 'var(--display)', fontSize: 22, color: 'var(--tx)' }}>{title}</div><div style={{ fontFamily: 'var(--term)', fontSize: 12, color: 'var(--tx-dim)' }}>{jp}</div></div>
          <button className="btn" style={{ marginLeft: 'auto', padding: '6px 12px' }} onClick={onClose}>✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}
// Análisis de referencia REAL (reference_analyzer + IA, streaming por reference_progress).
function ReferenceAnalysisModal({ onClose }) {
  const real = !!(window.tfBridge && window.tfBridge.analyze_reference);
  const [lines, setLines] = useState([]);
  const [status, setStatus] = useState('⏳ iniciando…');
  const [done, setDone] = useState(false);
  const boxRef = useRef(null);
  useEffect(() => {
    if (!real) { setDone(true); setStatus('sin puente'); return; }
    const ref = (window.__tfRef && window.__tfRef.value) || prompt('Ruta de la referencia a analizar (carpeta o .zip):') || '';
    if (!ref) { setDone(true); return; }
    const kind = (window.__tfRef && window.__tfRef.kind) || 'folder';
    const onProg = (j) => { let r = {}; try { r = JSON.parse(j); } catch (e) {}
      if (r.status) setStatus(r.status);
      if (r.text !== undefined) setLines(ls => [...ls, r.text]);
      if (r.done) { if (r.error) setLines(ls => [...ls, '\n⚠ ' + r.error]); setStatus(r.error ? '⚠ error' : '✓ Análisis IA listo — se inyectará en CLAUDE.md al crear el proyecto.'); setDone(true); } };
    if (window.tfBridge.reference_progress && window.tfBridge.reference_progress.connect) window.tfBridge.reference_progress.connect(onProg);
    window.tfBridge.analyze_reference(ref, kind);
    return () => { try { window.tfBridge.reference_progress.disconnect(onProg); } catch (e) {} };
  }, []);
  useEffect(() => { if (boxRef.current) boxRef.current.scrollTop = boxRef.current.scrollHeight; }, [lines]);
  return (
    <Modal title="Análisis de referencia · Claude Code" jp="参照分析" onClose={onClose} w={820}>
      <div ref={boxRef} style={{ padding: 16, fontFamily: 'var(--term)', fontSize: 12.5, lineHeight: 1.8, maxHeight: '52vh', overflowY: 'auto', background: 'var(--bg)', border: '1px solid var(--line)', borderRadius: 4 }}>
        <div style={{ color: 'var(--tx-dim)', whiteSpace: 'pre-wrap' }}>{lines.join('')}</div>
        {!done && <div style={{ color: 'var(--accent)', marginTop: 8 }}><span>▊</span> {status}</div>}
      </div>
      {done && <div style={{ marginTop: 12, padding: '10px 14px', borderRadius: 4, background: 'rgba(0,255,65,0.1)', border: '1px solid var(--accent)', color: 'var(--accent)', fontSize: 12.5, fontFamily: 'var(--term)' }}>✓ Análisis IA listo — se inyectará en <b>CLAUDE.md</b> al crear el proyecto (modo recreate).</div>}
      <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
        <button className="btn pri" style={{ marginLeft: 'auto' }} onClick={onClose}>💾 Guardar</button>
      </div>
    </Modal>
  );
}
function DeployModal({ onClose }) {
  const [t, setT] = useState('netlify'); const [phase, setPhase] = useState('idle'); const [log, setLog] = useState([]);
  const go = () => { setPhase('go'); setLog([]); const steps = ['> npm run build …', '[OK] build · 1.2 MB', `> subiendo a ${t} …`, '[OK] desplegado', '◤ LIVE']; let i = 0; const tick = () => { if (i >= steps.length) { setPhase('done'); return; } setLog(l => [...l, steps[i]]); i++; setTimeout(tick, 550); }; tick(); };
  return (
    <Modal title="▶ Deploy demo" jp="展開" onClose={onClose}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 16 }}>
        {DEPLOY_TARGETS.map(d => <button key={d.id} className={'tile' + (t === d.id ? ' on' : '')} disabled={phase !== 'idle'} onClick={() => setT(d.id)} style={{ display: 'flex', alignItems: 'center', gap: 8 }}><span style={{ fontSize: 16, color: 'var(--accent)' }}>{d.em}</span><b style={{ fontSize: 14, fontFamily: 'var(--term)' }}>{d.label}</b></button>)}
      </div>
      {phase === 'idle' ? <button className="btn pri" style={{ width: '100%', justifyContent: 'center' }} onClick={go}>▶ Deploy a {DEPLOY_TARGETS.find(d => d.id === t).label}</button>
        : <div style={{ background: 'var(--bg)', border: '1px solid var(--line)', borderRadius: 4, padding: 14, fontFamily: 'var(--term)', fontSize: 13, lineHeight: 1.9, minHeight: 110 }}>{log.map((l, i) => <div key={i} style={{ color: l.startsWith('[OK]') || l.startsWith('◤') ? 'var(--accent)' : 'var(--tx-dim)' }}>{l}</div>)}{phase === 'done' && <div style={{ color: 'var(--p3)', marginTop: 8 }}>→ https://{t}-aurora.app</div>}</div>}
    </Modal>
  );
}
function BuildModal({ onClose }) {
  const [zip, setZip] = useState(false);
  const ok = PREFLIGHT.filter(p => p.ok).length;
  return (
    <Modal title="✓ Pre-flight & ZIP" jp="出荷検査" onClose={onClose}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12, fontFamily: 'var(--term)' }}><span style={{ color: 'var(--tx-dim)' }}>Checklist marketplace</span><span className="tag" style={{ color: 'var(--accent)', borderColor: 'var(--accent)' }}>{ok}/{PREFLIGHT.length} OK</span></div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 16 }}>
        {PREFLIGHT.map((c, i) => <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 9, background: 'var(--bg)', border: '1px solid var(--line)', borderRadius: 4, padding: '9px 13px', fontFamily: 'var(--term)', fontSize: 13 }}><span style={{ color: c.ok ? 'var(--accent)' : 'var(--p3)' }}>{c.ok ? '[OK]' : '[!!]'}</span><span style={{ flex: 1 }}>{c.l}</span>{c.n && <span style={{ color: 'var(--tx-dim)', fontSize: 12 }}>{c.n}</span>}</div>)}
      </div>
      {!zip ? <button className="btn pri" style={{ width: '100%', justifyContent: 'center' }} onClick={() => setZip(true)}>⊞ Build ZIP para marketplace</button>
        : <div className="fade" style={{ background: 'var(--bg)', border: '1px solid var(--line)', borderRadius: 4, padding: 16, fontFamily: 'var(--term)' }}><b style={{ color: 'var(--accent)' }}>[OK] aurora-matrix.zip</b><div style={{ color: 'var(--tx-dim)', fontSize: 13, marginTop: 8 }}>312 archivos · 8.4 MB → <b style={{ color: 'var(--accent)' }}>2.1 MB</b> (75%)<br /><span style={{ fontSize: 11.5 }}>excluye node_modules · .env · context/ · reference/</span></div><button className="btn" style={{ marginTop: 12 }}>⬇ Descargar</button></div>}
    </Modal>
  );
}

/* ---- Command palette ---- */
function Palette({ open, onClose, onNav, onOpenProject }) {
  const [q, setQ] = useState(''); const [sel, setSel] = useState(0); const inp = useRef(null);
  const actions = [
    ...NAV.map(n => ({ id: n.id, label: 'Ir a ' + n.label, em: n.em, kind: 'nav' })),
    ...PROJECTS.map(p => ({ id: p.id, label: 'Abrir · ' + p.name, em: '▸', kind: 'proj', p })),
  ];
  const f = actions.filter(a => a.label.toLowerCase().includes(q.toLowerCase()));
  useEffect(() => { if (open) { setQ(''); setSel(0); setTimeout(() => inp.current?.focus(), 30); } }, [open]);
  useEffect(() => { setSel(0); }, [q]);
  const run = a => { if (!a) return; if (a.kind === 'proj') onOpenProject(a.p); else onNav(a.id); onClose(); };
  if (!open) return null;
  return (
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, zIndex: 320, background: 'rgba(0,8,2,0.6)', backdropFilter: 'blur(4px)', display: 'grid', placeItems: 'start center', paddingTop: '12vh' }}>
      <div className="panelc fade" onClick={e => e.stopPropagation()} style={{ width: 'min(560px,92vw)', padding: 12, boxShadow: 'var(--glow),0 20px 50px -10px rgba(0,0,0,.8)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', borderBottom: '1px solid var(--line)', marginBottom: 8, fontFamily: 'var(--term)' }}>
          <span style={{ fontSize: 16, color: 'var(--accent)' }}>{'>'}</span>
          <input ref={inp} value={q} onChange={e => setQ(e.target.value)} onKeyDown={e => { if (e.key === 'ArrowDown') { e.preventDefault(); setSel(s => Math.min(f.length - 1, s + 1)); } else if (e.key === 'ArrowUp') { e.preventDefault(); setSel(s => Math.max(0, s - 1)); } else if (e.key === 'Enter') run(f[sel]); }} placeholder="buscar comandos, proyectos…" style={{ flex: 1, border: 'none', background: 'none', outline: 'none', fontFamily: 'var(--term)', fontSize: 15, color: 'var(--tx)' }} />
          <span className="tag">ESC</span>
        </div>
        <div style={{ maxHeight: 340, overflowY: 'auto' }}>
          {f.map((a, i) => <div key={a.id + a.kind} onMouseEnter={() => setSel(i)} onClick={() => run(a)} style={{ display: 'flex', alignItems: 'center', gap: 11, padding: '10px 13px', borderRadius: 4, cursor: 'pointer', background: i === sel ? 'rgba(0,255,65,0.12)' : 'transparent', color: i === sel ? 'var(--accent)' : 'var(--tx)', fontFamily: 'var(--term)', border: i === sel ? '1px solid var(--accent)' : '1px solid transparent' }}><span style={{ fontSize: 15 }}>{a.em}</span>{a.label}</div>)}
          {f.length === 0 && <div style={{ padding: 24, textAlign: 'center', color: 'var(--tx-dim)', fontFamily: 'var(--term)' }}>sin coincidencias</div>}
        </div>
      </div>
    </div>
  );
}

/* ---- App shell ---- */
const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "palette": ["#00ff41", "#00b894"],
  "light": false,
  "rain": true
}/*EDITMODE-END*/;

const PALETTES = {
  'Matrix verde': ['#00ff41', '#00b894'],
  'Amber CRT': ['#ffb000', '#ff7b00'],
  'Ice / cyan': ['#00d9ff', '#0090ff'],
  'Red pill': ['#ff3131', '#b00020'],
  'Violeta': ['#b46fff', '#7c3aed'],
};

/* ---- Boot ---- */
function MatrixBoot({ onDone }) {
  const steps = [
    { s: 'estableciendo conexión segura', e: '◇' },
    { s: 'descifrando clave RSA-4096', e: '⚿' },
    { s: 'montando sistema de archivos', e: '▮' },
    { s: 'despertando daemons IA', e: '◈' },
    { s: 'inyectando contexto del proyecto', e: '⊟' },
    { s: 'ACCESO CONCEDIDO', e: '●' },
  ];
  const [n, setN] = useState(0);
  const [fade, setFade] = useState(false);
  useEffect(() => {
    if (n < steps.length) {
      const t = setTimeout(() => setN(n + 1), n === 0 ? 280 : 340 + Math.random() * 180);
      return () => clearTimeout(t);
    }
    const a = setTimeout(() => setFade(true), 560);
    const b = setTimeout(onDone, 1120);
    return () => { clearTimeout(a); clearTimeout(b); };
  }, [n]);
  const pct = Math.round((n / steps.length) * 100);
  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 900, display: 'grid', placeItems: 'center',
      background: 'radial-gradient(circle at 50% 35%,#08140a,#020402 70%)',
      transition: 'opacity .5s ease', opacity: fade ? 0 : 1, pointerEvents: fade ? 'none' : 'auto',
    }}>
      <div style={{ textAlign: 'center', position: 'relative', zIndex: 2, width: 'min(440px,88vw)' }}>
        <div style={{ fontFamily: 'var(--term)', fontSize: 92, lineHeight: 1, color: 'var(--accent)', textShadow: 'var(--glow)', animation: 'flick 2.4s infinite' }}>鍛</div>
        <div style={{ fontFamily: 'var(--display)', fontSize: 44, lineHeight: 1, color: 'var(--accent)', marginTop: 10, textShadow: 'var(--glow)' }}>ThemeForge</div>
        <div style={{ fontFamily: 'var(--term)', color: 'var(--tx-dim)', letterSpacing: '.42em', fontSize: 12, marginTop: 6 }}>// SISTEMA DE FORJA v3.0</div>
        <div style={{ minHeight: 24, marginTop: 26, fontFamily: 'var(--term)', color: n >= steps.length ? 'var(--accent)' : 'var(--tx)', fontSize: 14.5, textShadow: n >= steps.length ? 'var(--glow)' : 'none' }}>
          {n < steps.length
            ? <span className="fade" key={n}>{steps[n].e} {steps[n].s}<span style={{ animation: 'blinkk 1s infinite' }}> ▊</span></span>
            : <span>{steps[steps.length - 1].e} {steps[steps.length - 1].s}</span>}
        </div>
        <div style={{ height: 10, background: '#020402', border: '1px solid var(--line)', borderRadius: 2, marginTop: 18, overflow: 'hidden' }}>
          <div style={{ height: '100%', width: pct + '%', background: 'linear-gradient(90deg,var(--accent2),var(--accent))', boxShadow: '0 0 8px var(--accent)', transition: 'width .35s cubic-bezier(.3,1,.5,1)' }} />
        </div>
        <div style={{ marginTop: 8, fontFamily: 'var(--term)', color: 'var(--tx-dim)', fontSize: 13 }}>{pct}%</div>
        <div style={{ marginTop: 22, display: 'flex', gap: 16, justifyContent: 'center', fontFamily: 'var(--term)', fontSize: 20 }}>
          {Object.values(AGENTS).map((a, i) => (
            <span key={i} style={{ color: a.color, animation: `blinkk 1.4s ease-in-out ${i * 0.18}s infinite` }}>{a.em}</span>
          ))}
        </div>
      </div>
      <style>{`
        @keyframes blinkk{0%,49%{opacity:1}50%,100%{opacity:.25}}
        @keyframes flick{0%,100%{opacity:1}92%{opacity:1}94%{opacity:.4}96%{opacity:1}}
      `}</style>
    </div>
  );
}

function _hashProj() {
  try {
    const h = window.location.hash || '';
    const m = /[#&]proj=([^&]+)/.exec(h);
    if (!m) return null;
    const path = decodeURIComponent(m[1]);
    return { path, name: path.replace(/\/+$/, '').split('/').pop(), fresh: /[#&]fresh=1/.test(h) };
  } catch (e) { return null; }
}
function App() {
  const _hp = _hashProj();
  const _isWin = !!_hp;
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [booted, setBooted] = useState(_isWin);
  const [route, setRoute] = useState('gallery');
  const [project, setProject] = useState(_hp ? { id: _hp.name, name: _hp.name, path: _hp.path, fresh: _hp.fresh, status: 'live', jp: '制作' } : null);
  const [modal, setModal] = useState(null);
  const [palette, setPalette] = useState(false);
  const [buildLog, setBuildLog] = useState([]);
  useEffect(() => {
    const r = document.documentElement.style;
    const [a, b] = Array.isArray(t.palette) ? t.palette : ['#00ff41', '#00b894'];
    r.setProperty('--accent', a); r.setProperty('--accent2', b);
    r.setProperty('--glow', `0 0 12px ${a}88`);
    r.setProperty('--rain', t.rain ? '1' : '0');
    document.body.classList.toggle('light', t.light);
  }, [t]);
  useEffect(() => { startRain(); }, []);
  useEffect(() => {
    const h = e => { if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); setPalette(o => !o); } };
    window.addEventListener('keydown', h); return () => window.removeEventListener('keydown', h);
  }, []);

  const nav = (id) => { setProject(null); setRoute(id); };
  window.tfNav = nav;
  // Abre el proyecto en una VENTANA NUEVA del SO (como el nativo); fallback overlay.
  const openProject = (p) => {
    if (!_isWin && window.tfBridge && window.tfBridge.open_project_window && p && p.path) { window.tfBridge.open_project_window(p.path, false); return; }
    setProject(p);
  };
  const launch = (cfg) => {
    window.__tfLastAgent = cfg.agent;
    if (!(window.tfBridge && window.tfBridge.create_project)) {
      setProject({ ...cfg, id: cfg.name, status: 'live', fresh: true, jp: '制作' }); return;
    }
    window.tfBridge.create_project(JSON.stringify(cfg)).then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {}
      if (r && r.ok && r.path) {
        if (window.tfBridge.open_project_window) { window.tfBridge.open_project_window(r.path, true); setRoute('gallery'); }
        else setProject({ id: r.slug, name: cfg.name, path: r.path, agent: cfg.agent, status: 'live', fresh: true, jp: '制作' });
      } else if (r && r.ok === false) alert('Error al crear: ' + (r.error || '')); });
  };
  const titles = { gallery: '▤ Galería', new: '+ Nuevo proyecto', cost: '$ Coste de IA', compare: '⇄ Comparar agentes', operator: '⌬ Mission Control', market: '⊞ Market Analyzer', licensing: '⚿ Licencias', settings: '⚙ Ajustes', project: '▸ ' + (project ? project.name : '') };

  return (
    <div className="app">
      {!booted && <MatrixBoot onDone={() => setBooted(true)} />}
      <div className="side">
        <div className="brand"><span className="gl">ThemeForge</span><small>// MATRIX BUILD</small></div>
        <div className="nav">
          {NAV.map(n => (
            <button key={n.id} className={'navi' + (route === n.id ? ' on' : '')} onClick={() => nav(n.id)}>
              <span className="ico">{n.em}</span> {n.label} <span className="jp">{n.jp}</span>
            </button>
          ))}
        </div>
        <div className="agents">
          <div className="lbl">daemons IA</div>
          {Object.entries(AGENTS).map(([k, a], i) => (
            <div className="agrow" key={k}><span className="em" style={{ color: a.color }}>{a.em}</span> {a.label}<span className="dot" style={{ background: i < 2 ? a.color : 'var(--line)', boxShadow: i < 2 ? `0 0 6px ${a.color}` : 'none' }} /></div>
          ))}
        </div>
      </div>

      <div className="main">
        <div className="bar">
          <h1 className="h1">{titles[route]}</h1>
          <div className="search" onClick={() => setPalette(true)} style={{ cursor: 'pointer' }}><span style={{ color: 'var(--accent)' }}>{'>'}</span> <input placeholder="buscar…  ⌘K" readOnly style={{ cursor: 'pointer' }} /></div>
          <button className="btn pri" onClick={() => nav('new')}>+ Nuevo</button>
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

      {/* Proyecto en VENTANA/MODAL aparte (como la ProjectWindow nativa) */}
      {project && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 600, background: 'var(--bg2, #040804)', display: 'flex', flexDirection: 'column', padding: 20, overflow: 'auto' }}>
          <ProjectWindow p={project} onBack={() => { if (_isWin) window.close(); else setProject(null); }} onDeploy={() => setModal('deploy')} onBuild={() => setModal('build')} buildLog={buildLog} />
        </div>
      )}

      {modal === 'deploy' && <DeployModal onClose={() => setModal(null)} />}
      {modal === 'build' && <BuildModal onClose={() => setModal(null)} />}
      {modal === 'ref' && <ReferenceAnalysisModal onClose={() => setModal(null)} />}
      <Palette open={palette} onClose={() => setPalette(false)} onNav={nav} onOpenProject={openProject} />

      <TweaksPanel title="Tweaks">
        <TweakSection label="Phosphor" />
        <TweakColor label="Paleta" value={t.palette} options={Object.values(PALETTES)} onChange={v => setTweak('palette', v)} />
        <TweakToggle label="Modo claro" value={t.light} onChange={v => setTweak('light', v)} />
        <TweakSection label="Atmósfera" />
        <TweakToggle label="Lluvia digital" value={t.rain} onChange={v => setTweak('rain', v)} />
      </TweaksPanel>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
