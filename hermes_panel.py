"""hermes_panel.py — the **Hermes** tab: an advanced control center where the
user builds marketplace-ready websites/apps with specialized AI agents, creates
new agents, schedules missions, and lets Hermes learn across projects.

This is the Fase-A shell (see docs/HERMES-PANEL-DESIGN.md):

    [ status strip: Hermes vX · MCP themeforge · provider/model ]
    🚀 Misión │ 🤖 Agentes │ ➕ Crear │ 🧠 Memoria │ 📊 Kanban │ ⏰ Cron │ ⚙️ Admin │ 💬 Chat

Most heavy widgets (live preview, embedded Hermes chat, the per-project mission
dialog) are reused from `operator_panel.py`. Tabs not yet implemented show a
"próximamente" placeholder; the shell and the wiring around them are real, so
later phases drop functionality in without restructuring.

Hermes is **fully optional** — if it isn't installed the tab degrades to an
"install Hermes" hint and the rest of ThemeForge works exactly the same.
"""
from __future__ import annotations

import os
import socket
from pathlib import Path

from PyQt6.QtCore import Qt, QProcess, QProcessEnvironment, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QPlainTextEdit,
    QSpinBox, QComboBox, QMessageBox, QSplitter, QTabWidget, QFrame,
)

# Reuse the existing, battle-tested widgets + helpers.
from operator_panel import (
    find_hermes, operator_available, _mission_env,
    ProjectPreviewWidget, HermesTerminal, OperatorMissionDialog,
    OPERATOR_SKILL, PROJECTS_DIR,
)

HERMES_HOME = Path.home() / ".hermes"
SKILLS_DIR = HERMES_HOME / "skills" / "themeforge"


def hermes_available() -> bool:
    """True si Hermes está instalado → la pestaña Hermes (opcional) se muestra."""
    return operator_available()


def hermes_version() -> str | None:
    """Lee la versión de Hermes (best-effort, sin romper si falla)."""
    import subprocess
    exe = find_hermes()
    if not exe:
        return None
    try:
        out = subprocess.run([exe, "--version"], capture_output=True,
                             text=True, timeout=8)
        first = (out.stdout or out.stderr).splitlines()[0].strip()
        # "Hermes Agent v0.15.0 (2026.5.28)" → "v0.15.0"
        for tok in first.split():
            if tok.startswith("v") and tok[1:2].isdigit():
                return tok
        return first or None
    except Exception:
        return None


def _hermes_model_info() -> tuple[str | None, str | None]:
    """(provider, model) desde ~/.hermes/config.yaml — sin dependencias duras."""
    cfg = HERMES_HOME / "config.yaml"
    if not cfg.is_file():
        return None, None
    provider = model = None
    try:
        import yaml  # PyYAML viene con muchas deps; si no está, parseo a mano.
        data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
        m = data.get("model") or {}
        return m.get("provider"), m.get("default")
    except Exception:
        # Fallback ultra-simple por líneas (model: / provider: / default:).
        try:
            in_model = False
            for line in cfg.read_text(encoding="utf-8").splitlines():
                if line.startswith("model:"):
                    in_model = True
                    continue
                if in_model:
                    if line and not line.startswith((" ", "\t")):
                        break
                    s = line.strip()
                    if s.startswith("provider:"):
                        provider = s.split(":", 1)[1].strip()
                    elif s.startswith("default:"):
                        model = s.split(":", 1)[1].strip()
        except Exception:
            pass
    return provider, model


def _mcp_themeforge_registered() -> bool:
    """True si el server MCP `themeforge` está en la config de Hermes."""
    cfg = HERMES_HOME / "config.yaml"
    if not cfg.is_file():
        return False
    try:
        return "themeforge" in cfg.read_text(encoding="utf-8")
    except Exception:
        return False


def _free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


