# Changelog

All notable changes to Pcreative Studio will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.8.1] - 2026-06-19

### Fixed

- **El modo Vibe (y cualquier función de IA "one-shot") ya no falla con un
  escueto «exit 1».** El modelo de Claude por defecto era `claude-fable-5`, que
  no está disponible en todas las cuentas (devuelve `404 model_not_found`), así
  que el comando salía con error nada más usarlo. Ahora el **modelo por defecto
  es «Auto»** (el que tu cuenta del CLI use por defecto), que siempre funciona;
  Fable 5 y los demás siguen siendo elegibles en **Credenciales** para quien
  tenga acceso. Además, el diálogo del Vibe ahora **muestra el motivo real** del
  fallo (antes el error llegaba en la salida del CLI y no se veía).

## [1.8.0] - 2026-06-18

### Added — Pcreative Studio móvil (cliente fino + motor remoto)

- **El motor de Pcreative Studio se puede usar desde el móvil.** Nuevo `api_gateway.py`
  (FastAPI) que expone el puente nativo como API remota (JSON-RPC + WebSocket para
  streaming + subida de ficheros), con autenticación por *bearer token* (variable
  de entorno o fichero en `~/.config/themeforge`). Pensado para vivir detrás de una
  VPN/red privada, no expuesto crudo a internet.
- **PWA + envoltorio Capacitor** (`webui/mobile/`, `mobile/`): instala Pcreative Studio
  como app en el teléfono. `webui/remote/tfbridge-remote.js` reimplementa
  `window.tfBridge` sobre la API, así la misma Web UI funciona contra un motor
  remoto sin cambios.
- **Notificaciones push** (`push_service.py`, FCM HTTP v1) para avisar al teléfono
  cuando termina un build. Las credenciales se leen de un *service-account* fuera
  del repositorio.

### Added — Stacks e-commerce self-hosted

- **ForgeCommerce** (`forge-commerce`): stack headless basado en **Medusa 2 +
  Next.js**, self-hosted, multi-pasarela, con búsqueda semántica (pgvector) y
  scaffold no-interactivo (Docker para Postgres/Redis). Variante
  `forge-commerce-growshop` con guía de negocio para catálogos especializados
  (control de edad, avisos legales).

### Changed

- **Recomendación de MCPs por stack más fina.** Los MCP de UI para JS/React
  (Magic/Magic UI/shadcn) ya no se sugieren en stacks que no son JavaScript
  (PHP/Smarty/Ruby, etc.). El cableado de `.mcp.json` y la guía de animaciones
  (framer-motion / 21st.dev) se aplican solo en frontends Node/React, incluidos
  los monorepos.
- **Galería**: al abrir un tema React se asegura `UI-MOTION.md`, el MCP de 21st.dev
  y `framer-motion`. Portapapeles del terminal embebido y arreglo del conmutador de
  *viewport* (móvil / tablet / escritorio) en la ventana de proyecto.

## [1.7.1] - 2026-06-04

### Fixed

- **La Web UI ya no depende de un CDN externo.** React, ReactDOM y Babel se
  cargaban desde `unpkg.com`, así que sin conexión a internet (o con una red
  inestable) la interfaz web podía quedarse en blanco. Ahora estas librerías van
  **vendorizadas** localmente en cada tema (igual que `qwebchannel.js`), de modo
  que la Web UI funciona offline y arranca más rápido.

## [1.7.0] - 2026-05-30

### Added — Panel Hermes completo en la Web UI

- **El Operador (Hermes) alcanza paridad 1:1 con el panel nativo** en los tres
  temas web (Neo-Tokyo · Matrix · Kawaii): las 12 pestañas del panel
  `hermes_panel.py` ahora existen en la UI web, cableadas a datos/acciones
  reales (cero mock). Además de Misión y Chat/Admin (que ya estaban): **Proveedor**
  (login OAuth / API key / elegir modelo cerebro), **Imágenes** (Runware:
  buscar modelos, default, test), **Agentes** (skills: listar/buscar/instalar +
  pack curado + sembrar web), **Crear** (plantilla / redactar con IA / guardar
  SKILL.md), **Memoria** (MEMORY.md + USER.md con contadores + notas por
  proyecto + sesiones), **Kanban** (boards/tareas/dispatch en vivo), **Cron**
  (jobs + pausar/reanudar/ejecutar/eliminar + programar), **Remoto** (gateway:
  setup/estado, enviar, pairing) y **Avanzado** (seguridad/portal/perfil/bundle/
  insights/fallback).
- **Bridge (`web_shell.py`)**: 49 slots Hermes nuevos + señal `hermes_event`
  para operaciones asíncronas (instalar skill, dispatch, draft IA, enviar
  mensaje, insights, test del cerebro), wrappers finos sobre `hermes <args>`
  reutilizando la lógica de `hermes_panel.py`. Los flujos interactivos (OAuth,
  gateway setup, fallback add) se abren en terminal embebida.

### Changed

- Terminal embebida: `node-pty` → `@homebridge/node-pty-prebuilt-multiarch`
  (binarios prebuilt, sin compilación nativa).

## [1.6.0] - 2026-05-29

### Added — Web UI (Neo-Tokyo · Matrix · Kawaii)

