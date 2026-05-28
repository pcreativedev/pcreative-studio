# Trademarks

ThemeForge is an independent open-source project published under GPL v3
by the **pcreativedev** team. It is **not affiliated with, endorsed by,
sponsored by, or otherwise connected to** any of the third-party
products, brands, or marketplaces it references for integration.

This file lists the third-party marks referenced in ThemeForge source
code, documentation, scaffold templates, and prompts, and clarifies the
basis on which they are used.

## Basis of use

All third-party trademarks are used here strictly under the doctrine of
**nominative fair use**: the marks identify the corresponding products
so users and developers know which product ThemeForge integrates with
or analyses. Specifically:

- Only the wordmark / name is used. **No logos** of third-party products
  are reproduced anywhere in this repository.
- Usage is **factual and descriptive** (e.g., *"WordPress (Elementor
  Child Theme)"*, *"installs Bricks parent theme if declared in
  `wp_packs.json`"*, *"compatible with Divi"*).
- ThemeForge does **not** suggest sponsorship, partnership, certification,
  or any commercial relationship with the trademark owners.
- ThemeForge does **not** bundle, redistribute, modify, or sublicense any
  of the products listed below. Where auto-installation is offered, the
  product is downloaded from its **official source** (WordPress.org plugin
  repository, the project's own GitHub releases, or — for premium items —
  from a path supplied by the end user in a local config file).

## Trademarks referenced in this project

The following marks are owned by their respective holders. The list is
not exhaustive and inclusion here does not constitute endorsement,
neither by us of them nor by them of us.

### WordPress ecosystem

| Mark | Owner / Author | Use in ThemeForge |
|---|---|---|
| WordPress® | WordPress Foundation | Core CMS that ThemeForge auto-provisions in Docker for the WordPress stacks. Independent open-source platform under GPL v2+. |
| WooCommerce® | Automattic, Inc. | Mentioned as a representative e-commerce plugin for WordPress in scaffold notes and market-analysis prompts. |
| Bricks Builder™ | Bricks Builder GmbH | Named as the parent theme/builder targeted by the `wordpress-bricks` stack. Bricks itself is NOT bundled — the end user supplies their own purchased ZIP via `~/.config/themeforge/wp_packs.json`. |
| Elementor® | Elementor Ltd. | Free Elementor (from WordPress.org) is auto-installed for the `wordpress-elementor` stack. Elementor Pro is referenced by name only and requires a license obtained directly from elementor.com. |
| Hello Elementor | Elementor Ltd. | Auto-installed from WordPress.org (free, GPLv3) as the parent theme of the `wordpress-elementor` stack. |
| Divi™ | Elegant Themes Inc. | Named as the parent theme of the `wordpress-divi` stack. Divi is NOT bundled — the end user supplies their own purchased ZIP. |
| Breakdance® | SoftAndy Inc. | Free Breakdance (from WordPress.org) is auto-installed for the `wordpress-breakdance` stack. Breakdance Pro is referenced by name only. |
| Beaver Builder™ | Beaver Builder | Mentioned descriptively in market-analysis prompts and stack tables. Not installed by any stack. |
| Oxygen Builder | Soflyy LLC. | Mentioned descriptively in market-analysis prompts. Not installed. |
| Kadence | StellarWP / Liquid Web | Auto-installed from WordPress.org as the base theme of the `wordpress-breakdance` stack. Kadence Blocks Pro is referenced by name only. |
| GeneratePress / GenerateBlocks | Tom Usborne / Edge22 | GenerateBlocks free is auto-installed from WordPress.org for the `wordpress-block` stack. GenerateBlocks Pro is referenced by name only. |
| Spectra | Brainstorm Force (Astra) | Auto-installed from WordPress.org for the `wordpress-block` stack. |
| ACF® / Advanced Custom Fields® | WP Engine / Delicious Brains | ACF free is auto-installed from WordPress.org for all WordPress stacks. ACF Pro is referenced by name only. |
| Pods | Pods Foundation | Auto-installed from WordPress.org. |
| GreenShift | GreenShift Web | Auto-installed from WordPress.org for the `wordpress-bricks` stack. |
| Essential Addons for Elementor | WPDeveloper | Lite version auto-installed from WordPress.org for the `wordpress-elementor` stack. |
| JetEngine®, JetSmartFilters, Crocoblock® | Crocoblock | Referenced by name in scaffold notes and market-analysis prompts. Not bundled. |
| Bricksforge | Bricksforge GmbH | Referenced by name in scaffold notes for the `wordpress-bricks` stack. Not bundled. |
| Motion.page | Motion.page | Referenced by name in scaffold notes and prompts. Not bundled. |
| Royal MCP | Royal Plugins | Auto-installed from WordPress.org as the MCP plugin for all WordPress stacks. |
| Novamira / Novamira Pro | use-novamira | Free version auto-installed from the project's official GitHub releases (AGPL v3). Pro is referenced by name only. |
| Yoast SEO, Rank Math, AIOSEO | Yoast B.V. / Rank Math / All in One SEO | Mentioned descriptively in scaffold notes (Royal MCP integrates with their term meta). Not installed. |

