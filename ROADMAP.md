# Roadmap — Pcreative Studio

Future improvements organised by feature area. Items here are not
scheduled — they represent known gaps and ideas to revisit.

For pre-publication blockers (private to the maintainer), see
`ANTES-DE-PUBLICAR.md` (gitignored).

---

## Where we are right now

**v1.8.0 shipped on 2026-06-18.** Releases out the door:

- **v1.0.0** (2026-05-23) — initial public release. 60+ stacks,
  embedded preview + terminal, pre-flight, ZIP builder, demo
  deploy, cost tracker, multi-agent compare, plugin system.
- **v1.1.0** (2026-05-24) — UI UX Pro Max integration,
  autoskills coverage for all 7 providers, live stats for the
  reference analysis dialog on every provider (stream_parsers.py).
- **v1.2.0** (2026-05-24) — app theme system (5 sprints: tokens /
  variants / Lucide icons / visual editor / Figma DTCG import),
  Vibe scaffolder, "Nuevo proyecto" form redesigned with sub-tabs,
  MCP server + curated catalog of 12 community MCPs.
- **v1.2.1** (2026-05-25) — **Windows support
  (alpha)**: Inno Setup installer, bundled Node+git, software-GL
  fallback, prebuilt node-pty, cross-platform paths. Video splash,
  predefined niche field (90 niches), dependency setup wizard,
  assets/demo-data policy in generated CLAUDE.md.
- **v1.2.2** (2026-05-25) — first-run onboarding
  wizard, AI credentials manager (7 providers), form defaults, and
  cross-platform dependency-wizard hardening (Linux npm `~/.local` +
  single-terminal sudo, macOS Homebrew PATH/bootstrap, Windows winget
  `--disable-interactivity` + exit-code re-check, validated on a Win10 VM).
- **v1.2.3** (2026-05-26) — **🚀 Operator (Hermes,
  optional)**: autonomous missions (Mission Control tab) + live preview +
  interactive chat, run on new or existing/gallery projects, learns per-project.
  **Figma → build** (implement a Figma frame via figma-context MCP) + Figma token
  in credentials. Multiple project windows (open/create more while one runs).
  Windows single-UAC winget + PHP/Composer + venv path + terminal scrollbar.
  Package-manager auto-detect (pnpm/yarn/bun) with non-fatal install.
- **v1.8.0** (2026-06-18, current Latest) — **📱 Pcreative Studio mobile
  (thin client + remote engine)**: `api_gateway.py` (FastAPI JSON-RPC/WS,
  13 sync + 6 stream tools + upload), PWA + Capacitor shell, remote bridge
  `tfbridge-remote.js` (reimplements `window.tfBridge` over the API), FCM
  push notifications. **ForgeCommerce stack** (Medusa 2 + Next.js,
  self-hosted, multi-gateway, AI-native via pgvector) + growshop variant,
  added to the e-commerce stacks. **Per-stack MCP refinement** — the
  `.mcp.json` generator no longer recommends JS UI MCPs on non-JS stacks.

Linux ships as AppImage / .deb / .rpm / AUR; macOS + Windows alpha
builds from CI. See [Releases](../../releases) for downloads and
`CHANGELOG.md` for the full feature list.

The roadmap below covers post-v1.2 work. Items are grouped per
feature area; the "Current state" line at the top of each section
reflects what's already on `main`.

---

## 🚀 Demo deploy

Current state (v1.0): deploys static / SPA stacks to Netlify / Vercel /
Cloudflare Pages / Surge with auto-detected build command + dist dir.
See `docs/USER_GUIDE.md` §10 for full details.

### Future updates

- **Server-rendered support.** Add a "Server" deploy path for stacks
  that need a runtime (Laravel, WordPress, Express, Rails, Spring,
  Phoenix…). Candidate targets:
  - Render (`render.yaml` + Git push)
  - Railway (`railway up`)
  - Fly.io (`fly deploy`)
  - DigitalOcean App Platform (spec yaml)
  - VPS via SSH/rsync (manual config)
