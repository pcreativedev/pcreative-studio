# NOTICE — third-party software

ThemeForge ships under **GPL v3** (see `LICENSE`). It depends on,
embeds, or invokes the following third-party components. This NOTICE
file aggregates their licenses and attribution requirements for the
convenience of distributors and users.

## Embedded (shipped as part of this repo or auto-installed)

### Embedded terminal — `terminal/`

These are listed as dependencies in `terminal/package.json` and are
installed under `terminal/node_modules/` when you run `npm install`:

| Package | License | Project URL |
|---|---|---|
| `@xterm/xterm` | MIT | <https://xtermjs.org/> |
| `@xterm/addon-fit` | MIT | <https://xtermjs.org/> |
| `node-pty` | MIT | <https://github.com/microsoft/node-pty> |
| `ws` | MIT | <https://github.com/websockets/ws> |

The MIT license is included in each package's `LICENSE` file under
`terminal/node_modules/<package>/LICENSE`.

### Pixel Office visualizer

ThemeForge auto-installs (with user consent) a Node application that
shows AI agent sessions as pixel-art avatars on a virtual office. The
visualizer is fetched from:

- **Upstream**: <https://github.com/neomatrix25/pixel-office-openclaw>
  — by **neomatrix25**, MIT.
- **Fork used by ThemeForge**:
  <https://github.com/pcreativedev/pixel-office-openclaw> — same code +
  two commits adding a Claude Code session reader and same-origin
  auto-connect. Also MIT.

Neither the upstream nor the fork is bundled in this repository. They
are cloned at install time into
`~/.local/share/themeforge/pixel-office-openclaw/` from the user's
machine.

## Invoked as external subprocesses (NOT bundled)

ThemeForge does not bundle these tools; it only spawns them as child
processes when the user selects the corresponding provider. The user
is expected to install them through their distro's package manager or
each project's official channel.

| Tool | License | Project URL | Used as |
|---|---|---|---|
| Claude Code CLI (Anthropic) | Apache 2.0 | <https://github.com/anthropics/claude-code> | AI agent (`claude`) |
| Codex CLI (OpenAI) | Apache 2.0 | <https://github.com/openai/codex> | AI agent (`codex`) |
| Gemini CLI (Google) | Apache 2.0 | <https://github.com/google-gemini/gemini-cli> | AI agent (`gemini`) |
| OpenCode CLI | MIT | <https://github.com/sst/opencode> | AI agent (`opencode`, npm pkg `opencode-ai`) |
| UI UX Pro Max | MIT | <https://github.com/nextlevelbuilder/ui-ux-pro-max-skill> | Optional design skill (`uipro-cli init --ai <agent>`) for 161 reasoning rules + 67 UI styles + 161 paletas. Invoked when the "uipro" checkbox is enabled in the project form. |
| **Lucide icons** | ISC | <https://github.com/lucide-icons/lucide> | 38 SVG icons bundled in `assets/icons/lucide/` and used for the main-window tabs and Settings widgets. SVGs use `currentColor` so they re-tint to the active theme's accent. ISC is functionally equivalent to MIT — full attribution preserved in the SVG files. |
| W3C DTCG spec | (community) | <https://www.designtokens.org/tr/drafts/format/> | Theme JSON format reference for the Figma import path. ThemeForge parses tokens following the DTCG v2025.10 spec (`$type` + `$value` with `$`-prefixed metadata). |
| Tokens Studio for Figma | (referenced, not bundled) | <https://docs.tokens.studio/> | Recommended Figma plugin for exporting design tokens as DTCG JSON to feed ThemeForge's Figma import dialog. Not redistributed. |
| **MCP SDK** (`python-mcp`) | MIT | <https://github.com/modelcontextprotocol/python-sdk> | Anthropic's official MCP Python SDK. Used by `mcp_server.py` to expose ThemeForge actions (list_stacks / estimate_cost / run_preflight / build_zip / suggest_stack / …) as tools callable from any MCP client. |

## MCP catalog (referenced, not bundled)

