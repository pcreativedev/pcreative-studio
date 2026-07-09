"""
market_tab — pestaña «Mercado» del main window de Pcreative Studio.

Botones de análisis IA (vía OpenRouter + Gemini 2.5 Pro por defecto):
  · Mercado 2026 general
  · Por nicho concreto
  · Comparar 2 nichos
  · Por marketplace
  · Predicción 2027

Output: markdown renderizado en QTextBrowser. Histórico persistente.
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QObject, Qt, QThread, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QGuiApplication
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from market_analyzer import (
    DEFAULT_MODEL,
    MARKETPLACES,
    MODELS,
    MODEL_LABELS,
    NEXT_YEAR,
    YEAR,
    AnalysisRequest,
    build_request,
    call_openrouter,
    get_openrouter_key,
    list_analyses,
    load_analysis,
    parse_opportunities,
    save_analysis,
    split_hybrid,
)
from stacks import TEMPLATE_NICHES
import market_dashboard as md_dash


class _DashPage(QWebEnginePage):
    """Página del panel: los enlaces externos se abren en el navegador del sistema."""

    def acceptNavigationRequest(self, url: QUrl, nav_type, is_main_frame) -> bool:  # type: ignore[override]
        if nav_type == QWebEnginePage.NavigationType.NavigationTypeLinkClicked:
            QDesktopServices.openUrl(url)
            return False
        return True

# ─── Tema visual del análisis (Qt rich-text CSS: subconjunto de CSS2.1) ──────
# Se aplica al HTML que Qt genera desde el markdown → tablas, cabeceras y cajas
# con estilo, en vez del render plano de setMarkdown.
_MD_CSS = """
body { color:#dbe1ea; font-size:10.5pt; line-height:150%; }
h1 { color:#c7d2fe; font-size:19pt; font-weight:800; margin:14px 0 8px 0; }
h2 { color:#a5b4fc; font-size:14.5pt; font-weight:700;
     border-bottom:2px solid #3730a3; padding-bottom:3px; margin:22px 0 8px 0; }
h3 { color:#93c5fd; font-size:12pt; font-weight:700; margin:16px 0 6px 0; }
h4 { color:#a7f3d0; font-size:11pt; font-weight:700; margin:12px 0 4px 0; }
p  { margin:6px 0; }
a  { color:#60a5fa; text-decoration:none; }
strong { color:#f1f5f9; }
em { color:#cbd5e1; }
ul, ol { margin:6px 0 6px 4px; }
li { margin:3px 0; }
hr { border:0; border-top:1px solid #334155; }
code { background:#1e293b; color:#fbbf24; padding:1px 5px; border-radius:4px;
       font-family:monospace; font-size:9.5pt; }
pre  { background:#0b1220; color:#e2e8f0; padding:10px; border-radius:8px;
       border:1px solid #1e293b; }
blockquote { background:#111a2e; color:#c7d2fe; border-left:4px solid #6366f1;
             margin:10px 0; padding:8px 14px; }
table { border:1px solid #334155; margin:10px 0; }
th { background:#1e293b; color:#c7d2fe; font-weight:700; text-align:left;
     padding:7px 10px; border:1px solid #334155; }
td { padding:6px 10px; border:1px solid #263143; color:#dbe1ea; }
"""


def _score_color(goodness: int) -> str:
    """Verde/ámbar/rojo según lo BUENO que sea (0-100, mayor = mejor)."""
    if goodness >= 70:
        return "#22c55e"
    if goodness >= 45:
        return "#f59e0b"
    return "#ef4444"


def _bar(value: int, invert: bool = False) -> str:
    """Barra horizontal (tabla Qt) de 0-100. invert=True → alto es malo (competencia/dificultad)."""
    v = max(0, min(100, int(value or 0)))
    color = _score_color(100 - v if invert else v)
    rest = max(0, 100 - v)
    return (
        f'<table width="130" cellspacing="0" cellpadding="0" style="margin:0"><tr>'
        f'<td bgcolor="{color}" width="{v}%" style="font-size:3pt">&nbsp;</td>'
        f'<td bgcolor="#1e293b" width="{rest}%" style="font-size:3pt">&nbsp;</td>'
        f'</tr></table>'
    )


def _score_rows(scores: dict) -> str:
    """Filas label · barra · valor para los 5 scores."""
    defs = [
        ("Demanda", "demanda", False),
        ("Ingresos", "ingresos", False),
        ("Competencia", "competencia", True),
        ("Dificultad", "dificultad", True),
    ]
    rows = []
    for label, key, inv in defs:
        v = int(scores.get(key, 0) or 0)
        good = (100 - v) if inv else v
        rows.append(
            f'<tr><td width="90" style="color:#94a3b8;font-size:9pt;padding:2px 8px 2px 0">{label}</td>'
            f'<td width="130">{_bar(v, inv)}</td>'
            f'<td width="34" style="color:{_score_color(good)};font-weight:700;padding-left:8px">{v}</td></tr>'
        )
    return '<table cellspacing="0" cellpadding="0" style="margin:6px 0">' + "".join(rows) + "</table>"


def _stack_name(sid: str) -> str:
    try:
        import stacks
        s = stacks.STACKS.get(sid)
        return s.get("name", sid) if s else sid
    except Exception:
        return sid


def _render_opportunities_html(data: dict) -> str:
    """Convierte el JSON de oportunidades en tarjetas HTML visuales para el QTextBrowser."""
    ops = data.get("oportunidades") or []
    parts = [f'<h1>🎯 {data.get("titulo", "Oportunidades")}</h1>']
    for i, o in enumerate(ops, 1):
        sc = o.get("scores", {}) or {}
        opp = int(sc.get("oportunidad", 0) or 0)
        oc = _score_color(opp)
        nombre = str(o.get("nombre", "")).strip()
        pitch = str(o.get("pitch", "")).strip()
        mkt = str(o.get("marketplace", "")).strip()
        precio = str(o.get("precio", "")).strip()
        sid = str(o.get("stack", "")).strip()
        evidencia = str(o.get("evidencia", "")).strip()
        pasos = o.get("como_proceder") or []

        chips = []
        if mkt:
            chips.append(f'<span style="background:#1e293b;color:#c7d2fe;padding:2px 8px;border-radius:6px">🛒 {mkt}</span>')
        if precio:
            chips.append(f'<span style="background:#1e293b;color:#a7f3d0;padding:2px 8px;border-radius:6px">💶 {precio}</span>')
        if sid:
            chips.append(f'<span style="background:#312e81;color:#c7d2fe;padding:2px 8px;border-radius:6px">🧱 {_stack_name(sid)}</span>')
        chips_html = " &nbsp; ".join(chips)

        pasos_html = "".join(f"<li>{str(p)}</li>" for p in pasos)

        parts.append(
            f'<table width="100%" cellspacing="0" cellpadding="12" style="margin:12px 0">'
            f'<tr><td bgcolor="#111a2e" style="border-left:5px solid {oc}">'
            # cabecera: nombre + score grande
            f'<table width="100%" cellspacing="0" cellpadding="0"><tr>'
            f'<td><span style="font-size:14pt;font-weight:800;color:#f1f5f9">#{i} &nbsp;{nombre}</span></td>'
            f'<td align="right"><span style="font-size:22pt;font-weight:800;color:{oc}">{opp}</span>'
            f'<span style="color:#64748b;font-size:9pt">/100 oportunidad</span></td>'
            f'</tr></table>'
            f'<p style="color:#cbd5e1;margin:4px 0 8px 0">{pitch}</p>'
            f'<p style="margin:0 0 6px 0">{chips_html}</p>'
            f'{_score_rows(sc)}'
            + (f'<p style="color:#93c5fd;font-size:9.5pt;margin:8px 0 4px 0">📊 <em>{evidencia}</em></p>' if evidencia else "")
            + (f'<p style="color:#a5b4fc;font-weight:700;margin:8px 0 2px 0">Cómo proceder</p><ol style="margin:0 0 2px 0">{pasos_html}</ol>' if pasos_html else "")
            + '</td></tr></table>'
        )
    return "".join(parts)


def _md_to_html(md: str) -> str:
    """Markdown → HTML (para combinar con las tarjetas visuales en un solo panel)."""
    try:
        import markdown as _md
        return _md.markdown(md or "", extensions=["tables", "sane_lists", "fenced_code"])
    except Exception:
        return "<pre>" + (md or "").replace("<", "&lt;") + "</pre>"


def _render_scored_summary(items: list) -> str:
    """Panel resumen puntuado (ranking con barras) para general/niche."""
    if not items:
        return ""
    rows = []
    ordered = sorted(items, key=lambda x: -int(x.get("oportunidad", 0) or 0))
    for i, it in enumerate(ordered, 1):
        opp = int(it.get("oportunidad", 0) or 0)
        dem = int(it.get("demanda", 0) or 0)
        comp = int(it.get("competencia", 0) or 0)
        oc = _score_color(opp)
        rows.append(
            f'<tr>'
            f'<td width="22" style="color:#64748b;padding:5px 6px">{i}</td>'
            f'<td style="color:#f1f5f9;font-weight:600;padding:5px 6px">{str(it.get("nombre",""))}</td>'
            f'<td width="140" style="padding:5px 6px">{_bar(opp)}</td>'
            f'<td width="38" style="color:{oc};font-weight:800;font-size:12pt;padding:5px 6px">{opp}</td>'
            f'<td width="150" style="color:#94a3b8;font-size:8.5pt;padding:5px 6px">demanda {dem} · comp. {comp}</td>'
            f'</tr>'
        )
    return ('<h2>🏆 Oportunidades del análisis (resumen puntuado)</h2>'
            '<table width="100%" cellspacing="0" cellpadding="0" bgcolor="#111a2e" '
            'style="margin:6px 0">' + "".join(rows) + '</table>')


def _render_versus(data: dict) -> str:
    """Comparativa head-to-head con barras enfrentadas para el modo compare."""
    a = data.get("a", {}) or {}
    b = data.get("b", {}) or {}
    sa = a.get("scores", {}) or {}
    sb = b.get("scores", {}) or {}
    na = str(a.get("nombre", "A"))
    nb = str(b.get("nombre", "B"))
    defs = [("Demanda", "demanda", False), ("Ingresos", "ingresos", False),
            ("Competencia", "competencia", True), ("Dificultad", "dificultad", True),
            ("Oportunidad", "oportunidad", False)]
    rows = [
        f'<tr><td></td>'
        f'<td align="center" colspan="2" style="color:#c7d2fe;font-weight:800;font-size:11pt;padding-bottom:4px">{na}</td>'
        f'<td align="center" colspan="2" style="color:#a7f3d0;font-weight:800;font-size:11pt;padding-bottom:4px">{nb}</td></tr>'
    ]
    for label, key, inv in defs:
        va = int(sa.get(key, 0) or 0)
        vb = int(sb.get(key, 0) or 0)
        ca = _score_color((100 - va) if inv else va)
        cb = _score_color((100 - vb) if inv else vb)
        big = ' style="font-weight:800;font-size:11pt"' if key == "oportunidad" else ' style="font-size:9pt"'
        rows.append(
            f'<tr>'
            f'<td width="90"{big} valign="middle"><span style="color:#94a3b8">{label}</span></td>'
            f'<td width="120" valign="middle" style="padding:3px 4px">{_bar(va, inv)}</td>'
            f'<td width="34" valign="middle" style="color:{ca};font-weight:700;text-align:right;padding-right:12px">{va}</td>'
            f'<td width="120" valign="middle" style="padding:3px 4px">{_bar(vb, inv)}</td>'
            f'<td width="34" valign="middle" style="color:{cb};font-weight:700;text-align:right">{vb}</td>'
            f'</tr>'
        )
    return ('<h2>⚔️ Comparativa puntuada</h2>'
            '<table width="100%" cellspacing="0" cellpadding="4" bgcolor="#111a2e" '
            'style="margin:6px 0">' + "".join(rows) + '</table>')


# ─── Worker en QThread (HTTP fuera del GUI thread) ──────────────────────


class _MarketWorker(QObject):
    result_ready = pyqtSignal(str)        # markdown content
    error = pyqtSignal(str)

    def __init__(self, req: AnalysisRequest, api_key: str):
        super().__init__()
        self.req = req
        self.api_key = api_key

    def run(self):
        try:
            content = call_openrouter(self.req, self.api_key)
            self.result_ready.emit(content)
        except Exception as e:
            self.error.emit(str(e))


# ─── Dialog para «Comparar 2 nichos» ────────────────────────────────────


class _CompareDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Comparar 2 nichos")
        self.setMinimumWidth(420)
        form = QFormLayout(self)
        self.combo_a = QComboBox()
        self.combo_b = QComboBox()
        for combo in (self.combo_a, self.combo_b):
            for n in TEMPLATE_NICHES:
                if not n.startswith("("):
                    combo.addItem(n)
        # Defaults: A = 0, B = 1
        if self.combo_b.count() > 1:
            self.combo_b.setCurrentIndex(1)
        form.addRow("Nicho A:", self.combo_a)
        form.addRow("Nicho B:", self.combo_b)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def picked(self) -> tuple[str, str]:
        return self.combo_a.currentText(), self.combo_b.currentText()


# ─── La tab ─────────────────────────────────────────────────────────────


class MarketTab(QWidget):
    # Emitida cuando el usuario pulsa «Configurar OpenRouter» del banner.
    # El main window la conecta para saltar a la pestaña Settings.
    request_open_credentials = pyqtSignal()

    # Emitida cuando el usuario pulsa «Crear proyecto desde este análisis».
    # Arg: el markdown del análisis. El main window lo guarda como
    # _last_analysis del builder y salta a la pestaña New project.
    request_create_from_analysis = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker: _MarketWorker | None = None
        self._current_req: AnalysisRequest | None = None
        self._current_md: str = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # ─ Banner sin key (visible solo si no hay OPENROUTER_API_KEY) ─
        self._build_no_key_banner()
        root.addWidget(self._no_key_banner)

        # ─ Header: modelo + datos reales + status ─
        header = QHBoxLayout()
        header.addWidget(QLabel("Modelo:"))
        self.model_combo = QComboBox()
        for m in MODELS:
            self.model_combo.addItem(MODEL_LABELS.get(m, m), userData=m)
        idx = self.model_combo.findData(DEFAULT_MODEL)
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)
        self.model_combo.setMinimumWidth(320)
        header.addWidget(self.model_combo)
        # Toggle: grounding con búsqueda web (datos reales)
        self.web_toggle = QCheckBox("🌐 Datos reales (web)")
        self.web_toggle.setChecked(True)
        self.web_toggle.setToolTip(
            "Usa búsqueda web en tiempo real (bestsellers, ventas, precios reales).\n"
            "Los modelos Perplexity Sonar ya la traen; a los demás se les añade :online."
        )
        header.addWidget(self.web_toggle)
        header.addSpacing(20)
        self.status_lbl = QLabel("Listo")
        self.status_lbl.setStyleSheet("color:#9ca3af; font-style:italic;")
        header.addWidget(self.status_lbl, 1)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # indeterminate
        self.progress.setVisible(False)
        self.progress.setMaximumWidth(180)
        header.addWidget(self.progress)
        root.addLayout(header)

        # ─ Botones de análisis ─
        btns_box = QGridLayout()
        btns_box.setHorizontalSpacing(8)
        btns_box.setVerticalSpacing(8)
        self.btn_general = self._mk_btn(f"🌍 Mercado {YEAR} (general)", self._on_general)
        self.btn_stacks = self._mk_btn("📊 Análisis de stacks", self._on_stacks)
        self.btn_niche = self._mk_btn("🎯 Por nicho concreto", self._on_niche)
        self.btn_compare = self._mk_btn("⚖️ Comparar 2 nichos", self._on_compare)
        self.btn_marketplace = self._mk_btn("🏪 Por marketplace", self._on_marketplace)
        self.btn_predict = self._mk_btn(f"🔮 Predicción {NEXT_YEAR}", self._on_predict)
        self.btn_opportunities = self._mk_btn(
            "💎 Oportunidades — scoring + stack recomendado", self._on_opportunities
        )
        self.btn_opportunities.setStyleSheet(
            "QPushButton { background:#6d28d9; color:white; font-weight:bold; "
            "border:none; border-radius:8px; padding:9px 14px; } "
            "QPushButton:hover { background:#7c3aed; } "
            "QPushButton:disabled { background:#475569; color:#94a3b8; }"
        )
        btns_box.addWidget(self.btn_general,     0, 0)
        btns_box.addWidget(self.btn_stacks,      0, 1)
        btns_box.addWidget(self.btn_niche,       0, 2)
        btns_box.addWidget(self.btn_compare,     1, 0)
        btns_box.addWidget(self.btn_marketplace, 1, 1)
        btns_box.addWidget(self.btn_predict,     1, 2)
        btns_box.addWidget(self.btn_opportunities, 2, 0, 1, 3)
        root.addLayout(btns_box)

        # ─ Split: histórico | output ─
        splitter = QSplitter(Qt.Orientation.Horizontal)
        # histórico
        self.history_list = QListWidget()
        self.history_list.setMinimumWidth(220)
        self.history_list.setMaximumWidth(360)
        self.history_list.itemDoubleClicked.connect(self._on_history_open)
        splitter.addWidget(self.history_list)
        # output
        out_panel = QWidget()
        out_lay = QVBoxLayout(out_panel)
        out_lay.setContentsMargins(0, 0, 0, 0)
        # Panel de salida = QWebEngineView (dashboard con Chart.js). Enlaces externos → navegador.
        self.output = QWebEngineView()
        self.output.setPage(_DashPage(self.output))
        self.output.setHtml(md_dash.page(
            "<div style='color:#64748b;padding:30px;font-size:15px'>"
            "Aquí saldrá el análisis.<br><br>Pulsa uno de los botones de arriba para empezar."
            "</div>"))
        out_lay.addWidget(self.output, 1)
        footer = QHBoxLayout()
        self.btn_create = QPushButton("🚀 Crear proyecto desde este análisis")
        self.btn_create.setStyleSheet(
            "QPushButton { background:#2563eb; color:white; font-weight:bold; "
            "padding:8px 16px; border-radius:6px; } "
            "QPushButton:hover { background:#1d4ed8; } "
            "QPushButton:disabled { background:#475569; color:#94a3b8; }"
        )
        self.btn_create.setToolTip(
            "Salta a la pestaña «New project» con el análisis cargado.\n"
            "Modo: scratch (sin referencia) · stack y nicho sin fijar — el\n"
            "agente leerá el análisis y decidirá qué construir."
        )
        self.btn_export = QPushButton("💾 Exportar .md")
        self.btn_copy = QPushButton("📋 Copiar")
        self.btn_clear = QPushButton("🗑️ Limpiar")
        for b in (self.btn_create, self.btn_export, self.btn_copy, self.btn_clear):
            b.setEnabled(False)
        self.btn_create.clicked.connect(self._on_create_project)
        self.btn_export.clicked.connect(self._on_export)
        self.btn_copy.clicked.connect(self._on_copy)
        self.btn_clear.clicked.connect(self._on_clear)
        footer.addWidget(self.btn_create)
        footer.addSpacing(12)
        footer.addWidget(self.btn_export)
        footer.addWidget(self.btn_copy)
        footer.addWidget(self.btn_clear)
        footer.addStretch(1)
        self.meta_lbl = QLabel("")
        self.meta_lbl.setStyleSheet("color:#9ca3af; font-size:9pt;")
        footer.addWidget(self.meta_lbl)
        out_lay.addLayout(footer)
        splitter.addWidget(out_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([260, 900])
        root.addWidget(splitter, 1)

        self._refresh_history()
        self._refresh_key_state()

    # ─ Banner sin key ─

    def _build_no_key_banner(self):
        self._no_key_banner = QFrame()
        self._no_key_banner.setObjectName("market_no_key_banner")
        self._no_key_banner.setStyleSheet(
            "#market_no_key_banner { background:#3a2e1e; border:1px solid #f59e0b; "
            "border-radius:8px; padding:10px 14px; }"
        )
        self._no_key_banner.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        lay = QHBoxLayout(self._no_key_banner)
        lay.setContentsMargins(12, 10, 12, 10)
        txt = QLabel(
            "<b style='color:#fbbf24;'>⚠️ Necesitas una API key de OpenRouter</b>"
            "<br><span style='color:#fde68a; font-size:10pt;'>"
            "Crea una gratis en <a href='https://openrouter.ai/keys' style='color:#fcd34d;'>openrouter.ai/keys</a> "
            "y pégala en Settings → Credentials → OpenRouter. "
            "Coste típico por análisis con Gemini 2.5 Pro: ~$0.05-0.15."
            "</span>"
        )
        txt.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        txt.setOpenExternalLinks(True)
        txt.setWordWrap(True)
        lay.addWidget(txt, 1)
        btn = QPushButton("⚙️  Configurar OpenRouter")
        btn.setMinimumHeight(36)
        btn.clicked.connect(self.request_open_credentials)
        lay.addWidget(btn)

    def _refresh_key_state(self):
        """Muestra/oculta el banner según haya o no key de OpenRouter."""
        has_key = bool(get_openrouter_key())
        self._no_key_banner.setVisible(not has_key)

    def showEvent(self, e):
        # Cada vez que el usuario entra en la pestaña, re-comprobamos por si
        # añadió la key en Settings mientras tanto.
        self._refresh_key_state()
        super().showEvent(e)

    # ─ Helpers ─

    def _mk_btn(self, text: str, slot) -> QPushButton:
        b = QPushButton(text)
        b.setMinimumHeight(44)
        b.clicked.connect(slot)
        return b

    def _set_busy(self, busy: bool, msg: str = ""):
        for b in (self.btn_general, self.btn_stacks, self.btn_niche,
                  self.btn_compare, self.btn_marketplace, self.btn_predict,
                  self.btn_opportunities):
            b.setEnabled(not busy)
        self.progress.setVisible(busy)
        if busy:
            self.status_lbl.setText(msg or "Analizando…")
            self.status_lbl.setStyleSheet("color:#fbbf24; font-style:italic;")
        else:
            self.status_lbl.setText("Listo")
            self.status_lbl.setStyleSheet("color:#9ca3af; font-style:italic;")

    def _kick_off(self, req: AnalysisRequest):
        api_key = get_openrouter_key()
        if not api_key:
            QMessageBox.warning(
                self, "Mercado",
                "No hay OPENROUTER_API_KEY configurada. Settings → Credentials → OpenRouter."
            )
            return
        self._current_req = req
        self._set_busy(True, f"Pidiendo a {req.model}… (puede tardar 30-90 s)")
        self._thread = QThread(self)
        self._worker = _MarketWorker(req, api_key)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.result_ready.connect(self._on_result)
        self._worker.error.connect(self._on_error)
        self._worker.result_ready.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _display(self, content: str, kind: str) -> str:
        """Pinta el contenido en el dashboard (Chart.js) según el modo.
        Devuelve el texto 'limpio' (narrativa) para exportar/guardar."""
        # Oportunidades → dashboard con radar por oportunidad + ranking.
        if kind == "opportunities":
            data = parse_opportunities(content)
            if data:
                self.output.setHtml(md_dash.dashboard_opportunities(data))
                return content
        # General / nicho / comparar → ranking o versus (Chart.js) + análisis.
        if kind in ("general", "niche", "compare"):
            summary, narrative = split_hybrid(content)
            self.output.setHtml(
                md_dash.dashboard_hybrid(summary, _md_to_html(narrative), versus=(kind == "compare"))
            )
            return narrative
        # Resto → análisis en markdown → HTML con la misma estética.
        self.output.setHtml(md_dash.page(_md_to_html(content)))
        return content

    def _on_result(self, content: str):
        self._set_busy(False)
        kind = self._current_req.kind if self._current_req is not None else ""
        self._current_md = self._display(content, kind)
        for b in (self.btn_create, self.btn_export, self.btn_copy, self.btn_clear):
            b.setEnabled(True)
        # Guardar al histórico
        try:
            if self._current_req is not None:
                path = save_analysis(self._current_req, content)
                self.meta_lbl.setText(
                    f"{self._current_req.model} · guardado: {path.name}"
                )
        except Exception as e:
            self.meta_lbl.setText(f"⚠️ no se pudo guardar histórico: {e}")
        self._refresh_history()

    def _on_error(self, msg: str):
        self._set_busy(False)
        QMessageBox.critical(self, "Mercado", msg)

    # ─ Botones de análisis ─

    def _on_general(self):
        self._kick_off(build_request("general", self._model(), web=self._web()))

    def _on_stacks(self):
        self._kick_off(build_request("stacks", self._model(), web=self._web()))

    def _on_niche(self):
        niches = [n for n in TEMPLATE_NICHES if not n.startswith("(")]
        niche, ok = QInputDialog.getItem(
            self, "Por nicho", "Elige nicho:", niches, 0, False
        )
        if ok and niche:
            self._kick_off(build_request("niche", self._model(), {"niche": niche}, web=self._web()))

    def _on_compare(self):
        dlg = _CompareDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            a, b = dlg.picked()
            if a and b and a != b:
                self._kick_off(build_request(
                    "compare", self._model(), {"a": a, "b": b}, web=self._web()
                ))
            elif a == b:
                QMessageBox.information(self, "Comparar", "Elige dos nichos distintos.")

    def _on_marketplace(self):
        mp, ok = QInputDialog.getItem(
            self, "Por marketplace", "Elige marketplace:", MARKETPLACES, 0, False
        )
        if ok and mp:
            self._kick_off(build_request(
                "marketplace", self._model(), {"marketplace": mp}, web=self._web()
            ))

    def _on_predict(self):
        self._kick_off(build_request("prediction", self._model(), web=self._web()))

    def _on_opportunities(self):
        # Enfoque opcional (nicho/marketplace/tecnología); vacío = todo el mercado.
        focus, ok = QInputDialog.getText(
            self, "Oportunidades",
            "Enfoque (opcional): nicho, marketplace o tecnología.\nDéjalo vacío para escanear todo el mercado:",
        )
        if not ok:
            return
        self._kick_off(build_request(
            "opportunities", self._model(), {"n": 8, "focus": focus.strip()}, web=self._web()
        ))

    # ─ Helpers de selección ─
    def _model(self) -> str:
        """ID del modelo seleccionado (el userData del combo, no la etiqueta)."""
        return self.model_combo.currentData() or DEFAULT_MODEL

    def _web(self) -> bool:
        return self.web_toggle.isChecked()

    def _on_create_project(self):
        """Empuja el análisis al main window para crear un proyecto scratch
        con el contexto cargado en CLAUDE.md (sin fijar stack ni nicho)."""
        if not self._current_md:
            return
        self.request_create_from_analysis.emit(self._current_md)

    # ─ Footer ─

    def _on_export(self):
        if not self._current_md:
            return
        suggested = "market-analysis.md"
        if self._current_req:
            suggested = f"market-{self._current_req.kind}.md"
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar análisis", suggested, "Markdown (*.md)"
        )
        if path:
            Path(path).write_text(self._current_md, encoding="utf-8")

    def _on_copy(self):
        if self._current_md:
            QGuiApplication.clipboard().setText(self._current_md)
            self.status_lbl.setText("Copiado al portapapeles ✓")
            self.status_lbl.setStyleSheet("color:#34d399; font-style:italic;")

    def _on_clear(self):
        self.output.setHtml(md_dash.page(""))
        self._current_md = ""
        self._current_req = None
        self.meta_lbl.setText("")
        for b in (self.btn_create, self.btn_export, self.btn_copy, self.btn_clear):
            b.setEnabled(False)

    # ─ Histórico ─

    def _refresh_history(self):
        self.history_list.clear()
        for p in list_analyses():
            try:
                meta, _ = load_analysis(p)
            except Exception:
                meta = {}
            label_parts = []
            date = meta.get("date", "")[:16].replace("T", " ")
            if date:
                label_parts.append(date)
            kind = meta.get("kind", "?")
            params = meta.get("params", "")
            label = f"{date or '?'}  ·  {kind}"
            if params and params not in ("{}", ""):
                # mostrar el primer valor del JSON params
                label += f"  · {params[:50]}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, str(p))
            self.history_list.addItem(item)

    def _on_history_open(self, item: QListWidgetItem):
        path = Path(item.data(Qt.ItemDataRole.UserRole))
        try:
            meta, body = load_analysis(path)
        except Exception as e:
            QMessageBox.warning(self, "Histórico", f"No se pudo abrir: {e}")
            return
        self._current_md = self._display(body, meta.get("kind", ""))
        self._current_req = None  # un histórico no es una req nueva
        for b in (self.btn_create, self.btn_export, self.btn_copy, self.btn_clear):
            b.setEnabled(True)
        self.meta_lbl.setText(f"{meta.get('model', '?')} · {meta.get('date', '?')}")
