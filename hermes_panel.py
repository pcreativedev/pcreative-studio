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

import json
import os
import socket
import subprocess
from pathlib import Path

from PyQt6.QtCore import Qt, QProcess, QProcessEnvironment, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QPlainTextEdit,
    QSpinBox, QComboBox, QMessageBox, QSplitter, QTabWidget, QFrame,
    QLineEdit, QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QFormLayout, QDialog, QDialogButtonBox,
)

# Reuse the existing, battle-tested widgets + helpers.
from operator_panel import (
    find_hermes, operator_available, _mission_env,
    ProjectPreviewWidget, HermesTerminal, OperatorMissionDialog,
    OPERATOR_SKILL, PROJECTS_DIR,
)

HERMES_HOME = Path.home() / ".hermes"
SKILLS_DIR = HERMES_HOME / "skills"          # raíz de skills (categorías dentro)
TF_SKILLS_DIR = SKILLS_DIR / "themeforge"    # skills creadas desde ThemeForge
MEMORIES_DIR = HERMES_HOME / "memories"
CRON_JOBS = HERMES_HOME / "cron" / "jobs.json"

# Límites de los archivos de memoria de Hermes (se inyectan al system prompt).
MEMORY_LIMITS = {"MEMORY.md": 2200, "USER.md": 1375}


def _hermes_env() -> dict:
    """Entorno con ~/.local/bin en PATH para subprocess (igual que _mission_env)."""
    env = os.environ.copy()
    local_bin = str(Path.home() / ".local" / "bin")
    env["PATH"] = local_bin + os.pathsep + env.get("PATH", "")
    return env


def run_hermes(args: list[str], timeout: int = 25) -> tuple[int, str]:
    """Ejecuta `hermes <args>` y devuelve (returncode, salida combinada).

    Pensado para comandos rápidos (list/status/...). Para operaciones largas
    (dispatch, instalar, redactar con IA) usar QProcess async en su widget.
    """
    exe = find_hermes()
    if not exe:
        return 127, "Hermes no está instalado."
    try:
        r = subprocess.run([exe, *args], capture_output=True, text=True,
                           timeout=timeout, env=_hermes_env())
        return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()
    except subprocess.TimeoutExpired:
        return 124, f"`hermes {' '.join(args)}` excedió {timeout}s."
    except Exception as e:  # noqa: BLE001
        return 1, str(e)


def _parse_frontmatter(text: str) -> dict:
    """Parser mínimo del frontmatter YAML de un SKILL.md (sin dependencias)."""
    out: dict = {}
    if not text.startswith("---"):
        return out
    try:
        end = text.index("\n---", 3)
    except ValueError:
        return out
    indent_key = None
    for raw in text[3:end].splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if not raw.startswith((" ", "\t")) and ":" in raw:
            k, _, v = raw.partition(":")
            indent_key = k.strip()
            v = v.strip()
            if v:
                out[indent_key] = v.strip("\"'")
    return out


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


# ───────────────────────── helpers async ────────────────────────────────
def _spawn_hermes(parent, args, on_line, on_done) -> QProcess | None:
    """Lanza `hermes <args>` en background, stream línea a línea. Devuelve el
    QProcess (o None si Hermes no está)."""
    exe = find_hermes()
    if not exe:
        on_line("✗ Hermes no está instalado.")
        on_done(127)
        return None
    proc = QProcess(parent)
    proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
    proc.setProcessEnvironment(_mission_env())
    proc.readyReadStandardOutput.connect(
        lambda: on_line(bytes(proc.readAllStandardOutput()).decode(errors="replace")))
    proc.finished.connect(lambda code, _s: on_done(code))
    proc.errorOccurred.connect(lambda _e: on_line("✗ no se pudo ejecutar hermes."))
    proc.start(exe, args)
    return proc


def _no_hermes_banner(text: str) -> QLabel:
    info = QLabel(text)
    info.setTextFormat(Qt.TextFormat.RichText)
    info.setWordWrap(True)
    info.setStyleSheet("color:#7aa2f7; background:#1a1a22; padding:8px; "
                       "border-radius:6px;")
    return info


