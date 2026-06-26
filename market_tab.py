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

from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
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
    AnalysisRequest,
    build_request,
    call_openrouter,
    get_openrouter_key,
    list_analyses,
    load_analysis,
    save_analysis,
)
from stacks import TEMPLATE_NICHES


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

        # ─ Header: modelo + status ─
        header = QHBoxLayout()
        header.addWidget(QLabel("Modelo:"))
        self.model_combo = QComboBox()
        for m in MODELS:
            self.model_combo.addItem(m)
        idx = self.model_combo.findText(DEFAULT_MODEL)
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)
        self.model_combo.setMinimumWidth(280)
        header.addWidget(self.model_combo)
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
        self.btn_general = self._mk_btn("🌍 Mercado 2026 (general)", self._on_general)
        self.btn_stacks = self._mk_btn("📊 Análisis de stacks", self._on_stacks)
        self.btn_niche = self._mk_btn("🎯 Por nicho concreto", self._on_niche)
        self.btn_compare = self._mk_btn("⚖️ Comparar 2 nichos", self._on_compare)
        self.btn_marketplace = self._mk_btn("🏪 Por marketplace", self._on_marketplace)
        self.btn_predict = self._mk_btn("🔮 Predicción 2027", self._on_predict)
        btns_box.addWidget(self.btn_general,     0, 0)
        btns_box.addWidget(self.btn_stacks,      0, 1)
        btns_box.addWidget(self.btn_niche,       0, 2)
        btns_box.addWidget(self.btn_compare,     1, 0)
        btns_box.addWidget(self.btn_marketplace, 1, 1)
        btns_box.addWidget(self.btn_predict,     1, 2)
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
        self.output = QTextBrowser()
        self.output.setOpenExternalLinks(True)
        self.output.setPlaceholderText(
            "Aquí saldrá el análisis (markdown).\n\n"
            "Pulsa uno de los botones de arriba para empezar."
        )
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
                  self.btn_compare, self.btn_marketplace, self.btn_predict):
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

    def _on_result(self, content: str):
        self._set_busy(False)
        self._current_md = content
        self.output.setMarkdown(content)
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
        self._kick_off(build_request("general", self.model_combo.currentText()))

    def _on_stacks(self):
        self._kick_off(build_request("stacks", self.model_combo.currentText()))

    def _on_niche(self):
        niches = [n for n in TEMPLATE_NICHES if not n.startswith("(")]
        niche, ok = QInputDialog.getItem(
            self, "Por nicho", "Elige nicho:", niches, 0, False
        )
        if ok and niche:
            self._kick_off(build_request("niche", self.model_combo.currentText(), {"niche": niche}))

    def _on_compare(self):
        dlg = _CompareDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            a, b = dlg.picked()
            if a and b and a != b:
                self._kick_off(build_request(
                    "compare", self.model_combo.currentText(), {"a": a, "b": b}
                ))
            elif a == b:
                QMessageBox.information(self, "Comparar", "Elige dos nichos distintos.")

    def _on_marketplace(self):
        mp, ok = QInputDialog.getItem(
            self, "Por marketplace", "Elige marketplace:", MARKETPLACES, 0, False
        )
        if ok and mp:
            self._kick_off(build_request(
                "marketplace", self.model_combo.currentText(), {"marketplace": mp}
            ))

    def _on_predict(self):
        self._kick_off(build_request("prediction", self.model_combo.currentText()))

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
        self.output.clear()
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
        self.output.setMarkdown(body)
        self._current_md = body
        self._current_req = None  # un histórico no es una req nueva
        for b in (self.btn_create, self.btn_export, self.btn_copy, self.btn_clear):
            b.setEnabled(True)
        self.meta_lbl.setText(f"{meta.get('model', '?')} · {meta.get('date', '?')}")
