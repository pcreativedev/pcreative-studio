"""
ai_providers — registro de proveedores de IA soportados por ThemeForge.

Cada provider mapea a un CLI subyacente + método de autenticación.

  · claude              → `claude`   (Pro/Max OAuth)
  · claude-api          → `claude`   (ANTHROPIC_API_KEY)
  · codex               → `codex`    (ChatGPT OAuth)
  · codex-api           → `codex`    (OPENAI_API_KEY vía `codex login --with-api-key`)
  · gemini              → `gemini`   (Google OAuth o GEMINI_API_KEY)
  · opencode            → `opencode` (multi-provider, `opencode auth login`)
  · openrouter          → `opencode` (OPENROUTER_API_KEY, modelo `openrouter/...`)

Keys de API se guardan en ~/.config/themeforge/keys.json (chmod 0600).
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import stat
import subprocess
from pathlib import Path

import platform_compat as pc

HOME = Path.home()
CONFIG_DIR = pc.app_config_dir()
KEYS_PATH = CONFIG_DIR / "keys.json"

# ─── Registro de providers ─────────────────────────────────────────────
# `command` es el binario CLI. `context_file` se usa al generar el MD de
# contexto del proyecto. `autoskills_flag` se pasa a npx autoskills (None
# si el agente no es soportado todavía). `auth_kind` define cómo
# detectamos/configuramos la auth:
#   - "oauth": login interactivo del CLI (claude /login, codex login, gemini, opencode auth login)
#   - "api"  : la clave va por env var; usamos KEYS_PATH para guardarla
PROVIDERS: dict[str, dict] = {
    "claude": {
        "name": "Claude Code (Pro/Max OAuth)",
        "short": "Claude Code",
        "command": "claude",
        "context_file": "CLAUDE.md",
        "autoskills_flag": "claude",
        "auth_kind": "oauth",
        "login_argv": ["claude", "/login"],   # claude abre browser
        "logout_argv": ["claude", "/logout"],
        "model_hint": "Claude (cuenta Pro/Max)",
    },
    "claude-api": {
        "name": "Claude Code (API key)",
        "short": "Claude API",
        "command": "claude",
        "context_file": "CLAUDE.md",
        "autoskills_flag": "claude",
        "auth_kind": "api",
        "env_var": "ANTHROPIC_API_KEY",
        "key_id": "anthropic",
        "key_url": "https://console.anthropic.com/settings/keys",
        "model_hint": "Claude vía API directa",
    },
    "codex": {
        "name": "Codex CLI (ChatGPT OAuth)",
        "short": "Codex",
        "command": "codex",
        "context_file": "AGENTS.md",
        "autoskills_flag": "codex",
        "auth_kind": "oauth",
        "login_argv": ["codex", "login"],
        "logout_argv": ["codex", "logout"],
        "model_hint": "Codex (cuenta ChatGPT Plus/Pro)",
    },
    "codex-api": {
        "name": "Codex CLI (OpenAI API key)",
        "short": "Codex API",
        "command": "codex",
        "context_file": "AGENTS.md",
        "autoskills_flag": "codex",
        "auth_kind": "api",
        "env_var": "OPENAI_API_KEY",
        "key_id": "openai",
        "key_url": "https://platform.openai.com/api-keys",
        # codex necesita registrarse via `codex login --with-api-key` (stdin)
        "post_key_argv": ["codex", "login", "--with-api-key"],
        "model_hint": "Codex vía OpenAI API",
    },
    "gemini": {
        "name": "Gemini CLI (Google)",
        "short": "Gemini",
        "command": "gemini",
        "context_file": "GEMINI.md",
        "autoskills_flag": "gemini",  # autoskills v0.3.6+ ya soporta gemini
        "auth_kind": "oauth_or_api",
        # gemini lanza OAuth browser en el primer arranque; no hay subcomando login
        "login_argv": ["gemini"],
        "env_var": "GEMINI_API_KEY",
        "key_id": "gemini",
        "key_url": "https://aistudio.google.com/apikey",
        "model_hint": "Gemini 2.5 (Google OAuth o API key)",
    },
    "opencode": {
        "name": "OpenCode (multi-provider TUI)",
        "short": "OpenCode",
        "command": "opencode",
        "context_file": "AGENTS.md",
        "autoskills_flag": "opencode",  # autoskills v0.3.6+ ya soporta opencode
        "auth_kind": "oauth",   # opencode auth login es interactivo
        "login_argv": ["opencode", "auth", "login"],
        "logout_argv": ["opencode", "auth", "logout"],
        "model_hint": "OpenCode TUI · 75+ providers",
    },
    "openrouter": {
        "name": "OpenRouter (vía OpenCode)",
        "short": "OpenRouter",
        "command": "opencode",
        "context_file": "AGENTS.md",
        "autoskills_flag": "opencode",  # autoskills v0.3.6+ — vía opencode binary
        "auth_kind": "api",
        "env_var": "OPENROUTER_API_KEY",
        "key_id": "openrouter",
        "key_url": "https://openrouter.ai/keys",
        "model_hint": "OpenRouter · ruteo vía OpenCode",
        # extra arg para que opencode use openrouter por defecto
        "default_model": "openrouter/anthropic/claude-3.7-sonnet",
    },
}


# ─── Storage de keys ───────────────────────────────────────────────────
def _ensure_config_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    pc.secure_dir_chmod(CONFIG_DIR)


def load_keys() -> dict[str, str]:
    if not KEYS_PATH.is_file():
        return {}
    try:
        return json.loads(KEYS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_key(key_id: str, value: str) -> None:
    _ensure_config_dir()
    data = load_keys()
    data[key_id] = value.strip()
    KEYS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    pc.secure_file_chmod(KEYS_PATH)


def delete_key(key_id: str) -> None:
    data = load_keys()
    if key_id in data:
        del data[key_id]
        KEYS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def has_key(key_id: str) -> bool:
    return bool(load_keys().get(key_id)) or bool(os.environ.get(_env_for_key_id(key_id)))


def _env_for_key_id(key_id: str) -> str:
    """Mapea key_id → env var name."""
    return {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        # Integraciones (no son providers de IA, pero se guardan/inyectan igual):
        "figma": "FIGMA_API_KEY",  # PAT de Figma para el MCP figma-context
    }.get(key_id, "")


# ─── Detección de estado ───────────────────────────────────────────────
def cli_in_path(provider_key: str) -> bool:
    cmd = PROVIDERS[provider_key]["command"]
    return shutil.which(cmd) is not None


def detect_status(provider_key: str) -> tuple[str, str]:
    """Devuelve (state, info) donde state ∈ {"ok", "need_login", "need_key", "missing_cli"}."""
    p = PROVIDERS[provider_key]
    if not cli_in_path(provider_key):
        return "missing_cli", f"{p['command']} no instalado en PATH"
    kind = p["auth_kind"]
    if kind == "api":
        if has_key(p["key_id"]):
            return "ok", f"✓ key {p['env_var']} configurada"
        return "need_key", f"falta {p['env_var']} (configura tu API key)"
    if kind == "oauth_or_api":
        # Gemini: válido si hay key O hay credenciales OAuth
        if has_key(p.get("key_id", "")):
            return "ok", f"✓ key {p['env_var']} configurada"
        # heurística: ~/.gemini/credentials.json o similar
        cred_paths = [
            HOME / ".gemini" / "oauth_creds.json",
            HOME / ".config" / "gemini" / "auth.json",
        ]
        if any(p.is_file() for p in cred_paths):
            return "ok", "✓ OAuth de Google detectado"
        return "need_login", "ejecuta `gemini` para login OAuth o configura GEMINI_API_KEY"
    # oauth puro
    cred_paths = _oauth_credential_paths(provider_key)
    if any(c.is_file() for c in cred_paths):
        return "ok", f"✓ OAuth detectado ({cred_paths[0].name})"
    return "need_login", f"sin login — ejecuta `{' '.join(p['login_argv'])}`"


def _oauth_credential_paths(provider_key: str) -> list[Path]:
    """Rutas conocidas donde cada CLI guarda credenciales OAuth."""
    return {
        "claude": [
            HOME / ".claude" / ".credentials.json",
            HOME / ".claude" / "credentials.json",
            HOME / ".config" / "claude" / "credentials.json",
        ],
        "codex": [
            HOME / ".codex" / "auth.json",
            HOME / ".config" / "codex" / "auth.json",
        ],
        "opencode": [
            HOME / ".local" / "share" / "opencode" / "auth.json",
            HOME / ".config" / "opencode" / "auth.json",
        ],
    }.get(provider_key, [])


# ─── Env y argv ────────────────────────────────────────────────────────
def get_env(provider_key: str) -> dict[str, str]:
    """Devuelve dict de env vars a añadir al lanzar el CLI para este provider.
    Vacío para OAuth puro (el CLI lee sus creds locales)."""
    p = PROVIDERS[provider_key]
    env = {}
    kind = p["auth_kind"]
    if kind in ("api", "oauth_or_api"):
        key_id = p.get("key_id")
        if key_id:
            v = load_keys().get(key_id) or os.environ.get(p["env_var"])
            if v:
                env[p["env_var"]] = v
    return env


def apply_env(provider_key: str) -> None:
    """Mete las env vars del provider en os.environ. Se usa para que los
    procesos hijos (terminal server, scripts) las hereden."""
    for k, v in get_env(provider_key).items():
        os.environ[k] = v


def apply_all_known_keys() -> None:
    """Carga TODAS las keys conocidas a os.environ. Se llama una vez al
    arrancar ThemeForge para que cualquier terminal embebida tenga las
    keys disponibles según el provider que el usuario elija allí."""
    keys = load_keys()
    for key_id, value in keys.items():
        env_name = _env_for_key_id(key_id)
        if env_name and value:
            os.environ.setdefault(env_name, value)


def oneshot_argv(provider_key: str, allow_web: bool = True) -> list[str]:
    """Argv para una llamada one-shot (prompt vía stdin/argv, sin sesión).

    Cada CLI recibe el flag de output estructurado (JSON / stream-json)
    para que el ReferenceAnalysisDialog parsee TTFT / tokens / coste live
    via `stream_parsers`. Si en el futuro algún CLI rompe el schema
    upstream, el parser correspondiente cae a None y el dialog sigue
    mostrando texto plano sin métricas (degradación graceful).
    """
    p = PROVIDERS[provider_key]
    cmd = p["command"]
    if cmd == "claude":
        argv = [
            "claude", "--print",
            "--output-format=stream-json",
            "--include-partial-messages",
            "--verbose",
        ]
        if allow_web:
            argv += ["--allowed-tools", "WebSearch", "WebFetch"]
        argv += ["--permission-mode", "bypassPermissions"]
        return argv
    if cmd == "codex":
        # --json emite JSONL events (session_started, agent_message_delta,
        # token_count, task_complete). --skip-git-repo-check evita el
        # prompt "directorio no confiable" cuando se ejecuta en cwd del
        # proyecto recién creado (puede no tener .git aún).
        return ["codex", "exec", "--json", "--skip-git-repo-check", "-"]
    if cmd == "gemini":
        # -o stream-json emite eventos similares a Claude's stream-json
        # con usageMetadata al final.
        return ["gemini", "-p", "-", "-o", "stream-json"]
    if cmd == "opencode":
        argv = ["opencode", "run", "--format", "json"]
        model = p.get("default_model")
        if model:
            argv += ["-m", model]
        return argv
    return [cmd]


def interactive_cmd_args(provider_key: str) -> tuple[str, list[str]]:
    """Cmd y args para una sesión interactiva (terminal embebida).

    Claude siempre arranca con `--dangerously-skip-permissions` para
    que el agente pueda editar/ejecutar todo dentro del proyecto sin
    pedir confirmación a cada paso. ThemeForge ya sandboxea el agente
    dentro de la carpeta del proyecto (cwd del terminal embebido), así
    que el riesgo es controlado — el user explícitamente pidió que sea
    el comportamiento por defecto en cualquier modo / proyecto."""
    p = PROVIDERS[provider_key]
    cmd = p["command"]
    args: list[str] = []
    if cmd == "claude":
        args = ["--dangerously-skip-permissions"]
    if cmd == "opencode" and p.get("default_model"):
        args = ["-m", p["default_model"]]
    return cmd, args


def interactive_argv_for_binary(binary: str) -> list[str]:
    """Builds the full argv for invoking an agent CLI in interactive
    mode by binary name (`claude` / `codex` / `gemini` / `opencode`).
    Used by call sites that only know the command (not a provider key
    in PROVIDERS).
    """
    if binary == "claude":
        return ["claude", "--dangerously-skip-permissions"]
    return [binary]


# ─── Helpers de login ──────────────────────────────────────────────────
def login_argv(provider_key: str) -> list[str] | None:
    """Argv para arrancar el flujo de login interactivo. None si no aplica."""
    p = PROVIDERS[provider_key]
    return p.get("login_argv")


def open_login_in_konsole(provider_key: str) -> bool:
    """Abre una terminal externa con el comando de login del provider.

    Pese al nombre histórico (Konsole), usa platform_compat para elegir
    el emulador correcto según OS (Konsole/gnome-terminal/Terminal.app/
    cmd.exe).
    """
    argv = login_argv(provider_key)
    if not argv:
        return False
    try:
        import platform_compat as pc
        import shlex
        cmd_str = " ".join(shlex.quote(a) for a in argv)
        return pc.open_in_terminal(Path.home(), command=cmd_str, hold=True) is not None
    except Exception:
        return False


def register_api_key_in_cli(provider_key: str, key_value: str) -> tuple[bool, str]:
    """Para providers que requieren registrar la API key DENTRO del CLI
    (ej. `codex login --with-api-key` lee stdin), ejecuta el comando con
    la key como input. Devuelve (ok, msg). Si el provider no requiere
    este paso, devuelve (True, "no aplica")."""
    p = PROVIDERS[provider_key]
    argv = p.get("post_key_argv")
    if not argv:
        return True, "no aplica"
    if not shutil.which(argv[0]):
        return False, f"{argv[0]} no en PATH"
    try:
        r = subprocess.run(
            argv,
            input=key_value + "\n",
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode != 0:
            return False, (r.stderr or r.stdout).strip()[:300]
        return True, "registrada"
    except Exception as e:
        return False, str(e)