# ───────────────────────── 🤖 Agentes (skills) ──────────────────────────
class AgentsTab(QWidget):
    """Galería de skills/agentes de Hermes. Lista las instaladas en
    `~/.hermes/skills/`, resalta las de ThemeForge, y permite buscar/instalar
    del registro (`hermes skills search/install/inspect`)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hermes = find_hermes()
        self._proc: QProcess | None = None
        root = QVBoxLayout(self)

        bar = QHBoxLayout()
        title = QLabel("🤖 Agentes especializados")
        f = QFont(); f.setPointSize(13); f.setBold(True); title.setFont(f)
        bar.addWidget(title)
        bar.addStretch()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar en el registro (ej: react, shopify)…")
        self.search.returnPressed.connect(self._do_search)
        self.search.setFixedWidth(240)
        bar.addWidget(self.search)
        self.btn_search = QPushButton("🔍 Buscar")
        self.btn_search.clicked.connect(self._do_search)
        bar.addWidget(self.btn_search)
        self.btn_refresh = QPushButton("↻")
        self.btn_refresh.setFixedWidth(32)
        self.btn_refresh.clicked.connect(self.refresh)
        bar.addWidget(self.btn_refresh)
        root.addLayout(bar)

        split = QSplitter(Qt.Orientation.Horizontal)
        self.list = QListWidget()
        self.list.currentItemChanged.connect(self._show_selected)
        split.addWidget(self.list)
        self.detail = QPlainTextEdit()
        self.detail.setReadOnly(True)
        self.detail.setStyleSheet("font-family:monospace; font-size:11px; "
                                  "background:#111; color:#cdd;")
        split.addWidget(self.detail)
        split.setSizes([300, 480])
        root.addWidget(split, 1)

        ctl = QHBoxLayout()
        self.install_id = QLineEdit()
        self.install_id.setPlaceholderText("ID/URL de skill a instalar "
                                           "(ej: official/devops/docker)")
        ctl.addWidget(self.install_id, 1)
        self.btn_install = QPushButton("📥 Instalar")
        self.btn_install.clicked.connect(self._do_install)
        ctl.addWidget(self.btn_install)
        self.btn_use = QPushButton("🚀 Usar en misión")
        self.btn_use.setToolTip("Copia el nombre de la skill para usarla como "
                                "agente en la pestaña 🚀 Misión.")
        self.btn_use.clicked.connect(self._use_in_mission)
        ctl.addWidget(self.btn_use)
        root.addLayout(ctl)

        self.status = QLabel()
        self.status.setStyleSheet("color:#888;")
        root.addWidget(self.status)

        if not self._hermes:
            root.insertWidget(1, _no_hermes_banner(
                "ℹ️ <b>Hermes no instalado</b> (opcional). Las skills viven en "
                "<code>~/.hermes/skills/</code>."))
        self.refresh()

    # ── escaneo de skills locales ──
    def _scan(self) -> list[dict]:
        skills: list[dict] = []
        if not SKILLS_DIR.is_dir():
            return skills
        for md in sorted(SKILLS_DIR.glob("*/*/SKILL.md")) + \
                sorted(SKILLS_DIR.glob("*/SKILL.md")):
            try:
                text = md.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            fm = _parse_frontmatter(text)
            rel = md.relative_to(SKILLS_DIR)
            category = rel.parts[0] if len(rel.parts) >= 2 else "(raíz)"
            skills.append({
                "name": fm.get("name") or md.parent.name,
                "description": fm.get("description", ""),
                "category": fm.get("category") or category,
                "path": str(md),
                "text": text,
                "tf": category == "themeforge",
            })
        return skills

    def refresh(self):
        self.list.clear()
        skills = self._scan()
        for s in skills:
            label = f"{'⭐ ' if s['tf'] else ''}{s['name']}  ·  {s['category']}"
            it = QListWidgetItem(label)
            it.setData(Qt.ItemDataRole.UserRole, s)
            it.setToolTip(s["description"])
            self.list.addItem(it)
        n = len(skills)
        tf = sum(1 for s in skills if s["tf"])
        self.status.setText(
            f"{n} skill(s) instalada(s) · {tf} de ThemeForge ⭐"
            if n else "No hay skills instaladas todavía.")
        if not self.list.currentItem() and n:
            self.list.setCurrentRow(0)

    def _show_selected(self, cur, _prev=None):
        if not cur:
            self.detail.setPlainText("")
            return
        s = cur.data(Qt.ItemDataRole.UserRole)
        if isinstance(s, dict):
            self.detail.setPlainText(s.get("text", ""))

    def _use_in_mission(self):
        cur = self.list.currentItem()
        if not cur:
            return
        s = cur.data(Qt.ItemDataRole.UserRole)
        name = s.get("name") if isinstance(s, dict) else None
        if name:
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(name)
            self.status.setText(f"Copiado «{name}» — pégalo en 🚀 Misión → Agente.")

    # ── registro (async) ──
    def _busy(self, on: bool, msg: str = ""):
        for b in (self.btn_search, self.btn_install):
            b.setEnabled(not on and bool(self._hermes))
        if msg:
            self.status.setText(msg)

    def _do_search(self):
        q = self.search.text().strip()
        if not q or not self._hermes:
            return
        self.detail.setPlainText(f"$ hermes skills search {q}\n")
        self._busy(True, f"Buscando «{q}» en el registro…")
        self._proc = _spawn_hermes(
            self, ["skills", "search", q],
            lambda t: self.detail.appendPlainText(t.rstrip()),
            lambda code: self._busy(False, "Búsqueda terminada. Copia un ID al "
                                    "campo de instalar."))

    def _do_install(self):
        sid = self.install_id.text().strip()
        if not sid or not self._hermes:
            return
        self.detail.setPlainText(f"$ hermes skills install {sid}\n")
        self._busy(True, f"Instalando {sid}…")

        def done(code):
            self._busy(False, "Instalada ✓" if code == 0 else f"Falló (exit {code}).")
            self.refresh()
        self._proc = _spawn_hermes(
            self, ["skills", "install", sid],
            lambda t: self.detail.appendPlainText(t.rstrip()), done)

    def set_powered(self, on: bool):
        for b in (self.btn_search, self.btn_install):
            b.setEnabled(bool(self._hermes) and on)


# ───────────────────────── ➕ Crear agente (SKILL.md) ────────────────────
_SKILL_TEMPLATE = """---
name: {name}
description: {desc}
version: 1.0.0
metadata:
  hermes:
    category: themeforge
    tags: [{tags}]
