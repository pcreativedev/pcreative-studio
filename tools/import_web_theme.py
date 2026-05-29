#!/usr/bin/env python3
"""import_web_theme.py — convierte un tema de Claude Design en un web theme pack.

Uso interno (no expuesto al usuario final): cuando te pasan un prototipo de
Claude Design, este script extrae los CSS custom properties de su `:root`
(o de cualquier `.css` / carpeta) y genera `webui/themes/<slug>.json` con los
tokens mapeados a las CSS vars que usa la UI Neo-Tokyo (--bg-void, --accent…).

    python3 tools/import_web_theme.py <css|carpeta> --name "Synthwave" [--slug synthwave]
    python3 tools/import_web_theme.py "~/Descargas/tema (1)" --name "Mi Tema"

Mapea por dos vías, en orden:
  1. Passthrough: si el prototipo ya usa nuestros nombres de var, se copian tal cual.
  2. Heurística por nombre/valor para los nombres distintos (accent/bg/text/line…).

El resultado SIEMPRE se imprime para revisar; ajusta el JSON a mano si hace falta.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Vars canónicas que consume la UI (styles/neo-tokyo.css :root).
CANONICAL = [
    "--bg-void", "--bg-deep", "--bg-panel", "--bg-panel-2", "--bg-raise",
    "--tx", "--tx-dim", "--tx-faint", "--line", "--line-bright",
    "--accent", "--accent-2", "--accent-rgb", "--accent2-rgb",
]

# Heurística: para cada var canónica, palabras clave que suelen aparecer en el
# nombre de la var de origen (orden de preferencia).
HEURISTICS = {
    "--bg-void":     ["bg-void", "background", "bg-base", "bg-primary", "bg0", "base", "bg"],
    "--bg-deep":     ["bg-deep", "bg-secondary", "surface", "bg1", "elevated-0"],
    "--bg-panel":    ["bg-panel", "panel", "card", "bg-tertiary", "surface-1", "bg2"],
    "--bg-panel-2":  ["bg-panel-2", "panel-2", "bg-elevated", "surface-2", "bg3"],
    "--bg-raise":    ["bg-raise", "raise", "hover", "elevated", "bg4"],
    "--tx":          ["tx\\b", "text", "fg", "foreground", "text-primary", "on-bg"],
    "--tx-dim":      ["tx-dim", "text-secondary", "fg-dim", "muted", "text-2"],
    "--tx-faint":    ["tx-faint", "text-faint", "disabled", "subtle", "text-3"],
    "--line":        ["line\\b", "border", "divider", "outline"],
    "--line-bright": ["line-bright", "border-strong", "border-2", "ring"],
    "--accent":      ["accent\\b", "primary", "brand", "accent-1"],
    "--accent-2":    ["accent-2", "accent2", "secondary", "magenta", "pink", "highlight"],
}

_VAR_RE = re.compile(r"(--[\w-]+)\s*:\s*([^;]+);")
_HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")


def _extract_root_vars(css: str) -> dict:
    """Saca {--var: valor} de los bloques :root / [data-theme] / .dark / .theme-*."""
    out = {}
    # Concatena el contenido de los selectores de tema más comunes.
    blocks = re.findall(r"(?::root|\[data-theme[^\]]*\]|\.dark|\.theme-[\w-]+)\s*\{([^}]*)\}", css)
    text = "\n".join(blocks) if blocks else css
    for m in _VAR_RE.finditer(text):
        name, val = m.group(1), m.group(2).strip()
        out[name] = val
    return out


def _resolve_vars(src: dict) -> dict:
    """Expande referencias var(--x) a su valor concreto (2 pasadas)."""
    out = dict(src)
    ref = re.compile(r"var\(\s*(--[\w-]+)\s*(?:,[^)]*)?\)")
    for _ in range(3):
        changed = False
        for k, v in list(out.items()):
            m = ref.search(v or "")
            if m and m.group(1) in out:
                out[k] = ref.sub(lambda mm: out.get(mm.group(1), mm.group(0)), v)
                changed = True
        if not changed:
            break
    return out


def _hex_to_rgb(h: str) -> str | None:
    m = _HEX_RE.search(h or "")
    if not m:
        return None
    s = m.group(0).lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    try:
        return f"{int(s[0:2],16)}, {int(s[2:4],16)}, {int(s[4:6],16)}"
    except Exception:
        return None


def _pick(src: dict, claimed: set, canonical: str) -> tuple[str, str] | None:
    """Devuelve (var_origen, valor) para `canonical`, reclamando la var de
    origen (no se reutiliza para otra canónica). Passthrough exacto primero."""
    if canonical in src and canonical not in claimed:
        return canonical, src[canonical]
    for kw in HEURISTICS.get(canonical, []):
        pat = re.compile(kw, re.I)
        for name, val in src.items():
            if name in claimed:
                continue
            if pat.search(name):
                return name, val
    return None


def build_pack(css: str, name: str) -> dict:
    src = _resolve_vars(_extract_root_vars(css))
    vars_out = {}
    claimed: set = set()
    # Orden: fondo/texto/borde reclaman antes que accent (evita que
    # 'text-primary' se confunda con el accent 'primary').
    for c in CANONICAL:
        if c in ("--accent-rgb", "--accent2-rgb"):
            continue
        picked = _pick(src, claimed, c)
        if picked:
            origin, val = picked
            claimed.add(origin)
            vars_out[c] = val
    # Deriva los *-rgb del accent/accent-2 si no venían.
    if "--accent" in vars_out:
        rgb = _hex_to_rgb(vars_out["--accent"])
        if rgb:
            vars_out["--accent-rgb"] = rgb
    if "--accent-2" in vars_out:
        rgb2 = _hex_to_rgb(vars_out["--accent-2"])
        if rgb2:
            vars_out["--accent2-rgb"] = rgb2
    # Fuentes opcionales.
    for fv in ("--font-display", "--font-mega", "--font-mono"):
        if fv in src:
            vars_out[fv] = src[fv]
    return {"name": name, "jp": "", "vars": vars_out}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="archivo .css o carpeta del prototipo de Claude Design")
    ap.add_argument("--name", required=True, help="nombre del tema")
    ap.add_argument("--slug", default=None, help="slug del archivo (por defecto del nombre)")
    ap.add_argument("--out", default=None, help="ruta de salida (por defecto webui/themes/<slug>.json)")
    a = ap.parse_args()

    src = Path(a.source).expanduser()
    css_files = []
    if src.is_dir():
        css_files = sorted(src.rglob("*.css"))
    elif src.suffix.lower() == ".css":
        css_files = [src]
    if not css_files:
        print(f"No se encontró ningún .css en {src}", file=sys.stderr)
        sys.exit(1)
    css = "\n".join(f.read_text(encoding="utf-8", errors="replace") for f in css_files)

    pack = build_pack(css, a.name)
    slug = a.slug or re.sub(r"[^a-z0-9]+", "-", a.name.lower()).strip("-")
    out = Path(a.out).expanduser() if a.out else (
        Path(__file__).resolve().parent.parent / "webui" / "themes" / f"{slug}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(pack, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"✓ Pack escrito: {out}")
    print(f"  CSS leídos: {len(css_files)} · vars mapeadas: {len(pack['vars'])}")
    missing = [c for c in CANONICAL if c not in pack["vars"]]
    if missing:
        print(f"  ⚠ sin mapear (rellénalas a mano): {', '.join(missing)}")
    print(json.dumps(pack, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
