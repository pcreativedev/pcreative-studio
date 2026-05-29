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

// Preview REAL: arranca el dev server del proyecto (preview.py) y lo embebe.
function RealPreview({ path, accent, narrow }) {
  const [url, setUrl] = useState(null);
  const [err, setErr] = useState(null);
  useEffect(() => {
    if (!window.tfBridge || !window.tfBridge.start_preview || !path) return;
    const onReady = (j) => {
      let r = {}; try { r = JSON.parse(j); } catch (e) {}
      if (r.path === path) { if (r.url) setUrl(r.url); else setErr(r.error || 'error'); }
    };
    if (window.tfBridge.preview_ready && window.tfBridge.preview_ready.connect)
      window.tfBridge.preview_ready.connect(onReady);
    window.tfBridge.start_preview(path);
    return () => {
      if (window.tfBridge.preview_ready && window.tfBridge.preview_ready.disconnect)
        try { window.tfBridge.preview_ready.disconnect(onReady); } catch (e) {}
    };
  }, [path]);
  if (!window.tfBridge || !path) return <LivePreview accent={accent} narrow={narrow} />;
  if (err) return <div className="mono faint" style={{ padding: 24 }}>// preview: {err}</div>;
  if (!url) return <div className="mono faint" style={{ padding: 24 }}>// arrancando dev server real…</div>;
  return <iframe src={url} style={{ width: '100%', height: '72vh', border: 'none', background: '#fff', borderRadius: 8 }} />;
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

function ProjectWindow({ project, onBack, onDeploy, onBuild }) {
  const p = project;
  const [tab, setTab] = useState('desktop');
  const [running, setRunning] = useState(false);
  const [pushed, setPushed] = useState(false);
  const [reply, setReply] = useState('');
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
        <Btn icon="folderOpen" variant="ghost" onClick={() => window.tfBridge && window.tfBridge.open_folder && window.tfBridge.open_folder(p.path)}>Folder</Btn>
        <Btn icon="code" variant="ghost" onClick={() => window.tfBridge && window.tfBridge.open_vscode && window.tfBridge.open_vscode(p.path)}>VSCode</Btn>
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
        <Btn icon="github" variant={pushed ? '' : 'primary'} onClick={() => setPushed(true)}>
          {pushed ? '✓ Pushed' : 'Push to GitHub'}
        </Btn>
        <Btn icon="rocket" onClick={onDeploy}>Deploy</Btn>
      </div>

      {/* MCP servers strip */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 24px', borderBottom: '1px solid var(--line)', background: 'rgba(0,0,0,0.2)', overflowX: 'auto' }}>
        <span className="eyebrow" style={{ fontSize: 9, flexShrink: 0 }}>MCP ·</span>
        {MCP_SERVERS.slice(0, 8).map(m => (
          <span key={m.id} className="chip" style={{ fontSize: 9, padding: '2px 7px', flexShrink: 0, color: m.always ? 'var(--accent)' : 'var(--tx-dim)', borderColor: m.always ? 'rgba(var(--accent-rgb),0.4)' : 'var(--line)' }}>
            {m.always && '●'} {m.label}
          </span>
        ))}
        <span className="mono faint" style={{ fontSize: 10, flexShrink: 0 }}>+4 · .mcp.json</span>
      </div>

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
            <span className="mono faint" style={{ fontSize: 10.5 }}>localhost:5173</span>
            <button className="btn btn-ghost" style={{ padding: '5px 8px' }}><Icon name="refresh" size={13} /></button>
            <button className="btn btn-ghost" style={{ padding: '5px 8px' }}><Icon name="external" size={13} /></button>
          </div>
          <div style={{ flex: 1, overflow: 'auto', background: 'radial-gradient(circle at 50% 0%, #0a1020, #04060c)', display: 'grid', placeItems: 'center', padding: 20, minHeight: 0 }}>
            {tab === 'code'
              ? <CodePeek />
              : <div className="neon-edge" style={{ width: frameW[tab], maxWidth: '100%', background: '#070b16', borderRadius: 8, overflow: 'hidden', transition: 'width 0.3s' }}>
                  <RealPreview path={p.path} accent={p.accent || 'var(--accent)'} narrow={tab === 'mobile'} />
                </div>}
          </div>
        </div>

        {/* right: agent + terminal */}
        <div style={{ display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          <div style={{ padding: '10px 16px', borderBottom: '1px solid var(--line)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Icon name="terminal" size={15} style={{ color: 'var(--accent)' }} />
            <span style={{ fontSize: 12.5, fontWeight: 600 }}>Agent Terminal</span>
            <span className="chip" style={{ marginLeft: 'auto', fontSize: 9.5 }}>xterm · node-pty</span>
            {running && <span style={{ width: 7, height: 7, borderRadius: 99, background: 'var(--codex)', boxShadow: '0 0 8px var(--codex)', animation: 'blink 1.1s infinite' }} />}
          </div>
          <RealTerminal path={p.path} running={running} />
          {/* reply box */}
          <div style={{ borderTop: '1px solid var(--line)', padding: 12, display: 'flex', gap: 8 }}>
            <input value={reply} onChange={e => setReply(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && reply.trim()) { setReply(''); setRunning(false); setTimeout(() => setRunning(true), 60); } }}
              placeholder="Responder al agente…  (⏎ envía)"
              style={{ flex: 1, background: 'var(--bg-void)', border: '1px solid var(--line-bright)', borderRadius: 8, padding: '9px 12px', color: 'var(--tx)', fontFamily: 'var(--font-mono)', fontSize: 12, outline: 'none' }} />
            <Btn variant="primary" icon="play" onClick={() => { setRunning(false); setTimeout(() => setRunning(true), 60); }}>Run</Btn>
          </div>
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