ThemeForge can pre-configure a curated set of community MCP servers
per scaffolded project (writes `.mcp.json` in the project root). The
upstream code is **never** bundled — your AI client (Claude Code,
Cursor, Windsurf, OpenCode) downloads each MCP on demand via `npx`,
`uvx`, or `docker`. We just generate the config. All licenses are
permissive and verified at curation time (see `mcp_catalog.py`).

| MCP | License | Upstream |
|---|---|---|
| Filesystem (mcp official) | MIT | <https://github.com/modelcontextprotocol/servers> |
| Fetch (mcp official) | MIT | <https://github.com/modelcontextprotocol/servers-archived/tree/main/src/fetch> |
| Memory (mcp official) | MIT | <https://github.com/modelcontextprotocol/servers-archived/tree/main/src/memory> |
| GitHub (official) | MIT | <https://github.com/github/github-mcp-server> |
| Playwright (Microsoft official) | Apache-2.0 | <https://github.com/microsoft/playwright-mcp> |
| Chrome DevTools (Google official) | Apache-2.0 | <https://github.com/ChromeDevTools/chrome-devtools-mcp> |
| Figma Context | MIT | <https://github.com/GLips/Figma-Context-MCP> |
| Shopify Dev (official) | (per Shopify open-source standard; verify upstream) | <https://github.com/Shopify/dev-mcp> |
| Postgres (crystaldba) | MIT | <https://github.com/crystaldba/postgres-mcp> |
| Browser MCP | Apache-2.0 | <https://github.com/browsermcp/mcp> |

