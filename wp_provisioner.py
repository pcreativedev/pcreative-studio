"""
wp_provisioner — levanta un WordPress de desarrollo en Docker (WordPress +
MariaDB + wp-cli) para los stacks WordPress de ThemeForge.

Qué hace (idempotente por slug, análogo a db_provisioner):
  1. Crea una red `themeforge-wpnet-<slug>` y un MariaDB `themeforge-wpdb-<slug>`.
  2. Lanza WordPress `themeforge-wp-<slug>` en un puerto libre y monta el
     directorio del proyecto en `wp-content/themes/<slug>` (theme) o
     `wp-content/plugins/<slug>` (plugin).
  3. Instala WP core con wp-cli (admin/admin, sin asistente) vía un container
     `wordpress:cli` con `--volumes-from` del WP.
  4. Persiste todo en ~/.config/themeforge/wp_provisions.json y devuelve la URL.

NO activa el theme/plugin (al provisionar suele estar vacío — lo hace el agente
con wp-cli cuando ya tiene `style.css`/cabecera). El helper para activarlo se
documenta en WORDPRESS-DEV.md del proyecto.

CLI:
  python -m wp_provisioner provision <slug> <project_dir> <theme|plugin>
      → imprime JSON con la provisión
  python -m wp_provisioner down <slug> [--volume]
      → para los containers; con --volume borra también los datos
"""
from __future__ import annotations

import json
import secrets
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

import platform_compat as pc

CONFIG_DIR = pc.app_config_dir()
PROVISIONS_FILE = CONFIG_DIR / "wp_provisions.json"

WP_IMAGE = "wordpress:php8.3-apache"
DB_IMAGE = "mariadb:11"
CLI_IMAGE = "wordpress:cli-php8.3"
WP_PORT_START = 8090
# Plugin MCP oficial de WordPress (Automattic) — expone WP como servidor MCP.
WP_MCP_PLUGIN_ZIP = "https://github.com/Automattic/wordpress-mcp/releases/latest/download/wordpress-mcp.zip"
WP_MCP_SETTINGS = (
    '{"enabled":true,"enable_create_tools":true,"enable_update_tools":true,'
    '"enable_delete_tools":false,"features_adapter_enabled":true,'
    '"enable_rest_api_crud_tools":false}'
)


def docker_available() -> tuple[bool, str]:
    """Reutiliza la comprobación de db_provisioner."""
    try:
        from db_provisioner import docker_available as _da
        return _da()
    except Exception:
        if not shutil.which("docker"):
            return False, "docker no instalado"
        return True, "ok"


