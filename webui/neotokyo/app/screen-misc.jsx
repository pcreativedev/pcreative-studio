/* ================= NEO-TOKYO · Compare · Market · Settings · Licensing ================= */

/* ---------------- COMPARE AGENTS ---------------- */
const COMPARE_OUT = {
  claude:   ['✳ analizando prompt…', 'export function Pricing() {', '  return <Tiers data={PLANS} />', '}', '✓ TTFT 0.8s · 1.2s total'],
  codex:    ['◇ tokenizing…', 'const Pricing = () => (', '  <section className="tiers">…', ')', '✓ TTFT 1.1s · 1.6s total'],
  gemini:   ['✦ planning…', 'function PricingGrid() {', '  // 3 tiers, annual toggle', '}', '✓ TTFT 0.6s · 1.4s total'],
  opencode: ['⬡ loading local model…', 'export const Pricing = ...', '  // qwen-coder local', '✓ TTFT 2.3s · 3.1s total'],
};

function AgentPane({ k, running }) {
  const a = AGENTS[k];
  const [shown, setShown] = useState(0);
  useEffect(() => {
    if (!running) { setShown(0); return; }
    setShown(0);
    let i = 0;
    const t = setInterval(() => { i++; setShown(i); if (i >= COMPARE_OUT[k].length) clearInterval(t); }, 400 + Math.random() * 300);
    return () => clearInterval(t);
  }, [running, k]);
  return (
    <div className="panel" style={{ padding: 0, overflow: 'hidden', borderColor: shown > 0 ? a.color + '44' : 'var(--line)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px', borderBottom: '1px solid var(--line)', background: a.hex + '11' }}>
        <span style={{ color: a.color, fontSize: 15 }}>{a.glyph}</span>
        <span style={{ fontSize: 12.5, fontWeight: 600 }}>{a.label}</span>
        {running && shown < COMPARE_OUT[k].length && <span style={{ marginLeft: 'auto', width: 6, height: 6, borderRadius: 99, background: a.color, boxShadow: `0 0 8px ${a.color}`, animation: 'blink 0.9s infinite' }} />}
        {shown >= COMPARE_OUT[k].length && <Icon name="check" size={14} style={{ marginLeft: 'auto', color: 'var(--codex)' }} />}
      </div>
      <div className="mono" style={{ padding: 14, fontSize: 11.5, lineHeight: 1.8, minHeight: 130, color: 'var(--tx-dim)' }}>
        {COMPARE_OUT[k].slice(0, shown).map((l, i) => (
          <div key={i} style={{ color: l.startsWith('✓') ? a.color : (i === 0 ? a.color : 'var(--tx-dim)') }}>{l}</div>
        ))}
        {running && shown < COMPARE_OUT[k].length && <span style={{ color: a.color, animation: 'blink 0.8s infinite' }}>▊</span>}
      </div>
    </div>
  );
}

function CompareScreen() {
  const [running, setRunning] = useState(false);
  const [prompt, setPrompt] = useState('Build a 3-tier pricing section with annual/monthly toggle');
  return (
    <div style={{ padding: '34px 40px 60px', position: 'relative', zIndex: 2 }}>
      <Eyebrow jp="比較">COMPARE · 代理比較</Eyebrow>
      <h1 style={{ fontFamily: 'var(--font-mega)', fontSize: 38, margin: '12px 0 6px' }}>
        AGENT <span className="neon-text-2">VERSUS</span>
      </h1>
      <div className="dim" style={{ fontSize: 13.5, marginBottom: 22 }}>Mismo prompt · 4 modelos en paralelo · lado a lado.</div>

      <div className="panel" style={{ padding: 14, display: 'flex', gap: 10, marginBottom: 20 }}>
        <input value={prompt} onChange={e => setPrompt(e.target.value)}
          style={{ flex: 1, background: 'var(--bg-void)', border: '1px solid var(--line-bright)', borderRadius: 8, padding: '10px 14px', color: 'var(--tx)', fontFamily: 'var(--font-mono)', fontSize: 12.5, outline: 'none' }} />
        <Btn variant="primary" icon="play" onClick={() => { setRunning(false); setTimeout(() => setRunning(true), 50); }}>
          {running ? 'Re-run' : 'Run en 4'}
        </Btn>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {Object.keys(AGENTS).map(k => <AgentPane key={k} k={k} running={running} />)}
      </div>
    </div>
  );
}