Discovery / curation reference: [`punkpeye/awesome-mcp-servers`](https://github.com/punkpeye/awesome-mcp-servers)
(directory of 1500+ community servers maintained by Frank Fiegel). All
12 entries in our curated catalog can be inspected (and the catalog
extended) in `mcp_catalog.py`.
| GitHub CLI (`gh`) | MIT | <https://github.com/cli/cli> | Repo create / push from the ProjectWindow |
| `paru` | GPL v3 | <https://github.com/Morganamilo/paru> | AUR helper hint in docs |

## WordPress integration packs

When the user picks one of the WordPress stacks (`wordpress-block`,
`wordpress-bricks`, `wordpress-elementor`, `wordpress-divi`,
`wordpress-breakdance`), ThemeForge provisions a development WordPress +
MariaDB environment in Docker and **auto-installs** the free plugins/themes
listed below. None of this code is bundled in this repository — the
WordPress container fetches each item from its **official source** via
`wp-cli` at provisioning time.

### Auto-installed (FREE, public sources)

All items are GPL (or AGPL for Novamira) and freely downloadable.
ThemeForge calls `wp-cli` exactly the same way a user would by clicking
*Plugins → Add new* in `wp-admin`.

| Item | Source | License | Used by stack(s) |
|---|---|---|---|
| Hello Elementor (theme) | WordPress.org | GPL v2+ | `wordpress-elementor` (parent) |
| Kadence (theme) | WordPress.org | GPL v2+ | `wordpress-breakdance` (base) |
| Elementor (plugin, free) | WordPress.org | GPL v3 | `wordpress-elementor` |
| Essential Addons for Elementor — Lite | WordPress.org | GPL v3 | `wordpress-elementor` |
| Breakdance (plugin, free) | WordPress.org | GPL v3 | `wordpress-breakdance` |
| GenerateBlocks | WordPress.org | GPL v2+ | `wordpress-block` |
| Ultimate Addons for Gutenberg (Spectra) | WordPress.org | GPL v2+ | `wordpress-block` |
| GreenShift | WordPress.org | GPL v2+ | `wordpress-bricks` |
| Advanced Custom Fields (free) | WordPress.org | GPL v2+ | all WP stacks |
| Pods | WordPress.org | GPL v2+ | all WP stacks |
| Royal MCP | WordPress.org | GPL v2+ | all WP stacks |
| Novamira (free) | <https://github.com/use-novamira/novamira> (official releases) | **AGPL v3** | all WP stacks |
| WordPress MCP plugin (Automattic) | <https://github.com/Automattic/wordpress-mcp> | GPL v2+ | all WP stacks |

For Novamira, ThemeForge resolves the latest release asset URL via the
GitHub public API and passes it to `wp-cli plugin install`. We do not
modify Novamira or run it as a service on our infrastructure, so AGPL
network-use obligations do not attach to ThemeForge.

### Premium — referenced by name only, NEVER bundled

The following premium products are referenced in scaffold notes,
README templates, and the (gitignored) `~/.config/themeforge/wp_packs.json`
schema. **ThemeForge never bundles, distributes, or links to copies of
these products.** Users who want to auto-install one of them must
declare a path or URL to a copy they have legitimately licensed:

| Product | Holder | Where it appears |
|---|---|---|
| Bricks Builder | Bricks Builder GmbH | `wordpress-bricks` (parent theme placeholder) |
| Bricksforge | Bricksforge GmbH | `wordpress-bricks` (plugin placeholder) |
| Elementor Pro | Elementor Ltd. | `wordpress-elementor` (plugin placeholder) |
| Essential Addons for Elementor — Pro | WPDeveloper | `wordpress-elementor` (plugin placeholder) |
| Divi (theme) / Divi Builder | Elegant Themes Inc. | `wordpress-divi` (parent + plugin placeholder) |
| Breakdance Pro | SoftAndy Inc. | `wordpress-breakdance` (plugin placeholder) |
| JetEngine, JetSmartFilters | Crocoblock | `wordpress-bricks`, `wordpress-elementor`, `wordpress-breakdance` (plugin placeholder) |
| Motion.page | Motion.page | `wordpress-bricks`, `wordpress-elementor` (plugin placeholder) |
| Novamira Pro | use-novamira | All WP stacks (plugin placeholder) |
| ACF Pro | WP Engine / Delicious Brains | `wordpress-block` (plugin placeholder) |
| GenerateBlocks Pro | Edge22 | `wordpress-block` (plugin placeholder) |
| Kadence Blocks Pro | StellarWP | `wordpress-block` (plugin placeholder) |

Users are responsible for ensuring they hold a valid license for any
product they declare in `wp_packs.json`. ThemeForge does not verify
licenses and does not assume liability for unauthorized use of premium
plugins.

See [`TRADEMARKS.md`](TRADEMARKS.md) for the full trademark notice and
the legal basis on which third-party names are used.

## Shopify integration

When the user picks one of the Shopify stacks (`shopify-liquid`,
`shopify-hydrogen`), ThemeForge bootstraps the project by invoking
official Shopify CLI/scaffolds that **download from Shopify's official
sources at scaffold time**. None of the following is bundled in this
repository.

| Item | Source / scaffolder | License | Used by |
|---|---|---|---|
| Shopify CLI (`@shopify/cli`) | <https://github.com/Shopify/cli> | MIT | `shopify-liquid` (theme init) |
| Dawn theme (Shopify's reference OS 2.0 theme) | <https://github.com/Shopify/dawn> | MIT | `shopify-liquid` (cloned as the project starting point — MIT attribution preserved in the cloned repo) |
| Hydrogen template (`@shopify/create-hydrogen`) | <https://github.com/Shopify/hydrogen> | MIT | `shopify-hydrogen` |
| Shopify Dev MCP server (`@shopify/dev-mcp`) | <https://github.com/Shopify/dev-mcp> | MIT | both Shopify stacks (Liquid + Hydrogen). Includes Polaris design system. |
| Storefront MCP (hosted) | <https://shopify.dev/docs/apps/build/storefront-mcp> | Hosted by Shopify on every store, free, zero-auth | both Shopify stacks (the `.mcp.json` points to the user's store URL via HTTP) |
| Storefront UCP MCP (hosted) | <https://shopify.dev/docs/apps/build/storefront-mcp> | Hosted by Shopify on every store, free, zero-auth | both Shopify stacks |
| Polaris design system | <https://github.com/Shopify/polaris> | MIT | Available through `@shopify/dev-mcp`. Also referenced by name in the `shopify-polaris-app` scaffold (the user's app installs `@shopify/polaris` / `@shopify/polaris-icons` / `@shopify/app-bridge-react` / `@shopify/shopify-app-remix` directly at `npm install` time). |
| Shopify create-app template (`@shopify/create-app`) | <https://github.com/Shopify/shopify-app-template-remix> | MIT | `shopify-polaris-app` (scaffold) |
| Liquid Prettier plugin (`@shopify/prettier-plugin-liquid`) | <https://github.com/Shopify/theme-tools/tree/main/packages/prettier-plugin-liquid> | MIT | `shopify-liquid` (added to `package.json` at scaffold time; npm installs it from npmjs.com when the user runs `npm install`) |
| Prettier | <https://github.com/prettier/prettier> | MIT | `shopify-liquid` (added to `package.json`) |
| Shopify Lighthouse CI action | <https://github.com/Shopify/lighthouse-ci-action> | MIT | `shopify-liquid` (referenced in `.github/workflows/lighthouse-ci.yml`; only run if the user opts in by setting `SHOPIFY_AUTH_TOKEN` / `SHOPIFY_STORE` / `SHOPIFY_STORE_PWD` secrets) |

### About Dawn as a starting point

`shopify-liquid` invokes `shopify theme init --clone-url https://github.com/Shopify/dawn`,
which performs a `git clone` of the official Dawn repository into the
new project directory. Dawn is licensed MIT by Shopify and is explicitly
designed as a starting point for new themes. The cloned project
retains Dawn's `LICENSE.md` and copyright headers, as MIT requires. AI
agents using ThemeForge are instructed (via the CLAUDE.md) to
**personalise and extend** Dawn — not to repackage it as-is.

## Referenced by name (NOT redistributed)

When the `autoskills` checkbox is enabled and the AI provider supports
it (Claude or Codex), ThemeForge invokes `npx --yes autoskills -a
<provider>`, which in turn fetches the following skill packages by
name. ThemeForge does NOT bundle, redistribute, or modify these
packages.

| Skill package | Owner |
|---|---|
| `anthropics/skills/frontend-design` | Anthropic |
| `vercel/skills/nextjs-best-practices` | Vercel |
| `wordpress/skills/block-theme-development` | WordPress |
| `shopify/skills/theme-development` | Shopify |

Each skill package is governed by its own license; see the respective
repository for terms.

## ⚠️ autoskills (midudev) — CC BY-NC 4.0

[`autoskills`](https://github.com/midudev/autoskills) by **midudev** is
the tool ThemeForge invokes (via `npx`) to install the skill packages
listed above. It is licensed under **Creative Commons
Attribution-NonCommercial 4.0** (CC BY-NC 4.0).

Implications:

- ✅ Distributing ThemeForge for free under GPL v3 with autoskills as
  an optional dependency is consistent with the autoskills license.
- ⚠️ Selling ThemeForge or shipping it as part of a commercial product
  with the autoskills checkbox enabled by default is a grey area
  under CC BY-NC 4.0. Maintainers of downstream commercial builds
  should either:
  - keep the checkbox OFF by default and document the user opt-in,
  - obtain explicit permission from midudev, or
  - replace autoskills with a permissive alternative.

Attribution to midudev is preserved in:

- `themeforge.py` (tooltip of the autoskills checkbox).
- `docs/USER_GUIDE.md` (§17, "Credits and third-party licenses").
- This NOTICE file.

## Foundational dependencies

| Component | License | Why it matters |
|---|---|---|
| **PyQt6** (Riverbank) | GPL v3 or commercial | Forces ThemeForge as a whole to be distributed under GPL v3 (the LICENSE in this repo). |
| **CPython** ≥ 3.11 | PSF | Runtime. |
| **Qt 6** (The Qt Company) | LGPL v3 / commercial | Under the hood of PyQt6. |
| **Node.js** ≥ 20 | MIT | Runtime for the embedded terminal server and the scaffolding commands of most stacks. |

## Reporting an attribution error

If anything in this file is incorrect, outdated, or missing,
please open an issue against the repository.