- **Custom domain configuration.** After deploy, prompt to alias the
  generated `*.netlify.app` / `*.vercel.app` to a user-owned domain.
  Per provider:
  - Netlify: `netlify sites:update --custom-domain`
  - Vercel: `vercel domains add`
  - Cloudflare Pages: API call to attach custom domain
  - Surge: deploy directly to `<chosen>.example.com` if CNAME exists
- **Deploy history per project.** Persist every deploy (timestamp,
  provider, URL, build duration, dist size) in
  `~/.config/themeforge/deploys.json`. Show in a sub-tab of the
  ProjectWindow with rollback links (Netlify/Vercel preserve old
  deploys for free).
- **Multi-provider parallel deploy.** "Deploy to all" button that
  fires Netlify + Vercel + CF Pages simultaneously to compare
  cold-start performance / regional CDN coverage.
- **Pre-deploy lighthouse pass.** Optional checkbox to run
  `lighthouse <deployed-url>` after deploy and surface the score in
  the success popup (perf / a11y / SEO / best-practices).
- **Deploy to PR preview branch.** Detect current git branch; for
  branches != main, deploy to a preview slug
  (`<branch>--<project>.netlify.app`) and post the URL as a GitHub
  comment if a PR exists.
- **Auth-status indicator pre-deploy.** Run `netlify status` /
  `vercel whoami` synchronously before the deploy dialog opens and
  show a green dot / red dot per provider. Skip dropdown providers
  not authed unless user clicks "use anyway".
- **Headless / CI auth via env vars.** Document how to drive the
  deploy from a CI runner via `NETLIFY_AUTH_TOKEN`, `VERCEL_TOKEN`,
  `CLOUDFLARE_API_TOKEN`, `SURGE_LOGIN` + `SURGE_TOKEN`.

---

## 💰 AI cost tracker

Current state (v1.0): scans Claude Code + Codex local stores, renders
QtCharts donut + bar + stacked-bar, with detail tables. Pricing
hard-coded for common models. See §12 of USER_GUIDE.

### Future updates

- **Gemini scanner.** gemini-cli (v0.43+) does not currently persist
  token usage in a documented local format. Track upstream issue /
  wait for an API. Fallback: link to Google AI Studio billing page.
- **OpenCode scanner.** opencode-ai (v1.15+) stores session data
  but the schema is unstable. Implement once the format is documented.
- **Pricing refresh from a remote manifest.** Optional `pricing.json`
  in `~/.config/themeforge/` overrides `cost_tracker.PRICING`. Long
  term, fetch from a community-maintained manifest with consent.
- **Ephemeral 1h cache pricing.** Differentiate 5-min vs 1-hour cache
  rates per Anthropic's tiered cache pricing.
- **Long-context tier pricing** (`[1m]` Opus variants etc.).
- **Cost forecast.** "At this monthly burn rate you'll spend $X by
  EOM" — extrapolate from the current month's average daily cost.
- **Budget alerts.** Soft warning when crossing a configurable
  monthly threshold (e.g. notify when month-to-date > $500).
- **Per-project tagging.** Group projects into "client work" /
  "personal" / "research" buckets and show cost breakdown per bucket.

---

## 📦 Marketplace ZIP builder

Current state (v1.0): builds a ThemeForest-ready ZIP excluding 30+
noise patterns, with documentation/screenshots/source opt-ins.

### Future updates

- **Per-marketplace presets.** ThemeForest, CodeCanyon, Gumroad,
  Creative Market each have slightly different layout conventions
  (e.g. ThemeForest requires `Main Files/`, `Documentation/`,
  `Licensing/` subfolders). Add a preset picker that restructures the
  ZIP accordingly.
- **License file injection.** Auto-add `LICENSE.txt` (regular or
  extended depending on marketplace) at the ZIP root, generated from
  a template.
- **Demo-data ZIP variant.** Separate `<slug>-demo-data.zip` with
  WordPress export, Sanity dataset, etc., for buyers to populate
  their copy.

---

## 🔬 Pre-flight checker

Current state (v1.0): 13 automated checks for marketplace readiness.

### Future updates

