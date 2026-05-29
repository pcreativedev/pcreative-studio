"""web_shell.py — POC: render the Neo-Tokyo web prototype inside a Qt window.

This is the "Forma 1" proof-of-concept: the EXACT design (the React/HTML
prototype Claude Design produced) rendered pixel-for-pixel inside the app
via QWebEngineView (same Chromium engine), wired to the real ThemeForge
Python backend through a QWebChannel bridge.

What it proves:
  - The prototype runs unmodified inside Qt (served over a local HTTP
    origin so its `type="text/babel" src=` files load correctly).
  - A native bridge object (`window.tfBridge`) exposes real Python methods
    to the page. The POC wires ONE real action: `list_stacks()` returns the
    actual ThemeForge STACKS, and the page shows a confirmation banner.

Run standalone:

    python3 web_shell.py

Later, the same WebShell widget can be embedded as a tab in the main app
and the bridge grown to cover create_project / run_preflight / build_zip /
gallery / cost / etc.
"""
from __future__ import annotations

import json
import socket
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PyQt6.QtCore import (QObject, QUrl, QProcess, QProcessEnvironment, QTimer,
                          pyqtSlot, pyqtSignal)
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

WEBUI_DIR = Path(__file__).resolve().parent / "webui" / "neotokyo"
TERMINAL_DIR = Path(__file__).resolve().parent / "terminal"


def _free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _serve(directory: Path, port: int) -> ThreadingHTTPServer:
    """Arranca un servidor HTTP en un hilo daemon sirviendo `directory`."""
    class _QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, *_a):  # silenciar el log de acceso
            pass
    handler = partial(_QuietHandler, directory=str(directory))
    httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd


# ───────────────────────── datos reales ─────────────────────────────────
_AGENT_ACCENT = {
    "claude": "#62b4ff", "codex": "#86efac",
    "gemini": "#fbbf24", "opencode": "#c084fc",
}
_LANG_SHORT = {
    "TypeScript": "TS", "JavaScript": "JS", "PHP": "PHP", "Python": "PY",
    "Rust": "Rust", "Go": "Go", "Dart": "Dart", "Kotlin": "Kt",
    "Java": "Java", "Ruby": "Rb", "Elixir": "Ex", "C#": "C#",
}
_THEME_JP = {
    "neotokyo": "ネオ東京", "tokyo-night": "東京夜", "dracula": "吸血鬼",
    "nord": "北", "linear": "線形", "brutalism": "粗野", "soft-ui": "柔",
    "themeforge-dark": "暗", "themeforge-light": "明",
}


def _stacks_data() -> list:
    try:
        from stacks import STACKS
    except Exception:
        return []
    out = []
    # El stack "none" (sin stack — el agente decide) va PRIMERO, igual que en la
    # app normal: crea el proyecto sin scaffolding y el agente propone el stack.
    if "none" in STACKS:
        v = STACKS["none"]
        out.append({"key": "none", "label": v.get("name", "(Sin stack)"),
                    "jp": "自由", "cat": v.get("category", "Sin definir") or "Sin definir",
                    "n": "—"})
    for k, v in STACKS.items():
        if k == "none":
            continue
        lang = v.get("language", "") or ""
        out.append({
            "key": k,
            "label": v.get("name", k),
            "jp": "",
            "cat": v.get("category", "") or "",
            "n": _LANG_SHORT.get(lang, (lang[:4] if lang else "·")),
        })
    return out


def _projects_data() -> list:
    try:
        from themeforge import list_projects
        rows = list_projects(archived=False)
    except Exception:
        return []
    rows.sort(key=lambda r: r.get("mtime", 0), reverse=True)
    out = []
    for r in rows:
        agent = (r.get("provider") or r.get("agent") or "claude")
        git = r.get("git_status", "")
        out.append({
            "id": r.get("slug", "") or r.get("name", ""),
            "name": r.get("name", "") or r.get("slug", ""),
            "path": str(r.get("path", "") or ""),
            "jp": "",
            "type": r.get("category", "") or r.get("stack", "") or "Template",
            "stack": r.get("stack", "") or "",
            "stackKey": r.get("stack", "") or "",
            "agent": agent,
            "status": "live" if git == "clean" else ("building" if git else "draft"),
            "cost": float(r.get("cost", 0) or 0),
            "tokens": r.get("tokens", "—") or "—",
            "updated": r.get("mtime_iso", "") or "",
            "accent": _AGENT_ACCENT.get(agent, "#00f0ff"),
            "desc": r.get("description", "") or r.get("stack", "") or "",
            "tags": [t for t in [r.get("stack", "")] if t],
            "commits": int(r.get("commits", 0) or 0),
            "preview": "saas",
        })
    return out


def _providers_data() -> list:
    try:
        import ai_providers as aip
        out = []
        for key, p in aip.PROVIDERS.items():
            try:
                state, info = aip.detect_status(key)
            except Exception:
                state, info = "error", ""
            out.append({
                "key": key, "name": p.get("name", key),
                "short": p.get("short", key), "status": state,
                "accent": _AGENT_ACCENT.get(key, "#00f0ff"),
            })
        return out
    except Exception:
        return []


def _themes_data() -> dict:
    try:
        import themes
        cur = themes.current_theme_name()
        out = []
        for ti in themes.list_themes():
            try:
                pack = themes.load_theme(ti.name)
                acc = pack.color.accent
                acc2 = getattr(pack.color, "danger", "#ff2e88")
                bg = pack.color.bg_primary
            except Exception:
                acc, acc2, bg = "#00f0ff", "#ff2e88", "#04060c"
            out.append({
                "k": ti.name, "label": ti.display_name,
                "jp": _THEME_JP.get(ti.name, ""),
                "bg": bg, "acc": acc, "acc2": acc2,
            })
        return {"themes": out, "current": cur}
    except Exception:
        return {"themes": [], "current": "neotokyo"}


