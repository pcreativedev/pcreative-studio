"""hermes_skill_pack.py — pack curado de skills del registro relevantes para los
templates web de Pcreative Studio y TODOS sus stacks.

De las ~36k skills del registro de Hermes, esta es una selección verificada en vivo
(`hermes skills search --source skills-sh/official --json`, 2026-05-30), priorizando
fuentes OFICIALES/autoritativas: Shopify AI Toolkit, WordPress/Automattic, Vercel
(Next/React), Svelte oficial, antfu (Vue), addyosmani (web quality), Figma, Cloudflare
(web-perf), Microsoft (design review).

Se instalan con `hermes skills install <id> --force` en `~/.hermes/skills/` (globales,
complementan al pack de agentes propios y a lo que autoskills instala por proyecto).
"""
from __future__ import annotations

# (id de registro, etiqueta, dominio). Los ids están verificados contra el registro.
WEB_SKILL_PACK: list[tuple[str, str, str]] = [
    # Calidad web (transversal)
    ("skills-sh/addyosmani/web-quality-skills/accessibility", "Accessibility (addyosmani)", "Calidad web"),
    ("skills-sh/addyosmani/web-quality-skills/seo", "SEO (addyosmani)", "Calidad web"),
    ("skills-sh/addyosmani/web-quality-skills/web-quality-audit", "Web quality audit", "Calidad web"),
    ("skills-sh/cloudflare/skills/web-perf", "Web performance (Cloudflare)", "Calidad web"),
    # CSS / diseño
    ("skills-sh/wshobson/agents/tailwind-design-system", "Tailwind design system", "CSS / diseño"),
    ("skills-sh/wshobson/agents/responsive-design", "Responsive design", "CSS / diseño"),
    ("skills-sh/heygen-com/hyperframes/css-animations", "CSS animations", "CSS / diseño"),
    ("skills-sh/microsoft/skills/frontend-design-review", "Frontend design review (Microsoft)", "CSS / diseño"),
    ("skills-sh/jezweb/claude-skills/landing-page", "Landing page", "CSS / diseño"),
    ("skills-sh/wshobson/agents/typescript-advanced-types", "TypeScript avanzado", "CSS / diseño"),
    ("skills-sh/figma/mcp-server-guide/implement-design", "Figma → implementar diseño", "CSS / diseño"),
    # Frameworks frontend
    ("skills-sh/astrolicious/agent-skills/astro", "Astro", "Frameworks"),
    ("skills-sh/vercel/nextjs-skills/next-cache-components", "Next.js (Vercel)", "Frameworks"),
    ("skills-sh/wshobson/agents/nextjs-app-router-patterns", "Next.js App Router", "Frameworks"),
    ("skills-sh/vercel-labs/agent-skills/vercel-react-best-practices", "React best practices (Vercel)", "Frameworks"),
    ("skills-sh/antfu/skills/vue", "Vue (antfu)", "Frameworks"),
    ("skills-sh/sveltejs/ai-tools/svelte-core-bestpractices", "Svelte (oficial)", "Frameworks"),
    # E-commerce / CMS
    ("skills-sh/shopify/shopify-ai-toolkit/shopify-liquid", "Shopify Liquid (oficial)", "E-commerce / CMS"),
    ("skills-sh/shopify/shopify-ai-toolkit/shopify-dev", "Shopify dev (oficial)", "E-commerce / CMS"),
    ("skills-sh/shopify/shopify-ai-toolkit/shopify-storefront-graphql", "Shopify Storefront GraphQL", "E-commerce / CMS"),
    ("skills-sh/benjaminsehl/liquid-skills/liquid-theme-standards", "Liquid theme standards", "E-commerce / CMS"),
    ("skills-sh/benjaminsehl/liquid-skills/liquid-theme-a11y", "Liquid theme a11y", "E-commerce / CMS"),
    ("skills-sh/wordpress/agent-skills/blueprint", "WordPress blueprint (oficial)", "E-commerce / CMS"),
    ("skills-sh/automattic/agent-skills/wordpress-router", "WordPress router (Automattic)", "E-commerce / CMS"),
    ("skills-sh/maxnorm/magento2-agent-skills/magento-frontend-developer", "Magento frontend", "E-commerce / CMS"),
    ("skills-sh/jeffallan/claude-skills/laravel-specialist", "Laravel specialist", "E-commerce / CMS"),
]


def pack_by_domain() -> dict[str, list[tuple[str, str]]]:
    """Devuelve {dominio: [(id, label), …]} preservando el orden."""
    out: dict[str, list[tuple[str, str]]] = {}
    for sid, label, domain in WEB_SKILL_PACK:
        out.setdefault(domain, []).append((sid, label))
    return out


def all_ids() -> list[str]:
    return [sid for sid, _, _ in WEB_SKILL_PACK]
