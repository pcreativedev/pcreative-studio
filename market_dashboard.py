"""
market_dashboard — genera el HTML del panel de Mercado para QWebEngineView.

Renderiza los análisis con estética de dashboard real usando Chart.js (bundle
local inlineado, sin CDN → funciona offline). Tres salidas:
  · dashboard_opportunities(data)  → tarjetas con radar por oportunidad + ranking.
  · dashboard_hybrid(summary, narrative_html) → barra de ranking + análisis.
  · page(body_html)                → envuelve markdown-a-html en la misma estética.
"""
from __future__ import annotations

import json
from pathlib import Path

_CHARTJS_CACHE: str | None = None


def _chartjs() -> str:
    """Contenido de Chart.js (inlineado). "" si no está el bundle."""
    global _CHARTJS_CACHE
    if _CHARTJS_CACHE is None:
        p = Path(__file__).parent / "assets" / "vendor" / "chart.umd.min.js"
        try:
            _CHARTJS_CACHE = p.read_text(encoding="utf-8")
        except Exception:
            _CHARTJS_CACHE = ""
    return _CHARTJS_CACHE


_CSS = """
:root { color-scheme: dark; }
* { box-sizing: border-box; }
body { margin:0; padding:18px 20px 40px; background:#0b1220; color:#dbe1ea;
  font:14px/1.55 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; }
h1 { color:#c7d2fe; font-size:22px; font-weight:800; margin:2px 0 14px; }
h2 { color:#a5b4fc; font-size:17px; font-weight:700; border-bottom:2px solid #3730a3;
  padding-bottom:5px; margin:26px 0 12px; }
h3 { color:#93c5fd; font-size:14px; margin:14px 0 6px; }
a { color:#60a5fa; text-decoration:none; }
table { border-collapse:collapse; width:100%; margin:10px 0; }
th { background:#1e293b; color:#c7d2fe; text-align:left; padding:8px 11px; font-size:12px; }
td { padding:7px 11px; border:1px solid #22304a; }
blockquote { background:#111a2e; border-left:4px solid #6366f1; margin:10px 0; padding:8px 14px; color:#c7d2fe; }
code { background:#1e293b; color:#fbbf24; padding:1px 6px; border-radius:5px; }
.rankwrap { background:#0f1830; border:1px solid #1e293b; border-radius:14px; padding:14px 16px; margin-bottom:20px; }
.grid { display:grid; grid-template-columns:1fr; gap:16px; }
.card { background:#0f1830; border:1px solid #1e293b; border-radius:16px; padding:16px 18px;
  display:grid; grid-template-columns:220px 1fr; gap:18px; align-items:center; }
.card .radar { width:220px !important; height:200px !important; }
.rank-badge { display:inline-block; background:#1e293b; color:#94a3b8; border-radius:8px;
  padding:2px 9px; font-weight:700; font-size:12px; }
.opp { font-size:34px; font-weight:800; line-height:1; }
.opp small { font-size:12px; color:#64748b; font-weight:500; }
.name { font-size:18px; font-weight:800; color:#f1f5f9; margin:2px 0 6px; }
.pitch { color:#cbd5e1; margin:0 0 10px; }
.chips { margin:6px 0 10px; }
.chip { display:inline-block; padding:3px 10px; border-radius:8px; font-size:12px; font-weight:600; margin-right:8px; }
.evi { color:#93c5fd; font-size:12.5px; font-style:italic; margin:8px 0; }
.steps { margin:6px 0 0 0; padding-left:18px; }
.steps li { margin:3px 0; }
@media (max-width:640px){ .card{ grid-template-columns:1fr; } .card .radar{ width:100%; } }
"""


def _color(good: int) -> str:
    return "#22c55e" if good >= 70 else "#f59e0b" if good >= 45 else "#ef4444"


_CHARTJS_CDN = "https://cdn.jsdelivr.net/npm/chart.js@4.4.6/dist/chart.umd.min.js"


def page(body: str, with_charts: bool = False, scripts: str = "") -> str:
    cjs = ""
    if with_charts:
        local = _chartjs()
        cjs = f"<script>{local}</script>" if local else f"<script src='{_CHARTJS_CDN}'></script>"
    tail = f"<script>{scripts}</script>" if scripts else ""
    return (
        "<!doctype html><html lang='es'><head><meta charset='utf-8'>"
        f"<style>{_CSS}</style>{cjs}</head><body>{body}{tail}</body></html>"
    )


