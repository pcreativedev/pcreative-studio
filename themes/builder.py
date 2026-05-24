"""Theme application: ThemePack → (QPalette + QStyleSheet) → QApplication.

The QPalette controls fallback colors for native widgets that don't
match any QSS selector. The QSS string sets per-widget visuals on top.
Order matters: QSS overrides QPalette where both are set, so we apply
QPalette first then QSS.

The QSS is assembled from per-widget dispatchers (`_qss_button`,
`_qss_tab`, etc.) that emit different rules depending on the
component variant set in the ThemePack (`pack.components.*`). This
keeps each variant readable as its own rule block rather than a
giant conditional template.

References:
- https://doc.qt.io/qt-6/qpalette.html  (color roles)
- https://doc.qt.io/qt-6/stylesheet-reference.html (QSS spec)
"""
from __future__ import annotations

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

from .tokens import ThemePack


def _qc(hex_str: str) -> QColor:
    return QColor(hex_str)


def _build_palette(pack: ThemePack) -> QPalette:
    """Map our 21 color tokens to Qt's QPalette.ColorRole entries.
    Falls back to legitimate Qt defaults for roles we don't expose."""
    pal = QPalette()
    c = pack.color
    Role = QPalette.ColorRole
    Group = QPalette.ColorGroup

    pal.setColor(Role.Window, _qc(c.bg_primary))
    pal.setColor(Role.Base, _qc(c.bg_secondary))
    pal.setColor(Role.AlternateBase, _qc(c.bg_tertiary))
    pal.setColor(Role.WindowText, _qc(c.fg_primary))
    pal.setColor(Role.Text, _qc(c.fg_primary))
    pal.setColor(Role.PlaceholderText, _qc(c.fg_secondary))
    pal.setColor(Role.BrightText, _qc(c.fg_primary))
    pal.setColor(Role.Button, _qc(c.bg_tertiary))
    pal.setColor(Role.ButtonText, _qc(c.fg_primary))
    pal.setColor(Role.ToolTipBase, _qc(c.bg_elevated))
    pal.setColor(Role.ToolTipText, _qc(c.fg_primary))
    pal.setColor(Role.Highlight, _qc(c.selection_bg))
    pal.setColor(Role.HighlightedText, _qc(c.selection_fg))
    pal.setColor(Role.Link, _qc(c.accent))
    pal.setColor(Role.LinkVisited, _qc(c.accent_active))

    pal.setColor(Group.Disabled, Role.WindowText, _qc(c.fg_disabled))
    pal.setColor(Group.Disabled, Role.Text,       _qc(c.fg_disabled))
    pal.setColor(Group.Disabled, Role.ButtonText, _qc(c.fg_disabled))
    pal.setColor(Group.Disabled, Role.Highlight,  _qc(c.border))

    return pal


# ─────────────────── density helper ─────────────────────────────────
def _density_scale(density: str) -> tuple[int, int]:
    """Returns (extra_padding_v, extra_padding_h) modifier per density.
    compact = tighter spacing; spacious = more breathing room."""
    if density == "compact":
        return (-2, -2)
    if density == "spacious":
        return (4, 6)
    return (0, 0)


