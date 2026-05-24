"""dependency_setup.py — Detección e instalación automática de las
herramientas externas que ThemeForge invoca como subprocesos.

ThemeForge bundlea Python + PyQt6 (vía PyInstaller en Win/Mac, o el system
python en Linux), pero en runtime necesita binarios externos que NO van en
el bundle: Node.js, git, GitHub CLI y los CLIs de los agentes de IA
(Claude / Codex / Gemini / OpenCode) más netlify-cli para deploys.

Este módulo:
  - Define el catálogo de herramientas (`TOOLS`) con su id de instalación
    por package manager y OS.
  - Detecta cuáles faltan (`detect_missing`).
  - Genera los comandos de instalación correctos para el OS actual
    (`install_plan`), respetando el orden (Node antes que los paquetes npm).

La UI vive en `dependency_wizard.py` (DependencyWizard dialog), que ejecuta
el plan con QProcess y muestra progreso. Mantener la lógica aquí pura
(sin Qt) facilita testearla y reutilizarla desde el MCP server o un CLI.
"""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field

import platform_compat as pc


@dataclass(frozen=True)
class Tool:
    key: str                      # id interno
    name: str                     # nombre legible
    binary: str                   # binario a buscar en PATH
    description: str              # para qué sirve (UI)
    required: bool = False        # True → la app no funciona sin esto
    # Categoría para agrupar en la UI: "core" (Node/git, imprescindible),
    # "ai" (CLIs de agentes), "stack" (runtimes de stacks concretos).
    category: str = "core"
    winget: str | None = None     # winget package id (Windows)
    brew: str | None = None       # homebrew formula (macOS)
    # Paquetes de sistema por gestor Linux (paru/pacman usan el mismo id):
    pacman: str | None = None
    apt: str | None = None
    dnf: str | None = None
    # Si se instala vía npm global (cross-platform, requiere Node):
    npm: str | None = None
    # Fallback en Windows SIN winget (Win10 antiguo, ediciones sin App
    # Installer): descarga directa del instalador oficial.
    win_url: str | None = None        # URL del .msi / .exe
    win_kind: str | None = None       # "msi" o "exe"
    win_args: str = ""                # flags de instalación silenciosa
    # Script de instalación NATIVO en PowerShell (no necesita npm/Node).
    # Lo usan Claude Code y Codex — más robusto que npm.
    win_ps_install: str | None = None


