/* ================= NEO-TOKYO · modals ================= */

function ModalShell({ title, jp, onClose, width = 720, children, accentBorder }) {
  useEffect(() => {
    const h = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', h); return () => window.removeEventListener('keydown', h);
  }, []);
  return (
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, zIndex: 220, background: 'rgba(2,4,10,0.72)', backdropFilter: 'blur(6px)', display: 'grid', placeItems: 'center', padding: 24 }}>
      <div className="panel neon-edge fade-in" onClick={e => e.stopPropagation()}
        style={{ width: `min(${width}px, 94vw)`, maxHeight: '88vh', padding: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column', ...(accentBorder ? { borderColor: accentBorder } : {}) }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '16px 20px', borderBottom: '1px solid var(--line)' }}>
          <div style={{ flex: 1 }}>
            <div className="eyebrow" style={{ fontSize: 9.5 }}>{jp}</div>
            <div style={{ fontSize: 16, fontWeight: 600, marginTop: 3 }}>{title}</div>
          </div>
          <button className="btn btn-ghost" style={{ padding: '6px 9px' }} onClick={onClose}><Icon name="x" size={15} /></button>
        </div>
        <div style={{ overflowY: 'auto', flex: 1 }}>{children}</div>
      </div>
    </div>
  );
}

/* ---------- Reference Analysis (streaming, multi-turn AI) ---------- */
const REF_STREAM = [
  { t: 'sys', s: '🔍 Analizando referencia · agent=claude · parser=folder' },
  { t: 'out', s: 'Detectado: Next.js 14 (app router) + Tailwind + shadcn/ui' },
  { t: 'out', s: 'Layout: hero split · bento de 6 features · pricing 3-tier · footer mega' },
  { t: 'out', s: 'Paleta dominante: índigo #6366f1 · neutros slate · radios 12px' },
  { t: 'out', s: 'Tipografía: Geist Sans (display) + Geist Mono (code)' },
  { t: 'warn', s: '⚠ Imágenes propietarias detectadas → reemplazar por Unsplash del nicho' },
  { t: 'q', s: '¿Mantengo la estructura de pricing o propongo una alternativa original?' },
];

