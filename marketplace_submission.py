"""Marketplace submission helper.

Builds marketplace-ready ZIPs in the EXACT structure each marketplace
expects. The existing `build_marketplace_zip` in themeforge.py produces
a generic single-folder ZIP — good for Gumroad / generic uploads but
gets rejected on stricter marketplaces (ThemeForest, CodeCanyon).

Profiles validated against vendor docs (2026):

- ThemeForest HTML site templates
  https://help.author.envato.com/hc/en-us/articles/360000470826
- ThemeForest WordPress themes
  https://webdesign.tutsplus.com/selling-wordpress-themes-on-themeforest...
- CodeCanyon code items
  https://help.author.envato.com/hc/en-us/articles/360000471583
- Creative Market web themes
  https://support.creativemarket.com/hc/en-us/articles/1260803906370
- Gumroad (generic / flexible)
  https://mydesigns.io/blog/gumroad-for-selling-digital-products/

Public API:

  list_profiles() -> [str]                — available marketplace keys
  get_profile(key) -> MarketplaceProfile  — full spec for a key
  validate(project_dir, profile) -> [Issue]   — pre-flight checks
  build_submission(project_dir, profile, opts) -> (ok, msg, path)
"""
from __future__ import annotations

import io
import json
import os
import re
import shutil
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


# ─────────────────── Profile shape ──────────────────────────────────
@dataclass
class PreviewSpec:
    """Specification of a single required/optional preview image."""
    name: str            # filename inside the upload ZIP (e.g. "01_theme.jpg")
    width: int           # exact width in px (0 = no constraint)
    height: int          # exact height in px (0 = no constraint)
    min_width: int = 0   # alternative to exact width
    min_height: int = 0
    max_width: int = 0
    max_height: int = 0
    formats: tuple[str, ...] = ("png", "jpg", "jpeg")
    required: bool = True
    description: str = ""


@dataclass
class MarketplaceProfile:
    """All marketplace-specific rules for building a submission ZIP."""
    key: str
    name: str               # display name
    target: str             # what kind of item ("html-template", "wordpress-theme", "code-item", …)
    documentation_required: bool = True
    documentation_formats: tuple[str, ...] = ("pdf", "html")
    documentation_path: str = "Documentation"   # path inside the ZIP
    template_path: str = "Template"             # where the actual code goes
    license_required: bool = False
    license_files: tuple[str, ...] = ()         # file basenames expected in Licensing/
    license_path: str = "Licensing"
    previews: list[PreviewSpec] = field(default_factory=list)
    max_zip_size_mb: int = 2048      # 2GB Envato default
    notes: str = ""
    extra_required_files: list[str] = field(default_factory=list)
    structure_doc: str = ""           # human-readable description of the expected output


