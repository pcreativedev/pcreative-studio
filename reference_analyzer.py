"""
reference_analyzer — analiza una carpeta/zip de referencia, recoge datos
objetivos del stack y prepara un prompt para que la IA (Claude/Codex)
recomiende qué stack moderno usar al reimplementar.

Uso típico desde ThemeForge:

    facts = gather_facts(Path("/ruta/al/template"))
    prompt = build_prompt(facts)
    # async via QProcess: claude --print  <  prompt
"""
from __future__ import annotations

import json
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any

from preview import detect_subprojects, detect_preview_profile


# ─── extracción de facts por sub-proyecto ───────────────────────────────


def _read_json(p: Path) -> dict | None:
    try:
        return json.loads(p.read_text(errors="ignore", encoding="utf-8"))
    except Exception:
        return None


def _read_lines(p: Path, limit: int = 80) -> list[str]:
    try:
        return p.read_text(errors="ignore", encoding="utf-8").splitlines()[:limit]
    except Exception:
        return []


def _facts_for_node(path: Path) -> dict[str, Any]:
    pkg = _read_json(path / "package.json") or {}
    deps = {**(pkg.get("dependencies") or {}), **(pkg.get("devDependencies") or {})}
    scripts = pkg.get("scripts") or {}
    # Detectar el "framework principal"
    framework = None
    for k in ("next", "nuxt", "@angular/core", "@sveltejs/kit", "astro", "vite",
              "expo", "@ionic/react", "@ionic/angular", "remix", "gatsby"):
        if k in deps:
            framework = f"{k}@{deps[k]}"
            break
    return {
        "kind": "node",
        "framework": framework,
        "name": pkg.get("name"),
        "version": pkg.get("version"),
        "scripts_keys": sorted(scripts.keys()),
        "deps_summary": {k: v for k, v in deps.items()
                         if k in (
            "next", "nuxt", "react", "vue", "@angular/core", "astro",
            "@sveltejs/kit", "remix-run", "vite", "typescript", "tailwindcss",
            "@tailwindcss/vite", "drizzle-orm", "prisma", "@prisma/client",
            "postgres", "pg", "express", "fastify", "stripe", "@stripe/stripe-js",
            "expo", "react-native", "@ionic/react", "next-auth", "better-auth",
            "@nuxtjs/tailwindcss",
        )},
        "deps_count": len(deps),
    }


def _facts_for_laravel(path: Path) -> dict[str, Any]:
    composer = _read_json(path / "composer.json") or {}
    req = {**(composer.get("require") or {}), **(composer.get("require-dev") or {})}
    framework = None
    for k in ("laravel/framework", "laravel/laravel"):
        if k in req:
            framework = f"{k}@{req[k]}"
            break
    php_version = req.get("php", "?")
    return {
        "kind": "laravel",
        "framework": framework,
        "name": composer.get("name"),
        "php": php_version,
        "deps_summary": {k: v for k, v in req.items()
                         if k in (
            "laravel/framework", "laravel/sanctum", "laravel/jetstream",
            "laravel/breeze", "livewire/livewire", "filament/filament",
            "inertiajs/inertia-laravel", "spatie/laravel-permission",
            "laravel/cashier", "stripe/stripe-php", "laravel/pail",
        )},
        "deps_count": len(req),
    }


def _facts_for_flutter(path: Path) -> dict[str, Any]:
    pubspec = path / "pubspec.yaml"
    sdk = None
    deps_sample = []
    if pubspec.is_file():
        for line in _read_lines(pubspec, 60):
            m = re.match(r"\s*sdk:\s*(.+)", line)
            if m: sdk = m.group(1).strip()
            m = re.match(r"\s+([\w_]+):\s*(.+)", line)
            if m and m.group(1) not in ("flutter", "sdk"):
                deps_sample.append(f"{m.group(1)}: {m.group(2).strip()}")
                if len(deps_sample) >= 15: break
    return {
        "kind": "flutter",
        "framework": "flutter",
        "sdk": sdk,
        "deps_sample": deps_sample,
    }


