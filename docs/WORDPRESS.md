# WordPress integration in Pcreative Studio

Pcreative Studio ships **five WordPress theme stacks** plus one plugin stack,
each one bootstrapping a dev WordPress + MariaDB environment in Docker
with the right builder, plugin set, and MCPs preinstalled, plus a thick
per-stack `CLAUDE.md` context block so the AI agent can build at a
professional level out of the gate.

> All third-party WordPress tooling is downloaded from official sources
> (WordPress.org for free items, the project's own GitHub release for
> Novamira free, the user's `~/.config/themeforge/wp_packs.json` for
> premium). **Nothing is bundled in this repository.** See
> [`NOTICE.md`](../NOTICE.md) and [`TRADEMARKS.md`](../TRADEMARKS.md) for
> the legal layer.

## 1. The six stacks

| Stack | Use case | Parent / base | Pack of plugins (auto-installed free) |
|---|---|---|---|
| `wordpress-block` | FSE — block theme native, no external builder. Cleanest for ThemeForest "WordPress Themes" category. | standalone | GenerateBlocks · Spectra · ACF (free) · Pods · Royal MCP · Novamira (free) |
| `wordpress-bricks` | Bricks Builder child theme (premium parent) | Bricks (requires license, declared in `wp_packs.json`) | GreenShift · ACF · Pods · Royal MCP · Novamira (free) |
| `wordpress-elementor` | Hello Elementor child theme | Hello Elementor (free, auto-installed) | Elementor (free) · Essential Addons Lite · ACF · Pods · Royal MCP · Novamira (free) |
| `wordpress-divi` | Divi child theme (premium parent) | Divi (requires license, declared in `wp_packs.json`) | ACF · Pods · Royal MCP · Novamira (free) |
| `wordpress-breakdance` | Breakdance plugin over Kadence base theme | Kadence (free) + Breakdance free plugin | Kadence · Breakdance (free) · ACF · Pods · Royal MCP · Novamira (free) |
| `wordpress-plugin` | WordPress plugin scaffold (PHP 8.2 + PSR-4 + Composer + optional Vite/Vue admin UI) | — | (no Docker WordPress) |

### When to use which

- **First Envato listing, no builder dependency for the buyer →
  `wordpress-block`** (FSE). Cleanest, fastest, no buyer license cost.
- **You're already in the Bricks / Elementor / Divi / Breakdance world →
  pick the matching builder stack.** The buyer needs the builder license.
- **You're building a plugin, not a theme → `wordpress-plugin`.**

### Theme vs builder economics

| Path | Buyer needs to pay | Your price range | Volume on Envato |
|---|---|---|---|
| `wordpress-block` (FSE) | nothing | $39–69 | Mid (best sellers $$$/site) |
| `wordpress-elementor` | Elementor Pro (~$59/yr) | $59–89 | **Highest** (Elementor is ~43% of the market) |
| `wordpress-bricks` | Bricks license (~$79–199 one-time) | $69–129 | Growing fast in 2026 |
| `wordpress-divi` | Divi subscription (~$89/yr or $249 lifetime) | $59–99 | Steady |
| `wordpress-breakdance` | Breakdance Pro (~$149/yr) | $59–99 | Growing |

## 2. What happens at create time

### Common to every WordPress theme stack

Pcreative Studio invokes `wp_provisioner.py`, which:

1. **Starts a dedicated Docker network** (`themeforge-wpnet-<slug>`) so
   each project is isolated.
2. **Spins up MariaDB** (`themeforge-wpdb-<slug>`) with a random password
   on a persisted volume.
3. **Spins up WordPress** (`themeforge-wp-<slug>`) on a free local port
   (`127.0.0.1:809x`), mounted as a writable volume `themeforge-wp-<slug>-html`,
   plus your project folder bind-mounted to
   `wp-content/themes/<slug>` (or `wp-content/plugins/<slug>` for the
   plugin stack).
4. **Installs WordPress** via `wp-cli` (user `admin` / password `admin`),
   sets pretty permalinks (`/%postname%/`), installs and activates the
   official **Automattic `wordpress-mcp` plugin**, generates an
   **Application Password** for the MCP bridge.