# ─────────────────── The 5 profiles ─────────────────────────────────
PROFILES: dict[str, MarketplaceProfile] = {

    "themeforest-html": MarketplaceProfile(
        key="themeforest-html",
        name="ThemeForest — HTML Site Template",
        target="html-template",
        documentation_required=True,
        documentation_formats=("html", "pdf"),
        documentation_path="Documentation",
        template_path="Template",
        license_required=False,
        previews=[
            PreviewSpec(
                name="01_preview.jpg", width=590, height=300,
                formats=("jpg", "jpeg", "png"),
                required=True,
                description="Main preview shown on the item page (exact 590×300).",
            ),
            PreviewSpec(
                name="thumbnail.png", width=80, height=80,
                formats=("png",),
                required=True,
                description="Thumbnail shown in search results (exact 80×80, PNG).",
            ),
        ],
        notes=(
            "Top-level ZIP must contain a `Main Files.zip` with Template/ "
            "and Documentation/ inside, plus 01_preview.jpg and thumbnail.png "
            "at the root. Reviewers check structure before content."
        ),
        structure_doc=(
            "<theme>.zip\n"
            "├── 01_preview.jpg            (590×300)\n"
            "├── thumbnail.png             (80×80)\n"
            "└── Main Files.zip\n"
            "    ├── Template/             ← your theme code\n"
            "    └── Documentation/        ← HTML or PDF docs\n"
            "        ├── index.html\n"
            "        └── assets/"
        ),
    ),

    "themeforest-wordpress": MarketplaceProfile(
        key="themeforest-wordpress",
        name="ThemeForest — WordPress Theme",
        target="wordpress-theme",
        documentation_required=True,
        documentation_formats=("html", "pdf"),
        documentation_path="Documentation",
        template_path="",   # WP uses a different layout
        license_required=False,  # WP licenses auto-attached by Envato
        previews=[
            PreviewSpec(
                name="01_preview.jpg", width=590, height=300,
                formats=("jpg", "jpeg", "png"),
                required=True,
                description="Main preview shown on the item page (exact 590×300).",
            ),
            PreviewSpec(
                name="thumbnail.png", width=80, height=80,
                formats=("png",),
                required=True,
                description="Thumbnail shown in search results (80×80, PNG).",
            ),
        ],
        notes=(
            "WordPress themes need TWO inner zips: <theme>.zip (installable "
            "via Appearance → Themes → Upload) and <theme>_pack.zip (the "
            "production pack with docs / changelog / source assets)."
        ),
        structure_doc=(
            "production-pack.zip\n"
            "├── 01_preview.jpg            (590×300)\n"
            "├── thumbnail.png             (80×80)\n"
            "├── <theme>.zip               ← installable WP theme\n"
            "├── <theme>_pack.zip          ← extras (changelog, source)\n"
            "└── Documentation/\n"
            "    └── index.html"
        ),
    ),

    "codecanyon": MarketplaceProfile(
        key="codecanyon",
        name="CodeCanyon — Code Item",
        target="code-item",
        documentation_required=True,
        documentation_formats=("html", "pdf"),
        documentation_path="Documentation",
        template_path="Source",
        license_required=False,
        previews=[
            PreviewSpec(
                name="01_preview.jpg", width=590, height=300,
                formats=("jpg", "jpeg", "png"),
                required=True,
                description="Main preview (exact 590×300).",
            ),
            PreviewSpec(
                name="thumbnail.png", width=80, height=80,
                formats=("png",),
                required=True,
                description="Thumbnail (exact 80×80).",
            ),
        ],
        notes=(
            "CodeCanyon expects a Source/ folder (the actual project) and a "
            "Documentation/ folder at the same level."
        ),
        structure_doc=(
            "<item>.zip\n"
            "├── 01_preview.jpg            (590×300)\n"
            "├── thumbnail.png             (80×80)\n"
            "├── Source/                   ← project code\n"
            "└── Documentation/\n"
            "    ├── documentation.html\n"
            "    └── assets/"
        ),
    ),

    "creative-market": MarketplaceProfile(
        key="creative-market",
        name="Creative Market — Web Theme",
        target="web-theme",
        documentation_required=False,
        documentation_formats=("html", "pdf", "md"),
        documentation_path="docs",
        template_path="",   # flat structure
        license_required=False,
        previews=[
            PreviewSpec(
                name="preview-01.jpg", width=0, height=0,
                min_width=910, min_height=607,
                max_width=3640, max_height=10920,
                formats=("jpg", "jpeg", "png", "gif"),
                required=True,
                description=(
                    "Min 910×607, max 3640×10920, recommended 1820×1214. "
                    "Up to 100 screenshots per product."
                ),
            ),
        ],
        notes=(
            "Creative Market is FAR less strict on internal structure than "
            "Envato. Only ZIP format accepted (.rar / .7z may be removed). "
            "Focus on screenshot quality — that's what sells here."
        ),
        structure_doc=(
            "<theme>.zip\n"
            "├── preview-01.jpg            (1820×1214 recommended)\n"
            "├── preview-02.jpg            (optional, up to 100)\n"
            "└── <theme>/                  ← project (any internal layout)\n"
            "    ├── README.md\n"
            "    └── ..."
        ),
    ),

    "gumroad": MarketplaceProfile(
        key="gumroad",
        name="Gumroad — Digital Product",
        target="digital-product",
        documentation_required=False,
        documentation_formats=("md", "html", "pdf"),
        documentation_path="",  # README at root is enough
        template_path="",
        license_required=False,
        previews=[],   # uploaded separately on Gumroad's product page
        notes=(
            "Gumroad is the most flexible. Buyer pays, gets the ZIP, "
            "unzips it, expects to use it immediately. A clean README at "
            "the root + the project files is enough. Pricing sweet spot: "
            "$7-$17 single template, $19-$49 bundle."
        ),
        structure_doc=(
            "<theme>.zip\n"
            "├── README.md                 ← what's inside + how to use\n"
            "└── <theme>/                  ← project (your structure)"
        ),
    ),
}


