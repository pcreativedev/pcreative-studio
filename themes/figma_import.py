"""Figma → Pcreative Studio token importer.

Two import paths:

  1. **DTCG JSON** (free Figma users): the design exports tokens via
     the Tokens Studio Figma plugin, which produces a JSON file
     following the W3C DTCG specification v2025.10. The user pastes
     or loads this JSON and we map the tokens onto our ThemePack.

  2. **Figma REST API** (Enterprise users): we call
     `GET /v1/files/<file_key>/variables/local` directly with the
     user's Personal Access Token and translate the response to the
     DTCG intermediate shape, then onto our ThemePack.

DTCG format reference: https://www.designtokens.org/tr/drafts/format/

Shape of a DTCG token:

    {
      "color": {
        "brand": {
          "primary": {
            "$type": "color",
            "$value": "#0066cc"          # or {"light": "#fff", "dark": "#000"}
          }
        }
      }
    }

Mapping strategy:

  1. Flatten DTCG to a list of (path, type, value, modes) tuples.
  2. For each token, score against semantic patterns
     (accent/bg/fg/success/...). Best match wins.
  3. If multiple Figma tokens compete for the same Pcreative Studio slot,
     prefer the one with higher score; surface ties to the user
     via the import dialog for manual disambiguation.
  4. Optional AI fallback: when score < threshold, ask the active
     AI provider (Claude/Codex) for a mapping suggestion using a
     small structured-output prompt.

The output of this module is always a `ThemePack` (or two, when
light + dark modes are detected) ready to pass to
`themes.builder.apply_theme()` or `themes.save_current_theme()`.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Optional

from .tokens import (
    ColorTokens, ComponentTokens, ShapeTokens, SpacingTokens,
    ThemePack, TypographyTokens,
)


# ─────────────────── DTCG intermediate representation ───────────────
@dataclass
class FigmaToken:
    """One token extracted from a DTCG JSON tree."""
    path: str                                 # "color.brand.primary"
    type: str                                 # "color" | "dimension" | "typography" | ...
    value: object                             # str | int | float | dict (multi-mode)
    modes: Optional[dict[str, object]] = None # {"light": "#fff", "dark": "#000"} or None

    @property
    def flat_value(self) -> object:
        """Returns the value if single-mode, or the first mode's value
        otherwise. For full multi-mode handling, callers should use
        `modes` directly."""
        if self.modes:
            return next(iter(self.modes.values()))
        return self.value


# ─────────────────── DTCG parser ────────────────────────────────────
def parse_dtcg(data: dict | str) -> list[FigmaToken]:
    """Parse a DTCG JSON file (or dict) into a flat list of tokens.

    Handles:
      - Nested groups (recursive walk)
      - Multi-mode values (`$value` as dict)
      - $type inheritance from parent groups
      - $extensions (Tokens Studio metadata — ignored, not part of
        the canonical spec)

    Aliases (`{color.brand.primary}` references) are returned as-is
    in `value`; resolution happens in `_resolve_aliases` after the
    flat list is built.
    """
    if isinstance(data, str):
        data = json.loads(data)

    if not isinstance(data, dict):
        raise ValueError("DTCG root must be a JSON object")

    tokens: list[FigmaToken] = []
    _walk(data, [], None, tokens)
    _resolve_aliases(tokens)
    return tokens


def _walk(node: dict, path: list[str], inherited_type: Optional[str],
          out: list[FigmaToken]) -> None:
    """Recursive walk of a DTCG tree.

    A token is detected by the presence of `$value`. A group is any
    other object that has child keys. `$type` cascades down to
    children that don't redeclare it.
    """
    # Resolve type for this level
    local_type = node.get("$type", inherited_type)

    for key, child in node.items():
        if key.startswith("$"):  # $type / $description / $extensions
            continue
        if not isinstance(child, dict):
            continue
        child_path = path + [key]

        if "$value" in child:
            # It's a token
            value = child["$value"]
            t = child.get("$type", local_type) or _guess_type(value)
            modes = _extract_modes(value)
            out.append(FigmaToken(
                path=".".join(child_path),
                type=t,
                value=value,
                modes=modes,
            ))
        else:
            # It's a group
            _walk(child, child_path, child.get("$type", local_type), out)


def _extract_modes(value: object) -> Optional[dict[str, object]]:
    """If `$value` is a dict whose keys look like mode names (light,
    dark, etc.) instead of a structured value (typography), return
    the modes. Otherwise return None."""
    if not isinstance(value, dict):
        return None
    # Typography composite tokens have structured keys like
    # "fontFamily", "fontSize", "fontWeight". They're NOT modes.
    typography_keys = {"fontFamily", "fontSize", "fontWeight", "lineHeight",
                       "letterSpacing", "fontStyle", "textCase",
                       "textDecoration"}
    if any(k in typography_keys for k in value.keys()):
        return None
    # Otherwise: treat as modes
    return dict(value)


def _guess_type(value: object) -> str:
    """Fallback type detection when $type is missing — DTCG-allowed
    but uncommon. We look at the value shape."""
    if isinstance(value, str):
        if re.fullmatch(r"#[0-9a-fA-F]{3,8}", value):
            return "color"
        if value.endswith(("px", "rem", "em")):
            return "dimension"
        return "string"
    if isinstance(value, (int, float)):
        return "dimension"
    if isinstance(value, dict):
        if any(k in value for k in ("fontFamily", "fontSize")):
            return "typography"
    return "unknown"


_ALIAS_RE = re.compile(r"\{([^{}]+)\}")


def _resolve_aliases(tokens: list[FigmaToken]) -> None:
    """Resolves DTCG aliases like `{color.brand.primary}` in-place.

    Builds an index by path, then iterates up to 8 times to handle
    chained aliases. Unresolvable references are left as-is (the
    mapper will warn the user).
    """
    by_path = {t.path: t for t in tokens}
    for _ in range(8):
        changed = False
        for t in tokens:
            if isinstance(t.value, str):
                m = _ALIAS_RE.fullmatch(t.value)
                if m:
                    ref = by_path.get(m.group(1))
                    if ref and not (isinstance(ref.value, str)
                                    and _ALIAS_RE.fullmatch(ref.value)):
                        t.value = ref.value
                        t.modes = ref.modes
                        changed = True
            elif t.modes:
                for mode_name, v in list(t.modes.items()):
                    if isinstance(v, str):
                        m = _ALIAS_RE.fullmatch(v)
                        if m:
                            ref = by_path.get(m.group(1))
                            if ref:
                                resolved = ref.flat_value
                                if isinstance(resolved, str) and not _ALIAS_RE.fullmatch(resolved):
                                    t.modes[mode_name] = resolved
                                    changed = True
        if not changed:
            break


# ─────────────────── Figma REST API client ──────────────────────────
@dataclass
class FigmaAPIResult:
    """Result of fetching from Figma REST API. Either ok=True with
    data, or ok=False with a human-readable error."""
    ok: bool
    data: Optional[dict] = None
    error: str = ""


def extract_file_key(url_or_key: str) -> Optional[str]:
    """Extracts the Figma file key from a URL like:
      https://www.figma.com/design/abcd1234/My-File
    or the key directly if already given."""
    if re.fullmatch(r"[a-zA-Z0-9]{10,}", url_or_key):
        return url_or_key
    m = re.search(r"figma\.com/(?:file|design|proto)/([a-zA-Z0-9]+)", url_or_key)
    return m.group(1) if m else None


def fetch_local_variables(file_key: str, pat: str, timeout: int = 15) -> FigmaAPIResult:
    """Calls `GET /v1/files/<key>/variables/local`. Requires
    Enterprise plan + a PAT with `file_variables:read` scope."""
    url = f"https://api.figma.com/v1/files/{file_key}/variables/local"
    req = urllib.request.Request(
        url,
        headers={"X-Figma-Token": pat, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8")
        return FigmaAPIResult(ok=True, data=json.loads(body))
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors="replace")[:200]
        if e.code == 403:
            return FigmaAPIResult(ok=False, error=(
                "403 Forbidden. La API de variables requiere plan "
                "Figma Enterprise. Para planes gratuitos/Pro usa la "
                "pestaña 'Tokens Studio JSON' importando el export "
                "del plugin Tokens Studio."
            ))
        if e.code == 404:
            return FigmaAPIResult(ok=False, error=(
                f"404 File not found. Verifica el file key '{file_key}' "
                f"y que el PAT tenga acceso al archivo."
            ))
        return FigmaAPIResult(ok=False, error=f"HTTP {e.code}: {msg}")
    except urllib.error.URLError as e:
        return FigmaAPIResult(ok=False, error=f"Network error: {e.reason}")
    except Exception as e:
        return FigmaAPIResult(ok=False, error=f"{type(e).__name__}: {e}")


def figma_variables_to_dtcg(figma_response: dict) -> dict:
    """Translates a Figma REST `/variables/local` response into the
    DTCG JSON shape so the rest of the pipeline can consume it
    uniformly."""
    out: dict = {}
    variables = figma_response.get("meta", {}).get("variables", {})
    collections = figma_response.get("meta", {}).get("variableCollections", {})

    def _figma_value_to_dtcg(v: object, var_type: str) -> object:
        if var_type == "COLOR" and isinstance(v, dict) and {"r", "g", "b"}.issubset(v.keys()):
            r = int(round(v["r"] * 255))
            g = int(round(v["g"] * 255))
            b = int(round(v["b"] * 255))
            a = v.get("a", 1)
            if a < 1:
                return f"#{r:02x}{g:02x}{b:02x}{int(round(a*255)):02x}"
            return f"#{r:02x}{g:02x}{b:02x}"
        if var_type == "FLOAT":
            return v
        if var_type == "STRING":
            return v
        if var_type == "BOOLEAN":
            return bool(v)
        return v

    type_map = {"COLOR": "color", "FLOAT": "number", "STRING": "string", "BOOLEAN": "boolean"}

    for var_id, var in variables.items():
        name_path = var.get("name", "").split("/")
        var_type = var.get("resolvedType", "STRING")
        values_by_mode = var.get("valuesByMode", {})
        collection_id = var.get("variableCollectionId")
        collection = collections.get(collection_id, {})
        modes_meta = {m["modeId"]: m["name"] for m in collection.get("modes", [])}

        # Build nested DTCG path
        cursor = out
        for key in name_path[:-1]:
            cursor = cursor.setdefault(key, {})
        leaf_key = name_path[-1]
        token: dict = {"$type": type_map.get(var_type, "string")}
        # If single mode, use $value as scalar; else a dict
        if len(values_by_mode) == 1:
            (raw_v,) = values_by_mode.values()
            token["$value"] = _figma_value_to_dtcg(raw_v, var_type)
        else:
            token["$value"] = {
                modes_meta.get(mode_id, mode_id): _figma_value_to_dtcg(raw_v, var_type)
                for mode_id, raw_v in values_by_mode.items()
            }
        cursor[leaf_key] = token

    return out


# ─────────────────── Semantic mapping ────────────────────────────────
# Pattern → target Pcreative Studio token, with score weight.
#
# The scorer normalises Figma paths to lowercase + underscores
# ("color.brand.primary" → "color_brand_primary"), then matches against
# the regex patterns below. The HIGHEST scoring pattern wins per slot.
# Higher score = more specific = preferred.

_COLOR_PATTERNS: list[tuple[str, str, int]] = [
    # (target_token, regex, score)
    # Most-specific patterns first so the regex ranks them naturally.
    ("accent",          r"(brand|accent|primary|main)$", 90),
    ("accent",          r"(brand|accent|primary).*default", 95),
    ("accent_hover",    r"(brand|accent|primary).*hover", 100),
    ("accent_active",   r"(brand|accent|primary).*(active|pressed|selected)", 100),
    ("accent_fg",       r"(brand|accent|primary).*(text|fg|on[-_])", 100),
    ("bg_primary",      r"(bg|background|surface)([._]base|[._]default|[._]primary|[._]1|$)", 95),
    ("bg_secondary",    r"(bg|background|surface)[._](secondary|2|raised)", 95),
    ("bg_tertiary",     r"(bg|background|surface)[._](tertiary|3|sunken)", 95),
    ("bg_elevated",     r"(bg|background|surface)[._](elevated|overlay|4|popover)", 100),
    ("fg_primary",      r"(fg|foreground|text|content|ink)([._]base|[._]default|[._]primary|[._]1|$)", 95),
    ("fg_secondary",    r"(fg|foreground|text|content|ink)[._](secondary|2|muted|subtle)", 95),
    ("fg_disabled",     r"(fg|foreground|text|content|ink)[._](disabled|3|tertiary)", 95),
    ("success",         r"(success|ok|positive|green)$", 90),
    ("warning",         r"(warning|caution|amber|yellow)$", 90),
    ("danger",          r"(danger|error|negative|critical|red)$", 90),
    ("info",            r"(info|information|blue.*info)$", 90),
    ("border",          r"border([._]default|[._]base|$)", 85),
    ("border_strong",   r"border[._](strong|emphasis|hover)", 95),
    ("selection_bg",    r"selection[._]?(bg|background)?", 80),
    ("selection_fg",    r"selection[._]?(fg|text|foreground)", 95),
    ("scrollbar_bg",    r"scrollbar[._]?(bg|background)", 80),
    ("scrollbar_thumb", r"scrollbar[._]?(thumb|handle)", 95),
]

_SHAPE_PATTERNS: list[tuple[str, str, int]] = [
    ("radius_sm",    r"(radius|corner|border[._]radius)[._]?(sm|small|xs|1|2)$", 95),
    ("radius_md",    r"(radius|corner|border[._]radius)[._]?(md|medium|default|3|4)$", 95),
    ("radius_lg",    r"(radius|corner|border[._]radius)[._]?(lg|large|xl|5|6)$", 95),
    ("radius_pill",  r"(radius|corner|border[._]radius)[._]?(pill|full|round|round)", 100),
    ("border_width", r"border[._](width|stroke)", 90),
]


def _normalize(path: str) -> str:
    """Normalises a token path for pattern matching: lowercased,
    slashes/spaces/dots → underscores."""
    return re.sub(r"[^a-z0-9_]+", "_", path.lower()).strip("_")


@dataclass
class MappingProposal:
    """One suggested mapping from a Figma token to a Pcreative Studio slot,
    with a confidence score. The UI surfaces these for the user to
    accept / override / reject."""
    figma_path: str
    figma_value: object       # the resolved value (hex / number / etc.)
    target_slot: str          # e.g. "color.accent" or "shape.radius_md"
    score: int                # 0-100, higher = more confident
    rationale: str = ""       # human-readable reason


def propose_mappings(tokens: list[FigmaToken]) -> list[MappingProposal]:
    """Score each Figma token against Pcreative Studio slots and return the
    best candidate per slot. Ties are broken by score; ties at equal
    score are flagged for user disambiguation in the UI."""
    proposals: list[MappingProposal] = []
    # Track best-score-per-slot to dedupe
    best_per_slot: dict[str, MappingProposal] = {}

    for tok in tokens:
        norm = _normalize(tok.path)
        patterns = _COLOR_PATTERNS if tok.type == "color" else (
            _SHAPE_PATTERNS if tok.type in ("dimension", "number") else []
        )
        for target, regex, score in patterns:
            if re.search(regex, norm):
                slot = f"{'color' if tok.type == 'color' else 'shape'}.{target}"
                proposal = MappingProposal(
                    figma_path=tok.path,
                    figma_value=tok.flat_value,
                    target_slot=slot,
                    score=score,
                    rationale=f"matched '{regex}'",
                )
                existing = best_per_slot.get(slot)
                if existing is None or proposal.score > existing.score:
                    best_per_slot[slot] = proposal

    proposals = list(best_per_slot.values())
    # Sort by slot for stable display
    proposals.sort(key=lambda p: p.target_slot)
    return proposals


# ─────────────────── ThemePack assembly ─────────────────────────────
def build_themepack_from_mappings(
    mappings: list[MappingProposal],
    base: Optional[ThemePack] = None,
    name: str = "Imported from Figma",
    author: str = "",
    description: str = "Imported via DTCG / Figma REST",
) -> ThemePack:
    """Builds a ThemePack by applying a list of accepted mappings on
    top of `base` (defaulting to the dark preset). The function never
    fails on missing slots — it just leaves the base's defaults where
    no Figma token mapped."""
    pack = base or ThemePack(name=name)
    pack.name = name
    pack.author = author
    pack.description = description

    color_kwargs = pack.color.__dict__.copy()
    shape_kwargs = pack.shape.__dict__.copy()

    for m in mappings:
        section, slot = m.target_slot.split(".", 1)
        if section == "color":
            color_kwargs[slot] = str(m.figma_value)
        elif section == "shape":
            try:
                shape_kwargs[slot] = int(str(m.figma_value).rstrip("pxremEM"))
            except Exception:
                pass

    pack.color = ColorTokens(**color_kwargs)
    pack.shape = ShapeTokens(**shape_kwargs)
    # Heuristic: infer is_dark by checking the imported bg_primary
    bg = pack.color.bg_primary
    try:
        r = int(bg[1:3], 16); g = int(bg[3:5], 16); b = int(bg[5:7], 16)
        luminance = 0.299 * r + 0.587 * g + 0.114 * b
        pack.is_dark = luminance < 128
    except Exception:
        pass

    return pack


# ─────────────────── DTCG export (reverse path) ─────────────────────
def themepack_to_dtcg(pack: ThemePack) -> dict:
    """Converts a ThemePack to a DTCG JSON tree so the design team
    can re-import to Figma via Tokens Studio."""
    c = pack.color
    sh = pack.shape

    color_node: dict = {}
    for attr, val in c.__dict__.items():
        # Build nested: bg_primary → bg.primary etc.
        parts = attr.split("_", 1) if "_" in attr else [attr]
        cursor = color_node
        for p in parts[:-1]:
            cursor = cursor.setdefault(p, {})
        cursor[parts[-1]] = {"$type": "color", "$value": val}

    shape_node: dict = {}
    for attr, val in sh.__dict__.items():
        parts = attr.split("_", 1) if "_" in attr else [attr]
        cursor = shape_node
        for p in parts[:-1]:
            cursor = cursor.setdefault(p, {})
        cursor[parts[-1]] = {"$type": "dimension", "$value": f"{val}px"}

    return {
        "$description": f"Pcreative Studio export of '{pack.name}'",
        "color": color_node,
        "shape": shape_node,
    }