# Catálogo. El orden importa: Node primero (los npm dependen de él).
TOOLS: list[Tool] = [
    Tool("node", "Node.js", "node",
         "Runtime para scaffold de stacks JS y el terminal embebido.",
         required=True,
         winget="OpenJS.NodeJS.LTS", brew="node",
         pacman="nodejs npm", apt="nodejs npm", dnf="nodejs npm",
         win_url="https://nodejs.org/dist/v22.11.0/node-v22.11.0-x64.msi",
         win_kind="msi", win_args="/quiet /norestart"),
    Tool("git", "Git", "git",
         "Control de versiones — clonar, commit, push.",
         required=True,
         winget="Git.Git", brew="git",
         pacman="git", apt="git", dnf="git",
         win_url="https://github.com/git-for-windows/git/releases/download/"
                 "v2.47.1.windows.1/Git-2.47.1-64-bit.exe",
         win_kind="exe", win_args="/VERYSILENT /NORESTART /NOCANCEL /SP- /SUPPRESSMSGBOXES"),
    Tool("gh", "GitHub CLI", "gh",
         "Crear repos, releases y PRs desde la app.",
         required=False, category="core",
         winget="GitHub.cli", brew="gh",
         pacman="github-cli", apt="gh", dnf="gh",
         win_url="https://github.com/cli/cli/releases/download/"
                 "v2.63.2/gh_2.63.2_windows_amd64.msi",
         win_kind="msi", win_args="/quiet /norestart"),
    # ── Agentes de IA (npm / script oficial) ────────────────────────────
    Tool("claude", "Claude Code", "claude",
         "Agente IA de Anthropic (recomendado).",
         required=False, category="ai",
         winget="Anthropic.ClaudeCode",
         npm="@anthropic-ai/claude-code",
         # Instalador nativo oficial (no necesita Node). Requiere git.
         win_ps_install="irm https://claude.ai/install.ps1 | iex"),
    Tool("codex", "Codex CLI", "codex",
         "Agente IA de OpenAI.",
         required=False, category="ai",
         npm="@openai/codex",
         win_ps_install='irm https://chatgpt.com/codex/install.ps1 | iex'),
    Tool("gemini", "Gemini CLI", "gemini",
         "Agente IA de Google.",
         required=False, category="ai",
         npm="@google/gemini-cli"),
    Tool("opencode", "OpenCode", "opencode",
         "Agente IA open source.",
         required=False, category="ai",
         npm="opencode-ai"),
    Tool("netlify", "Netlify CLI", "netlify",
         "Deploy de demos públicas (botón 🚀 Demo).",
         required=False, category="ai",
         npm="netlify-cli"),
    # ── Runtimes de stacks concretos (winget IDs verificados) ───────────
    # Solo se instalan si el usuario va a usar un stack que los necesita.
    Tool("python", "Python 3.12", "python",
         "Stacks FastAPI y Django.",
         required=False, category="stack",
         winget="Python.Python.3.12", brew="python@3.12",
         pacman="python", apt="python3 python3-venv python3-pip", dnf="python3",
         win_url="https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe",
         win_kind="exe", win_args="/quiet InstallAllUsers=1 PrependPath=1 Include_pip=1"),
    Tool("java", "Java (OpenJDK 21)", "java",
         "Stacks Spring Boot, Ktor y Kotlin Compose.",
         required=False, category="stack",
         winget="Microsoft.OpenJDK.21", brew="openjdk",
         pacman="jdk-openjdk", apt="default-jdk", dnf="java-latest-openjdk"),
    Tool("rust", "Rust", "cargo",
         "Stacks Tauri y Axum.",
         required=False, category="stack",
         winget="Rustlang.Rustup", brew="rustup", pacman="rustup"),
    Tool("go", "Go", "go",
         "Stack Fiber (Go).",
         required=False, category="stack",
         winget="GoLang.Go", brew="go", pacman="go", apt="golang-go", dnf="golang"),
    Tool("bun", "Bun", "bun",
         "Stacks Hono (Bun) y Elysia.",
         required=False, category="stack",
         winget="Oven-sh.Bun", brew="bun", pacman="bun-bin"),
    Tool("deno", "Deno", "deno",
         "Stack Fresh (Deno).",
         required=False, category="stack",
         winget="DenoLand.Deno", brew="deno", pacman="deno"),
    Tool("ruby", "Ruby", "ruby",
         "Stack Rails.",
         required=False, category="stack",
         winget="RubyInstallerTeam.Ruby.3.3", brew="ruby", pacman="ruby", apt="ruby-full"),
    Tool("hugo", "Hugo Extended", "hugo",
         "Stack Hugo (sitios estáticos).",
         required=False, category="stack",
         winget="Hugo.Hugo.Extended", brew="hugo", pacman="hugo", apt="hugo", dnf="hugo"),
    # PHP/Composer: sin winget oficial fiable → en Windows el wizard avisará
    # (instalación manual). brew/pacman/apt sí los cubren en Mac/Linux.
    Tool("php", "PHP", "php",
         "Stacks Laravel y WordPress (block theme / plugin).",
         required=False, category="stack",
         brew="php", pacman="php", apt="php-cli", dnf="php-cli"),
    Tool("composer", "Composer", "composer",
         "Gestor de paquetes PHP (Laravel). Requiere PHP.",
         required=False, category="stack",
         brew="composer", pacman="composer", apt="composer", dnf="composer"),
]


