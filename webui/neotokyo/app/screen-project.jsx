/* ================= NEO-TOKYO · Project Window ================= */

const TERM_SCRIPT = [
  { t: 'cmd', s: '$ themeforge agent --provider claude --task "build hero + features"' },
  { t: 'sys', s: '✳ Claude Code · session forge-7f2a · model claude-sonnet-4.5' },
  { t: 'out', s: '⟳ reading CLAUDE.md … context loaded (2.4k tokens)' },
  { t: 'out', s: '⟳ scaffolding app/(marketing)/page.tsx' },
  { t: 'ok',  s: '✓ wrote components/Hero.tsx (+148 −0)' },
  { t: 'ok',  s: '✓ wrote components/FeatureBento.tsx (+212 −0)' },
  { t: 'out', s: '⟳ wiring tailwind tokens · neon palette' },
  { t: 'ok',  s: '✓ wrote app/globals.css (+64 −12)' },
  { t: 'out', s: '⟳ running typecheck …' },
  { t: 'ok',  s: '✓ tsc — 0 errors · 0 warnings' },
  { t: 'dim', s: '  tokens: 2.1M in · 38k out · $4.82 · 1m 47s' },
  { t: 'done', s: '◤ task complete — preview hot-reloaded' },
];

function Terminal({ running }) {
  const [lines, setLines] = useState([]);
  const [cur, setCur] = useState('');
  const boxRef = useRef(null);
  const idx = useRef(0);

  useEffect(() => {
    if (!running) return;
    setLines([]); setCur(''); idx.current = 0;
    let timer;
    const next = () => {
      if (idx.current >= TERM_SCRIPT.length) return;
      const line = TERM_SCRIPT[idx.current];
      if (line.t === 'cmd') {
        // typewriter the command
        let c = 0;
        const type = () => {
          setCur(line.s.slice(0, c));
          c++;
          if (c <= line.s.length) timer = setTimeout(type, 16);
          else { setLines(l => [...l, line]); setCur(''); idx.current++; timer = setTimeout(next, 380); }
        };
        type();
      } else {
        setLines(l => [...l, line]); idx.current++;
        timer = setTimeout(next, 220 + Math.random() * 280);
      }
    };
    timer = setTimeout(next, 400);
    return () => clearTimeout(timer);
  }, [running]);

  useEffect(() => { if (boxRef.current) boxRef.current.scrollTop = boxRef.current.scrollHeight; }, [lines, cur]);

  const color = { cmd: 'var(--cyan)', sys: 'var(--claude)', out: 'var(--tx-dim)', ok: 'var(--codex)', dim: 'var(--tx-faint)', done: 'var(--magenta)' };
  return (
    <div ref={boxRef} className="mono" style={{
      background: '#03050b', borderTop: '1px solid var(--line)', padding: '12px 16px',
      fontSize: 12, lineHeight: 1.75, overflowY: 'auto', flex: 1, minHeight: 0,
    }}>
      {lines.map((l, i) => <div key={i} style={{ color: color[l.t], whiteSpace: 'pre-wrap' }}>{l.s}</div>)}
      {cur && <div style={{ color: color.cmd }}>{cur}<span style={{ animation: 'blink 0.9s infinite' }}>▊</span></div>}
      {!running && lines.length === 0 && <div className="faint">// terminal lista — ⏎ para lanzar agente</div>}
      {lines.length >= TERM_SCRIPT.length && (
        <div style={{ color: 'var(--accent)', marginTop: 4 }}>$ <span style={{ animation: 'blink 0.9s infinite' }}>▊</span></div>
      )}
    </div>
  );
}

// Terminal REAL embebida: xterm + node-pty servido por terminal/server.js,
// arrancado por el puente nativo. Cae al terminal mock si no hay puente.
function RealTerminal({ path, running }) {
  const [url, setUrl] = useState(null);
  useEffect(() => {
    if (!window.tfBridge || !window.tfBridge.start_terminal || !path) return;
    const onReady = (j) => {
      let r = {}; try { r = JSON.parse(j); } catch (e) {}
      if (r.path === path && r.url) setUrl(r.url);
    };
    if (window.tfBridge.terminal_ready && window.tfBridge.terminal_ready.connect)
      window.tfBridge.terminal_ready.connect(onReady);
    window.tfBridge.start_terminal(path);
    return () => {
      if (window.tfBridge.terminal_ready && window.tfBridge.terminal_ready.disconnect)
        try { window.tfBridge.terminal_ready.disconnect(onReady); } catch (e) {}
    };
  }, [path]);
  if (!window.tfBridge || !path) return <Terminal running={running} />;
  if (!url) return <div className="mono faint" style={{ flex: 1, padding: 16 }}>// iniciando terminal real (xterm · node-pty)…</div>;
  return <iframe src={url} style={{ flex: 1, width: '100%', height: '100%', border: 'none', background: '#0c0c0d' }} />;
}

// Una terminal real por «kind» (agent/shell/hermes), filtrada por path+kind.
function TermFrame({ path, kind, running }) {
  const [url, setUrl] = useState(null);
  const [err, setErr] = useState(null);
  useEffect(() => {
    const B = window.tfBridge;
    if (!B || !path) return;
    const onReady = (j) => { let r = {}; try { r = JSON.parse(j); } catch (e) {} if (r.path === path && r.kind === kind) { if (r.url) setUrl(r.url); else if (r.error) setErr(r.error); } };
    if (B.terminal_ready && B.terminal_ready.connect) B.terminal_ready.connect(onReady);
    const fn = kind === 'agent' ? B.start_terminal : kind === 'shell' ? B.start_shell : kind === 'hermes' ? B.start_hermes : kind === 'setup' ? B.start_setup : null;
    if (fn) fn.call(B, path);
    return () => { try { B.terminal_ready.disconnect(onReady); } catch (e) {} };
  }, [path, kind]);
  if (!window.tfBridge || !path) return <Terminal running={running} />;
  if (err) return <div className="mono faint" style={{ flex: 1, padding: 16, color: 'var(--gemini)' }}>// {kind}: {err}</div>;
  if (!url) return <div className="mono faint" style={{ flex: 1, padding: 16 }}>// iniciando {kind} (xterm · node-pty)…</div>;
  return <iframe src={url} style={{ flex: 1, width: '100%', height: '100%', border: 'none', background: '#0c0c0d' }} />;
}
// Pestaña «Office» — dashboard pixel-art (visualizador de sesiones).
function OfficeFrame() {
  const [url, setUrl] = useState(null);
  const [msg, setMsg] = useState('// cargando Office…');
  useEffect(() => {
    const B = window.tfBridge;
    if (!B || !B.pixel_office_url) { setMsg('// Office no disponible'); return; }
    B.pixel_office_url().then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {} if (r.installed && r.url) setUrl(r.url); else setMsg('// Pixel Office no instalado — Settings → Pixel Office'); });
  }, []);
  if (!url) return <div className="mono faint" style={{ flex: 1, padding: 16 }}>{msg}</div>;
  return <iframe src={url} style={{ flex: 1, width: '100%', height: '100%', border: 'none', background: '#0c0c0d' }} />;
}
// Pestañas encima del terminal (como en la app normal): Agent · Shell · Hermes · Office.
function TermTabs({ path, running, fresh }) {
  const op = (window.__TF_DATA__ && window.__TF_DATA__.operator) || {};
  const tabs = [];
  if (fresh) tabs.push(['setup', '⚙ Setup']);
  tabs.push(['agent', '◈ Agent'], ['shell', '▮ Shell']);
  if (op.available) tabs.push(['hermes', '🚀 Hermes']);
  tabs.push(['office', '🎮 Office']);
  const first = fresh ? 'setup' : 'agent';
  const [active, setActive] = useState(first);
  const [seen, setSeen] = useState({ [first]: true });
  const open = (k) => { setActive(k); setSeen(s => ({ ...s, [k]: true })); };
  // Al terminar el setup → cambia solo a la pestaña Agent.
  useEffect(() => {
    const B = window.tfBridge;
    if (!fresh || !B || !B.setup_done || !B.setup_done.connect) return;
    const onDone = (j) => { let r = {}; try { r = JSON.parse(j); } catch (e) {} if (r.path === path) { setSeen(s => ({ ...s, agent: true })); setActive('agent'); } };
    B.setup_done.connect(onDone);
    return () => { try { B.setup_done.disconnect(onDone); } catch (e) {} };
  }, [path, fresh]);
  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
      <div style={{ display: 'flex', gap: 5, padding: '8px 12px', borderBottom: '1px solid var(--line)', flexWrap: 'wrap' }}>
        {tabs.map(([k, l]) => (
          <button key={k} onClick={() => open(k)} style={{ cursor: 'pointer', padding: '5px 11px', borderRadius: 7, fontSize: 11.5, fontFamily: 'var(--font-display)', background: active === k ? 'rgba(var(--accent-rgb),0.12)' : 'transparent', border: '1px solid ' + (active === k ? 'rgba(var(--accent-rgb),0.45)' : 'var(--line)'), color: active === k ? 'var(--accent)' : 'var(--tx-dim)' }}>{l}</button>
        ))}
      </div>
      {tabs.map(([k]) => seen[k] ? (
        <div key={k} style={{ display: active === k ? 'flex' : 'none', flex: active === k ? 1 : 0, flexDirection: 'column', minHeight: 0 }}>
          {k === 'office' ? <OfficeFrame /> : <TermFrame path={path} kind={k} running={running} />}
        </div>
      ) : null)}
    </div>
  );
}

