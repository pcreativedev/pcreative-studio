# Roadmap — ThemeForge

Future improvements organised by feature area. Items here are not
scheduled — they represent known gaps and ideas to revisit.

For pre-publication blockers (private to the maintainer), see
`ANTES-DE-PUBLICAR.md` (gitignored).

---

## Where we are right now

**v1.0.0 shipped on 2026-05-23** with full Linux support (AppImage /
.deb / .rpm / AUR) and a macOS alpha `.app` produced by CI. See the
[Releases](../../releases) page for downloads and `CHANGELOG.md` for
the full list of features included in 1.0.

The roadmap below covers post-1.0 work. Items are grouped per feature
area; the "Current state" line at the top of each section reflects
what shipped in v1.0.

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
- 🪟 **Windows:** backlog. No code paths tested.

### macOS — next steps

What's left to graduate from alpha to beta:

- **Real-machine smoke test.** Mac user (anyone) downloads
  `ThemeForge-macOS.zip`, drags to `/Applications`, confirms the
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

### Windows — port plan

Larger porting effort:

- **PowerShell shell helper.** Currently
  `platform_compat.shell_argv()` returns `["cmd", "/c", ...]` on
  Windows. PowerShell would be cleaner for long-running pipes
  (better unicode + JSON support).
- **Path conventions.** Most code still hardcodes
  `~/.config/themeforge/` — migrate to
  `platform_compat.app_config_dir()` everywhere.
- **`.exe` bundling.** `pyinstaller --onefile --windowed` on
  `windows-latest` GitHub runner. Or `briefcase` (BeeWare) for a
  proper MSIX.
- **CI workflow.** `.github/workflows/build-windows.yml` mirroring
  the macOS workflow.
- **AI CLI invocation paths.** Claude/Codex/Gemini/OpenCode all
  ship cross-platform Node binaries via npm — should JustWork™ once
  shell abstraction is verified on Windows.
- **Test in PowerShell 7+.** Older PowerShell versions have unicode
  bugs that affect emoji output in the UI panels.

### Cross-platform infrastructure (apply to all)

- ✅ ~~Cross-platform `platform_compat.py` module~~ — done in v1.0.
- ⏳ Replace direct `~/.config/themeforge/` references with
  `pc.app_config_dir()`. The helper exists; ~30 call sites still
  hardcode the Linux path.
- ⏳ Replace direct `~/.cache/themeforge/` with `pc.app_cache_dir()`.
- ⏳ CI test matrix once we have 1.x stable: Ubuntu 24, Fedora 40,
  Arch (rolling), macOS 13+, Windows 11.