---

# {title}

## Cuándo usar
{desc}

## Stacks base
{stacks}

## Procedimiento
1. Lee el contexto del proyecto (CLAUDE.md/AGENTS.md) y la referencia si la hay.
2. Sigue el skill `themeforge-operator` para crear/construir/QA/empaquetar.
3. Aplica las convenciones del/los stack(s) de arriba.

## Verificación
- Cumple el checklist Envato (§B) del proyecto.
- Lighthouse/accesibilidad según el formato del stack.
"""


class CreateAgentTab(QWidget):
    """Crea una skill/agente propio: form → SKILL.md (opción de redactarlo con
    IA vía `hermes -z`) → guarda en `~/.hermes/skills/themeforge/<name>/`."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hermes = find_hermes()
        self._proc: QProcess | None = None
        root = QVBoxLayout(self)

        title = QLabel("➕ Crear agente especializado")
        f = QFont(); f.setPointSize(13); f.setBold(True); title.setFont(f)
        root.addWidget(title)
        sub = QLabel("Define un agente reutilizable. Se guarda como skill de "
                     "Hermes y aparece en 🤖 Agentes y como <code>/&lt;nombre&gt;</code>.")
        sub.setTextFormat(Qt.TextFormat.RichText); sub.setWordWrap(True)
        sub.setStyleSheet("color:#9aa;")
        root.addWidget(sub)

        form = QFormLayout()
        self.in_name = QLineEdit(); self.in_name.setPlaceholderText("shopify-pro")
        self.in_stacks = QLineEdit()
        self.in_stacks.setPlaceholderText("shopify-liquid, hydrogen, …")
        self.in_desc = QLineEdit()
        self.in_desc.setPlaceholderText("Especialidad: qué hace este agente y cuándo usarlo.")
        form.addRow("Nombre:", self.in_name)
        form.addRow("Stacks base:", self.in_stacks)
        form.addRow("Especialidad:", self.in_desc)
        root.addLayout(form)

        ctl = QHBoxLayout()
        self.btn_template = QPushButton("📄 Plantilla")
        self.btn_template.clicked.connect(self._fill_template)
        ctl.addWidget(self.btn_template)
        self.btn_ai = QPushButton("✍️ Redactar con IA")
        self.btn_ai.setToolTip("Hermes redacta el SKILL.md a partir del form (hermes -z).")
        self.btn_ai.clicked.connect(self._draft_ai)
        self.btn_ai.setEnabled(bool(self._hermes))
        ctl.addWidget(self.btn_ai)
        ctl.addStretch()
        self.btn_save = QPushButton("💾 Guardar skill")
        self.btn_save.clicked.connect(self._save)
        ctl.addWidget(self.btn_save)
        root.addLayout(ctl)

        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("El SKILL.md aparecerá aquí (editable)…")
        self.editor.setStyleSheet("font-family:monospace; font-size:12px; "
                                  "background:#111; color:#cdd;")
        root.addWidget(self.editor, 1)

        self.status = QLabel(); self.status.setStyleSheet("color:#888;")
        root.addWidget(self.status)

    def _fill_template(self):
        name = (self.in_name.text().strip() or "mi-agente").lower().replace(" ", "-")
        stacks = self.in_stacks.text().strip() or "—"
        desc = self.in_desc.text().strip() or "Agente especializado de ThemeForge."
        tags = ", ".join(t.strip() for t in self.in_stacks.text().split(",") if t.strip())
        self.editor.setPlainText(_SKILL_TEMPLATE.format(
            name=name, desc=desc, title=name.replace("-", " ").title(),
            stacks=stacks, tags=tags or "themeforge"))
        self.status.setText("Plantilla lista. Edítala o pulsa 💾 Guardar.")

    def _draft_ai(self):
        if not self._hermes:
            return
        name = self.in_name.text().strip()
        desc = self.in_desc.text().strip()
        if not name or not desc:
            QMessageBox.information(self, "Crear agente",
                                    "Pon al menos nombre y especialidad.")
            return
        stacks = self.in_stacks.text().strip()
        prompt = (
            "Write a Hermes SKILL.md for a ThemeForge specialized agent. Output ONLY "
            "the file content (YAML frontmatter + markdown), no commentary. "
            f"name: {name}. category: themeforge. Base stacks: {stacks or 'any web'}. "
            f"Specialty: {desc}. Include sections: When to use, Procedure, Pitfalls, "
            "Verification (Envato checklist + Lighthouse). Keep it concise and practical.")
        self.editor.setPlainText("✍️ Redactando con IA… (hermes -z)\n")
        self.btn_ai.setEnabled(False)
        self.status.setText("Hermes está redactando el SKILL.md…")
        buf: list[str] = []

        def line(t):
            buf.append(t)
            self.editor.setPlainText("".join(buf))

        def done(code):
            self.btn_ai.setEnabled(True)
            self.status.setText("Borrador listo ✓ Revísalo y pulsa 💾 Guardar."
                                if code == 0 else f"IA falló (exit {code}).")
        self._proc = _spawn_hermes(self, ["-z", prompt], line, done)

    def _save(self):
        name = self.in_name.text().strip().lower().replace(" ", "-")
        body = self.editor.toPlainText().strip()
        if not name:
            QMessageBox.information(self, "Crear agente", "Falta el nombre.")
            return
        if not body:
            self._fill_template()
            body = self.editor.toPlainText().strip()
        dest = TF_SKILLS_DIR / name
        try:
            dest.mkdir(parents=True, exist_ok=True)
            (dest / "SKILL.md").write_text(body + "\n", encoding="utf-8")
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(self, "Crear agente", f"No se pudo guardar:\n{e}")
            return
        self.status.setText(f"✓ Guardada en {dest/'SKILL.md'} — visible en 🤖 Agentes.")

    def set_powered(self, on: bool):
        self.btn_ai.setEnabled(bool(self._hermes) and on)


