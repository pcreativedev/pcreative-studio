"""
Mapeo "stack detectado" → comando que levanta el dev server + URL local.

Cada perfil tiene:
  - name        : etiqueta legible.
  - command     : lista de args (subprocess / QProcess).
  - url         : URL del dev server (con {port} si parametrizable).
  - default_port: puerto por defecto del stack.
  - port_inject : cómo inyectar un puerto distinto. Valores:
                    None              → no se cambia el puerto (Docker, etc).
                    "env:PORT"        → variable de entorno PORT=<n>.
                    "flag:--port"     → añadir `--port <n>` al final.
                    "flag:--port="    → añadir `--port=<n>` al final.
                    "flag:-p"         → añadir `-p <n>` al final.
                    "flag:--web-port="→ añadir `--web-port=<n>` (Flutter).
  - stop        : (opcional) comando para detener (Docker / wp-env).
  - note        : (opcional) nota mostrada al user.
"""
from __future__ import annotations

import json
import socket
from pathlib import Path
from typing import TypedDict

import platform_compat as pc


class PreviewProfile(TypedDict, total=False):
    name: str
    command: list[str]
    url: str
    default_port: int
    port_inject: str
    stop: list[str]
    note: str
    # Lista de procesos extra lanzados en paralelo. Cada entrada:
    #   {"name": "vite", "command": [...], "optional": True}
    # optional=True → si falla al arrancar, no mata el preview principal.
    secondary_processes: list[dict]


HOME = Path.home()
PORTS_FILE = pc.app_config_dir() / "ports.json"