# ─────────────────── per-widget dispatchers ────────────────────────
def _qss_button(c, t, s, sh, v) -> str:
    """Variants: flat | raised | pill | brutalist | ghost"""
    dv, dh = _density_scale(v.density)
    pad_v = max(2, s.sm + dv)
    pad_h = max(6, s.md + dh)

    if v.button_variant == "pill":
        return f"""
QPushButton {{
    background-color: {c.bg_tertiary};
    color: {c.fg_primary};
    border: {sh.border_width}px solid {c.border};
    border-radius: {sh.radius_pill}px;
    padding: {pad_v}px {pad_h + s.md}px;
    font-weight: {t.weight_medium};
}}
QPushButton:hover {{ background-color: {c.bg_elevated}; border-color: {c.accent}; }}
QPushButton:pressed {{ background-color: {c.bg_secondary}; }}
QPushButton:disabled {{ color: {c.fg_disabled}; background-color: {c.bg_secondary}; }}
QPushButton:default {{ background-color: {c.accent}; color: {c.accent_fg}; border-color: {c.accent}; }}
QPushButton:default:hover {{ background-color: {c.accent_hover}; }}
"""

    if v.button_variant == "brutalist":
        bw = max(2, sh.border_width * 2)
        return f"""
QPushButton {{
    background-color: {c.bg_tertiary};
    color: {c.fg_primary};
    border: {bw}px solid {c.fg_primary};
    border-radius: 0px;
    padding: {pad_v}px {pad_h}px;
    font-weight: {t.weight_bold};
    text-transform: uppercase;
}}
QPushButton:hover {{ background-color: {c.accent}; color: {c.accent_fg}; }}
QPushButton:pressed {{ background-color: {c.fg_primary}; color: {c.bg_primary}; }}
QPushButton:disabled {{ color: {c.fg_disabled}; border-color: {c.fg_disabled}; }}
QPushButton:default {{ background-color: {c.accent}; color: {c.accent_fg}; border-color: {c.fg_primary}; }}
"""

    if v.button_variant == "ghost":
        return f"""
QPushButton {{
    background-color: transparent;
    color: {c.accent};
    border: {sh.border_width}px solid transparent;
    border-radius: {sh.radius_sm}px;
    padding: {pad_v}px {pad_h}px;
    font-weight: {t.weight_medium};
}}
QPushButton:hover {{ background-color: {c.bg_tertiary}; color: {c.accent_hover}; }}
QPushButton:pressed {{ background-color: {c.bg_secondary}; }}
QPushButton:disabled {{ color: {c.fg_disabled}; }}
QPushButton:default {{ background-color: {c.accent}; color: {c.accent_fg}; }}
"""

    if v.button_variant == "raised":
        return f"""
QPushButton {{
    background-color: {c.bg_elevated};
    color: {c.fg_primary};
    border: {sh.border_width}px solid {c.border_strong};
    border-radius: {sh.radius_md}px;
    padding: {pad_v}px {pad_h}px;
    font-weight: {t.weight_medium};
}}
QPushButton:hover {{ background-color: {c.bg_tertiary}; }}
QPushButton:pressed {{ background-color: {c.bg_secondary}; padding-top: {pad_v + 1}px; }}
QPushButton:disabled {{ color: {c.fg_disabled}; }}
QPushButton:default {{ background-color: {c.accent}; color: {c.accent_fg}; border-color: {c.accent}; }}
QPushButton:default:hover {{ background-color: {c.accent_hover}; }}
"""

    # default: flat
    return f"""
QPushButton {{
    background-color: {c.bg_tertiary};
    color: {c.fg_primary};
    border: {sh.border_width}px solid {c.border};
    border-radius: {sh.radius_sm}px;
    padding: {pad_v}px {pad_h}px;
    font-weight: {t.weight_medium};
}}
QPushButton:hover {{ background-color: {c.bg_elevated}; border-color: {c.border_strong}; }}
QPushButton:pressed {{ background-color: {c.bg_secondary}; }}
QPushButton:disabled {{ color: {c.fg_disabled}; background-color: {c.bg_secondary}; }}
QPushButton:default {{ background-color: {c.accent}; color: {c.accent_fg}; border-color: {c.accent}; }}
QPushButton:default:hover {{ background-color: {c.accent_hover}; }}
"""


def _qss_tab(c, t, s, sh, v) -> str:
    """Variants: underline | card | pill | segmented"""
    if v.tab_variant == "card":
        return f"""
QTabWidget::pane {{ background-color: {c.bg_primary}; border: none; top: 4px; }}
QTabBar::tab {{
    background-color: {c.bg_secondary};
    color: {c.fg_secondary};
    padding: {s.sm}px {s.lg}px;
    border: {sh.border_width}px solid {c.border};
    border-radius: {sh.radius_md}px;
    margin-right: {s.xs}px;
    font-weight: {t.weight_medium};
}}
QTabBar::tab:selected {{ background-color: {c.bg_elevated}; color: {c.fg_primary}; border-color: {c.accent}; }}
QTabBar::tab:hover:!selected {{ background-color: {c.bg_tertiary}; color: {c.fg_primary}; }}
"""

    if v.tab_variant == "pill":
        return f"""
QTabWidget::pane {{ background-color: {c.bg_primary}; border: none; top: 4px; }}
QTabBar::tab {{
    background-color: transparent;
    color: {c.fg_secondary};
    padding: {s.sm}px {s.lg}px;
    border: none;
    border-radius: {sh.radius_pill}px;
    margin-right: {s.xs}px;
    font-weight: {t.weight_medium};
}}
QTabBar::tab:selected {{ background-color: {c.accent}; color: {c.accent_fg}; }}
QTabBar::tab:hover:!selected {{ background-color: {c.bg_tertiary}; color: {c.fg_primary}; }}
"""

    if v.tab_variant == "segmented":
        return f"""
QTabWidget::pane {{ background-color: {c.bg_primary}; border: none; top: 2px; }}
QTabBar {{ qproperty-drawBase: 0; background-color: {c.bg_secondary}; border-radius: {sh.radius_md}px; }}
QTabBar::tab {{
    background-color: transparent;
    color: {c.fg_secondary};
    padding: {s.xs}px {s.md}px;
    border: none;
    border-radius: {sh.radius_sm}px;
    margin: 2px;
    font-weight: {t.weight_medium};
}}
QTabBar::tab:selected {{ background-color: {c.bg_elevated}; color: {c.fg_primary}; }}
QTabBar::tab:hover:!selected {{ background-color: {c.bg_tertiary}; color: {c.fg_primary}; }}
"""

    # default: underline
    return f"""
QTabWidget::pane {{
    background-color: {c.bg_primary};
    border: none;
    border-top: {sh.border_width}px solid {c.border};
    top: -{sh.border_width}px;
}}
QTabBar::tab {{
    background-color: transparent;
    color: {c.fg_secondary};
    padding: {s.sm}px {s.lg}px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: {s.sm}px;
    font-weight: {t.weight_medium};
}}
QTabBar::tab:selected {{ color: {c.accent}; border-bottom-color: {c.accent}; }}
QTabBar::tab:hover:!selected {{ color: {c.fg_primary}; }}
"""