def _facts_for_wordpress(path: Path) -> dict[str, Any] | None:
    """Detecta y extrae facts de un plugin/theme WordPress.
    Devuelve None si no es WordPress."""
    plugin_php = None
    plugin_meta: dict[str, str] = {}
    # ── Plugin: cualquier .php raíz con header `Plugin Name:` ───────
    try:
        for php in path.glob("*.php"):
            try:
                head = php.read_text(errors="ignore", encoding="utf-8")[:3000]
                if "Plugin Name:" in head:
                    plugin_php = php.name
                    # Extraer cabeceras estándar de plugin
                    for key in ("Plugin Name", "Description", "Version", "Author",
                                "Requires at least", "Requires PHP", "License",
                                "Text Domain", "Plugin URI"):
                        m = re.search(rf"^\s*\*?\s*{re.escape(key)}:\s*(.+)$",
                                      head, re.MULTILINE)
                        if m:
                            plugin_meta[key] = m.group(1).strip()
                    break
            except Exception:
                continue
    except Exception:
        pass

    # ── Theme: style.css con header `Theme Name:` ───────────────────
    theme_meta: dict[str, str] = {}
    style_css = path / "style.css"
    if style_css.is_file():
        try:
            head = style_css.read_text(errors="ignore", encoding="utf-8")[:3000]
            if "Theme Name:" in head:
                for key in ("Theme Name", "Description", "Version", "Author",
                            "Requires at least", "Requires PHP", "License",
                            "Text Domain", "Theme URI", "Tags"):
                    m = re.search(rf"^\s*{re.escape(key)}:\s*(.+)$",
                                  head, re.MULTILINE)
                    if m:
                        theme_meta[key] = m.group(1).strip()
        except Exception:
            pass

    if not plugin_php and not theme_meta:
        return None

    # ── Composer/Node deps si las hay ────────────────────────────────
    composer_deps: dict[str, str] = {}
    composer = _read_json(path / "composer.json")
    if composer:
        composer_deps = {**(composer.get("require") or {}),
                         **(composer.get("require-dev") or {})}
    node_facts = None
    if (path / "package.json").is_file():
        node_facts = _facts_for_node(path)

    # ── Estructura: tablas custom vs CPTs ────────────────────────────
    # Heurística rápida: buscar dbDelta / register_post_type en PHP
    uses_custom_tables = False
    uses_cpts = False
    uses_freemius = False
    try:
        for php in list(path.rglob("*.php"))[:200]:
            try:
                txt = php.read_text(errors="ignore", encoding="utf-8")
                if "dbDelta" in txt or "$wpdb->prefix" in txt:
                    uses_custom_tables = True
                if "register_post_type" in txt:
                    uses_cpts = True
                if "freemius" in txt.lower() or "fs_dynamic_init" in txt:
                    uses_freemius = True
                if uses_custom_tables and uses_cpts and uses_freemius:
                    break
            except Exception:
                continue
    except Exception:
        pass

    # readme.txt (WordPress.org style)
    has_readme_txt = (path / "readme.txt").is_file()
    # Block theme markers
    is_block_theme = bool(theme_meta) and (path / "theme.json").is_file()

    is_plugin = bool(plugin_php)
    return {
        "kind": "wordpress-plugin" if is_plugin else "wordpress-theme",
        "main_file": plugin_php if is_plugin else "style.css",
        "headers": plugin_meta if is_plugin else theme_meta,
        "block_theme": is_block_theme,
        "has_wp_org_readme": has_readme_txt,
        "uses_custom_tables": uses_custom_tables,
        "uses_cpts": uses_cpts,
        "uses_freemius": uses_freemius,
        "composer_deps_count": len(composer_deps),
        "composer_deps_summary": {k: v for k, v in composer_deps.items()
                                  if k.startswith(("symfony/", "illuminate/",
                                                   "guzzlehttp/", "stripe/",
                                                   "monolog/", "psr/",
                                                   "wp-coding-standards/",
                                                   "wpfluent/", "pestphp/",
                                                   "phpunit/", "freemius/"))},
        "node": node_facts,
    }


