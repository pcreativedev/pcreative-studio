"""
licensing_scaffold.py — emite comandos bash que dropean los archivos
de integración con un sistema de licencias propio (verify-license
endpoint + setup wizard) en un proyecto recién scaffoldeado.

Lo consume `write_setup_script()` en themeforge.py: si el usuario ha
marcado el checkbox del sistema de licencias en el formulario, las
funciones de este módulo añaden las líneas necesarias al script de
setup tras el scaffold del stack base.

URL del endpoint y otros valores sensibles se leen en runtime de
`~/.config/themeforge/licensing.json` vía `licensing_config.load()`.

Spec canónico: `context/LICENSING-SYSTEM.template.md` (estructura
genérica) + `~/.config/themeforge/context-private/LICENSING-SYSTEM.md`
(versión real del usuario, fuera del repo).
"""
from __future__ import annotations

from pathlib import Path

from platform_compat import app_config_dir

# ─── Stack key → familia de scaffolding ──────────────────────────────
STACK_FAMILIES: dict[str, str] = {
    # Next.js (App Router)
    "nextjs-tailwind":  "nextjs",
    "nextjs-shadcn":    "nextjs",
    "nextjs-mantine":   "nextjs",
    "nextjs-heroui":    "nextjs",
    "t3-stack":         "nextjs",
    # Laravel
    "laravel-inertia":  "laravel",
    # WordPress
    "wordpress-block":  "wordpress",
    "wordpress-plugin": "wordpress",
    # Backends Express-style con SPA
    "hono-bun":         "express",
    "hono-cloudflare":  "express",
    "nestjs-prisma":    "express",
    "bun-elysia":       "express",
}

def _load_known_slugs() -> set[str]:
    """Lee la lista de slugs conocidos desde un archivo privado del
    usuario (uno por línea, '#' = comentario). Si no existe, devuelve
    set vacío — el código público NO contiene nombres de productos.

    Crea `~/.config/themeforge/known-product-slugs.txt` con tus slugs
    si quieres que el checkbox del sistema de licencias se auto-marque
    al detectar uno de ellos en el nombre del proyecto nuevo.
    """
    p = app_config_dir() / "known-product-slugs.txt"
    if not p.is_file():
        return set()
    try:
        return {
            line.strip()
            for line in p.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        }
    except Exception:
        return set()


KNOWN_PRODUCT_SLUGS: set[str] = _load_known_slugs()

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates" / "licensing"


def detect_family(stack_key: str) -> str | None:
    return STACK_FAMILIES.get(stack_key)


def likely_known_product(slug: str) -> bool:
    """¿El slug aparece en la lista de productos conocidos del usuario?
    Útil para preseleccionar el checkbox en la UI. La lista se lee de
    `~/.config/themeforge/known-product-slugs.txt` — si el archivo no
    existe, esta función devuelve False y no hay auto-detección."""
    return slug in KNOWN_PRODUCT_SLUGS




# ─── API pública ──────────────────────────────────────────────────────

def scaffold(stack_key: str, slug: str, project_name: str,
             create_gh_repo_under_org: bool = False) -> list[str]:
    """Devuelve líneas bash para embeber en el setup script.

    El stack base ya está scaffoldeado cuando esto se ejecuta; aquí
    solo añadimos los archivos de integración del sistema de licencias.
    """
    family = detect_family(stack_key)
    parts: list[str] = ['echo ""', 'echo "→ licensing scaffold…"']

    if family is None:
        parts.append(
            'echo "  (sin scaffold específico para este stack — '
            'consulta context/LICENSING-SYSTEM.md y crea los archivos a mano)."'
        )
    elif family == "nextjs":
        parts += _scaffold_nextjs(slug, project_name)
    elif family == "laravel":
        parts += _scaffold_laravel(slug, project_name)
    elif family == "wordpress":
        parts += _scaffold_wordpress(slug, project_name)
    elif family == "express":
        parts += _scaffold_express(slug, project_name)

    # Phase 3 — gh repo create (opcional, usa github_org de licensing.json)
    if create_gh_repo_under_org:
        parts += _gh_repo_create(slug, project_name)

    return parts


# ─── Render helper ────────────────────────────────────────────────────