def _qss_input(c, t, s, sh, v) -> str:
    """Variants: outlined | filled | underlined | brutalist"""
    pad_v = s.xs if v.density == "compact" else s.sm

    if v.input_variant == "filled":
        return f"""
QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background-color: {c.bg_tertiary};
    color: {c.fg_primary};
    border: none;
    border-bottom: 2px solid {c.border};
    border-radius: {sh.radius_sm}px;
    border-bottom-left-radius: 0;
    border-bottom-right-radius: 0;
    padding: {pad_v}px {s.sm}px;
    selection-background-color: {c.selection_bg};
    selection-color: {c.selection_fg};
}}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QComboBox:focus,
QSpinBox:focus, QDoubleSpinBox:focus {{ border-bottom-color: {c.accent}; }}
QComboBox::drop-down {{ border: none; width: 22px; subcontrol-position: right center; }}
QComboBox::down-arrow {{ image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid {c.fg_secondary}; width: 0; height: 0; margin-right: 6px; }}
QComboBox::down-arrow:on {{ border-top: none; border-bottom: 5px solid {c.accent}; }}
QComboBox QAbstractItemView {{ background-color: {c.bg_elevated}; color: {c.fg_primary}; border: {sh.border_width}px solid {c.border_strong}; selection-background-color: {c.selection_bg}; outline: 0; padding: {s.xs}px; }}
QComboBox QAbstractItemView::item {{ min-height: 22px; padding: {s.xs}px {s.sm}px; }}
"""

    if v.input_variant == "underlined":
        return f"""
QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background-color: transparent;
    color: {c.fg_primary};
    border: none;
    border-bottom: {sh.border_width}px solid {c.border};
    border-radius: 0;
    padding: {pad_v}px 0;
    selection-background-color: {c.selection_bg};
    selection-color: {c.selection_fg};
}}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QComboBox:focus,
QSpinBox:focus, QDoubleSpinBox:focus {{ border-bottom-color: {c.accent}; border-bottom-width: 2px; }}
QComboBox::drop-down {{ border: none; width: 22px; subcontrol-position: right center; }}
QComboBox::down-arrow {{ image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid {c.fg_secondary}; width: 0; height: 0; margin-right: 6px; }}
QComboBox::down-arrow:on {{ border-top: none; border-bottom: 5px solid {c.accent}; }}
QComboBox QAbstractItemView {{ background-color: {c.bg_elevated}; color: {c.fg_primary}; border: {sh.border_width}px solid {c.border_strong}; selection-background-color: {c.selection_bg}; outline: 0; padding: {s.xs}px; }}
QComboBox QAbstractItemView::item {{ min-height: 22px; padding: {s.xs}px {s.sm}px; }}
"""

    if v.input_variant == "brutalist":
        bw = max(2, sh.border_width * 2)
        return f"""
QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background-color: {c.bg_primary};
    color: {c.fg_primary};
    border: {bw}px solid {c.fg_primary};
    border-radius: 0;
    padding: {pad_v}px {s.sm}px;
    selection-background-color: {c.accent};
    selection-color: {c.accent_fg};
}}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QComboBox:focus,
QSpinBox:focus, QDoubleSpinBox:focus {{ border-color: {c.accent}; }}
QComboBox::drop-down {{ border-left: {bw}px solid {c.fg_primary}; width: 24px; subcontrol-position: right center; }}
QComboBox::down-arrow {{ image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 7px solid {c.fg_primary}; width: 0; height: 0; margin-right: 6px; }}
QComboBox::down-arrow:on {{ border-top: none; border-bottom: 7px solid {c.accent}; }}
QComboBox QAbstractItemView {{ background-color: {c.bg_primary}; color: {c.fg_primary}; border: {bw}px solid {c.fg_primary}; selection-background-color: {c.accent}; selection-color: {c.accent_fg}; outline: 0; padding: 0; }}
QComboBox QAbstractItemView::item {{ min-height: 24px; padding: {s.xs}px {s.sm}px; }}
"""

    # default: outlined
    return f"""
QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background-color: {c.bg_secondary};
    color: {c.fg_primary};
    border: {sh.border_width}px solid {c.border};
    border-radius: {sh.radius_sm}px;
    padding: {pad_v}px {s.sm}px;
    selection-background-color: {c.selection_bg};
    selection-color: {c.selection_fg};
}}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QComboBox:focus,
QSpinBox:focus, QDoubleSpinBox:focus {{ border-color: {c.accent}; }}
QComboBox::drop-down {{ border: none; width: 22px; subcontrol-position: right center; }}
QComboBox::down-arrow {{ image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid {c.fg_secondary}; width: 0; height: 0; margin-right: 6px; }}
QComboBox::down-arrow:on {{ border-top: none; border-bottom: 5px solid {c.accent}; }}
QComboBox QAbstractItemView {{ background-color: {c.bg_elevated}; color: {c.fg_primary}; border: {sh.border_width}px solid {c.border_strong}; selection-background-color: {c.selection_bg}; outline: 0; padding: {s.xs}px; }}
QComboBox QAbstractItemView::item {{ min-height: 22px; padding: {s.xs}px {s.sm}px; }}
"""