def _docker(*args: str, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", *args], capture_output=True, text=True, timeout=timeout)


def _load() -> dict[str, dict]:
    try:
        return json.loads(PROVISIONS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(d: dict[str, dict]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    PROVISIONS_FILE.write_text(json.dumps(d, indent=2, sort_keys=True), encoding="utf-8")


def _is_port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def _next_free_port(start: int = WP_PORT_START) -> int:
    used = {p.get("port") for p in _load().values()}
    for cand in range(start, start + 200):
        if cand not in used and _is_port_free(cand):
            return cand
    raise RuntimeError(f"No hay puertos libres en el rango {start}-{start + 200}")


def _wait_db(container: str, root_pw: str, timeout: int = 120) -> None:
    deadline = time.time() + timeout
    last = ""
    while time.time() < deadline:
        r = _docker("exec", container, "mariadb", "-uroot", f"-p{root_pw}", "-e", "SELECT 1", timeout=15)
        if r.returncode == 0:
            return
        last = (r.stderr or r.stdout).strip()[:200]
        time.sleep(2)
    raise RuntimeError(f"MariaDB ({container}) no respondió en {timeout}s: {last}")


def _wait_http(port: int, timeout: int = 150) -> None:
    """Espera a que WordPress sirva (install.php responde, aunque sea 30x/50x)."""
    deadline = time.time() + timeout
    url = f"http://127.0.0.1:{port}/wp-admin/install.php"
    while time.time() < deadline:
        try:
            urlopen(url, timeout=4)
            return
        except HTTPError:
            return  # responde HTTP → WordPress está arriba
        except Exception:
            time.sleep(2)
    raise RuntimeError(f"WordPress no respondió por HTTP en el puerto {port} ({timeout}s)")


def _write_project_files(project_dir: str, prov: dict) -> None:
    """Escribe WORDPRESS-DEV.md + el helper ./wp en el proyecto (desde Python,
    para no pelearnos con heredocs/comillas en el bash del setup) y los añade
    a .gitignore. Idempotente."""
    pd = Path(project_dir)
    kind = prov["mount_kind"]
    slug = prov["slug"]
    # Helper ./wp → wp-cli dentro del contenedor (comparte sus volúmenes).
    wp_helper = (
        "#!/usr/bin/env bash\n"
        "# wp-cli contra el WordPress de desarrollo de este proyecto (ThemeForge).\n"
        f'exec docker run --rm -i --volumes-from {prov["wp_container"]} '
        f'--network {prov["network"]} --user 33:33 -e HOME=/tmp '
        f'-e WORDPRESS_DB_HOST=wpdb -e WORDPRESS_DB_USER=wordpress '
        f'-e WORDPRESS_DB_PASSWORD={prov["db_password"]} -e WORDPRESS_DB_NAME=wordpress '
        f'{prov["wp_cli_image"]} wp "$@" --allow-root\n'
    )
    try:
        (pd / "wp").write_text(wp_helper, encoding="utf-8")
        (pd / "wp").chmod(0o755)
    except Exception:
        pass

    doc = f"""# WordPress de desarrollo (Docker) — ya instalado y funcional

ThemeForge ha levantado WordPress + MariaDB en Docker y **ha instalado WordPress**.
**El preview de ThemeForge ya apunta a este WordPress.** No hay que instalar nada.

- URL:    {prov["url"]}
- Admin:  {prov["url"]}/wp-admin  (usuario: `{prov["admin_user"]}` · contraseña: `{prov["admin_password"]}`)
- Tu {kind} está montado en `wp-content/{"themes" if kind == "theme" else "plugins"}/{slug}` —
  lo que edites aquí se ve en vivo en el WordPress del preview.

## Activar tu {kind}

Cuando tenga su cabecera ({"style.css" if kind == "theme" else "cabecera de plugin"}), actívalo:

```bash
./wp {kind} activate {slug}
```

`./wp` ejecuta wp-cli dentro del contenedor. Ej.: `./wp {kind} list`, `./wp option get siteurl`.

## Gestionar el entorno

- Parar/borrar: `python3 -m wp_provisioner down {slug}` (con `--volume` borra también los datos).
- Contenedores: `{prov["wp_container"]}` (WordPress) y `{prov["db_container"]}` (MariaDB).
"""
    try:
        (pd / "WORDPRESS-DEV.md").write_text(doc, encoding="utf-8")
    except Exception:
        pass

    # .mcp.json — servidor MCP de WordPress para Claude Code (bridge oficial de
    # Automattic + application password). Permite al agente operar WP por MCP.
    if prov.get("app_password"):
        mcp_cfg = {
            "mcpServers": {
                "wordpress": {
                    "command": "npx",
                    "args": ["-y", "@automattic/mcp-wordpress-remote@latest"],
                    "env": {
                        "WP_API_URL": prov["url"] + "/",
                        "WP_API_USERNAME": prov["admin_user"],
                        "WP_API_PASSWORD": prov["app_password"],
                        "LOG_FILE": "/tmp/wpmcp.log",
                    },
                }
            }
        }
        try:
            (pd / ".mcp.json").write_text(json.dumps(mcp_cfg, indent=2), encoding="utf-8")
        except Exception:
            pass

    # .gitignore (no versionar artefactos del entorno local).
    try:
        gi = pd / ".gitignore"
        existing = gi.read_text(encoding="utf-8") if gi.exists() else ""
        lines = set(existing.splitlines())
        add = [e for e in ("WORDPRESS-DEV.md", "/wp", ".mcp.json") if e not in lines]
        if add:
            with gi.open("a", encoding="utf-8") as f:
                if existing and not existing.endswith("\n"):
                    f.write("\n")
                f.write("\n".join(add) + "\n")
    except Exception:
        pass


def _wpcli(wp_container: str, net: str, db_pw: str, *args: str, timeout: int = 300) -> subprocess.CompletedProcess:
    """wp-cli contra el WP del contenedor. CLAVE: el wp-config de la imagen usa
    getenv_docker(), así que el contenedor CLI necesita las MISMAS env vars de BD;
    y corre como UID 33 (www-data de la imagen apache) para poder escribir en el
    volumen. Sin esto, wp-cli no conecta a la BD ni puede instalar plugins."""
    return _docker(
        "run", "--rm",
        "--volumes-from", wp_container,
        "--network", net,
        "--user", "33:33",
        "-e", "HOME=/tmp",
        "-e", "WORDPRESS_DB_HOST=wpdb",
        "-e", "WORDPRESS_DB_USER=wordpress",
        "-e", f"WORDPRESS_DB_PASSWORD={db_pw}",
        "-e", "WORDPRESS_DB_NAME=wordpress",
        CLI_IMAGE, "wp", *args, "--allow-root",
        timeout=timeout,
    )


def _configure_wp(wp: str, net: str, db_pw: str, port: int, slug: str, admin_pw: str) -> dict:
    """Idempotente: instala WP core + permalinks + plugin MCP (activado) + crea un
    application password para el bridge MCP. Devuelve {installed, mcp_enabled, app_password}."""
    url = f"http://localhost:{port}"
    _wpcli(wp, net, db_pw, "core", "install", f"--url={url}", f"--title={slug}",
           "--admin_user=admin", f"--admin_password={admin_pw}",
           "--admin_email=admin@example.com", "--skip-email")
    installed = _wpcli(wp, net, db_pw, "core", "is-installed").returncode == 0
    if not installed:
        return {"installed": False, "mcp_enabled": False, "app_password": ""}
    # Permalinks bonitos (necesario para que /wp-json/ rutee).
    _wpcli(wp, net, db_pw, "rewrite", "structure", "/%postname%/", "--hard")

    # Plugin MCP (Automattic) + activarlo.
    mcp_enabled = False
    try:
        _wpcli(wp, net, db_pw, "plugin", "install", WP_MCP_PLUGIN_ZIP, "--activate", timeout=300)
        _wpcli(wp, net, db_pw, "option", "update", "wordpress_mcp_settings", "--format=json", WP_MCP_SETTINGS)
        mcp_enabled = _wpcli(wp, net, db_pw, "plugin", "is-active", "wordpress-mcp").returncode == 0
    except Exception:
        pass

    # Application password para el bridge MCP (idempotente: limpia y crea uno).
    app_password = ""
    try:
        _wpcli(wp, net, db_pw, "user", "application-password", "delete", "admin", "themeforge-mcp")
        r = _wpcli(wp, net, db_pw, "user", "application-password", "create", "admin", "themeforge-mcp", "--porcelain")
        if r.returncode == 0:
            app_password = (r.stdout or "").strip().splitlines()[-1].strip() if r.stdout.strip() else ""
    except Exception:
        pass
    return {"installed": True, "mcp_enabled": mcp_enabled, "app_password": app_password}


def provision_wordpress_for(slug: str, project_dir: str, kind: str = "theme") -> dict:
    """Idempotente. kind ∈ {'theme','plugin'}. Devuelve la provisión completa."""
    ok, msg = docker_available()
    if not ok:
        raise RuntimeError(f"docker no disponible: {msg}")

    if kind not in ("theme", "plugin"):
        kind = "theme"
    subdir = "themes" if kind == "theme" else "plugins"

    provs = _load()
    net = f"themeforge-wpnet-{slug}"
    wp = f"themeforge-wp-{slug}"
    db = f"themeforge-wpdb-{slug}"
    html_vol = f"{wp}-html"
    db_vol = f"{db}-data"
    mount_target = f"/var/www/html/wp-content/{subdir}/{slug}"

    existing = provs.get(slug)
    port = existing["port"] if existing else _next_free_port()
    db_pw = existing["db_password"] if existing else secrets.token_urlsafe(16)
    admin_pw = existing["admin_password"] if existing else "admin"

    # Idempotente: si el WP del slug ya existe, lo arrancamos y devolvemos.
    r = _docker("ps", "-a", "--filter", f"name=^{wp}$", "--format", "{{.Status}}")
    if existing and r.stdout.strip():
        if not r.stdout.strip().lower().startswith("up "):
            _docker("start", db)
            _docker("start", wp)
        _wait_http(port)
        cfg = _configure_wp(wp, net, db_pw, port, slug, existing.get("admin_password", "admin"))
        existing.update(installed=cfg["installed"], mcp_enabled=cfg["mcp_enabled"], app_password=cfg["app_password"])
        provs[slug] = existing
        _save(provs)
        _write_project_files(project_dir, existing)
        return existing

    # Red (idempotente).
    _docker("network", "create", net)

    # MariaDB.
    _docker("rm", "-f", db)
    r = _docker(
        "run", "-d",
        "--name", db,
        "--network", net,
        "--network-alias", "wpdb",
        "--restart", "unless-stopped",
        "-e", "MARIADB_DATABASE=wordpress",
        "-e", "MARIADB_USER=wordpress",
        "-e", f"MARIADB_PASSWORD={db_pw}",
        "-e", f"MARIADB_ROOT_PASSWORD={db_pw}",
        "-v", f"{db_vol}:/var/lib/mysql",
        DB_IMAGE,
        timeout=600,  # primer pull puede tardar
    )
    if r.returncode != 0:
        raise RuntimeError(f"docker run mariadb falló: {r.stderr.strip()[:400]}")
    _wait_db(db, db_pw)

    # WordPress (monta el proyecto en wp-content/<subdir>/<slug>).
    Path(project_dir).mkdir(parents=True, exist_ok=True)
    _docker("rm", "-f", wp)
    r = _docker(
        "run", "-d",
        "--name", wp,
        "--network", net,
        "--restart", "unless-stopped",
        "-p", f"127.0.0.1:{port}:80",
        "-e", "WORDPRESS_DB_HOST=wpdb",
        "-e", "WORDPRESS_DB_USER=wordpress",
        "-e", f"WORDPRESS_DB_PASSWORD={db_pw}",
        "-e", "WORDPRESS_DB_NAME=wordpress",
        "-e", "WORDPRESS_DEBUG=1",
        # entorno local → permite Application Passwords sobre HTTP (las usa el MCP).
        "-e", "WP_ENVIRONMENT_TYPE=local",
        "-v", f"{html_vol}:/var/www/html",
        "-v", f"{project_dir}:{mount_target}",
        WP_IMAGE,
        timeout=600,
    )
    if r.returncode != 0:
        raise RuntimeError(f"docker run wordpress falló: {r.stderr.strip()[:400]}")
    _wait_http(port)

    # Configurar WP: core install + permalinks + plugin MCP + app-password.
    url = f"http://localhost:{port}"
    cfg = _configure_wp(wp, net, db_pw, port, slug, admin_pw)

    prov = {
        "kind": "wordpress",
        "mount_kind": kind,
        "slug": slug,
        "port": port,
        "url": url,
        "admin_user": "admin",
        "admin_password": admin_pw,
        "db_password": db_pw,
        "network": net,
        "wp_container": wp,
        "db_container": db,
        "html_volume": html_vol,
        "db_volume": db_vol,
        "mount_target": mount_target,
        "wp_cli_image": CLI_IMAGE,
        "installed": cfg["installed"],
        "mcp_enabled": cfg["mcp_enabled"],
        "app_password": cfg["app_password"],
    }
    provs[slug] = prov
    _save(provs)
    _write_project_files(project_dir, prov)
    return prov


def down_for(slug: str, *, also_volume: bool = False) -> None:
    provs = _load()
    prov = provs.get(slug)
    if not prov:
        return
    _docker("rm", "-f", prov.get("wp_container", ""))
    _docker("rm", "-f", prov.get("db_container", ""))
    if also_volume:
        _docker("volume", "rm", prov.get("html_volume", ""))
        _docker("volume", "rm", prov.get("db_volume", ""))
        _docker("network", "rm", prov.get("network", ""))
        del provs[slug]
        _save(provs)


def get_provision(slug: str) -> dict | None:
    return _load().get(slug)


def _main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__, file=sys.stderr)
        return 2
    cmd = args[0]
    if cmd == "provision":
        if len(args) < 3:
            print("uso: provision <slug> <project_dir> [theme|plugin]", file=sys.stderr)
            return 2
        slug, project_dir = args[1], args[2]
        kind = args[3] if len(args) > 3 else "theme"
        prov = provision_wordpress_for(slug, project_dir, kind)
        print(json.dumps(prov))
        return 0
    if cmd == "down":
        down_for(args[1], also_volume="--volume" in args)
        return 0
    print(f"comando desconocido: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main())