def _render(template_name: str, *, slug: str, project_name: str) -> str:
    """Lee templates/licensing/<template_name> y sustituye placeholders.

    Placeholders soportados:
      __SLUG__              — slug del proyecto generado
      __PROJECT__           — nombre legible del proyecto
      __LICENSE_API_URL__   — URL del endpoint verify (de licensing.json)
      __LICENSE_HOST__      — protocolo + host del endpoint (de licensing.json)
      __LICENSE_HOST_BARE__ — host sin protocolo (de licensing.json)
    """
    from licensing_config import load as _load_licensing_config
    cfg = _load_licensing_config()
    api_url = cfg["license_api_url"]
    # Derivar host con y sin protocolo a partir del api_url
    if "://" in api_url:
        proto, rest = api_url.split("://", 1)
        host = rest.split("/", 1)[0]
        host_with_proto = f"{proto}://{host}"
    else:
        host = api_url.split("/", 1)[0]
        host_with_proto = host

    path = TEMPLATES_DIR / template_name
    text = path.read_text(encoding="utf-8")
    return (text
            .replace("__SLUG__", slug)
            .replace("__PROJECT__", project_name)
            .replace("__LICENSE_API_URL__", api_url)
            .replace("__LICENSE_HOST__", host_with_proto)
            .replace("__LICENSE_HOST_BARE__", host))


def _heredoc(dest_path: str, content: str, tag: str = "PCRE_EOF") -> str:
    """Genera un comando bash que escribe `content` en `dest_path` vía
    heredoc. Crea el directorio padre si hace falta."""
    # Nota: usamos sustitución de comando para crear el dir padre
    # (no `mkdir -p $(dirname …)` con interpolación de fish — esto se
    # ejecuta en bash via `bash -lc` así que está bien).
    return (
        f'mkdir -p "$(dirname {_shq(dest_path)})" 2>/dev/null || true\n'
        f"cat > {_shq(dest_path)} <<'{tag}'\n"
        f"{content}\n"
        f"{tag}"
    )


def _heredoc_append(dest_path: str, content: str, marker: str,
                    tag: str = "PCRE_EOF") -> str:
    """Append a un archivo si no contiene ya `marker`. Idempotente."""
    return (
        f"if [ -f {_shq(dest_path)} ] && ! grep -q {_shq(marker)} {_shq(dest_path)}; then\n"
        f"  cat >> {_shq(dest_path)} <<'{tag}'\n"
        f"{content}\n"
        f"{tag}\n"
        f"elif [ ! -f {_shq(dest_path)} ]; then\n"
        f"  cat > {_shq(dest_path)} <<'{tag}'\n"
        f"{content}\n"
        f"{tag}\n"
        f"fi"
    )


def _shq(s: str) -> str:
    """Single-quote para bash: 'foo' → 'foo', it's → 'it'\"'\"'s'"""
    return "'" + s.replace("'", "'\"'\"'") + "'"


# ─── Familia Next.js ──────────────────────────────────────────────────

def _scaffold_nextjs(slug: str, project_name: str) -> list[str]:
    parts: list[str] = []
    parts.append('echo "  · Next.js: verify-license + setup wizard + middleware"')

    # verify-license route
    parts.append(_heredoc(
        "src/app/api/verify-license/route.ts",
        _render("nextjs/verify-license.route.ts.tpl", slug=slug, project_name=project_name),
    ))
    # setup page
    parts.append(_heredoc(
        "src/app/setup/page.tsx",
        _render("nextjs/setup.page.tsx.tpl", slug=slug, project_name=project_name),
    ))
    # zustand store
    parts.append(_heredoc(
        "src/store/setup-store.ts",
        _render("nextjs/setup-store.ts.tpl", slug=slug, project_name=project_name),
    ))
    # middleware (root)
    parts.append(_heredoc(
        "middleware.ts",
        _render("nextjs/middleware.ts.tpl", slug=slug, project_name=project_name),
    ))
    # env.example (append)
    env_add = _render("nextjs/env.additions.txt", slug=slug, project_name=project_name)
    parts.append(_heredoc_append(".env.example", env_add, "licensing integration"))
    # Asegurar zustand instalado (no rompe si ya está)
    parts.append('npm install zustand 2>&1 | tail -3 || true')
    return parts


# ─── Familia Laravel ──────────────────────────────────────────────────