- **Customizable check list.** YAML-driven check definitions in
  `~/.config/themeforge/preflight.yaml` so users can disable / add
  custom checks without editing `preflight.py`.
- **Automatic fix suggestions.** For some warns (missing LICENSE,
  missing README, .env tracked) offer a one-click "fix it" action.
- **Lighthouse integration.** Auto-run lighthouse against the local
  preview URL and surface scores in the pre-flight report.
- **HTML validation.** Auto-run html-validate against built output
  and report violations.
- **CSS lint pass.** stylelint pass surfaced in the report.
- **Image weight check.** Flag images > 200 KB unoptimized.

---

## 🖼️ Gallery

Current state (v1.0): card view with thumbnails, tags, last AI
session, archive toggle, command palette (Ctrl+K).

### Future updates

- **Bulk operations.** Multi-select projects in the gallery and bulk
  archive / tag / delete.
- **Sort options.** Sort by last modified, last AI session, alphabetic,
  cost burned, lines of code.
- **Search by content.** Full-text search across CLAUDE.md /
  AGENTS.md files in project tree (not just project names).
- **Project templates.** Pin certain projects as "template starters"
  for one-click cloning into a new project.

---

## 🧩 Plugin system

Current state (v1.0): user plugins at `~/.config/themeforge/plugins/*.py`
can register stacks / template types / agents.

### Future updates

- **Hook plugins.** Allow plugins to register lifecycle hooks
  (`on_project_created`, `pre_deploy`, `post_deploy`,
  `before_zip_build`) for advanced customisation.
- **Plugin marketplace.** Optional plugin browser that pulls from a
  community git repo (`themeforge-plugins/awesome-plugins`).
- **Sandboxing.** Currently plugins have full Python access. For
  shared / community plugins, add a permission model (filesystem,
  network, subprocess).
- **Hot-reload.** Watch the plugins dir and reload without restart.

---

## 🤝 Multi-agent compare

Current state (v1.0): main-window tab that runs the same prompt
across Claude / Codex / Gemini / OpenCode CLIs in parallel,
side-by-side panes with live streaming output, TTFT and wall time
per agent. See §13 of USER_GUIDE.

### Future updates

- **LibreUIUX integration (Claude-only)** — evaluate adding optional
  bundling of [HermeticOrmus/LibreUIUX-Claude-Code](https://github.com/HermeticOrmus/LibreUIUX-Claude-Code)
  (MIT): 74 skills + 152 agents + 76 slash commands + 70 plugins
  curated for Claude Code UI/UX work. Asymmetry caveat: upstream
  targets `.claude/{agents,commands,skills}/` only — would break the
  "full provider parity" rule unless we either:
  (a) ship as a Claude-only optional toggle (disabled for
       codex/gemini/opencode/openrouter),
  (b) source equivalent content for other providers from somewhere
       else, or
  (c) keep it as a documented community resource without auto-install.
  Decision deferred. Volume is also large (296+ files), so a
  selective subset picker may be the right UX.
- **Token / cost extraction.** Parse stream-json from Claude
  (`--output-format stream-json`) and equivalent from Codex to
  extract `input_tokens`, `output_tokens`, model, and compute cost
  via `cost_tracker.PRICING`. Show in pane stats line.
- **Per-agent model picker.** Dropdown per agent to override the
  default model (opus vs sonnet for claude, o3 vs gpt-5-codex-pro
  for codex, etc.).
- **Diff view.** Toggle to show line-by-line diff between two
  agents' outputs (highlights divergences).
- **Vote-merge / cherry-pick.** Select paragraphs from each agent's
  output and assemble a composite response. Output to clipboard or
  inject into a target file.
- **"Use as canonical" action.** Pick the winner and inject its
  response into the project's CLAUDE.md as the canonical answer to
  the prompt.
- **Per-agent system prompt / temperature.** Configure prompt
  variations per agent for A/B testing.
- **Prompt history.** Persist last N prompts in
  `~/.config/themeforge/multi_agent_history.json` for quick recall.
- **Markdown rendering pane toggle.** Toggle between raw text and
  rendered markdown view per pane.
- **Concurrent prompt template variables.** Run the same template
  with different variables (`{name}` → "Alice" / "Bob" / "Carol")
  across one agent to compare outputs.

---

## 🎨 App themes

Current state (post-v1.1.0, on main): 5 sprints shipped — full theme
system for Pcreative Studio's own UI (separate from uipro/autoskills which
theme the projects it generates). See `themes/` module and §17 of
USER_GUIDE.

