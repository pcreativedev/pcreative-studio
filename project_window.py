"""
ProjectWindow — ventana per-proyecto con preview web embebida + terminal
embebida real (xterm.js + node-pty vía servidor Node local).

Layout:

  ┌────────────────────────────┬────────────────────────────┐
  │                            │  Terminales (QTabWidget)    │
  │   Preview (WebEngineView)  │  ├─ Shell                  │
  │                            │  ├─ Claude Code            │
  │                            │  └─ Codex                  │
  ├────────────────────────────┴────────────────────────────┤
  │ Logs del dev server (QPlainTextEdit)                    │
  └─────────────────────────────────────────────────────────┘
"""
from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import time
from pathlib import Path

from datetime import datetime

from PyQt6.QtCore import (
    Qt, QObject, QProcess, QProcessEnvironment, QTimer, QUrl, QUrlQuery, pyqtSlot,
)
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTabBar,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

# Viewports presets (label, width)
VIEWPORTS = [
    ("📱 360", 360),
    ("📱 iPhone 14", 390),
    ("📋 Tablet", 768),
    ("💻 1280", 1280),
    ("🖥️ 1920", 1920),
    ("⛶ Full", 0),  # 0 = sin restricción
]

from preview import apply_port, detect_preview_profile, detect_subprojects, get_port_for_project
import platform_compat as pc


def _licensing_github_org() -> str:
    """Lee el campo `github_org` de `~/.config/pcreative-studio/licensing.json`.
    Devuelve '' si no hay config o el campo está vacío."""
    try:
        from licensing_config import load as _load_cfg
        return _load_cfg().get("github_org", "").strip()
    except Exception:
        return ""

BUILDER_DIR = Path(__file__).resolve().parent
# El servidor de terminal (xterm.js + node-pty) vive en `terminal/`. node-pty
# es un módulo NATIVO (binario por OS), así que `terminal/node_modules` debe
# estar compilado para el OS actual. Override con PCREATIVE STUDIO_TERMINAL_DIR para
# apuntar a una copia con los binarios correctos (p.ej. al correr desde un
# shared folder cuyo node_modules es de otro OS).
TERMINAL_DIR = Path(os.environ.get("PCREATIVE STUDIO_TERMINAL_DIR") or (BUILDER_DIR / "terminal"))


class _TermClipboard(QObject):
    """Puente JS↔Qt para copiar/pegar en la terminal embebida usando el
    portapapeles real del sistema (evita las restricciones del clipboard de
    QWebEngine/Chromium, que son inconsistentes en Wayland)."""

    @pyqtSlot(str)
    def copy(self, text: str):
        try:
            from PyQt6.QtGui import QGuiApplication
            QGuiApplication.clipboard().setText(text or "")
        except Exception:
            pass

    @pyqtSlot(result=str)
    def paste(self) -> str:
        try:
            from PyQt6.QtGui import QGuiApplication
            return QGuiApplication.clipboard().text() or ""
        except Exception:
            return ""