# ───────────────────────── 🧠 Memoria ───────────────────────────────────
class _MemoryFileEditor(QWidget):
    """Editor de un archivo de memoria con contador de caracteres y guardado."""

    def __init__(self, filename: str, limit: int, parent=None):
        super().__init__(parent)
        self.path = MEMORIES_DIR / filename
        self.limit = limit
        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0)
        head = QHBoxLayout()
        head.addWidget(QLabel(f"<b>{filename}</b>"))
        head.addStretch()
        self.counter = QLabel()
        head.addWidget(self.counter)
        self.btn_save = QPushButton("💾 Guardar")
        self.btn_save.clicked.connect(self.save)
        head.addWidget(self.btn_save)
        root.addLayout(head)
        self.edit = QPlainTextEdit()
        self.edit.setStyleSheet("font-family:monospace; font-size:12px; "
                                "background:#111; color:#cdd;")
        self.edit.textChanged.connect(self._count)
        root.addWidget(self.edit, 1)
        self.reload()

    def reload(self):
        try:
            self.edit.setPlainText(self.path.read_text(encoding="utf-8")
                                   if self.path.is_file() else "")
        except Exception:
            self.edit.setPlainText("")
        self._count()

    def _count(self):
        n = len(self.edit.toPlainText())
        over = n > self.limit
        self.counter.setText(f"<span style='color:{'#f85149' if over else '#888'}'>"
                             f"{n}/{self.limit}</span>")
        self.counter.setTextFormat(Qt.TextFormat.RichText)

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(self.edit.toPlainText(), encoding="utf-8")
            self.btn_save.setText("✓ Guardado")
            QTimer.singleShot(1500, lambda: self.btn_save.setText("💾 Guardar"))
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(self, "Memoria", f"No se pudo guardar:\n{e}")


