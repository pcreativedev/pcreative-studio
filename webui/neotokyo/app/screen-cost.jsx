/* ================= NEO-TOKYO · AI Cost Tracker ================= */

const _COST = (typeof window !== 'undefined' && window.__TF_DATA__ && window.__TF_DATA__.cost) || {};
const _MOCK_COST_BY_AGENT = [];
const COST_BY_AGENT = (_COST.by_agent && _COST.by_agent.length) ? _COST.by_agent : [];
const DAYS = (_COST.days && _COST.days.length) ? _COST.days : Array.from({ length: 30 }, () => 0);
const COST_MODELS = (_COST.models && _COST.models.length) ? _COST.models : [];

function Donut({ data, total }) {
  const prog = useCountUp(1, 1100, []);
  const r = 78, cx = 100, cy = 100, circ = 2 * Math.PI * r;
  let acc = 0;
  return (
    <svg viewBox="0 0 200 200" style={{ width: 220, height: 220 }}>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="20" />
      {data.map((d, i) => {
        const frac = d.v / total;
        const dash = circ * frac * prog;
        const el = (
          <circle key={d.k} cx={cx} cy={cy} r={r} fill="none"
            stroke={AGENTS[d.k].hex} strokeWidth="20"
            strokeDasharray={`${dash} ${circ}`}
            strokeDashoffset={-circ * acc * prog}
            transform={`rotate(-90 ${cx} ${cy})`}
            style={{ filter: `drop-shadow(0 0 6px ${AGENTS[d.k].hex})`, transition: 'stroke-dasharray 0.1s' }} />
        );
        acc += frac;
        return el;
      })}
      <text x={cx} y={cy - 6} textAnchor="middle" fill="var(--tx)" style={{ fontFamily: 'var(--font-mega)', fontSize: 22 }}>
        ${(total * prog).toFixed(2)}
      </text>
      <text x={cx} y={cy + 14} textAnchor="middle" fill="var(--tx-faint)" style={{ fontFamily: 'var(--font-mono)', fontSize: 9, letterSpacing: '0.1em' }}>
        ALL-TIME
      </text>
    </svg>
  );
}

function BarChart({ days }) {
  const prog = useCountUp(1, 1200, []);
  const max = Math.max(...days);
  const W = 560, H = 150, n = days.length, bw = W / n;
  return (
    <svg viewBox={`0 0 ${W} ${H + 24}`} style={{ width: '100%' }}>
      <line x1="0" y1={H} x2={W} y2={H} stroke="var(--line-bright)" />
      {days.map((v, i) => {
        const bh = (v / max) * H * prog;
        const hot = i >= 25;
        return (
          <rect key={i} x={i * bw + 1.5} y={H - bh} width={bw - 3} height={bh} rx="2"
            fill={hot ? 'var(--accent-2)' : 'var(--accent)'}
            style={{ filter: `drop-shadow(0 0 4px ${hot ? 'rgba(var(--accent2-rgb),0.6)' : 'rgba(var(--accent-rgb),0.5)'})`, opacity: 0.92 }} />
        );
      })}
      {[0, 7, 14, 21, 29].map(i => (
        <text key={i} x={i * bw + bw / 2} y={H + 16} textAnchor="middle" fill="var(--tx-faint)" style={{ fontFamily: 'var(--font-mono)', fontSize: 9 }}>
          {30 - i}d
        </text>
      ))}
    </svg>
  );
}

