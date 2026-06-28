"""operator_panel.py — Mission Control for the Pcreative Studio Operator (Hermes).

A GUI tab to launch autonomous template-building missions: type a brief, hit
Launch, and Hermes (the `pcreative-studio-operator` skill + the `pcreative-studio` MCP
tools) plans → creates → builds (via the configured agent) → QA-loops →
packages, streaming progress here.

Requires Hermes installed (`~/.local/bin/hermes`) with the `pcreative-studio` MCP
server registered in `~/.hermes/config.yaml` and the `pcreative-studio-operator`
skill enabled. See the Operator setup docs.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from PyQt6.QtCore import Qt, QProcess, QProcessEnvironment
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QPlainTextEdit,
    QSpinBox, QComboBox, QMessageBox, QDialog, QSplitter, QFileDialog, QTabWidget,
)

OPERATOR_SKILL = "pcreative-studio-operator"
PROJECTS_DIR = Path.home() / "Proyectos" / "themes"
TERMINAL_DIR = Path(os.environ.get("PCREATIVE_STUDIO_TERMINAL_DIR")
                    or os.environ.get("THEMEFORGE_TERMINAL_DIR")
                    or (Path(__file__).resolve().parent / "terminal"))


def find_hermes() -> str | None:
    """Locate the hermes launcher (per-user install or on PATH)."""
    cand = Path.home() / ".local" / "bin" / "hermes"
    if cand.is_file():
        return str(cand)
    return shutil.which("hermes")


def operator_available() -> bool:
    """True si Hermes está instalado → el Operator (opcional) puede usarse."""
    return find_hermes() is not None


# ── Lock GLOBAL de misiones ──────────────────────────────────────────────
# El guard "misión en curso" de cada widget era local; dos pestañas/diálogos
# podían lanzar misiones autónomas a la vez (cada una corre un agente que toca
# el FS). Este contador compartido lo impide en toda la app.
_active_missions = 0

def mission_active() -> bool:
    return _active_missions > 0

def mission_begin() -> None:
    global _active_missions
    _active_missions += 1

def mission_end() -> None:
    global _active_missions
    _active_missions = max(0, _active_missions - 1)


def _mission_env() -> QProcessEnvironment:
    env = QProcessEnvironment.systemEnvironment()
    local_bin = str(Path.home() / ".local" / "bin")
    env.insert("PATH", local_bin + os.pathsep + env.value("PATH", ""))
    return env


class ProjectPreviewWidget(QWidget):
    """Preview web en vivo de un proyecto: arranca su dev server (vía
    `preview.py`) y lo carga en un QWebEngineView. Versión condensada del
    preview de ProjectWindow, reutilizable en la pestaña Operator."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._proc: QProcess | None = None
        self._project: Path | None = None
        self._url = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        self.lbl = QLabel("Preview — sin proyecto")
        self.lbl.setStyleSheet("color:#888;")
        self.lbl.setWordWrap(True)
        bar.addWidget(self.lbl, 1)
        self.btn_pick = QPushButton("📂")
        self.btn_pick.setToolTip("Elegir proyecto a previsualizar")
        self.btn_pick.clicked.connect(self._pick)
        self.btn_start = QPushButton("▶ Preview")
        self.btn_start.clicked.connect(self.start)
        self.btn_start.setEnabled(False)
        self.btn_stop = QPushButton("⏹")
        self.btn_stop.clicked.connect(self.stop)
        self.btn_stop.setEnabled(False)
        self.btn_reload = QPushButton("⟳")
        self.btn_reload.clicked.connect(self._reload)
        for b in (self.btn_pick, self.btn_start, self.btn_stop, self.btn_reload):
            bar.addWidget(b)
        root.addLayout(bar)

        self._web = None
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            from PyQt6.QtCore import QUrl
            self._web = QWebEngineView()
            self._web.setUrl(QUrl("about:blank"))
            root.addWidget(self._web, 1)
        except Exception as e:
            root.addWidget(QLabel(f"Preview no disponible (QtWebEngine): {e}"), 1)

    def set_project(self, path):
        self._project = Path(path) if path else None
        self.lbl.setText(f"Preview — {self._project.name}" if self._project
                         else "Preview — sin proyecto")
        self.btn_start.setEnabled(self._project is not None and self._web is not None)

    def _pick(self):
        base = str(PROJECTS_DIR if PROJECTS_DIR.is_dir() else Path.home())
        d = QFileDialog.getExistingDirectory(self, "Elegir proyecto", base)
        if d:
            self.set_project(d)

    def _reload(self):
        if self._web:
            self._web.reload()

    def start(self):
        if not self._project or not self._web:
            return
        try:
            from preview import detect_preview_profile, apply_port, get_port_for_project
            from PyQt6.QtCore import QUrl, QTimer
            import shlex
            import platform_compat as pc
        except Exception as e:
            self.lbl.setText(f"Preview: error import ({e})")
            return
        prof = detect_preview_profile(self._project)
        if not prof:
            self.lbl.setText(f"{self._project.name}: sin preview detectable "
                             "(¿stack soportado / deps instaladas?)")
            return
        port = get_port_for_project(self._project.name, prof.get("default_port", 5173))
        cmd, env_extra, url = apply_port(prof, port)
        self._url = url
        self._proc = QProcess(self)
        self._proc.setWorkingDirectory(str(self._project))
        self._proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        env = QProcessEnvironment.systemEnvironment()
        env.insert("PATH", str(Path.home() / ".local" / "bin")
                   + os.pathsep + env.value("PATH", ""))
        for k, v in (env_extra or {}).items():
            env.insert(k, str(v))
        self._proc.setProcessEnvironment(env)
        cmd_str = " ".join(shlex.quote(c) for c in cmd)
        sh, args = pc.shell_program_and_args(cmd_str)
        self._proc.start(sh, args)
        self.lbl.setText(f"{self._project.name} · arrancando dev server "
                         f"(puerto {port})…")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        QTimer.singleShot(4500, self._load)

    def _load(self):
        from PyQt6.QtCore import QUrl
        if self._web and self._url:
            self._web.setUrl(QUrl(self._url))
            self.lbl.setText(f"{self._project.name} · {self._url}")

    def stop(self):
        from PyQt6.QtCore import QUrl
        if self._proc and self._proc.state() != QProcess.ProcessState.NotRunning:
            self._proc.kill()
        if self._web:
            self._web.setUrl(QUrl("about:blank"))
        self.btn_start.setEnabled(self._project is not None)
        self.btn_stop.setEnabled(False)
        if self._project:
            self.lbl.setText(f"Preview — {self._project.name} (detenido)")