- **Pcreative Studio ahora tiene una UI web** renderizada en `QWebEngineView` + puente `QWebChannel` (`window.tfBridge`): los prototipos React/HTML son la interfaz principal. Por defecto arranca en modo web; `PCREATIVE STUDIO_CLASSIC=1` (o Ajustes → Temas → un tema clásico) vuelve a la UI nativa de QWidgets. Implementación en `web_shell.py` (+40 slots de puente) y `webui/`.
- **3 temas web completos**, cada uno con su propio splash de arranque: **Neo-Tokyo** (cyberpunk cian/magenta, por defecto), **Matrix** (terminal verde fósforo) y **Kawaii** (pastel). Se cambian en Ajustes → Temas. Los temas **web** recolorean la UI en vivo (CSS vars); los **clásicos** reinician la app para cargar la UI nativa.
- **Temas web enchufables**: suelta un JSON en `webui/themes/<slug>.json` y aparece como tema nuevo (recolor en vivo). Importador `tools/import_web_theme.py` convierte un tema de Claude Design (CSS) → pack JSON.
- **Todas las pantallas con datos/acciones REALES** (cero mock), a paridad con la app nativa, en los 3 temas:
  - **Galería** — proyectos en vivo + favoritos ★ · tags · archivar/restaurar · eliminar · filtros · búsqueda.
  - **New project** — 4 modos (desde cero / recreate referencia / adopt local / repo existente), análisis de referencia con IA + «Examinar», extras (PostgreSQL · licensing pcreative + repo gh + forzar), toggles autoskills/UI-UX Pro/MCP/docs, nicho, stacks por categoría plegable, nombre.
  - **Ventana de proyecto** — se abre en **ventana/modal aparte**; el **setup corre en un terminal real (node-pty/PTY)** y al terminar salta solo a la pestaña del agente; pestañas de terminal **Setup · Agente · Shell · Hermes · Office**; **preview** con sondeo de puerto + seguir la URL real del dev server + log en vivo + viewport (360/768/1280/1920/full) + 📸 screenshot + dropdown de sub-proyectos (mono-repo); **barra MCP** que lee/edita el `.mcp.json` real; toolbar Folder · VSCode · Terminal ext. · Operator · Pre-flight · ZIP · GitHub · Push · Deploy.
  - **AI Cost** — donut por proveedor + barras 30 días + tabla por modelo + totales + Re-scan.
  - **Compare** — el mismo prompt en cada IA en su terminal real lado a lado, con checkboxes para elegir agentes + limpiar.
  - **Market** — 6 análisis (general/stacks/predicción/nicho/marketplace/comparar-2) + copiar + exportar `.md` + «crear proyecto desde análisis».
  - **Licensing** — sistema anti-nulled real (estado del backend + licencias + crear + Productos/Gumroad/Tools).
  - **Settings** — estado del sistema (github/agentes/runtimes/tools) + diálogos nativos reales (credenciales con login OAuth/instalar CLI · dependencias · onboarding · editor de temas · import Figma) + skills por stack + atajos.
  - **Operator / Hermes** — power on/off + status strip (versión · MCP · modelo) + misión con fases (Plan→Crear→Build→QA→Empaquetar)/variantes/agente/log en vivo + Chat + Admin (dashboard web embebido) + pestañas Agentes/Crear/Memoria/Kanban/Cron.
  - **Command Palette** (⌘/Ctrl+K).
- **Preview robusto** (compartido por la UI web y la nativa): sondeo del puerto del dev server (sin delays fijos → adiós `ERR_CONNECTION_REFUSED`), seguimiento de la URL real del stdout (si el framework coge otro puerto), detección de sub-proyectos en mono-repos. El **setup** se ejecuta con TTY real (los scaffolders interactivos como `create-next-app` ya funcionan).
- **Capas Neo-Tokyo nativas** (para `PCREATIVE STUDIO_CLASSIC=1`): tema built-in Neo-Tokyo, splash de secuencia de arranque, atmósfera (grid + glows) y la pestaña **Operator → Hermes** con su shell de 8 sub-pestañas.

### Added — E-commerce expansion