def _facts_for_subproject(path: Path) -> dict[str, Any]:
    # WordPress primero (plugins/themes son específicos)
    wp = _facts_for_wordpress(path)
    if wp is not None:
        return wp
    # Laravel (puede tener package.json también, para Vite frontend)
    if (path / "artisan").is_file() and (path / "composer.json").is_file():
        out = _facts_for_laravel(path)
        # Si además hay package.json, anexa info del frontend
        if (path / "package.json").is_file():
            out["frontend"] = _facts_for_node(path)
        return out
    if (path / "package.json").is_file():
        return _facts_for_node(path)
    if (path / "pubspec.yaml").is_file():
        return _facts_for_flutter(path)
    return {"kind": "unknown"}


# ─── gather_facts ────────────────────────────────────────────────────────


def _is_design_export(path: Path) -> bool:
    """Detecta carpetas tipo export de claude.ai/design, v0.dev, Figma
    Make, etc.: HTML/JSX/TSX/CSS pero SIN build system real (package.json,
    composer.json, pubspec.yaml, artisan…) en NINGUNA sub-carpeta hasta
    profundidad 7.

    También descarta señales típicas de producto comercial empaquetado
    (Envato/CodeCanyon/ThemeForest): nombre de carpeta que contiene
    "codecanyon" / "themeforest" / "envato", carpetas `Documentation/`,
    `Files/`, `Updates/`, archivos `licensing.txt`, README mencionando
    "Envato", múltiples sub-stacks anidados. El check de carpetas y
    READMEs se hace recursivamente hasta profundidad 4 para tolerar
    wrappers tipo `OvoRide v2.0/codecanyon-XXXXX/{Documentation, Files,
    Updates}`.
    """
    # 0. Nombre de la carpeta (o cualquier ancestro hasta profundidad 4)
    # contiene marcador de marketplace
    marketplace_kw = ("codecanyon", "themeforest", "envato",
                      "creative-market", "creativemarket", "themeforest")
    name_lower = path.name.lower()
    if any(kw in name_lower for kw in marketplace_kw):
        return False
    try:
        for d in path.rglob("*"):
            parts = d.relative_to(path).parts
            if len(parts) > 3:
                continue
            if d.is_dir() and any(kw in d.name.lower() for kw in marketplace_kw):
                return False
    except Exception:
        pass

    # 1. Marcadores de build system en cualquier sub-carpeta (≤7 niveles
    # para tolerar wrappers: padre/zip-wrapper/Files/<Stack>/core/<bm>)
    build_markers = (
        "package.json", "composer.json", "pubspec.yaml", "artisan",
        "Cargo.toml", "go.mod", "pyproject.toml", "requirements.txt",
        "Gemfile", "build.gradle", "build.gradle.kts", "pom.xml",
        "Package.swift", "CMakeLists.txt",
    )
    try:
        for f in path.rglob("*"):
            parts = f.relative_to(path).parts
            if len(parts) > 7:
                continue
            if any(p in {"node_modules", "vendor", ".git", "build", "dist"} for p in parts):
                continue
            if f.is_file() and f.name in build_markers:
                return False
    except Exception:
        pass

    # 2. Señales de producto comercial empaquetado (Envato-style) en
    # cualquier sub-carpeta hasta profundidad 4
    commercial_dir_markers = {
        "Documentation", "documentation", "Files", "Updates",
        "Theme Documentation",
    }
    commercial_file_markers = {
        "licensing.txt", "LICENSE-Envato.txt",
    }
    try:
        for entry in path.rglob("*"):
            parts = entry.relative_to(path).parts
            if len(parts) > 4:
                continue
            if entry.is_dir() and entry.name in commercial_dir_markers:
                return False
            if entry.is_file() and entry.name in commercial_file_markers:
                return False
    except Exception:
        pass

    # 3. Texto del README sugiere producto comercial — buscado hasta
    # profundidad 3 para tolerar wrappers
    readme_kw = (
        "envato", "codecanyon", "themeforest", "creative market",
        "regular license", "extended license", "purchase code",
        "buy now", "item support",
    )
    try:
        for entry in path.rglob("*"):
            parts = entry.relative_to(path).parts
            if len(parts) > 3:
                continue
            if not entry.is_file():
                continue
            if entry.name.lower() not in {
                "readme.md", "readme.txt", "readme", "license.txt",
                "license.md",
            }:
                continue
            try:
                txt = entry.read_text(errors="ignore", encoding="utf-8")[:3000].lower()
                if any(k in txt for k in readme_kw):
                    return False
            except Exception:
                pass
    except Exception:
        pass

    # 4. Debe haber archivos UI sin build → entonces SÍ es design export
    design_exts = (".html", ".htm", ".jsx", ".tsx", ".vue", ".svelte", ".css", ".scss")
    try:
        for f in path.rglob("*"):
            if f.is_file() and f.suffix.lower() in design_exts:
                return True
    except Exception:
        pass
    return False