def _qss_scrollbar(c, sh, v) -> str:
    """Variants: thin | thick | hidden"""
    if v.scrollbar_variant == "hidden":
        return """
QScrollBar:vertical, QScrollBar:horizontal { background: transparent; width: 0; height: 0; }
QScrollBar::handle { background: transparent; }
QScrollBar::add-line, QScrollBar::sub-line { background: none; border: none; height: 0; width: 0; }
"""

    if v.scrollbar_variant == "thick":
        return f"""
QScrollBar:vertical {{ background-color: {c.scrollbar_bg}; width: 16px; margin: 0; }}
QScrollBar::handle:vertical {{ background-color: {c.scrollbar_thumb}; min-height: 30px; border-radius: 4px; margin: 2px; }}
QScrollBar::handle:vertical:hover {{ background-color: {c.fg_secondary}; }}
QScrollBar:horizontal {{ background-color: {c.scrollbar_bg}; height: 16px; margin: 0; }}
QScrollBar::handle:horizontal {{ background-color: {c.scrollbar_thumb}; min-width: 30px; border-radius: 4px; margin: 2px; }}
QScrollBar::handle:horizontal:hover {{ background-color: {c.fg_secondary}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ background: none; border: none; height: 0; width: 0; }}
"""

    # default: thin
    return f"""
QScrollBar:vertical {{ background-color: {c.scrollbar_bg}; width: 10px; margin: 0; }}
QScrollBar::handle:vertical {{ background-color: {c.scrollbar_thumb}; min-height: 30px; border-radius: 5px; margin: 2px; }}
QScrollBar::handle:vertical:hover {{ background-color: {c.fg_secondary}; }}
QScrollBar:horizontal {{ background-color: {c.scrollbar_bg}; height: 10px; margin: 0; }}
QScrollBar::handle:horizontal {{ background-color: {c.scrollbar_thumb}; min-width: 30px; border-radius: 5px; margin: 2px; }}
QScrollBar::handle:horizontal:hover {{ background-color: {c.fg_secondary}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ background: none; border: none; height: 0; width: 0; }}
"""