class MemoryTab(QWidget):
    """Lo que Hermes recuerda: MEMORY.md (notas del agente) + USER.md (perfil),
    notas por proyecto (.hermes.md) y estadísticas de sesiones."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hermes = find_hermes()
        root = QVBoxLayout(self)
        bar = QHBoxLayout()
        title = QLabel("🧠 Memoria de Hermes")
        f = QFont(); f.setPointSize(13); f.setBold(True); title.setFont(f)
        bar.addWidget(title); bar.addStretch()
        self.btn_reload = QPushButton("↻ Recargar")
        self.btn_reload.clicked.connect(self.reload_all)
        bar.addWidget(self.btn_reload)
        root.addLayout(bar)

        split = QSplitter(Qt.Orientation.Horizontal)
        mem = QWidget(); ml = QVBoxLayout(mem); ml.setContentsMargins(0, 0, 0, 0)
        self.mem_editor = _MemoryFileEditor("MEMORY.md", MEMORY_LIMITS["MEMORY.md"])
        self.user_editor = _MemoryFileEditor("USER.md", MEMORY_LIMITS["USER.md"])
        msplit = QSplitter(Qt.Orientation.Vertical)
        msplit.addWidget(self.mem_editor); msplit.addWidget(self.user_editor)
        ml.addWidget(msplit)
        split.addWidget(mem)

        right = QWidget(); rl = QVBoxLayout(right); rl.setContentsMargins(0, 0, 0, 0)
        rl.addWidget(QLabel("<b>Notas por proyecto</b> (.hermes.md)"))
        self.proj_list = QListWidget()
        self.proj_list.currentItemChanged.connect(self._show_proj)
        rl.addWidget(self.proj_list, 1)
        self.proj_view = QPlainTextEdit(); self.proj_view.setReadOnly(True)
        self.proj_view.setStyleSheet("font-family:monospace; font-size:11px; "
                                     "background:#111; color:#cdd;")
        rl.addWidget(self.proj_view, 1)
        rl.addWidget(QLabel("<b>Sesiones</b>"))
        self.sessions = QPlainTextEdit(); self.sessions.setReadOnly(True)
        self.sessions.setMaximumHeight(120)
        self.sessions.setStyleSheet("font-family:monospace; font-size:11px; "
                                    "background:#111; color:#9aa;")
        rl.addWidget(self.sessions)
        split.addWidget(right)
        split.setSizes([460, 380])
        root.addWidget(split, 1)

        if not self._hermes:
            root.insertWidget(1, _no_hermes_banner(
                "ℹ️ Hermes no instalado. La memoria vive en "
                "<code>~/.hermes/memories/</code>."))
        self.reload_all()

    def reload_all(self):
        self.mem_editor.reload()
        self.user_editor.reload()
        self.proj_list.clear()
        try:
            for hm in sorted(PROJECTS_DIR.glob("*/.hermes.md")):
                it = QListWidgetItem(f"📁 {hm.parent.name}")
                it.setData(Qt.ItemDataRole.UserRole, str(hm))
                self.proj_list.addItem(it)
        except Exception:
            pass
        if self.proj_list.count() == 0:
            self.proj_list.addItem("(ningún proyecto con .hermes.md todavía)")
        if self._hermes:
            code, out = run_hermes(["sessions", "stats"], timeout=15)
            self.sessions.setPlainText(out or "(sin datos)")
        else:
            self.sessions.setPlainText("Hermes no instalado.")

    def _show_proj(self, cur, _prev=None):
        if not cur:
            return
        p = cur.data(Qt.ItemDataRole.UserRole)
        if not p:
            self.proj_view.setPlainText("")
            return
        try:
            self.proj_view.setPlainText(Path(p).read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            self.proj_view.setPlainText(str(e))

    def set_powered(self, on: bool):
        pass


# ───────────────────────── 📊 Kanban (hermes kanban) ────────────────────
class KanbanTab(QWidget):
    """Tablero real de Hermes (`hermes kanban`): boards + tareas en paralelo,
    crear, dispatch (workers) y seguimiento."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hermes = find_hermes()
        self._proc: QProcess | None = None
        root = QVBoxLayout(self)

        bar = QHBoxLayout()
        title = QLabel("📊 Kanban")
        f = QFont(); f.setPointSize(13); f.setBold(True); title.setFont(f)
        bar.addWidget(title)
        bar.addWidget(QLabel("Board:"))
        self.boards = QComboBox(); self.boards.setMinimumWidth(160)
        self.boards.currentTextChanged.connect(lambda _t: self.refresh())
        bar.addWidget(self.boards)
        bar.addStretch()
        self.btn_new = QPushButton("➕ Tarea")
        self.btn_new.clicked.connect(self._new_task)
        bar.addWidget(self.btn_new)
        self.btn_dispatch = QPushButton("▶ Dispatch")
        self.btn_dispatch.setToolTip("Lanza un pase: asigna y ejecuta las tareas listas.")
        self.btn_dispatch.clicked.connect(self._dispatch)
        bar.addWidget(self.btn_dispatch)
        self.btn_refresh = QPushButton("↻")
        self.btn_refresh.setFixedWidth(32)
        self.btn_refresh.clicked.connect(self._reload_boards)
        bar.addWidget(self.btn_refresh)
        root.addLayout(bar)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Tarea", "Estado", "Asignado", "Prio"])
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        root.addWidget(self.table, 2)

        self.log = QPlainTextEdit(); self.log.setReadOnly(True)
        self.log.setStyleSheet("font-family:monospace; font-size:11px; "
                               "background:#111; color:#cdd;")
        self.log.setPlaceholderText("Salida de dispatch / kanban…")
        root.addWidget(self.log, 1)

        self.status = QLabel(); self.status.setStyleSheet("color:#888;")
        root.addWidget(self.status)

        if not self._hermes:
            root.insertWidget(1, _no_hermes_banner(
                "ℹ️ Hermes no instalado. El Kanban usa <code>hermes kanban</code>."))
        else:
            self._reload_boards()

    def _reload_boards(self):
        if not self._hermes:
            return
        self.boards.blockSignals(True)
        self.boards.clear()
        code, out = run_hermes(["kanban", "boards", "list", "--json"], timeout=15)
        added = False
        try:
            data = json.loads(out)
            items = data if isinstance(data, list) else data.get("boards", [])
            for b in items:
                slug = b.get("slug") or b.get("id") if isinstance(b, dict) else str(b)
                if slug:
                    self.boards.addItem(slug); added = True
        except Exception:
            # Fallback: salida de texto, una board por línea.
            for ln in out.splitlines():
                s = ln.strip().split()[0] if ln.strip() else ""
                if s and not s.startswith(("#", "-", "•", "No")):
                    self.boards.addItem(s); added = True
        self.boards.blockSignals(False)
        if not added:
            self.status.setText("No hay boards. Crea una tarea para empezar "
                                "(usa el board por defecto).")
        self.refresh()

    def _board_args(self) -> list[str]:
        b = self.boards.currentText().strip()
        return ["--board", b] if b else []

    def refresh(self):
        if not self._hermes:
            return
        self.table.setRowCount(0)
        code, out = run_hermes(["kanban", *self._board_args(), "list", "--json"],
                               timeout=15)
        rows = []
        try:
            data = json.loads(out)
            rows = data if isinstance(data, list) else data.get("tasks", [])
        except Exception:
            self.status.setText("kanban list: salida no-JSON (¿versión antigua?).")
            self.log.setPlainText(out)
            return
        for t in rows:
            if not isinstance(t, dict):
                continue
            r = self.table.rowCount(); self.table.insertRow(r)
            vals = [str(t.get("id", "")), t.get("title", ""), t.get("status", ""),
                    t.get("assignee", "") or "—", str(t.get("priority", "") or "")]
            for c, v in enumerate(vals):
                self.table.setItem(r, c, QTableWidgetItem(v))
        self.status.setText(f"{self.table.rowCount()} tarea(s) en "
                            f"«{self.boards.currentText() or 'default'}».")

    def _new_task(self):
        if not self._hermes:
            return
        dlg = QDialog(self); dlg.setWindowTitle("Nueva tarea de Kanban")
        fl = QFormLayout(dlg)
        title = QLineEdit(); body = QPlainTextEdit(); body.setMaximumHeight(80)
        prio = QComboBox(); prio.addItems(["", "low", "medium", "high", "urgent"])
        skill = QLineEdit(); skill.setPlaceholderText("(opcional) skill a cargar")
        fl.addRow("Título:", title)
        fl.addRow("Detalle:", body)
        fl.addRow("Prioridad:", prio)
        fl.addRow("Skill:", skill)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                              QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(dlg.accept); bb.rejected.connect(dlg.reject)
        fl.addRow(bb)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        t = title.text().strip()
        if not t:
            return
        args = ["kanban", *self._board_args(), "create", t]
        if body.toPlainText().strip():
            args += ["--body", body.toPlainText().strip()]
        if prio.currentText():
            args += ["--priority", prio.currentText()]
        if skill.text().strip():
            args += ["--skill", skill.text().strip()]
        code, out = run_hermes(args, timeout=20)
        self.log.setPlainText(out)
        self.status.setText("Tarea creada ✓" if code == 0 else f"Error (exit {code}).")
        self.refresh()

    def _dispatch(self):
        if not self._hermes:
            return
        self.log.setPlainText("$ hermes kanban dispatch\n")
        self.btn_dispatch.setEnabled(False)
        self.status.setText("Dispatch en curso… (workers ejecutando tareas listas)")

        def done(code):
            self.btn_dispatch.setEnabled(True)
            self.status.setText("Dispatch terminado." if code == 0
                                else f"Dispatch exit {code}.")
            self.refresh()
        self._proc = _spawn_hermes(
            self, ["kanban", *self._board_args(), "dispatch"],
            lambda t: self.log.appendPlainText(t.rstrip()), done)

    def set_powered(self, on: bool):
        for b in (self.btn_new, self.btn_dispatch):
            b.setEnabled(bool(self._hermes) and on)
        if on and self._hermes:
            self._reload_boards()