- **NEW unified "E-commerce" category** in the stack picker. All 15 ecommerce stacks (the 7 Shopify variants plus the 8 below) are now grouped under a single `E-commerce` category, replacing the previous per-platform `CMS · Shopify`, `CMS · Magento`, etc. sub-categories.
- **NEW stack `magento-hyva`** — Magento 2.4.8+ child theme on **Hyvä Theme** (OSL 3.0 + AFL 3.0, open-source since 2025-11-10). 19-step scaffold: `composer require hyva-themes/magento2-default-theme + magento2-theme-module`, `composer require freento/module-mcp` (the MIT Freento MCP plug-in that turns the store into a queryable MCP server), `bin/magento module:enable Freento_Mcp + setup:upgrade + cache:flush`, full child-theme structure under `app/design/frontend/Pcreative/<slug>/` with `theme.xml` parent=`Hyva/default`, `composer.json` of type `magento2-theme` licence `OSL-3.0`, Tailwind v4 + Alpine config (`web/tailwind/{package.json,tailwind.config.js,tailwind-source.css}` with the Hyvä preset), `Magento_Theme/layout/default.xml` override, `.mcp.json` wired to the Freento MCP with placeholders, and `README-MAGENTO.md` covering build/deploy + MCP setup workflow.
- **NEW stack `saleor-nextjs`** — official Saleor Storefront (React 18 + Next.js 15 App Router + TypeScript + GraphQL Codegen with TypedDocumentString + Tailwind, BSD-3). 7-step scaffold: clones `saleor/storefront`, strips upstream `.git`, sets `name` + `version` in `package.json`, writes `.env.example` (and `.env`) pointing to the public Saleor demo, writes `README-SALEOR.md` covering backend options (Cloud / self-hosted / public demo), GraphQL workflow, channels/regions, and Saleor-vs-Hydrogen decision matrix.
- **NEW stack `vendure`** — headless commerce backend MIT (NestJS + TypeScript + GraphQL + TypeORM Postgres) with embedded Angular admin. 2-step scaffold via `npx @vendure/create@latest . --quick --skip-confirmation` + `README-VENDURE.md` covering plugins (`@vendure/asset-server-plugin`, `email`, `admin-ui`, `dashboard`, `payments`), multi-channel, Vendure-vs-Saleor-vs-Medusa comparison.
- **NEW stack `bigcommerce-stencil`** — BigCommerce theme based on the official `bigcommerce/cornerstone` (MIT) + Stencil CLI (Handlebars + SCSS Citadel / Foundation 5.5). 6-step scaffold: clones Cornerstone, strips `.git`, sets `name` + `version`, warns if Stencil CLI not installed (`npm install -g @bigcommerce/stencil-cli`), `README-BIGCOMMERCE.md` covering setup (init/start/bundle/push/release), theme structure, and BigCommerce Theme Store gating (Cornerstone-derived themes ineligible, same restriction as Dawn for Shopify).
- **NEW stack `prestashop-theme`** — PrestaShop 9 child theme inheriting from `classic` (OSL 3.0). 6-step scaffold: `themes/<slug>/config/theme.yml` declaring `parent: classic` with 4 available layouts (full-width / left-column / right-column / both-columns) and `use_parent_assets: true`, `preview.png` placeholder, full directory structure (`assets/{css,js,img}` + `templates/` + `modules/` + `_dev/`), `README-PRESTASHOP.md` covering activation via `bin/console prestashop:themes:enable`, Smarty override workflow, and marketplace targets (PrestaShop Addons 2k+ templates + ThemeForest 900+).
- **NEW stack `opencart-theme`** — OpenCart 4 theme packaged as an extension (GPL, OC 4 moved themes to `extension/<vendor>/`). 11-step scaffold: full `extension/<slug>/{admin,catalog}/...` tree, `install.json` manifest, `catalog/controller/startup/theme.php` that auto-loads the theme CSS when active, `catalog/view/stylesheet/<slug>.css` brand variables, `catalog/view/template/common/header.twig` override sample, `README-OPENCART.md` covering packaging (`.ocmod.zip`), admin installation flow, Twig override workflow, and OpenCart Marketplace + ThemeForest distribution. OCMod is deprecated in OC 4 — only events are supported.
- **NEW stack `sylius`** — Sylius 2.x full e-commerce framework (MIT) on Symfony 7.4 + Doctrine ORM 3 + Twig 3 + API Platform 3 + Webpack Encore + multi-channel native. 4-step scaffold via `composer create-project --no-interaction sylius/sylius-standard .` + `README-SYLIUS.md` covering bootstrap (`sylius:install` for DB + admin + sample data + `yarn build`), SyliusThemeBundle for custom themes, channels multi-store, and distribution via Sylius Marketplace + Packagist.
- **NEW MCP catalog entry `magento-freento-mcp`** — Freento MCP server for Magento 2 (MIT per `composer.json` + Packagist v1.2.0). HTTP transport, OAuth Bearer auth (`requires_auth=True`). Tools exposed: orders, quotes, credit memos, products, stock, customers, admin users, system status. Auto-wired in the `magento-hyva` stack's `.mcp.json` with placeholders; user generates the token in Magento Admin → System → Freento MCP → ACL Rules + AI MCP Clients + Generate OTP / Token.
- **NEW user guide `docs/ECOMMERCE.md`** (~440 lines) covering all 8 non-Shopify ecommerce stacks: per-stack prereqs, scaffold steps, activation workflow, template-override workflow, distribution channels, and licence breakdown. Comparison matrices for Saleor vs Hydrogen, Vendure vs Saleor vs Medusa. Decision matrix to pick the right ecommerce stack by goal (themes for SMB volume / enterprise / custom client builds / Shopify apps / embeddable commerce).
- **`docs/USER_GUIDE.md` §7 expanded** with the full E-commerce non-Shopify block (8 stacks) and pointer to `docs/ECOMMERCE.md`.
- **`README.md` navbar** adds a link to the new `docs/ECOMMERCE.md` guide.

## [1.5.0] - 2026-05-28

### Added — Licensing system for Shopify