def _qss_checkbox(c, sh, v) -> str:
    """Variants: square | rounded | pill"""
    radius = {"square": "0", "rounded": f"{sh.radius_sm}px", "pill": "7px"}.get(
        v.checkbox_variant, f"{sh.radius_sm}px"
    )
    return f"""
QCheckBox, QRadioButton {{ color: {c.fg_primary}; spacing: 8px; }}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 14px; height: 14px;
    border: {sh.border_width}px solid {c.border_strong};
    background-color: {c.bg_secondary};
}}
QCheckBox::indicator {{ border-radius: {radius}; }}
QRadioButton::indicator {{ border-radius: 7px; }}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background-color: {c.accent}; border-color: {c.accent};
}}
QCheckBox::indicator:hover, QRadioButton::indicator:hover {{ border-color: {c.accent}; }}
"""


# ─────────────────── master assembly ───────────────────────────────
def _qss_base(c, t, s, sh) -> str:
    """Common QSS that doesn't change with component variants."""
    return f"""
* {{ font-family: {t.font_family}; font-size: {t.size_base}pt; color: {c.fg_primary}; }}
QWidget {{ background-color: {c.bg_primary}; color: {c.fg_primary}; }}
QWidget:disabled {{ color: {c.fg_disabled}; }}

QFrame[frameShape="4"], QFrame[frameShape="5"] {{ background-color: {c.border}; border: none; }}

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
    background-color: {c.selection_bg}; color: {c.selection_fg};
}}
QListView::item:hover, QTreeView::item:hover, QListWidget::item:hover {{ background-color: {c.bg_elevated}; }}
QHeaderView::section {{
    background-color: {c.bg_tertiary};
    color: {c.fg_secondary};
    padding: {s.xs}px {s.sm}px;
    border: none;
    border-right: {sh.border_width}px solid {c.border};
    font-weight: {t.weight_medium};
}}

QProgressBar {{
    background-color: {c.bg_secondary};
    border: {sh.border_width}px solid {c.border};
    border-radius: {sh.radius_sm}px;
    text-align: center;
    color: {c.fg_primary};
}}
QProgressBar::chunk {{ background-color: {c.accent}; border-radius: {sh.radius_sm}px; }}

QSlider::groove:horizontal {{ background: {c.bg_tertiary}; height: 4px; border-radius: 2px; }}
QSlider::handle:horizontal {{ background: {c.accent}; width: 14px; margin: -5px 0; border-radius: 7px; }}

QMenu {{
    background-color: {c.bg_elevated};
    color: {c.fg_primary};
    border: {sh.border_width}px solid {c.border_strong};
    border-radius: {sh.radius_md}px;
    padding: {s.xs}px;
}}
QMenu::item {{ padding: {s.xs}px {s.md}px; border-radius: {sh.radius_sm}px; }}
QMenu::item:selected {{ background-color: {c.accent}; color: {c.accent_fg}; }}
QMenu::separator {{ height: {sh.border_width}px; background-color: {c.border}; margin: {s.xs}px {s.sm}px; }}

QToolTip {{
    background-color: {c.bg_elevated};
    color: {c.fg_primary};
    border: {sh.border_width}px solid {c.border_strong};
    border-radius: {sh.radius_sm}px;
    padding: {s.xs}px {s.sm}px;
}}

QStatusBar {{ background-color: {c.bg_secondary}; color: {c.fg_secondary}; }}
QStatusBar::item {{ border: none; }}
QSplitter::handle {{ background-color: {c.border}; }}
QSplitter::handle:horizontal {{ width: {sh.border_width}px; }}
QSplitter::handle:vertical   {{ height: {sh.border_width}px; }}
QDockWidget::title {{ background-color: {c.bg_secondary}; padding: {s.xs}px; }}

QDialog, QMessageBox {{ background-color: {c.bg_primary}; }}
QPlainTextEdit, QTextEdit[mono="true"] {{ font-family: {t.font_family_mono}; }}
"""


def _render_qss(pack: ThemePack) -> str:
    c, t, s, sh, v = pack.color, pack.typography, pack.spacing, pack.shape, pack.components
    parts = [
        _qss_base(c, t, s, sh),
        _qss_button(c, t, s, sh, v),
        _qss_tab(c, t, s, sh, v),
        _qss_input(c, t, s, sh, v),
        _qss_scrollbar(c, sh, v),
        _qss_checkbox(c, sh, v),
    ]
    return "\n".join(parts)


def apply_theme(app: QApplication, pack: ThemePack) -> None:
    """Apply a theme to the running QApplication.

    Sets QPalette first (so native widgets without QSS selectors
    behave) then QStyleSheet on top. Safe to call repeatedly — Qt
    repaints the widget tree.
    """
    app.setStyle("Fusion")
    app.setPalette(_build_palette(pack))
    app.setStyleSheet(_render_qss(pack))