# ───────────────────────── status strip ─────────────────────────────────
class HermesStatusStrip(QFrame):
    """Tira de estado siempre visible: versión de Hermes, MCP themeforge,
    proveedor/modelo activos. Cada chip verde/ámbar/rojo."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            "QFrame { background:#15151c; border:1px solid #262633; "
            "border-radius:8px; } QLabel { padding:2px 4px; }"
        )
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        # Botón maestro de encendido/apagado: el usuario decide si usar Hermes
        # y cuándo. La señal la maneja HermesPanel.
        self.btn_power = QPushButton("⏻ Encender Hermes")
        self.btn_power.setCheckable(True)
        self.btn_power.setToolTip("Arrancar / parar Hermes. Apagado no consume "
                                  "nada ni hace llamadas a la IA.")
        lay.addWidget(self.btn_power)
        sep = QLabel("│"); sep.setStyleSheet("color:#333;")
        lay.addWidget(sep)
        self.lbl_hermes = QLabel()
        self.lbl_mcp = QLabel()
        self.lbl_model = QLabel()
        for w in (self.lbl_hermes, self.lbl_mcp, self.lbl_model):
            w.setTextFormat(Qt.TextFormat.RichText)
            lay.addWidget(w)
        lay.addStretch()
        self.btn_refresh = QPushButton("↻")
        self.btn_refresh.setFixedWidth(30)
        self.btn_refresh.setToolTip("Refrescar estado")
        self.btn_refresh.clicked.connect(self.refresh)
        lay.addWidget(self.btn_refresh)
        self.refresh()
        self.set_powered(False)

    def set_powered(self, on: bool):
        """Refleja el estado encendido/apagado en el botón maestro."""
        self.btn_power.setChecked(on)
        if on:
            self.btn_power.setText("⏻ Apagar Hermes")
            self.btn_power.setStyleSheet(
                "QPushButton { background:#1f3a24; color:#3fb950; "
                "border:1px solid #2ea043; border-radius:6px; padding:4px 10px; }")
        else:
            self.btn_power.setText("⏻ Encender Hermes")
            self.btn_power.setStyleSheet(
                "QPushButton { background:#3a1f24; color:#f85149; "
                "border:1px solid #b62324; border-radius:6px; padding:4px 10px; }")

    @staticmethod
    def _chip(ok: bool | None, label: str) -> str:
        color = "#888" if ok is None else ("#3fb950" if ok else "#f85149")
        dot = "●"
        return f"<span style='color:{color}'>{dot}</span> {label}"

    def refresh(self):
        ver = hermes_version()
        self.lbl_hermes.setText(self._chip(
            bool(ver), f"Hermes {ver}" if ver else "Hermes no instalado"))
        mcp = _mcp_themeforge_registered()
        self.lbl_mcp.setText(self._chip(
            mcp, "MCP themeforge" if mcp else "MCP themeforge sin registrar"))
        prov, model = _hermes_model_info()
        if prov or model:
            self.lbl_model.setText(self._chip(
                True, f"{prov or '?'} · {model or '?'}"))
        else:
            self.lbl_model.setText(self._chip(None, "modelo sin configurar"))


# ───────────────────────── 🚀 Misión ────────────────────────────────────
_PHASES = ["Plan", "Crear", "Build", "QA", "Empaquetar"]
# Marcadores en el stdout de Hermes → índice de fase alcanzada.
_PHASE_MARKERS = [
    ("plan", 0),
    ("create_project", 1), ("scaffold", 1), ("creando", 1),
    ("run_agent_build", 2), ("building", 2), ("build agent", 2),
    ("run_preflight", 3), ("preflight", 3), ("qa", 3),
    ("build_zip", 4), ("packaged", 4), (".zip", 4),
]


class MissionTab(QWidget):
    """Lanzar una misión one-shot: brief → Hermes planifica y construye →
    preview en vivo. Versión independiente (el Chat es ahora un tab aparte)."""

    SKILL = OPERATOR_SKILL

    def __init__(self, parent=None):
        super().__init__(parent)
        self._proc: QProcess | None = None
        self._hermes = find_hermes()
        self._phase = -1

        outer = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        outer.addWidget(splitter, 1)

        left = QWidget()
        root = QVBoxLayout(left)
        splitter.addWidget(left)
        self.preview = ProjectPreviewWidget()
        splitter.addWidget(self.preview)
        splitter.setSizes([560, 520])

        title = QLabel("🚀 Misión")
        f = QFont(); f.setPointSize(14); f.setBold(True)
        title.setFont(f)
        root.addWidget(title)
        sub = QLabel(
            "Describe una misión y Hermes la construye sola: plan → crear → "
            "build → QA → empaquetar. Con ≥2 variantes, cada una recibe un "
            "estilo UI/UX Pro Max distinto.")
        sub.setWordWrap(True)
        sub.setStyleSheet("color:#9aa;")
        root.addWidget(sub)

        if not self._hermes:
            info = QLabel(
                "ℹ️ <b>Hermes no activado</b> (opcional). Instálalo desde "
                "Settings → 🔧 Setup dependencies para habilitar las misiones "
                "autónomas. El resto de ThemeForge funciona igual.")
            info.setTextFormat(Qt.TextFormat.RichText)
            info.setStyleSheet("color:#7aa2f7; background:#1a1a22; "
                               "padding:8px; border-radius:6px;")
            info.setWordWrap(True)
            root.addWidget(info)

        root.addWidget(QLabel("Brief de la misión:"))
        self.brief = QPlainTextEdit()
        self.brief.setPlaceholderText(
            "Ej: 2 variantes Envato-ready de landing para clínica dental, "
            "stack Astro+Tailwind, paletas distintas, demo data completa.")
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
        self.provider.addItems(["codex", "opencode", "claude-api", "gemini"])
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

        self.phase_lbl = QLabel()
        self.phase_lbl.setTextFormat(Qt.TextFormat.RichText)
        self._render_phase()
        root.addWidget(self.phase_lbl)

        self.status = QLabel("Listo." if self._hermes else "Hermes no disponible.")
        self.status.setStyleSheet("color:#888;")
        root.addWidget(self.status)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet("font-family: monospace; font-size: 11px; "
                               "background:#111; color:#cdd;")
        self.log.setPlaceholderText("La actividad de la misión aparecerá aquí…")
        root.addWidget(self.log, 1)

    # ── phase indicator ──
    def _render_phase(self):
        parts = []
        for i, name in enumerate(_PHASES):
            if i < self._phase:
                parts.append(f"<span style='color:#3fb950'>✓ {name}</span>")
            elif i == self._phase:
                parts.append(f"<span style='color:#e3b341'>● {name}</span>")
            else:
                parts.append(f"<span style='color:#666'>○ {name}</span>")
        self.phase_lbl.setText("Fase:  " + "  →  ".join(parts))

    def _bump_phase(self, line: str):
        low = line.lower()
        for marker, idx in _PHASE_MARKERS:
            if marker in low and idx > self._phase:
                self._phase = idx
                self._render_phase()

    # ── helpers ──
    def _append(self, text: str):
        self.log.appendPlainText(text.rstrip("\n"))
        sb = self.log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _build_prompt(self) -> str:
        brief = self.brief.toPlainText().strip()
        n = self.variants.value()
        prov = self.provider.currentText()
        return (
            f"Run a ThemeForge Operator mission. Build agent (provider): {prov}. "
            f"Number of variants: {n}. Mission brief: {brief}\n\n"
            "Use the themeforge MCP tools and follow the themeforge-operator skill: "
            "plan with a DISTINCT UI/UX Pro Max style+palette per variant, then for "
            "each variant call create_project (run_autoskills=true, run_uipro=true), "
            "run_agent_build with a detailed prompt (sections + complete demo data + "
            "Unsplash/Pixabay images, Envato-ready), run_preflight in a QA loop "
            "(max 3 fixes), and build_zip. For multiple variants dispatch parallel "
            "delegate_task subagents. Report each variant: path, style, QA result, zip.")

    # ── run / stop ──
    def _launch(self):
        if not self._hermes:
            return
        if not self.brief.toPlainText().strip():
            QMessageBox.information(self, "Hermes", "Escribe un brief para la misión.")
            return
        if self._proc and self._proc.state() != QProcess.ProcessState.NotRunning:
            QMessageBox.information(self, "Hermes", "Ya hay una misión en curso.")
            return
        self.log.clear()
        self._phase = 0
        self._render_phase()
        self._append(
            f"▶ Lanzando misión ({self.variants.value()} variante/s, "
            f"agente {self.provider.currentText()})…\n"
            "(Hermes planifica y orquesta; esto puede tardar varios minutos.)\n")
        self.status.setText("Misión en curso…")
        self.btn_launch.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self._proc = QProcess(self)
        self._proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._proc.setProcessEnvironment(_mission_env())
        self._proc.readyReadStandardOutput.connect(self._on_output)
        self._proc.finished.connect(self._on_finished)
        self._proc.errorOccurred.connect(
            lambda _e: self._append("✗ no se pudo ejecutar hermes."))
        self._proc.start(self._hermes, ["chat", "-q", self._build_prompt(),
                                        "-s", self.SKILL])

    def _on_output(self):
        if not self._proc:
            return
        data = bytes(self._proc.readAllStandardOutput()).decode(errors="replace")
        for line in data.splitlines():
            if line.strip():
                self._append(line)
                self._bump_phase(line)

    def _on_finished(self, code: int, _status):
        self._phase = len(_PHASES)
        self._render_phase()
        self._append(f"\n■ Misión terminada (exit {code}).")
        self.status.setText(f"Terminada (exit {code}).")
        self.btn_launch.setEnabled(True)
        self.btn_stop.setEnabled(False)
        try:
            if PROJECTS_DIR.is_dir():
                projs = [p for p in PROJECTS_DIR.iterdir()
                         if p.is_dir() and not p.name.startswith(".")]
                if projs:
                    newest = max(projs, key=lambda p: p.stat().st_mtime)
                    self.preview.set_project(newest)
                    self._append(f"→ Preview listo para '{newest.name}'. Pulsa "
                                 "▶ Preview, o ve a 💬 Chat para seguir.")
        except Exception:
            pass

    def _stop(self):
        if self._proc and self._proc.state() != QProcess.ProcessState.NotRunning:
            self._proc.kill()
            self._append("\n⏹ Misión detenida por el usuario.")
        self.btn_launch.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def set_powered(self, on: bool):
        """Encendido/apagado maestro: al apagar, detiene la misión en curso y
        bloquea el lanzamiento."""
        if not on:
            self._stop()
        self.btn_launch.setEnabled(bool(self._hermes) and on)
        if not on:
            self.status.setText("Hermes apagado.")
        elif self._hermes:
            self.status.setText("Listo.")


# ───────────────────────── ⚙️ Admin (dashboard embebido) ─────────────────
class AdminTab(QWidget):
    """Embebe el dashboard web nativo de Hermes (`hermes dashboard --tui`):
    Status (sesiones/salud), Config (editor schema-driven), Env (API keys) y
    un Chat embebido. Arranca un proceso local en 127.0.0.1:<puerto libre> y
    lo carga en un QWebEngineView."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hermes = find_hermes()
        self._proc: QProcess | None = None
        self._port: int | None = None
        self._tries = 0

        root = QVBoxLayout(self)
        bar = QHBoxLayout()
        self.lbl = QLabel("⚙️ Admin — dashboard de Hermes")
        self.lbl.setWordWrap(True)
        bar.addWidget(self.lbl, 1)
        self.btn_start = QPushButton("▶ Abrir panel")
        self.btn_start.clicked.connect(self.start)
        self.btn_start.setEnabled(bool(self._hermes))
        self.btn_stop = QPushButton("⏹ Cerrar")
        self.btn_stop.clicked.connect(self.stop)
        self.btn_stop.setEnabled(False)
        self.btn_reload = QPushButton("⟳")
        self.btn_reload.clicked.connect(self._reload)
        for b in (self.btn_start, self.btn_stop, self.btn_reload):
            bar.addWidget(b)
        root.addLayout(bar)

        self._web = None
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            self._web = QWebEngineView()
            self._web.setHtml(
                "<body style='background:#0c0c0d;color:#888;font:13px sans-serif;"
                "padding:1.5em'>Pulsa <b>▶ Abrir panel</b> para iniciar el "
                "dashboard de Hermes (Status · Config · API keys · Chat).</body>")
            root.addWidget(self._web, 1)
        except Exception as e:
            root.addWidget(QLabel(f"Panel no disponible (QtWebEngine): {e}"), 1)

        if not self._hermes:
            self.lbl.setText("⚙️ Admin — instala Hermes (opcional) para el "
                             "panel de administración.")

    def start(self):
        if not self._hermes or not self._web:
            return
        if self._proc and self._proc.state() != QProcess.ProcessState.NotRunning:
            self._load()
            return
        self._port = _free_port()
        self._proc = QProcess(self)
        self._proc.setProcessEnvironment(_mission_env())
        self._proc.start(self._hermes, [
            "dashboard", "--tui", "--no-open", "--skip-build",
            "--host", "127.0.0.1", "--port", str(self._port)])
        self.lbl.setText(f"⚙️ Admin — iniciando dashboard en :{self._port}…")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self._tries = 0
        QTimer.singleShot(2500, self._try_load)

    def _try_load(self):
        """Reintenta cargar hasta que el dashboard responda (sin bloquear UI)."""
        self._tries += 1
        if self._port and self._is_up(self._port):
            self._load()
        elif self._tries < 12:
            QTimer.singleShot(1200, self._try_load)
        else:
            self.lbl.setText("⚙️ Admin — el dashboard no respondió. Pulsa ⟳ "
                             "para reintentar.")

    @staticmethod
    def _is_up(port: int) -> bool:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        except OSError:
            return False

    def _load(self):
        from PyQt6.QtCore import QUrl
        if self._web and self._port:
            self._web.setUrl(QUrl(f"http://127.0.0.1:{self._port}/"))
            self.lbl.setText(f"⚙️ Admin — dashboard en http://127.0.0.1:{self._port}/")

    def _reload(self):
        if self._web and self._port and self._is_up(self._port):
            self._web.reload()
        else:
            self.start()

    def stop(self):
        import subprocess
        from PyQt6.QtCore import QUrl
        if self._proc and self._proc.state() != QProcess.ProcessState.NotRunning:
            self._proc.kill()
        # Limpia cualquier proceso dashboard remanente.
        try:
            subprocess.run([self._hermes, "dashboard", "--stop"],
                           capture_output=True, timeout=8)
        except Exception:
            pass
        if self._web:
            self._web.setHtml("<body style='background:#0c0c0d;color:#888;"
                              "font:13px sans-serif;padding:1.5em'>Panel "
                              "detenido.</body>")
        self.btn_start.setEnabled(bool(self._hermes))
        self.btn_stop.setEnabled(False)
        self.lbl.setText("⚙️ Admin — dashboard de Hermes")

    def set_powered(self, on: bool):
        """Al apagar Hermes, cierra el dashboard y bloquea su arranque."""
        if not on:
            self.stop()
        self.btn_start.setEnabled(bool(self._hermes) and on)
        if not on:
            self.lbl.setText("⚙️ Admin — Hermes apagado.")