def _load_ports() -> dict:
    try:
        return json.loads(PORTS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_ports(d: dict) -> None:
    try:
        PORTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        PORTS_FILE.write_text(json.dumps(d, indent=2, sort_keys=True), encoding="utf-8")
    except Exception:
        pass


def _is_port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def find_free_port(start: int, max_tries: int = 200) -> int:
    """Devuelve el primer puerto libre desde `start`. Salta puertos
    asignados (en uso) sobre la marcha."""
    for offset in range(max_tries):
        p = start + offset
        if _is_port_free(p):
            return p
    return start  # fallback


def get_port_for_project(project_name: str, default_port: int) -> int:
    """Devuelve un puerto persistente asignado a este proyecto. Si el
    default_port del stack cambia (se redetectó otro stack), se reasigna.
    Formato JSON: {project: {"port": N, "default_port": M}} o legacy {project: N}.
    """
    ports = _load_ports()
    entry = ports.get(project_name)

    # Normaliza legacy: si entry es int en lugar de dict, lo convertimos a dict
    if isinstance(entry, int):
        entry = {"port": entry, "default_port": default_port}
        ports[project_name] = entry

    # Reusar puerto guardado SOLO si:
    #   - se asignó con el mismo default_port (mismo stack)
    #   - está libre ahora
    if entry and entry.get("default_port") == default_port and _is_port_free(entry["port"]):
        return entry["port"]

    # Sino reasignar
    used = {e["port"] if isinstance(e, dict) else e for e in ports.values()}
    if entry:
        used.discard(entry["port"])
    candidate = default_port
    while candidate in used or not _is_port_free(candidate):
        candidate += 1
    ports[project_name] = {"port": candidate, "default_port": default_port}
    _save_ports(ports)
    return candidate


def apply_port(profile: PreviewProfile, port: int) -> tuple[list[str], dict, str]:
    """Devuelve (command, env_extra, url) con el puerto inyectado según
    `port_inject`. env_extra está pensado para QProcess.setProcessEnvironment."""
    cmd = list(profile["command"])
    env_extra: dict[str, str] = {}
    inj = profile.get("port_inject")
    if inj is None:
        url = profile["url"].replace("{port}", str(port))
        return cmd, env_extra, url

    if inj == "env:PORT":
        env_extra["PORT"] = str(port)
    elif inj == "env:WP_ENV_PORT":
        env_extra["WP_ENV_PORT"] = str(port)
    elif inj == "flag:--port":
        cmd += ["--port", str(port)]
    elif inj == "flag:--port=":
        cmd += [f"--port={port}"]
    elif inj == "flag:-p":
        cmd += ["-p", str(port)]
    elif inj == "flag:--web-port=":
        cmd += [f"--web-port={port}"]
    elif inj == "flag:bare":
        cmd += [str(port)]

    url = profile["url"].replace("{port}", str(port))
    return cmd, env_extra, url


def _env_contains(project_path: Path, *keywords: str) -> bool:
    """Devuelve True si alguno de los archivos .env del proyecto contiene
    cualquiera de las palabras (case-insensitive)."""
    candidates = [".env", ".env.local", ".env.development", ".env.example"]
    kws = [k.lower() for k in keywords]
    for name in candidates:
        f = project_path / name
        if f.is_file():
            try:
                txt = f.read_text(errors="ignore", encoding="utf-8").lower()
                if any(k in txt for k in kws):
                    return True
            except Exception:
                pass
    return False


def _composer_has(project_path: Path, *packages: str) -> bool:
    """Devuelve True si composer.json tiene alguno de esos paquetes."""
    c = project_path / "composer.json"
    if not c.is_file():
        return False
    try:
        data = json.loads(c.read_text(errors="ignore", encoding="utf-8"))
        req = {**(data.get("require") or {}), **(data.get("require-dev") or {})}
        return any(p in req for p in packages)
    except Exception:
        return False


def _which(cmd: str) -> bool:
    import shutil
    return shutil.which(cmd) is not None


def _detect_webhook_url(project_path: Path, default_port: int) -> str:
    """Heurística para la ruta de webhook Stripe según stack."""
    if (project_path / "artisan").is_file():
        return f"localhost:{default_port}/stripe/webhook"
    pkg = project_path / "package.json"
    if pkg.is_file():
        try:
            data = json.loads(pkg.read_text(errors="ignore", encoding="utf-8"))
            deps = {**(data.get("dependencies") or {}), **(data.get("devDependencies") or {})}
            if "next" in deps:
                return f"localhost:{default_port}/api/webhooks/stripe"
        except Exception:
            pass
    return f"localhost:{default_port}/webhooks/stripe"


def _collect_extra_processes(project_path: Path, deps: dict | None = None, default_port: int = 3000) -> list[dict]:
    """Detecta procesos auxiliares útiles basándose en archivos del proyecto.
    Solo añade procesos cuyos binarios estén instalados en el sistema."""
    deps = deps or {}
    secs: list[dict] = []

    # ── Prisma Studio ──────────────────────────────────────────────
    if (
        (project_path / "prisma" / "schema.prisma").is_file()
        or "prisma" in deps
        or "@prisma/client" in deps
    ):
        secs.append({
            "name": "prisma studio",
            "command": ["npx", "prisma", "studio", "--port", "5555", "--browser", "none"],
            "optional": True,
        })

    # ── Drizzle Studio ─────────────────────────────────────────────
    if "drizzle-orm" in deps or (project_path / "drizzle.config.ts").is_file():
        secs.append({
            "name": "drizzle studio",
            "command": ["npx", "drizzle-kit", "studio", "--port", "5556"],
            "optional": True,
        })

    # ── Django + django-tailwind ───────────────────────────────────
    if (project_path / "manage.py").is_file():
        req = project_path / "requirements.txt"
        if req.is_file() and "django-tailwind" in req.read_text(errors="ignore", encoding="utf-8"):
            secs.append({
                "name": "tailwind watcher",
                "command": ["python", "manage.py", "tailwind", "start"],
                "optional": True,
            })

    # ── Inngest dev server ─────────────────────────────────────────
    if "inngest" in deps:
        secs.append({
            "name": "inngest dev",
            "command": ["npx", "inngest-cli@latest", "dev"],
            "optional": True,
        })

    # ── Redis / Valkey (cualquier proyecto que lo use) ─────────────
    needs_redis = (
        "redis" in deps
        or "ioredis" in deps
        or "@upstash/redis" in deps
        or _composer_has(project_path, "predis/predis")
        or _env_contains(project_path, "REDIS_URL", "REDIS_HOST", "REDIS_PORT")
        or (project_path / "redis.conf").is_file()
    )
    if needs_redis:
        # Preferir redis-server, fallback valkey-server
        bin_name = None
        if _which("redis-server"): bin_name = "redis-server"
        elif _which("valkey-server"): bin_name = "valkey-server"
        if bin_name:
            secs.append({
                "name": "redis",
                "command": [bin_name, "--port", "6379", "--daemonize", "no", "--save", "", "--appendonly", "no"],
                "optional": True,
            })

    # ── Mailpit (capturar emails de dev) ───────────────────────────
    needs_mail = (
        _env_contains(project_path, "MAIL_HOST=localhost", "MAIL_HOST=127.0.0.1",
                      "SMTP_HOST=localhost", "SMTP_HOST=127.0.0.1",
                      "MAIL_MAILER=smtp", "MAIL_MAILER=log",
                      "mailhog", "mailpit")
    )
    if needs_mail and _which("mailpit"):
        secs.append({
            "name": "mailpit",
            "command": ["mailpit"],
            "optional": True,
        })

    # ── Stripe CLI listen (webhooks dev) ───────────────────────────
    needs_stripe = (
        "stripe" in deps
        or _composer_has(project_path, "stripe/stripe-php", "cashier/cashier", "laravel/cashier")
        or _env_contains(project_path, "STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET")
    )
    if needs_stripe and _which("stripe"):
        webhook = _detect_webhook_url(project_path, default_port)
        secs.append({
            "name": "stripe listen",
            "command": ["stripe", "listen", "--forward-to", webhook],
            "optional": True,
        })

    # ── ngrok tunnel (si está configurado en .env o el user lo quiere) ─
    needs_ngrok = (
        _env_contains(project_path, "NGROK_AUTHTOKEN", "USE_NGROK=true", "EXPOSE_NGROK=true")
        or (project_path / ".ngrok.yml").is_file()
    )
    if needs_ngrok and _which("ngrok"):
        secs.append({
            "name": "ngrok",
            "command": ["ngrok", "http", str(default_port)],
            "optional": True,
        })

    return secs


# ─── helpers de detección ────────────────────────────────────────────
def has_docker_compose(path: Path) -> Path | None:
    for n in ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"):
        p = path / n
        if p.is_file():
            return p
    return None


# Imágenes Docker que son SOLO infraestructura (BD, cache, admin UIs).
# Si un docker-compose contiene únicamente estas, NO es la app principal
# del proyecto — son servicios auxiliares. detect_preview_profile debe
# ignorarlo y caer al siguiente detector (mono-repo, package.json, etc.).
_INFRA_IMAGES = (
    "postgres", "mysql", "mariadb", "mongo", "redis", "valkey",
    "memcached", "rabbitmq", "elasticsearch", "opensearch",
    "adminer", "phpmyadmin", "mailpit", "mailhog", "minio",
    "meilisearch", "typesense", "qdrant", "clickhouse",
)


def compose_is_infra_only(compose_path: Path) -> bool:
    """Devuelve True si el docker-compose contiene SOLO imágenes de
    infraestructura (Postgres, Redis, Adminer, etc.) y no la app real.
    Útil para que el detector de preview no se quede en el compose
    cuando la app de verdad está en apps/web."""
    try:
        text = compose_path.read_text(errors="ignore", encoding="utf-8").lower()
    except Exception:
        return False
    # Buscar líneas "image: <something>"
    import re
    images = re.findall(r"image:\s*['\"]?([\w./-]+?)(?::|['\"\s]|$)", text)
    if not images:
        return False
    # Si TODAS las imágenes son infra → es infra-only
    for img in images:
        base = img.split("/")[-1].split(":")[0]
        if not any(base.startswith(prefix) for prefix in _INFRA_IMAGES):
            return False
    return True


def has_wp_env(path: Path) -> bool:
    # 1. Marcador directo: existe .wp-env.json
    if (path / ".wp-env.json").is_file():
        return True
    # 2. Block theme clásico: style.css + theme.json
    if (path / "style.css").is_file() and (path / "theme.json").is_file():
        return True
    # 3. Plugin WP: cualquier .php raíz con header `Plugin Name:`
    try:
        for php in path.glob("*.php"):
            try:
                head = php.read_text(errors="ignore", encoding="utf-8")[:2000]
                if "Plugin Name:" in head:
                    return True
            except Exception:
                pass
    except Exception:
        pass
    return False


def parse_package_scripts(path: Path) -> dict:
    pkg = path / "package.json"
    if not pkg.is_file():
        return {}
    try:
        data = json.loads(pkg.read_text(errors="ignore", encoding="utf-8"))
        return data.get("scripts") or {}
    except Exception:
        return {}


def _enrich_with_extras(project_path: Path, profile: PreviewProfile, deps: dict | None = None) -> PreviewProfile:
    """Añade procesos secundarios automáticos a CUALQUIER perfil."""
    default_port = profile.get("default_port", 3000)
    extras = _collect_extra_processes(project_path, deps, default_port)
    if extras:
        existing = profile.get("secondary_processes") or []
        # Evitar duplicados por nombre
        names = {s["name"] for s in existing}
        for e in extras:
            if e["name"] not in names:
                existing.append(e)
        profile["secondary_processes"] = existing
        names_str = ", ".join(s["name"] for s in existing)
        prev_note = profile.get("note", "")
        profile["note"] = (prev_note + f"  Procesos extra: {names_str}.").strip()
    return profile


def detect_preview_profile(project_path: Path) -> PreviewProfile | None:
    """Heurística → devuelve cómo levantar y dónde ver el preview."""
    profile = _detect_base_profile(project_path)
    if profile is None:
        return None
    # Recolectar deps si tiene package.json (para que _enrich los use)
    deps = {}
    pkg = project_path / "package.json"
    if pkg.is_file():
        try:
            data = json.loads(pkg.read_text(errors="ignore", encoding="utf-8"))
            deps = {**(data.get("dependencies") or {}), **(data.get("devDependencies") or {})}
        except Exception:
            pass
    return _enrich_with_extras(project_path, profile, deps)


# ─── Mono-repo / sub-proyectos ──────────────────────────────────────────


class Subproject(TypedDict, total=False):
    name: str               # nombre legible (basename del directorio)
    path: Path              # ruta absoluta al sub-proyecto
    rel_path: str           # ruta relativa a la raíz del mono-repo
    profile: PreviewProfile | None  # perfil de preview, si detectable
    from_reference: bool    # True si vive dentro de reference/ (modo recreate)


def _is_workspace_root(p: Path) -> bool:
    """Detecta si una carpeta es la raíz de un mono-repo de workspaces
    (pnpm-workspace, yarn workspaces, turbo, nx, lerna…). En ese caso,
    aunque tenga package.json en raíz, la app real está en apps/*."""
    if (p / "pnpm-workspace.yaml").is_file(): return True
    if (p / "turbo.json").is_file(): return True
    if (p / "nx.json").is_file(): return True
    if (p / "lerna.json").is_file(): return True
    if (p / "rush.json").is_file(): return True
    # yarn workspaces o npm workspaces en package.json
    pkg = p / "package.json"
    if pkg.is_file():
        try:
            data = json.loads(pkg.read_text(errors="ignore", encoding="utf-8"))
            if data.get("workspaces"):
                return True
        except Exception:
            pass
    return False


def _looks_like_stack(p: Path) -> bool:
    """¿Hay algún marcador de stack reconocible en este directorio?"""
    markers = (
        "package.json", "composer.json", "pubspec.yaml", "build.gradle",
        "build.gradle.kts", "Gemfile", "Cargo.toml", "go.mod", "pyproject.toml",
        "requirements.txt", "manage.py", "hugo.toml", "hugo.yaml",
        "astro.config.mjs", "astro.config.ts", "drizzle.config.ts",
        "vite.config.ts", "vite.config.js", "nuxt.config.ts", "next.config.js",
        "next.config.mjs", "next.config.ts", "artisan",
    )
    return any((p / m).exists() for m in markers)


def _ignore_subdir(name: str) -> bool:
    """Ignorar directorios técnicos que nunca son sub-proyectos."""
    if name.startswith("."):
        return True
    # NOTA: NO incluimos 'web' aquí aunque sea común en Flutter como
    # carpeta de output, porque también es estándar en mono-repos JS
    # (apps/web). El detector de stack la filtrará igualmente si no
    # tiene marcadores válidos.
    return name in {
        "node_modules", "vendor", "dist", "build", ".next", ".nuxt",
        "out", "coverage", "__MACOSX", "documentation", "docs", "doc",
        "screenshots", "context", "reference",
        # carpetas Flutter de salida (web se omite a propósito)
        "ios", "android", "macos", "windows", "linux", "test",
    }


def _scan_subprojects_in(scan_dir: Path, rel_root: Path, from_reference: bool,
                         *, max_depth: int = 3) -> list[Subproject]:
    """Escanea `scan_dir` recursivamente buscando subdirectorios con
    marcador de stack. Para cada hijo:

    - Si SÍ es stack → lo añade y NO sigue bajando dentro (es una
      unidad coherente).
    - Si NO es stack → desciende un nivel más (hasta `max_depth`) para
      cubrir patrones tipo `Files/Laravel/`, `Files/Flutter/Driver/`,
      `apps/web/`, `packages/ui/`, etc.

    `max_depth=3` cubre estos casos comunes:

      apps/web                       (depth 1)
      Files/Laravel                  (depth 1)
      Files/Flutter/Driver           (depth 2)
      apps/mobile/ios-shell          (depth 2)
      monorepo/services/api/server   (depth 3)

    Esto reemplaza el viejo "un nivel de wrapping si grandchildren == 1"
    que fallaba en mono-repos comerciales como OvoRide (varios stacks
    anidados bajo `Files/`).
    """
    out: list[Subproject] = []
    if max_depth <= 0:
        return out
    try:
        children = sorted(scan_dir.iterdir())
    except Exception:
        return out
    for child in children:
        if not child.is_dir() or _ignore_subdir(child.name):
            continue
        if _looks_like_stack(child):
            try:
                rel = str(child.relative_to(rel_root))
            except ValueError:
                rel = str(child)
            out.append({
                "name": child.name,
                "path": child,
                "rel_path": rel,
                "profile": detect_preview_profile(child),
                "from_reference": from_reference,
            })
        else:
            # Bajar otro nivel para cubrir Files/, apps/, packages/, src/,
            # services/, etc.
            out.extend(_scan_subprojects_in(
                child, rel_root, from_reference, max_depth=max_depth - 1
            ))
    return out


def detect_subprojects(root: Path) -> list[Subproject]:
    """Devuelve la lista de sub-proyectos detectados bajo `root`.

    Reglas:
    - Si la raíz misma es un stack: la incluimos como el "principal"
      (from_reference=False).
    - Si la raíz NO es stack pero contiene varios subdirectorios con
      stack: mono-repo en raíz, los incluimos todos.
    - Si existe `root/reference/`: escaneamos también ahí y marcamos los
      hallazgos con `from_reference=True` (modo recreate: el agente los
      estudia, no los modifica).
    - Si tras todo solo hay 1 elemento y no es from_reference, devolvemos
      lista vacía (no es mono-repo, solo un proyecto normal).
    """
    if not root.is_dir():
        return []

    subs: list[Subproject] = []
    root_is_stack = _looks_like_stack(root)
    # ¿La raíz declara workspaces? (pnpm, yarn, turbo, nx, lerna, rush…)
    # Si sí, es mono-repo aunque tenga package.json en raíz — escaneamos
    # apps/* y packages/* dentro.
    is_workspace_root = _is_workspace_root(root)

    if root_is_stack and not is_workspace_root:
        # Proyecto normal con stack en raíz.
        profile = detect_preview_profile(root)
        if profile:
            subs.append({
                "name": root.name,
                "path": root,
                "rel_path": ".",
                "profile": profile,
                "from_reference": False,
            })
    else:
        # Mono-repo: raíz sin stack ejecutable o raíz que solo declara
        # workspaces. Escanear sub-apps.
        subs.extend(_scan_subprojects_in(root, root, from_reference=False))

    # Reference/ — modo recreate: estudio, no modificación
    ref_dir = root / "reference"
    if ref_dir.is_dir():
        subs.extend(_scan_subprojects_in(ref_dir, root, from_reference=True))

    # Solo 1 elemento y no es referencia → trato como proyecto normal,
    # no merece la pena el dropdown.
    has_reference = any(s.get("from_reference") for s in subs)
    if len(subs) <= 1 and not has_reference:
        return []
    return subs


def _detect_base_profile(project_path: Path) -> PreviewProfile | None:
    """Lógica original sin extras automáticos."""
    # 0. Laravel (artisan + composer.json) — prioridad absoluta.
    if (project_path / "artisan").is_file() and (project_path / "composer.json").is_file():
        try:
            cdata = json.loads((project_path / "composer.json").read_text(errors="ignore", encoding="utf-8"))
            req = {**(cdata.get("require") or {}), **(cdata.get("require-dev") or {})}
            if "laravel/framework" in req or "laravel/laravel" in req:
                pkg_scripts = parse_package_scripts(project_path)
                secondaries: list[dict] = []
                if "dev" in pkg_scripts:
                    secondaries.append({
                        "name": "vite (HMR)",
                        "command": ["npm", "run", "dev"],
                        "optional": True,
                    })
                # Queue listener (siempre, suele estar disponible)
                secondaries.append({
                    "name": "queue",
                    "command": ["php", "artisan", "queue:listen", "--tries=1", "--timeout=0"],
                    "optional": True,
                })
                # Pail (logs en vivo) — laravel/pail viene en require-dev de Laravel 11+
                if "laravel/pail" in {**req, **(cdata.get("require") or {})}:
                    secondaries.append({
                        "name": "pail (logs)",
                        "command": ["php", "artisan", "pail", "--timeout=0"],
                        "optional": True,
                    })
                return {
                    "name": "Laravel artisan + Vite + Queue + Pail",
                    "command": ["php", "artisan", "serve"],
                    "url": "http://localhost:{port}",
                    "default_port": 8000,
                    "port_inject": "flag:--port=",
                    "note": "Stack completo: server + HMR + queue + logs en paralelo.",
                    "secondary_processes": secondaries,
                }
        except Exception:
            pass

    # 1. Docker Compose — solo si NO es infra-only.
    #    Si el compose solo levanta Postgres/Redis/Adminer/etc, son
    #    servicios auxiliares: lo lanzamos como proceso secundario y
    #    seguimos buscando la app real en mono-repo/package.json.
    compose_path = has_docker_compose(project_path)
    if compose_path and not compose_is_infra_only(compose_path):
        return {
            "name": "Docker Compose",
            "command": ["docker", "compose", "up", "-d"],
            "stop": ["docker", "compose", "down"],
            "url": "http://localhost:8080",
            "default_port": 8080,
            "port_inject": None,
            "note": "Revisa el compose para ver el puerto real.",
        }

    # 2. WordPress wp-env.
    if has_wp_env(project_path):
        return {
            "name": "WordPress (wp-env)",
            "command": ["npx", "--yes", "@wordpress/env", "start"],
            "stop": ["npx", "--yes", "@wordpress/env", "stop"],
            "url": "http://localhost:{port}",
            "default_port": 8888,
            "port_inject": "env:WP_ENV_PORT",  # wp-env honra esto en .wp-env.json
            "note": "Login: admin / password.",
        }

    # 3. package.json
    scripts = parse_package_scripts(project_path)
    deps = {}
    pkg = project_path / "package.json"
    if pkg.is_file():
        try:
            data = json.loads(pkg.read_text(errors="ignore", encoding="utf-8"))
            deps = {**(data.get("dependencies") or {}), **(data.get("devDependencies") or {})}
        except Exception:
            pass

    # 3a. Expo (React Native web)
    if "expo" in deps:
        return {
            "name": "Expo (web)",
            "command": ["npx", "expo", "start", "--web"],
            "url": "http://localhost:{port}",
            "default_port": 8081,
            "port_inject": "flag:--port",
            "note": "Móvil: app Expo Go + escanear QR.",
        }

    # 3b. Ionic
    if any(k in deps for k in ("@ionic/react", "@ionic/angular", "@ionic/vue")):
        return {
            "name": "Ionic serve",
            "command": ["npx", "ionic", "serve", "--no-open"],
            "url": "http://localhost:{port}",
            "default_port": 8100,
            "port_inject": "flag:--port",
        }

    if "dev" in scripts:
        if "next" in deps:
            return {
                "name": "Next.js dev",
                "command": ["npm", "run", "dev"],
                "url": "http://localhost:{port}",
                "default_port": 3000,
                "port_inject": "env:PORT",
            }
        if "astro" in deps:
            return {
                "name": "Astro dev",
                "command": ["npm", "run", "dev", "--"],
                "url": "http://localhost:{port}",
                "default_port": 4321,
                "port_inject": "flag:--port",
            }
        if "vite" in deps:
            return {
                "name": "Vite dev",
                "command": ["npm", "run", "dev", "--"],
                "url": "http://localhost:{port}",
                "default_port": 5173,
                "port_inject": "flag:--port",
            }
        if "@angular/core" in deps:
            return {
                "name": "Angular ng serve",
                "command": ["npx", "ng", "serve"],
                "url": "http://localhost:{port}",
                "default_port": 4200,
                "port_inject": "flag:--port",
            }
        if "nuxt" in deps:
            return {
                "name": "Nuxt dev",
                "command": ["npm", "run", "dev"],
                "url": "http://localhost:{port}",
                "default_port": 3000,
                "port_inject": "env:PORT",
            }
        if "@sveltejs/kit" in deps:
            return {
                "name": "SvelteKit dev",
                "command": ["npm", "run", "dev", "--"],
                "url": "http://localhost:{port}",
                "default_port": 5173,
                "port_inject": "flag:--port",
            }
        if "@builder.io/qwik-city" in deps or "@builder.io/qwik" in deps:
            return {
                "name": "Qwik City dev",
                "command": ["npm", "run", "dev"],
                "url": "http://localhost:{port}",
                "default_port": 5173,
                "port_inject": "env:PORT",
            }
        return {
            "name": "npm run dev",
            "command": ["npm", "run", "dev"],
            "url": "http://localhost:{port}",
            "default_port": 3000,
            "port_inject": "env:PORT",
        }

    if "start" in scripts:
        if "@angular/core" in deps:
            return {
                "name": "Angular ng serve",
                "command": ["npx", "ng", "serve"],
                "url": "http://localhost:{port}",
                "default_port": 4200,
                "port_inject": "flag:--port",
            }
        return {
            "name": "npm start",
            "command": ["npm", "start"],
            "url": "http://localhost:{port}",
            "default_port": 3000,
            "port_inject": "env:PORT",
        }

    # 4. Flutter (pubspec.yaml)
    if (project_path / "pubspec.yaml").is_file():
        return {
            "name": "Flutter (web preview)",
            "command": ["flutter", "run", "-d", "chrome"],
            "url": "http://localhost:{port}",
            "default_port": 8083,
            "port_inject": "flag:--web-port=",
        }

    # 5. Android Gradle (no preview web)
    if (project_path / "build.gradle").is_file() or (project_path / "build.gradle.kts").is_file():
        return {
            "name": "Android (Gradle)",
            "command": ["./gradlew", "installDebug"],
            "url": "about:blank",
            "default_port": 0,
            "port_inject": None,
            "note": "Sin preview web. Compila en emulador/dispositivo.",
        }

    # 5b. Rails (Gemfile + bin/rails)
    if (project_path / "Gemfile").is_file() and ((project_path / "bin" / "rails").is_file() or (project_path / "bin" / "dev").is_file()):
        # Rails 8 trae bin/dev que arranca server + css watcher + jobs
        if (project_path / "bin" / "dev").is_file():
            return {
                "name": "Rails bin/dev (foreman)",
                "command": ["bin/dev"],
                "url": "http://localhost:{port}",
                "default_port": 3000,
                "port_inject": "env:PORT",
                "note": "bin/dev incluye server + css watcher + jobs.",
            }
        return {
            "name": "Rails server",
            "command": ["bin/rails", "server"],
            "url": "http://localhost:{port}",
            "default_port": 3000,
            "port_inject": "flag:-p",
        }

    # 6. Hugo
    if (project_path / "hugo.toml").is_file() or (project_path / "hugo.yaml").is_file() or (project_path / "config.toml").is_file():
        return {
            "name": "Hugo server",
            "command": ["hugo", "server"],
            "url": "http://localhost:{port}",
            "default_port": 1313,
            "port_inject": "flag:-p",
        }

    # 7. Astro standalone
    if (project_path / "astro.config.mjs").is_file() or (project_path / "astro.config.ts").is_file():
        return {
            "name": "Astro dev",
            "command": ["npm", "run", "dev", "--"],
            "url": "http://localhost:{port}",
            "default_port": 4321,
            "port_inject": "flag:--port",
        }

    # 8. Shopify theme
    if (project_path / "config" / "settings_schema.json").is_file():
        return {
            "name": "Shopify theme dev",
            "command": ["shopify", "theme", "dev"],
            "url": "http://127.0.0.1:{port}",
            "default_port": 9292,
            "port_inject": "flag:--port=",
            "note": "Requiere `shopify login` previo.",
        }

    # 9. HTML estático
    if (project_path / "index.html").is_file():
        return {
            "name": "Python http.server",
            "command": ["python3", "-m", "http.server"],
            "url": "http://localhost:{port}",
            "default_port": 8080,
            "port_inject": "flag:bare",  # python3 -m http.server <port>
        }

    return None