5. **Installs the `themeforge-autologin` mu-plugin**: when you visit the
   preview URL from `localhost`, you land in the WordPress dashboard
   already logged in as admin. Skipped for REST / XML-RPC / cron / AJAX
   / CLI requests so it doesn't break MCPs or wp-cron.
6. **Installs the free pack** of plugins/themes for the selected stack
   (see table above) via `wp-cli plugin install` and `wp-cli theme
   install`, with sources `WordPress.org` for the slug-based ones and
   `https://github.com/use-novamira/novamira/releases/latest/download/...`
   for Novamira (resolved via the GitHub public API, no auth, AGPL v3).
7. **Installs the premium pack** if `~/.config/themeforge/wp_packs.json`
   has matching `zip:` paths (see §3).
8. **Activates the child theme** (`bricks` / `elementor` / `divi` /
   `breakdance` packs) once the parent theme is in place. The FSE pack
   leaves activation to the agent because the theme starts empty.
9. Writes **`.mcp.json`** with the Automattic WordPress MCP bridge
   wired to the local store and the freshly minted app password.
10. Writes **`WORDPRESS-DEV.md`** (URL, admin credentials, the
    `./wp` wp-cli helper, the active UX pack, where Royal MCP / Novamira
    Pro MCP configs go) and **`WORDPRESS-LEGAL.md`** (per-project legal
    disclaimer — see §10).
11. Adds **`WORDPRESS-DEV.md`**, **`WORDPRESS-LEGAL.md`**, **`/wp`** and
    **`.mcp.json`** to the project's `.gitignore`.

### The `wp` helper

Every WordPress project gets an executable **`./wp`** wrapper that
runs `wp-cli` inside the WordPress container with the right DB env vars
and UID. Use it like the regular CLI:

```bash
./wp plugin list
./wp option get siteurl
./wp theme activate <your-theme-slug>
./wp post create --post_type=page --post_title="About"
```

## 3. The `wp_packs.json` premium-pack file

Pcreative Studio auto-installs every **free** WordPress plugin/theme from its
official source. To extend a stack with **premium** items you have a
license for, declare them in **`~/.config/themeforge/wp_packs.json`**
(this file lives in your `$HOME`, **never** in the repo). The schema
mirrors the five stacks:

```json
{
  "fse": {
    "plugins": [
      { "name": "acf-pro",            "zip": "" },
      { "name": "generateblocks-pro", "zip": "" },
      { "name": "kadence-blocks-pro", "zip": "" },
      { "name": "motion-page",        "zip": "" }
    ]
  },
  "bricks": {
    "theme":  { "name": "bricks", "zip": "" },
    "plugins": [
      { "name": "bricksforge",     "zip": "" },
      { "name": "jetengine",       "zip": "" },
      { "name": "jetsmartfilters", "zip": "" },
      { "name": "motion-page",     "zip": "" },
      { "name": "novamira-pro",    "zip": "" }
    ]
  },
  "elementor": {
    "plugins": [
      { "name": "elementor-pro",                  "zip": "" },
      { "name": "essential-addons-for-elementor", "zip": "" },
      { "name": "jetengine",                      "zip": "" },
      { "name": "motion-page",                    "zip": "" },
      { "name": "novamira-pro",                   "zip": "" }
    ]
  },
  "divi": {
    "theme":  { "name": "Divi", "zip": "" },
    "plugins": [
      { "name": "divi-builder", "zip": "" },
      { "name": "novamira-pro", "zip": "" }
    ]
  },
  "breakdance": {
    "plugins": [
      { "name": "breakdance-pro", "zip": "" },
      { "name": "jetengine",      "zip": "" },
      { "name": "novamira-pro",   "zip": "" }
    ]
  }
}
```

For each entry:

- **`name`** — informational label that appears in the install log.
- **`zip`** — absolute path to a local ZIP **or** an HTTPS URL. Leave
  empty to skip that item. Pcreative Studio passes the value straight to
  `wp-cli plugin install` (or `theme install` for the `theme` key).

The file is created with empty placeholders the first time you launch
a WordPress stack. It is **gitignored by definition** (it never lives
in the repo).

