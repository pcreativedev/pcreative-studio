"""
Definiciones de stacks soportados.

Cada stack tiene:
  - name        : Nombre legible (para la GUI)
  - category    : Frontend / Full-stack / CMS
  - language    : Lenguaje principal
  - scaffold    : Lista de comandos shell que crean el proyecto. Se ejecutan
                  dentro de la carpeta del proyecto (que YA está creada y
                  estamos `cd` dentro). Pueden ser interactivos.
  - min_version : Versión mínima segura (string informativo) — para alertar
                  si en el futuro hay que actualizar.
  - skills      : Lista de skills sugeridas (autoskills las redetectará al
                  ejecutar pero esta lista guía).
  - notes       : Notas que se inyectarán en CLAUDE.md / AGENTS.md.
"""

STACKS = {
    "none": {
        "name": "(Sin stack — decidir con el agente)",
        "category": "Sin definir",
        "language": "—",
        "scaffold": [],
        "min_version": "—",
        "skills": [],
        "notes": "No se ejecuta scaffolding. El agente debe analizar la referencia (si la hay) y los MDs de mercado, y proponer el stack óptimo antes de empezar.",
    },
    "nextjs-tailwind": {
        "name": "Next.js + Tailwind",
        "category": "Web · Frontend",
        "language": "TypeScript",
        "scaffold": [
            'npx --yes create-next-app@latest . '
            '--ts --tailwind --eslint --app --src-dir --import-alias "@/*" --no-turbopack --use-npm',
        ],
        "min_version": "next@^15",
        "skills": ["anthropics/skills/frontend-design", "vercel/skills/nextjs-best-practices"],
        "notes": "Next.js App Router con TS, Tailwind, ESLint, src/ y alias @/*. Ideal para landings, SaaS y dashboards.",
    },
    "astro-tailwind": {
        "name": "Astro + Tailwind",
        "category": "Web · Frontend",
        "language": "TypeScript",
        "scaffold": [
            'npm create astro@latest . -- --template minimal --typescript strict --install --no-git --yes',
            'npx astro add tailwind --yes',
        ],
        "min_version": "astro@>=5.17.2 (CVE-2026-25545 fix)",
        "skills": ["anthropics/skills/frontend-design"],
        "notes": "Astro >= 5.17.2 (parches SSRF). Ideal para blogs, marketing, sitios estáticos rápidos. Soporta islands con React/Vue si las añades luego.",
    },
    "wordpress-block": {
        "name": "WordPress (Block Theme)",
        "category": "CMS · WordPress",
        "language": "PHP",
        "scaffold": [
            # ── 1. style.css del theme ───────────────────────────────
            'cat > style.css <<\'THEMEFORGE_EOF\'\n'
            '/*\n'
            'Theme Name: __PROJECT__\n'
            'Description: Block theme generado por ThemeForge.\n'
            'Version: 0.1.0\n'
            'Text Domain: __SLUG__\n'
            'License: GPLv2 or later\n'
            'Requires at least: 6.7\n'
            'Requires PHP: 8.0\n'
            '*/\n'
            'THEMEFORGE_EOF',
            # ── 2. theme.json mínimo válido ──────────────────────────
            'cat > theme.json <<\'THEMEFORGE_EOF\'\n'
            '{\n'
            '  "$schema": "https://schemas.wp.org/trunk/theme.json",\n'
            '  "version": 3,\n'
            '  "settings": {\n'
            '    "appearanceTools": true,\n'
            '    "color": { "palette": [] },\n'
            '    "typography": { "fluid": true, "fontFamilies": [] }\n'
            '  },\n'
            '  "styles": {}\n'
            '}\n'
            'THEMEFORGE_EOF',
            # ── 3. estructura de carpetas ────────────────────────────
            "mkdir -p templates parts patterns assets",
            # ── 4. template index mínimo ─────────────────────────────
            'cat > templates/index.html <<\'THEMEFORGE_EOF\'\n'
            '<!-- wp:template-part {"slug":"header","tagName":"header"} /-->\n'
            '<!-- wp:group {"tagName":"main","layout":{"type":"constrained"}} -->\n'
            '<main class="wp-block-group"><!-- wp:post-content /--></main>\n'
            '<!-- /wp:group -->\n'
            '<!-- wp:template-part {"slug":"footer","tagName":"footer"} /-->\n'
            'THEMEFORGE_EOF',
        ],
        "min_version": "WordPress 6.7+ / PHP 8.0",
        "skills": ["wordpress/skills/block-theme-development"],
        "ux_pack": "fse",
        "notes": "Block theme moderno (theme.json v3 + FSE). Pack UX «FSE Pro»: ThemeForge auto-instala GenerateBlocks, Spectra, ACF, Pods y Royal MCP (todos gratis). Premium opcionales (GenerateBlocks Pro, ACF Pro, Motion.page) si los declaras en ~/.config/themeforge/wp_packs.json (gitignored). El agente opera WP con wp-cli vía ./wp.",
    },
    "wordpress-bricks": {
        "name": "WordPress (Bricks Child Theme)",
        "category": "CMS · WordPress",
        "language": "PHP",
        "scaffold": [
            # ── 1. style.css del child theme (declara Template: bricks) ──
            'cat > style.css <<\'THEMEFORGE_EOF\'\n'
            '/*\n'
            'Theme Name: __PROJECT__ (Bricks child)\n'
            'Template: bricks\n'
            'Description: Child theme de Bricks Builder generado por ThemeForge.\n'
            'Version: 0.1.0\n'
            'Text Domain: __SLUG__\n'
            'License: GPLv2 or later\n'
            'Requires at least: 6.7\n'
            'Requires PHP: 8.0\n'
            '*/\n'
            'THEMEFORGE_EOF',
            # ── 2. functions.php (enqueue del child + hook bootstrap) ─
            'cat > functions.php <<\'THEMEFORGE_EOF\'\n'
            '<?php\n'
            "if (!defined('ABSPATH')) { exit; }\n"
            '\n'
            "add_action('wp_enqueue_scripts', function () {\n"
            "    wp_enqueue_style('__SLUG___parent', get_template_directory_uri() . '/style.css');\n"
            "    wp_enqueue_style('__SLUG___child', get_stylesheet_uri(), ['__SLUG___parent'], '0.1.0');\n"
            "});\n"
            '\n'
            "// Hooks del child theme: añadir aquí filtros/acciones específicos del proyecto.\n"
            'THEMEFORGE_EOF',
            # ── 3. estructura de carpetas ────────────────────────────
            "mkdir -p assets/css assets/js assets/images "
            "bricks-templates/{header,footer,single,archive,page,patterns} "
            "includes",
            # ── 4. README con el flujo Bricks ─────────────────────────
            'cat > README.md <<\'THEMEFORGE_EOF\'\n'
            '# __PROJECT__ — Child theme de Bricks\n'
            '\n'
            'Stack: **Bricks Builder + Bricksforge + JetEngine + Motion.page** + Royal MCP.\n'
            '\n'
            '## Flujo de trabajo\n'
            '1. **Bricks (parent theme)** se instala automáticamente si declaras\n'
            '   `wp_packs.json` con `bricks_theme.zip`; si no, súbelo a mano a\n'
            '   Apariencia → Temas → Subir.\n'
            '2. **Este child theme** se activa solo cuando el parent está presente.\n'
            '3. Diseña con Bricks en `/wp-admin/` (autologueado). Cada template\n'
            '   (header / footer / single / archive / page) se **exporta como JSON**\n'
            '   vía *Bricks → Templates → Export* y se commitea en `bricks-templates/`.\n'
            '4. CSS / JS customizado va en `assets/` y se enqueue desde `functions.php`.\n'
            '5. Patrones reutilizables / Global Classes se exportan también a JSON\n'
            '   y entran en `bricks-templates/patterns/`.\n'
            '\n'
            '## Por qué child theme y no theme suelto\n'
            'Los templates de Bricks viven en BD (no en archivos), así que el\n'
            'deliverable son los **JSON exportados** + el child theme con tu CSS/PHP.\n'
            'El comprador instala Bricks, importa los JSON, activa el child y queda\n'
            'idéntico a la demo.\n'
            'THEMEFORGE_EOF',
        ],
        "min_version": "WordPress 6.7+ / PHP 8.0 / Bricks Builder (licencia aparte)",
        "skills": ["wordpress/skills/block-theme-development"],
        "ux_pack": "bricks",
        "notes": "Child theme de Bricks Builder. Pack UX «Bricks»: ThemeForge auto-instala los gratis (GreenShift, ACF, Pods, Royal MCP). Premium (Bricks parent theme, Bricksforge, JetEngine, Novamira Pro, Motion.page) requieren licencia y se autoinstalan si los declaras en ~/.config/themeforge/wp_packs.json (gitignored, NUNCA al repo). Sin la licencia de Bricks, sube bricks.zip a mano y activa el child theme luego.",
    },
    "wordpress-elementor": {
        "name": "WordPress (Elementor Child Theme)",
        "category": "CMS · WordPress",
        "language": "PHP",
        "scaffold": [
            'cat > style.css <<\'THEMEFORGE_EOF\'\n'
            '/*\n'
            'Theme Name: __PROJECT__ (Elementor child)\n'
            'Template: hello-elementor\n'
            'Description: Child theme de Hello Elementor + Elementor (Pro opcional), generado por ThemeForge.\n'
            'Version: 0.1.0\n'
            'Text Domain: __SLUG__\n'
            'License: GPLv2 or later\n'
            'Requires at least: 6.7\n'
            'Requires PHP: 8.0\n'
            '*/\n'
            'THEMEFORGE_EOF',
            'cat > functions.php <<\'THEMEFORGE_EOF\'\n'
            '<?php\n'
            "if (!defined('ABSPATH')) { exit; }\n"
            '\n'
            "add_action('wp_enqueue_scripts', function () {\n"
            "    wp_enqueue_style('__SLUG___parent', get_template_directory_uri() . '/style.css');\n"
            "    wp_enqueue_style('__SLUG___child', get_stylesheet_uri(), ['__SLUG___parent'], '0.1.0');\n"
            "}, 20);\n"
            'THEMEFORGE_EOF',
            "mkdir -p assets/css assets/js assets/images "
            "elementor-templates/header elementor-templates/footer "
            "elementor-templates/single elementor-templates/archive "
            "elementor-templates/page elementor-templates/popups "
            "elementor-templates/kits includes",
            'cat > README.md <<\'THEMEFORGE_EOF\'\n'
            '# __PROJECT__ — Child theme de Elementor (Hello Elementor parent)\n'
            '\n'
            'Stack: Elementor + Hello Elementor (free) o Elementor Pro (paid).\n'
            'Plugins típicos: ACF, Pods, Essential Addons, JetEngine (paid), Royal MCP, Novamira Pro (paid).\n'
            '\n'
            '## Flujo\n'
            '1. ThemeForge instala Hello Elementor + Elementor free + Essential Addons Lite + ACF + Pods + Royal MCP.\n'
            '   Elementor Pro y JetEngine via `wp_packs.json` si los tienes.\n'
            '2. Diseña con Elementor en /wp-admin/ (autologueado).\n'
            '3. Templates (header/footer/single/archive/page/popup) + Kits (paletas, tipografía global) se exportan\n'
            '   vía Elementor → Templates → Export y se commitean en `elementor-templates/`.\n'
            '4. CSS/JS/hooks del child van en `assets/` + `functions.php`.\n'
            'THEMEFORGE_EOF',
        ],
        "min_version": "WordPress 6.7+ / PHP 8.0 / Elementor",
        "skills": ["wordpress/skills/block-theme-development"],
        "ux_pack": "elementor",
        "notes": "Child theme de Hello Elementor + Elementor. Pack UX «Elementor»: free auto-install (Hello Elementor + Elementor free + Essential Addons Lite + ACF + Pods + Royal MCP). Premium (Elementor Pro, JetEngine, Motion.page, Novamira Pro) via wp_packs.json.",
    },
    "wordpress-divi": {
        "name": "WordPress (Divi Child Theme)",
        "category": "CMS · WordPress",
        "language": "PHP",
        "scaffold": [
            'cat > style.css <<\'THEMEFORGE_EOF\'\n'
            '/*\n'
            'Theme Name: __PROJECT__ (Divi child)\n'
            'Template: Divi\n'
            'Description: Child theme de Divi (Elegant Themes) generado por ThemeForge.\n'
            'Version: 0.1.0\n'
            'Text Domain: __SLUG__\n'
            'License: GPLv2 or later\n'
            'Requires at least: 6.7\n'
            'Requires PHP: 8.0\n'
            '*/\n'
            'THEMEFORGE_EOF',
            'cat > functions.php <<\'THEMEFORGE_EOF\'\n'
            '<?php\n'
            "if (!defined('ABSPATH')) { exit; }\n"
            '\n'
            "add_action('wp_enqueue_scripts', function () {\n"
            "    wp_enqueue_style('__SLUG___parent', get_template_directory_uri() . '/style.css');\n"
            "    wp_enqueue_style('__SLUG___child', get_stylesheet_uri(), ['__SLUG___parent'], '0.1.0');\n"
            "}, 20);\n"
            'THEMEFORGE_EOF',
            "mkdir -p assets/css assets/js assets/images "
            "divi-layouts/header divi-layouts/footer divi-layouts/single "
            "divi-layouts/archive divi-layouts/page divi-layouts/modules "
            "includes",
            'cat > README.md <<\'THEMEFORGE_EOF\'\n'
            '# __PROJECT__ — Child theme de Divi\n'
            '\n'
            'Stack: Divi 5 (Elegant Themes, paid). Plugins típicos: ACF, Pods, Royal MCP, Novamira Pro (paid).\n'
            '\n'
            '## Flujo\n'
            '1. Declara el ZIP de Divi en wp_packs.json > divi > theme para auto-instalación.\n'
            '2. Diseña con Divi Builder. Exporta layouts vía Divi → Library → Export a JSON.\n'
            '3. Commitea los JSON en `divi-layouts/`.\n'
            'THEMEFORGE_EOF',
        ],
        "min_version": "WordPress 6.7+ / PHP 8.0 / Divi (licencia aparte)",
        "skills": ["wordpress/skills/block-theme-development"],
        "ux_pack": "divi",
        "notes": "Child theme de Divi. Pack UX «Divi»: free auto-install (ACF + Pods + Royal MCP). Premium (Divi parent theme, Novamira Pro) via wp_packs.json.",
    },
    "wordpress-breakdance": {
        "name": "WordPress (Breakdance Theme)",
        "category": "CMS · WordPress",
        "language": "PHP",
        "scaffold": [
            'cat > style.css <<\'THEMEFORGE_EOF\'\n'
            '/*\n'
            'Theme Name: __PROJECT__ (Breakdance child)\n'
            'Template: kadence\n'
            'Description: Child theme base con Breakdance plugin (render engine).\n'
            'Version: 0.1.0\n'
            'Text Domain: __SLUG__\n'
            'License: GPLv2 or later\n'
            'Requires at least: 6.7\n'
            'Requires PHP: 8.0\n'
            '*/\n'
            'THEMEFORGE_EOF',
            'cat > functions.php <<\'THEMEFORGE_EOF\'\n'
            '<?php\n'
            "if (!defined('ABSPATH')) { exit; }\n"
            '\n'
            "add_action('wp_enqueue_scripts', function () {\n"
            "    wp_enqueue_style('__SLUG___parent', get_template_directory_uri() . '/style.css');\n"
            "    wp_enqueue_style('__SLUG___child', get_stylesheet_uri(), ['__SLUG___parent'], '0.1.0');\n"
            "}, 20);\n"
            'THEMEFORGE_EOF',
            "mkdir -p assets/css assets/js assets/images "
            "breakdance-templates/global breakdance-templates/headers "
            "breakdance-templates/footers breakdance-templates/popups "
            "breakdance-templates/singles breakdance-templates/archives "
            "includes",
            'cat > README.md <<\'THEMEFORGE_EOF\'\n'
            '# __PROJECT__ — Breakdance template (child de Kadence)\n'
            '\n'
            'Stack: Breakdance (plugin, free + Pro opcional) sobre Kadence como theme base.\n'
            'Breakdance reemplaza el render del front; el theme base solo sirve para wp-admin y fallback.\n'
            '\n'
            '## Flujo\n'
            '1. ThemeForge instala Kadence + Breakdance free + ACF + Pods + Royal MCP.\n'
            '2. Breakdance Pro y plugins paid (en wp_packs.json > breakdance > plugins).\n'
            '3. Diseña con Breakdance. Exporta global settings / headers / footers / popups\n'
            '   vía Breakdance → Templates → Export y commitea en `breakdance-templates/`.\n'
            'THEMEFORGE_EOF',
        ],
        "min_version": "WordPress 6.7+ / PHP 8.0 / Breakdance",
        "skills": ["wordpress/skills/block-theme-development"],
        "ux_pack": "breakdance",
        "notes": "Child theme de Kadence con Breakdance como engine de render. Pack UX «Breakdance»: free auto-install (Kadence + Breakdance + ACF + Pods + Royal MCP). Breakdance Pro y plugins paid via wp_packs.json.",
    },
    "wordpress-plugin": {
        "name": "WordPress Plugin (PHP 8.2)",
        "category": "CMS · WordPress",
        "language": "PHP + JS",
        "scaffold": [
            # ── 1. estructura de carpetas ────────────────────────────
            "mkdir -p src/{Admin,Frontend,Core,Database} assets/{js,css,images} "
            "templates languages tests/{Unit,Integration,E2E} build",
            # ── 2. archivo principal del plugin con header WP ────────
            'cat > __SLUG__.php <<\'THEMEFORGE_EOF\'\n'
            '<?php\n'
            '/**\n'
            ' * Plugin Name: __PROJECT__\n'
            ' * Description: Plugin generado por ThemeForge.\n'
            ' * Version: 0.1.0\n'
            ' * Author: ThemeForge\n'
            ' * Text Domain: __SLUG__\n'
            ' * Requires at least: 6.7\n'
            ' * Requires PHP: 8.2\n'
            ' * License: GPLv2 or later\n'
            ' */\n'
            '\n'
            "if (!defined('ABSPATH')) { exit; }\n"
            '\n'
            "define('__SLUG___VERSION', '0.1.0');\n"
            "define('__SLUG___FILE', __FILE__);\n"
            "define('__SLUG___DIR', plugin_dir_path(__FILE__));\n"
            "define('__SLUG___URL', plugin_dir_url(__FILE__));\n"
            '\n'
            "if (file_exists(__DIR__ . '/vendor/autoload.php')) {\n"
            "    require_once __DIR__ . '/vendor/autoload.php';\n"
            "}\n"
            '\n'
            "// Bootstrap (placeholder — el agente IA implementará el core).\n"
            "add_action('plugins_loaded', function () {\n"
            "    // TODO: cargar el bootstrap real desde src/Core/Plugin.php\n"
            "});\n"
            'THEMEFORGE_EOF',
            # ── 3. composer.json con PSR-4 autoload ──────────────────
            'cat > composer.json <<\'THEMEFORGE_EOF\'\n'
            '{\n'
            '  "name": "themeforge/__SLUG__",\n'
            '  "description": "__PROJECT__ — WordPress plugin",\n'
            '  "type": "wordpress-plugin",\n'
            '  "license": "GPL-2.0-or-later",\n'
            '  "require": {\n'
            '    "php": "^8.2",\n'
            '    "symfony/event-dispatcher": "^7.0",\n'
            '    "illuminate/database": "^11.0"\n'
            '  },\n'
            '  "require-dev": {\n'
            '    "phpunit/phpunit": "^11.0",\n'
            '    "pestphp/pest": "^3.0",\n'
            '    "wp-coding-standards/wpcs": "^3.0"\n'
            '  },\n'
            '  "autoload": {\n'
            '    "psr-4": { "Themeforge\\\\__PASCAL__\\\\": "src/" }\n'
            '  },\n'
            '  "autoload-dev": {\n'
            '    "psr-4": { "Themeforge\\\\__PASCAL__\\\\Tests\\\\": "tests/" }\n'
            '  },\n'
            '  "config": { "allow-plugins": { "pestphp/pest-plugin": true } }\n'
            '}\n'
            'THEMEFORGE_EOF',
            # ── 4. package.json con Vite + Vue para admin UI ─────────
            'cat > package.json <<\'THEMEFORGE_EOF\'\n'
            '{\n'
            '  "name": "__SLUG__",\n'
            '  "version": "0.1.0",\n'
            '  "private": true,\n'
            '  "type": "module",\n'
            '  "scripts": {\n'
            '    "dev": "vite",\n'
            '    "build": "vite build",\n'
            '    "test:php": "vendor/bin/pest",\n'
            '    "test:e2e": "playwright test"\n'
            '  },\n'
            '  "devDependencies": {\n'
            '    "vite": "^6.0",\n'
            '    "vue": "^3.5",\n'
            '    "@vitejs/plugin-vue": "^5.0",\n'
            '    "tailwindcss": "^4.0",\n'
            '    "@tailwindcss/vite": "^4.0",\n'
            '    "@playwright/test": "^1.50"\n'
            '  }\n'
            '}\n'
            'THEMEFORGE_EOF',
            # ── 5. vite.config.js (build a /build con manifest) ──────
            'cat > vite.config.js <<\'THEMEFORGE_EOF\'\n'
            "import { defineConfig } from 'vite';\n"
            "import vue from '@vitejs/plugin-vue';\n"
            "import tailwindcss from '@tailwindcss/vite';\n"
            '\n'
            'export default defineConfig({\n'
            '  plugins: [vue(), tailwindcss()],\n'
            '  build: {\n'
            "    outDir: 'build',\n"
            '    manifest: true,\n'
            '    emptyOutDir: true,\n'
            '    rollupOptions: {\n'
            '      input: {\n'
            "        admin: 'assets/js/admin.js',\n"
            "        public: 'assets/js/public.js',\n"
            '      },\n'
            '    },\n'
            '  },\n'
            '});\n'
            'THEMEFORGE_EOF',
            # ── 7. .gitignore ────────────────────────────────────────
            'cat > .gitignore <<\'THEMEFORGE_EOF\'\n'
            'vendor/\n'
            'node_modules/\n'
            'build/\n'
            '*.log\n'
            '/.env\n'
            'tests/_output/\n'
            'tests/_data/dumps/\n'
            '/coverage/\n'
            'THEMEFORGE_EOF',
            # ── 8. README con instrucciones ──────────────────────────
            'cat > README.md <<\'THEMEFORGE_EOF\'\n'
            '# __PROJECT__\n\n'
            'WordPress plugin generado por ThemeForge.\n\n'
            '## Stack\n\n'
            '- PHP 8.2 + Composer (autoload PSR-4 `Themeforge\\\\__PASCAL__\\\\`)\n'
            '- WordPress 6.7+ (entorno Docker levantado por ThemeForge — ver WORDPRESS-DEV.md)\n'
            '- Admin UI: Vue 3.5 + Vite 6 + Tailwind 4\n'
            '- Tests: Pest + Playwright E2E\n\n'
            '## Arrancar\n\n'
            '```bash\n'
            'composer install\n'
            'npm install\n'
            '# WordPress lo levanta ThemeForge automáticamente (ver WORDPRESS-DEV.md)\n'
            'npm run dev             # Vite HMR para admin UI\n'
            '```\n\n'
            '## WordPress de desarrollo\n\n'
            'ThemeForge levanta WordPress en Docker automáticamente y monta este plugin.\n'
            'URL, credenciales y el helper `./wp` (wp-cli): ver `WORDPRESS-DEV.md`.\n\n'
            '## Tests\n\n'
            '```bash\n'
            'npm run test:php       # Pest (unitarios + integración)\n'
            'npm run test:e2e       # Playwright (end-to-end)\n'
            '```\n\n'
            '## Build para distribución\n\n'
            '```bash\n'
            'npm run build          # genera build/ con manifest\n'
            'composer install --no-dev --optimize-autoloader\n'
            '```\n\n'
            'Luego empaqueta en zip excluyendo `node_modules/`, `tests/`, `build/`.\n'
            'THEMEFORGE_EOF',
            # ── 9. composer install (descarga deps, vendor/) ─────────
            'composer install --no-interaction --quiet 2>&1 | tail -5 '
            '|| echo "(composer install falló — instálalo a mano)"',
            # ── npm install (Vite + Vue + Tailwind) ──
            'npm install --silent 2>&1 | tail -5 '
            '|| echo "(npm install falló — instálalo a mano)"',
        ],
        "min_version": "WordPress 6.7 / PHP 8.2",
        "skills": [],
        "notes": (
            "Plugin WP. El entorno WordPress (Docker) lo levanta ThemeForge "
            "automáticamente al crear el proyecto y monta el plugin (ver WORDPRESS-DEV.md). "
            "El agente opera WP con wp-cli vía ./wp. "
            "Canal de venta: CodeCanyon, Freemius, web propia. "
            "REQUISITOS: Docker corriendo + Node 18+ + Composer 2.x."
        ),
    },
    "shopify-liquid": {
        "name": "Shopify Liquid (Online Store 2.0 + Dawn)",
        "category": "CMS · Shopify",
        "language": "Liquid + JS",
        "scaffold": [
            # Dawn = el theme oficial de Shopify (MIT). Es la base que usa el
            # 80%+ del mercado real — partir de aquí ahorra meses y el código
            # ya cumple Theme Store Quality Guidelines de salida. El agente lo
            # personaliza/extiende; NO se copia tal cual.
            "npx --yes @shopify/cli@latest theme init . --clone-url https://github.com/Shopify/dawn",
            # ── package.json: prettier + liquid plugin + scripts útiles
            'cat > package.json <<\'THEMEFORGE_EOF\'\n'
            '{\n'
            '  "name": "__SLUG__",\n'
            '  "version": "0.1.0",\n'
            '  "private": true,\n'
            '  "type": "module",\n'
            '  "scripts": {\n'
            '    "dev": "shopify theme dev",\n'
            '    "check": "shopify theme check",\n'
            '    "format": "prettier --write \\"**/*.{liquid,json,js,css}\\"",\n'
            '    "format:check": "prettier --check \\"**/*.{liquid,json,js,css}\\"",\n'
            '    "package": "shopify theme package"\n'
            '  },\n'
            '  "devDependencies": {\n'
            '    "@shopify/prettier-plugin-liquid": "^1.7.0",\n'
            '    "prettier": "^3.4.0"\n'
            '  }\n'
            '}\n'
            'THEMEFORGE_EOF',
            # ── .prettierrc.json con el plugin de Liquid
            'cat > .prettierrc.json <<\'THEMEFORGE_EOF\'\n'
            '{\n'
            '  "plugins": ["@shopify/prettier-plugin-liquid"],\n'
            '  "printWidth": 100,\n'
            '  "singleQuote": false,\n'
            '  "overrides": [\n'
            '    {\n'
            '      "files": "*.liquid",\n'
            '      "options": { "liquidSingleQuote": false, "embeddedSingleQuote": false }\n'
            '    }\n'
            '  ]\n'
            '}\n'
            'THEMEFORGE_EOF',
            # ── .theme-check.yml estricto para Theme Store
            'cat > .theme-check.yml <<\'THEMEFORGE_EOF\'\n'
            '# Theme Check config — recomendado + estricto para Theme Store.\n'
            '# Cambia thresholds o desactiva checks individuales si tu caso lo justifica.\n'
            'extends: theme-check:recommended\n'
            '\n'
            'AssetSizeJavaScript:\n'
            '  enabled: true\n'
            '  threshold_in_bytes: 16384  # 16 KB cap oficial del Theme Store\n'
            'AssetSizeCSS:\n'
            '  enabled: true\n'
            '  threshold_in_bytes: 100000\n'
            'ParserBlockingJavaScript:\n'
            '  enabled: true\n'
            'RemoteAsset:\n'
            '  enabled: true\n'
            'UnknownFilter:\n'
            '  enabled: true\n'
            'UnusedAssign:\n'
            '  enabled: true\n'
            'MissingTemplate:\n'
            '  enabled: true\n'
            'ContentForHeaderModification:\n'
            '  enabled: true\n'
            'ContentForIndexModification:\n'
            '  enabled: true\n'
            'LiquidTag:\n'
            '  enabled: true\n'
            'DeprecatedFilter:\n'
            '  enabled: true\n'
            'TemplateLength:\n'
            '  enabled: true\n'
            '  max_length: 600\n'
            'THEMEFORGE_EOF',
            # ── GitHub Actions Lighthouse CI (action oficial de Shopify)
            "mkdir -p .github/workflows",
            'cat > .github/workflows/lighthouse-ci.yml <<\'THEMEFORGE_EOF\'\n'
            '# Lighthouse CI con la action oficial de Shopify.\n'
            '# Necesitas estos secrets en el repo GitHub para que funcione:\n'
            '#   SHOPIFY_AUTH_TOKEN  — Theme Access App password (genérala en la tienda dev)\n'
            '#   SHOPIFY_STORE       — tu-tienda.myshopify.com\n'
            '#   SHOPIFY_STORE_PWD   — password del storefront si la tienda está protegida\n'
            'name: Lighthouse CI\n'
            '\n'
            'on:\n'
            '  push:\n'
            '    branches: [main]\n'
            '  pull_request:\n'
            '    branches: [main]\n'
            '\n'
            'jobs:\n'
            '  lighthouse:\n'
            '    runs-on: ubuntu-latest\n'
            '    steps:\n'
            '      - uses: actions/checkout@v4\n'
            '      - name: Shopify Lighthouse CI\n'
            '        uses: shopify/lighthouse-ci-action@v1\n'
            '        with:\n'
            '          access_token: ${{ secrets.SHOPIFY_AUTH_TOKEN }}\n'
            '          store: ${{ secrets.SHOPIFY_STORE }}\n'
            '          password: ${{ secrets.SHOPIFY_STORE_PWD }}\n'
            'THEMEFORGE_EOF',
            # ── .mcp.json: Shopify Dev MCP (admin/storefront/checkout APIs
            #    + Polaris) + Storefront MCP (placeholder con tu shop).
            #    Polaris ya viene integrado en @shopify/dev-mcp — sin flag.
            'cat > .mcp.json <<\'THEMEFORGE_EOF\'\n'
            '{\n'
            '  "mcpServers": {\n'
            '    "shopify-dev": {\n'
            '      "command": "npx",\n'
            '      "args": ["-y", "@shopify/dev-mcp@latest"]\n'
            '    },\n'
            '    "shopify-storefront": {\n'
            '      "type": "http",\n'
            '      "url": "https://YOUR-SHOP.myshopify.com/api/mcp",\n'
            '      "_doc": "Storefront MCP zero-auth. Sustituye YOUR-SHOP por tu dominio. Tools: get_cart, update_cart, search_shop_policies_and_faqs."\n'
            '    },\n'
            '    "shopify-storefront-catalog": {\n'
            '      "type": "http",\n'
            '      "url": "https://YOUR-SHOP.myshopify.com/api/ucp/mcp",\n'
            '      "_doc": "Storefront UCP (Unified Commerce Protocol) — catálogo con búsqueda natural. Tools: search_catalog, lookup_catalog, get_product."\n'
            '    }\n'
            '  }\n'
            '}\n'
            'THEMEFORGE_EOF',
            # ── README rápido del MCP + comandos CLI ─────────────────
            'cat > README-MCP.md <<\'THEMEFORGE_EOF\'\n'
            '# Shopify Dev MCP + Shopify CLI\n\n'
            'Este proyecto incluye `.mcp.json` configurado con **Shopify Dev MCP**,\n'
            'el servidor MCP oficial de Shopify (`@shopify/dev-mcp`).\n\n'
            '## Qué da el MCP\n\n'
            'Acceso programático a los recursos de desarrollo de Shopify desde tu\n'
            'agente AI (Claude Code, Codex, Cursor):\n\n'
            '- Docs y referencia de la Storefront API, Admin API, Theme API.\n'
            '- Schemas GraphQL.\n'
            '- Tipos Liquid (objects, filters, tags).\n'
            '- Esquemas de sections y blocks.\n\n'
            'Corre localmente vía STDIO, **sin autenticación**. La primera vez\n'
            'que un agente intente usarlo, `npx` descargará el paquete.\n\n'
            '## Login en tu tienda Shopify\n\n'
            '```bash\n'
            'shopify login                                # OAuth en navegador\n'
            'shopify login --store=tu-tienda.myshopify.com\n'
            '```\n\n'
            '## Cheat-sheet `shopify theme`\n\n'
            '| Comando | Para qué |\n'
            '|---|---|\n'
            '| `shopify theme dev`              | Dev server local en http://127.0.0.1:9292 con hot reload |\n'
            '| `shopify theme dev --store=X`    | Forzar tienda concreta |\n'
            '| `shopify theme pull`             | Bajar archivos del tema remoto |\n'
            '| `shopify theme push`             | Subir archivos locales al tema remoto |\n'
            '| `shopify theme push --unpublished --json` | Crear tema nuevo como borrador |\n'
            '| `shopify theme list`             | Listar temas de la tienda con sus IDs |\n'
            '| `shopify theme check`            | Linter oficial (errores y best practices) |\n'
            '| `shopify theme package`          | Generar el `.zip` para subir a ThemeForest |\n'
            '| `shopify theme publish <id>`     | Publicar un tema (lo hace activo) |\n'
            '| `shopify theme delete <id>`      | Borrar un tema de la tienda |\n\n'
            '## Workflow recomendado para ThemeForest\n\n'
            '1. `shopify theme dev`            → desarrollo local.\n'
            '2. `shopify theme check`          → arreglar todos los errores.\n'
            '3. `shopify theme push --unpublished --json` → subir como borrador.\n'
            '4. Probar en preview de la tienda dev.\n'
            '5. `shopify theme package`        → generar el ZIP de entrega.\n'
            '6. Subir el ZIP a ThemeForest.\n\n'
            '## Necesario antes\n\n'
            '- Cuenta Shopify Partners (gratis).\n'
            '- Tienda de desarrollo asociada (Partners → Stores → Add store).\n'
            'THEMEFORGE_EOF',
        ],
        "min_version": "Online Store 2.0 / Shopify CLI 3.x / Dawn",
        "skills": ["shopify/skills/theme-development"],
        "ux_pack": "shopify-liquid",
        "notes": "Online Store 2.0 sobre Dawn (theme oficial Shopify, MIT) como base. Incluye .mcp.json con (1) Shopify Dev MCP — admin/storefront/checkout API docs + Polaris components, (2) Storefront MCP (zero-auth, sustituye YOUR-SHOP), (3) Storefront UCP MCP (catálogo + búsqueda natural). Necesitas tienda dev en Shopify Partners (gratis) para `shopify theme dev`.",
    },
    "shopify-hydrogen": {
        "name": "Shopify Hydrogen (Remix + React)",
        "category": "CMS · Shopify",
        "language": "TypeScript + React",
        "scaffold": [
            # Scaffold oficial de Shopify para Hydrogen (template skeleton).
            # Si no se puede ejecutar el create no-interactivo, el agente
            # debe correrlo a mano. --quickstart bypasses la mayoría de
            # prompts; --no-install evita yarn/npm install al arrancar.
            "npx --yes @shopify/create-hydrogen@latest . --quickstart --no-install || "
            "(echo 'Fallback: ejecuta a mano `npm create @shopify/hydrogen@latest .` y elige las opciones.' && exit 0)",
            # ── .mcp.json: mismo set que Liquid + el storefront URL hint ──
            'cat > .mcp.json <<\'THEMEFORGE_EOF\'\n'
            '{\n'
            '  "mcpServers": {\n'
            '    "shopify-dev": {\n'
            '      "command": "npx",\n'
            '      "args": ["-y", "@shopify/dev-mcp@latest"]\n'
            '    },\n'
            '    "shopify-storefront": {\n'
            '      "type": "http",\n'
            '      "url": "https://YOUR-SHOP.myshopify.com/api/mcp",\n'
            '      "_doc": "Storefront MCP zero-auth. Sustituye YOUR-SHOP por tu dominio."\n'
            '    },\n'
            '    "shopify-storefront-catalog": {\n'
            '      "type": "http",\n'
            '      "url": "https://YOUR-SHOP.myshopify.com/api/ucp/mcp",\n'
            '      "_doc": "Storefront UCP — catálogo con búsqueda natural."\n'
            '    }\n'
            '  }\n'
            '}\n'
            'THEMEFORGE_EOF',
            # README-HYDROGEN.md con CLI + workflow
            'cat > README-HYDROGEN.md <<\'THEMEFORGE_EOF\'\n'
            '# Hydrogen (Remix + React 19 + Oxygen)\n\n'
            'Storefront headless de Shopify para tiendas con catálogos\n'
            'grandes (500+ SKUs), multi-mercado o necesidades visuales\n'
            'que el theme Liquid no cubre.\n\n'
            '## Cuándo Hydrogen vs Liquid\n\n'
            '| Necesidad | Liquid (OS 2.0) | Hydrogen |\n'
            '|---|---|---|\n'
            '| Catálogo < 500 SKU | ✅ | ❌ overkill |\n'
            '| Catálogo 500-5k SKU + filtros complejos | ⚠️ | ✅ |\n'
            '| Multi-currency / multi-language fuerte | ⚠️ | ✅ |\n'
            '| Build time (semanas) | 3-8 | 12-20 |\n'
            '| Lighthouse out-of-box | ~60% pasan CWV | controlable 95+ |\n'
            '| Curva | media | alta |\n\n'
            '## Stack\n\n'
            '- **Remix v3 / React Router v7** (server-driven UI).\n'
            '- **Oxygen** (deploy edge gratuito de Shopify).\n'
            '- **Tailwind v4** o CSS Modules a elegir.\n'
            '- **GraphQL** contra Storefront API (sin REST).\n'
            '- **Optimistic UI** + nested routing.\n\n'
            '## Comandos\n\n'
            '```bash\n'
            'npm install                         # primera vez\n'
            'npm run dev                         # http://localhost:3000\n'
            'npm run build                       # build edge-ready\n'
            'npm run preview                     # preview build local\n'
            'npx shopify hydrogen deploy         # deploy a Oxygen\n'
            'npx shopify hydrogen link           # vincular a tienda\n'
            '```\n\n'
            '## MCPs activos\n\n'
            '- `shopify-dev` — schemas GraphQL Admin/Storefront, Polaris components, Liquid docs (útil para apps).\n'
            '- `shopify-storefront` — cart + policies + FAQ via lenguaje natural.\n'
            '- `shopify-storefront-catalog` — búsqueda en catálogo con NL.\n\n'
            'Sustituye `YOUR-SHOP` en `.mcp.json` por tu dominio (formato `tu-tienda`,\n'
            'no incluye `.myshopify.com`).\n\n'
            '## Vender en ThemeForest / Theme Store\n\n'
            'ThemeForest acepta Hydrogen como categoría aparte (mayor margen,\n'
            'menos competencia). El Theme Store de Shopify aún no acepta\n'
            'Hydrogen como tema oficial (sigue siendo Liquid), pero sí como\n'
            'app/template en marketplaces de partners.\n'
            'THEMEFORGE_EOF',
        ],
        "min_version": "Hydrogen 2026.x / React 19 / Node 22+",
        "skills": ["shopify/skills/theme-development"],
        "ux_pack": "shopify-hydrogen",
        "notes": "Storefront headless con Remix + React + Oxygen. Para catálogos grandes, multi-mercado y diseños premium. Mismo set de MCPs que Liquid. Requiere Node 22+. Deploy a Oxygen (edge gratuito de Shopify) o cualquier provider Node.",
    },
    "shopify-polaris-app": {
        "name": "Shopify App (Polaris + App Bridge + Remix)",
        "category": "CMS · Shopify",
        "language": "TypeScript + React",
        "scaffold": [
            # Scaffold oficial de apps Shopify (Remix template).
            # Si no se puede no-interactivo, el agente lo corre a mano.
            "npx --yes @shopify/create-app@latest --template remix --name __SLUG__ --no-install || "
            "(echo 'Fallback: ejecuta a mano `npm init @shopify/app@latest` y elige template Remix.' && exit 0)",
            # .mcp.json — Shopify Dev MCP (incluye Polaris) + storefront opcionales
            'cat > .mcp.json <<\'THEMEFORGE_EOF\'\n'
            '{\n'
            '  "mcpServers": {\n'
            '    "shopify-dev": {\n'
            '      "command": "npx",\n'
            '      "args": ["-y", "@shopify/dev-mcp@latest"],\n'
            '      "_doc": "Admin/Storefront/Checkout API + Polaris components."\n'
            '    }\n'
            '  }\n'
            '}\n'
            'THEMEFORGE_EOF',
            'cat > README-APP.md <<\'THEMEFORGE_EOF\'\n'
            '# Shopify App (Polaris + App Bridge)\n\n'
            'App embebida en el Admin de Shopify, construida con el template\n'
            'oficial **Remix** de Shopify CLI. Incluye Polaris (design system),\n'
            'App Bridge (puente nativo entre app y Admin), OAuth, sesiones,\n'
            'webhooks y GraphQL contra Admin API.\n\n'
            '## Stack\n\n'
            '- **Remix v3** — routing + loaders/actions.\n'
            '- **Polaris** (`@shopify/polaris` + `@shopify/polaris-icons`) — Cards, DataTable,\n'
            '  IndexTable, ResourcePicker, Modal, Toast, Banner, Form, etc.\n'
            '- **App Bridge 4** (`@shopify/app-bridge-react`) — navegación, contextual\n'
            '  save bar, resource picker, scopes API, billing UI.\n'
            '- **Shopify CLI 3** — `shopify app dev` con tunnel automático (cloudflared).\n'
            '- **Prisma + SQLite** (dev) / PostgreSQL (prod) — sesiones y datos.\n'
            '- **Shopify Functions** (opcional) — extensiones de checkout / pricing /\n'
            '  delivery / discount con Rust o Wasm-JS.\n\n'
            '## Comandos\n\n'
            '```bash\n'
            'npm install                          # primera vez\n'
            'npm run dev                          # shopify app dev con tunnel\n'
            'npm run build                        # build de la app\n'
            'npm run deploy                       # publica versión nueva\n'
            'shopify app generate extension       # añadir extensiones (theme, checkout, discount...)\n'
            'shopify app function build           # build de Shopify Function\n'
            '```\n\n'
            '## Tipos de extensiones que puedes generar\n\n'
            '- **Theme app extension** — bloques que el merchant añade a su theme.\n'
            '- **Checkout UI extension** — UI custom en checkout (Plus).\n'
            '- **Customer account UI extension** — UI custom en cuenta cliente nueva.\n'
            '- **Admin block / Admin action** — extiende el Admin con bloques o acciones.\n'
            '- **Shopify Functions** — discount, payment, delivery, validation logic.\n'
            '- **Flow action / trigger** — integraciones para Shopify Flow.\n'
            '- **POS UI extension** — UI custom en Shopify POS.\n\n'
            '## Distribución\n\n'
            '- **Shopify App Store** (público, revisión Shopify, ~$99-499/mes promedios).\n'
            '- **Custom** (privada, una tienda concreta, sin store).\n'
            '- **Partner Manage Tier** (apps para clientes managed).\n\n'
            '## MCP activo\n\n'
            '`shopify-dev` incluye Polaris — el agente puede preguntar por props,\n'
            'variantes y patterns de cada componente Polaris en tiempo real.\n'
            'THEMEFORGE_EOF',
        ],
        "min_version": "Shopify CLI 3.x / Remix v3 / Polaris 13+ / Node 22+",
        "skills": ["shopify/skills/theme-development"],
        "ux_pack": "shopify-polaris-app",
        "notes": "App embebida en el Admin de Shopify con Polaris + App Bridge + Remix + Prisma. Para apps públicas en Shopify App Store, custom apps de una sola tienda, o extensiones (theme/checkout/customer-account/admin/POS/Flow/Functions). Incluye `shopify-dev` MCP con conocimiento nativo de Polaris.",
    },
    "html-tailwind": {
        "name": "HTML + Tailwind + Vite",
        "category": "Web · Static",
        "language": "HTML / JS",
        "scaffold": [
            "npm create vite@latest . -- --template vanilla-ts",
            "npm install",
            "npm install -D tailwindcss@latest @tailwindcss/vite",
        ],
        "min_version": "tailwindcss@^4",
        "skills": ["anthropics/skills/frontend-design"],
        "notes": "Vite + Vanilla TS + Tailwind v4. Para site templates HTML clásicos modernizados. Build estático listo para envato-package.",
    },
    "html-bootstrap": {
        "name": "HTML + Bootstrap 5",
        "category": "Web · Static",
        "language": "HTML / JS",
        "scaffold": [
            "npm create vite@latest . -- --template vanilla",
            "npm install",
            "npm install bootstrap@5 @popperjs/core sass",
        ],
        "min_version": "bootstrap@^5",
        "skills": [],
        "notes": "Vite + Bootstrap 5 + Sass. Para site templates corporativos clásicos.",
    },
    "react-vite-tailwind": {
        "name": "React (Vite) + Tailwind",
        "category": "Web · Frontend",
        "language": "TypeScript",
        "scaffold": [
            "npm create vite@latest . -- --template react-ts",
            "npm install",
            "npm install -D tailwindcss@latest @tailwindcss/vite",
        ],
        "min_version": "react@^19",
        "skills": ["anthropics/skills/frontend-design"],
        "notes": "React 19 + Vite + Tailwind v4. SPA, admin panels, dashboards. Sin Next.js si no necesitas SSR.",
    },
    "vue3-vite-tailwind": {
        "name": "Vue 3 (Vite) + Tailwind",
        "category": "Web · Frontend",
        "language": "TypeScript",
        "scaffold": [
            "npm create vite@latest . -- --template vue-ts",
            "npm install",
            "npm install -D tailwindcss@latest @tailwindcss/vite",
        ],
        "min_version": "vue@^3.5",
        "skills": [],
        "notes": "Vue 3 + Vite + Tailwind v4. Admin SPAs estilo Vuexy/Materio.",
    },
    "angular-tailwind": {
        "name": "Angular + Tailwind",
        "category": "Web · Frontend",
        "language": "TypeScript",
        "scaffold": [
            "npx --yes @angular/cli@latest new . --style=scss --routing=true --skip-git --skip-install --defaults",
            "npm install",
            "npm install -D tailwindcss postcss autoprefixer",
            "npx tailwindcss init",
        ],
        "min_version": "@angular/core@^19",
        "skills": [],
        "notes": "Angular 19 standalone components. Admin enterprise.",
    },
    # ════════════════════════════════════════════════════════════════
    #  STACKS MÓVILES
    # ════════════════════════════════════════════════════════════════
    "expo-rn-nativewind": {
        "name": "React Native + Expo + NativeWind",
        "category": "Móvil · Cross-platform",
        "language": "TypeScript",
        "scaffold": [
            "npx --yes create-expo-app@latest . --template blank-typescript --no-install",
            "npm install",
            "npm install nativewind tailwindcss react-native-reanimated react-native-safe-area-context",
            "npx --yes tailwindcss init",
        ],
        "min_version": "expo SDK 52+",
        "skills": [],
        "notes": "Expo SDK 52 + TypeScript + NativeWind (Tailwind para React Native). Target iOS/Android/Web. Preview con `npm run web` (puerto 8081). Build de producción con EAS Build.",
    },
    "expo-rn-router": {
        "name": "React Native + Expo Router (file-based)",
        "category": "Móvil · Cross-platform",
        "language": "TypeScript",
        "scaffold": [
            "npx --yes create-expo-app@latest . --template default --no-install",
            "npm install",
        ],
        "min_version": "expo SDK 52+ con expo-router v4",
        "skills": [],
        "notes": "Expo + expo-router (filesystem routing tipo Next.js). Carpeta `app/` define rutas. Ideal para apps con muchas pantallas. Preview web 8081.",
    },
    "flutter": {
        "name": "Flutter",
        "category": "Móvil · Cross-platform",
        "language": "Dart",
        "scaffold": [
            'command -v flutter >/dev/null 2>&1 || { echo "❌ Flutter no instalado. Descarga el SDK desde https://docs.flutter.dev/get-started/install/linux y añádelo al PATH. Después reintenta."; exit 1; }',
            "flutter create . --org __ORG_ID__ --platforms=android,ios,web",
            "flutter pub get",
        ],
        "min_version": "Flutter 3.24+",
        "skills": [],
        "notes": "Flutter con Material 3. Multi-target: Android + iOS + Web + Linux + Windows + macOS. Preview con `flutter run -d chrome`. Requiere Flutter SDK instalado.",
    },
    "ionic-capacitor": {
        "name": "Ionic + Capacitor (React)",
        "category": "Móvil · Cross-platform",
        "language": "TypeScript",
        "scaffold": [
            "npx --yes @ionic/cli@latest start . blank --type=react --no-deps --no-git --confirm --quiet",
            "npm install",
            "npm install @capacitor/core @capacitor/cli @capacitor/android @capacitor/ios",
            "npx --yes cap init --web-dir=dist --skip-appid",
        ],
        "min_version": "Ionic 8 + Capacitor 6",
        "skills": [],
        "notes": "Ionic 8 (React) + Capacitor 6. Empaqueta como app nativa con webview. Preview con `ionic serve` (puerto 8100). Build nativo: `ionic capacitor build android/ios`.",
    },
    "kotlin-compose": {
        "name": "Android nativo (Kotlin + Compose)",
        "category": "Móvil · Nativo",
        "language": "Kotlin",
        "scaffold": [
            'echo "⚠️  Stack Android nativo requiere Android Studio para el scaffold completo."',
            'echo "Pasos manuales:"',
            'echo "  1. Abre Android Studio → New Project → Empty Activity (Compose)"',
            'echo "  2. Selecciona esta carpeta como destino"',
            'echo "  3. Vuelve aquí y el agente AI te ayuda a desarrollar"',
            "mkdir -p app/src/main/{java,res}",
        ],
        "min_version": "Compose BOM 2024.10+, Kotlin 2.0+",
        "skills": [],
        "notes": "Android nativo: Kotlin + Jetpack Compose + Material 3. ThemeForge crea solo la carpeta — el scaffold real necesita Android Studio. Ideal para apps con UX 100% Material y mejor rendimiento que cross-platform.",
    },
    "laravel-inertia": {
        "name": "Laravel + Inertia + Tailwind",
        "category": "Web · Full-stack",
        "language": "PHP + TypeScript",
        "scaffold": [
            "composer create-project laravel/laravel . --prefer-dist",
            "php artisan install:api",
            "composer require inertiajs/inertia-laravel",
            "npm install",
            "npm install -D tailwindcss @tailwindcss/vite",
        ],
        "min_version": "laravel/framework@^11",
        "skills": [],
        "notes": "Laravel 11 + Inertia.js + Tailwind. Para SaaS full-stack PHP. Compatible con tu agencyflow previo.",
    },

    # ════════════════════════════════════════════════════════════════
    #  WEB FRONTEND — modernos (alta demanda 2026)
    # ════════════════════════════════════════════════════════════════
    "sveltekit-tailwind": {
        "name": "SvelteKit + Tailwind",
        "category": "Web · Frontend",
        "language": "TypeScript",
        "scaffold": [
            "npx --yes sv@latest create . --template=minimal --types=ts --no-add-ons --install=npm",
            "npx --yes sv@latest add tailwindcss --yes",
        ],
        "min_version": "Svelte 5 + SvelteKit 2.x",
        "skills": [],
        "notes": "SvelteKit 2 con Svelte 5 (runes). Bundles más pequeños que Next/Nuxt. Buen rendimiento en SSR + edge.",
    },
    "remix-tailwind": {
        "name": "Remix (React Router 7) + Tailwind",
        "category": "Web · Frontend",
        "language": "TypeScript",
        "scaffold": [
            "npx --yes create-react-router@latest . --template=remix-run/react-router-templates/default --yes --install",
            "npm install -D tailwindcss @tailwindcss/vite",
        ],
        "min_version": "React Router 7 (Remix v2 fusionado)",
        "skills": [],
        "notes": "Remix v3 unificado en React Router 7. SSR + nested routes + loaders/actions. Buen SEO.",
    },
    "qwik-tailwind": {
        "name": "Qwik City + Tailwind",
        "category": "Web · Frontend",
        "language": "TypeScript",
        "scaffold": [
            "npm create qwik@latest . -- --it empty",
            "npm install",
            "npm install -D tailwindcss @tailwindcss/vite",
        ],
        "min_version": "Qwik 1.10+",
        "skills": [],
        "notes": "Qwik con resumability. Cero hidratación inicial. Ideal para e-commerce y landings con TTI agresivo.",
    },
    "solidstart-tailwind": {
        "name": "SolidStart + Tailwind",
        "category": "Web · Frontend",
        "language": "TypeScript",
        "scaffold": [
            "npm init solid@latest .",
            "npm install",
            "npm install -D tailwindcss @tailwindcss/vite",
        ],
        "min_version": "Solid 1.9+ / SolidStart 1.x",
        "skills": [],
        "notes": "Reactividad fine-grained. Más rápido que React en updates. Sintaxis JSX familiar.",
    },

    # ════════════════════════════════════════════════════════════════
    #  WEB BACKEND / API — edge-first y modernos
    # ════════════════════════════════════════════════════════════════
    "hono-bun": {
        "name": "Hono + Bun",
        "category": "Backend · API",
        "language": "TypeScript",
        "scaffold": [
            'command -v bun >/dev/null 2>&1 || { echo "❌ Bun no instalado. curl -fsSL https://bun.sh/install | bash"; exit 1; }',
            "bun create hono@latest . --template=bun --install --no-git --pm=bun",
        ],
        "min_version": "Hono 4 + Bun 1.x",
        "skills": [],
        "notes": "Hono + Bun runtime. Web Standards (Request/Response). 3-5x más rápido que Express. Type-safe RPC. Despliegue en Cloudflare Workers, Deno, Bun, Node.",
    },
    "hono-cloudflare": {
        "name": "Hono + Cloudflare Workers",
        "category": "Backend · API",
        "language": "TypeScript",
        "scaffold": [
            "npm create hono@latest . -- --template=cloudflare-workers --install --no-git --pm=npm",
        ],
        "min_version": "Hono 4 + Wrangler 4.x",
        "skills": [],
        "notes": "Hono optimizado para Cloudflare Workers. Edge global, KV/D1/R2 listos. Despliegue con `wrangler deploy`.",
    },
    "nestjs-prisma": {
        "name": "NestJS + Prisma + Postgres",
        "category": "Backend · API",
        "language": "TypeScript",
        "scaffold": [
            "npx --yes @nestjs/cli@latest new . --package-manager=npm --skip-git",
            "npm install -D prisma && npm install @prisma/client",
            "npx prisma init --datasource-provider postgresql",
        ],
        "min_version": "NestJS 11 + Prisma 6",
        "skills": [],
        "notes": "NestJS (decorators, DI) + Prisma ORM + Postgres. Estándar enterprise. Ideal para APIs vendibles con SaaS templates.",
    },
    "fastapi": {
        "name": "FastAPI + Postgres",
        "category": "Backend · API",
        "language": "Python",
        "scaffold": [
            "python3 -m venv .venv",
            ". .venv/*/activate && pip install --quiet fastapi uvicorn[standard] sqlalchemy alembic psycopg2-binary python-jose passlib[bcrypt]",
            'mkdir -p app && printf "%s\\n" "from fastapi import FastAPI" "" "app = FastAPI(title=\\"__PROJECT__\\")" "" "@app.get(\\"/\\")" "def read_root():" "    return {\\"ok\\": True}" > app/main.py',
            "echo '.venv/' > .gitignore",
        ],
        "min_version": "FastAPI 0.115+",
        "skills": [],
        "notes": "FastAPI con SQLAlchemy 2.0 + Alembic + JWT (python-jose) + bcrypt. Servir con `uvicorn app.main:app --reload`.",
    },

    # ════════════════════════════════════════════════════════════════
    #  WEB FULL-STACK — opinionados
    # ════════════════════════════════════════════════════════════════
    "t3-stack": {
        "name": "T3 Stack (Next.js + tRPC + Prisma + NextAuth + Tailwind)",
        "category": "Web · Full-stack",
        "language": "TypeScript",
        "scaffold": [
            "npm create t3-app@latest . --noGit -- --CI --tailwind --trpc --nextAuth --prisma --appRouter --dbProvider=postgres",
        ],
        "min_version": "T3 Stack 7.x (Next.js 15+)",
        "skills": [],
        "notes": "Stack opinionado: Next.js 15 + tRPC + Prisma + NextAuth.js + Tailwind. Type-safety end-to-end. Plantilla SaaS vendible directo.",
    },
    "django-tailwind": {
        "name": "Django + Tailwind",
        "category": "Web · Full-stack",
        "language": "Python",
        "scaffold": [
            "python3 -m venv .venv",
            ". .venv/*/activate && pip install --quiet django django-tailwind[reload]",
            ". .venv/*/activate && django-admin startproject config .",
            ". .venv/*/activate && python manage.py startapp theme",
            "echo '.venv/' > .gitignore",
        ],
        "min_version": "Django 5.x",
        "skills": [],
        "notes": "Django 5 + django-tailwind (Tailwind v4 integrado). Servir con `python manage.py runserver`.",
    },

    # ════════════════════════════════════════════════════════════════
    #  DESKTOP
    # ════════════════════════════════════════════════════════════════
    "tauri-react": {
        "name": "Tauri 2 + React + Tailwind",
        "category": "Desktop",
        "language": "TypeScript + Rust",
        "scaffold": [
            'command -v cargo >/dev/null 2>&1 || { echo "❌ Rust no instalado. rustup curl --proto =https --tlsv1.2 -sSf https://sh.rustup.rs | sh"; exit 1; }',
            "npm create tauri-app@latest . -- --template=react-ts --manager=npm --yes --identifier=__ORG_ID__.__SLUG__",
            "npm install",
            "npm install -D tailwindcss @tailwindcss/vite",
        ],
        "min_version": "Tauri 2.x + Rust 1.80+",
        "skills": [],
        "notes": "Tauri 2 (Rust + webview nativo). Bundles ~25x más pequeños que Electron. Target Win/Mac/Linux + iOS/Android. Requiere Rust toolchain.",
    },
    "electron-react": {
        "name": "Electron + React + Vite",
        "category": "Desktop",
        "language": "TypeScript",
        "scaffold": [
            "npm create @quick-start/electron@latest . -- --template react-ts --skipPrompts --skipInstall",
            "npm install",
        ],
        "min_version": "Electron 34+ + React 19",
        "skills": [],
        "notes": "Electron + React + Vite (electron-vite). Más pesado que Tauri (~150 MB típico) pero compat amplia y ecosistema mayor.",
    },

    # ════════════════════════════════════════════════════════════════
    #  DOCS · SITES
    # ════════════════════════════════════════════════════════════════
    "docusaurus": {
        "name": "Docusaurus 3 (docs site)",
        "category": "Docs · Static",
        "language": "TypeScript",
        "scaffold": [
            "npx --yes create-docusaurus@latest . classic --typescript --skip-install",
            "npm install",
        ],
        "min_version": "Docusaurus 3.6+",
        "skills": [],
        "notes": "Docusaurus 3 (React-based). Docs + blog + versionado + i18n incluidos. Ideal para documentar tus templates al subirlos.",
    },
    "vitepress": {
        "name": "VitePress (docs site)",
        "category": "Docs · Static",
        "language": "TypeScript",
        "scaffold": [
            "npm init -y",
            "npm install -D vitepress",
            "npx vitepress init . --theme=default --useTypeScript",
        ],
        "min_version": "VitePress 1.5+",
        "skills": [],
        "notes": "VitePress (Vue + Vite). Más rápido que Docusaurus en build. Bonito por defecto. Perfecto para docs de librerías/SDKs.",
    },
    "starlight": {
        "name": "Astro Starlight (docs)",
        "category": "Docs · Static",
        "language": "TypeScript",
        "scaffold": [
            "npm create astro@latest . -- --template starlight --no-git --install --typescript strict --yes",
        ],
        "min_version": "Astro 5+ Starlight 0.30+",
        "skills": [],
        "notes": "Starlight (Astro): docs muy rápidas, MDX, búsqueda, i18n. Tema premium incluido. Astro >= 5.17.2 (CVE-2026-25545 fix).",
    },

    # ════════════════════════════════════════════════════════════════
    #  STATIC SITE GENERATORS (no-JS)
    # ════════════════════════════════════════════════════════════════
    "hugo": {
        "name": "Hugo (SSG en Go)",
        "category": "Web · Static",
        "language": "Go templates + Markdown",
        "scaffold": [
            'command -v hugo >/dev/null 2>&1 || { echo "❌ Hugo no instalado. sudo pacman -S hugo"; exit 1; }',
            "hugo new site . --force",
            "echo 'theme = \"papermod\"' >> hugo.toml",
        ],
        "min_version": "Hugo Extended 0.135+",
        "skills": [],
        "notes": "Hugo (binary Go). Blog/portfolio/docs rapidísimos. Tema PaperMod por defecto (puedes cambiarlo).",
    },
    "eleventy": {
        "name": "Eleventy (11ty)",
        "category": "Web · Static",
        "language": "JavaScript + Markdown",
        "scaffold": [
            "npm init -y",
            "npm install -D @11ty/eleventy",
            'mkdir -p src && echo "# Hello world" > src/index.md',
            'printf "%s\\n" "module.exports = function(c) { c.setUseTemplateCache(true); return { dir: { input: \\"src\\" } }; };" > .eleventy.js',
        ],
        "min_version": "Eleventy 3.x",
        "skills": [],
        "notes": "Eleventy (JavaScript SSG). Sin opiniones. Liviano. Buen ratio dev-experience/output para blogs y marketing.",
    },

    # ════════════════════════════════════════════════════════════════
    #  HEADLESS CMS
    # ════════════════════════════════════════════════════════════════
    "payload-cms": {
        "name": "Payload CMS (Next.js)",
        "category": "Headless CMS",
        "language": "TypeScript",
        "scaffold": [
            "npx --yes create-payload-app@latest . --template=blank --use-npm --no-deps=false --db=postgres",
        ],
        "min_version": "Payload 3.x",
        "skills": [],
        "notes": "Payload 3 (vive dentro de Next.js 15). Admin UI + REST + GraphQL + relations. Vendible directo como SaaS template.",
    },
    "strapi": {
        "name": "Strapi 5 (Headless CMS)",
        "category": "Headless CMS",
        "language": "TypeScript",
        "scaffold": [
            "npx --yes create-strapi@latest . --quickstart --no-run --skip-cloud --skip-db --use-npm --typescript",
        ],
        "min_version": "Strapi 5.x",
        "skills": [],
        "notes": "Strapi 5: admin UI + content modeling + REST + GraphQL. Plugin marketplace. SQLite local, Postgres en prod.",
    },

    # ════════════════════════════════════════════════════════════════
    #  E-COMMERCE
    # ════════════════════════════════════════════════════════════════
    "medusa": {
        "name": "Medusa 2 + Next.js Storefront",
        "category": "E-commerce",
        "language": "TypeScript",
        "scaffold": [
            "npx --yes create-medusa-app@latest . --no-browser --skip-db --with-nextjs-starter",
        ],
        "min_version": "Medusa 2.x",
        "skills": [],
        "notes": "Medusa 2 (admin + backend) + Next.js storefront en el mismo proyecto. Alternativa OSS a Shopify. Vendible como template.",
    },

    # ════════════════════════════════════════════════════════════════
    #  COMPONENT LIBRARIES
    # ════════════════════════════════════════════════════════════════
    "storybook-react": {
        "name": "Storybook + React + Vite",
        "category": "Component Lib",
        "language": "TypeScript",
        "scaffold": [
            "npm create vite@latest . -- --template react-ts",
            "npm install",
            "npx --yes storybook@latest init --yes --type react --skip-install --no-package-manager-arg",
            "npm install",
        ],
        "min_version": "Storybook 8.x",
        "skills": [],
        "notes": "Storybook 8 sobre React + Vite. Ideal para vender librerías de componentes en Gumroad/Creative Market.",
    },

    # ════════════════════════════════════════════════════════════════
    #  BROWSER EXTENSIONS
    # ════════════════════════════════════════════════════════════════
    "plasmo": {
        "name": "Plasmo (Browser Extension)",
        "category": "Browser Extension",
        "language": "TypeScript",
        "scaffold": [
            "npx --yes plasmo@latest init . --with-tailwindcss --with-popup --skip-prompts",
        ],
        "min_version": "Plasmo 0.90+",
        "skills": [],
        "notes": "Plasmo (Next.js para extensiones). Multi-target: Chrome, Firefox, Edge, Brave. Tailwind incluido. Popup + content scripts + bg.",
    },
    "wxt": {
        "name": "WXT (Browser Extension)",
        "category": "Browser Extension",
        "language": "TypeScript",
        "scaffold": [
            "npx --yes wxt@latest init . --template=react --pm=npm --skip-install",
            "npm install",
        ],
        "min_version": "WXT 0.20+",
        "skills": [],
        "notes": "WXT (Vite-based, más ligero que Plasmo). MV3, hot reload, file-based entries. Tendencia 2026.",
    },

    # ════════════════════════════════════════════════════════════════
    #  EMAIL
    # ════════════════════════════════════════════════════════════════
    "react-email": {
        "name": "React Email (templates)",
        "category": "Email",
        "language": "TypeScript",
        "scaffold": [
            "npx --yes create-email@latest .",
            "npm install",
        ],
        "min_version": "React Email 3+",
        "skills": [],
        "notes": "React Email: escribe emails en JSX, compila a HTML compatible con todos los clientes. Vendible como packs en Gumroad ($29-49).",
    },

    # ════════════════════════════════════════════════════════════════
    #  STACKS DE NICHO
    # ════════════════════════════════════════════════════════════════
    "phoenix-liveview": {
        "name": "Phoenix LiveView (Elixir)",
        "category": "Web · Full-stack",
        "language": "Elixir",
        "scaffold": [
            'command -v mix >/dev/null 2>&1 || { echo "❌ Elixir/Mix no instalado. paru -S elixir"; exit 1; }',
            "mix archive.install hex phx_new --force",
            "mix phx.new . --app __SLUG__ --module __PROJECT__ --install",
        ],
        "min_version": "Phoenix 1.7+ / Elixir 1.17+",
        "skills": [],
        "notes": "Phoenix LiveView: SSR + WebSockets reactivos sin escribir JS. SPA-feel sin SPA. Killer en realtime/colaborativos.",
    },
    "rails-tailwind": {
        "name": "Ruby on Rails 8 + Tailwind",
        "category": "Web · Full-stack",
        "language": "Ruby",
        "scaffold": [
            'command -v rails >/dev/null 2>&1 || { echo "❌ Rails no instalado. paru -S ruby ruby-rails"; exit 1; }',
            "rails new . --css=tailwind --javascript=esbuild --skip-bundle",
            "bundle install",
        ],
        "min_version": "Rails 8.x / Ruby 3.3+",
        "skills": [],
        "notes": "Rails 8 con Hotwire, Solid Queue/Cache/Cable (sin Redis), Kamal 2 para deploy. Tailwind oficial.",
    },
    "go-fiber": {
        "name": "Go + Fiber (API)",
        "category": "Backend · API",
        "language": "Go",
        "scaffold": [
            'command -v go >/dev/null 2>&1 || { echo "❌ Go no instalado. sudo pacman -S go"; exit 1; }',
            "go mod init __SLUG__",
            "go get -u github.com/gofiber/fiber/v3",
            'printf "%s\\n" "package main" "" "import \\"github.com/gofiber/fiber/v3\\"" "" "func main() {" "    app := fiber.New()" "    app.Get(\\"/\\", func(c fiber.Ctx) error { return c.SendString(\\"ok\\") })" "    app.Listen(\\":3000\\")" "}" > main.go',
        ],
        "min_version": "Fiber v3 / Go 1.23+",
        "skills": [],
        "notes": "Go + Fiber v3. Mismo enfoque que Express (familiar) pero ~10x más rápido. Build a binario único, deploy trivial.",
    },
    "rust-axum": {
        "name": "Rust + Axum",
        "category": "Backend · API",
        "language": "Rust",
        "scaffold": [
            'command -v cargo >/dev/null 2>&1 || { echo "❌ Rust no instalado. curl --proto =https --tlsv1.2 -sSf https://sh.rustup.rs | sh"; exit 1; }',
            "cargo init . --name __SLUG__",
            "cargo add axum tokio --features tokio/full",
            "cargo add tracing tracing-subscriber serde --features serde/derive",
        ],
        "min_version": "Axum 0.8+ / Tokio 1.x / Rust 1.80+",
        "skills": [],
        "notes": "Rust + Axum + Tokio + Serde. APIs ultra-rápidas y seguras. Compila a binario. Excelente para microservicios y backends de alta carga.",
    },
    "bun-elysia": {
        "name": "Bun + Elysia",
        "category": "Backend · API",
        "language": "TypeScript",
        "scaffold": [
            'command -v bun >/dev/null 2>&1 || { echo "❌ Bun no instalado. curl -fsSL https://bun.sh/install | bash"; exit 1; }',
            "bun create elysia . --no-git",
        ],
        "min_version": "Elysia 1.x / Bun 1.x",
        "skills": [],
        "notes": "Elysia (Bun-native, type-safe). Más rápido que Hono en benchmarks Bun-only. Ergonomía similar a Fastify.",
    },
    "deno-fresh": {
        "name": "Deno + Fresh",
        "category": "Web · Frontend",
        "language": "TypeScript",
        "scaffold": [
            'command -v deno >/dev/null 2>&1 || { echo "❌ Deno no instalado. curl -fsSL https://deno.land/install.sh | sh"; exit 1; }',
            "deno run -A -r https://fresh.deno.dev . --tailwind --vscode",
        ],
        "min_version": "Fresh 1.7+ / Deno 2.x",
        "skills": [],
        "notes": "Fresh: islands architecture (como Astro pero con Preact). Edge-native en Deno Deploy. Zero JS por defecto.",
    },
    "spring-boot": {
        "name": "Spring Boot 3 (Java)",
        "category": "Backend · API",
        "language": "Java",
        "scaffold": [
            'command -v curl >/dev/null 2>&1 || { echo "❌ curl no instalado"; exit 1; }',
            'curl -s https://start.spring.io/starter.tgz -d type=gradle-project -d language=java -d bootVersion=3.4.0 -d baseDir=tmp-spring -d groupId=__ORG_ID__ -d artifactId=__SLUG__ -d name=__PROJECT__ -d packageName=__ORG_ID__.__SLUG__ -d packaging=jar -d javaVersion=21 -d dependencies=web,validation,data-jpa,postgresql,security | tar -xz --strip-components=1',
            'echo "spring.application.name=__SLUG__" >> src/main/resources/application.properties',
        ],
        "min_version": "Spring Boot 3.4+ / Java 21",
        "skills": [],
        "notes": "Spring Boot 3.4 con Web + JPA + Postgres + Security. Stack enterprise dominante en Java. Build con Gradle.",
    },
    "ktor-server": {
        "name": "Ktor (Kotlin server)",
        "category": "Backend · API",
        "language": "Kotlin",
        "scaffold": [
            'curl -s https://start.ktor.io/api/v1/project/generate -d "name=__SLUG__&package_name=__ORG_ID__.__SLUG__&engine=netty&kotlin_version=2.0.21&ktor_version=3.0.1" -o /tmp/ktor.zip || echo "(ajusta versiones si la API cambió)"',
            'unzip -q /tmp/ktor.zip -d . && rm /tmp/ktor.zip',
        ],
        "min_version": "Ktor 3.x / Kotlin 2.x",
        "skills": [],
        "notes": "Ktor (JetBrains). API server async en Kotlin con corutinas. Más ligero que Spring. Buen complemento si haces Android con Kotlin.",
    },
    "nuxt-tailwind": {
        "name": "Nuxt 4 + Tailwind",
        "category": "Web · Full-stack",
        "language": "TypeScript",
        "scaffold": [
            "npx --yes nuxi@latest init . --packageManager=npm --gitInit=false --yes",
            "npx --yes nuxi@latest module add tailwindcss",
        ],
        "min_version": "Nuxt 4 / Vue 3.5+",
        "skills": [],
        "notes": "Nuxt 4 (Vue 3) con SSR/SSG/SPA modes. Auto-imports, file-based routing, módulos oficiales (auth, image, content).",
    },
    "sanity-studio": {
        "name": "Sanity Studio (CMS)",
        "category": "Headless CMS",
        "language": "TypeScript",
        "scaffold": [
            "npx --yes create-sanity@latest --typescript --no-git --output-path=. --template clean --dataset=production --create-project=false --skip-cli-config-warning",
            "npm install",
        ],
        "min_version": "Sanity Studio 3.x",
        "skills": [],
        "notes": "Sanity Studio v3 (React). Headless CMS con block content editor avanzado. GROQ query language. Real-time collaborative editing.",
    },
    "directus": {
        "name": "Directus (Headless)",
        "category": "Headless CMS",
        "language": "TypeScript",
        "scaffold": [
            "npm init directus-project@latest . -- --no-prompt --use-pg=false --skip-install",
            "npm install",
        ],
        "min_version": "Directus 11.x",
        "skills": [],
        "notes": "Directus 11: instant REST + GraphQL sobre tu DB existente. Admin UI moderno. Alternativa OSS a Strapi/Sanity.",
    },

    # ════════════════════════════════════════════════════════════════
    #  VARIANTES UI (mismo stack, distinta librería de componentes)
    # ════════════════════════════════════════════════════════════════
    "nextjs-shadcn": {
        "name": "Next.js + Tailwind + shadcn/ui",
        "category": "Web · Frontend",
        "language": "TypeScript",
        "scaffold": [
            'npx --yes create-next-app@latest . --ts --tailwind --eslint --app --src-dir --import-alias "@/*" --no-turbopack --use-npm',
            "npx --yes shadcn@latest init --yes --base-color=slate --css-variables",
            "npx --yes shadcn@latest add button card input form dialog dropdown-menu tabs --yes",
        ],
        "min_version": "Next.js 15+ / shadcn 2.x",
        "skills": ["anthropics/skills/frontend-design"],
        "notes": "Next.js + shadcn/ui con 7 componentes base preinstalados. La combinación más usada en CodeCanyon/ThemeForest 2026.",
    },
    "nextjs-mantine": {
        "name": "Next.js + Mantine",
        "category": "Web · Frontend",
        "language": "TypeScript",
        "scaffold": [
            'npx --yes create-next-app@latest . --ts --no-tailwind --eslint --app --src-dir --import-alias "@/*" --no-turbopack --use-npm',
            "npm install @mantine/core @mantine/hooks @mantine/form @mantine/notifications @tabler/icons-react",
            "npm install -D postcss postcss-preset-mantine postcss-simple-vars",
        ],
        "min_version": "Mantine 7.x / Next.js 15+",
        "skills": [],
        "notes": "Mantine 7 sobre Next.js. 100+ componentes, hooks, formularios, notificaciones. Buen para admin dashboards.",
    },
    "nextjs-heroui": {
        "name": "Next.js + Tailwind + HeroUI",
        "category": "Web · Frontend",
        "language": "TypeScript",
        "scaffold": [
            'npx --yes create-next-app@latest . --ts --tailwind --eslint --app --src-dir --import-alias "@/*" --no-turbopack --use-npm',
            "npm install @heroui/react framer-motion",
        ],
        "min_version": "HeroUI 2.x (ex-NextUI)",
        "skills": [],
        "notes": "HeroUI (rebranding de NextUI). Componentes modernos con Framer Motion. Estética premium para SaaS/landings.",
    },
    "astro-shadcn": {
        "name": "Astro + Tailwind + shadcn (React islands)",
        "category": "Web · Frontend",
        "language": "TypeScript",
        "scaffold": [
            "npm create astro@latest . -- --template minimal --typescript strict --install --no-git --yes",
            "npx astro add tailwind react --yes",
            "npx --yes shadcn@latest init --yes --base-color=slate --css-variables",
            "npx --yes shadcn@latest add button card --yes",
        ],
        "min_version": "Astro 5+ / shadcn 2.x",
        "skills": [],
        "notes": "Astro + React islands + shadcn. Mejor de los dos mundos: estático rápido + componentes interactivos donde hacen falta.",
    },
    "react-mantine": {
        "name": "React (Vite) + Mantine",
        "category": "Web · Frontend",
        "language": "TypeScript",
        "scaffold": [
            "npm create vite@latest . -- --template react-ts",
            "npm install",
            "npm install @mantine/core @mantine/hooks @tabler/icons-react",
            "npm install -D postcss postcss-preset-mantine postcss-simple-vars",
        ],
        "min_version": "Mantine 7.x / React 19",
        "skills": [],
        "notes": "React Vite + Mantine sin SSR. Para SPAs admin/dashboards. Más rápido que Next.js si no necesitas SSR.",
    },
    "vue-naive": {
        "name": "Vue 3 + Vite + Naive UI",
        "category": "Web · Frontend",
        "language": "TypeScript",
        "scaffold": [
            "npm create vite@latest . -- --template vue-ts",
            "npm install",
            "npm install -D naive-ui vfonts @vicons/ionicons5",
        ],
        "min_version": "Naive UI 2.40+",
        "skills": [],
        "notes": "Vue 3 + Naive UI: ~90 componentes, tree-shakeable, sin estilos globales. TypeScript-first. Buena alternativa a Element Plus.",
    },
    # ── Videojuegos ──────────────────────────────────────────────────
    "phaser-vite-ts": {
        "name": "Phaser 3 + Vite + TS",
        "category": "Game · Web 2D",
        "language": "TypeScript",
        "scaffold": [
            "npx --yes degit phaserjs/template-vite-ts .",
            "npm install",
        ],
        "min_version": "phaser@^3.90",
        "skills": [],
        "notes": (
            "Phaser 3 con Vite + TypeScript. Template oficial de PhaserJS. "
            "Preview embebida en localhost via Vite. Licencia MIT, ideal para "
            "vender en Gumroad / itch.io / Poki. Nichos hot 2026: "
            "vampire-survivors-like, endless runner, match-3, idle clicker."
        ),
    },
    "pixijs-vite-ts": {
        "name": "PixiJS + Vite + TS",
        "category": "Game · Web 2D",
        "language": "TypeScript",
        "scaffold": [
            "npm create vite@latest . -- --template vanilla-ts",
            "npm install",
            "npm install pixi.js@latest",
            "npm install -D @pixi/devtools",
        ],
        "min_version": "pixi.js@^8",
        "skills": [],
        "notes": (
            "PixiJS 8 con Vite + TypeScript. El render WebGL/WebGPU 2D más "
            "rápido del web. Licencia MIT. Para juegos high-perf, "
            "interactivas premium, demos de gameplay viral en Twitter/Reddit."
        ),
    },
    "r3f-vite-ts": {
        "name": "Three.js + React Three Fiber + Vite",
        "category": "Game · Web 3D",
        "language": "TypeScript",
        "scaffold": [
            "npm create vite@latest . -- --template react-ts",
            "npm install",
            "npm install three @react-three/fiber @react-three/drei",
            "npm install -D @types/three",
            "npm install -D tailwindcss@latest @tailwindcss/vite",
        ],
        "min_version": "three@^0.171 / @react-three/fiber@^8",
        "skills": ["anthropics/skills/frontend-design"],
        "notes": (
            "React Three Fiber + drei sobre Vite. 3D web declarativo, perfecto "
            "para mini-juegos en landings, product showcases interactivos, "
            "scenes WebGL para web premium. Licencia MIT."
        ),
    },
}

