/* ================= NEO-TOKYO · Operator (Hermes Mission Control) ================= */

const HSTUBS = [
  ['agentes', '🤖 Agentes', 'Galería de agentes especializados por familia de stack (Shopify · Hydrogen · WordPress · Magento+Hyvä · Frontend · Mobile…). Elige, edita o mira lo aprendido.', 'Fase B'],
  ['crear', '➕ Crear', 'Crea tu propio agente: nombre + stacks base + especialidad. Hermes redacta el SKILL.md por ti y aprende con cada proyecto.', 'Fase E'],
  ['memoria', '🧠 Memoria', 'Lo que Hermes ha aprendido: memorias globales + notas por proyecto (.hermes.md). Cada misión añade lo que funcionó.', 'Fase H'],
  ['kanban', '📊 Kanban', 'Misiones en paralelo (varias variantes) con workers → verificador → sintetizador, cada worker en su git worktree. Progreso en vivo.', 'Fase F'],
  ['cron', '⏰ Cron', 'Misiones programadas: «cada lunes 9am genera la landing del nicho top y mándame el zip». Sobre el scheduler nativo de Hermes.', 'Fase G'],
];

function MissionRow({ m }) {
  const ag = AGENTS[m.agent];
  const sc = m.status === 'running' ? 'var(--accent)' : m.status === 'done' ? 'var(--codex)' : 'var(--tx-faint)';
  const prog = useCountUp(m.progress, 1000, [m.id]);
  return (
    <div className="panel" style={{ padding: '14px 18px', borderColor: m.status === 'running' ? 'rgba(var(--accent-rgb),0.3)' : 'var(--line)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <span style={{ color: ag.color, fontSize: 16 }}>{ag.glyph}</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 13.5, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{m.name}</div>
          <div className="mono faint" style={{ fontSize: 11, marginTop: 2 }}>{m.step}</div>
        </div>
        <span className="mono" style={{ fontSize: 11, color: sc, letterSpacing: '0.08em' }}>{m.status.toUpperCase()}</span>
        <span className="mono dim" style={{ fontSize: 11, width: 58, textAlign: 'right' }}>{m.eta}</span>
      </div>
      <div style={{ height: 5, background: 'rgba(255,255,255,0.06)', borderRadius: 99, marginTop: 11, overflow: 'hidden' }}>
        <div style={{ width: prog + '%', height: '100%', borderRadius: 99,
          background: m.status === 'done' ? 'var(--codex)' : 'linear-gradient(90deg,var(--accent),var(--accent-2))',
          boxShadow: m.status === 'running' ? '0 0 10px rgba(var(--accent-rgb),0.6)' : 'none',
          transition: 'width 0.3s' }} />
      </div>
    </div>
  );
}

function HermesFrame({ kind, start }) {
  const [url, setUrl] = useState(null); const [err, setErr] = useState(null);
  useEffect(() => {
    const B = window.tfBridge;
    if (!B || !B.terminal_ready || !B.terminal_ready.connect) { setErr('sin puente'); return; }
    const onReady = (j) => { let r = {}; try { r = JSON.parse(j); } catch (e) {} if (r.kind === kind) { if (r.url) setUrl(r.url); else if (r.error) setErr(r.error); } };
    B.terminal_ready.connect(onReady);
    if (B[start]) B[start]();
    return () => { try { B.terminal_ready.disconnect(onReady); } catch (e) {} };
  }, [kind]);
  if (err) return <div className="panel mono faint" style={{ padding: 20, color: 'var(--gemini)' }}>// {err}</div>;
  if (!url) return <div className="panel mono faint" style={{ padding: 20 }}>// iniciando {kind === 'hermes-admin' ? 'dashboard' : 'chat'} de Hermes…</div>;
  return <iframe src={url} style={{ width: '100%', height: '70vh', border: '1px solid var(--line)', borderRadius: 8, background: '#0c0c0d' }} />;
}
function OperatorScreen() {
  const _op = (window.__TF_DATA__ && window.__TF_DATA__.operator) || {};
  const real = !!(window.tfBridge && window.tfBridge.launch_mission);
  const [missions, setMissions] = useState(real ? (_op.missions || []) : MISSIONS);
  const [power, setPower] = useState(!!_op.available);
  const [tab, setTab] = useState('mision');
  const [hs, setHs] = useState({ available: _op.available, version: _op.version });
  const [brief, setBrief] = useState('');
  const [variants, setVariants] = useState(1);
  const [prov, setProv] = useState('codex');
  const [log, setLog] = useState('');
  const refreshHs = () => { const B = window.tfBridge; if (B && B.hermes_status) B.hermes_status().then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {} setHs(r); }); };
  useEffect(() => {
    refreshHs();
    const B = window.tfBridge;
    if (!B || !B.progress || !B.progress.connect) return;
    const onLog = (line) => { setLog(l => (l + line).slice(-6000)); if (/terminada \(exit/.test(line)) setMissions(ms => ms.map((m, i) => i === 0 ? { ...m, status: 'done', progress: 100, step: 'completada' } : m)); };
    B.progress.connect(onLog);
    return () => { try { B.progress.disconnect(onLog); } catch (e) {} };
  }, []);
  const running = missions.filter(m => m.status === 'running').length;
  const queued = missions.filter(m => m.status === 'queued').length;
  const launchMission = () => {
    if (!real || !power) return;
    if (!hs.available && !_op.available) { alert('Instala Hermes Agent para usar el Operator.'); return; }
    if (!brief.trim()) { alert('Escribe el brief de la misión.'); return; }
    setLog('');
    if (window.tfBridge.launch_mission_opts) window.tfBridge.launch_mission_opts(brief, prov, variants);
    else window.tfBridge.launch_mission(brief);
    setMissions(ms => [{ id: 'm' + Date.now(), name: brief.slice(0, 60), agent: prov, status: 'running', progress: 10, eta: variants + 'x', step: 'Hermes orquestando…' }, ...ms]);
  };
  const tabs = [['mision', '🎯 Misión'], ...HSTUBS.map(s => [s[0], s[1]]), ['chat', '💬 Chat'], ['admin', '⚙ Admin']];
  const chip = (ok, l) => <span className="mono" style={{ fontSize: 11.5, color: ok == null ? 'var(--tx-faint)' : (ok ? 'var(--codex)' : 'var(--gemini)') }}>● {l}</span>;
  const stub = HSTUBS.find(s => s[0] === tab);
  return (
    <div style={{ padding: '34px 40px 60px', position: 'relative', zIndex: 2 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 18 }}>
        <div>
          <Eyebrow jp="司令室">OPERATOR · HERMES MISSION CONTROL</Eyebrow>
          <h1 style={{ fontFamily: 'var(--font-mega)', fontSize: 38, margin: '12px 0 6px' }}>
            MISSION <span className="neon-text">CONTROL</span>
          </h1>
          <div className="dim" style={{ fontSize: 13.5 }}>Orquesta builds autónomos en paralelo · {running} activos · {queued} en cola</div>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <Btn variant="ghost" icon="power" onClick={() => setPower(p => !p)} disabled={!_op.available}>{power ? 'Hermes ON' : 'Hermes OFF'}</Btn>
          {tab === 'mision' && <Btn variant="primary" icon="rocket" onClick={launchMission}>Lanzar misión</Btn>}
        </div>
      </div>

      <div className="panel" style={{ display: 'flex', gap: 18, alignItems: 'center', padding: '10px 16px', marginBottom: 16, flexWrap: 'wrap' }}>
        {chip(hs.available, hs.available ? ('Hermes ' + (hs.version || '')) : 'Hermes no instalado')}
        {chip(hs.mcp, hs.mcp ? 'MCP themeforge' : 'MCP sin registrar')}
        {chip(hs.provider || hs.model ? true : null, (hs.provider || hs.model) ? ((hs.provider || '?') + ' · ' + (hs.model || '?')) : 'modelo sin configurar')}
        <button className="btn btn-ghost" style={{ marginLeft: 'auto', padding: '4px 10px' }} onClick={refreshHs}><Icon name="refresh" size={13} /></button>
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
        {tabs.map(([k, l]) => <button key={k} onClick={() => setTab(k)} style={{ cursor: 'pointer', padding: '8px 14px', borderRadius: 10, fontSize: 12.5, fontFamily: 'var(--font-display)', background: tab === k ? 'rgba(var(--accent-rgb),0.12)' : 'transparent', border: '1px solid ' + (tab === k ? 'rgba(var(--accent-rgb),0.45)' : 'var(--line)'), color: tab === k ? 'var(--accent)' : 'var(--tx-dim)' }}>{l}</button>)}
      </div>

      {stub && <div className="panel card-corner" style={{ textAlign: 'center', padding: 48 }}><div style={{ fontSize: 32 }}>{stub[1].split(' ')[0]}</div><h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, margin: '12px 0 0' }}>{stub[1]}</h2><div className="dim" style={{ fontSize: 13.5, maxWidth: 540, margin: '12px auto 0', lineHeight: 1.6 }}>{stub[2]}</div><Chip color="var(--accent)" style={{ marginTop: 16 }}>⏳ {stub[3]}</Chip></div>}
      {tab === 'chat' && (power ? <HermesFrame kind="hermes-chat" start="start_hermes_chat" /> : <div className="panel mono faint" style={{ padding: 20 }}>// enciende Hermes para el chat</div>)}
      {tab === 'admin' && (power ? <HermesFrame kind="hermes-admin" start="hermes_admin" /> : <div className="panel mono faint" style={{ padding: 20 }}>// enciende Hermes para el dashboard</div>)}

      {tab === 'mision' && <>
      <div className="panel" style={{ padding: 16, marginBottom: 18 }}>
        <textarea value={brief} onChange={e => setBrief(e.target.value)} placeholder='Brief de la misión — ej: "landing Envato para clínica dental, stack Astro"'
          style={{ width: '100%', minHeight: 64, resize: 'vertical', background: 'var(--bg-void)', border: '1px solid var(--line-bright)', borderRadius: 8, padding: 12, color: 'var(--tx)', fontFamily: 'var(--font-mono)', fontSize: 12.5, outline: 'none' }} />
        <div style={{ display: 'flex', gap: 14, marginTop: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <label className="mono" style={{ fontSize: 12, color: 'var(--tx-dim)' }}>variantes <input type="number" min={1} max={6} value={variants} onChange={e => setVariants(+e.target.value)} style={{ width: 56, background: 'var(--bg-void)', border: '1px solid var(--line-bright)', borderRadius: 6, padding: '5px 8px', color: 'var(--tx)' }} /></label>
          <label className="mono" style={{ fontSize: 12, color: 'var(--tx-dim)' }}>agente <select value={prov} onChange={e => setProv(e.target.value)} style={{ background: 'var(--bg-void)', border: '1px solid var(--line-bright)', borderRadius: 6, padding: '5px 8px', color: 'var(--tx)' }}>{['codex', 'opencode', 'claude-api', 'gemini'].map(p => <option key={p} value={p}>{p}</option>)}</select></label>
        </div>
      </div>
      {log && <div className="panel mono" style={{ padding: 14, marginBottom: 18, fontSize: 11.5, color: 'var(--tx-dim)', whiteSpace: 'pre-wrap', maxHeight: 220, overflow: 'auto' }}>{log}</div>}
      {/* live stats strip */}
      <div style={{ display: 'flex', gap: 14, marginBottom: 22 }}>
        {[['ACTIVAS', running, 'var(--accent)'], ['EN COLA', queued, 'var(--gemini)'], ['TOTAL', missions.length, 'var(--codex)'], ['HERMES', _op.available ? (_op.version || 'on') : 'off', 'var(--accent-2)']].map(([l, v, c]) => (
          <div key={l} className="panel" style={{ flex: 1, padding: '14px 18px' }}>
            <div className="eyebrow" style={{ fontSize: 9.5 }}>{l}</div>
            <div style={{ fontFamily: 'var(--font-mega)', fontSize: 24, marginTop: 6, color: c }}>{v}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 20, alignItems: 'start' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div className="eyebrow" style={{ marginBottom: 2 }}>MISIONES · 任務</div>
          {missions.length ? missions.map(m => <MissionRow key={m.id} m={m} />)
            : <div className="faint mono" style={{ padding: 24, textAlign: 'center' }}>// sin misiones — pulsa «Lanzar misión» 待機中</div>}
        </div>

        {/* agent pool */}
        <div className="panel card-corner" style={{ padding: 20 }}>
          <div className="eyebrow" style={{ marginBottom: 14 }}>POOL DE AGENTES · 代理</div>
          {Object.entries(AGENTS).map(([k, a]) => {
            const busy = missions.some(m => m.agent === k && m.status === 'running');
            return (
              <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 0', borderBottom: '1px solid var(--line)' }}>
                <span style={{ color: a.color, fontSize: 15 }}>{a.glyph}</span>
                <span style={{ flex: 1, fontSize: 13 }}>{a.label}</span>
                <span style={{ width: 7, height: 7, borderRadius: 99, background: busy ? a.color : 'var(--tx-faint)', boxShadow: busy ? `0 0 8px ${a.color}` : 'none', animation: busy ? 'blink 1.1s infinite' : 'none' }} />
                <span className="mono faint" style={{ fontSize: 10.5, width: 52, textAlign: 'right' }}>{busy ? 'busy' : 'idle'}</span>
              </div>
            );
          })}
          <div style={{ marginTop: 14, fontSize: 11.5 }} className="faint">
            <span className="jp">ヘルメス</span> · Hermes orquesta hasta 4 agentes simultáneos con presupuesto compartido.
          </div>
        </div>
      </div>
      </>}
    </div>
  );
}

Object.assign(window, { OperatorScreen });