def list_profiles() -> list[str]:
    """Returns the list of available marketplace keys."""
    return list(PROFILES.keys())


def get_profile(key: str) -> MarketplaceProfile | None:
    return PROFILES.get(key)


# ─────────────────── Validation ─────────────────────────────────────
@dataclass
class Issue:
    """One validation finding."""
    level: str        # "pass" | "warn" | "fail" | "info"
    title: str
    message: str
    hint: str = ""


def _list_images(path: Path) -> list[Path]:
    if not path.is_dir():
        return []
    exts = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
    return sorted(p for p in path.rglob("*") if p.suffix.lower() in exts and p.is_file())


def _read_image_dims(p: Path) -> tuple[int, int] | None:
    """Best-effort image dimension reader without PIL dependency."""
    try:
        # Use Qt if available (we're a PyQt app anyway)
        from PyQt6.QtGui import QImage
        img = QImage(str(p))
        if not img.isNull():
            return img.width(), img.height()
    except Exception:
        pass
    return None


def validate(project_dir: Path, profile: MarketplaceProfile) -> list[Issue]:
    """Runs marketplace-specific pre-flight checks against the project.

    Issues returned at levels:
      - pass : check passed (informational)
      - warn : likely OK but reviewer may flag
      - fail : will be auto-rejected (must fix)
      - info : neutral note
    """
    issues: list[Issue] = []
    project_dir = Path(project_dir).resolve()

    if not project_dir.is_dir():
        return [Issue("fail", "Project path", f"Not a directory: {project_dir}")]

    # Documentation
    doc_dirs = [project_dir / "documentation", project_dir / "docs", project_dir / "Documentation"]
    doc_dir = next((d for d in doc_dirs if d.is_dir()), None)
    if profile.documentation_required:
        if doc_dir is None:
            issues.append(Issue(
                "fail", "Documentation",
                f"{profile.name} requires a documentation folder; none found.",
                hint=("Create `documentation/` with an index.html or "
                      "documentation.pdf. Pcreative Studio can generate a starter "
                      "via the AI agent — ask for 'documentation HTML for "
                      "buyers' in CLAUDE.md."),
            ))
        else:
            # Check at least one acceptable file inside
            wanted_exts = tuple("." + e for e in profile.documentation_formats)
            has_doc = any(p.suffix.lower() in wanted_exts for p in doc_dir.rglob("*") if p.is_file())
            if not has_doc:
                issues.append(Issue(
                    "fail", "Documentation",
                    f"Found `{doc_dir.name}/` but no {'/'.join(profile.documentation_formats).upper()} file inside.",
                    hint=f"Add an index.{profile.documentation_formats[0]} at minimum.",
                ))
            else:
                issues.append(Issue("pass", "Documentation",
                                    f"Found valid docs in `{doc_dir.name}/`."))
    else:
        if doc_dir:
            issues.append(Issue("pass", "Documentation",
                                f"Optional `{doc_dir.name}/` found and will be bundled."))

    # README presence (for Gumroad / Creative Market)
    if not profile.documentation_required:
        readme_paths = list(project_dir.glob("README*"))
        if readme_paths:
            issues.append(Issue("pass", "README",
                                f"Found `{readme_paths[0].name}` at project root."))
        else:
            issues.append(Issue(
                "warn", "README",
                "No README found at project root. Buyers expect one.",
                hint="Add a README.md with: what this is, what's included, install steps.",
            ))

    # Previews
    screenshots_dir = next(
        (project_dir / d for d in ("screenshots", "previews", "assets/screenshots")
         if (project_dir / d).is_dir()),
        None,
    )
    images = _list_images(screenshots_dir) if screenshots_dir else []
    for spec in profile.previews:
        if not spec.required and not images:
            continue
        matching = []
        for img in images:
            dims = _read_image_dims(img)
            if dims is None:
                continue
            w, h = dims
            if spec.width and spec.height:
                if w == spec.width and h == spec.height:
                    matching.append((img, w, h))
            elif spec.min_width and w >= spec.min_width and h >= spec.min_height:
                if spec.max_width and (w > spec.max_width or h > spec.max_height):
                    continue
                matching.append((img, w, h))
        if matching:
            issues.append(Issue(
                "pass", f"Preview ({spec.name})",
                f"Found {len(matching)} matching image(s): {matching[0][0].name} ({matching[0][1]}×{matching[0][2]}).",
            ))
        else:
            dim_req = (f"{spec.width}×{spec.height} exact"
                       if spec.width and spec.height
                       else f"min {spec.min_width}×{spec.min_height}")
            issues.append(Issue(
                "warn" if not spec.required else "fail",
                f"Preview ({spec.name})",
                f"No image found matching {dim_req}.",
                hint=(f"Place a {dim_req} {'/'.join(spec.formats).upper()} in "
                      f"`screenshots/`. Pcreative Studio's screenshot button (📸 in "
                      f"ProjectWindow) captures the preview pane; resize as needed."),
            ))

    # ZIP size estimate
    try:
        total_size = sum(
            p.stat().st_size for p in project_dir.rglob("*")
            if p.is_file() and "node_modules" not in p.parts and ".git" not in p.parts
        )
        size_mb = total_size / 1_048_576
        if size_mb > profile.max_zip_size_mb:
            issues.append(Issue(
                "fail", "ZIP size",
                f"Estimated payload ~{size_mb:.0f} MB exceeds max {profile.max_zip_size_mb} MB.",
                hint="Strip large assets (node_modules, dist/, source PSDs) and re-check.",
            ))
        elif size_mb > profile.max_zip_size_mb * 0.5:
            issues.append(Issue(
                "warn", "ZIP size",
                f"Estimated payload ~{size_mb:.0f} MB is over 50% of the limit.",
            ))
        else:
            issues.append(Issue("pass", "ZIP size", f"Estimated ~{size_mb:.1f} MB."))
    except Exception as e:
        issues.append(Issue("info", "ZIP size", f"Could not estimate: {e}"))

    # License files (Envato Joomla/Drupal/PrestaShop/Magento require these)
    if profile.license_required:
        license_dir = project_dir / "Licensing"
        if not license_dir.is_dir():
            issues.append(Issue(
                "fail", "Licensing",
                f"{profile.name} requires a `Licensing/` folder with the "
                f"Envato license .txt files.",
                hint="Envato provides the two .txt files in their author panel.",
            ))
        else:
            present = {p.name for p in license_dir.glob("*.txt")}
            missing = [f for f in profile.license_files if f not in present]
            if missing:
                issues.append(Issue(
                    "fail", "Licensing",
                    f"Missing files: {', '.join(missing)}",
                ))
            else:
                issues.append(Issue("pass", "Licensing",
                                    f"Found all {len(profile.license_files)} license files."))

    return issues