**Shipped:**

- ✅ **Sprint 1** — JSON-token schema, QPalette + QSS pipeline, 5
  builtin themes (Dark/Light/Dracula/Nord/Tokyo Night), Settings
  dropdown with hot-reload, persistence.
- ✅ **Sprint 2** — Component variants (`button: flat|raised|pill|
  brutalist|ghost`, `tab: underline|card|pill|segmented`, `input:
  outlined|filled|underlined|brutalist`, `density: compact|
  comfortable|spacious`, etc.) + 3 showcase themes (Brutalism,
  Linear, Soft UI).
- ✅ **Sprint 3** — 38 Lucide SVG icons in `assets/icons/lucide/`,
  `tf_icon(name, color, size)` renderer that swaps `currentColor`
  for the theme's accent, applied to the 6 main tabs. Re-tints on
  theme change via `theme_signals.theme_changed` pyqtSignal.
- ✅ **Sprint 4** — Live visual editor `ThemeEditorDialog`: 21 color
  swatches with QColorDialog pickers, 5 shape sliders, 6 component
  dropdowns, metadata fields. Every edit re-applies the working
  ThemePack to the whole app (the app IS the preview). Save writes
  to `~/.config/themeforge/themes/<slug>.json`.
- ✅ **Sprint 5** — Figma DTCG import (`themes/figma_import.py` +
  `figma_import_dialog.py`). Two paths: paste/load DTCG JSON from
  Tokens Studio (free Figma) or call REST API `/variables/local`
  (Enterprise). 26 color + 5 shape regex patterns score Figma
  tokens against Pcreative Studio slots; user can re-target or skip rows.
  Reverse export `themepack_to_dtcg()` for round-trips back to
  designers.

### Future updates

- **Sprint 6 — Motion + density deeper.** `motion` tokens (transition
  duration / easing). QPropertyAnimation pulses on theme change.
  Density modes (compact / comfortable / spacious) propagate to
  font sizes, not just padding.
- **Sprint 7 — Effects opt-in.** Glassmorphism via cached
  `QGraphicsBlurEffect` (per Qt research, performance-sensitive —
  cache the blurred pixmap once per resize). Neumorphism via double
  shadow (inset + drop). Optional per-theme; off by default.
- **Sprint 8 — Theme marketplace.** Read-only browser of a community
  themes repo (e.g. `pcreativedev/themeforge-themes-community`),
  one-click install. Optional `share-via-gist` button.
- **Sprint 9 — Per-tab accent variations.** Each main tab gets a
  slight color shift (Builder=accent_blue, Gallery=teal,
  Cost=amber, Compare=purple, Settings=neutral) for visual hierarchy.
- **Sprint 10 — AI mapping assist.** When importing DTCG with
  ambiguous token names, fall back to Claude/Codex (via cost
  tracker pricing) to suggest mappings. User confirms.
- **Sprint 11 — VSCode theme import.** Parse VSCode `theme.json`
  (`colors` + `tokenColors`) into our ThemePack format. Cross-
  pollinates from the VS Code community theme ecosystem.
- **Sprint 12 — Animated theme transitions.** Cross-fade between
  themes instead of instant switch.
- **More builtin themes**: Catppuccin Mocha/Latte, Solarized,
  Gruvbox, One Dark, GitHub light/dark, Carbon (IBM), Bento (Apple).

---

## 📡 MCP integration

Current state (on main, post-v1.1.0): two complementary capabilities
in the Model Context Protocol ecosystem (the standard adopted by
Anthropic / OpenAI / Google / cursor / windsurf in 2025-2026).

**Shipped:**

