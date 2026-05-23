# Changelog

All notable changes to ThemeForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **📥 App theme system Sprint 5 — Figma import + DTCG support.**
  Two new modules:
  - `themes/figma_import.py` — DTCG v2025.10 JSON parser (W3C Design
    Tokens Community Group spec, the standard used by Tokens Studio,
    Style Dictionary, and 20+ tool vendors). Handles nested groups,
    `$type` inheritance, multi-mode `$value`, and DTCG aliases like
    `{color.brand.primary}` (resolved transitively up to 8 levels).
    Plus a Figma REST API client that calls
    `GET /v1/files/<key>/variables/local` with a Personal Access
    Token (Enterprise plan required by Figma) and translates the
    response into the same DTCG intermediate shape so the rest of
    the pipeline is unified.
  - `figma_import_dialog.py` — UI with two tabs: paste/load Tokens
    Studio JSON (free path) or fill Figma URL + PAT (Enterprise
    path). Auto-detected mappings appear in an editable table where
    every row has a checkbox to accept/skip, a confidence score
    (green ≥ 95 / yellow ≥ 85 / red < 85), a dropdown to re-target
    the ThemeForge slot, and editable raw value.
  - **Semantic mapping engine** with 26 color patterns + 5 shape
    patterns that score Figma token paths against ThemeForge slots
    (`color.brand.primary` → `accent`, `color.bg.elevated` →
    `bg_elevated`, `radius.full` → `radius_pill`, etc.). Higher
    score = more specific match wins per slot.
  - **Light/dark mode detection** via luminance heuristic on the
    detected `bg_primary` — imports default to the right tier
    automatically.
  - **Reverse path** `themepack_to_dtcg()` exports any ThemePack
    back to a DTCG JSON tree so designers can re-import it to Figma
    via Tokens Studio.
  Button **📥 Importar desde Figma…** added next to the theme picker
  in Settings.
- **✏️ App theme system Sprint 4 — Live theme editor.** New
  `theme_editor.py` module with `ThemeEditorDialog` opened from
  Settings → 🎨 Tema de la app → *"Personalizar tema actual…"*.
  Exposes every token of the active ThemePack as an editable widget:
  - **21 color rows** with hex text input + clickable color swatch
    that opens `QColorDialog` (organized into 5 sections:
    Fondos / Textos / Accent / Semánticos / Bordes-selección).
  - **5 shape sliders** (radius_sm/md/lg/pill, border_width).
  - **6 component dropdowns** (button/tab/input/scrollbar/checkbox/density).
  - Metadata fields (name, author, description, dark/light toggle).
  The whole app re-paints on every edit because the dialog calls
  `apply_theme()` after each change — there's no separate preview
  pane, the app itself IS the preview. **💾 Guardar como…** writes
  the working pack to `~/.config/themeforge/themes/<slug>.json` and
  switches the active theme to the new custom. **Cancelar** restores
  the theme that was active when the dialog opened.
- **🎨 App theme system Sprint 3 — Lucide iconography.** Tabs of the
  main window (`Nuevo proyecto`, `Galería`, `Coste IA`, `Comparar`,
  `licencias`, `Settings`) now render with Lucide SVG icons tinted
  in the active theme's accent color, replacing the previous emoji
  prefix in tab labels. New helper `themes.tf_icon(name, color, size)`
  reads SVGs from `assets/icons/lucide/`, swaps the `currentColor`
  attribute for the requested hex, and returns a QIcon cached by
  `(name, color, size)`. 38 icons bundled (search/settings/folder/
  code/terminal/play/stop/rocket/package/check/warning/info/refresh/
  trash/copy/download/save/file/image/box/gallery/dollar/users/key/
  monitor/archive/sparkles/palette/globe/+more). Lucide is ISC-licensed
  — compatible with GPL v3 redistribution.
- **🔁 Theme-change signal.** `themes.theme_signals.theme_changed`
  is a `pyqtSignal(str)` emitted whenever the user picks a different
  theme via Settings. Widgets that cache theme-dependent visuals
  subscribe to refresh without an app restart. Tab icons are the
  first consumer; future consumers will include the cost-tracker
  chart palette and the multi-agent compare pane colors.
