/* ================= NEO-TOKYO · New Project (sub-tabs Vibe/Setup/Mode/Extras/Preview) ================= */

function StackTile({ s, active, onClick }) {
  return (
    <button onClick={onClick} className={active ? 'neon-edge' : ''}
      style={{
        position: 'relative', textAlign: 'left', cursor: 'pointer',
        background: active ? 'rgba(var(--accent-rgb),0.10)' : 'rgba(255,255,255,0.02)',
        border: '1px solid ' + (active ? 'rgba(var(--accent-rgb),0.5)' : 'var(--line)'),
        borderRadius: 'var(--radius-sm)', padding: '13px 14px', color: 'var(--tx)',
        transition: 'all 0.15s', overflow: 'hidden',
      }}>
      <div className="jp" style={{ position: 'absolute', top: 6, right: 8, fontSize: 18, color: active ? 'var(--accent)' : 'var(--tx-faint)', opacity: 0.55 }}>{s.jp}</div>
      <div style={{ fontSize: 14.5, fontWeight: 600 }}>{s.label}</div>
      <div style={{ display: 'flex', gap: 6, marginTop: 8 }}>
        <span className="chip" style={{ fontSize: 9.5, padding: '2px 7px' }}>{s.cat}</span>
        <span className="chip" style={{ fontSize: 9.5, padding: '2px 7px' }}>{s.n}</span>
      </div>
    </button>
  );
}

const VIBE_PRESETS = [
  { vibe: 'Landing premium para clínica dental en Madrid, paleta cálida, sección de reservas', stack: 'wp', type: 'Clínica / Booking', agent: 'claude' },
  { vibe: 'SaaS B2B con dashboard analítico, dark mode, pricing de 3 tiers', stack: 'next', type: 'SaaS Landing', agent: 'claude' },
  { vibe: 'Portfolio de estudio creativo nórdico, editorial, mucho whitespace y GSAP', stack: 'astro', type: 'Creative Agency', agent: 'codex' },
];

const MODES = [
  { k: 'scratch', label: 'Desde cero', jp: '新規', icon: 'sparkles', desc: 'Scaffold oficial del stack + agente IA desde cero.' },
  { k: 'recreate', label: 'Recreate ref', jp: '再現', icon: 'copy', desc: 'Carpeta / .zip / URL / Figma — la IA estudia y reimplementa.' },
  { k: 'adopt', label: 'Adopt local', jp: '採用', icon: 'folderOpen', desc: 'Export de claude.ai/design, v0.dev o Figma Make.' },
  { k: 'repo', label: 'Existing repo', jp: '既存', icon: 'github', desc: 'Continúa un repo de GitHub existente.' },
];

const REF_KINDS = [
  { k: 'folder', label: 'Carpeta local' },
  { k: 'zip', label: 'Archivo .zip' },
  { k: 'url', label: 'URL de demo' },
  { k: 'figma', label: 'Figma (frame)' },
];

function Toggle({ on, onClick }) {
  return (
    <button onClick={onClick} style={{ cursor: 'pointer', width: 38, height: 22, borderRadius: 99, padding: 2, border: 'none',
      background: on ? 'var(--accent)' : 'rgba(255,255,255,0.12)', boxShadow: on ? '0 0 12px rgba(var(--accent-rgb),0.5)' : 'none', transition: 'all 0.18s' }}>
      <span style={{ display: 'block', width: 18, height: 18, borderRadius: 99, background: on ? '#04060c' : '#9fb0d8', transform: on ? 'translateX(16px)' : 'none', transition: 'transform 0.18s' }} />
    </button>
  );
}

function CheckRow({ label, sub, on, onToggle, jp }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 0', borderBottom: '1px solid var(--line)' }}>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 13.5, display: 'flex', alignItems: 'center', gap: 8 }}>{label} {jp && <span className="jp faint" style={{ fontSize: 11 }}>{jp}</span>}</div>
        {sub && <div className="faint" style={{ fontSize: 11.5, marginTop: 3 }}>{sub}</div>}
      </div>
      <Toggle on={on} onClick={onToggle} />
    </div>
  );
}

