"""
trends — señal de demanda REAL de Google Trends (vía pytrends, gratis y sin key)
para el analizador de mercado de Pcreative Studio.

Google Trends bloquea (429) con cierta frecuencia, así que TODO es tolerante a
fallos: si algo falla, las funciones devuelven None/"" y el análisis sigue con
Envato + búsqueda web. Cacheado en memoria por término para no repetir llamadas.
"""
from __future__ import annotations

_CACHE: dict[str, dict | None] = {}


def trend_signal(term: str, geo: str = "", timeframe: str = "today 12-m") -> dict | None:
    """Interés medio, pico, tendencia (subiendo/estable/bajando) y búsquedas al alza.
    Devuelve None si Trends falla o no hay datos."""
    term = (term or "").strip()
    if not term:
        return None
    ck = f"{term}|{geo}|{timeframe}"
    if ck in _CACHE:
        return _CACHE[ck]
    result: dict | None = None
    try:
        from pytrends.request import TrendReq
        p = TrendReq(hl="es", tz=60, timeout=(4, 12), retries=1, backoff_factor=0.3)
        p.build_payload([term], timeframe=timeframe, geo=geo)
        df = p.interest_over_time()
        if df is not None and not df.empty and term in df:
            vals = [int(v) for v in df[term].tolist()]
            vals = [v for v in vals if v is not None]
            if vals:
                n = len(vals)
                third = max(1, n // 3)
                first = sum(vals[:third]) / third
                last = sum(vals[-third:]) / third
                trend = ("subiendo" if last > first * 1.15
                         else "bajando" if last < first * 0.85 else "estable")
                rising = []
                try:
                    rq = (p.related_queries() or {}).get(term, {}) or {}
                    r = rq.get("rising")
                    if r is not None and not r.empty:
                        rising = [str(x) for x in r["query"].tolist()[:5]]
                except Exception:
                    pass
                result = {
                    "term": term,
                    "interes_medio": round(sum(vals) / n, 1),
                    "pico": max(vals),
                    "actual": vals[-1],
                    "tendencia": trend,
                    "rising": rising,
                }
    except Exception:
        result = None
    _CACHE[ck] = result
    return result


def trend_block(term: str, geo: str = "") -> str:
    """Bloque markdown con la señal de Trends para inyectar en el prompt. "" si falla."""
    s = trend_signal(term, geo=geo)
    if not s:
        return ""
    arrow = {"subiendo": "📈", "estable": "➡️", "bajando": "📉"}.get(s["tendencia"], "")
    rising = ""
    if s["rising"]:
        rising = " · búsquedas al alza: " + ", ".join(s["rising"])
    return (
        f"## GOOGLE TRENDS — «{term}» (últimos 12 meses, dato real)\n"
        f"Interés medio {s['interes_medio']}/100 · pico {s['pico']} · tendencia {arrow} **{s['tendencia']}**{rising}.\n"
        f"Usa esta señal de demanda real para tu análisis y el scoring.\n"
    )