function Stat({ label, value, sub, color }) {
  return (
    <div className="panel" style={{ padding: '16px 18px', flex: 1 }}>
      <div className="eyebrow" style={{ fontSize: 10 }}>{label}</div>
      <div style={{ fontFamily: 'var(--font-mega)', fontSize: 26, marginTop: 8, color: color || 'var(--tx)' }}>{value}</div>
      {sub && <div className="mono faint" style={{ fontSize: 11, marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

function CostScreen() {
  const [c, setC] = useState(_COST);
  const rescan = () => { const B = window.tfBridge; if (B && B.cost_data) B.cost_data().then(j => { let r = {}; try { r = JSON.parse(j); } catch (e) {} if (!r.error) setC(r); }); };
  const byAgent = (c.by_agent && c.by_agent.length) ? c.by_agent : [];
  const days = (c.days && c.days.length) ? c.days : Array.from({ length: 30 }, () => 0);
  const models = c.models || [];
  const total = (typeof c.total === 'number') ? c.total : byAgent.reduce((s, d) => s + d.v, 0);
  const month = (typeof c.month === 'number') ? c.month : days.reduce((s, v) => s + v, 0);
  const tokensLabel = (c.tokens || '0') + ' tokens';
  return (
    <div style={{ padding: '34px 40px 60px', position: 'relative', zIndex: 2 }}>
      <Eyebrow jp="費用追跡">AI COST · 費用</Eyebrow>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', margin: '12px 0 24px' }}>
        <h1 style={{ fontFamily: 'var(--font-mega)', fontSize: 38, margin: 0 }}><span className="neon-text">COST</span> TRACKER</h1>
        <Btn variant="ghost" icon="refresh" onClick={rescan}>Re-scan</Btn>
      </div>

      <div style={{ display: 'flex', gap: 16, marginBottom: 20 }}>
        <Stat label="TOTAL ALL-TIME" value={`$${total.toFixed(2)}`} sub={tokensLabel} color="var(--accent)" />
        <Stat label="ESTE MES" value={`$${month.toFixed(2)}`} sub="últimos 30 días" color="var(--codex)" />
        <Stat label="MODELOS" value={String(models.length)} sub="con coste registrado" />
        <Stat label="PROVEEDORES" value={String(byAgent.length)} sub="activos" color="var(--gemini)" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 20 }}>
        {/* donut */}
        <div className="panel card-corner" style={{ padding: 22, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <div className="eyebrow" style={{ alignSelf: 'flex-start', marginBottom: 8 }}>POR PROVEEDOR · 代理別</div>
          {byAgent.length ? <Donut data={byAgent} total={total || 1} /> : <div className="mono faint" style={{ padding: 40 }}>sin gasto registrado</div>}
          <div style={{ width: '100%', marginTop: 16, display: 'flex', flexDirection: 'column', gap: 8 }}>
            {byAgent.map(d => { const ag = AGENTS[d.k] || { hex: '#00f0ff', color: 'var(--accent)', label: d.k }; return (
              <div key={d.k} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 12.5 }}>
                <span style={{ width: 10, height: 10, borderRadius: 3, background: ag.hex, boxShadow: `0 0 8px ${ag.hex}` }} />
                <span style={{ flex: 1 }}>{ag.label}</span>
                <span className="mono" style={{ color: ag.color }}>${d.v.toFixed(2)}</span>
                <span className="mono faint" style={{ fontSize: 10, width: 38, textAlign: 'right' }}>{total ? ((d.v / total) * 100).toFixed(0) : 0}%</span>
              </div>); })}
          </div>
        </div>

        {/* bars + table */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div className="panel" style={{ padding: 22 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
              <div className="eyebrow">GASTO DIARIO · 日別 (30d)</div>
            </div>
            <BarChart days={days} />
          </div>
          <div className="panel" style={{ padding: 0, overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12.5 }}>
              <thead>
                <tr style={{ background: 'rgba(255,255,255,0.03)' }}>
                  {['Modelo', 'Sesiones', 'Input', 'Output', 'Tarifa', 'Coste'].map(h => (
                    <th key={h} className="mono" style={{ textAlign: h === 'Modelo' ? 'left' : 'right', padding: '11px 16px', fontSize: 10.5, letterSpacing: '0.08em', color: 'var(--tx-faint)', textTransform: 'uppercase', fontWeight: 500 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {models.length === 0 && <tr><td colSpan={6} className="mono faint" style={{ padding: 22, textAlign: 'center' }}>// sin sesiones de IA registradas</td></tr>}
                {models.map((r, i) => {
                  const ag = AGENTS[r.agent] || { color: 'var(--accent)', glyph: '◆' };
                  return (
                  <tr key={i} style={{ borderTop: '1px solid var(--line)' }}>
                    <td style={{ padding: '10px 16px' }}>
                      <span style={{ color: ag.color }}>{ag.glyph}</span> <span className="mono">{r.model}</span>
                    </td>
                    <td className="mono dim" style={{ textAlign: 'right', padding: '10px 16px' }}>{r.sessions}</td>
                    <td className="mono dim" style={{ textAlign: 'right', padding: '10px 16px' }}>{r.input}</td>
                    <td className="mono dim" style={{ textAlign: 'right', padding: '10px 16px' }}>{r.output}</td>
                    <td className="mono faint" style={{ textAlign: 'right', padding: '10px 16px' }}>{r.rate}</td>
                    <td className="mono" style={{ textAlign: 'right', padding: '10px 16px', color: ag.color }}>${r.cost.toFixed(2)}</td>
                  </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { CostScreen });
