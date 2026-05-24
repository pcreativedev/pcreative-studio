"""
db_provisioner — aprovisiona automáticamente BDs en containers Docker para
cada proyecto que cree ThemeForge.

Detecta si el proyecto necesita Postgres (drizzle/prisma/etc.) y, en ese caso:
  1. Lanza un container `themeforge-pg-<slug>` con puerto único.
  2. Persiste las credenciales en ~/.config/themeforge/db_provisions.json.
  3. Devuelve un DATABASE_URL listo para inyectar en .env.

Idempotente: si ya hay container para el slug, lo reutiliza (o lo levanta si
está parado).
"""
from __future__ import annotations

import json
import secrets
import shutil
import socket
import subprocess
import time
from pathlib import Path
from typing import Literal, TypedDict

import platform_compat as pc

HOME = Path.home()
CONFIG_DIR = pc.app_config_dir()
PROVISIONS_FILE = CONFIG_DIR / "db_provisions.json"

DbKind = Literal["postgres", "mysql", None]


class Provision(TypedDict):
    kind: str
    container: str
    volume: str
    port: int
    user: str
    password: str
    database: str
    url: str


# ─── detección ──────────────────────────────────────────────────────────


def detect_db_kind(project_path: Path) -> DbKind:
    """Heurística → devuelve qué tipo de BD necesita el proyecto, o None."""
    # 1) drizzle.config.{ts,js,mjs}
    for name in ("drizzle.config.ts", "drizzle.config.js", "drizzle.config.mjs"):
        f = project_path / name
        if f.is_file():
            try:
                txt = f.read_text(errors="ignore", encoding="utf-8").lower()
                if "postgresql" in txt or '"postgres"' in txt or "'postgres'" in txt:
                    return "postgres"
                if "mysql" in txt:
                    return "mysql"
            except Exception:
                pass

    # 2) prisma/schema.prisma
    prisma = project_path / "prisma" / "schema.prisma"
    if prisma.is_file():
        try:
            txt = prisma.read_text(errors="ignore", encoding="utf-8").lower()
            if 'provider = "postgresql"' in txt or "provider = 'postgresql'" in txt:
                return "postgres"
            if 'provider = "mysql"' in txt or "provider = 'mysql'" in txt:
                return "mysql"
        except Exception:
            pass

    # 3) package.json deps
    pkg = project_path / "package.json"
    if pkg.is_file():
        try:
            data = json.loads(pkg.read_text(errors="ignore", encoding="utf-8"))
            deps = {**(data.get("dependencies") or {}), **(data.get("devDependencies") or {})}
            if "postgres" in deps or "pg" in deps or "@neondatabase/serverless" in deps:
                return "postgres"
            if "mysql2" in deps or "mysql" in deps:
                return "mysql"
        except Exception:
            pass

    return None


# ─── docker helpers ─────────────────────────────────────────────────────


