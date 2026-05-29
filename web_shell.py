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

# Bootstrap del puente inyectado en CUALQUIER prototipo (tras qwebchannel.js).
# Define window.tfApplyTheme + window.tfBridge / tfBridgeReady, y aplica las
# CSS vars del tema activo. Idempotente.
_BRIDGE_BOOTSTRAP_JS = r"""
(function(){
  window.tfApplyTheme = function(vars){
    if(!vars) return; var r=document.documentElement;
    Object.keys(vars).forEach(function(k){ r.style.setProperty(k, vars[k]); });
  };
  try { var d=window.__TF_DATA__||{}; var cur=d.current_theme;
    var t=(d.themes||[]).find(function(x){return x.k===cur;});
    if(t&&t.vars) window.tfApplyTheme(t.vars);
  } catch(e){}
  if (window.__tfBridgeInit) return; window.__tfBridgeInit = true;
  window.tfBridge = null;
  window.tfBridgeReady = new Promise(function(resolve){
    function connect(){
      if(typeof qt==='undefined' || !qt.webChannelTransport){ return resolve(null); }
      new QWebChannel(qt.webChannelTransport, function(ch){
        window.tfBridge = ch.objects.bridge; resolve(window.tfBridge);
      });
    }
    if(document.readyState!=='loading') connect();
    else window.addEventListener('DOMContentLoaded', connect);
  });
})();
"""


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


# Temas "web" (recolor en vivo de la UI Neo-Tokyo). El resto son clásicos
# (UI nativa de QWidgets) y al elegirlos se reinicia en modo clásico.
_WEB_THEMES = {"neotokyo"}


def _hex_rgb(h: str) -> str:
    """'#rrggbb' → 'r, g, b' (para las CSS vars *-rgb del prototipo)."""
    try:
        h = h.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return f"{int(h[0:2],16)}, {int(h[2:4],16)}, {int(h[4:6],16)}"
    except Exception:
        return "0, 240, 255"


def _theme_css_vars(pack) -> dict:
    """Mapea los tokens del ThemePack a las CSS vars que usa el prototipo web,
    para que elegir un tema RECOLOREE la UI web en vivo."""
    c = pack.color
    acc = c.accent
    acc2 = getattr(c, "danger", None) or getattr(c, "accent_hover", None) or "#ff2e88"
    return {
        "--bg-void": c.bg_primary, "--bg-deep": c.bg_secondary,
        "--bg-panel": c.bg_secondary, "--bg-panel-2": c.bg_tertiary,
        "--bg-raise": c.bg_elevated,
        "--tx": c.fg_primary, "--tx-dim": c.fg_secondary, "--tx-faint": c.fg_disabled,
        "--line": c.border, "--line-bright": c.border_strong,
        "--accent": acc, "--accent-2": acc2,
        "--accent-rgb": _hex_rgb(acc), "--accent2-rgb": _hex_rgb(acc2),
    }


WEBTHEMES_DIR = WEBUI_DIR.parent / "themes"   # webui/themes/*.json (packs)