def _scan_design_export(path: Path) -> dict[str, Any]:
    """Recoge metadata útil de un design export para que la IA pueda
    sugerir stack: tipos de archivo, número, primera muestra de HTML/JSX
    para ver libs implícitas (Tailwind classes, React hooks, etc.)."""
    counts: dict[str, int] = {}
    samples: dict[str, str] = {}
    total_files = 0
    target_exts = (".html", ".jsx", ".tsx", ".vue", ".svelte", ".css", ".scss", ".js", ".ts", ".json", ".md")
    try:
        for f in sorted(path.rglob("*")):
            if not f.is_file(): continue
            ext = f.suffix.lower()
            if ext in target_exts:
                counts[ext] = counts.get(ext, 0) + 1
                total_files += 1
                # Guardar una muestra de los primeros 800 chars de archivos clave
                if ext in (".html", ".jsx", ".tsx", ".vue") and ext not in samples and f.stat().st_size < 200_000:
                    try:
                        samples[ext] = f.read_text(errors="ignore", encoding="utf-8")[:800]
                    except Exception:
                        pass
    except Exception:
        pass

    # Detectar features rápidamente en los samples (Tailwind, React, etc.)
    text_combined = "\n".join(samples.values())
    features = []
    if "class=" in text_combined or "className=" in text_combined:
        features.append("html/jsx con clases")
    if any(kw in text_combined for kw in (" flex ", " grid ", "text-", "bg-", "rounded-")):
        features.append("Tailwind utilities detectadas")
    if "useState" in text_combined or "useEffect" in text_combined:
        features.append("React hooks")
    if "<template>" in text_combined or "v-if=" in text_combined:
        features.append("Vue SFC")
    if "<script setup" in text_combined:
        features.append("Vue 3 script setup")
    if "{#if" in text_combined or "$state" in text_combined:
        features.append("Svelte")
    if "html5doctype" in text_combined.lower() or "<!doctype html>" in text_combined.lower():
        features.append("HTML5 estático")
    return {
        "total_files": total_files,
        "extension_counts": counts,
        "features_detected": features,
        "samples": {ext: (samples[ext][:400] + "…") for ext in samples},
    }


def gather_facts(path: Path) -> dict[str, Any]:
    """Recolecta facts del path de referencia. Soporta:
      - carpeta directamente
      - .zip (se mira sin descomprimir)
      - design-export (HTML/JSX/CSS sin package.json, p.ej. claude.ai/design,
        v0.dev, Figma Make)
    """
    if path.is_file() and path.suffix.lower() == ".zip":
        return _gather_from_zip(path)
    if not path.is_dir():
        return {"error": f"No es carpeta ni zip: {path}"}

    # ¿Es un design-export?
    if _is_design_export(path):
        return {
            "kind": "design-export",
            "root": str(path),
            "hint": "código de diseño sin build system — necesita stack moderno asignado",
            **_scan_design_export(path),
        }

    # ¿Mono-repo o proyecto único?
    subs = detect_subprojects(path)
    if subs:
        # Mono-repo
        out: dict[str, Any] = {
            "kind": "mono-repo",
            "root": str(path),
            "subprojects": [],
        }
        for s in subs:
            p = s.get("profile")
            sub_facts = _facts_for_subproject(s["path"])
            out["subprojects"].append({
                "name": s["name"],
                "rel_path": s.get("rel_path"),
                "preview_profile": p["name"] if p else None,
                "default_port": p.get("default_port") if p else None,
                **sub_facts,
            })
        return out

    # Proyecto único
    profile = detect_preview_profile(path)
    facts = _facts_for_subproject(path)
    return {
        "kind": "single",
        "root": str(path),
        "preview_profile": profile["name"] if profile else None,
        "default_port": profile.get("default_port") if profile else None,
        **facts,
    }