- **Full pcreative licensing scaffold for the 7 Shopify stacks**. Mirrors the WordPress pattern: 6-layer anti-nulled (online activation → offline RS256 JWT verify with browser-native `SubtleCrypto` or `jose` on Node → domain binding → 24 h heartbeat → visible watermark on unlicensed installs → invisible `watermark_id` claim for piracy tracing). Implemented per family in `templates/licensing/`:
  - `shopify-liquid/` (used by `shopify-liquid` + `shopify-liquid-blank`) — `assets/pcreative-license.js` (vanilla, zero-deps), `snippets/license-gate.liquid`, `snippets/license-watermark.liquid`, `config/license-section.json` (add to settings_schema), `README.licensing.md`. Auto-injects the `<script>` and `{% render 'license-watermark' %}` into `layout/theme.liquid` via `sed`.
  - `shopify-storefront-webcomponents/` — `assets/pcreative-license.js` that **removes all `<shopify-*>` from the DOM** before hydration if licence invalid. Auto-injects `<script>` in `index.html`.
  - `shopify-hydrogen/` — server-side `app/lib/license.server.ts` (offline `jose` RS256 + in-memory cache + 24 h heartbeat), `app/routes/admin.license._index.tsx` status UI, `.env` additions, `README.licensing.md`.
  - `shopify-polaris-app/` (also used by `shopify-checkout-extension`) — `app/lib/license.server.ts` + Polaris UI route `app/routes/app.license.tsx` (`Banner` + `DataTable`) + Prisma `License` model migration + `.env` additions + `README.licensing.md`.
  - `shopify-functions/` — `scripts/pre-deploy-license-check.mjs` that runs on `predeploy` + `prebuild` and exits 1 if the licence is invalid (Functions run inside Shopify infra so runtime validation isn't possible; gating the deploy + the backend download is the only protection that survives the bytecode). `.env` additions + `README.licensing.md`.
- **`licensing_scaffold.py` STACK_FAMILIES extended** with the 5 missing WordPress builder variants (`wordpress-bricks`, `-elementor`, `-divi`, `-breakdance` already mapped via family `wordpress`) and the 7 Shopify entries mapped to 5 families (`shopify-liquid`/`liquid-blank` → `shopify-liquid`; `shopify-checkout-extension` shares the `shopify-polaris-app` family; the other four have their own family). Five new `_scaffold_shopify_*` dispatcher functions wire each into the setup script.
- **`licensing_panel.py` fix** — the `_create_license()` button in the Licensing tab was reading `data.get('key')` but the backend returns `{license: {key, type, …}}` wrapped, so the success dialog always showed the whole JSON dump. Now parses `data.license.key` correctly.

### Added — Shopify stacks (foundation: hydrogen + polaris-app + Liquid 2026 context)

- **3 Shopify stacks** in the selector:
  - `shopify-liquid` — Online Store 2.0 theme, clones [Dawn](https://github.com/Shopify/dawn) (MIT) as the starting point. Now scaffolds **`package.json`** + **`.prettierrc.json`** with `@shopify/prettier-plugin-liquid`, **`.theme-check.yml`** (strict: 16 KB JS cap, parser-blocking checks, deprecated filters, template length), **`.github/workflows/lighthouse-ci.yml`** using the official `shopify/lighthouse-ci-action@v1`. Free Dawn warning: themes derived from Dawn/Horizon are INELIGIBLE for the Shopify Theme Store (rebuild from scratch for that route).
  - `shopify-hydrogen` (NEW) — headless storefront with Remix v3 + React 19 + Oxygen. Scaffold via `@shopify/create-hydrogen@latest`. For large catalogs (500+ SKUs), multi-market builds, ThemeForest "Hydrogen" category, partner channel.
  - `shopify-polaris-app` (NEW) — embedded Shopify Admin apps with Polaris + App Bridge 4 + Remix + Prisma. Scaffold via `@shopify/create-app --template remix`. Supports theme/checkout/customer-account/admin/POS/Flow/Functions extensions.
- **3 official Shopify MCPs** wired into every Shopify project's `.mcp.json`:
  - `shopify-dev` (official, STDIO) — GraphQL Admin/Storefront/Checkout schemas, Liquid types, section/block schemas, and Polaris design system.
  - `shopify-storefront` (official, HTTP, zero-auth) — cart, policies, FAQ. User replaces `YOUR-SHOP` with their subdomain.
  - `shopify-storefront-catalog` (official, HTTP, UCP) — natural-language catalog search.
- **Per-stack AI context block** (`_SHOPIFY_BUILDER_CONTEXT`) injected into each project's `CLAUDE.md`: ~10.9 KB for Liquid covering OS 2.0 architecture (config/, layout/, sections with `{% schema %}`, blocks/ for theme blocks, templates JSON, locales), performance targets (Lighthouse 60+/90 A11Y/16 KB JS), 18 mandatory Theme Store features, 11 official developer tools (CLI, Theme Check, VS Code extension, Liquid Prettier plugin, Theme Inspector Chrome, Lighthouse CI Action, GitHub integration, Theme Access App, Dev Stores, LiquidDoc, Admin Theme Editor), conversion patterns, canonical code examples for templates/index.json + sections/hero-banner.liquid + config/settings_schema.json.
- **Updated objectives block** for Shopify product format with exact Theme Store Quality Guidelines (60+ Lighthouse mobile, 90+ accessibility, WCAG AA contrast 4.5:1/3:1, touch targets ≥44×44 px, supported browsers, mandatory JSON templates, 18 mandatory features, restrictions: no Sass/React/Vue/Angular/jQuery, no Lorem Ipsum, no embedded affiliate links, Theme Store exclusivity).
- **NEW stack `shopify-liquid-blank`** — scaffolds the minimal valid OS 2.0 structure from scratch (no Dawn, no Horizon). The Dawn-derived restriction means `shopify-liquid` (Dawn clone) cannot be submitted to the **Shopify Theme Store**; this new stack is the eligible alternative. Includes `config/{settings_schema,settings_data}.json` curated, `layout/theme.liquid` canonical, `sections/{header,footer}-group.json` + their Liquid skeletons, the 14 mandatory `templates/*.json` (404, article, blog, cart, collection, gift_card, index, list-collections, page, password, product, search + customers/*), `locales/en.default.{json,schema.json}` + `es.{json,schema.json}`, `assets/base.css`, same scaffold extras (prettier + theme-check + lighthouse-ci.yml) and same 3 MCPs as the Dawn-based stack. ~5 KB context block with submission-route guidance.
- **`shopify-hydrogen` context expanded** with Customer Account API (new) canonical patterns: loader auth + `app/routes/account.$.tsx`, CUSTOMER_QUERY GraphQL fragment, mutations for addresses/orders, `context.customerAccount.logout()`. Passwordless OAuth via `.customer-account.com` endpoint.
- **`shopify-polaris-app` context expanded** with Theme App Extensions (TAE) deeper: `shopify app generate extension --type theme_app_extension`, full directory structure (`extensions/<name>/{shopify.extension.toml, blocks/, snippets/, assets/, locales/}`), canonical `block.liquid` with `{% schema %}` (target: section|head, stylesheet, javascript, settings), how merchants add blocks via theme editor without touching Liquid.
- **MCP catalog updates** (`mcp_catalog.py`):
  - new `shopify-storefront` (HTTP zero-auth) and `shopify-storefront-catalog` (HTTP UCP zero-auth) entries.
  - NEW `shopify-customer-account` entry — OAuth 2.0 with PKCE, custom-domain-only, New Customer Accounts gate. NOT auto-wired in `.mcp.json` (user configures once their OAuth flow is ready).
- **Stricter `.theme-check.yml`** in both `shopify-liquid` and `shopify-liquid-blank` scaffolds — adds `ValidJSON`, `ValidSchema`, `RequiredLayoutThemeObject`, `UnreachableCode`, `ImgWidthAndHeight`, `MatchingTranslations` on top of the previous set.
- **Preview detection fix** for the 3 Shopify stacks (`preview.py`): the generic `npm run dev` fallback was firing before the Liquid file-based check, so the Liquid stack was incorrectly detected as port 3000 instead of `127.0.0.1:9292`. New explicit detectors for shopify-liquid (incl. `shopify-liquid-blank`), shopify-hydrogen and shopify-polaris-app are placed right after the Expo / Ionic detectors. Hydrogen gets a "Shopify Hydrogen dev" name + port 3000 with hint about `shopify hydrogen link`. Polaris-app gets "Shopify App (tunnel Cloudflared)" + port 3000 + note explaining the CLI prints the public tunnel URL.
- **Section Rendering API + Ajax endpoints + Metaobjects/Metafields** added to the Liquid context blocks: the canonical OS 2.0 fetch+DOMParser+replace pattern (used for cart drawer / variant picker / predictive search / faceted search), the full Ajax API endpoint reference (`/cart/add.js`, `/cart/change.js`, `/cart.js`, `/cart/update.js`, `/cart/clear.js`, `/cart/shipping_rates.json`, `/products/{handle}.js`, `/collections/{handle}/products.json`, `/search/suggest.json`, `/localization`), Liquid metafield access by type (text/richtext/money/date/color/references/json), metaobject loops (`shop.metaobjects.<type>.values`) and `metaobject` / `metaobject_list` settings types.
- **App Bridge 4 patterns** added to the Polaris-app context: `NavMenu`, `SaveBar` with `useAppBridge`, `resourcePicker` async API, `shopify.toast.show()` (vs Banner), `Modal` with `shopify.modal.show()`, Contextual Actions.
- **GDPR webhooks (mandatory for App Store)** added with canonical code: `customers/data_request`, `customers/redact`, `shop/redact` Remix action handlers + `shopify.app.toml` subscriptions block.
- **"Built for Shopify" certification gates** documented: TTI < 1s, Polaris-only, mobile-first, WCAG 2.1 AA, storefront perf if injecting scripts, 4.0+ stars with ≥ 50 reviews. Includes the revenue split detail (0% on first $1M USD then 15%).
- **App Store launch checklist (5 phases)**: Quality Standards, Monetization (billing API), Hosting, App Store Review (2-6 weeks typical, top rejection reasons), Customer Care.
- **Extension types deep dive**: complete table of all 11 extension types generatable via `shopify app generate extension --type <type>` — theme_app_extension, checkout_ui_extension, customer_account_ui_extension, ui_extension (admin block), admin_action, pos_ui_extension, flow_action, flow_trigger, web_pixel_extension, product/order/shipping_discounts, payment/delivery/cart_validations.
- **Hydrogen Markets API + multi-locale patterns**: `@inContext` directive on Storefront API queries, `parseLocale` helper, `CountrySelector` component pattern, `hreflang` generation in `root.tsx`. Note that `<Money>` and `<Image>` Hydrogen primitives are Market-aware automatically.
- **NEW stack `shopify-functions`** — Rust + Wasm extensions inside a Shopify app for discount/payment/delivery/validation logic running inside Shopify infra (≤ 5 ms runtime budget). Scaffold creates an app shell + sample `cart.lines.discounts.generate.run` function with `Cargo.toml`, `shopify.extension.toml`, `src/run.graphql`, `src/run.rs`, and `README-FUNCTIONS.md` covering the 6 supported targets. Distribution: App Store with $19-99/mo recurring typical.
- **NEW stack `shopify-storefront-webcomponents`** — embedded commerce in non-Shopify sites (blogs, landing pages, WordPress, Webflow, Framer). Scaffold ships `index.html` with the official Shopify Storefront Web Components loaded from `cdn.shopify.com/storefront/web-components.esm.js`, `assets/main.css` with `::part()` examples, `package.json` for Vite dev, `.mcp.json` with the 3 Shopify MCPs, `README-WEBCOMPONENTS.md` covering setup (Storefront API token + scopes), components reference (`<shopify-context>`, `<shopify-product>`, `<shopify-cart>`, …), styling with `::part()`, and use cases. Checkout stays hosted on Shopify.
- **NEW stack `shopify-checkout-extension`** — UI extension inside the hosted Shopify checkout. **Shopify Plus only.** Scaffold creates an app shell + `extensions/checkout-ui-extension/` with `shopify.extension.toml`, `src/Checkout.tsx` using `@shopify/ui-extensions-react/checkout`, and a `README-CHECKOUT.md` documenting all 9 supported targets (`purchase.checkout.block.render`, `purchase.thank-you.block.render`, …), capabilities (`network_access`, `block_progress`, `api_access`), sandbox restrictions, `useApi` patterns, and the UI component set. Pricing: $50-500/mo recurring for Plus merchants.
- **Updated `NOTICE.md` Shopify section**: Shopify CLI, Dawn, Hydrogen template, Polaris, App Bridge, create-app template, Liquid Prettier plugin, Prettier, Lighthouse CI action — all auto-installed at scaffold time from official sources; nothing bundled in this repo.
- **Updated `TRADEMARKS.md` Shopify ecosystem section**: Shopify, Liquid, Online Store 2.0, Dawn, Hydrogen, Oxygen, Polaris, App Bridge, Shopify CLI, Shopify App Store — declared under nominative fair use with no implied affiliation.

## [1.4.0] - 2026-05-28

### Added — WordPress expansion

- **5 WordPress stacks** in the selector: `wordpress-block` (FSE), `wordpress-bricks` (Bricks Builder child theme), `wordpress-elementor` (Hello Elementor child theme), `wordpress-divi`, `wordpress-breakdance`. Auto-installs the FREE plugin/theme pack per stack from WordPress.org via wp-cli, plus Novamira free from its official GitHub release (AGPL v3). Premium plugins/themes (Bricks, Elementor Pro, Divi, Breakdance Pro, JetEngine, Novamira Pro, ACF Pro, Motion.page, etc.) are referenced by name only — never bundled — and auto-install if and only if the user supplies a path in `~/.config/themeforge/wp_packs.json` (gitignored, local-only).
- **Market analysis tab** ("Market" between Compare and Operator) — six AI-driven analyses via OpenRouter (Gemini 2.5 Pro by default + 7 alternative models): `🌍 Mercado 2026 (general)`, `📊 Análisis de stacks`, `🎯 Por nicho concreto`, `⚖️ Comparar 2 nichos`, `🏪 Por marketplace`, `🔮 Predicción 2027`. Output rendered as markdown, persistent history at `~/.config/themeforge/market_analyses/`, "🚀 Crear proyecto desde este análisis" button that feeds the analysis into a new scratch project's `CLAUDE.md`. Yellow banner if `OPENROUTER_API_KEY` is missing, with deep-link to Settings → Credentials.
- **5 gaming sub-niches** added to `TEMPLATE_NICHES`: indie game dev / pixel studio, mobile games, game assets / marketplace, game launcher / storefront, tournament / ladder platform.
- **Legal hardening**: new `TRADEMARKS.md` (nominative fair use, ownership table, take-down channel), extended `NOTICE.md` with WordPress integration section (free auto-installed + premium referenced only, with AGPL Novamira clarification), `WORDPRESS-LEGAL.md` written into every WP project (free vs premium, marketplace rules, GPL obligations).

### Fixed (in v1.4.0)

- **Reference analyzer no longer mis-classifies commercial WordPress themes as `design-export`**. Any folder with a `style.css` containing `Theme Name:` or any root-level `.php` with `Plugin Name:` is now routed to the WordPress detector instead of falling into the design-export branch (which previously caused agents to see contradictory facts and refuse to proceed in recreate mode).
- **Stack autodetect respects the user's WP variant pick.** When the user manually selected `wordpress-bricks`/`-elementor`/`-divi`/`-breakdance` and then ran "Analyze reference with AI", the analyzer no longer downgrades the stack to plain `wordpress-block`.
- **Market analyzer `urllib` encoding fix.** The X-Title HTTP header used an em-dash (U+2014) that broke the latin-1 codec inside `urllib.request`. Replaced with ASCII hyphen.
- **Preview detector no longer attempts the deprecated `wp-env` profile.** Block themes were incorrectly matched by `has_wp_env()`, causing a flash of broken wp-env attempts before the real WordPress (Docker) profile took over.

## [1.3.4] - 2026-05-28

### Fixed
- **Reference analyzer no longer classifies WordPress themes/plugins as `design-export`** (any folder whose `style.css` has `Theme Name:` or root `.php` has `Plugin Name:` → WordPress detector).

## [1.3.3] - 2026-05-28

### Added
- **WordPress auto-login on `localhost`** (Pcreative Studio mu-plugin) + real **Start/Stop** buttons for the Docker WordPress preview (start/stop containers without losing data).

## [1.3.2] - 2026-05-28

### Fixed
- Removed the obsolete `WordPress (wp-env)` profile from the preview detector.

## [1.3.1] - 2026-05-28

### Fixed
- **Auto-detect the WordPress stack on `recreate`** from a theme/plugin folder without needing to run the AI analysis first.

## [1.3.0] - 2026-05-27

### Added
- **Self-provisioned WordPress dev environment in Docker** — Pcreative Studio brings up WordPress + MariaDB, installs WP (admin/admin) and mounts the project under `wp-content/{themes,plugins}/<slug>` before setup. The preview points straight at the live container (`no_server` profile); a `./wp` helper runs wp-cli inside the container. `wp-env` was dropped in favour of this.
- **WordPress MCP** (official Automattic bridge) auto-wired in `.mcp.json` for native control of the WP core from the agent.
- **Licensing client v2** (anti-nulled): RS256-signed JWT, offline verification with the embedded public key, gated auto-updater, and a `demo-installer`. Replaces the v1 client.
- **§B Envato checklist per product format** in the generated `CLAUDE.md` (Site Template vs Script/App vs WordPress vs Mobile), so the agent applies the right marketplace rules.

### Fixed
- wp-cli inside Docker: DB env + file permissions.

## [1.2.4] - 2026-05-26

### Changed / Fixed

- **Installed skills are now in the agent's context.** When a new project (any
  mode) installs autoskills / UI-UX Pro skills, the generated `CLAUDE.md`/`AGENTS.md`
  now includes a **"Skills instaladas — ÚSALAS"** section and the agent's startup
  prompt tells it to list `.claude/skills/` and use them — previously the skills
  were installed but the agent didn't invoke them on launch (not in context).

## [1.2.3] - 2026-05-26

### Added

- **✨ Vibe scaffolder — "🚀 Crear proyecto ya".** The Vibe dialog can now create
  the project in one click straight from the proposal (applies it, forces *from
  scratch* mode and launches creation), in addition to the existing "Aplicar al
  form".
- **🚀 Operator (Hermes) — optional autonomous missions.** Optional integration
  with [Hermes Agent](https://github.com/NousResearch/hermes-agent) (Nous, MIT) as
  an orchestration brain. A new **Operator** tab (Mission Control) takes a
  natural-language brief and autonomously plans → creates → builds → QA-loops →
  packages a project, with a **live web preview** and an interactive
  **💬 Chat con Hermes** terminal to keep modifying it. **🚀 Operator** buttons in
  the Gallery and in each ProjectWindow run it on *existing* projects; Hermes
  learns per-project (`.hermes.md`). Installable from the dependency wizard.
  **Fully optional** — the tab/buttons only appear if Hermes is installed;
  Pcreative Studio works exactly as before without it. See User Guide §23.
- **Build from a Figma design.** *New project → Recreate from reference →
  Figma (URL)* lets the AI agent implement your Figma frame faithfully via the
  `figma-context` MCP. Set your token at *Settings → 🔑 AI credentials → Figma*
  (`FIGMA_API_KEY`, a Figma personal access token).
- **Open/create more projects while one is running.** Each ProjectWindow now has
  **➕ Nuevo** and **📂 Abrir otro** — multiple project windows run side by side.

### Changed / Fixed

- **Vibe no longer restyles the app.** The proposed `theme_hint` is now only a
  suggestion for the generated project (it is already part of the dev prompt); it
  no longer applies/persists itself onto Pcreative Studio's own UI, which could leave
  the IDE stuck on a light theme. The Settings theme picker is unchanged.
- **Monorepo preview picks the customer-facing sub-app.** When opening a
  monorepo, the default active sub-app is now scored to favour the public site
  (`web`, `landing`, `frontend`…) over back-office apps (`admin`, `api`,
  `dashboard`…), so the preview opens the storefront, not the panel.
- **Dependency setup — auto-detect package manager.** The scaffold/open flow now
  detects **pnpm / yarn / bun / npm** (a `workspace:*` dependency or
  `pnpm-lock.yaml` ⇒ pnpm, with `corepack enable`). Dependency install is now
  **non-fatal**, so the AI agent still launches if `install` fails (it can fix it)
  — fixes monorepos failing with `EUNSUPPORTEDPROTOCOL "workspace:"`.
- **Figma MCP fixed.** The `figma-context` catalog entry now uses `--stdio` and
  passes the key only via env (`FIGMA_API_KEY`), not as a CLI arg.
- **Dependency wizard — Windows winget in a single elevated window.** Instead
  of one UAC prompt per package, all admin installs (winget + npm + installers)
  now run in one elevated PowerShell launched via `ShellExecuteW("runas")` — a
  single UAC, with a PATH refresh between winget and npm so Node/PHP are found.
- **PHP and Composer on Windows.** PHP installs via winget (`PHP.PHP.8.4`);
  Composer via the official `Composer-Setup.exe` (silent), after PHP so it is
  detected. `winget install` now also passes `--exact`.
- **venv path on Windows.** Python stacks (FastAPI, Django) activate the venv
  via `. .venv/*/activate`, which resolves to `Scripts` on Windows and `bin`
  on Unix.
- **Embedded terminal scrollbar.** The xterm.js viewport scrollbar is now
  visible and styled in the QtWebEngine view (was effectively hidden).

## [1.2.2] - 2026-05-25

### Added

- **First-run onboarding wizard.** A 5-step wizard (welcome → dependencies
  → AI credentials → defaults → finish) runs the first time Pcreative Studio
  starts, so new users land in a configured app. Re-openable from
  *Settings → 🧙 Setup wizard*.
- **AI credentials manager.** A panel (in onboarding and *Settings → 🔑 AI
  credentials*) listing all 7 providers with live status and per-provider
  actions: install the CLI, log in via OAuth in a terminal, or add / edit /
  remove an API key.
- **Form defaults.** Default stack, provider and template type are saved to
  `preferences.json` and pre-selected in the "New project" form.

### Changed / Fixed

- **Dependency wizard — Linux.** `npm install -g` now installs to `~/.local`
  (`NPM_CONFIG_PREFIX`) to avoid `EACCES` without sudo; system package
  managers that need a sudo password (paru / pacman / apt / dnf) run in a
  single terminal so the password is typed once, with a clear completion
  banner.
- **Dependency wizard — macOS.** Homebrew's `bin` directories are added to
  `PATH` at startup (GUI apps launched from Finder don't inherit the login
  shell `PATH`), so `brew` and tools installed with it are detected;
  Homebrew is bootstrapped in a terminal if missing; keg-only formula paths
  (`python@3.12`, `openjdk`, `ruby`) are included.
- **Dependency wizard — Windows.** `winget` calls pass
  `--disable-interactivity`; a step whose package was already installed
  (non-zero `winget` exit) is treated as success when the binary is now on
  `PATH`. Validated end-to-end on a Windows 10 VM.

## [1.2.1] - 2026-05-25

### Added

- **🪟 Windows support (alpha).** Pcreative Studio now runs on Windows 10/11
  with a real installer:

  - **Inno Setup installer** (`Pcreative Studio-Setup-X.Y.Z.exe`) built on
    `windows-latest` via GitHub Actions. Installs to `Program Files`
    (per-machine, UAC) like any normal app, with an entry in *Add/remove
    programs*, Start Menu + optional desktop shortcuts, App Paths registry
    (launch `themeforge` from Win+R), and a clean uninstaller that keeps
    your config.
  - **Bundled Node.js + git (PortableGit)** inside the installer — no
    separate downloads or admin needed for the two heavy runtimes.
  - **Software-OpenGL fallback** auto-detected for GPU-less environments
    (VMs, RDP): prevents the QtWebEngine black-window issue.
  - **`@homebridge/node-pty-prebuilt-multiarch`** for the embedded
    terminal — prebuilt binaries for Windows/macOS/Linux, no compilation.
  - Setup scripts now use POSIX paths and a `python3→python` shim so the
    scaffold runs correctly under Git Bash.

  **Not yet validated as stable** — expect rough edges; the installer is
  not code-signed yet (SmartScreen warning on first run).

- **🎬 Video splash screen** on startup (`assets/videosplash.mp4`),
  skippable with a click/keypress. Auto-skips on GPU-less environments.

- **🎯 Predefined niche field** in *New project* — 90 industries/niches
  (SaaS, restaurant, medical, real-estate, wedding, fitness, crypto…) or
  type your own. Injected into the generated `CLAUDE.md` so the AI nails
  the palette, copy tone, themed stock images and demo data for the sector.

- **🔧 Dependency setup wizard.** Detects and installs the external tools
  Pcreative Studio needs (Node, git, GitHub CLI, the AI CLIs, netlify, plus
  per-stack runtimes: Python, Java, Rust, Go, Bun, Deno, Ruby, Hugo, PHP)
  via winget / brew / paru — or direct official installers when no package
  manager is present. Opens automatically on first run if Node/git are
  missing, and when a chosen stack needs a runtime that isn't installed.

- **Assets & demo-data policy in generated `CLAUDE.md`** (§C/§D/§E):
  concrete Unsplash/Pexels/DiceBear URLs, per-template-type demo data,
  niche-specific guidance, and an interaction policy that makes the agent
  ask before design decisions instead of assuming.

### Changed

- **Cross-platform path handling.** All config/cache writes go through
  `platform_compat.app_config_dir()` / `app_cache_dir()` (→
  `%APPDATA%/themeforge` on Windows, `~/Library/Application Support` on
  macOS, `~/.config/themeforge` on Linux). Shell calls, process control
  and `chmod` now route through cross-platform helpers.
- All file I/O uses explicit `encoding="utf-8"` (Windows defaulted to
  cp1252 and choked on emoji-rich files like `CLAUDE.md`).

## [1.2.0] - 2026-05-24

### Added

- **📡 MCP server + curated catalog of community MCPs.** Two new
  capabilities for the Model Context Protocol ecosystem (2026's
  fastest-growing standard for AI tool exposure):

  1. **`mcp_server.py`** — Pcreative Studio's own stdio MCP server. Exposes
     8 tools (`list_stacks`, `list_themes`, `list_recent_projects`,
     `list_supported_providers`, `estimate_cost`, `suggest_stack`,
     `run_preflight`, `build_zip`) to any MCP client (Claude Code,
     Cursor, Windsurf, OpenCode). Built on Anthropic's official
     `mcp` Python SDK + FastMCP. Runs as a subprocess of the client
     — no VPS, no network, no remote endpoint.

  2. **`mcp_catalog.py`** — curated registry of 12 community MCP
     servers organized by stack relevance (universal / web-frontend /
     wordpress / shopify / database / design). When the
     **📡 Pre-configurar MCP servers** toggle in Setup sub-tab is on
     (default), Pcreative Studio writes a `.mcp.json` in every scaffolded
     project pointing at the right MCPs. The user's AI client reads
     it on startup and downloads each MCP via `npx` / `uvx` / `docker`
     on first invocation — Pcreative Studio never bundles their source,
     just generates the config.

  Catalog (license-verified at curation time):
    - **Universal (any stack):** filesystem (MIT), fetch (MIT),
      memory (MIT), github (MIT), themeforge (GPL-3.0).
    - **Web frontend / CMS:** playwright (Apache-2.0), chrome-devtools
      (Apache-2.0), figma-context (MIT), browsermcp (Apache-2.0).
    - **Shopify:** Shopify/dev-mcp (official).
    - **Backend with DB:** postgres (MIT, crystaldba).

  All licenses fully compatible with Pcreative Studio's GPL v3 — they're
  subprocess invocations, not embedded code. Discovery reference:
  [punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers).

### Fixed

- **🔽 QComboBox dropdown arrow now visible across all themes.**
  The QSS for inputs styled `QComboBox::drop-down` (the click-target
  area) but never `::down-arrow` (the chevron icon inside it). With
  Fusion style + our QSS overrides, the default arrow rendering got
  suppressed and dropdowns looked like flat editable fields — users
  had no visual affordance to expand the list. Now drawn as a CSS
  border-triangle (no image asset needed) in `fg_secondary` when
  closed and `accent` when open, applied to all 4 input variants
  (outlined / filled / underlined / brutalist).
- **↻ Repo loader now auto-opens the dropdown.** After
  `_load_repos()` populates the combo from `gh repo list`, the
  dropdown auto-pops 150ms later so the user immediately sees
  their repos. Button text confirms `✓ N repos cargados`. No more
  "I clicked the button and nothing happened" — the list is right
  there.

### Changed

- **🏗️ "Nuevo proyecto" tab redesigned with sub-tabs.** The form was
  getting crowded — vibe input, 6 basic fields, 4 modes (each with
  their own sub-form), 3 advanced toggles, preview pane, all in one
  vertical scroll. Now organized in 5 sub-tabs:
  - **✨ Vibe** — natural language → form auto-fill (hero feature).
  - **🏗️ Setup** — name, stack, type, provider, autoskills + uipro.
  - **📦 Modo** — scratch / recreate / adopt / existing. Sub-forms
    of non-selected modes are now **hidden** instead of just disabled
    (eliminates the "se solapan los modos" visual clutter).
  - **🔌 Extras** — postgres + licensing toggles (advanced).
  - **👁 Preview** — final command preview before create.
  Footer (Salir / Crear proyecto) stays always visible across sub-tabs.

### Added

- **✨ Vibe scaffolder mode.** New input at the top of the "Nuevo
  proyecto" form: the user types a natural-language description
  ("Landing premium para clínica dental en Madrid, paleta cálida,
  conversion-optimized") and clicks **✨ Pre-rellenar form con IA**.
  The active AI provider returns a structured JSON proposal that
  auto-populates: stack key, template type, theme of the app,
  autoskills/uipro toggles, and a polished 150-300 word dev prompt
  injected into the generated CLAUDE.md/AGENTS.md so the agent
  starts with full context. New module `vibe_scaffolder.py`:
  - `build_vibe_prompt()` — composes a structured prompt with the
    61 available stacks, 21 template types, 8 builtin themes and
    decision rules (WordPress → wordpress-block, mobile → flutter,
    premium/wellness → soft-ui theme, etc.).
  - `parse_vibe_response()` — robust JSON extractor (markdown
    fences, leading/trailing prose, balanced brace scan as fallback).
  - `VibeDialog` — streams the AI response live using the
    `stream_parsers` infrastructure, shows a preview pane on
    completion with stack/type/theme + reasoning, lets the user
    Apply or Discard. The dev_prompt feeds the existing
    `ai_analysis` injection pipeline so it lands inside CLAUDE.md
    without extra plumbing.
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
    the Pcreative Studio slot, and editable raw value.
  - **Semantic mapping engine** with 26 color patterns + 5 shape
    patterns that score Figma token paths against Pcreative Studio slots
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
  JSON-token-driven theming for the Pcreative Studio UI itself. Ships with
  5 builtin themes:
  - **Pcreative Studio Dark** (default) — blue accent, VSCode-inspired.
  - **Pcreative Studio Light** — paper-white with blue accent.
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
  works identically on the 7 Pcreative Studio providers. Cost is computed
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
  previously `None`). All 7 Pcreative Studio providers now get the full
  autoskills + uipro skill stack on scaffold.
- **🎨 UI UX Pro Max integration.** New *"uipro UI/UX Pro Max"*
  checkbox in the project form (auto-checked for any stack with a
  visual UI surface; OFF only for `Backend · API` stacks). When on,
  Pcreative Studio runs `npx --yes uipro-cli init --ai <agent>` after
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
- **🎨 App icon + desktop launcher.** Pcreative Studio ships an app icon in
  `assets/themeforge.png` (anvil + hammer + code/screens — branded for
  the project) plus pre-rendered sizes (16/32/48/64/128/256). The icon
  is loaded at startup and propagates to titlebar / taskbar / alt-tab
  / dock. A `scripts/install-desktop-entry.sh` script installs a
  user-local `.desktop` entry so Pcreative Studio shows up in the DE app
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
- Initial public release of Pcreative Studio.
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