> **Responsibility**: Pcreative Studio does not verify licenses. If you point
> a `zip:` at a copy of a commercial plugin or theme, you must hold a
> valid license for it. The repo neither ships nor links to premium
> ZIPs.

## 4. The MCPs available in WordPress projects

Every WordPress project's `.mcp.json` is generated with the **Automattic
WordPress MCP bridge** preconfigured against the freshly provisioned
store, authenticated via the application password Pcreative Studio created at
provisioning time:

```json
{
  "mcpServers": {
    "wordpress": {
      "command": "npx",
      "args": ["-y", "@automattic/mcp-wordpress-remote@latest"],
      "env": {
        "WP_API_URL": "http://localhost:809x/",
        "WP_API_USERNAME": "admin",
        "WP_API_PASSWORD": "<app-password>",
        "LOG_FILE": "/tmp/wpmcp.log"
      }
    }
  }
}
```

This gives the agent native WordPress control: posts, pages, media,
options, customizer, users.

Two more MCPs are **installed in the WordPress container** but need a
one-step wiring on your side (they use API keys generated inside
`wp-admin`):

- **Royal MCP** (free, auto-installed on every WP stack) — 67
  operations: posts, media, comments, users, **meta of
  ACF / Meta Box / JetEngine / Pods / CPT UI**, and term meta of
  Yoast / Rank Math / AIOSEO. Generate an API key at
  `http://localhost:809x/wp-admin/admin.php?page=royal-mcp` and add an
  entry to `.mcp.json`:

  ```json
  "royal-mcp": {
    "url": "http://localhost:809x/wp-json/royal-mcp/v1/mcp",
    "headers": { "X-Royal-MCP-Key": "YOUR_KEY" }
  }
  ```