function NewProjectScreen({ onLaunch, onAnalyze }) {
  const [sub, setSub] = useState('vibe');
  const [vibe, setVibe] = useState('');
  const [pname, setPname] = useState('');  // nombre del proyecto
  const [stack, setStack] = useState((typeof STACKS !== 'undefined' && STACKS[0]) ? STACKS[0].key : 'next');
  const [agent, setAgent] = useState('claude');
  const [type, setType] = useState('');  // vacío = «(Sin tipo específico)» → no impone formato Envato
  const [mode, setMode] = useState('scratch');
  const [refKind, setRefKind] = useState('folder');
  const [refVal, setRefVal] = useState('');
  const [repoId, setRepoId] = useState('');  // owner/repo o URL (modo existing)
  const [openCats, setOpenCats] = useState({});  // categoría → abierta? (acordeón)
  const [thinking, setThinking] = useState(false);
  const [filled, setFilled] = useState(false);
  const [genPrompt, setGenPrompt] = useState('');
  const [opts, setOpts] = useState({ autoskills: true, uipro: true, mcp: true, postgres: false, licensing: false, licensing_gh: false, licensing_force: false, docs: true });
  const tog = (k) => setOpts(o => ({ ...o, [k]: !o[k] }));

  const runVibe = (preset) => {
    const desc = preset ? preset.vibe : vibe;
    if (preset) setVibe(preset.vibe);
    setThinking(true); setFilled(false);
    // Pre-fill REAL con IA (suggest_stack) — async vía señal suggest_result.
    if (window.tfBridge && window.tfBridge.suggest_stack && (desc || '').trim()) {
      const onRes = (jsonStr) => {
        let r = {}; try { r = JSON.parse(jsonStr); } catch (e) {}
        if (r && r.stack && (STACKS.find(s => s.key === r.stack))) setStack(r.stack);
        if (r && r.template_type) setType(r.template_type);
        setGenPrompt(r.prompt || r.dev_prompt || ('Build: ' + desc));
        setThinking(false); setFilled(true);
        try { window.tfBridge.suggest_result.disconnect(onRes); } catch (e) {}
      };
      if (window.tfBridge.suggest_result && window.tfBridge.suggest_result.connect)
        window.tfBridge.suggest_result.connect(onRes);
      window.tfBridge.suggest_stack(desc);
      return;
    }
    // Fallback (prototipo suelto sin puente).
    const v = preset || VIBE_PRESETS[1];
    setTimeout(() => {
      setStack(v.stack); setAgent(v.agent); setType(v.type);
      setGenPrompt(`Build a production-ready ${v.type} using ${(STACKS.find(s => s.key === v.stack)||{label:v.stack}).label}. ${(preset || { vibe }).vibe || vibe}. Cohesive design system, WCAG AA, real copy (no lorem), Unsplash imagery del nicho, deploy-ready. Anti-copy: layout original.`);
      setThinking(false); setFilled(true);
    }, 1400);
  };

  const Pill = ({ k, label, jp }) => (
    <button onClick={() => setSub(k)} style={{ cursor: 'pointer', padding: '9px 16px', borderRadius: 10, fontSize: 13, fontFamily: 'var(--font-display)', display: 'flex', alignItems: 'center', gap: 7,
      background: sub === k ? 'rgba(var(--accent-rgb),0.12)' : 'transparent', border: '1px solid ' + (sub === k ? 'rgba(var(--accent-rgb),0.45)' : 'var(--line)'),
      color: sub === k ? 'var(--accent)' : 'var(--tx-dim)', boxShadow: sub === k ? '0 0 14px rgba(var(--accent-rgb),0.22)' : 'none', transition: 'all 0.15s' }}>
      {label} <span className="jp" style={{ fontSize: 10, opacity: 0.7 }}>{jp}</span>
    </button>
  );

  return (
    <div style={{ padding: '34px 40px 60px', position: 'relative', zIndex: 2, maxWidth: 1180, margin: '0 auto' }}>
      <Eyebrow jp="新規制作">NEW PROJECT · 鍛造</Eyebrow>
      <h1 style={{ fontFamily: 'var(--font-mega)', fontSize: 36, margin: '12px 0 4px' }}>
        <span className="neon-text-2">VIBE</span> <span style={{ color: 'var(--tx)' }}>SCAFFOLDER</span>
      </h1>
      <div className="dim" style={{ fontSize: 13.5, marginBottom: 20 }}>Describe → la IA pre-rellena · 63 stacks · 4 modos · MCP auto-config.</div>

      {/* sub-tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 22, flexWrap: 'wrap' }}>
        {NP_SUBTABS.map(s => <Pill key={s.k} k={s.k} label={s.label} jp={s.jp} />)}
      </div>

      {/* ---- VIBE ---- */}
      {sub === 'vibe' && (
        <div className="fade-in" style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: 22, alignItems: 'start' }}>
          <div className="panel card-corner" style={{ padding: 22 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 12 }}>
              <Icon name="sparkles" size={17} style={{ color: 'var(--accent-2)' }} />
              <span style={{ fontWeight: 600, fontSize: 14 }}>Describe tu vibe</span>
            </div>
            <textarea value={vibe} onChange={e => setVibe(e.target.value)}
              placeholder='Ej: "Landing premium para clínica dental en Madrid, paleta cálida…"'
              style={{ width: '100%', minHeight: 92, resize: 'vertical', background: 'var(--bg-void)', border: '1px solid var(--line-bright)', borderRadius: 'var(--radius-sm)', padding: 14, color: 'var(--tx)', fontFamily: 'var(--font-mono)', fontSize: 13, lineHeight: 1.6, outline: 'none' }} />
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 12 }}>
              <span className="faint" style={{ fontSize: 11, alignSelf: 'center' }}>probar:</span>
              {VIBE_PRESETS.map((p, i) => (
                <button key={i} onClick={() => runVibe(p)} className="chip" style={{ cursor: 'pointer', maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis' }}>{p.vibe.slice(0, 26)}…</button>
              ))}
            </div>
            <div style={{ marginTop: 16, display: 'flex', gap: 10, alignItems: 'center' }}>
              <Btn variant="primary" icon="sparkles" onClick={() => runVibe(null)}>{thinking ? 'Pensando…' : '✨ Pre-fill con IA'}</Btn>
              {thinking && <span className="mono" style={{ fontSize: 12, color: 'var(--accent)' }}><span style={{ animation: 'blink 0.8s infinite' }}>◢◣</span> {agent} analizando…</span>}
            </div>
            {(filled || thinking) && (
              <div className="fade-in" style={{ marginTop: 18, borderTop: '1px solid var(--line)', paddingTop: 16 }}>
                <div className="eyebrow" style={{ marginBottom: 8 }}>PROMPT GENERADO · 生成プロンプト</div>
                <div className="mono" style={{ background: 'var(--bg-void)', border: '1px solid var(--line)', borderRadius: 8, padding: 14, fontSize: 12, lineHeight: 1.7, color: 'var(--codex)', minHeight: 70 }}>
                  {thinking ? <span style={{ animation: 'blink 0.8s infinite' }}>▊ generando…</span> : genPrompt}
                </div>
              </div>
            )}
          </div>
          <div className="panel" style={{ padding: 18 }}>
            <div className="eyebrow" style={{ marginBottom: 12 }}>AGENTE IA · 代理</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              {Object.entries(AGENTS).map(([k, a]) => (
                <button key={k} onClick={() => setAgent(k)} style={{ cursor: 'pointer', padding: '11px 12px', borderRadius: 8, display: 'flex', alignItems: 'center', gap: 9,
                  background: agent === k ? 'rgba(255,255,255,0.04)' : 'transparent', border: '1px solid ' + (agent === k ? a.color + '88' : 'var(--line)'),
                  boxShadow: agent === k ? `0 0 16px ${a.hex}33` : 'none', color: 'var(--tx)', transition: 'all 0.15s' }}>
                  <span style={{ color: a.color, fontSize: 15 }}>{a.glyph}</span>
                  <span style={{ fontSize: 12.5 }}>{a.label}</span>
                </button>
              ))}
            </div>
            <div className="eyebrow" style={{ margin: '18px 0 10px' }}>SUGERENCIA IA · 提案</div>
            {filled
              ? <div className="dim fade-in" style={{ fontSize: 12.5, lineHeight: 1.7 }}>
                  Stack <span style={{ color: 'var(--accent)' }}>{(STACKS.find(s => s.key === stack)||{label:stack}).label}</span> · tipo <span style={{ color: 'var(--accent)' }}>{type || 'sin especificar'}</span> · agente <span style={{ color: AGENTS[agent].color }}>{AGENTS[agent].label}</span>
                </div>
              : <div className="faint" style={{ fontSize: 12 }}>Pulsa «Pre-fill con IA» para autorrellenar.</div>}
          </div>
        </div>
      )}

      {/* ---- SETUP (stack + UI Pro + MCP) ---- */}
      {sub === 'setup' && (
        <div className="fade-in">
          {/* Nombre del proyecto (carpeta ~/Proyectos/themes/<slug>). */}
          <div className="panel" style={{ padding: 20, marginBottom: 18 }}>
            <div className="eyebrow" style={{ marginBottom: 10 }}>NOMBRE DEL PROYECTO · 名前</div>
            <input value={pname} onChange={e => setPname(e.target.value)}
              placeholder="Ej: Aurora Dental · se crea en ~/Proyectos/themes/<slug>"
              style={{ width: '100%', background: 'var(--bg-void)', border: '1px solid var(--line-bright)', borderRadius: 8, padding: '11px 14px', color: 'var(--tx)', fontFamily: 'var(--font-display)', fontSize: 14, outline: 'none' }} />
          </div>
          <div className="panel" style={{ padding: 20, marginBottom: 18 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 14 }}>
              <div className="eyebrow">STACK · 基盤 <span style={{ color: 'var(--tx-faint)' }}>· {STACKS.length} disponibles</span></div>
              {filled && <Chip color="var(--accent)">✦ sugerido por IA</Chip>}
            </div>
            {/* Stacks agrupados por categoría (como en la app normal). */}
            {(() => {
              const groups = {};
              STACKS.forEach(s => { const c = s.cat || 'Otros'; (groups[c] = groups[c] || []).push(s); });
              const selCat = (STACKS.find(s => s.key === stack) || {}).cat;  // categoría del stack activo
              return Object.keys(groups).map(cat => {
                // Abierta por defecto solo la categoría del stack seleccionado;
                // el resto plegadas. El usuario puede toggle cada cabecera.
                const open = openCats[cat] !== undefined ? openCats[cat] : (cat === selCat);
                return (
                <div key={cat} style={{ marginBottom: 10 }}>
                  <button onClick={() => setOpenCats(o => ({ ...o, [cat]: !open }))}
                    style={{ width: '100%', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8,
                      background: 'rgba(255,255,255,0.02)', border: '1px solid var(--line)', borderRadius: 8,
                      padding: '9px 12px', color: 'var(--tx-dim)', textAlign: 'left', transition: 'all 0.12s' }}>
                    <span style={{ color: 'var(--accent)', transform: open ? 'rotate(90deg)' : 'none', transition: 'transform 0.15s', display: 'inline-block', width: 12 }}>▸</span>
                    <span className="mono" style={{ fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase', flex: 1 }}>{cat}</span>
                    <span className="chip" style={{ fontSize: 9.5 }}>{groups[cat].length}</span>
                    {groups[cat].some(s => s.key === stack) && <span style={{ width: 6, height: 6, borderRadius: 99, background: 'var(--accent)', boxShadow: '0 0 6px var(--accent)' }} />}
                  </button>
                  {open && (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: 10, padding: '10px 2px 4px' }}>
                      {groups[cat].map(s => <StackTile key={s.key} s={s} active={stack === s.key} onClick={() => setStack(s.key)} />)}
                    </div>
                  )}
                </div>
                );
              });
            })()}
          </div>
          {/* Tipo + agente (como el form nativo de Setup). */}
          <div className="panel" style={{ padding: 18, marginBottom: 18, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div>
              <div className="eyebrow" style={{ marginBottom: 8 }}>TIPO DE TEMPLATE · 種類</div>
              <input value={type} onChange={e => setType(e.target.value)} placeholder="SaaS Landing · E-commerce · Dashboard…"
                style={{ width: '100%', background: 'var(--bg-void)', border: '1px solid var(--line-bright)', borderRadius: 8, padding: '9px 12px', color: 'var(--tx)', fontFamily: 'var(--font-mono)', fontSize: 12.5, outline: 'none' }} />
            </div>
            <div>
              <div className="eyebrow" style={{ marginBottom: 8 }}>AGENTE IA · 代理</div>
              <select value={agent} onChange={e => setAgent(e.target.value)}
                style={{ width: '100%', background: 'var(--bg-void)', border: '1px solid var(--line-bright)', borderRadius: 8, padding: '9px 12px', color: 'var(--tx)', fontFamily: 'var(--font-mono)', fontSize: 12.5 }}>
                {Object.keys(AGENTS).map(k => <option key={k} value={k}>{AGENTS[k].label}</option>)}
              </select>
            </div>
          </div>
          <div className="panel" style={{ padding: '6px 20px 14px' }}>
            <CheckRow label="npx autoskills" jp="技能" sub="auto-instala skills del stack (a11y/SEO/design) en .claude/skills/" on={opts.autoskills} onToggle={() => tog('autoskills')} />
            <CheckRow label="UI/UX Pro Max" jp="高級UI" sub="shadcn/ui · Aceternity · Magic UI + sistema de diseño (67 estilos / 161 paletas)" on={opts.uipro} onToggle={() => tog('uipro')} />
            <CheckRow label="Pre-configurar MCP servers" jp="接続" sub="genera .mcp.json (filesystem · github · playwright · figma-context · themeforge…)" on={opts.mcp} onToggle={() => tog('mcp')} />
            <CheckRow label="Documentación" jp="文書" sub="documentation/ con guía de instalación + changelog" on={opts.docs} onToggle={() => tog('docs')} />
          </div>
        </div>
      )}

      {/* ---- MODE ---- */}
      {sub === 'mode' && (
        <div className="fade-in">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 12, marginBottom: 16 }}>
            {MODES.map(m => (
              <button key={m.k} onClick={() => setMode(m.k)} className={mode === m.k ? 'neon-edge' : ''}
                style={{ cursor: 'pointer', textAlign: 'left', padding: '16px 18px', borderRadius: 12, display: 'flex', gap: 13,
                  background: mode === m.k ? 'rgba(var(--accent-rgb),0.10)' : 'rgba(255,255,255,0.02)', border: '1px solid ' + (mode === m.k ? 'rgba(var(--accent-rgb),0.5)' : 'var(--line)'), color: 'var(--tx)', transition: 'all 0.15s' }}>
                <Icon name={m.icon} size={20} style={{ color: mode === m.k ? 'var(--accent)' : 'var(--tx-faint)', flexShrink: 0, marginTop: 2 }} />
                <div>
                  <div style={{ fontSize: 14.5, fontWeight: 600, display: 'flex', gap: 8, alignItems: 'center' }}>{m.label} <span className="jp faint" style={{ fontSize: 11 }}>{m.jp}</span></div>
                  <div className="dim" style={{ fontSize: 12, marginTop: 5, lineHeight: 1.5 }}>{m.desc}</div>
                </div>
              </button>
            ))}
          </div>
          {/* reference sub-form for recreate/adopt */}
          {(mode === 'recreate' || mode === 'adopt') && (
            <div className="panel card-corner fade-in" style={{ padding: 20 }}>
              <div className="eyebrow" style={{ marginBottom: 14 }}>REFERENCIA · 参照</div>
              {mode === 'recreate' && (
                <div style={{ display: 'flex', gap: 6, marginBottom: 12, flexWrap: 'wrap' }}>
                  {REF_KINDS.map(r => (
                    <button key={r.k} onClick={() => setRefKind(r.k)} className="chip" style={{ cursor: 'pointer', color: refKind === r.k ? 'var(--accent)' : 'var(--tx-dim)', borderColor: refKind === r.k ? 'rgba(var(--accent-rgb),0.5)' : 'var(--line-bright)' }}>{r.label}</button>
                  ))}
                </div>
              )}
              <div style={{ display: 'flex', gap: 10 }}>
                <input value={refVal} onChange={e => setRefVal(e.target.value)} placeholder={refKind === 'url' ? 'https://demo-template.com' : refKind === 'figma' ? 'figma.com/file/…?node-id=' : 'Ruta o examinar…'}
                  style={{ flex: 1, background: 'var(--bg-void)', border: '1px solid var(--line-bright)', borderRadius: 8, padding: '9px 12px', color: 'var(--tx)', fontFamily: 'var(--font-mono)', fontSize: 12, outline: 'none' }} />
                <Btn icon="folderOpen" variant="ghost" onClick={() => {
                  if (!window.tfBridge) return;
                  const picker = refKind === 'zip' ? window.tfBridge.pick_file : window.tfBridge.pick_folder;
                  if (!picker) return;
                  picker().then(j => {
                    let r = {}; try { r = JSON.parse(j); } catch (e) {}
                    if (!r.path) return;
                    setRefVal(r.path);
                    // Auto-detecta el stack (WordPress) desde la referencia, como el normal.
                    if (window.tfBridge.detect_ref_stack) window.tfBridge.detect_ref_stack(r.path).then(dj => {
                      let d = {}; try { d = JSON.parse(dj); } catch (e) {}
                      if (d.stack && STACKS.find(s => s.key === d.stack)) setStack(d.stack);
                    });
                  });
                }}>Examinar</Btn>
              </div>
              <div style={{ marginTop: 14, display: 'flex', gap: 10, alignItems: 'center' }}>
                <Btn variant="primary" icon="search" onClick={() => { window.__tfRef = { value: refVal, kind: refKind }; onAnalyze(); }}>🔍 Analizar con IA</Btn>
                <span className="faint" style={{ fontSize: 11.5 }}>
                  {refKind === 'figma' ? 'Lee el frame vía MCP figma-context (sin anti-copy: es tu diseño).' : 'Detecta stack + estudia layout/paleta/tipo, multi-turno.'}
                </span>
              </div>
            </div>
          )}
          {mode === 'repo' && (
            <div className="panel fade-in" style={{ padding: 20 }}>
              <div className="eyebrow" style={{ marginBottom: 12 }}>REPOSITORIO · GITHUB</div>
              <input value={repoId} onChange={e => setRepoId(e.target.value)} placeholder="owner/repo o https://github.com/owner/repo" style={{ width: '100%', background: 'var(--bg-void)', border: '1px solid var(--line-bright)', borderRadius: 8, padding: '9px 12px', color: 'var(--tx)', fontFamily: 'var(--font-mono)', fontSize: 12, outline: 'none' }} />
              <div className="faint" style={{ fontSize: 11, marginTop: 8 }}>No hace falta nombre: se usa el de la repo. <code>gh repo clone</code> con historial intacto.</div>
            </div>
          )}
        </div>
      )}

      {/* ---- EXTRAS ---- */}
      {sub === 'extras' && (
        <div className="fade-in panel" style={{ padding: '6px 20px 14px' }}>
          <div className="faint" style={{ fontSize: 11, padding: '8px 0' }}>Integraciones opcionales. Los toggles de build (autoskills · UI/UX Pro · MCP · docs) están en <b style={{ color: 'var(--accent)' }}>Setup 基礎</b>.</div>
          <CheckRow label="🐘 PostgreSQL en Docker" jp="DB" sub="contenedor postgres:17 dedicado + DATABASE_URL en .env (requiere Docker)" on={opts.postgres} onToggle={() => tog('postgres')} />
          <CheckRow label="🔑 Sistema de licencias (pcreative anti-nulled)" jp="認可" sub="genera verify-license + setup wizard según la familia del stack (tu backend en licensing.json)" on={opts.licensing} onToggle={() => tog('licensing')} />
          {opts.licensing && (
            <div style={{ paddingLeft: 18, borderLeft: '2px solid var(--line-bright)', marginLeft: 6 }}>
              <CheckRow label="└─ Crear repo gh <org>/<slug>" jp="" sub="gh repo create privado tras el scaffold (org en licensing.json · github_org)" on={opts.licensing_gh} onToggle={() => tog('licensing_gh')} />
              <CheckRow label="└─ Forzar también en adopt / existing" jp="強制" sub="por defecto el licensing solo corre en scratch/recreate" on={opts.licensing_force} onToggle={() => tog('licensing_force')} />
            </div>
          )}
        </div>
      )}

      {/* ---- PREVIEW ---- */}
      {sub === 'preview' && (
        <div className="fade-in panel card-corner" style={{ padding: 22 }}>
          <div className="eyebrow" style={{ marginBottom: 14 }}>VISTA PREVIA · 確認</div>
          <div className="mono" style={{ background: 'var(--bg-void)', border: '1px solid var(--line)', borderRadius: 8, padding: 18, fontSize: 12.5, lineHeight: 1.9, color: 'var(--tx-dim)' }}>
            <div><span className="faint"># stack ····</span> <span style={{ color: 'var(--accent)' }}>{(STACKS.find(s => s.key === stack)||{label:stack}).label}</span></div>
            <div><span className="faint"># tipo ·····</span> {type || '(sin especificar — lo define el stack/análisis)'}</div>
            <div><span className="faint"># modo ·····</span> {(MODES.find(m => m.k === mode)||{label:mode}).label}</div>
            <div><span className="faint"># agente ···</span> <span style={{ color: AGENTS[agent].color }}>{AGENTS[agent].label}</span></div>
            <div><span className="faint"># mcp ······</span> {opts.mcp ? '.mcp.json (8 servers)' : 'off'}</div>
            <div><span className="faint"># ui pro ···</span> {opts.uipro ? 'shadcn + aceternity' : 'off'}</div>
            <div><span className="faint"># extras ···</span> {[opts.postgres && 'postgres', opts.licensing && 'licensing', opts.docs && 'docs'].filter(Boolean).join(' · ') || '—'}</div>
            <div><span className="faint"># coste est</span> <span style={{ color: 'var(--codex)' }}>~$0.40</span></div>
          </div>
        </div>
      )}

      {/* launch bar (always) */}
      <div className="panel" style={{ marginTop: 22, padding: '16px 22px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderColor: 'rgba(var(--accent-rgb),0.3)' }}>
        <div className="mono" style={{ fontSize: 12.5, color: 'var(--tx-dim)' }}>
          <span style={{ color: 'var(--accent)' }}>{(STACKS.find(s => s.key === stack)||{label:stack}).label}</span>{' · '}{(MODES.find(m => m.k === mode)||{label:mode}).label}{' · '}<span style={{ color: AGENTS[agent].color }}>{AGENTS[agent].label}</span>{' · ~$0.40'}
        </div>
        <Btn variant="primary" icon="rocket" onClick={() => {
          if (mode === 'repo') {
            const rid = (repoId || '').trim();
            if (!rid || rid.indexOf('/') < 0) { alert('Indica el repo como owner/repo o una URL de GitHub.'); return; }
            // El nombre = nombre de la repo (último segmento, sin .git).
            const repoName = rid.replace(/\.git$/, '').replace(/\/$/, '').split('/').pop();
            onLaunch({ stack: 'none', agent, type, mode: 'existing', opts, niche: vibe,
              name: repoName, existing_repo: rid });
            return;
          }
          const name = (pname || '').trim() || (vibe || '').trim().slice(0, 42) || type || 'Untitled Forge';
          if (!(pname || '').trim() && !confirm('Sin nombre — se usará «' + name + '». ¿Continuar?')) return;
          onLaunch({ stack, agent, type, mode, opts, niche: vibe, name,
            reference: refVal, reference_kind: refKind });
        }}>Forjar proyecto</Btn>
      </div>
    </div>
  );
}

Object.assign(window, { NewProjectScreen });