def _fmt_tokens(n: int) -> str:
    n = int(n or 0)
    if n >= 1_000_000:
        return f"{n / 1e6:.1f}M"
    if n >= 1_000:
        return f"{n / 1e3:.0f}k"
    return str(n)


def _cost_data() -> dict:
    """Datos reales del cost tracker (mismos scanners que la GUI)."""
    try:
        from cost_tracker import aggregate, PRICING
        rep = aggregate()
    except Exception:
        return {}
    by_agent = [{"k": k, "v": round(v["cost"], 2)}
                for k, v in rep.by_provider.items() if v.get("cost", 0) > 0]
    import datetime as _dt
    today = _dt.date.today()
    days = []
    for i in range(29, -1, -1):
        d = (today - _dt.timedelta(days=i)).isoformat()
        days.append(round(rep.by_day.get(d, 0.0), 2))
    models = []
    for model, m in sorted(rep.by_model.items(), key=lambda kv: -kv[1].get("cost", 0)):
        if m.get("cost", 0) <= 0:
            continue
        rate = ""
        if model in PRICING:
            pin, pout = PRICING[model][0], PRICING[model][1]
            rate = f"${pin:g}/${pout:g}"
        models.append({
            "agent": m.get("provider", ""), "model": model,
            "sessions": m.get("events", 0),
            "input": _fmt_tokens(m.get("in", 0)),
            "output": _fmt_tokens(m.get("out", 0)),
            "rate": rate or "—", "cost": round(m.get("cost", 0), 2),
        })
    return {
        "by_agent": by_agent, "days": days, "models": models,
        "total": round(rep.total_cost_usd, 2),
        "tokens": _fmt_tokens(rep.total_input + rep.total_output),
        "month": round(rep.this_month_usd, 2),
    }


_ALWAYS_MCP = {"filesystem", "fetch", "memory", "github", "themeforge"}


def _mcp_data() -> list:
    """Catálogo MCP real (mcp_catalog.CATALOG) en la forma del prototipo."""
    try:
        import mcp_catalog as mc
    except Exception:
        return []
    out = []
    for e in mc.CATALOG:
        rel = e.relevance[0] if e.relevance else "any"
        cat = "core" if e.key in _ALWAYS_MCP else rel
        out.append({
            "id": e.key, "label": e.key, "cat": cat,
            "always": e.key in _ALWAYS_MCP,
            "desc": e.description, "lic": e.license,
            "repo": e.repo, "auth": bool(e.requires_auth),
        })
    return out


_CRED_SLOTS = [
    ("anthropic", "Anthropic API key", "#62b4ff"),
    ("openai", "OpenAI / Codex key", "#86efac"),
    ("gemini", "Google Gemini key", "#fbbf24"),
    ("figma", "Figma API key", "#00f0ff"),
    ("openrouter", "OpenRouter key", "#c084fc"),
    ("github", "GitHub token", "#e9f0ff"),
]


def _creds_data() -> list:
    """Estado real de credenciales: cuenta tanto la API key (keys.json) como la
    autenticación OAuth/CLI del provider (claude/codex/gemini login). Así
    refleja lo que de verdad funciona, no solo las keys guardadas."""
    try:
        import ai_providers as aip
        keys = aip.load_keys()
    except Exception:
        import ai_providers as aip  # noqa
        keys = {}
    # Mapa slot → provider(s) cuyo login OAuth/CLI también cuenta como configurado.
    auth_provider = {"anthropic": ["claude", "claude-api"],
                     "openai": ["codex", "codex-api"],
                     "gemini": ["gemini"],
                     "openrouter": ["openrouter"]}

    def _provider_ok(pkey):
        try:
            state, _ = aip.detect_status(pkey)
            return state == "ok"
        except Exception:
            return False

    out = []
    for kid, label, color in _CRED_SLOTS:
        configured = bool(keys.get(kid))
        via = "key" if configured else ""
        if not configured and kid in auth_provider:
            if any(_provider_ok(pk) for pk in auth_provider[kid]):
                configured = True; via = "oauth"
        if not configured and kid == "github":
            # gh CLI autenticado cuenta como configurado.
            try:
                import shutil, subprocess
                if shutil.which("gh"):
                    r = subprocess.run(["gh", "auth", "status"],
                                       capture_output=True, timeout=6)
                    if r.returncode == 0:
                        configured = True; via = "gh-cli"
            except Exception:
                pass
        out.append({"id": kid, "label": label, "color": color,
                    "configured": configured, "via": via})
    return out


def _operator_data() -> dict:
    """Estado real del Operator (Hermes): disponible + versión."""
    try:
        from operator_panel import find_hermes
        hermes = find_hermes()
        if not hermes:
            return {"available": False, "missions": []}
        ver = ""
        try:
            from hermes_panel import hermes_version
            ver = hermes_version() or ""
        except Exception:
            pass
        return {"available": True, "version": ver, "missions": []}
    except Exception:
        return {"available": False, "missions": []}


def bootstrap_data() -> dict:
    """Todos los datos reales que el prototipo necesita, en su forma exacta."""
    td = _themes_data()
    return {
        "stacks": _stacks_data(),
        "projects": _projects_data(),
        "providers": _providers_data(),
        "themes": td["themes"],
        "current_theme": td["current"],
        "cost": _cost_data(),
        "mcp": _mcp_data(),
        "operator": _operator_data(),
        "creds": _creds_data(),
    }


