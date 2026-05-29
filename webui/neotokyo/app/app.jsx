/* ================= NEO-TOKYO · App Shell ================= */

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "accent": ["#00f0ff", "#ff2e88"],
  "glow": 1,
  "scanlines": true,
  "rain": true,
  "mono": false,
  "density": "regular"
}/*EDITMODE-END*/;

const ACCENT_OPTS = [
  ['#00f0ff', '#ff2e88'], // cyan / magenta
  ['#ff2e88', '#b14dff'], // magenta / violet
  ['#9dff3c', '#00f0ff'], // lime / cyan
  ['#b14dff', '#00f0ff'], // violet / cyan
  ['#ffb000', '#ff2e88'], // amber / magenta
];

function hexToRgb(h) {
  const n = parseInt(h.slice(1), 16);
  return `${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}`;
}

const NAV = [
  { id: 'gallery', icon: 'grid', label: 'Gallery', jp: 'ギャラリー' },
  { id: 'new', icon: 'box', label: 'New', jp: '新規' },
  { id: 'cost', icon: 'dollar', label: 'Cost', jp: '費用' },
  { id: 'compare', icon: 'users', label: 'Compare', jp: '比較' },
  { id: 'operator', icon: 'rocket', label: 'Operator', jp: '司令' },
  { id: 'market', icon: 'globe', label: 'Market', jp: '市場' },
  { id: 'licensing', icon: 'key', label: 'License', jp: '認可' },
  { id: 'settings', icon: 'settings', label: 'Settings', jp: '設定' },
];

function NavRail({ route, onNav }) {
  return (
    <div style={{
      width: 78, flexShrink: 0, borderRight: '1px solid var(--line)',
      background: 'var(--bg-deep)', display: 'flex', flexDirection: 'column',
      alignItems: 'center', padding: '14px 0', zIndex: 10, position: 'relative',
    }}>
      {/* logo mark */}
      <div style={{ position: 'relative', marginBottom: 22 }}>
        <div className="neon-text" style={{ fontFamily: 'var(--font-mega)', fontSize: 22, lineHeight: 1 }}>鍛</div>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, flex: 1 }}>
        {NAV.map(n => {
          const active = route === n.id;
          return (
            <button key={n.id} onClick={() => onNav(n.id)} title={n.label}
              style={{
                position: 'relative', width: 58, padding: '10px 0', borderRadius: 12, cursor: 'pointer',
                display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4,
                background: active ? 'rgba(var(--accent-rgb),0.12)' : 'transparent',
                border: '1px solid ' + (active ? 'rgba(var(--accent-rgb),0.4)' : 'transparent'),
                color: active ? 'var(--accent)' : 'var(--tx-faint)', transition: 'all 0.16s',
              }}
              onMouseEnter={e => { if (!active) e.currentTarget.style.color = 'var(--tx-dim)'; }}
              onMouseLeave={e => { if (!active) e.currentTarget.style.color = 'var(--tx-faint)'; }}>
              {active && <span style={{ position: 'absolute', left: -1, top: '50%', transform: 'translateY(-50%)', width: 3, height: 22, borderRadius: 2, background: 'var(--accent)', boxShadow: '0 0 10px var(--accent)' }} />}
              <Icon name={n.icon} size={20} style={active ? { filter: 'drop-shadow(0 0 5px var(--accent))' } : {}} />
              <span style={{ fontSize: 9, fontFamily: 'var(--font-mono)', letterSpacing: '0.04em' }}>{n.label}</span>
            </button>
          );
        })}
      </div>
      <div className="kana-v" style={{ marginTop: 14, opacity: 0.5 }}>制作システム</div>
    </div>
  );
}

