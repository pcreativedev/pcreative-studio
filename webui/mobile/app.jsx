/* ============================================================================
 * Pcreative Studio Móvil — cliente fino (PWA) sobre el API Gateway.
 * Usa window.tfBridge (reimplementado por tfbridge-remote.js). Mobile-first.
 * Módulo base: Crear (creación de proyectos vía gateway). Pantallas opcionales
 * se auto-registran en window.TF_PRIVATE_SCREENS si su fichero está presente.
 * ========================================================================== */
const { useState, useEffect, useRef } = React;

function B(name, ...args) {
  const br = window.tfBridge;
  if (!br || !br[name]) return Promise.resolve({ ok: false, error: 'sin puente' });
  try { return br[name](...args).then(j => { try { return JSON.parse(j); } catch (e) { return { ok: false, error: 'json' }; } }); }
  catch (e) { return Promise.resolve({ ok: false, error: '' + e }); }
}
function useSignal(sigName, handler, deps) {
  useEffect(() => {
    const br = window.tfBridge; const sig = br && br[sigName];
    if (!sig || !sig.connect) return;
    const cb = (j) => { let r = {}; try { r = JSON.parse(j); } catch (e) {} handler(r); };
    sig.connect(cb);
    return () => { try { sig.disconnect(cb); } catch (e) {} };
  }, deps || []);
}
const cfg = () => { try { return JSON.parse(localStorage.getItem('tf_remote') || '{}'); } catch (e) { return {}; } };

const card = { background: 'var(--panel)', border: '1px solid var(--line)', borderRadius: 14, padding: 14 };
const fld = { width: '100%', background: 'var(--panel2)', border: '1px solid var(--line)', borderRadius: 10, padding: '11px 13px', color: 'var(--tx)', outline: 'none' };
const btn = { background: 'var(--accent)', color: '#062018', border: 'none', borderRadius: 10, padding: '11px 16px', fontWeight: 700 };
const ghost = { background: 'var(--panel2)', color: 'var(--tx)', border: '1px solid var(--line)', borderRadius: 10, padding: '10px 14px' };