/* ---------------- MARKET ANALYZER ---------------- */
function MarketScreen() {
  const [niche, setNiche] = useState('');
  const [done, setDone] = useState(false);
  const [loading, setLoading] = useState(false);
  const [md, setMd] = useState('');
  const real = !!(window.tfBridge && window.tfBridge.analyze_market);
  useEffect(() => {
    if (!real || !window.tfBridge.market_result || !window.tfBridge.market_result.connect) return;
    const onResult = (j) => {
      let r = {}; try { r = JSON.parse(j); } catch (e) {}
      setLoading(false);
      if (r.error) { setMd('⚠ ' + r.error); setDone(true); }
      else { setMd(r.markdown || ''); setDone(true); }
    };
    window.tfBridge.market_result.connect(onResult);
    return () => { try { window.tfBridge.market_result.disconnect(onResult); } catch (e) {} };
  }, []);
  const run = () => {
    if (real) { setLoading(true); setDone(false); setMd(''); window.tfBridge.analyze_market(niche); return; }
    setLoading(true); setDone(false); setTimeout(() => { setLoading(false); setDone(true); }, 1400);
  };
  const rows = [
    ['Dental clinic landing', '$39', '★ 4.8', '1,240', 'alta'],
    ['Medical / health WP', '$59', '★ 4.6', '890', 'media'],
    ['Booking + calendar', '$49', '★ 4.9', '2,100', 'alta'],
    ['Multipurpose business', '$29', '★ 4.4', '8,400', 'saturada'],
  ];
  return (
    <div style={{ padding: '34px 40px 60px', position: 'relative', zIndex: 2 }}>
      <Eyebrow jp="市場分析">MARKET · 市場</Eyebrow>
      <h1 style={{ fontFamily: 'var(--font-mega)', fontSize: 38, margin: '12px 0 6px' }}>
        <span className="neon-text">MARKET</span> ANALYZER
      </h1>
      <div className="dim" style={{ fontSize: 13.5, marginBottom: 22 }}>Investiga el nicho antes de forjar · precio · competencia · demanda.</div>

      <div className="panel" style={{ padding: 14, display: 'flex', gap: 10, marginBottom: 20 }}>
        <Icon name="globe" size={18} style={{ color: 'var(--accent)', alignSelf: 'center', marginLeft: 6 }} />
        <input value={niche} onChange={e => setNiche(e.target.value)} placeholder='Nicho a investigar — ej: "dental clinic", "yoga studio"…'
          style={{ flex: 1, background: 'var(--bg-void)', border: '1px solid var(--line-bright)', borderRadius: 8, padding: '10px 14px', color: 'var(--tx)', fontFamily: 'var(--font-mono)', fontSize: 12.5, outline: 'none' }} />
        <Btn variant="primary" icon="search" onClick={run}>{loading ? 'Analizando…' : 'Analizar'}</Btn>
      </div>

      {/* Tipos de análisis (como en la app normal) + crear proyecto. */}
      {real && (
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 18 }}>
          {[['@general', 'Mercado 2026'], ['@stacks', 'Stacks'], ['@prediction', 'Predicción 2027']].map(([k, l]) => (
            <button key={k} className="chip" style={{ cursor: 'pointer' }} onClick={() => { setLoading(true); setDone(false); setMd(''); window.tfBridge.analyze_market(k); }}>{l}</button>
          ))}
          {done && md && <button className="chip" style={{ cursor: 'pointer', marginLeft: 'auto', color: 'var(--codex)', borderColor: 'var(--codex)' }} onClick={() => window.tfNav && window.tfNav('new')}>🚀 Crear proyecto desde este análisis</button>}
        </div>
      )}

      {loading && <div className="mono" style={{ color: 'var(--accent)', fontSize: 13, padding: 30, textAlign: 'center' }}><span style={{ animation: 'blink 0.8s infinite' }}>◢◣◤◥</span> analizando mercado con IA (OpenRouter) — puede tardar…</div>}

      {/* Análisis REAL: markdown del motor de ThemeForge (OpenRouter). */}
      {done && real && (
        <div className="fade-in panel" style={{ padding: 24 }}>
          <div className="eyebrow" style={{ marginBottom: 12 }}>ANÁLISIS · {niche || 'general'} · 判定</div>
          <pre className="mono" style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: 12.5, lineHeight: 1.7, color: 'var(--tx)', margin: 0 }}>{md}</pre>
        </div>
      )}

      {done && !real && (
        <div className="fade-in" style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: 20 }}>
          <div className="panel" style={{ padding: 0, overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12.5 }}>
              <thead><tr style={{ background: 'rgba(255,255,255,0.03)' }}>
                {['Template', 'Precio', 'Rating', 'Ventas', 'Competencia'].map((h, i) => <th key={h} style={{ textAlign: i === 0 ? 'left' : 'right', padding: '11px 16px', fontFamily: 'var(--font-mono)', fontSize: 10.5, letterSpacing: '0.08em', color: 'var(--tx-faint)', textTransform: 'uppercase', fontWeight: 500 }}>{h}</th>)}
              </tr></thead>
              <tbody>{rows.map((r, i) => (
                <tr key={i} style={{ borderTop: '1px solid var(--line)' }}>
                  <td style={{ padding: '12px 16px' }}>{r[0]}</td>
                  <td className="mono" style={{ textAlign: 'right', padding: '12px 16px', color: 'var(--codex)' }}>{r[1]}</td>
                  <td className="mono" style={{ textAlign: 'right', padding: '12px 16px', color: 'var(--gemini)' }}>{r[2]}</td>
                  <td className="mono dim" style={{ textAlign: 'right', padding: '12px 16px' }}>{r[3]}</td>
                  <td style={{ textAlign: 'right', padding: '12px 16px' }}>
                    <Chip color={r[4] === 'alta' ? 'var(--codex)' : r[4] === 'saturada' ? 'var(--magenta)' : 'var(--gemini)'}>{r[4]}</Chip>
                  </td>
                </tr>
              ))}</tbody>
            </table>
          </div>
          <div className="panel card-corner" style={{ padding: 20 }}>
            <div className="eyebrow" style={{ marginBottom: 14 }}>VEREDICTO · 判定</div>
            <div style={{ fontFamily: 'var(--font-mega)', fontSize: 30, color: 'var(--codex)', textShadow: '0 0 16px rgba(157,255,60,0.5)' }}>FORJAR</div>
            <div className="dim" style={{ fontSize: 12.5, marginTop: 10, lineHeight: 1.6 }}>
              Demanda alta, competencia media. Sweet-spot de precio <span className="mono" style={{ color: 'var(--accent)' }}>$45–55</span>. Diferénciate con booking integrado.
            </div>
            <div style={{ marginTop: 16, paddingTop: 14, borderTop: '1px solid var(--line)', display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[['Demanda', 82], ['Margen', 68], ['Saturación', 41]].map(([l, v]) => (
                <div key={l}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 3 }}><span className="dim">{l}</span><span className="mono" style={{ color: 'var(--accent)' }}>{v}%</span></div>
                  <div style={{ height: 5, background: 'rgba(255,255,255,0.06)', borderRadius: 99 }}><div style={{ width: v + '%', height: '100%', background: 'linear-gradient(90deg,var(--accent),var(--accent-2))', borderRadius: 99, boxShadow: '0 0 8px rgba(var(--accent-rgb),0.5)' }} /></div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      {!done && !loading && <div className="faint mono" style={{ textAlign: 'center', padding: 50 }}>// introduce un nicho para empezar — 待機中</div>}
    </div>
  );
}

/* ---------------- SETTINGS / THEME EDITOR ---------------- */
const _MOCK_APP_THEMES = [
  { k: 'neotokyo', label: 'Neo-Tokyo', jp: 'ネオ東京', bg: '#04060c', acc: '#00f0ff', acc2: '#ff2e88' },
  { k: 'tokyonight', label: 'Tokyo Night', jp: '東京夜', bg: '#1a1b26', acc: '#7aa2f7', acc2: '#bb9af7' },
  { k: 'dracula', label: 'Dracula', jp: '吸血鬼', bg: '#282a36', acc: '#bd93f9', acc2: '#ff79c6' },
  { k: 'nord', label: 'Nord', jp: '北', bg: '#2e3440', acc: '#88c0d0', acc2: '#81a1c1' },
  { k: 'linear', label: 'Linear', jp: '線形', bg: '#0e0e10', acc: '#5e6ad2', acc2: '#8a8f98' },
  { k: 'brutalism', label: 'Brutalism', jp: '粗野', bg: '#0a0a0a', acc: '#ffff00', acc2: '#ff0000' },
];

// Temas REALES de ThemeForge (inyectados por el shell) con fallback al mock.
const _TFD = (typeof window !== 'undefined' && window.__TF_DATA__) || {};
const APP_THEMES = (_TFD.themes && _TFD.themes.length) ? _TFD.themes : _MOCK_APP_THEMES;

function SettingsScreen() {
  const [theme, setTheme] = useState(_TFD.current_theme || 'neotokyo');
  const [sub, setSub] = useState('themes');
  const subs = [['themes', 'Temas', '🎨'], ['creds', 'Credenciales', '🔑'], ['mcp', 'MCP servers', '📡'], ['office', 'Pixel Office', '🎮']];
  const cur = APP_THEMES.find(t => t.k === theme);

  const SubPill = ({ k, label, ic }) => (
    <button onClick={() => setSub(k)} style={{ cursor: 'pointer', padding: '9px 15px', borderRadius: 10, fontSize: 13, fontFamily: 'var(--font-display)', display: 'flex', gap: 7, alignItems: 'center',
      background: sub === k ? 'rgba(var(--accent-rgb),0.12)' : 'transparent', border: '1px solid ' + (sub === k ? 'rgba(var(--accent-rgb),0.45)' : 'var(--line)'),
      color: sub === k ? 'var(--accent)' : 'var(--tx-dim)', transition: 'all 0.15s' }}>{ic} {label}</button>
  );

  return (
    <div style={{ padding: '34px 40px 60px', position: 'relative', zIndex: 2 }}>
      <Eyebrow jp="設定">SETTINGS · 設定</Eyebrow>
      <h1 style={{ fontFamily: 'var(--font-mega)', fontSize: 38, margin: '12px 0 18px' }}>
        THEME <span className="neon-text">EDITOR</span>
      </h1>
      <div style={{ display: 'flex', gap: 8, marginBottom: 24, flexWrap: 'wrap' }}>
        {subs.map(([k, l, ic]) => <SubPill key={k} k={k} label={l} ic={ic} />)}
      </div>

      {/* ---- THEMES ---- */}
      {sub === 'themes' && (
      <div className="fade-in" style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: 22 }}>
        <div className="panel" style={{ padding: 22 }}>
          <div className="eyebrow" style={{ marginBottom: 16 }}>TEMAS BUILT-IN · テーマ <span className="faint">· 8 + editor + Figma DTCG</span></div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 12 }}>
            {APP_THEMES.map(t => (
              <button key={t.k} onClick={() => { setTheme(t.k); if (window.tfBridge) window.tfBridge.set_theme(t.k); }}
                className={theme === t.k ? 'neon-edge' : ''}
                style={{ cursor: 'pointer', padding: 0, borderRadius: 10, overflow: 'hidden', border: '1px solid ' + (theme === t.k ? 'rgba(var(--accent-rgb),0.5)' : 'var(--line)'), background: 'transparent' }}>
                <div style={{ height: 64, background: t.bg, position: 'relative', padding: 10 }}>
                  <div style={{ display: 'flex', gap: 5 }}>
                    <span style={{ width: 14, height: 14, borderRadius: 4, background: t.acc, boxShadow: `0 0 8px ${t.acc}` }} />
                    <span style={{ width: 14, height: 14, borderRadius: 4, background: t.acc2 }} />
                  </div>
                  <div style={{ marginTop: 8, height: 4, width: '70%', borderRadius: 2, background: t.acc, opacity: 0.5 }} />
                  <div style={{ marginTop: 4, height: 4, width: '45%', borderRadius: 2, background: '#fff', opacity: 0.15 }} />
                </div>
                <div style={{ padding: '8px 10px', textAlign: 'left', background: 'var(--bg-panel)' }}>
                  <div style={{ fontSize: 12.5, fontWeight: 600, color: theme === t.k ? 'var(--accent)' : 'var(--tx)' }}>{t.label}</div>
                  <div className="jp faint" style={{ fontSize: 10 }}>{t.jp}</div>
                </div>
              </button>
            ))}
          </div>
          <div style={{ marginTop: 18, paddingTop: 16, borderTop: '1px solid var(--line)', display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <Btn icon="palette">Editar colores</Btn>
            <Btn icon="download" variant="ghost">Import Figma DTCG</Btn>
            <Btn icon="save" variant="ghost">Exportar tema</Btn>
          </div>
        </div>
        <div className="panel card-corner" style={{ padding: 22 }}>
          <div className="eyebrow" style={{ marginBottom: 16 }}>TOKENS · live preview</div>
          {[['Background', cur.bg], ['Accent', cur.acc], ['Accent 2', cur.acc2], ['Text', '#e9f0ff']].map(([l, c]) => (
            <div key={l} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '9px 0', borderBottom: '1px solid var(--line)' }}>
              <span style={{ width: 30, height: 30, borderRadius: 7, background: c, border: '1px solid rgba(255,255,255,0.15)', boxShadow: `0 0 10px ${c}66` }} />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 12.5 }}>{l}</div>
                <div className="mono faint" style={{ fontSize: 10.5 }}>{c}</div>
              </div>
              <Icon name="penTool" size={14} style={{ color: 'var(--tx-faint)' }} />
            </div>
          ))}
          <div style={{ marginTop: 16 }}>
            <div className="eyebrow" style={{ marginBottom: 8 }}>PREVIEW</div>
            <div style={{ display: 'flex', gap: 8 }}>
              <span className="btn btn-primary" style={{ pointerEvents: 'none' }}>Primary</span>
              <span className="btn" style={{ pointerEvents: 'none' }}>Default</span>
            </div>
          </div>
        </div>
      </div>
      )}

      {/* ---- CREDENTIALS ---- */}
      {sub === 'creds' && (
        <div className="fade-in panel" style={{ padding: '6px 22px 16px', maxWidth: 760 }}>
          {(_TFD.creds || [
            { id: 'anthropic', label: 'Anthropic API key', color: 'var(--claude)', configured: false },
            { id: 'openrouter', label: 'OpenRouter key', color: 'var(--opencode)', configured: false },
          ]).map((cr) => (
            <div key={cr.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '13px 0', borderBottom: '1px solid var(--line)' }}>
              <span style={{ color: cr.color, fontSize: 15, width: 18 }}>◈</span>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13.5 }}>{cr.label}</div>
                <div className="mono faint" style={{ fontSize: 11, marginTop: 2 }}>{cr.configured ? ('✓ configurada' + (cr.via === 'oauth' ? ' · OAuth/CLI login' : cr.via === 'gh-cli' ? ' · gh CLI' : ' · API key')) : 'sin configurar'}</div>
              </div>
              <span style={{ width: 7, height: 7, borderRadius: 99, background: cr.configured ? 'var(--codex)' : 'var(--tx-faint)', boxShadow: cr.configured ? '0 0 8px var(--codex)' : 'none' }} />
              <Btn variant="ghost" icon="penTool" style={{ padding: '6px 10px' }} onClick={() => {
                if (!window.tfBridge || !window.tfBridge.set_credential) return;
                const v = prompt('Pega la ' + cr.label + ' (vacío para borrar):');
                if (v === null) return;
                window.tfBridge.set_credential(cr.id, v).then(() => { cr.configured = !!v.trim(); location.reload(); });
              }}>Editar</Btn>
            </div>
          ))}
          <div className="faint" style={{ fontSize: 11.5, marginTop: 14 }}>Las claves se guardan en <span className="mono">~/.config/themeforge/keys.json</span> (chmod 0600) · nunca en el proyecto.</div>
        </div>
      )}

      {/* ---- MCP SERVERS ---- */}
      {sub === 'mcp' && (
        <div className="fade-in">
          <div className="dim" style={{ fontSize: 13, marginBottom: 16 }}>Catálogo curado · auto-config en <span className="mono" style={{ color: 'var(--accent)' }}>.mcp.json</span> · el cliente IA los descarga vía npx/uvx. Todos MIT/Apache — nunca bundleados.</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px,1fr))', gap: 12 }}>
            {MCP_SERVERS.map(m => (
              <div key={m.id} className="panel" style={{ padding: 16, borderColor: m.always ? 'rgba(var(--accent-rgb),0.28)' : 'var(--line)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Icon name="layers" size={15} style={{ color: m.always ? 'var(--accent)' : 'var(--tx-dim)' }} />
                  <span className="mono" style={{ fontSize: 13, fontWeight: 600, flex: 1 }}>{m.label}</span>
                  {m.always ? <Chip color="var(--accent)" style={{ fontSize: 9 }}>always</Chip> : <Chip style={{ fontSize: 9 }}>{m.cat}</Chip>}
                </div>
                <div className="dim" style={{ fontSize: 11.5, marginTop: 9, lineHeight: 1.5, minHeight: 34 }}>{m.desc}</div>
                <div className="faint mono" style={{ fontSize: 10, marginTop: 8 }}>{m.lic}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ---- PIXEL OFFICE ---- */}
      {sub === 'office' && (
        <div className="fade-in panel card-corner" style={{ padding: 28, maxWidth: 720, textAlign: 'center' }}>
          <div style={{ fontSize: 40 }}>🎮</div>
          <div style={{ fontFamily: 'var(--font-mega)', fontSize: 22, margin: '12px 0 4px' }}>PIXEL OFFICE</div>
          <div className="jp faint" style={{ fontSize: 12, marginBottom: 14 }}>ピクセルオフィス · 可視化</div>
          <div className="dim" style={{ fontSize: 13, lineHeight: 1.7, maxWidth: 480, margin: '0 auto 18px' }}>
            Visualizador pixel-art que muestra tus sesiones de Claude Code (y OpenClaw) como avatares en una oficina virtual. Lee directo de <span className="mono" style={{ color: 'var(--accent)' }}>~/.claude/projects/*.jsonl</span>.
          </div>
          {/* mini pixel scene */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(8,1fr)', gap: 3, maxWidth: 260, margin: '0 auto 20px', background: '#0a1020', padding: 10, borderRadius: 8, border: '1px solid var(--line)' }}>
            {Array.from({ length: 32 }, (_, i) => {
              const isAgent = [10, 13, 19, 21].includes(i);
              const cols = ['#62b4ff', '#86efac', '#fbbf24', '#c084fc'];
              return <div key={i} style={{ aspectRatio: '1', borderRadius: 2, background: isAgent ? cols[i % 4] : 'rgba(255,255,255,0.04)', boxShadow: isAgent ? `0 0 6px ${cols[i % 4]}` : 'none' }} />;
            })}
          </div>
          <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
            <Btn variant="primary" icon="play" onClick={() => window.tfBridge && window.tfBridge.pixel_office_launch && window.tfBridge.pixel_office_launch().then(j => { let r={}; try{r=JSON.parse(j)}catch(e){} alert(r.ok ? (r.already ? 'Pixel Office ya está activo.' : '🎮 Pixel Office lanzado.') : ('Error: ' + (r.error||''))); })}>Lanzar dashboard</Btn>
            <Btn variant="ghost" icon="download" onClick={() => window.tfBridge && window.tfBridge.pixel_office_launch && window.tfBridge.pixel_office_launch()}>Reinstalar</Btn>
          </div>
        </div>
      )}
    </div>
  );
}

/* ---------------- LICENSING ---------------- */
function LicensingScreen() {
  const real = !!(window.tfBridge && window.tfBridge.licensing_status);
  const [st, setSt] = useState(null);
  const [np, setNp] = useState(''); const [ne, setNe] = useState(''); const [nt, setNt] = useState('regular');
  const refresh = () => { if (real) window.tfBridge.licensing_status().then(j => { try { setSt(JSON.parse(j)); } catch (e) {} }); };
  useEffect(() => { refresh(); }, []);
  const create = () => {
    if (!real || !np.trim()) return;
    window.tfBridge.licensing_create(np, ne, nt).then(j => {
      let r = {}; try { r = JSON.parse(j); } catch (e) {}
      alert(r.ok ? ('✓ Licencia creada: ' + (r.key || '')) : ('Error: ' + (r.error || r.code)));
      refresh();
    });
  };
  // Vista REAL del sistema de licencias anti-nulled de ThemeForge.
  if (real) {
    return (
      <div style={{ padding: '34px 40px 60px', position: 'relative', zIndex: 2, maxWidth: 1040 }}>
        <Eyebrow jp="認可">LICENSING · 認可</Eyebrow>
        <h1 style={{ fontFamily: 'var(--font-mega)', fontSize: 38, margin: '12px 0 6px' }}>LICENSE <span className="neon-text-2">FORGE</span></h1>
        <div className="dim" style={{ fontSize: 13.5, marginBottom: 18 }}>Sistema anti-nulled: activación → JWT RS256 → verificación offline → binding de dominio → watermark. Cableado en cada tema generado.</div>
        <div className="panel" style={{ padding: 16, marginBottom: 18, display: 'flex', alignItems: 'center', gap: 14 }}>
          <span style={{ width: 9, height: 9, borderRadius: 99, background: st ? (st.configured ? (st.reachable ? 'var(--codex)' : 'var(--gemini)') : 'var(--tx-faint)') : 'var(--tx-faint)', boxShadow: st && st.reachable ? '0 0 8px var(--codex)' : 'none' }} />
          <span className="mono" style={{ fontSize: 12.5 }}>
            {!st ? 'consultando…' : !st.configured ? 'Sin backend configurado — pon tu endpoint en ~/.config/themeforge/licensing.json (los usuarios de GitHub usan el suyo).'
              : st.reachable ? ('Backend operativo · ' + (st.licenses ? st.licenses.length : 0) + ' licencias · ' + (st.products ? st.products.length : 0) + ' productos') : 'Configurado pero el backend no responde.'}
          </span>
          <div style={{ flex: 1 }} />
          <Btn icon="refresh" variant="ghost" onClick={refresh}>Refrescar</Btn>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: 20 }}>
          <div className="panel" style={{ padding: 0, overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead><tr style={{ background: 'rgba(255,255,255,0.03)' }}>
                {['Key', 'Producto', 'Tipo', 'Estado', 'Email'].map((h, i) => <th key={h} style={{ textAlign: i === 0 ? 'left' : 'left', padding: '10px 14px', fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '0.08em', color: 'var(--tx-faint)', textTransform: 'uppercase' }}>{h}</th>)}
              </tr></thead>
              <tbody>
                {(st && st.licenses && st.licenses.length) ? st.licenses.map((l, i) => (
                  <tr key={i} style={{ borderTop: '1px solid var(--line)' }}>
                    <td className="mono" style={{ padding: '9px 14px', color: 'var(--accent)' }}>{l.key}</td>
                    <td style={{ padding: '9px 14px' }}>{l.product}</td>
                    <td className="mono dim" style={{ padding: '9px 14px' }}>{l.type}</td>
                    <td style={{ padding: '9px 14px' }}><Chip color={l.status === 'active' ? 'var(--codex)' : 'var(--gemini)'}>{l.status}</Chip></td>
                    <td className="mono faint" style={{ padding: '9px 14px' }}>{l.email}</td>
                  </tr>
                )) : <tr><td colSpan={5} className="faint mono" style={{ padding: 24, textAlign: 'center' }}>// sin licencias</td></tr>}
              </tbody>
            </table>
          </div>
          <div className="panel card-corner" style={{ padding: 22 }}>
            <div className="eyebrow" style={{ marginBottom: 14 }}>CREAR LICENCIA · 発行</div>
            {[['Producto (slug)', np, setNp], ['Email comprador', ne, setNe]].map(([l, v, set]) => (
              <div key={l} style={{ marginBottom: 12 }}>
                <div className="eyebrow" style={{ fontSize: 9.5, marginBottom: 5 }}>{l}</div>
                <input value={v} onChange={e => set(e.target.value)} style={{ width: '100%', background: 'var(--bg-void)', border: '1px solid var(--line-bright)', borderRadius: 7, padding: '9px 12px', color: 'var(--tx)', fontFamily: 'var(--font-mono)', fontSize: 12, outline: 'none' }} />
              </div>
            ))}
            <div style={{ marginBottom: 12 }}>
              <div className="eyebrow" style={{ fontSize: 9.5, marginBottom: 5 }}>Tipo</div>
              <select value={nt} onChange={e => setNt(e.target.value)} style={{ width: '100%', background: 'var(--bg-void)', border: '1px solid var(--line-bright)', borderRadius: 7, padding: '9px 12px', color: 'var(--tx)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
                <option value="regular">regular</option><option value="extended">extended</option>
              </select>
            </div>
            <Btn variant="primary" icon="key" onClick={create}>Crear licencia</Btn>
          </div>
        </div>
      </div>
    );
  }
  const [provider, setProvider] = useState('lemon');
  const provs = [
    { k: 'lemon', label: 'Lemon Squeezy', jp: '檸檬', color: '#ffc233' },
    { k: 'polar', label: 'Polar', jp: '極', color: '#00e5ff' },
    { k: 'paddle', label: 'Paddle', jp: '櫂', color: '#ff70a6' },
    { k: 'custom', label: 'Custom endpoint', jp: '独自', color: '#9dff3c' },
  ];
  return (
    <div style={{ padding: '34px 40px 60px', position: 'relative', zIndex: 2, maxWidth: 980 }}>
      <Eyebrow jp="認可">LICENSING · 認可</Eyebrow>
      <h1 style={{ fontFamily: 'var(--font-mega)', fontSize: 38, margin: '12px 0 6px' }}>
        LICENSE <span className="neon-text-2">FORGE</span>
      </h1>
      <div className="dim" style={{ fontSize: 13.5, marginBottom: 22 }}>Cablea tu sistema de licencias en cada tema generado · validación de claves.</div>

      <div className="panel" style={{ padding: 22, marginBottom: 20 }}>
        <div className="eyebrow" style={{ marginBottom: 14 }}>PROVEEDOR · 提供者</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 12 }}>
          {provs.map(pr => (
            <button key={pr.k} onClick={() => setProvider(pr.k)}
              style={{ cursor: 'pointer', padding: '16px 14px', borderRadius: 10, textAlign: 'left', background: provider === pr.k ? 'rgba(255,255,255,0.04)' : 'transparent', border: '1px solid ' + (provider === pr.k ? pr.color + '88' : 'var(--line)'), boxShadow: provider === pr.k ? `0 0 18px ${pr.color}33` : 'none', transition: 'all 0.15s' }}>
              <Icon name="key" size={18} style={{ color: pr.color }} />
              <div style={{ fontSize: 13.5, fontWeight: 600, marginTop: 10 }}>{pr.label}</div>
              <div className="jp faint" style={{ fontSize: 11 }}>{pr.jp}</div>
            </button>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        <div className="panel" style={{ padding: 22 }}>
          <div className="eyebrow" style={{ marginBottom: 14 }}>CONFIG · 設定</div>
          {[['Store ID', 'store_8f2a9c'], ['Product ID', 'prod_neotokyo_01'], ['API key', '••••••••••••3f7a'], ['Webhook secret', '••••••••••••']].map(([l, v]) => (
            <div key={l} style={{ marginBottom: 12 }}>
              <div className="eyebrow" style={{ fontSize: 9.5, marginBottom: 5 }}>{l}</div>
              <div className="mono" style={{ background: 'var(--bg-void)', border: '1px solid var(--line-bright)', borderRadius: 7, padding: '9px 12px', fontSize: 12, color: 'var(--tx-dim)' }}>{v}</div>
            </div>
          ))}
          <Btn variant="primary" icon="check" style={{ marginTop: 6 }}>Cablear en proyecto</Btn>
        </div>
        <div className="panel card-corner" style={{ padding: 22 }}>
          <div className="eyebrow" style={{ marginBottom: 14 }}>VALIDADOR · license.ts</div>
          <div className="mono" style={{ background: 'var(--bg-void)', border: '1px solid var(--line)', borderRadius: 8, padding: 16, fontSize: 11.5, lineHeight: 1.8, color: '#cdd6f4', whiteSpace: 'pre-wrap' }}>
            <span style={{ color: 'var(--magenta)' }}>export async function</span> <span style={{ color: 'var(--codex)' }}>validate</span>(key) {'{'}{'\n'}
            {'  '}<span style={{ color: 'var(--magenta)' }}>const</span> r = <span style={{ color: 'var(--magenta)' }}>await</span> fetch(<span style={{ color: 'var(--gemini)' }}>API</span>, {'{'}{'\n'}
            {'    '}body: {'{'} key, instance {'}'}{'\n'}
            {'  }'});{'\n'}
            {'  '}<span style={{ color: 'var(--magenta)' }}>return</span> r.valid === <span style={{ color: 'var(--cyan)' }}>true</span>;{'\n'}
            {'}'}
          </div>
          <div style={{ marginTop: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Icon name="check" size={15} style={{ color: 'var(--codex)' }} />
            <span style={{ fontSize: 12, color: 'var(--codex)' }}>Validación activa · 256-bit signed</span>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { CompareScreen, MarketScreen, SettingsScreen, LicensingScreen });