function TopChrome({ onPalette }) {
  const [time, setTime] = useState('');
  useEffect(() => {
    const tick = () => setTime(new Date().toLocaleTimeString('ja-JP', { hour12: false }));
    tick(); const t = setInterval(tick, 1000); return () => clearInterval(t);
  }, []);
  return (
    <div style={{
      height: 42, flexShrink: 0, display: 'flex', alignItems: 'center', gap: 14,
      padding: '0 16px 0 18px', borderBottom: '1px solid var(--line)',
      background: 'var(--bg-deep)', zIndex: 10, position: 'relative',
    }}>
      <div style={{ display: 'flex', gap: 8 }}>
        <span style={{ width: 11, height: 11, borderRadius: 99, background: '#ff2e88', boxShadow: '0 0 8px #ff2e88' }} />
        <span style={{ width: 11, height: 11, borderRadius: 99, background: '#ffb000' }} />
        <span style={{ width: 11, height: 11, borderRadius: 99, background: '#9dff3c' }} />
      </div>
      <span className="mono" style={{ fontSize: 12, color: 'var(--tx-dim)', letterSpacing: '0.02em' }}>
        ThemeForge<span style={{ color: 'var(--tx-faint)' }}> — ThemeForest builder</span>
      </span>
      <span className="jp faint" style={{ fontSize: 11 }}>ネオ東京 v2.6</span>
      <div style={{ flex: 1 }} />
      <button onClick={onPalette} className="btn btn-ghost" style={{ padding: '5px 12px', fontSize: 11.5 }}>
        <Icon name="search" size={13} /> Buscar <span className="chip" style={{ fontSize: 9, padding: '1px 5px', marginLeft: 2 }}>⌘K</span>
      </button>
      <span className="mono faint" style={{ fontSize: 11.5 }}>{time}</span>
      <span style={{ width: 7, height: 7, borderRadius: 99, background: 'var(--codex)', boxShadow: '0 0 8px var(--codex)' }} title="online" />
    </div>
  );
}

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [route, setRoute] = useState('gallery');
  const [project, setProject] = useState(null);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [booted, setBooted] = useState(false);
  const [modal, setModal] = useState(null); // 'ref' | 'deploy' | 'build'

  // apply tweaks → CSS vars
  useEffect(() => {
    const r = document.documentElement.style;
    const [a, a2] = Array.isArray(t.accent) ? t.accent : ['#00f0ff', '#ff2e88'];
    r.setProperty('--accent', a);
    r.setProperty('--accent-2', a2);
    r.setProperty('--accent-rgb', hexToRgb(a));
    r.setProperty('--accent2-rgb', hexToRgb(a2));
    r.setProperty('--glow', String(t.glow));
    r.setProperty('--scanline-op', t.scanlines ? '0.5' : '0');
    r.setProperty('--rain-op', t.rain ? '0.55' : '0');
    r.setProperty('--font-display', t.mono ? "'JetBrains Mono', monospace" : "'Chakra Petch', sans-serif");
    document.body.classList.toggle('scanlines', t.scanlines);
  }, [t]);

  // Ctrl/Cmd+K
  useEffect(() => {
    const h = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); setPaletteOpen(o => !o); }
    };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, []);

  const nav = (id) => {
    if (id && id.startsWith('cmd:')) {
      const c = id.slice(4);
      if (c === 'deploy') return setModal('deploy');
      if (c === 'preflight' || c === 'zip') return setModal('build');
      if (c === 'mcp' || c === 'pixel') return setRoute('settings');
      return;
    }
    setProject(null); setRoute(id);
  };
  const openProject = (p) => {
    if (p && p.__new) { setRoute('new'); return; }
    // Con el shell nativo, abrir un proyecto lanza la ProjectWindow REAL
    // (terminal xterm + preview + git + build, ya con tema Neo-Tokyo).
    if (window.tfBridge && p && p.path) { window.tfBridge.open_project(p.path); return; }
    setProject(p); setRoute('project');
  };
  const launch = (cfg) => { setProject({ ...cfg, status: 'building', jp: '制作', accent: 'var(--accent)' }); setRoute('project'); };

  const pad = t.density === 'compact' ? 0.85 : t.density === 'comfy' ? 1.15 : 1;

  return (
    <div className="scanlines" style={{ height: '100vh', display: 'flex', flexDirection: 'column', position: 'relative', '--density': pad }}>
      {!booted && <BootSequence onDone={() => setBooted(true)} />}
      <RainCanvas on={t.rain && booted} />

      <TopChrome onPalette={() => setPaletteOpen(true)} />
      <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>
        <NavRail route={route === 'project' ? null : route} onNav={nav} />
        <div style={{ flex: 1, position: 'relative', overflow: route === 'project' ? 'hidden' : 'auto' }}>
          <Atmosphere />
          {route === 'gallery' && <GalleryScreen onOpen={openProject} />}
          {route === 'new' && <NewProjectScreen onLaunch={launch} onAnalyze={() => setModal('ref')} />}
          {route === 'project' && <ProjectWindow project={project || PROJECTS[0]} onBack={() => nav('gallery')} onDeploy={() => setModal('deploy')} onBuild={() => setModal('build')} />}
          {route === 'cost' && <CostScreen />}
          {route === 'compare' && <CompareScreen />}
          {route === 'operator' && <OperatorScreen />}
          {route === 'market' && <MarketScreen />}
          {route === 'licensing' && <LicensingScreen />}
          {route === 'settings' && <SettingsScreen />}
        </div>
      </div>

      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} onNav={nav}
        projects={PROJECTS} onOpenProject={openProject} />

      {modal === 'ref' && <ReferenceAnalysisModal onClose={() => setModal(null)} />}
      {modal === 'deploy' && <DeployModal onClose={() => setModal(null)} />}
      {modal === 'build' && <BuildModal onClose={() => setModal(null)} />}

      {/* Tweaks */}
      <TweaksPanel title="Tweaks">
        <TweakSection label="Neón · 色彩" />
        <TweakColor label="Acento" value={t.accent} options={ACCENT_OPTS} onChange={v => setTweak('accent', v)} />
        <TweakSlider label="Glow" value={t.glow} min={0} max={1.4} step={0.1} onChange={v => setTweak('glow', v)} />
        <TweakSection label="Atmósfera · 雰囲気" />
        <TweakToggle label="Scanlines / CRT" value={t.scanlines} onChange={v => setTweak('scanlines', v)} />
        <TweakToggle label="Lluvia neón" value={t.rain} onChange={v => setTweak('rain', v)} />
        <TweakSection label="Tipo · 字体" />
        <TweakToggle label="Todo monospace" value={t.mono} onChange={v => setTweak('mono', v)} />
        <TweakRadio label="Densidad" value={t.density} options={['compact', 'regular', 'comfy']} onChange={v => setTweak('density', v)} />
      </TweaksPanel>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
