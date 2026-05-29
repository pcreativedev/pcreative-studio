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

from PyQt6.QtCore import QObject, QUrl, QProcess, pyqtSlot, pyqtSignal
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

    def __init__(self, parent=None):
        super().__init__(parent)
        self._procs = []  # mantener vivas las QProcess en vuelo

    @pyqtSlot(str, result=str)
    def start_terminal(self, path: str) -> str:
        """Arranca el servidor de terminal real (xterm + node-pty) con cwd en el
        proyecto y emite `terminal_ready` con la URL para embeber por iframe."""
        import shutil
        node = shutil.which("node")
        if not node:
            self.terminal_ready.emit(json.dumps({"path": path, "error": "node no encontrado"}))
            return json.dumps({"ok": False, "error": "node no encontrado"})
        proc = QProcess(self)
        proc.setWorkingDirectory(str(TERMINAL_DIR))
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)

        def _on_out():
            import urllib.parse
            data = bytes(proc.readAllStandardOutput()).decode(errors="replace")
            for line in data.splitlines():
                if line.startswith("PORT="):
                    port = line.split("=", 1)[1].strip()
                    url = (f"http://127.0.0.1:{port}/?cwd="
                           f"{urllib.parse.quote(path)}&cmd=bash")
                    self.terminal_ready.emit(json.dumps({"path": path, "url": url}))

        proc.readyReadStandardOutput.connect(_on_out)
        proc.start(node, [str(TERMINAL_DIR / "server.js"), "0"])
        self._procs.append(proc)
        return json.dumps({"ok": True, "starting": True})

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
        try:
            script = write_setup_script(
                project_dir=project_dir, stack_key=stack, template_type=ttype,
                project_name=name, agent_key=provider,
                run_autoskills=bool(opts.get("uipro", True)),
                mode="scratch", reference_kind=None, reference_value=None,
                existing_repo=None, create_github_repo=False, github_user=None,
                embedded=True, run_uipro=bool(opts.get("uipro", True)),
                niche=(niche or None), launch_agent=False,
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
    def suggest_stack(self, description: str) -> str:
        """Pre-fill Vibe real: usa el motor de sugerencia de ThemeForge
        (mismo que la GUI) para recomendar stack/tipo/prompt desde texto."""
        try:
            from mcp_server import suggest_stack as _ss
            return json.dumps(_ss(description))
        except Exception as e:
            return json.dumps({"error": str(e)})

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