def _gather_from_zip(zip_path: Path) -> dict[str, Any]:
    """Lectura ligera del zip sin descomprimirlo."""
    out: dict[str, Any] = {
        "kind": "zip",
        "root": str(zip_path),
        "size_mb": round(zip_path.stat().st_size / 1024 / 1024, 1),
    }
    try:
        with zipfile.ZipFile(zip_path) as z:
            names = z.namelist()
            out["entries"] = len(names)
            # Buscar package.json / composer.json / pubspec.yaml en cualquier sitio
            markers = {
                "package.json": [],
                "composer.json": [],
                "pubspec.yaml": [],
                "artisan": [],
                "drizzle.config.ts": [],
            }
            for n in names:
                base = n.rsplit("/", 1)[-1]
                if base in markers:
                    markers[base].append(n)
            out["markers"] = {k: v[:5] for k, v in markers.items() if v}
            # Leer el primer package.json para tener una idea
            for pkg_name in markers.get("package.json", [])[:3]:
                try:
                    with z.open(pkg_name) as f:
                        data = json.loads(f.read())
                        out.setdefault("package_jsons", []).append({
                            "path": pkg_name,
                            "name": data.get("name"),
                            "scripts": list((data.get("scripts") or {}).keys()),
                            "deps_count": len((data.get("dependencies") or {}))
                                          + len((data.get("devDependencies") or {})),
                        })
                except Exception:
                    pass
    except Exception as e:
        out["error"] = str(e)
    return out


# ─── prompt generation ──────────────────────────────────────────────────


