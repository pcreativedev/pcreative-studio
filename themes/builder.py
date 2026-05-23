"""Theme application: ThemePack → (QPalette + QStyleSheet) → QApplication.

The QPalette controls fallback colors for native widgets that don't
match any QSS selector. The QSS string sets per-widget visuals on top.
Order matters: QSS overrides QPalette where both are set, so we apply
QPalette first then QSS.

References:
- https://doc.qt.io/qt-6/qpalette.html  (color roles)
- https://doc.qt.io/qt-6/stylesheet-reference.html (QSS spec)
"""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

from .tokens import ThemePack


def _qc(hex_str: str) -> QColor:
    """Hex → QColor with #RGBA support."""
    return QColor(hex_str)


def _build_palette(pack: ThemePack) -> QPalette:
    """Build a QPalette from theme color tokens.

    Maps our 21 color tokens to Qt's QPalette.ColorRole entries.
    Falls back to legitimate Qt defaults for roles we don't expose.
    """
    pal = QPalette()
    c = pack.color
    Role = QPalette.ColorRole
    Group = QPalette.ColorGroup

    # Window / background
    pal.setColor(Role.Window, _qc(c.bg_primary))
    pal.setColor(Role.Base, _qc(c.bg_secondary))
    pal.setColor(Role.AlternateBase, _qc(c.bg_tertiary))

    # Foreground / text
    pal.setColor(Role.WindowText, _qc(c.fg_primary))
    pal.setColor(Role.Text, _qc(c.fg_primary))
    pal.setColor(Role.PlaceholderText, _qc(c.fg_secondary))
    pal.setColor(Role.BrightText, _qc(c.fg_primary))

    # Buttons (native)
    pal.setColor(Role.Button, _qc(c.bg_tertiary))
    pal.setColor(Role.ButtonText, _qc(c.fg_primary))

    # Tooltips
    pal.setColor(Role.ToolTipBase, _qc(c.bg_elevated))
    pal.setColor(Role.ToolTipText, _qc(c.fg_primary))

    # Selection / highlight
    pal.setColor(Role.Highlight, _qc(c.selection_bg))
    pal.setColor(Role.HighlightedText, _qc(c.selection_fg))

    # Links
    pal.setColor(Role.Link, _qc(c.accent))
    pal.setColor(Role.LinkVisited, _qc(c.accent_active))

    # Disabled overrides — gray everything out coherently
    pal.setColor(Group.Disabled, Role.WindowText, _qc(c.fg_disabled))
    pal.setColor(Group.Disabled, Role.Text,       _qc(c.fg_disabled))
    pal.setColor(Group.Disabled, Role.ButtonText, _qc(c.fg_disabled))
    pal.setColor(Group.Disabled, Role.Highlight,  _qc(c.border))

    return pal