# ───────────────────────── ⏰ Cron ──────────────────────────────────────
class CronTab(QWidget):
    """Misiones programadas (`hermes cron`): tabla de jobs (jobs.json), crear,
    pausar/reanudar/ejecutar/eliminar."""

    DELIVER = ["local", "origin", "telegram", "discord", "slack", "email", "all"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hermes = find_hermes()
        root = QVBoxLayout(self)

        bar = QHBoxLayout()
        title = QLabel("⏰ Cron")
        f = QFont(); f.setPointSize(13); f.setBold(True); title.setFont(f)
        bar.addWidget(title); bar.addStretch()
        self.btn_refresh = QPushButton("↻")
        self.btn_refresh.setFixedWidth(32)
        self.btn_refresh.clicked.connect(self.refresh)
        bar.addWidget(self.btn_refresh)
        root.addLayout(bar)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Nombre/ID", "Schedule", "Prompt", "Estado", "Próx."])
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        root.addWidget(self.table, 2)

        ops = QHBoxLayout()
        for label, slot in (("⏸ Pausar", "pause"), ("▶ Reanudar", "resume"),
                            ("⚡ Ejecutar", "run"), ("🗑 Eliminar", "remove")):
            b = QPushButton(label)
            b.clicked.connect(lambda _c=False, s=slot: self._op(s))
            ops.addWidget(b)
        ops.addStretch()
        root.addLayout(ops)

        # Crear
        box = QFrame(); box.setFrameShape(QFrame.Shape.StyledPanel)
        bl = QVBoxLayout(box)
        bl.addWidget(QLabel("<b>Programar nueva misión</b>"))
        form = QFormLayout()
        self.in_sched = QLineEdit()
        self.in_sched.setPlaceholderText("every 1d · 30m · 0 9 * * 1-5 · 2026-06-01T09:00")
        self.in_prompt = QPlainTextEdit(); self.in_prompt.setMaximumHeight(60)
        self.in_prompt.setPlaceholderText("Ej: genera una landing del nicho top de la "
                                          "semana y mándame el zip.")
        self.in_skill = QLineEdit()
        self.in_skill.setPlaceholderText("(opcional) skill, ej: themeforge-operator")
        self.in_deliver = QComboBox(); self.in_deliver.addItems(self.DELIVER)
        self.in_name = QLineEdit(); self.in_name.setPlaceholderText("(opcional) nombre")
        form.addRow("Cuándo:", self.in_sched)
        form.addRow("Tarea:", self.in_prompt)
        form.addRow("Skill:", self.in_skill)
        form.addRow("Entregar a:", self.in_deliver)
        form.addRow("Nombre:", self.in_name)
        bl.addLayout(form)
        self.btn_create = QPushButton("➕ Programar")
        self.btn_create.clicked.connect(self._create)
        bl.addWidget(self.btn_create)
        root.addWidget(box)

        self.status = QLabel(); self.status.setStyleSheet("color:#888;")
        root.addWidget(self.status)

        if not self._hermes:
            root.insertWidget(1, _no_hermes_banner(
                "ℹ️ Hermes no instalado. Cron usa <code>hermes cron</code> "
                "(jobs en <code>~/.hermes/cron/jobs.json</code>)."))
        self.refresh()

    def _jobs_from_file(self) -> list[dict]:
        if not CRON_JOBS.is_file():
            return []
        try:
            data = json.loads(CRON_JOBS.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return list(data.get("jobs", data.values()))
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def refresh(self):
        self.table.setRowCount(0)
        jobs = self._jobs_from_file()
        for j in jobs:
            if not isinstance(j, dict):
                continue
            r = self.table.rowCount(); self.table.insertRow(r)
            ident = j.get("name") or j.get("id", "")
            prompt = (j.get("prompt") or j.get("task") or "")[:60]
            state = "⏸" if j.get("paused") or j.get("enabled") is False else "▶"
            nxt = str(j.get("next_run") or j.get("next") or "")[:16]
            sched = j.get("schedule") or j.get("cron") or ""
            for c, v in enumerate([str(ident), str(sched), prompt, state, nxt]):
                self.table.setItem(r, c, QTableWidgetItem(v))
        self.status.setText(f"{self.table.rowCount()} job(s) programado(s)."
                            if jobs else "No hay misiones programadas.")

    def _selected_id(self) -> str | None:
        r = self.table.currentRow()
        if r < 0:
            return None
        it = self.table.item(r, 0)
        return it.text() if it else None

    def _op(self, action: str):
        if not self._hermes:
            return
        jid = self._selected_id()
        if not jid:
            self.status.setText("Selecciona un job en la tabla.")
            return
        if action == "remove":
            if QMessageBox.question(self, "Cron", f"¿Eliminar el job «{jid}»?") \
                    != QMessageBox.StandardButton.Yes:
                return
        code, out = run_hermes(["cron", action, jid], timeout=20)
        self.status.setText(f"{action} {jid}: {'ok' if code == 0 else out[:80]}")
        self.refresh()

    def _create(self):
        if not self._hermes:
            return
        sched = self.in_sched.text().strip()
        prompt = self.in_prompt.toPlainText().strip()
        if not sched or not prompt:
            QMessageBox.information(self, "Cron", "Pon al menos cuándo y la tarea.")
            return
        args = ["cron", "create", sched, prompt]
        if self.in_skill.text().strip():
            args += ["--skill", self.in_skill.text().strip()]
        if self.in_deliver.currentText():
            args += ["--deliver", self.in_deliver.currentText()]
        if self.in_name.text().strip():
            args += ["--name", self.in_name.text().strip()]
        code, out = run_hermes(args, timeout=25)
        self.status.setText("Programada ✓" if code == 0 else f"Error: {out[:100]}")
        if code == 0:
            self.in_prompt.clear(); self.in_sched.clear(); self.in_name.clear()
        self.refresh()

    def set_powered(self, on: bool):
        for b in (self.btn_create, self.btn_refresh):
            b.setEnabled(bool(self._hermes) and on or b is self.btn_refresh)
        if on:
            self.refresh()


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
        # Distribuye/actualiza el skill themeforge-operator del repo a ~/.hermes.
        try:
            from hermes_operator_skill import ensure_operator_skill_installed
            ensure_operator_skill_installed()
        except Exception:
            pass
        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)

        self.strip = HermesStatusStrip()
        self.strip.btn_power.clicked.connect(self._toggle_power)
        outer.addWidget(self.strip)

        self.tabs = QTabWidget()
        outer.addWidget(self.tabs, 1)

        self.mission = MissionTab()
        self.agents = AgentsTab()
        self.create = CreateAgentTab()
        self.memory = MemoryTab()
        self.kanban = KanbanTab()
        self.cron = CronTab()
        self.chat = HermesTerminal()
        self.admin = AdminTab()

        self.tabs.addTab(self.mission, "🚀 Misión")
        self.tabs.addTab(self.agents, "🤖 Agentes")
        self.tabs.addTab(self.create, "➕ Crear")
        self.tabs.addTab(self.memory, "🧠 Memoria")
        self.tabs.addTab(self.kanban, "📊 Kanban")
        self.tabs.addTab(self.cron, "⏰ Cron")
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
        for t in (self.mission, self.agents, self.create, self.memory,
                  self.kanban, self.cron, self.admin):
            try:
                t.set_powered(on)
            except Exception:
                pass
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