def dashboard_opportunities(data: dict) -> str:
    ops = data.get("oportunidades") or []
    titulo = data.get("titulo", "Oportunidades")
    # Ranking (barra horizontal) por oportunidad.
    ordered = sorted(ops, key=lambda o: -int((o.get("scores") or {}).get("oportunidad", 0) or 0))
    labels = [str(o.get("nombre", ""))[:34] for o in ordered]
    vals = [int((o.get("scores") or {}).get("oportunidad", 0) or 0) for o in ordered]
    bar_colors = [_color(v) for v in vals]

    cards = []
    radar_cfgs = []
    for i, o in enumerate(ordered):
        sc = o.get("scores") or {}
        opp = int(sc.get("oportunidad", 0) or 0)
        oc = _color(opp)
        dem = int(sc.get("demanda", 0) or 0)
        ing = int(sc.get("ingresos", 0) or 0)
        comp = int(sc.get("competencia", 0) or 0)
        dif = int(sc.get("dificultad", 0) or 0)
        # ejes "mayor = mejor": hueco = 100-competencia, facilidad = 100-dificultad
        radar_vals = [dem, ing, 100 - comp, 100 - dif, opp]
        cid = f"radar{i}"
        radar_cfgs.append((cid, radar_vals, oc))

        chips = []
        if o.get("marketplace"):
            chips.append(f'<span class="chip" style="background:#1e293b;color:#c7d2fe">🛒 {o["marketplace"]}</span>')
        if o.get("precio"):
            chips.append(f'<span class="chip" style="background:#1e293b;color:#a7f3d0">💶 {o["precio"]}</span>')
        if o.get("stack"):
            from importlib import import_module
            try:
                stacks = import_module("stacks")
                sname = stacks.STACKS.get(o["stack"], {}).get("name", o["stack"])
            except Exception:
                sname = o["stack"]
            chips.append(f'<span class="chip" style="background:#312e81;color:#c7d2fe">🧱 {sname}</span>')
        steps = "".join(f"<li>{s}</li>" for s in (o.get("como_proceder") or []))
        evi = f'<div class="evi">📊 {o.get("evidencia","")}</div>' if o.get("evidencia") else ""
        cards.append(
            f'<div class="card" style="border-left:5px solid {oc}">'
            f'<canvas id="{cid}" class="radar" width="220" height="200"></canvas>'
            f'<div>'
            f'<span class="rank-badge">#{i+1}</span> '
            f'<span class="opp" style="color:{oc}">{opp}<small>/100 oportunidad</small></span>'
            f'<div class="name">{o.get("nombre","")}</div>'
            f'<div class="pitch">{o.get("pitch","")}</div>'
            f'<div class="chips">{"".join(chips)}</div>'
            f'{evi}'
            + (f'<h3>Cómo proceder</h3><ol class="steps">{steps}</ol>' if steps else "")
            + '</div></div>'
        )

    body = (
        f"<h1>💎 {titulo}</h1>"
        f'<div class="rankwrap"><canvas id="rank" height="{max(120, 34*len(labels))}"></canvas></div>'
        f'<div class="grid">{"".join(cards)}</div>'
    )

    # JS de los gráficos
    radar_js = ""
    for cid, rv, color in radar_cfgs:
        radar_js += f"""
new Chart(document.getElementById('{cid}'), {{
  type:'radar',
  data:{{ labels:['Demanda','Ingresos','Hueco','Facilidad','Oport.'],
    datasets:[{{ data:{json.dumps(rv)}, fill:true,
      backgroundColor:'{color}33', borderColor:'{color}', borderWidth:2,
      pointBackgroundColor:'{color}', pointRadius:2 }}] }},
  options:{{ responsive:false, maintainAspectRatio:false,
    plugins:{{legend:{{display:false}}}}, scales:{{ r:{{
    min:0,max:100, ticks:{{display:false,stepSize:25}},
    grid:{{color:'#233152'}}, angleLines:{{color:'#233152'}},
    pointLabels:{{color:'#94a3b8',font:{{size:10}}}} }} }},
    animation:{{duration:500}} }}
}});"""
    scripts = f"""
new Chart(document.getElementById('rank'), {{
  type:'bar',
  data:{{ labels:{json.dumps(labels)},
    datasets:[{{ label:'Oportunidad', data:{json.dumps(vals)},
      backgroundColor:{json.dumps(bar_colors)}, borderRadius:6 }}] }},
  options:{{ indexAxis:'y', plugins:{{legend:{{display:false}},
    title:{{display:true,text:'Ranking por score de oportunidad',color:'#a5b4fc',font:{{size:13}}}}}},
    scales:{{ x:{{min:0,max:100,grid:{{color:'#1e293b'}},ticks:{{color:'#64748b'}}}},
      y:{{grid:{{display:false}},ticks:{{color:'#dbe1ea',font:{{size:11}}}}}} }},
    animation:{{duration:500}} }}
}});
{radar_js}"""
    return page(body, with_charts=True, scripts=scripts)