### Shopify ecosystem

| Mark | Owner | Use in ThemeForge |
|---|---|---|
| Shopify® | Shopify Inc. | E-commerce platform that the Shopify stacks (`shopify-liquid`, `shopify-hydrogen`) target. |
| Liquid® | Shopify Inc. | Templating language used by Online Store 2.0 themes. |
| Online Store 2.0™ | Shopify Inc. | Theme architecture targeted by `shopify-liquid`. |
| Dawn | Shopify Inc. | Official reference theme (MIT) used as the starting point of `shopify-liquid` via `shopify theme init --clone-url`. |
| Hydrogen™ | Shopify Inc. | Headless storefront framework (MIT) used as the starting point of `shopify-hydrogen` via `npm create @shopify/hydrogen`. |
| Oxygen | Shopify Inc. | Hosting/edge platform for Hydrogen, referenced in scaffold notes. |
| Polaris® | Shopify Inc. | Design system for Shopify Admin embedded apps, used by the `shopify-polaris-app` stack and accessible via `@shopify/dev-mcp`. |
| App Bridge | Shopify Inc. | Embedded-app runtime (`@shopify/app-bridge-react`) used by the `shopify-polaris-app` stack. |
| Shopify CLI | Shopify Inc. | Developer CLI invoked by ThemeForge to scaffold themes and apps. |
| Shopify App Store | Shopify Inc. | Marketplace for public Shopify apps, mentioned descriptively in scaffold notes for `shopify-polaris-app`. |

### Marketplaces & ecosystems referenced in market-analysis prompts

| Mark | Owner |
|---|---|
| ThemeForest®, CodeCanyon®, Envato® | Envato Pty Ltd. |
| Gumroad® | Gumroad, Inc. |
| Lemon Squeezy® | Lemon Squeezy LLC |
| Creative Market® | Creative Market |
| Itch.io | itch corp. |
| ArtStation | Epic Games, Inc. |
| Shopify® | Shopify Inc. |
| Unity® / Unity Asset Store | Unity Technologies |

### Page builders & competing themes mentioned in market-analysis

| Mark | Owner |
|---|---|
| Astra | Brainstorm Force |
| Flatsome, Woodmart, Avada | XTemos / ThemeFusion |
| Webflow® | Webflow, Inc. |
| Framer® | Framer B.V. |

Any other third-party name mentioned in `market_analyzer.py` prompts or
in scaffold documentation belongs to its respective owner. We use these
names solely to identify the products in their function as market
context, in line with nominative fair use.

## If you own a trademark referenced here

If you believe a use in this repository goes beyond what nominative
fair use allows, please open an issue at
<https://github.com/pcreativedev/themeforge/issues> describing:

1. The exact file and line where the mark appears.
2. The legal basis for the request.
3. The desired remedy (rewording, removal, etc.).

We will respond promptly and in good faith.

## Our own marks

"ThemeForge" and "pcreativedev" are project / team names. We do not
register them as trademarks and offer no objection to descriptive,
non-misleading use of these names by third parties (e.g., *"built with
ThemeForge"*).

---

Last updated: 2026-05-28.
