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
import os
import re
import socket
import threading
import time
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


def _projects_data(archived: bool = False) -> list:
    try:
        from themeforge import list_projects, load_favorites, load_projects_meta
        rows = list_projects(archived=archived)
    except Exception:
        return []
    try:
        favs = load_favorites()
    except Exception:
        favs = set()
    try:
        meta = load_projects_meta()
    except Exception:
        meta = {}
    rows.sort(key=lambda r: r.get("mtime", 0), reverse=True)
    out = []
    for r in rows:
        agent = (r.get("provider") or r.get("agent") or "claude")
        git = r.get("git_status", "")
        slug = r.get("slug", "") or r.get("name", "")
        mtags = (meta.get(slug, {}) or {}).get("tags") or []
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
            "tags": mtags if mtags else [t for t in [r.get("stack", "")] if t],
            "fav": slug in favs,
            "archived": bool(archived),
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


# Scripts de setup pendientes (path → script), GLOBAL para que la pestaña Setup
# de una VENTANA DE PROYECTO nueva (otra instancia de bridge) lo encuentre.
_SETUP_SCRIPTS = {}


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
    # Pide al WebShell abrir el proyecto en una VENTANA NUEVA (como el nativo): (path, fresh).
    open_window_requested = pyqtSignal(str, bool)
    # Eventos de operaciones Hermes async (instalar skill, dispatch, draft IA,
    # enviar mensaje, insights, test del cerebro…). JSON {op, line?|done?|ok?|out?|text?}.
    hermes_event = pyqtSignal(str)

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
        self._preview_states = {}  # path -> dict de estado del sondeo de preview
        self._setup_scripts = _SETUP_SCRIPTS  # ref al dict GLOBAL (compartido entre ventanas)
        self._dialogs = []  # refs a diálogos nativos abiertos (evitar GC)
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

    @pyqtSlot(result=str)
    def start_hermes_chat(self) -> str:
        """Chat Hermes (Operator) sin proyecto concreto — corre en ~ . Emite
        `terminal_ready` con kind 'hermes-chat' (path = home)."""
        import shutil
        from pathlib import Path
        hermes = shutil.which("hermes") or str(Path.home() / ".local" / "bin" / "hermes")
        if not Path(hermes).is_file():
            self.terminal_ready.emit(json.dumps({"path": "~", "kind": "hermes-chat", "error": "Hermes no instalado"}))
            return json.dumps({"ok": False, "error": "Hermes no instalado"})
        return self._start_terminal(str(Path.home()), hermes, ["-s", "themeforge-operator"], "hermes-chat")

    @pyqtSlot(result=str)
    def hermes_admin(self) -> str:
        """Arranca el dashboard web de Hermes (`hermes dashboard --tui`) en un
        puerto libre, sondea hasta que responda y emite `terminal_ready`
        {kind:'hermes-admin', url} para embeberlo por iframe."""
        import shutil
        from pathlib import Path
        hermes = shutil.which("hermes") or str(Path.home() / ".local" / "bin" / "hermes")
        if not Path(hermes).is_file():
            self.terminal_ready.emit(json.dumps({"kind": "hermes-admin", "error": "Hermes no instalado"}))
            return json.dumps({"ok": False, "error": "Hermes no instalado"})
        port = _free_port()
        proc = QProcess(self)
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.start(hermes, ["dashboard", "--tui", "--no-open", "--skip-build",
                            "--host", "127.0.0.1", "--port", str(port)])
        self._procs.append(proc)
        state = {"n": 0}
        timer = QTimer(self)
        timer.setInterval(700)

        def _poll():
            state["n"] += 1
            if self._port_is_open("127.0.0.1", port):
                self.terminal_ready.emit(json.dumps(
                    {"kind": "hermes-admin", "url": f"http://127.0.0.1:{port}/"}))
                timer.stop()
            elif state["n"] > 40:  # ~28s
                self.terminal_ready.emit(json.dumps(
                    {"kind": "hermes-admin", "error": "el dashboard no respondió a tiempo"}))
                timer.stop()
        timer.timeout.connect(_poll)
        timer.start()
        return json.dumps({"ok": True, "starting": True})

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
        """Arranca el dev server real (subproject-aware) y **sondea el puerto**
        hasta que escuche antes de cargar el iframe (igual que la app nativa) —
        nada de delays fijos. Sigue la URL real del stdout por si el framework
        coge otro puerto. Emite `preview_ready` {path,url}|{path,error}|{path,log}."""
        try:
            from preview import apply_port, get_port_for_project
            import platform_compat as pc
            import shlex
            from pathlib import Path
            proj = Path(path)
            prof, root = _active_preview(proj)
            if not prof:
                self.preview_ready.emit(json.dumps(
                    {"path": path, "error": "sin preview detectable (¿deps instaladas? ¿está en un subdir?)"}))
                return json.dumps({"ok": False, "error": "sin preview"})
            # Perfil sin servidor (WordPress en Docker): URL directa, sin sondeo.
            if prof.get("no_server"):
                url = prof.get("url") or ""
                self._preview_procs[path] = (None, url)
                self.preview_ready.emit(json.dumps({"path": path, "url": url}))
                return json.dumps({"ok": True, "url": url, "no_server": True})
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
            st = {"proc": proc, "url": url, "detected": False,
                  "deadline": time.monotonic() + 60.0,
                  "detached": bool(prof.get("stop"))}
            self._preview_states[path] = st
            proc.readyReadStandardOutput.connect(lambda: self._preview_out(path))
            cmd_str = " ".join(shlex.quote(c) for c in cmd)
            sh, args = pc.shell_program_and_args(cmd_str)
            proc.start(sh, args)
            self._procs.append(proc)
            self._preview_procs[path] = (proc, url)
            self.preview_ready.emit(json.dumps({"path": path, "log": f"$ {' '.join(cmd)}  (puerto {port})\n"}))
            QTimer.singleShot(400, lambda: self._preview_wait(path))
            return json.dumps({"ok": True, "starting": True, "url": url})
        except Exception as e:
            self.preview_ready.emit(json.dumps({"path": path, "error": str(e)}))
            return json.dumps({"ok": False, "error": str(e)})

    _DEV_URL_RE = re.compile(r"https?://(?:localhost|127\.0\.0\.1|0\.0\.0\.0):(\d+)", re.IGNORECASE)

    def _preview_out(self, path: str):
        """Lee stdout del dev server: lo manda al log del frontend y SIGUE la URL
        real que imprime el server (Vite/Next/Astro pueden coger otro puerto)."""
        st = self._preview_states.get(path)
        if not st or not st.get("proc"):
            return
        try:
            data = bytes(st["proc"].readAllStandardOutput()).decode(errors="replace")
        except Exception:
            return
        if not data:
            return
        self.preview_ready.emit(json.dumps({"path": path, "log": data}))
        if st.get("detected"):
            return
        m = self._DEV_URL_RE.search(data)
        if not m:
            return
        st["detected"] = True
        new_port = int(m.group(1))
        try:
            from PyQt6.QtCore import QUrl
            cur = QUrl(st["url"]).port()
        except Exception:
            cur = None
        if new_port and new_port != cur:
            st["url"] = f"http://localhost:{new_port}/"
            self._preview_procs[path] = (st["proc"], st["url"])
            st["deadline"] = time.monotonic() + 60.0
            self._preview_wait(path)

    def _preview_wait(self, path: str):
        """Sondea el puerto del dev server; carga el iframe SOLO cuando escucha.
        Si el proceso muere (y no es detached) avisa; si no responde en 60s carga
        igualmente para que el usuario pueda recargar."""
        st = self._preview_states.get(path)
        if not st:
            return
        proc = st.get("proc")
        proc_dead = (proc is None or proc.state() == QProcess.ProcessState.NotRunning)
        if proc_dead and not st.get("detached"):
            self.preview_ready.emit(json.dumps(
                {"path": path, "error": "el dev server terminó (revisa que el setup instaló las deps)"}))
            return
        try:
            from PyQt6.QtCore import QUrl
            u = QUrl(st["url"])
            host = u.host() or "127.0.0.1"
            port = u.port() or 0
        except Exception:
            host, port = "127.0.0.1", 0
        if port and self._port_is_open(host, port):
            QTimer.singleShot(400, lambda: self.preview_ready.emit(
                json.dumps({"path": path, "url": st["url"]})))
            return
        if time.monotonic() < st.get("deadline", 0):
            QTimer.singleShot(500, lambda: self._preview_wait(path))
        else:
            self.preview_ready.emit(json.dumps(
                {"path": path, "url": st["url"], "slow": True}))

    @staticmethod
    def _port_is_open(host: str, port: int, timeout: float = 0.4) -> bool:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            return False

    @pyqtSlot(str, result=str)
    def stop_preview(self, path: str) -> str:
        """Para el dev server de preview de un proyecto (sin borrar datos)."""
        try:
            self._preview_states.pop(path, None)  # corta el sondeo en curso
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
    def list_subprojects(self, path: str) -> str:
        """Sub-proyectos de un mono-repo (apps/web, apps/api…), para el dropdown
        de preview. Cada uno con su ruta absoluta y si tiene preview detectable."""
        try:
            from preview import detect_subprojects
            from pathlib import Path
            subs = detect_subprojects(Path(path)) or []
            out = [{"name": s.get("name", ""), "path": str(s.get("path", "")),
                    "rel": s.get("rel_path", ""), "has_preview": bool(s.get("profile")),
                    "ref": bool(s.get("from_reference"))} for s in subs]
            return json.dumps({"ok": True, "subprojects": out})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e), "subprojects": []})

    @pyqtSlot(str, result=str)
    def screenshot_preview(self, path: str) -> str:
        """Captura PNG del preview en marcha (Chromium headless) → guarda en
        <proyecto>/screenshots/preview-<ts>.png. Igual idea que el 📸 nativo."""
        try:
            import shutil
            import subprocess
            from pathlib import Path
            entry = self._preview_procs.get(path)
            url = entry[1] if entry else None
            if not url:
                return json.dumps({"ok": False, "error": "preview no arrancado"})
            chrome = next((c for c in ("chromium", "chromium-browser", "google-chrome",
                                       "google-chrome-stable", "brave", "brave-browser")
                           if shutil.which(c)), None)
            if not chrome:
                return json.dumps({"ok": False, "error": "no se encontró Chromium/Chrome para capturar"})
            shots = Path(path) / "screenshots"
            shots.mkdir(parents=True, exist_ok=True)
            stamp = time.strftime("%Y%m%d-%H%M%S")
            out = shots / f"preview-{stamp}.png"
            subprocess.Popen([chrome, "--headless=new", "--hide-scrollbars",
                              "--window-size=1440,900",
                              f"--screenshot={out}", url])
            return json.dumps({"ok": True, "file": str(out)})
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

    @pyqtSlot(str, str, int, result=str)
    def launch_mission_opts(self, brief: str, provider: str, variants: int) -> str:
        """Igual que launch_mission pero con N variantes + provider preferido
        (como la MissionTab nativa: el brief incluye «N variantes» y el provider)."""
        b = (brief or "").strip()
        if not b:
            return json.dumps({"ok": False, "error": "brief vacío"})
        n = max(1, min(int(variants or 1), 6))
        full = b
        if n > 1:
            full = f"Genera {n} variantes Envato-ready de: {b}"
        if provider:
            full += f"\n\n(Usa el agente «{provider}» para construir.)"
        return self.launch_mission(full)

    @pyqtSlot(result=str)
    def hermes_status(self) -> str:
        """Estado de Hermes para el status strip: versión · MCP themeforge
        registrado · provider·modelo configurados (igual que la tira nativa)."""
        try:
            from hermes_panel import hermes_version, _mcp_themeforge_registered, _hermes_model_info
            ver = hermes_version()
            prov, model = _hermes_model_info()
            return json.dumps({"available": bool(ver), "version": ver or "",
                               "mcp": bool(_mcp_themeforge_registered()),
                               "provider": prov or "", "model": model or ""})
        except Exception as e:
            return json.dumps({"available": False, "error": str(e)})

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
    def list_archived(self) -> str:
        """Proyectos archivados (en ~/Proyectos/themes-archive/)."""
        try:
            return json.dumps(_projects_data(archived=True))
        except Exception as e:
            return json.dumps({"error": str(e)})

    @pyqtSlot(str, str, str, result=str)
    def gallery_op(self, slug: str, op: str, arg: str) -> str:
        """Operaciones de la Galería sobre un proyecto (datos reales, igual que
        la GalleryPanel nativa): favorite | tags | archive | unarchive | delete."""
        try:
            from themeforge import (load_favorites, save_favorites,
                                    load_projects_meta, save_projects_meta,
                                    archive_project, unarchive_project, PROJECTS_DIR)
            if op == "favorite":
                favs = load_favorites()
                on = slug not in favs
                (favs.add if on else favs.discard)(slug)
                save_favorites(favs)
                return json.dumps({"ok": True, "fav": on})
            if op == "tags":
                meta = load_projects_meta()
                m = meta.get(slug, {}) or {}
                m["tags"] = [t.strip() for t in (arg or "").split(",") if t.strip()]
                meta[slug] = m
                save_projects_meta(meta)
                return json.dumps({"ok": True, "tags": m["tags"]})
            if op == "archive":
                ok, msg = archive_project(slug)
                return json.dumps({"ok": ok, "msg": msg})
            if op == "unarchive":
                ok, msg = unarchive_project(slug)
                return json.dumps({"ok": ok, "msg": msg})
            if op == "delete":
                import shutil
                from pathlib import Path
                d = PROJECTS_DIR / slug
                # Limpieza best-effort del contenedor Docker (postgres/WP) si lo hubiera.
                try:
                    from wp_provisioner import destroy as _wp_destroy
                    _wp_destroy(slug)
                except Exception:
                    pass
                if Path(d).is_dir():
                    shutil.rmtree(d, ignore_errors=True)
                favs = load_favorites(); favs.discard(slug); save_favorites(favs)
                meta = load_projects_meta(); meta.pop(slug, None); save_projects_meta(meta)
                return json.dumps({"ok": True, "deleted": slug})
            return json.dumps({"ok": False, "error": f"op desconocida: {op}"})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(result=str)
    def cost_data(self) -> str:
        """Re-escanea el coste de IA (donut + 30d + tabla de modelos + totales)."""
        try:
            return json.dumps(_cost_data())
        except Exception as e:
            return json.dumps({"error": str(e)})

    @pyqtSlot(str, result=str)
    def market_export(self, markdown: str) -> str:
        """Exporta un análisis de mercado a .md (selector de archivo nativo)."""
        try:
            from PyQt6.QtWidgets import QFileDialog
            f, _ = QFileDialog.getSaveFileName(None, "Exportar análisis", "analisis-mercado.md", "Markdown (*.md)")
            if not f:
                return json.dumps({"ok": False, "cancelled": True})
            from pathlib import Path
            Path(f).write_text(markdown or "", encoding="utf-8")
            return json.dumps({"ok": True, "file": f})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

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
    def read_mcp(self, path: str) -> str:
        """Lee el `.mcp.json` REAL del proyecto y devuelve el catálogo de MCP
        servers con flag `active` (presente en el archivo). Igual fuente que el
        setup nativo (mcp_catalog.CATALOG)."""
        try:
            import mcp_catalog as mc
            from pathlib import Path
            f = Path(path) / ".mcp.json"
            active = set()
            if f.is_file():
                try:
                    data = json.loads(f.read_text(encoding="utf-8", errors="ignore"))
                    active = set((data.get("mcpServers") or {}).keys())
                except Exception:
                    pass
            out = []
            cat_keys = set()
            for e in mc.CATALOG:
                cat_keys.add(e.key)
                out.append({"id": e.key, "label": e.name, "desc": e.description,
                            "lic": e.license, "auth": bool(getattr(e, "requires_auth", False)),
                            "active": e.key in active})
            # Servers en el .mcp.json que no están en el catálogo (custom).
            for k in (active - cat_keys):
                out.append({"id": k, "label": k, "desc": "(personalizado)",
                            "lic": "", "auth": False, "active": True})
            return json.dumps({"ok": True, "servers": out, "has_file": f.is_file()})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e), "servers": []})

    @pyqtSlot(str, str, result=str)
    def toggle_mcp(self, path: str, key: str) -> str:
        """Activa/desactiva un MCP server en el `.mcp.json` del proyecto (escritura
        real, preservando servers personalizados). Devuelve {ok, active}."""
        try:
            import mcp_catalog as mc
            from pathlib import Path
            f = Path(path) / ".mcp.json"
            data = {"mcpServers": {}}
            if f.is_file():
                try:
                    loaded = json.loads(f.read_text(encoding="utf-8", errors="ignore"))
                    if isinstance(loaded, dict):
                        data = loaded
                except Exception:
                    pass
            servers = data.get("mcpServers") or {}
            if key in servers:
                del servers[key]
            else:
                e = mc.by_key(key)
                if not e:
                    return json.dumps({"ok": False, "error": f"MCP desconocido: {key}"})
                spec = mc.generate_mcp_json([e], Path(path))["mcpServers"].get(key, {})
                servers[key] = spec
            data["mcpServers"] = servers
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            return json.dumps({"ok": True, "active": list(servers.keys()),
                               "on": key in servers})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    # ───────────────────────── Settings (Tanda 2) ──────────────────────────
    @pyqtSlot(result=str)
    def system_status(self) -> str:
        """Estado del sistema: GitHub, agentes IA, runtimes y tools detectados
        (igual que el panel «System status» nativo). Presencia por `which`."""
        import shutil
        import subprocess
        def _ver(args):
            try:
                out = subprocess.run(args, capture_output=True, text=True, timeout=2.5)
                return (out.stdout or out.stderr).splitlines()[0].strip()[:60]
            except Exception:
                return ""
        sections = []
        # GitHub
        gh = shutil.which("gh")
        gh_detail = ""
        if gh:
            try:
                r = subprocess.run(["gh", "api", "user", "-q", ".login"], capture_output=True, text=True, timeout=3)
                gh_detail = ("@" + r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else "sin login (gh auth login)"
            except Exception:
                gh_detail = "instalado"
        sections.append({"title": "GitHub", "items": [
            {"name": "gh", "ok": bool(gh), "detail": gh_detail or "no instalado"}]})
        # Agentes IA
        agents = []
        for t in ("claude", "codex", "gemini", "opencode", "sgpt"):
            p = shutil.which(t)
            agents.append({"name": t, "ok": bool(p), "detail": p or "✗ no en PATH"})
        sections.append({"title": "Agentes IA", "items": agents})
        # Runtimes
        rt = []
        for t, args in (("node", ["node", "--version"]), ("npm", ["npm", "--version"]),
                        ("bun", ["bun", "--version"]), ("pnpm", ["pnpm", "--version"]),
                        ("python3", ["python3", "--version"]), ("php", ["php", "--version"]),
                        ("composer", ["composer", "--version"]), ("flutter", ["flutter", "--version"]),
                        ("go", ["go", "version"]), ("cargo", ["cargo", "--version"]),
                        ("deno", ["deno", "--version"]), ("ruby", ["ruby", "--version"])):
            p = shutil.which(t)
            rt.append({"name": t, "ok": bool(p), "detail": (_ver(args) or p) if p else "✗ no en PATH"})
        sections.append({"title": "Runtimes", "items": rt})
        # Tools
        tools = []
        for t in ("docker", "git", "wget", "unzip", "sshpass", "shopify", "wp", "netlify", "vercel", "surge"):
            p = shutil.which(t)
            tools.append({"name": t, "ok": bool(p), "detail": p or "✗ no en PATH"})
        sections.append({"title": "Tools", "items": tools})
        return json.dumps({"ok": True, "sections": sections})

    def _open_native_dialog(self, factory):
        """Crea y muestra un diálogo nativo (no modal), guardando ref para que no
        lo recoja el GC. `factory` devuelve el QWidget/QDialog."""
        try:
            w = factory()
            self._dialogs = [d for d in self._dialogs if d is not None]
            self._dialogs.append(w)
            w.show()
            w.raise_()
            w.activateWindow()
            return json.dumps({"ok": True})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(result=str)
    def open_credentials(self) -> str:
        """Abre el gestor de credenciales NATIVO (instalar CLI / login OAuth /
        add-edit-remove API key + token Figma) en una ventana."""
        def _f():
            from PyQt6.QtWidgets import QDialog, QVBoxLayout
            from credentials_panel import CredentialsWidget
            dlg = QDialog()
            dlg.setWindowTitle("ThemeForge — Credenciales IA")
            dlg.resize(560, 480)
            lay = QVBoxLayout(dlg)
            lay.addWidget(CredentialsWidget(dlg))
            return dlg
        return self._open_native_dialog(_f)

    @pyqtSlot(result=str)
    def open_dependency_wizard(self) -> str:
        """Abre el asistente NATIVO de instalación de dependencias."""
        def _f():
            from dependency_wizard import DependencyWizard
            return DependencyWizard(None, only_missing=False)
        return self._open_native_dialog(_f)

    @pyqtSlot(result=str)
    def open_onboarding(self) -> str:
        """Abre el asistente de onboarding NATIVO (deps · credenciales · defaults)."""
        def _f():
            from onboarding_wizard import OnboardingWizard
            return OnboardingWizard(None)
        return self._open_native_dialog(_f)

    @pyqtSlot(result=str)
    def open_theme_editor(self) -> str:
        """Abre el editor de tema NATIVO (colores/shape/components en vivo)."""
        def _f():
            from theme_editor import ThemeEditorDialog
            return ThemeEditorDialog(None)
        return self._open_native_dialog(_f)

    @pyqtSlot(result=str)
    def open_figma_import(self) -> str:
        """Abre el importador de tema desde Figma NATIVO (DTCG / REST API)."""
        def _f():
            from figma_import_dialog import FigmaImportDialog
            return FigmaImportDialog(None)
        return self._open_native_dialog(_f)

    @pyqtSlot(str, result=str)
    def provider_login(self, provider_id: str) -> str:
        """Lanza el login OAuth del provider en una terminal externa real."""
        try:
            import ai_providers as aip
            import shutil
            import subprocess
            argv = aip.login_argv(provider_id)
            if not argv:
                return json.dumps({"ok": False, "error": "este provider no usa login (usa API key)"})
            inner = " ".join(argv)
            for term, mk in (("konsole", lambda: ["konsole", "-e", "bash", "-lc", inner + "; exec bash"]),
                             ("gnome-terminal", lambda: ["gnome-terminal", "--", "bash", "-lc", inner + "; exec bash"]),
                             ("kitty", lambda: ["kitty", "bash", "-lc", inner + "; exec bash"]),
                             ("xterm", lambda: ["xterm", "-e", "bash", "-lc", inner + "; exec bash"])):
                if shutil.which(term):
                    subprocess.Popen(mk())
                    return json.dumps({"ok": True, "terminal": term})
            return json.dumps({"ok": False, "error": "no se encontró terminal"})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(result=str)
    def list_stack_skills(self) -> str:
        """Skills predeclaradas por stack (read-only), igual que la sección nativa."""
        try:
            from stacks import STACKS
            out = []
            for k, s in STACKS.items():
                skills = s.get("skills") or []
                if skills:
                    out.append({"key": k, "label": s.get("name", k), "skills": list(skills)})
            return json.dumps({"ok": True, "stacks": out})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(str, result=str)
    def open_shortcut(self, kind: str) -> str:
        """Atajos: abrir carpeta de ThemeForge / context/ / editar stacks.py."""
        try:
            from pathlib import Path
            import subprocess
            import shutil
            base = Path(__file__).resolve().parent
            if kind == "themeforge":
                target, edit = base, False
            elif kind == "context":
                target, edit = base / "context", False
            elif kind == "stacks":
                target, edit = base / "stacks.py", True
            else:
                return json.dumps({"ok": False, "error": "atajo desconocido"})
            if edit:
                for ed in ("code", "codium", "kate", "gedit"):
                    if shutil.which(ed):
                        subprocess.Popen([ed, str(target)]); return json.dumps({"ok": True, "editor": ed})
            try:
                import platform_compat as pc
                pc.open_path(str(target))
            except Exception:
                subprocess.Popen(["xdg-open", str(target)])
            return json.dumps({"ok": True})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(str, bool, result=str)
    def open_project_window(self, path: str, fresh: bool) -> str:
        """Abre el proyecto en una VENTANA NUEVA del SO (como la ProjectWindow
        nativa) — no en la misma ventana. El WebShell crea un QWebEngineView
        aparte con el mismo tema apuntando a #proj=<path>."""
        self.open_window_requested.emit(path, bool(fresh))
        return json.dumps({"ok": True})

    # ════════════════ Hermes — paridad con el panel nativo ════════════════
    # Wrappers finos sobre `hermes <args>` (la lógica vive en hermes_panel.py).
    # Operaciones rápidas → slot síncrono que devuelve JSON. Operaciones lentas
    # (red/IA/streaming) → async: emiten `hermes_event` {op,...}. Los flujos
    # interactivos (OAuth, gateway setup, fallback add) → terminal embebida.
    def _h_exe(self):
        import shutil
        from pathlib import Path
        c = shutil.which("hermes")
        if c:
            return c
        p = Path.home() / ".local" / "bin" / "hermes"
        return str(p) if p.is_file() else None

    def _h_run(self, args, timeout=25):
        try:
            from hermes_panel import run_hermes
            return run_hermes(list(args), timeout=timeout)
        except Exception as e:  # noqa: BLE001
            return 1, str(e)

    def _h_async(self, op, args, timeout=120):
        """Corre `hermes <args>` en un hilo y emite hermes_event al terminar."""
        import threading

        def _w():
            rc, out = self._h_run(args, timeout=timeout)
            self.hermes_event.emit(json.dumps({"op": op, "done": True,
                                               "ok": rc == 0, "out": out}))
        threading.Thread(target=_w, daemon=True).start()

    def _h_spawn(self, op, args):
        """Corre `hermes <args>` async (QProcess) con streaming por hermes_event."""
        exe = self._h_exe()
        if not exe:
            self.hermes_event.emit(json.dumps({"op": op, "done": True, "ok": False,
                                               "out": "Hermes no instalado"}))
            return
        proc = QProcess(self)
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.readyReadStandardOutput.connect(
            lambda: self.hermes_event.emit(json.dumps({"op": op, "line":
                bytes(proc.readAllStandardOutput()).decode(errors="replace")})))
        proc.finished.connect(
            lambda code, _s: self.hermes_event.emit(json.dumps(
                {"op": op, "done": True, "ok": code == 0, "code": code})))
        proc.start(exe, list(args))
        self._procs.append(proc)

    # ── 🔌 Proveedor (cerebro de Hermes) ──────────────────────────────────
    @pyqtSlot(result=str)
    def hermes_providers(self) -> str:
        try:
            from hermes_panel import (HERMES_PROVIDERS, _hermes_model_info,
                                      _provider_has_auth, _cached_models)
            kwmap = {"google-gemini-cli": ["gemini"], "gemini": ["gemini"],
                     "xai-oauth": ["grok"], "qwen-oauth": ["qwen"]}
            cur_p, cur_m = _hermes_model_info()
            provs = []
            for p in HERMES_PROVIDERS:
                kws = kwmap.get(p["key"])
                live = _cached_models(kws) if kws else []
                provs.append({"key": p["key"], "auth": p["auth"], "label": p["label"],
                              "note": p.get("note", ""),
                              "models": (live or p.get("models", [])),
                              "has_auth": _provider_has_auth(p["key"])})
            return json.dumps({"ok": True, "providers": provs,
                               "current_provider": cur_p or "",
                               "current_model": cur_m or ""})
        except Exception as e:  # noqa: BLE001
            return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(str, str, result=str)
    def hermes_set_model(self, provider: str, model: str) -> str:
        if not provider or not model:
            return json.dumps({"ok": False, "error": "provider/model vacío"})
        base = "https://openrouter.ai/api/v1" if provider == "openrouter" else ""
        outs = []
        for kv in (["config", "set", "model.provider", provider],
                   ["config", "set", "model.default", model],
                   ["config", "set", "model.base_url", base]):
            _rc, o = self._h_run(kv, timeout=20)
            if o:
                outs.append(o)
        return json.dumps({"ok": True, "out": "\n".join(outs)})

    @pyqtSlot(str, str, result=str)
    def hermes_save_key(self, provider: str, key: str) -> str:
        if not provider or not key:
            return json.dumps({"ok": False, "error": "provider/key vacío"})
        rc, out = self._h_run(["auth", "add", provider, "--api-key", key], timeout=25)
        return json.dumps({"ok": rc == 0, "out": out})

    @pyqtSlot(str, result=str)
    def hermes_login(self, provider: str) -> str:
        """Login OAuth del cerebro en terminal embebida (flujo de navegador)."""
        from pathlib import Path
        exe = self._h_exe()
        if not exe:
            self.terminal_ready.emit(json.dumps({"kind": "hermes-login", "error": "Hermes no instalado"}))
            return json.dumps({"ok": False, "error": "Hermes no instalado"})
        return self._start_terminal(str(Path.home()), exe,
                                    ["auth", "add", provider, "--type", "oauth"], "hermes-login")

    @pyqtSlot(result=str)
    def hermes_test_brain(self) -> str:
        self._h_async("test_brain", ["-z", "ping: responde OK"], timeout=90)
        return json.dumps({"ok": True, "running": True})

    # ── 🎨 Imágenes (Runware) ─────────────────────────────────────────────
    @pyqtSlot(result=str)
    def runware_status(self) -> str:
        try:
            import runware_images as ri
            return json.dumps({"ok": True, "has_key": bool(ri.get_api_key()),
                               "default": ri.get_default_model() or "",
                               "categories": list(ri.CATEGORIES),
                               "architectures": list(ri.ARCHITECTURES)})
        except Exception as e:  # noqa: BLE001
            return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(str, result=str)
    def runware_save_key(self, key: str) -> str:
        try:
            import ai_providers as aip
            aip.save_key("runware", (key or "").strip())
            return json.dumps({"ok": True})
        except Exception as e:  # noqa: BLE001
            return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(str, str, result=str)
    def runware_search(self, query: str, architecture: str) -> str:
        import threading

        def _w():
            try:
                import runware_images as ri
                res = ri.search_models(query or "", architecture=architecture or "", limit=40)
                self.hermes_event.emit(json.dumps({"op": "runware_search", "done": True,
                                                   "ok": bool(res.get("ok")),
                                                   "models": res.get("models", []),
                                                   "error": res.get("error", "")}))
            except Exception as e:  # noqa: BLE001
                self.hermes_event.emit(json.dumps({"op": "runware_search", "done": True,
                                                   "ok": False, "error": str(e)}))
        threading.Thread(target=_w, daemon=True).start()
        return json.dumps({"ok": True, "running": True})

    @pyqtSlot(str, result=str)
    def runware_set_default(self, air: str) -> str:
        try:
            import runware_images as ri
            ri.set_default_model(air)
            return json.dumps({"ok": True})
        except Exception as e:  # noqa: BLE001
            return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(str, str, result=str)
    def runware_test(self, prompt: str, air: str) -> str:
        import threading

        def _w():
            try:
                import runware_images as ri
                res = ri.generate(prompt or "neon tokyo street, cyberpunk",
                                  width=768, height=512, model=(air or None))
                url = (res.get("urls") or [""])[0] if res.get("ok") else ""
                self.hermes_event.emit(json.dumps({"op": "runware_test", "done": True,
                                                   "ok": bool(res.get("ok")), "url": url,
                                                   "error": res.get("error", "")}))
            except Exception as e:  # noqa: BLE001
                self.hermes_event.emit(json.dumps({"op": "runware_test", "done": True,
                                                   "ok": False, "error": str(e)}))
        threading.Thread(target=_w, daemon=True).start()
        return json.dumps({"ok": True, "running": True})

    # ── 🤖 Agentes (skills) ───────────────────────────────────────────────
    def _scan_skills(self):
        from hermes_panel import SKILLS_DIR, _parse_frontmatter
        out = []
        if not SKILLS_DIR.is_dir():
            return out
        for md in sorted(SKILLS_DIR.glob("*/*/SKILL.md")) + sorted(SKILLS_DIR.glob("*/SKILL.md")):
            try:
                text = md.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            fm = _parse_frontmatter(text)
            rel = md.relative_to(SKILLS_DIR)
            category = rel.parts[0] if len(rel.parts) >= 2 else "(raíz)"
            out.append({"name": fm.get("name") or md.parent.name,
                        "description": fm.get("description", ""),
                        "category": fm.get("category") or category,
                        "path": str(md), "tf": category == "themeforge"})
        return out

    @pyqtSlot(bool, result=str)
    def hermes_skills(self, webonly: bool) -> str:
        try:
            skills = self._scan_skills()
            if webonly:
                skills = [s for s in skills if s["tf"]]
            skills = sorted(skills, key=lambda s: (not s["tf"], s["name"]))
            return json.dumps({"ok": True, "skills": skills})
        except Exception as e:  # noqa: BLE001
            return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(str, result=str)
    def hermes_skill_detail(self, path: str) -> str:
        try:
            from pathlib import Path
            return json.dumps({"ok": True, "text": Path(path).read_text(encoding="utf-8", errors="replace")})
        except Exception as e:  # noqa: BLE001
            return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(result=str)
    def hermes_skill_pack(self) -> str:
        try:
            from hermes_skill_pack import pack_by_domain
            groups = pack_by_domain()
            return json.dumps({"ok": True, "groups": [
                {"domain": dom, "items": [{"id": sid, "label": lbl} for sid, lbl in items]}
                for dom, items in groups.items()]})
        except Exception as e:  # noqa: BLE001
            return json.dumps({"ok": False, "error": str(e), "groups": []})

    @pyqtSlot(result=str)
    def hermes_seed_web_agents(self) -> str:
        try:
            from hermes_web_agents import seed_web_agents
            return json.dumps({"ok": True, "names": list(seed_web_agents(force=True))})
        except Exception as e:  # noqa: BLE001
            return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(str, result=str)
    def hermes_skills_search(self, query: str) -> str:
        self._h_async("skills_search", ["skills", "search", query or ""], timeout=40)
        return json.dumps({"ok": True, "running": True})

    @pyqtSlot(str, result=str)
    def hermes_install_skill(self, skill_id: str) -> str:
        if not (skill_id or "").strip():
            return json.dumps({"ok": False, "error": "id vacío"})
        self._h_spawn("install_skill", ["skills", "install", skill_id.strip(), "--force"])
        return json.dumps({"ok": True, "running": True})

    @pyqtSlot(str, result=str)
    def hermes_install_pack(self, ids_csv: str) -> str:
        ids = [x.strip() for x in (ids_csv or "").split(",") if x.strip()]
        if not ids:
            return json.dumps({"ok": False, "error": "sin ids"})
        import threading

        def _w():
            for i in ids:
                self.hermes_event.emit(json.dumps({"op": "install_pack", "line": f"\n▶ {i}…\n"}))
                _rc, out = self._h_run(["skills", "install", i, "--force"], timeout=120)
                self.hermes_event.emit(json.dumps({"op": "install_pack", "line": (out or "") + "\n"}))
            self.hermes_event.emit(json.dumps({"op": "install_pack", "done": True, "ok": True}))
        threading.Thread(target=_w, daemon=True).start()
        return json.dumps({"ok": True, "running": True})

    # ── ➕ Crear agente (SKILL.md) ────────────────────────────────────────
    @pyqtSlot(str, str, str, result=str)
    def hermes_skill_template(self, name: str, stacks: str, desc: str) -> str:
        nm = ((name or "agente").strip().lower().replace(" ", "-")) or "agente"
        title = (name or "Agente").strip()
        d = (desc or "").strip() or "Describe qué hace y cuándo usarlo."
        tags = ", ".join([s.strip() for s in (stacks or "").split(",") if s.strip()][:6]) or "themeforge"
        tmpl = (f"---\nname: {nm}\ndescription: {d}\nversion: 1.0.0\n"
                f"metadata:\n  hermes:\n    category: themeforge\n    tags: [{tags}]\n---\n\n"
                f"# {title}\n\n## Cuándo usar\n{d}\n\n## Stacks base\n{stacks or '-'}\n\n"
                f"## Procedimiento\n1. Lee el contexto del proyecto (CLAUDE.md/AGENTS.md).\n2. …\n")
        return json.dumps({"ok": True, "template": tmpl})

    @pyqtSlot(str, str, str, result=str)
    def hermes_skill_draft_ai(self, name: str, stacks: str, desc: str) -> str:
        if not (name or "").strip() or not (desc or "").strip():
            return json.dumps({"ok": False, "error": "nombre y especialidad requeridos"})
        prompt = ("Write a Hermes SKILL.md for a ThemeForge specialized agent. Output ONLY "
                  "the file content (YAML frontmatter + markdown body, in Spanish). "
                  f"name: {name}. base stacks: {stacks}. specialty: {desc}.")
        self._h_async("draft_skill", ["-z", prompt], timeout=120)
        return json.dumps({"ok": True, "running": True})

    @pyqtSlot(str, str, result=str)
    def hermes_skill_save(self, name: str, body: str) -> str:
        try:
            from hermes_panel import TF_SKILLS_DIR
            nm = (name or "").strip().lower().replace(" ", "-")
            if not nm:
                return json.dumps({"ok": False, "error": "nombre vacío"})
            if not (body or "").strip():
                return json.dumps({"ok": False, "error": "cuerpo vacío"})
            d = TF_SKILLS_DIR / nm
            d.mkdir(parents=True, exist_ok=True)
            (d / "SKILL.md").write_text(body, encoding="utf-8")
            return json.dumps({"ok": True, "path": str(d / "SKILL.md")})
        except Exception as e:  # noqa: BLE001
            return json.dumps({"ok": False, "error": str(e)})

    # ── 🧠 Memoria ────────────────────────────────────────────────────────
    @pyqtSlot(result=str)
    def hermes_memory(self) -> str:
        try:
            from hermes_panel import MEMORIES_DIR, MEMORY_LIMITS, run_hermes
            from operator_panel import PROJECTS_DIR
            from pathlib import Path

            def _rd(p):
                try:
                    return Path(p).read_text(encoding="utf-8")
                except Exception:
                    return ""
            projs = []
            pd = Path(PROJECTS_DIR)
            if pd.is_dir():
                for d in sorted(pd.iterdir()):
                    note = d / ".hermes.md"
                    if note.is_file():
                        projs.append({"name": d.name, "path": str(note)})
            _rc, sess = run_hermes(["sessions", "stats"], timeout=15)
            return json.dumps({"ok": True,
                               "memory": _rd(MEMORIES_DIR / "MEMORY.md"),
                               "user": _rd(MEMORIES_DIR / "USER.md"),
                               "limits": MEMORY_LIMITS, "projects": projs,
                               "sessions": sess})
        except Exception as e:  # noqa: BLE001
            return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(str, str, result=str)
    def hermes_memory_save(self, fname: str, text: str) -> str:
        try:
            from hermes_panel import MEMORIES_DIR, MEMORY_LIMITS
            if fname not in MEMORY_LIMITS:
                return json.dumps({"ok": False, "error": "archivo no permitido"})
            MEMORIES_DIR.mkdir(parents=True, exist_ok=True)
            (MEMORIES_DIR / fname).write_text(text or "", encoding="utf-8")
            return json.dumps({"ok": True})
        except Exception as e:  # noqa: BLE001
            return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(str, result=str)
    def hermes_project_note(self, path: str) -> str:
        try:
            from pathlib import Path
            return json.dumps({"ok": True, "text": Path(path).read_text(encoding="utf-8", errors="replace")})
        except Exception as e:  # noqa: BLE001
            return json.dumps({"ok": False, "error": str(e)})

    # ── 📊 Kanban ─────────────────────────────────────────────────────────
    def _kanban_json(self, args):
        _rc, out = self._h_run(args, timeout=20)
        try:
            return json.loads(out)
        except Exception:
            return None

    @pyqtSlot(result=str)
    def kanban_boards(self) -> str:
        data = self._kanban_json(["kanban", "boards", "list", "--json"])
        boards = []
        src = data.get("boards") if isinstance(data, dict) else data
        if isinstance(src, list):
            boards = [b.get("name") if isinstance(b, dict) else str(b) for b in src]
        return json.dumps({"ok": True, "boards": [b for b in boards if b]})

    @pyqtSlot(str, result=str)
    def kanban_tasks(self, board: str) -> str:
        if not board:
            return json.dumps({"ok": True, "tasks": []})
        data = self._kanban_json(["kanban", "--board", board, "list", "--json"])
        raw = data if isinstance(data, list) else (data.get("tasks") if isinstance(data, dict) else [])
        norm = []
        for t in (raw or []):
            if not isinstance(t, dict):
                continue
            norm.append({"id": str(t.get("id", "")),
                         "title": t.get("title") or t.get("task") or "",
                         "status": t.get("status", ""),
                         "assignee": t.get("assignee") or t.get("assigned") or "",
                         "priority": t.get("priority", "")})
        return json.dumps({"ok": True, "tasks": norm})

    @pyqtSlot(str, str, str, str, str, result=str)
    def kanban_create(self, board: str, title: str, body: str, priority: str, skill: str) -> str:
        if not board or not title:
            return json.dumps({"ok": False, "error": "board/título vacío"})
        args = ["kanban", "--board", board, "create", title]
        if body:
            args += ["--body", body]
        if priority:
            args += ["--priority", priority]
        if skill:
            args += ["--skill", skill]
        rc, out = self._h_run(args, timeout=25)
        return json.dumps({"ok": rc == 0, "out": out})

    @pyqtSlot(str, result=str)
    def kanban_dispatch(self, board: str) -> str:
        if not board:
            return json.dumps({"ok": False, "error": "board vacío"})
        self._h_spawn("kanban_dispatch", ["kanban", "--board", board, "dispatch"])
        return json.dumps({"ok": True, "running": True})

    # ── ⏰ Cron ───────────────────────────────────────────────────────────
    @pyqtSlot(result=str)
    def cron_jobs(self) -> str:
        try:
            from hermes_panel import CRON_JOBS
            jobs = []
            if CRON_JOBS.is_file():
                d = json.loads(CRON_JOBS.read_text(encoding="utf-8"))
                raw = d.get("jobs") if isinstance(d, dict) else d
                for jb in (raw or []):
                    if not isinstance(jb, dict):
                        continue
                    paused = (bool(jb.get("paused")) or jb.get("status") == "paused"
                              or not jb.get("enabled", True))
                    jobs.append({"id": str(jb.get("id") or jb.get("name") or ""),
                                 "name": jb.get("name", ""),
                                 "schedule": jb.get("schedule") or jb.get("cron") or "",
                                 "prompt": (jb.get("prompt") or jb.get("task") or "")[:120],
                                 "paused": paused,
                                 "next": jb.get("next_run") or jb.get("next") or ""})
            return json.dumps({"ok": True, "jobs": jobs})
        except Exception as e:  # noqa: BLE001
            return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(str, str, str, str, str, result=str)
    def cron_create(self, schedule: str, prompt: str, skill: str, deliver: str, name: str) -> str:
        if not schedule or not prompt:
            return json.dumps({"ok": False, "error": "cuándo/tarea vacío"})
        args = ["cron", "create", schedule, prompt]
        if skill:
            args += ["--skill", skill]
        if deliver and deliver != "local":
            args += ["--deliver", deliver]
        if name:
            args += ["--name", name]
        rc, out = self._h_run(args, timeout=25)
        return json.dumps({"ok": rc == 0, "out": out})

    @pyqtSlot(str, str, result=str)
    def cron_op(self, action: str, jid: str) -> str:
        if action not in ("pause", "resume", "run", "remove") or not jid:
            return json.dumps({"ok": False, "error": "acción/id inválido"})
        rc, out = self._h_run(["cron", action, jid], timeout=25)
        return json.dumps({"ok": rc == 0, "out": out})

    # ── 📲 Remoto (gateway / mensajería) ──────────────────────────────────
    @pyqtSlot(result=str)
    def gateway_platforms(self) -> str:
        try:
            from hermes_panel import GATEWAY_PLATFORMS
            return json.dumps({"ok": True, "platforms": [
                {"key": k, "env": e, "hint": h} for (k, e, h) in GATEWAY_PLATFORMS]})
        except Exception as e:  # noqa: BLE001
            return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(str, result=str)
    def gateway_op(self, op: str) -> str:
        if op not in ("status", "install", "start", "stop"):
            return json.dumps({"ok": False, "error": "op inválida"})
        rc, out = self._h_run(["gateway", op], timeout=30)
        return json.dumps({"ok": rc == 0, "out": out})

    @pyqtSlot(result=str)
    def gateway_setup(self) -> str:
        from pathlib import Path
        exe = self._h_exe()
        if not exe:
            self.terminal_ready.emit(json.dumps({"kind": "hermes-gateway", "error": "Hermes no instalado"}))
            return json.dumps({"ok": False, "error": "Hermes no instalado"})
        return self._start_terminal(str(Path.home()), exe, ["gateway", "setup"], "hermes-gateway")

    @pyqtSlot(result=str)
    def gateway_targets(self) -> str:
        rc, out = self._h_run(["send", "--list"], timeout=20)
        return json.dumps({"ok": rc == 0, "out": out})

    @pyqtSlot(str, str, result=str)
    def gateway_send(self, target: str, msg: str) -> str:
        if not target or not msg:
            return json.dumps({"ok": False, "error": "destino/mensaje vacío"})
        self._h_async("gateway_send", ["send", "--to", target, msg], timeout=40)
        return json.dumps({"ok": True, "running": True})

    @pyqtSlot(result=str)
    def pairing_list(self) -> str:
        rc, out = self._h_run(["pairing", "list"], timeout=20)
        return json.dumps({"ok": rc == 0, "out": out})

    @pyqtSlot(str, str, result=str)
    def pairing_approve(self, plat: str, code: str) -> str:
        if not plat or not code:
            return json.dumps({"ok": False, "error": "plataforma/código vacío"})
        rc, out = self._h_run(["pairing", "approve", plat, code], timeout=20)
        return json.dumps({"ok": rc == 0, "out": out})

    # ── 🛡️ Avanzado ──────────────────────────────────────────────────────
    @pyqtSlot(result=str)
    def hermes_security(self) -> str:
        try:
            from hermes_panel import HERMES_HOME
            backend, mode = "local", "smart"
            cfg = HERMES_HOME / "config.yaml"
            if cfg.is_file():
                for ln in cfg.read_text(encoding="utf-8", errors="replace").splitlines():
                    s = ln.strip()
                    if s.startswith("backend:"):
                        backend = s.split(":", 1)[1].strip() or backend
                    elif s.startswith("mode:"):
                        mode = s.split(":", 1)[1].strip() or mode
            return json.dumps({"ok": True, "backend": backend, "mode": mode})
        except Exception as e:  # noqa: BLE001
            return json.dumps({"ok": False, "error": str(e)})

    @pyqtSlot(str, str, result=str)
    def hermes_security_apply(self, backend: str, mode: str) -> str:
        outs = []
        for kv in (["config", "set", "terminal.backend", backend],
                   ["config", "set", "approvals.mode", mode]):
            _rc, o = self._h_run(kv, timeout=20)
            if o:
                outs.append(o)
        return json.dumps({"ok": True, "out": "\n".join(outs)})

    @pyqtSlot(str, result=str)
    def hermes_portal(self, op: str) -> str:
        if op not in ("status", "tools"):
            return json.dumps({"ok": False, "error": "op inválida"})
        rc, out = self._h_run(["portal", op], timeout=30)
        return json.dumps({"ok": rc == 0, "out": out})

    @pyqtSlot(result=str)
    def hermes_profile_create(self) -> str:
        rc, out = self._h_run(["profile", "create", "themeforge", "--clone"], timeout=30)
        return json.dumps({"ok": rc == 0, "out": out})

    @pyqtSlot(result=str)
    def hermes_profile_list(self) -> str:
        rc, out = self._h_run(["profile", "list"], timeout=20)
        return json.dumps({"ok": rc == 0, "out": out})

    @pyqtSlot(result=str)
    def hermes_bundle_create(self) -> str:
        try:
            from hermes_web_agents import web_agent_names
            skills = ["themeforge-operator"] + list(web_agent_names())
        except Exception:
            skills = ["themeforge-operator"]
        args = ["bundles", "create", "themeforge"]
        for s in skills:
            args += ["--skill", s]
        rc, out = self._h_run(args, timeout=30)
        return json.dumps({"ok": rc == 0, "out": out})

    @pyqtSlot(int, result=str)
    def hermes_insights(self, days: int) -> str:
        self._h_async("insights", ["insights", "--days", str(int(days or 30))], timeout=60)
        return json.dumps({"ok": True, "running": True})

    @pyqtSlot(result=str)
    def hermes_fallback_list(self) -> str:
        rc, out = self._h_run(["fallback", "list"], timeout=20)
        return json.dumps({"ok": rc == 0, "out": out})

    @pyqtSlot(result=str)
    def hermes_fallback_add(self) -> str:
        from pathlib import Path
        exe = self._h_exe()
        if not exe:
            self.terminal_ready.emit(json.dumps({"kind": "hermes-fallback", "error": "Hermes no instalado"}))
            return json.dumps({"ok": False, "error": "Hermes no instalado"})
        return self._start_terminal(str(Path.home()), exe, ["fallback", "add"], "hermes-fallback")

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

        self._child_windows = []  # ventanas de proyecto aparte (evitar GC)
        self._view = QWebEngineView()
        self._bridge = ThemeForgeBridge()
        # Reload del shell cuando se cambia de prototipo web (Matrix/Kawaii/…).
        self._bridge.reload_requested.connect(self._reload_active)
        # Abrir proyecto en VENTANA NUEVA (como el nativo).
        self._bridge.open_window_requested.connect(self._spawn_project_window)
        self._channel = QWebChannel(self._view.page())
        self._channel.registerObject("bridge", self._bridge)
        self._view.page().setWebChannel(self._channel)
        self._inject_scripts(self._view.page())
        root.addWidget(self._view)
        self._reload_active()

    def _spawn_project_window(self, path: str, fresh: bool):
        """Crea una ventana NUEVA (QWidget top-level) con su propio WebEngineView
        + puente, cargando el mismo tema en modo «solo proyecto» (#proj=<path>)."""
        try:
            import urllib.parse
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            from PyQt6.QtWebChannel import QWebChannel
            from PyQt6.QtCore import QUrl
            win = QWidget()
            from pathlib import Path as _P
            win.setWindowTitle(f"ThemeForge — {_P(path).name}")
            win.resize(1280, 860)
            lay = QVBoxLayout(win)
            lay.setContentsMargins(0, 0, 0, 0)
            view = QWebEngineView()
            bridge = ThemeForgeBridge()
            bridge.reload_requested.connect(self._reload_active)
            bridge.open_window_requested.connect(self._spawn_project_window)
            ch = QWebChannel(view.page())
            ch.registerObject("bridge", bridge)
            view.page().setWebChannel(ch)
            self._inject_scripts(view.page())
            lay.addWidget(view)
            slug = self._active_slug()
            frag = f"#proj={urllib.parse.quote(path)}&fresh={'1' if fresh else '0'}"
            view.setUrl(QUrl(f"http://127.0.0.1:{self._port}/{slug}/index.html{frag}"))
            # Mantener refs vivas (view+channel+bridge+win) mientras la ventana exista.
            self._child_windows.append((win, view, ch, bridge))
            win.show()
            win.raise_()
            win.activateWindow()
        except Exception as e:
            print(f"[webshell] no se pudo abrir ventana de proyecto: {e}")

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

    def _inject_scripts(self, page=None):
        """Inyecta en DocumentCreation: (1) window.__TF_DATA__ con datos reales,
        (2) el puente (qwebchannel + window.tfBridge + tfApplyTheme). Así CUALQUIER
        prototipo (Neo-Tokyo/Matrix/Kawaii) recibe datos + puente sin editar su HTML."""
        try:
            from PyQt6.QtWebEngineCore import QWebEngineScript
            if page is None:
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