def _web_theme_packs() -> list:
    """Auto-descubre temas web enchufables: cualquier webui/themes/*.json se
    convierte en un tema seleccionable que recolorea la UI web en vivo. Soltar
    un JSON = nuevo tema, sin código (design-tokens → CSS vars)."""
    out = []
    if not WEBTHEMES_DIR.is_dir():
        return out
    for f in sorted(WEBTHEMES_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        v = data.get("vars") or {}
        out.append({
            "k": "web:" + f.stem, "label": data.get("name", f.stem),
            "jp": data.get("jp", ""),
            "bg": v.get("--bg-void", "#04060c"),
            "acc": v.get("--accent", "#00f0ff"),
            "acc2": v.get("--accent-2", "#ff2e88"),
            "vars": v, "web": True, "pack": True,
        })
    return out


# Paleta de swatch para las cards de los prototipos web (color de preview).
_PROTO_META = {
    "neotokyo": {"label": "Neo-Tokyo", "jp": "ネオ東京", "bg": "#04060c", "acc": "#00f0ff", "acc2": "#ff2e88"},
    "matrix":   {"label": "Matrix", "jp": "マトリックス", "bg": "#040804", "acc": "#00ff41", "acc2": "#00b894"},
    "kawaii":   {"label": "Kawaii", "jp": "カワイイ", "bg": "#fff5fa", "acc": "#ff8fc7", "acc2": "#b9a3ff"},
}


def _web_prototypes() -> list:
    """Prototipos web completos (carpetas en webui/ con index.html). Cada uno es
    un DISEÑO entero con su splash; cambiar a uno recarga el WebShell."""
    out = []
    base = WEBUI_DIR.parent
    if not base.is_dir():
        return out
    for d in sorted(base.iterdir()):
        if not d.is_dir() or d.name == "themes" or not (d / "index.html").is_file():
            continue
        m = _PROTO_META.get(d.name, {"label": d.name.title(), "jp": "",
                                     "bg": "#0b0b10", "acc": "#888", "acc2": "#aaa"})
        out.append({"k": d.name, "label": m["label"], "jp": m["jp"],
                    "bg": m["bg"], "acc": m["acc"], "acc2": m["acc2"],
                    "vars": {}, "web": True, "proto": True})
    return out


def _themes_data() -> dict:
    try:
        import themes
        try:
            import app_prefs as ap
            cur = ap.get("web_theme") or themes.current_theme_name()
        except Exception:
            cur = themes.current_theme_name()
        # Prototipos web (diseños completos) primero, luego packs recolor.
        out = _web_prototypes() + list(_web_theme_packs())
        _proto_keys = {p["k"] for p in out if p.get("proto")}
        for ti in themes.list_themes():
            if ti.name in _proto_keys:  # neotokyo ya está como prototipo web
                continue
            try:
                pack = themes.load_theme(ti.name)
                acc = pack.color.accent
                acc2 = getattr(pack.color, "danger", "#ff2e88")
                bg = pack.color.bg_primary
                cssvars = _theme_css_vars(pack)
            except Exception:
                acc, acc2, bg, cssvars = "#00f0ff", "#ff2e88", "#04060c", {}
            out.append({
                "k": ti.name, "label": ti.display_name,
                "jp": _THEME_JP.get(ti.name, ""),
                "bg": bg, "acc": acc, "acc2": acc2, "vars": cssvars,
                # 'web' = recolorea la UI web en vivo; el resto = UI nativa
                # (requiere reinicio para cargar el sistema clásico de QWidgets).
                "web": ti.name in _WEB_THEMES,
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


def _active_preview(proj):
    """(profile, root) del preview — igual que `_compute_active_profile` nativo:
    si la raíz no tiene perfil pero hay sub-proyectos (mono-repo, o app dentro de
    apps/, web/, etc.), elige el sub-proyecto de cara al cliente con perfil. Así
    Re-detectar/Start funcionan aunque el scaffold haya quedado en un subdir."""
    from pathlib import Path
    try:
        from preview import detect_preview_profile, detect_subprojects
    except Exception:
        return None, proj
    prof = detect_preview_profile(proj)
    if prof:
        return prof, proj
    try:
        subs = detect_subprojects(proj) or []
    except Exception:
        subs = []
    cands = [s for s in subs if s.get("profile")]
    if not cands:
        return None, proj
    _FRONT = ("web", "site", "storefront", "frontend", "www", "app", "client",
              "landing", "marketing", "shop", "store", "public")
    _BACK = ("admin", "api", "backend", "server", "dashboard", "cms", "docs", "studio", "worker")

    def _rank(s):
        name = (s.get("name") or "").lower()
        return (1, 1 if any(k in name for k in _FRONT) else 0,
                0 if any(k in name for k in _BACK) else 1)

    best = max(cands, key=_rank)
    return best.get("profile"), Path(best["path"])


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
    # Pide al WebShell recargar el prototipo activo (cambio de diseño web).
    reload_requested = pyqtSignal()
    # El setup (pestaña Setup) terminó: JSON {path} → la UI pasa a la pestaña Agente.
    setup_done = pyqtSignal(str)

    @pyqtSlot(str, result=str)
    def use_web_theme(self, slug: str) -> str:
        """Cambia el DISEÑO web (prototipo Neo-Tokyo/Matrix/Kawaii): persiste y
        recarga el WebShell al prototipo elegido (cada uno con su splash propio)."""
        try:
            import app_prefs as ap
            ap.set("web_theme", slug)
            ap.set_ui_mode("web")
            self.reload_requested.emit()
            return json.dumps({"ok": True, "slug": slug})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

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
        self._preview_procs = {}  # path -> (QProcess, url) del dev server de preview
        self._setup_scripts = {}  # path -> ruta del setup script pendiente (pestaña Setup)
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
        cmd, args = self._agent_launch_for(path)
        return self._start_terminal(path, cmd, args, "agent")

    @pyqtSlot(str, result=str)
    def start_shell(self, path: str) -> str:
        """Shell bash pelado (sin IA). Pestaña «Shell»."""
        return self._start_terminal(path, "bash", [], "shell")

    @pyqtSlot(str, result=str)
    def start_hermes(self, path: str) -> str:
        """Pestaña «Hermes»: corre `hermes -s themeforge-operator` interactivo en
        el cwd del proyecto (si Hermes está instalado), igual que el tab nativo."""
        import shutil
        from pathlib import Path
        hermes = shutil.which("hermes") or str(Path.home() / ".local" / "bin" / "hermes")
        if not Path(hermes).is_file():
            self.terminal_ready.emit(json.dumps({"path": path, "kind": "hermes", "error": "Hermes no instalado"}))
            return json.dumps({"ok": False, "error": "Hermes no instalado"})
        return self._start_terminal(path, hermes, ["-s", "themeforge-operator"], "hermes")

    @pyqtSlot(str, result=str)
    def start_setup(self, path: str) -> str:
        """Pestaña «Setup»: ejecuta el setup REAL (scaffold + npm install +
        autoskills + UI/UX Pro) en un terminal con PTY (node-pty) y deja una
        shell interactiva al terminar — idéntico al tab «Setup» de la app nativa.
        Al acabar el script toca un fichero-marca y el bridge emite `setup_done`
        para que la UI cambie sola a la pestaña Agente."""
        import shlex
        from pathlib import Path
        script = self._setup_scripts.get(path)
        if not script:
            self.terminal_ready.emit(json.dumps({"path": path, "kind": "setup", "error": "sin setup pendiente (proyecto ya creado)"}))
            return json.dumps({"ok": False, "error": "sin setup"})
        marker = Path(path) / ".tf_setup_done"
        try:
            if marker.exists():
                marker.unlink()
        except Exception:
            pass
        wrapper = (f"clear; echo '─── ThemeForge: ejecutando setup ───'; "
                   f"bash {shlex.quote(script)}; "
                   f"echo ''; echo '─── setup terminado. Shell lista. ───'; "
                   f"touch {shlex.quote(str(marker))} 2>/dev/null; exec bash -i")
        out = self._start_terminal(path, "bash", ["-lc", wrapper], "setup")
        # Vigila el fichero-marca → emite setup_done (la UI pasa a Agente).
        timer = QTimer(self)
        timer.setInterval(1500)
        ticks = {"n": 0}

        def _poll():
            ticks["n"] += 1
            if marker.exists():
                try:
                    marker.unlink()
                except Exception:
                    pass
                self.setup_done.emit(json.dumps({"path": path}))
                timer.stop()
            elif ticks["n"] > 1200:  # ~30 min de guarda
                timer.stop()

        timer.timeout.connect(_poll)
        timer.start()
        return out

    def _start_terminal(self, path: str, cmd: str, args, kind: str) -> str:
        import shutil
        node = shutil.which("node")
        if not node:
            self.terminal_ready.emit(json.dumps({"path": path, "kind": kind, "error": "node no encontrado"}))
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
                    q = (f"cwd={urllib.parse.quote(path)}"
                         f"&cmd={urllib.parse.quote(cmd)}")
                    if args:
                        q += "&args=" + urllib.parse.quote("\x1f".join(args))
                    url = f"http://127.0.0.1:{port}/?{q}"
                    self.terminal_ready.emit(json.dumps({"path": path, "kind": kind, "url": url}))

        proc.readyReadStandardOutput.connect(_on_out)
        proc.start(node, [str(TERMINAL_DIR / "server.js"), "0"])
        self._procs.append(proc)
        return json.dumps({"ok": True, "starting": True, "kind": kind})

    @pyqtSlot(str, result=str)
    def start_preview(self, path: str) -> str:
        """Arranca el dev server real del proyecto (detección de preview.py) y
        emite `preview_ready` con la URL para embeber por iframe."""
        try:
            from preview import apply_port, get_port_for_project
            import platform_compat as pc
            import shlex
            from pathlib import Path
            proj = Path(path)
            # Detección subproject-aware (mono-repo / app en subdir), como la nativa.
            prof, root = _active_preview(proj)
            if not prof:
                self.preview_ready.emit(json.dumps(
                    {"path": path, "error": "sin preview detectable (¿deps instaladas? ¿está en un subdir?)"}))
                return json.dumps({"ok": False, "error": "sin preview"})
            port = get_port_for_project(root.name, prof.get("default_port", 5173))
            cmd, env_extra, url = apply_port(prof, port)
            proc = QProcess(self)
            proc.setWorkingDirectory(str(root))
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
            self._preview_procs[path] = (proc, url)
            QTimer.singleShot(4800, lambda: self.preview_ready.emit(
                json.dumps({"path": path, "url": url})))
            return json.dumps({"ok": True, "starting": True, "url": url})
        except Exception as e:
            self.preview_ready.emit(json.dumps({"path": path, "error": str(e)}))
            return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(str, result=str)
    def stop_preview(self, path: str) -> str:
        """Para el dev server de preview de un proyecto (sin borrar datos)."""
        try:
            entry = self._preview_procs.pop(path, None)
            if not entry:
                return json.dumps({"ok": True, "already": True})
            proc, _url = entry
            if proc and proc.state() != QProcess.ProcessState.NotRunning:
                proc.terminate()
                if not proc.waitForFinished(3000):
                    proc.kill()
            self.preview_ready.emit(json.dumps({"path": path, "stopped": True}))
            return json.dumps({"ok": True, "stopped": True})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(str, result=str)
    def refresh_profile(self, path: str) -> str:
        """Re-detecta el perfil de preview (tras instalar deps / correr setup),
        mirando también sub-proyectos (mono-repo / app en subdir). Devuelve
        {ok, detected, profile, root}."""
        try:
            from pathlib import Path
            prof, root = _active_preview(Path(path))
            return json.dumps({"ok": True, "detected": bool(prof),
                               "profile": (prof or {}).get("name", ""),
                               "root": str(root)})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(str, result=str)
    def open_preview_external(self, path: str) -> str:
        """Abre la URL del preview en el navegador externo (modo app)."""
        try:
            entry = self._preview_procs.get(path)
            url = entry[1] if entry else None
            if not url:
                return json.dumps({"ok": False, "error": "preview no arrancado"})
            import webbrowser
            webbrowser.open(url)
            return json.dumps({"ok": True, "url": url})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(str, result=str)
    def open_external_terminal(self, path: str) -> str:
        """Abre una terminal externa del sistema con cwd en el proyecto."""
        try:
            import shutil
            import subprocess
            for term, args in (("konsole", ["--workdir", path]),
                               ("gnome-terminal", ["--working-directory=" + path]),
                               ("xterm", ["-e", "cd " + path + " && bash"]),
                               ("kitty", ["--directory", path]),
                               ("alacritty", ["--working-directory", path])):
                if shutil.which(term):
                    subprocess.Popen([term] + args)
                    return json.dumps({"ok": True, "terminal": term})
            return json.dumps({"ok": False, "error": "no se encontró terminal"})
        except Exception as e:
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

    @pyqtSlot(str, result=str)
    def detect_ref_stack(self, path: str) -> str:
        """Auto-detección de stack desde una referencia (igual que el normal):
        si la carpeta/.zip es un theme/plugin de WordPress, devuelve ese stack
        para fijarlo automáticamente; si no, devuelve el framework detectado."""
        from pathlib import Path
        try:
            import reference_analyzer as ra
            from stacks import STACKS
            p = Path(path)
            if not p.exists():
                return json.dumps({"stack": "", "framework": ""})
            wp = None
            try:
                wp = ra.detect_wordpress_stack(p)
            except Exception:
                wp = None
            if wp and wp in STACKS:
                return json.dumps({"stack": wp, "label": STACKS[wp].get("name", wp), "wp": True})
            # Framework genérico (informativo; el stack final lo recomienda la IA).
            try:
                facts = ra.gather_facts(p)
                fw = facts.get("framework") or facts.get("preview_profile") or ""
            except Exception:
                fw = ""
            return json.dumps({"stack": "", "framework": fw})
        except Exception as e:
            return json.dumps({"stack": "", "error": str(e)})

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
        mode = cfg.get("mode") or "scratch"
        if mode not in ("scratch", "recreate", "adopt", "existing"):
            mode = "scratch"
        existing_repo = (cfg.get("existing_repo") or "").strip() or None
        # Modo existing (work on existing repo): slug/nombre = nombre de la repo,
        # NO se pide nombre (como pidió el user, en web y nativo).
        if mode == "existing" and existing_repo:
            repo_clean = existing_repo.replace(".git", "").rstrip("/")
            repo_name = repo_clean.split("/")[-1] or "repo"
            name = name or repo_name
            slug = repo_name
            project_dir = PROJECTS_DIR / slug
        else:
            slug = slugify(name)
            project_dir = PROJECTS_DIR / slug
            n = 2
            while project_dir.exists() and any(project_dir.iterdir()):
                slug = f"{slugify(name)}-{n}"; project_dir = PROJECTS_DIR / slug; n += 1
        # Inyecta el análisis IA de referencia (si se hizo uno) en CLAUDE.md,
        # igual que el modo recreate del normal — así "se queda guardado".
        ai_analysis = None
        ref_value = (cfg.get("reference") or "").strip()
        ref_kind = cfg.get("reference_kind") or None
        if self._last_reference_analysis and self._last_reference_analysis[1]:
            stored_val, stored_txt = self._last_reference_analysis
            if (not ref_value) or stored_val == ref_value:
                ai_analysis = stored_txt
        # Toggles del Setup (como en el normal): autoskills + UI/UX Pro + MCP.
        run_autoskills = bool(opts.get("autoskills", True))
        run_uipro = bool(opts.get("uipro", True))
        want_mcp = bool(opts.get("mcp", True))
        force_pg = bool(opts.get("postgres", False))
        adopt_src = ref_value if mode == "adopt" else None
        try:
            script = write_setup_script(
                project_dir=project_dir, stack_key=stack, template_type=ttype,
                project_name=name, agent_key=provider,
                run_autoskills=run_autoskills,
                mode=mode,
                reference_kind=(ref_kind if mode == "recreate" else None),
                reference_value=(ref_value if mode == "recreate" else None),
                existing_repo=(existing_repo if mode == "existing" else None),
                create_github_repo=False, github_user=None,
                embedded=True, run_uipro=run_uipro,
                force_postgres=force_pg, adopt_src=adopt_src,
                is_licensed_product=bool(opts.get("licensing", False)),
                licensing_create_gh_repo=bool(opts.get("licensing_gh", False)),
                licensing_force_all_modes=bool(opts.get("licensing_force", False)),
                niche=(niche or None), launch_agent=False,
                ai_analysis=ai_analysis, ai_analysis_kind="reference",
            )
        except Exception as e:
            return json.dumps({"ok": False, "error": f"write_setup_script: {e}"})
        # Pre-configurar MCP servers (.mcp.json) si el toggle está activo —
        # paso separado, igual que el builder nativo.
        if want_mcp:
            try:
                import mcp_catalog as _mc
                project_dir.mkdir(parents=True, exist_ok=True)
                recs = _mc.recommend_for_stack(stack, STACKS.get(stack, {}))
                if (mode == "recreate" and ref_kind == "figma"
                        and not any(getattr(e, "key", "") == "figma-context" for e in recs)):
                    _fig = next((e for e in _mc.CATALOG if e.key == "figma-context"), None)
                    if _fig:
                        recs.append(_fig)
                _mc.write_mcp_json(project_dir, recs)
            except Exception as e:
                self.progress.emit(f"[mcp] aviso: {e}\n")
        # Registrar en projects-meta (igual que el normal).
        try:
            meta = load_projects_meta()
            meta[slug] = {"name": name, "stack": stack, "provider": provider,
                          "mode": mode, "type": ttype}
            save_projects_meta(meta)
        except Exception:
            pass

        PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
        # El setup PESADO (scaffold + npm install + autoskills + UI/UX Pro) se
        # ejecuta en un TERMINAL REAL con PTY (node-pty) en la pestaña «Setup»,
        # igual que la app nativa — NO headless: los scaffolders interactivos
        # (create-next-app, composer, etc.) necesitan TTY o fallan al instante.
        self._setup_scripts[str(project_dir)] = str(script)
        # Abrimos la ventana del proyecto ya; la pestaña Setup arrancará el script.
        self.build_done.emit(json.dumps(
            {"ok": True, "slug": slug, "name": name,
             "path": str(project_dir), "fresh": True}))
        return json.dumps({"ok": True, "slug": slug, "path": str(project_dir),
                           "name": name, "fresh": True})

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
    def list_projects(self) -> str:
        """Galería en vivo: re-escanea ~/Proyectos/themes/ y devuelve los
        proyectos reales (para refrescar tras crear uno, sin recargar)."""
        try:
            return json.dumps(_projects_data())
        except Exception as e:
            return json.dumps({"error": str(e)})

    @pyqtSlot(result=str)
    def bootstrap_data(self) -> str:
        """Todos los datos reales (stacks/proyectos/providers/temas) para
        refrescar el prototipo en vivo si hace falta."""
        try:
            return json.dumps(bootstrap_data())
        except Exception as e:
            return json.dumps({"error": str(e)})

    @pyqtSlot(str, result=str)
    def switch_to_classic(self, theme: str) -> str:
        """Cambia al SISTEMA DE TEMAS NORMAL (UI nativa QWidgets): persiste el
        tema + ui_mode=classic y REINICIA ThemeForge para cargar la UI clásica
        (los temas nativos no aplican sobre la UI web)."""
        try:
            import themes
            import app_prefs as ap
            themes.save_current_theme(theme)
            ap.set_ui_mode("classic")
            self._restart()
            return json.dumps({"ok": True, "restarting": True})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(result=str)
    def use_web_ui(self) -> str:
        """Vuelve a la UI web Neo-Tokyo (ui_mode=web) y reinicia."""
        try:
            import app_prefs as ap
            ap.set_ui_mode("web")
            self._restart()
            return json.dumps({"ok": True, "restarting": True})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    def _restart(self):
        """Reinicio limpio cross-platform (Qt docs): startDetached + quit."""
        import sys
        from PyQt6.QtWidgets import QApplication
        QProcess.startDetached(sys.executable, sys.argv)
        app = QApplication.instance()
        if app is not None:
            QTimer.singleShot(150, app.quit)

    @pyqtSlot(str, result=str)
    def set_theme(self, name: str) -> str:
        """Persiste el tema web elegido. Los temas-pack ('web:slug') se guardan
        en app_prefs (no son temas nativos); los nativos en settings.json."""
        try:
            import app_prefs as ap
            if name.startswith("web:"):
                ap.set("web_theme", name)
                return json.dumps({"ok": True, "theme": name, "pack": True})
            # Tema web base (neotokyo) o nativo: recordar y aplicar a lo nativo.
            ap.set("web_theme", name)
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
    def licensing_api(self, path: str, method: str, body_json: str) -> str:
        """Passthrough al panel de licencias local (mismos endpoints que la
        LicensingPanel nativa): /api/products/versions, /api/gumroad,
        /api/integrations/status, /api/tools/ping, /api/products/versions/release,
        /api/tools/notify-update… PANEL_BASE viene de config local (gitignored)."""
        try:
            from licensing_panel import _api
            body = json.loads(body_json) if (body_json or "").strip() else None
            code, data = _api(path, method or "GET", body)
            return json.dumps({"code": code, "data": data})
        except Exception as e:
            return json.dumps({"code": 0, "data": {"error": str(e)}})

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

    @pyqtSlot(result=str)
    def pixel_office_url(self) -> str:
        """URL del dashboard Pixel Office para la pestaña «Office» (lo arranca si
        está instalado pero apagado). Devuelve {installed, up, url}."""
        try:
            import pixel_office
            url = getattr(pixel_office, "DASHBOARD_URL", "")
            up = pixel_office.is_dashboard_up()
            installed = up or bool(pixel_office.find_install_dir())
            if installed and not up:
                try:
                    pixel_office.launch_background()
                except Exception:
                    pass
            return json.dumps({"installed": installed, "up": up, "url": url})
        except Exception as e:
            return json.dumps({"installed": False, "up": False, "url": "", "error": str(e)})

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

    @pyqtSlot(str, result=str)
    def github_create(self, path: str) -> str:
        """Crea el repo en GitHub (gh repo create) si no hay remote, y empuja.
        Async; progreso por la señal `progress`. Igual que el botón GitHub nativo."""
        from pathlib import Path
        import shutil
        proj = Path(path)
        if not shutil.which("gh"):
            self.progress.emit("[github] falta gh CLI (instala github-cli y haz gh auth login)\n")
            return json.dumps({"ok": False, "error": "gh CLI no encontrado"})
        name = proj.name
        cmd = (
            'git rev-parse --git-dir >/dev/null 2>&1 || git init; '
            'git add -A && git commit -m "ThemeForge: publish" || true; '
            'if git remote get-url origin >/dev/null 2>&1; then '
            '  git push -u origin HEAD 2>&1; '
            f'else gh repo create "{name}" --private --source=. --remote=origin --push 2>&1; fi'
        )
        proc = QProcess(self)
        proc.setWorkingDirectory(str(proj))
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.readyReadStandardOutput.connect(
            lambda: self.progress.emit(bytes(proc.readAllStandardOutput()).decode(errors="replace")))
        proc.finished.connect(lambda c, _s: self.progress.emit(f"\n■ github (exit {c}).\n"))
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
        self._port = None
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            from PyQt6.QtWebChannel import QWebChannel
        except Exception as e:
            root.addWidget(QLabel(f"QtWebEngine no disponible: {e}"))
            return

        webui_root = WEBUI_DIR.parent  # sirve TODA webui/ → /<tema>/index.html
        self._port = _free_port()
        self._httpd = _serve(webui_root, self._port)

        self._view = QWebEngineView()
        self._bridge = ThemeForgeBridge()
        # Reload del shell cuando se cambia de prototipo web (Matrix/Kawaii/…).
        self._bridge.reload_requested.connect(self._reload_active)
        self._channel = QWebChannel(self._view.page())
        self._channel.registerObject("bridge", self._bridge)
        self._view.page().setWebChannel(self._channel)
        self._inject_scripts()
        root.addWidget(self._view)
        self._reload_active()

    def _active_slug(self) -> str:
        """Prototipo web activo (carpeta en webui/). Packs/temas sin carpeta →
        prototipo base 'neotokyo' (el pack recolorea encima)."""
        try:
            import app_prefs as ap
            raw = (ap.get("web_theme") or "neotokyo")
        except Exception:
            raw = "neotokyo"
        slug = raw[4:] if raw.startswith("web:") else raw
        if (WEBUI_DIR.parent / slug / "index.html").is_file():
            return slug
        return "neotokyo"

    def _inject_scripts(self):
        """Inyecta en DocumentCreation: (1) window.__TF_DATA__ con datos reales,
        (2) el puente (qwebchannel + window.tfBridge + tfApplyTheme). Así CUALQUIER
        prototipo (Neo-Tokyo/Matrix/Kawaii) recibe datos + puente sin editar su HTML."""
        try:
            from PyQt6.QtWebEngineCore import QWebEngineScript
            page = self._view.page()
            # 1) datos reales.
            s1 = QWebEngineScript()
            s1.setName("tf_data")
            s1.setSourceCode("window.__TF_DATA__ = " + json.dumps(bootstrap_data()) + ";")
            s1.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
            s1.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
            page.scripts().insert(s1)
            # 2) puente (qwebchannel.js embebido + bootstrap).
            qwc = ""
            qwc_file = WEBUI_DIR / "qwebchannel.js"
            if qwc_file.is_file():
                qwc = qwc_file.read_text(encoding="utf-8", errors="replace")
            s2 = QWebEngineScript()
            s2.setName("tf_bridge")
            s2.setSourceCode(qwc + "\n" + _BRIDGE_BOOTSTRAP_JS)
            s2.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
            s2.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
            page.scripts().insert(s2)
        except Exception as e:
            print(f"[webshell] no se pudieron inyectar scripts: {e}")

    def _reload_active(self):
        from PyQt6.QtCore import QUrl
        slug = self._active_slug()
        self._view.setUrl(QUrl(f"http://127.0.0.1:{self._port}/{slug}/index.html"))

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