class HermesTerminal(QWidget):
    """Terminal embebido que corre `hermes -s pcreative-studio-operator` interactivo
    (chat con Hermes) en un cwd dado. Reutiliza terminal/server.js + xterm.js
    (mismo mecanismo que ProjectWindow). Permite conversar con Hermes y pedirle
    que modifique cualquier cosa del proyecto."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._server: QProcess | None = None
        self._port: int | None = None
        self._token: str = ""
        self._hermes = find_hermes()
        self._cwd = str(PROJECTS_DIR if PROJECTS_DIR.is_dir() else Path.home())

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        self.lbl = QLabel("💬 Chat con Hermes")
        self.lbl.setWordWrap(True)
        bar.addWidget(self.lbl, 1)
        self.btn_restart = QPushButton("↻ Reiniciar chat")
        self.btn_restart.clicked.connect(self._load)
        bar.addWidget(self.btn_restart)
        root.addLayout(bar)

        self._web = None
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            self._web = QWebEngineView()
            self._web.setHtml("<body style='background:#0c0c0d;color:#888;"
                              "font:13px monospace;padding:1em'>"
                              "iniciando chat con Hermes…</body>")
            root.addWidget(self._web, 1)
        except Exception as e:
            root.addWidget(QLabel(f"Chat no disponible (QtWebEngine): {e}"), 1)

        if not self._hermes:
            self.lbl.setText("💬 Chat con Hermes — instala Hermes (opcional) "
                             "para conversar y modificar proyectos.")
            self.btn_restart.setEnabled(False)
        elif self._web:
            self._start_server()

    def set_cwd(self, path):
        """Apunta el chat al directorio de un proyecto (auto-carga su contexto)."""
        self._cwd = str(path)
        # Expone las skills de autoskills/uipro a Hermes (AGENTS.md) antes de
        # cargar el chat — idempotente y barato.
        try:
            from hermes_skills_bridge import bridge_skills_for_hermes
            bridge_skills_for_hermes(path)
        except Exception:
            pass
        self.lbl.setText(f"💬 Chat con Hermes · {Path(self._cwd).name}")
        if self._port:
            self._load()

    def _start_server(self):
        import shutil
        node = shutil.which("node")
        if not node or not self._web:
            self.lbl.setText("💬 Chat — Node.js no encontrado (necesario para el terminal).")
            return
        self._server = QProcess(self)
        self._server.setProgram(node)
        self._server.setArguments([str(TERMINAL_DIR / "server.js"), "0"])
        self._server.setWorkingDirectory(str(TERMINAL_DIR))
        self._server.setProcessEnvironment(_mission_env())
        self._server.readyReadStandardOutput.connect(self._read_server)
        self._server.start()

    def _read_server(self):
        if not self._server:
            return
        out = self._server.readAllStandardOutput().data().decode(errors="replace")
        for line in out.splitlines():
            if line.startswith("PORT="):
                try:
                    self._port = int(line.split("=", 1)[1])
                except ValueError:
                    pass
            elif line.startswith("TOKEN="):
                self._token = line.split("=", 1)[1].strip()
            if self._port and self._token:
                self._load()

    def _load(self):
        from PyQt6.QtCore import QUrl, QUrlQuery
        if not (self._web and self._port and self._token and self._hermes):
            return
        url = QUrl(f"http://127.0.0.1:{self._port}/")
        q = QUrlQuery()
        q.addQueryItem("cwd", self._cwd)
        q.addQueryItem("cmd", self._hermes)
        q.addQueryItem("args", "\x1f".join(["-s", OPERATOR_SKILL]))
        q.addQueryItem("token", self._token)
        url.setQuery(q)
        self._web.setUrl(url)
        self.lbl.setText(f"💬 Chat con Hermes · {Path(self._cwd).name}")

    def shutdown(self):
        """Mata el servidor de terminal y limpia la vista. Lo usa el botón
        maestro de encendido/apagado de Hermes."""
        from PyQt6.QtCore import QUrl
        if self._server and self._server.state() != QProcess.ProcessState.NotRunning:
            self._server.kill()
        self._server = None
        self._port = None
        self._token = ""
        if self._web:
            self._web.setHtml("<body style='background:#0c0c0d;color:#888;"
                              "font:13px monospace;padding:1em'>chat detenido — "
                              "enciende Hermes para reanudar.</body>")

    def relaunch(self):
        """Reinicia el servidor de terminal si estaba apagado."""
        if not self._hermes or not self._web:
            return
        if self._server and self._server.state() != QProcess.ProcessState.NotRunning:
            self._load()
            return
        self._start_server()


class OperatorPanel(QWidget):
    """Mission Control: launch Hermes-orchestrated Pcreative Studio missions."""

    SKILL = "pcreative-studio-operator"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._proc: QProcess | None = None
        self._hermes = find_hermes()

        # Layout: izquierda = misión (brief + controles + log);
        # derecha = preview en vivo del proyecto que Hermes construye.
        outer = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        outer.addWidget(splitter)
        # Izquierda: tabs 🎯 Misión (lanzar brief one-shot) + 💬 Chat
        # (conversación interactiva con Hermes para modificar el proyecto).
        self._left_tabs = QTabWidget()
        splitter.addWidget(self._left_tabs)
        # Derecha: preview web en vivo del proyecto construido.
        self.preview = ProjectPreviewWidget()
        splitter.addWidget(self.preview)
        splitter.setSizes([560, 520])

        mission = QWidget()
        root = QVBoxLayout(mission)

        title = QLabel("🚀 Operator — Mission Control")
        f = QFont(); f.setPointSize(15); f.setBold(True)
        title.setFont(f)
        root.addWidget(title)

        sub = QLabel(
            "<b>Modo opcional.</b> Describe una misión y Hermes la construye "
            "sola: plan → crear → build → QA → empaquetar. Cada variante recibe "
            "un estilo UI/UX Pro Max distinto. Pcreative Studio funciona perfectamente "
            "sin esto — el Operator es un extra para automatización autónoma."
        )
        sub.setTextFormat(Qt.TextFormat.RichText)
        sub.setWordWrap(True)
        root.addWidget(sub)

        if not self._hermes:
            info = QLabel(
                "ℹ️ <b>Operator no activado</b> (opcional). Para habilitarlo, "
                "instala Hermes Agent y registra el MCP de Pcreative Studio:<br>"
                "<code>curl -fsSL https://raw.githubusercontent.com/NousResearch/"
                "hermes-agent/main/scripts/install.sh | bash</code><br>"
                "Luego configura una API key (p.ej. OpenRouter) y registra el "
                "servidor MCP. Mientras tanto, el resto de Pcreative Studio funciona igual."
            )
            info.setTextFormat(Qt.TextFormat.RichText)
            info.setStyleSheet("color:#7aa2f7; background:#1a1a22; padding:8px; border-radius:6px;")
            info.setWordWrap(True)
            info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            root.addWidget(info)

        root.addWidget(QLabel("Brief de la misión:"))
        self.brief = QPlainTextEdit()
        self.brief.setPlaceholderText(
            "Ej: 2 variantes Envato-ready de landing para clínica dental, "
            "stack Astro+Tailwind, paletas distintas, demo data completa."
        )
        self.brief.setMaximumHeight(90)
        root.addWidget(self.brief)

        ctl = QHBoxLayout()
        ctl.addWidget(QLabel("Variantes:"))
        self.variants = QSpinBox()
        self.variants.setRange(1, 6)
        self.variants.setValue(1)
        ctl.addWidget(self.variants)
        ctl.addWidget(QLabel("Agente:"))
        self.provider = QComboBox()
        self.provider.addItems(["claude", "codex", "opencode", "gemini", "openrouter", "claude-api"])
        ctl.addWidget(self.provider)
        ctl.addStretch()
        self.btn_launch = QPushButton("🚀 Lanzar misión")
        self.btn_launch.clicked.connect(self._launch)
        self.btn_launch.setEnabled(bool(self._hermes))
        ctl.addWidget(self.btn_launch)
        self.btn_stop = QPushButton("⏹ Detener")
        self.btn_stop.clicked.connect(self._stop)
        self.btn_stop.setEnabled(False)
        ctl.addWidget(self.btn_stop)
        root.addLayout(ctl)

        self.status = QLabel("Listo." if self._hermes else "Hermes no disponible.")
        self.status.setStyleSheet("color:#888;")
        root.addWidget(self.status)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet(
            "font-family: monospace; font-size: 11px; background:#111; color:#cdd;"
        )
        self.log.setPlaceholderText("La actividad de la misión aparecerá aquí…")
        root.addWidget(self.log, 1)

        # Montar las tabs de la izquierda: Misión (lo de arriba) + Chat.
        self._left_tabs.addTab(mission, "🎯 Misión")
        self.chat = HermesTerminal()
        self._left_tabs.addTab(self.chat, "💬 Chat con Hermes")

    # ── helpers ──────────────────────────────────────────────────────
    def _append(self, text: str):
        self.log.appendPlainText(text.rstrip("\n"))
        sb = self.log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _build_prompt(self) -> str:
        brief = self.brief.toPlainText().strip()
        n = self.variants.value()
        prov = self.provider.currentText()
        return (
            f"Run a Pcreative Studio Operator mission. Build agent (provider): {prov}. "
            f"Number of variants: {n}. Mission brief: {brief}\n\n"
            "Use the pcreative-studio MCP tools and follow the pcreative-studio-operator skill: "
            "plan with a DISTINCT UI/UX Pro Max style+palette per variant, then for "
            "each variant call create_project (run_autoskills=true, run_uipro=true), "
            "run_agent_build with a detailed prompt (sections + complete demo data + "
            "Unsplash/Pixabay images, Envato-ready), run_preflight in a QA loop "
            "(max 3 fixes), and build_zip. For multiple variants dispatch parallel "
            "delegate_task subagents. Report each variant: path, style, QA result, zip."
        )

    # ── run / stop ───────────────────────────────────────────────────
    def _launch(self):
        if not self._hermes:
            return
        if not self.brief.toPlainText().strip():
            QMessageBox.information(self, "Operator", "Escribe un brief para la misión.")
            return
        if self._proc and self._proc.state() != QProcess.ProcessState.NotRunning:
            QMessageBox.information(self, "Operator", "Ya hay una misión en curso.")
            return
        if mission_active():
            QMessageBox.information(self, "Operator",
                                    "Ya hay una misión en curso en otra pestaña/ventana.")
            return

        self.log.clear()
        self._append(
            f"▶ Lanzando misión ({self.variants.value()} variante/s, "
            f"agente {self.provider.currentText()})…\n"
            "(Hermes planifica y orquesta; esto puede tardar varios minutos.)\n"
        )
        self.status.setText("Misión en curso…")
        self.btn_launch.setEnabled(False)
        self.btn_stop.setEnabled(True)

        self._proc = QProcess(self)
        self._proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        env = QProcessEnvironment.systemEnvironment()
        local_bin = str(Path.home() / ".local" / "bin")
        env.insert("PATH", local_bin + os.pathsep + env.value("PATH", ""))
        self._proc.setProcessEnvironment(env)
        self._proc.readyReadStandardOutput.connect(self._on_output)
        self._proc.finished.connect(self._on_finished)
        self._proc.errorOccurred.connect(self._on_proc_error)
        # `hermes chat -q` = one-shot no-interactivo con progreso visible.
        self._counted = True
        mission_begin()
        self._proc.start(self._hermes, ["chat", "-q", self._build_prompt(),
                                        "-s", self.SKILL])

    def _release_mission(self):
        if getattr(self, "_counted", False):
            self._counted = False
            mission_end()

    def _on_proc_error(self, _e):
        self._append("✗ no se pudo ejecutar hermes.")
        self._release_mission()
        self.btn_launch.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def _on_output(self):
        if not self._proc:
            return
        data = bytes(self._proc.readAllStandardOutput()).decode(errors="replace")
        for line in data.splitlines():
            if line.strip():
                self._append(line)

    def _on_finished(self, code: int, _status):
        self._release_mission()
        self._append(f"\n■ Misión terminada (exit {code}).")
        self.status.setText(f"Terminada (exit {code}).")
        self.btn_launch.setEnabled(True)
        self.btn_stop.setEnabled(False)
        # Auto-cargar en el preview el proyecto más reciente (el que Hermes
        # acaba de construir) para que el user pulse ▶ Preview.
        try:
            if PROJECTS_DIR.is_dir():
                projs = [p for p in PROJECTS_DIR.iterdir()
                         if p.is_dir() and not p.name.startswith(".")]
                if projs:
                    newest = max(projs, key=lambda p: p.stat().st_mtime)
                    self.preview.set_project(newest)
                    if hasattr(self, "chat"):
                        self.chat.set_cwd(newest)  # el chat ya apunta al proyecto
                    self._append(f"→ Preview listo para '{newest.name}'. Pulsa "
                                 "▶ Preview; o ve a 💬 Chat para seguir modificándolo.")
        except Exception:
            pass

    def _stop(self):
        if self._proc and self._proc.state() != QProcess.ProcessState.NotRunning:
            self._proc.kill()
            self._append("\n⏹ Misión detenida por el usuario.")
        self.btn_launch.setEnabled(True)
        self.btn_stop.setEnabled(False)


class OperatorMissionDialog(QDialog):
    """Lanza una misión del Operator sobre un proyecto EXISTENTE (galería /
    preview). El usuario escribe la tarea; Hermes localiza el proyecto, entra
    en su carpeta (auto-carga su AGENTS.md/.hermes.md) y lo automatiza."""

    def __init__(self, project_name: str, project_path, parent=None):
        super().__init__(parent)
        self._proc: QProcess | None = None
        self._hermes = find_hermes()
        self._name = project_name
        self._path = str(project_path)
        self.setWindowTitle(f"🚀 Operator — {project_name}")
        self.setMinimumSize(620, 480)

        root = QVBoxLayout(self)
        head = QLabel(f"<b>Automatizar con el Operator</b><br>"
                      f"Proyecto: <b>{project_name}</b><br>"
                      f"<small style='color:#888'>{self._path}</small>")
        head.setTextFormat(Qt.TextFormat.RichText)
        head.setWordWrap(True)
        root.addWidget(head)

        root.addWidget(QLabel("¿Qué quieres que el Operator haga en este proyecto?"))
        self.task = QPlainTextEdit()
        self.task.setPlaceholderText(
            "Ej: añade una sección de pricing con 3 planes, mejora el hero y "
            "pásale preflight. (Hermes trabaja sobre el proyecto existente, no "
            "crea uno nuevo, y aprende de él.)")
        self.task.setMaximumHeight(90)
        root.addWidget(self.task)

        ctl = QHBoxLayout()
        ctl.addWidget(QLabel("Agente:"))
        self.provider = QComboBox()
        self.provider.addItems(["claude", "codex", "opencode", "gemini", "openrouter", "claude-api"])
        ctl.addWidget(self.provider)
        ctl.addStretch()
        self.btn_launch = QPushButton("🚀 Lanzar")
        self.btn_launch.clicked.connect(self._launch)
        self.btn_launch.setEnabled(bool(self._hermes))
        self.btn_stop = QPushButton("⏹ Detener")
        self.btn_stop.clicked.connect(self._stop)
        self.btn_stop.setEnabled(False)
        ctl.addWidget(self.btn_launch)
        ctl.addWidget(self.btn_stop)
        root.addLayout(ctl)

        if not self._hermes:
            w = QLabel("ℹ️ Operator no activado (opcional). Instala Hermes Agent "
                       "para automatizar proyectos.")
            w.setStyleSheet("color:#7aa2f7;")
            w.setWordWrap(True)
            root.addWidget(w)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet("font-family: monospace; font-size: 11px; "
                               "background:#111; color:#cdd;")
        self.log.setPlaceholderText("La actividad de la misión aparecerá aquí…")
        root.addWidget(self.log, 1)

    def _append(self, text: str):
        self.log.appendPlainText(text.rstrip("\n"))
        sb = self.log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _brief(self) -> str:
        task = self.task.toPlainText().strip()
        return (
            f"Work on the EXISTING Pcreative Studio project '{self._name}' "
            f"(path: {self._path}). Build agent (provider): "
            f"{self.provider.currentText()}. Task: {task}\n\n"
            "Use the pcreative-studio MCP. Locate it with list_recent_projects, work IN "
            "its directory (its AGENTS.md/.hermes.md auto-loads), then run_agent_build "
            "for the task and run_preflight to verify (fix issues, max 3). Do NOT "
            "create a new project. Read/update its .hermes.md with what you did and "
            "learn from it. Report what changed.")

    def _launch(self):
        if not self._hermes:
            return
        if not self.task.toPlainText().strip():
            QMessageBox.information(self, "Operator", "Escribe qué quieres que haga.")
            return
        if self._proc and self._proc.state() != QProcess.ProcessState.NotRunning:
            QMessageBox.information(self, "Operator", "Ya hay una misión en curso.")
            return
        if mission_active():
            QMessageBox.information(self, "Operator",
                                    "Ya hay una misión en curso en otra pestaña/ventana.")
            return
        self.log.clear()
        self._append(f"▶ Automatizando '{self._name}' con el Operator "
                     f"(agente {self.provider.currentText()})…\n")
        self.btn_launch.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self._proc = QProcess(self)
        self._proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._proc.setProcessEnvironment(_mission_env())
        self._proc.readyReadStandardOutput.connect(self._on_output)
        self._proc.finished.connect(self._on_finished)
        self._proc.errorOccurred.connect(self._on_proc_error)
        self._counted = True
        mission_begin()
        self._proc.start(self._hermes, ["chat", "-q", self._brief(),
                                        "-s", OPERATOR_SKILL])

    def _release_mission(self):
        if getattr(self, "_counted", False):
            self._counted = False
            mission_end()

    def _on_proc_error(self, _e):
        self._append("✗ no se pudo ejecutar hermes.")
        self._release_mission()
        self.btn_launch.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def _on_output(self):
        if not self._proc:
            return
        data = bytes(self._proc.readAllStandardOutput()).decode(errors="replace")
        for line in data.splitlines():
            if line.strip():
                self._append(line)

    def _on_finished(self, code: int, _status):
        self._release_mission()
        self._append(f"\n■ Misión terminada (exit {code}).")
        self.btn_launch.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def _stop(self):
        if self._proc and self._proc.state() != QProcess.ProcessState.NotRunning:
            self._proc.kill()
            self._append("\n⏹ Detenida por el usuario.")
        self.btn_launch.setEnabled(True)
        self.btn_stop.setEnabled(False)