def build_prompt(facts: dict[str, Any], target: str = "gumroad+web") -> str:
    """Genera un prompt en español para Claude/Codex que pida:
      - análisis técnico del stack + recomendación moderna,
      - análisis de mercado del nicho (saturación, top sellers, pricing),
      - estrategia de venta para Gumroad + web propia.

    Pide explícitamente usar WebSearch/WebFetch antes de responder para
    tener datos reales de 2026 (no solo el knowledge cutoff del modelo).
    """
    facts_json = json.dumps(facts, indent=2, ensure_ascii=False)

    # Si es un design-export (claude.ai/design, v0.dev, Figma Make), el
    # prompt es DISTINTO: el objetivo no es "estudiar y reimplementar"
    # sino "asignar stack moderno y migrar este código de diseño a un
    # proyecto real". No hay análisis de mercado de competencia porque
    # el código original NO es producto vendido por nadie — es tu propio
    # diseño exportado.
    if facts.get("kind") == "design-export":
        return f"""ThemeForge ha clasificado el contenido de `{facts.get("root", "?")}`
como un **export de diseño** (estilo claude.ai/design, v0.dev, Figma Make):
HTML/JSX/CSS sin build system, sin marcadores de producto comercial
detectables. La asunción de trabajo es que **es diseño tuyo** (no código
ajeno) y por tanto se puede usar libremente como punto de partida del
producto real.

El export es **HTML/JSX/CSS sin build system** — necesito que me ayudes
a elegir el stack moderno con el que voy a construir el producto real,
y a planificar cómo integrar este diseño como punto de partida.

## ⚠️ Usa WebSearch antes de recomendar

Tienes habilitadas las tools **WebSearch** y **WebFetch**. USALAS para:

1. **Última versión estable en 2026** de los frameworks candidatos
   (Next, Nuxt, Astro, Vite+React, SvelteKit, etc.).
2. **Cuál encaja mejor según los features detectados** en el export
   (Tailwind, React hooks, Vue SFC, HTML5 estático, etc.).
3. **Tendencias 2026** en stacks para landings/apps/dashboards/etc.
   según el tipo de UI que parece ser el export.

Cita versiones exactas verificadas con WebSearch.

## Facts del design export

```json
{facts_json}
```

## Lo que necesito de ti (responde en este orden)

### 0. Sanity check ⚠️
ANTES de aceptar la premisa, mira tú mismo el directorio. Si detectas
cualquiera de estas señales **PARA EL TRABAJO** y avisa al usuario en
vez de seguir el guion:

- Nombre del producto o de la carpeta menciona un marketplace
  (CodeCanyon / ThemeForest / Envato / Creative Market / Lemon Squeezy /
  Gumroad) o tiene un código numérico tipo "55665868".
- Archivos `licensing.txt`, `LICENSE-Envato.txt`, `Theme Documentation`,
  `Documentation/`, `Updates/`, etc.
- README/docs mencionan "Regular License", "Extended License",
  "purchase code", "buyer", "buy now", autor distinto al usuario.
- Estructura multi-stack profesional anidada (`Files/<Stack>/`,
  app móvil + backend + admin web junto).

En cualquiera de esos casos NO sigas con este prompt: detente y dile al
usuario textualmente que parece producto comercial, lista las señales,
y pídele que confirme su situación (autor original / licencia para
forkear / quiere ayuda con deploy / quiere reimplementar usando esto
solo como inspiración).

Si NO hay señales de producto comercial, empieza con esta frase exacta
en bold:

> **"Export de diseño asumido como propio. Recomendaré stack moderno
> para construir el producto sobre este diseño, sin restricciones de
> copia. Si esto NO es diseño propio, páreme aquí antes de seguir."**

### 1. ¿Qué hay aquí?
Una frase: ¿qué tipo de UI es? (landing, dashboard admin, app móvil web,
ecommerce, blog, formulario…) y qué señales viste en los features
detectados.

### 2. Stack recomendado para construir el producto
1 stack principal + 2 alternativas. Para cada uno:
- Framework principal con versión 2026 verificada.
- Sistema de estilos (Tailwind 4 si las clases lo sugieren, etc.).
- ORM/auth/pagos sugerido SI hace falta (no todos los diseños lo
  necesitan).
- 2-3 líneas de justificación con foco en por qué encaja con LO QUE
  YA HAS DISEÑADO (no en lo que se vende en marketplaces).

### 3. Plan de migración del diseño al stack
Pasos concretos (5-8) para integrar el export en el scaffold del stack
recomendado:
- Qué archivos del export se convierten en componentes del nuevo stack.
- Qué partes del HTML se vuelven páginas/rutas/layouts.
- Qué assets se mueven a public/.
- Si hay JS inline, cómo se reescribe en el framework elegido.
- Cómo preservar el look exacto sin romper la implementación final.

### 4. Mejoras sugeridas
Cosas que claude.ai/design suele dejar a medias y que ahora puedes
arreglar al construir el producto real:
- Responsive completo si solo tiene breakpoints básicos.
- a11y / WCAG.
- Estados (hover, focus, active, disabled, loading, error).
- Dark mode si no estaba.
- Integraciones reales (auth, BD, pagos).

### 5. Fuentes
URLs principales consultadas con WebSearch.

Sé directo, técnico, en español. No formules con disclaimer.
"""

    kind = facts.get("kind")
    if kind in ("wordpress-theme", "wordpress-plugin"):
        _wp_what = "theme" if kind == "wordpress-theme" else "plugin"
        wp_constraint = (
            "\n## ⚠️ La referencia es WordPress — recomienda SOLO WordPress\n\n"
            f"ThemeForge ha detectado que la referencia es un **{_wp_what} de WordPress** "
            "y el producto se construirá y venderá COMO WordPress. Por tanto:\n\n"
            "- Recomienda **EXCLUSIVAMENTE** enfoques WordPress: **block theme (FSE)**, "
            "**classic/hybrid theme**, o basado en page-builder si la referencia lo usa "
            "(Elementor, WPBakery, etc.). Para plugins, arquitectura de plugin WP estándar.\n"
            "- **NO** propongas Astro, Next, Nuxt, Vite, Laravel ni ningún stack que NO sea "
            "WordPress — aquí no son una opción.\n"
            "- El checklist Envato aplicable es el de **ThemeForest WordPress** (Theme Check, "
            "estándares WP), no Site Template estático ni CodeCanyon script.\n"
            "- Da 1 recomendación principal + 2 variantes, **todas dentro de WordPress** "
            "(p.ej. FSE puro vs híbrido classic+blocks vs page-builder).\n"
        )
    else:
        wp_constraint = ""

    return f"""Soy desarrollador y quiero usar este template como **REFERENCIA para
estudiar funcionalidades**, NO como código a copiar.
{wp_constraint}
## ⚠️ Pre-acuerdo — la licencia NO es objeto del análisis

Estás en el modo **"recrear"** de ThemeForge. Al elegir este modo el
usuario YA HA DECLARADO y aceptado lo siguiente — **no requiere
confirmación tuya** y **no es parte del análisis**:

- El template puede ser un producto comercial de terceros (de
  CodeCanyon / ThemeForest / Creative Market / GitHub privado /
  lo que sea). Eso es lo esperable.
- El template se usa SOLO como referencia conceptual de features y UX.
- TODO se reimplementa desde cero con código propio, branding propio
  y assets propios (Unsplash, Pexels, Heroicons).
- NO se redistribuye el template original.
- La discusión de "tienes licencia para esto" es ajena a este análisis;
  el usuario asume la responsabilidad legal de cómo obtuvo la
  referencia. Tu análisis se limita a lo TÉCNICO y de mercado.

**Por tanto:**

- ✅ SÍ debes identificar qué es el template (nombre, autor si lo ves)
  como información para el usuario.
- ❌ NO debes pedir confirmación sobre la licencia.
- ❌ NO debes preguntar "¿lo compraste?", "¿eres el autor?", "¿es
  legal?". Eso ya está fuera del alcance.
- ❌ NO debes ofrecer "ayudarte con el deploy del producto tal cual" —
  ese NO es el modo "recrear".

Solo pararte y pedir aclaración si detectas contenido manifiestamente
ilegal (CSAM, malware activo, datos personales de terceros). En
cualquier OTRO caso, procede al análisis.

## 🚨 Regla anti-copia (operativa para tu análisis)

Bajo NINGÚN concepto el análisis sugiere copiar ni reutilizar del
template:

- ❌ NADA de código fuente (HTML, CSS, JS, TS, PHP, Dart…).
- ❌ NADA de assets propietarios (imágenes, iconos, fuentes con licencia
   restrictiva, datos de demo).
- ❌ NADA de copy textual ni branding (nombres, eslóganes, logos).
- ❌ NADA de configuración propietaria (claves API, IDs de Stripe ajenos,
   webhooks de cuentas que no son mías).

✅ **Solo se copian IDEAS**: qué features tiene, cómo está estructurada
la UI, qué flujos de usuario plantea, qué integraciones, qué problemas
resuelve. Todo eso lo reimplemento desde cero con mi propio código,
mi propio branding y mis propios assets.

Cuando recomiendas stack o funcionalidades, asume que voy a
REIMPLEMENTAR desde cero con ese stack — NO sugieras "fork del template"
ni "modifica este archivo" ni "reusa este componente". Sugiere
"construye con X stack inspirado en las funcionalidades de Y".

---

**Canales de venta**: NO voy a vender en ThemeForest/CodeCanyon.
Mi modelo es:

  · **Gumroad** (canal principal)
  · **Mi propia web** (canal secundario, con su pasarela Stripe)

Pero quiero saber qué se está vendiendo en TODOS los marketplaces
relevantes (ThemeForest, CodeCanyon, Creative Market, Gumroad, Lemon
Squeezy, Mintlify Themes, etc.) para entender qué nichos están de moda,
qué stacks dominan y dónde hay saturación que evitar.

## ⚠️ Importante: usa WebSearch antes de responder

Tienes habilitadas las tools **WebSearch** y **WebFetch**. USALAS:

### Búsquedas técnicas (para la recomendación de stack)
1. Última versión estable en 2026 de los frameworks que detectes en
   los facts (next, laravel, nuxt, flutter, react native, tailwind, etc.).
2. Breaking changes recientes que aplican al template original.

### Búsquedas de mercado (para análisis de nicho)
3. **Top sellers del nicho** en cada marketplace:
   - `gumroad best selling [nicho] 2026`
   - `themeforest top admin templates 2026`
   - `codecanyon top [nicho] templates 2026`
   - `creative market top [nicho]`
   - `lemonsqueezy top [nicho] 2026`
4. **Saturación**: cuántos productos hay del mismo nicho, qué los
   diferencia, qué reseñas/quejas tienen los líderes.
5. **Pricing observado**: rangos típicos en Gumroad vs marketplaces
   gestionados (los precios suelen ser MUY distintos).
6. **Tendencias 2026**: qué nichos están en alza vs en declive.

Cita versiones, URLs y números exactos que encontraste. No inventes.

## Facts objetivos del template de referencia

```json
{facts_json}
```

## Lo que necesito de ti (responde en este orden, breve y directo)

### 0. Confirmación de la regla anti-copia ⚠️
Empieza tu respuesta con esta frase EXACTA en bold para que quede claro:

> **"Análisis exclusivo de referencia. Las recomendaciones asumen
> reimplementación desde cero con código propio; no se copia código,
> assets ni branding del template original."**

Sin esa frase al inicio el análisis es inválido.

### 1. ¿Qué hay aquí?
Una frase resumiendo qué tipo de producto es (admin, ecommerce, delivery
multivendor, dashboard, landing, etc.) y la arquitectura (mono-repo, single,
sub-piezas).

### 2. Estado del stack actual
Para cada pieza: versión que tiene, si es **moderna / mantenible /
obsoleta** en 2026. Cita la versión actual estable que encontraste con
WebSearch para comparar.

### 3. Stack recomendado para reimplementar
Stack CONCRETO en 2026 con versiones exactas verificadas en tu búsqueda.
Da 1 principal y 1-2 alternativas. Para cada uno: 2-3 líneas + versión +
por qué encaja con lo que se vende AHORA en los marketplaces que has visto.

### 4. Análisis de mercado del nicho 🆕
- **¿Se vende este nicho?** Sí/no/moderado y datos que lo respalden.
- **Saturación**: ¿el mercado está lleno o hay hueco? Cita 3-5 productos
  líderes en distintas plataformas, con sus precios y nº de ventas si
  está visible.
- **Diferenciadores observados**: qué hace que un producto destaque vs
  los demás en este nicho (features, UI, branding, integraciones).
- **Reseñas/quejas recurrentes** en los top sellers — son las
  oportunidades para diferenciarte.
- **Nichos adyacentes** que están en alza y podrías abordar antes.

### 5. Estrategia de venta (Gumroad + web propia) 🆕
- **Precio sugerido** para Gumroad — basado en lo que cobran tus
  competidores en esa plataforma.
- **Precio sugerido para tu web** — Gumroad suele ser low-cost
  (29-99€), tu web puede ir más alto con valor añadido
  (soporte, actualizaciones, demo en vivo).
- **3-5 ángulos diferenciadores** concretos basados en gaps del mercado.
- **Plataformas secundarias** opcionales (Lemon Squeezy, Polar, etc.)
  que podrían interesar más adelante.

### 6. Riesgos / cuidado
- "Trampas" técnicas del template (deps muertos, licencias raras, etc.).
- Riesgos comerciales: ¿el nicho está pivotando? ¿hay regulación nueva
  que afecta? ¿alguna lib core va a desaparecer?

### 7. Veredicto en una línea
Si vale la pena reimplementar este template para Gumroad+web, o si es
mejor pivotar hacia un nicho adyacente menos saturado que viste.

### 8. Fuentes
Lista las 5-8 URLs principales que consultaste, agrupadas:
- Versiones de frameworks.
- Top sellers del nicho en distintos marketplaces.
- Pricing observado.

Sé directo, técnico, en español. No formules con disclaimer.
"""


# ─── CLI (debug) ────────────────────────────────────────────────────────


if __name__ == "__main__":
    import sys
    p = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    facts = gather_facts(p)
    print(json.dumps(facts, indent=2, ensure_ascii=False))
    print("\n" + "=" * 70 + "\nPROMPT GENERADO:\n" + "=" * 70 + "\n")
    print(build_prompt(facts))