def _scaffold_laravel(slug: str, project_name: str) -> list[str]:
    parts: list[str] = []
    parts.append('echo "  · Laravel: SetupWizard (controller + model + middleware + view + migration)"')

    parts.append(_heredoc(
        "app/Http/Controllers/SetupWizardController.php",
        _render("laravel/SetupWizardController.php.tpl", slug=slug, project_name=project_name),
    ))
    parts.append(_heredoc(
        "app/Http/Middleware/CheckSetupWizard.php",
        _render("laravel/CheckSetupWizard.php.tpl", slug=slug, project_name=project_name),
    ))
    parts.append(_heredoc(
        "app/Models/SetupState.php",
        _render("laravel/SetupState.php.tpl", slug=slug, project_name=project_name),
    ))
    # Migration con timestamp dinámico generado en el momento del setup
    parts.append('PCRE_TS="$(date +%Y_%m_%d_%H%M%S)"')
    parts.append(_heredoc(
        '"database/migrations/${PCRE_TS}_create_setup_state_table.php"',
        _render("laravel/migration.php.tpl", slug=slug, project_name=project_name),
    ).replace(
        # Lo de arriba con _shq habrá quoted el path con ${PCRE_TS} dentro,
        # rompiendo la expansión. Lo emitimos sin _shq para esta sola línea.
        "'\"database/migrations/${PCRE_TS}_create_setup_state_table.php\"'",
        '"database/migrations/${PCRE_TS}_create_setup_state_table.php"',
    ))
    parts.append(_heredoc(
        "resources/views/setup/index.blade.php",
        _render("laravel/setup-index.blade.php.tpl", slug=slug, project_name=project_name),
    ))
    # routes/web.php (append)
    routes_add = _render("laravel/routes.additions.php.tpl", slug=slug, project_name=project_name)
    parts.append(_heredoc_append("routes/web.php", routes_add, "SetupWizardController"))

    # .env.example (append)
    env_add = _render("laravel/env.additions.txt", slug=slug, project_name=project_name)
    parts.append(_heredoc_append(".env.example", env_add, "PRODUCT_SLUG"))

    # Registrar middleware en bootstrap/app.php (Laravel 11+).
    # Inserta el use statement y la línea `$middleware->append(...)`
    # solo si no están ya.
    parts.append(
        "if [ -f bootstrap/app.php ]; then\n"
        "  grep -q 'use App\\\\Http\\\\Middleware\\\\CheckSetupWizard;' bootstrap/app.php || \\\n"
        "    sed -i '0,/^<?php$/{s|^<?php$|<?php\\n\\nuse App\\\\Http\\\\Middleware\\\\CheckSetupWizard;|}' bootstrap/app.php\n"
        "  grep -q 'CheckSetupWizard::class' bootstrap/app.php || \\\n"
        "    sed -i 's|withMiddleware(function (Middleware $middleware) {|withMiddleware(function (Middleware $middleware) {\\n        $middleware->append(CheckSetupWizard::class);|' bootstrap/app.php\n"
        "fi"
    )
    return parts


# ─── Familia WordPress ────────────────────────────────────────────────

def _scaffold_wordpress(slug: str, project_name: str) -> list[str]:
    parts: list[str] = []
    parts.append('echo "  · WordPress: clase License + página admin"')
    parts.append(_heredoc(
        "inc/class-license.php",
        _render("wordpress/class-license.php.tpl", slug=slug, project_name=project_name),
    ))
    parts.append(_heredoc(
        "inc/admin-license-page.php",
        _render("wordpress/admin-license-page.php.tpl", slug=slug, project_name=project_name),
    ))
    parts.append(_heredoc(
        "README.licensing.md",
        _render("wordpress/README.licensing.md", slug=slug, project_name=project_name),
    ))
    parts.append(
        'echo "  · README.licensing.md generado — léelo para cablear class-license en el bootstrap del plugin/theme."'
    )
    return parts


# ─── Familia Express / Hono / Nest / Elysia ──────────────────────────

def _scaffold_express(slug: str, project_name: str) -> list[str]:
    parts: list[str] = []
    parts.append('echo "  · Express-style: license route (stub adaptable)"')
    parts.append(_heredoc(
        "src/routes/license.ts",
        _render("express/license.route.ts.tpl", slug=slug, project_name=project_name),
    ))
    env_add = _render("express/env.additions.txt", slug=slug, project_name=project_name)
    parts.append(_heredoc_append(".env.example", env_add, "PRODUCT_SLUG"))
    return parts


# ─── Phase 3 — gh repo create ─────────────────────────────────────────

def _gh_repo_create(slug: str, project_name: str) -> list[str]:
    """Si `gh` está instalado y la config tiene `github_org`, crea el
    repo privado bajo esa org y lo enlaza como `origin`. Si la config no
    tiene `github_org`, se omite (el botón "📦 GitHub" del ProjectWindow
    es el flujo recomendado para crear el repo manualmente)."""
    from licensing_config import load as _load_licensing_config
    org = _load_licensing_config().get("github_org", "").strip()
    if not org:
        return [
            'echo ""',
            'echo "→ Phase 3 omitida (no hay github_org en licensing.json)."',
        ]
    full = f"{org}/{slug}"
    return [
        'echo ""',
        'echo "→ gh repo create ' + full + ' (Phase 3)…"',
        'if command -v gh >/dev/null 2>&1; then',
        '  if gh repo view ' + _shq(full) + ' >/dev/null 2>&1; then',
        '    echo "  repo ya existe — omito create."',
        '  else',
        '    gh repo create ' + _shq(full) + ' --private --source . --remote origin --description ' + _shq(project_name) + ' || \\',
        '      echo "  (gh repo create falló — añade el remoto manualmente)"',
        '  fi',
        'else',
        '  echo "  gh no está instalado — omito Phase 3."',
        'fi',
    ]
