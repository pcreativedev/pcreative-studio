"""
preflight.py — checks de "¿listo para marketplace?" para un proyecto.

Inspirado por `context/REQUISITOS-THEMEFOREST.md` + buenas prácticas
genéricas. Corre sobre el directorio del proyecto y devuelve una lista
de resultados que la UI renderiza con iconos pass/warn/fail/info.

Diseñado para ser:
  · Rápido: solo filesystem + grep, sin herramientas externas por
    defecto.
  · Amigable: cada check explica cómo arreglar el problema.
  · Extensible: cada check es una función top-level que devuelve un
    Check; añadir nuevos es trivial.

Tools externos (Lighthouse, W3C validator) se gating: solo corren si
el binario está en PATH, y fallan suave si no lo está.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


# Niveles de resultado por orden de severidad
LEVEL_PASS = "pass"   # ✓ OK
LEVEL_WARN = "warn"   # ⚠ aviso, no bloqueante
LEVEL_FAIL = "fail"   # ✗ no pasa requisito (rechazo de marketplace)
LEVEL_INFO = "info"   # ℹ informativo / skip

LEVEL_ICONS = {
    LEVEL_PASS: "✓",
    LEVEL_WARN: "⚠",
    LEVEL_FAIL: "✗",
    LEVEL_INFO: "ℹ",
}


@dataclass
class Check:
    id: str
    title: str
    level: str  # LEVEL_PASS / LEVEL_WARN / LEVEL_FAIL / LEVEL_INFO
    message: str
    hint: str = ""  # cómo arreglar
    details: list[str] = field(default_factory=list)


# ── Helpers internos ──────────────────────────────────────────────────


_IGNORE_DIRS = {
    "node_modules", ".git", ".next", ".nuxt", "out", "dist", "build",
    "vendor", "target", ".venv", "venv", "__pycache__", ".cache",
    "screenshots", "documentation", "source", ".turbo",
}


def _walk_source(project_path: Path):
    """Iterar archivos del proyecto, saltando dirs ruidosos."""
    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in _IGNORE_DIRS and not d.startswith(".")]
        for f in files:
            yield Path(root) / f


def _grep_any(project_path: Path, patterns: tuple[str, ...],
              extensions: tuple[str, ...]) -> list[tuple[Path, str]]:
    """Devuelve [(file_path, matched_line)] para cada coincidencia."""
    hits: list[tuple[Path, str]] = []
    pat = re.compile("|".join(patterns), re.IGNORECASE)
    for fp in _walk_source(project_path):
        if not fp.suffix.lower() in extensions:
            continue
        try:
            text = fp.read_text(errors="ignore", encoding="utf-8")
        except Exception:
            continue
        for line in text.splitlines():
            if pat.search(line):
                hits.append((fp, line.strip()[:200]))
                break  # un hit por archivo basta para la métrica
    return hits


def _has_file(project_path: Path, *names: str) -> Path | None:
    """Primera coincidencia case-sensitive en raíz."""
    for n in names:
        p = project_path / n
        if p.exists():
            return p
    return None


# ── Checks individuales ──────────────────────────────────────────────


def check_readme(project_path: Path) -> Check:
    if _has_file(project_path, "README.md", "README.txt", "README", "Readme.md"):
        return Check("readme", "README presente", LEVEL_PASS,
                     "Hay README en la raíz del proyecto.")
    return Check(
        "readme", "README presente", LEVEL_FAIL,
        "No se encontró README en la raíz.",
        hint="Crea un README.md con descripción, features, requisitos y "
             "uso. Es lo primero que ve un comprador.",
    )


def check_license_or_licensing(project_path: Path) -> Check:
    p = _has_file(project_path, "LICENSE", "LICENSE.md", "licensing.txt",
                  "LICENSE.txt", "license.txt")
    if p:
        return Check("license", "LICENSE / licensing.txt", LEVEL_PASS,
                     f"Encontrado: {p.name}")
    return Check(
        "license", "LICENSE / licensing.txt", LEVEL_WARN,
        "No hay LICENSE ni licensing.txt en la raíz.",
        hint="Envato requiere `licensing.txt` con la lista de assets de "
             "terceros y sus licencias. Para canales propios "
             "(Gumroad/web) basta con un LICENSE.md describiendo el "
             "uso permitido.",
    )


def check_documentation(project_path: Path) -> Check:
    docs = project_path / "documentation"
    if not docs.is_dir():
        return Check(
            "docs", "documentation/ HTML", LEVEL_WARN,
            "No existe la carpeta `documentation/`.",
            hint="Envato exige documentación HTML estática "
                 "(documentation/index.html). Para Gumroad es "
                 "recomendable. Genérala con tu herramienta favorita.",
        )
    has_index = (docs / "index.html").is_file()
    n_files = sum(1 for _ in docs.rglob("*") if _.is_file())
    if has_index and n_files > 1:
        return Check("docs", "documentation/ HTML", LEVEL_PASS,
                     f"documentation/ con {n_files} archivos y index.html.")
    if not has_index:
        return Check(
            "docs", "documentation/ HTML", LEVEL_WARN,
            "documentation/ existe pero falta index.html.",
            hint="Envato espera abrir `documentation/index.html` como "
                 "entrada principal de las docs.",
        )
    return Check("docs", "documentation/ HTML", LEVEL_WARN,
                 f"documentation/ con solo {n_files} archivo(s).",
                 hint="Añade más contenido: getting-started, "
                      "customization, changelog, support.")


def check_screenshots(project_path: Path) -> Check:
    sh = project_path / "screenshots"
    if not sh.is_dir():
        return Check(
            "screenshots", "screenshots/", LEVEL_WARN,
            "No existe la carpeta `screenshots/`.",
            hint="Captura PNG/JPG de cada layout principal (≥1920x1200 "
                 "para Envato). Lánzalo con el botón 📸 del preview.",
        )
    imgs = [p for p in sh.iterdir()
            if p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
    if not imgs:
        return Check(
            "screenshots", "screenshots/", LEVEL_WARN,
            "screenshots/ existe pero está vacía.",
            hint="Captura PNG/JPG con el botón 📸 del preview.",
        )
    if len(imgs) < 3:
        return Check("screenshots", "screenshots/", LEVEL_WARN,
                     f"Solo {len(imgs)} capturas.",
                     hint="Envato recomienda 5+ screenshots de layouts "
                          "distintos (home, dashboard, blog, formulario…).")
    return Check("screenshots", "screenshots/", LEVEL_PASS,
                 f"{len(imgs)} capturas en screenshots/.")


def check_jquery_legacy(project_path: Path) -> Check:
    hits = _grep_any(
        project_path,
        (r"jquery[-_ ]1\.\d", r"jquery[-_ ]2\.\d", r"jquery.min.js.*1\.\d",),
        (".html", ".htm", ".php", ".liquid", ".vue", ".jsx", ".tsx", ".js", ".ts"),
    )
    if not hits:
        return Check("jquery-legacy", "Sin jQuery 1.x/2.x legacy",
                     LEVEL_PASS, "Sin referencias a jQuery legacy.")
    return Check(
        "jquery-legacy", "Sin jQuery 1.x/2.x legacy", LEVEL_FAIL,
        f"{len(hits)} archivos referencian jQuery legacy.",
        hint="Envato rechaza jQuery 1.x/2.x. Usa jQuery 3+ (si imprescindible) "
             "o reescribe en JS vanilla.",
        details=[f"{p.relative_to(project_path)}: {ln[:120]}" for p, ln in hits[:8]],
    )


def check_bootstrap_legacy(project_path: Path) -> Check:
    hits = _grep_any(
        project_path,
        (r"bootstrap[-_ ]?3\.", r"bootstrap[-_ ]?4\.", r"bootstrap\.min\.css.*3\."),
        (".html", ".htm", ".php", ".liquid", ".vue", ".jsx", ".tsx", ".css", ".scss"),
    )
    if not hits:
        return Check("bootstrap-legacy", "Sin Bootstrap 3/4", LEVEL_PASS,
                     "Sin referencias a Bootstrap legacy.")
    return Check(
        "bootstrap-legacy", "Sin Bootstrap 3/4", LEVEL_WARN,
        f"{len(hits)} archivos referencian Bootstrap 3/4.",
        hint="Envato prefiere Bootstrap 5+. Migra los componentes.",
        details=[f"{p.relative_to(project_path)}: {ln[:120]}" for p, ln in hits[:5]],
    )


def check_no_analytics(project_path: Path) -> Check:
    hits = _grep_any(
        project_path,
        (r"UA-\d{4,}-\d", r"\bG-[A-Z0-9]{8,}\b", r"\bgtag\s*\(",
         r"\bfbq\s*\(", r"hotjar\.com/c/hotjar"),
        (".html", ".htm", ".php", ".liquid", ".vue", ".jsx", ".tsx", ".js", ".ts"),
    )
    if not hits:
        return Check("no-analytics", "Sin tracking hardcoded", LEVEL_PASS,
                     "Sin Google Analytics / FB Pixel / Hotjar hardcoded.")
    return Check(
        "no-analytics", "Sin tracking hardcoded", LEVEL_FAIL,
        f"{len(hits)} archivos tienen tracking hardcoded.",
        hint="Envato rechaza GA/FB/Hotjar hardcoded en theme. El "
             "comprador lo añade después. Si quieres dejarlo como "
             "ejemplo, hazlo opt-in vía variable de entorno comentada.",
        details=[f"{p.relative_to(project_path)}: {ln[:120]}" for p, ln in hits[:8]],
    )


def check_reduced_motion(project_path: Path) -> Check:
    hits = _grep_any(
        project_path,
        (r"prefers-reduced-motion",),
        (".css", ".scss", ".sass", ".less", ".html", ".vue", ".jsx", ".tsx"),
    )
    if hits:
        return Check("reduced-motion", "prefers-reduced-motion respetado",
                     LEVEL_PASS, f"{len(hits)} archivos lo usan.")
    return Check(
        "reduced-motion", "prefers-reduced-motion respetado", LEVEL_WARN,
        "Ningún archivo usa `prefers-reduced-motion`.",
        hint="Envato lo recomienda. Añade un `@media (prefers-reduced-motion: "
             "reduce) { ... }` en tu CSS principal con transiciones "
             "deshabilitadas / acortadas.",
    )


def check_env_not_committed(project_path: Path) -> Check:
    """Verifica que ningún `.env*` (excepto `.env.example`) esté tracked en git."""
    if not (project_path / ".git").is_dir():
        return Check("env-tracked", ".env fuera de git", LEVEL_INFO,
                     "El proyecto aún no es un repo git.",
                     hint="`git init` para activar checks de git.")
    try:
        r = subprocess.run(
            ["git", "-C", str(project_path), "ls-files"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode != 0:
            return Check("env-tracked", ".env fuera de git", LEVEL_WARN,
                         "git ls-files falló.")
    except Exception:
        return Check("env-tracked", ".env fuera de git", LEVEL_WARN,
                     "git no disponible.")
    bad = []
    for line in r.stdout.splitlines():
        if line == ".env.example":
            continue
        if line == ".env" or line.startswith(".env."):
            bad.append(line)
    if bad:
        return Check(
            "env-tracked", ".env fuera de git", LEVEL_FAIL,
            f"{len(bad)} `.env*` están tracked en git.",
            hint="Añade `.env`, `.env.*` (excepto `.env.example`) al "
                 ".gitignore. Para limpiar el historial: "
                 "`git rm --cached <archivo>`.",
            details=bad,
        )
    return Check("env-tracked", ".env fuera de git", LEVEL_PASS,
                 "Ningún `.env*` está tracked en git.")


def check_size(project_path: Path) -> Check:
    """Total del proyecto sin node_modules + lista de archivos grandes."""
    total = 0
    big_files: list[tuple[Path, int]] = []
    for fp in _walk_source(project_path):
        try:
            sz = fp.stat().st_size
        except OSError:
            continue
        total += sz
        if sz > 10 * 1024 * 1024:  # >10 MB
            big_files.append((fp, sz))

    total_mb = total // (1024 * 1024)
    if total_mb > 50:
        level = LEVEL_WARN
        msg = f"Proyecto pesa {total_mb} MB (sin node_modules)."
        hint = ("Marketplaces prefieren <50 MB. Mira archivos grandes en "
                "details. Reduce imágenes (WebP / AVIF), comprime fuentes, "
                "elimina assets no usados.")
    elif total_mb > 100:
        level = LEVEL_FAIL
        msg = f"Proyecto pesa {total_mb} MB (sin node_modules) — demasiado."
        hint = "Optimiza imágenes y elimina assets pesados."
    else:
        level = LEVEL_PASS
        msg = f"Proyecto pesa {total_mb} MB (sin node_modules). OK."
        hint = ""

    details = []
    if big_files:
        big_files.sort(key=lambda x: -x[1])
        for p, sz in big_files[:10]:
            details.append(f"{sz // 1024 // 1024} MB  ·  {p.relative_to(project_path)}")
        if level == LEVEL_PASS:
            level = LEVEL_WARN
            msg += f"  ⚠ {len(big_files)} archivos >10 MB."
            hint = "Revisa los archivos grandes (en details)."

    return Check("size", "Tamaño del proyecto", level, msg, hint=hint, details=details)


def check_lighthouse(project_path: Path) -> Check:
    """Check informativo: ¿tienes lighthouse instalado? Si sí, sugiere
    ejecutarlo manualmente; corremos lighthouse en este preflight
    requiere arrancar un dev server, lo cual escapa al scope."""
    if not shutil.which("lighthouse"):
        return Check(
            "lighthouse", "Lighthouse instalado", LEVEL_INFO,
            "`lighthouse` no está en PATH.",
            hint="Para auditar performance/SEO/a11y: `npm install -g "
                 "lighthouse`. Luego, con el dev server corriendo: "
                 "`lighthouse http://localhost:3000 --view`.",
        )
    return Check(
        "lighthouse", "Lighthouse instalado", LEVEL_INFO,
        "lighthouse disponible — lánzalo manualmente con el dev server.",
        hint="`lighthouse http://localhost:<port> --view` "
             "(Performance ≥90, SEO ≥95, Accessibility ≥90, Best Practices ≥95).",
    )


def check_w3c_validator(project_path: Path) -> Check:
    """¿html-validate disponible para validación local?"""
    if shutil.which("html-validate"):
        return Check(
            "html-validate", "HTML validator disponible", LEVEL_INFO,
            "`html-validate` disponible.",
            hint="Ejecuta: `html-validate <archivos>.html`. Para W3C "
                 "validation oficial, usa https://validator.w3.org/.",
        )
    return Check(
        "html-validate", "HTML validator disponible", LEVEL_INFO,
        "`html-validate` no está en PATH.",
        hint="`npm install -g html-validate`. Para W3C, usa el validator "
             "web: https://validator.w3.org/.",
    )


def check_pcreative_secrets(project_path: Path) -> Check:
    """Detecta si en el theme generado han quedado URLs de licensing
    sin sustituir o secrets de los templates."""
    hits = _grep_any(
        project_path,
        (r"YOUR_DOMAIN", r"__LICENSE_API_URL__", r"__SLUG__",
         r"__PROJECT__", r"__LICENSE_HOST__", r"change-me-to-"),
        (".html", ".htm", ".php", ".liquid", ".vue", ".jsx", ".tsx",
         ".js", ".ts", ".env.example", ".env"),
    )
    if not hits:
        return Check("placeholders", "Placeholders del scaffold sustituidos",
                     LEVEL_PASS, "Sin placeholders sin resolver.")
    return Check(
        "placeholders", "Placeholders del scaffold sustituidos", LEVEL_FAIL,
        f"{len(hits)} archivos tienen placeholders sin sustituir.",
        hint="Reemplaza `YOUR_DOMAIN`, `__SLUG__`, `__PROJECT__`, "
             "`__LICENSE_API_URL__`, etc. por valores reales antes de "
             "empaquetar.",
        details=[f"{p.relative_to(project_path)}: {ln[:120]}" for p, ln in hits[:8]],
    )


# ── Orchestrator ─────────────────────────────────────────────────────


ALL_CHECKS = (
    check_readme,
    check_license_or_licensing,
    check_documentation,
    check_screenshots,
    check_jquery_legacy,
    check_bootstrap_legacy,
    check_no_analytics,
    check_reduced_motion,
    check_env_not_committed,
    check_size,
    check_pcreative_secrets,
    check_lighthouse,
    check_w3c_validator,
)


def run_all(project_path: Path) -> list[Check]:
    """Ejecuta todos los checks sobre `project_path` y devuelve la lista
    de resultados en el orden de ALL_CHECKS."""
    results: list[Check] = []
    for fn in ALL_CHECKS:
        try:
            results.append(fn(project_path))
        except Exception as e:
            results.append(Check(
                fn.__name__, f"Check {fn.__name__}", LEVEL_WARN,
                f"Error ejecutando check: {e}",
            ))
    return results


def summary(results: list[Check]) -> dict[str, int]:
    """Cuenta por nivel."""
    out = {LEVEL_PASS: 0, LEVEL_WARN: 0, LEVEL_FAIL: 0, LEVEL_INFO: 0}
    for r in results:
        out[r.level] = out.get(r.level, 0) + 1
    return out