- **🎨 App theme system Sprint 2 — component variants.** Adds
  per-widget variant tokens to the theme schema. Each ThemePack now
  carries a `components` section that selects between visual rule
  blocks:
  - **button_variant**: `flat` | `raised` | `pill` | `brutalist` | `ghost`
  - **tab_variant**: `underline` | `card` | `pill` | `segmented`
  - **input_variant**: `outlined` | `filled` | `underlined` | `brutalist`
  - **scrollbar_variant**: `thin` | `thick` | `hidden`
  - **checkbox_variant**: `square` | `rounded` | `pill`
  - **density**: `compact` | `comfortable` | `spacious`
  The QSS renderer is now a dispatch system — `_qss_button`,
  `_qss_tab`, etc. emit different rules per variant. Density modifies
  padding across all interactive widgets. 3 new builtin themes
  showcase the system end-to-end:
  - **Brutalism** — light, hard borders (2px), no radius, brutalist
    buttons/inputs, card tabs, orange accent.
  - **Linear** — dark, ghost buttons, segmented tabs (iOS-style),
    compact density, blue-violet accent (inspired by linear.app).
  - **Soft UI** — light, pill buttons + pill tabs + filled inputs,
    spacious density, generous radii (Apple-ish wellness vibe).
  Existing themes (Dark/Light/Dracula/Nord/Tokyo Night) keep their
  defaults (flat/underline/outlined/comfortable) for backwards
  compatibility — no visual regression.
- **🎨 App theme system (Sprint 1).** New `themes/` module with
  JSON-token-driven theming for the ThemeForge UI itself. Ships with
  5 builtin themes:
  - **ThemeForge Dark** (default) — blue accent, VSCode-inspired.
  - **ThemeForge Light** — paper-white with blue accent.
  - **Dracula** — purple + green pastel.
  - **Nord** — cool polar blues.
  - **Tokyo Night** — deep blues with neon accents.
  Each theme is ~20 lines of JSON exposing color, typography,
  spacing and shape tokens. User themes go in
  `~/.config/themeforge/themes/*.json` and override builtins with
  the same name. Theme picker in Settings → 🎨 Tema de la app, with
  instant hot-reload (no restart). Selection persists in
  `~/.config/themeforge/settings.json`. Architecture inspired by
  qt-material + PyQtDarkTheme but written from scratch to give full
  control over future component-variant + motion + effects layers
  (deferred to later sprints).

## [1.1.0] - 2026-05-24

### Added

- **🔍 Reference analysis live stats for ALL providers.** New module
  `stream_parsers.py` with per-CLI parsers (Claude, Codex, Gemini,
  OpenCode) that normalise their structured-output events into one
  canonical event shape consumed by the analysis dialog. As a result,
  the **TTFT + tokens + cost meter** (previously Claude-only) now
  works identically on the 7 ThemeForge providers. Cost is computed
  locally via `cost_tracker.cost_for` when the agent doesn't report
  it (currently only Claude reports `total_cost_usd` natively).
- **Structured output flags wired in `oneshot_argv`.** Each CLI is
  now invoked with its JSON event stream:
  - claude `--output-format=stream-json --include-partial-messages --verbose`
  - codex `exec --json --skip-git-repo-check -`
  - gemini `-p - -o stream-json`
  - opencode `run --format json [-m model]`
- **Graceful fallback to text mode** when the CLI binary is unknown
  or no parser is registered — old behaviour preserved.
- **autoskills coverage expanded to Gemini + OpenCode.** `autoskills`
  v0.3.6+ supports `gemini` / `opencode` / `cursor` / `windsurf` /
  `copilot` agents. Updated `ai_providers.py` to set
  `autoskills_flag` for `gemini`, `opencode` and `openrouter` (was
  previously `None`). All 7 ThemeForge providers now get the full
  autoskills + uipro skill stack on scaffold.
- **🎨 UI UX Pro Max integration.** New *"uipro UI/UX Pro Max"*
  checkbox in the project form (auto-checked for any stack with a
  visual UI surface; OFF only for `Backend · API` stacks). When on,
  ThemeForge runs `npx --yes uipro-cli init --ai <agent>` after
  autoskills, dropping the design-intelligence skill from
  [`nextlevelbuilder/ui-ux-pro-max-skill`](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)
  (MIT) into the project — 161 reasoning rules, 67 UI styles, 161
  paletas, 57 font pairings, 25 chart types. Complements
  `autoskills` (technical) with design intelligence. Provider mapping
  handles claude/claude-api/codex/codex-api/gemini/opencode/openrouter.
  Attribution in NOTICE + USER_GUIDE §8.

