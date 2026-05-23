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
from .tokens import ThemePack, ColorTokens, TypographyTokens, SpacingTokens, ShapeTokens
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

__all__ = [
    "ThemePack", "ColorTokens", "TypographyTokens", "SpacingTokens", "ShapeTokens",
    "apply_theme",
    "list_themes", "load_theme", "current_theme_name", "save_current_theme",
    "ensure_user_themes_dir", "ThemeInfo",
    "DEFAULT_THEME_NAME", "PRESETS_DIR", "USER_THEMES_DIR",
]