def dashboard_hybrid(summary: dict | None, narrative_html: str, versus: bool = False) -> str:
    """Panel para general/niche (ranking bar + análisis) o compare (versus + análisis)."""
    top = ""
    scripts = ""
    if summary and not versus and summary.get("items"):
        items = sorted(summary["items"], key=lambda x: -int(x.get("oportunidad", 0) or 0))
        labels = [str(it.get("nombre", ""))[:36] for it in items]
        vals = [int(it.get("oportunidad", 0) or 0) for it in items]
        colors = [_color(v) for v in vals]
        top = (f'<h2>🏆 Oportunidades del análisis</h2>'
               f'<div class="rankwrap"><canvas id="rank" height="{max(120,34*len(labels))}"></canvas></div>')
        scripts = f"""
new Chart(document.getElementById('rank'), {{
  type:'bar', data:{{ labels:{json.dumps(labels)},
   datasets:[{{data:{json.dumps(vals)},backgroundColor:{json.dumps(colors)},borderRadius:6}}] }},
  options:{{ indexAxis:'y', plugins:{{legend:{{display:false}}}},
   scales:{{x:{{min:0,max:100,grid:{{color:'#1e293b'}},ticks:{{color:'#64748b'}}}},
     y:{{grid:{{display:false}},ticks:{{color:'#dbe1ea',font:{{size:11}}}}}}}},
   animation:{{duration:450}} }}
}});"""
    elif summary and versus and ("a" in summary or "b" in summary):
        a = summary.get("a", {}) or {}
        b = summary.get("b", {}) or {}
        axes = ["Demanda", "Ingresos", "Hueco", "Facilidad", "Oport."]
        keys = ["demanda", "ingresos", "competencia", "dificultad", "oportunidad"]
        def vec(s):
            s = s or {}
            return [int(s.get("demanda", 0) or 0), int(s.get("ingresos", 0) or 0),
                    100 - int(s.get("competencia", 0) or 0), 100 - int(s.get("dificultad", 0) or 0),
                    int(s.get("oportunidad", 0) or 0)]
        va, vb = vec(a.get("scores")), vec(b.get("scores"))
        top = (f'<h2>⚔️ {a.get("nombre","A")} vs {b.get("nombre","B")}</h2>'
               f'<div class="rankwrap"><canvas id="vs" height="260"></canvas></div>')
        scripts = f"""
new Chart(document.getElementById('vs'), {{
  type:'radar',
  data:{{ labels:{json.dumps(axes)}, datasets:[
    {{label:{json.dumps(a.get("nombre","A"))}, data:{json.dumps(va)}, backgroundColor:'#6366f133', borderColor:'#818cf8', borderWidth:2, pointRadius:2}},
    {{label:{json.dumps(b.get("nombre","B"))}, data:{json.dumps(vb)}, backgroundColor:'#22c55e33', borderColor:'#4ade80', borderWidth:2, pointRadius:2}} ]}},
  options:{{ plugins:{{legend:{{labels:{{color:'#dbe1ea'}}}}}},
   scales:{{r:{{min:0,max:100,ticks:{{display:false}},grid:{{color:'#233152'}},angleLines:{{color:'#233152'}},pointLabels:{{color:'#94a3b8',font:{{size:11}}}}}}}},
   animation:{{duration:500}} }}
}});"""
    body = top + ("<hr style='border:0;border-top:1px solid #22304a;margin:18px 0'>" if top else "") + narrative_html
    return page(body, with_charts=bool(scripts), scripts=scripts)