# ───────────────────────── stubs (fases siguientes) ─────────────────────
class _StubTab(QWidget):
    """Placeholder honesto para tabs aún no implementados. Explica qué hará."""

    def __init__(self, title: str, what: str, phase: str, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.addStretch()
        t = QLabel(title)
        f = QFont(); f.setPointSize(15); f.setBold(True)
        t.setFont(f)
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(t)
        body = QLabel(what)
        body.setWordWrap(True)
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.setStyleSheet("color:#9aa;")
        body.setMaximumWidth(560)
        wrap = QHBoxLayout(); wrap.addStretch(); wrap.addWidget(body); wrap.addStretch()
        root.addLayout(wrap)
        tag = QLabel(f"⏳ {phase}")
        tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tag.setStyleSheet("color:#7aa2f7; padding-top:8px;")
        root.addWidget(tag)
        root.addStretch()


# ───────────────────────── el panel completo ────────────────────────────
class HermesPanel(QWidget):
    """Pestaña Hermes — centro de control de agentes de diseño web."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._powered = False
        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)

        self.strip = HermesStatusStrip()
        self.strip.btn_power.clicked.connect(self._toggle_power)
        outer.addWidget(self.strip)

        self.tabs = QTabWidget()
        outer.addWidget(self.tabs, 1)

        self.mission = MissionTab()
        self.chat = HermesTerminal()
        self.admin = AdminTab()

        self.tabs.addTab(self.mission, "🚀 Misión")
        self.tabs.addTab(_StubTab(
            "🤖 Agentes especializados",
            "Galería de agentes (uno por familia de stack): Shopify Liquid, "
            "Hydrogen, WordPress, Magento+Hyvä, Frontend, Mobile… Elige uno "
            "para tu misión, edítalo o mira lo que ha aprendido.",
            "Fase B"), "🤖 Agentes")
        self.tabs.addTab(_StubTab(
            "➕ Crear agente",
            "Crea tu propio agente especializado: nombre + stacks base + "
            "especialidad. Hermes puede redactar el SKILL.md por ti con IA. "
            "Aparecerá en la galería y aprenderá con cada proyecto.",
            "Fase E"), "➕ Crear")
        self.tabs.addTab(_StubTab(
            "🧠 Memoria",
            "Lo que Hermes ha aprendido: memorias globales y las notas por "
            "proyecto (.hermes.md). Cada misión añade aquí lo que funcionó.",
            "Fase H"), "🧠 Memoria")
        self.tabs.addTab(_StubTab(
            "📊 Kanban",
            "Misiones en paralelo (varias variantes a la vez) con workers → "
            "verificador → sintetizador, cada worker aislado en su propio "
            "git worktree. Aquí ves el progreso en tiempo real.",
            "Fase F"), "📊 Kanban")
        self.tabs.addTab(_StubTab(
            "⏰ Cron",
            "Misiones programadas: «cada lunes 9am genera una landing del "
            "nicho top de la semana y mándame el zip por Telegram». Encima "
            "del scheduler nativo de Hermes.",
            "Fase G"), "⏰ Cron")
        self.tabs.addTab(self.admin, "⚙️ Admin")
        self.tabs.addTab(self.chat, "💬 Chat")

        # Arranca APAGADO: el usuario decide si usar Hermes y cuándo.
        self._apply_power(False)

    # ── encendido / apagado maestro ──
    def _toggle_power(self):
        self._apply_power(not self._powered)

    def _apply_power(self, on: bool):
        self._powered = on
        self.strip.set_powered(on)
        self.mission.set_powered(on)
        self.admin.set_powered(on)
        try:
            if on:
                self.chat.relaunch()
            else:
                self.chat.shutdown()
        except Exception:
            pass
        if on:
            self.strip.refresh()

    def closeEvent(self, ev):  # noqa: N802
        try:
            self._apply_power(False)
        except Exception:
            pass
        super().closeEvent(ev)


# Compat: algunos sitios antiguos importan estos nombres.
HermesMissionDialog = OperatorMissionDialog