TEMPLATE_TYPES = [
    "(Sin tipo — detectar de la referencia)",
    "Admin / Dashboard",
    "Landing Page",
    "SaaS",
    "E-commerce",
    "Portfolio",
    "Blog / Magazine",
    "Documentation",
    "Coming Soon / Under Construction",
    "Agency / Studio",
    "App Showcase",
    "Multipurpose",
    "Videojuego · Vampire Survivors-like",
    "Videojuego · Endless Runner",
    "Videojuego · Match-3 / Merge",
    "Videojuego · Idle / Clicker",
    "Videojuego · Card battler / Deckbuilder",
    "Videojuego · Platformer 2D",
    "Videojuego · Tower Defense",
    "Videojuego · Hypercasual web",
    "3D Web · Product showcase interactivo",
]

# Nichos / industrias predefinidos. El user puede elegir uno O escribir
# el suyo en el combo editable. El nicho se inyecta en CLAUDE.md/AGENTS.md
# para que la IA pille tono, paleta, copy y demo data coherentes con la
# audiencia objetivo del template. Lista basada en categorías ThemeForest +
# CodeCanyon + Creative Market + Gumroad (Envato + populares 2025).
TEMPLATE_NICHES = [
    "(Sin nicho — propósito general)",
    # Business / Corporate
    "Startup / SaaS",
    "Corporativo / Empresa",
    "Consultoría / Coaching",
    "Servicios profesionales",
    "Legal / Abogados",
    "Financiero / Banking / Fintech",
    "Seguros",
    # Health & Wellness
    "Médico / Clínica",
    "Dental",
    "Veterinaria",
    "Fitness / Gym",
    "Yoga / Mindfulness",
    "Nutricionista / Dietista",
    "Spa / Belleza",
    "Psicología / Terapia",
    # Tech & Digital
    "Agencia digital / Marketing",
    "Software / Tech",
    "AI / Machine Learning",
    "Crypto / Web3 / NFT",
    "Cybersecurity",
    "DevTools / Developer products",
    "Hosting / Cloud",
    # Creative
    "Fotografía",
    "Diseño gráfico / Studio",
    "Arquitectura / Interiorismo",
    "Música / Banda / Artist",
    "Cine / Producción audiovisual",
    "Tatuajes / Body art",
    "Arte / Galería",
    # E-commerce niches
    "Moda / Fashion",
    "Joyería / Watches",
    "Cosmética / Skincare",
    "Tecnología / Gadgets",
    "Hogar / Decoración",
    "Muebles",
    "Comida gourmet / Delicatessen",
    "Vinos / Bebidas",
    "Mascotas / Pet shop",
    "Bebés / Infantil",
    "Deportes / Outdoor",
    # Food & Hospitality
    "Restaurante",
    "Cafetería / Coffee shop",
    "Pizzería",
    "Bar / Pub",
    "Catering / Eventos",
    "Food truck",
    "Bakery / Pastelería",
    # Travel & Real Estate
    "Hotel / Hospedaje",
    "Agencia de viajes / Tour operator",
    "Aerolínea",
    "Inmobiliaria / Real estate",
    "Property management",
    "Vacation rental / Airbnb",
    # Education
    "E-learning / Cursos online",
    "Universidad / Academia",
    "Colegio / School",
    "Guardería / Kindergarten",
    "Tutorías / Clases particulares",
    "Idiomas / Escuela de idiomas",
    # Events & Lifestyle
    "Boda / Wedding",
    "Eventos / Conferences",
    "DJ / Disco / Nightlife",
    "Quinceañera / Sweet 16",
    "Fiestas infantiles",
    # Industry & Trade
    "Construcción",
    "Industria / Manufactura",
    "Logística / Transporte",
    "Automoción / Concesionario",
    "Energía / Renewables",
    "Agricultura / Farm",
    # Non-profit & Public
    "ONG / Charity",
    "Iglesia / Religioso",
    "Política / Campaña",
    "Sindicato / Asociación",
    "Government / Public sector",
    # Media & News
    "Periódico / News",
    "Magazine / Editorial",
    "Podcast",
    "Streaming / OTT",
    "Radio",
    # Gaming & Entertainment
    "Gaming / Streamer",
    "Esports team",
    "Game studio",
    "Indie game dev / Pixel studio",
    "Mobile games",
    "Game assets / Marketplace",
    "Game launcher / Storefront",
    "Tournament / Ladder platform",
    "Casino / Apuestas",
    # Misc
    "Personal portfolio",
    "Currículum / CV online",
    "Influencer / Creador de contenido",
    "Membership / Comunidad",
    "Crowdfunding",
]

# AGENTS se sincroniza desde ai_providers.PROVIDERS para que la GUI y
# write_setup_script vean los 7 providers (Claude/Codex/Gemini/OpenCode/
# Claude-API/Codex-API/OpenRouter). Mantenemos las mismas keys legibles
# (`name`, `command`, `context_file`, `autoskills_flag`) por
# compatibilidad con el código existente.
def _build_agents() -> dict:
    try:
        import ai_providers
        out = {}
        for key, p in ai_providers.PROVIDERS.items():
            out[key] = {
                "name": p["name"],
                "command": p["command"],
                "context_file": p["context_file"],
                "autoskills_flag": p.get("autoskills_flag"),
            }
        return out
    except Exception:
        # Fallback si ai_providers no carga (durante migraciones)
        return {
            "claude": {"name": "Claude Code", "command": "claude",
                       "context_file": "CLAUDE.md", "autoskills_flag": "claude"},
            "codex": {"name": "Codex CLI", "command": "codex",
                      "context_file": "AGENTS.md", "autoskills_flag": "codex"},
        }


AGENTS = _build_agents()