## [1.0.0] - 2026-05-23

Initial public release.

### Added

- **Gallery: card view with thumbnails.** Toggle between dense list
  and 220×190 cards with project thumbnails (200×120). Thumbnails are
  cached at `~/.cache/themeforge/thumbnails/<slug>.png` and generated
  either from screenshots captured with 📸 or as branded placeholders
  (vertical gradient with stack colour + project initials).
- **Gallery: custom tags per project.** Edit with **🏷️ Tags…**.
  Stored in `~/.config/themeforge/projects-meta.json`. Filter the
  gallery with `tag:<name>` in the search bar (chainable:
  `tag:venta tag:aurora`).
- **Gallery: last AI session indicator.** Each project row shows the
  time since the latest Claude Code conversation, by inspecting
  `~/.claude/projects/<encoded-path>/*.jsonl` mtimes.
- **Gallery: project archive.** Move projects to
  `~/Proyectos/themes-archive/` with **📦 Archivar**, reversible via
  **↩️ Restaurar**. Toggle **📦 Archivados** to switch views.
- **Command palette (Ctrl+K).** Spotlight-style fuzzy-finder over
  tabs, projects (active + archived), and quick actions. Multi-word
  queries, positional scoring, keyboard-only navigation.
- **🔬 Pre-flight checker.** Toolbar button in ProjectWindow that
  runs 13 automated checks against ThemeForest requirements + best
  practices: README, LICENSE, documentation/, screenshots/, jQuery
  legacy, Bootstrap legacy, hardcoded tracking, prefers-reduced-motion,
  .env tracked in git, project size + large files, unresolved scaffold
  placeholders, lighthouse / html-validate availability. Results grouped
  by severity with actionable hints.
- **📦 Marketplace ZIP builder.** Toolbar button in ProjectWindow that
  packages the project ready for upload to ThemeForest / CodeCanyon /
  Gumroad / Creative Market. Excludes node_modules, .git, .next, dist,
  .env, .cache, .vscode, .claude, CLAUDE.md, AGENTS.md, MEMORY.md,
  *.log, .DS_Store, vendor, target, etc. Dialog opt-in for
  documentation/, screenshots/, source/. Output:
  `~/Proyectos/themes-builds/<slug>-<ts>.zip`.
- **Plugin system.** User-defined plugins at
  `~/.config/themeforge/plugins/*.py` can register custom stacks,
  template types and AI agents without forking. Files starting with
  `_` are ignored (convention for disabled). Examples shipped in
  `examples/plugins/`.
- **💰 AI cost tracker.** New main-window tab "Coste IA" that scans
  local AI session stores (`~/.claude/projects/*.jsonl` for Claude
  Code, `~/.codex/logs_2.sqlite` for Codex) and reports cost / tokens
  by provider, model, project and day. Three QtCharts visualizations
  (donut by provider, horizontal bar for top 10 projects, stacked bar
  for last 30 days) with consistent provider colors, dark theme,
  animations, native tooltips. Pricing hard-coded for common Claude
  3.x/4.x, GPT-5.x, o3 and Gemini 2.x models in `cost_tracker.PRICING`;
  unknown models fall back to Opus rates marked with ⚠. No external
  API calls — entirely local.
- **🚀 Demo deploy.** Toolbar button in ProjectWindow that builds
  the project and deploys to **Netlify**, **Vercel**, **Cloudflare
  Pages** or **Surge.sh**, then copies the public URL to the clipboard
  and offers to open it in the browser. Auto-detects build command and
  dist directory for Next.js, Astro, Vite, SvelteKit, Gatsby, Nuxt,
  CRA, Angular, Hugo, Jekyll and plain HTML; user can override both in
  the dialog. CLI availability check with install hint, build → deploy
  chain runs in QProcess (UI remains responsive), logs streamed live to
  the project log panel.
