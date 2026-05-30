"""hermes_web_agents.py — pack de AGENTES ESPECIALIZADOS en web / UX / UI / estética.

La pestaña 🤖 Agentes lista las skills de `~/.hermes/skills/`, pero Hermes trae su
propia librería genérica (apple, gaming, devops…) que NO tiene que ver con diseño
web. Este módulo siembra un conjunto curado de agentes especializados de ThemeForge
(formato agentskills.io) bajo `~/.hermes/skills/themeforge/<name>/SKILL.md`, todos
enfocados a construir webs/plantillas premium. Cada uno se apoya en el
`themeforge-operator` para el pipeline (create/build/QA/auditoría/zip) y aporta su
especialidad de diseño.

Versionado en el repo a través de este módulo (no archivos sueltos). Idempotente:
solo escribe si falta o si sube la versión; respeta `user_modified: true`.
"""
from __future__ import annotations

from pathlib import Path

TF_SKILLS_DIR = Path.home() / ".hermes" / "skills" / "themeforge"
VERSION = "1.0.0"

# Cada agente: name, title, desc (when-to-use), tags, expertise (bullets).
WEB_AGENTS = [
    {
        "name": "uiux-designer",
        "title": "UX/UI Designer",
        "desc": "Diseño visual y de experiencia: jerarquía, retícula, tipografía, "
                "color, componentes, estados y micro-interacciones para webs premium.",
        "tags": ["web-design", "ux", "ui", "visual-design", "accessibility"],
        "expertise": [
            "Jerarquía visual y composición: foco, ritmo, espacio en blanco, regla "
            "de proximidad/alineación.",
            "Escala tipográfica modular (1.2–1.333), pesos, line-height, medida de "
            "línea (45–75 car.), pairing de fuentes.",
            "Sistemas de color: primario/secundario/acento + neutrales, estados, "
            "contraste WCAG AA (4.5:1 texto, 3:1 UI).",
            "Sistema de componentes: botones, inputs, cards, nav, modales — con "
            "estados hover/focus/active/disabled/error.",
            "Espaciado por escala (4/8px), grid de 12 columnas, breakpoints "
            "360/768/1024/1280/1920.",
            "Micro-interacciones y motion con propósito; respeta prefers-reduced-motion.",
        ],
    },
    {
        "name": "frontend-web-engineer",
        "title": "Frontend Web Engineer",
        "desc": "Implementación frontend moderna y limpia (Astro/Next/Vite/Tailwind): "
                "HTML semántico, responsive, rendimiento y SEO técnico.",
        "tags": ["frontend", "web", "tailwind", "astro", "nextjs", "performance", "seo"],
        "expertise": [
            "HTML semántico y accesible (landmarks, headings en orden, alt, labels, ARIA "
            "solo cuando hace falta).",
            "CSS/Tailwind: utilidades consistentes, design tokens, dark mode, sin estilos "
            "huérfanos; container queries cuando aporta.",
            "Responsive real 360→1920, imágenes responsive (srcset, lazy, width/height), "
            "fuentes con font-display: swap.",
            "Rendimiento: Core Web Vitals (LCP/CLS/INP), code-splitting, prefetch, evitar "
            "JS innecesario; Lighthouse ≥ 90.",
            "SEO técnico por página: title/meta/canonical/OG/JSON-LD, sitemap, robots.",
            "Multipágina con rutas reales del stack; navegación header/footer coherente.",
        ],
    },
    {
        "name": "landing-cro",
        "title": "Landing / Conversion (CRO)",
        "desc": "Landing pages que convierten: propuesta de valor, prueba social, "
                "estructura de oferta, CTAs y patrones de conversión.",
        "tags": ["landing", "cro", "conversion", "copywriting", "marketing", "web"],
        "expertise": [
            "Estructura que vende: hero con propuesta de valor clara en 5s, beneficios > "
            "features, objeciones, prueba social, CTA repetido.",
            "Jerarquía de CTAs (primario/secundario), contraste y ubicación above/below "
            "the fold; fricción mínima en formularios.",
            "Prueba social: testimonios reales, logos, métricas, reseñas, casos.",
            "Pricing: tiers, ancla de precio, plan destacado, FAQ de objeciones.",
            "Copy orientado a beneficio, escaneable (bullets, negritas), tono del nicho.",
            "Medición: eventos/analytics placeholders, A/B-ready, sin dark patterns.",
        ],
    },
    {
        "name": "design-researcher",
        "title": "Design Researcher",
        "desc": "Investiga la web (tendencias, competencia, referencias, paletas) y "
                "produce un design brief antes de diseñar.",
        "tags": ["research", "web-design", "trends", "competitive-analysis", "moodboard"],
        "expertise": [
            "Usa web_search + browser para estudiar tendencias del nicho, top sellers de "
            "ThemeForest, Dribbble y Awwwards.",
            "Analiza 2–3 competidores: layout, secciones, paleta, tipografía, tono, qué "
            "los hace convertir.",
            "Extrae paletas y referencias concretas; documenta un design brief "
            "(layout + paleta + tipografía + hero + secciones must-have).",
            "Detecta lo que está sobre-explotado vs. lo diferenciador en el nicho.",
            "Guarda el brief en `.hermes.md` del proyecto para alimentar el build.",
        ],
    },
    {
        "name": "brand-identity",
        "title": "Brand & Aesthetic Director",
        "desc": "Dirección de marca y estética: logo, paleta, pairing tipográfico, "
                "moodboard e imágenes originales on-brand.",
        "tags": ["branding", "logo", "identity", "aesthetics", "image-generation"],
        "expertise": [
            "Define una dirección estética distinta por variante (editorial/brutalist/"
            "glassmorphic/minimal…) coherente con el nicho.",
            "Logo y marca: usa mcp_themeforge_generate_image con modelo vectorial/flat "
            "(Runware) + prompts de logo limpio.",
            "Paleta y pairing tipográfico que transmiten la personalidad de marca.",
            "Imágenes originales on-brand (hero/OG/ilustraciones) en vez de stock genérico.",
            "OG/social preview por página; favicon; consistencia de marca en todo el sitio.",
        ],
    },
    {
        "name": "ecommerce-ux",
        "title": "E-commerce UX",
        "desc": "UX de tienda: listado/colección, ficha de producto, carrito y checkout "
                "optimizados para conversión.",
        "tags": ["ecommerce", "ux", "shopify", "product-page", "checkout", "web"],
        "expertise": [
            "Ficha de producto: galería, variantes, precio, disponibilidad, reseñas, "
            "cross-sell, sticky add-to-cart en móvil.",
            "Colección/listado: filtros y orden usables, paginación/infinite, quick-view.",
            "Carrito y checkout: pasos mínimos, confianza (envíos/devoluciones), errores "
            "claros, métodos de pago.",
            "Trust & conversión: badges, urgencia honesta, reseñas, garantías.",
            "Accesibilidad y rendimiento en páginas de catálogo (muchas imágenes).",
        ],
    },
    {
        "name": "wordpress-theme-designer",
        "title": "WordPress Theme Designer",
        "desc": "Diseño de temas WordPress (Block/FSE y child themes) vendibles en "
                "ThemeForest, editables por el usuario.",
        "tags": ["wordpress", "theme", "block-theme", "fse", "web-design"],
        "expertise": [
            "theme.json: tokens (color/tipografía/espaciado), patterns y template parts "
            "reutilizables.",
            "Block/FSE: plantillas (front-page, single, archive, 404), patterns de "
            "secciones, editor coherente con el front.",
            "Editable por el usuario final sin tocar código; demo content importable.",
            "Cumple estándares de ThemeForest (docs, i18n, escape/sanitize, sin errores PHP).",
            "Responsive + WCAG AA + Lighthouse alto.",
        ],
    },
    {
        "name": "shopify-theme-designer",
        "title": "Shopify Theme Designer",
        "desc": "Diseño de themes Shopify (Online Store 2.0 / Liquid / Hydrogen) con "
                "sections, presets y alto Lighthouse.",
        "tags": ["shopify", "liquid", "hydrogen", "theme", "ecommerce", "web-design"],
        "expertise": [
            "Sections everywhere: bloques y presets configurables desde el editor, "
            "settings_schema con tokens de marca.",
            "Plantillas home/collection/product/cart con buena UX de compra.",
            "Lighthouse mobile alto (top themes 90+), accesibilidad 90+, theme-check limpio.",
            "i18n (locales/*.json, sin texto hardcoded), multilocale.",
            "Compatibilidad con apps top (reseñas, email) vía placeholders.",
        ],
    },
]