- **Novamira (free)** (auto-installed on every WP stack from the
  project's official GitHub releases, AGPL v3) — PHP execution, file
  read/write, database queries against the WordPress container. The
  **Pro** version, if you own a license and declared it in
  `wp_packs.json`, adds **native knowledge of Elementor atomic widgets,
  Bricks templates, Divi layouts, ACF/JetEngine/Meta Box/ACPT/Pods**.
  Copy the exact MCP config from the plugin's settings page.

## 5. What the AI knows (the `CLAUDE.md` brain)

Each WordPress stack injects a per-stack context block
(`_WP_BUILDER_CONTEXT` in `themeforge.py`) plus a common WordPress dev
environment block that lists:

- The container URL, admin credentials, and the autologin behaviour.
- The active UX pack and which plugins/themes were installed (free
  successes, premium successes, premium missing).
- The three MCPs (Automattic bridge active, Royal MCP installed
  needs API key, Novamira installed — Pro optional).
- The autoskills installed (`wordpress/agent-skills/wp-block-themes`,
  `wp-block-development`, `wp-plugin-development`, `wp-rest-api`,
  `wp-performance`, `wp-project-triage`, `wp-wpcli-and-ops`, etc.).

Per-stack context (`_WP_BUILDER_CONTEXT`):

- **`wordpress-block`**: FSE architecture (theme.json design tokens,
  `templates/*.html`, `parts/*.html`, `patterns/*.php`), no external
  builder, free plugin list.
- **`wordpress-bricks`**: child theme of Bricks, Templates → Export to
  JSON, Global Classes & Theme Styles export, free vs paid plugins.
- **`wordpress-elementor`**: child theme of Hello Elementor, Templates +
  Site Kits export to JSON, Elementor Pro vs free split, JetEngine /
  Motion.page / Novamira Pro paid.
- **`wordpress-divi`**: child theme of Divi (paid parent), Divi Library
  Export to JSON.
- **`wordpress-breakdance`**: Kadence base + Breakdance plugin
  (render engine), global / headers / footers / popups exported to
  JSON.

## 6. Workflow

```bash
# 1) Create the project in Pcreative Studio (pick e.g. "WordPress (Block Theme)").
#    → Pcreative Studio starts MariaDB + WordPress in Docker, installs WP,
#      installs the free pack + Novamira (free), writes WORDPRESS-DEV.md
#      + WORDPRESS-LEGAL.md + .mcp.json, drops the autologin mu-plugin.

# 2) Open the project. The preview tab points at http://localhost:809x
#    and you land in /wp-admin/ already logged in.

# 3) (Optional) Edit wp_packs.json to add premium items you have licenses
#    for and re-provision: python3 -m wp_provisioner provision <slug> <dir> theme <pack>

# 4) Talk to your AI agent (Claude Code / Cursor / Windsurf):
#    · The .mcp.json wires the Automattic WordPress MCP bridge live.
#    · The CLAUDE.md context tells it which builder is active, which
#      plugins are installed, and where the template files live.
#    · The skills are already in .claude/skills/.

# 5) The ./wp helper runs wp-cli inside the container
./wp theme list
./wp plugin status
./wp post create --post_type=page --post_title="Home"

# 6) Stop / restart the container without losing data
python3 -m wp_provisioner down <slug>            # stop, keep volume
python3 -m wp_provisioner down <slug> --volume   # nuke everything
```

## 7. Lifecycle controls in the preview tab

The ProjectWindow's **Start / Stop** buttons for WordPress projects are
non-destructive (since v1.3.3):

- **Start** — `docker start` of the container if it was stopped. Loads
  the URL in the embedded preview.
- **Stop** — `docker stop`. Volumes are intact, restart with Start
  brings WordPress back exactly as you left it.

`down --volume` is the only path that wipes data.

## 8. References from the Market tab

The **Market** tab (since v1.4.0) ships several AI analyses that
explicitly cover the WordPress builder market — including which builder
is winning what niche, the relative shares of Bricks / Elementor /
Divi / Breakdance / FSE, and gap analysis. Use that before committing
to a stack for a brand-new product idea.

## 9. The `wordpress-plugin` stack

Different beast — no Docker WordPress provisioned. The scaffold creates
a PHP 8.2+ plugin skeleton with PSR-4 (`composer.json`), an optional
Vite + Vue admin UI (`package.json`), tests dirs, and the `WP-DEMO-
INSTALLER.md` spec for the demo importer. The AI agent receives the
`wp-plugin-development` skill and the `WP-DEMO-INSTALLER.md` brief.

## 10. Legal & attribution

Every WordPress project gets a generated **`WORDPRESS-LEGAL.md`**
explaining:

- **Free items** auto-installed from WordPress.org or the official
  Novamira GitHub release (all GPL or AGPL).
- **Premium items** the user declared in `wp_packs.json` (responsibility
  is on the user — must hold a valid license).
- **Trademarks** of Bricks, Elementor, Divi, Breakdance, JetEngine, ACF,
  WooCommerce, WordPress, Motion.page, etc. — used here only to identify
  the products they refer to.
- **Publishing rules**: the theme/plugin you write must be GPL-compatible
  (WordPress requires it); do not bundle commercial plugins/themes inside
  your sale ZIP (ThemeForest / Theme Store also forbid it).

For the repo-level legal layer, see
[`NOTICE.md`](../NOTICE.md) (WordPress integration packs section) and
[`TRADEMARKS.md`](../TRADEMARKS.md) (WordPress ecosystem section).

## 11. Further reading

Official references the context block distils:

- <https://developer.wordpress.org/themes/block-themes/> — FSE / Block
  themes.
- <https://developer.wordpress.org/themes/global-settings-and-styles/>
  — theme.json reference.
- <https://developer.wordpress.org/news/2026/02/from-abilities-to-ai-agents-introducing-the-wordpress-mcp-adapter/>
  — the WordPress MCP adapter (Abilities API + WP 6.9 core).
- <https://github.com/Automattic/wordpress-mcp> — the MCP plugin
  Pcreative Studio installs.
- <https://wordpress.org/plugins/royal-mcp/> — Royal MCP.
- <https://github.com/use-novamira/novamira> — Novamira free.
- Bricks: <https://bricksbuilder.io/>
- Elementor: <https://elementor.com/>
- Divi: <https://www.elegantthemes.com/gallery/divi/>
- Breakdance: <https://breakdance.com/>