# ─────────────────── Build ZIP ──────────────────────────────────────
# Reuse exclusion sets from the existing builder
_EXCLUDE_DIRS = frozenset({
    "node_modules", ".git", ".next", ".nuxt", "out", "dist", "build",
    ".cache", "__pycache__", ".venv", "venv", "env", "ENV",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "coverage",
    ".turbo", ".vercel", ".netlify",
    ".vscode", ".idea", ".cursor", ".windsurf", ".claude", ".aider",
    "target", "vendor", ".gradle", ".dart_tool",
    "screenshots-private", "tmp", ".tmp",
})
_EXCLUDE_FILES = frozenset({
    ".env", ".env.local", ".env.development", ".env.production",
    ".env.test", ".DS_Store", "Thumbs.db", "desktop.ini",
    "CLAUDE.md", "AGENTS.md", "GEMINI.md", "MEMORY.md", ".eslintcache",
})
_EXCLUDE_SUFFIXES = (".log", ".pyc", ".pyo", ".swp", ".swo", ".bak", ".tmp")


def _should_include_dir(name: str) -> bool:
    return name not in _EXCLUDE_DIRS


def _should_include_file(name: str) -> bool:
    if name in _EXCLUDE_FILES:
        return False
    if name.startswith(".env."):
        return False
    if any(name.endswith(s) for s in _EXCLUDE_SUFFIXES):
        return False
    return True


