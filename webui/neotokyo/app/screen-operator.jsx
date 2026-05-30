/* ================= NEO-TOKYO · Operator (Hermes Mission Control) =================
 * Paridad COMPLETA con el panel Hermes nativo (hermes_panel.py): 12 pestañas
 * cableadas al bridge (web_shell.py ThemeForgeBridge). Cero mock.
 */

/* ── helpers de puente ───────────────────────────────────────────────── */
function callB(name, ...args) {
  const B = window.tfBridge;
  if (!B || !B[name]) return Promise.resolve({ ok: false, error: 'sin puente' });
  try { return B[name](...args).then(j => { try { return JSON.parse(j); } catch (e) { return { ok: false, error: 'json' }; } }); }
  catch (e) { return Promise.resolve({ ok: false, error: '' + e }); }
}
function useHermesEvent(handler, deps) {
  useEffect(() => {
    const B = window.tfBridge;
    if (!B || !B.hermes_event || !B.hermes_event.connect) return;
    const cb = (j) => { let r = {}; try { r = JSON.parse(j); } catch (e) {} handler(r); };
    B.hermes_event.connect(cb);
    return () => { try { B.hermes_event.disconnect(cb); } catch (e) {} };
  }, deps || []);
}
const FLD = { background: 'var(--bg-void)', border: '1px solid var(--line-bright)', borderRadius: 6, padding: '6px 9px', color: 'var(--tx)', fontFamily: 'var(--font-mono)', fontSize: 12, outline: 'none' };
const SBTN = { cursor: 'pointer', padding: '6px 12px', borderRadius: 8, fontSize: 12, fontFamily: 'var(--font-display)', background: 'rgba(var(--accent-rgb),0.10)', border: '1px solid rgba(var(--accent-rgb),0.35)', color: 'var(--accent)' };
const GBTN = { cursor: 'pointer', padding: '6px 12px', borderRadius: 8, fontSize: 12, fontFamily: 'var(--font-display)', background: 'transparent', border: '1px solid var(--line)', color: 'var(--tx-dim)' };
function Out({ text }) {
  if (!text) return null;
  return <div className="panel mono" style={{ padding: 12, marginTop: 12, fontSize: 11, color: 'var(--tx-dim)', whiteSpace: 'pre-wrap', maxHeight: 260, overflow: 'auto' }}>{text}</div>;
}
function Sec({ title, children }) {
  return <div className="panel" style={{ padding: 16, marginBottom: 16 }}>
    <div className="eyebrow" style={{ marginBottom: 12 }}>{title}</div>{children}</div>;
}

/* ── 🔌 Proveedor (cerebro de Hermes) ────────────────────────────────── */
function ProviderTab() {
  const [data, setData] = useState(null);
  const [key, setKey] = useState('');
  const [model, setModel] = useState('');
  const [sel, setSel] = useState('');
  const [out, setOut] = useState('');
  const [login, setLogin] = useState(false);
  const load = () => callB('hermes_providers').then(r => {
    if (r.ok) { setData(r); const cur = r.current_provider || (r.providers[0] && r.providers[0].key); setSel(cur); setModel(r.current_model || ''); }
  });
  useEffect(() => { load(); }, []);
  useHermesEvent(r => { if (r.op === 'test_brain' && r.done) setOut(o => o + '\n' + (r.out || (r.ok ? 'OK' : 'fallo'))); });
  if (!data) return <div className="faint mono" style={{ padding: 20 }}>// cargando proveedores…</div>;
  const spec = data.providers.find(p => p.key === sel) || data.providers[0];
  return <div>
    <Sec title="ESTADO ACTUAL · 現状">
      <div className="mono" style={{ fontSize: 12.5 }}>cerebro: <b style={{ color: 'var(--accent)' }}>{data.current_provider || '—'}</b> · <b>{data.current_model || '—'}</b></div>
    </Sec>
    <Sec title="CONFIGURAR CEREBRO · 頭脳">
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
        <label className="mono" style={{ fontSize: 12, color: 'var(--tx-dim)' }}>proveedor{' '}
          <select value={sel} onChange={e => { setSel(e.target.value); setModel(''); }} style={FLD}>
            {data.providers.map(p => <option key={p.key} value={p.key}>{p.label}{p.has_auth ? ' ✓' : ''}</option>)}
          </select></label>
        <label className="mono" style={{ fontSize: 12, color: 'var(--tx-dim)' }}>modelo{' '}
          <input list="np-models" value={model} onChange={e => setModel(e.target.value)} placeholder="modelo…" style={{ ...FLD, width: 220 }} />
          <datalist id="np-models">{(spec.models || []).map(m => <option key={m} value={m} />)}</datalist></label>
      </div>
      <div className="dim" style={{ fontSize: 11.5, marginTop: 8, lineHeight: 1.5 }}>{spec.note}</div>
      <div style={{ display: 'flex', gap: 10, marginTop: 12, flexWrap: 'wrap', alignItems: 'center' }}>
        {spec.auth === 'api'
          ? <><input type="password" value={key} onChange={e => setKey(e.target.value)} placeholder={'API key de ' + spec.key} style={{ ...FLD, width: 260 }} />
            <button style={GBTN} onClick={() => callB('hermes_save_key', spec.key, key).then(r => { setOut(o => o + '\n' + (r.out || (r.ok ? 'key guardada' : r.error))); setKey(''); load(); })}>Guardar key</button></>
          : <button style={GBTN} onClick={() => { setLogin(true); callB('hermes_login', spec.key); }}>🔐 Login OAuth</button>}
        <button style={SBTN} onClick={() => callB('hermes_set_model', spec.key, model).then(r => { setOut(o => o + '\n' + (r.out || (r.ok ? 'modelo aplicado' : r.error))); load(); })}>Usar este modelo</button>
        <button style={GBTN} onClick={() => { setOut(o => o + '\n▶ probando…'); callB('hermes_test_brain'); }}>Probar</button>
        <button style={GBTN} onClick={load}>↻</button>
      </div>
    </Sec>
    {login && <HermesFrame kind="hermes-login" onStart={() => {}} />}
    <Out text={out} />
  </div>;
}

