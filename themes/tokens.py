"""Theme token dataclasses.

A ThemePack is the in-memory representation of a theme JSON file.
The schema is intentionally flat-ish: 4 grouped sections (color,
typography, spacing, shape) that cover ~90% of visual identity.
Component variants / motion / effects belong in future sprints.

JSON example (a minimal theme):

    {
      "name": "Dracula",
      "author": "Zeno Rocha",
      "is_dark": true,
      "color": {
        "bg_primary": "#282a36",
        ...
      },
      "typography": { ... },
      "spacing": { ... },
      "shape": { ... }
    }

Validation is best-effort: missing optional keys fall back to the
default-dark token values so partial themes still work.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict


# ─── Default token values (used as fallback for partial themes) ──────
_DEFAULT_DARK_COLOR = {
    "bg_primary":      "#1e1e1e",
    "bg_secondary":    "#252526",
    "bg_tertiary":     "#2d2d30",
    "bg_elevated":     "#333333",
    "fg_primary":      "#e6e6e6",
    "fg_secondary":    "#9e9e9e",
    "fg_disabled":     "#5a5a5a",
    "accent":          "#62b4ff",
    "accent_hover":    "#80c4ff",
    "accent_active":   "#4a9fee",
    "accent_fg":       "#000000",
    "success":         "#86efac",
    "warning":         "#fbbf24",
    "danger":          "#f87171",
    "info":            "#7dd3fc",
    "border":          "#3c3c3c",
    "border_strong":   "#555555",
    "selection_bg":    "#264f78",
    "selection_fg":    "#ffffff",
    "scrollbar_bg":    "#252526",
    "scrollbar_thumb": "#555555",
}

_DEFAULT_TYPOGRAPHY = {
    "font_family":      "system-ui, -apple-system, Inter, Segoe UI, sans-serif",
    "font_family_mono": "JetBrains Mono, Fira Code, Cascadia Code, monospace",
    "size_xs":   9,
    "size_sm":   10,
    "size_base": 11,
    "size_lg":   13,
    "size_xl":   16,
    "weight_normal": 400,
    "weight_medium": 500,
    "weight_bold":   700,
}

_DEFAULT_SPACING = {
    "xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24,
}

_DEFAULT_SHAPE = {
    "radius_sm":    3,
    "radius_md":    6,
    "radius_lg":    10,
    "radius_pill":  999,
    "border_width": 1,
}


@dataclass
class ColorTokens:
    bg_primary:      str = _DEFAULT_DARK_COLOR["bg_primary"]
    bg_secondary:    str = _DEFAULT_DARK_COLOR["bg_secondary"]
    bg_tertiary:     str = _DEFAULT_DARK_COLOR["bg_tertiary"]
    bg_elevated:     str = _DEFAULT_DARK_COLOR["bg_elevated"]
    fg_primary:      str = _DEFAULT_DARK_COLOR["fg_primary"]
    fg_secondary:    str = _DEFAULT_DARK_COLOR["fg_secondary"]
    fg_disabled:     str = _DEFAULT_DARK_COLOR["fg_disabled"]
    accent:          str = _DEFAULT_DARK_COLOR["accent"]
    accent_hover:    str = _DEFAULT_DARK_COLOR["accent_hover"]
    accent_active:   str = _DEFAULT_DARK_COLOR["accent_active"]
    accent_fg:       str = _DEFAULT_DARK_COLOR["accent_fg"]
    success:         str = _DEFAULT_DARK_COLOR["success"]
    warning:         str = _DEFAULT_DARK_COLOR["warning"]
    danger:          str = _DEFAULT_DARK_COLOR["danger"]
    info:            str = _DEFAULT_DARK_COLOR["info"]
    border:          str = _DEFAULT_DARK_COLOR["border"]
    border_strong:   str = _DEFAULT_DARK_COLOR["border_strong"]
    selection_bg:    str = _DEFAULT_DARK_COLOR["selection_bg"]
    selection_fg:    str = _DEFAULT_DARK_COLOR["selection_fg"]
    scrollbar_bg:    str = _DEFAULT_DARK_COLOR["scrollbar_bg"]
    scrollbar_thumb: str = _DEFAULT_DARK_COLOR["scrollbar_thumb"]


@dataclass
class TypographyTokens:
    font_family:      str = _DEFAULT_TYPOGRAPHY["font_family"]
    font_family_mono: str = _DEFAULT_TYPOGRAPHY["font_family_mono"]
    size_xs:   int = _DEFAULT_TYPOGRAPHY["size_xs"]
    size_sm:   int = _DEFAULT_TYPOGRAPHY["size_sm"]
    size_base: int = _DEFAULT_TYPOGRAPHY["size_base"]
    size_lg:   int = _DEFAULT_TYPOGRAPHY["size_lg"]
    size_xl:   int = _DEFAULT_TYPOGRAPHY["size_xl"]
    weight_normal: int = _DEFAULT_TYPOGRAPHY["weight_normal"]
    weight_medium: int = _DEFAULT_TYPOGRAPHY["weight_medium"]
    weight_bold:   int = _DEFAULT_TYPOGRAPHY["weight_bold"]


@dataclass
class SpacingTokens:
    xs: int = _DEFAULT_SPACING["xs"]
    sm: int = _DEFAULT_SPACING["sm"]
    md: int = _DEFAULT_SPACING["md"]
    lg: int = _DEFAULT_SPACING["lg"]
    xl: int = _DEFAULT_SPACING["xl"]


@dataclass
class ShapeTokens:
    radius_sm:    int = _DEFAULT_SHAPE["radius_sm"]
    radius_md:    int = _DEFAULT_SHAPE["radius_md"]
    radius_lg:    int = _DEFAULT_SHAPE["radius_lg"]
    radius_pill:  int = _DEFAULT_SHAPE["radius_pill"]
    border_width: int = _DEFAULT_SHAPE["border_width"]


@dataclass
class ThemePack:
    """In-memory representation of a theme. Loaded from a JSON file
    via `themes.registry.load_theme(name)` and applied via
    `themes.builder.apply_theme(app, pack)`."""
    name: str
    is_dark: bool = True
    author: str = ""
    description: str = ""
    color: ColorTokens = field(default_factory=ColorTokens)
    typography: TypographyTokens = field(default_factory=TypographyTokens)
    spacing: SpacingTokens = field(default_factory=SpacingTokens)
    shape: ShapeTokens = field(default_factory=ShapeTokens)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ThemePack":
        """Build a ThemePack from a parsed JSON dict. Missing keys
        fall back to defaults (dark palette). Unknown keys are
        silently ignored — future tokens are forward-compatible."""
        def _filtered(target_cls, src: dict | None) -> dict:
            if not src:
                return {}
            known = {f for f in target_cls.__dataclass_fields__}
            return {k: v for k, v in src.items() if k in known}

        return cls(
            name=data.get("name", "Untitled"),
            is_dark=bool(data.get("is_dark", True)),
            author=data.get("author", ""),
            description=data.get("description", ""),
            color=ColorTokens(**_filtered(ColorTokens, data.get("color"))),
            typography=TypographyTokens(**_filtered(TypographyTokens, data.get("typography"))),
            spacing=SpacingTokens(**_filtered(SpacingTokens, data.get("spacing"))),
            shape=ShapeTokens(**_filtered(ShapeTokens, data.get("shape"))),
        )