class ProjectWindow(QWidget):
    def __init__(self, project_path: Path, initial_cmd: str | None = None,
                 provider_key: str | None = None, auto_agent: bool = False):
        """
        initial_cmd: si se pasa, el primer tab "Setup" arranca con
        `bash -c '<initial_cmd>; exec bash -i'` para ejecutar el setup
        embebido dentro de la propia ventana del proyecto y dejar luego
        una shell viva.

        provider_key: key del provider seleccionado al crear el proyecto
        (claude/codex/gemini/opencode/openrouter/claude-api/codex-api).
        Solo se abre la tab del CLI de ese provider; si es None se
        abren todas las disponibles en PATH.
        """
        super().__init__()
        self.project_path = Path(project_path)
        # Asegurar que el directorio existe (modo "existing" lo borra y
        # gh clone lo recrea durante el setup; aquí lo dejamos creado para
        # que la ventana abra sin fallar al detectar el perfil).
        self.project_path.mkdir(parents=True, exist_ok=True)
        self._initial_cmd = initial_cmd
        self._provider_key = provider_key
        # Al abrir desde la galería: auto-ejecutar el agente con el contexto
        # del proyecto (lee CLAUDE.md/AGENTS.md y propone siguientes pasos).
        self._auto_agent = auto_agent
        self._auto_agent_tab_index: int | None = None

        # Enlazar las skills que instala autoskills (.agents/skills/) dentro de
        # .claude/skills/ para que el agente las DESCUBRA (autoskills no siempre
        # crea ese symlink → el agente solo veía la de UI/UX Pro). Idempotente,
        # aplica a cualquier modo de apertura.
        try:
            import skills_wireup
            _linked = skills_wireup.ensure_skills_discoverable(self.project_path)
            if _linked:
                print(f"[project_window] skills de autoskills enlazadas: {', '.join(_linked)}")
        except Exception as _e:
            print(f"[project_window] skills_wireup falló: {_e}")

        # ── Multi-stack / mono-repo support ──────────────────────────
        # Si la raíz contiene varios sub-proyectos (Laravel + Next +
        # Flutter, etc.), trabajamos con uno cada vez vía dropdown.
        self.subprojects = detect_subprojects(self.project_path)
        self._active_sub_idx: int | None = None
        if self.subprojects:
            # Elegir como activo el sub-app de cara al cliente (web/landing)
            # por encima de los de back-office (admin/api), para que el preview
            # de un mono-repo abra la web pública por defecto, no el panel.
            _FRONT = ("web", "site", "storefront", "frontend", "www", "app",
                      "client", "landing", "marketing", "shop", "store", "public")
            _BACK = ("admin", "api", "backend", "server", "dashboard",
                     "cms", "docs", "studio", "worker")

            def _rank(sub: dict) -> tuple:
                name = (sub.get("name") or "").lower()
                has_profile = 1 if sub.get("profile") else 0
                is_front = 1 if any(k in name for k in _FRONT) else 0
                not_back = 0 if any(k in name for k in _BACK) else 1
                return (has_profile, is_front, not_back)

            cands = [i for i, s in enumerate(self.subprojects) if s.get("profile")]
            if cands:
                self._active_sub_idx = max(cands, key=lambda i: _rank(self.subprojects[i]))
            else:
                self._active_sub_idx = 0

        self.profile, self._preview_root = self._compute_active_profile()
        # Asignar puerto único al proyecto (persistido en ~/.config/pcreative-studio/ports.json)
        if self.profile and self.profile.get("port_inject") is not None:
            self.preview_port = get_port_for_project(
                self._port_slug(),
                self.profile.get("default_port", 3000),
            )
        else:
            self.preview_port = self.profile["default_port"] if self.profile else 0
        self.preview_proc: QProcess | None = None
        # Lista de tuplas (name, QProcess) para los procesos secundarios
        self.secondary_procs: list[tuple[str, QProcess]] = []
        self.term_server: QProcess | None = None
        self.term_port: int | None = None
        self.term_token: str = ""
        # Lista de tabs (view, cmd, args) pendientes de cargar URL
        # hasta que el server esté listo
        self._pending_term_tabs: list[tuple[QWebEngineView, str, list[str]]] = []
        # Puentes de portapapeles de cada terminal (evita que el GC los recoja)
        self._term_clip_refs: list = []

        self._build_ui()
        self._update_status()
        self._start_terminal_server()
        self.setWindowTitle(f"Pcreative Studio — {self.project_path.name}")
        self.resize(1500, 900)

        # WordPress (Docker) ya provisionado → cargar el preview de entrada.
        self._load_no_server_preview()

        # UI pro al ABRIR un tema (Galería): guía UI-MOTION.md + MCP 21st.dev +
        # framer-motion. En proyectos nuevos ya lo hace el setup script.
        self._ensure_web_enhancements()

        # Auto-re-detect: si el perfil aún no se detectó (modo "existing"
        # o setup en curso), reintentamos cada 3 segundos durante 5 min.
        self._auto_detect_attempts = 0
        self._auto_detect_max = 100  # 100 × 3 s = 5 min
        if self.profile is None:
            self._auto_detect_timer = QTimer(self)
            self._auto_detect_timer.setInterval(3000)
            self._auto_detect_timer.timeout.connect(self._auto_detect_tick)
            self._auto_detect_timer.start()
        else:
            self._auto_detect_timer = None

    def _ensure_web_enhancements(self):
        """Al abrir un tema React desde la Galería: escribe UI-MOTION.md, asegura
        el MCP `magic` (21st.dev) en .mcp.json y, si falta framer-motion, lo
        instala en un tab. Solo proyectos frontend Node; en proyectos NUEVOS lo
        hace ya el setup script (initial_cmd presente)."""
        if self._initial_cmd:
            return
        try:
            import web_enhancements as we
        except Exception:
            return
        try:
            if not we.is_node_frontend(self.project_path):
                return
            res = we.ensure_for_project(self.project_path, install_motion=True)
            if res.get("needs_motion") and res.get("install_cmd"):
                self._add_term_tab(
                    "✨ Motion", "bash",
                    ["-c", "echo '→ Instalando framer-motion (animaciones)…'; "
                           f"{res['install_cmd']}; "
                           "echo '✓ Listo. El agente debe leer UI-MOTION.md.'; "
                           "exec bash -i"])
        except Exception as e:
            try:
                self.logs.appendPlainText(f"[ui-enhance] {e}")
            except Exception:
                pass

    # ── Multi-stack helpers ─────────────────────────────────────────
    def _compute_active_profile(self) -> tuple[dict | None, Path]:
        """Devuelve (profile, root_path_para_el_preview).

        Si hay sub-proyectos, usa el activo. Si no, usa la raíz.
        El root_path es el cwd que QProcess usa para arrancar el preview.
        """
        if self.subprojects and self._active_sub_idx is not None:
            sub = self.subprojects[self._active_sub_idx]
            return sub.get("profile"), Path(sub["path"])
        return detect_preview_profile(self.project_path), self.project_path

    def _port_slug(self) -> str:
        """Slug usado para la asignación persistente de puerto. En
        mono-repos, incluye el sub-proyecto para que cada uno tenga
        puerto distinto."""
        if self.subprojects and self._active_sub_idx is not None:
            sub_name = self.subprojects[self._active_sub_idx]["name"]
            return f"{self.project_path.name}:{sub_name}"
        return self.project_path.name

    def _switch_subproject(self, idx: int):
        """Cambia el sub-proyecto activo y refresca el UI."""
        if not self.subprojects:
            return
        if idx == self._active_sub_idx:
            return
        # Parar preview actual antes de cambiar
        if self.preview_proc and self.preview_proc.state() != QProcess.ProcessState.NotRunning:
            self.stop_preview()
        self._active_sub_idx = idx
        self.profile, self._preview_root = self._compute_active_profile()
        if self.profile and self.profile.get("port_inject") is not None:
            self.preview_port = get_port_for_project(
                self._port_slug(),
                self.profile.get("default_port", 3000),
            )
        else:
            self.preview_port = self.profile["default_port"] if self.profile else 0
        if self.profile:
            self.url_edit.setText(self.profile["url"].replace("{port}", str(self.preview_port)))
        else:
            self.url_edit.setText("")
        self.btn_start.setEnabled(self.profile is not None)
        self.webview.setUrl(QUrl("about:blank"))
        self._update_status()
        sub = self.subprojects[idx]
        if sub.get("from_reference"):
            self.logs.appendPlainText(
                f"\n=== 📚 Referencia activa: {sub['name']} ({sub.get('rel_path')}) ===\n"
                f"    Esto está en reference/ para que lo estudies. NO copies código "
                f"a la raíz: el modo recreate exige reimplementación limpia."
            )
        else:
            self.logs.appendPlainText(
                f"\n=== 🏗️ Sub-proyecto activo: {sub['name']} ({sub.get('rel_path')}) ===")

    # ── UI ───────────────────────────────────────────────────────────
    def _git_status_str(self) -> str:
        """Devuelve '·branch · X cambios pendientes' o '' si no es repo."""
        if not (self.project_path / ".git").is_dir():
            return ""
        try:
            br = subprocess.check_output(
                ["git", "branch", "--show-current"],
                cwd=str(self.project_path), stderr=subprocess.DEVNULL, timeout=5,
            ).decode().strip()
            dirty = subprocess.check_output(
                ["git", "status", "--porcelain"],
                cwd=str(self.project_path), stderr=subprocess.DEVNULL, timeout=5,
            ).decode().strip()
            changes = len([l for l in dirty.splitlines() if l.strip()])
            mark = f"{changes} cambios" if changes else "limpio"
            return f"  ·  <span style='color:#62b4ff'>git: {br}</span> · {mark}"
        except Exception:
            return ""

    def _build_ui(self):
        title = QLabel(
            f"<b>{self.project_path.name}</b>"
            f"  <span style='color:#888'>{self.project_path}</span>"
            f"{self._git_status_str()}"
        )
        title.setTextFormat(Qt.TextFormat.RichText)

        # Toolbar superior
        self.btn_open_folder = QPushButton("📁 Folder")
        self.btn_open_folder.clicked.connect(self._open_folder)
        self.btn_open_vscode = QPushButton("VSCode")
        self.btn_open_vscode.clicked.connect(self._open_vscode)
        self.btn_refresh_profile = QPushButton("🔄 Re-detectar")
        self.btn_refresh_profile.setToolTip(
            "Re-detect the preview profile (after running setup, installing "
            "dependencies, etc.)"
        )
        self.btn_refresh_profile.clicked.connect(self._refresh_profile)
        self.btn_preflight = QPushButton("🔬 Pre-flight")
        self.btn_preflight.setToolTip(
            "Runs a battery of checks against marketplace-readiness rules + "
            "best practices: README, LICENSE, documentation/, screenshots/, "
            "legacy jQuery, legacy Bootstrap, hardcoded GA/FB tracking, "
            "prefers-reduced-motion, .env committed by accident, total size, "
            "unresolved placeholders, lighthouse / html-validator availability. "
            "Fast (filesystem + grep)."
        )
        self.btn_preflight.clicked.connect(self._run_preflight)

        self.btn_zip = QPushButton("📦 ZIP")
        self.btn_zip.setToolTip(
            "Package this project into a marketplace-ready ZIP.\n"
            "Auto-excludes: node_modules, .git, dist, .next, build, .env, "
            ".cache, .vscode, .idea, .cursor, .claude, CLAUDE.md / "
            "AGENTS.md / MEMORY.md, *.log, .DS_Store, vendor, target, etc.\n"
            "Output: ~/Proyectos/themes-builds/<slug>-<timestamp>.zip"
        )
        self.btn_zip.clicked.connect(self._build_zip)

        self.btn_deploy_demo = QPushButton("🚀 Demo")
        self.btn_deploy_demo.setToolTip(
            "Deploy a public demo of the project to Netlify / Vercel / "
            "Cloudflare Pages / Surge.sh so you can share the URL with "
            "buyers or clients. Auto-detects build command and dist "
            "directory; you can override both in the dialog."
        )
        self.btn_deploy_demo.clicked.connect(self._deploy_demo)

        self.btn_github = QPushButton("📦 GitHub")
        self.btn_github.setToolTip(
            "Create a private GitHub repo and push the code. Detects "
            "whether an 'origin' remote already exists and only pushes "
            "in that case."
        )
        self.btn_github.clicked.connect(self._github_create_or_push)
        self.btn_open_external_term = QPushButton("External terminal")
        self.btn_open_external_term.clicked.connect(self._open_external_terminal)
        # Operator (Hermes) — OPCIONAL: solo visible si Hermes está instalado.
        self.btn_operator = QPushButton("🚀 Operator")
        self.btn_operator.setToolTip("Automatizar/continuar este proyecto con el "
                                     "Operator (Hermes) — opcional")
        self.btn_operator.clicked.connect(self._automate_with_operator)
        try:
            from operator_panel import operator_available
            self.btn_operator.setVisible(operator_available())
        except Exception:
            self.btn_operator.setVisible(False)
        # Abrir/crear MÁS proyectos sin cerrar este (Pcreative Studio soporta varias
        # ProjectWindow a la vez).
        self.btn_new_project = QPushButton("➕ Nuevo")
        self.btn_new_project.setToolTip("Crear otro proyecto (abre 'New project' "
                                        "en la ventana principal) — sin cerrar este")
        self.btn_new_project.clicked.connect(self._new_project)
        self.btn_open_other = QPushButton("📂 Abrir otro")
        self.btn_open_other.setToolTip("Abrir otro proyecto en una ventana nueva")
        self.btn_open_other.clicked.connect(self._open_other_project)

        toolbar = QHBoxLayout()
        toolbar.addWidget(self.btn_new_project)
        toolbar.addWidget(self.btn_open_other)
        toolbar.addWidget(self.btn_open_folder)
        toolbar.addWidget(self.btn_open_vscode)
        toolbar.addWidget(self.btn_refresh_profile)
        toolbar.addWidget(self.btn_preflight)
        toolbar.addWidget(self.btn_zip)
        toolbar.addWidget(self.btn_deploy_demo)
        toolbar.addWidget(self.btn_github)
        toolbar.addWidget(self.btn_operator)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_open_external_term)

        # Fila selector de sub-proyecto (solo si es mono-repo)
        self.sub_combo: QComboBox | None = None
        if self.subprojects:
            self.sub_combo = QComboBox()
            for i, sub in enumerate(self.subprojects):
                p = sub.get("profile")
                tag = p["name"] if p else "sin preview"
                icon = "📚" if sub.get("from_reference") else "🏗️"
                suffix = "  (referencia · solo estudio)" if sub.get("from_reference") else ""
                self.sub_combo.addItem(
                    f"{icon}  {sub['name']}  —  {tag}{suffix}", userData=i
                )
            if self._active_sub_idx is not None:
                self.sub_combo.setCurrentIndex(self._active_sub_idx)
            self.sub_combo.currentIndexChanged.connect(
                lambda i: self._switch_subproject(self.sub_combo.itemData(i))
            )

        # Fila de controles del preview
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("http://localhost:3000")
        if self.profile:
            self.url_edit.setText(self.profile["url"].replace("{port}", str(self.preview_port)))
        self.url_edit.returnPressed.connect(self._url_bar_navigate)
        self.btn_start = QPushButton("▶ Start preview")
        self.btn_start.clicked.connect(self.start_preview)
        self.btn_stop = QPushButton("■ Stop")
        self.btn_stop.clicked.connect(self.stop_preview)
        self.btn_stop.setEnabled(False)
        self.btn_reload = QPushButton("↻")
        self.btn_reload.setToolTip("Reload the active tab")
        self.btn_reload.clicked.connect(self._reload_current_tab)
        self.btn_open_browser = QPushButton("🚀 Open in browser")
        self.btn_open_browser.setToolTip(
            "Abre la preview en Chromium/Firefox externo en modo app "
            "(ventana sin barra de URL). Performance nativa — sin lag de "
            "QtWebEngine en Wayland. Recomendado para sesiones largas de "
            "dev o cuando la preview embebida vaya lenta."
        )
        self.btn_open_browser.setStyleSheet("font-weight:bold;")
        self.btn_open_browser.clicked.connect(self._open_external)
        self.btn_21st = QPushButton("🎨 21st.dev")
        self.btn_21st.setToolTip(
            "Abre la galería de componentes/animaciones de 21st.dev en una "
            "pestaña. El agente también los usa solo (con `/ui`) según el tipo "
            "de web.")
        self.btn_21st.clicked.connect(self._open_21st_gallery)

        prev_row = QHBoxLayout()
        prev_row.addWidget(QLabel("URL:"))
        prev_row.addWidget(self.url_edit, 1)
        prev_row.addWidget(self.btn_start)
        prev_row.addWidget(self.btn_stop)
        prev_row.addWidget(self.btn_reload)
        prev_row.addWidget(self.btn_21st)
        prev_row.addWidget(self.btn_open_browser)

        # Fila de viewports + screenshot + devtools
        self.btn_screenshot = QPushButton("📸")
        self.btn_screenshot.setToolTip("Capture the preview to PNG")
        self.btn_screenshot.clicked.connect(self._capture_screenshot)
        self.btn_devtools = QPushButton("🔧 DevTools")
        self.btn_devtools.setToolTip("Open the webview DevTools")
        self.btn_devtools.clicked.connect(self._open_devtools)

        vp_row = QHBoxLayout()
        vp_row.addWidget(QLabel("Viewport:"))
        for label, width in VIEWPORTS:
            b = QToolButton()
            b.setText(label)
            b.clicked.connect(lambda _c=False, w=width: self._set_viewport(w))
            vp_row.addWidget(b)
        vp_row.addStretch()
        vp_row.addWidget(self.btn_screenshot)
        vp_row.addWidget(self.btn_devtools)

        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color:#aaa;")
        self.status_lbl.setTextFormat(Qt.TextFormat.RichText)

        # Lado izquierdo: tabs de preview (el primer tab es la "Preview"
        # ligada al dev server; los demás son tabs ad-hoc del usuario,
        # útiles p.ej. para abrir wp-admin sin perder la home).
        self.preview_tabs = QTabWidget()
        self.preview_tabs.setTabsClosable(True)
        self.preview_tabs.setMovable(True)
        self.preview_tabs.setDocumentMode(True)
        self.preview_tabs.tabCloseRequested.connect(self._close_preview_tab)
        self.preview_tabs.currentChanged.connect(self._on_preview_tab_changed)

        # Botón "+" en la esquina superior derecha de la barra de tabs
        btn_add_tab = QToolButton()
        btn_add_tab.setText("+")
        btn_add_tab.setAutoRaise(True)
        btn_add_tab.setToolTip("New tab (uses the URL from the bar)")
        btn_add_tab.clicked.connect(lambda: self._new_preview_tab())
        self.preview_tabs.setCornerWidget(btn_add_tab, Qt.Corner.TopRightCorner)

        # Primer tab "Preview" — no cerrable, vinculado al dev server.
        # self.webview se mantiene como alias del primer tab para que
        # viewport, screenshot, devtools, start/stop preview… sigan
        # operando exactamente como antes.
        self.webview = QWebEngineView()
        self.webview.setUrl(QUrl("about:blank"))
        self.webview.titleChanged.connect(
            lambda t: self._set_tab_title(self._preview_wrap, t or "Preview")
        )
        self.webview.urlChanged.connect(self._on_tab_url_changed)
        # El webview va DENTRO de un contenedor con HBox (no directo como página
        # del QTabWidget): el QStackedLayout del tab ignora setMaximumWidth, así
        # que sin wrapper los botones de Viewport (📱/📋/💻) no hacían nada. Con
        # el HBox + stretches, fijar maxWidth en el webview lo centra al ancho
        # del dispositivo elegido.
        self.webview.setSizePolicy(QSizePolicy.Policy.Expanding,
                                   QSizePolicy.Policy.Expanding)
        self.webview.setMinimumWidth(0)
        self._preview_wrap = QWidget()
        _pw = QHBoxLayout(self._preview_wrap)
        _pw.setContentsMargins(0, 0, 0, 0)
        _pw.setSpacing(0)
        # Factores de stretch: el webview DOMINA (1000) frente a los spacers (1),
        # así llena casi todo cuando no hay tope; al fijar un ancho de dispositivo
        # (setFixedWidth) los spacers lo centran. Empieza en "Full".
        _pw.addStretch(1)
        _pw.addWidget(self.webview, 1000)
        _pw.addStretch(1)
        idx = self.preview_tabs.addTab(self._preview_wrap, "Preview")
        tabbar = self.preview_tabs.tabBar()
        tabbar.setTabButton(idx, QTabBar.ButtonPosition.RightSide, None)
        tabbar.setTabButton(idx, QTabBar.ButtonPosition.LeftSide, None)

        # Lado derecho: tabs de terminal
        self.term_tabs = QTabWidget()
        # Si hay setup pendiente, el primer tab lo ejecuta y luego deja
        # una shell interactiva. Si no, shell bash plana.
        if self._initial_cmd:
            wrapper = (
                f"clear; echo '─── Pcreative Studio: ejecutando setup ───'; "
                f"bash {self._initial_cmd}; "
                f"echo ''; echo '─── setup terminado. Shell lista. ───'; "
                f"exec bash -i"
            )
            self._add_term_tab("Setup", "bash", ["-c", wrapper])
        else:
            self._add_term_tab("Shell", None)            # bash plano
        # Tab solo del provider seleccionado al crear el proyecto. Si no
        # se pasó (modo abrir desde galería), se abren todas las
        # disponibles en PATH como fallback.
        import shutil as _sh
        _AI_TABS = (
            ("Claude", "claude"),
            ("Codex", "codex"),
            ("Gemini", "gemini"),
            ("OpenCode", "opencode"),
        )
        if self._provider_key:
            try:
                import ai_providers as _aip
                binary = _aip.PROVIDERS[self._provider_key]["command"]
                short = _aip.PROVIDERS[self._provider_key]["short"]
                # extra args para opencode con OpenRouter
                _, extra = _aip.interactive_cmd_args(self._provider_key)
                if _sh.which(binary):
                    self._add_term_tab(short, binary, extra or None)
                else:
                    print(f"[project_window] {binary} no en PATH — no se añade tab del provider")
            except Exception as e:
                print(f"[project_window] error añadiendo tab del provider: {e}")
        else:
            # Abrir SOLO la IA seleccionada en el provider (app_prefs), en
            # cualquier modo — no todas las CLIs. Si auto_agent (galería /
            # abrir otro), va alimentada con el prompt de contexto del tema.
            import ai_providers as _aip2
            import app_prefs as _ap
            sel_key = _ap.default_provider()
            binary = _aip2.PROVIDERS.get(sel_key, {}).get("command")
            if binary and _sh.which(binary):
                short = _aip2.PROVIDERS[sel_key]["short"]
                _cmd, _extra = _aip2.interactive_cmd_args(sel_key)
                if self._auto_agent:
                    prompt = self._build_open_project_prompt(sel_key)
                    extra = list(_extra or [])
                    # Reanudar la ÚLTIMA sesión: si es Claude y este proyecto ya
                    # tuvo sesiones de IA, arranca con `--continue` (continúa la
                    # conversación más reciente) además de mandar el prompt. En
                    # proyectos nuevos (sin sesión previa) no se añade, para no
                    # romper con "No conversation found".
                    if _cmd == "claude":
                        try:
                            from pcreative_studio import last_ai_activity
                            if last_ai_activity(self.project_path) is not None:
                                extra.append("--continue")
                        except Exception:
                            pass
                    self._add_term_tab(short, _cmd, extra + [prompt])
                    self._auto_agent_tab_index = self.term_tabs.count() - 1
                else:
                    self._add_term_tab(short, _cmd, _extra or None)
            elif binary:
                print(f"[project_window] {binary} (provider '{sel_key}') no en PATH — no se añade tab de IA")
        # Tab 🚀 Hermes (Operator) — OPCIONAL: solo si Hermes está instalado.
        # Corre `hermes -s pcreative-studio-operator` interactivo en el cwd del
        # proyecto → auto-carga su AGENTS.md/.hermes.md, lo modifica y aprende.
        try:
            _hermes_bin = _sh.which("hermes") or str(Path.home() / ".local" / "bin" / "hermes")
            if Path(_hermes_bin).is_file():
                self._add_term_tab("🚀 Hermes", _hermes_bin,
                                   ["-s", "pcreative-studio-operator"])
        except Exception as e:
            print(f"[project_window] no se añadió tab Hermes: {e}")
        # Indicador en la barra de status si el server falla
        self._terminal_ready = False

        # Tab "Office" — visualizer pixel-art de sesiones IA. Carga
        # el dashboard del fork MIT (pixel-office-openclaw + reader de
        # Claude Code) vía WebEngineView en localhost:3002.
        try:
            import pixel_office
            if pixel_office.is_dashboard_up() or pixel_office.find_install_dir():
                self.pixel_view = QWebEngineView()
                self.pixel_view.setUrl(QUrl(pixel_office.DASHBOARD_URL))
                self.term_tabs.addTab(self.pixel_view, "🎮 Office")
            else:
                # Placeholder informativo si no está instalado.
                self.pixel_view = QWebEngineView()
                self.pixel_view.setHtml(
                    "<body style='background:#0c0c0d;color:#888;font:13px monospace;padding:2em'>"
                    "<h2 style='color:#fff'>🎮 Pixel Office not installed</h2>"
                    "<p>Enable from Pcreative Studio Settings → 🎮 Office → Install.</p>"
                    "<p style='color:#555'>Upstream MIT: "
                    "<a style='color:#62b4ff' href='https://github.com/neomatrix25/pixel-office-openclaw'>"
                    "neomatrix25/pixel-office-openclaw</a></p>"
                    "</body>"
                )
                self.term_tabs.addTab(self.pixel_view, "🎮 Office")
        except Exception as e:
            print(f"[pixel-office] tab no creada: {e}")

        # Si auto-lanzamos un agente, dejarlo como pestaña activa.
        if self._auto_agent_tab_index is not None:
            self.term_tabs.setCurrentIndex(self._auto_agent_tab_index)

        # Splitter horizontal: preview | terminales
        h_split = QSplitter(Qt.Orientation.Horizontal)
        h_split.addWidget(self.preview_tabs)
        h_split.addWidget(self.term_tabs)
        h_split.setStretchFactor(0, 3)
        h_split.setStretchFactor(1, 2)

        # Logs abajo
        self.logs = QPlainTextEdit()
        self.logs.setReadOnly(True)
        self.logs.setMaximumBlockCount(2000)
        fixed = QFont("monospace"); fixed.setStyleHint(QFont.StyleHint.Monospace)
        self.logs.setFont(fixed)
        self.logs.setPlaceholderText("Logs del dev server aparecerán aquí cuando pulses Start preview.")

        # Splitter vertical: arriba (preview+term), abajo logs
        v_split = QSplitter(Qt.Orientation.Vertical)
        v_split.addWidget(h_split)
        v_split.addWidget(self.logs)
        v_split.setStretchFactor(0, 5)
        v_split.setStretchFactor(1, 1)

        root = QVBoxLayout()
        root.addWidget(title)
        root.addLayout(toolbar)
        if self.sub_combo is not None:
            sub_row = QHBoxLayout()
            sub_row.addWidget(QLabel("Sub-proyecto:"))
            sub_row.addWidget(self.sub_combo, 1)
            root.addLayout(sub_row)
        root.addLayout(prev_row)
        root.addLayout(vp_row)
        root.addWidget(self.status_lbl)
        root.addWidget(v_split, 1)
        self.setLayout(root)

        # Wrapper para limitar ancho del webview (viewports)
        self._dev_tools_window: QWebEngineView | None = None

    def _add_term_tab(self, label: str, cmd: str | None, args: list[str] | None = None):
        view = QWebEngineView()
        # Permite copiar/pegar al portapapeles del sistema desde xterm.js.
        try:
            st = view.settings()
            st.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
            st.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanPaste, True)
        except Exception:
            pass
        view.setHtml("<body style='background:#0c0c0d;color:#888;font:13px monospace;padding:1em'>"
                     "iniciando servidor de terminal…</body>")
        self.term_tabs.addTab(view, label)
        # cmd None → shell por defecto
        self._pending_term_tabs.append((view, cmd or "bash", list(args or [])))

    # ── Auto-arranque del agente al abrir desde galería ──────────────
    def _project_has_skills(self) -> bool:
        """¿El proyecto tiene skills instaladas por autoskills / UI-UX Pro?

        OJO: NO cuenta skills genéricas que trae un fork (p. ej. las de Medusa
        —reviewing-prs, writing-docs…— en `.claude/skills/`), solo las que
        Pcreative Studio instala: autoskills escribe en `.agents/skills/` y crea
        SYMLINKS en `.claude/skills/`; uipro-cli crea una carpeta `ui-ux-pro-max`.
        Detectar cualquier `.claude/skills/*` daba un falso positivo y hacía que
        el prompt afirmara skills que el agente luego no encontraba.
        Mira raíz y, en mono-repos, apps/* y packages/*."""
        _UIPRO_HINTS = ("ui-ux-pro", "uiux-pro", "uipro")
        roots = [self.project_path]
        for sub in ("apps", "packages"):
            d = self.project_path / sub
            if d.is_dir():
                try:
                    roots += [p for p in d.iterdir() if p.is_dir()]
                except OSError:
                    pass
        for r in roots:
            # autoskills instala aquí: fuente de la verdad.
            ag = r / ".agents" / "skills"
            try:
                if ag.is_dir() and any(ag.iterdir()):
                    return True
            except OSError:
                pass
            # En `.claude/skills/` solo cuentan symlinks (autoskills) o la de uipro.
            try:
                for e in (r / ".claude" / "skills").iterdir():
                    if e.is_symlink() or any(h in e.name.lower() for h in _UIPRO_HINTS):
                        return True
            except OSError:
                continue
        return False

    def _build_open_project_prompt(self, provider_key: str) -> str:
        """Prompt inicial al abrir un proyecto existente desde la galería:
        leer el contexto del tema y proponer cómo continuar."""
        import ai_providers as _aip
        # Usar el archivo de contexto que exista en el proyecto (el del
        # provider elegido si está; si no, cualquiera de los conocidos).
        candidates = [
            _aip.PROVIDERS[provider_key].get("context_file", "CLAUDE.md"),
            "CLAUDE.md", "AGENTS.md", "GEMINI.md",
        ]
        ctx_file = next(
            (c for c in candidates if (self.project_path / c).is_file()),
            candidates[0],
        )
        # Si hay skills instaladas (autoskills / UI-UX Pro), decírselo
        # explícitamente — vale para proyectos viejos sin la sección en el MD.
        skills_line = ""
        if self._project_has_skills():
            skills_line = (
                " Este proyecto tiene **skills instaladas** (autoskills / UI-UX "
                "Pro) en `.claude/skills/` (y en mono-repos `apps/*/.claude/skills/`): "
                "lístalas, léelas y ÚSALAS durante el trabajo."
            )
        # Directivo de UI pro SIEMPRE en contexto: si es un frontend con la guía
        # UI-MOTION.md (la escribe web_enhancements al abrir), el agente debe
        # seguirla para cualquier trabajo visual.
        ui_line = ""
        if (self.project_path / "UI-MOTION.md").is_file():
            ui_line = (
                " Este proyecto tiene **`UI-MOTION.md`** (LECTURA OBLIGATORIA): "
                "léela. Para CUALQUIER trabajo de UI debes dejar la web a nivel "
                "de **estudio de diseño** — usa **21st.dev** (`/ui`, comprueba "
                "`/mcp` que `magic` está connected) + **framer-motion** "
                "(reveal/stagger/hover/parallax, respeta reduced-motion). NUNCA "
                "entregues UI básica."
            )
        name = self.project_path.name
        return (
            f"Acabas de abrir el proyecto «{name}» desde Pcreative Studio. "
            f"Lee COMPLETAMENTE {ctx_file} y todo lo que haya en context/ para "
            f"entender el estado actual del proyecto (qué es, stack, qué se ha "
            f"hecho ya).{skills_line}{ui_line}\n\n"
            f"Antes de tocar NADA del código:\n"
            f"1. Resume en 4-6 líneas el estado del proyecto y lo ya hecho.\n"
            f"2. Lista los primeros 3-5 pasos que propones para continuar "
            f"(incluye, si aplica, mejoras de UI/animación a nivel estudio).\n"
            f"3. Espera mi OK antes de ejecutar nada."
        )

    # ── Servidor Node con xterm.js ───────────────────────────────────
    def _start_terminal_server(self):
        node = shutil.which("node")
        if not node:
            self._terminal_error("Node.js no encontrado en PATH.")
            return
        self.term_server = QProcess(self)
        self.term_server.setProgram(node)
        self.term_server.setArguments([str(TERMINAL_DIR / "server.js"), "0"])
        self.term_server.setWorkingDirectory(str(TERMINAL_DIR))
        self.term_server.readyReadStandardOutput.connect(self._read_term_server)
        self.term_server.readyReadStandardError.connect(self._read_term_server_err)
        self.term_server.errorOccurred.connect(lambda e: self._terminal_error(f"node-pty: {e}"))
        self.term_server.start()

    def _read_term_server(self):
        if not self.term_server:
            return
        out = self.term_server.readAllStandardOutput().data().decode(errors="replace")
        for line in out.splitlines():
            if line.startswith("PORT="):
                try:
                    self.term_port = int(line.split("=", 1)[1])
                except ValueError:
                    self._terminal_error(f"PORT inválido: {line!r}")
            elif line.startswith("TOKEN="):
                self.term_token = line.split("=", 1)[1].strip()
            if self.term_port and self.term_token:
                self._terminal_ready = True
                self._load_pending_terminals()

    def _read_term_server_err(self):
        if not self.term_server: return
        err = self.term_server.readAllStandardError().data().decode(errors="replace")
        if err.strip():
            self.logs.appendPlainText(f"[term-server stderr] {err.strip()}")

    def _terminal_error(self, msg: str):
        self.logs.appendPlainText(f"[ERROR terminal embebida] {msg}")
        for view, cmd, _args in self._pending_term_tabs:
            view.setHtml(f"<body style='background:#0c0c0d;color:#ed1c57;font:13px monospace;padding:1em'>"
                         f"No se pudo iniciar la terminal embebida.<br>{msg}<br><br>"
                         f"Usa el botón <b>Konsole externa</b> arriba.</body>")
        self._pending_term_tabs.clear()

    def _load_pending_terminals(self):
        if self.term_port is None or not self.term_token: return
        cwd = str(self.project_path)
        for view, cmd, args in self._pending_term_tabs:
            # Puente de portapapeles (QWebChannel) ANTES de cargar la página,
            # para que `qt.webChannelTransport` exista cuando xterm arranque.
            try:
                bridge = _TermClipboard()
                channel = QWebChannel(view.page())
                channel.registerObject("tfClip", bridge)
                view.page().setWebChannel(channel)
                self._term_clip_refs.append((bridge, channel))
            except Exception:
                pass
            url = QUrl(f"http://127.0.0.1:{self.term_port}/")
            qry = QUrlQuery()
            qry.addQueryItem("cwd", cwd)
            qry.addQueryItem("cmd", cmd)
            if args:
                # El server.js parsea args separados por \x1f
                qry.addQueryItem("args", "\x1f".join(args))
            qry.addQueryItem("token", self.term_token)
            url.setQuery(qry)
            view.setUrl(url)
        self._pending_term_tabs.clear()
        self.logs.appendPlainText(f"[terminal embebida lista en puerto {self.term_port}]")

    # ── Pestañas de preview ──────────────────────────────────────────
    def _new_preview_tab(self, url=None, label: str = "Nueva"):
        """Crea una pestaña nueva en el navegador de preview.

        Si `url` es None, usa lo que haya en la barra de URL (o
        about:blank si está vacía). Si es str o QUrl, usa eso.
        """
        view = QWebEngineView()
        if url is None:
            s = self.url_edit.text().strip()
            qurl = QUrl(s) if s else QUrl("about:blank")
        elif isinstance(url, str):
            qurl = QUrl(url)
        else:
            qurl = url
        view.setUrl(qurl)
        view.titleChanged.connect(
            lambda t, v=view: self._set_tab_title(v, t or label)
        )
        view.urlChanged.connect(self._on_tab_url_changed)
        idx = self.preview_tabs.addTab(view, label)
        self.preview_tabs.setCurrentIndex(idx)
        return view

    def _open_21st_gallery(self):
        """Abre (o enfoca) la galería de componentes 21st.dev en una pestaña."""
        # Si ya está abierta, enfócala en vez de duplicar.
        for i in range(self.preview_tabs.count()):
            if self.preview_tabs.tabText(i).startswith("🎨"):
                self.preview_tabs.setCurrentIndex(i)
                return
        self._new_preview_tab("https://21st.dev/community/components",
                              label="🎨 21st.dev")

    def _webview_of(self, w):
        """Devuelve el QWebEngineView real de una pestaña: la principal va
        envuelta en self._preview_wrap; las demás son el propio view."""
        if isinstance(w, QWebEngineView):
            return w
        if w is getattr(self, "_preview_wrap", None):
            return self.webview
        return None

    def _close_preview_tab(self, index: int):
        widget = self.preview_tabs.widget(index)
        if widget is self._preview_wrap:
            return  # nunca cerrar el tab principal de Preview
        self.preview_tabs.removeTab(index)
        try:
            widget.deleteLater()
        except Exception:
            pass

    def _set_tab_title(self, view, title: str):
        idx = self.preview_tabs.indexOf(view)
        if idx >= 0:
            t = (title or "").strip()[:25]
            self.preview_tabs.setTabText(idx, t or "•")

    def _on_preview_tab_changed(self, _index: int):
        w = self._webview_of(self.preview_tabs.currentWidget())
        if isinstance(w, QWebEngineView):
            s = w.url().toString()
            if s and s != "about:blank":
                self.url_edit.setText(s)

    def _on_tab_url_changed(self, qurl: QUrl):
        sender = self.sender()
        if (
            isinstance(sender, QWebEngineView)
            and self._webview_of(self.preview_tabs.currentWidget()) is sender
        ):
            s = qurl.toString()
            if s and s != "about:blank":
                self.url_edit.setText(s)

    def _url_bar_navigate(self):
        url = self.url_edit.text().strip()
        if not url:
            return
        if not url.startswith(("http://", "https://", "about:", "file://")):
            url = "http://" + url
        w = self._webview_of(self.preview_tabs.currentWidget())
        if isinstance(w, QWebEngineView):
            w.setUrl(QUrl(url))

    def _reload_current_tab(self):
        w = self._webview_of(self.preview_tabs.currentWidget())
        if isinstance(w, QWebEngineView):
            w.reload()

    # ── Acciones de botones ──────────────────────────────────────────
    def _open_folder(self):
        if pc.open_in_file_manager(self.project_path) is None:
            QMessageBox.warning(self, "Folder",
                                "No encuentro un file manager en el sistema.")

    def _open_vscode(self):
        # Linux: prefer codium/code-oss fork if available (some distros
        # ship those instead of upstream `code`). Otherwise delegate to
        # the cross-platform helper which handles macOS .app fallback
        # and Windows default install paths.
        if pc.IS_LINUX:
            for cmd in ("code", "codium", "code-oss"):
                if shutil.which(cmd):
                    subprocess.Popen([cmd, str(self.project_path)])
                    return
        argv = pc.vscode_argv(self.project_path)
        if argv:
            subprocess.Popen(argv)
            return
        QMessageBox.warning(self, "VSCode",
                            "No encuentro VS Code instalado.")

    def _open_external(self):
        """Abre la preview en navegador externo en modo --app (sin barra
        de pestañas, sin URL bar, ventana limpia tipo app standalone).
        Performance nativa total — sin lag de QtWebEngine en Wayland.

        Prioriza Chromium-based (mejor soporte --app), cae a Firefox o
        xdg-open como fallback.
        """
        url = self.url_edit.text().strip() or "about:blank"
        # Chromium en app-mode: ventana sin chrome del navegador.
        # Brave primero (más privacy-friendly, mismo engine que Chrome).
        # `brave` = AUR/Arch, `brave-browser` = Debian/Ubuntu.
        # Solo --app + --user-data-dir aislado, sin flags experimentales.
        for binary in ("brave", "brave-browser",
                       "chromium", "google-chrome-stable", "google-chrome",
                       "microsoft-edge", "vivaldi"):
            if shutil.which(binary):
                subprocess.Popen([
                    binary,
                    f"--app={url}",
                    f"--user-data-dir={pc.app_cache_dir() / f'{binary}-app'}",
                ])
                return
        # Firefox: --kiosk es full-screen; -new-window es lo más cercano
        if shutil.which("firefox"):
            subprocess.Popen(["firefox", "--new-window", url])
            return
        # Fallback genérico — webbrowser.open cross-platform
        pc.open_url(url)

    def _open_external_terminal(self):
        if pc.open_in_terminal(self.project_path) is None:
            QMessageBox.warning(self, "Terminal externa",
                                "No encuentro un emulador de terminal soportado.")

    def _new_project(self):
        """Vuelve a 'New project' en la ventana principal (sin cerrar este)."""
        from PyQt6.QtWidgets import QMessageBox
        try:
            from pcreative_studio import focus_new_project
            if not focus_new_project():
                QMessageBox.information(
                    self, "Nuevo proyecto",
                    "Abre la ventana principal de Pcreative Studio y usa la pestaña "
                    "'New project'. Este proyecto seguirá abierto.")
        except Exception as e:
            QMessageBox.warning(self, "Nuevo proyecto", f"Error: {e}")

    def _open_other_project(self):
        """Abre OTRO proyecto en una ventana nueva (sin cerrar este)."""
        from PyQt6.QtWidgets import QMessageBox, QFileDialog
        try:
            from pcreative_studio import open_project_window, PROJECTS_DIR
            base = str(PROJECTS_DIR if Path(PROJECTS_DIR).is_dir() else Path.home())
            d = QFileDialog.getExistingDirectory(self, "Abrir otro proyecto", base)
            if d:
                # Igual que la galería: auto-ejecutar el agente con el contexto.
                open_project_window(Path(d), auto_agent=True)
        except Exception as e:
            QMessageBox.warning(self, "Abrir proyecto", f"Error: {e}")

    def _automate_with_operator(self):
        """Abre el Operator (Hermes) sobre ESTE proyecto (el de la preview)."""
        from PyQt6.QtWidgets import QMessageBox
        try:
            from operator_panel import OperatorMissionDialog, operator_available
            if not operator_available():
                QMessageBox.information(
                    self, "Operator",
                    "Instala Hermes Agent (opcional) para automatizar este "
                    "proyecto con el Operator.")
                return
            OperatorMissionDialog(self.project_path.name, self.project_path, self).exec()
        except Exception as e:
            QMessageBox.warning(self, "Operator", f"Error: {e}")

    def _run_preflight(self):
        """Ejecuta `preflight.run_all` y abre un diálogo con resultados
        coloreados por nivel + hints accionables + detalles plegables."""
        from PyQt6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget,
            QTreeWidgetItem, QDialogButtonBox,
        )
        from PyQt6.QtGui import QColor
        try:
            import preflight
        except Exception as e:
            QMessageBox.critical(self, "Pre-flight", f"No se pudo importar preflight: {e}")
            return

        # Para mono-repos, correr en el sub-proyecto activo
        target = self._preview_root if hasattr(self, "_preview_root") else self.project_path

        results = preflight.run_all(target)
        summary = preflight.summary(results)
        total_blocking = summary[preflight.LEVEL_FAIL]

        dlg = QDialog(self)
        dlg.setWindowTitle(f"🔬 Pre-flight — {target.name}")
        dlg.resize(820, 600)

        # Cabecera con resumen
        header = QLabel(
            f"<b>{target.name}</b><br>"
            f"<span style='color:#86efac;'>✓ {summary[preflight.LEVEL_PASS]} pass</span>  ·  "
            f"<span style='color:#fbbf24;'>⚠ {summary[preflight.LEVEL_WARN]} warn</span>  ·  "
            f"<span style='color:#ed1c57;'>✗ {summary[preflight.LEVEL_FAIL]} fail</span>  ·  "
            f"<span style='color:#888;'>ℹ {summary[preflight.LEVEL_INFO]} info</span>"
        )
        header.setTextFormat(Qt.TextFormat.RichText)
        header.setStyleSheet("padding:6px 0; font-size:14px;")

        verdict = QLabel()
        verdict.setTextFormat(Qt.TextFormat.RichText)
        if total_blocking == 0 and summary[preflight.LEVEL_WARN] == 0:
            verdict.setText("<b style='color:#86efac;'>✓ Listo para empaquetar y subir.</b>")
        elif total_blocking == 0:
            verdict.setText(
                "<b style='color:#fbbf24;'>⚠ Sin fallos críticos pero hay "
                "warnings que conviene resolver antes de subir.</b>"
            )
        else:
            verdict.setText(
                f"<b style='color:#ed1c57;'>✗ {total_blocking} fallos "
                "bloqueantes. Arregla antes de subir a marketplace.</b>"
            )
        verdict.setStyleSheet("padding:6px 0 12px;")

        # Árbol con los resultados
        tree = QTreeWidget()
        tree.setColumnCount(2)
        tree.setHeaderLabels(["Check", "Mensaje"])
        tree.setColumnWidth(0, 320)
        tree.setStyleSheet(
            "QTreeWidget { background:#1a1d24; alternate-background-color:#1f222b; "
            "color:#e6e9ef; border:1px solid #2d3340; font-size:13px; }"
            "QTreeWidget::item { padding:6px; }"
        )
        tree.setAlternatingRowColors(True)

        level_colors = {
            preflight.LEVEL_PASS: QColor("#86efac"),
            preflight.LEVEL_WARN: QColor("#fbbf24"),
            preflight.LEVEL_FAIL: QColor("#ed1c57"),
            preflight.LEVEL_INFO: QColor("#9ca3af"),
        }

        # Ordenar: fail > warn > pass > info (lo más urgente arriba)
        order = {preflight.LEVEL_FAIL: 0, preflight.LEVEL_WARN: 1,
                 preflight.LEVEL_PASS: 2, preflight.LEVEL_INFO: 3}
        results_sorted = sorted(results, key=lambda r: order[r.level])

        for r in results_sorted:
            icon = preflight.LEVEL_ICONS[r.level]
            top = QTreeWidgetItem([f"{icon}  {r.title}", r.message])
            top.setForeground(0, level_colors[r.level])
            top.setForeground(1, QColor("#e6e9ef"))
            if r.hint:
                hint_item = QTreeWidgetItem(["", f"💡  {r.hint}"])
                hint_item.setForeground(1, QColor("#62b4ff"))
                top.addChild(hint_item)
            if r.details:
                det = QTreeWidgetItem(["", f"Detalles ({len(r.details)}):"])
                det.setForeground(1, QColor("#888"))
                top.addChild(det)
                for d in r.details:
                    di = QTreeWidgetItem(["", f"   · {d}"])
                    di.setForeground(1, QColor("#aaa"))
                    det.addChild(di)
            tree.addTopLevelItem(top)
            # Auto-expandir fails y warns; pass/info colapsados
            if r.level in (preflight.LEVEL_FAIL, preflight.LEVEL_WARN):
                top.setExpanded(True)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, parent=dlg)
        bb.rejected.connect(dlg.reject)
        bb.button(QDialogButtonBox.StandardButton.Close).clicked.connect(dlg.accept)

        lay = QVBoxLayout(dlg)
        lay.addWidget(header)
        lay.addWidget(verdict)
        lay.addWidget(tree, 1)
        lay.addWidget(bb)
        dlg.exec()

    def _build_zip(self):
        """Empaqueta el proyecto en un ZIP para marketplace. Muestra
        un diálogo con opciones de inclusión, luego construye y abre
        la carpeta del resultado."""
        from PyQt6.QtWidgets import (
            QDialog, QCheckBox, QDialogButtonBox, QVBoxLayout, QLabel,
        )
        try:
            from pcreative_studio import build_marketplace_zip, BUILDS_DIR
        except Exception as e:
            QMessageBox.critical(self, "ZIP", f"No se pudo importar el builder: {e}")
            return

        # Detectar qué carpetas opcionales existen para preseleccionar
        has_docs = (self.project_path / "documentation").is_dir()
        has_shots = (self.project_path / "screenshots").is_dir()
        has_source = (self.project_path / "source").is_dir()

        dlg = QDialog(self)
        dlg.setWindowTitle(f"📦 Build ZIP — {self.project_path.name}")
        dlg.resize(480, 280)

        info = QLabel(
            f"Empaquetar <code>{self.project_path}</code> en un ZIP listo "
            f"para marketplace.<br>Excluye automáticamente node_modules, "
            f".git, .env, dist, .next, build, .cache, .vscode, .idea, "
            f".cursor, .claude, CLAUDE.md, AGENTS.md, MEMORY.md, *.log, "
            f".DS_Store, target, vendor, …<br><br>Salida: "
            f"<code>{BUILDS_DIR}/{self.project_path.name}-&lt;timestamp&gt;.zip</code>"
        )
        info.setTextFormat(Qt.TextFormat.RichText)
        info.setWordWrap(True)

        cb_docs = QCheckBox("Incluir documentation/")
        cb_docs.setChecked(has_docs)
        cb_docs.setEnabled(has_docs)
        if not has_docs:
            cb_docs.setText("Incluir documentation/  (no existe)")

        cb_shots = QCheckBox("Incluir screenshots/")
        cb_shots.setChecked(has_shots)
        cb_shots.setEnabled(has_shots)
        if not has_shots:
            cb_shots.setText("Incluir screenshots/  (no existe)")

        cb_source = QCheckBox("Incluir source/ (PSDs, Figma exports…)")
        cb_source.setChecked(has_source)
        cb_source.setEnabled(has_source)
        if not has_source:
            cb_source.setText("Incluir source/  (no existe)")

        bb = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel,
            parent=dlg,
        )
        bb.button(QDialogButtonBox.StandardButton.Ok).setText("📦 Build")
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)

        lay = QVBoxLayout(dlg)
        lay.addWidget(info)
        lay.addSpacing(6)
        lay.addWidget(cb_docs)
        lay.addWidget(cb_shots)
        lay.addWidget(cb_source)
        lay.addStretch()
        lay.addWidget(bb)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        self.logs.appendPlainText(f"\n[zip] empaquetando {self.project_path}…")
        ok, msg, out = build_marketplace_zip(
            self.project_path,
            include_documentation=cb_docs.isChecked(),
            include_screenshots=cb_shots.isChecked(),
            include_source=cb_source.isChecked(),
        )
        self.logs.appendPlainText(f"[zip] {msg}")
        if ok and out:
            r = QMessageBox.information(
                self, "📦 ZIP creado",
                f"{msg}\n\n¿Abrir la carpeta de builds?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if r == QMessageBox.StandardButton.Yes:
                pc.open_in_file_manager(out.parent)
        else:
            QMessageBox.warning(self, "📦 ZIP", msg)

    def _deploy_demo(self):
        """Despliega una demo pública del proyecto a Netlify / Vercel /
        Cloudflare Pages / Surge.sh. Encadena build → deploy con
        QProcess para mantener la UI responsive y stream-ear logs."""
        from PyQt6.QtWidgets import (
            QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QLabel,
            QLineEdit, QRadioButton, QButtonGroup, QFormLayout, QFrame,
        )
        from PyQt6.QtGui import QGuiApplication
        try:
            import demo_deploy as dd
        except Exception as e:
            QMessageBox.critical(self, "Demo deploy", f"No se pudo cargar el módulo: {e}")
            return

        cfg = dd.detect_build_config(self.project_path)

        dlg = QDialog(self)
        dlg.setWindowTitle(f"🚀 Deploy demo — {self.project_path.name}")
        dlg.resize(560, 440)

        info = QLabel(
            f"Despliega <code>{self.project_path.name}</code> a un host estático "
            f"y comparte la URL.<br>"
            f"Stack detectado: <b>{cfg.stack_hint}</b>"
            + (f" — {cfg.notes}" if cfg.notes else "")
        )
        info.setTextFormat(Qt.TextFormat.RichText)
        info.setWordWrap(True)

        # Provider radios
        provider_group = QButtonGroup(dlg)
        provider_row = QHBoxLayout()
        rb_netlify = QRadioButton("Netlify")
        rb_vercel = QRadioButton("Vercel")
        rb_cf = QRadioButton("Cloudflare Pages")
        rb_surge = QRadioButton("Surge.sh")
        for rb, key in (
            (rb_netlify, "netlify"), (rb_vercel, "vercel"),
            (rb_cf, "cloudflare"), (rb_surge, "surge"),
        ):
            rb.setProperty("provider_key", key)
            provider_group.addButton(rb)
            provider_row.addWidget(rb)
        # Pick default: first CLI that's available
        default_picked = False
        for rb, key in (
            (rb_netlify, "netlify"), (rb_vercel, "vercel"),
            (rb_cf, "cloudflare"), (rb_surge, "surge"),
        ):
            ok, _ = dd.check_cli_available(key)
            if ok and not default_picked:
                rb.setChecked(True)
                default_picked = True
                break
        if not default_picked:
            rb_cf.setChecked(True)  # always works via npx

        ed_build = QLineEdit(cfg.build_cmd)
        ed_build.setPlaceholderText("(vacío = sin build, deploy directo del dist)")
        ed_dist = QLineEdit(cfg.dist_dir)

        cli_status = QLabel()
        cli_status.setWordWrap(True)
        cli_status.setTextFormat(Qt.TextFormat.RichText)

        def update_cli_status():
            btn = provider_group.checkedButton()
            if not btn:
                cli_status.setText("")
                return
            key = btn.property("provider_key")
            info_p = dd.provider_info(key)
            ok, msg = dd.check_cli_available(key)
            if ok:
                cli_status.setText(
                    f"✅ <code>{info_p.cli}</code> disponible — {msg}"
                )
            else:
                cli_status.setText(
                    f"⚠️  <code>{info_p.cli}</code> no encontrado.<br>"
                    f"Instala con: <code>{info_p.install_cmd}</code><br>"
                    f"Después vuelve a abrir este diálogo."
                )

        provider_group.buttonToggled.connect(lambda *_: update_cli_status())
        update_cli_status()

        form = QFormLayout()
        form.addRow("Build command:", ed_build)
        form.addRow("Dist dir:", ed_dist)

        hint = QLabel(
            "<small>· Vercel ignora el dist dir (inspecciona el repo).<br>"
            "· Cloudflare Pages se ejecuta con <code>npx wrangler</code> "
            "(no requiere instalación global).<br>"
            "· La primera vez tendrás que autenticarte en el navegador.</small>"
        )
        hint.setTextFormat(Qt.TextFormat.RichText)
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #888;")

        bb = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel,
            parent=dlg,
        )
        bb.button(QDialogButtonBox.StandardButton.Ok).setText("🚀 Build & Deploy")
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        lay = QVBoxLayout(dlg)
        lay.addWidget(info)
        lay.addSpacing(6)
        lay.addWidget(QLabel("<b>Provider:</b>"))
        lay.addLayout(provider_row)
        lay.addWidget(cli_status)
        lay.addWidget(sep)
        lay.addLayout(form)
        lay.addWidget(hint)
        lay.addStretch()
        lay.addWidget(bb)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        chosen_btn = provider_group.checkedButton()
        if not chosen_btn:
            return
        provider_key = chosen_btn.property("provider_key")
        build_cmd = ed_build.text().strip()
        dist_dir = ed_dist.text().strip() or "."

        # Pre-flight CLI check
        ok, msg = dd.check_cli_available(provider_key)
        if not ok:
            QMessageBox.warning(
                self, "🚀 Demo deploy",
                f"CLI no disponible: {msg}\n\n"
                f"Instala con: {dd.provider_info(provider_key).install_cmd}",
            )
            return

        deploy_argv = dd.build_deploy_command(provider_key, dist_dir)
        deploy_str = " ".join(shlex.quote(a) for a in deploy_argv)

        self.btn_deploy_demo.setEnabled(False)
        self._deploy_output_buf: list[str] = []
        self._deploy_provider_key = provider_key
        self.logs.appendPlainText(
            f"\n[deploy] ⇢ {dd.provider_info(provider_key).name}"
        )

        def run_deploy():
            self.logs.appendPlainText(f"$ {deploy_str}")
            proc = QProcess(self)
            proc.setWorkingDirectory(str(self.project_path))
            proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
            proc.readyReadStandardOutput.connect(
                lambda p=proc: self._deploy_read_output(p)
            )
            proc.finished.connect(
                lambda code, status, p=proc: self._deploy_finished(p, code)
            )
            _sh, _args = pc.shell_program_and_args(deploy_str)
            proc.start(_sh, _args)
            self._deploy_proc = proc

        if build_cmd:
            self.logs.appendPlainText(f"$ {build_cmd}")
            proc = QProcess(self)
            proc.setWorkingDirectory(str(self.project_path))
            proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
            proc.readyReadStandardOutput.connect(
                lambda p=proc: self._deploy_read_output(p, prefix="[build] ")
            )

            def on_build_finished(code, _status, p=proc):
                if code != 0:
                    self.logs.appendPlainText(f"[build] FAILED (exit {code}) — abort deploy")
                    self.btn_deploy_demo.setEnabled(True)
                    QMessageBox.warning(
                        self, "🚀 Build failed",
                        f"El build falló con código {code}. Revisa los logs.",
                    )
                    return
                self.logs.appendPlainText("[build] OK — continuando con deploy…")
                run_deploy()

            proc.finished.connect(on_build_finished)
            _sh, _args = pc.shell_program_and_args(build_cmd)
            proc.start(_sh, _args)
            self._deploy_proc = proc
        else:
            run_deploy()

    def _deploy_read_output(self, proc, prefix: str = ""):
        try:
            data = proc.readAllStandardOutput().data().decode(errors="replace")
        except Exception:
            return
        if not data:
            return
        # Buffer para extraer URL al final
        self._deploy_output_buf.append(data)
        for line in data.rstrip().splitlines():
            self.logs.appendPlainText(f"{prefix}{line}" if prefix else line)

    def _deploy_finished(self, proc, exit_code: int):
        from PyQt6.QtGui import QGuiApplication
        try:
            import demo_deploy as dd
        except Exception:
            self.btn_deploy_demo.setEnabled(True)
            return

        self.btn_deploy_demo.setEnabled(True)
        full_output = "".join(self._deploy_output_buf)
        url = dd.extract_url(self._deploy_provider_key, full_output)

        if exit_code != 0:
            self.logs.appendPlainText(f"[deploy] FAILED (exit {exit_code})")
            QMessageBox.warning(
                self, "🚀 Deploy failed",
                f"El deploy falló con código {exit_code}.\n\n"
                f"Revisa los logs para más detalle. Si es la primera vez "
                f"con este provider puede que necesites autenticarte: "
                f"abre una terminal y ejecuta:\n\n"
                f"  {dd.provider_info(self._deploy_provider_key).auth_check_cmd[0]} login",
            )
            return

        self.logs.appendPlainText(f"[deploy] OK ✅")
        if url:
            self.logs.appendPlainText(f"[deploy] URL: {url}")
            cb = QGuiApplication.clipboard()
            cb.setText(url)
            r = QMessageBox.information(
                self, "🚀 Demo desplegada",
                f"URL: <a href='{url}'>{url}</a><br><br>"
                f"(copiada al portapapeles)<br><br>"
                f"¿Abrir en el navegador?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if r == QMessageBox.StandardButton.Yes:
                import webbrowser
                webbrowser.open(url)
        else:
            QMessageBox.information(
                self, "🚀 Deploy completado",
                "El deploy terminó pero no se pudo extraer la URL "
                "automáticamente. Revisa los logs para encontrarla.",
            )

    def _github_create_or_push(self):
        """Detecta repos en gh con el mismo nombre que la carpeta del
        proyecto y te ofrece elegir: actualizar uno existente o crear
        uno nuevo. Después configura `origin` y hace push.

        Búsqueda de matches:
          - `gh repo list` del usuario activo.
          - `gh repo list <github_org>` si la config `licensing.json`
            define una org (campo `github_org`).

        Estados posibles del proyecto local:
          - Sin .git → init + commit antes de seguir.
          - Con git pero sin origin → set origin → push.
          - Con git y origin que no coincide → set-url al repo elegido → push.
          - Con git y origin que coincide → push directo.
        """
        if not shutil.which("gh"):
            QMessageBox.critical(self, "GitHub",
                "No encuentro `gh` (GitHub CLI). Instálalo con `paru -S github-cli` y luego `gh auth login`.")
            return

        # Resolver username gh
        try:
            who = subprocess.run(["gh", "api", "user", "--jq", ".login"],
                                 capture_output=True, text=True, timeout=10)
            if who.returncode != 0:
                QMessageBox.critical(self, "GitHub",
                    "No estás autenticado en gh. Abre una terminal y ejecuta `gh auth login`.")
                return
            gh_user = who.stdout.strip()
        except Exception as e:
            QMessageBox.critical(self, "GitHub", f"Error consultando gh: {e}")
            return

        slug = self.project_path.name

        # Buscar repos existentes que matcheen el slug
        matches = self._gh_find_matching_repos(slug)

        # Construir opciones del selector. Cada opción es una tupla:
        # (label_visible, name_with_owner, "update"|"create-user"|"create-org")
        options: list[tuple[str, str, str]] = []
        for r in matches:
            name = r["nameWithOwner"]
            vis = (r.get("visibility") or "").lower()
            options.append((f"↻ Actualizar  {name}  [{vis}]", name, "update"))
        # Opciones de crear nuevo
        options.append((f"＋ CREAR nuevo  {gh_user}/{slug}  [privado]",
                        f"{gh_user}/{slug}", "create"))
        # Si licensing.json define una org de GitHub, ofrecer crear ahí.
        org = _licensing_github_org()
        if org and org != gh_user:
            options.append((f"＋ CREAR nuevo  {org}/{slug}  [privado, org]",
                            f"{org}/{slug}", "create"))

        labels = [o[0] for o in options]
        default_idx = 0 if matches else len(options) - 1  # si hay matches, preselecciona el primero

        from PyQt6.QtWidgets import QInputDialog
        choice, ok = QInputDialog.getItem(
            self, "GitHub",
            f"Repos coincidentes con «{slug}»:\n"
            f"(↻ = push a existente, ＋ = crear nuevo)",
            labels, current=default_idx, editable=False,
        )
        if not ok:
            return

        # Recuperar la opción elegida
        try:
            sel = next(o for o in options if o[0] == choice)
        except StopIteration:
            return
        _label, repo_full, action = sel

        cwd = str(self.project_path)
        has_git = (self.project_path / ".git").is_dir()
        cur_origin = ""
        if has_git:
            r = subprocess.run(["git", "remote", "get-url", "origin"],
                               cwd=cwd, capture_output=True, text=True)
            if r.returncode == 0:
                cur_origin = r.stdout.strip()

        self.logs.appendPlainText(
            f"\n[github] {'actualizando' if action == 'update' else 'creando'} {repo_full}…"
        )

        try:
            # Garantizar git inicializado con al menos un commit
            if not has_git:
                self.logs.appendPlainText("[github] git init…")
                subprocess.run(["git", "init", "-q"], cwd=cwd, check=True)

            # Antes de cualquier add/push: .gitignore con defaults
            # (node_modules, .next, dist, .env, …) + untrack de lo que
            # estuviese ya staged.
            self._ensure_gitignore_and_clean_index(cwd)

            if not has_git:
                # Primer add/commit (ahora ya con .gitignore bueno).
                subprocess.run(["git", "add", "-A"], cwd=cwd, check=True)
                subprocess.run(["git", "commit", "-m", "init: scaffold por Pcreative Studio", "-q"],
                               cwd=cwd, check=False)

            if action == "create":
                r = subprocess.run(
                    ["gh", "repo", "create", repo_full, "--private",
                     "--source=.", "--remote=origin", "--push"],
                    cwd=cwd, capture_output=True, text=True,
                )
            else:
                # action == "update": asegurar que origin apunta al repo elegido
                remote_url = f"https://github.com/{repo_full}.git"
                if not cur_origin:
                    subprocess.run(["git", "remote", "add", "origin", remote_url],
                                   cwd=cwd, check=True)
                elif repo_full not in cur_origin:
                    self.logs.appendPlainText(
                        f"[github] origin actual ({cur_origin}) NO coincide — re-apuntando a {remote_url}"
                    )
                    subprocess.run(["git", "remote", "set-url", "origin", remote_url],
                                   cwd=cwd, check=True)
                r = subprocess.run(["git", "push", "-u", "origin", "HEAD"],
                                   cwd=cwd, capture_output=True, text=True)

            if r.returncode == 0:
                url = f"https://github.com/{repo_full}"
                verb = "creado y subido" if action == "create" else "cambios subidos"
                self.logs.appendPlainText(f"[github] ✓ {verb}: {url}")
                QMessageBox.information(self, "GitHub",
                    f"✓ {verb.capitalize()}:\n{url}")
            else:
                err = (r.stderr or r.stdout or "(sin output)").strip()[:600]
                self.logs.appendPlainText(f"[github] ❌ falló: {err}")
                QMessageBox.warning(self, "GitHub", f"Operación falló:\n\n{err}")
        except Exception as e:
            self.logs.appendPlainText(f"[github] excepción: {e}")
            QMessageBox.critical(self, "GitHub", str(e))

    # Entradas que se aseguran en .gitignore antes de subir a GitHub.
    # Por convención NO se versionan node_modules, builds, secretos ni
    # cachés de IDE / OS. Si alguna estaba previamente trackeada, se
    # destrackea con `git rm --cached` antes del push.
    _GITIGNORE_DEFAULTS = [
        "# Added by Pcreative Studio",
        "# Node",
        "node_modules/",
        ".next/",
        "out/",
        "dist/",
        "build/",
        "# Logs",
        "*.log",
        "npm-debug.log*",
        "yarn-debug.log*",
        "yarn-error.log*",
        "# Env / secretos",
        ".env",
        ".env.local",
        ".env.*.local",
        ".env.development",
        ".env.production",
        "# Python",
        "__pycache__/",
        "*.pyc",
        ".venv/",
        "venv/",
        "# Rust / Java / Go",
        "target/",
        "*.class",
        "vendor/",
        "# IDE / OS",
        ".idea/",
        ".vscode/",
        ".DS_Store",
        "Thumbs.db",
    ]

    def _ensure_gitignore_and_clean_index(self, cwd: str) -> None:
        """Garantiza que .gitignore tiene los defaults y destrackea de la
        index lo que ya estuviera commiteado por error (típicamente
        node_modules del scaffold inicial)."""
        gi = Path(cwd) / ".gitignore"
        existing_text = gi.read_text(encoding="utf-8") if gi.exists() else ""
        existing_lines = {l.strip() for l in existing_text.splitlines() if l.strip()}

        # Solo añadimos entradas no comentadas que falten
        missing = [
            line for line in self._GITIGNORE_DEFAULTS
            if line.strip() and not line.startswith("#") and line not in existing_lines
        ]
        if missing or not existing_text:
            with gi.open("a", encoding="utf-8") as f:
                if existing_text and not existing_text.endswith("\n"):
                    f.write("\n")
                f.write("\n")
                for line in self._GITIGNORE_DEFAULTS:
                    if line.startswith("#"):
                        f.write(line + "\n")
                    elif line not in existing_lines:
                        f.write(line + "\n")
            self.logs.appendPlainText(
                f"[github] .gitignore: añadidas {len(missing)} entradas faltantes"
            )

        # Destrackear lo que ya estaba commiteado por error
        untrack_paths = [
            p for p in self._GITIGNORE_DEFAULTS
            if p.strip() and not p.startswith("#")
        ]
        subprocess.run(
            ["git", "rm", "-r", "--cached", "--ignore-unmatch", "--quiet", "--"]
            + untrack_paths,
            cwd=cwd, capture_output=True, text=True,
        )

        # Si hay algo que commitear (.gitignore nuevo o untrack), commit silencioso
        status = subprocess.run(["git", "status", "--porcelain"],
                                cwd=cwd, capture_output=True, text=True)
        if status.stdout.strip():
            subprocess.run(["git", "add", ".gitignore"], cwd=cwd, capture_output=True)
            r = subprocess.run(
                ["git", "commit", "-am", "chore: Pcreative Studio .gitignore defaults", "-q"],
                cwd=cwd, capture_output=True, text=True,
            )
            if r.returncode == 0:
                self.logs.appendPlainText(
                    "[github] commit de limpieza creado (.gitignore + untrack)"
                )

    def _gh_find_matching_repos(self, slug: str) -> list[dict]:
        """Devuelve repos del user activo + de la org de GitHub
        configurada en `licensing.json` (si la hay) que tengan el mismo
        nombre que `slug` (insensible a mayúsculas)."""
        out: list[dict] = []
        seen: set[str] = set()
        slug_lower = slug.lower()

        def _query(target: str | None):
            cmd = ["gh", "repo", "list"]
            if target:
                cmd.append(target)
            cmd += ["--json", "nameWithOwner,visibility", "--limit", "200"]
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
                if r.returncode != 0:
                    return
                data = json.loads(r.stdout or "[]")
                for repo in data:
                    nwo = repo.get("nameWithOwner", "")
                    name = nwo.split("/", 1)[1] if "/" in nwo else nwo
                    if name.lower() == slug_lower and nwo not in seen:
                        seen.add(nwo)
                        out.append({
                            "nameWithOwner": nwo,
                            "visibility": repo.get("visibility", ""),
                        })
            except Exception:
                pass

        _query(None)                # del user activo
        org = _licensing_github_org()
        if org:
            _query(org)             # de la org de la config (si hay)
        return out

    def _refresh_profile(self):
        """Re-detecta el perfil de preview y actualiza la UI. Útil tras
        completar el setup o instalar dependencias. Si es mono-repo,
        re-detecta sub-proyectos también."""
        # Re-detectar sub-proyectos (puede que tras un clone aparezcan)
        new_subs = detect_subprojects(self.project_path)
        if new_subs != self.subprojects:
            self.subprojects = new_subs
            if self.subprojects:
                self._active_sub_idx = 0
                if self.sub_combo is not None:
                    self.sub_combo.blockSignals(True)
                    self.sub_combo.clear()
                    for i, sub in enumerate(self.subprojects):
                        p = sub.get("profile")
                        tag = p["name"] if p else "sin preview"
                        self.sub_combo.addItem(f"{sub['name']}  —  {tag}", userData=i)
                    self.sub_combo.setCurrentIndex(0)
                    self.sub_combo.blockSignals(False)
        self.profile, self._preview_root = self._compute_active_profile()
        if self.profile and self.profile.get("port_inject") is not None:
            self.preview_port = get_port_for_project(
                self._port_slug(),
                self.profile.get("default_port", 3000),
            )
        else:
            self.preview_port = self.profile["default_port"] if self.profile else 0
        if self.profile:
            self.url_edit.setText(self.profile["url"].replace("{port}", str(self.preview_port)))
        self.btn_start.setEnabled(self.profile is not None)
        self._update_status()
        self.logs.appendPlainText("[perfil re-detectado]")
        self._load_no_server_preview()

    def _auto_detect_tick(self):
        """Reintenta detectar el perfil mientras el setup clona/instala."""
        self._auto_detect_attempts += 1
        prev = self.profile
        self.profile = detect_preview_profile(self.project_path)
        if self.profile is not None and prev is None:
            self._refresh_profile()
            self.logs.appendPlainText(f"[auto-detect] perfil detectado: {self.profile['name']}")
            if self._auto_detect_timer is not None:
                self._auto_detect_timer.stop()
        elif self._auto_detect_attempts >= self._auto_detect_max:
            if self._auto_detect_timer is not None:
                self._auto_detect_timer.stop()
            self.logs.appendPlainText(
                "[auto-detect] desistido tras 5 min. Pulsa 🔄 Re-detectar manualmente."
            )

    # ── Viewport / Screenshot / DevTools ─────────────────────────────
    def _set_viewport(self, width: int):
        """Fija el ancho del webview para simular un viewport (centrado por los
        spacers del contenedor). width<=0 = Full (sin tope, llena el panel)."""
        if width <= 0:
            # quita el ancho fijo → vuelve a expandir y llenar el panel
            self.webview.setMinimumWidth(0)
            self.webview.setMaximumWidth(16777215)
        else:
            self.webview.setFixedWidth(width)  # ancho exacto → spacers lo centran
        wrap = getattr(self, "_preview_wrap", None)
        if wrap is not None and wrap.layout() is not None:
            wrap.layout().activate()
        self.webview.updateGeometry()
        # Repintar el surface de Chromium tras el cambio de tamaño.
        self.webview.show()

    def _capture_screenshot(self):
        try:
            shots_dir = self.project_path / "screenshots"
            shots_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            png = shots_dir / f"preview-{ts}.png"
            pix: QPixmap = self.webview.grab()
            if pix.save(str(png), "PNG"):
                self.logs.appendPlainText(f"[screenshot] {png}")
                # También usar el screenshot como thumbnail del proyecto
                # en la galería (cards view). Silencioso — si falla, no
                # afecta a la captura principal.
                try:
                    from pcreative_studio import save_project_thumbnail
                    save_project_thumbnail(self.project_path.name, pix)
                except Exception:
                    pass
                QMessageBox.information(
                    self, "Screenshot",
                    f"Guardado:\n{png}\n\n"
                    "También se ha actualizado el thumbnail del proyecto "
                    "en la galería (vista 🖼️ Cards)."
                )
            else:
                QMessageBox.warning(self, "Screenshot", "Could not save the screenshot.")
        except Exception as e:
            QMessageBox.critical(self, "Screenshot error", str(e))

    def _open_devtools(self):
        if self._dev_tools_window is None or not self._dev_tools_window.isVisible():
            self._dev_tools_window = QWebEngineView()
            self._dev_tools_window.setWindowTitle(f"DevTools — {self.project_path.name}")
            self._dev_tools_window.resize(900, 700)
            self.webview.page().setDevToolsPage(self._dev_tools_window.page())
            self._dev_tools_window.show()
        else:
            self._dev_tools_window.raise_()
            self._dev_tools_window.activateWindow()

    # ── Preview ──────────────────────────────────────────────────────
    def _update_status(self):
        if not self.profile:
            self.status_lbl.setText(
                "⚠️ No se detectó un perfil de preview automático. "
                "Edita la URL e inicia manualmente (o desde una terminal embebida)."
            )
            self.btn_start.setEnabled(False)
        else:
            note = f" — {self.profile.get('note','')}" if self.profile.get("note") else ""
            self.status_lbl.setText(
                f"Perfil detectado: <b>{self.profile['name']}</b> · "
                f"<span style='color:#62b4ff'>puerto único: {self.preview_port}</span> → "
                f"<code>{' '.join(self.profile['command'])}</code>{note}"
            )

    def _load_no_server_preview(self) -> bool:
        """Para perfiles `no_server` (p.ej. WordPress en Docker, ya corriendo):
        carga la URL directamente en el webview sin arrancar ningún proceso."""
        if not (self.profile and self.profile.get("no_server")):
            return False
        url = self.profile["url"].replace("{port}", str(self.preview_port))
        self.url_edit.setText(url)
        cur = self.webview.url().toString() if self.webview else ""
        if cur in ("", "about:blank") or cur != url:
            self.webview.setUrl(QUrl(url))
        self.logs.appendPlainText(f"[preview] {self.profile['name']} → {url}")
        self._reflect_no_server_state()
        return True

    def _reflect_no_server_state(self):
        """Refleja en los botones Start/Stop si el contenedor (WordPress
        Docker u otro perfil `no_server`) está realmente corriendo. Sin
        esto, Start se podía pulsar repetido y Stop nunca se activaba."""
        if not (self.profile and self.profile.get("no_server")):
            return
        running = False
        try:
            from wp_provisioner import is_running
            running = is_running(self.project_path.name)
        except Exception:
            running = False
        self.btn_start.setEnabled(not running)
        self.btn_stop.setEnabled(running)

    def _kill_stale_dev_servers(self):
        """Mata dev servers HUÉRFANOS cuyo cwd sea este proyecto (next-server,
        vite, node…) y borra el lock por-carpeta de Next 16. Sin esto, un dev
        server que quedó vivo de antes impide arrancar el preview. Solo Linux
        (/proc); no-op en otros SO."""
        import os
        import signal
        roots = {os.path.realpath(str(self._preview_root)),
                 os.path.realpath(str(self.project_path))}
        try:
            mypid = os.getpid()
            for pid in os.listdir("/proc"):
                if not pid.isdigit() or int(pid) == mypid:
                    continue
                try:
                    cwd = os.path.realpath(f"/proc/{pid}/cwd")
                    if cwd not in roots:
                        continue
                    with open(f"/proc/{pid}/cmdline", "rb") as f:
                        cmdl = f.read().replace(b"\x00", b" ").decode("utf-8", "ignore")
                except Exception:
                    continue
                if any(k in cmdl for k in ("next", "vite", "node", "astro",
                                           "remix", "nuxt", "expo")):
                    try:
                        os.kill(int(pid), signal.SIGKILL)
                        self.logs.appendPlainText(
                            f"[preview] dev server huérfano matado (pid {pid})")
                    except Exception:
                        pass
        except Exception:
            pass
        # Lock de Next 16 (.next/dev) — si quedó tras matar el huérfano.
        for r in roots:
            try:
                import shutil
                shutil.rmtree(Path(r) / ".next" / "dev", ignore_errors=True)
            except Exception:
                pass

    def start_preview(self):
        if not self.profile: return
        # WordPress (Docker) y otros perfiles sin servidor: no se arranca
        # proceso, pero sí nos aseguramos de que los contenedores estén
        # arriba (por si se habían parado) y reflejamos el estado en los
        # botones para que Start/Stop dejen de ser "tontos".
        if self.profile.get("no_server"):
            slug = self.project_path.name
            cmd = self.profile.get("command")
            if cmd:
                # Docker genérico (PrestaShop, etc.): arranca el stack si está parado.
                try:
                    import subprocess
                    self.logs.appendPlainText(f"[preview] $ {' '.join(cmd)}")
                    subprocess.run(cmd, cwd=str(self._preview_root), timeout=180,
                                   capture_output=True)
                except Exception as e:
                    self.logs.appendPlainText(f"[preview] no pude arrancar el stack: {e}")
            else:
                try:
                    from wp_provisioner import start_containers, is_running
                    if not is_running(slug):
                        self.logs.appendPlainText(f"[preview] arrancando contenedor WordPress de «{slug}»…")
                        start_containers(slug)
                except Exception as e:
                    self.logs.appendPlainText(f"[preview] no pude arrancar contenedor: {e}")
            self._load_no_server_preview()
            return
        if self.preview_proc and self.preview_proc.state() != QProcess.ProcessState.NotRunning:
            return
        # Next.js 16 (y otros) dejan un dev server HUÉRFANO si el anterior no se
        # cerró limpio, y su lock por-carpeta (.next/dev/lock) BLOQUEA un nuevo
        # `next dev` → el preview da "connection refused". Limpiamos cualquier dev
        # server viejo de ESTE proyecto + el lock antes de arrancar.
        self._kill_stale_dev_servers()
        # Inyectar puerto único en command + env
        cmd, env_extra, url = apply_port(self.profile, self.preview_port)
        self.url_edit.setText(url)
        port_note = f"  (puerto: {self.preview_port})"
        env_str = " ".join(f"{k}={v}" for k, v in env_extra.items())
        prefix = f"{env_str} " if env_str else ""
        self.logs.appendPlainText(f"$ {prefix}{' '.join(cmd)}{port_note}\n")

        cwd = str(self._preview_root)
        self.preview_proc = QProcess(self)
        self.preview_proc.setWorkingDirectory(cwd)
        self.preview_proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        # Envolvemos en `bash -lc` para garantizar PATH y entorno completos
        # (npm, npx, expo, php, etc. pueden vivir en ~/.local/bin o
        # /usr/local/bin que QProcess no hereda si Pcreative Studio se abre
        # desde un launcher gráfico).
        if env_extra:
            env = QProcessEnvironment.systemEnvironment()
            for k, v in env_extra.items():
                env.insert(k, v)
            self.preview_proc.setProcessEnvironment(env)
        self.preview_proc.readyReadStandardOutput.connect(self._read_preview_output)
        self.preview_proc.finished.connect(self._preview_finished)
        self.preview_proc.errorOccurred.connect(lambda e: self.logs.appendPlainText(f"[preview error: {e}]"))
        cmd_str = " ".join(shlex.quote(c) for c in cmd)
        _sh, _args = pc.shell_program_and_args(cmd_str)
        self.preview_proc.start(_sh, _args)

        # Procesos secundarios (HMR / queue / pail / etc.) en paralelo
        for entry in self.profile.get("secondary_processes", []) or []:
            sec_name = entry.get("name", "extra")
            sec_cmd = entry.get("command") or []
            if not sec_cmd:
                continue
            self.logs.appendPlainText(f"$ [{sec_name}] {' '.join(sec_cmd)}")
            proc = QProcess(self)
            proc.setWorkingDirectory(cwd)
            proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
            # Captura por closure el name para que aparezca prefijado en logs
            proc.readyReadStandardOutput.connect(
                lambda p=proc, n=sec_name: self._read_sec_output(p, n)
            )
            sec_str = " ".join(shlex.quote(c) for c in sec_cmd)
            _sh, _args = pc.shell_program_and_args(sec_str)
            proc.start(_sh, _args)
            self.secondary_procs.append((sec_name, proc))

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        # Resetear la detección de URL real (la sacamos del stdout del server).
        self._detected_url_done = False
        # En vez de un wait fijo (causaba ERR_CONNECTION_REFUSED cuando el
        # dev server tardaba más en compilar), sondeamos el puerto hasta que
        # escuche y solo entonces cargamos la URL.
        self._begin_preview_wait()

    def _read_sec_output(self, proc: QProcess, name: str):
        try:
            data = proc.readAllStandardOutput().data().decode(errors="replace")
        except Exception:
            return
        if data:
            for line in data.rstrip().splitlines():
                self.logs.appendPlainText(f"[{name}] {line}")

    # URL que imprime el dev server (Astro/Vite/Next/etc.): seguimos ESA,
    # porque el puerto real puede no coincidir con el que inyectamos (flags
    # --port duplicados, puerto ocupado, default del framework…).
    _DEV_URL_RE = re.compile(
        r"https?://(?:localhost|127\.0\.0\.1|0\.0\.0\.0):(\d+)", re.IGNORECASE
    )

    def _read_preview_output(self):
        if not self.preview_proc: return
        data = self.preview_proc.readAllStandardOutput().data().decode(errors="replace")
        if data:
            self.logs.appendPlainText(data.rstrip())
            self._maybe_follow_server_url(data)

    def _maybe_follow_server_url(self, text: str):
        """Si el server reporta una URL con un puerto distinto al esperado,
        actualizamos el destino del preview y reapuntamos el sondeo."""
        if getattr(self, "_detected_url_done", False):
            return
        m = self._DEV_URL_RE.search(text)
        if not m:
            return
        self._detected_url_done = True
        port = int(m.group(1))
        cur_port = QUrl(self.url_edit.text().strip()).port()
        if port == cur_port:
            return  # ya apuntábamos bien
        detected = f"http://localhost:{port}/"
        self.logs.appendPlainText(
            f"[preview] el server escucha en {detected} (esperábamos puerto "
            f"{cur_port}) → sigo ese."
        )
        self.url_edit.setText(detected)
        # Reapuntar el sondeo al puerto real (resetea la cuenta atrás).
        self._begin_preview_wait()

    def _load_preview_url(self):
        url = self.url_edit.text().strip()
        if url:
            self.webview.setUrl(QUrl(url))

    # ── Espera activa a que el dev server escuche ────────────────────
    def _preview_host_port(self) -> tuple[str, int]:
        """Host+puerto del preview, sacados de la URL (con fallback al
        puerto asignado al proyecto)."""
        u = QUrl(self.url_edit.text().strip())
        host = u.host() or "127.0.0.1"
        port = u.port()
        if port is None or port < 0:
            try:
                port = int(self.preview_port)
            except (TypeError, ValueError):
                port = 0
        return host, port

    @staticmethod
    def _port_open(host: str, port: int, timeout: float = 0.4) -> bool:
        if not port:
            return False
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            return False

    def _begin_preview_wait(self, max_wait: float = 60.0):
        """Arranca el sondeo del puerto del dev server. Carga la URL en
        cuanto el puerto escuche; si no responde en `max_wait` s, carga
        igualmente para que el usuario vea el estado y pueda recargar."""
        self._preview_wait_deadline = time.monotonic() + max_wait
        # Pequeño primer intento por si el server ya estaba caliente.
        QTimer.singleShot(300, self._wait_for_server)

    def _wait_for_server(self):
        # Si el proceso de preview murió (y no es un perfil detached tipo
        # docker que sale con exit 0 pero sigue vivo), no seguimos sondeando.
        proc_dead = (
            self.preview_proc is None
            or self.preview_proc.state() == QProcess.ProcessState.NotRunning
        )
        is_detached = bool(self.profile and self.profile.get("stop"))
        if proc_dead and not is_detached:
            return

        host, port = self._preview_host_port()
        if self._port_open(host, port):
            self.logs.appendPlainText(f"[preview] {host}:{port} escuchando → cargando…")
            # Pequeña gracia: el socket abre un pelín antes de que el HTTP
            # server sirva la primera respuesta.
            QTimer.singleShot(400, self._load_preview_url)
            return

        if time.monotonic() < getattr(self, "_preview_wait_deadline", 0):
            QTimer.singleShot(500, self._wait_for_server)
        else:
            self.logs.appendPlainText(
                f"[preview] {host}:{port} no respondió a tiempo; cargando igualmente "
                f"(pulsa ↻ para reintentar cuando el server termine de compilar)."
            )
            self._load_preview_url()

    def _preview_finished(self, code, _status):
        self.logs.appendPlainText(f"\n[preview terminado: exit {code}]")
        # Perfiles "detached" (wp-env, docker compose -d): el comando de
        # start sale con exit 0 una vez los contenedores están arriba,
        # pero la preview sigue viva en Docker. En ese caso mantenemos
        # Stop habilitado para que el usuario pueda apagar los
        # contenedores con el comando `stop` del perfil; si no, sería
        # imposible pararlos desde la UI.
        if code == 0 and self.profile and self.profile.get("stop"):
            return
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def stop_preview(self):
        # Perfiles `no_server` (WordPress en Docker): paramos los contenedores
        # SIN borrarlos ni tocar volúmenes. Restart con Start los vuelve a
        # levantar con los datos intactos.
        if self.profile and self.profile.get("no_server"):
            slug = self.project_path.name
            try:
                from wp_provisioner import stop_containers
                self.logs.appendPlainText(f"\n[preview] parando contenedor WordPress de «{slug}»…")
                stop_containers(slug)
            except Exception as e:
                self.logs.appendPlainText(f"[preview] error parando contenedor: {e}")
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)
            self.webview.setUrl(QUrl("about:blank"))
            return
        if self.profile and self.profile.get("stop"):
            stop = self.profile["stop"]
            self.logs.appendPlainText(f"\n$ {' '.join(stop)}")
            try:
                subprocess.run(stop, cwd=str(self._preview_root), check=False, timeout=60)
            except Exception as e:
                self.logs.appendPlainText(f"[stop error: {e}]")
        if self.preview_proc and self.preview_proc.state() != QProcess.ProcessState.NotRunning:
            self.preview_proc.terminate()
            if not self.preview_proc.waitForFinished(3000):
                self.preview_proc.kill()
        # Parar todos los secundarios
        for name, proc in self.secondary_procs:
            try:
                if proc.state() != QProcess.ProcessState.NotRunning:
                    proc.terminate()
                    if not proc.waitForFinished(2000):
                        proc.kill()
            except Exception: pass
        self.secondary_procs.clear()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.webview.setUrl(QUrl("about:blank"))

    # ── Cierre limpio ────────────────────────────────────────────────
    def closeEvent(self, e):
        # 1) Parar preview (sin diálogos modales que cuelguen)
        try:
            if self.profile and self.profile.get("stop"):
                subprocess.Popen(self.profile["stop"], cwd=str(self.project_path),
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception: pass
        try:
            if self.preview_proc and self.preview_proc.state() != QProcess.ProcessState.NotRunning:
                self.preview_proc.terminate()
                self.preview_proc.waitForFinished(1500)
                if self.preview_proc.state() != QProcess.ProcessState.NotRunning:
                    self.preview_proc.kill()
        except Exception: pass
        try:
            for name, proc in self.secondary_procs:
                try:
                    if proc.state() != QProcess.ProcessState.NotRunning:
                        proc.terminate()
                        proc.waitForFinished(1500)
                        if proc.state() != QProcess.ProcessState.NotRunning:
                            proc.kill()
                except Exception: pass
        except Exception: pass
        # 2) Parar servidor terminal
        try:
            if self.term_server and self.term_server.state() != QProcess.ProcessState.NotRunning:
                self.term_server.terminate()
                self.term_server.waitForFinished(1500)
                if self.term_server.state() != QProcess.ProcessState.NotRunning:
                    self.term_server.kill()
        except Exception: pass
        # 3) Limpiar webviews
        try:
            self.webview.stop(); self.webview.setUrl(QUrl("about:blank"))
            for i in range(self.term_tabs.count()):
                w = self.term_tabs.widget(i)
                try:
                    w.stop(); w.setUrl(QUrl("about:blank"))
                except Exception: pass
        except Exception: pass
        super().closeEvent(e)
