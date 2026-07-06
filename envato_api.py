"""
envato_api — datos REALES del mercado Envato (ThemeForest / CodeCanyon) para el
analizador de mercado de Pcreative Studio.

Usa la API oficial (https://api.envato.com) con un token personal (permiso
"View and search Envato sites"). El token se guarda en la config del programa
(ai_providers → keys.json, key_id "envato"). Todo es tolerante a fallos: si no
hay token o la API falla, las funciones devuelven vacío y el analizador sigue
con solo la búsqueda web.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.envato.com"
_UA = "Pcreative Studio Market Analyzer"

# Sitios de Envato relevantes para nosotros (código/web).
SITES = {
    "themeforest": "themeforest.net",
    "codecanyon": "codecanyon.net",
}


def get_token() -> str:
    """Token de Envato desde la config del programa o el entorno."""
    try:
        import ai_providers as aip
        keys = aip.load_keys()
        if keys.get("envato"):
            return keys["envato"].strip()
    except Exception:
        pass
    import os
    return os.environ.get("ENVATO_API_TOKEN", "").strip()


def has_token() -> bool:
    return bool(get_token())


def _get(path: str, timeout: int = 25):
    token = get_token()
    if not token:
        raise RuntimeError("Falta el token de Envato")
    req = urllib.request.Request(
        BASE + path,
        headers={"Authorization": "Bearer " + token, "User-Agent": _UA},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _fmt_int(n) -> str:
    try:
        return f"{int(n):,}".replace(",", ".")
    except Exception:
        return str(n)


def top_sellers(site: str = "themeforest", term: str = "", category: str = "",
                limit: int = 12) -> list[dict]:
    """Ítems reales ordenados por nº de ventas (bestsellers). term/category opcionales."""
    site_domain = SITES.get(site, site if "." in site else site + ".net")
    q = {"site": site_domain, "sort_by": "sales", "sort_direction": "desc",
         "page_size": str(max(1, min(limit, 30)))}
    if term:
        q["term"] = term
    if category:
        q["category"] = category
    try:
        data = _get("/v1/discovery/search/search/item?" + urllib.parse.urlencode(q))
    except Exception:
        return []
    out = []
    for m in (data.get("matches") or [])[:limit]:
        out.append({
            "name": (m.get("name") or "").strip(),
            "sales": m.get("number_of_sales") or 0,
            "price": round((m.get("price_cents") or 0) / 100),
            "rating": (m.get("rating") or {}).get("rating") if isinstance(m.get("rating"), dict) else m.get("rating"),
            "category": m.get("classification") or "",
            "author": m.get("author_username") or "",
            "url": m.get("url") or "",
        })
    return out


def popular_week(site: str = "themeforest", limit: int = 12) -> list[dict]:
    """Ítems que MÁS se están vendiendo esta semana (trending real)."""
    site_key = site.split(".")[0]
    try:
        data = _get(f"/v1/market/popular:{site_key}.json")
    except Exception:
        return []
    pop = data.get("popular", data) or {}
    out = []
    for it in (pop.get("items_last_week") or [])[:limit]:
        out.append({
            "name": (it.get("item") or "").strip(),
            "price": it.get("cost"),
            "url": it.get("url") or "",
        })
    return out


def market_snapshot(site: str = "themeforest", term: str = "", limit: int = 12) -> str:
    """Bloque de texto con DATOS REALES de Envato para inyectar en el prompt del
    analizador. Devuelve "" si no hay token o no hay datos."""
    if not has_token():
        return ""
    site_name = "ThemeForest" if site == "themeforest" else "CodeCanyon" if site == "codecanyon" else site
    sellers = top_sellers(site, term=term, limit=limit)
    trending = popular_week(site, limit=8)
    if not sellers and not trending:
        return ""

    lines = [f"## DATOS REALES DE ENVATO — {site_name}"
             + (f" · nicho «{term}»" if term else "") + " (vía API oficial, ahora mismo)"]
    if sellers:
        lines.append("\n**Más vendidos (por nº de ventas reales):**\n")
        lines.append("| # | Ítem | Ventas | Precio | Categoría |")
        lines.append("|---|------|--------|--------|-----------|")
        for i, s in enumerate(sellers, 1):
            lines.append(f"| {i} | {s['name'][:48]} | {_fmt_int(s['sales'])} | ${s['price']} | {s['category']} |")
    if trending:
        names = ", ".join(f"{t['name'][:40]}" + (f" (${t['price']})" if t.get('price') else "") for t in trending[:8])
        lines.append(f"\n**Trending esta semana:** {names}")
    lines.append("\n> Usa estos datos REALES como base del análisis (no los inventes ni contradigas). "
                 "Puedes complementarlos con la búsqueda web para tendencias y precios de otros marketplaces.\n")
    return "\n".join(lines)