- ✅ **`mcp_server.py`** — Pcreative Studio's own stdio MCP server.
  Exposes 8 tools to any MCP client:
  `list_stacks`, `list_themes`, `list_recent_projects`,
  `list_supported_providers`, `estimate_cost`, `suggest_stack`,
  `run_preflight`, `build_zip`. Built on Anthropic's official `mcp`
  Python SDK (FastMCP). Runs as a subprocess — no VPS, no network.
- ✅ **`mcp_catalog.py`** — curated registry of 12 community MCPs
  (license-verified at curation time: 11 MIT/Apache-2.0 + 1
  Pcreative Studio). Auto-generates `.mcp.json` in scaffolded projects
  with the relevant subset per stack (web → playwright + chrome
  devtools + figma + browsermcp; shopify → +shopify-dev; backend
  with DB → +postgres; etc.).
- ✅ **Per-stack MCP refinement** (v1.8.0) — the recommendation engine
  is now stack-language aware: JS-oriented UI MCPs (browsermcp,
  chrome-devtools, figma, etc.) are no longer injected into non-JS
  stacks (Laravel/PHP, Rails, Spring, Phoenix, Python backends…),
  which keep only the MCPs that actually apply (e.g. postgres for a
  DB stack). Cleaner `.mcp.json`, no irrelevant tooling.

### Future updates

- **Tool: `scaffold_project`** — let MCP clients invoke the full
  scaffolder via a tool call (Claude says "create a Next.js
  landing for X" and Pcreative Studio runs the scaffold + uipro +
  autoskills in the background, no GUI click). High value, needs
  careful UX around async progress reporting.
- **Tool: `deploy_demo`** — same as above for the 🚀 Demo deploy
  flow.
- **MCP marketplace UI** — a Settings panel that lists the 12
  curated MCPs with toggles to enable/disable per project. Each
  entry shows: license, repo link, env vars required.
- **Auth manager** — for MCPs that need tokens (GitHub, Figma,
  Postgres), surface a one-click "configure token" flow in
  Settings that writes to `~/.config/themeforge/mcp-secrets.json`
  (chmod 0600) and injects into env at MCP launch time.
- **Per-project MCP overrides** — let users edit a project's
  `.mcp.json` from the ProjectWindow without dropping to the
  filesystem.
- **HTTP/SSE transport for `mcp_server`** — Phase 2 of the MCP
  server: expose it over HTTP for remote / cloud clients. Tied to
  [[project-themeforge-cloud]] (the future SaaS direction).
- **More MCPs in the catalog**: WordPress MCP (when one stabilises),
  Lemon Squeezy / Polar / Paddle (for licensing flow), Vercel /
  Netlify (deploy automation), Linear / Notion (ticket import).
- **MCP usage analytics** — track which MCPs are actually invoked
  per project so the recommendation engine learns over time.
- **Tool schemas via JSON Schema** — currently FastMCP infers from
  Python type hints; richer schemas (with examples + validation)
  improve client UX.

---

## 📦 Distribution

Current state (v1.0): GitHub Actions builds **AppImage** (universal),
**.deb** (Debian/Ubuntu), **.rpm** (Fedora/RHEL/openSUSE) and
**.app** (macOS) on every `v*` tag, attached to a draft Release.
PKGBUILDs for **AUR** (`themeforge` + `themeforge-git`) live in
`packaging/aur/`. Source tarball auto-generated by GitHub.

### Future updates

- **Code-signing / notarization for macOS.** Sign the `.app` bundle
  with an Apple Developer ID ($99/year) so Gatekeeper doesn't block
  first launch. Add `xcrun notarytool submit` to the macOS workflow.
- **AUR publish automation.** GitHub Actions job that pushes the
  bumped PKGBUILD to AUR on each tagged release using `ssh-aur-bot`.
- **Homebrew tap.** `homebrew-themeforge` tap with a cask that
  installs the macOS .app and the necessary deps via brew.
- **PyPI package.** `pip install themeforge` for users who want to
  vendor it in their own venv. Tricky because PyQt6 versioning is
  not fully consistent across PyPI / distro packages.
- **Flatpak.** FlatHub manifest for sandboxed installation across
  distros. Higher cost than AppImage (review process + manifest
  maintenance). Worth doing once we have telemetry showing demand.