class ThemeForgeBridge(QObject):
    """Objeto puente expuesto a la página como `window.tfBridge`. Cada
    @pyqtSlot es invocable desde JavaScript. Aquí va la lógica REAL de
    ThemeForge. Las señales se reciben en JS con `bridge.<signal>.connect(cb)`."""

    # Progreso de un build/scaffold en curso (texto de log).
    progress = pyqtSignal(str)
    # Build terminado: JSON {ok, slug, path, exit}.
    build_done = pyqtSignal(str)
    # Terminal real lista: JSON {path, url} para iframe.
    terminal_ready = pyqtSignal(str)
    # Preview (dev server) listo: JSON {path, url} o {path, error}.
    preview_ready = pyqtSignal(str)
    # Análisis de mercado terminado: JSON {niche, markdown} o {error}.
    market_result = pyqtSignal(str)
    # Streaming del análisis de referencia: JSON {line} o {done, error?}.
    reference_progress = pyqtSignal(str)
    # Terminal de Compare lista por provider: JSON {provider, url}.
    compare_ready = pyqtSignal(str)
    # Resultado de suggest_stack (Vibe pre-fill): JSON {stack, template_type, prompt} o {error}.
    suggest_result = pyqtSignal(str)

    @pyqtSlot(str, result=str)
    def compare(self, prompt: str) -> str:
        """Compare REAL: corre el MISMO prompt en cada CLI de IA disponible, cada
        uno en su propio terminal (xterm+node-pty), en paralelo. Emite
        `compare_ready` {provider,url} por cada uno para embeber lado a lado."""
        import shutil
        import urllib.parse
        from pathlib import Path
        node = shutil.which("node")
        if not node:
            return json.dumps({"ok": False, "error": "node no encontrado"})
        try:
            import ai_providers as aip
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})
        cwd = str(Path.home())
        started = []
        for pkey in ("claude", "codex", "gemini", "opencode"):
            p = aip.PROVIDERS.get(pkey, {})
            binary = p.get("command")
            if not binary or not shutil.which(binary):
                continue
            try:
                cmd, extra = aip.interactive_cmd_args(pkey)
            except Exception:
                cmd, extra = binary, []
            args = (extra or []) + [prompt]
            proc = QProcess(self)
            proc.setWorkingDirectory(str(TERMINAL_DIR))
            proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)

            def _mk(pk, c, a, pr):
                def _on_out():
                    data = bytes(pr.readAllStandardOutput()).decode(errors="replace")
                    for line in data.splitlines():
                        if line.startswith("PORT="):
                            port = line.split("=", 1)[1].strip()
                            q = (f"cwd={urllib.parse.quote(cwd)}"
                                 f"&cmd={urllib.parse.quote(c)}")
                            if a:
                                q += "&args=" + urllib.parse.quote("\x1f".join(a))
                            self.compare_ready.emit(json.dumps(
                                {"provider": pk, "url": f"http://127.0.0.1:{port}/?{q}"}))
                return _on_out

            proc.readyReadStandardOutput.connect(_mk(pkey, cmd, args, proc))
            proc.start(node, [str(TERMINAL_DIR / "server.js"), "0"])
            self._procs.append(proc)
            started.append(pkey)
        return json.dumps({"ok": True, "providers": started})

    @pyqtSlot(str, result=str)
    def analyze_market(self, niche: str) -> str:
        """Análisis de mercado REAL (OpenRouter) para un nicho — async en un
        hilo para no congelar la UI; emite `market_result` con el markdown."""
        import threading
        try:
            from market_analyzer import (build_request, call_openrouter,
                                         get_openrouter_key, DEFAULT_MODEL)
        except Exception as e:
            self.market_result.emit(json.dumps({"error": f"import: {e}"}))
            return json.dumps({"ok": False, "error": str(e)})
        key = get_openrouter_key()
        if not key:
            self.market_result.emit(json.dumps(
                {"error": "Configura tu OpenRouter API key en Settings → Credenciales."}))
            return json.dumps({"ok": False, "error": "sin OpenRouter key"})

        def _work():
            try:
                # niche puede venir como "kind:valor" para forzar el tipo.
                kind = "niche" if (niche or "").strip() else "general"
                params = {"niche": niche} if kind == "niche" else None
                if (niche or "").startswith("@"):  # @general / @stacks / @prediction
                    kind = niche[1:].strip() or "general"; params = None
                req = build_request(kind, DEFAULT_MODEL, params)
                md = call_openrouter(req, key)
                self.market_result.emit(json.dumps({"niche": niche, "markdown": md}))
            except Exception as e:
                self.market_result.emit(json.dumps({"error": str(e)}))

        threading.Thread(target=_work, daemon=True).start()
        return json.dumps({"ok": True, "running": True})

    def __init__(self, parent=None):
        super().__init__(parent)
        self._procs = []  # mantener vivas las QProcess en vuelo
        self._last_reference_analysis = None  # (value, texto) del último análisis IA

    def _agent_launch_for(self, path: str):
        """(cmd, args) para auto-lanzar la IA del provider activo con el prompt
        de contexto del proyecto — replica el auto-agent de ProjectWindow."""
        from pathlib import Path
        try:
            import ai_providers as aip
            import app_prefs as ap
            import shutil
            sel = ap.default_provider()
            binary = aip.PROVIDERS.get(sel, {}).get("command")
            if not binary or not shutil.which(binary):
                return "bash", []
            cmd, extra = aip.interactive_cmd_args(sel)
            ctx_file = aip.PROVIDERS[sel].get("context_file", "CLAUDE.md")
            proj = Path(path)
            cands = [ctx_file, "CLAUDE.md", "AGENTS.md", "GEMINI.md"]
            ctx = next((c for c in cands if (proj / c).is_file()), ctx_file)
            skills = ""
            if (proj / ".claude" / "skills").is_dir():
                skills = (" Este proyecto tiene **skills instaladas** (autoskills / "
                          "UI-UX Pro) en `.claude/skills/`: lístalas, léelas y ÚSALAS.")
            prompt = (
                f"Acabas de abrir el proyecto «{proj.name}» desde ThemeForge. "
                f"Lee COMPLETAMENTE {ctx} y todo lo que haya en context/ para entender "
                f"el estado actual (qué es, stack, qué se ha hecho ya).{skills}\n\n"
                f"Antes de tocar NADA del código:\n"
                f"1. Resume en 4-6 líneas el estado del proyecto y lo ya hecho.\n"
                f"2. Lista los primeros 3-5 pasos que propones para continuar.\n"
                f"3. Espera mi OK antes de ejecutar nada."
            )
            return cmd, (extra or []) + [prompt]
        except Exception:
            return "bash", []

    @pyqtSlot(str, result=str)
    def start_terminal(self, path: str) -> str:
        """Auto-lanza la IA (provider activo + contexto del proyecto) en un
        terminal real (xterm + node-pty) con cwd en el proyecto, igual que la
        app normal. Emite `terminal_ready` con la URL para embeber."""
        return self._start_terminal(path, agent=True)

    @pyqtSlot(str, result=str)
    def start_shell(self, path: str) -> str:
        """Igual que start_terminal pero shell pelado (sin IA)."""
        return self._start_terminal(path, agent=False)

    def _start_terminal(self, path: str, agent: bool) -> str:
        import shutil
        node = shutil.which("node")
        if not node:
            self.terminal_ready.emit(json.dumps({"path": path, "error": "node no encontrado"}))
            return json.dumps({"ok": False, "error": "node no encontrado"})
        cmd, args = self._agent_launch_for(path) if agent else ("bash", [])
        proc = QProcess(self)
        proc.setWorkingDirectory(str(TERMINAL_DIR))
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)

        def _on_out():
            import urllib.parse
            data = bytes(proc.readAllStandardOutput()).decode(errors="replace")
            for line in data.splitlines():
                if line.startswith("PORT="):
                    port = line.split("=", 1)[1].strip()
                    q = (f"cwd={urllib.parse.quote(path)}"
                         f"&cmd={urllib.parse.quote(cmd)}")
                    if args:
                        q += "&args=" + urllib.parse.quote("\x1f".join(args))
                    url = f"http://127.0.0.1:{port}/?{q}"
                    self.terminal_ready.emit(json.dumps({"path": path, "url": url}))

        proc.readyReadStandardOutput.connect(_on_out)
        proc.start(node, [str(TERMINAL_DIR / "server.js"), "0"])
        self._procs.append(proc)
        return json.dumps({"ok": True, "starting": True, "agent": agent})

    @pyqtSlot(str, result=str)
    def start_preview(self, path: str) -> str:
        """Arranca el dev server real del proyecto (detección de preview.py) y
        emite `preview_ready` con la URL para embeber por iframe."""
        try:
            from preview import (detect_preview_profile, apply_port,
                                 get_port_for_project)
            import platform_compat as pc
            import shlex
            from pathlib import Path
            proj = Path(path)
            prof = detect_preview_profile(proj)
            if not prof:
                self.preview_ready.emit(json.dumps(
                    {"path": path, "error": "sin preview detectable (¿deps instaladas?)"}))
                return json.dumps({"ok": False, "error": "sin preview"})
            port = get_port_for_project(proj.name, prof.get("default_port", 5173))
            cmd, env_extra, url = apply_port(prof, port)
            proc = QProcess(self)
            proc.setWorkingDirectory(str(proj))
            proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
            env = QProcessEnvironment.systemEnvironment()
            local_bin = str(Path.home() / ".local" / "bin")
            env.insert("PATH", local_bin + os.pathsep + env.value("PATH", ""))
            for k, v in (env_extra or {}).items():
                env.insert(k, str(v))
            proc.setProcessEnvironment(env)
            cmd_str = " ".join(shlex.quote(c) for c in cmd)
            sh, args = pc.shell_program_and_args(cmd_str)
            proc.start(sh, args)
            self._procs.append(proc)
            QTimer.singleShot(4800, lambda: self.preview_ready.emit(
                json.dumps({"path": path, "url": url})))
            return json.dumps({"ok": True, "starting": True, "url": url})
        except Exception as e:
            self.preview_ready.emit(json.dumps({"path": path, "error": str(e)}))
            return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(str, result=str)
    def open_folder(self, path: str) -> str:
        """Abre la carpeta del proyecto en el explorador de archivos."""
        try:
            import platform_compat as pc
            pc.open_path(path)
            return json.dumps({"ok": True})
        except Exception:
            import subprocess
            try:
                subprocess.Popen(["xdg-open", path])
                return json.dumps({"ok": True})
            except Exception as e:
                return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(result=str)
    def pick_folder(self) -> str:
        """Selector de carpeta nativo (para New→recreate/adopt). Devuelve la ruta."""
        try:
            from PyQt6.QtWidgets import QFileDialog
            d = QFileDialog.getExistingDirectory(None, "Elegir carpeta de referencia")
            return json.dumps({"path": d or ""})
        except Exception as e:
            return json.dumps({"path": "", "error": str(e)})

    @pyqtSlot(result=str)
    def pick_file(self) -> str:
        """Selector de archivo nativo (p.ej. .zip de referencia)."""
        try:
            from PyQt6.QtWidgets import QFileDialog
            f, _ = QFileDialog.getOpenFileName(None, "Elegir archivo (.zip)")
            return json.dumps({"path": f or ""})
        except Exception as e:
            return json.dumps({"path": "", "error": str(e)})

    @pyqtSlot(str, result=str)
    def open_vscode(self, path: str) -> str:
        """Abre el proyecto en VS Code (o el editor disponible)."""
        import shutil
        import subprocess
        for ed in ("code", "codium", "cursor"):
            if shutil.which(ed):
                try:
                    subprocess.Popen([ed, path]); return json.dumps({"ok": True, "editor": ed})
                except Exception:
                    pass
        return json.dumps({"ok": False, "error": "no se encontró VS Code/Codium/Cursor"})

    @pyqtSlot(str, result=str)
    def run_preflight(self, path: str) -> str:
        """Pre-flight real (checks de marketplace) sobre el proyecto."""
        try:
            from mcp_server import run_preflight as _rp
            return json.dumps(_rp(path))
        except Exception as e:
            return json.dumps({"error": str(e)})

    @pyqtSlot(str, result=str)
    def build_zip(self, path: str) -> str:
        """Empaqueta el proyecto para el marketplace (zip real)."""
        try:
            from mcp_server import build_zip as _bz
            return json.dumps(_bz(path))
        except Exception as e:
            return json.dumps({"error": str(e)})

    @pyqtSlot(str, result=str)
    def create_project(self, payload_json: str) -> str:
        """Crea un proyecto REAL: escribe el setup script (scaffold + autoskills
        + UI/UX Pro) y lo ejecuta async; emite `progress`; al terminar abre la
        ProjectWindow nativa real y emite `build_done`."""
        try:
            cfg = json.loads(payload_json or "{}")
        except Exception:
            cfg = {}
        name = (cfg.get("name") or "").strip() or "Untitled Forge"
        stack = cfg.get("stack") or ""
        ttype = cfg.get("type") or "(Sin tipo específico)"
        provider = cfg.get("agent") or "codex"
        niche = cfg.get("niche") or ""
        opts = cfg.get("opts") or {}
        try:
            from stacks import STACKS
            import ai_providers as aip
            from themeforge import (write_setup_script, PROJECTS_DIR, slugify,
                                    load_projects_meta, save_projects_meta)
        except Exception as e:
            return json.dumps({"ok": False, "error": f"import: {e}"})
        if stack not in STACKS:
            return json.dumps({"ok": False, "error": f"stack desconocido: {stack}"})
        if provider not in aip.PROVIDERS:
            provider = "codex" if "codex" in aip.PROVIDERS else next(iter(aip.PROVIDERS))
        from pathlib import Path
        slug = slugify(name)
        project_dir = PROJECTS_DIR / slug
        n = 2
        while project_dir.exists() and any(project_dir.iterdir()):
            slug = f"{slugify(name)}-{n}"; project_dir = PROJECTS_DIR / slug; n += 1
        # Inyecta el análisis IA de referencia (si se hizo uno) en CLAUDE.md,
        # igual que el modo recreate del normal — así "se queda guardado".
        ai_analysis = None
        ref_value = (cfg.get("reference") or "").strip()
        if self._last_reference_analysis and self._last_reference_analysis[1]:
            stored_val, stored_txt = self._last_reference_analysis
            if (not ref_value) or stored_val == ref_value:
                ai_analysis = stored_txt
        mode = cfg.get("mode") or "scratch"
        try:
            script = write_setup_script(
                project_dir=project_dir, stack_key=stack, template_type=ttype,
                project_name=name, agent_key=provider,
                run_autoskills=bool(opts.get("uipro", True)),
                mode="scratch", reference_kind=None, reference_value=None,
                existing_repo=None, create_github_repo=False, github_user=None,
                embedded=True, run_uipro=bool(opts.get("uipro", True)),
                niche=(niche or None), launch_agent=False,
                ai_analysis=ai_analysis, ai_analysis_kind="reference",
            )
        except Exception as e:
            return json.dumps({"ok": False, "error": f"write_setup_script: {e}"})
        try:
            meta = load_projects_meta()
            if slug not in meta:
                meta[slug] = {"name": name, "stack": stack}
                save_projects_meta(meta)
        except Exception:
            pass

        PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
        proc = QProcess(self)
        proc.setWorkingDirectory(str(PROJECTS_DIR))
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.readyReadStandardOutput.connect(
            lambda: self.progress.emit(
                bytes(proc.readAllStandardOutput()).decode(errors="replace")))

        def _done(code, _status):
            self.progress.emit(f"\n■ Scaffold terminado (exit {code}).\n")
            # La UI web navega a su project screen (terminal real embebida) al
            # recibir build_done — no abrimos ventana nativa: todo en Neo-Tokyo web.
            self.build_done.emit(json.dumps(
                {"ok": code == 0, "slug": slug, "name": name,
                 "path": str(project_dir), "exit": code}))
            if proc in self._procs:
                self._procs.remove(proc)

        proc.finished.connect(_done)
        self._procs.append(proc)
        self.progress.emit(f"▶ Creando '{name}' ({stack}, {provider})…\n")
        proc.start("bash", [str(script)])
        return json.dumps({"ok": True, "slug": slug, "path": str(project_dir),
                           "started": True})

    @pyqtSlot(str, result=str)
    def launch_mission(self, brief: str) -> str:
        """Lanza una misión REAL del Operator (Hermes) async; stream por
        `progress`. Igual que el OperatorPanel nativo."""
        try:
            from operator_panel import find_hermes, _mission_env
        except Exception as e:
            return json.dumps({"ok": False, "error": f"import: {e}"})
        hermes = find_hermes()
        if not hermes:
            return json.dumps({"ok": False, "error": "Hermes no instalado"})
        if not (brief or "").strip():
            return json.dumps({"ok": False, "error": "brief vacío"})
        proc = QProcess(self)
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        try:
            proc.setProcessEnvironment(_mission_env())
        except Exception:
            pass
        proc.readyReadStandardOutput.connect(
            lambda: self.progress.emit(
                bytes(proc.readAllStandardOutput()).decode(errors="replace")))
        proc.finished.connect(
            lambda code, _s: self.progress.emit(f"\n■ Misión terminada (exit {code}).\n"))
        self.progress.emit(f"▶ Lanzando misión: {brief[:80]}…\n")
        proc.start(hermes, ["chat", "-q", brief, "-s", "themeforge-operator"])
        self._procs.append(proc)
        return json.dumps({"ok": True, "running": True})

    @pyqtSlot(str, result=str)
    def suggest_stack(self, description: str) -> str:
        """Pre-fill Vibe real (motor de sugerencia de ThemeForge) — ASÍNCRONO en
        un hilo para no congelar la UI; emite `suggest_result` con el resultado."""
        import threading

        def _work():
            try:
                from mcp_server import suggest_stack as _ss
                self.suggest_result.emit(json.dumps(_ss(description)))
            except Exception as e:
                self.suggest_result.emit(json.dumps({"error": str(e)}))

        threading.Thread(target=_work, daemon=True).start()
        return json.dumps({"ok": True, "running": True})

    @pyqtSlot(result=str)
    def list_stacks(self) -> str:
        """Acción real: devuelve los stacks de verdad de ThemeForge."""
        return json.dumps(_stacks_data())

    @pyqtSlot(result=str)
    def bootstrap_data(self) -> str:
        """Todos los datos reales (stacks/proyectos/providers/temas) para
        refrescar el prototipo en vivo si hace falta."""
        try:
            return json.dumps(bootstrap_data())
        except Exception as e:
            return json.dumps({"error": str(e)})

    @pyqtSlot(str, result=str)
    def set_theme(self, name: str) -> str:
        """Persiste el tema elegido en Settings → temas y lo aplica a las
        superficies nativas. En la UI web sirve para recordar la selección."""
        try:
            import themes
            from PyQt6.QtWidgets import QApplication
            themes.save_current_theme(name)
            try:
                themes.apply_theme(QApplication.instance(), themes.load_theme(name))
                themes.theme_signals.theme_changed.emit(name)
            except Exception:
                pass
            return json.dumps({"ok": True, "theme": name})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(str, result=str)
    def open_project(self, path_or_slug: str) -> str:
        """Abre la ProjectWindow NATIVA real (terminal xterm + preview + git +
        build + deploy, ya con el tema Neo-Tokyo). Acepta una ruta o un slug."""
        try:
            from pathlib import Path
            p = Path(path_or_slug)
            if not p.is_dir():
                # Resolver por slug contra los proyectos reales.
                for proj in _projects_data():
                    if proj.get("id") == path_or_slug and proj.get("path"):
                        p = Path(proj["path"]); break
            if not p.is_dir():
                return json.dumps({"ok": False, "error": f"no existe: {path_or_slug}"})
            from themeforge import open_project_window
            open_project_window(p)
            return json.dumps({"ok": True, "path": str(p)})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(result=str)
    def new_project(self) -> str:
        """Abre el flujo nativo de New project (formulario completo)."""
        try:
            from themeforge import focus_new_project
            ok = focus_new_project()
            return json.dumps({"ok": bool(ok)})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(str, str, result=str)
    def set_credential(self, key_id: str, value: str) -> str:
        """Guarda una API key real (keys.json, chmod 0600) y la aplica al entorno."""
        try:
            import ai_providers as aip
            import os as _os
            if (value or "").strip():
                aip.save_key(key_id, value.strip())
                env_map = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY",
                           "gemini": "GEMINI_API_KEY", "figma": "FIGMA_API_KEY",
                           "openrouter": "OPENROUTER_API_KEY", "github": "GITHUB_TOKEN"}
                if key_id in env_map:
                    _os.environ[env_map[key_id]] = value.strip()
                try:
                    aip.apply_all_known_keys()
                except Exception:
                    pass
            else:
                aip.delete_key(key_id)
            return json.dumps({"ok": True, "id": key_id, "configured": bool(value.strip())})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(result=str)
    def licensing_status(self) -> str:
        """Estado real del sistema de licencias: si está configurado + lista de
        licencias y productos del panel (si el backend local responde)."""
        try:
            from licensing_config import load as _lc
            cfg = _lc()
        except Exception as e:
            return json.dumps({"configured": False, "error": str(e)})
        configured = bool(cfg.get("panel_base")) and "YOUR_" not in str(cfg.get("panel_base", ""))
        out = {"configured": configured, "licenses": [], "products": [], "reachable": False}
        if not configured:
            return json.dumps(out)
        try:
            from licensing_panel import _api
            code, data = _api("/api/licenses")
            if code in (200, 201):
                out["reachable"] = True
                lst = data if isinstance(data, list) else data.get("licenses", [])
                out["licenses"] = [
                    {"key": (l.get("key") or "")[:18] + "…", "product": l.get("product", ""),
                     "type": l.get("type", ""), "status": l.get("status", ""),
                     "email": l.get("email", "")}
                    for l in (lst or [])[:50]
                ]
            code2, data2 = _api("/api/products/versions")
            if code2 in (200, 201):
                prods = data2 if isinstance(data2, list) else data2.get("products", [])
                out["products"] = [
                    {"slug": p.get("slug", ""), "version": p.get("version", "")}
                    for p in (prods or [])
                ]
        except Exception as e:
            out["error"] = str(e)
        return json.dumps(out)

    @pyqtSlot(str, str, str, result=str)
    def licensing_create(self, product: str, email: str, lic_type: str) -> str:
        """Crea una licencia real en el panel (POST /api/licenses)."""
        try:
            from licensing_panel import _api
            code, data = _api("/api/licenses", method="POST",
                              body={"product": product, "email": email,
                                    "type": lic_type or "regular"})
            lic = data.get("license") if isinstance(data, dict) else None
            key = (lic or {}).get("key") or (data or {}).get("key") or ""
            return json.dumps({"ok": code in (200, 201), "code": code, "key": key})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(result=str)
    def pixel_office_launch(self) -> str:
        """Lanza el dashboard Pixel Office (visualizador de sesiones)."""
        try:
            import pixel_office
            if pixel_office.is_dashboard_up():
                return json.dumps({"ok": True, "already": True})
            pixel_office.launch_background()
            return json.dumps({"ok": True})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(str, result=str)
    def git_push(self, path: str) -> str:
        """git add+commit+push real en el proyecto (async, progreso por señal)."""
        from pathlib import Path
        proj = Path(path)
        if not (proj / ".git").is_dir():
            # init + commit inicial
            cmd = ('git init && git add -A && git commit -m "ThemeForge: initial" '
                   '|| true')
        else:
            cmd = ('git add -A && git commit -m "ThemeForge update" || true; '
                   'git push 2>&1 || echo "[push] configura el remote primero]"')
        proc = QProcess(self)
        proc.setWorkingDirectory(str(proj))
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.readyReadStandardOutput.connect(
            lambda: self.progress.emit(bytes(proc.readAllStandardOutput()).decode(errors="replace")))
        proc.finished.connect(lambda c, _s: self.progress.emit(f"\n■ git (exit {c}).\n"))
        proc.start("bash", ["-lc", cmd])
        self._procs.append(proc)
        return json.dumps({"ok": True, "running": True})

    @pyqtSlot(str, str, result=str)
    def deploy_demo(self, path: str, provider: str) -> str:
        """Despliegue real de demo (Netlify/Vercel/Cloudflare/Surge) async."""
        try:
            import demo_deploy as dd
            from pathlib import Path
            proj = Path(path)
            cfg = dd.detect_build_config(proj)
            info = dd.provider_info(provider or "surge")
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})
        # Construir comando de deploy del provider (build primero si aplica).
        steps = []
        if getattr(cfg, "build_cmd", None):
            steps.append(cfg.build_cmd)
        dist = getattr(cfg, "dist_dir", "dist")
        deploy_cmds = {
            "netlify": f"netlify deploy --prod --dir {dist}",
            "vercel": "vercel --prod --yes",
            "surge": f"surge {dist}",
            "cloudflare": f"npx wrangler pages deploy {dist}",
        }
        steps.append(deploy_cmds.get(provider, deploy_cmds["surge"]))
        proc = QProcess(self)
        proc.setWorkingDirectory(str(proj))
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.readyReadStandardOutput.connect(
            lambda: self.progress.emit(bytes(proc.readAllStandardOutput()).decode(errors="replace")))
        proc.finished.connect(lambda c, _s: self.progress.emit(f"\n■ deploy (exit {c}).\n"))
        self.progress.emit(f"▶ Deploy a {provider}…\n")
        proc.start("bash", ["-lc", " && ".join(steps)])
        self._procs.append(proc)
        return json.dumps({"ok": True, "running": True})

    @pyqtSlot(str, str, result=str)
    def analyze_reference(self, value: str, kind: str) -> str:
        """Análisis de referencia REAL — idéntico al _ReferenceAnalysisDialog
        nativo: corre el CLI del provider activo en modo stream-json con
        WebSearch/WebFetch habilitados (oneshot_argv allow_web=True), prompt por
        stdin, parsea con stream_parsers → emite `reference_progress` con status
        en vivo (pensando/buscando en internet/usando tool/generando) + texto.
        Al terminar GUARDA el análisis (para inyectarlo en CLAUDE.md al crear)."""
        from pathlib import Path
        try:
            import reference_analyzer as ra
            import ai_providers as aip
            import app_prefs as ap
            import stream_parsers as sp
        except Exception as e:
            self.reference_progress.emit(json.dumps({"done": True, "error": f"import: {e}"}))
            return json.dumps({"ok": False, "error": str(e)})

        provider = ap.default_provider()
        state, info = ("error", "")
        try:
            state, info = aip.detect_status(provider)
        except Exception:
            pass
        if state != "ok":
            self.reference_progress.emit(json.dumps(
                {"done": True, "error": f"Provider {provider} no listo: {info}"}))
            return json.dumps({"ok": False, "error": "provider no listo"})

        try:
            p = Path(value)
            facts = ra.gather_facts(p) if p.exists() else {"reference": value, "kind": "url"}
            prompt = ra.build_prompt(facts)
            # "Detecta el stack" de la referencia (como el normal): muestra lo
            # que gather_facts reconoció antes de pedir la recomendación a la IA.
            det = (facts.get("framework") or facts.get("preview_profile")
                   or facts.get("kind") or "?")
            subs = facts.get("subprojects") or []
            det_txt = (f"mono-repo · {len(subs)} sub-proyectos" if subs else str(det))
            self.reference_progress.emit(json.dumps(
                {"status": f"📂 Detectado: {det_txt} · pidiendo stack óptimo a la IA…"}))
        except Exception as e:
            self.reference_progress.emit(json.dumps({"done": True, "error": f"facts: {e}"}))
            return json.dumps({"ok": False, "error": str(e)})

        argv = aip.oneshot_argv(provider, allow_web=True)
        parser = sp.parser_for(aip.PROVIDERS[provider]["command"])
        try:
            extra_env = aip.get_env(provider)
        except Exception:
            extra_env = {}

        proc = QProcess(self)
        proc.setProgram(argv[0])
        proc.setArguments(argv[1:])
        env = QProcessEnvironment.systemEnvironment()
        for k, v in (extra_env or {}).items():
            env.insert(k, str(v))
        proc.setProcessEnvironment(env)

        state_buf = {"buf": "", "text": [], "value": value}

        def _on_out():
            data = bytes(proc.readAllStandardOutput()).decode(errors="replace")
            if parser is None:
                state_buf["text"].append(data)
                self.reference_progress.emit(json.dumps({"text": data}))
                return
            state_buf["buf"] += data
            while "\n" in state_buf["buf"]:
                line, state_buf["buf"] = state_buf["buf"].split("\n", 1)
                if not line.strip():
                    continue
                try:
                    evt = parser(line) or {}
                except Exception:
                    evt = {}
                payload = {}
                if evt.get("text_delta"):
                    state_buf["text"].append(evt["text_delta"])
                    payload["text"] = evt["text_delta"]
                if evt.get("status"):
                    payload["status"] = evt["status"]
                if payload:
                    self.reference_progress.emit(json.dumps(payload))

        def _on_done(code, _s):
            full = "".join(state_buf["text"]).strip()
            self._last_reference_analysis = (state_buf["value"], full)
            try:
                if full:
                    ra_mod = __import__("reference_analyzer")
                    if hasattr(ra_mod, "save_analysis"):
                        pass  # guardado opcional; ya queda en _last_reference_analysis
            except Exception:
                pass
            self.reference_progress.emit(json.dumps(
                {"done": True, "saved": bool(full), "exit": code}))
            if proc in self._procs:
                self._procs.remove(proc)

        proc.readyReadStandardOutput.connect(_on_out)
        proc.finished.connect(_on_done)
        self.reference_progress.emit(json.dumps({"status": "⏳ Arrancando agente…"}))
        proc.start()
        proc.waitForStarted(5000)
        proc.write(prompt.encode("utf-8"))
        proc.closeWriteChannel()
        self._procs.append(proc)
        return json.dumps({"ok": True, "running": True})

    @pyqtSlot(str, result=str)
    def ping(self, msg: str) -> str:
        return json.dumps({"pong": msg})


