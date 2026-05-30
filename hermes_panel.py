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

from PyQt6.QtCore import Qt, QProcess, QProcessEnvironment, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QPlainTextEdit,
    QSpinBox, QComboBox, QMessageBox, QSplitter, QTabWidget, QFrame,
    QLineEdit, QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QFormLayout, QDialog, QDialogButtonBox,
    QCheckBox, QScrollArea, QGridLayout, QToolButton,
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


def _provider_has_auth(provider: str) -> bool:
    """True si el provider tiene credenciales en Hermes (login OAuth o API key).
    Se basa en los encabezados de `hermes auth list` ('<provider> (N credentials):')."""
    if not provider:
        return False
    exe = find_hermes()
    if not exe:
        return False
    try:
        r = subprocess.run([exe, "auth", "list"], capture_output=True, text=True,
                           timeout=12, env=_hermes_env())
        out = (r.stdout or "") + (r.stderr or "")
    except Exception:
        return False
    for ln in out.splitlines():
        s = ln.strip()
        if s.startswith(provider + " ") or s.startswith(provider + "("):
            return True
    return False


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
            # Verde si el provider configurado tiene credenciales (login/API key);
            # ámbar si está configurado pero sin auth todavía.
            authed = _provider_has_auth(prov) if prov else False
            label = f"modelo: {prov or '?'} · {model or '?'}"
            if authed:
                self.lbl_model.setText(self._chip(True, label + "  ✓ activo"))
            else:
                self.lbl_model.setText(self._chip(False, label + "  (sin login/key)"))
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