def _add_dir_to_zip(zf: zipfile.ZipFile, source_dir: Path, arc_prefix: str) -> int:
    """Walks source_dir and adds files under arc_prefix in the zip.
    Returns number of files added."""
    n = 0
    for root, dirs, files in os.walk(source_dir):
        dirs[:] = [d for d in dirs if _should_include_dir(d)]
        for f in files:
            if not _should_include_file(f):
                continue
            src = Path(root) / f
            rel = src.relative_to(source_dir)
            arc = f"{arc_prefix}/{rel}" if arc_prefix else str(rel)
            try:
                zf.write(str(src), arc)
                n += 1
            except OSError:
                continue
    return n


def _build_inner_zip(source_dir: Path, arc_prefix: str = "") -> bytes:
    """Builds an in-memory zip of source_dir (used for nested zips like
    `Main Files.zip`)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        _add_dir_to_zip(zf, source_dir, arc_prefix)
    return buf.getvalue()


def _find_screenshot_dir(project_dir: Path) -> Path | None:
    for d in ("screenshots", "previews", "assets/screenshots"):
        c = project_dir / d
        if c.is_dir() and any(c.iterdir()):
            return c
    return None


def _find_doc_dir(project_dir: Path) -> Path | None:
    for d in ("documentation", "docs", "Documentation"):
        c = project_dir / d
        if c.is_dir() and any(c.iterdir()):
            return c
    return None


def build_submission(
    project_dir: Path,
    profile: MarketplaceProfile,
    output_dir: Path,
    slug: str | None = None,
    timestamp: bool = True,
) -> tuple[bool, str, Path | None]:
    """Builds the marketplace-ready ZIP in the EXACT structure required.

    Args:
        project_dir: source project root.
        profile: marketplace profile (themeforest-html / wordpress / codecanyon / etc.).
        output_dir: where to write the final ZIP (must exist or be creatable).
        slug: override the default (project_dir.name).
        timestamp: append YYYYMMDD-HHMMSS to the filename.

    Returns:
        (ok, message, output_path)
    """
    project_dir = Path(project_dir).resolve()
    output_dir = Path(output_dir).resolve()
    if not project_dir.is_dir():
        return False, f"Not a directory: {project_dir}", None
    output_dir.mkdir(parents=True, exist_ok=True)

    slug = slug or project_dir.name
    ts = "-" + datetime.now().strftime("%Y%m%d-%H%M%S") if timestamp else ""
    final_path = output_dir / f"{slug}-{profile.key}{ts}.zip"

    screenshot_dir = _find_screenshot_dir(project_dir)
    doc_dir = _find_doc_dir(project_dir)

    try:
        with zipfile.ZipFile(
            final_path, "w",
            compression=zipfile.ZIP_DEFLATED, compresslevel=6,
        ) as zf:

            # Dispatcher by profile target
            if profile.target == "html-template":
                # Top-level ZIP layout:
                #   01_preview.jpg, thumbnail.png at root
                #   + Main Files.zip containing Template/ and Documentation/
                main_files_buf = io.BytesIO()
                with zipfile.ZipFile(
                    main_files_buf, "w",
                    compression=zipfile.ZIP_DEFLATED, compresslevel=6,
                ) as mfzip:
                    _add_dir_to_zip(mfzip, project_dir, profile.template_path)
                    if doc_dir:
                        _add_dir_to_zip(mfzip, doc_dir, profile.documentation_path)
                zf.writestr("Main Files.zip", main_files_buf.getvalue())
                # Previews at root
                if screenshot_dir:
                    _embed_previews(zf, screenshot_dir, profile.previews, prefix="")

            elif profile.target == "wordpress-theme":
                # Production pack with <theme>.zip + <theme>_pack.zip + Docs
                theme_buf = _build_inner_zip(project_dir, slug)
                zf.writestr(f"{slug}.zip", theme_buf)
                # Pack with extras (changelog, source assets, …)
                source_dir = project_dir / "source"
                if source_dir.is_dir():
                    pack_buf = _build_inner_zip(source_dir, "")
                    zf.writestr(f"{slug}_pack.zip", pack_buf)
                if doc_dir:
                    _add_dir_to_zip(zf, doc_dir, profile.documentation_path)
                if screenshot_dir:
                    _embed_previews(zf, screenshot_dir, profile.previews, prefix="")

            elif profile.target == "code-item":
                # Source/ + Documentation/ at the root, previews at root
                _add_dir_to_zip(zf, project_dir, profile.template_path)
                if doc_dir:
                    _add_dir_to_zip(zf, doc_dir, profile.documentation_path)
                if screenshot_dir:
                    _embed_previews(zf, screenshot_dir, profile.previews, prefix="")

            elif profile.target == "web-theme":
                # Creative Market — flat structure with previews + project dir
                _add_dir_to_zip(zf, project_dir, slug)
                if screenshot_dir:
                    # Take all screenshots in the dir
                    for i, img in enumerate(_list_images(screenshot_dir), start=1):
                        arc = f"preview-{i:02d}{img.suffix.lower()}"
                        zf.write(str(img), arc)

            elif profile.target == "digital-product":
                # Gumroad — flat with README at root, project below
                _add_dir_to_zip(zf, project_dir, slug)

            else:
                # Generic fallback
                _add_dir_to_zip(zf, project_dir, slug)

    except Exception as e:
        return False, f"Build failed: {e}", None

    size = final_path.stat().st_size
    return True, (
        f"Built {profile.name} submission: {final_path.name} "
        f"({size / 1_048_576:.1f} MB)"
    ), final_path


def _embed_previews(
    zf: zipfile.ZipFile,
    screenshot_dir: Path,
    specs: list[PreviewSpec],
    prefix: str = "",
) -> None:
    """Embeds preview images matching each spec at the given prefix.
    Picks the first image matching each spec's dimensions; falls back
    to the first available image with a warning name suffix."""
    images = _list_images(screenshot_dir)
    if not images:
        return

    for spec in specs:
        target_name = f"{prefix}{spec.name}" if prefix else spec.name
        picked = None
        for img in images:
            dims = _read_image_dims(img)
            if dims is None:
                continue
            w, h = dims
            if spec.width and spec.height:
                if w == spec.width and h == spec.height:
                    picked = img
                    break
            elif spec.min_width and w >= spec.min_width and h >= spec.min_height:
                if spec.max_width and (w > spec.max_width or h > spec.max_height):
                    continue
                picked = img
                break
        if picked is None and images:
            # Fallback: use first available but rename with a warning
            picked = images[0]
            target_name = f"_DIMENSION_MISMATCH__{target_name}"
        if picked:
            zf.write(str(picked), target_name)
