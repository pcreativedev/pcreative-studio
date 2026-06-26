"""Icon registry — theme-aware SVG icons.

Currently ships Lucide icons (ISC license). Each icon is referenced
by a semantic name (`tf_icon("rocket")`) that maps to a Lucide SVG
filename. At render time the SVG's `currentColor` placeholder is
replaced with the theme's foreground color, so icons automatically
recolor when the theme changes.

Public API:

    tf_icon(name, color="#e6e6e6", size=16) -> QIcon
    clear_cache()  # call on theme change

Adding a new icon family in the future:
1. Drop the SVG set into `assets/icons/<family>/*.svg`
2. Add a sibling map (e.g. `HEROICONS_MAP`)
3. Extend `tf_icon` with an optional `family` arg
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer


_LUCIDE_DIR = Path(__file__).parent.parent / "assets" / "icons" / "lucide"


# Semantic name → Lucide filename (without `.svg`)
ICON_MAP_LUCIDE: dict[str, str] = {
    # Common actions
    "search":        "search",
    "settings":      "settings",
    "save":          "save",
    "copy":          "copy",
    "download":      "download",
    "trash":         "trash-2",
    "edit":          "pen-tool",
    "refresh":       "refresh-cw",
    "plus":          "plus",
    "minus":         "minus",
    "check":         "check",
    "x":             "x",
    "external_link": "external-link",
    "chevron_right": "chevron-right",
    "chevron_down":  "chevron-down",
    # Files / folders
    "folder":        "folder",
    "folder_open":   "folder-open",
    "file":          "file",
    "file_text":     "file-text",
    "image":         "image",
    "archive":       "archive",
    "package":       "package",
    # Status / feedback
    "warning":       "triangle-alert",
    "info":          "info",
    # Code / dev
    "code":          "code",
    "terminal":      "terminal",
    "github":        "globe",       # fallback (Lucide removed pure github icon)
    "monitor":       "monitor",
    # Run / control
    "play":          "play",
    "stop":          "square",
    "rocket":        "rocket",
    # Pcreative Studio tabs / domains
    "box":           "box",
    "gallery":       "grid-2x2",
    "dollar":        "dollar-sign",
    "users":         "users",
    "key":           "key",
    "sparkles":      "sparkles",
    "palette":       "palette",
    "globe":         "globe",
}


_CACHE: dict[tuple, QIcon] = {}


def tf_icon(name: str, color: str = "#e6e6e6", size: int = 16) -> QIcon:
    """Returns a QIcon for the semantic name `name`, rendered with the
    given hex color at the given pixel size. Result is cached by
    `(name, color, size)` so repeated calls are cheap.

    Unknown names fall back to the `globe` icon, then to an empty
    QIcon — never raises.
    """
    cache_key = (name, color, size)
    cached = _CACHE.get(cache_key)
    if cached is not None:
        return cached

    filename = ICON_MAP_LUCIDE.get(name, name)
    svg_path = _LUCIDE_DIR / f"{filename}.svg"
    if not svg_path.is_file():
        # Fallback to a known icon if mapping is missing
        svg_path = _LUCIDE_DIR / "globe.svg"
        if not svg_path.is_file():
            empty = QIcon()
            _CACHE[cache_key] = empty
            return empty

    try:
        svg_text = svg_path.read_text(encoding="utf-8")
        # Lucide stroke is `currentColor` by convention
        svg_text = svg_text.replace("currentColor", color)
        renderer = QSvgRenderer(QByteArray(svg_text.encode("utf-8")))
    except Exception:
        empty = QIcon()
        _CACHE[cache_key] = empty
        return empty

    # 2x for HiDPI sharpness
    px_size = size * 2
    pm = QPixmap(px_size, px_size)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    try:
        renderer.render(painter)
    finally:
        painter.end()
    pm.setDevicePixelRatio(2)

    icon = QIcon(pm)
    _CACHE[cache_key] = icon
    return icon


def clear_cache() -> None:
    """Drops the icon cache. Call when the theme changes so subsequent
    `tf_icon` calls regenerate with the new accent / foreground color."""
    _CACHE.clear()


def list_icons() -> list[str]:
    """Returns all registered semantic icon names (for debugging /
    discovery / theme editor pickers)."""
    return sorted(ICON_MAP_LUCIDE.keys())
