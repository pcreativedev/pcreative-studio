"""
pixel_office — integración con un visualizer pixel art de sesiones de
agentes IA. Por defecto apunta al fork `pcreativedev/pixel-office-openclaw`
(MIT, basado en `neomatrix25/pixel-office-openclaw`), que escanea tanto
sesiones OpenClaw como Claude Code (`~/.claude/projects/*/`) y muestra
avatares en una oficina virtual + dashboard web en localhost:3002.

Pcreative Studio lo gestiona así:
  · Auto-detect: busca instalación local en rutas conocidas.
  · Auto-install: si no está, clona+npm install con consentimiento.
  · Auto-launch: arranca `node server.js` en background con Pcreative Studio.
  · Tab embebida: cada ProjectWindow tiene un tab "🎮 Office" con
    WebEngineView a http://localhost:3002.

Como el visualizer lee directamente de `~/.claude/projects/*/*.jsonl`
(mtime + último mensaje de cada sesión), NO necesita registrar hooks en
`~/.claude/settings.json`. Es un puente puramente lector.
"""
from __future__ import annotations

import os
import shutil
import socket
import subprocess
from pathlib import Path

HOME = Path.home()
INSTALL_DIR = HOME / ".local" / "share" / "themeforge" / "pixel-office-openclaw"
REPO_URL = "https://github.com/pcreativedev/pixel-office-openclaw.git"
DASHBOARD_PORT = 3002
DASHBOARD_URL = f"http://localhost:{DASHBOARD_PORT}/"

# Rutas alternativas donde el user puede haber clonado el repo a mano.
ALT_LOCATIONS = (
    HOME / "Proyectos" / "pixel-office-openclaw",
    HOME / "pixel-office-openclaw",
)


def find_install_dir() -> Path | None:
    """Busca la ruta donde está instalado el visualizer. Devuelve None
    si no está en ninguna de las rutas conocidas."""
    candidates = [INSTALL_DIR, *ALT_LOCATIONS]
    for c in candidates:
        if (c / "package.json").is_file():
            return c
    return None


def is_dashboard_up() -> bool:
    """Comprueba si el dashboard web (localhost:3002) responde."""
    try:
        with socket.create_connection(("127.0.0.1", DASHBOARD_PORT), timeout=1):
            return True
    except OSError:
        return False


def install(node_bin: str = "node", git_bin: str = "git") -> tuple[bool, str]:
    """Clona el repo y ejecuta `npm install` + `npm run build`.

    Returns: (success, message) — el message es legible para mostrar
    al user en un QMessageBox.
    """
    if not shutil.which(git_bin):
        return False, "git no instalado"
    if not shutil.which("npm"):
        return False, "npm no instalado (necesitas Node 20+)"

    INSTALL_DIR.parent.mkdir(parents=True, exist_ok=True)

    # Clone o pull
    if INSTALL_DIR.is_dir() and (INSTALL_DIR / ".git").is_dir():
        r = subprocess.run(
            ["git", "-C", str(INSTALL_DIR), "pull", "--ff-only"],
            capture_output=True, text=True, timeout=120,
        )
        if r.returncode != 0:
            return False, f"git pull falló: {r.stderr.strip()[:300]}"
    else:
        if INSTALL_DIR.exists():
            shutil.rmtree(INSTALL_DIR, ignore_errors=True)
        r = subprocess.run(
            ["git", "clone", "--depth", "1", REPO_URL, str(INSTALL_DIR)],
            capture_output=True, text=True, timeout=300,
        )
        if r.returncode != 0:
            return False, f"git clone falló: {r.stderr.strip()[:300]}"

    # npm install
    r = subprocess.run(
        ["npm", "install", "--no-audit", "--no-fund"],
        cwd=str(INSTALL_DIR),
        capture_output=True, text=True, timeout=600,
    )
    if r.returncode != 0:
        return False, f"npm install falló: {(r.stderr or r.stdout).strip()[:400]}"

    # npm run build (genera dist/ que server.js sirve)
    r = subprocess.run(
        ["npm", "run", "build"],
        cwd=str(INSTALL_DIR),
        capture_output=True, text=True, timeout=300,
    )
    if r.returncode != 0:
        return False, f"npm run build falló: {(r.stderr or r.stdout).strip()[:400]}"

    return True, f"Instalado en {INSTALL_DIR}"


def launch_background() -> subprocess.Popen | None:
    """Arranca el dashboard en background. Devuelve el Popen o None si
    no se pudo arrancar (no instalado, node no encontrado). Si el
    dashboard ya está arriba, devuelve None sin duplicar."""
    if is_dashboard_up():
        return None
    install_dir = find_install_dir()
    if install_dir is None:
        return None
    node = shutil.which("node")
    if node is None:
        return None
    try:
        # Lanzamos `node server.js` directamente (no `npm start`) para
        # que el proceso hijo sea node y se pueda matar limpio.
        env = {**os.environ, "PORT": str(DASHBOARD_PORT)}
        proc = subprocess.Popen(
            [node, "server.js"],
            cwd=str(install_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
        )
        return proc
    except Exception:
        return None


def stop(proc: subprocess.Popen | None) -> None:
    """Para el proceso del dashboard si lo lanzamos nosotros."""
    if proc is None:
        return
    try:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
    except Exception:
        pass


def status() -> dict:
    """Devuelve un dict con el estado actual de la integración."""
    install_dir = find_install_dir()
    return {
        "installed": install_dir is not None,
        "install_dir": str(install_dir) if install_dir else None,
        "dashboard_up": is_dashboard_up(),
        "dashboard_url": DASHBOARD_URL,
    }
