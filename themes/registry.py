"""Theme discovery and loading.

Themes are JSON files. Two search paths:

  1. `themes/presets/*.json` in the repo (builtin themes shipped
     with ThemeForge).
  2. `~/.config/themeforge/themes/*.json` (user-installed / custom
     themes — take precedence on name collision).

Public API:

  - `list_themes()`       → [ThemeInfo(...)] sorted by name
  - `load_theme(name)`    → ThemePack
  - `current_theme_name()` → str saved in settings.json
  - `save_current_theme(name)` → persist selection
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .tokens import ThemePack


PRESETS_DIR = Path(__file__).parent / "presets"
USER_THEMES_DIR = Path.home() / ".config" / "themeforge" / "themes"
SETTINGS_PATH = Path.home() / ".config" / "themeforge" / "settings.json"
DEFAULT_THEME_NAME = "themeforge-dark"


@dataclass
class ThemeInfo:
    name: str         # filename without .json
    display_name: str # 'name' field from JSON, fallback to filename
    author: str
    is_dark: bool
    description: str
    path: Path
    is_user: bool     # True if from ~/.config, False if builtin


def _scan_dir(d: Path, is_user: bool) -> list[ThemeInfo]:
    if not d.is_dir():
        return []
    out: list[ThemeInfo] = []
    for f in sorted(d.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        out.append(ThemeInfo(
            name=f.stem,
            display_name=data.get("name", f.stem),
            author=data.get("author", ""),
            is_dark=bool(data.get("is_dark", True)),
            description=data.get("description", ""),
            path=f,
            is_user=is_user,
        ))
    return out


def list_themes() -> list[ThemeInfo]:
    """All themes (builtin first, then user-installed). User themes
    with the same `name` as a builtin override the builtin."""
    builtin = _scan_dir(PRESETS_DIR, is_user=False)
    user = _scan_dir(USER_THEMES_DIR, is_user=True)
    # Deduplicate by name (user wins)
    user_names = {t.name for t in user}
    deduped_builtin = [t for t in builtin if t.name not in user_names]
    combined = deduped_builtin + user
    combined.sort(key=lambda t: (not t.is_user, t.display_name.lower()))
    return combined


def load_theme(name: str) -> ThemePack:
    """Load a theme by name. Falls back to default if not found."""
    for t in list_themes():
        if t.name == name:
            data = json.loads(t.path.read_text(encoding="utf-8"))
            return ThemePack.from_dict(data)
    # Fallback: default
    default_path = PRESETS_DIR / f"{DEFAULT_THEME_NAME}.json"
    if default_path.is_file():
        return ThemePack.from_dict(json.loads(default_path.read_text(encoding="utf-8")))
    # Last resort: in-memory default (just instantiate ThemePack)
    return ThemePack(name="ThemeForge Dark")


def current_theme_name() -> str:
    """Read the saved theme name from settings.json. Returns the
    default if no setting exists yet."""
    try:
        if SETTINGS_PATH.is_file():
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            return data.get("theme", DEFAULT_THEME_NAME)
    except Exception:
        pass
    return DEFAULT_THEME_NAME


def save_current_theme(name: str) -> None:
    """Persist the user's theme choice. Creates settings.json if it
    doesn't exist."""
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    data: dict = {}
    if SETTINGS_PATH.is_file():
        try:
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    data["theme"] = name
    SETTINGS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def ensure_user_themes_dir() -> Path:
    """Ensures ~/.config/themeforge/themes/ exists and returns it.
    Useful for the future theme editor when saving custom themes."""
    USER_THEMES_DIR.mkdir(parents=True, exist_ok=True)
    return USER_THEMES_DIR