_TEMPLATE = """---
name: {name}
description: "{desc}"
version: {version}
platforms: [linux, macos, windows]
metadata:
  hermes:
    category: themeforge
    tags: [{tags}]
    related_skills: [themeforge-operator]
---

# {title}

## When to use
{desc} Use this agent (alone or combined) when a ThemeForge mission needs this
specialty. It runs **inside the ThemeForge pipeline** — defer to the
`themeforge-operator` skill for create_project → build → QA → security audit →
package, and contribute your expertise to the build prompts and reviews.

## Expertise
{expertise}

## How you work
- Read the project's `AGENTS.md` (incl. the installed autoskills/UI-UX-Pro skills)
  and `.hermes.md`, and follow them.
- For imagery, use `mcp_themeforge_generate_image` (Runware) with a model fit for the
  asset (see `mcp_themeforge_list_image_models`). For research, use web_search/browser.
- Build MULTIPAGE, with complete realistic demo data and real images — never a generic
  scaffold. Feed concrete, specific instructions into `run_agent_build`.

## Verification
- Envato/ThemeForest checklist (§B), Lighthouse ≥ 90 (or stack target), WCAG AA.
- Visual QA: screenshot the preview and critique it like a senior designer; fix.
- Security & compliance audit passes before packaging.
"""