/* ── 🎨 Imágenes (Runware) ───────────────────────────────────────────── */
function ImagesTab() {
  const [st, setSt] = useState(null);
  const [key, setKey] = useState('');
  const [arch, setArch] = useState('');
  const [q, setQ] = useState('');
  const [models, setModels] = useState([]);
  const [air, setAir] = useState('');
  const [prompt, setPrompt] = useState('neon tokyo street, cyberpunk');
  const [img, setImg] = useState('');
  const [out, setOut] = useState('');
  const load = () => callB('runware_status').then(setSt);
  useEffect(() => { load(); }, []);
  useHermesEvent(r => {
    if (r.op === 'runware_search' && r.done) { setModels(r.models || []); setOut(o => o + '\n' + (r.ok ? (r.models || []).length + ' modelos' : r.error)); }
    if (r.op === 'runware_test' && r.done) { if (r.url) setImg(r.url); setOut(o => o + '\n' + (r.ok ? '✓ imagen generada' : '✗ ' + r.error)); }
  });
  if (!st) return <div className="faint mono" style={{ padding: 20 }}>// cargando…</div>;
  if (!st.ok) return <div className="panel mono faint" style={{ padding: 20, color: 'var(--gemini)' }}>// Runware no disponible: {st.error}</div>;
  return <div>
    <Sec title="API KEY RUNWARE · 鍵">
      <div className="mono" style={{ fontSize: 12, color: st.has_key ? 'var(--codex)' : 'var(--tx-faint)' }}>● {st.has_key ? 'key configurada' : 'sin key'}</div>
      <div style={{ display: 'flex', gap: 10, marginTop: 10 }}>
        <input type="password" value={key} onChange={e => setKey(e.target.value)} placeholder="RUNWARE_API_KEY" style={{ ...FLD, width: 280 }} />
        <button style={GBTN} onClick={() => callB('runware_save_key', key).then(() => { setKey(''); load(); })}>Guardar</button>
      </div>
    </Sec>
    <Sec title="BUSCAR MODELO · 検索">
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
        <select value={arch} onChange={e => setArch(e.target.value)} style={FLD}><option value="">arquitectura…</option>{(st.architectures || []).map(a => <option key={a} value={a}>{a}</option>)}</select>
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="ej: flux realistic" style={{ ...FLD, width: 220 }} />
        <button style={SBTN} onClick={() => { setOut(o => o + '\n▶ buscando…'); callB('runware_search', q, arch); }}>Buscar</button>
      </div>
      {models.length > 0 && <div className="panel" style={{ marginTop: 10, maxHeight: 180, overflow: 'auto', padding: 6 }}>
        {models.map(m => <div key={m.air} onClick={() => setAir(m.air)} style={{ cursor: 'pointer', padding: '6px 8px', borderRadius: 6, fontSize: 11.5, background: air === m.air ? 'rgba(var(--accent-rgb),0.12)' : 'transparent' }}>
          <span className="mono">{m.name}</span> <span className="faint">· {m.architecture}</span></div>)}
      </div>}
      <div style={{ display: 'flex', gap: 10, marginTop: 10, alignItems: 'center' }}>
        <span className="mono faint" style={{ fontSize: 11 }}>defecto: {st.default || '—'}{air ? ' → ' + air : ''}</span>
        <button style={GBTN} disabled={!air} onClick={() => callB('runware_set_default', air).then(load)}>Usar por defecto</button>
      </div>
    </Sec>
    <Sec title="PROBAR GENERACIÓN · 試">
      <div style={{ display: 'flex', gap: 10 }}>
        <input value={prompt} onChange={e => setPrompt(e.target.value)} style={{ ...FLD, flex: 1 }} />
        <button style={SBTN} onClick={() => { setOut(o => o + '\n▶ generando…'); callB('runware_test', prompt, air); }}>Probar</button>
      </div>
      {img && <img src={img} alt="" style={{ marginTop: 12, maxWidth: '100%', borderRadius: 8, border: '1px solid var(--line)' }} />}
    </Sec>
    <Out text={out} />
  </div>;
}