# Qué runtime extra necesita cada stack (los que NO son Node puro). Los
# stacks JS/TS no aparecen → les basta `node` (core). flutter/elixir quedan
# fuera: su SDK no se instala bien por gestor → el scaffold ya avisa.
STACK_REQUIRES: dict[str, list[str]] = {
    "laravel-inertia":  ["php", "composer"],
    "wordpress-block":  ["php", "composer"],
    "wordpress-plugin": ["php", "composer"],
    "spring-boot":      ["java"],
    "ktor-server":      ["java"],
    "kotlin-compose":   ["java"],
    "tauri-react":      ["rust"],
    "rust-axum":        ["rust"],
    "go-fiber":         ["go"],
    "hono-bun":         ["bun"],
    "bun-elysia":       ["bun"],
    "deno-fresh":       ["deno"],
    "fastapi":          ["python"],
    "django-tailwind":  ["python"],
    "rails-tailwind":   ["ruby"],
    "hugo":             ["hugo"],
}


def is_installed(tool: Tool) -> bool:
    return shutil.which(tool.binary) is not None


def tools_for_stack(stack_key: str) -> list[Tool]:
    """Runtimes extra que necesita un stack (además de node/git)."""
    by_key = {t.key: t for t in TOOLS}
    return [by_key[k] for k in STACK_REQUIRES.get(stack_key, []) if k in by_key]


def missing_tools_for_stack(stack_key: str) -> list[Tool]:
    """Runtimes del stack que faltan en PATH."""
    return [t for t in tools_for_stack(stack_key) if not is_installed(t)]


def detect_missing(only_required: bool = False) -> list[Tool]:
    """Devuelve las herramientas que faltan en PATH."""
    out = []
    for t in TOOLS:
        if only_required and not t.required:
            continue
        if not is_installed(t):
            out.append(t)
    return out


def detect_present() -> list[Tool]:
    return [t for t in TOOLS if is_installed(t)]


def native_package_manager() -> tuple[str, list[str]] | None:
    """Devuelve (nombre, argv_base_install) del gestor nativo del OS, o
    None si no se encuentra ninguno.

    - Windows: winget
    - macOS: brew
    - Linux: paru → yay → pacman (con sudo) → apt → dnf
    """
    if pc.IS_WINDOWS:
        if shutil.which("winget"):
            return "winget", ["winget", "install", "--silent",
                              "--accept-source-agreements",
                              "--accept-package-agreements", "--id"]
        return None
    if pc.IS_MACOS:
        if shutil.which("brew"):
            return "brew", ["brew", "install"]
        return None
    # Linux
    if shutil.which("paru"):
        return "paru", ["paru", "-S", "--noconfirm", "--needed"]
    if shutil.which("yay"):
        return "yay", ["yay", "-S", "--noconfirm", "--needed"]
    if shutil.which("pacman"):
        return "pacman", ["sudo", "pacman", "-S", "--noconfirm", "--needed"]
    if shutil.which("apt"):
        return "apt", ["sudo", "apt", "install", "-y"]
    if shutil.which("dnf"):
        return "dnf", ["sudo", "dnf", "install", "-y"]
    return None


def _native_pkg_id(tool: Tool, pm_name: str) -> str | None:
    """El identificador del paquete para el gestor nativo dado."""
    return {
        "winget": tool.winget,
        "brew": tool.brew,
        "paru": tool.pacman,
        "yay": tool.pacman,
        "pacman": tool.pacman,
        "apt": tool.apt,
        "dnf": tool.dnf,
    }.get(pm_name)


@dataclass
class InstallStep:
    label: str            # texto para la UI ("Instalando Node.js…")
    argv: list[str]       # comando a ejecutar
    tool_key: str         # qué tool cubre


