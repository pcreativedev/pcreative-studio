# E-commerce stacks in ThemeForge

ThemeForge ships **16 e-commerce stacks** under a single "E-commerce"
category in the stack picker. They cover the full spectrum from
SaaS-themed (Shopify, BigCommerce) to self-hosted PHP frameworks
(Magento, PrestaShop, OpenCart, Sylius) and headless TypeScript backends
(Hydrogen, Saleor, Vendure, Medusa, ForgeCommerce). This guide walks each
non-Shopify platform; for Shopify see [`docs/SHOPIFY.md`](SHOPIFY.md).

> All third-party tooling is pulled from official sources at scaffold
> time (Composer, npm, git). Nothing is bundled in this repository. See
> [`NOTICE.md`](../NOTICE.md) and [`TRADEMARKS.md`](../TRADEMARKS.md).

## At a glance

| Stack | Family | License | Best for | Marketplaces |
|---|---|---|---|---|
| `shopify-*` (×7) | SaaS · proprietary platform, MIT/proprietary tooling | mixed | Shopify Theme Store, ThemeForest, App Store, Plus partner channel | see `docs/SHOPIFY.md` |
| **`magento-hyva`** | Self-hosted PHP | OSL 3.0 + AFL 3.0 | Adobe Commerce builds, enterprise Magento with modern frontend | Adobe Commerce Marketplace, ThemeForest |
| **`saleor-nextjs`** | Headless TypeScript / GraphQL | BSD-3 | Multi-channel B2B + B2C, multi-region | GitHub, enterprise custom |
| **`vendure`** | Headless TypeScript / NestJS | MIT | Self-hosted typed commerce, plugin-first | Self-distributed |
| **`bigcommerce-stencil`** | SaaS · Handlebars themes | Cornerstone MIT | BigCommerce Theme Store, ThemeForest | BigCommerce Theme Store ($150-300), ThemeForest (900+) |
| **`medusa`** | Headless TypeScript | MIT | MVP-fast commerce backends + Next.js storefront | Self-distributed |
| **`prestashop-theme`** | Self-hosted PHP / Smarty | OSL 3.0 | EU SMB online stores, Spanish/French market | PrestaShop Addons (2k+), ThemeForest (900+) |
| **`opencart-theme`** | Self-hosted PHP / Twig | GPL | Small/medium stores, English-speaking market | OpenCart Marketplace, ThemeForest (1.5k+) |
| **`sylius`** | Self-hosted PHP / Symfony 7 | MIT | Custom enterprise PHP commerce, multi-channel | Sylius Marketplace, Packagist |
| **`forge-commerce`** | Headless TypeScript (Medusa 2 + Next.js) | MIT | Self-hosted, 0%-commission commerce with multi-gateway + semantic search | Self-distributed |
| **`forge-commerce-growshop`** | Headless TypeScript (Medusa 2 + Next.js) | MIT | Same as `forge-commerce` + business guide for specialised/age-gated catalogs | Self-distributed |

## 1. Magento 2 + Hyvä (`magento-hyva`)

Magento 2 child theme using the **Hyvä Theme** as parent. Hyvä replaced
the legacy Luma frontend with Tailwind v4 + Alpine.js, taking Lighthouse
mobile from 25–40 to 90+ and JS bundle from 1.5+ MB to ~95 KB.

**Licence:** OSL 3.0 + AFL 3.0 (same as Magento core). Hyvä became
open-source on **2025-11-10**.

### Prereqs

- PHP 8.1+, Composer 2.
- Magento 2.4.8+ already installed (this stack scaffolds the child theme
  only — it does NOT bootstrap Magento itself).