class WebShell(QWidget):
    """Ventana/widget que sirve el prototipo y lo embebe en un WebEngineView
    con el puente nativo conectado."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._httpd = None
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            from PyQt6.QtWebChannel import QWebChannel
        except Exception as e:
            root.addWidget(QLabel(f"QtWebEngine no disponible: {e}"))
            return

        if not (WEBUI_DIR / "index.html").is_file():
            root.addWidget(QLabel(f"No se encuentra el prototipo en {WEBUI_DIR}"))
            return

        port = _free_port()
        self._httpd = _serve(WEBUI_DIR, port)

        self._view = QWebEngineView()
        self._bridge = ThemeForgeBridge()
        self._channel = QWebChannel(self._view.page())
        self._channel.registerObject("bridge", self._bridge)
        self._view.page().setWebChannel(self._channel)

        # Inyecta los DATOS REALES como window.__TF_DATA__ en DocumentCreation
        # (antes de que corra cualquier script de la página), así React los lee
        # síncronamente al montar — sin carrera con el puente asíncrono.
        try:
            from PyQt6.QtWebEngineCore import QWebEngineScript
            data_js = "window.__TF_DATA__ = " + json.dumps(bootstrap_data()) + ";"
            script = QWebEngineScript()
            script.setName("tf_bootstrap_data")
            script.setSourceCode(data_js)
            script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
            script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
            script.setRunsOnSubFrames(False)
            self._view.page().scripts().insert(script)
        except Exception as e:
            print(f"[webshell] no se pudo inyectar __TF_DATA__: {e}")

        self._view.setUrl(QUrl(f"http://127.0.0.1:{port}/index.html"))
        root.addWidget(self._view)

    def shutdown(self):
        if self._httpd is not None:
            try:
                self._httpd.shutdown()
            except Exception:
                pass
            self._httpd = None

    def closeEvent(self, ev):  # noqa: N802
        self.shutdown()
        super().closeEvent(ev)


def main():
    import sys
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication
    # QtWebEngine exige compartir contexto OpenGL antes de crear la QApplication.
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)
    app = QApplication(sys.argv)
    w = WebShell()
    w.resize(1280, 820)
    w.setWindowTitle("ThemeForge // Neo-Tokyo (WebEngine POC)")
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