- **Nix flake.** For the NixOS minority. Low effort, PR-friendly.
- **Snap.** Lower priority — most desktop Linux users are off Ubuntu,
  and snap auto-updates are contentious in the community.
- **Windows installer.** See "Windows port" below for the bundling
  side once the codebase actually runs there.

---

## 📱 Mobile / remote engine

Current state (post-v1.8.0, on main): thin client + remote engine
architecture so the heavy Pcreative Studio engine runs on a host machine
(or VPS) while a phone drives it over the network.

**Shipped:**

- ✅ **`api_gateway.py`** (v1.8.0) — FastAPI gateway exposing the
  engine over JSON-RPC + WebSockets: 13 synchronous tools, 6
  streaming tools, plus file upload. Lets any remote client invoke
  the scaffolder, gallery, cost tracker, preflight, etc.
- ✅ **PWA + Capacitor shell** (v1.8.0) — the existing WebUI runs as a
  Progressive Web App and is wrapped with Capacitor for installable
  iOS/Android builds.
- ✅ **`tfbridge-remote.js`** (v1.8.0) — remote bridge that
  reimplements `window.tfBridge` over the gateway API, so the same
  WebUI screens work unchanged against a remote engine instead of the
  in-process QWebChannel bridge.
- ✅ **FCM push notifications** (v1.8.0) — Firebase Cloud Messaging
  push so long-running jobs (scaffold finished, build done) notify the
  phone even when the app is backgrounded.

### Future updates

- **Auth / pairing flow.** Secure pairing between the phone client and
  the host engine (token + QR pairing over Tailscale / LAN), so the
  gateway isn't open to anything that can reach the port.
- **Offline queueing.** Queue actions on the client while the engine
  host is unreachable and replay on reconnect.
- **Mobile-native gallery polish.** Touch-optimised gallery and
  project views (swipe actions, pull-to-refresh) beyond the desktop
  WebUI reflow.
- **Ephemeral engine container.** Spin up a throwaway containerised
  engine on demand (per session) so the phone doesn't need a
  permanently-on host. Tied to the cloud direction.

---

## 🛒 E-commerce stacks

Current state (post-v1.8.0, on main): the e-commerce category groups
all commerce platforms under one flat picker (the platform lives in
the stack `name`, not in sub-categories). Each ships scaffold +
platform-specific CLAUDE.md guidance and the relevant MCP subset.

**Shipped:**

- ✅ **ForgeCommerce stack** (v1.8.0) — first-party agency commerce
  stack: **Medusa 2 + Next.js**, self-hosted, multi-gateway payments,
  AI-native (pgvector). Non-interactive scaffold with a Docker compose
  (pgvector + redis) and a security/payments/AI blueprint baked into
  the generated CLAUDE.md. Ships a **growshop variant** preconfigured
  for that niche.

### Future updates

- **More first-party niche variants** on top of ForgeCommerce
  (restaurant, services, B2B wholesale) reusing the Medusa 2 + Next.js
  base.
- **Storefront theme starters** — opinionated Next.js storefront
  templates (minimal, editorial, high-conversion) selectable at
  scaffold time.
- **Seed/demo dataset** generator for ForgeCommerce so a fresh
  scaffold has browsable products out of the box.

---

## 🌐 General product

### Future updates

- **i18n.** Currently UI is in Spanish / docs in English. Add a
  language picker (en / es / pt / fr) for the UI.
- **Onboarding tour.** First-launch interactive walkthrough that
  builds a sample project, runs preflight, builds a ZIP.
- **Telemetry (opt-in).** Anonymised usage stats so we can see which
  stacks / providers people actually use.
- **Update notifier.** Check GitHub releases on startup and surface
  available updates in the Settings panel.
- **Discord / Matrix community.** A chat space for users to share
  templates, plugins, scaffolds and questions. Discord is the
  default for OSS dev communities right now.
- **Demo video / GIF on README.** A 30-second screencast going from
  "Nuevo proyecto" to "🚀 Demo deployed" would significantly improve
  conversion on the README landing.