def docker_available() -> tuple[bool, str]:
    """Devuelve (ok, message). ok=False si docker no se puede invocar sin sudo."""
    if not shutil.which("docker"):
        return False, "docker no instalado"
    try:
        r = subprocess.run(
            ["docker", "info"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0:
            return True, "ok"
        if "permission denied" in (r.stderr + r.stdout).lower():
            return False, "Necesitas estar en el grupo `docker`. Haz logout/login tras `sudo usermod -aG docker $USER`."
        return False, f"docker info falla: {r.stderr.strip()[:200]}"
    except Exception as e:
        return False, f"docker info excepción: {e}"


def _docker(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", *args], capture_output=True, text=True, timeout=120)


# ─── persistencia ───────────────────────────────────────────────────────


def _load_provisions() -> dict[str, Provision]:
    try:
        return json.loads(PROVISIONS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_provisions(d: dict[str, Provision]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    PROVISIONS_FILE.write_text(json.dumps(d, indent=2, sort_keys=True), encoding="utf-8")


def _is_port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def _next_free_port(start: int = 5433) -> int:
    used = {p["port"] for p in _load_provisions().values()}
    for cand in range(start, start + 200):
        if cand not in used and _is_port_free(cand):
            return cand
    raise RuntimeError("No hay puertos libres en el rango 5433-5632")


# ─── provisioning Postgres ──────────────────────────────────────────────


PG_IMAGE = "postgres:17-alpine"
USER_PREFIX = "tf"


def provision_postgres_for(slug: str) -> Provision:
    """Idempotente. Si ya existe el container, lo reutiliza/arranca.
    Devuelve la provisión completa."""
    ok, msg = docker_available()
    if not ok:
        raise RuntimeError(f"docker no disponible: {msg}")

    provs = _load_provisions()
    container = f"themeforge-pg-{slug}"
    volume = container

    existing = provs.get(slug)
    if existing and existing["kind"] == "postgres":
        # ¿Container vivo? Si no, levantarlo.
        r = _docker("ps", "-a", "--filter", f"name=^{container}$", "--format", "{{.Status}}")
        status = r.stdout.strip()
        if status:
            if not status.lower().startswith("up "):
                _docker("start", container)
            _wait_for_postgres(container, existing["user"], existing["database"])
            return existing

    # No existe (o se borró el container) → crearlo
    port = existing["port"] if existing else _next_free_port()
    user = existing["user"] if existing else f"{USER_PREFIX}_{slug.replace('-','_')[:32]}"
    password = existing["password"] if existing else secrets.token_urlsafe(18)
    database = existing["database"] if existing else slug.replace("-", "_")

    # rm container existente si está roto
    _docker("rm", "-f", container)

    r = _docker(
        "run", "-d",
        "--name", container,
        "--restart", "unless-stopped",
        "-e", f"POSTGRES_USER={user}",
        "-e", f"POSTGRES_PASSWORD={password}",
        "-e", f"POSTGRES_DB={database}",
        "-p", f"127.0.0.1:{port}:5432",
        "-v", f"{volume}:/var/lib/postgresql/data",
        PG_IMAGE,
    )
    if r.returncode != 0:
        raise RuntimeError(f"docker run falló: {r.stderr.strip()[:400]}")

    _wait_for_postgres(container, user, database)

    prov: Provision = {
        "kind": "postgres",
        "container": container,
        "volume": volume,
        "port": port,
        "user": user,
        "password": password,
        "database": database,
        "url": f"postgresql://{user}:{password}@127.0.0.1:{port}/{database}",
    }
    provs[slug] = prov
    _save_provisions(provs)
    return prov


def _wait_for_postgres(container: str, user: str, database: str, timeout: int = 60) -> None:
    """Espera a que pg_isready devuelva ok."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = _docker("exec", container, "pg_isready", "-U", user, "-d", database)
        if r.returncode == 0 and "accepting" in r.stdout.lower():
            return
        time.sleep(1)
    raise RuntimeError(f"Postgres del container {container} no respondió a pg_isready en {timeout}s")


def cleanup_for(slug: str, *, also_volume: bool = False) -> None:
    """Para y elimina el container del slug. Si also_volume=True, borra
    también los datos (irreversible)."""
    provs = _load_provisions()
    prov = provs.get(slug)
    if not prov:
        return
    _docker("rm", "-f", prov["container"])
    if also_volume:
        _docker("volume", "rm", prov["volume"])
        del provs[slug]
    else:
        # mantenemos la entrada para poder re-provisionar conservando los datos
        pass
    _save_provisions(provs)


def get_provision(slug: str) -> Provision | None:
    return _load_provisions().get(slug)


# ─── CLI ────────────────────────────────────────────────────────────────


def _main() -> int:
    """CLI invocable desde el setup.sh tras clonar.

      python -m db_provisioner detect <project_path>
        → imprime "postgres" | "mysql" | (nada)
      python -m db_provisioner provision <slug>
        → imprime JSON con la provisión Postgres
      python -m db_provisioner cleanup <slug> [--volume]
        → para el container; si --volume, borra también los datos
    """
    import sys
    args = sys.argv[1:]
    if not args:
        print(_main.__doc__, file=sys.stderr)
        return 2

    cmd = args[0]
    if cmd == "detect":
        path = Path(args[1] if len(args) > 1 else ".")
        kind = detect_db_kind(path)
        if kind:
            print(kind)
        return 0

    if cmd == "provision":
        slug = args[1]
        prov = provision_postgres_for(slug)
        print(json.dumps(prov))
        return 0

    if cmd == "cleanup":
        slug = args[1]
        also = "--volume" in args
        cleanup_for(slug, also_volume=also)
        return 0

    print(f"comando desconocido: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main())
