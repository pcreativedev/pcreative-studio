/* ================= NEO-TOKYO · AI Cost Tracker ================= */

const _COST = (typeof window !== 'undefined' && window.__TF_DATA__ && window.__TF_DATA__.cost) || {};
const _MOCK_COST_BY_AGENT = [
  { k: 'claude', v: 12.77 },
  { k: 'codex', v: 3.32 },
  { k: 'gemini', v: 7.34 },
  { k: 'opencode', v: 1.63 },
];
const COST_BY_AGENT = (_COST.by_agent && _COST.by_agent.length) ? _COST.by_agent : _MOCK_COST_BY_AGENT;
const DAYS = (_COST.days && _COST.days.length) ? _COST.days : Array.from({ length: 30 }, (_, i) => {
  const base = 0.4 + Math.sin(i / 3) * 0.3 + Math.random() * 0.9;
  return Math.max(0, +(base * (i > 24 ? 1.8 : 1)).toFixed(2));
});
// Filas de la tabla de modelos (reales si hay datos, mock si no).
const COST_MODELS = (_COST.models && _COST.models.length) ? _COST.models : [
  { agent: 'claude', model: 'sonnet-4.5', sessions: 47, input: '5.1M', output: '92k', rate: '$3/$15', cost: 12.77 },
  { agent: 'gemini', model: '2.5-pro', sessions: 23, input: '3.4M', output: '58k', rate: '$1.25/$10', cost: 7.34 },
  { agent: 'codex', model: 'gpt-5-codex', sessions: 31, input: '1.8M', output: '41k', rate: '$1.5/$8', cost: 3.32 },
  { agent: 'opencode', model: 'local-qwen', sessions: 12, input: '0.9M', output: '22k', rate: 'free', cost: 1.63 },
];

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
  const total = (typeof _COST.total === 'number') ? _COST.total : COST_BY_AGENT.reduce((s, d) => s + d.v, 0);
  const month = (typeof _COST.month === 'number') ? _COST.month : DAYS.reduce((s, v) => s + v, 0);
  const tokensLabel = _COST.tokens || '8.2M tokens';
  return (
    <div style={{ padding: '34px 40px 60px', position: 'relative', zIndex: 2 }}>
      <Eyebrow jp="費用追跡">AI COST · 費用</Eyebrow>
      <h1 style={{ fontFamily: 'var(--font-mega)', fontSize: 38, margin: '12px 0 24px' }}>
        <span className="neon-text">COST</span> TRACKER
      </h1>

      <div style={{ display: 'flex', gap: 16, marginBottom: 20 }}>
        <Stat label="TOTAL ALL-TIME" value={`$${total.toFixed(2)}`} sub={tokensLabel} color="var(--accent)" />
        <Stat label="ESTE MES" value={`$${month.toFixed(2)}`} sub="últimos 30 días" color="var(--codex)" />
        <Stat label="POR PROYECTO" value="$3.94" sub="media · 6 proyectos" />
        <Stat label="TOKENS / $" value="421K" sub="eficiencia media" color="var(--gemini)" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 20 }}>
        {/* donut */}
        <div className="panel card-corner" style={{ padding: 22, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <div className="eyebrow" style={{ alignSelf: 'flex-start', marginBottom: 8 }}>POR PROVEEDOR · 代理別</div>
          <Donut data={COST_BY_AGENT} total={total} />
          <div style={{ width: '100%', marginTop: 16, display: 'flex', flexDirection: 'column', gap: 8 }}>
            {COST_BY_AGENT.map(d => (
              <div key={d.k} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 12.5 }}>
                <span style={{ width: 10, height: 10, borderRadius: 3, background: AGENTS[d.k].hex, boxShadow: `0 0 8px ${AGENTS[d.k].hex}` }} />
                <span style={{ flex: 1 }}>{AGENTS[d.k].label}</span>
                <span className="mono" style={{ color: AGENTS[d.k].color }}>${d.v.toFixed(2)}</span>
                <span className="mono faint" style={{ fontSize: 10, width: 38, textAlign: 'right' }}>{((d.v / total) * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* bars + table */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div className="panel" style={{ padding: 22 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
              <div className="eyebrow">GASTO DIARIO · 日別 (30d)</div>
              <span className="mono" style={{ fontSize: 11, color: 'var(--accent-2)' }}>▲ pico semana actual</span>
            </div>
            <BarChart days={DAYS} />
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
                {COST_MODELS.map((r, i) => {
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
