# Shopify integration in Pcreative Studio

Pcreative Studio ships **three Shopify stacks** that scaffold complete, opinionated
projects with the official Shopify tooling, three official MCPs preconfigured,
and a thick `CLAUDE.md` context block so the AI agent works at a professional
level out of the gate.

> All third-party tooling is downloaded from official sources at scaffold
> time — nothing is bundled in this repository. See
> [`NOTICE.md`](../NOTICE.md) and [`TRADEMARKS.md`](../TRADEMARKS.md) for
> the legal layer.

## 1. The three stacks

| Stack | Use case | Scaffolded from | Where to sell |
|---|---|---|---|
| `shopify-liquid` | Online Store 2.0 themes (the mainstream Shopify path) | Clones [Dawn](https://github.com/Shopify/dawn) (MIT) | ThemeForest + Partner builds. **NOT** Shopify Theme Store (Dawn-derived themes are ineligible per the official policy) |
| `shopify-liquid-blank` (since v1.5.0) | Online Store 2.0 themes for the **Shopify Theme Store route** | Scaffolds the minimal valid OS 2.0 structure from scratch (no Dawn / no Horizon) | **Shopify Theme Store** (eligible) + ThemeForest |
| `shopify-hydrogen` | Headless storefronts (Remix + React 19 + Oxygen) | `@shopify/create-hydrogen` (MIT) | ThemeForest "Hydrogen" category + Partner channel |
| `shopify-polaris-app` | Embedded Admin apps (Polaris + App Bridge + Remix) | `@shopify/create-app --template remix` (MIT) | Shopify App Store + Custom apps |
| `shopify-functions` (since v1.5.0) | Custom server-side logic — discounts, payment/delivery customization, cart validations, fulfillment constraints. Compiled to Wasm, ≤5 ms runtime budget. | `@shopify/create-app` + Rust function extension | Shopify App Store + Custom apps. High margin, $19-99/mo recurring typical. |
| `shopify-storefront-webcomponents` (since v1.5.0) | Embedded commerce in non-Shopify sites (blogs, landing pages, WordPress, Webflow, Framer). Cart + payment + fulfillment stay on Shopify; your site is the storefront. | Vite + Shopify Storefront Web Components from CDN | ThemeForest HTML Templates / Shopify Themes — $19-49 high volume |
| `shopify-checkout-extension` (since v1.5.0) | Custom UI inside the hosted Shopify checkout (banners, surveys, upsells, loyalty). **Shopify Plus only.** | `@shopify/create-app` + checkout UI extension | Custom enterprise / Plus agencies. $50-500/mo recurring. |

### When to use which

- **Most projects → `shopify-liquid`.** OS 2.0 covers 80%+ of real-world
  store needs and ships fastest (3–8 weeks for a serious theme).
- **Catalog > 500 SKUs, multi-market, or you need pixel-perfect non-Liquid
  UX → `shopify-hydrogen`** (12–20 weeks build, higher ticket).
- **You're building an app for the Shopify Admin, not a theme →
  `shopify-polaris-app`.**

### Theme Store vs ThemeForest

If your target is the **Shopify Theme Store** (the official curated
marketplace), you **cannot** use `shopify-liquid` as-is: themes derived
from Dawn or Horizon are auto-rejected. You'd need to rebuild from the
empty OS 2.0 structure documented in `CLAUDE.md`. For ThemeForest, where
Dawn-as-base is standard practice, the `shopify-liquid` stack is the
fast path. The `CLAUDE.md` context warns the agent about this explicitly.

## 2. What happens at create time

### `shopify-liquid`

Pcreative Studio runs this pipeline:

1. `npx --yes @shopify/cli@latest theme init . --clone-url https://github.com/Shopify/dawn`
2. Writes **`package.json`** with `prettier` + `@shopify/prettier-plugin-liquid`
   and scripts: `dev`, `check`, `format`, `format:check`, `package`.
3. Writes **`.prettierrc.json`** activating the Liquid plugin.
4. Writes **`.theme-check.yml`** in strict mode (16 KB JS cap from the
   Theme Store budget, parser-blocking checks, deprecated filters,
   `TemplateLength` ≤ 600, etc.).
5. Writes **`.github/workflows/lighthouse-ci.yml`** using the official
   `shopify/lighthouse-ci-action@v1`. Gated by three optional repo
   secrets: `SHOPIFY_AUTH_TOKEN`, `SHOPIFY_STORE`, `SHOPIFY_STORE_PWD`.
6. Writes **`.mcp.json`** with three official Shopify MCPs (see §3).
7. Writes **`README-MCP.md`** with the Shopify CLI cheat sheet.
8. Injects **~10.9 KB of Shopify context** into the project's `CLAUDE.md`.

### `shopify-hydrogen`

1. `npx --yes @shopify/create-hydrogen@latest . --quickstart --no-install`
2. Writes **`.mcp.json`** with the same three Shopify MCPs.
3. Writes **`README-HYDROGEN.md`** with Hydrogen workflow + Oxygen deploy.
4. Injects ~2.9 KB of Hydrogen-specific context into `CLAUDE.md`.

### `shopify-polaris-app`

1. `npx --yes @shopify/create-app@latest --template remix --name <slug> --no-install`
2. Writes **`.mcp.json`** with `shopify-dev` (which includes Polaris).
3. Writes **`README-APP.md`** with stack, commands, extension types,
   distribution channels.
4. Injects ~2.7 KB of app-specific context into `CLAUDE.md`.

## 3. The three official MCPs (wired into every Shopify project)

| MCP | Transport | Auth | What it gives the agent |
|---|---|---|---|
| `shopify-dev` | STDIO (`npx @shopify/dev-mcp@latest`) | none | GraphQL schemas for Admin / Storefront / Checkout APIs, Liquid types, section/block schemas, and the **Polaris** design system for embedded apps. |
| `shopify-storefront` | HTTP (zero-auth) | none | Cart, policies, FAQ for the store URL. Tools: `get_cart`, `update_cart`, `search_shop_policies_and_faqs`. |
| `shopify-storefront-catalog` | HTTP (UCP, zero-auth) | none | Catalog with **natural-language product search**. Tools: `search_catalog`, `lookup_catalog`, `get_product`. |
| `shopify-customer-account` (catalog entry, **NOT auto-wired**) | HTTP | **OAuth 2.0 with PKCE** | Order tracking, returns, customer info. ONLY works with the store's **custom domain** (`.myshopify.com` returns 404). Requires **New Customer Accounts** enabled. Discovery: `https://${shopDomain}/.well-known/openid-configuration`. Configure once you've implemented the OAuth flow in your client. |

### What's NOT a separate MCP

- **GraphQL Storefront API queries** — handled by `shopify-dev` MCP
  (schema introspection + write queries). No separate "Storefront API
  MCP" exists.
- **Admin REST/GraphQL queries** — same, handled by `shopify-dev`.
- **Polaris design system** — bundled inside `shopify-dev`.

The HTTP MCPs are per-store endpoints. **Replace `YOUR-SHOP`** in
`.mcp.json` with your store subdomain (just `your-shop`, not the full
`.myshopify.com`).

```json
{
  "mcpServers": {
    "shopify-dev": {
      "command": "npx",
      "args": ["-y", "@shopify/dev-mcp@latest"]
    },
    "shopify-storefront": {
      "type": "http",
      "url": "https://YOUR-SHOP.myshopify.com/api/mcp"
    },
    "shopify-storefront-catalog": {
      "type": "http",
      "url": "https://YOUR-SHOP.myshopify.com/api/ucp/mcp"
    }
  }
}
```

## 4. What the AI knows (the `CLAUDE.md` brain)

Each stack injects a per-stack context block (`_SHOPIFY_BUILDER_CONTEXT`
in `themeforge.py`):

### `shopify-liquid` context (~10.9 KB)

- **Architecture OS 2.0**: complete layout of `config/`, `layout/theme.liquid`,
  `sections/*.liquid` with `{% schema %}` (settings, blocks with `@app`,
  `max_blocks` up to 50, presets, `enabled_on`/`disabled_on`),
  `sections/*.json` (section groups: header, footer, aside, up to 25
  sections each), `blocks/*.liquid` (theme blocks reusable across sections),
  `templates/*.json` (mandatory templates for Theme Store: 404, article,
  blog, cart, collection, customers/*, gift_card, index, page, password,
  product, search), `snippets/`, `locales/` (i18n is mandatory),
  `assets/` (no Sass, no jQuery / React / Vue / Angular).
- **Official performance budget**: Lighthouse mobile **60+ minimum**
  (top themes ship 90+), **accessibility 90+ mandatory**, **JS bundle 16 KB
  minified maximum**, max 2 preload hints per template, `defer`/`async`
  scripts, IIFE pattern, system fonts preferred.
- **18 mandatory Theme Store features**: Sections Everywhere, faceted
  search, gift cards, image focal points, country/language selection,
  multi-level menus, newsletter, pickup availability, product
  recommendations, rich media (3D, video), predictive search, selling
  plans, Shop Pay Installments, unit pricing, variant images, Follow
  on Shop, etc.
- **11 official developer tools**: Shopify CLI (with the full subcommand
  list), Theme Check (linter, configured via `.theme-check.yml`), the
  Shopify Liquid VS Code extension, the Liquid Prettier plugin, the
  Shopify Theme Inspector Chrome extension, Lighthouse CI GitHub Action,
  Shopify GitHub Integration (bidirectional sync), Theme Access App
  (CI/CD without Partner login), Development Stores, LiquidDoc, and the
  Admin Theme Editor.
- **Conversion patterns** that ship in top-selling themes: cart drawer,
  quick add, predictive search custom, sticky add-to-cart bar, variant
  swatches via metafields, recently viewed (localStorage), trust badges,
  reviews placeholders, upsells in cart drawer.
- **Canonical copy-paste examples**: `templates/index.json` with sections
  and ordered blocks; `sections/hero-banner.liquid` with a full
  `{% schema %}` (settings, blocks including `@app`, `max_blocks`,
  presets, `enabled_on`); `config/settings_schema.json` excerpt with
  `color_scheme_group`, `font_picker`, `range`.
- **Critical warning**: Themes derived from Dawn or Horizon are
  **INELIGIBLE for the Shopify Theme Store**. If you target the Theme
  Store, rebuild from the empty OS 2.0 structure.

### `shopify-hydrogen` context (~2.9 KB)

- Remix v3 / React Router v7 route conventions (`loader` server,
  `action` mutations, server-driven UI).
- Cache hints (`CacheLong`, `CacheShort`, `CacheNone`, `CacheCustom`).
- GraphQL fragments pattern (`app/lib/fragments.ts`).
- Optimistic UI via `useOptimisticCart` + `<CartForm>`.
- Hydrogen primitives (`<Money>`, `<Image>`, `<CartProvider>`,
  `<ShopifyAnalytics>`, `<PaymentTokens>`).
- Customer Account API (new) — OAuth-based, replaces Classic.
- Oxygen deployment (Shopify's free edge platform).
- Performance: Lighthouse 95+ achievable, streaming SSR with `<Suspense>`,
  per-loader `Cache-Control`, edge caching.
- Tailwind v4 with CSS custom properties so tokens stay portable.

### `shopify-polaris-app` context (~2.7 KB)

- Remix v3 + Polaris (`@shopify/polaris` + `@shopify/polaris-icons`) +
  App Bridge 4 + Prisma + Shopify Functions.
- Auth via `@shopify/shopify-app-remix`.
- `shopify app dev` starts a Cloudflare tunnel so the Admin iframe can
  reach your localhost.
- Extension types you can generate via `shopify app generate extension`:
  theme app extension, checkout UI, customer account UI, admin block /
  action, Shopify Functions, Flow action / trigger, POS UI.
- Distribution paths: Shopify App Store (public, $99–499/mo average),
  Custom (single store), Partner Managed.
- App Store quality gates: GDPR webhooks (`customers/data_request`,
  `customers/redact`, `shop/redact`), billing, OAuth complete, embedded
  TTI < 100 ms, Polaris-only UI.

## 5. Workflow (Liquid)

```bash
# 1) Create the project from Pcreative Studio (pick "Shopify Liquid")
#    → Pcreative Studio clones Dawn, writes extras and CLAUDE.md.

# 2) Install dev dependencies (prettier + Liquid plugin)
npm install

# 3) Log in to your Shopify Partners dev store
shopify login --store=your-shop.myshopify.com

# 4) Local dev with hot reload on http://127.0.0.1:9292
npm run dev                  # = shopify theme dev

# 5) Work with the AI agent (Claude Code, Cursor, …)
#    The agent already has:
#      · The three Shopify MCPs live in .mcp.json.
#      · 10.9 KB of context in CLAUDE.md.
#      · The shopify/skills/theme-development skill auto-installed.

# 6) Quality gates before pushing
npm run format               # = prettier --write **/*.liquid
npm run check                # = shopify theme check (must pass clean)

# 7) Push as a draft theme to preview in the live admin
shopify theme push --unpublished --json

# 8) Package the ZIP for ThemeForest / Theme Store
shopify theme package
```

## 6. Workflow (Hydrogen)

```bash
npm install
npm run dev                  # http://localhost:3000
npm run build
npm run preview              # local edge preview

npx shopify hydrogen link    # link this codebase to a store
npx shopify hydrogen deploy  # deploy to Oxygen (Shopify's edge, free)
```

## 7. Workflow (Polaris App)

```bash
npm install
npm run dev                  # spawns shopify app dev with a Cloudflare tunnel

# Generate extensions on demand
shopify app generate extension  # interactive: theme, checkout, customer-account, admin, POS, Flow, Functions

# Publish a new app version
npm run deploy
```

## 8. The `CLAUDE.md` "objectives" block

When a Shopify project is created, the `objetivos_block` is filled with
the **Shopify Theme Store Quality Guidelines** as the bar — even if you
sell on ThemeForest. That covers:

- Lighthouse mobile 60+ minimum (top themes ship 90+).
- Accessibility score 90+ mandatory.
- `shopify theme check` clean.
- WCAG 2.1 AA: contrast 4.5:1 (regular text) / 3:1 (large or UI), focus
  visible, keyboard navigation, skip link, alt on all images,
  `aria-live` for dynamic UI changes (cart, search), touch targets
  ≥ 44 × 44 px.
- Full multi-locale (i18n in `locales/*.json`, zero hardcoded text).
- Browser support: Safari (last 2), Chrome (last 3), Firefox (last 3),
  Edge (last 2); mobile Safari, Chrome Mobile, Samsung Internet; plus
  Instagram / Facebook / Pinterest webviews.

Restrictions (auto-reject by Theme Store reviewers if violated):

- JS bundle < 16 KB minified. **No** React / Vue / Angular / jQuery.
- **No** Sass / SCSS — plain CSS only.
- No dependency on apps for core functionality.
- No Lorem Ipsum or onboarding text in the demo.
- No embedded designer credits or affiliate links.
- Theme Store exclusivity (if you go that route — themes there cannot
  be sold elsewhere).
- Compatibility with top apps (Klaviyo, Loox / Judge.me, Bold) — keep
  hooks open as placeholders, not hardcoded integrations.

## 9. Legal & attribution

All third-party Shopify tooling is downloaded from official sources at
scaffold or install time — **nothing** is bundled in this repository:

- Shopify CLI, Dawn theme, Hydrogen template, Polaris, App Bridge,
  shopify-app-remix, create-app template, dev-mcp, polaris-icons,
  Liquid Prettier plugin, Prettier, Shopify Lighthouse CI action — all MIT.
- Storefront MCP and Storefront UCP MCP are hosted by Shopify on every
  store, free, zero-auth.
- `Shopify®`, `Liquid®`, `Online Store 2.0™`, `Dawn`, `Hydrogen™`,
  `Oxygen`, `Polaris®`, `App Bridge`, `Shopify CLI`, `Shopify App Store`
  are trademarks of Shopify Inc., used under nominative fair use.

See [`NOTICE.md`](../NOTICE.md) (the Shopify integration section) and
[`TRADEMARKS.md`](../TRADEMARKS.md) for the full statement.

## 10. Further reading

Official Shopify docs that the `CLAUDE.md` context distils:

- <https://shopify.dev/docs/storefronts/themes> — themes overview.
- <https://shopify.dev/docs/storefronts/themes/architecture> — sections,
  blocks, templates, section groups, layouts, snippets, config, locales.
- <https://shopify.dev/docs/storefronts/themes/best-practices/performance>
- <https://shopify.dev/docs/storefronts/themes/best-practices/accessibility>
- <https://shopify.dev/docs/storefronts/themes/store/requirements>
- <https://shopify.dev/docs/storefronts/themes/tools> — the 11 developer
  tools the context references.
- <https://shopify.dev/docs/api/hydrogen> — Hydrogen API reference.
- <https://shopify.dev/docs/api/polaris> — Polaris components.
- <https://shopify.dev/docs/apps/build/storefront-mcp> — Storefront MCP
  servers (zero-auth, per-store).