/* ── 🤖 Agentes (skills) ─────────────────────────────────────────────── */
function AgentsTab() {
  const [skills, setSkills] = useState([]);
  const [webonly, setWebonly] = useState(false);
  const [detail, setDetail] = useState('');
  const [q, setQ] = useState('');
  const [iid, setIid] = useState('');
  const [out, setOut] = useState('');
  const [pack, setPack] = useState(null);
  const [picked, setPicked] = useState({});
  const load = () => callB('hermes_skills', webonly).then(r => { if (r.ok) setSkills(r.skills); });
  useEffect(() => { load(); }, [webonly]);
  useHermesEvent(r => {
    if (r.op === 'skills_search' && r.done) setOut(o => o + '\n' + (r.out || ''));
    if (r.op === 'install_skill') { if (r.line) setOut(o => (o + r.line).slice(-6000)); if (r.done) { setOut(o => o + '\n■ instalación terminada'); load(); } }
    if (r.op === 'install_pack') { if (r.line) setOut(o => (o + r.line).slice(-6000)); if (r.done) { setOut(o => o + '\n■ pack instalado'); load(); } }
  });
  const openPack = () => callB('hermes_skill_pack').then(r => { setPack(r.groups || []); const p = {}; (r.groups || []).forEach(g => g.items.forEach(it => p[it.id] = true)); setPicked(p); });
  return <div>
    <Sec title="AGENTES INSTALADOS · 代理">
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center', marginBottom: 10 }}>
        <label className="mono" style={{ fontSize: 12, color: 'var(--tx-dim)' }}><input type="checkbox" checked={webonly} onChange={e => setWebonly(e.target.checked)} /> solo web/diseño</label>
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="buscar en el registro…" style={{ ...FLD, width: 220 }} />
        <button style={GBTN} onClick={() => { setOut(o => o + '\n▶ buscando «' + q + '»…'); callB('hermes_skills_search', q); }}>Buscar registro</button>
        <button style={GBTN} onClick={() => callB('hermes_seed_web_agents').then(r => { setOut(o => o + '\n' + (r.ok ? 'sembrados: ' + (r.names || []).join(', ') : r.error)); load(); })}>Sembrar web</button>
        <button style={GBTN} onClick={openPack}>📦 Pack web</button>
        <button style={GBTN} onClick={load}>↻</button>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <div className="panel" style={{ maxHeight: 240, overflow: 'auto', padding: 6 }}>
          {skills.length ? skills.map(s => <div key={s.path} onClick={() => callB('hermes_skill_detail', s.path).then(r => setDetail(r.text || ''))} style={{ cursor: 'pointer', padding: '7px 9px', borderRadius: 6, fontSize: 12 }}>
            {s.tf ? '⭐ ' : ''}<b>{s.name}</b><div className="faint" style={{ fontSize: 10.5 }}>{s.category}</div></div>)
            : <div className="faint mono" style={{ padding: 16 }}>// sin skills</div>}
        </div>
        <div className="panel mono" style={{ maxHeight: 240, overflow: 'auto', padding: 10, fontSize: 10.5, whiteSpace: 'pre-wrap', color: 'var(--tx-dim)' }}>{detail || '// selecciona un agente'}</div>
      </div>
      <div style={{ display: 'flex', gap: 10, marginTop: 10 }}>
        <input value={iid} onChange={e => setIid(e.target.value)} placeholder="id/url a instalar — ej: official/devops/docker" style={{ ...FLD, flex: 1 }} />
        <button style={SBTN} onClick={() => { setOut(o => o + '\n▶ instalando…'); callB('hermes_install_skill', iid); }}>Instalar</button>
      </div>
    </Sec>
    {pack && <Sec title="PACK CURADO · 束">
      <div style={{ maxHeight: 220, overflow: 'auto' }}>
        {pack.map(g => <div key={g.domain} style={{ marginBottom: 8 }}>
          <div className="mono" style={{ fontSize: 11, color: 'var(--accent)' }}>{g.domain}</div>
          {g.items.map(it => <label key={it.id} className="mono" style={{ display: 'block', fontSize: 11.5, padding: '2px 0' }}>
            <input type="checkbox" checked={!!picked[it.id]} onChange={e => setPicked(p => ({ ...p, [it.id]: e.target.checked }))} /> {it.label}</label>)}
        </div>)}
      </div>
      <button style={SBTN} onClick={() => { const ids = Object.keys(picked).filter(k => picked[k]).join(','); setOut(o => o + '\n▶ instalando pack…'); callB('hermes_install_pack', ids); setPack(null); }}>📥 Instalar seleccionadas</button>
    </Sec>}
    <Out text={out} />
  </div>;
}

/* ── ➕ Crear agente ─────────────────────────────────────────────────── */
function CreateTab() {
  const [name, setName] = useState('');
  const [stacks, setStacks] = useState('');
  const [spec, setSpec] = useState('');
  const [body, setBody] = useState('');
  const [out, setOut] = useState('');
  useHermesEvent(r => { if (r.op === 'draft_skill' && r.done) { if (r.ok && r.out) setBody(r.out); setOut(o => o + '\n' + (r.ok ? '✓ redactado' : '✗ ' + (r.out || ''))); } });
  return <div>
    <Sec title="NUEVO AGENTE · 新規">
      <div style={{ display: 'grid', gap: 10 }}>
        <input value={name} onChange={e => setName(e.target.value)} placeholder="nombre — ej: shopify-pro" style={FLD} />
        <input value={stacks} onChange={e => setStacks(e.target.value)} placeholder="stacks base (separados por coma)" style={FLD} />
        <input value={spec} onChange={e => setSpec(e.target.value)} placeholder="especialidad — qué hace y cuándo usarlo" style={FLD} />
      </div>
      <div style={{ display: 'flex', gap: 10, marginTop: 10 }}>
        <button style={GBTN} onClick={() => callB('hermes_skill_template', name, stacks, spec).then(r => { if (r.ok) setBody(r.template); })}>Plantilla</button>
        <button style={GBTN} onClick={() => { setOut(o => o + '\n▶ Hermes redactando…'); callB('hermes_skill_draft_ai', name, stacks, spec); }}>Redactar con IA</button>
        <button style={SBTN} onClick={() => callB('hermes_skill_save', name, body).then(r => setOut(o => o + '\n' + (r.ok ? '✓ guardado en ' + r.path : '✗ ' + r.error)))}>Guardar skill</button>
      </div>
    </Sec>
    <textarea value={body} onChange={e => setBody(e.target.value)} placeholder="El SKILL.md aparecerá aquí (editable)…" style={{ ...FLD, width: '100%', minHeight: 280, fontSize: 11.5, lineHeight: 1.5 }} />
    <Out text={out} />
  </div>;
}

/* ── 🧠 Memoria ──────────────────────────────────────────────────────── */
function MemFile({ label, value, max, onSave }) {
  const [v, setV] = useState(value || '');
  const [msg, setMsg] = useState('');
  return <div className="panel" style={{ padding: 12, flex: 1 }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <div className="eyebrow">{label}</div>
      <span className="mono faint" style={{ fontSize: 10.5, color: v.length > max ? 'var(--gemini)' : 'var(--tx-faint)' }}>{v.length}/{max}</span>
    </div>
    <textarea value={v} onChange={e => setV(e.target.value)} style={{ ...FLD, width: '100%', minHeight: 160, marginTop: 8, fontSize: 11.5 }} />
    <button style={{ ...GBTN, marginTop: 8 }} onClick={() => onSave(v).then(r => { setMsg(r.ok ? '✓ guardado' : '✗ ' + r.error); setTimeout(() => setMsg(''), 2000); })}>Guardar {msg}</button>
  </div>;
}
function MemoryTab() {
  const [d, setD] = useState(null);
  const [note, setNote] = useState('');
  const load = () => callB('hermes_memory').then(setD);
  useEffect(() => { load(); }, []);
  if (!d) return <div className="faint mono" style={{ padding: 20 }}>// cargando memoria…</div>;
  if (!d.ok) return <div className="panel mono faint" style={{ padding: 20, color: 'var(--gemini)' }}>// {d.error}</div>;
  const lim = d.limits || {};
  return <div>
    <div style={{ display: 'flex', gap: 14, marginBottom: 16, flexWrap: 'wrap' }}>
      <MemFile label="MEMORY.md · エージェント" value={d.memory} max={lim['MEMORY.md'] || 2200} onSave={v => callB('hermes_memory_save', 'MEMORY.md', v)} />
      <MemFile label="USER.md · 利用者" value={d.user} max={lim['USER.md'] || 1375} onSave={v => callB('hermes_memory_save', 'USER.md', v)} />
    </div>
    <Sec title="NOTAS POR PROYECTO · 案件">
      <div style={{ display: 'grid', gridTemplateColumns: '240px 1fr', gap: 12 }}>
        <div className="panel" style={{ maxHeight: 200, overflow: 'auto', padding: 6 }}>
          {(d.projects || []).length ? d.projects.map(p => <div key={p.path} onClick={() => callB('hermes_project_note', p.path).then(r => setNote(r.text || ''))} style={{ cursor: 'pointer', padding: '6px 8px', borderRadius: 6, fontSize: 12 }}>{p.name}</div>)
            : <div className="faint mono" style={{ padding: 12 }}>// sin .hermes.md</div>}
        </div>
        <div className="panel mono" style={{ maxHeight: 200, overflow: 'auto', padding: 10, fontSize: 10.5, whiteSpace: 'pre-wrap', color: 'var(--tx-dim)' }}>{note || '// selecciona un proyecto'}</div>
      </div>
    </Sec>
    <Sec title="SESIONES · 履歴"><div className="mono" style={{ fontSize: 11, whiteSpace: 'pre-wrap', color: 'var(--tx-dim)' }}>{d.sessions || '—'}</div></Sec>
  </div>;
}

/* ── 📊 Kanban ───────────────────────────────────────────────────────── */
function KanbanTab() {
  const [boards, setBoards] = useState([]);
  const [board, setBoard] = useState('');
  const [tasks, setTasks] = useState([]);
  const [nt, setNt] = useState({ title: '', body: '', priority: '', skill: '' });
  const [out, setOut] = useState('');
  useEffect(() => { callB('kanban_boards').then(r => { if (r.ok) { setBoards(r.boards); if (r.boards[0]) setBoard(r.boards[0]); } }); }, []);
  const loadTasks = (b) => callB('kanban_tasks', b || board).then(r => { if (r.ok) setTasks(r.tasks); });
  useEffect(() => { if (board) loadTasks(board); }, [board]);
  useHermesEvent(r => { if (r.op === 'kanban_dispatch') { if (r.line) setOut(o => (o + r.line).slice(-6000)); if (r.done) { setOut(o => o + '\n■ dispatch terminado'); loadTasks(); } } });
  return <div>
    <Sec title="TABLERO · 板">
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
        <select value={board} onChange={e => setBoard(e.target.value)} style={FLD}>{boards.length ? boards.map(b => <option key={b} value={b}>{b}</option>) : <option value="">(sin tableros)</option>}</select>
        <button style={SBTN} onClick={() => { setOut(o => o + '\n▶ dispatch…'); callB('kanban_dispatch', board); }}>▶ Dispatch</button>
        <button style={GBTN} onClick={() => loadTasks()}>↻</button>
      </div>
      <div className="panel" style={{ marginTop: 10, padding: 0, overflow: 'hidden' }}>
        {tasks.length ? tasks.map(t => <div key={t.id} style={{ display: 'flex', gap: 10, padding: '8px 12px', borderBottom: '1px solid var(--line)', fontSize: 12 }}>
          <span className="mono faint" style={{ width: 60 }}>{t.id}</span>
          <span style={{ flex: 1 }}>{t.title}</span>
          <span className="mono" style={{ color: 'var(--accent)' }}>{t.status}</span>
          <span className="mono faint" style={{ width: 90, textAlign: 'right' }}>{t.assignee}</span>
          <span className="mono dim" style={{ width: 60, textAlign: 'right' }}>{t.priority}</span>
        </div>) : <div className="faint mono" style={{ padding: 16 }}>// sin tareas</div>}
      </div>
    </Sec>
    <Sec title="NUEVA TAREA · 新規">
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <input value={nt.title} onChange={e => setNt({ ...nt, title: e.target.value })} placeholder="título" style={FLD} />
        <select value={nt.priority} onChange={e => setNt({ ...nt, priority: e.target.value })} style={FLD}><option value="">prioridad…</option>{['low', 'medium', 'high', 'urgent'].map(p => <option key={p} value={p}>{p}</option>)}</select>
        <input value={nt.skill} onChange={e => setNt({ ...nt, skill: e.target.value })} placeholder="skill (opcional)" style={FLD} />
        <input value={nt.body} onChange={e => setNt({ ...nt, body: e.target.value })} placeholder="detalle (opcional)" style={FLD} />
      </div>
      <button style={{ ...SBTN, marginTop: 10 }} onClick={() => callB('kanban_create', board, nt.title, nt.body, nt.priority, nt.skill).then(r => { setOut(o => o + '\n' + (r.ok ? '✓ creada' : '✗ ' + (r.out || r.error))); setNt({ title: '', body: '', priority: '', skill: '' }); loadTasks(); })}>Crear tarea</button>
    </Sec>
    <Out text={out} />
  </div>;
}

/* ── ⏰ Cron ─────────────────────────────────────────────────────────── */
function CronTab() {
  const [jobs, setJobs] = useState([]);
  const [sel, setSel] = useState('');
  const [f, setF] = useState({ schedule: '', prompt: '', skill: '', deliver: 'local', name: '' });
  const [out, setOut] = useState('');
  const load = () => callB('cron_jobs').then(r => { if (r.ok) setJobs(r.jobs); });
  useEffect(() => { load(); }, []);
  const op = (a) => { if (!sel) return; if (a === 'remove' && !confirm('¿Eliminar el job?')) return; callB('cron_op', a, sel).then(r => { setOut(o => o + '\n' + (r.ok ? '✓ ' + a : '✗ ' + r.out)); load(); }); };
  return <div>
    <Sec title="MISIONES PROGRAMADAS · 予定">
      <div className="panel" style={{ padding: 0, overflow: 'hidden' }}>
        {jobs.length ? jobs.map(j => <div key={j.id} onClick={() => setSel(j.id)} style={{ cursor: 'pointer', display: 'flex', gap: 10, padding: '8px 12px', borderBottom: '1px solid var(--line)', fontSize: 12, background: sel === j.id ? 'rgba(var(--accent-rgb),0.10)' : 'transparent' }}>
          <span>{j.paused ? '⏸' : '▶'}</span>
          <span className="mono" style={{ width: 120 }}>{j.schedule}</span>
          <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{j.name || j.prompt}</span>
          <span className="mono faint" style={{ width: 120, textAlign: 'right' }}>{j.next}</span>
        </div>) : <div className="faint mono" style={{ padding: 16 }}>// sin jobs</div>}
      </div>
      <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
        <button style={GBTN} onClick={() => op('pause')}>⏸ Pausar</button>
        <button style={GBTN} onClick={() => op('resume')}>▶ Reanudar</button>
        <button style={GBTN} onClick={() => op('run')}>⚡ Ejecutar</button>
        <button style={{ ...GBTN, color: 'var(--gemini)' }} onClick={() => op('remove')}>🗑 Eliminar</button>
        <button style={{ ...GBTN, marginLeft: 'auto' }} onClick={load}>↻</button>
      </div>
    </Sec>
    <Sec title="PROGRAMAR · 設定">
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <input value={f.schedule} onChange={e => setF({ ...f, schedule: e.target.value })} placeholder="cuándo — every 1d · 30m · 0 9 * * 1-5" style={FLD} />
        <input value={f.name} onChange={e => setF({ ...f, name: e.target.value })} placeholder="nombre (opcional)" style={FLD} />
        <input value={f.skill} onChange={e => setF({ ...f, skill: e.target.value })} placeholder="skill — ej: themeforge-operator" style={FLD} />
        <select value={f.deliver} onChange={e => setF({ ...f, deliver: e.target.value })} style={FLD}>{['local', 'origin', 'telegram', 'discord', 'slack', 'email', 'all'].map(d => <option key={d} value={d}>{d}</option>)}</select>
      </div>
      <textarea value={f.prompt} onChange={e => setF({ ...f, prompt: e.target.value })} placeholder="tarea / prompt…" style={{ ...FLD, width: '100%', minHeight: 70, marginTop: 10 }} />
      <button style={{ ...SBTN, marginTop: 10 }} onClick={() => callB('cron_create', f.schedule, f.prompt, f.skill, f.deliver, f.name).then(r => { setOut(o => o + '\n' + (r.ok ? '✓ programada' : '✗ ' + (r.out || r.error))); if (r.ok) setF({ schedule: '', prompt: '', skill: '', deliver: 'local', name: '' }); load(); })}>Programar</button>
    </Sec>
    <Out text={out} />
  </div>;
}

/* ── 📲 Remoto (gateway) ─────────────────────────────────────────────── */
function RemoteTab() {
  const [plats, setPlats] = useState([]);
  const [plat, setPlat] = useState('');
  const [target, setTarget] = useState('');
  const [msg, setMsg] = useState('');
  const [pcode, setPcode] = useState({ plat: '', code: '' });
  const [out, setOut] = useState('');
  const [setup, setSetup] = useState(false);
  useEffect(() => { callB('gateway_platforms').then(r => { if (r.ok) { setPlats(r.platforms); if (r.platforms[0]) setPlat(r.platforms[0].key); } }); }, []);
  useHermesEvent(r => { if (r.op === 'gateway_send' && r.done) setOut(o => o + '\n' + (r.ok ? '✓ enviado' : '✗ ' + r.out)); });
  const run = (slot, ...a) => callB(slot, ...a).then(r => setOut(o => (o + '\n' + (r.out || (r.ok ? 'ok' : r.error))).slice(-6000)));
  const hint = (plats.find(p => p.key === plat) || {}).hint;
  return <div>
    <Sec title="SERVICIO GATEWAY · 接続">
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <button style={SBTN} onClick={() => setSetup(true)}>⚙ Configurar plataformas</button>
        <button style={GBTN} onClick={() => run('gateway_op', 'status')}>Estado</button>
        <button style={GBTN} onClick={() => run('gateway_op', 'install')}>Instalar servicio</button>
        <button style={GBTN} onClick={() => run('gateway_op', 'start')}>Arrancar</button>
        <button style={GBTN} onClick={() => run('gateway_op', 'stop')}>Parar</button>
      </div>
      {setup && <HermesFrame kind="hermes-gateway" onStart={() => callB('gateway_setup')} />}
    </Sec>
    <Sec title="ENVIAR MENSAJE · 送信">
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
        <select value={plat} onChange={e => setPlat(e.target.value)} style={FLD}>{plats.map(p => <option key={p.key} value={p.key}>{p.key}</option>)}</select>
        <button style={GBTN} onClick={() => run('gateway_targets')}>Ver targets</button>
      </div>
      <div className="dim" style={{ fontSize: 11, marginTop: 6 }}>{hint}</div>
      <div style={{ display: 'flex', gap: 10, marginTop: 10 }}>
        <input value={target} onChange={e => setTarget(e.target.value)} placeholder="destino — telegram · discord:#ops · slack:#eng" style={{ ...FLD, width: 240 }} />
        <input value={msg} onChange={e => setMsg(e.target.value)} placeholder="mensaje de prueba" style={{ ...FLD, flex: 1 }} />
        <button style={SBTN} onClick={() => { setOut(o => o + '\n▶ enviando…'); callB('gateway_send', target, msg); }}>Enviar</button>
      </div>
    </Sec>
    <Sec title="PAIRING · 承認">
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
        <button style={GBTN} onClick={() => run('pairing_list')}>Ver pairings</button>
        <input value={pcode.plat} onChange={e => setPcode({ ...pcode, plat: e.target.value })} placeholder="plataforma" style={{ ...FLD, width: 120 }} />
        <input value={pcode.code} onChange={e => setPcode({ ...pcode, code: e.target.value })} placeholder="código" style={{ ...FLD, width: 120 }} />
        <button style={SBTN} onClick={() => run('pairing_approve', pcode.plat, pcode.code)}>Aprobar</button>
      </div>
    </Sec>
    <Out text={out} />
  </div>;
}

/* ── 🛡️ Avanzado ─────────────────────────────────────────────────────── */
function AdvancedTab() {
  const [sec, setSec] = useState({ backend: 'local', mode: 'smart' });
  const [out, setOut] = useState('');
  const [fb, setFb] = useState(false);
  useEffect(() => { callB('hermes_security').then(r => { if (r.ok) setSec({ backend: r.backend, mode: r.mode }); }); }, []);
  useHermesEvent(r => { if (r.op === 'insights' && r.done) setOut(o => o + '\n' + (r.out || '')); });
  const run = (slot, ...a) => callB(slot, ...a).then(r => setOut(o => (o + '\n' + (r.out || (r.ok ? 'ok' : r.error))).slice(-6000)));
  return <div>
    <Sec title="AISLAMIENTO & SEGURIDAD · 隔離">
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
        <label className="mono" style={{ fontSize: 12, color: 'var(--tx-dim)' }}>backend{' '}
          <select value={sec.backend} onChange={e => setSec({ ...sec, backend: e.target.value })} style={FLD}>{['local', 'docker', 'ssh', 'modal', 'daytona', 'singularity'].map(b => <option key={b} value={b}>{b}</option>)}</select></label>
        <label className="mono" style={{ fontSize: 12, color: 'var(--tx-dim)' }}>aprobaciones{' '}
          <select value={sec.mode} onChange={e => setSec({ ...sec, mode: e.target.value })} style={FLD}>{['manual', 'smart', 'off'].map(m => <option key={m} value={m}>{m}</option>)}</select></label>
        <button style={SBTN} onClick={() => run('hermes_security_apply', sec.backend, sec.mode)}>Aplicar seguridad</button>
      </div>
    </Sec>
    <Sec title="PORTAL DE HERRAMIENTAS · 道具">
      <div style={{ display: 'flex', gap: 8 }}>
        <button style={GBTN} onClick={() => run('hermes_portal', 'status')}>Estado del portal</button>
        <button style={GBTN} onClick={() => run('hermes_portal', 'tools')}>Herramientas</button>
      </div>
    </Sec>
    <Sec title="PERFIL & BUNDLE · 束">
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <button style={GBTN} onClick={() => run('hermes_profile_create')}>Crear perfil themeforge</button>
        <button style={GBTN} onClick={() => run('hermes_bundle_create')}>Crear bundle /themeforge</button>
        <button style={GBTN} onClick={() => run('hermes_profile_list')}>Listar perfiles</button>
      </div>
    </Sec>
    <Sec title="COSTE & FALLBACK · 費用">
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <button style={GBTN} onClick={() => { setOut(o => o + '\n▶ insights…'); callB('hermes_insights', 30); }}>Insights (30d)</button>
        <button style={GBTN} onClick={() => run('hermes_fallback_list')}>Ver fallback</button>
        <button style={GBTN} onClick={() => setFb(true)}>Añadir fallback</button>
      </div>
      {fb && <HermesFrame kind="hermes-fallback" onStart={() => callB('hermes_fallback_add')} />}
    </Sec>
    <Out text={out} />
  </div>;
}

/* ── misión: fila + frame embebido ───────────────────────────────────── */
function MissionRow({ m }) {
  const ag = AGENTS[m.agent] || { color: 'var(--accent)', glyph: '◆', label: m.agent };
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

function HermesFrame({ kind, start, onStart }) {
  const [url, setUrl] = useState(null); const [err, setErr] = useState(null);
  useEffect(() => {
    const B = window.tfBridge;
    if (!B || !B.terminal_ready || !B.terminal_ready.connect) { setErr('sin puente'); return; }
    const onReady = (j) => { let r = {}; try { r = JSON.parse(j); } catch (e) {} if (r.kind === kind) { if (r.url) setUrl(r.url); else if (r.error) setErr(r.error); } };
    B.terminal_ready.connect(onReady);
    if (onStart) onStart(); else if (B[start]) B[start]();
    return () => { try { B.terminal_ready.disconnect(onReady); } catch (e) {} };
  }, [kind]);
  if (err) return <div className="panel mono faint" style={{ padding: 20, color: 'var(--gemini)' }}>// {err}</div>;
  if (!url) return <div className="panel mono faint" style={{ padding: 20 }}>// iniciando {kind}…</div>;
  return <iframe src={url} style={{ width: '100%', height: '70vh', border: '1px solid var(--line)', borderRadius: 8, background: '#0c0c0d', marginTop: 12 }} />;
}

/* ── pantalla Operator ───────────────────────────────────────────────── */
const HTABS = [
  ['mision', '🎯 Misión'], ['proveedor', '🔌 Proveedor'], ['imagenes', '🎨 Imágenes'],
  ['agentes', '🤖 Agentes'], ['crear', '➕ Crear'], ['memoria', '🧠 Memoria'],
  ['kanban', '📊 Kanban'], ['cron', '⏰ Cron'], ['remoto', '📲 Remoto'],
  ['avanzado', '🛡️ Avanzado'], ['chat', '💬 Chat'], ['admin', '⚙ Admin'],
];

function OperatorScreen() {
  const _op = (window.__TF_DATA__ && window.__TF_DATA__.operator) || {};
  const real = !!(window.tfBridge && window.tfBridge.launch_mission);
  const [missions, setMissions] = useState(real ? (_op.missions || []) : (typeof MISSIONS !== 'undefined' ? MISSIONS : []));
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
  const chip = (ok, l) => <span className="mono" style={{ fontSize: 11.5, color: ok == null ? 'var(--tx-faint)' : (ok ? 'var(--codex)' : 'var(--gemini)') }}>● {l}</span>;
  const off = <div className="panel mono faint" style={{ padding: 20 }}>// enciende Hermes para usar esta pestaña</div>;
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
        {HTABS.map(([k, l]) => <button key={k} onClick={() => setTab(k)} style={{ cursor: 'pointer', padding: '8px 14px', borderRadius: 10, fontSize: 12.5, fontFamily: 'var(--font-display)', background: tab === k ? 'rgba(var(--accent-rgb),0.12)' : 'transparent', border: '1px solid ' + (tab === k ? 'rgba(var(--accent-rgb),0.45)' : 'var(--line)'), color: tab === k ? 'var(--accent)' : 'var(--tx-dim)' }}>{l}</button>)}
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
      <div className="panel" style={{ padding: 16, marginBottom: 18 }}>
        <textarea value={brief} onChange={e => setBrief(e.target.value)} placeholder='Brief de la misión — ej: "landing Envato para clínica dental, stack Astro"'
          style={{ width: '100%', minHeight: 64, resize: 'vertical', background: 'var(--bg-void)', border: '1px solid var(--line-bright)', borderRadius: 8, padding: 12, color: 'var(--tx)', fontFamily: 'var(--font-mono)', fontSize: 12.5, outline: 'none' }} />
        <div style={{ display: 'flex', gap: 14, marginTop: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <label className="mono" style={{ fontSize: 12, color: 'var(--tx-dim)' }}>variantes <input type="number" min={1} max={6} value={variants} onChange={e => setVariants(+e.target.value)} style={{ width: 56, background: 'var(--bg-void)', border: '1px solid var(--line-bright)', borderRadius: 6, padding: '5px 8px', color: 'var(--tx)' }} /></label>
          <label className="mono" style={{ fontSize: 12, color: 'var(--tx-dim)' }}>agente <select value={prov} onChange={e => setProv(e.target.value)} style={{ background: 'var(--bg-void)', border: '1px solid var(--line-bright)', borderRadius: 6, padding: '5px 8px', color: 'var(--tx)' }}>{['codex', 'opencode', 'claude-api', 'gemini'].map(p => <option key={p} value={p}>{p}</option>)}</select></label>
        </div>
      </div>
      {log && <div className="panel mono" style={{ padding: 14, marginBottom: 18, fontSize: 11.5, color: 'var(--tx-dim)', whiteSpace: 'pre-wrap', maxHeight: 220, overflow: 'auto' }}>{log}</div>}
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
