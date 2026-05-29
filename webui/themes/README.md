# Web theme packs (plug-and-play)

Drop a `*.json` file in this folder and it becomes a selectable **web theme**
in ThemeForge → Settings → Temas (recolors the Neo-Tokyo web UI live, no code,
no restart). This is the easy path for a new Claude Design visual direction:
extract its colors/fonts into one JSON here and it just works.

## Schema

```jsonc
{
  "name": "Synthwave",          // display label
  "jp": "シンセ",                // optional katakana/kanji eyebrow
  "vars": {                      // CSS custom properties applied to :root
    "--bg-void":    "#0d0221",   // window background
    "--bg-deep":    "#120a2a",   // nav rail / chrome
    "--bg-panel":   "#1a0f33",   // panels
    "--bg-panel-2": "#241544",
    "--bg-raise":   "#2e1a55",
    "--tx":         "#f5e6ff",   // text
    "--tx-dim":     "#c9a9e9",
    "--tx-faint":   "#8a6fb0",
    "--line":       "rgba(200,120,255,0.14)",
    "--line-bright":"rgba(255,120,220,0.30)",
    "--accent":     "#ff2bd6",   // primary accent
    "--accent-2":   "#00e5ff",   // secondary accent
    "--accent-rgb": "255, 43, 214",   // accent as "r, g, b" (for rgba())
    "--accent2-rgb":"0, 229, 255",
    "--font-display": "'Chakra Petch', sans-serif",   // optional
    "--font-mega":    "'Zen Dots', sans-serif"         // optional
  }
}
```

- Only `name` + `vars` are required. Any CSS var the prototype uses can be
  overridden (see `styles/neo-tokyo.css` `:root` for the full list).
- `--accent-rgb` / `--accent2-rgb` must be the `r, g, b` form (used inside
  `rgba(var(--accent-rgb), 0.x)` all over the UI). If omitted, the accent's
  hex is reused but rgba() helpers won't tint correctly — include them.
- Fonts: reference any family; bundle the `.ttf` in `assets/fonts/` (the
  splash loader picks it up) or rely on a system font.

## How to add a Claude Design theme

1. Open the prototype's `styles/*.css` and copy the `:root` color/font values.
2. Map them to the `vars` above (most map 1:1 to the Neo-Tokyo var names).
3. Save as `webui/themes/<slug>.json`.
4. Launch ThemeForge → Settings → Temas → your theme appears. Click → applied.

That's it — no editing React, no bridge wiring, no restart.

## Importador automático (uso interno)

Cuando te pasen un tema de Claude Design, en vez de escribir el JSON a mano:

```bash
python3 tools/import_web_theme.py <css|carpeta-del-prototipo> --name "Nombre"
```

Extrae los CSS custom properties del `:root` del prototipo, resuelve los
`var()`, y mapea a nuestras vars (`--bg-void/--accent/...`) por passthrough +
heurística (texto/fondo/borde reclaman antes que el accent). Escribe el pack en
`webui/themes/<slug>.json` e imprime qué quedó sin mapear para revisarlo.