/* ============================ Config ============================ */
function ConfigScreen({ onSaved }) {
  const c = cfg();
  // Si la PWA se sirve desde el propio gateway, autorellena la dirección.
  const sameOrigin = location.protocol.startsWith('http') ? location.origin : '';
  const [base, setBase] = useState(c.base || sameOrigin);
  const [token, setToken] = useState(c.token || '');
  const save = () => {
    localStorage.setItem('tf_remote', JSON.stringify({ base: base.trim().replace(/\/$/, ''), token: token.trim() }));
    onSaved();
  };
  return (
    <div style={{ padding: 22, paddingTop: 'max(22px, env(safe-area-inset-top))' }}>
      <h1 style={{ fontSize: 24, margin: '8px 0 4px' }}>Pcreative Studio <span style={{ color: 'var(--accent)' }}>Móvil</span></h1>
      <p style={{ color: 'var(--dim)', fontSize: 14, lineHeight: 1.5 }}>
        Conecta con tu motor (VPS o portátil). Mete la URL del gateway y el token.
        Recomendado: dentro de tu red <b>Tailscale</b>, p.ej. <span className="mono" style={{ color: 'var(--accent2)' }}>http://100.x.x.x:8765</span>
      </p>
      <div style={{ ...card, marginTop: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
        <label style={{ color: 'var(--dim)', fontSize: 13 }}>URL del gateway
          <input value={base} onChange={e => setBase(e.target.value)} placeholder="http://100.x.x.x:8765" style={{ ...fld, marginTop: 6 }} inputMode="url" autoCapitalize="off" autoCorrect="off" /></label>
        <label style={{ color: 'var(--dim)', fontSize: 13 }}>Token (PCREATIVE STUDIO_API_TOKEN)
          <input value={token} onChange={e => setToken(e.target.value)} placeholder="token…" type="password" style={{ ...fld, marginTop: 6 }} autoCapitalize="off" autoCorrect="off" /></label>
        <button style={btn} onClick={save} disabled={!base.trim()}>Conectar</button>
      </div>
    </div>
  );
}

/* ============================ Crear (Vibe/Recreate/Stack) ============================ */
function CrearScreen() {
  const [mode, setMode] = useState('vibe');
  const [name, setName] = useState('');
  const [desc, setDesc] = useState('');
  const [ref, setRef] = useState('');
  const [stacks, setStacks] = useState([]);
  const [stack, setStack] = useState('none');
  const [niche, setNiche] = useState('');
  const [niches, setNiches] = useState([]);
  const [provider, setProvider] = useState('claude');
  const [providers, setProviders] = useState(['claude', 'codex']);
  const [doBuild, setDoBuild] = useState(true);
  const [running, setRunning] = useState(false);
  const [phase, setPhase] = useState('');
  const [logs, setLogs] = useState([]);
  const [msg, setMsg] = useState('');
  const logRef = useRef(null);

  useEffect(() => {
    B('list_stacks').then(r => {
      if (r.ok) { setStacks(r.stacks || []); setNiches(r.niches || []); if (r.providers && r.providers.length) { setProviders(r.providers); setProvider(r.providers.includes('claude') ? 'claude' : r.providers[0]); } }
    });
  }, []);
  useSignal('build_event', r => {
    if (r.op !== 'build' && r.op !== 'suggest') return;
    if (r.event === 'log') setLogs(l => [...l, r.line || '']);
    else if (r.event === 'phase') setLogs(l => [...l, '──── ' + (r.phase === 'agent' ? '🤖 agente IA' : '⚙ setup') + ' ────']) || setPhase(r.phase);
    else if (r.event === 'stack_suggested') setLogs(l => [...l, '→ stack: ' + r.stack + (r.reasoning ? '  ·  ' + r.reasoning : '')]);
    else if (r.event === 'started') setLogs(l => [...l, '▶ iniciando…']);
    else if (r.done !== undefined && !r.event) { setRunning(false); setPhase(''); setLogs(l => [...l, r.ok ? ('✅ Proyecto creado: ' + (r.slug || '') + (r.built ? ' (construido)' : '')) : ('❌ ' + (r.error || 'error'))]); }
  }, []);
  useEffect(() => { if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight; }, [logs]);

  const grouped = () => {
    const g = {};
    stacks.forEach(s => { (g[s.category || 'Otros'] = g[s.category || 'Otros'] || []).push(s); });
    return g;
  };
  const start = () => {
    if (running) return;
    if (!name.trim()) { setMsg('Pon un nombre'); setTimeout(() => setMsg(''), 3000); return; }
    if (mode === 'vibe' && !desc.trim()) { setMsg('Describe la web'); setTimeout(() => setMsg(''), 3000); return; }
    if (mode === 'recreate' && !ref.trim()) { setMsg('Pon la URL a recrear'); setTimeout(() => setMsg(''), 3000); return; }
    const cfg = { mode, name: name.trim(), provider, build: doBuild };
    if (mode === 'vibe') cfg.description = desc.trim();
    if (mode === 'recreate') { cfg.reference = ref.trim(); cfg.reference_kind = 'url'; }
    if (mode === 'stack') { cfg.stack = stack; if (niche) cfg.niche = niche; }
    setLogs([]); setRunning(true); setPhase('');
    B('create_build', JSON.stringify(cfg));
  };

  const MODE = (id, ic, lb) => (
    <button onClick={() => !running && setMode(id)} style={{ ...ghost, flex: 1, padding: '9px 4px', fontSize: 12.5, borderColor: mode === id ? 'var(--accent)' : 'var(--line)', color: mode === id ? 'var(--accent)' : 'var(--dim)' }}>{ic} {lb}</button>
  );

  return (
    <div style={{ padding: 14, paddingBottom: 90, display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        {MODE('vibe', '✨', 'Vibe')}{MODE('recreate', '🔁', 'Recreate')}{MODE('stack', '🧩', 'Stack')}
      </div>

      <div style={{ ...card, display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 12 }}>
        <input value={name} onChange={e => setName(e.target.value)} placeholder="Nombre del proyecto" style={fld} disabled={running} />
        {mode === 'vibe' && <textarea value={desc} onChange={e => setDesc(e.target.value)} placeholder="Describe la web que quieres (la IA elige el stack)…" style={{ ...fld, minHeight: 110 }} disabled={running} />}
        {mode === 'recreate' && <input value={ref} onChange={e => setRef(e.target.value)} placeholder="https://web-a-recrear.com" style={fld} inputMode="url" autoCapitalize="off" disabled={running} />}
        {mode === 'stack' && <>
          <select value={stack} onChange={e => setStack(e.target.value)} style={fld} disabled={running}>
            {Object.entries(grouped()).map(([cat, arr]) => (
              <optgroup key={cat} label={cat}>{arr.map(s => <option key={s.key} value={s.key}>{s.name}</option>)}</optgroup>
            ))}
          </select>
          <input value={niche} onChange={e => setNiche(e.target.value)} placeholder="nicho (opcional: restaurante, clínica…)" style={fld} list="niches" disabled={running} />
          <datalist id="niches">{niches.slice(0, 60).map(n => <option key={n} value={n} />)}</datalist>
        </>}
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <select value={provider} onChange={e => setProvider(e.target.value)} style={{ ...fld, flex: 1 }} disabled={running}>
            {providers.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
          <label style={{ color: 'var(--dim)', fontSize: 13, display: 'flex', alignItems: 'center', gap: 6 }}>
            <input type="checkbox" checked={doBuild} onChange={e => setDoBuild(e.target.checked)} disabled={running} /> construir IA
          </label>
        </div>
        <button style={{ ...btn, padding: 13, opacity: running ? 0.5 : 1 }} onClick={start} disabled={running}>
          {running ? (phase === 'agent' ? '🤖 Construyendo…' : '⚙ Creando…') : '🚀 Crear' + (doBuild ? ' y construir' : '')}
        </button>
        {msg && <div style={{ color: 'var(--bad)', fontSize: 12.5 }}>{msg}</div>}
      </div>

      {/* logs en vivo */}
      <div ref={logRef} className="mono" style={{ flex: 1, minHeight: 180, background: '#05070c', border: '1px solid var(--line)', borderRadius: 12, padding: 12, fontSize: 11.5, color: 'var(--dim)', overflowY: 'auto', whiteSpace: 'pre-wrap', lineHeight: 1.5 }}>
        {logs.length === 0 ? <span style={{ color: 'var(--faint)' }}>// los logs del build aparecerán aquí en vivo</span> : logs.join('\n')}
      </div>
    </div>
  );
}

/* ============================ App ============================ */
function App() {
  // Pestaña base "Crear" + pantallas opcionales auto-registradas (plugins).
  const baseTabs = [{ id: 'crear', ic: '🚀', label: 'Crear', render: () => <CrearScreen /> }];
  const TABS = ((typeof window !== 'undefined' && window.TF_PRIVATE_SCREENS) || []).concat(baseTabs);
  const [connected, setConnected] = useState(!!(window.TF_REMOTE && window.TF_REMOTE.base));
  const [tab, setTab] = useState(TABS[0].id);

  if (!connected) return <ConfigScreen onSaved={() => location.reload()} />;
  const active = TABS.find(t => t.id === tab) || TABS[0];

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: 'max(14px,env(safe-area-inset-top)) 16px 10px', borderBottom: '1px solid var(--line)', display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ fontWeight: 800, fontSize: 18 }}>Pcreative Studio</span>
        <span style={{ color: 'var(--accent)', fontSize: 12 }}>● {(cfg().base || '').replace(/^https?:\/\//, '')}</span>
        <div style={{ flex: 1 }} />
        <button style={{ ...ghost, padding: '6px 10px', fontSize: 12 }} onClick={() => { localStorage.removeItem('tf_remote'); location.reload(); }}>⚙</button>
      </div>

      <div style={{ flex: 1, overflowY: 'auto' }}>
        {active && active.render()}
      </div>

      {/* bottom nav (oculto si solo hay una pestaña) */}
      {TABS.length > 1 && (
        <div style={{ display: 'flex', borderTop: '1px solid var(--line)', background: 'var(--panel)', paddingBottom: 'var(--safe-b)' }}>
          {TABS.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)} style={{ flex: 1, background: 'none', border: 'none', padding: '12px 0', color: tab === t.id ? 'var(--accent)' : 'var(--faint)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3 }}>
              <span style={{ fontSize: 20 }}>{t.ic}</span><span style={{ fontSize: 11 }}>{t.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