def install_plan(tools: list[Tool]) -> tuple[list[InstallStep], list[str]]:
    """Construye el plan de instalación ordenado para el OS actual.

    Devuelve (steps, warnings). `warnings` lista herramientas que no se
    pueden instalar automáticamente (sin método para este OS/PM).

    Reglas:
      - Node siempre primero (los paquetes npm lo necesitan).
      - Si una tool tiene id nativo (winget/brew/pacman/…) se usa el gestor
        nativo. Si solo tiene `npm`, se usa `npm install -g` (tras Node).
      - Si no hay ni nativo ni npm para este OS → warning.
    """
    steps: list[InstallStep] = []
    warnings: list[str] = []

    pm = native_package_manager()
    pm_name = pm[0] if pm else None
    pm_base = pm[1] if pm else None

    # Ordena: Node primero, luego git, luego el resto.
    order = {"node": 0, "git": 1}
    tools_sorted = sorted(tools, key=lambda t: order.get(t.key, 9))

    npm_installs_needed = any(t.npm and not _native_pkg_id(t, pm_name or "") for t in tools_sorted)
    node_will_be_installed = any(t.key == "node" for t in tools_sorted)

    for t in tools_sorted:
        native_id = _native_pkg_id(t, pm_name or "") if pm_name else None
        if native_id:
            # Gestor nativo. winget usa --id; el resto pasa el id (o varios) suelto.
            if pm_name == "winget":
                argv = pm_base + [native_id]
            else:
                # pacman/apt pueden recibir varios paquetes ("nodejs npm")
                argv = pm_base + native_id.split()
            steps.append(InstallStep(f"Instalando {t.name} ({pm_name})…", argv, t.key))
        elif pc.IS_WINDOWS and t.win_ps_install:
            # Instalador nativo PowerShell (Claude/Codex) — no depende de npm.
            steps.append(InstallStep(
                f"Instalando {t.name} (instalador oficial)…",
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-Command", t.win_ps_install], t.key))
        elif pc.IS_WINDOWS and t.win_url:
            # Windows sin winget → descarga directa del instalador oficial.
            steps.append(InstallStep(
                f"Descargando e instalando {t.name} (instalador oficial)…",
                _win_direct_install_argv(t), t.key))
        elif t.npm:
            # npm global. En Windows lo lanzamos por `cmd /c` para que resuelva
            # npm.cmd (QProcess no encuentra "npm" a secas en Windows).
            if pc.IS_WINDOWS:
                argv = ["cmd", "/c", "npm", "install", "-g", t.npm]
            else:
                argv = ["npm", "install", "-g", t.npm]
            steps.append(InstallStep(f"Instalando {t.name} (npm)…", argv, t.key))
        else:
            warnings.append(
                f"{t.name}: sin método de instalación automática para "
                f"{pc.platform_label()}. Instálalo manualmente."
            )

    if not pm_name and not pc.IS_WINDOWS:
        warnings.insert(
            0,
            f"No se detectó gestor de paquetes nativo en {pc.platform_label()}. "
            "Las tools nativas (Node, git, gh) tendrás que instalarlas a mano."
        )
    elif not pm_name and pc.IS_WINDOWS:
        warnings.insert(
            0,
            "winget no está disponible — usando descarga directa de los "
            "instaladores oficiales. Reinicia ThemeForge al terminar para "
            "que el PATH actualizado (Node/git) se vea."
        )

    return steps, warnings


def _win_direct_install_argv(tool: Tool) -> list[str]:
    """Comando PowerShell que descarga el instalador oficial de `tool` y lo
    ejecuta en silencio. Para Windows sin winget."""
    if tool.win_kind == "msi":
        run = (f'$o="$env:TEMP\\tf_{tool.key}.msi"; '
               f'Invoke-WebRequest "{tool.win_url}" -OutFile $o -UseBasicParsing; '
               f'Start-Process msiexec -Wait -ArgumentList "/i `"$o`" {tool.win_args}"')
    else:  # exe
        run = (f'$o="$env:TEMP\\tf_{tool.key}.exe"; '
               f'Invoke-WebRequest "{tool.win_url}" -OutFile $o -UseBasicParsing; '
               f'Start-Process $o -Wait -ArgumentList "{tool.win_args}"')
    return ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", run]


def summary() -> dict:
    """Snapshot del estado para UI / MCP / diagnóstico."""
    present = detect_present()
    missing = detect_missing()
    return {
        "platform": pc.platform_label(),
        "package_manager": (native_package_manager() or ("none", []))[0],
        "present": [t.key for t in present],
        "missing": [t.key for t in missing],
        "missing_required": [t.key for t in missing if t.required],
    }
