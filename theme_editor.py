"""Live theme editor — visual color pickers + sliders + variant dropdowns
that mutate a working ThemePack and apply it to the QApplication on every
change, so the whole app becomes the preview.

Cancel restores the theme that was active when the dialog opened.
Save asks for a slug and writes the JSON to
`~/.config/themeforge/themes/<slug>.json`, then emits
`theme_signals.theme_changed` so the Settings dropdown refreshes.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QColorDialog, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout, QFrame, QGridLayout, QGroupBox,
    QHBoxLayout, QInputDialog, QLabel, QLineEdit, QMessageBox,
    QPushButton, QScrollArea, QSlider, QVBoxLayout, QWidget,
)

import themes
from themes.tokens import (
    ColorTokens, ComponentTokens, ShapeTokens, SpacingTokens,
    ThemePack, TypographyTokens,
)


# ─── Token group definitions (drive the form layout) ────────────────
_COLOR_GROUPS: list[tuple[str, list[tuple[str, str]]]] = [
    ("Fondos", [
        ("bg_primary",   "Background primary"),
        ("bg_secondary", "Background secondary"),
        ("bg_tertiary",  "Background tertiary"),
        ("bg_elevated",  "Background elevated (menus, tooltips)"),
    ]),
    ("Textos", [
        ("fg_primary",   "Foreground primary"),
        ("fg_secondary", "Foreground secondary (muted)"),
        ("fg_disabled",  "Foreground disabled"),
    ]),
    ("Accent", [
        ("accent",       "Accent color"),
        ("accent_hover", "Accent on hover"),
        ("accent_active","Accent on press / active"),
        ("accent_fg",    "Foreground on accent (contrast)"),
    ]),
    ("Semánticos", [
        ("success", "Success / OK"),
        ("warning", "Warning"),
        ("danger",  "Danger / error"),
        ("info",    "Info"),
    ]),
    ("Bordes y selección", [
        ("border",          "Border"),
        ("border_strong",   "Border strong (hover)"),
        ("selection_bg",    "Selection background"),
        ("selection_fg",    "Selection foreground"),
        ("scrollbar_bg",    "Scrollbar background"),
        ("scrollbar_thumb", "Scrollbar thumb"),
    ]),
]

_SHAPE_RANGES = [
    ("radius_sm",    "Radius small",  0, 20),
    ("radius_md",    "Radius medium", 0, 24),
    ("radius_lg",    "Radius large",  0, 32),
    ("radius_pill",  "Radius pill",   0, 999),
    ("border_width", "Border width",  0, 6),
]

_COMPONENT_OPTIONS = [
    ("button_variant",    "Button",   ["flat", "raised", "pill", "brutalist", "ghost"]),
    ("tab_variant",       "Tab",      ["underline", "card", "pill", "segmented"]),
    ("input_variant",     "Input",    ["outlined", "filled", "underlined", "brutalist"]),
    ("scrollbar_variant", "Scrollbar",["thin", "thick", "hidden"]),
    ("checkbox_variant",  "Checkbox", ["square", "rounded", "pill"]),
    ("density",           "Density",  ["compact", "comfortable", "spacious"]),
]


def _slugify(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9-]+", "-", name.lower().strip())
    return re.sub(r"-+", "-", s).strip("-") or "untitled"


# ─── Helper widgets ──────────────────────────────────────────────────
class _ColorSwatch(QPushButton):
    """Square button that shows a color and opens QColorDialog on click."""

    def __init__(self, hex_color: str, on_change, parent=None):
        super().__init__(parent)
        self._color = hex_color
        self._on_change = on_change
        self.setFixedSize(34, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._refresh()
        self.clicked.connect(self._pick)

    def color(self) -> str:
        return self._color

    def set_color(self, hex_color: str) -> None:
        self._color = hex_color
        self._refresh()

    def _refresh(self) -> None:
        self.setStyleSheet(
            f"background-color: {self._color};"
            "border: 1px solid rgba(128,128,128,0.5);"
            "border-radius: 3px;"
        )

    def _pick(self) -> None:
        dlg = QColorDialog(QColor(self._color), self)
        dlg.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, False)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            c = dlg.currentColor()
            if c.isValid():
                self.set_color(c.name())
                self._on_change()


class _ColorRow(QWidget):
    """Label + hex line edit + swatch button — one color token."""

    def __init__(self, label: str, hex_color: str, on_change, parent=None):
        super().__init__(parent)
        self._on_change = on_change
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.swatch = _ColorSwatch(hex_color, self._swatch_changed)
        self.hex_edit = QLineEdit(hex_color)
        self.hex_edit.setMaxLength(9)
        self.hex_edit.setFixedWidth(90)
        self.hex_edit.textChanged.connect(self._hex_typed)
        lbl = QLabel(label)
        lbl.setMinimumWidth(220)
        lay.addWidget(lbl)
        lay.addStretch()
        lay.addWidget(self.hex_edit)
        lay.addWidget(self.swatch)

    def _swatch_changed(self) -> None:
        # Sync hex edit to swatch
        self.hex_edit.blockSignals(True)
        self.hex_edit.setText(self.swatch.color())
        self.hex_edit.blockSignals(False)
        self._on_change()

    def _hex_typed(self, text: str) -> None:
        # Only accept valid #RRGGBB / #RGB
        if re.fullmatch(r"#[0-9a-fA-F]{3,8}", text):
            self.swatch.set_color(text)
            self._on_change()

    def value(self) -> str:
        return self.swatch.color()


class _NumericSlider(QWidget):
    """Slider + numeric label + range hint for an integer token."""

    def __init__(self, label: str, initial: int, lo: int, hi: int,
                 on_change, parent=None):
        super().__init__(parent)
        self._on_change = on_change
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(label)
        lbl.setMinimumWidth(220)
        # radius_pill range is huge → use logarithmic-style stepping
        if hi > 100:
            display_max = min(hi, 50)  # for sliders, clamp visible to 50
            self._stretch_to_full = (hi == 999)
        else:
            display_max = hi
            self._stretch_to_full = False
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(lo, display_max)
        clamped = min(initial, display_max) if not self._stretch_to_full else (
            display_max if initial > display_max else initial
        )
        self.slider.setValue(clamped)
        self.value_lbl = QLabel(str(initial))
        self.value_lbl.setFixedWidth(40)
        self.slider.valueChanged.connect(self._on_slider)
        lay.addWidget(lbl)
        lay.addWidget(self.slider, 1)
        lay.addWidget(self.value_lbl)
        self._actual = initial

    def _on_slider(self, v: int) -> None:
        # For pill: snap to 999 if at max
        if self._stretch_to_full and v == self.slider.maximum():
            self._actual = 999
        else:
            self._actual = v
        self.value_lbl.setText(str(self._actual))
        self._on_change()

    def value(self) -> int:
        return self._actual


# ─── Main dialog ─────────────────────────────────────────────────────
class ThemeEditorDialog(QDialog):
    """Visual editor for a ThemePack. Mutates a working copy and
    applies changes to the QApplication on every edit. Save persists
    to ~/.config/themeforge/themes/<slug>.json; Cancel restores the
    theme that was active when the dialog opened."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("✏️ Personalizar tema")
        self.resize(720, 720)

        # Capture the active theme as the "original" to restore on cancel
        self._original_name = themes.current_theme_name()
        self._original_pack = themes.load_theme(self._original_name)

        # Working copy starts as a clone of the original
        self._working = themes.load_theme(self._original_name)

        # ── Metadata ────────────────────────────────────────────────
        meta_box = QGroupBox("Metadatos")
        meta_form = QFormLayout()
        self.name_edit = QLineEdit(self._working.name + " (custom)")
        self.author_edit = QLineEdit(self._working.author or "pcreativedev")
        self.desc_edit = QLineEdit(self._working.description)
        self.dark_check = QCheckBox("Dark mode")
        self.dark_check.setChecked(self._working.is_dark)
        self.dark_check.stateChanged.connect(self._on_changed)
        meta_form.addRow("Nombre:", self.name_edit)
        meta_form.addRow("Autor:", self.author_edit)
        meta_form.addRow("Descripción:", self.desc_edit)
        meta_form.addRow("", self.dark_check)
        meta_box.setLayout(meta_form)

        # ── Colors ──────────────────────────────────────────────────
        self._color_rows: dict[str, _ColorRow] = {}
        color_outer = QVBoxLayout()
        for group_label, tokens in _COLOR_GROUPS:
            sub = QGroupBox(group_label)
            sub_lay = QVBoxLayout()
            for attr, label in tokens:
                row = _ColorRow(
                    label,
                    getattr(self._working.color, attr),
                    self._on_changed,
                )
                self._color_rows[attr] = row
                sub_lay.addWidget(row)
            sub.setLayout(sub_lay)
            color_outer.addWidget(sub)
        color_box = QGroupBox("Colores")
        color_box.setLayout(color_outer)

        # ── Shape ───────────────────────────────────────────────────
        self._shape_sliders: dict[str, _NumericSlider] = {}
        shape_lay = QVBoxLayout()
        for attr, label, lo, hi in _SHAPE_RANGES:
            sl = _NumericSlider(
                label, getattr(self._working.shape, attr), lo, hi,
                self._on_changed,
            )
            self._shape_sliders[attr] = sl
            shape_lay.addWidget(sl)
        shape_box = QGroupBox("Forma")
        shape_box.setLayout(shape_lay)

        # ── Components ──────────────────────────────────────────────
        self._component_combos: dict[str, QComboBox] = {}
        comp_form = QFormLayout()
        for attr, label, options in _COMPONENT_OPTIONS:
            cb = QComboBox()
            cb.addItems(options)
            current = getattr(self._working.components, attr)
            if current in options:
                cb.setCurrentText(current)
            cb.currentTextChanged.connect(lambda _v, a=attr: self._on_changed())
            self._component_combos[attr] = cb
            comp_form.addRow(label + ":", cb)
        comp_box = QGroupBox("Componentes")
        comp_box.setLayout(comp_form)

        # ── Scroll wrapper ──────────────────────────────────────────
        scroll_content = QWidget()
        sc_lay = QVBoxLayout(scroll_content)
        sc_lay.addWidget(meta_box)
        sc_lay.addWidget(color_box)
        sc_lay.addWidget(shape_box)
        sc_lay.addWidget(comp_box)
        sc_lay.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(scroll_content)

        # ── Footer ──────────────────────────────────────────────────
        hint = QLabel(
            "<small>Los cambios se aplican a toda la app al instante. "
            "Guarda para conservarlos como tema custom, o cancela para "
            "volver al tema actual.</small>"
        )
        hint.setWordWrap(True)
        hint.setTextFormat(Qt.TextFormat.RichText)

        bb = QDialogButtonBox(parent=self)
        self.btn_save = bb.addButton("💾 Guardar como…", QDialogButtonBox.ButtonRole.AcceptRole)
        self.btn_cancel = bb.addButton("Cancelar", QDialogButtonBox.ButtonRole.RejectRole)
        self.btn_save.clicked.connect(self._save)
        self.btn_cancel.clicked.connect(self._cancel)

        root = QVBoxLayout(self)
        root.addWidget(scroll, 1)
        root.addWidget(hint)
        root.addWidget(bb)

    # ── Live re-apply ───────────────────────────────────────────────
    def _build_working_pack(self) -> ThemePack:
        """Collects current widget values into a fresh ThemePack."""
        color_kwargs = {
            attr: row.value() for attr, row in self._color_rows.items()
        }
        shape_kwargs = {
            attr: sl.value() for attr, sl in self._shape_sliders.items()
        }
        component_kwargs = {
            attr: cb.currentText() for attr, cb in self._component_combos.items()
        }
        return ThemePack(
            name=self.name_edit.text().strip() or "Custom",
            is_dark=self.dark_check.isChecked(),
            author=self.author_edit.text().strip(),
            description=self.desc_edit.text().strip(),
            color=ColorTokens(**color_kwargs),
            typography=self._working.typography,  # not editable in v1
            spacing=self._working.spacing,
            shape=ShapeTokens(**shape_kwargs),
            components=ComponentTokens(**component_kwargs),
        )

    def _on_changed(self) -> None:
        """Called by every widget on edit — rebuilds pack and applies."""
        try:
            self._working = self._build_working_pack()
            themes.apply_theme(QApplication.instance(), self._working)
            themes.clear_icon_cache()
            # Don't emit theme_changed — that would persist to settings.json
        except Exception as e:
            print(f"[theme_editor] preview failed: {e}")

    # ── Save / Cancel ───────────────────────────────────────────────
    def _save(self) -> None:
        pack = self._working
        default_slug = _slugify(pack.name)
        slug, ok = QInputDialog.getText(
            self, "Guardar tema",
            "Slug del tema (a-z, 0-9, guiones):",
            text=default_slug,
        )
        if not ok or not slug.strip():
            return
        slug = _slugify(slug)
        target = themes.ensure_user_themes_dir() / f"{slug}.json"
        if target.exists():
            r = QMessageBox.question(
                self, "Sobrescribir",
                f"Ya existe {target.name}. ¿Sobrescribir?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if r != QMessageBox.StandardButton.Yes:
                return
        try:
            target.write_text(
                json.dumps(asdict(pack), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            # Persist as the active theme so the Settings dropdown
            # picks it up.
            themes.save_current_theme(slug)
            themes.clear_icon_cache()
            themes.theme_signals.theme_changed.emit(slug)
            QMessageBox.information(
                self, "Guardado",
                f"Tema guardado en:\n{target}\n\n"
                "Aparecerá en el dropdown de Settings con el sufijo (custom).",
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error al guardar", str(e))

    def _cancel(self) -> None:
        """Restore the theme that was active when the dialog opened."""
        try:
            themes.apply_theme(QApplication.instance(), self._original_pack)
            themes.clear_icon_cache()
            themes.theme_signals.theme_changed.emit(self._original_name)
        except Exception as e:
            print(f"[theme_editor] restore failed: {e}")
        self.reject()