def _render_qss(pack: ThemePack) -> str:
    """Render the QSS stylesheet string from theme tokens.

    Selectors target every commonly-used Qt widget. The pattern is
    Material/Linear-inspired: minimal borders, soft radii, accent on
    interactive states.
    """
    c = pack.color
    t = pack.typography
    s = pack.spacing
    sh = pack.shape

    return f"""
/* ─── Base ───────────────────────────────────────────────── */
* {{
    font-family: {t.font_family};
    font-size: {t.size_base}pt;
    color: {c.fg_primary};
}}

QWidget {{
    background-color: {c.bg_primary};
    color: {c.fg_primary};
}}

QWidget:disabled {{
    color: {c.fg_disabled};
}}

/* ─── Containers ─────────────────────────────────────────── */
QFrame[frameShape="4"], /* HLine */
QFrame[frameShape="5"]  /* VLine */ {{
    background-color: {c.border};
    border: none;
}}

QGroupBox {{
    background-color: transparent;
    border: {sh.border_width}px solid {c.border};
    border-radius: {sh.radius_md}px;
    margin-top: {s.md}px;
    padding-top: {s.md}px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 {s.sm}px;
    color: {c.fg_secondary};
    font-weight: {t.weight_medium};
}}

/* ─── Buttons ────────────────────────────────────────────── */
QPushButton {{
    background-color: {c.bg_tertiary};
    color: {c.fg_primary};
    border: {sh.border_width}px solid {c.border};
    border-radius: {sh.radius_sm}px;
    padding: {s.sm}px {s.md}px;
    font-weight: {t.weight_medium};
}}
QPushButton:hover {{
    background-color: {c.bg_elevated};
    border-color: {c.border_strong};
}}
QPushButton:pressed {{
    background-color: {c.bg_secondary};
}}
QPushButton:disabled {{
    color: {c.fg_disabled};
    background-color: {c.bg_secondary};
}}
QPushButton:default, QPushButton[primary="true"] {{
    background-color: {c.accent};
    color: {c.accent_fg};
    border-color: {c.accent};
}}
QPushButton:default:hover, QPushButton[primary="true"]:hover {{
    background-color: {c.accent_hover};
    border-color: {c.accent_hover};
}}

/* ─── Inputs ─────────────────────────────────────────────── */
QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background-color: {c.bg_secondary};
    color: {c.fg_primary};
    border: {sh.border_width}px solid {c.border};
    border-radius: {sh.radius_sm}px;
    padding: {s.xs}px {s.sm}px;
    selection-background-color: {c.selection_bg};
    selection-color: {c.selection_fg};
}}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QComboBox:focus,
QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {c.accent};
}}
QComboBox::drop-down {{
    border: none;
    width: 18px;
}}
QComboBox QAbstractItemView {{
    background-color: {c.bg_elevated};
    color: {c.fg_primary};
    border: {sh.border_width}px solid {c.border_strong};
    selection-background-color: {c.selection_bg};
}}

/* ─── Tabs ───────────────────────────────────────────────── */
QTabWidget::pane {{
    background-color: {c.bg_primary};
    border: {sh.border_width}px solid {c.border};
    border-radius: {sh.radius_md}px;
    top: -{sh.border_width}px;
}}
QTabBar::tab {{
    background-color: {c.bg_secondary};
    color: {c.fg_secondary};
    padding: {s.sm}px {s.lg}px;
    border: {sh.border_width}px solid {c.border};
    border-bottom: none;
    border-top-left-radius: {sh.radius_sm}px;
    border-top-right-radius: {sh.radius_sm}px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background-color: {c.bg_primary};
    color: {c.fg_primary};
    border-bottom: {sh.border_width}px solid {c.bg_primary};
}}
QTabBar::tab:hover:!selected {{
    background-color: {c.bg_tertiary};
    color: {c.fg_primary};
}}

/* ─── Lists / Trees / Tables ─────────────────────────────── */
QListView, QTreeView, QTableView, QListWidget, QTreeWidget, QTableWidget {{
    background-color: {c.bg_secondary};
    color: {c.fg_primary};
    border: {sh.border_width}px solid {c.border};
    border-radius: {sh.radius_sm}px;
    alternate-background-color: {c.bg_tertiary};
    gridline-color: {c.border};
}}
QListView::item:selected, QTreeView::item:selected,
QTableView::item:selected, QListWidget::item:selected {{
    background-color: {c.selection_bg};
    color: {c.selection_fg};
}}
QListView::item:hover, QTreeView::item:hover, QListWidget::item:hover {{
    background-color: {c.bg_elevated};
}}
QHeaderView::section {{
    background-color: {c.bg_tertiary};
    color: {c.fg_secondary};
    padding: {s.xs}px {s.sm}px;
    border: none;
    border-right: {sh.border_width}px solid {c.border};
    font-weight: {t.weight_medium};
}}

/* ─── Scrollbars (slim, modern) ──────────────────────────── */
QScrollBar:vertical {{
    background-color: {c.scrollbar_bg};
    width: 12px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background-color: {c.scrollbar_thumb};
    min-height: 30px;
    border-radius: 6px;
    margin: 2px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {c.fg_secondary};
}}
QScrollBar:horizontal {{
    background-color: {c.scrollbar_bg};
    height: 12px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background-color: {c.scrollbar_thumb};
    min-width: 30px;
    border-radius: 6px;
    margin: 2px;
}}
QScrollBar::handle:horizontal:hover {{
    background-color: {c.fg_secondary};
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    background: none;
    border: none;
    height: 0;
    width: 0;
}}

/* ─── Checkboxes / Radio buttons ─────────────────────────── */
QCheckBox, QRadioButton {{
    color: {c.fg_primary};
    spacing: {s.sm}px;
}}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 14px;
    height: 14px;
    border: {sh.border_width}px solid {c.border_strong};
    background-color: {c.bg_secondary};
}}
QCheckBox::indicator {{
    border-radius: {sh.radius_sm}px;
}}
QRadioButton::indicator {{
    border-radius: 7px;
}}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background-color: {c.accent};
    border-color: {c.accent};
}}
QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
    border-color: {c.accent};
}}

/* ─── Progress bars / Sliders ────────────────────────────── */
QProgressBar {{
    background-color: {c.bg_secondary};
    border: {sh.border_width}px solid {c.border};
    border-radius: {sh.radius_sm}px;
    text-align: center;
    color: {c.fg_primary};
}}
QProgressBar::chunk {{
    background-color: {c.accent};
    border-radius: {sh.radius_sm}px;
}}
QSlider::groove:horizontal {{
    background: {c.bg_tertiary};
    height: 4px;
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {c.accent};
    width: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}

/* ─── Menus / Tooltips ───────────────────────────────────── */
QMenu {{
    background-color: {c.bg_elevated};
    color: {c.fg_primary};
    border: {sh.border_width}px solid {c.border_strong};
    border-radius: {sh.radius_md}px;
    padding: {s.xs}px;
}}
QMenu::item {{
    padding: {s.xs}px {s.md}px;
    border-radius: {sh.radius_sm}px;
}}
QMenu::item:selected {{
    background-color: {c.accent};
    color: {c.accent_fg};
}}
QMenu::separator {{
    height: {sh.border_width}px;
    background-color: {c.border};
    margin: {s.xs}px {s.sm}px;
}}
QToolTip {{
    background-color: {c.bg_elevated};
    color: {c.fg_primary};
    border: {sh.border_width}px solid {c.border_strong};
    border-radius: {sh.radius_sm}px;
    padding: {s.xs}px {s.sm}px;
}}

/* ─── Status / dock / splitter ───────────────────────────── */
QStatusBar {{
    background-color: {c.bg_secondary};
    color: {c.fg_secondary};
}}
QStatusBar::item {{
    border: none;
}}
QSplitter::handle {{
    background-color: {c.border};
}}
QSplitter::handle:horizontal {{
    width: {sh.border_width}px;
}}
QSplitter::handle:vertical {{
    height: {sh.border_width}px;
}}
QDockWidget {{
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}}
QDockWidget::title {{
    background-color: {c.bg_secondary};
    padding: {s.xs}px;
}}

/* ─── Dialogs ────────────────────────────────────────────── */
QDialog {{
    background-color: {c.bg_primary};
}}
QMessageBox {{
    background-color: {c.bg_primary};
}}

/* ─── Mono font for code-like widgets ────────────────────── */
QPlainTextEdit, QTextEdit[mono="true"] {{
    font-family: {t.font_family_mono};
}}
"""


def apply_theme(app: QApplication, pack: ThemePack) -> None:
    """Apply a theme to the running QApplication.

    Sets QPalette first (so native widgets without QSS selectors
    behave) then QStyleSheet on top. Safe to call repeatedly — Qt
    repaints the widget tree.
    """
    app.setStyle("Fusion")            # uniform base across platforms
    app.setPalette(_build_palette(pack))
    app.setStyleSheet(_render_qss(pack))
