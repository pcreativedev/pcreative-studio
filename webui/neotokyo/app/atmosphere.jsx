/* ================= NEO-TOKYO · atmosphere ================= */

/* Rain — diagonal neon streaks on a canvas */
function RainCanvas({ on }) {
  const ref = useRef(null);
  useEffect(() => {
    if (!on) return;
    const cv = ref.current;
    const ctx = cv.getContext('2d');
    let raf, drops = [], w, h;
    const resize = () => {
      w = cv.width = cv.offsetWidth * devicePixelRatio;
      h = cv.height = cv.offsetHeight * devicePixelRatio;
      const n = Math.floor((w * h) / 90000);
      drops = Array.from({ length: n }, () => mk());
    };
    const mk = () => ({
      x: Math.random() * w, y: Math.random() * h,
      len: 8 + Math.random() * 26, sp: 6 + Math.random() * 14,
      a: 0.06 + Math.random() * 0.22,
    });
    const draw = () => {
      ctx.clearRect(0, 0, w, h);
      const ang = 0.28;
      for (const d of drops) {
        const grad = ctx.createLinearGradient(d.x, d.y, d.x - ang * d.len, d.y + d.len);
        grad.addColorStop(0, `rgba(150,220,255,0)`);
        grad.addColorStop(1, `rgba(150,225,255,${d.a})`);
        ctx.strokeStyle = grad;
        ctx.lineWidth = 1.1 * devicePixelRatio;
        ctx.beginPath();
        ctx.moveTo(d.x, d.y);
        ctx.lineTo(d.x - ang * d.len, d.y + d.len);
        ctx.stroke();
        d.y += d.sp; d.x -= ang * d.sp * 0.4;
        if (d.y > h) { d.y = -d.len; d.x = Math.random() * w; }
      }
      raf = requestAnimationFrame(draw);
    };
    resize(); draw();
    window.addEventListener('resize', resize);
    return () => { cancelAnimationFrame(raf); window.removeEventListener('resize', resize); };
  }, [on]);
  if (!on) return null;
  return <canvas ref={ref} className="rain-canvas" />;
}

/* Atmosphere wrapper — grid + glows */
function Atmosphere() {
  return (
    <div className="atmos">
      <div className="atmos-glow-a" />
      <div className="atmos-glow-b" />
      <div className="atmos-grid" />
    </div>
  );
}

/* Boot sequence overlay */
function BootSequence({ onDone }) {
  const lines = [
    '> themeforge.core // 鍛造エンジン',
    '> mounting neon kernel ............ OK',
    '> loading agents [claude·codex·gemini·opencode] .. OK',
    '> calibrating glow matrix ......... OK',
    '> establishing uplink 東京/NEO ..... OK',
    '> ready.',
  ];
  const [shown, setShown] = useState(0);
  const [fade, setFade] = useState(false);
  useEffect(() => {
    if (shown < lines.length) {
      const t = setTimeout(() => setShown(shown + 1), shown === 0 ? 220 : 150 + Math.random() * 120);
      return () => clearTimeout(t);
    }
    const t1 = setTimeout(() => setFade(true), 420);
    const t2 = setTimeout(onDone, 900);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, [shown]);
  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 999, background: 'var(--bg-void)',
      display: 'grid', placeItems: 'center', transition: 'opacity 0.45s',
      opacity: fade ? 0 : 1, pointerEvents: fade ? 'none' : 'auto',
    }}>
      <Atmosphere />
      <div style={{ position: 'relative', textAlign: 'center', zIndex: 2 }}>
        <div className="neon-text" style={{
          fontFamily: 'var(--font-mega)', fontSize: 46, letterSpacing: '0.04em',
          marginBottom: 6, animation: 'flicker 2.5s infinite',
        }}>PCREATIVE STUDIO</div>
        <div className="jp" style={{ color: 'var(--tx-faint)', letterSpacing: '0.5em', fontSize: 13, marginBottom: 30 }}>
          ネオ東京 ・ 鍛造システム
        </div>
        <div className="mono" style={{ textAlign: 'left', fontSize: 12.5, lineHeight: 1.9, color: 'var(--codex)', minHeight: 150 }}>
          {lines.slice(0, shown).map((l, i) => (
            <div key={i} style={{ animation: 'float-in 0.2s both' }}>
              {l}{i === shown - 1 && shown < lines.length && <span style={{ animation: 'blink 1s infinite' }}>▊</span>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { RainCanvas, Atmosphere, BootSequence });