- **Bug template + feature template** in `.github/ISSUE_TEMPLATE/`.

---

## 🖥️ Cross-platform support

Current state (v1.0):

- 🐧 **Linux:** stable. Tested on CachyOS / Arch / Ubuntu / Fedora.
  Pre-built AppImage / .deb / .rpm available.
- 🍎 **macOS:** alpha. Cross-platform refactor complete
  (`platform_compat.py` handles all OS-specific calls — file
  manager, terminal launcher, shell exec, VS Code launcher, config
  dirs). Pre-built `.app` from CI on every release. **Not yet
  validated on real Mac hardware** — looking for beta testers.
- 🪟 **Windows:** alpha. PyInstaller `--onedir` + Inno Setup
  installer built on every release tag. All filesystem paths
  migrated to `pc.app_config_dir()` / `pc.app_cache_dir()` so
  config lands in `%APPDATA%/themeforge`. Shell calls and process
  control go through helpers. **Not yet validated on real Windows
  hardware** — looking for beta testers.

### macOS — next steps

What's left to graduate from alpha to beta:

- **Real-machine smoke test.** Mac user (anyone) downloads
  `Pcreative Studio-macOS.zip`, drags to `/Applications`, confirms the
  .app launches and the main tabs render. Report issues. This is
  the single biggest unknown.
- **Migrate paths to `~/Library/Application Support/themeforge/`.**
  Currently `platform_compat.app_config_dir()` returns the right
  Mac path, but most of the codebase still writes to
  `~/.config/themeforge/` directly. Mass replace once Mac is
  validated.
- **Code-signing + notarization.** $99/year Apple Developer ID.
  Without it, Gatekeeper warning on first launch (workable for
  alpha, ugly for stable).
- **Retina icon polish.** Verify the .icns renders crisp at 2x DPI
  on real Macs.
- **PyInstaller `.app` plumbing for QtWebEngine.** Confirm
  `--collect-data PyQt6.QtWebEngineCore` correctly bundles the
  Qt framework — this is the most fragile piece on Mac.

### Windows — next steps

What's left to graduate from alpha to beta:

- **Real-machine smoke test.** Windows 10/11 user downloads
  `Pcreative Studio-Setup-X.Y.Z.exe` from a release, runs the installer
  (no-admin per-user install), confirms the .exe launches and the
  main tabs render. Report issues. Biggest unknown — like macOS.
- **SmartScreen "unknown publisher" warning** on first run. User
  must click "More info → Run anyway". Documented in README.
- **Code-signing.** Options:
  - Microsoft Azure Trusted Signing (~$9.99/mo) — managed, modern.
  - DigiCert/Sectigo Standard ($200/year) — needs reputation
    building.
  - EV cert with hardware token (~$400/year) — skips SmartScreen
    instantly.
  - Defer until install volume warrants.
- **winget submission.** PR to `microsoft/winget-pkgs` so users
  can `winget install pcreativedev.Pcreative Studio`. Stable channel.
- **`--onefile` mode evaluation.** Current build uses `--onedir`
  to reduce antivirus false positives. Re-evaluate once code-signed.
- **Embedded node-pty smoke test.** ConPTY backend (Windows 10
  1809+) should work but unverified.
- **wp-env / Docker validation.** Requires Docker Desktop + WSL2
  backend on the user's machine. Document the requirement.

### Cross-platform infrastructure (apply to all)

- ✅ ~~Cross-platform `platform_compat.py` module~~ — done in v1.0.
- ✅ ~~Replace direct `~/.config/themeforge/` with `pc.app_config_dir()`~~
  — done in v1.3 (all functional sites migrated).
- ✅ ~~Replace direct `~/.cache/themeforge/` with `pc.app_cache_dir()`~~
  — done in v1.3.
- ✅ ~~Wrap `pkill` / `chmod 0600` in cross-platform helpers~~ —
  done in v1.3 (`kill_processes_under_path`, `secure_file_chmod`,
  `secure_dir_chmod`).
- ⏳ CI test matrix once we have 1.x stable: Ubuntu 24, Fedora 40,
  Arch (rolling), macOS 13+, Windows 11.