// Preview REAL con controles (Start/Stop/Reload/Navegador/Re-detectar), igual
// que la barra de preview de la ProjectWindow nativa.
const VPORTS = [['📱', 360], ['📋', 768], ['💻', 1280], ['🖥', 1920], ['⛶', 0]];
function RealPreview({ path, accent, narrow }) {
  const B = window.tfBridge;
  const [activePath, setActivePath] = useState(path);
  const [subs, setSubs] = useState([]);
  const [url, setUrl] = useState(null);
  const [err, setErr] = useState(null);
  const [status, setStatus] = useState('idle');
  const [k, setK] = useState(0);
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
  const shot = () => { if (B && B.screenshot_preview && activePath) B.screenshot_preview(activePath).then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {} tfToast(r.ok ? ('📸 ' + r.file) : ('Error: ' + (r.error || '')), r.ok ? '#9dff3c' : '#ff2e88'); }); };
  const switchSub = (sp) => { if (status === 'up' && B.stop_preview) B.stop_preview(activePath); setUrl(null); setErr(null); setStatus('idle'); setActivePath(sp); };
  const redetect = () => {
    if (!(B && B.refresh_profile && activePath)) return;
    B.refresh_profile(activePath).then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {}
      if (r.detected) { tfToast('✓ preview detectado: ' + r.profile + ' — arrancando…', '#9dff3c'); if (B.stop_preview) B.stop_preview(activePath); setUrl(null); setErr(null); setStatus('starting'); setTimeout(start, 500); }
      else tfToast('Aún sin preview detectable — ¿el setup terminó de instalar deps?', '#ffb000'); });
  };
  useEffect(() => { if (B && activePath && status === 'idle') start(); }, [activePath]);
  if (!B || !path) return <LivePreview accent={accent} narrow={narrow} />;
  const cbtn = { cursor: 'pointer', padding: '5px 9px', borderRadius: 7, fontSize: 11.5, fontFamily: 'var(--font-display)', background: 'transparent', border: '1px solid var(--line-bright)', color: 'var(--tx-dim)' };
  return (
    <div style={{ display: 'flex', flexDirection: 'column', width: '100%', height: '100%', minHeight: 0 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 10px', borderBottom: '1px solid var(--line)', flexWrap: 'wrap' }}>
        <button style={{ ...cbtn, opacity: (status === 'up' || status === 'starting') ? 0.4 : 1 }} onClick={start}>▶ Start</button>
        <button style={{ ...cbtn, opacity: status !== 'up' ? 0.4 : 1 }} onClick={stop}>■ Stop</button>
        <button style={{ ...cbtn, opacity: status !== 'up' ? 0.4 : 1 }} onClick={reload}>↻</button>
        <button style={{ ...cbtn, opacity: status !== 'up' ? 0.4 : 1 }} onClick={openExt}>🗗</button>
        <button style={{ ...cbtn, opacity: status !== 'up' ? 0.4 : 1 }} onClick={shot}>📸</button>
        <button style={cbtn} onClick={redetect}>🔄</button>
        {subs.length > 1 && <select className="mono" value={activePath} onChange={e => switchSub(e.target.value)} style={{ ...cbtn, padding: '5px 8px' }}>{subs.map(s => <option key={s.path} value={s.path}>{s.name}{s.ref ? ' (ref)' : ''}</option>)}</select>}
        <input className="mono" readOnly value={url || ''} placeholder="URL…" style={{ flex: 1, minWidth: 80, background: 'var(--bg-void)', border: '1px solid var(--line)', borderRadius: 7, padding: '5px 9px', color: 'var(--tx-dim)', fontSize: 11, outline: 'none' }} />
        {VPORTS.map(([e, w]) => <button key={w} style={{ ...cbtn, padding: '5px 7px', background: vw === w ? 'rgba(var(--accent-rgb),0.14)' : 'transparent', color: vw === w ? 'var(--accent)' : 'var(--tx-dim)' }} title={w ? w + 'px' : 'full'} onClick={() => setVw(w)}>{e}</button>)}
      </div>
      <div style={{ flex: 1, display: 'grid', placeItems: 'stretch', minHeight: 0, overflow: 'auto', background: '#070b16' }}>
        {err ? <div className="mono faint" style={{ placeSelf: 'center', padding: 24 }}>// preview: {err}</div>
          : status === 'stopped' ? <div className="mono faint" style={{ placeSelf: 'center', padding: 24 }}>■ preview detenido — pulsa ▶ Start</div>
          : !url ? <div className="mono faint" style={{ alignSelf: 'stretch', width: '100%', overflow: 'auto', padding: 14, fontSize: 11.5, whiteSpace: 'pre-wrap' }}>{'// arrancando dev server (sondeando puerto)…\n' + (log || '')}</div>
          : <iframe key={k} src={url} style={{ width: vw ? vw : '100%', maxWidth: '100%', height: '100%', minHeight: 320, border: 'none', background: '#fff', justifySelf: 'center' }} />}
      </div>
    </div>
  );
}

// Log del setup/scaffold en vivo (señal progress) mientras se construye.
function BuildLog({ lines }) {
  const box = useRef(null);
  useEffect(() => { if (box.current) box.current.scrollTop = box.current.scrollHeight; }, [lines]);
  return (
    <div ref={box} className="mono" style={{ flex: 1, padding: 16, fontSize: 12, lineHeight: 1.7, overflowY: 'auto', minHeight: 0, whiteSpace: 'pre-wrap', color: 'var(--tx-dim)', background: '#03050b' }}>
      {(lines && lines.length) ? lines.join('') : '> esperando salida del scaffold…'}
      <div style={{ color: 'var(--accent)' }}>▊ instalando (scaffold · autoskills · UI/UX Pro · MCP)…</div>
    </div>
  );
}

function tfToast(msg, color) {
  const b = document.createElement('div');
  b.textContent = msg;
  b.style.cssText = 'position:fixed;left:50%;bottom:18px;transform:translateX(-50%);z-index:99999;' +
    'background:#0b1020;color:' + (color || '#00f0ff') + ';border:1px solid ' + (color || '#00f0ff') +
    ';border-radius:10px;padding:10px 18px;font:13px JetBrains Mono,monospace;box-shadow:0 0 18px rgba(0,240,255,.4);max-width:70%';
  document.body.appendChild(b);
  setTimeout(() => b.remove(), 6000);
}

// Barra de MCP servers REAL: lee el .mcp.json del proyecto; clic = activar/desactivar.
function MCPBar({ path }) {
  const B = window.tfBridge;
  const [servers, setServers] = useState([]);
  const load = () => { if (B && B.read_mcp && path) B.read_mcp(path).then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {} if (r.servers) setServers(r.servers); }); };
  useEffect(load, [path]);
  const toggle = (id) => { if (!(B && B.toggle_mcp && path)) return; setServers(s => s.map(x => x.id === id ? { ...x, active: !x.active } : x)); B.toggle_mcp(path, id).then(load); };
  const list = servers.length ? servers : MCP_SERVERS.map(m => ({ id: m.id, label: m.label, active: !!m.always, desc: m.desc }));
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 24px', borderBottom: '1px solid var(--line)', background: 'rgba(0,0,0,0.2)', overflowX: 'auto' }}>
      <span className="eyebrow" style={{ fontSize: 9, flexShrink: 0 }}>MCP ·</span>
      {list.map(m => (
        <button key={m.id} className="chip" title={(m.active ? 'activo · ' : 'inactivo · ') + (m.desc || '')} onClick={() => toggle(m.id)}
          style={{ cursor: 'pointer', fontSize: 9, padding: '2px 8px', flexShrink: 0, opacity: m.active ? 1 : 0.5, color: m.active ? 'var(--accent)' : 'var(--tx-dim)', borderColor: m.active ? 'rgba(var(--accent-rgb),0.5)' : 'var(--line)', background: 'transparent' }}>
          {m.active ? '●' : '○'} {m.label}
        </button>
      ))}
      <span className="mono faint" style={{ fontSize: 10, flexShrink: 0 }}>· clic = on/off (.mcp.json)</span>
    </div>
  );
}
function ProjectWindow({ project, onBack, onDeploy, onBuild, buildLog }) {
  const p = project;
  const [tab, setTab] = useState('desktop');
  const [running, setRunning] = useState(false);
  const [pushed, setPushed] = useState(false);
  const [reply, setReply] = useState('');
  const building = p.status === 'building';
  const B = window.tfBridge;
  const ag = AGENTS[p.agent || 'claude'] || { color: 'var(--accent)', glyph: '◆', label: p.agent || 'agent' };

  useEffect(() => { const t = setTimeout(() => setRunning(true), 600); return () => clearTimeout(t); }, []);

  const realPreflight = () => {
    if (window.tfBridge && window.tfBridge.run_preflight && p.path) {
      tfToast('⟳ Pre-flight en curso…');
      window.tfBridge.run_preflight(p.path).then((j) => {
        let r = {}; try { r = JSON.parse(j); } catch (e) {}
        const verdict = r.verdict || r.status || (r.ok ? 'PASS' : 'revisar');
        const fails = (r.fail || r.failures || r.errors || []).length || 0;
        tfToast('✓ Pre-flight: ' + verdict + (fails ? ' · ' + fails + ' fallos' : ''), fails ? '#ffb000' : '#9dff3c');
      }).catch(e => tfToast('Pre-flight error: ' + e, '#ff2e88'));
      return;
    }
    onBuild && onBuild();
  };

  const devices = [
    { k: 'desktop', icon: 'monitor', label: 'Desktop' },
    { k: 'tablet', icon: 'box', label: 'Tablet' },
    { k: 'mobile', icon: 'box', label: 'Mobile' },
    { k: 'code', icon: 'code', label: 'Code' },
  ];
  const frameW = { desktop: '100%', tablet: 540, mobile: 300, code: '100%' };

  return (
    <div className="fade-in" style={{ position: 'relative', zIndex: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* top bar */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 14, padding: '14px 24px',
        borderBottom: '1px solid var(--line)', background: 'var(--bg-glass)', backdropFilter: 'blur(10px)',
      }}>
        <button className="btn btn-ghost" onClick={onBack} style={{ padding: '7px 11px' }}>
          <Icon name="chevR" size={15} style={{ transform: 'rotate(180deg)' }} /> Gallery
        </button>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
          <span style={{ fontSize: 17, fontWeight: 600 }}>{p.name}</span>
          <span className="jp faint" style={{ fontSize: 13 }}>{p.jp || '制作'}</span>
          <StatusDot status={p.status || 'building'} />
        </div>
        <div style={{ flex: 1 }} />
        <span style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: 12, color: ag.color }}>
          <span>{ag.glyph}</span> {ag.label}
        </span>
        <Btn icon="sparkles" variant="ghost" onClick={() => window.tfNav && window.tfNav('new')}>Nuevo</Btn>
        <Btn icon="folderOpen" variant="ghost" onClick={() => window.tfNav && window.tfNav('gallery')}>Abrir otro</Btn>
        <Btn icon="folderOpen" variant="ghost" onClick={() => B && B.open_folder && B.open_folder(p.path)}>Folder</Btn>
        <Btn icon="code" variant="ghost" onClick={() => B && B.open_vscode && B.open_vscode(p.path)}>VSCode</Btn>
        <Btn icon="terminal" variant="ghost" onClick={() => B && B.open_external_terminal && B.open_external_terminal(p.path)}>Terminal ext.</Btn>
        <Btn icon="rocket" variant="ghost" onClick={() => window.tfNav && window.tfNav('operator')}>Operator</Btn>
        <Btn icon="check" variant="ghost" onClick={realPreflight}>Pre-flight</Btn>
        <Btn icon="box" variant="ghost" onClick={() => {
          if (window.tfBridge && window.tfBridge.build_zip && p.path) {
            tfToast('⟳ Empaquetando ZIP…');
            window.tfBridge.build_zip(p.path).then((j) => {
              let r = {}; try { r = JSON.parse(j); } catch (e) {}
              tfToast(r.zip_path || r.zip || r.path ? ('✓ ZIP: ' + (r.zip_path || r.zip || r.path)) : ('ZIP: ' + (r.error || 'hecho')), '#9dff3c');
            }).catch(e => tfToast('ZIP error: ' + e, '#ff2e88'));
          } else onBuild && onBuild();
        }}>Build ZIP</Btn>
        <Btn icon="github" variant="ghost" onClick={() => { if (B && B.github_create && p.path) { tfToast('⎇ GitHub: creando/empujando repo… mira el log'); B.github_create(p.path); } }}>GitHub</Btn>
        <Btn icon="github" variant={pushed ? '' : 'primary'} onClick={() => {
          if (window.tfBridge && window.tfBridge.git_push && p.path) {
            tfToast('⟳ git add+commit+push…'); window.tfBridge.git_push(p.path); setPushed(true);
          } else setPushed(true);
        }}>{pushed ? '✓ Pushed' : 'Push'}</Btn>
        <Btn icon="rocket" onClick={() => {
          if (window.tfBridge && window.tfBridge.deploy_demo && p.path) {
            const prov = prompt('Deploy a (netlify/vercel/cloudflare/surge):', 'surge');
            if (prov) { tfToast('🚀 Deploy a ' + prov + '… mira la terminal'); window.tfBridge.deploy_demo(p.path, prov); }
          } else onDeploy && onDeploy();
        }}>Deploy</Btn>
      </div>

      {/* MCP servers strip (real, clic = on/off) */}
      <MCPBar path={p.path} />

      {/* body: preview | terminal */}
      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1.55fr 1fr', minHeight: 0 }}>
        {/* preview */}
        <div style={{ display: 'flex', flexDirection: 'column', borderRight: '1px solid var(--line)', minHeight: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '10px 16px', borderBottom: '1px solid var(--line)' }}>
            {devices.map(d => (
              <button key={d.k} onClick={() => setTab(d.k)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer',
                  padding: '6px 11px', borderRadius: 7, fontSize: 12, fontFamily: 'var(--font-display)',
                  background: tab === d.k ? 'rgba(var(--accent-rgb),0.12)' : 'transparent',
                  border: '1px solid ' + (tab === d.k ? 'rgba(var(--accent-rgb),0.45)' : 'transparent'),
                  color: tab === d.k ? 'var(--accent)' : 'var(--tx-dim)', transition: 'all 0.15s',
                }}>
                <Icon name={d.icon} size={14} /> {d.label}
              </button>
            ))}
            <div style={{ flex: 1 }} />
            <span className="mono faint" style={{ fontSize: 10.5 }}>preview real · controles abajo</span>
          </div>
          <div style={{ flex: 1, overflow: 'hidden', background: 'radial-gradient(circle at 50% 0%, #0a1020, #04060c)', display: 'grid', placeItems: 'stretch', minHeight: 0 }}>
            {tab === 'code'
              ? <div style={{ overflow: 'auto', placeSelf: 'center' }}><CodePeek /></div>
              : <RealPreview path={p.path} accent={p.accent || 'var(--accent)'} narrow={tab === 'mobile'} />}
          </div>
        </div>

        {/* right: agent + terminal */}
        <div style={{ display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          <div style={{ padding: '10px 16px', borderBottom: '1px solid var(--line)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Icon name="terminal" size={15} style={{ color: 'var(--accent)' }} />
            <span style={{ fontSize: 12.5, fontWeight: 600 }}>Terminales</span>
            <span className="chip" style={{ marginLeft: 'auto', fontSize: 9.5 }}>xterm · node-pty</span>
            {running && <span style={{ width: 7, height: 7, borderRadius: 99, background: 'var(--codex)', boxShadow: '0 0 8px var(--codex)', animation: 'blink 1.1s infinite' }} />}
          </div>
          <TermTabs path={p.path} running={running} fresh={p.fresh} />
        </div>
      </div>
    </div>
  );
}

function LivePreview({ accent, narrow }) {
  return (
    <div style={{ fontFamily: 'var(--font-display)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <span style={{ fontWeight: 700, color: accent }}>Aurora</span>
        {!narrow && <div style={{ display: 'flex', gap: 14, fontSize: 11, color: 'var(--tx-dim)' }}><span>Features</span><span>Pricing</span><span>Docs</span></div>}
        <span style={{ fontSize: 10.5, padding: '4px 10px', borderRadius: 6, background: accent, color: '#04060c', fontWeight: 600 }}>Start free</span>
      </div>
      <div style={{ padding: narrow ? '26px 18px' : '40px 28px', textAlign: 'center' }}>
        <div style={{ fontSize: narrow ? 22 : 30, fontWeight: 700, lineHeight: 1.15, letterSpacing: '-0.01em' }}>
          Ship production-ready<br /><span style={{ color: accent }}>SaaS in days</span>, not months
        </div>
        <div style={{ fontSize: 12.5, color: 'var(--tx-dim)', marginTop: 12, maxWidth: 320, margin: '12px auto 0' }}>
          The all-in-one platform to build, launch and scale your product.
        </div>
        <div style={{ display: 'flex', gap: 10, justifyContent: 'center', marginTop: 18 }}>
          <span style={{ padding: '9px 18px', borderRadius: 8, background: accent, color: '#04060c', fontSize: 12, fontWeight: 600 }}>Start free trial</span>
          <span style={{ padding: '9px 18px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.15)', fontSize: 12 }}>Watch demo</span>
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: narrow ? '1fr 1fr' : 'repeat(3,1fr)', gap: 8, padding: '0 20px 24px' }}>
        {['AI search', 'Realtime sync', 'Edge deploy', 'Analytics', 'Auth', 'Webhooks'].slice(0, narrow ? 4 : 6).map(f => (
          <div key={f} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 8, padding: '14px 12px' }}>
            <div style={{ width: 22, height: 22, borderRadius: 6, background: accent, opacity: 0.85, marginBottom: 8 }} />
            <div style={{ fontSize: 11.5, fontWeight: 600 }}>{f}</div>
            <div style={{ fontSize: 9.5, color: 'var(--tx-faint)', marginTop: 3 }}>Fast & reliable</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function CodePeek() {
  const code = [
    ['kw', 'export default'], ['fn', ' function '], ['id', 'Hero'], ['p', '() {'],
  ];
  const src = `export default function Hero() {
  return (
    <section className="relative isolate">
      <Glow tone="neon" />
      <h1 className="text-6xl font-bold tracking-tight">
        Ship <span className="text-accent">SaaS in days</span>
      </h1>
      <p className="mt-4 text-muted">Build · launch · scale.</p>
      <div className="mt-8 flex gap-4">
        <Button primary>Start free trial</Button>
        <Button ghost>Watch demo</Button>
      </div>
    </section>
  );
}`;
  return (
    <div className="mono" style={{ width: '100%', maxWidth: 640, background: '#03050b', border: '1px solid var(--line)', borderRadius: 8, padding: 18, fontSize: 12.5, lineHeight: 1.7, color: '#cdd6f4', textAlign: 'left', whiteSpace: 'pre' }}>
      <div className="faint" style={{ marginBottom: 8, fontSize: 11 }}>components/Hero.tsx</div>
      {src.split('\n').map((l, i) => (
        <div key={i}><span className="faint" style={{ display: 'inline-block', width: 24, opacity: 0.5 }}>{i + 1}</span><span dangerouslySetInnerHTML={{ __html: hl(l) }} /></div>
      ))}
    </div>
  );
}
function hl(l) {
  return l
    .replace(/(export default|function|return|const)/g, '<span style="color:#ff2e88">$1</span>')
    .replace(/(className|primary|ghost|tone)/g, '<span style="color:#00f0ff">$1</span>')
    .replace(/(&quot;|&#39;|"[^"]*")/g, m => m)
    .replace(/(Hero|Glow|Button|section|h1|p|span|div)/g, '<span style="color:#86efac">$1</span>');
}

Object.assign(window, { ProjectWindow });
