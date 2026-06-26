"""Figma import dialog — paste DTCG JSON or fetch from Figma REST API,
preview the auto-detected token mappings in an editable table, then
save as a new Pcreative Studio theme.

Two-tab interface:

  - **Tokens Studio JSON** (recommended, works for free Figma): paste
    the JSON or open a file exported from the Tokens Studio plugin.

  - **Figma URL + PAT** (Enterprise): paste the file URL and a
    Personal Access Token; we call the REST `/variables/local`
    endpoint and translate to the DTCG intermediate shape.

The mapping table is fully editable: the user can re-target a row
to a different Pcreative Studio slot, edit the hex value, or uncheck rows
to exclude them. Save writes the resulting ThemePack to
`~/.config/themeforge/themes/<slug>.json` and switches the active
theme.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QFileDialog, QFormLayout, QHBoxLayout, QHeaderView, QInputDialog,
    QLabel, QLineEdit, QMessageBox, QPlainTextEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)

import themes
from themes import figma_import as fi
from themes.tokens import ColorTokens, ShapeTokens, ThemePack


# Slots available for re-targeting in the dropdown
_COLOR_SLOTS = list(ColorTokens.__dataclass_fields__.keys())
_SHAPE_SLOTS = list(ShapeTokens.__dataclass_fields__.keys())
_ALL_SLOTS = ([f"color.{s}" for s in _COLOR_SLOTS]
              + [f"shape.{s}" for s in _SHAPE_SLOTS]
              + ["(skip)"])


class FigmaImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📥 Importar tema desde Figma")
        self.resize(900, 720)

        self._tokens: list[fi.FigmaToken] = []
        self._mappings: list[fi.MappingProposal] = []

        # ── Tab widget ──────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_dtcg_tab(), "Tokens Studio JSON")
        self.tabs.addTab(self._build_rest_tab(), "Figma URL + PAT (Enterprise)")

        # ── Mappings preview table ─────────────────────────────────
        self.mappings_table = QTableWidget(0, 5)
        self.mappings_table.setHorizontalHeaderLabels(
            ["✓", "Figma path", "Score", "→ Pcreative Studio slot", "Valor"]
        )
        self.mappings_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.mappings_table.verticalHeader().setVisible(False)
        self.mappings_table.setMinimumHeight(280)

        self.summary_lbl = QLabel(
            "<small>Paste/open a Tokens Studio JSON or use the Figma "
            "REST API to parse tokens. Checked (✓) rows will be applied "
            "to the new theme.</small>"
        )
        self.summary_lbl.setTextFormat(Qt.TextFormat.RichText)
        self.summary_lbl.setWordWrap(True)

        # ── Theme metadata ─────────────────────────────────────────
        self.name_edit = QLineEdit("Imported from Figma")
        self.author_edit = QLineEdit("Imported")
        self.desc_edit = QLineEdit("Auto-imported via DTCG / Figma REST")
        meta_form = QFormLayout()
        meta_form.addRow("Theme name:", self.name_edit)
        meta_form.addRow("Author:", self.author_edit)
        meta_form.addRow("Description:", self.desc_edit)

        # ── Buttons ─────────────────────────────────────────────────
        bb = QDialogButtonBox()
        self.btn_preview = bb.addButton(
            "👁  Live preview", QDialogButtonBox.ButtonRole.ActionRole
        )
        self.btn_save = bb.addButton(
            "💾 Save as theme", QDialogButtonBox.ButtonRole.AcceptRole
        )
        self.btn_cancel = bb.addButton(
            "Cancel", QDialogButtonBox.ButtonRole.RejectRole
        )
        self.btn_preview.clicked.connect(self._on_preview)
        self.btn_save.clicked.connect(self._on_save)
        self.btn_cancel.clicked.connect(self.reject)

        # Capture original theme so cancel can restore
        self._original_name = themes.current_theme_name()
        self._original_pack = themes.load_theme(self._original_name)

        # ── Root layout ────────────────────────────────────────────
        root = QVBoxLayout(self)
        root.addWidget(self.tabs)
        root.addWidget(QLabel("<b>Detected mappings:</b>"))
        root.addWidget(self.summary_lbl)
        root.addWidget(self.mappings_table, 1)
        root.addLayout(meta_form)
        root.addWidget(bb)

    # ── Tab 1: DTCG JSON paste / load ──────────────────────────────
    def _build_dtcg_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        info = QLabel(
            "Paste here the JSON exported by the <a href='https://docs.tokens.studio/'>"
            "<b>Tokens Studio for Figma</b></a> plugin, or open it from a file.<br>"
            "<small>Compatible with DTCG v2025.10 (W3C Design Tokens Community Group).</small>"
        )
        info.setTextFormat(Qt.TextFormat.RichText)
        info.setOpenExternalLinks(True)
        info.setWordWrap(True)

        self.dtcg_textarea = QPlainTextEdit()
        self.dtcg_textarea.setPlaceholderText('{\n  "color": {\n    "brand": {\n      "primary": {"$type": "color", "$value": "#0066cc"}\n    }\n  }\n}')

        btn_row = QHBoxLayout()
        btn_load = QPushButton("📂 Open JSON file…")
        btn_parse = QPushButton("⚡ Parse and propose mappings")
        btn_load.clicked.connect(self._on_load_dtcg_file)
        btn_parse.clicked.connect(self._on_parse_dtcg)
        btn_row.addWidget(btn_load)
        btn_row.addStretch()
        btn_row.addWidget(btn_parse)

        lay.addWidget(info)
        lay.addWidget(self.dtcg_textarea, 1)
        lay.addLayout(btn_row)
        return w

    # ── Tab 2: Figma REST API ──────────────────────────────────────
    def _build_rest_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        info = QLabel(
            "Calls the Figma REST API directly "
            "(<code>GET /v1/files/.../variables/local</code>).<br>"
            "<small>Requires <b>Figma Enterprise</b> plan and a <a href="
            "'https://www.figma.com/developers/api#access-tokens'>Personal "
            "Access Token</a> with scope <code>file_variables:read</code>. "
            "For Free / Pro plans use the previous tab.</small>"
        )
        info.setTextFormat(Qt.TextFormat.RichText)
        info.setOpenExternalLinks(True)
        info.setWordWrap(True)

        self.rest_url_edit = QLineEdit()
        self.rest_url_edit.setPlaceholderText(
            "https://www.figma.com/design/<file-key>/Project-Name  or just the file key"
        )
        self.rest_pat_edit = QLineEdit()
        self.rest_pat_edit.setPlaceholderText("figd_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        self.rest_pat_edit.setEchoMode(QLineEdit.EchoMode.Password)

        form = QFormLayout()
        form.addRow("Figma file URL / key:", self.rest_url_edit)
        form.addRow("Personal Access Token:", self.rest_pat_edit)

        btn_fetch = QPushButton("🌐 Fetch + parsear")
        btn_fetch.clicked.connect(self._on_fetch_rest)

        lay.addWidget(info)
        lay.addLayout(form)
        lay.addWidget(btn_fetch)
        lay.addStretch()
        return w

    # ── Handlers ────────────────────────────────────────────────────
    def _on_load_dtcg_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir JSON de tokens", "", "JSON files (*.json);;All files (*)"
        )
        if path:
            try:
                self.dtcg_textarea.setPlainText(open(path, encoding="utf-8").read())
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Couldn't read the file: {e}")

    def _on_parse_dtcg(self):
        raw = self.dtcg_textarea.toPlainText().strip()
        if not raw:
            QMessageBox.information(self, "Empty", "Paste or load a JSON first.")
            return
        try:
            data = json.loads(raw)
        except Exception as e:
            QMessageBox.critical(self, "Invalid JSON", f"Could not parse:\n{e}")
            return
        self._process_dtcg(data)

    def _on_fetch_rest(self):
        url = self.rest_url_edit.text().strip()
        pat = self.rest_pat_edit.text().strip()
        if not url or not pat:
            QMessageBox.warning(self, "Missing data", "URL and PAT are required.")
            return
        key = fi.extract_file_key(url)
        if not key:
            QMessageBox.warning(self, "Invalid URL",
                                "Could not extract the file key from the URL.")
            return
        self.btn_save.setEnabled(False)
        QApplication.processEvents()
        result = fi.fetch_local_variables(key, pat)
        if not result.ok:
            QMessageBox.critical(self, "Figma API", result.error)
            self.btn_save.setEnabled(True)
            return
        dtcg = fi.figma_variables_to_dtcg(result.data)
        self._process_dtcg(dtcg)
        self.btn_save.setEnabled(True)

    def _process_dtcg(self, data: dict):
        try:
            self._tokens = fi.parse_dtcg(data)
        except Exception as e:
            QMessageBox.critical(self, "Parser DTCG", f"Error: {e}")
            return
        if not self._tokens:
            QMessageBox.information(
                self, "No tokens",
                "The JSON parsed but no tokens with $value were found."
            )
            return

        self._mappings = fi.propose_mappings(self._tokens)
        self._refresh_table()
        n_color = sum(1 for m in self._mappings if m.target_slot.startswith("color."))
        n_shape = sum(1 for m in self._mappings if m.target_slot.startswith("shape."))
        n_total = len(self._tokens)
        n_mapped = len(self._mappings)
        self.summary_lbl.setText(
            f"<small><b>{n_total}</b> tokens parsed · "
            f"<b>{n_mapped}</b> mappings proposed "
            f"({n_color} colors · {n_shape} dimensions) · "
            f"<b>{n_total - n_mapped}</b> with no slot assigned "
            f"(ignored unless you re-target them manually).</small>"
        )

    def _refresh_table(self):
        self.mappings_table.setRowCount(len(self._mappings))
        for row, m in enumerate(self._mappings):
            # Column 0: checkbox (apply this mapping)
            cb = QCheckBox()
            cb.setChecked(True)
            self.mappings_table.setCellWidget(row, 0, cb)

            # Column 1: Figma path (read-only)
            self.mappings_table.setItem(row, 1, QTableWidgetItem(m.figma_path))

            # Column 2: Score
            score_item = QTableWidgetItem(str(m.score))
            score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if m.score >= 95:
                score_item.setForeground(QColor("#86efac"))
            elif m.score >= 85:
                score_item.setForeground(QColor("#fbbf24"))
            else:
                score_item.setForeground(QColor("#f87171"))
            self.mappings_table.setItem(row, 2, score_item)

            # Column 3: target slot (dropdown — user can re-target)
            combo = QComboBox()
            combo.addItems(_ALL_SLOTS)
            if m.target_slot in _ALL_SLOTS:
                combo.setCurrentText(m.target_slot)
            self.mappings_table.setCellWidget(row, 3, combo)

            # Column 4: value (editable hex / number)
            val_item = QTableWidgetItem(str(m.figma_value))
            self.mappings_table.setItem(row, 4, val_item)

        self.mappings_table.resizeColumnsToContents()
        self.mappings_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )

    def _collect_accepted_mappings(self) -> list[fi.MappingProposal]:
        out: list[fi.MappingProposal] = []
        for row, m in enumerate(self._mappings):
            cb: QCheckBox = self.mappings_table.cellWidget(row, 0)  # type: ignore
            combo: QComboBox = self.mappings_table.cellWidget(row, 3)  # type: ignore
            val_item = self.mappings_table.item(row, 4)
            if not cb or not cb.isChecked():
                continue
            slot = combo.currentText() if combo else m.target_slot
            if slot == "(skip)":
                continue
            value = val_item.text() if val_item else m.figma_value
            out.append(fi.MappingProposal(
                figma_path=m.figma_path,
                figma_value=value,
                target_slot=slot,
                score=m.score,
                rationale=m.rationale,
            ))
        return out

    def _on_preview(self):
        """Apply the current mapping selection live without saving."""
        mappings = self._collect_accepted_mappings()
        if not mappings:
            QMessageBox.information(self, "Preview", "Sin mapeos para previsualizar.")
            return
        pack = fi.build_themepack_from_mappings(
            mappings,
            base=themes.load_theme(self._original_name),
            name=self.name_edit.text().strip() or "Imported",
            author=self.author_edit.text().strip(),
            description=self.desc_edit.text().strip(),
        )
        themes.apply_theme(QApplication.instance(), pack)
        themes.clear_icon_cache()

    def _on_save(self):
        mappings = self._collect_accepted_mappings()
        if not mappings:
            QMessageBox.warning(self, "Empty", "No mappings selected.")
            return
        name = self.name_edit.text().strip() or "Imported from Figma"
        slug = re.sub(r"[^a-zA-Z0-9-]+", "-", name.lower()).strip("-") or "imported"
        slug, ok = QInputDialog.getText(
            self, "Theme slug",
            "Slug (a-z, 0-9, hyphens):", text=slug,
        )
        if not ok or not slug.strip():
            return
        slug = re.sub(r"[^a-zA-Z0-9-]+", "-", slug.lower()).strip("-")

        pack = fi.build_themepack_from_mappings(
            mappings,
            base=themes.load_theme(self._original_name),
            name=name,
            author=self.author_edit.text().strip(),
            description=self.desc_edit.text().strip(),
        )

        target = themes.ensure_user_themes_dir() / f"{slug}.json"
        if target.exists():
            r = QMessageBox.question(
                self, "Overwrite",
                f"{target.name} already exists. Overwrite?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if r != QMessageBox.StandardButton.Yes:
                return

        try:
            target.write_text(
                json.dumps(asdict(pack), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            themes.save_current_theme(slug)
            themes.apply_theme(QApplication.instance(), pack)
            themes.clear_icon_cache()
            themes.theme_signals.theme_changed.emit(slug)
            QMessageBox.information(
                self, "Imported",
                f"Theme saved at:\n{target}\n\n"
                f"It appears as '{name}' (custom) in the Settings dropdown."
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Save error", str(e))

    def reject(self) -> None:
        # Restore the original theme if we previewed
        try:
            themes.apply_theme(QApplication.instance(), self._original_pack)
            themes.clear_icon_cache()
        except Exception:
            pass
        super().reject()