def _render(agent: dict) -> str:
    tags = ", ".join(agent["tags"])
    expertise = "\n".join(f"- {e}" for e in agent["expertise"])
    return _TEMPLATE.format(
        name=agent["name"], title=agent["title"], desc=agent["desc"],
        version=VERSION, tags=tags, expertise=expertise)


def _installed_version(md: Path) -> tuple[int, ...]:
    try:
        for ln in md.read_text(encoding="utf-8").splitlines():
            if ln.strip().startswith("version:"):
                v = ln.split(":", 1)[1].strip().strip("\"'")
                return tuple(int(x) for x in v.split(".") if x.isdigit()) or (0,)
    except Exception:
        pass
    return (0,)


def web_agent_names() -> list[str]:
    return [a["name"] for a in WEB_AGENTS]


def seed_web_agents(force: bool = False) -> list[str]:
    """Escribe los agentes web en ~/.hermes/skills/themeforge/<name>/SKILL.md.
    Idempotente: salta si ya existe a igual/mayor versión y no es user_modified.
    Devuelve los nombres efectivamente escritos."""
    cur = tuple(int(x) for x in VERSION.split("."))
    written: list[str] = []
    for agent in WEB_AGENTS:
        dest = TF_SKILLS_DIR / agent["name"] / "SKILL.md"
        if dest.is_file() and not force:
            try:
                if "user_modified: true" in dest.read_text(encoding="utf-8"):
                    continue
            except Exception:
                pass
            if _installed_version(dest) >= cur:
                continue
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(_render(agent), encoding="utf-8")
            written.append(agent["name"])
        except Exception:
            pass
    return written


if __name__ == "__main__":
    done = seed_web_agents()
    print("  ✓ agentes web sembrados: " + (", ".join(done) if done else "(ya al día)"))