- **📦 Multi-format Linux distribution.** GitHub Actions workflow
  `.github/workflows/build-linux.yml` builds three Linux artifacts
  from a single PyInstaller bundle on every tagged release:
  AppImage (universal), `.deb` (Debian/Ubuntu) and `.rpm`
  (Fedora/RHEL/openSUSE) — all via `fpm`. PKGBUILDs for AUR
  (`packaging/aur/themeforge` stable + `themeforge-git` git tip)
  to publish to the Arch User Repository. Local build script:
  `scripts/build-linux-appimage.sh`.
- **🖥️ Cross-platform refactor + macOS alpha.** New
  `platform_compat.py` module centralises every OS-specific call
  (file manager, terminal launcher, shell exec, VS Code launcher,
  config/cache dirs). All previously-Linux-only call sites
  (`bash -lc`, `konsole`, `dolphin`, `xdg-open`) now dispatch by OS.
  GitHub Actions workflow `.github/workflows/build-macos.yml`
  builds a `.app` bundle on every tagged release using a
  GitHub-hosted `macos-latest` runner — no Apple Developer ID
  required for distribution as alpha (Gatekeeper warning expected
  on first launch). Local build script: `scripts/build-macos.sh`.
- **🎨 App icon + desktop launcher.** ThemeForge ships an app icon in
  `assets/themeforge.png` (anvil + hammer + code/screens — branded for
  the project) plus pre-rendered sizes (16/32/48/64/128/256). The icon
  is loaded at startup and propagates to titlebar / taskbar / alt-tab
  / dock. A `scripts/install-desktop-entry.sh` script installs a
  user-local `.desktop` entry so ThemeForge shows up in the DE app
  menu (run with `--uninstall` to remove).
- **🤝 Multi-agent compare.** New main-window tab that runs the same
  prompt across multiple AI CLIs (Claude Code, Codex, Gemini, OpenCode)
  in parallel and displays the outputs side-by-side in resizable panes.
  Each agent shows live status (idle → running → done/error), TTFT
  (time-to-first-token) and total wall time. Agents not installed are
  shown disabled with the install hint. Per-pane **📋 Copiar** action
  copies the output to clipboard. Useful for: choosing the best agent
  for a task, debugging which model has the right take on a problem,
  or generating multiple competing solutions for a manual merge.
- Initial public release of ThemeForge.
- GUI builder (PyQt6) for scaffolding template projects across 60+
  stacks (Next.js, Astro, Laravel, WordPress, Shopify, Flutter, Tauri,
  Spring, Ktor, Phaser, R3F, …).
- Four creation modes: scratch, recreate-from-reference, adopt-local,
  existing-GitHub-repo.
- Conversational reference analysis dialog with multi-turn history,
  streaming, TTFT/token/cost metrics, and CLAUDE.md injection.
- Per-project window with embedded multi-tab preview, embedded
  terminal (xterm.js + node-pty), live dev-server logs, GitHub
  push/create with `.gitignore` sanitisation.
- Pixel Office visualizer integration (auto-install + auto-launch +
  embedded tab) using a fork of `neomatrix25/pixel-office-openclaw`
  (MIT) with Claude Code session reader added.
- Optional licensing system scaffolding for Next.js, Laravel,
  WordPress and Express stacks (verify-license route, setup wizard,
  middleware) driven by a configurable verify endpoint.
- Settings panel with diagnostic info, AI provider key management,
  Pixel Office install/launch/stop, default stack picker.
- Comprehensive English user guide (`docs/USER_GUIDE.md`) + styled
  HTML version (`docs/user-guide.html`) generated from the Markdown.
- AI agent support: Claude Code, Codex (OpenAI), Gemini (Google),
  OpenCode (with OpenRouter).
- Multi-stack mono-repo detection with sub-project dropdown.
- Stderr secret redactor (sk-…, gho_…, AIza…, glpat-…) so AI keys
  never reach the log panel.
- Context override system: `~/.config/themeforge/context-private/`
  takes precedence over the repo's `context/` so per-user private
  research / strategy can be injected into every project without
  touching the repo.

## Versioning policy

Until v1.0.0 the API is unstable. Breaking changes may happen between
0.x.y versions; the changelog will call them out under **Changed** or
**Removed**.

<!--
TEMPLATE for future releases (delete this comment when filling):

## [0.2.0] - YYYY-MM-DD

### Added
- …

### Changed
- …

### Fixed
- …

### Removed
- …

### Security
- …
-->
