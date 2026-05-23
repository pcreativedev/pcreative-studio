"""ThemeForge themes package — UI theming for the app itself.

Public API:

    from themes import apply_theme, load_theme, list_themes
    from themes import current_theme_name, save_current_theme

    # Apply on app startup:
    pack = load_theme(current_theme_name())
    apply_theme(app, pack)

    # User picks a different theme in Settings:
    pack = load_theme("dracula")
    apply_theme(app, pack)
    save_current_theme("dracula")
"""
from .tokens import (
    ThemePack, ColorTokens, TypographyTokens, SpacingTokens,
    ShapeTokens, ComponentTokens,
)
from .builder import apply_theme
from .registry import (
    list_themes,
    load_theme,
    current_theme_name,
    save_current_theme,
    ensure_user_themes_dir,
    ThemeInfo,
    DEFAULT_THEME_NAME,
    PRESETS_DIR,
    USER_THEMES_DIR,
)
from .icons import tf_icon, list_icons, clear_cache as clear_icon_cache

# ── Theme change signal ──────────────────────────────────────────────
# Emitted whenever the user picks a different theme. Widgets that
# cache theme-dependent visuals (e.g. tab icons) subscribe here to
# refresh themselves without a full window restart.
from PyQt6.QtCore import QObject, pyqtSignal


class _ThemeSignals(QObject):
    theme_changed = pyqtSignal(str)  # new theme name (e.g. "dracula")


theme_signals = _ThemeSignals()


__all__ = [
    "ThemePack", "ColorTokens", "TypographyTokens", "SpacingTokens",
    "ShapeTokens", "ComponentTokens",
    "apply_theme",
    "list_themes", "load_theme", "current_theme_name", "save_current_theme",
    "ensure_user_themes_dir", "ThemeInfo",
    "DEFAULT_THEME_NAME", "PRESETS_DIR", "USER_THEMES_DIR",
    "tf_icon", "list_icons", "clear_icon_cache",
    "theme_signals",
]