function ReferenceAnalysisModal({ onClose }) {
  const real = !!(window.tfBridge && window.tfBridge.analyze_reference);
  const [shown, setShown] = useState(0);
  const [done, setDone] = useState(false);
  const [reply, setReply] = useState('');
  const [turns, setTurns] = useState([]);
  const [lines, setLines] = useState([]);  // streaming real
  const boxRef = useRef(null);

  // Streaming REAL del análisis de referencia (reference_analyzer + IA).
  useEffect(() => {
    if (!real) return;
    const ref = (window.__tfRef && window.__tfRef.value) || prompt('Ruta de la referencia a analizar (carpeta o .zip):') || '';
    if (!ref) { setDone(true); return; }
    const kind = (window.__tfRef && window.__tfRef.kind) || 'folder';
    const onProg = (j) => {
      let r = {}; try { r = JSON.parse(j); } catch (e) {}
      if (r.line !== undefined) setLines(ls => [...ls, r.line]);
      if (r.done) { if (r.error) setLines(ls => [...ls, '⚠ ' + r.error]); setDone(true); }
    };
    if (window.tfBridge.reference_progress && window.tfBridge.reference_progress.connect)
      window.tfBridge.reference_progress.connect(onProg);
    window.tfBridge.analyze_reference(ref, kind);
    return () => { try { window.tfBridge.reference_progress.disconnect(onProg); } catch (e) {} };
  }, []);

  // Fallback mock (prototipo suelto sin puente).
  useEffect(() => {
    if (real) return;
    if (shown >= REF_STREAM.length) { setDone(true); return; }
    const t = setTimeout(() => setShown(s => s + 1), 380 + Math.random() * 320);
    return () => clearTimeout(t);
  }, [shown]);
  useEffect(() => { if (boxRef.current) boxRef.current.scrollTop = boxRef.current.scrollHeight; }, [shown, turns, lines]);

  const send = () => {
    if (!reply.trim()) return;
    setTurns(t => [...t, { you: reply, ai: 'Entendido — propondré un layout de pricing original (toggle anual + tier destacado), anti-copy. Inyectado al CLAUDE.md del proyecto.' }]);
    setReply('');
  };

  const color = { sys: 'var(--claude)', out: 'var(--tx-dim)', warn: 'var(--gemini)', q: 'var(--accent)' };
  return (
    <ModalShell title="Análisis de referencia con Claude Code" jp="参照分析 · REFERENCE ANALYSIS" onClose={onClose} width={820}>
      <div ref={boxRef} className="mono" style={{ padding: 18, fontSize: 12.5, lineHeight: 1.8, maxHeight: '52vh', overflowY: 'auto', background: '#03050b' }}>
        {real
          ? lines.map((l, i) => <div key={i} style={{ color: 'var(--tx-dim)', marginBottom: 2, whiteSpace: 'pre-wrap' }}>{l}</div>)
          : REF_STREAM.slice(0, shown).map((l, i) => <div key={i} style={{ color: color[l.t], marginBottom: 2 }}>{l.s}</div>)}
        {!done && <span style={{ color: 'var(--accent)', animation: 'blink 0.8s infinite' }}>▊ {real ? 'analizando referencia con IA…' : 'streaming…'}</span>}
        {turns.map((t, i) => (
          <div key={i} style={{ marginTop: 12, borderTop: '1px solid var(--line)', paddingTop: 10 }}>
            <div style={{ color: 'var(--accent-2)' }}>👤 Tú: {t.you}</div>
            <div style={{ color: 'var(--codex)', marginTop: 6 }}>🤖 {t.ai}</div>
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', gap: 8, padding: 14, borderTop: '1px solid var(--line)' }}>
        <input value={reply} onChange={e => setReply(e.target.value)} onKeyDown={e => e.key === 'Enter' && send()}
          disabled={!done} placeholder={done ? 'Responder al agente…' : 'esperando análisis…'}
          style={{ flex: 1, background: 'var(--bg-void)', border: '1px solid var(--line-bright)', borderRadius: 8, padding: '9px 12px', color: 'var(--tx)', fontFamily: 'var(--font-mono)', fontSize: 12, outline: 'none', opacity: done ? 1 : 0.5 }} />
        <Btn icon="check" onClick={send}>➡ Enviar</Btn>
        <Btn variant="primary" icon="save" onClick={onClose}>💾 Guardar</Btn>
      </div>
    </ModalShell>
  );
}

/* ---------- Deploy modal ---------- */
function DeployModal({ onClose }) {
  const [target, setTarget] = useState('netlify');
  const [phase, setPhase] = useState('idle'); // idle|building|live
  const [log, setLog] = useState([]);
  const steps = ['⟳ npm run build …', '✓ build OK · 1.2 MB', `⟳ subiendo a ${target} …`, '✓ desplegado', '◤ LIVE'];
  const go = () => {
    setPhase('building'); setLog([]);
    let i = 0;
    const tick = () => {
      if (i >= steps.length) { setPhase('live'); return; }
      setLog(l => [...l, steps[i]]); i++;
      setTimeout(tick, 600);
    };
    tick();
  };
  const t = DEPLOY_TARGETS.find(d => d.id === target);
  return (
    <ModalShell title="Deploy demo" jp="展開 · DEPLOY" onClose={onClose} width={620}>
      <div style={{ padding: 20 }}>
        <div className="eyebrow" style={{ marginBottom: 12 }}>DESTINO · 宛先</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 18 }}>
          {DEPLOY_TARGETS.map(d => (
            <button key={d.id} onClick={() => setTarget(d.id)} disabled={phase !== 'idle'}
              style={{ cursor: 'pointer', padding: '13px 14px', borderRadius: 9, textAlign: 'left', display: 'flex', alignItems: 'center', gap: 10,
                background: target === d.id ? 'rgba(255,255,255,0.04)' : 'transparent',
                border: '1px solid ' + (target === d.id ? d.color + '88' : 'var(--line)'),
                boxShadow: target === d.id ? `0 0 16px ${d.color}33` : 'none', color: 'var(--tx)', transition: 'all 0.15s' }}>
              <Icon name="rocket" size={16} style={{ color: d.color }} />
              <span style={{ fontSize: 13.5, fontWeight: 600, flex: 1 }}>{d.label}</span>
              <span className="jp faint" style={{ fontSize: 11 }}>{d.jp}</span>
            </button>
          ))}
        </div>
        {phase === 'idle'
          ? <Btn variant="primary" icon="rocket" onClick={go} style={{ width: '100%', justifyContent: 'center' }}>Deploy a {t.label}</Btn>
          : <div className="mono" style={{ background: 'var(--bg-void)', border: '1px solid var(--line)', borderRadius: 8, padding: 14, fontSize: 12, lineHeight: 1.9, minHeight: 120 }}>
              {log.map((l, i) => <div key={i} style={{ color: l.startsWith('✓') || l.startsWith('◤') ? 'var(--codex)' : 'var(--tx-dim)' }}>{l}</div>)}
              {phase === 'live' && <div style={{ marginTop: 8, color: 'var(--accent)' }}>→ https://{t.id}-aurora-saas.app <span className="faint">· copiado al portapapeles</span></div>}
            </div>}
      </div>
    </ModalShell>
  );
}

/* ---------- Build / Pre-flight / ZIP modal ---------- */
function BuildModal({ onClose }) {
  const [tab, setTab] = useState('preflight');
  const [zipped, setZipped] = useState(false);
  const passed = PREFLIGHT.filter(p => p.status === 'pass').length;
  return (
    <ModalShell title="Pre-flight & ZIP builder" jp="出荷検査 · SHIP CHECK" onClose={onClose} width={640}>
      <div style={{ display: 'flex', gap: 6, padding: '12px 18px 0' }}>
        {[['preflight', 'Pre-flight'], ['zip', 'Build ZIP']].map(([k, l]) => (
          <button key={k} onClick={() => setTab(k)} style={{ cursor: 'pointer', padding: '8px 14px', borderRadius: '8px 8px 0 0', fontSize: 12.5, fontFamily: 'var(--font-display)',
            background: tab === k ? 'rgba(var(--accent-rgb),0.12)' : 'transparent', border: '1px solid ' + (tab === k ? 'rgba(var(--accent-rgb),0.4)' : 'transparent'), borderBottom: 'none', color: tab === k ? 'var(--accent)' : 'var(--tx-dim)' }}>{l}</button>
        ))}
      </div>
      {tab === 'preflight' ? (
        <div style={{ padding: 18 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 14 }}>
            <span className="dim" style={{ fontSize: 13 }}>Checklist marketplace · ThemeForest / CodeCanyon</span>
            <Chip color={passed === PREFLIGHT.length ? 'var(--codex)' : 'var(--gemini)'}>{passed}/{PREFLIGHT.length} OK</Chip>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {PREFLIGHT.map(c => (
              <div key={c.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '9px 12px', borderRadius: 8, background: 'rgba(255,255,255,0.02)', border: '1px solid var(--line)' }}>
                <Icon name={c.status === 'pass' ? 'check' : 'alert'} size={15} style={{ color: c.status === 'pass' ? 'var(--codex)' : 'var(--gemini)' }} />
                <span style={{ flex: 1, fontSize: 13 }}>{c.label}</span>
                {c.note && <span className="mono faint" style={{ fontSize: 10.5 }}>{c.note}</span>}
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div style={{ padding: 18 }}>
          <div className="dim" style={{ fontSize: 13, marginBottom: 14 }}>Empaqueta el proyecto. Excluye <span className="mono" style={{ color: 'var(--accent-2)' }}>node_modules · .env · .git · context/ · reference/</span></div>
          {!zipped ? (
            <Btn variant="primary" icon="package" onClick={() => setZipped(true)} style={{ width: '100%', justifyContent: 'center' }}>Build ZIP para marketplace</Btn>
          ) : (
            <div className="fade-in panel" style={{ padding: 16, borderColor: 'rgba(157,255,60,0.3)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 10 }}>
                <Icon name="check" size={16} style={{ color: 'var(--codex)' }} />
                <span style={{ fontWeight: 600, color: 'var(--codex)' }}>aurora-saas-20260529.zip</span>
              </div>
              <div className="mono dim" style={{ fontSize: 12, lineHeight: 1.8 }}>
                312 archivos · 8.4 MB sin comprimir → <span style={{ color: 'var(--accent)' }}>2.1 MB</span> comprimido (75% reducción)
              </div>
              <Btn icon="download" style={{ marginTop: 14 }}>Descargar ZIP</Btn>
            </div>
          )}
        </div>
      )}
    </ModalShell>
  );
}

Object.assign(window, { ModalShell, ReferenceAnalysisModal, DeployModal, BuildModal });