- Free [hyva.io account](https://www.hyva.io/) to obtain Composer auth
  credentials for the Hyvä packagist.
- Node 22+ for Tailwind builds.

### What the scaffold does

Runs (in order):
1. `composer require hyva-themes/magento2-default-theme hyva-themes/magento2-theme-module`
2. `composer require freento/module-mcp` — auto-installs the
   [Freento MCP module](https://github.com/Freento/Magento-2-Mcp) (MIT)
   that exposes the store as an MCP HTTP server.
3. `bin/magento module:enable Freento_Mcp && setup:upgrade && cache:flush`
4. Writes `app/design/frontend/Pcreative/<slug>/{registration.php,theme.xml,composer.json,etc/view.xml}` with `parent: Hyva/default`.
5. Writes `web/tailwind/{package.json,tailwind.config.js,tailwind-source.css}` with Tailwind v4 + Hyvä preset.
6. Writes `Magento_Theme/layout/default.xml` override sample.
7. Writes `.mcp.json` wired to the Freento MCP with placeholders.
8. Writes `README-MAGENTO.md` with the full activation workflow.

### Activate the theme

```bash
composer dump-autoload
cd app/design/frontend/Pcreative/<slug>/web/tailwind && npm install && npm run build-prod && cd -
bin/magento setup:upgrade
bin/magento setup:di:compile
bin/magento setup:static-content:deploy -f
bin/magento cache:flush
# Admin → Stores → Configuration → Design → Design Theme = Pcreative/<slug>
```

### Wire the Freento MCP

The scaffold drops a `.mcp.json` with placeholders. To make the agent
talk to your Magento as an MCP tool:

1. Magento Admin → **System → Freento MCP → ACL Rules** → New Role →
   tick which tools to expose (sales / catalog / customer / admin /
   system).
2. → **AI MCP Clients** → New Client → assign the role above → Save.
3. Click the client → **Generate OTP** (valid 24 h) → **Generate Token**.
4. Open `.mcp.json` and replace:
   ```json
   {
     "mcpServers": {
       "magento": {
         "type": "http",
         "url": "https://YOUR-STORE.com/freento_mcp/index/index",
         "headers": { "Authorization": "Bearer YOUR_ACCESS_TOKEN" }
       }
     }
   }
   ```
5. Restart Claude Code / Cursor / Windsurf. The agent can now query
   orders, products, customers, stock, admins, system status.

### Override templates

```bash
cp vendor/hyva-themes/magento2-default-theme/Magento_Catalog/templates/product/list.phtml \
   app/design/frontend/Pcreative/<slug>/Magento_Catalog/templates/product/list.phtml
```

### Distribution

- Composer package on your own Packagist repo (e.g.
  `pcreative/magento2-theme-<slug>`).
- **Adobe Commerce Marketplace** — $99–499 per theme.
- ThemeForest — Magento category.

## 2. Saleor + Next.js (`saleor-nextjs`)

Official Saleor Storefront — React 18 + Next.js 15 (App Router) +
TypeScript + GraphQL Codegen + Tailwind.

**Licence:** BSD-3.

### Prereqs

- Node 22+.
- A Saleor backend (one of):
  - **Saleor Cloud** (managed, paid).
  - **Self-hosted** — `docker compose up` from
    [Saleor's GitHub](https://github.com/saleor/saleor).
  - **Public demo** — `store-public-uefa-iad.saleor.cloud/graphql/`
    (works out of the box for development).

### What the scaffold does

1. Clones [`saleor/storefront`](https://github.com/saleor/storefront).
2. Strips the upstream `.git` so your repo becomes the source of truth.
3. Sets `name` + `version` in `package.json`.
4. Writes `.env.example` (and `.env`) pointing to the public demo.
5. Writes `README-SALEOR.md`.

### Run

```bash
pnpm install         # or npm install
pnpm dev             # http://localhost:3000
pnpm generate        # GraphQL codegen after editing queries
pnpm build && pnpm start
```

### When to pick Saleor vs Hydrogen

| Case | Saleor | Hydrogen |
|---|---|---|
| Multi-channel B2B + B2C in one | ✓ native | requires Plus apps |
| Enterprise catalog modelling | ✓ | limited |
| Self-hosted total control | ✓ | only Oxygen |
| Plug-and-play SaaS | self-host effort | ✓ |
| GraphQL-first | ✓ from day 1 | ✓ |

## 3. Vendure (`vendure`)

Backend-only commerce framework — NestJS + TypeScript + GraphQL +
TypeORM (Postgres recommended) with an embedded Angular Admin UI.

**Licence:** MIT.

### Prereqs

- Node 22+.
- PostgreSQL 14+ (MySQL / SQLite also supported).

### What the scaffold does

```bash
npx @vendure/create@latest . --quick --skip-confirmation
```

`@vendure/create` is partly interactive; if `--quick` is not available
in your version, the scaffold falls back to a notice telling you to run
`npx @vendure/create .` manually.

### Run

```bash
npm install
npm run dev               # backend at :3000, admin at /admin
npm run dev:storefront    # if you opted in to the Next.js storefront
npx vendure add           # add plugins (asset-server, email, payments…)
```

### When to pick Vendure vs Saleor vs Medusa

- **Vendure** — most structured, cleanest plugin API, Angular admin
  native. Best fit for TypeScript-first teams.
- **Saleor** — Python backend, GraphQL-first since day 1, the most
  mature multi-region story for enterprise.
- **Medusa** — most MVP-friendly, growing fast, plugins are newer.

## 4. BigCommerce Stencil (`bigcommerce-stencil`)

BigCommerce theme based on the official **Cornerstone** template,
served by the Stencil framework (Handlebars + SCSS Citadel /
Foundation 5.5).

**Licence:** Cornerstone is **MIT**. The BigCommerce platform itself is
SaaS (proprietary); the theme code you write is yours under your chosen
licence.

### Prereqs

- Node 22+ (20 also supported).
- **Stencil CLI** installed globally:
  ```bash
  npm install -g @bigcommerce/stencil-cli
  ```
- A BigCommerce account (a free trial works for dev).
- API token from BigCommerce Admin → **Settings → API → Store-level API
  accounts → Create API account** (scope: Themes).

### What the scaffold does

1. Clones [`bigcommerce/cornerstone`](https://github.com/bigcommerce/cornerstone).
2. Strips the upstream `.git`.
3. Sets `name` + `version` in `package.json`.
4. Warns if `stencil` CLI is not installed.
5. Writes `README-BIGCOMMERCE.md`.

### Run

```bash
npm install
stencil init        # interactive: paste store URL + API token
stencil start       # https://localhost:3000 (HMR + live data)
stencil bundle      # produce .zip
stencil push        # upload to the connected store
```

### Theme Store gating

Like Shopify's Dawn, **themes derived from Cornerstone are ineligible
for the BigCommerce Theme Store**. For that route the theme must be
genuinely original. For ThemeForest the Cornerstone-as-base path is
standard.

## 5. Medusa (`medusa`)

Existing stack since v1.x — backend + Next.js storefront. Fastest path
to a typed commerce MVP.

**Licence:** MIT.

Refer to the upstream [Medusa docs](https://docs.medusajs.com/) for the
runtime commands. ThemeForge scaffolds the standard structure and wires
the dev preview on port 9000 (backend) + 8000 (storefront).

## 6. PrestaShop child theme (`prestashop-theme`)

Child theme inheriting from **`classic`** (the official PrestaShop
theme) on PrestaShop 9.

**Licence:** OSL 3.0 (same as PrestaShop core).

### Prereqs

- PHP 8.1+, MySQL 8 / MariaDB 10.5+.
- PrestaShop 9.x installed (`composer create-project prestashop/prestashop`).
- The `themes/classic/` directory must exist (it ships with PrestaShop).

### What the scaffold does

Creates `themes/<slug>/`:

```
config/theme.yml         # parent: classic + 4 layouts + settings
preview.png              # placeholder, replace with your 1080×640 mock
assets/{css,js,img}/     # only used if you set use_parent_assets: false
templates/               # .tpl Smarty overrides
modules/                 # module template overrides
_dev/                    # optional sources before compiling
```

### Activate

```bash
php bin/console prestashop:themes:enable <slug>
# or in the Back Office: Design → Theme & Logo → Use this theme
```

### Override a template

```bash
cp themes/classic/templates/catalog/product.tpl themes/<slug>/templates/catalog/
```

Smarty searches the child first, then the parent.

### Distribution

- **PrestaShop Addons** (official) — 2.000+ templates, €40–150 typical.
- **ThemeForest** — 900+ PrestaShop themes, $39–89.

## 7. OpenCart 4 theme extension (`opencart-theme`)

OpenCart 4 treats themes as **extensions** under `extension/<vendor>/`
(a big change from OC 3). OCMod is removed in OC 4 — only events are
supported.

**Licence:** GPL (same as OpenCart core).

### Prereqs

- OpenCart 4.0+ installed.
- PHP 8.0+ and MySQL 8 / MariaDB 10.5+.

### What the scaffold does

Creates `extension/<slug>/`:

```
install.json                                # manifest
admin/                                      # back office files
catalog/                                    # storefront files
  controller/startup/theme.php              # auto-loads the theme CSS
  view/
    template/                               # .twig overrides
      common/, product/, checkout/, …
    stylesheet/<slug>.css                   # theme CSS
    javascript/
    image/
```

### Pack and activate

```bash
cd extension && zip -r <slug>.ocmod.zip <slug>/
# Admin → Extensions → Installer → upload the .ocmod.zip
# Admin → Extensions → Extensions → Themes → install + activate
# Admin → Design → Theme → choose the theme
```

### Override a template

Mirror the original path in your extension and OpenCart will pick it up
automatically when the theme is active:

```bash
cp catalog/view/template/common/header.twig \
   extension/<slug>/catalog/view/template/common/header.twig
```

### Distribution

- **OpenCart Marketplace** — themes typically $30–150.
- **ThemeForest** — 1.500+ OpenCart themes.

## 8. Sylius 2.x (`sylius`)

A full-blown PHP commerce framework built on Symfony 7 — composer-driven
project with Doctrine ORM 3, Twig 3, Webpack Encore, API Platform 3.

**Licence:** MIT.

### Prereqs

- PHP 8.2+, Composer 2.
- PostgreSQL 14+ / MySQL 8.
- Node 22+ and Yarn (Webpack Encore for assets).
- Symfony CLI recommended.

### What the scaffold does

```bash
composer create-project --no-interaction sylius/sylius-standard .
```

Then writes a detailed `README-SYLIUS.md`. Sylius's `bin/console
sylius:install` is left for you to run because it prompts for an admin
password and a sample-data choice.

### Bootstrap a fresh Sylius project

```bash
cp .env .env.local
# edit DATABASE_URL and MAILER_DSN
php bin/console sylius:install   # creates DB + admin user + sample data
yarn install && yarn build
symfony server:start             # http://127.0.0.1:8000 (front) + /admin
```

### Custom theme via SyliusThemeBundle

`SyliusThemeBundle` ships preinstalled. To register your own:

```bash
mkdir -p themes/<slug>/templates/SyliusShopBundle
mkdir -p themes/<slug>/templates/SyliusAdminBundle
```

```json
{
  "name": "pcreative/sylius-<slug>",
  "extra": {
    "sylius-theme": {
      "title": "<Project Name>",
      "authors": [{ "name": "you", "email": "support@example.com" }]
    }
  }
}
```

Override Twig:

```bash
cp vendor/sylius/shop-bundle/templates/Product/show.html.twig \
   themes/<slug>/templates/SyliusShopBundle/Product/show.html.twig
```

Assign the theme to a channel in **Admin → Configuration → Channels →
edit channel → Theme dropdown**.

### Multi-channel

Sylius supports multi-channel natively: per channel you can configure a
distinct domain, theme, locales, currencies and tax zones.

### Distribution

- **Sylius Marketplace** (`sylius.com/store`).
- **Packagist** as a Composer package.

## 9. ForgeCommerce (`forge-commerce`, `forge-commerce-growshop`)

The agency's own headless e-commerce stack: a self-hosted **Medusa 2 +
Next.js** storefront built for 0%-commission, full-control stores. Unlike
the bare `medusa` stack (§5), ForgeCommerce ships an opinionated blueprint
(in the project's `CLAUDE.md`) covering multi-gateway payments, semantic
catalog search via **pgvector**, and a non-interactive Docker scaffold.

**Licence:** MIT (Medusa core + Next.js storefront). Anything you build on
top is yours under the licence of your choice.

### Prereqs

- Node 22+.
- **Docker** + Docker Compose — the scaffold brings up Postgres (with the
  `pgvector` extension) and Redis for you; you do not need a local DB.

### What the scaffold does

1. Runs the Medusa 2 scaffold non-interactively (backend + Next.js
   storefront), with `.git` stripped so your repo is the source of truth.
2. Writes a `docker-compose.yml` provisioning **Postgres (pgvector)** +
   **Redis**, so the stack is up with one command and no manual DB setup.
3. Wires `DATABASE_URL` / `REDIS_URL` and the storefront publishable key
   placeholders in `.env`.
4. Writes a `CLAUDE.md` blueprint with the security, payments and AI
   guidance for the agent: multi-gateway checkout (incl. high-risk
   providers), pgvector-backed semantic product search, and the
   pcreative licensing hooks shared by the other ThemeForge stacks.
5. Writes `README-FORGECOMMERCE.md` with the run workflow.

### Run

```bash
docker compose up -d            # Postgres (pgvector) + Redis
npm install
npm run dev                     # Medusa backend at :9000 (admin at /app)
cd storefront && npm install && npm run dev   # Next.js storefront at :8000
```

### Semantic search (pgvector)

The Postgres container ships the `pgvector` extension enabled, so the
storefront can embed products and run vector similarity search natively —
no external search SaaS required. The blueprint in `CLAUDE.md` documents
how to populate and query the embeddings.

### Multi-gateway payments

ForgeCommerce is designed to wire several payment providers side by side
through Medusa's payment-module API, so a store can route different
methods/regions to different processors. The provider keys are configured
per environment; nothing is hard-coded in the scaffold.

### The `forge-commerce-growshop` variant

`forge-commerce-growshop` is the same Medusa 2 + Next.js base with an
additional **business guide** aimed at specialised, age-gated catalogs
(e.g. growshop products). The extra material in its `CLAUDE.md` covers
age-verification gating and the legal notices/disclaimers a specialised
catalog typically needs, on top of the standard ForgeCommerce blueprint.
The technical scaffold (Docker, pgvector, multi-gateway) is identical to
`forge-commerce`.

### Distribution

- Self-hosted — you own the deployment end to end (0% platform
  commission).
- Distributable as your own template/repo; no marketplace dependency.

## MCPs available for e-commerce stacks

| MCP | Stack(s) | Transport | Auth | Tools |
|---|---|---|---|---|
| `shopify-dev` | All Shopify | STDIO | — | Admin / Storefront / Checkout API schemas + Polaris |
| `shopify-storefront` | All Shopify | HTTP (per-store) | none | cart, policies, FAQ |
| `shopify-storefront-catalog` | All Shopify | HTTP UCP | none | catalog NLP search |
| `shopify-customer-account` | catalog only (not auto-wired) | HTTP | OAuth 2.0 PKCE | order tracking, returns, addresses |
| `magento-freento-mcp` | `magento-hyva` (auto-wired in `.mcp.json`) | HTTP | OAuth Bearer | orders, quotes, credit memos, products, stock, customers, admins, system |

Saleor, Vendure, Medusa, ForgeCommerce, BigCommerce, PrestaShop, OpenCart
and Sylius do not ship native MCPs at the time of writing. The agent uses the
schema/docs already loaded via `autoskills` plus the project's
`CLAUDE.md` for those stacks.

## Picking the right e-commerce stack

Quick decision matrix:

- **Selling themes for thousands of small stores → Shopify Liquid /
  WordPress + WooCommerce / PrestaShop / OpenCart.** High volume, lower
  ticket.
- **Selling themes/apps for enterprise → Magento (Hyvä) / BigCommerce
  / Sylius / Shopify Plus.** Lower volume, higher ticket ($150-499).
- **Building a custom headless storefront for one client → Hydrogen /
  Saleor / Vendure / Medusa.** Project work, $15k-50k+ per build.
- **Building a Shopify App → Polaris-app / Functions / Checkout-ext.**
  Recurring revenue, $19-499/mo per merchant.
- **Embedding commerce on a non-Shopify site → Storefront Web
  Components.** Tiny ticket, very high volume potential ($19-49).

## Legal & licensing

All third-party tooling auto-installed by these stacks is fetched from
official sources at scaffold time. Licences enforced at install:

- Hyvä — OSL 3.0 + AFL 3.0 (OSS since 2025-11-10).
- Saleor Storefront — BSD-3 Clause.
- Vendure — MIT.
- Cornerstone — MIT.
- Medusa — MIT.
- ForgeCommerce (Medusa 2 + Next.js) — MIT.
- PrestaShop core — OSL 3.0.
- OpenCart core — GPL.
- Sylius — MIT.
- Freento MCP — MIT (per `composer.json` + Packagist v1.2.0).

Anything you write **on top** of these stacks is yours, under the
licence of your choice (the platforms above are permissive enough not
to constrain your downstream work, with the OSL/GPL caveat for
PrestaShop/OpenCart: the theme/extension code distributed back to
buyers must remain compatible with the parent licence).

See [`NOTICE.md`](../NOTICE.md) and [`TRADEMARKS.md`](../TRADEMARKS.md)
for the full breakdown.
