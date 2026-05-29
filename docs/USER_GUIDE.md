# ThemeForge — User Guide

A GUI builder (PyQt6) for scaffolding modern template projects that you
can sell on marketplaces like ThemeForest, CodeCanyon, Creative Market
and Gumroad — driven end-to-end by AI coding agents (Claude Code,
Codex, Gemini, OpenCode).

This guide covers installation, first-time setup, the project creation
workflow, advanced features (multi-stack mono-repo support, embedded
preview, conversational reference analysis, GitHub integration, pixel-
art session visualizer), configuration files, the optional licensing
system, and troubleshooting.

---

## Table of contents

1. [What is ThemeForge](#1-what-is-themeforge)
   - [The Web UI (Neo-Tokyo · Matrix · Kawaii)](#the-web-ui-neo-tokyo--matrix--kawaii)
2. [System requirements](#2-system-requirements)
3. [Installation](#3-installation)
4. [Initial setup](#4-initial-setup)
5. [Quickstart — your first project](#5-quickstart--your-first-project)
6. [Project creation modes](#6-project-creation-modes)
7. [Supported stacks](#7-supported-stacks)
8. [AI providers](#8-ai-providers)
9. [Reference analysis (conversational)](#9-reference-analysis-conversational)
10. [ProjectWindow features](#10-projectwindow-features)
11. [Gallery and productivity shortcuts](#11-gallery-and-productivity-shortcuts)
12. [AI cost tracker](#12-ai-cost-tracker)
13. [Multi-agent compare](#13-multi-agent-compare)
14. [GitHub integration](#14-github-integration)
15. [Pixel Office visualizer](#15-pixel-office-visualizer)
16. [Settings panel](#16-settings-panel)
17. [App themes](#17-app-themes)
18. [Vibe scaffolder](#18-vibe-scaffolder)
19. [MCP servers](#19-mcp-servers)
20. [Optional licensing system](#20-optional-licensing-system)
21. [Configuration files](#21-configuration-files)
22. [Troubleshooting](#22-troubleshooting)
23. [Operator (Hermes) — autonomous missions](#23-operator-hermes--autonomous-missions)
24. [Credits and third-party licenses](#24-credits-and-third-party-licenses)

---

## 1. What is ThemeForge

ThemeForge is a PyQt6 desktop application that automates the boring
parts of starting a new template project:

- Scaffolds 60+ modern stacks (Next.js, Astro, Laravel, WordPress
  themes/plugins, Shopify, Flutter, Tauri, Spring, Ktor, Phaser, R3F…)
  with up-to-date defaults and security patches.
- Drops a CLAUDE.md/AGENTS.md context file in the project so any AI
  coding agent (Claude Code, Codex, Gemini, OpenCode) understands the
  goals and constraints from the first message.
- Provides modes for scratch, recreate-from-reference, adopt-local
  and existing-GitHub-repo workflows.
- Lets you analyse a reference template **interactively** with the AI
  agent — including stack recommendation, market research and
  reimplementation plan — and inject the analysis into the project's
  CLAUDE.md.
- Opens a per-project window with embedded preview (multi-tab
  browser), embedded terminal (xterm.js + node-pty), live logs and a
  one-click GitHub push/create flow.
- Optionally integrates your own licensing system (verify endpoint +
  setup wizard + admin panel hooks) into every theme generated.
- Optionally shows your active AI sessions as pixel-art avatars in a
  virtual office (via the bundled `pixel-office` visualizer).

ThemeForge does **not** generate the actual code of your templates —
the AI agent does. ThemeForge prepares the ground so the agent starts
with maximum context and minimum boilerplate.

---

## The Web UI (Neo-Tokyo · Matrix · Kawaii)

Since **v1.6.0** ThemeForge runs by default in a **web interface** rendered
inside QtWebEngine and connected to the same Python backend via a `QWebChannel`
bridge — so every screen below works exactly like the classic UI (real
scaffolding, preview, cost, licensing, Operator… nothing is mocked).

- **Three themes**, switchable in **Settings → Themes**, each with its own boot
  splash: **Neo-Tokyo** (cyberpunk, default), **Matrix** (green terminal),
  **Kawaii** (pastel). Web themes recolor instantly; choosing a *classic*
  theme restarts the app into the native QWidget UI.
- **Switching UI mode**: `THEMEFORGE_CLASSIC=1 themeforge` forces the classic
  native UI; `THEMEFORGE_WEB=1` forces the web UI. The choice is saved in
  `~/.config/themeforge/app_prefs.json` (`ui_mode`).
- **Opening a project** pops it in its **own window/modal** (like the native
  ProjectWindow) — it doesn't replace the gallery. When you forge a new
  project, the **setup runs in a real terminal** (the *Setup* tab) and the view
  switches to the **Agent** tab automatically when it finishes.
- **Add your own theme**: drop a JSON in `webui/themes/<slug>.json` (live
  recolor), or convert a Claude Design CSS export with
  `python tools/import_web_theme.py`.

All the features documented below (project modes, reference analysis,
ProjectWindow, Gallery, Cost, Compare, Market, Settings, Operator/Hermes)
are available identically in the web UI and the classic UI.

---

## 2. System requirements

| Component | Minimum | Notes |
|---|---|---|
| OS | Linux (Arch / CachyOS / Manjaro / EndeavourOS recommended) | Tested on KDE Plasma 6 Wayland. Should work on GNOME and other DEs. |
| Python | 3.11+ | For PyQt6 type hints. |
| PyQt6 | 6.6+ | Includes `PyQt6.QtWebEngineWidgets` for the embedded browser. |
| Node.js | 20+ | For the embedded terminal server, AI CLIs, and most stack scaffolds. |
| npm | latest | Bundled with Node. |
| Git | 2.40+ | For repo operations. |
| GitHub CLI (`gh`) | optional | Needed only if you want the "📦 GitHub" button to create/update repos. |
| Docker | optional | Required for stacks that use `docker-compose` or `wp-env` (WordPress). |
| Composer + PHP 8.3+ | optional | Required for Laravel / WordPress stacks. |

For the AI agents you'll want at least one of:

- `claude` (Claude Code CLI, Apache 2.0)
- `codex` (OpenAI Codex CLI, Apache 2.0)
- `gemini` (Google Gemini CLI, Apache 2.0)
- `opencode` (OpenCode CLI)

All four are invoked as external processes; ThemeForge does not bundle
them. Install whichever you plan to use.

---

## 3. Installation

ThemeForge is currently distributed as a Python project that you clone
and run with `launch.sh`. No PyPI package yet.

```bash
git clone https://github.com/pcreativedev/themeforge.git
cd themeforge

# Python dependencies — only PyQt6 needs to be installed.
# On Arch / CachyOS:
sudo pacman -S --needed python python-pyqt6 python-pyqt6-webengine

# On Debian / Ubuntu:
sudo apt install python3 python3-pyqt6 python3-pyqt6.qtwebengine

# Build the embedded terminal server (Node).
cd terminal
npm install
cd ..

# Launch
./launch.sh
```

Alternative: KDE menu entry. After cloning, copy or symlink
`themeforge.desktop` into `~/.local/share/applications/` (you'll need
to create it manually pointing at your `launch.sh` location).

---

## 4. Initial setup

The first time you launch ThemeForge, it creates `~/.config/themeforge/`
with:

```
~/.config/themeforge/
├── favorites.json          # bookmarked stacks (empty initially)
├── ports.json              # per-project port assignments
└── (you create the rest)
```

Optional files you can add to extend ThemeForge to your workflow:

- `~/.config/themeforge/keys.json` — API keys for AI providers
  (Anthropic, OpenAI, Google, OpenRouter). Permissions are auto-set to
  `0600`. The Settings panel offers a UI to populate this.
- `~/.config/themeforge/licensing.json` — URL of your own license
  verification endpoint, admin panel base, GitHub org, Java/Kotlin
  package ID. See §16.
- `~/.config/themeforge/known-product-slugs.txt` — one slug per line of
  your own product catalogue, used to auto-tick the "🔑 Activar
  sistema de licencias" checkbox when you start a new project with a
  matching name.
- `~/.config/themeforge/context-private/*.md` — your private versions
  of the context docs (market research, competitor analysis, licensing
  spec) that get injected into each new project's CLAUDE.md. See §16.

None of these are required for basic use.

---

## 5. Quickstart — your first project

1. Launch ThemeForge.
2. In the main form:
   - **Nombre** (Name): `My First Template`
   - **Stack**: click the button and pick *Next.js + Tailwind* (the
     default).
   - **Tipo** (Type): pick the category, e.g. *SaaS Landing*.
   - **Provider**: pick the AI agent you have installed (e.g. Claude).
   - **Modo** (Mode): leave on *Desde cero* (scratch).
3. Click **Crear proyecto y lanzar agente**.

What happens behind the scenes:

1. ThemeForge creates `~/Proyectos/themes/my-first-template/`.
2. Runs the Next.js scaffolder (`npx create-next-app@latest …`).
3. Copies the context MDs (`context/*.md`) into the project.
4. Generates `CLAUDE.md` (or `AGENTS.md` depending on provider) with:
   project metadata, market analysis, the template type, requirements
   from `REQUIREMENTS-THEMEFOREST.md`, your private context overrides
   if any (see §16).
5. Runs `npx autoskills -a claude` to install relevant skills for the
   stack (skips silently if `autoskills` is not installed; see §18).
6. `git init` + initial commit.
7. Opens the **ProjectWindow** with the embedded preview, terminal,
   logs and the AI agent ready to chat in a tab.

In the project window:

- The terminal tab on the right has the AI agent already loaded.
- Type something like *"Read CLAUDE.md and tell me what you understand
  before changing anything"* to confirm the agent has the full
  context.
- When you're happy, click **▶ Start preview** to launch the dev
  server in the embedded browser.

---

## 6. Project creation modes

### Desde cero (scratch)

Pure greenfield. Runs the stack scaffolder and gives you a clean
project. Best for new ideas that don't reference any existing template.

### Recrear referencia (recreate-from-reference)

You point ThemeForge at a folder, ZIP, or URL that contains the
"reference" template. ThemeForge:

1. Runs the stack scaffolder.
2. Drops the reference contents in `reference/` (added to `.gitignore`).
3. Sets up the CLAUDE.md so the AI agent treats `reference/` as
   read-only inspiration material, NOT as code to copy.

Use this when you want to build *your own* implementation of an idea
seen in a competitor template. The CLAUDE.md generated includes
strict anti-copy rules so the agent reimplements every line from
scratch with your branding.

This mode pairs with the **🔍 Analizar referencia con IA** button
(see §9) which produces a written analysis of the reference (market,
stack, gaps, plan) that gets injected into CLAUDE.md.

### Adoptar template local (adopt)

You already have a template in a folder and want to work on it
in-place with the ThemeForge workflow. ThemeForge:

1. Copies the contents of your local folder into
   `~/Proyectos/themes/<slug>/`.
2. Adds the context MDs and CLAUDE.md on top, so the agent inherits
   the ThemeForge conventions without altering your existing code.
3. Detects mono-repos automatically and gives you a sub-project
   selector in the ProjectWindow.

### Trabajar sobre repo existente (existing)

You point at a GitHub repo (`owner/name`). ThemeForge:

1. `gh repo clone owner/name <slug>`.
2. Detects the stack from the repo contents.
3. Adds the context MDs + CLAUDE.md.
4. Opens the ProjectWindow.

This is best when you want to continue an existing project under the
ThemeForge umbrella — same preview/terminal/agent UI as new projects.

---

## 7. Supported stacks

The full list lives in `stacks.py`. As of the current version, 60+
stacks are supported including (non-exhaustive):

- **Web frontend**: Next.js (Tailwind / shadcn / Mantine / HeroUI),
  Astro (Tailwind / shadcn), Remix, Nuxt, SvelteKit, Qwik,
  SolidStart, React-Vite, Vue 3-Vite, Angular, plain HTML+Tailwind /
  Bootstrap.
- **Frontend libraries**: Storybook (React).
- **CMS · WordPress** (6 stacks since v1.4.0):
  - `wordpress-block` — FSE block theme (theme.json + templates/parts/
    patterns). Free pack: GenerateBlocks, Spectra, ACF free, Pods,
    Royal MCP, Novamira (free).
  - `wordpress-bricks` — Bricks Builder child theme (you supply Bricks
    via `wp_packs.json`). Free pack: GreenShift, ACF, Pods, Royal MCP,
    Novamira (free).
  - `wordpress-elementor` — Hello Elementor child theme. Free pack:
    Elementor (free), Essential Addons Lite, ACF, Pods, Royal MCP,
    Novamira (free) — plus auto-installs Hello Elementor as parent.
  - `wordpress-divi` — Divi child theme (you supply Divi via
    `wp_packs.json`). Free pack: ACF, Pods, Royal MCP, Novamira (free).
  - `wordpress-breakdance` — Breakdance plugin on Kadence base. Free
    pack: Kadence, Breakdance (free), ACF, Pods, Royal MCP, Novamira
    (free).
  - `wordpress-plugin` — PHP 8.2 plugin scaffold (PSR-4 + Composer +
    optional Vite/Vue admin UI). No Docker WP provisioning.

  Every WordPress theme stack auto-provisions WordPress + MariaDB in
  Docker, installs WP (admin/admin), drops a localhost autologin
  mu-plugin, installs the free pack via wp-cli, wires the Automattic
  WordPress MCP bridge in `.mcp.json`, and lays down `WORDPRESS-DEV.md`
  + `WORDPRESS-LEGAL.md` + a `./wp` wp-cli helper. Premium plugins or
  parent themes you have licensed are installed if and only if you
  declare a path or URL in `~/.config/themeforge/wp_packs.json`
  (gitignored, local-only). See [`docs/WORDPRESS.md`](WORDPRESS.md) for
  the full pipeline.

- **CMS · other**: Payload CMS, Strapi, Medusa, Sanity Studio,
  Directus, Docusaurus, VitePress, Starlight, Hugo, Eleventy.
- **Backend**: Hono (Bun / Cloudflare), NestJS + Prisma, FastAPI,
  Django + Tailwind, Phoenix LiveView, Rails + Tailwind, Bun-Elysia,
  Deno-Fresh, Spring Boot, Ktor, Go-Fiber, Rust-Axum.
- **Full-stack**: T3 Stack, Laravel + Inertia + Tailwind.
- **Mobile**: Flutter, Expo / React Native (NativeWind / Expo Router),
  Ionic + Capacitor, Kotlin + Compose.
- **Desktop**: Tauri (React), Electron (React).
- **Game-dev** (Vite + TypeScript): Phaser, PixiJS, React Three Fiber.
- **Email templates**: react-email.
- **Browser extensions**: Plasmo, WXT.
- **Shopify** (3 stacks since v1.5.0):
  - `shopify-liquid` — Online Store 2.0 theme. Clones the official
    [Dawn](https://github.com/Shopify/dawn) (MIT) as a starting point
    and adds `package.json` with the Liquid prettier plugin,
    `.prettierrc.json`, a strict `.theme-check.yml` (16 KB JS cap from
    the official Theme Store budget, parser-blocking checks, deprecated
    filters, template length), a GitHub Actions workflow using the
    official `shopify/lighthouse-ci-action@v1`, and `.mcp.json` wired to
    **3 official Shopify MCPs** — `shopify-dev` (STDIO, includes Polaris),
    `shopify-storefront` (HTTP, zero-auth) and `shopify-storefront-catalog`
    (HTTP, UCP, natural-language catalog search). ⚠️ Themes derived from
    Dawn are INELIGIBLE for the Shopify Theme Store (official rule); they
    are perfectly fine for **ThemeForest** or **Partner builds**. See
    [`docs/SHOPIFY.md`](SHOPIFY.md) for the full workflow.
  - `shopify-hydrogen` (NEW in v1.5.0) — headless storefront with
    **Remix v3 + React 19 + Oxygen + Tailwind**. Scaffold via
    `@shopify/create-hydrogen`. For catalogs > 500 SKUs, multi-market
    builds, and the ThemeForest "Hydrogen" category (higher ticket).
  - `shopify-polaris-app` (NEW in v1.5.0) — embedded Shopify Admin app
    with **Polaris + App Bridge 4 + Remix + Prisma**. Scaffold via
    `@shopify/create-app --template remix`. Targets the **Shopify App
    Store** or custom apps with theme/checkout/customer-account/admin/
    POS/Flow/Functions extensions.
  - `shopify-liquid-blank` (NEW in v1.5.0) — Online Store 2.0 theme
    from scratch (no Dawn clone) — eligible for the **Shopify Theme
    Store** since Dawn-derived themes are auto-rejected.
  - `shopify-functions` (NEW in v1.5.0) — Rust + Wasm extensions for
    custom server-side logic (discounts, payment/delivery
    customization, cart validations, fulfillment constraints). Runs
    inside Shopify infra with a ≤ 5 ms budget.
  - `shopify-storefront-webcomponents` (NEW in v1.5.0) — embedded
    commerce in non-Shopify sites (blogs, landings, WordPress,
    Webflow). Vanilla HTML + Shopify CDN-hosted Web Components.
  - `shopify-checkout-extension` (NEW in v1.5.0) — UI extension inside
    the hosted Shopify checkout. **Shopify Plus only.** $50-500/mo
    typical pricing.
- **E-commerce — non-Shopify** (NEW in v1.5.0, all under the unified
  `E-commerce` category in the picker):
  - `magento-hyva` — Magento 2.4.8+ child theme on top of **Hyvä**
    (Tailwind v4 + Alpine.js). Hyvä went open-source on 2025-11-10
    under OSL 3.0 + AFL 3.0. The scaffold also auto-installs the
    **Freento MCP** module (MIT) so the agent can query orders,
    products, customers, etc. against the store. Marketplaces: Adobe
    Commerce Marketplace + ThemeForest.
  - `saleor-nextjs` — official Saleor Storefront (Next.js 15 App
    Router + GraphQL Codegen + Tailwind, BSD-3). Backend = Saleor
    Cloud / self-hosted / public demo.
  - `vendure` — MIT headless commerce backend (NestJS + GraphQL +
    TypeORM/Postgres) with embedded Angular admin. Optional Next.js
    storefront chosen during the `@vendure/create` scaffold.
  - `bigcommerce-stencil` — BigCommerce theme based on the official
    **Cornerstone** (MIT) + Stencil CLI (Handlebars + SCSS Citadel /
    Foundation 5.5). 2nd theme store after Shopify by volume;
    Cornerstone-derived themes are ineligible for the BigCommerce
    Theme Store.
  - `medusa` — existing stack since v1.x; MIT (Node + Next.js).
  - `prestashop-theme` — PrestaShop 9 child theme inheriting from
    `classic` (OSL 3.0). Smarty templates + assets pipeline. Markets:
    PrestaShop Addons (2k+ templates, €40-150) + ThemeForest.
  - `opencart-theme` — OpenCart 4.x theme packaged as an extension
    (GPL). Twig templates. OCMod was removed in OC 4 — only events
    are supported. Markets: OpenCart Marketplace + ThemeForest (1.5k+).
  - `sylius` — Sylius 2.x full commerce framework (MIT) on Symfony
    7.4. Doctrine ORM 3 + Twig 3 + API Platform 3, multi-channel
    native. SyliusThemeBundle for custom themes.

  All 15 e-commerce stacks live under the single **E-commerce**
  category in the stack picker. Full walk-through with prereqs,
  scaffold steps, activation and distribution channels in
  [`docs/ECOMMERCE.md`](ECOMMERCE.md).

Each stack has:
- A `scaffold` command list run via bash.
- A `skills` list (Anthropic / Vercel / WordPress / Shopify skill
  packages auto-installed by `npx autoskills`).
- A `preview` profile (the dev-server command + port).
- A `notes` string with stack-specific gotchas surfaced in the UI.

To add a new stack, see `stacks.py` — append a dict to the `STACKS`
constant. Pull requests welcome.

---

## 8. AI providers

ThemeForge invokes external AI agent CLIs as subprocesses. Supported:

| Provider | CLI binary | API key env var | License of CLI |
|---|---|---|---|
| Claude (Anthropic) | `claude` | `ANTHROPIC_API_KEY` | Apache 2.0 |
| Codex (OpenAI) | `codex` | `OPENAI_API_KEY` (via `codex login --with-api-key`) | Apache 2.0 |
| Gemini (Google) | `gemini` | Google OAuth or `GEMINI_API_KEY` | Apache 2.0 |
| OpenCode | `opencode` | `OPENROUTER_API_KEY` (for OpenRouter models) | Apache 2.0 |

### Setting API keys

Open the Settings panel (gear icon) and use the provider picker. Keys
are stored in `~/.config/themeforge/keys.json` with `chmod 0600`. The
directory is `0700`.

Keys are never logged. The UI shows only `set` / `unset`, never the
value. They are passed to the AI agent subprocess via
`QProcessEnvironment`. As an extra defense, the stderr panel of the
reference-analysis dialog redacts `sk-…`, `sk-ant-…`, `sk-proj-…`,
`sk-or-v1-…`, `AIza…`, `gho_…`, `ghp_…`, `glpat-…` patterns before
showing them.

### Skills auto-install (`autoskills`)

If the **npx autoskills** checkbox is on (default), ThemeForge runs
`npx autoskills -a <provider>` after scaffolding to install the
provider-specific skills declared by the stack. Skills are official
packages from Anthropic / Vercel / WordPress / Shopify referenced by
slug; ThemeForge doesn't redistribute them.

`autoskills` itself is by **midudev**
(<https://github.com/midudev/autoskills>) under **CC BY-NC 4.0**. See
§18 for the implication and how to disable in commercial builds.

### Design intelligence (`uipro` — UI/UX Pro Max)

A second, complementary skill: **UI UX Pro Max** by
[nextlevelbuilder](https://github.com/nextlevelbuilder)
(<https://github.com/nextlevelbuilder/ui-ux-pro-max-skill>, MIT).
Whereas `autoskills` covers *technical* skills (Next.js patterns,
WordPress block themes, Shopify Liquid, …), `uipro` covers the
**visual** side: design systems, UI styles, color palettes, font
pairings, anti-patterns to avoid.

When the **uipro UI/UX Pro Max** checkbox is on (auto-checked for any
stack with a visual surface — disabled by default only for
backend-only stacks), ThemeForge runs
`npx --yes uipro-cli init --ai <agent>` immediately after autoskills.
This drops 161 reasoning rules + 67 UI styles + 161 palettes + 57
font pairings into the agent's context — so when the agent starts
writing CSS / Tailwind / SwiftUI / Flutter widgets, it does so with
a coherent design system already in mind.

Supported agents (auto-mapped by ThemeForge):
`claude`, `claude-api` → `claude` · `codex`, `codex-api` → `codex` ·
`gemini` → `gemini` · `opencode`, `openrouter` → `opencode`.

UI UX Pro Max is **MIT** licensed and invoked at runtime (never
bundled), so it imposes no extra licensing constraints on themes
generated with ThemeForge.

---

## 9. Reference analysis (conversational)

In `recrear` or `adopt` mode, the form shows a **🔍 Analizar
referencia con IA** button (and **🔍 Analizar con IA** for adopt).

When clicked, ThemeForge:

1. Scans the reference folder/zip with `reference_analyzer.py`:
   detects build-system markers (package.json, composer.json,
   pubspec.yaml, artisan…), recognises commercial-marketplace
   structures (`codecanyon-*` folder name, `Documentation/` /
   `Files/` / `Updates/` dirs, README mentioning Envato or purchase
   codes), and detects multi-stack mono-repos to depth 3.
2. Builds a prompt with the detected facts and either:
   - The **reference prompt** (anti-copy rules — for commercial
     templates that you'll reimplement in your own code), or
   - The **design-export prompt** (when the reference looks like an
     export from claude.ai/design, v0.dev or Figma Make — assumes
     it's your own design).
   The classifier is conservative: any marketplace marker
   (CodeCanyon / ThemeForest / Envato / commercial folder structure)
   forces the reference prompt with explicit "license is out of
   scope" framing.
3. Launches the selected AI provider with the prompt via the
   ReferenceAnalysisDialog. Streams the response, tracks tokens,
   TTFT and cost in real time (for stream-json capable CLIs like
   `claude --output-format=stream-json`).
4. When the turn ends, the **reply input** below the output enables.
   Type a follow-up and press **➡ Enviar respuesta**: ThemeForge
   builds a multi-turn prompt that includes the original prompt +
   full conversation history + your new reply, and relaunches the
   CLI. Each turn is appended to the same panel with visual
   separators (`👤 Tú:` and `🤖 Agente:`).
5. When you click **💾 Guardar y cerrar**, the full conversation is
   stored as the analysis, and gets injected into the project's
   CLAUDE.md when you click **Crear proyecto y lanzar agente**.

This is the killer feature: the project's AI agent starts already
aware of your detailed analysis of the reference (stack recommendation,
market research, gaps, your specific follow-ups). The agent confirms
what it understood before changing any code.

---

## 10. ProjectWindow features

Opening any project (newly created or via the Galería tab) gives you
a per-project window with:

```
┌────────────────────────────┬────────────────────────────┐
│  Tabs of embedded preview  │  Tabs of embedded terminals │
│  - Preview (default)       │  - Setup / Shell           │
│  - + (additional pages)    │  - Claude / Codex / Gemini │
│                            │  - 🎮 Office (visualizer)  │
├────────────────────────────┴────────────────────────────┤
│ Logs of the dev server (live tail)                      │
└─────────────────────────────────────────────────────────┘
```

### Preview tabs

The preview panel is a `QTabWidget` of `QWebEngineView`s. The first
tab ("Preview") is bound to the project's dev server. Click the **+**
button to add additional tabs (e.g. one for the landing, one for
`/wp-admin`, one for `/docs`).

- The URL bar is shared across tabs; pressing Enter navigates the
  active tab. The ↻ reload button also targets the active tab.
- Tab titles auto-update from the page's `<title>`.
- The first tab cannot be closed (it's the dev server preview).
- The 🚀 button opens the active URL in your external browser in
  `--app` mode (Brave / Chromium / Firefox) — useful for sustained
  performance on Wayland where QWebEngine can lag.
- 📸 captures a screenshot of the active tab to PNG.
- 🔧 opens a Chromium DevTools window on the active tab.

### Viewport presets

Buttons to clip the preview width to common breakpoints (360, iPhone
14, Tablet, 1280, 1920, Full). Useful for responsive QA without
opening a separate browser.

### Multi-stack mono-repo

If the project root has more than one stack (e.g. `Files/Laravel/`,
`Files/Flutter/Driver/`), a **Sub-proyecto** dropdown appears at the
top. Switching it changes the active preview profile, port and dev
server commands. Each sub-project gets its own port assigned in
`~/.config/themeforge/ports.json`.

### Terminal tabs

Backed by an embedded Node server (`terminal/server.js`) using
xterm.js + node-pty. On startup, ThemeForge spawns the server on a
random port and creates the configured tabs:

- **Setup** (if the project just scaffolded) — runs the setup script
  and leaves a shell.
- **Shell** — plain bash in the project root.
- **<AI Provider>** — runs your chosen agent CLI (`claude`, `codex`,
  `gemini`, `opencode`) in the project root.

You can switch tabs while the AI is running; each is an independent
PTY.

### ▶ Start preview / ■ Stop

Runs the stack's preview profile. For **detached** profiles (wp-env,
`docker compose up -d`), Stop remains enabled after Start exits with
code 0 because the containers are still up — Stop will invoke the
`stop` command of the profile (e.g. `npx @wordpress/env stop`).

### Dev server logs

The bottom pane is a live tail of stdout/stderr from the dev server.
Useful for catching compile errors without leaving ThemeForge.

### 🔬 Pre-flight checker

Toolbar button that runs a battery of automated checks against the
project to verify it's ready for marketplace upload (Envato, Gumroad,
Creative Market, etc.). Fast — filesystem + grep only, no external
tools required by default.

Checks (13 total, grouped by severity):

| Check | What it verifies |
|---|---|
| README presente | `README.md` / `README.txt` exists in root |
| LICENSE / licensing.txt | Required by Envato; recommended elsewhere |
| documentation/ HTML | `documentation/index.html` present (required by Envato) |
| screenshots/ | Folder with PNG/JPG captures; ≥3 recommended |
| Sin jQuery 1.x/2.x legacy | greps for `jquery-1.*`, `jquery-2.*` references |
| Sin Bootstrap 3/4 | greps for legacy Bootstrap versions |
| Sin tracking hardcoded | greps for GA, FB Pixel, Hotjar IDs |
| prefers-reduced-motion respetado | CSS includes the media query |
| .env fuera de git | `git ls-files` shows no `.env*` tracked (except `.env.example`) |
| Tamaño del proyecto | Total <50 MB ideal, lists files >10 MB |
| Placeholders del scaffold sustituidos | greps for `__SLUG__`, `__PROJECT__`, `YOUR_DOMAIN`, `__LICENSE_API_URL__`, etc. |
| Lighthouse instalado | Info-only: hints `npm i -g lighthouse` if missing |
| HTML validator | Info-only: hints `npm i -g html-validate` if missing |

Result dialog shows each check with pass / warn / fail / info icons,
ordered by severity (fail at top). Each item expands to show the
actionable hint ("how to fix") and details (e.g. list of files where a
problem was found).

Header verdict:

- **✓ Listo para empaquetar y subir.** — zero fails, zero warns.
- **⚠ Sin fallos críticos pero hay warnings…** — proceed but consider
  fixing the warns.
- **✗ N fallos bloqueantes…** — must resolve before upload (likely
  causes marketplace rejection).

Typical flow before publishing:

1. ProjectWindow → **🔬 Pre-flight** → review warns/fails.
2. Fix what each hint suggests.
3. Re-run → all green.
4. **📦 ZIP** (next section) → upload.

### 📦 Marketplace ZIP builder

Toolbar button that packages the project into a ZIP ready for upload
to any marketplace. Excludes development noise aggressively.

Auto-excluded directories: `node_modules/`, `.git/`, `.next/`, `.nuxt/`,
`out/`, `dist/`, `build/`, `.cache/`, `__pycache__/`, `.venv/`, `venv/`,
`.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `coverage/`, `.turbo/`,
`.vercel/`, `.netlify/`, `.vscode/`, `.idea/`, `.cursor/`, `.windsurf/`,
`.claude/`, `.aider/`, `target/`, `vendor/`, `.gradle/`, `.dart_tool/`.

Auto-excluded files: `.env`, `.env.local`, `.env.development`,
`.env.production`, `.env.test`, `.env.<anything>`, `.DS_Store`,
`Thumbs.db`, `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `MEMORY.md`,
`.eslintcache`.

Auto-excluded suffixes: `*.log`, `*.pyc`, `*.pyo`, `*.swp`, `*.swo`,
`*.bak`, `*.tmp`.

Dialog options (auto-detects which folders exist and pre-checks them):

- ✓ Include `documentation/`
- ✓ Include `screenshots/`
- ✓ Include `source/` (PSDs, Figma exports, editable assets)

Output: `~/Proyectos/themes-builds/<slug>-<YYYYMMDD-HHMMSS>.zip`. The
ZIP wraps content in a `<slug>/` root directory — standard marketplace
convention so unzipping doesn't pollute the buyer's cwd.

After build, popup shows:

- File count + uncompressed size + compressed size + compression ratio.
- Option to open the builds folder in your file manager.

Compression: `ZIP_DEFLATED` level 6 (good balance speed/size).
Typical ratio: 50-70% reduction for text-heavy themes.

### 🚀 Demo deploy

Toolbar button that builds the project and deploys to a public host
so you can share a working preview URL with a client, reviewer or
prospective buyer.

**Supported targets:**

| Provider | CLI | Auth required | Notes |
|---|---|---|---|
| **Netlify** | `netlify-cli` (`npm i -g netlify-cli`) | First time: opens browser for OAuth | Best static-site experience, edge functions if needed |
| **Vercel** | `vercel` (`npm i -g vercel`) | First time: opens browser for OAuth | Inspects the repo and picks its own dist; ideal for Next.js |
| **Cloudflare Pages** | `npx wrangler` (no install) | First time: opens browser for OAuth | Generous free tier, global edge |
| **Surge.sh** | `surge` (`npm i -g surge`) | First time: email/password prompt | Fast, anon-friendly for quick demos |

**Stack auto-detection** (from `package.json` deps + config files):

| Stack | Build command | Dist directory |
|---|---|---|
| Next.js (w/ `output: 'export'`) | `npm run build` | `out/` |
| Next.js (default) | `npm run build` | `.next/` (Vercel only) |
| Astro / Vite | `npm run build` | `dist/` |
| SvelteKit + adapter-static | `npm run build` | `build/` |
| Gatsby | `npm run build` | `public/` |
| Create React App | `npm run build` | `build/` |
| Angular | `npm run build` | `dist/` (verify `angular.json`) |
| Nuxt | `npm run generate` | `.output/public/` |
| Hugo | `hugo --minify` | `public/` |
| Jekyll | `bundle exec jekyll build` | `_site/` |
| Plain HTML | (none) | `./` |

The dialog pre-fills both fields with the detected values — you can
override them manually for stacks not in the table or for non-default
configurations.

**Flow:**

1. Click **🚀 Demo** in the project toolbar.
2. Pick a provider (default = first available CLI on PATH).
3. Confirm or edit build command + dist directory.
4. Hit **🚀 Build & Deploy**. UI shows live build logs, then live
   deploy logs (streamed via QProcess, so the app stays responsive).
5. On success: a popup shows the deployed URL, copies it to your
   clipboard, and offers to open it in your default browser.

**Server-rendered stacks** (Laravel, WordPress, Express, Rails…) are
NOT supported by this deploy — they need a Node/PHP/Ruby runtime that
static hosts don't provide. For those, use the **📦 ZIP** + manual FTP
or a server provider (Render, Railway, Fly.io, etc.).

**Auth troubleshooting:** Most providers open the browser the first
time. If you're using ThemeForge over SSH or in a headless setup,
the deploy will fail with an auth error. Run the CLI's `login` command
in a real terminal first:

```bash
netlify login
vercel login
npx wrangler login
surge login
```

---

## 11. Gallery and productivity shortcuts

The **Galería** tab lists every project ever created in
`~/Proyectos/themes/` plus archived projects in
`~/Proyectos/themes-archive/`. Each row shows: name, stack, last
modified, git status, CLAUDE.md presence, last AI session, tags.

### Tags

Each project can have one or more user-defined tags (lowercase, no
`#`). Tags help organise large catalogues by status (`borrador`,
`venta-activa`, `archivado-2025`), client (`cliente-x`), or stack
(`aurora-*`).

Edit tags with the **🏷️ Tags…** button — input is comma- or space-
separated. Tags are normalised: lowercased, deduplicated, sorted.

To filter the gallery by tag, type `tag:<name>` in the search bar:

```
tag:venta-gumroad           # only projects tagged 'venta-gumroad'
tag:venta tag:aurora        # must have BOTH tags
aurora tag:venta            # matches 'aurora' in name/stack AND tagged 'venta'
```

Tags persist in `~/.config/themeforge/projects-meta.json` (JSON, one
entry per slug).

### Last AI session

Each project row shows the time since the last Claude Code session
(e.g. `🤖 hace 2h`, `🤖 hace 3 d`, `🤖 sin sesiones`). ThemeForge
inspects `~/.claude/projects/<encoded-path>/*.jsonl` and reports the
most recent file mtime.

This helps locate the "I was working on this yesterday" project
without remembering its name.

### Archive

Projects you're not actively working on can be moved to an archive
without deleting them.

- **📦 Archivar** button on a selected project → moves it to
  `~/Proyectos/themes-archive/<slug>/`. Confirms before moving.
- Toggle **📦 Archivados** (checkbox in filter row) → switches the
  gallery view to show archived projects only.
- In archive view, the action button changes to **↩️ Restaurar** —
  click it to move the project back to `~/Proyectos/themes/<slug>/`.

Archive is fully reversible. Conflicts (e.g. a project named `foo`
already exists in archive) raise a clear error without overwriting.

### Card view with thumbnails

Toggle **🖼️ Cards** / **📋 Lista** in the filter row switches between
the two view modes. State persists between sessions.

- **Lista** (default): dense rows with full metadata. Good for
  searching across many projects.
- **🖼️ Cards**: 220×190 cards in a responsive grid with a thumbnail
  (200×120). Visual recognition is faster.

Thumbnails are stored at `~/.cache/themeforge/thumbnails/<slug>.png`.

Sources of thumbnails (in priority order):

1. **Cached screenshot**: every time you click 📸 in a ProjectWindow,
   a 200×120 crop is saved as the project's thumbnail.
2. **Generated placeholder**: if no real thumbnail exists, ThemeForge
   draws one with QPainter — vertical gradient using the stack's
   brand colour (60+ stacks mapped) + project initials centred + stack
   name at the bottom. Looks clean even with zero captures.

To capture a real thumbnail for a project:

1. Open the project, **▶ Start preview**, wait for the dev server.
2. Click **📸** on the preview toolbar.
3. The screenshot is saved both to `screenshots/preview-<ts>.png` and
   as the gallery thumbnail.

### Command palette (Ctrl+K)

Press **Ctrl+K** from anywhere in the ThemeForge main window to open
a spotlight-style command palette. Fuzzy-finder over:

- **Navigation**: jump to any tab (Nuevo proyecto, Galería,
  licencias, Settings).
- **Projects**: open any active or archived project directly in a
  ProjectWindow without scrolling the gallery.
- **Actions**: new project, refresh gallery, switch to cards/lista
  view, jump to settings.

The palette regenerates the action list on each open, so newly
created or archived projects show up immediately.

Keyboard:

- `↑↓` navigate, `Enter` execute, `Esc` close.
- Type multiple words: `aurora laravel` matches items containing both.

The matching algorithm is substring with positional scoring: items
where the query appears earlier in the label rank higher; an exact
prefix match wins over a mid-string match.

### Other gallery actions

- **★ Favorito** — toggle. Filter to favourites-only with the **Solo
  favoritos ★** checkbox.
- **🔄 Regenerar contexto** — re-creates `CLAUDE.md` / `AGENTS.md`
  for the selected project with the latest context MDs.
- **🗑️ Eliminar** — permanent delete (project dir + Postgres
  container + ports.json entry + favourites entry). Irreversible —
  requires confirmation with typed project name.
- **VSCode**, **Codex**, **Claude Code** — open the selected project
  with the chosen tool.
- **Abrir carpeta** — opens the project dir in Dolphin / Nautilus /
  whatever file manager is installed.

---

## 12. AI cost tracker

The **💰 Coste IA** tab in the main window aggregates token usage
and cost across every AI provider's local session store and renders
three QtCharts visualizations + detail tables.

### Scanners

| Provider | Source | Status |
|---|---|---|
| **Claude Code** | `~/.claude/projects/<encoded-path>/*.jsonl` (`message.usage` + `message.model` per `type:assistant` event) | Fully supported, robust parsing |
| **Codex (OpenAI)** | `~/.codex/logs_2.sqlite` table `logs` — `feedback_log_body` strings parsed with regex looking for embedded JSON `response.usage` | Best-effort. May miss events depending on log format |
| **Gemini (Google)** | n/a — gemini-cli does not persist token data in a documented local format | "Not supported" — link to Google AI Studio billing |
| **OpenCode** | n/a — likewise | "Not supported" — link to OpenRouter activity |

Each provider's scanner is registered in `cost_tracker.SCANNERS`; the
panel calls them in parallel, aggregates the results into one
`AggregateReport` and feeds the charts/tables.

### Pricing

Pricing per 1M tokens is hard-coded in `cost_tracker.PRICING` for the
common Claude 3.x/4.x, GPT-5.x, o3 and Gemini 2.x model IDs. Each
event's cost is computed as:

```
cost = (input_tokens          / 1M) × price_input
     + (output_tokens         / 1M) × price_output
     + (cache_creation_tokens / 1M) × price_cache_write
     + (cache_read_tokens     / 1M) × price_cache_read
```

For models not in `PRICING`, the panel uses conservative defaults
(Opus rates) and marks the row with **⚠ default** in the "Tarifa"
column so you can see the number is an estimate.

Two known sources of divergence vs the official billing dashboards:

1. **Ephemeral 1-hour cache** has higher rates than the standard 5-min
   cache (~2× cache write). `PRICING` uses the 5-min rates.
2. **`[1m]` long-context variants** of Opus may have different
   pricing tiers depending on the API tier — not modelled.

For relative breakdowns (which project / model burns the most), the
tracker is reliable. For exact billing reconciliation, cross-check
with the provider's official dashboard.

### Charts

| Chart | Type | What it shows |
|---|---|---|
| **🍩 Donut by provider** | `QPieSeries` with 45% hole | Slice per provider with `<provider> $<amount> (<percent>%)`. Colors are consistent across charts (claude → blue, codex → green, gemini → amber, opencode → purple). |
| **📊 Top 10 projects** | `QHorizontalBarSeries` | Project paths decoded from Claude's encoded format (`-home-uther-Proyectos-themes-foo` → `~/Proyectos/themes/foo`), top 10 by cost, labels formatted `$amount`. |
| **📅 Last 30 days stacked** | `QStackedBarSeries` | One bar per day for the last 30 days, segmented by provider with consistent colors. Hover tooltips show exact values. |

All three charts use the dark theme with transparent background,
series animations on refresh, and native hover tooltips. They scale
with the window — resize the ThemeForge window to enlarge them.

### Filter

The combo at the top filters to a single provider:

- **Todos los proveedores** (default): aggregate across all known
  scanners.
- `claude`, `codex`, `gemini`, `opencode`: focus on one provider. The
  donut becomes a single-slice (less useful) but the daily chart and
  top projects refocus to that provider only.

Click **↻ Re-escanear** to re-read the session stores after using the
AI agents — the tracker doesn't auto-refresh while you work.

### Detail tables

Below the charts:

- **Por modelo (top 10)** — table with cost, events, tokens in/out,
  and tariff status (`✓ conocida` / `⚠ default`).
- **Por proveedor** — same data the donut shows but in tabular form
  with scanner notes (file paths scanned, event counts).
- **Por proyecto (detalle)** — same data as the top-10 horizontal bar
  but with full path and event counts.

### Privacy

The cost tracker reads ONLY local files in your home (`~/.claude/`,
`~/.codex/`). It does NOT contact any provider's API; pricing is
embedded constants. Your token data never leaves your machine.

---

## 13. Multi-agent compare

The **🤝 Comparar** tab in the main window runs the same prompt
across multiple AI CLIs in parallel and displays the outputs
side-by-side in resizable panes.

### Supported agents

| Agent | CLI | Invocation |
|---|---|---|
| Claude Code | `claude` | `claude -p "<prompt>"` |
| Codex | `codex` | `codex exec "<prompt>"` |
| Gemini | `gemini` | `gemini -p "<prompt>"` |
| OpenCode | `opencode` | `opencode run "<prompt>"` |

Agents whose CLI is not on PATH are shown disabled with the label
`<agent> (no instalado)`. Each agent has a consistent color across the
ThemeForge UI (claude blue, codex green, gemini amber, opencode purple).

### Flow

1. Open the **🤝 Comparar** tab.
2. Type the prompt in the textarea (anything from a one-liner to a
   multi-paragraph spec works).
3. Check the agents to run (defaults to all available).
4. Click **▶ Ejecutar**.
5. One pane per agent appears side-by-side, each streaming output as
   the CLI produces it. Stats line shows live status, TTFT
   (time-to-first-token) and total wall time.
6. Click **📋 Copiar** in any pane to copy that agent's output to
   the clipboard.
7. **■ Cancelar** kills all running processes; **🧹 Limpiar** clears
   the panes.

### Metrics shown per pane

- **⏳ idle** — pane created, process not started.
- **▶ corriendo…** — process started, waiting for first output.
- **⏱ TTFT 1.2s · corriendo…** — first output received at 1.2s, still streaming.
- **✅ TTFT 1.2s · total 8.4s** — finished successfully.
- **❌ exit 1 · 3.2s** — process failed (auth missing, prompt too long, etc.).
- **■ cancelado** — user clicked Cancel.

### Cost considerations

This tab does *not* track cost — each invocation runs in the CLI's
default account (OAuth for Pro/Max accounts, or API key if `--bare`
mode is configured). To see the cost of these runs, switch to the
**💰 Coste IA** tab and click **↻ Re-escanear** — the local session
stores get updated by each CLI invocation.

### Limitations (MVP)

- No per-agent model picker (uses each CLI's default model). For
  Claude that's the OAuth default; for Codex it's gpt-5-codex-pro
  (depending on the plan).
- No token / cost extraction (planned — see ROADMAP).
- No diff view between agents' outputs (planned).
- No "vote-merge" composite (planned).
- Server-rendered streaming responses are shown as plain text — any
  agent-specific formatting/markdown is preserved verbatim.

### Use cases

- **Choose the best agent for a task.** Different models excel at
  different domains (Claude on long-form code review, Codex on tight
  code edits, etc.) — compare empirically.
- **Debug an unclear specification.** Run the same prompt on N agents
  and check whether they all converge on the same interpretation. If
  they diverge, your prompt is ambiguous.
- **Generate competing solutions for manual merge.** Get 2-3 distinct
  approaches and cherry-pick the best parts.

---

## 14. GitHub integration

The **📦 GitHub** button in the project toolbar discovers existing
repos and offers update-or-create.

When clicked:

1. Verifies `gh` is installed and authenticated. If not, prompts to
   install via paru/apt and run `gh auth login`.
2. Calls `gh repo list` for your active user AND for the
   organisation listed in `~/.config/themeforge/licensing.json`
   (`github_org` field) if configured. Filters by repos whose name
   matches the project folder name (case-insensitive).
3. Shows a dialog with:
   - `↻ Actualizar  <owner>/<slug>  [public/private]` — for each
     match found.
   - `＋ CREAR nuevo  <your-gh-user>/<slug>  [privado]`.
   - `＋ CREAR nuevo  <github_org>/<slug>  [privado, org]` if
     `github_org` is set.
4. Once you pick an option:
   - **Sanitises the index**: ensures `.gitignore` blocks
     `node_modules/`, `.next/`, `dist/`, `build/`, `.env*`,
     `__pycache__/`, `.venv/`, `target/`, `vendor/`, `.idea/`,
     `.vscode/`, `.DS_Store`. If any of these were accidentally
     committed before, runs `git rm --cached` to untrack them, then
     creates a tidy-up commit.
   - **Updates existing**: sets `origin` to the chosen repo (if it
     doesn't match), then `git push -u origin HEAD`.
   - **Creates new**: `gh repo create <slug> --private --source=.
     --remote=origin --push`.
5. Logs the URL on success, shows a popup with the link.

---

## 15. Pixel Office visualizer

Optional. Visualises your active AI agent sessions as pixel-art
avatars in a virtual office, served as a web dashboard on
`localhost:3002`.

ThemeForge integrates with the MIT-licensed fork at
`pcreativedev/pixel-office-openclaw` (based on
`neomatrix25/pixel-office-openclaw`), with an additional reader for
Claude Code sessions added to its `server.js`.

### First run

The first time ThemeForge launches, if it doesn't find Pixel Office
installed, it asks:

> Pixel Office no está instalado. ¿Instalar ahora? (clones the repo
> to `~/.local/share/themeforge/pixel-office-openclaw/`, runs npm
> install + npm run build. Takes ~1-2 min.)

If you accept, ThemeForge installs and auto-launches `node server.js`
in background. The dashboard is then embedded in every
ProjectWindow's "🎮 Office" tab.

### How the Claude Code reader works

The server scans `~/.claude/projects/*/*.jsonl` files (where Claude
Code stores its conversations). For each `.jsonl` younger than the
active-window threshold (default 60 minutes):

- The file mtime → `lastActivity`.
- The first `{"type": "ai-title", ...}` line found → `name`.
- The `model` field of the last assistant message → `model`.
- The last user or assistant message → `lastMessage`.

These are exposed at `/sessions_list` in the same schema as OpenClaw
sessions. The React frontend renders one avatar per agent (project),
with status `active` / `waiting` / `idle` based on recency.

### Disable

Settings → 🎮 Office → ■ Stop. Or set
`PIXEL_OFFICE_NO_CLAUDE_CODE=1` to scan only OpenClaw, or pass
`--no-claude-code` to the CLI binary.

---

## 16. Settings panel

The Settings tab in the main window exposes:

- **AI providers**: API key configuration per provider (see §8).
- **Default stack**: select the stack used as the form default.
- **Postgres provisioning**: auto-spin a per-project Docker postgres
  container when scaffolding stacks that need a DB (Next + Drizzle,
  Laravel + Postgres, etc.).
- **🎮 Office**: install / launch / stop / open the Pixel Office
  dashboard.

---

## 17. App themes

> **TL;DR.** ThemeForge's own UI is fully themable: 8 builtin
> themes, a visual editor, and a Figma DTCG importer.
> This section is about **how the app you're using looks** — not
> about themes you generate for marketplaces. The latter is what
> autoskills / uipro (§8) do.

### 17.1 What's in the box

The `themes/` module ships **8 builtin themes**:

| Theme | Mode | Vibe |
|---|---|---|
| **ThemeForge Dark** (default) | 🌑 | VSCode-inspired, blue accent |
| **ThemeForge Light** | ☀️ | Paper-white, blue accent |
| **Dracula** | 🌑 | Purple + green pastel |
| **Nord** | 🌑 | Cool polar blues |
| **Tokyo Night** | 🌑 | Deep blues + neon accents |
| **Brutalism** | ☀️ | Hard 2px borders, no radius, orange accent |
| **Linear** | 🌑 | Ghost buttons, segmented tabs, compact density |
| **Soft UI** | ☀️ | Pill buttons, generous radii, spacious |

Pick one from **⚙ Settings → 🎨 Tema de la app → Theme** dropdown.
Changes apply **instantly without restart** — Qt repaints the
entire widget tree.

The active theme persists in
`~/.config/themeforge/settings.json` under the `theme` key.

### 17.2 Theme tokens — what each theme controls

Each theme JSON exposes 5 token groups (~50 tokens total):

1. **Color** (21 tokens): `bg_primary`, `bg_secondary`, `bg_tertiary`,
   `bg_elevated`, `fg_primary`, `fg_secondary`, `fg_disabled`,
   `accent`, `accent_hover`, `accent_active`, `accent_fg`, `success`,
   `warning`, `danger`, `info`, `border`, `border_strong`,
   `selection_bg`, `selection_fg`, `scrollbar_bg`, `scrollbar_thumb`.
2. **Typography** (11 tokens): font families + size scale + weights.
3. **Spacing** (5 tokens): `xs`, `sm`, `md`, `lg`, `xl` (in pixels).
4. **Shape** (5 tokens): `radius_sm`, `radius_md`, `radius_lg`,
   `radius_pill`, `border_width`.
5. **Components** (6 variant tokens):
   - `button_variant`: `flat | raised | pill | brutalist | ghost`
   - `tab_variant`: `underline | card | pill | segmented`
   - `input_variant`: `outlined | filled | underlined | brutalist`
   - `scrollbar_variant`: `thin | thick | hidden`
   - `checkbox_variant`: `square | rounded | pill`
   - `density`: `compact | comfortable | spacious`

The QSS builder dispatches by variant — `tab_variant: "pill"` emits
a different QSS rule block than `tab_variant: "underline"`. So
**two themes with identical colors can look radically different**
just by changing variant tokens.

### 17.3 Visual editor

**⚙ Settings → 🎨 Tema de la app → ✏️ Personalizar tema actual…**
opens a dialog with:

- 21 color rows with hex line edit + clickable swatch that opens
  `QColorDialog`.
- 5 shape sliders.
- 6 component dropdowns.
- Metadata fields (name, author, description, dark/light toggle).

Every edit re-applies the working ThemePack to the **entire app**
on the fly — the app itself is the live preview. **💾 Guardar
como…** prompts for a slug (auto-suggested from the name), writes
the JSON to `~/.config/themeforge/themes/<slug>.json`, switches the
active theme, and refreshes the dropdown with the new entry tagged
`(custom)`. **Cancelar** restores whatever was active when the
dialog opened.

### 17.4 Figma import

**⚙ Settings → 🎨 Tema de la app → 📥 Importar desde Figma…**
opens a two-tab dialog:

#### Path A: Tokens Studio JSON (free Figma)

1. In Figma, install the **Tokens Studio** plugin (free):
   <https://docs.tokens.studio/>
2. Define your design tokens in the plugin (colors, spacing, radius…).
3. Export to JSON (Tokens Studio's "Export" button) — output is W3C
   [DTCG v2025.10](https://www.designtokens.org/tr/drafts/format/)
   compatible.
4. Paste the JSON in the ThemeForge dialog tab, or click **📂 Abrir
   archivo JSON…**.
5. Click **⚡ Parsear y proponer mapeos**.

#### Path B: Figma REST API (Enterprise plan)

Requires Figma Enterprise + a Personal Access Token with
`file_variables:read` scope (see [Figma developer docs](https://www.figma.com/developers/api)).

1. Paste the Figma file URL (or just the file key).
2. Paste your PAT.
3. Click **🌐 Fetch + parsear** — ThemeForge calls
   `GET /v1/files/<key>/variables/local` and translates the response
   to DTCG.

#### Mapping table

In both paths, after parsing you get a table:

| ✓ | Figma path | Score | → ThemeForge slot | Valor |
|---|---|---|---|---|
| ☑ | `color.brand.primary` | 90 🟡 | `color.accent` | `#6366f1` |
| ☑ | `color.bg.base` | 95 🟢 | `color.bg_primary` | `#0d0d10` |
| ☑ | `radius.full` | 100 🟢 | `shape.radius_pill` | `999` |

- **Score** is the confidence of the auto-mapping (0-100).
  Green ≥ 95 / yellow ≥ 85 / red < 85.
- **Re-target** any row via the dropdown (e.g., the auto-mapper
  picked `accent` for `color.action` but you want it as `info`).
- **Uncheck** rows to skip them.
- Click **👁 Preview en vivo** to apply the current selection to the
  whole app without saving.
- Click **💾 Guardar como tema** to persist as a new theme JSON.
- **Cancelar** restores the original theme.

#### Multi-mode + alias support

If your DTCG file has multi-mode `$value` (e.g.
`{"light": "#fff", "dark": "#000"}`), the first mode is used by
default; future updates will surface a mode picker. DTCG aliases
(`{color.brand.primary}` references) are resolved transitively up
to 8 levels deep.

### 17.5 Theme file format

A complete theme JSON looks like:

```json
{
  "name": "My Custom Theme",
  "author": "you",
  "is_dark": true,
  "description": "...",
  "color": {
    "bg_primary":   "#1e1e1e",
    "accent":       "#62b4ff",
    "...": "..."
  },
  "shape": {
    "radius_sm": 3,
    "radius_md": 6,
    "...": "..."
  },
  "components": {
    "button_variant": "flat",
    "tab_variant": "underline",
    "density": "comfortable"
  }
}
```

Themes live in two locations:

- **Builtins** (read-only, shipped with ThemeForge):
  `themes/presets/*.json` inside the repo.
- **User-installed** (read-write):
  `~/.config/themeforge/themes/*.json`.

User themes **override** builtins with the same `name`, so you can
customize ThemeForge Dark without forking the repo. Forward-
compatible: unknown JSON keys are ignored silently, missing keys
fall back to the dark defaults.

### 17.6 Round-trip back to Figma

ThemeForge exposes `themepack_to_dtcg()` (see `themes/figma_import.py`)
which converts any ThemePack back to a DTCG JSON tree. The reverse
flow is: edit a theme in ThemeForge → save → re-import to Figma via
Tokens Studio. This closes the loop between designers and the dev
team.

### 17.7 Limitations

- Typography tokens are not yet editable from the visual editor
  (you can hand-edit the JSON in `~/.config/themeforge/themes/`).
- DTCG `typography` composite tokens (font family + size + weight in
  one) are parsed but not currently mapped to ThemeForge slots.
- Motion / animation tokens are not yet implemented (Sprint 6).
- Glassmorphism / neumorphism effects are not yet supported (Sprint 7).

See [`ROADMAP.md`](../ROADMAP.md#-app-themes) for the planned
sprints.

---

## 18. Vibe scaffolder

The **"Nuevo proyecto"** tab opens on the **✨ Vibe** sub-tab. Type
what you want to build in plain Spanish or English — no need to
know stack names, just describe the goal:

```
Landing premium para clínica dental en Madrid, paleta cálida
confianza, conversion-optimized
```

Click **✨ Pre-rellenar form con IA** and ThemeForge:

1. Sends the description to the active AI provider (the one selected
   in the Provider field — defaults to Claude).
2. Receives a structured JSON proposal with:
   - `stack_key` — one of the 60+ stacks (e.g. `astro-tailwind`).
   - `template_type` — Landing / SaaS / Portfolio / …
   - `theme_hint` — one of the 8 builtin themes that fits the vibe.
   - `dev_prompt` — a polished 150-300 word brief in the user's
     language, structured (niche / aesthetic / required sections /
     constraints / tech requirements).
   - `reasoning` — 2-3 sentences explaining the picks.
3. The form auto-fills: stack, type, theme of the app (switches live),
   autoskills + uipro toggles, suggested name (slug-derived).
4. The `dev_prompt` is stashed and injected into the generated
   `CLAUDE.md` / `AGENTS.md` when you hit **Crear proyecto** — so the
   dev agent starts with the full brief, not the original 1-line
   description.

### Decision rules

The vibe prompt embeds explicit rules so the AI's pick is predictable:

- WordPress / WP keyword → `wordpress-block` or `wordpress-plugin`.
- Shopify keyword → `shopify-liquid`.
- "Landing" / "marketing" → Astro or Next.js.
- "Admin" / "dashboard" / "SaaS app" → Next.js.
- "Mobile app" → Flutter or Expo.
- Premium / wellness / spa → Soft UI theme.
- Tech / SaaS / productivity → Linear theme.
- Creative / portfolio → Dracula or Brutalism theme.
- Gaming / cyber → Tokyo Night theme.

### Robust parsing

The response parser handles:

- Clean JSON output.
- JSON wrapped in markdown code fences.
- JSON with leading/trailing prose ("Here's the proposal: ...").
- Balanced-brace fallback for malformed trailing content.

If parsing fails, the dialog surfaces a clear error and lets you
retry. The dev_prompt is the most important field — if it's empty,
the proposal is rejected.

### When to skip

If you already know exactly what you want (stack + theme + type),
skip the Vibe tab and go straight to **🏗️ Setup**. Vibe is a
productivity accelerator, not a requirement.

---

## 19. MCP servers

ThemeForge participates in the **Model Context Protocol (MCP)**
ecosystem in two ways:

### 19.1 ThemeForge as an MCP server

`mcp_server.py` exposes 8 tools to any MCP client (Claude Code,
Cursor, Windsurf, OpenCode, etc.). Once registered, the client can
invoke ThemeForge actions from its own conversation window — no need
to switch to the GUI.

#### Tools exposed

| Tool | What it returns |
|---|---|
| `list_stacks` | The 60+ scaffold targets with key + name + category + language |
| `list_themes` | The 8 builtin themes + any user-installed custom themes |
| `list_recent_projects` | Recent ThemeForge projects sorted by last-modified (with git status, AI session age, etc.) |
| `list_supported_providers` | The 7 AI providers + per-provider auth status |
| `estimate_cost` | USD cost for `(model, in_tokens, out_tokens)` via the pricing table |
| `suggest_stack` | Natural-language → recommended `{stack_key, template_type, theme_hint, dev_prompt, reasoning}` (same engine as the Vibe scaffolder) |
| `run_preflight` | The 13 marketplace-readiness checks against a project path |
| `build_zip` | Marketplace ZIP packaging (excludes node_modules, .env, .claude/, etc.) |

#### Registering in Claude Code

Edit `~/.claude.json` (or whatever config file Claude Code uses on
your platform) and add:

```json
{
  "mcpServers": {
    "themeforge": {
      "command": "python3",
      "args": ["/home/<you>/Proyectos/themeforge/mcp_server.py"]
    }
  }
}
```

Restart `claude`. The 8 tools appear under `mcp__themeforge__*`.

#### Registering in Cursor

`~/.cursor/mcp.json` uses the same JSON shape — drop the `themeforge`
entry there and reload Cursor.

#### Registering in Windsurf

Settings → MCP → add a new entry with command + args matching the
example above.

#### Transport

Stdio (JSON-RPC over stdin/stdout). The client launches `mcp_server.py`
as a subprocess on demand. **No network, no VPS, no remote endpoint.**
Built on Anthropic's official `mcp` Python SDK (FastMCP).

### 19.2 ThemeForge configures community MCPs in each scaffolded project

When the **📡 Pre-configurar MCP servers** checkbox in the Setup
sub-tab is on (default), ThemeForge writes a `.mcp.json` at the root
of every new project pointing at a curated subset of 12 community
MCP servers, selected based on the stack:

| MCP | License | When it's included |
|---|---|---|
| **filesystem** (modelcontextprotocol) | MIT | Always — sandboxed FS access |
| **fetch** (modelcontextprotocol) | MIT | Always — web content with HTML→md |
| **memory** (modelcontextprotocol) | MIT | Always — knowledge-graph persistence |
| **github** (official) | MIT | Always — issues / PRs / Actions |
| **themeforge** | GPL-3.0 | Always — ThemeForge's own MCP |
| **playwright** (Microsoft official) | Apache-2.0 | Web frontend / WordPress / Shopify |
| **chrome-devtools** (Google official) | Apache-2.0 | Web frontend / WordPress / Shopify |
| **figma-context** (GLips) | MIT | Web frontend (design-driven) |
| **browsermcp** | Apache-2.0 | Web frontend |
| **shopify-dev** (Shopify official) | (Shopify standard) | Shopify only |
| **postgres** (crystaldba) | MIT | Backend with DB |

The catalog lives in `mcp_catalog.py`. Each entry has metadata:
`key`, `license`, `repo`, `description`, `relevance` tags, and the
install command (`npx` / `uvx` / `docker run`). Adding new MCPs to
the catalog is a pure-Python edit — see the module docstring.

#### How the AI client uses `.mcp.json`

1. User opens the project directory (e.g. `cd
   ~/Proyectos/themes/my-new-theme`).
2. User runs `claude` (or opens Cursor with the folder).
3. The client reads `.mcp.json`, lists the registered servers.
4. On the first invocation of a tool, the client downloads the MCP
   via `npx` or `uvx` (cached afterwards) and launches it.
5. The agent sees ~9 new tools available (playwright, chrome
   devtools, github, themeforge, …) and uses them seamlessly.

#### Authentication

Some MCPs require user-provided tokens (env vars):

- **github**: `GH_TOKEN` env var with a fine-grained PAT.
  ThemeForge inherits the token from `gh auth token` if you ran
  `gh auth login` previously.
- **figma-context**: `FIGMA_API_KEY` env var with a Figma personal
  access token.
- **postgres**: `DATABASE_URL` env var. ThemeForge's Postgres
  toggle (Extras sub-tab) injects this automatically when a
  per-project container is provisioned.

The agent will tell you which env vars are missing on first use.

#### License compatibility

All 12 catalog entries are MIT or Apache-2.0 (verified at curation
time, see `NOTICE.md` for the full table). ThemeForge **never bundles**
their source — `.mcp.json` is a configuration pointer; the client
downloads each MCP at runtime via `npx` / `uvx` / `docker`. GPL v3 of
ThemeForge is therefore unaffected (subprocess invocation, not
linking).

Discovery reference for catalog curation:
[`punkpeye/awesome-mcp-servers`](https://github.com/punkpeye/awesome-mcp-servers)
— a community-maintained directory of 1500+ MCP servers.

### 19.3 Disabling MCP integration

If you don't want `.mcp.json` written:

- Uncheck **📡 Pre-configurar MCP servers** in the Setup sub-tab
  before clicking Create.

If you want to remove ThemeForge's MCP from your Claude Code config
later, just delete the `themeforge` entry from
`~/.claude.json` → `mcpServers`.

---

## 20. Optional licensing system

> **TL;DR — what's bundled and what isn't.**
>
> ThemeForge ships the **client side** of a license verification flow:
> setup wizard UI, middleware guard, and a small HTTP client that
> calls your verification endpoint with a documented request/response
> schema. ThemeForge does **NOT** ship the backend (the verify endpoint,
> the license database, the admin panel, the Gumroad/Stripe webhook).
> You bring your own, or you point the client at a third-party service
> (Lemon Squeezy License API, Polar, Paddle, Gumroad License Verify…)
> with a tiny adapter. If you don't sell themes with license keys at
> all, leave the checkbox off and nothing licensing-related is added
> to the project.

ThemeForge can scaffold a **license verification client** into every
new theme — useful if you sell on Gumroad / your own web store and
want each downloaded theme to verify the purchase code before
running.

Activation: check **🔑 Activar sistema de licencias** in the project
creation form. Optional sub-checkboxes:

- **└─ Crear repo gh `<your-org>/<slug>` (Phase 3)**: at end of
  scaffolding, runs `gh repo create` under your org.
- **└─ Forzar también en modos `adopt` / `existing`**: by default the
  scaffold only runs in `scratch` and `recreate` modes to avoid
  collisions; tick this if you want to overlay the licensing files on
  a template that doesn't have them yet.

The checkbox is auto-ticked if the project name matches one of the
slugs in `~/.config/themeforge/known-product-slugs.txt`.

### What gets dropped per stack family

| Stack family | Files generated |
|---|---|
| Next.js | `src/app/api/verify-license/route.ts`, `src/app/setup/page.tsx`, `src/store/setup-store.ts`, `middleware.ts`, `.env.example` additions, `npm install zustand` |
| Laravel | `app/Http/Controllers/SetupWizardController.php`, `CheckSetupWizard.php` middleware, `SetupState.php` model, dated migration, Blade view with Alpine wizard, `routes/web.php` and `bootstrap/app.php` patches (idempotent), `.env.example` additions |
| WordPress (plugin/theme) | `inc/class-license.php`, `inc/admin-license-page.php`, `README.licensing.md` |
| Express / Hono / NestJS / Bun-Elysia | `src/routes/license.ts` (stub), `.env.example` additions |
| Other stacks | A note in the project README pointing to `context/LICENSING-SYSTEM.md` for manual integration |

### URL templating

The verify-license URL, the panel base URL, and other host-specific
values are NOT hardcoded in the templates. They use placeholders
(`__LICENSE_API_URL__`, `__LICENSE_HOST__`, `__LICENSE_HOST_BARE__`,
`__ORG_ID__`) which `licensing_scaffold.py` substitutes at scaffold
time from `~/.config/themeforge/licensing.json`. If the config file
doesn't exist, placeholders (e.g. `https://YOUR_DOMAIN/...`) are
emitted instead.

### Bring your own backend

The PHP backend is not required to be a specific implementation. As
long as your endpoint accepts:

```http
POST /api/license/verify
Content-Type: application/json

{
  "license_key": "XXXX-YYYY-ZZZZ-WWWW",
  "product":     "<product-slug>",
  "domain":      "buyer-host.com",
  "action":      "activate",
  "version":     "1.2.3"
}
```

…and returns:

```json
{
  "valid":   true,
  "type":    "regular|pro|extended|developer",
  "email":   "buyer@example.com",
  "expires": "",
  "uses":    1,
  "max":     1,
  "product": "<product-slug>",
  "server_time": 1735689600
}
```

…the scaffolded clients (Next.js / Laravel / WordPress / Express) will
work. Drop-in compatible backends: Lemon Squeezy License API, Polar,
Paddle MoR, Gumroad license verify, or your own PHP/Node endpoint.

---

## 21. Configuration files

Under `~/.config/themeforge/`:

| File | Purpose | Permissions |
|---|---|---|
| `favorites.json` | Bookmarked stacks in the picker. | 0644 |
| `ports.json` | Per-project (and per-sub-project for mono-repos) port assignments. | 0644 |
| `projects-meta.json` | Per-project tags (`{"slug": {"tags": [...]}}`). See §11. | 0644 |
| `keys.json` | AI provider API keys. **Sensitive.** | 0600 |
| `licensing.json` | URLs, GitHub org, package ID for the optional licensing system. **Sensitive (URLs may be private).** | 0600 |
| `known-product-slugs.txt` | Your product catalogue, one slug per line. Used to auto-tick the licensing checkbox. | 0644 |
| `context-private/*.md` | Your private versions of context MDs (market research, competitor analysis, licensing spec). Overrides the public stubs in `context/`. | 0644 |

ThemeForge also persists state outside `~/.config/`:

| Location | Purpose |
|---|---|
| `~/Proyectos/themes/` | All active projects you've created with ThemeForge. |
| `~/Proyectos/themes-archive/` | Projects archived from the gallery (§11). Reversible. |
| `~/Proyectos/themes-builds/` | Marketplace ZIPs produced by **📦 ZIP** in ProjectWindow (§10). |
| `~/.cache/themeforge/thumbnails/<slug>.png` | Card-view thumbnails for the gallery (200×120). Generated from screenshots or as placeholders. Safe to delete — they regenerate. |
| `~/.local/share/themeforge/pixel-office-openclaw/` | Auto-installed Pixel Office visualizer (§13). |

### Context override pattern

When ThemeForge generates a new project, it copies context MDs to
`<project>/context/`. Discovery is dynamic:

1. Each `*.md` under `~/.config/themeforge/context-private/`.
2. Each `*.md` and `*.template.md` under `<repo>/context/` whose stem
   doesn't already exist in (1).

Templates have a `.template.md` suffix; their `.template` is stripped
on copy. This means you can ship public neutral stubs in the repo
(`MARKET-RESEARCH.template.md`) while injecting your real research
(`~/.config/themeforge/context-private/MARKET-RESEARCH.md`) into every
project you build locally.

The public stubs in `context/` are intentionally neutral — no product
names, no domains, no strategies leak from the repo.

---

## 22. Troubleshooting

### ThemeForge does not start (ImportError on PyQt6)

Install `python-pyqt6` and `python-pyqt6-webengine` from your distro.
On Arch: `sudo pacman -S python-pyqt6 python-pyqt6-webengine`. On
Debian: `sudo apt install python3-pyqt6 python3-pyqt6.qtwebengine`.

### Embedded terminal does not load

The terminal needs Node. Verify:

```bash
which node
node --version          # must be 20+
cd terminal && npm install
```

If still broken, look at the `[term-server stderr]` lines in the
project window's bottom log pane.

### Embedded preview shows blank in Wayland

QtWebEngine has known performance issues on some Wayland setups. Use
the 🚀 button to open the preview in Brave/Chromium in `--app` mode
instead. The native browser handles the page natively.

### "🎮 Pixel Office no está instalado" but I already installed it

The auto-detect checks two paths:

```
~/.local/share/themeforge/pixel-office-openclaw/
~/Proyectos/pixel-office-openclaw/
```

If you cloned elsewhere, either move it or symlink one of the above
to your install location.

### Project shows the "Connect to OpenClaw" gateway screen

ThemeForge's `pixel_office.py` serves the SPA at `localhost:3002`. The
SPA auto-connects to same-origin if `/sessions_list` responds. If the
gateway screen appears anyway, reload (Ctrl+R). If it persists, clear
browser cache for `localhost:3002`.

### `wp-env start` exits with `Error: No plugins activated`

A previous version of ThemeForge's wp-env config injected a buggy
`afterStart` hook. Open the `.wp-env.json` in your WordPress project
and delete the entire `lifecycleScripts` block — wp-env auto-activates
plugins listed in `plugins`. ThemeForge no longer emits the broken
hook for new projects.

### `start preview` succeeds but Stop is greyed out

For detached profiles (wp-env, `docker compose -d`), the start command
exits with code 0 after launching containers. Recent ThemeForge keeps
Stop enabled when the profile defines a `stop` command. Make sure
you're on the latest commit.

### `📦 GitHub` says "No estás autenticado en gh"

Run `gh auth login` in any terminal and complete the flow. ThemeForge
will pick up the auth on the next click. The OAuth token lives in
`~/.config/gh/hosts.yml` (managed by gh, NOT touched by ThemeForge).

### Brave / Chromium does not detect as installed

ThemeForge looks for one of: `brave`, `brave-browser`, `chromium`,
`google-chrome-stable`, `google-chrome`, `microsoft-edge`, `vivaldi`,
`firefox`, `xdg-open`. If none are found, the 🚀 button errors out.

### NTFS USB or disk won't mount

Install `ntfs-3g`. On Arch: `sudo pacman -S ntfs-3g`. CachyOS's
linux-cachyos kernel doesn't include the `ntfs3` in-kernel module by
default; `ntfs-3g` provides FUSE-based access.

### Reference-analysis dialog says "Need login" for Gemini

Gemini requires Google OAuth via `gemini` CLI's first-run flow OR a
`GEMINI_API_KEY` env var. Run `gemini` once in a terminal to complete
OAuth, or set the key via the Settings panel.

---

## 23. Operator (Hermes) — autonomous missions

The **Operator** is an **optional** integration that lets
[Hermes Agent](https://github.com/NousResearch/hermes-agent) (Nous Research, MIT)
act as an **autonomous orchestration brain** for ThemeForge: you give it a brief
in natural language and it plans, creates/builds, quality-checks, packages — and
**learns from each project** — without you driving every step.

> **100% optional.** ThemeForge works fully without Hermes. The Operator tab and
> the 🚀 buttons only appear **if Hermes is installed**. If you never install
> Hermes, nothing changes.

### 23.1 How it works (architecture)

- **Brain** = Hermes. It reasons/plans using an LLM provider (see below) and calls
  tools. It runs as a local CLI (`hermes`).
- **Hands** = ThemeForge's engine, exposed to Hermes as an **MCP server**
  (`mcp_server.py`), plus the AI coding agents ThemeForge already drives
  (Codex, Claude Code, OpenCode…). Hermes calls `create_project`,
  `run_agent_build`, `run_preflight`, `build_zip`, `list_recent_projects`, etc.
- The autoskills + UI/UX Pro Max quality layer is inherited automatically.

```
You (brief) → Hermes (plan) → MCP → ThemeForge tools → your agent CLIs (build)
                    │                                         │
                    └── QA loop (preflight) ── package (zip) ─┘
```

### 23.2 Install Hermes

Two ways (both optional):

- **From ThemeForge:** *Settings → 🔧 Setup dependencies → check
  “🚀 Hermes Agent (Operator)” → Install.* (Linux/macOS; on Windows it needs WSL.)
- **Manual:**
  ```bash
  curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
  ```
  Installs to `~/.hermes/`, binary at `~/.local/bin/hermes`.

### 23.3 Configure the brain (provider + API key)

Hermes uses an **API key** provider (not a subscription — see the compliance note).
Recommended: **OpenRouter** (one key, 200+ models).

```bash
hermes config set OPENROUTER_API_KEY sk-or-...
hermes config set model.provider openrouter
hermes config set model.default anthropic/claude-sonnet-4.6
```

Direct providers also work: `anthropic` / `openai` (`ANTHROPIC_API_KEY` /
`OPENAI_API_KEY`). Config lives in `~/.hermes/config.yaml` (settings) and
`~/.hermes/.env` (keys).

> **⚠ Compliance — important.** Anthropic's terms **prohibit** driving the Claude
> Code CLI with a **Pro/Max subscription** from an automated third-party tool;
> use an **API key** instead. OpenAI/ChatGPT subscriptions carry the same risk.
> The safe, supported path for any automation is **API keys, not subscriptions**.
> Using your own subscription (e.g. Codex logged in with ChatGPT) is your own
> decision and risk. This is not legal advice — check your plan's current terms.

### 23.4 Register the ThemeForge MCP server in Hermes

Add to `~/.hermes/config.yaml` so Hermes can call ThemeForge:

```yaml
mcp_servers:
  themeforge:
    command: python3
    args:
      - /home/<you>/Proyectos/themeforge/mcp_server.py
    env:
      QT_QPA_PLATFORM: offscreen
```

Verify the bridge:

```bash
hermes -z "Use the themeforge MCP list_stacks tool; reply with only the count."
# → e.g. 62
```

### 23.5 The Operator skill

The orchestration logic lives in a Hermes skill at
`~/.hermes/skills/themeforge/themeforge-operator/SKILL.md` (it ships with the
Operator setup). It teaches Hermes the workflow (plan → create/continue → build →
QA loop → package), how to assign a **distinct UI/UX Pro Max style+palette per
variant**, when to spawn **parallel subagents** (`delegate_task`), and how to
**learn** (see 23.8). Load it with `-s themeforge-operator`.

### 23.6 Using it — three entry points

**A) Operator tab → NEW project (from scratch).**
Open the **🚀 Operator** tab. Write a brief, pick the number of variants and the
build agent, and hit **🚀 Lanzar misión**. Hermes **creates the project**
(`create_project`) and builds it. A **live web preview** of the project Hermes
builds appears on the right (it auto-loads the newest project when the mission
ends — press **▶ Preview**).

> Example brief: *“Build ONE Envato-ready coffee-shop landing, stack
> astro-tailwind, provider codex, single variant. create_project → run_agent_build
> → run_preflight, then report the path.”*

**B) Gallery / Preview → EXISTING project (continue / automate).**
Select a project in the **Gallery** (or open it and use the **ProjectWindow**
toolbar) and click **🚀 Operator**. A dialog asks what to do; Hermes works **on the
existing project** (it does *not* create a new one) via `run_agent_build` in its
folder, then `run_preflight`. Example task: *“add a pricing section with 3 plans
and pass preflight”*.

**C) Terminal.**
```bash
# interactive (you can watch and stop with Ctrl+C)
hermes -s themeforge-operator
# one-shot
hermes chat -q "Build ONE Envato-ready ... " -s themeforge-operator
```

### 23.7 What a mission does

1. **Plan** — choose stack (`suggest_stack`/`list_stacks`), style/palette per variant.
2. **Create or continue** — `create_project` (new) or work in the existing path.
3. **Build** — `run_agent_build` runs your agent (e.g. Codex) autonomously with a
   detailed prompt (sections + complete demo data + Unsplash/Pixabay images,
   Envato-ready), with autoskills + UI/UX Pro Max applied.
4. **QA loop** — `run_preflight`; if it fails, build again with the issues (max 3).
5. **Package** — `build_zip` → marketplace ZIP (only the template, no dev tooling).
6. **Report** — path, style, QA result, zip. Multiple variants run as parallel
   `delegate_task` subagents.

### 23.8 How Hermes learns from a project

- **Per-project context (auto):** Hermes auto-loads the project's `AGENTS.md` /
  `.hermes.md` / `CLAUDE.md` when working in its directory — so it inherits prior
  decisions and conventions.
- **Per-project notes:** the skill has Hermes maintain a **`.hermes.md`** in each
  project (decisions, TODOs, gotchas, your preferences) — auto-loaded next time
  (highest priority), so the project “teaches” it across sessions.
- **Cross-project memory:** Hermes's `memory` tool (`~/.hermes/memories/MEMORY.md`)
  captures reusable lessons; `session_search` recalls past work.
- **Procedural skills:** after non-trivial workflows, Hermes saves reusable skills
  via `skill_manage` (e.g. “build-pricing-section-astro”).

### 23.9 Figma integration (related)

ThemeForge can build **from a Figma design**: in *New project → Recreate from
reference* choose **“Figma (URL del frame)”** and paste the frame link
(right-click in Figma → *Copy link to selection*). The build agent reads it via
the **figma-context MCP** (read-only Figma→code, MIT). Set your Figma token at
*Settings → 🔑 AI credentials → Figma* (`FIGMA_API_KEY`, a Figma personal access
token, scope: read). See §19 (MCP servers).

### 23.10 Troubleshooting

- **No Operator tab / buttons:** Hermes isn't installed (it's optional). Install it
  (23.2) and restart ThemeForge.
- **`list_stacks` count not returned / MCP errors:** the `themeforge` MCP isn't
  registered or `python3` lacks deps. Check `~/.hermes/config.yaml` (23.4) and that
  `python3 mcp_server.py` runs.
- **Build fails immediately:** the build agent (e.g. `codex`) isn't authenticated.
  Check `hermes`'s provider key and the agent CLI auth.
- **Preview empty:** the dev server didn't start (missing deps) or the stack has no
  preview profile. Run the project's install (`npm install`, etc.) first.

---

## 24. Credits and third-party licenses

ThemeForge is licensed under **GPL v3** (forced by the PyQt6
dependency which is GPL v3 or commercial). See `LICENSE`.

### Direct integrations

| Component | License | How it's used |
|---|---|---|
| [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) | GPL v3 (or commercial) | The whole GUI. |
| [`@xterm/xterm`](https://xtermjs.org/) | MIT | Embedded terminal in `terminal/`. Bundled via npm. |
| [`@xterm/addon-fit`](https://xtermjs.org/) | MIT | Resize support for the terminal. |
| [`node-pty`](https://github.com/microsoft/node-pty) | MIT | PTY backend for the terminal. |
| [`ws`](https://github.com/websockets/ws) | MIT | WebSocket transport between the terminal frontend and `node-pty`. |
| [`autoskills`](https://github.com/midudev/autoskills) (midudev) | **CC BY-NC 4.0** | Invoked via `npx autoskills -a <provider>` to install skills declared by each stack. **Non-commercial license** — if you ship a commercial build of ThemeForge, the autoskills checkbox must be off-by-default or replaced with a permissive alternative. |
| [`pixel-office-openclaw`](https://github.com/neomatrix25/pixel-office-openclaw) (neomatrix25) | MIT | Visualizer dashboard. Fork at `pcreativedev/pixel-office-openclaw` adds the Claude Code session reader. |

### Invoked-as-subprocess

These are external CLIs ThemeForge invokes; they're not bundled.

| Tool | License |
|---|---|
| [Claude Code CLI](https://github.com/anthropics/claude-code) (Anthropic) | Apache 2.0 |
| [Codex CLI](https://github.com/openai/codex) (OpenAI) | Apache 2.0 |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli) (Google) | Apache 2.0 |
| [OpenCode CLI](https://github.com/opencode-ai/opencode) | Apache 2.0 |
| [GitHub CLI (`gh`)](https://github.com/cli/cli) | MIT |

### Referenced skill packages (not redistributed — invoked by name)

- `anthropics/skills/frontend-design` (Anthropic).
- `vercel/skills/nextjs-best-practices` (Vercel).
- `wordpress/skills/block-theme-development` (WordPress).
- `shopify/skills/theme-development` (Shopify).

### Acknowledgements

- **midudev** for [autoskills](https://github.com/midudev/autoskills)
  and the broader Spanish-speaking dev community he educates.
- **neomatrix25** for [pixel-office-openclaw](https://github.com/neomatrix25/pixel-office-openclaw),
  the foundation of the visualizer.
- The Qt team for PyQt6 and PySide6.
- Anthropic, OpenAI, Google and the open-source AI community for the
  CLIs that make this workflow possible.

---

## Appendix A — Directory layout of a generated project

After ThemeForge creates a project, the on-disk layout looks like
this (for a Next.js + licensing example):

```
~/Proyectos/themes/my-template/
├── .git/
├── .gitignore
├── CLAUDE.md                    # injected by ThemeForge
├── README.md                    # from the stack scaffolder
├── context/                     # market/competitors/requirements MDs
│   ├── REQUIREMENTS-THEMEFOREST.md
│   ├── MARKET-RESEARCH.md       # private if you have ~/.config/.../context-private/
│   └── …
├── public/
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   └── verify-license/route.ts   # licensing scaffold
│   │   ├── setup/
│   │   │   └── page.tsx                  # licensing wizard
│   │   └── …
│   └── store/
│       └── setup-store.ts                # Zustand store for setup
├── middleware.ts                # redirects to /setup if not completed
├── package.json
└── tsconfig.json
```

For multi-stack mono-repos (e.g. Laravel + Flutter), each stack lives
in its own subdirectory and the sub-project dropdown lets you switch
the active preview between them.

---

## Appendix B — Reporting issues

If you hit a bug:

1. Check §17 (Troubleshooting) first.
2. Run ThemeForge from a terminal so you can capture stack traces:
   `python3 ~/Proyectos/themeforge/themeforge.py`.
3. Report at the repo's Issues tracker including:
   - Distro + kernel (`uname -a`).
   - Python version, PyQt6 version (`pip show pyqt6`).
   - Node version.
   - Stack you were creating.
   - Mode (scratch / recreate / adopt / existing).
   - The traceback.
