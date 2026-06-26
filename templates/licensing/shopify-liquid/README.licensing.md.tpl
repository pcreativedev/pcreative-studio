# __PROJECT__ — License system

Pcreative Studio has scaffolded a 6-layer anti-nulled licensing system into
this Shopify Liquid theme. It validates the merchant's purchase code
against your backend, verifies the returned JWT offline (RS256), gates
premium sections, and stamps unlicensed installs with a visible
watermark + invisible tracking id.

## Files

- **`assets/pcreative-license.js`** — the client. Loaded with `defer`
  from `layout/theme.liquid`. Exposes `window.pcreativeLicense.{isValid,
  claims, gate}`.
- **`snippets/license-gate.liquid`** — wraps premium content. Renders
  a "premium locked" placeholder when no purchase code is set.
- **`snippets/license-watermark.liquid`** — always renders; visible only
  when JS marks the license invalid.
- **`config/settings_schema.json`** — gets a new "License" section with
  a `purchase_code` input.

## The protocol

The client speaks to a backend that implements the pcreative license
protocol:

```
POST <LICENSE_API_URL>
  Content-Type: application/json
  body: { license_key: "<code>", product: "__SLUG__", domain: "shop.myshopify.com" }
  response: { valid: true, jwt: "<RS256-signed token>" }
```

The JWT must carry these claims (in addition to standard `iat`/`exp`):
- `iss` — your issuer (must match `EXPECTED_ISSUER` in the JS).
- `sub` — the license key.
- `product` — the product slug (must match `EXPECTED_PRODUCT` in the JS).
- `domain` — the Shopify shop domain.
- `type` — `regular` or `extended`.
- `watermark` — unique id per license (used for piracy tracing).

## 6-layer protection

1. **Online activation** — first run sends purchase code to your backend.
2. **Offline verify** — JWT signature verified with embedded RS256 pubkey
   using browser-native SubtleCrypto. Zero deps, zero latency.
3. **Domain binding** — JWT carries the Shopify shop domain. If the
   theme is re-deployed elsewhere, the cached JWT is rejected.
4. **24h heartbeat** — JWT is refreshed daily. Revoke a license server-
   side → invalidated within 24h.
5. **Visible watermark** — `snippets/license-watermark.liquid` stamps
   unlicensed installs with a "Demo mode" badge.
6. **Tracking id** — every JWT carries a unique `watermark` claim. Find
   the theme nulled on another store → grep the DOM, you know who leaked.

## How to use the gate in your sections

Wrap any premium content:

```liquid
{% comment %} sections/premium-section.liquid {% endcomment %}
<div class="premium-section">
  {%- if settings.purchase_code != blank -%}
    <div data-pcreative-gated="true">
      <!-- premium content here -->
    </div>
  {%- else -%}
    {% render 'license-gate-placeholder' %}
  {%- endif -%}
</div>
```

Or via the gate snippet (if you prefer one-liner):

```liquid
{%- render 'license-gate' with content -%}
  <h2>Premium content</h2>
  ...
{%- endrender -%}
```

## Update gating (optional, recommended)

Your backend should also gate **updates** to the theme — that's the
real anti-piracy layer (no JS in the world stops a determined pirate
from deleting your watermark, but they can't fake a server-signed
update endpoint).

Pattern: when you ship a new version, push it to
`<LICENSE_API_URL>/api/update?product=__SLUG__&jwt=<valid>` and
return a signed update package URL. Themes without valid JWT can't
fetch it.

## Configuration

Replace these placeholders in `assets/pcreative-license.js`:

- `__LICENSE_API_URL__` — your backend activation endpoint.
- `__LICENSE_PUBKEY__` — PEM-encoded RS256 public key.
- `__LICENSE_ISSUER__` — your issuer domain.

For local dev with Pcreative Studio, these come from
`~/.config/themeforge/licensing.json` automatically. For the public
release, the user replaces them with their own backend.