class StackPickerDialog(QDialog):
    """Modal para elegir stack: agrupado por categoría, con cards clicables +
    buscador. Devuelve `selected_key` y `selected_label`."""

    def __init__(self, current: str = "", parent=None, multi: bool = False,
                 current_keys: list[str] | None = None):
        super().__init__(parent)
        self.multi = multi
        self.setWindowTitle("Elegir stacks" if multi else "Elegir stack")
        self.resize(880, 640)
        self.selected_key = current or ""
        self.selected_label = "Auto — que Hermes elija el stack"
        self.selected_keys: set[str] = set(current_keys or [])
        self._names: dict[str, str] = {}

        root = QVBoxLayout(self)
        head = QHBoxLayout()
        t = QLabel("🧱 Elige el stack")
        f = QFont(); f.setPointSize(13); f.setBold(True); t.setFont(f)
        head.addWidget(t)
        head.addStretch()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Filtrar (ej: astro, shopify, laravel)…")
        self.search.setFixedWidth(280)
        self.search.textChanged.connect(self._filter)
        head.addWidget(self.search)
        root.addLayout(head)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        self._wrap = QWidget(); self._vbox = QVBoxLayout(self._wrap)
        self._vbox.setContentsMargins(4, 4, 4, 4)
        scroll.setWidget(self._wrap)
        root.addWidget(scroll, 1)

        self._cards: list[tuple[str, str, QToolButton]] = []  # (key, search_text, btn)
        self._sections: list[tuple[QLabel, list[QToolButton]]] = []
        self._build()

        if self.multi:
            bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                  QDialogButtonBox.StandardButton.Cancel)
            bb.accepted.connect(self._accept_multi)
            bb.rejected.connect(self.reject)
            root.addWidget(bb)

    def _make_card(self, key: str, title: str, subtitle: str, tip: str) -> QToolButton:
        b = QToolButton()
        b.setText(f"{title}\n{subtitle}")
        b.setToolTip(tip)
        b.setCheckable(True)
        b.setChecked(key == self.selected_key)
        b.setMinimumSize(250, 64)
        b.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setChecked((key in self.selected_keys) if self.multi
                     else (key == self.selected_key))
        b.setStyleSheet(
            "QToolButton { text-align:left; padding:8px 12px; border:1px solid "
            "#2a2a33; border-radius:8px; background:#15151c; color:#cdd; }"
            "QToolButton:hover { border-color:#7aa2f7; background:#1a1a25; }"
            "QToolButton:checked { border-color:#3fb950; background:#16241a; }")
        self._names[key] = title
        b.clicked.connect(lambda _c=False, k=key, lbl=title, bb=b:
                          self._choose(k, lbl, bb))
        return b

    def _add_section(self, title: str, cards: list[tuple]):
        hdr = QLabel(title)
        hf = QFont(); hf.setBold(True); hdr.setFont(hf)
        hdr.setStyleSheet("color:#7aa2f7; padding-top:10px;")
        self._vbox.addWidget(hdr)
        grid_host = QWidget(); grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 0, 0, 0); grid.setSpacing(8)
        btns = []
        for i, (key, title2, subtitle, tip, search) in enumerate(cards):
            b = self._make_card(key, title2, subtitle, tip)
            grid.addWidget(b, i // 3, i % 3)
            self._cards.append((key, search, b))
            btns.append(b)
        self._vbox.addWidget(grid_host)
        self._sections.append((hdr, btns))

    def _build(self):
        # Card "Auto" arriba del todo (solo en modo single).
        if not self.multi:
            self._add_section("Recomendado", [(
                "", "Auto", "Que Hermes sugiera/elija el stack",
                "Hermes analiza el brief/referencia y elige el mejor stack web.",
                "auto recomendado sugerir")])
        try:
            from stacks import STACKS
        except Exception:
            STACKS = {}
        by_cat: dict[str, list] = {}
        for key, v in STACKS.items():
            cat = v.get("category", "Otros")
            if cat == "Sin definir":
                continue
            by_cat.setdefault(cat, []).append((key, v))
        for cat in sorted(by_cat):
            cards = []
            for key, v in sorted(by_cat[cat], key=lambda x: x[1].get("name", x[0])):
                name = v.get("name", key)
                lang = v.get("language", "")
                notes = v.get("notes", "")
                cards.append((key, name, lang or cat,
                              notes or name, f"{name} {key} {lang} {cat}".lower()))
            self._add_section(cat, cards)
        self._vbox.addStretch()

    def _choose(self, key: str, label: str, btn=None):
        if self.multi:
            # Toggle: mantiene el diálogo abierto, confirma con OK.
            if key in self.selected_keys:
                self.selected_keys.discard(key)
            else:
                self.selected_keys.add(key)
            if btn is not None:
                btn.setChecked(key in self.selected_keys)
            return
        self.selected_key = key
        self.selected_label = ("Auto — que Hermes elija el stack" if not key
                               else label)
        self.accept()

    def _accept_multi(self):
        self.selected_label = ", ".join(
            self._names.get(k, k) for k in sorted(self.selected_keys))
        self.accept()

    def selected_csv(self) -> str:
        """Claves seleccionadas separadas por coma (modo multi)."""
        return ", ".join(sorted(self.selected_keys))

    def _filter(self, text: str):
        q = text.strip().lower()
        for hdr, btns in self._sections:
            any_visible = False
            for b in btns:
                # localizar el search_text de este botón
                st = next((s for k, s, bb in self._cards if bb is b), "")
                vis = (q in st) if q else True
                b.setVisible(vis)
                any_visible = any_visible or vis
            hdr.setVisible(any_visible)


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

        # Stack: TODOS los de ThemeForge (Hermes los detecta vía el MCP, aquí
        # el usuario puede fijar uno o dejar que Hermes elija).
        row_stack = QHBoxLayout()
        row_stack.addWidget(QLabel("Stack:"))
        self._stack_key = ""
        self._stack_label = "Auto — que Hermes elija el stack"
        self.btn_stack = QPushButton("🧱  " + self._stack_label)
        self.btn_stack.setMinimumWidth(280)
        self.btn_stack.setStyleSheet("text-align:left; padding:5px 10px;")
        self.btn_stack.clicked.connect(self._pick_stack)
        row_stack.addWidget(self.btn_stack, 1)
        self.cb_research = QCheckBox("🌐 Investigación web")
        self.cb_research.setChecked(True)
        self.cb_research.setToolTip("Hermes estudia tendencias/competencia con "
                                    "web_search/browser antes de diseñar.")
        row_stack.addWidget(self.cb_research)
        self.cb_images = QCheckBox("🎨 Imágenes IA")
        self.cb_images.setChecked(True)
        self.cb_images.setToolTip("Genera assets originales (hero/OG/logos/ilustraciones) "
                                  "con image_generate, además de Unsplash/Pixabay.")
        row_stack.addWidget(self.cb_images)
        self.cb_visualqa = QCheckBox("👁️ QA visual")
        self.cb_visualqa.setChecked(True)
        self.cb_visualqa.setToolTip("Screenshot del preview → vision_analyze → "
                                    "crítica de diseño → fix (loop estético).")
        row_stack.addWidget(self.cb_visualqa)
        self.cb_audit = QCheckBox("🔒 Auditoría")
        self.cb_audit.setChecked(True); self.cb_audit.setEnabled(False)
        self.cb_audit.setToolTip("Auditoría de seguridad/compliance OBLIGATORIA "
                                 "antes de empaquetar (gate no negociable).")
        row_stack.addWidget(self.cb_audit)
        root.addLayout(row_stack)

        # Aviso al terminar (manda resumen al canal de mensajería elegido).
        row_notify = QHBoxLayout()
        self.cb_notify = QCheckBox("🔔 Avisar al acabar a")
        self.cb_notify.setToolTip("Al terminar, envía un aviso por el gateway "
                                  "(requiere plataforma configurada en 📲 Remoto).")
        row_notify.addWidget(self.cb_notify)
        self.in_notify = QLineEdit("telegram")
        self.in_notify.setPlaceholderText("destino: telegram · discord:#ops")
        self.in_notify.setFixedWidth(180)
        row_notify.addWidget(self.in_notify)
        row_notify.addStretch()
        root.addLayout(row_notify)

        ctl = QHBoxLayout()
        ctl.addWidget(QLabel("Variantes:"))
        self.variants = QSpinBox()
        self.variants.setRange(1, 6)
        self.variants.setValue(1)
        ctl.addWidget(self.variants)
        ctl.addWidget(QLabel("Agente build:"))
        self.provider = QComboBox()
        self.provider.addItems(["codex", "opencode", "claude-api", "gemini"])
        self.provider.setToolTip("Agente que ESCRIBE el código (aparte del "
                                 "modelo cerebro de Hermes → pestaña 🔌 Proveedor).")
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

    def _pick_stack(self):
        """Abre el modal de selección de stack (categorías + cards)."""
        dlg = StackPickerDialog(self._stack_key, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._stack_key = dlg.selected_key
            self._stack_label = dlg.selected_label
            self.btn_stack.setText("🧱  " + self._stack_label)

    def _build_prompt(self) -> str:
        brief = self.brief.toPlainText().strip()
        n = self.variants.value()
        prov = self.provider.currentText()
        stack_key = self._stack_key or ""
        stack_line = (f"Target stack: {stack_key} (use it for create_project). "
                      if stack_key else
                      "Stack: not fixed — call suggest_stack/list_stacks and pick the "
                      "best web stack. ")
        research = ("FIRST do design research on the web (web_search + browser): niche "
                    "trends, top ThemeForest/Dribbble/Awwwards references and 2-3 "
                    "competitors → a short design brief that feeds the build prompts. "
                    if self.cb_research.isChecked() else "")
        images = ("Generate ORIGINAL imagery with mcp_themeforge_generate_image "
                  "(Runware): pick a model via mcp_themeforge_list_image_models, then "
                  "create hero/section/OG/logo assets on-brand with each palette and "
                  "reference them in the markup. "
                  if self.cb_images.isChecked() else "")
        visualqa = ("Then a VISUAL QA loop: screenshot_project key routes (desktop + "
                    "mobile) → vision_analyze → fix design issues (max 3 passes), and a "
                    "browser smoke test of the multipage nav. "
                    if self.cb_visualqa.isChecked() else "")
        return (
            f"Run a ThemeForge Operator mission. Build agent (provider): {prov}. "
            f"Number of variants: {n}. {stack_line}Mission brief: {brief}\n\n"
            "Follow the themeforge-operator skill (web/UX-UI specialized). " + research +
            "Plan a MULTIPAGE web template with a DISTINCT UI/UX Pro Max style+palette "
            "per variant; read & follow the skills listed in the project's AGENTS.md. "
            + images +
            "For each variant: create_project (run_autoskills=true, run_uipro=true), "
            "run_agent_build with a detailed prompt (real routes/pages + complete demo "
            "data + real images, Envato-ready), run_preflight in a QA loop (max 3 fixes). "
            + visualqa +
            "THEN the mandatory SECURITY & COMPLIANCE AUDIT (no leaked secrets, npm/"
            "composer audit, no malicious code, asset licenses, XSS/CSRF/SQLi) — only "
            "package with build_zip if the audit passes. For multiple variants dispatch "
            "parallel delegate_task subagents. Report each variant: path, style, QA "
            "result, visual-QA notes, security verdict, zip.")

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
        args = ["chat", "-q", self._build_prompt(), "-s", self.SKILL]
        # Toolsets extra según los toggles (web/browser research, imágenes, visión).
        # Imágenes van por la tool MCP de ThemeForge (Runware), no por el toolset
        # image_gen del Portal de Hermes.
        tsets = ["terminal", "delegation"]
        if self.cb_research.isChecked() or self.cb_visualqa.isChecked():
            tsets += ["web", "browser"]
        if self.cb_visualqa.isChecked():
            tsets.append("vision")
        args += ["-t", ",".join(dict.fromkeys(tsets))]
        self._proc.start(self._hermes, args)

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
        # Aviso por el gateway (Telegram/WhatsApp/…) si está activado.
        if self.cb_notify.isChecked():
            target = self.in_notify.text().strip()
            if target:
                try:
                    proj = ""
                    if PROJECTS_DIR.is_dir():
                        ps = [p for p in PROJECTS_DIR.iterdir() if p.is_dir()
                              and not p.name.startswith(".")]
                        if ps:
                            proj = max(ps, key=lambda p: p.stat().st_mtime).name
                    msg = (f"✅ ThemeForge: misión terminada (exit {code})."
                           + (f" Proyecto: {proj}." if proj else ""))
                    rc, out = run_hermes(["send", "--to", target, msg], timeout=30)
                    self._append(f"🔔 Aviso a «{target}»: "
                                 + ("enviado ✓" if rc == 0 else f"falló ({out[:80]})"))
                except Exception as e:  # noqa: BLE001
                    self._append(f"🔔 Aviso falló: {e}")

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


# ───────────────────────── 🔌 Proveedor (cerebro de Hermes) ─────────────
# El modelo "cerebro" de Hermes se configura aparte de los agentes de build
# (codex/claude-OAuth/…). OJO: Claude para Hermes va SIEMPRE por API key
# (no usa el OAuth de Claude Code que sí usan los agentes de build).
_MODELS_CACHE = HERMES_HOME / "models_dev_cache.json"


_MODEL_BAD = ("embed", "image", "imagine", "video", "tts", "whisper", "audio",
              "rerank", "deep-research", "-ocr", "guard", "-oss")


def _cached_models(keywords: list[str], limit: int = 25) -> list[str]:
    """Lee el catálogo de modelos en vivo de Hermes (~/.hermes/models_dev_cache.json)
    y devuelve ids LIMPIOS de chat de esa familia (gemini/grok/qwen…). Así el combo
    muestra los modelos ACTUALES (p.ej. gemini-3.1-pro) sin hardcodear versiones."""
    try:
        d = json.loads(_MODELS_CACHE.read_text(encoding="utf-8"))
    except Exception:
        return []
    out: set[str] = set()
    for prov in (d.values() if isinstance(d, dict) else []):
        models = prov.get("models") if isinstance(prov, dict) else None
        if isinstance(models, dict):
            for mid in models:
                s = str(mid); low = s.lower()
                if any(c in s for c in ("/", "~", "@", ":")):
                    continue  # descarta ids con prefijo de agregador
                if low.split(".")[0] in ("us", "jp", "eu", "global", "apac"):
                    continue  # descarta prefijos de región (us.anthropic.claude…)
                if any(b in low for b in _MODEL_BAD):
                    continue  # solo modelos de texto/chat
                if any(k in low for k in keywords):
                    out.add(s)
    # Orden inverso: tiende a poner las versiones nuevas (3.x) antes que 2.x.
    return sorted(out, reverse=True)[:limit]


# auth: "api" (API key) u "oauth" (login en el navegador). `key` = provider id de
# Hermes — VERIFICADO contra PROVIDER_REGISTRY y _OAUTH_CAPABLE_PROVIDERS del
# Hermes instalado (2026-05-30): oauth-capables = anthropic, nous, openai-codex,
# xai-oauth, qwen-oauth, google-gemini-cli, minimax-oauth.
# model_keywords: familias para poblar el combo desde el caché de modelos en vivo.
HERMES_PROVIDERS = [
    {"key": "anthropic", "auth": "api", "label": "Anthropic (Claude) · API key",
     "models": ["claude-opus-4-8", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
     "note": "Claude para Hermes requiere API key de Anthropic (no el login de "
             "Claude Code / Pro-Max)."},
    {"key": "openai-codex", "auth": "oauth", "label": "ChatGPT / Codex (OpenAI) · login",
     "models": ["gpt-5.5", "gpt-5.1", "o4"],
     "note": "Login con tu cuenta ChatGPT (OAuth) — no necesita API key."},
    {"key": "google-gemini-cli", "auth": "oauth", "label": "Gemini (Google) · login",
     "models": ["gemini-2.5-pro", "gemini-2.5-flash"],
     "note": "Login con tu cuenta de Google (OAuth, vía Gemini CLI)."},
    {"key": "xai-oauth", "auth": "oauth", "label": "xAI / Grok · login",
     "models": ["grok-4", "grok-4-fast"],
     "note": "Login con tu cuenta de xAI (OAuth)."},
    {"key": "qwen-oauth", "auth": "oauth", "label": "Qwen · login",
     "models": ["qwen3-coder", "qwen3-max"],
     "note": "Login con tu cuenta de Qwen (OAuth)."},
    {"key": "nous", "auth": "oauth", "label": "Nous Portal · login",
     "models": ["hermes-4-405b", "hermes-4-70b"],
     "note": "`hermes setup --portal` o login OAuth — 300+ modelos + tool gateway."},
    {"key": "openrouter", "auth": "api", "label": "OpenRouter (200+ modelos) · API key",
     "models": ["anthropic/claude-opus-4.8", "openai/gpt-5.5",
                "google/gemini-2.5-pro", "deepseek/deepseek-r1"],
     "note": "Un solo API key da acceso a cientos de modelos."},
    {"key": "openai-api", "auth": "api", "label": "OpenAI · API key",
     "models": ["gpt-5.5", "gpt-5.1", "o4"], "note": ""},
    {"key": "gemini", "auth": "api", "label": "Gemini (Google) · API key",
     "models": ["gemini-2.5-pro", "gemini-2.5-flash"],
     "note": "Alternativa por API key (Google AI Studio)."},
    {"key": "opencode-zen", "auth": "api", "label": "OpenCode Zen · API key",
     "models": ["claude-sonnet-4", "gpt-5", "qwen3-coder", "kimi-k2"],
     "note": "Gateway de modelos de OpenCode (opencode.ai/zen, OPENCODE_ZEN_API_KEY). "
             "Endpoint propio — el base_url lo pone Hermes solo."},
    {"key": "opencode-go", "auth": "api", "label": "OpenCode Go (plan) · API key",
     "models": ["glm-4.6", "kimi-k2", "minimax-m2", "qwen3.7"],
     "note": "Plan OpenCode Go (opencode.ai/zen/go, OPENCODE_GO_API_KEY): GLM/Kimi/"
             "MiniMax/Qwen. Endpoint propio."},
]


class ProviderTab(QWidget):
    """Auth y selección del modelo CEREBRO de Hermes — independiente de los
    agentes de build. Envuelve `hermes config set` + `hermes auth add`."""

    model_changed = pyqtSignal()  # emitido al aplicar provider/modelo

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hermes = find_hermes()
        root = QVBoxLayout(self)

        title = QLabel("🔌 Proveedor de Hermes (cerebro)")
        f = QFont(); f.setPointSize(13); f.setBold(True); title.setFont(f)
        root.addWidget(title)
        sub = QLabel(
            "El modelo que <b>razona y orquesta</b> las misiones. Es <b>aparte</b> "
            "de los agentes que escriben el código (codex/claude-OAuth/…). "
            "Ojo: <b>Claude aquí va por API key</b>, no por el login de Claude Code.")
        sub.setTextFormat(Qt.TextFormat.RichText); sub.setWordWrap(True)
        sub.setStyleSheet("color:#9aa;")
        root.addWidget(sub)

        self.current = QLabel()
        self.current.setTextFormat(Qt.TextFormat.RichText)
        self.current.setStyleSheet("background:#15151c; border:1px solid #262633; "
                                   "border-radius:6px; padding:8px;")
        root.addWidget(self.current)

        form = QFormLayout()
        self.cb_provider = QComboBox()
        for p in HERMES_PROVIDERS:
            self.cb_provider.addItem(p["label"], p["key"])
        self.cb_provider.currentIndexChanged.connect(self._provider_changed)
        form.addRow("Proveedor:", self.cb_provider)

        self.cb_model = QComboBox(); self.cb_model.setEditable(True)
        form.addRow("Modelo:", self.cb_model)

        self.in_key = QLineEdit()
        self.in_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.in_key.setPlaceholderText("API key (se guarda en ~/.hermes/.env)")
        form.addRow("API key:", self.in_key)
        root.addLayout(form)

        self.note = QLabel(); self.note.setWordWrap(True)
        self.note.setStyleSheet("color:#7aa2f7;")
        root.addWidget(self.note)

        ctl = QHBoxLayout()
        self.btn_login = QPushButton("🔓 Login (OAuth)")
        self.btn_login.setToolTip("Abre el navegador para iniciar sesión "
                                  "(Gemini/ChatGPT/Copilot/Nous).")
        self.btn_login.clicked.connect(self._login_oauth)
        ctl.addWidget(self.btn_login)
        self.btn_savekey = QPushButton("💾 Guardar API key")
        self.btn_savekey.clicked.connect(self._save_key)
        ctl.addWidget(self.btn_savekey)
        self.btn_apply = QPushButton("✅ Usar este modelo")
        self.btn_apply.clicked.connect(self._apply_model)
        ctl.addWidget(self.btn_apply)
        ctl.addStretch()
        self.btn_test = QPushButton("🧪 Probar")
        self.btn_test.setToolTip("Manda un ping al modelo (hermes -z).")
        self.btn_test.clicked.connect(self._test)
        ctl.addWidget(self.btn_test)
        self.btn_refresh = QPushButton("↻")
        self.btn_refresh.setFixedWidth(32)
        self.btn_refresh.clicked.connect(self.refresh)
        ctl.addWidget(self.btn_refresh)
        root.addLayout(ctl)

        self.log = QPlainTextEdit(); self.log.setReadOnly(True)
        self.log.setStyleSheet("font-family:monospace; font-size:11px; "
                               "background:#111; color:#cdd;")
        root.addWidget(self.log, 1)

        if not self._hermes:
            root.insertWidget(1, _no_hermes_banner(
                "ℹ️ Hermes no instalado. El proveedor se configura en "
                "<code>~/.hermes/config.yaml</code> + <code>.env</code>."))
        self._provider_changed()
        self.refresh()

    def _spec(self) -> dict:
        return HERMES_PROVIDERS[max(0, self.cb_provider.currentIndex())]

    # Solo familias cuyos ids en el caché salen limpios. Claude/OpenAI/Nous usan
    # la lista estática (el caché trae variantes regionales/oss confusas).
    _MODEL_KW = {
        "google-gemini-cli": ["gemini"],
        "gemini": ["gemini"],
        "xai-oauth": ["grok"],
        "qwen-oauth": ["qwen"],
    }

    def _provider_changed(self):
        sp = self._spec()
        self.cb_model.clear()
        # Modelos en vivo del caché de Hermes (siempre actuales); fallback a la
        # lista estática. El combo es editable: puedes escribir cualquier id.
        kws = self._MODEL_KW.get(sp["key"])
        live = _cached_models(kws) if kws else []
        self.cb_model.addItems(live or sp["models"])
        self.note.setText("ℹ️ " + sp["note"] if sp.get("note") else "")
        # Muestra login OAuth o campo de API key según el provider.
        # La configuración de proveedor/auth está SIEMPRE disponible (no depende
        # del interruptor maestro: configuras antes de encender).
        is_oauth = sp.get("auth") == "oauth"
        has = bool(self._hermes)
        self.btn_login.setVisible(is_oauth)
        self.btn_login.setEnabled(has and is_oauth)
        self.in_key.setVisible(not is_oauth)
        self.btn_savekey.setVisible(not is_oauth)
        self.in_key.setEnabled(has and not is_oauth)
        self.btn_savekey.setEnabled(has and not is_oauth)

    def refresh(self):
        prov, model = _hermes_model_info()
        txt = (f"<b>Configurado:</b> {prov or '—'} · {model or '—'} "
               "<span style='color:#888'>(no verifica que la key sea válida)</span>"
               if (prov or model) else "<b>Sin configurar.</b>")
        if self._hermes:
            code, out = run_hermes(["auth", "list"], timeout=12)
            if code == 0 and out:
                first = out.strip().splitlines()[0][:80]
                txt += f"<br><span style='color:#888'>auth pool: {first}</span>"
        self.current.setText(txt)
        # Preselecciona el provider activo si coincide.
        if prov:
            for i, p in enumerate(HERMES_PROVIDERS):
                if p["key"] == prov:
                    self.cb_provider.setCurrentIndex(i); break

    def _save_key(self):
        if not self._hermes:
            return
        key = self.in_key.text().strip()
        if not key:
            QMessageBox.information(self, "Proveedor", "Pega una API key.")
            return
        prov = self._spec()["key"]
        code, out = run_hermes(["auth", "add", prov, "--api-key", key], timeout=20)
        self.in_key.clear()
        self.log.appendPlainText(f"$ hermes auth add {prov} --api-key ****\n{out}")
        self.log.appendPlainText("✓ key guardada" if code == 0 else f"✗ exit {code}")
        self.refresh()

    def _login_oauth(self):
        if not self._hermes:
            return
        prov = self._spec()["key"]
        self.log.appendPlainText(
            f"$ hermes auth add {prov} --type oauth\n"
            "→ Se abrirá el navegador para iniciar sesión. Completa el login ahí…")
        self.btn_login.setEnabled(False)

        def done(code):
            self.btn_login.setEnabled(True)
            self.log.appendPlainText("✓ login OK — pulsa «✅ Usar este modelo»."
                                     if code == 0 else f"✗ login exit {code}")
            self.refresh()
        self._proc = _spawn_hermes(
            self, ["auth", "add", prov, "--type", "oauth"],
            lambda t: self.log.appendPlainText(t.rstrip()), done)

    def _apply_model(self):
        if not self._hermes:
            return
        prov = self._spec()["key"]
        model = self.cb_model.currentText().strip()
        if not model:
            QMessageBox.information(self, "Proveedor", "Elige/escribe un modelo.")
            return
        # base_url: OpenRouter usa el suyo; el resto (OAuth/nativos) debe quedar
        # VACÍO — si se hereda el de OpenRouter, el nuevo provider no funciona.
        base = "https://openrouter.ai/api/v1" if prov == "openrouter" else ""
        c1, o1 = run_hermes(["config", "set", "model.provider", prov], timeout=15)
        c2, o2 = run_hermes(["config", "set", "model.default", model], timeout=15)
        c3, o3 = run_hermes(["config", "set", "model.base_url", base], timeout=15)
        self.log.appendPlainText(
            f"$ hermes config set model.provider {prov}\n{o1}\n"
            f"$ hermes config set model.default {model}\n{o2}\n"
            f"$ hermes config set model.base_url {base or '(vacío)'}\n{o3}")
        ok = c1 == 0 and c2 == 0 and c3 == 0
        self.log.appendPlainText("✓ modelo aplicado" if ok else "✗ revisa la salida")
        self.refresh()
        if ok:
            self.model_changed.emit()  # refresca el chip de arriba

    def _test(self):
        if not self._hermes:
            return
        self.log.appendPlainText("$ hermes -z \"ping: responde OK\"  (probando modelo…)")
        self.btn_test.setEnabled(False)
        buf: list[str] = []

        def line(t): buf.append(t)

        def done(code):
            self.btn_test.setEnabled(True)
            self.log.appendPlainText(("".join(buf).strip() or "(sin respuesta)")
                                     + f"\n■ exit {code}")
        _spawn_hermes(self, ["-z", "ping: responde solo 'OK'"], line, done)

    def set_powered(self, on: bool):
        # La pestaña Proveedor se usa para CONFIGURAR (login/key/modelo): siempre
        # disponible si Hermes está instalado, independientemente del encendido.
        self._powered_on = on
        for b in (self.btn_apply, self.btn_test):
            b.setEnabled(bool(self._hermes))
        self._provider_changed()
        if on:
            self.refresh()


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
        self.cb_webonly = QCheckBox("Solo web/diseño")
        self.cb_webonly.setChecked(True)
        self.cb_webonly.setToolTip("Muestra solo los agentes de ThemeForge "
                                   "(web/UX-UI), no toda la librería de Hermes.")
        self.cb_webonly.stateChanged.connect(lambda _s: self.refresh())
        bar.addWidget(self.cb_webonly)
        bar.addStretch()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar en el registro (ej: react, shopify)…")
        self.search.returnPressed.connect(self._do_search)
        self.search.setFixedWidth(220)
        bar.addWidget(self.search)
        self.btn_search = QPushButton("🔍 Buscar")
        self.btn_search.clicked.connect(self._do_search)
        bar.addWidget(self.btn_search)
        self.btn_seed = QPushButton("🌱 Sembrar agentes web")
        self.btn_seed.setToolTip("(Re)instala el pack de agentes web/UX-UI de ThemeForge.")
        self.btn_seed.clicked.connect(self._seed)
        bar.addWidget(self.btn_seed)
        self.btn_refresh = QPushButton("↻")
        self.btn_refresh.setFixedWidth(32)
        self.btn_refresh.clicked.connect(self.refresh)
        bar.addWidget(self.btn_refresh)
        root.addLayout(bar)

        # Siembra el pack de agentes web la primera vez (idempotente).
        try:
            from hermes_web_agents import seed_web_agents
            seed_web_agents()
        except Exception:
            pass

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
        webonly = self.cb_webonly.isChecked()
        shown = [s for s in skills if s["tf"]] if webonly else skills
        # ThemeForge primero (⭐), luego el resto.
        shown = sorted(shown, key=lambda s: (not s["tf"], s["name"]))
        for s in shown:
            label = f"{'⭐ ' if s['tf'] else ''}{s['name']}  ·  {s['category']}"
            it = QListWidgetItem(label)
            it.setData(Qt.ItemDataRole.UserRole, s)
            it.setToolTip(s["description"])
            self.list.addItem(it)
        tf = sum(1 for s in skills if s["tf"])
        if webonly:
            self.status.setText(
                f"{len(shown)} agente(s) web/diseño de ThemeForge ⭐  "
                f"· desmarca «Solo web/diseño» para ver las {len(skills)} skills de Hermes."
                if shown else "No hay agentes web — pulsa 🌱 Sembrar agentes web.")
        else:
            self.status.setText(f"{len(skills)} skill(s) instalada(s) · {tf} de "
                                "ThemeForge ⭐")
        if not self.list.currentItem() and self.list.count():
            self.list.setCurrentRow(0)

    def _seed(self):
        try:
            from hermes_web_agents import seed_web_agents
            done = seed_web_agents(force=True)
            self.status.setText(f"🌱 {len(done)} agente(s) web (re)instalados."
                                if done else "Agentes web ya al día.")
        except Exception as e:  # noqa: BLE001
            self.status.setText(f"Error sembrando: {e}")
        self.refresh()

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
        # Stacks base: línea editable + botón que abre el modal multi (cards).
        stacks_row = QHBoxLayout(); stacks_row.setContentsMargins(0, 0, 0, 0)
        self.in_stacks = QLineEdit()
        self.in_stacks.setPlaceholderText("shopify-liquid, hydrogen, …")
        stacks_row.addWidget(self.in_stacks, 1)
        self.btn_pick_stacks = QPushButton("📚 Elegir…")
        self.btn_pick_stacks.clicked.connect(self._pick_stacks)
        stacks_row.addWidget(self.btn_pick_stacks)
        stacks_host = QWidget(); stacks_host.setLayout(stacks_row)
        self.in_desc = QLineEdit()
        self.in_desc.setPlaceholderText("Especialidad: qué hace este agente y cuándo usarlo.")
        form.addRow("Nombre:", self.in_name)
        form.addRow("Stacks base:", stacks_host)
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

    def _pick_stacks(self):
        """Modal multi-selección de stacks (categorías + cards) → llena el campo."""
        cur = [s.strip() for s in self.in_stacks.text().split(",") if s.strip()]
        dlg = StackPickerDialog(parent=self, multi=True, current_keys=cur)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.in_stacks.setText(dlg.selected_csv())

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


# ───────────────────────── 🎨 Imágenes (Runware) ────────────────────────
class ImagesTab(QWidget):
    """Selector de modelos de imagen de Runware (cientos, por API key). Categorías
    curadas + búsqueda en vivo (modelSearch) + modelo por defecto + test."""

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        title = QLabel("🎨 Imágenes (Runware)")
        f = QFont(); f.setPointSize(13); f.setBold(True); title.setFont(f)
        root.addWidget(title)
        sub = QLabel("Generación de imágenes por <b>API key</b> (pay-as-you-go, sin "
                     "suscripción). El operator las usa para hero/OG/logos originales.")
        sub.setTextFormat(Qt.TextFormat.RichText); sub.setWordWrap(True)
        sub.setStyleSheet("color:#9aa;")
        root.addWidget(sub)

        # ── API key ──
        krow = QHBoxLayout()
        self.key_status = QLabel(); self.key_status.setTextFormat(Qt.TextFormat.RichText)
        krow.addWidget(self.key_status, 1)
        self.in_key = QLineEdit(); self.in_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.in_key.setPlaceholderText("Runware API key…"); self.in_key.setFixedWidth(220)
        krow.addWidget(self.in_key)
        self.btn_savekey = QPushButton("💾"); self.btn_savekey.setFixedWidth(40)
        self.btn_savekey.setToolTip("Guardar key (keys.json 0600)")
        self.btn_savekey.clicked.connect(self._save_key)
        krow.addWidget(self.btn_savekey)
        root.addLayout(krow)

        # ── Categorías curadas ──
        try:
            import runware_images as ri
            self._ri = ri
        except Exception:
            self._ri = None
        cats = QHBoxLayout(); cats.addWidget(QLabel("Categoría:"))
        if self._ri:
            for c in self._ri.CATEGORIES:
                b = QPushButton(c["label"])
                b.clicked.connect(lambda _x=False, cc=c: self._use_category(cc))
                cats.addWidget(b)
        cats.addStretch()
        root.addLayout(cats)

        # ── Búsqueda ──
        srow = QHBoxLayout()
        self.cb_arch = QComboBox(); self.cb_arch.addItem("Cualquier arquitectura", "")
        if self._ri:
            for a in self._ri.ARCHITECTURES:
                self.cb_arch.addItem(a, a)
        srow.addWidget(self.cb_arch)
        self.in_search = QLineEdit()
        self.in_search.setPlaceholderText("Buscar modelo (ej: flux, realistic, anime)…")
        self.in_search.returnPressed.connect(self._search)
        srow.addWidget(self.in_search, 1)
        self.btn_search = QPushButton("🔍 Buscar")
        self.btn_search.clicked.connect(self._search)
        srow.addWidget(self.btn_search)
        root.addLayout(srow)

        self.results = QListWidget()
        self.results.currentItemChanged.connect(self._sel_changed)
        root.addWidget(self.results, 1)

        drow = QHBoxLayout()
        self.lbl_default = QLabel(); self.lbl_default.setTextFormat(Qt.TextFormat.RichText)
        drow.addWidget(self.lbl_default, 1)
        self.btn_default = QPushButton("✅ Usar como modelo por defecto")
        self.btn_default.clicked.connect(self._set_default)
        self.btn_default.setEnabled(False)
        drow.addWidget(self.btn_default)
        root.addLayout(drow)

        # ── Test ──
        trow = QHBoxLayout()
        self.in_test = QLineEdit()
        self.in_test.setPlaceholderText("Prompt de prueba (genera 1 imagen)…")
        trow.addWidget(self.in_test, 1)
        self.btn_test = QPushButton("🧪 Probar")
        self.btn_test.clicked.connect(self._test)
        trow.addWidget(self.btn_test)
        root.addLayout(trow)

        self.status = QLabel(); self.status.setStyleSheet("color:#888;")
        self.status.setWordWrap(True)
        root.addWidget(self.status)
        self.refresh()

    def _has_key(self) -> bool:
        return bool(self._ri and self._ri.get_api_key())

    def refresh(self):
        ok = self._has_key()
        self.key_status.setText(("🟢 <b>Runware</b> key configurada"
                                 if ok else "⚪ <b>Runware</b> sin key — añádela"))
        if self._ri:
            self.lbl_default.setText(
                f"Modelo por defecto: <code>{self._ri.get_default_model()}</code>")

    def _save_key(self):
        k = self.in_key.text().strip()
        if not k:
            return
        try:
            import ai_providers as aip
            aip.save_key("runware", k)
            self.in_key.clear()
            self.status.setText("✓ Key de Runware guardada (chmod 0600).")
            self.refresh()
        except Exception as e:  # noqa: BLE001
            self.status.setText(f"Error guardando key: {e}")

    def _use_category(self, cat: dict):
        self.in_search.setText(cat["search"])
        idx = self.cb_arch.findData(cat.get("architecture", ""))
        if idx >= 0:
            self.cb_arch.setCurrentIndex(idx)
        self._search()

    def _search(self):
        if not self._ri:
            return
        if not self._has_key():
            self.status.setText("Añade la API key de Runware primero.")
            return
        self.status.setText("Buscando modelos en Runware…")
        self.results.clear()
        res = self._ri.search_models(query=self.in_search.text().strip(),
                                     architecture=self.cb_arch.currentData() or "",
                                     limit=40)
        if not res.get("ok"):
            self.status.setText(f"Error: {res.get('error')}")
            return
        for m in res["models"]:
            it = QListWidgetItem(f"{m['name']}  ·  {m.get('architecture','?')}  "
                                 f"·  {m['air']}")
            it.setData(Qt.ItemDataRole.UserRole, m["air"])
            self.results.addItem(it)
        self.status.setText(f"{self.results.count()} modelo(s). Selecciona y "
                            "«Usar como modelo por defecto».")

    def _sel_changed(self, cur, _prev=None):
        self.btn_default.setEnabled(cur is not None)

    def _set_default(self):
        cur = self.results.currentItem()
        if not cur or not self._ri:
            return
        air = cur.data(Qt.ItemDataRole.UserRole)
        try:
            self._ri.set_default_model(air)
            self.status.setText(f"✓ Modelo por defecto: {air}")
            self.refresh()
        except Exception as e:  # noqa: BLE001
            self.status.setText(f"Error: {e}")

    def _test(self):
        if not self._ri or not self._has_key():
            self.status.setText("Falta la API key de Runware.")
            return
        prompt = self.in_test.text().strip()
        if not prompt:
            return
        air = None
        cur = self.results.currentItem()
        if cur:
            air = cur.data(Qt.ItemDataRole.UserRole)
        self.status.setText("Generando imagen de prueba…")
        self.btn_test.setEnabled(False)
        try:
            res = self._ri.generate(prompt, model=air, width=768, height=512)
        finally:
            self.btn_test.setEnabled(True)
        if res.get("ok"):
            self.status.setText(f"✓ Imagen generada: {res['urls'][0]}")
        else:
            self.status.setText(f"✗ {res.get('error')}")

    def set_powered(self, on: bool):
        pass


# ───────────────────────── 📲 Remoto (mensajería / gateway) ─────────────
# Plataformas soportadas + su env var de credencial (en ~/.hermes/.env).
GATEWAY_PLATFORMS = [
    ("telegram", "TELEGRAM_BOT_TOKEN", "BotFather → /newbot → token"),
    ("discord", "DISCORD_TOKEN", "Discord Developer Portal → Bot token"),
    ("slack", "SLACK_BOT_TOKEN", "Slack app → Bot User OAuth Token (xoxb-)"),
    ("whatsapp", "WHATSAPP_*", "WhatsApp Cloud API / proveedor"),
    ("signal", "SIGNAL_*", "signal-cli vinculado"),
    ("matrix", "MATRIX_*", "homeserver + access token"),
    ("email", "EMAIL_*", "IMAP/SMTP"),
    ("sms", "SMS_*", "Twilio u otro"),
    ("teams", "TEAMS_*", "Microsoft Graph / Azure app"),
]


class MessagingTab(QWidget):
    """Control remoto vía el gateway de Hermes: configurar plataformas (Telegram,
    WhatsApp, Discord…), arrancar/parar el servicio, enviar de prueba y pairing.
    Permite lanzar misiones y recibir resultados desde el móvil."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hermes = find_hermes()
        self._proc: QProcess | None = None
        root = QVBoxLayout(self)

        title = QLabel("📲 Remoto (mensajería)")
        f = QFont(); f.setPointSize(13); f.setBold(True); title.setFont(f)
        root.addWidget(title)
        sub = QLabel("Conecta Telegram/WhatsApp/Discord/Slack/… para <b>lanzar "
                     "misiones desde el móvil</b> y recibir avisos + zips. El "
                     "gateway corre en segundo plano y también tickea el cron.")
        sub.setTextFormat(Qt.TextFormat.RichText); sub.setWordWrap(True)
        sub.setStyleSheet("color:#9aa;")
        root.addWidget(sub)

        # ── Servicio gateway ──
        gbox = QFrame(); gbox.setFrameShape(QFrame.Shape.StyledPanel)
        gl = QVBoxLayout(gbox)
        gl.addWidget(QLabel("<b>Servicio del gateway</b>"))
        grow = QHBoxLayout()
        self.btn_setup = QPushButton("⚙️ Configurar plataformas")
        self.btn_setup.setToolTip("Abre el asistente `hermes gateway setup` en una "
                                  "terminal (elige plataforma y pega el token).")
        self.btn_setup.clicked.connect(self._setup)
        grow.addWidget(self.btn_setup)
        for label, args in (("Estado", ["gateway", "status"]),
                            ("Instalar servicio", ["gateway", "install"]),
                            ("▶ Arrancar", ["gateway", "start"]),
                            ("⏹ Parar", ["gateway", "stop"])):
            b = QPushButton(label)
            b.clicked.connect(lambda _c=False, a=args: self._run(a))
            grow.addWidget(b)
        grow.addStretch()
        gl.addLayout(grow)
        root.addWidget(gbox)

        # ── Plataformas + credenciales (env) ──
        pbox = QFrame(); pbox.setFrameShape(QFrame.Shape.StyledPanel)
        pl = QVBoxLayout(pbox)
        pl.addWidget(QLabel("<b>Plataformas</b> — credencial en "
                            "<code>~/.hermes/.env</code> (deny-by-default; añade "
                            "tu ID a <code>&lt;PLAT&gt;_ALLOWED_USERS</code>)"))
        prow = QHBoxLayout()
        prow.addWidget(QLabel("Plataforma:"))
        self.cb_plat = QComboBox()
        for name, env, hint in GATEWAY_PLATFORMS:
            self.cb_plat.addItem(f"{name}  ·  {env}", name)
        self.cb_plat.currentIndexChanged.connect(self._plat_hint)
        prow.addWidget(self.cb_plat, 1)
        self.btn_list = QPushButton("📋 Targets configurados")
        self.btn_list.clicked.connect(lambda: self._run(["send", "--list"]))
        prow.addWidget(self.btn_list)
        pl.addLayout(prow)
        self.plat_hint = QLabel(); self.plat_hint.setStyleSheet("color:#7aa2f7;")
        self.plat_hint.setWordWrap(True)
        pl.addWidget(self.plat_hint)
        root.addWidget(pbox)

        # ── Enviar de prueba ──
        sbox = QFrame(); sbox.setFrameShape(QFrame.Shape.StyledPanel)
        sl = QVBoxLayout(sbox)
        sl.addWidget(QLabel("<b>Enviar mensaje de prueba</b>"))
        srow = QHBoxLayout()
        self.in_target = QLineEdit()
        self.in_target.setPlaceholderText("destino: telegram · discord:#ops · slack:#eng")
        srow.addWidget(self.in_target, 1)
        self.in_msg = QLineEdit()
        self.in_msg.setPlaceholderText("mensaje…")
        srow.addWidget(self.in_msg, 2)
        self.btn_send = QPushButton("📤 Enviar")
        self.btn_send.clicked.connect(self._send)
        srow.addWidget(self.btn_send)
        sl.addLayout(srow)
        root.addWidget(sbox)

        # ── Pairing ──
        pgbox = QFrame(); pgbox.setFrameShape(QFrame.Shape.StyledPanel)
        pgl = QVBoxLayout(pgbox)
        pgl.addWidget(QLabel("<b>Pairing</b> — autoriza usuarios desconocidos por código"))
        pgrow = QHBoxLayout()
        self.btn_pair_list = QPushButton("Ver pairing")
        self.btn_pair_list.clicked.connect(lambda: self._run(["pairing", "list"]))
        pgrow.addWidget(self.btn_pair_list)
        self.in_pair_plat = QLineEdit(); self.in_pair_plat.setPlaceholderText("plataforma")
        self.in_pair_plat.setFixedWidth(110)
        pgrow.addWidget(self.in_pair_plat)
        self.in_pair_code = QLineEdit(); self.in_pair_code.setPlaceholderText("código")
        self.in_pair_code.setFixedWidth(110)
        pgrow.addWidget(self.in_pair_code)
        self.btn_pair_ok = QPushButton("✓ Aprobar")
        self.btn_pair_ok.clicked.connect(self._approve)
        pgrow.addWidget(self.btn_pair_ok)
        pgrow.addStretch()
        pgl.addLayout(pgrow)
        root.addWidget(pgbox)

        self.log = QPlainTextEdit(); self.log.setReadOnly(True)
        self.log.setStyleSheet("font-family:monospace; font-size:11px; "
                               "background:#111; color:#cdd;")
        root.addWidget(self.log, 1)

        if not self._hermes:
            root.insertWidget(1, _no_hermes_banner("ℹ️ Hermes no instalado."))
        self._plat_hint()

    def _plat_hint(self):
        i = max(0, self.cb_plat.currentIndex())
        name, env, hint = GATEWAY_PLATFORMS[i]
        self.plat_hint.setText(f"ℹ️ {name}: credencial <code>{env}</code> — {hint}. "
                               "Configúrala con «Configurar plataformas».")
        self.plat_hint.setTextFormat(Qt.TextFormat.RichText)

    def _setup(self):
        if not self._hermes:
            return
        try:
            import platform_compat as pc
            pc.open_in_terminal(str(Path.home() / ".hermes"),
                                command=f"{self._hermes} gateway setup", hold=True)
            self.log.appendPlainText("→ Asistente abierto en una terminal: elige "
                                     "plataforma y pega el token. Luego «▶ Arrancar».")
        except Exception as e:  # noqa: BLE001
            self.log.appendPlainText(f"✗ no se pudo abrir la terminal: {e}\n"
                                     f"Ejecuta a mano: hermes gateway setup")

    def _run(self, args: list[str]):
        if not self._hermes:
            return
        self.log.appendPlainText(f"$ hermes {' '.join(args)}")
        self._proc = _spawn_hermes(
            self, args, lambda t: self.log.appendPlainText(t.rstrip()),
            lambda code: self.log.appendPlainText(f"■ exit {code}"))

    def _send(self):
        if not self._hermes:
            return
        target = self.in_target.text().strip()
        msg = self.in_msg.text().strip()
        if not target or not msg:
            self.log.appendPlainText("Pon destino y mensaje.")
            return
        code, out = run_hermes(["send", "--to", target, msg], timeout=30)
        self.log.appendPlainText(f"$ hermes send --to {target} …\n{out}\n"
                                 + ("✓ enviado" if code == 0 else f"✗ exit {code}"))

    def _approve(self):
        plat = self.in_pair_plat.text().strip()
        code_ = self.in_pair_code.text().strip()
        if not plat or not code_:
            self.log.appendPlainText("Pon plataforma y código.")
            return
        rc, out = run_hermes(["pairing", "approve", plat, code_], timeout=20)
        self.log.appendPlainText(f"$ hermes pairing approve {plat} {code_}\n{out}")
        self.in_pair_code.clear()

    def set_powered(self, on: bool):
        pass


# ───────────────────────── 🛡️ Avanzado (sandbox + portal + perfil/insights) ──
class AdvancedTab(QWidget):
    """Seguridad/aislamiento de ejecución, portal de imágenes y control remoto
    (gateway). Envuelve `hermes config set` + `hermes portal` + `hermes gateway`."""

    BACKENDS = ["local", "docker", "ssh", "modal", "daytona", "singularity"]
    APPROVALS = ["manual", "smart", "off"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hermes = find_hermes()
        self._proc: QProcess | None = None
        root = QVBoxLayout(self)

        title = QLabel("🛡️ Avanzado")
        f = QFont(); f.setPointSize(13); f.setBold(True); title.setFont(f)
        root.addWidget(title)

        # ── Sandbox / seguridad ──
        sbox = QFrame(); sbox.setFrameShape(QFrame.Shape.StyledPanel)
        sl = QVBoxLayout(sbox)
        sl.addWidget(QLabel("<b>🔒 Aislamiento & seguridad de ejecución</b>"))
        sl.addWidget(QLabel("Para cadenas autónomas, ejecuta los builds en contenedor "
                            "(el sandbox es la frontera de seguridad) y controla la "
                            "aprobación de comandos peligrosos."))
        sform = QFormLayout()
        self.cb_backend = QComboBox(); self.cb_backend.addItems(self.BACKENDS)
        self.cb_backend.setToolTip("local = en tu máquina · docker/modal/daytona = "
                                   "aislado en contenedor (recomendado para cadenas).")
        sform.addRow("Backend terminal:", self.cb_backend)
        self.cb_approvals = QComboBox(); self.cb_approvals.addItems(self.APPROVALS)
        self.cb_approvals.setToolTip("manual = siempre pregunta · smart = la IA evalúa "
                                     "el riesgo · off = sin checks (solo en sandbox).")
        sform.addRow("Aprobaciones:", self.cb_approvals)
        sl.addLayout(sform)
        self.btn_apply_sec = QPushButton("Aplicar seguridad")
        self.btn_apply_sec.clicked.connect(self._apply_security)
        sl.addWidget(self.btn_apply_sec)
        root.addWidget(sbox)

        # ── Portal / imágenes ──
        pbox = QFrame(); pbox.setFrameShape(QFrame.Shape.StyledPanel)
        pl = QVBoxLayout(pbox)
        pl.addWidget(QLabel("<b>🎨 Portal de herramientas (imágenes, web, browser)</b>"))
        pl.addWidget(QLabel("El Nous Portal habilita image_generate (FLUX/Recraft/"
                            "Ideogram), web search y cloud browser con una sola cuenta."))
        prow = QHBoxLayout()
        self.btn_portal = QPushButton("Estado del portal")
        self.btn_portal.clicked.connect(lambda: self._run(["portal", "status"]))
        prow.addWidget(self.btn_portal)
        self.btn_portal_tools = QPushButton("Herramientas del portal")
        self.btn_portal_tools.clicked.connect(lambda: self._run(["portal", "tools"]))
        prow.addWidget(self.btn_portal_tools)
        prow.addStretch()
        pl.addLayout(prow)
        root.addWidget(pbox)

        # ── Perfil + bundle ThemeForge ──
        prbox = QFrame(); prbox.setFrameShape(QFrame.Shape.StyledPanel)
        prl = QVBoxLayout(prbox)
        prl.addWidget(QLabel("<b>👤 Perfil + bundle ThemeForge</b>"))
        prl.addWidget(QLabel("Perfil Hermes aislado (config/skills/memoria propias) y "
                            "un bundle <code>/themeforge</code> que agrupa los agentes web."))
        prow2 = QHBoxLayout()
        self.btn_profile = QPushButton("Crear perfil 'themeforge'")
        self.btn_profile.clicked.connect(self._create_profile)
        prow2.addWidget(self.btn_profile)
        self.btn_bundle = QPushButton("Crear bundle /themeforge")
        self.btn_bundle.clicked.connect(self._create_bundle)
        prow2.addWidget(self.btn_bundle)
        self.btn_profiles = QPushButton("Listar perfiles")
        self.btn_profiles.clicked.connect(lambda: self._run(["profile", "list"]))
        prow2.addWidget(self.btn_profiles)
        prow2.addStretch()
        prl.addLayout(prow2)
        root.addWidget(prbox)

        # ── Insights de coste + fallback ──
        ibox = QFrame(); ibox.setFrameShape(QFrame.Shape.StyledPanel)
        il = QVBoxLayout(ibox)
        il.addWidget(QLabel("<b>📈 Coste & fallback</b>"))
        il.addWidget(QLabel("Analítica de tokens/coste por misión, y cadena de fallback "
                            "de proveedor si el cerebro falla."))
        irow = QHBoxLayout()
        self.btn_insights = QPushButton("Insights (30 días)")
        self.btn_insights.clicked.connect(lambda: self._run(["insights", "--days", "30"]))
        irow.addWidget(self.btn_insights)
        self.btn_fallback_list = QPushButton("Ver fallback")
        self.btn_fallback_list.clicked.connect(lambda: self._run(["fallback", "list"]))
        irow.addWidget(self.btn_fallback_list)
        self.btn_fallback_add = QPushButton("➕ Añadir fallback")
        self.btn_fallback_add.setToolTip("Abre `hermes fallback add` en una terminal "
                                         "(elige proveedor/modelo).")
        self.btn_fallback_add.clicked.connect(self._fallback_add)
        irow.addWidget(self.btn_fallback_add)
        irow.addStretch()
        il.addLayout(irow)
        root.addWidget(ibox)

        self.log = QPlainTextEdit(); self.log.setReadOnly(True)
        self.log.setStyleSheet("font-family:monospace; font-size:11px; "
                               "background:#111; color:#cdd;")
        root.addWidget(self.log, 1)

        if not self._hermes:
            root.insertWidget(1, _no_hermes_banner("ℹ️ Hermes no instalado."))
        self.refresh()

    def refresh(self):
        prov, model = _hermes_model_info()  # noqa: F841 (toca config; barato)
        # Lee backend/approvals actuales del config.
        be = ap = None
        cfg = HERMES_HOME / "config.yaml"
        if cfg.is_file():
            try:
                txt = cfg.read_text(encoding="utf-8")
                for ln in txt.splitlines():
                    s = ln.strip()
                    if s.startswith("backend:") and be is None:
                        be = s.split(":", 1)[1].strip()
                    if s.startswith("mode:") and ap is None:
                        ap = s.split(":", 1)[1].strip()
            except Exception:
                pass
        if be in self.BACKENDS:
            self.cb_backend.setCurrentText(be)
        if ap in self.APPROVALS:
            self.cb_approvals.setCurrentText(ap)

    def _apply_security(self):
        if not self._hermes:
            return
        be = self.cb_backend.currentText()
        ap = self.cb_approvals.currentText()
        c1, o1 = run_hermes(["config", "set", "terminal.backend", be], timeout=15)
        c2, o2 = run_hermes(["config", "set", "approvals.mode", ap], timeout=15)
        self.log.appendPlainText(
            f"$ hermes config set terminal.backend {be}\n{o1}\n"
            f"$ hermes config set approvals.mode {ap}\n{o2}")
        self.log.appendPlainText("✓ seguridad aplicada" if c1 == 0 and c2 == 0
                                 else "✗ revisa la salida")

    def _run(self, args: list[str]):
        if not self._hermes:
            return
        self.log.appendPlainText(f"$ hermes {' '.join(args)}")
        self._proc = _spawn_hermes(
            self, args, lambda t: self.log.appendPlainText(t.rstrip()),
            lambda code: self.log.appendPlainText(f"■ exit {code}"))

    def _create_profile(self):
        if not self._hermes:
            return
        rc, out = run_hermes(["profile", "create", "themeforge", "--clone"], timeout=30)
        self.log.appendPlainText(f"$ hermes profile create themeforge --clone\n{out}\n"
                                 + ("✓ perfil creado (úsalo: hermes -p themeforge …)"
                                    if rc == 0 else f"✗ exit {rc}"))

    def _create_bundle(self):
        if not self._hermes:
            return
        skills = ["themeforge-operator"]
        try:
            from hermes_web_agents import web_agent_names
            skills += web_agent_names()
        except Exception:
            pass
        args = ["bundles", "create", "themeforge"]
        for s in skills:
            args += ["--skill", s]
        rc, out = run_hermes(args, timeout=30)
        self.log.appendPlainText(
            f"$ hermes bundles create themeforge --skill … ({len(skills)} skills)\n{out}\n"
            + ("✓ bundle creado → usa /themeforge en el chat" if rc == 0 else f"✗ exit {rc}"))

    def _fallback_add(self):
        if not self._hermes:
            return
        try:
            import platform_compat as pc
            pc.open_in_terminal(str(Path.home() / ".hermes"),
                                command=f"{self._hermes} fallback add", hold=True)
            self.log.appendPlainText("→ `hermes fallback add` abierto en una terminal "
                                     "(elige proveedor/modelo de respaldo).")
        except Exception as e:  # noqa: BLE001
            self.log.appendPlainText(f"✗ {e} — ejecuta a mano: hermes fallback add")

    def set_powered(self, on: bool):
        for b in (self.btn_apply_sec, self.btn_portal, self.btn_portal_tools,
                  self.btn_profile, self.btn_bundle, self.btn_insights):
            b.setEnabled(bool(self._hermes) and on)
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
        self.provider = ProviderTab()
        # Al aplicar un modelo en Proveedor, refresca el chip de estado de arriba.
        self.provider.model_changed.connect(self.strip.refresh)
        self.agents = AgentsTab()
        self.create = CreateAgentTab()
        self.memory = MemoryTab()
        self.kanban = KanbanTab()
        self.cron = CronTab()
        self.images = ImagesTab()
        self.messaging = MessagingTab()
        self.advanced = AdvancedTab()
        self.chat = HermesTerminal()
        self.admin = AdminTab()

        self.tabs.addTab(self.mission, "🚀 Misión")
        self.tabs.addTab(self.provider, "🔌 Proveedor")
        self.tabs.addTab(self.images, "🎨 Imágenes")
        self.tabs.addTab(self.agents, "🤖 Agentes")
        self.tabs.addTab(self.create, "➕ Crear")
        self.tabs.addTab(self.memory, "🧠 Memoria")
        self.tabs.addTab(self.kanban, "📊 Kanban")
        self.tabs.addTab(self.cron, "⏰ Cron")
        self.tabs.addTab(self.messaging, "📲 Remoto")
        self.tabs.addTab(self.advanced, "🛡️ Avanzado")
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
        for t in (self.mission, self.provider, self.images, self.agents,
                  self.create, self.memory, self.kanban, self.cron,
                  self.messaging, self.advanced, self.admin):
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
