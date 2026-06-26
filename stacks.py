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
            'cat > style.css <<\'PCREATIVE STUDIO_EOF\'\n'
            '/*\n'
            'Theme Name: __PROJECT__\n'
            'Description: Block theme generado por Pcreative Studio.\n'
            'Version: 0.1.0\n'
            'Text Domain: __SLUG__\n'
            'License: GPLv2 or later\n'
            'Requires at least: 6.7\n'
            'Requires PHP: 8.0\n'
            '*/\n'
            'PCREATIVE STUDIO_EOF',
            # ── 2. theme.json mínimo válido ──────────────────────────
            'cat > theme.json <<\'PCREATIVE STUDIO_EOF\'\n'
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
            'PCREATIVE STUDIO_EOF',
            # ── 3. estructura de carpetas ────────────────────────────
            "mkdir -p templates parts patterns assets",
            # ── 4. template index mínimo ─────────────────────────────
            'cat > templates/index.html <<\'PCREATIVE STUDIO_EOF\'\n'
            '<!-- wp:template-part {"slug":"header","tagName":"header"} /-->\n'
            '<!-- wp:group {"tagName":"main","layout":{"type":"constrained"}} -->\n'
            '<main class="wp-block-group"><!-- wp:post-content /--></main>\n'
            '<!-- /wp:group -->\n'
            '<!-- wp:template-part {"slug":"footer","tagName":"footer"} /-->\n'
            'PCREATIVE STUDIO_EOF',
        ],
        "min_version": "WordPress 6.7+ / PHP 8.0",
        "skills": ["wordpress/skills/block-theme-development"],
        "ux_pack": "fse",
        "notes": "Block theme moderno (theme.json v3 + FSE). Pack UX «FSE Pro»: Pcreative Studio auto-instala GenerateBlocks, Spectra, ACF, Pods y Royal MCP (todos gratis). Premium opcionales (GenerateBlocks Pro, ACF Pro, Motion.page) si los declaras en ~/.config/themeforge/wp_packs.json (gitignored). El agente opera WP con wp-cli vía ./wp.",
    },
    "wordpress-bricks": {
        "name": "WordPress (Bricks Child Theme)",
        "category": "CMS · WordPress",
        "language": "PHP",
        "scaffold": [
            # ── 1. style.css del child theme (declara Template: bricks) ──
            'cat > style.css <<\'PCREATIVE STUDIO_EOF\'\n'
            '/*\n'
            'Theme Name: __PROJECT__ (Bricks child)\n'
            'Template: bricks\n'
            'Description: Child theme de Bricks Builder generado por Pcreative Studio.\n'
            'Version: 0.1.0\n'
            'Text Domain: __SLUG__\n'
            'License: GPLv2 or later\n'
            'Requires at least: 6.7\n'
            'Requires PHP: 8.0\n'
            '*/\n'
            'PCREATIVE STUDIO_EOF',
            # ── 2. functions.php (enqueue del child + hook bootstrap) ─
            'cat > functions.php <<\'PCREATIVE STUDIO_EOF\'\n'
            '<?php\n'
            "if (!defined('ABSPATH')) { exit; }\n"
            '\n'
            "add_action('wp_enqueue_scripts', function () {\n"
            "    wp_enqueue_style('__SLUG___parent', get_template_directory_uri() . '/style.css');\n"
            "    wp_enqueue_style('__SLUG___child', get_stylesheet_uri(), ['__SLUG___parent'], '0.1.0');\n"
            "});\n"
            '\n'
            "// Hooks del child theme: añadir aquí filtros/acciones específicos del proyecto.\n"
            'PCREATIVE STUDIO_EOF',
            # ── 3. estructura de carpetas ────────────────────────────
            "mkdir -p assets/css assets/js assets/images "
            "bricks-templates/{header,footer,single,archive,page,patterns} "
            "includes",
            # ── 4. README con el flujo Bricks ─────────────────────────
            'cat > README.md <<\'PCREATIVE STUDIO_EOF\'\n'
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
            'PCREATIVE STUDIO_EOF',
        ],
        "min_version": "WordPress 6.7+ / PHP 8.0 / Bricks Builder (licencia aparte)",
        "skills": ["wordpress/skills/block-theme-development"],
        "ux_pack": "bricks",
        "notes": "Child theme de Bricks Builder. Pack UX «Bricks»: Pcreative Studio auto-instala los gratis (GreenShift, ACF, Pods, Royal MCP). Premium (Bricks parent theme, Bricksforge, JetEngine, Novamira Pro, Motion.page) requieren licencia y se autoinstalan si los declaras en ~/.config/themeforge/wp_packs.json (gitignored, NUNCA al repo). Sin la licencia de Bricks, sube bricks.zip a mano y activa el child theme luego.",
    },
    "wordpress-elementor": {
        "name": "WordPress (Elementor Child Theme)",
        "category": "CMS · WordPress",
        "language": "PHP",
        "scaffold": [
            'cat > style.css <<\'PCREATIVE STUDIO_EOF\'\n'
            '/*\n'
            'Theme Name: __PROJECT__ (Elementor child)\n'
            'Template: hello-elementor\n'
            'Description: Child theme de Hello Elementor + Elementor (Pro opcional), generado por Pcreative Studio.\n'
            'Version: 0.1.0\n'
            'Text Domain: __SLUG__\n'
            'License: GPLv2 or later\n'
            'Requires at least: 6.7\n'
            'Requires PHP: 8.0\n'
            '*/\n'
            'PCREATIVE STUDIO_EOF',
            'cat > functions.php <<\'PCREATIVE STUDIO_EOF\'\n'
            '<?php\n'
            "if (!defined('ABSPATH')) { exit; }\n"
            '\n'
            "add_action('wp_enqueue_scripts', function () {\n"
            "    wp_enqueue_style('__SLUG___parent', get_template_directory_uri() . '/style.css');\n"
            "    wp_enqueue_style('__SLUG___child', get_stylesheet_uri(), ['__SLUG___parent'], '0.1.0');\n"
            "}, 20);\n"
            'PCREATIVE STUDIO_EOF',
            "mkdir -p assets/css assets/js assets/images "
            "elementor-templates/header elementor-templates/footer "
            "elementor-templates/single elementor-templates/archive "
            "elementor-templates/page elementor-templates/popups "
            "elementor-templates/kits includes",
            'cat > README.md <<\'PCREATIVE STUDIO_EOF\'\n'
            '# __PROJECT__ — Child theme de Elementor (Hello Elementor parent)\n'
            '\n'
            'Stack: Elementor + Hello Elementor (free) o Elementor Pro (paid).\n'
            'Plugins típicos: ACF, Pods, Essential Addons, JetEngine (paid), Royal MCP, Novamira Pro (paid).\n'
            '\n'
            '## Flujo\n'
            '1. Pcreative Studio instala Hello Elementor + Elementor free + Essential Addons Lite + ACF + Pods + Royal MCP.\n'
            '   Elementor Pro y JetEngine via `wp_packs.json` si los tienes.\n'
            '2. Diseña con Elementor en /wp-admin/ (autologueado).\n'
            '3. Templates (header/footer/single/archive/page/popup) + Kits (paletas, tipografía global) se exportan\n'
            '   vía Elementor → Templates → Export y se commitean en `elementor-templates/`.\n'
            '4. CSS/JS/hooks del child van en `assets/` + `functions.php`.\n'
            'PCREATIVE STUDIO_EOF',
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
            'cat > style.css <<\'PCREATIVE STUDIO_EOF\'\n'
            '/*\n'
            'Theme Name: __PROJECT__ (Divi child)\n'
            'Template: Divi\n'
            'Description: Child theme de Divi (Elegant Themes) generado por Pcreative Studio.\n'
            'Version: 0.1.0\n'
            'Text Domain: __SLUG__\n'
            'License: GPLv2 or later\n'
            'Requires at least: 6.7\n'
            'Requires PHP: 8.0\n'
            '*/\n'
            'PCREATIVE STUDIO_EOF',
            'cat > functions.php <<\'PCREATIVE STUDIO_EOF\'\n'
            '<?php\n'
            "if (!defined('ABSPATH')) { exit; }\n"
            '\n'
            "add_action('wp_enqueue_scripts', function () {\n"
            "    wp_enqueue_style('__SLUG___parent', get_template_directory_uri() . '/style.css');\n"
            "    wp_enqueue_style('__SLUG___child', get_stylesheet_uri(), ['__SLUG___parent'], '0.1.0');\n"
            "}, 20);\n"
            'PCREATIVE STUDIO_EOF',
            "mkdir -p assets/css assets/js assets/images "
            "divi-layouts/header divi-layouts/footer divi-layouts/single "
            "divi-layouts/archive divi-layouts/page divi-layouts/modules "
            "includes",
            'cat > README.md <<\'PCREATIVE STUDIO_EOF\'\n'
            '# __PROJECT__ — Child theme de Divi\n'
            '\n'
            'Stack: Divi 5 (Elegant Themes, paid). Plugins típicos: ACF, Pods, Royal MCP, Novamira Pro (paid).\n'
            '\n'
            '## Flujo\n'
            '1. Declara el ZIP de Divi en wp_packs.json > divi > theme para auto-instalación.\n'
            '2. Diseña con Divi Builder. Exporta layouts vía Divi → Library → Export a JSON.\n'
            '3. Commitea los JSON en `divi-layouts/`.\n'
            'PCREATIVE STUDIO_EOF',
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
            'cat > style.css <<\'PCREATIVE STUDIO_EOF\'\n'
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
            'PCREATIVE STUDIO_EOF',
            'cat > functions.php <<\'PCREATIVE STUDIO_EOF\'\n'
            '<?php\n'
            "if (!defined('ABSPATH')) { exit; }\n"
            '\n'
            "add_action('wp_enqueue_scripts', function () {\n"
            "    wp_enqueue_style('__SLUG___parent', get_template_directory_uri() . '/style.css');\n"
            "    wp_enqueue_style('__SLUG___child', get_stylesheet_uri(), ['__SLUG___parent'], '0.1.0');\n"
            "}, 20);\n"
            'PCREATIVE STUDIO_EOF',
            "mkdir -p assets/css assets/js assets/images "
            "breakdance-templates/global breakdance-templates/headers "
            "breakdance-templates/footers breakdance-templates/popups "
            "breakdance-templates/singles breakdance-templates/archives "
            "includes",
            'cat > README.md <<\'PCREATIVE STUDIO_EOF\'\n'
            '# __PROJECT__ — Breakdance template (child de Kadence)\n'
            '\n'
            'Stack: Breakdance (plugin, free + Pro opcional) sobre Kadence como theme base.\n'
            'Breakdance reemplaza el render del front; el theme base solo sirve para wp-admin y fallback.\n'
            '\n'
            '## Flujo\n'
            '1. Pcreative Studio instala Kadence + Breakdance free + ACF + Pods + Royal MCP.\n'
            '2. Breakdance Pro y plugins paid (en wp_packs.json > breakdance > plugins).\n'
            '3. Diseña con Breakdance. Exporta global settings / headers / footers / popups\n'
            '   vía Breakdance → Templates → Export y commitea en `breakdance-templates/`.\n'
            'PCREATIVE STUDIO_EOF',
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
            'cat > __SLUG__.php <<\'PCREATIVE STUDIO_EOF\'\n'
            '<?php\n'
            '/**\n'
            ' * Plugin Name: __PROJECT__\n'
            ' * Description: Plugin generado por Pcreative Studio.\n'
            ' * Version: 0.1.0\n'
            ' * Author: Pcreative Studio\n'
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
            'PCREATIVE STUDIO_EOF',
            # ── 3. composer.json con PSR-4 autoload ──────────────────
            'cat > composer.json <<\'PCREATIVE STUDIO_EOF\'\n'
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
            'PCREATIVE STUDIO_EOF',
            # ── 4. package.json con Vite + Vue para admin UI ─────────
            'cat > package.json <<\'PCREATIVE STUDIO_EOF\'\n'
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
            'PCREATIVE STUDIO_EOF',
            # ── 5. vite.config.js (build a /build con manifest) ──────
            'cat > vite.config.js <<\'PCREATIVE STUDIO_EOF\'\n'
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
            'PCREATIVE STUDIO_EOF',
            # ── 7. .gitignore ────────────────────────────────────────
            'cat > .gitignore <<\'PCREATIVE STUDIO_EOF\'\n'
            'vendor/\n'
            'node_modules/\n'
            'build/\n'
            '*.log\n'
            '/.env\n'
            'tests/_output/\n'
            'tests/_data/dumps/\n'
            '/coverage/\n'
            'PCREATIVE STUDIO_EOF',
            # ── 8. README con instrucciones ──────────────────────────
            'cat > README.md <<\'PCREATIVE STUDIO_EOF\'\n'
            '# __PROJECT__\n\n'
            'WordPress plugin generado por Pcreative Studio.\n\n'
            '## Stack\n\n'
            '- PHP 8.2 + Composer (autoload PSR-4 `Themeforge\\\\__PASCAL__\\\\`)\n'
            '- WordPress 6.7+ (entorno Docker levantado por Pcreative Studio — ver WORDPRESS-DEV.md)\n'
            '- Admin UI: Vue 3.5 + Vite 6 + Tailwind 4\n'
            '- Tests: Pest + Playwright E2E\n\n'
            '## Arrancar\n\n'
            '```bash\n'
            'composer install\n'
            'npm install\n'
            '# WordPress lo levanta Pcreative Studio automáticamente (ver WORDPRESS-DEV.md)\n'
            'npm run dev             # Vite HMR para admin UI\n'
            '```\n\n'
            '## WordPress de desarrollo\n\n'
            'Pcreative Studio levanta WordPress en Docker automáticamente y monta este plugin.\n'
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
            'PCREATIVE STUDIO_EOF',
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
            "Plugin WP. El entorno WordPress (Docker) lo levanta Pcreative Studio "
            "automáticamente al crear el proyecto y monta el plugin (ver WORDPRESS-DEV.md). "
            "El agente opera WP con wp-cli vía ./wp. "
            "Canal de venta: CodeCanyon, Freemius, web propia. "
            "REQUISITOS: Docker corriendo + Node 18+ + Composer 2.x."
        ),
    },
    "shopify-liquid": {
        "name": "Shopify Liquid (Online Store 2.0 + Dawn)",
        "category": "E-commerce",
        "language": "Liquid + JS",
        "scaffold": [
            # Dawn = el theme oficial de Shopify (MIT). Es la base que usa el
            # 80%+ del mercado real — partir de aquí ahorra meses y el código
            # ya cumple Theme Store Quality Guidelines de salida. El agente lo
            # personaliza/extiende; NO se copia tal cual.
            "npx --yes @shopify/cli@latest theme init . --clone-url https://github.com/Shopify/dawn",
            # ── package.json: prettier + liquid plugin + scripts útiles
            'cat > package.json <<\'PCREATIVE STUDIO_EOF\'\n'
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
            'PCREATIVE STUDIO_EOF',
            # ── .prettierrc.json con el plugin de Liquid
            'cat > .prettierrc.json <<\'PCREATIVE STUDIO_EOF\'\n'
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
            'PCREATIVE STUDIO_EOF',
            # ── .theme-check.yml estricto para Theme Store
            'cat > .theme-check.yml <<\'PCREATIVE STUDIO_EOF\'\n'
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
            'ValidJSON:\n'
            '  enabled: true\n'
            'ValidSchema:\n'
            '  enabled: true\n'
            'RequiredLayoutThemeObject:\n'
            '  enabled: true\n'
            'UnreachableCode:\n'
            '  enabled: true\n'
            'ImgWidthAndHeight:\n'
            '  enabled: true\n'
            'MatchingTranslations:\n'
            '  enabled: true\n'
            'PCREATIVE STUDIO_EOF',
            # ── GitHub Actions Lighthouse CI (action oficial de Shopify)
            "mkdir -p .github/workflows",
            'cat > .github/workflows/lighthouse-ci.yml <<\'PCREATIVE STUDIO_EOF\'\n'
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
            'PCREATIVE STUDIO_EOF',
            # ── .mcp.json: Shopify Dev MCP (admin/storefront/checkout APIs
            #    + Polaris) + Storefront MCP (placeholder con tu shop).
            #    Polaris ya viene integrado en @shopify/dev-mcp — sin flag.
            'cat > .mcp.json <<\'PCREATIVE STUDIO_EOF\'\n'
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
            'PCREATIVE STUDIO_EOF',
            # ── README rápido del MCP + comandos CLI ─────────────────
            'cat > README-MCP.md <<\'PCREATIVE STUDIO_EOF\'\n'
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
            'PCREATIVE STUDIO_EOF',
        ],
        "min_version": "Online Store 2.0 / Shopify CLI 3.x / Dawn",
        "skills": ["shopify/skills/theme-development"],
        "ux_pack": "shopify-liquid",
        "notes": "Online Store 2.0 sobre Dawn (theme oficial Shopify, MIT) como base. Incluye .mcp.json con (1) Shopify Dev MCP — admin/storefront/checkout API docs + Polaris components, (2) Storefront MCP (zero-auth, sustituye YOUR-SHOP), (3) Storefront UCP MCP (catálogo + búsqueda natural). Necesitas tienda dev en Shopify Partners (gratis) para `shopify theme dev`.",
    },
    "shopify-liquid-blank": {
        "name": "Shopify Liquid (Theme Store, sin Dawn)",
        "category": "E-commerce",
        "language": "Liquid + JS",
        "scaffold": [
            # Estructura OS 2.0 MÍNIMA que cumple los requisitos del Shopify
            # Theme Store sin derivarse de Dawn ni Horizon. Los themes
            # Dawn-derived son INELEGIBLES — este stack construye desde cero
            # la estructura técnica válida y deja que el agente la complete
            # con tu identidad visual única.
            "mkdir -p config layout sections blocks templates/customers snippets locales assets .github/workflows",
            # config/settings_schema.json — tokens + theme info + paletas
            'cat > config/settings_schema.json <<\'PCREATIVE STUDIO_EOF\'\n'
            '[\n'
            '  { "name": "theme_info", "theme_name": "__PROJECT__", "theme_version": "0.1.0",\n'
            '    "theme_author": "you", "theme_documentation_url": "https://your-docs.example.com",\n'
            '    "theme_support_email": "support@example.com" },\n'
            '  { "name": "Layout", "settings": [\n'
            '    { "type": "range", "id": "page_width", "min": 1000, "max": 1600, "step": 100, "unit": "px", "label": "Page width", "default": 1280 }\n'
            '  ]},\n'
            '  { "name": "Colors", "settings": [\n'
            '    { "type": "color_scheme_group", "id": "color_schemes", "label": "Color schemes",\n'
            '      "definition": [\n'
            '        { "type": "color", "id": "background", "label": "Background", "default": "#FFFFFF" },\n'
            '        { "type": "color", "id": "text",       "label": "Text",       "default": "#1A1A1A" },\n'
            '        { "type": "color", "id": "accent",     "label": "Accent",     "default": "#C56A4D" }\n'
            '      ],\n'
            '      "role": { "text": "text", "background": { "solid": "background" } }\n'
            '    }\n'
            '  ]},\n'
            '  { "name": "Typography", "settings": [\n'
            '    { "type": "font_picker", "id": "type_heading_font", "label": "Heading", "default": "fraunces_n4" },\n'
            '    { "type": "font_picker", "id": "type_body_font",    "label": "Body",    "default": "inter_n4" }\n'
            '  ]},\n'
            '  { "name": "Social", "settings": [\n'
            '    { "type": "url", "id": "social_instagram_link", "label": "Instagram" },\n'
            '    { "type": "url", "id": "social_youtube_link",   "label": "YouTube" }\n'
            '  ]},\n'
            '  { "name": "Favicon", "settings": [\n'
            '    { "type": "image_picker", "id": "favicon", "label": "Favicon" }\n'
            '  ]}\n'
            ']\n'
            'PCREATIVE STUDIO_EOF',
            # config/settings_data.json — el editor lo regenera
            'cat > config/settings_data.json <<\'PCREATIVE STUDIO_EOF\'\n'
            '{ "current": "Default", "presets": { "Default": {} } }\n'
            'PCREATIVE STUDIO_EOF',
            # layout/theme.liquid — canónico OS 2.0 con section groups
            'cat > layout/theme.liquid <<\'PCREATIVE STUDIO_EOF\'\n'
            '<!DOCTYPE html>\n'
            '<html lang="{{ request.locale.iso_code }}">\n'
            '  <head>\n'
            '    <meta charset="UTF-8">\n'
            '    <meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '    <link rel="canonical" href="{{ canonical_url }}">\n'
            '    {%- if settings.favicon != blank -%}\n'
            '      <link rel="icon" type="image/png" href="{{ settings.favicon | image_url: width: 32 }}">\n'
            '    {%- endif -%}\n'
            '    <title>{{ page_title }}{% if current_page > 1 %} &mdash; {{ "general.meta.page" | t: page: current_page }}{% endif %}{% unless page_title contains shop.name %} &mdash; {{ shop.name }}{% endunless %}</title>\n'
            '    {%- if page_description -%}<meta name="description" content="{{ page_description | escape }}">{%- endif -%}\n'
            '    {{ content_for_header }}\n'
            '  </head>\n'
            '  <body class="template-{{ template.name }}">\n'
            '    <a class="skip-link" href="#MainContent">{{ \'accessibility.skip_to_content\' | t }}</a>\n'
            '    {% sections \'header-group\' %}\n'
            '    <main id="MainContent" role="main">{{ content_for_layout }}</main>\n'
            '    {% sections \'footer-group\' %}\n'
            '  </body>\n'
            '</html>\n'
            'PCREATIVE STUDIO_EOF',
            # sections/header-group.json y footer-group.json
            'cat > sections/header-group.json <<\'PCREATIVE STUDIO_EOF\'\n'
            '{ "type": "header", "name": "Header group",\n'
            '  "sections": { "header": { "type": "header", "settings": {} } },\n'
            '  "order": ["header"] }\n'
            'PCREATIVE STUDIO_EOF',
            'cat > sections/footer-group.json <<\'PCREATIVE STUDIO_EOF\'\n'
            '{ "type": "footer", "name": "Footer group",\n'
            '  "sections": { "footer": { "type": "footer", "settings": {} } },\n'
            '  "order": ["footer"] }\n'
            'PCREATIVE STUDIO_EOF',
            # sections/header.liquid mínimo válido
            'cat > sections/header.liquid <<\'PCREATIVE STUDIO_EOF\'\n'
            '<header class="site-header">\n'
            '  <a href="{{ routes.root_url }}" class="site-header__logo">{{ shop.name }}</a>\n'
            '  <nav role="navigation" aria-label="{{ \'accessibility.main_nav\' | t }}">\n'
            '    {%- for link in linklists[section.settings.menu].links -%}\n'
            '      <a href="{{ link.url }}">{{ link.title }}</a>\n'
            '    {%- endfor -%}\n'
            '  </nav>\n'
            '</header>\n'
            '{% schema %}\n'
            '{ "name": "Header", "tag": "section", "class": "section section--header",\n'
            '  "settings": [\n'
            '    { "type": "link_list", "id": "menu", "default": "main-menu", "label": "Main menu" }\n'
            '  ],\n'
            '  "blocks": [{ "type": "@app" }],\n'
            '  "enabled_on": { "groups": ["header"] } }\n'
            '{% endschema %}\n'
            'PCREATIVE STUDIO_EOF',
            # sections/footer.liquid mínimo válido
            'cat > sections/footer.liquid <<\'PCREATIVE STUDIO_EOF\'\n'
            '<footer class="site-footer" role="contentinfo">\n'
            '  <p>&copy; {{ "now" | date: "%Y" }} {{ shop.name }}. {{ \'general.rights\' | t }}</p>\n'
            '</footer>\n'
            '{% schema %}\n'
            '{ "name": "Footer", "tag": "section", "class": "section section--footer",\n'
            '  "settings": [],\n'
            '  "blocks": [{ "type": "@app" }],\n'
            '  "enabled_on": { "groups": ["footer"] } }\n'
            '{% endschema %}\n'
            'PCREATIVE STUDIO_EOF',
            # Templates JSON obligatorios para Theme Store (14)
            "for t in 404 article blog cart collection gift_card index list-collections page password product search; do "
            "echo '{ \"sections\": {}, \"order\": [] }' > templates/${t}.json; done",
            "for t in account addresses login order register reset_password; do "
            "echo '{ \"sections\": {}, \"order\": [] }' > templates/customers/${t}.json; done",
            # locales por defecto (storefront + schema)
            'cat > locales/en.default.json <<\'PCREATIVE STUDIO_EOF\'\n'
            '{\n'
            '  "accessibility": { "skip_to_content": "Skip to content", "main_nav": "Main navigation" },\n'
            '  "general":       { "rights": "All rights reserved.", "country": "Country", "language": "Language", "update": "Update", "meta": { "page": "Page {{ page }}" } },\n'
            '  "cart":          { "general": { "title": "Cart", "empty_html": "Your cart is empty" } },\n'
            '  "products":      { "product": { "add_to_cart": "Add to cart", "sold_out": "Sold out" } }\n'
            '}\n'
            'PCREATIVE STUDIO_EOF',
            'cat > locales/en.default.schema.json <<\'PCREATIVE STUDIO_EOF\'\n'
            '{ "settings_schema": { "theme_info": { "theme_name": "Theme name" } } }\n'
            'PCREATIVE STUDIO_EOF',
            'cat > locales/es.json <<\'PCREATIVE STUDIO_EOF\'\n'
            '{\n'
            '  "accessibility": { "skip_to_content": "Saltar al contenido", "main_nav": "Navegación principal" },\n'
            '  "general":       { "rights": "Todos los derechos reservados.", "country": "País", "language": "Idioma", "update": "Actualizar", "meta": { "page": "Página {{ page }}" } },\n'
            '  "cart":          { "general": { "title": "Carrito", "empty_html": "Tu carrito está vacío" } },\n'
            '  "products":      { "product": { "add_to_cart": "Añadir al carrito", "sold_out": "Agotado" } }\n'
            '}\n'
            'PCREATIVE STUDIO_EOF',
            'cat > locales/es.schema.json <<\'PCREATIVE STUDIO_EOF\'\n'
            '{ "settings_schema": { "theme_info": { "theme_name": "Nombre del tema" } } }\n'
            'PCREATIVE STUDIO_EOF',
            # CSS base mínimo
            'cat > assets/base.css <<\'PCREATIVE STUDIO_EOF\'\n'
            ':root { --color-bg: #fff; --color-text: #1a1a1a; --color-accent: #c56a4d; }\n'
            'body { margin: 0; font-family: var(--font-body, system-ui, sans-serif); color: var(--color-text); background: var(--color-bg); }\n'
            '.skip-link { position: absolute; left: -9999px; }\n'
            '.skip-link:focus { left: 0; top: 0; padding: 1rem; background: var(--color-bg); }\n'
            'PCREATIVE STUDIO_EOF',
            # package.json + prettier + theme-check + lighthouse (igual que liquid)
            'cat > package.json <<\'PCREATIVE STUDIO_EOF\'\n'
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
            'PCREATIVE STUDIO_EOF',
            'cat > .prettierrc.json <<\'PCREATIVE STUDIO_EOF\'\n'
            '{\n'
            '  "plugins": ["@shopify/prettier-plugin-liquid"],\n'
            '  "printWidth": 100,\n'
            '  "singleQuote": false\n'
            '}\n'
            'PCREATIVE STUDIO_EOF',
            'cat > .theme-check.yml <<\'PCREATIVE STUDIO_EOF\'\n'
            '# Theme Check — modo Theme Store estricto (apunta a aprobación oficial).\n'
            'extends: theme-check:recommended\n'
            '\n'
            'AssetSizeJavaScript:\n'
            '  enabled: true\n'
            '  threshold_in_bytes: 16384   # 16 KB cap oficial\n'
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
            'DeprecatedFilter:\n'
            '  enabled: true\n'
            'TemplateLength:\n'
            '  enabled: true\n'
            '  max_length: 600\n'
            'ValidJSON:\n'
            '  enabled: true\n'
            'ValidSchema:\n'
            '  enabled: true\n'
            'RequiredLayoutThemeObject:\n'
            '  enabled: true\n'
            'UnreachableCode:\n'
            '  enabled: true\n'
            'ImgWidthAndHeight:\n'
            '  enabled: true\n'
            'MatchingTranslations:\n'
            '  enabled: true\n'
            'PCREATIVE STUDIO_EOF',
            'cat > .github/workflows/lighthouse-ci.yml <<\'PCREATIVE STUDIO_EOF\'\n'
            'name: Lighthouse CI\n'
            'on:\n'
            '  push:\n'
            '    branches: [main]\n'
            '  pull_request:\n'
            '    branches: [main]\n'
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
            'PCREATIVE STUDIO_EOF',
            # .mcp.json — los 3 MCPs Shopify (mismo que liquid Dawn)
            'cat > .mcp.json <<\'PCREATIVE STUDIO_EOF\'\n'
            '{\n'
            '  "mcpServers": {\n'
            '    "shopify-dev": {\n'
            '      "command": "npx",\n'
            '      "args": ["-y", "@shopify/dev-mcp@latest"]\n'
            '    },\n'
            '    "shopify-storefront": {\n'
            '      "type": "http",\n'
            '      "url": "https://YOUR-SHOP.myshopify.com/api/mcp"\n'
            '    },\n'
            '    "shopify-storefront-catalog": {\n'
            '      "type": "http",\n'
            '      "url": "https://YOUR-SHOP.myshopify.com/api/ucp/mcp"\n'
            '    }\n'
            '  }\n'
            '}\n'
            'PCREATIVE STUDIO_EOF',
            'cat > README-THEME-STORE.md <<\'PCREATIVE STUDIO_EOF\'\n'
            '# __PROJECT__ — Shopify Theme (Theme Store route)\n'
            '\n'
            'Stack: **Online Store 2.0 desde cero** (sin Dawn, sin Horizon).\n'
            'Elegible para el **Shopify Theme Store** porque NO se deriva de\n'
            'ninguno de los themes oficiales (Dawn-derived es auto-reject).\n'
            '\n'
            '## Qué te ha scaffoldeado Pcreative Studio\n'
            '\n'
            'Estructura técnica OS 2.0 mínima válida:\n'
            '- `config/settings_schema.json` + `settings_data.json`\n'
            '- `layout/theme.liquid` canónico\n'
            '- `sections/header-group.json` + `footer-group.json` + sus liquids\n'
            '- `blocks/` (vacío — listo para que añadas theme blocks)\n'
            '- `templates/*.json` (14 obligatorios + customers/*) vacíos\n'
            '- `snippets/` (vacío)\n'
            '- `locales/en.default.json` + `.schema.json` + `es.json` + `.schema.json`\n'
            '- `assets/base.css`\n'
            '- `package.json` con prettier + scripts dev/check/format\n'
            '- `.theme-check.yml` modo estricto\n'
            '- `.github/workflows/lighthouse-ci.yml` con la action oficial\n'
            '- `.mcp.json` con los 3 MCPs Shopify\n'
            '\n'
            '## Lo que TÚ tienes que construir\n'
            '\n'
            '1. **Identidad visual única** — paleta, tipografía, layout,\n'
            '   componentes que NO sean reproducibles cosméticamente.\n'
            '2. **Sections premium** dentro de los templates JSON: hero, featured\n'
            '   collection, image-with-text, testimonials, FAQ, newsletter, etc.\n'
            '3. **Las 18 features mandatorias** del Theme Store (faceted search,\n'
            '   predictive search, gift cards, selling plans, Shop Pay Installments,\n'
            '   pickup availability, variant images, etc. — ver CLAUDE.md).\n'
            '4. **JS modular sin frameworks** (< 16 KB total minified).\n'
            '5. **i18n completo** (zero hardcoded strings).\n'
            '6. **Documentation HTML** estática para entregar al comprador.\n'
            '\n'
            'El `CLAUDE.md` lleva la checklist completa de submission al final.\n'
            'PCREATIVE STUDIO_EOF',
        ],
        "min_version": "Online Store 2.0 / Shopify CLI 3.x",
        "skills": ["shopify/skills/theme-development"],
        "ux_pack": "shopify-liquid-blank",
        "notes": "Online Store 2.0 desde CERO, sin clonar Dawn ni Horizon. ELEGIBLE para Shopify Theme Store. Estructura técnica válida pero vacía: tu trabajo es construir identidad visual única + las 18 features mandatorias + i18n + docs. Más curva de aprendizaje pero margen mayor (Theme Store premia themes únicos). Mismos 3 MCPs Shopify + scaffold extras (prettier/theme-check/lighthouse-ci) que el stack Liquid+Dawn.",
    },
    "shopify-hydrogen": {
        "name": "Shopify Hydrogen (Remix + React)",
        "category": "E-commerce",
        "language": "TypeScript + React",
        "scaffold": [
            # Scaffold oficial de Shopify para Hydrogen (template skeleton).
            # Si no se puede ejecutar el create no-interactivo, el agente
            # debe correrlo a mano. --quickstart bypasses la mayoría de
            # prompts; --no-install evita yarn/npm install al arrancar.
            "npx --yes @shopify/create-hydrogen@latest . --quickstart --no-install || "
            "(echo 'Fallback: ejecuta a mano `npm create @shopify/hydrogen@latest .` y elige las opciones.' && exit 0)",
            # ── .mcp.json: mismo set que Liquid + el storefront URL hint ──
            'cat > .mcp.json <<\'PCREATIVE STUDIO_EOF\'\n'
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
            'PCREATIVE STUDIO_EOF',
            # README-HYDROGEN.md con CLI + workflow
            'cat > README-HYDROGEN.md <<\'PCREATIVE STUDIO_EOF\'\n'
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
            'PCREATIVE STUDIO_EOF',
        ],
        "min_version": "Hydrogen 2026.x / React 19 / Node 22+",
        "skills": ["shopify/skills/theme-development"],
        "ux_pack": "shopify-hydrogen",
        "notes": "Storefront headless con Remix + React + Oxygen. Para catálogos grandes, multi-mercado y diseños premium. Mismo set de MCPs que Liquid. Requiere Node 22+. Deploy a Oxygen (edge gratuito de Shopify) o cualquier provider Node.",
    },
    "shopify-polaris-app": {
        "name": "Shopify App (Polaris + App Bridge + Remix)",
        "category": "E-commerce",
        "language": "TypeScript + React",
        "scaffold": [
            # Scaffold oficial de apps Shopify (Remix template).
            # Si no se puede no-interactivo, el agente lo corre a mano.
            "npx --yes @shopify/create-app@latest --template remix --name __SLUG__ --no-install || "
            "(echo 'Fallback: ejecuta a mano `npm init @shopify/app@latest` y elige template Remix.' && exit 0)",
            # .mcp.json — Shopify Dev MCP (incluye Polaris) + storefront opcionales
            'cat > .mcp.json <<\'PCREATIVE STUDIO_EOF\'\n'
            '{\n'
            '  "mcpServers": {\n'
            '    "shopify-dev": {\n'
            '      "command": "npx",\n'
            '      "args": ["-y", "@shopify/dev-mcp@latest"],\n'
            '      "_doc": "Admin/Storefront/Checkout API + Polaris components."\n'
            '    }\n'
            '  }\n'
            '}\n'
            'PCREATIVE STUDIO_EOF',
            'cat > README-APP.md <<\'PCREATIVE STUDIO_EOF\'\n'
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
            'PCREATIVE STUDIO_EOF',
        ],
        "min_version": "Shopify CLI 3.x / Remix v3 / Polaris 13+ / Node 22+",
        "skills": ["shopify/skills/theme-development"],
        "ux_pack": "shopify-polaris-app",
        "notes": "App embebida en el Admin de Shopify con Polaris + App Bridge + Remix + Prisma. Para apps públicas en Shopify App Store, custom apps de una sola tienda, o extensiones (theme/checkout/customer-account/admin/POS/Flow/Functions). Incluye `shopify-dev` MCP con conocimiento nativo de Polaris.",
    },
    "shopify-functions": {
        "name": "Shopify Functions (Rust + Wasm)",
        "category": "E-commerce",
        "language": "Rust + GraphQL",
        "scaffold": [
            # Scaffold via Shopify CLI. Genera una app contenedora (necesario)
            # y dentro una extension de tipo product_discounts (la más común).
            # El user añade más extensions con `shopify app generate extension`.
            "npx --yes @shopify/create-app@latest --template remix --name __SLUG__ --no-install || "
            "(echo 'Fallback: ejecuta a mano `npm init @shopify/app@latest`' && exit 0)",
            # mkdir para la extension de ejemplo
            "mkdir -p extensions/discount-function/src",
            # shopify.extension.toml del function
            'cat > extensions/discount-function/shopify.extension.toml <<\'PCREATIVE STUDIO_EOF\'\n'
            'api_version = "2026-01"\n'
            '\n'
            '[[extensions]]\n'
            'type = "function"\n'
            'name = "discount-function"\n'
            'handle = "discount-function"\n'
            '\n'
            '[extensions.build]\n'
            'command = "cargo wasi build --release"\n'
            'path = "target/wasm32-wasi/release/discount_function.wasm"\n'
            '\n'
            '[extensions.targeting]\n'
            'target = "cart.lines.discounts.generate.run"\n'
            'input_query = "src/run.graphql"\n'
            'export = "run"\n'
            'PCREATIVE STUDIO_EOF',
            # Cargo.toml mínimo
            'cat > extensions/discount-function/Cargo.toml <<\'PCREATIVE STUDIO_EOF\'\n'
            '[package]\n'
            'name = "discount-function"\n'
            'version = "0.1.0"\n'
            'edition = "2021"\n'
            '\n'
            '[lib]\n'
            'crate-type = ["cdylib"]\n'
            'path = "src/run.rs"\n'
            '\n'
            '[dependencies]\n'
            'serde = { version = "1.0", features = ["derive"] }\n'
            'serde_json = "1.0"\n'
            'shopify_function = "0.10"\n'
            'PCREATIVE STUDIO_EOF',
            # input.graphql (qué datos recibe la function)
            'cat > extensions/discount-function/src/run.graphql <<\'PCREATIVE STUDIO_EOF\'\n'
            'query RunInput {\n'
            '  cart {\n'
            '    lines {\n'
            '      id\n'
            '      quantity\n'
            '      merchandise {\n'
            '        ... on ProductVariant {\n'
            '          id\n'
            '          product { id title vendor }\n'
            '        }\n'
            '      }\n'
            '      cost { totalAmount { amount currencyCode } }\n'
            '    }\n'
            '    cost { totalAmount { amount currencyCode } }\n'
            '  }\n'
            '  presentmentCurrencyRate\n'
            '}\n'
            'PCREATIVE STUDIO_EOF',
            # run.rs (la function en Rust)
            'cat > extensions/discount-function/src/run.rs <<\'PCREATIVE STUDIO_EOF\'\n'
            'use shopify_function::prelude::*;\n'
            'use shopify_function::Result;\n'
            '\n'
            '#[shopify_function]\n'
            'fn run(input: input::ResponseData) -> Result<output::FunctionRunResult> {\n'
            '    // Ejemplo: 10% off si el cart supera $100\n'
            '    let total: f64 = input.cart.cost.total_amount.amount.parse()?;\n'
            '    if total < 100.0 {\n'
            '        return Ok(output::FunctionRunResult { discounts: vec![], discount_application_strategy: output::DiscountApplicationStrategy::FIRST });\n'
            '    }\n'
            '    Ok(output::FunctionRunResult {\n'
            '        discount_application_strategy: output::DiscountApplicationStrategy::FIRST,\n'
            '        discounts: vec![output::Discount {\n'
            '            message: Some("10% off when you spend $100+".to_string()),\n'
            '            value: output::Value::Percentage(output::Percentage { value: 10.0 }),\n'
            '            targets: vec![output::Target::OrderSubtotal(output::OrderSubtotalTarget {\n'
            '                excluded_variant_ids: vec![],\n'
            '            })],\n'
            '        }],\n'
            '    })\n'
            '}\n'
            'PCREATIVE STUDIO_EOF',
            'cat > README-FUNCTIONS.md <<\'PCREATIVE STUDIO_EOF\'\n'
            '# __PROJECT__ — Shopify Functions\n'
            '\n'
            'Stack: **app Shopify + Functions en Rust compilados a Wasm**.\n'
            'Functions ejecutan lógica server-side sin servidor propio: Shopify\n'
            'los ejecuta dentro de su infraestructura como Wasm modules.\n'
            '\n'
            '## Targets disponibles\n'
            '\n'
            '| Target | Para qué |\n'
            '|---|---|\n'
            '| `cart.lines.discounts.generate.run` | Product/order discount (este ejemplo) |\n'
            '| `cart.delivery_options.transform.run` | Reordenar/renombrar/ocultar shipping options |\n'
            '| `cart.payment_methods.transform.run` | Reordenar/ocultar payment methods |\n'
            '| `cart.validations.generate.run` | Bloquear checkout si cart no cumple reglas |\n'
            '| `fulfillment_constraints.run` | Constraints sobre fulfillment (warehouse) |\n'
            '| `purchase.product_run.run` | Custom pricing/product transforms |\n'
            '\n'
            '## Comandos\n'
            '\n'
            '```bash\n'
            'rustup target add wasm32-wasi             # primera vez\n'
            'cargo install cargo-wasi                  # primera vez\n'
            'npm install\n'
            'npm run dev                               # arranca app + functions con tunnel\n'
            'shopify app function build                # build de Wasm\n'
            'shopify app function run                  # test local con input.json\n'
            'npm run deploy                            # publish (incluye Wasm)\n'
            '```\n'
            '\n'
            '## Generar más Functions\n'
            '\n'
            '```bash\n'
            'shopify app generate extension --type product_discounts --name my-discount\n'
            'shopify app generate extension --type delivery_customization --name reorder-shipping\n'
            'shopify app generate extension --type cart_validations --name min-quantity\n'
            '```\n'
            '\n'
            '## Por qué Rust\n'
            '\n'
            'Functions deben ejecutar en <5 ms (Shopify lo enforcea). Rust →\n'
            'Wasm es la única manera realista de garantizarlo + binarios\n'
            'pequeños. JS-Wasm también está disponible pero es más lento.\n'
            'PCREATIVE STUDIO_EOF',
        ],
        "min_version": "Shopify CLI 3.x / Rust 1.75+ / cargo-wasi",
        "skills": ["shopify/skills/theme-development"],
        "ux_pack": "shopify-functions",
        "notes": "Shopify Functions en Rust compilados a Wasm para lógica server-side custom: discounts (product/order/shipping), payment/delivery customization, cart validations, fulfillment constraints. Functions ejecutan dentro de la infra de Shopify (sin servidor propio). Bundle con app embebida (Polaris + App Bridge). Requiere rustup + cargo-wasi. Alternativa: JS-Wasm (más lento).",
    },
    "shopify-storefront-webcomponents": {
        "name": "Shopify Storefront Web Components",
        "category": "E-commerce",
        "language": "HTML + JS vanilla",
        "scaffold": [
            "mkdir -p assets",
            'cat > index.html <<\'PCREATIVE STUDIO_EOF\'\n'
            '<!DOCTYPE html>\n'
            '<html lang="en">\n'
            '<head>\n'
            '  <meta charset="UTF-8">\n'
            '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '  <title>__PROJECT__ — Shopify Storefront Web Components</title>\n'
            '  <link rel="stylesheet" href="assets/main.css">\n'
            '  <!-- Storefront Web Components loader (oficial Shopify) -->\n'
            '  <script type="module" src="https://cdn.shopify.com/storefront/web-components.esm.js"></script>\n'
            '</head>\n'
            '<body>\n'
            '  <header>\n'
            '    <h1>__PROJECT__</h1>\n'
            '    <shopify-context type="store" store="YOUR-SHOP.myshopify.com" token="YOUR_STOREFRONT_API_TOKEN">\n'
            '    </shopify-context>\n'
            '  </header>\n'
            '\n'
            '  <main>\n'
            '    <section class="featured">\n'
            '      <h2>Featured product</h2>\n'
            '      <shopify-product handle="example-product">\n'
            '        <shopify-product-media slot="media"></shopify-product-media>\n'
            '        <shopify-product-title slot="title"></shopify-product-title>\n'
            '        <shopify-product-price slot="price"></shopify-product-price>\n'
            '        <shopify-product-buy-button slot="cta">Buy now</shopify-product-buy-button>\n'
            '      </shopify-product>\n'
            '    </section>\n'
            '\n'
            '    <section class="cart">\n'
            '      <shopify-cart></shopify-cart>\n'
            '    </section>\n'
            '  </main>\n'
            '</body>\n'
            '</html>\n'
            'PCREATIVE STUDIO_EOF',
            'cat > assets/main.css <<\'PCREATIVE STUDIO_EOF\'\n'
            ':root { --color-bg: #fff; --color-text: #1a1a1a; --color-accent: #c56a4d; }\n'
            'body { margin: 0; font-family: system-ui, sans-serif; color: var(--color-text); background: var(--color-bg); }\n'
            'main { max-width: 1200px; margin: 0 auto; padding: 2rem 1rem; }\n'
            'shopify-product { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }\n'
            '@media (max-width: 768px) { shopify-product { grid-template-columns: 1fr; } }\n'
            'shopify-product-buy-button::part(button) { background: var(--color-accent); color: white; padding: 1rem 2rem; border: 0; border-radius: 999px; cursor: pointer; }\n'
            'PCREATIVE STUDIO_EOF',
            'cat > package.json <<\'PCREATIVE STUDIO_EOF\'\n'
            '{\n'
            '  "name": "__SLUG__",\n'
            '  "version": "0.1.0",\n'
            '  "private": true,\n'
            '  "scripts": {\n'
            '    "dev": "vite",\n'
            '    "build": "vite build",\n'
            '    "preview": "vite preview"\n'
            '  },\n'
            '  "devDependencies": {\n'
            '    "vite": "^6.0"\n'
            '  }\n'
            '}\n'
            'PCREATIVE STUDIO_EOF',
            'cat > .mcp.json <<\'PCREATIVE STUDIO_EOF\'\n'
            '{\n'
            '  "mcpServers": {\n'
            '    "shopify-dev": {\n'
            '      "command": "npx",\n'
            '      "args": ["-y", "@shopify/dev-mcp@latest"]\n'
            '    },\n'
            '    "shopify-storefront": {\n'
            '      "type": "http",\n'
            '      "url": "https://YOUR-SHOP.myshopify.com/api/mcp"\n'
            '    },\n'
            '    "shopify-storefront-catalog": {\n'
            '      "type": "http",\n'
            '      "url": "https://YOUR-SHOP.myshopify.com/api/ucp/mcp"\n'
            '    }\n'
            '  }\n'
            '}\n'
            'PCREATIVE STUDIO_EOF',
            'cat > README-WEBCOMPONENTS.md <<\'PCREATIVE STUDIO_EOF\'\n'
            '# __PROJECT__ — Shopify Storefront Web Components\n'
            '\n'
            'Embedded commerce en sites NO-Shopify (blogs, landing pages,\n'
            'WordPress, Webflow, sites estáticos). Los Web Components son\n'
            'oficiales de Shopify y se cargan via CDN — cero build complejo.\n'
            '\n'
            '## Setup\n'
            '\n'
            '1. Activa la **Storefront API** en tu Shopify Admin: Apps →\n'
            '   Develop apps → Create an app → Configure Storefront API\n'
            '   access. Selecciona scopes (unauthenticated_read_product_listings,\n'
            '   unauthenticated_write_checkouts).\n'
            '2. Copia el **Storefront access token** y pégalo en `index.html`\n'
            '   en `<shopify-context ... token="...">`.\n'
            '3. Sustituye `YOUR-SHOP.myshopify.com` por tu subdominio.\n'
            '4. `npm install && npm run dev` → http://localhost:5173\n'
            '\n'
            '## Componentes disponibles\n'
            '\n'
            '- `<shopify-context>` — root, configura store + token.\n'
            '- `<shopify-product handle="...">` — wrapper de producto.\n'
            '- `<shopify-product-media>` — media gallery.\n'
            '- `<shopify-product-title>` / `<shopify-product-price>` /\n'
            '  `<shopify-product-description>`.\n'
            '- `<shopify-product-variant-selector>` — selector de variantes.\n'
            '- `<shopify-product-quantity>` — input de cantidad.\n'
            '- `<shopify-product-buy-button>` — botón add-to-cart.\n'
            '- `<shopify-cart>` — cart drawer/widget.\n'
            '- `<shopify-collection handle="...">` — wrapper de collection.\n'
            '\n'
            '## Estilizado\n'
            '\n'
            'Cada componente expone `parts` CSS via `::part()`:\n'
            '\n'
            '```css\n'
            'shopify-product-buy-button::part(button) { background: red; }\n'
            'shopify-product-title::part(text) { font-size: 2rem; }\n'
            '```\n'
            '\n'
            '## Checkout\n'
            '\n'
            'Al añadir al carrito, el `<shopify-product-buy-button>` redirige\n'
            'al checkout hosted de tu tienda Shopify (tu-tienda.myshopify.com\n'
            '/checkout) — el carrito + payment + fulfillment los gestiona\n'
            'Shopify. Tu site solo se ocupa de la vitrina.\n'
            '\n'
            '## Casos de uso\n'
            '\n'
            '- Blog de marca con productos featured embebidos.\n'
            '- Landing page de campaña paid ads (separada del store).\n'
            '- WordPress / Webflow / Framer site que embebe productos.\n'
            '- Microsite de colaboración (artist drop, collab).\n'
            'PCREATIVE STUDIO_EOF',
        ],
        "min_version": "Storefront API 2026-01 / Modern browsers (custom elements)",
        "skills": ["shopify/skills/theme-development"],
        "ux_pack": "shopify-storefront-webcomponents",
        "notes": "Storefront Web Components oficiales de Shopify (CDN) para embebido commerce en sites NO-Shopify. HTML + JS vanilla, sin frameworks. Para blogs, landing pages, WordPress, Webflow, Framer. Checkout sigue siendo hosted en Shopify. Requiere Storefront API token con scopes unauthenticated_*.",
    },
    "shopify-checkout-extension": {
        "name": "Shopify Checkout UI Extension (Plus only)",
        "category": "E-commerce",
        "language": "TypeScript + React",
        "scaffold": [
            "npx --yes @shopify/create-app@latest --template remix --name __SLUG__ --no-install || "
            "(echo 'Fallback: ejecuta `npm init @shopify/app@latest`' && exit 0)",
            "mkdir -p extensions/checkout-ui-extension/src",
            'cat > extensions/checkout-ui-extension/shopify.extension.toml <<\'PCREATIVE STUDIO_EOF\'\n'
            'api_version = "2026-01"\n'
            '\n'
            '[[extensions]]\n'
            'type = "ui_extension"\n'
            'name = "checkout-ui-extension"\n'
            'handle = "checkout-ui-extension"\n'
            '\n'
            '[[extensions.targeting]]\n'
            'module = "./src/Checkout.tsx"\n'
            'target = "purchase.checkout.block.render"\n'
            '\n'
            '[extensions.capabilities]\n'
            'network_access = false\n'
            'block_progress = false\n'
            'api_access = true\n'
            'collect_buyer_consent.sms_marketing = false\n'
            'PCREATIVE STUDIO_EOF',
            'cat > extensions/checkout-ui-extension/src/Checkout.tsx <<\'PCREATIVE STUDIO_EOF\'\n'
            'import {\n'
            '  reactExtension,\n'
            '  Banner,\n'
            '  BlockStack,\n'
            '  Heading,\n'
            '  Text,\n'
            '  useApi,\n'
            '} from "@shopify/ui-extensions-react/checkout";\n'
            '\n'
            'export default reactExtension("purchase.checkout.block.render", () => <Extension />);\n'
            '\n'
            'function Extension() {\n'
            '  const { extension } = useApi();\n'
            '\n'
            '  return (\n'
            '    <BlockStack spacing="loose">\n'
            '      <Banner status="info">\n'
            '        <Text>Free shipping on orders over $50!</Text>\n'
            '      </Banner>\n'
            '      <Heading level={2}>Custom content for {extension.target}</Heading>\n'
            '    </BlockStack>\n'
            '  );\n'
            '}\n'
            'PCREATIVE STUDIO_EOF',
            'cat > extensions/checkout-ui-extension/package.json <<\'PCREATIVE STUDIO_EOF\'\n'
            '{\n'
            '  "name": "checkout-ui-extension",\n'
            '  "private": true,\n'
            '  "type": "module",\n'
            '  "dependencies": {\n'
            '    "@shopify/ui-extensions": "^2026.1.0",\n'
            '    "@shopify/ui-extensions-react": "^2026.1.0",\n'
            '    "react": "^18.0.0"\n'
            '  }\n'
            '}\n'
            'PCREATIVE STUDIO_EOF',
            'cat > README-CHECKOUT.md <<\'PCREATIVE STUDIO_EOF\'\n'
            '# __PROJECT__ — Shopify Checkout UI Extension\n'
            '\n'
            'Stack: **app Shopify + extension UI custom en checkout (solo\n'
            'Shopify Plus)**. UI custom dentro del checkout hosted de Shopify\n'
            '— donde la app puede insertar banners, surveys, custom fields,\n'
            'upsells, loyalty, etc.\n'
            '\n'
            '## ⚠️ Solo Shopify Plus\n'
            '\n'
            'Checkout UI Extensions REQUIEREN que la tienda tenga el plan\n'
            'Shopify Plus. En tiendas non-Plus, la extension no se carga.\n'
            'Mercado: agencias Plus, brands premium, B2B.\n'
            '\n'
            '## Targets disponibles\n'
            '\n'
            '| Target | Dónde aparece |\n'
            '|---|---|\n'
            '| `purchase.checkout.block.render` | Bloque libre que el merchant coloca |\n'
            '| `purchase.checkout.delivery-address.render-before` | Antes del bloque de shipping |\n'
            '| `purchase.checkout.payment-method-list.render-after` | Tras la lista de payment methods |\n'
            '| `purchase.checkout.shipping-option-list.render-after` | Tras shipping options |\n'
            '| `purchase.checkout.cart-line-item.render-after` | Tras cada line item |\n'
            '| `purchase.checkout.header.render-after` | Header del checkout |\n'
            '| `purchase.checkout.footer.render-after` | Footer del checkout |\n'
            '| `purchase.thank-you.block.render` | Thank you page |\n'
            '| `purchase.order-status.block.render` | Order status page |\n'
            '\n'
            '## Capabilities (en shopify.extension.toml)\n'
            '\n'
            '- `network_access` — para hacer fetch a tu backend.\n'
            '- `block_progress` — para bloquear avance del checkout si tu UI\n'
            '  requiere acción (peligroso, úsalo con cuidado).\n'
            '- `api_access` — para queries Storefront API desde la extension.\n'
            '- `collect_buyer_consent.sms_marketing` — para opt-in SMS.\n'
            '\n'
            '## Comandos\n'
            '\n'
            '```bash\n'
            'npm install\n'
            'npm run dev                                # arranca app + extension con tunnel\n'
            'shopify app generate extension --type checkout_ui_extension --name <name>  # generar más\n'
            'npm run deploy                             # publish\n'
            '```\n'
            '\n'
            '## API disponible\n'
            '\n'
            '`useApi()` da acceso a: `buyerJourney`, `applyCartLinesChange`,\n'
            '`applyDiscountCodeChange`, `applyAttributeChange`, `cost`, `lines`,\n'
            '`shippingAddress`, `paymentOption`, `extensionPoint`, etc.\n'
            '\n'
            '## NO permitido\n'
            '\n'
            '- Tracking de PII fuera de los webhooks GDPR.\n'
            '- Custom JS DOM manipulation (sandboxed Worker — solo componentes).\n'
            '- Network access sin declararlo en capabilities.\n'
            'PCREATIVE STUDIO_EOF',
        ],
        "min_version": "Shopify CLI 3.x / Shopify Plus / React 18+",
        "skills": ["shopify/skills/theme-development"],
        "ux_pack": "shopify-checkout-extension",
        "notes": "Checkout UI Extension (solo Shopify Plus) para customizar el checkout hosted con bloques React sandboxeados (@shopify/ui-extensions-react/checkout). 9 targets disponibles (block.render, delivery-address, payment-method, shipping-option, cart-line-item, header, footer, thank-you, order-status). Mercado: agencias Plus + brands premium + B2B. Ticket por trabajo: alto.",
    },
    "magento-hyva": {
        "name": "Magento 2 + Hyvä Theme (OSL 3.0)",
        "category": "E-commerce",
        "language": "PHP + Tailwind + Alpine.js",
        "scaffold": [
            # ASUME Magento 2.4.8+ ya instalado en este directorio + composer
            # configurado con la auth de Hyvä packagist (registro gratis en
            # https://hyva.io). Si no, el setup fallará con mensajes claros.
            "echo '→ Comprobando Magento + Hyvä prerequisites…'",
            "command -v composer >/dev/null || { echo '❌ composer no instalado'; exit 1; }",
            "[ -f bin/magento ] || echo '⚠️  bin/magento no encontrado — instala Magento 2.4.8+ ANTES de continuar'",
            # Composer require del parent Hyvä (gratis desde Nov 2025, OSL 3.0)
            "composer require hyva-themes/magento2-default-theme hyva-themes/magento2-theme-module --no-interaction || \\\n"
            "  echo '⚠️  composer require Hyvä falló — necesitas key Hyvä gratis (hyva.io account → packagist credentials)'",
            # Freento MCP — server MCP nativo para Magento 2 (MIT)
            "composer require freento/module-mcp --no-interaction || \\\n"
            "  echo '⚠️  composer require Freento MCP falló — instálalo a mano si quieres conectar la IA al store'",
            "[ -f bin/magento ] && bin/magento module:enable Freento_Mcp 2>&1 | head -5 || true",
            "[ -f bin/magento ] && bin/magento setup:upgrade --keep-generated 2>&1 | tail -3 || true",
            "[ -f bin/magento ] && bin/magento cache:flush 2>&1 | tail -3 || true",
            # .mcp.json con el Freento MCP — placeholders YOUR-STORE + YOUR_TOKEN
            'cat > .mcp.json <<\'PCREATIVE STUDIO_EOF\'\n'
            '{\n'
            '  "mcpServers": {\n'
            '    "magento": {\n'
            '      "type": "http",\n'
            '      "url": "https://YOUR-STORE.com/freento_mcp/index/index",\n'
            '      "headers": { "Authorization": "Bearer YOUR_ACCESS_TOKEN" },\n'
            '      "_doc": "Freento MCP (MIT) — Magento 2 store como MCP server. Genera el token en Admin → System → Freento MCP → AI MCP Clients."\n'
            '    }\n'
            '  }\n'
            '}\n'
            'PCREATIVE STUDIO_EOF',
            # Crear estructura del child theme
            "mkdir -p app/design/frontend/Pcreative/__SLUG__/{etc,web/{css/source,tailwind,images},Magento_Theme/layout,Magento_Catalog/templates/product}",
            # registration.php
            'cat > app/design/frontend/Pcreative/__SLUG__/registration.php <<\'PCREATIVE STUDIO_EOF\'\n'
            '<?php\n'
            "use Magento\\Framework\\Component\\ComponentRegistrar;\n"
            "ComponentRegistrar::register(ComponentRegistrar::THEME, 'frontend/Pcreative/__SLUG__', __DIR__);\n"
            'PCREATIVE STUDIO_EOF',
            # theme.xml — declara parent Hyva/default
            'cat > app/design/frontend/Pcreative/__SLUG__/theme.xml <<\'PCREATIVE STUDIO_EOF\'\n'
            "<?xml version=\"1.0\"?>\n"
            "<theme xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:noNamespaceSchemaLocation=\"urn:magento:framework:Config/etc/theme.xsd\">\n"
            "    <title>__PROJECT__ (Hyvä child)</title>\n"
            "    <parent>Hyva/default</parent>\n"
            "    <media><preview_image>media/preview.jpg</preview_image></media>\n"
            "</theme>\n"
            'PCREATIVE STUDIO_EOF',
            # composer.json del child theme
            'cat > app/design/frontend/Pcreative/__SLUG__/composer.json <<\'PCREATIVE STUDIO_EOF\'\n'
            '{\n'
            '  "name": "pcreative/magento2-theme-__SLUG__",\n'
            '  "description": "__PROJECT__ — Hyvä child theme",\n'
            '  "type": "magento2-theme",\n'
            '  "version": "0.1.0",\n'
            '  "license": "OSL-3.0",\n'
            '  "require": {\n'
            '    "php": "^8.1",\n'
            '    "hyva-themes/magento2-default-theme": "^1.4.0"\n'
            '  },\n'
            '  "autoload": { "files": ["registration.php"] }\n'
            '}\n'
            'PCREATIVE STUDIO_EOF',
            # web/tailwind/package.json — Tailwind v4
            'cat > app/design/frontend/Pcreative/__SLUG__/web/tailwind/package.json <<\'PCREATIVE STUDIO_EOF\'\n'
            '{\n'
            '  "name": "__SLUG__-tailwind",\n'
            '  "private": true,\n'
            '  "scripts": {\n'
            '    "build": "tailwindcss -i tailwind-source.css -o ../css/styles.css",\n'
            '    "build-prod": "tailwindcss -i tailwind-source.css -o ../css/styles.css --minify",\n'
            '    "watch": "tailwindcss -i tailwind-source.css -o ../css/styles.css --watch"\n'
            '  },\n'
            '  "devDependencies": {\n'
            '    "tailwindcss": "^4.0",\n'
            '    "@tailwindcss/cli": "^4.0",\n'
            '    "@tailwindcss/forms": "^0.5.7",\n'
            '    "@tailwindcss/typography": "^0.5.10"\n'
            '  }\n'
            '}\n'
            'PCREATIVE STUDIO_EOF',
            # tailwind.config.js — apunta al parent Hyva
            'cat > app/design/frontend/Pcreative/__SLUG__/web/tailwind/tailwind.config.js <<\'PCREATIVE STUDIO_EOF\'\n'
            "import path from 'path';\n"
            "import hyvaConfig from '../../../../../../vendor/hyva-themes/magento2-default-theme/Magento_Theme/web/tailwind/tailwind.config.js';\n"
            "\n"
            "export default {\n"
            "  presets: [hyvaConfig],\n"
            "  content: [\n"
            "    '../../**/*.phtml',\n"
            "    '../../**/*.html',\n"
            "    '../../**/*.js',\n"
            "    path.resolve(__dirname, '../../../../../../app/code/**/*.phtml'),\n"
            "  ],\n"
            "  theme: {\n"
            "    extend: {\n"
            "      colors: { brand: { DEFAULT: '#C56A4D', accent: '#8FA68E' } },\n"
            "      fontFamily: {\n"
            "        sans: ['Inter', 'system-ui', 'sans-serif'],\n"
            "        display: ['Fraunces', 'Georgia', 'serif']\n"
            "      }\n"
            "    }\n"
            "  }\n"
            "}\n"
            'PCREATIVE STUDIO_EOF',
            # tailwind-source.css con @import "tailwindcss"
            'cat > app/design/frontend/Pcreative/__SLUG__/web/tailwind/tailwind-source.css <<\'PCREATIVE STUDIO_EOF\'\n'
            '@import "tailwindcss";\n'
            '\n'
            '/* Custom global styles del child theme */\n'
            'body { font-family: theme(fontFamily.sans); }\n'
            'h1, h2, h3 { font-family: theme(fontFamily.display); }\n'
            'PCREATIVE STUDIO_EOF',
            # etc/view.xml (heredado de Hyva, pero file vacío para override)
            'cat > app/design/frontend/Pcreative/__SLUG__/etc/view.xml <<\'PCREATIVE STUDIO_EOF\'\n'
            "<?xml version=\"1.0\"?>\n"
            "<view xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:noNamespaceSchemaLocation=\"urn:magento:framework:Config/etc/view.xsd\">\n"
            "  <!-- Override de view config si quieres tamaños de imagen distintos -->\n"
            "</view>\n"
            'PCREATIVE STUDIO_EOF',
            # Magento_Theme/layout/default.xml — ejemplo de layout override
            'cat > app/design/frontend/Pcreative/__SLUG__/Magento_Theme/layout/default.xml <<\'PCREATIVE STUDIO_EOF\'\n'
            "<?xml version=\"1.0\"?>\n"
            "<page xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:noNamespaceSchemaLocation=\"urn:magento:framework:View/Layout/etc/page_configuration.xsd\">\n"
            "  <body>\n"
            "    <referenceContainer name=\"header.container\">\n"
            "      <block class=\"Magento\\Framework\\View\\Element\\Template\" name=\"custom.announcement\" template=\"Magento_Theme::announcement.phtml\" />\n"
            "    </referenceContainer>\n"
            "  </body>\n"
            "</page>\n"
            'PCREATIVE STUDIO_EOF',
            # README-MAGENTO.md
            'cat > README-MAGENTO.md <<\'PCREATIVE STUDIO_EOF\'\n'
            '# __PROJECT__ — Magento 2 + Hyvä child theme\n'
            '\n'
            'Stack: **Magento 2.4.8+** (Open Source o Adobe Commerce) +\n'
            '**Hyvä Theme 1.4.4+** (OSL 3.0 + AFL 3.0, OSS desde 2025-11-10) +\n'
            '**Tailwind v4** + **Alpine.js**.\n'
            '\n'
            '## Prerequisites\n'
            '\n'
            '1. **Magento 2.4.8+** ya instalado (este scaffold NO lo instala —\n'
            '   asume tu setup Composer + base de datos + bin/magento listos).\n'
            '2. **Cuenta gratis en hyva.io** → packagist credentials para\n'
            '   composer auth (necesarios incluso siendo OSS por gobernanza\n'
            '   del registry Hyvä).\n'
            '3. **Node 22 + npm** para build de Tailwind v4.\n'
            '4. **PHP 8.1+**.\n'
            '\n'
            '## Estructura generada\n'
            '\n'
            '```\n'
            'app/design/frontend/Pcreative/__SLUG__/\n'
            '├── composer.json                      # type=magento2-theme, OSL-3.0\n'
            '├── registration.php                   # ComponentRegistrar\n'
            '├── theme.xml                          # parent=Hyva/default\n'
            '├── etc/view.xml                       # view config overrides\n'
            '├── web/\n'
            '│   ├── css/source/                    # less/scss source (heredado)\n'
            '│   ├── images/                        # logo, preview.jpg\n'
            '│   └── tailwind/\n'
            '│       ├── package.json               # Tailwind v4 build scripts\n'
            '│       ├── tailwind.config.js         # preset Hyvä + custom theme\n'
            '│       └── tailwind-source.css        # @import "tailwindcss"\n'
            '├── Magento_Theme/layout/default.xml   # override del default page\n'
            '└── Magento_Catalog/templates/product/ # .phtml overrides\n'
            '```\n'
            '\n'
            '## Build & activate\n'
            '\n'
            '```bash\n'
            '# 1. Composer install (re-genera autoload con el nuevo theme)\n'
            'composer dump-autoload\n'
            '\n'
            '# 2. Build Tailwind\n'
            'cd app/design/frontend/Pcreative/__SLUG__/web/tailwind\n'
            'npm install\n'
            'npm run build-prod\n'
            'cd -\n'
            '\n'
            '# 3. Aplicar el theme via Magento CLI\n'
            'bin/magento setup:upgrade\n'
            'bin/magento setup:di:compile\n'
            'bin/magento setup:static-content:deploy -f\n'
            'bin/magento cache:flush\n'
            '\n'
            '# 4. Asignar el theme a un store en Admin\n'
            '#    Stores > Configuration > Design > Design Theme = Pcreative/__SLUG__\n'
            '```\n'
            '\n'
            '## Hyvä vs Luma\n'
            '\n'
            '| Métrica | Luma (default Magento) | Hyvä |\n'
            '|---|---|---|\n'
            '| Lighthouse mobile | 25-40 | 90-100 |\n'
            '| JS bundle | 1.5+ MB | ~95 KB |\n'
            '| LCP | 3-6s | < 1.5s |\n'
            '| Adopción 2026 | declining | dominante en builds nuevos |\n'
            '\n'
            'Hyvä reemplaza RequireJS + KnockoutJS + heavy CSS con Tailwind + Alpine.js.\n'
            '\n'
            '## Override de templates\n'
            '\n'
            'Copia el .phtml original del módulo a la misma ruta dentro de tu\n'
            'theme. Ejemplo override `list.phtml` de catálogo:\n'
            '\n'
            '```bash\n'
            'cp vendor/hyva-themes/magento2-default-theme/Magento_Catalog/templates/product/list.phtml \\\n'
            '   app/design/frontend/Pcreative/__SLUG__/Magento_Catalog/templates/product/list.phtml\n'
            '```\n'
            '\n'
            'Luego edita libremente.\n'
            '\n'
            '## MCP — Freento MCP server para Magento 2 (MIT)\n'
            '\n'
            'Pcreative Studio ha instalado el módulo `freento/module-mcp` automáticamente.\n'
            'Esto convierte tu Magento en un **MCP server HTTP**: la IA (Claude\n'
            'Code, Cursor, Windsurf) puede consultar productos, órdenes,\n'
            'inventario, clientes, admins y system health del store con lenguaje\n'
            'natural.\n'
            '\n'
            'Tools disponibles: orders, quotes, credit memos, products, stock,\n'
            'customers, admin users, system status.\n'
            '\n'
            '### Setup OAuth (3 pasos en Admin)\n'
            '\n'
            '1. **System → Freento MCP → ACL Rules** → Add New Role → marca los\n'
            '   tools que quieras exponer (sales / catalog / customer / admin /\n'
            '   system) → Save.\n'
            '2. **System → Freento MCP → AI MCP Clients** → Add New Client →\n'
            '   asigna la Role del paso 1 → Save. Copia el Client ID + Client\n'
            '   Secret.\n'
            '3. Abre ese Client → **Generate OTP** (válido 24h) → **Generate\n'
            '   Token** introduciendo el OTP → copia el **Access Token**.\n'
            '\n'
            '### Wire el token en `.mcp.json`\n'
            '\n'
            'El scaffold ha dejado un `.mcp.json` con placeholders. Sustituye:\n'
            '\n'
            '```json\n'
            '{\n'
            '  "mcpServers": {\n'
            '    "magento": {\n'
            '      "type": "http",\n'
            '      "url": "https://tu-store.com/freento_mcp/index/index",\n'
            '      "headers": { "Authorization": "Bearer EL_TOKEN_DEL_ADMIN" }\n'
            '    }\n'
            '  }\n'
            '}\n'
            '```\n'
            '\n'
            'Reinicia Claude Code (o tu cliente MCP) y ya tienes el store como\n'
            'tool callable.\n'
            '\n'
            '## Distribución\n'
            '\n'
            'Vende como composer package (`pcreative/magento2-theme-__SLUG__`)\n'
            'en tu propio repo packagist, o súbelo a Adobe Commerce Marketplace\n'
            '($99-499 por theme). Tu propio sistema de licencias gates updates +\n'
            'features premium vía un módulo helper (ver README.licensing.md\n'
            'si has activado el sistema de licencias).\n'
            'PCREATIVE STUDIO_EOF',
        ],
        "min_version": "Magento 2.4.8+ / Hyvä 1.4.4+ / PHP 8.1+ / Node 22+",
        "skills": [],
        "ux_pack": "magento-hyva",
        "notes": "Magento 2 + Hyvä Theme — el frontend OSS más usado para Magento 2 desde Nov 2025 (antes era €1000/store). Tailwind v4 + Alpine.js reemplazando RequireJS/KnockoutJS, Lighthouse 90+ vs 25-40 de Luma. Stack scaffoldea SOLO el child theme — Magento debe estar ya instalado. Requiere cuenta gratis en hyva.io para composer auth packagist.",
    },
    "saleor-nextjs": {
        "name": "Saleor + Next.js Storefront (BSD-3)",
        "category": "E-commerce",
        "language": "TypeScript + GraphQL",
        "scaffold": [
            "echo '→ Clonando Saleor Storefront oficial (Next.js 15 + App Router)…'",
            # Clone the official storefront into current dir. The official repo
            # ships as a flat template; we strip the .git so it becomes our own.
            "git clone --depth 1 https://github.com/saleor/storefront.git _saleor_tmp 2>&1 | head",
            "cp -a _saleor_tmp/. . && rm -rf _saleor_tmp/.git _saleor_tmp",
            # Set package name + version
            "if [ -f package.json ] && command -v jq >/dev/null 2>&1; then "
            "jq '.name = \"__SLUG__\" | .version = \"0.1.0\"' package.json > _pkg.tmp && mv _pkg.tmp package.json; fi",
            # .env baseline pointing to demo (user must replace)
            'cat > .env.example <<\'PCREATIVE STUDIO_EOF\'\n'
            '# Apuntar al GraphQL endpoint de tu instancia Saleor (Cloud o self-hosted)\n'
            'NEXT_PUBLIC_SALEOR_API_URL=https://store-public-uefa-iad.saleor.cloud/graphql/\n'
            'NEXT_PUBLIC_STOREFRONT_URL=http://localhost:3000\n'
            'PCREATIVE STUDIO_EOF',
            "cp .env.example .env 2>/dev/null || true",
            'cat > README-SALEOR.md <<\'PCREATIVE STUDIO_EOF\'\n'
            '# __PROJECT__ — Saleor Storefront (Next.js)\n'
            '\n'
            'Storefront headless oficial de Saleor — React 18 + Next.js 15 App\n'
            'Router + TypeScript + GraphQL Codegen + Tailwind CSS. Licencia BSD-3.\n'
            '\n'
            '## Backend Saleor — 3 opciones\n'
            '\n'
            '1. **Saleor Cloud** (managed, $1k+/mes enterprise) — más rápido para empezar.\n'
            '2. **Self-hosted** — `docker compose up` desde https://github.com/saleor/saleor\n'
            '   (Python/Django + Postgres + Redis + Celery). Free.\n'
            '3. **Demo público** — `store-public-uefa-iad.saleor.cloud/graphql/` (datos\n'
            '   de prueba). Útil para empezar a desarrollar sin backend propio.\n'
            '\n'
            '## Comandos\n'
            '\n'
            '```bash\n'
            'pnpm install        # (o npm install)\n'
            'pnpm dev            # http://localhost:3000\n'
            'pnpm generate       # GraphQL codegen tras editar queries\n'
            'pnpm build          # production build\n'
            'pnpm start          # serve production build\n'
            '```\n'
            '\n'
            '## Arquitectura clave\n'
            '\n'
            '- **App Router** (`src/app/`) — server components + route handlers.\n'
            '- **GraphQL queries** en `src/gql/` con `.graphql` files → codegen genera\n'
            '  TypedDocumentString para zero-overhead types + tree-shaking.\n'
            '- **Channels + Regions** — multi-currency / multi-language via\n'
            '  Saleor channels (definidos en Admin → Configuration → Channels).\n'
            '- **Checkout** — `/checkout` route con multi-step Stripe/Adyen.\n'
            '- **Custom apps** — instalables en Saleor Admin via OAuth.\n'
            '\n'
            '## Cuando elegir Saleor vs Shopify/Hydrogen\n'
            '\n'
            '| Caso | Saleor | Hydrogen |\n'
            '|---|---|---|\n'
            '| Multi-channel B2B + B2C en una | ✓ nativo | requiere apps Plus |\n'
            '| Enterprise catalog modelling | ✓ | limitado |\n'
            '| Self-hosted total control | ✓ | sólo Oxygen |\n'
            '| Plug-and-play SaaS | ✗ (self-host esfuerzo) | ✓ |\n'
            '| GraphQL-first | ✓ desde día 0 | ✓ |\n'
            'PCREATIVE STUDIO_EOF',
        ],
        "min_version": "Saleor 3.20+ / Next.js 15 / Node 22+ / GraphQL",
        "skills": [],
        "ux_pack": "saleor-nextjs",
        "notes": "Storefront oficial Saleor (Next.js 15 + App Router + GraphQL Codegen + Tailwind). Multi-channel multi-region enterprise. Backend Saleor (Python/Django) self-host gratis o Saleor Cloud (paid). Licencia BSD-3. Para catálogos B2B+B2C complejos con multi-currency real.",
    },
    "restaurant-saas": {
        "name": "Restaurant SaaS (Next.js + Supabase + Stripe · carta QR + pedidos + pago + admin)",
        "category": "E-commerce",
        "language": "TypeScript + Next.js + Supabase + Stripe",
        "scaffold": [
            "echo '→ Restaurant SaaS — Next.js 15 + Supabase + Stripe…'",
            'npx --yes create-next-app@latest . --ts --tailwind --eslint --app --src-dir --import-alias "@/*" --no-turbopack --use-npm',
            "echo '→ Dependencias (Supabase + Stripe + QR)…'",
            "npm install @supabase/supabase-js @supabase/ssr stripe @stripe/stripe-js qrcode 2>&1 | tail -3",
            "npm install -D @types/qrcode 2>&1 | tail -2",
            "echo '→ Copiando boilerplate (esquema BD, carta QR, pedidos, pago, panel admin)…'",
            "cp -a __TFDIR__/templates/restaurant-saas/. . 2>/dev/null || echo '(plantilla no encontrada — el agente la generará desde el brief)'",
            "cp .env.example .env.local 2>/dev/null || true",
        ],
        "min_version": "Next.js 15 / Supabase / Stripe / Node 20+",
        "skills": ["anthropics/skills/frontend-design", "vercel/skills/nextjs-best-practices"],
        "ux_pack": "restaurant-saas",
        "notes": (
            "Mini-SaaS para restaurantes/bares. Boilerplate INCLUIDO (no lo rehagas, "
            "rellénalo con el brief): Next.js 15 App Router + TS + Tailwind. "
            "Supabase Postgres con esquema `supabase/schema.sql` (tablas: restaurants, "
            "categories, menu_items, dining_tables [QR], orders, order_items) + RLS. "
            "Carta digital pública por QR en `/m/[table]` (cliente escanea → ve carta → "
            "añade al carrito → paga). Pago con Stripe (`/api/checkout` + webhook "
            "`/api/stripe/webhook` que marca el pedido pagado). Panel admin en `/admin` "
            "(login Supabase Auth, pedidos en tiempo real vía Realtime, CRUD de carta, "
            "generación de QR por mesa). El brief del negocio está en `src/data/brief.json` "
            "(datos + carta real). Tu trabajo: cargar esa carta en la BD (seed), aplicar el "
            "branding/colores/fotos del negocio y dejar el diseño x100 respecto a su web actual. "
            "Variables en `.env.example` (Supabase URL/keys + Stripe keys)."
        ),
    },
    "booking-saas": {
        "name": "Booking SaaS (Next.js + Supabase + Stripe · reservas online + agenda + recordatorios)",
        "category": "E-commerce",
        "language": "TypeScript + Next.js + Supabase + Stripe",
        "scaffold": [
            "echo '→ Booking SaaS — Next.js 15 + Supabase + Stripe…'",
            'npx --yes create-next-app@latest . --ts --tailwind --eslint --app --src-dir --import-alias "@/*" --no-turbopack --use-npm',
            "echo '→ Dependencias (Supabase + Stripe + fechas)…'",
            "npm install @supabase/supabase-js @supabase/ssr stripe @stripe/stripe-js date-fns 2>&1 | tail -3",
            "echo '→ Copiando boilerplate (esquema BD anti-doble-reserva, agenda, reserva pública, depósito, panel admin)…'",
            "cp -a __TFDIR__/templates/booking-saas/. . 2>/dev/null || echo '(plantilla no encontrada — el agente la generará desde el brief)'",
            "cp .env.example .env.local 2>/dev/null || true",
        ],
        "min_version": "Next.js 15 / Supabase / Stripe / Node 20+",
        "skills": ["anthropics/skills/frontend-design", "vercel/skills/nextjs-best-practices"],
        "ux_pack": "booking-saas",
        "notes": (
            "Mini-SaaS de RESERVAS para servicios con cita (peluquerías, estética, "
            "fisio, clínicas, talleres…). Boilerplate INCLUIDO (no lo rehagas, "
            "rellénalo con el brief): Next.js 15 App Router + TS + Tailwind. "
            "Supabase Postgres con esquema `supabase/schema.sql` (tablas: business, "
            "staff, services [con duración y precio], appointments, customers) + RLS "
            "(lectura pública de servicios/horarios, escritura solo admin). "
            "CLAVE ANTI-DOBLE-RESERVA a nivel BD: extensión `btree_gist` + constraint "
            "EXCLUDE USING GIST (staff_id WITH =, tstzrange(starts_at, ends_at, '[)') "
            "WITH &&) WHERE (status <> 'cancelled') — dos clientes NUNCA pillan el mismo "
            "hueco. Reserva pública en `/reservar`: el cliente elige servicio → ve slots "
            "libres (calculados por duración + horario, refresco realtime de Supabase) → "
            "confirma. Depósito opcional con Stripe (`/api/checkout` + webhook "
            "`/api/stripe/webhook` idempotente con tabla processed_webhooks). Panel admin "
            "en `/admin` (login Supabase Auth, agenda del día en tiempo real, CRUD de "
            "servicios y horarios, gestión de citas). Webhook: raw body con req.text() → "
            "stripe.webhooks.constructEvent → idempotencia en la MISMA transacción → 200 "
            "rápido. El brief está en `src/data/brief.json` (datos + servicios reales en "
            "menu.sections[].items[] con precio y duración). Variables en `.env.example`."
        ),
    },
    "shop-lite": {
        "name": "Shop Lite (Next.js + Supabase + Stripe · catálogo + carrito + pago/WhatsApp)",
        "category": "E-commerce",
        "language": "TypeScript + Next.js + Supabase + Stripe",
        "scaffold": [
            "echo '→ Shop Lite — Next.js 15 + Supabase + Stripe…'",
            'npx --yes create-next-app@latest . --ts --tailwind --eslint --app --src-dir --import-alias "@/*" --no-turbopack --use-npm',
            "echo '→ Dependencias (Supabase + Stripe)…'",
            "npm install @supabase/supabase-js @supabase/ssr stripe @stripe/stripe-js 2>&1 | tail -3",
            "echo '→ Copiando boilerplate (esquema BD, catálogo, carrito, checkout Stripe/WhatsApp, panel admin)…'",
            "cp -a __TFDIR__/templates/shop-lite/. . 2>/dev/null || echo '(plantilla no encontrada — el agente la generará desde el brief)'",
            "cp .env.example .env.local 2>/dev/null || true",
        ],
        "min_version": "Next.js 15 / Supabase / Stripe / Node 20+",
        "skills": ["anthropics/skills/frontend-design", "vercel/skills/nextjs-best-practices"],
        "ux_pack": "shop-lite",
        "notes": (
            "Mini-tienda para comercios de retail (boutiques, floristerías, ferreterías, "
            "ópticas…) que aún no venden online. Boilerplate INCLUIDO (no lo rehagas, "
            "rellénalo con el brief): Next.js 15 App Router + TS + Tailwind. Supabase "
            "Postgres con esquema `supabase/schema.sql` (tablas: shop, categories, "
            "products [precio, stock, imagen], orders, order_items) + RLS (catálogo de "
            "lectura pública, escritura solo admin con is_admin((select auth.uid())), "
            "auth envuelto en select y columnas indexadas). Catálogo público en `/` y "
            "`/producto/[slug]`, carrito en cliente (localStorage). DOS modos de checkout "
            "(el comercio elige por env): (1) Stripe (`/api/checkout` + webhook idempotente "
            "`/api/stripe/webhook` con tabla processed_webhooks, eventos "
            "checkout.session.completed + payment_intent.succeeded) o (2) pedido por "
            "WhatsApp (link wa.me con el carrito pre-rellenado, sin pasarela — baja la "
            "fricción al comercio que empieza). Panel admin en `/admin` (login Supabase "
            "Auth, CRUD de productos/categorías, pedidos en tiempo real). El brief está en "
            "`src/data/brief.json` (datos + productos reales en menu.sections[].items[] "
            "con precio e imagen). Variables en `.env.example` (Supabase + Stripe + "
            "NEXT_PUBLIC_CHECKOUT_MODE=stripe|whatsapp + NEXT_PUBLIC_WHATSAPP)."
        ),
    },
    "pro-landing": {
        "name": "Pro Landing (Next.js + Tailwind · landing premium + captación de leads)",
        "category": "Sitios y Landing",
        "language": "TypeScript + Next.js + Tailwind",
        "scaffold": [
            "echo '→ Pro Landing — Next.js 15 + Tailwind…'",
            'npx --yes create-next-app@latest . --ts --tailwind --eslint --app --src-dir --import-alias "@/*" --no-turbopack --use-npm',
            "echo '→ Copiando boilerplate (landing premium + formulario de captación anti-spam)…'",
            "cp -a __TFDIR__/templates/pro-landing/. . 2>/dev/null || echo '(plantilla no encontrada — el agente la generará desde el brief)'",
            "cp .env.example .env.local 2>/dev/null || true",
        ],
        "min_version": "Next.js 15 / Node 20+",
        "skills": ["anthropics/skills/frontend-design", "vercel/skills/nextjs-best-practices"],
        "ux_pack": "pro-landing",
        "notes": (
            "Landing premium de CAPTACIÓN para servicios profesionales y negocios locales "
            "(abogados, inmobiliarias, gimnasios, gestorías, reformas…) y como fallback "
            "genérico. Boilerplate INCLUIDO (no lo rehagas, rellénalo con el brief): "
            "Next.js 15 App Router + TS + Tailwind, SIN backend pesado (no Supabase). "
            "Secciones: hero con propuesta de valor, servicios (de menu.sections[].items[]), "
            "prueba social (reseñas/rating de Google del brief), FAQ, CTA y un FORMULARIO "
            "DE CONTACTO/LEAD con anti-spam por capas: honeypot (campo oculto que los bots "
            "rellenan), rate-limit básico por IP en memoria y validación de email; el lead "
            "se envía por email vía un Server Action a `/api/lead` (configurable: log, "
            "Resend o webhook). Pensada para SEO local (metadata, JSON-LD LocalBusiness, "
            "Open Graph). El brief está en `src/data/brief.json` (datos + servicios reales). "
            "Variables en `.env.example` (LEAD_EMAIL / RESEND_API_KEY opcionales)."
        ),
    },
    "vendure": {
        "name": "Vendure (MIT, NestJS + GraphQL)",
        "category": "E-commerce",
        "language": "TypeScript + NestJS + GraphQL",
        "scaffold": [
            # @vendure/create es interactivo; el flag --skip-init evita prompts
            # cuando se puede; si falla, fallback al user.
            "npx --yes @vendure/create@latest . --quick --skip-confirmation || "
            "(echo '⚠️ scaffold no-interactivo no disponible; ejecuta `npx @vendure/create .` manualmente' && exit 0)",
            'cat > README-VENDURE.md <<\'PCREATIVE STUDIO_EOF\'\n'
            '# __PROJECT__ — Vendure (headless commerce)\n'
            '\n'
            'Backend de ecommerce headless construido con NestJS + TypeScript +\n'
            'GraphQL + TypeORM. Licencia MIT. Plugin-first architecture.\n'
            '\n'
            '## Stack\n'
            '\n'
            '- **Vendure Core 3.x** — backend.\n'
            '- **NestJS** — framework de Node.js para aplicaciones server.\n'
            '- **GraphQL** — schema generado dinámicamente del catálogo + channels.\n'
            '- **TypeORM** — Postgres recomendado (también MySQL/MariaDB/SQLite).\n'
            '- **Admin UI** (Angular) — embebida en `/admin`.\n'
            '- **Storefront opcional** — Next.js / Remix / Angular starter.\n'
            '\n'
            '## Comandos\n'
            '\n'
            '```bash\n'
            'npm install\n'
            'npm run dev            # backend en localhost:3000, admin en /admin\n'
            'npm run dev:storefront # si has elegido incluir storefront durante el scaffold\n'
            'npx vendure add        # añadir plugins (e.g. asset-server, email)\n'
            '```\n'
            '\n'
            '## Plugins típicos\n'
            '\n'
            '- `@vendure/asset-server-plugin` — gestión de assets/imágenes.\n'
            '- `@vendure/email-plugin` — emails transaccionales (Handlebars).\n'
            '- `@vendure/admin-ui-plugin` — Admin UI.\n'
            '- `@vendure/dashboard-plugin` — analytics.\n'
            '- `@vendure/payments-plugin` — Stripe/Mollie/Braintree.\n'
            '\n'
            '## Channels + Regions\n'
            '\n'
            'Vendure soporta multi-channel nativo (multi-currency, multi-tax,\n'
            'multi-language). Configura desde Admin UI o `vendure-config.ts`.\n'
            '\n'
            '## Cuando Vendure vs Saleor vs Medusa\n'
            '\n'
            '- **Vendure**: más estructurado, plugin API más limpio, Admin UI\n'
            '  nativa Angular. Ideal para devs TypeScript.\n'
            '- **Saleor**: Python backend, GraphQL desde día 1, multi-region\n'
            '  más maduro para enterprise.\n'
            '- **Medusa**: más MVP-friendly, growing fast, plugins más nuevos.\n'
            'PCREATIVE STUDIO_EOF',
        ],
        "min_version": "Vendure 3.x / Node 22+ / Postgres 14+",
        "skills": [],
        "ux_pack": "vendure",
        "notes": "Vendure — backend headless commerce con NestJS + GraphQL + TypeORM (Postgres). Plugin-first architecture, admin UI Angular incluido, storefront opcional (Next/Remix/Angular). Licencia MIT. Self-hosted total. Para devs TypeScript que prefieren arquitectura más estructurada que Medusa.",
    },
    "bigcommerce-stencil": {
        "name": "BigCommerce Stencil + Cornerstone (MIT)",
        "category": "E-commerce",
        "language": "Handlebars + SCSS",
        "scaffold": [
            "echo '→ Clonando Cornerstone (theme oficial BigCommerce, MIT)…'",
            "git clone --depth 1 https://github.com/bigcommerce/cornerstone.git _cs_tmp 2>&1 | head",
            "cp -a _cs_tmp/. . && rm -rf _cs_tmp/.git _cs_tmp",
            "if [ -f package.json ] && command -v jq >/dev/null 2>&1; then "
            "jq '.name = \"__SLUG__\" | .version = \"0.1.0\"' package.json > _pkg.tmp && mv _pkg.tmp package.json; fi",
            # Stencil CLI debe estar instalado global; check + instrucción
            "command -v stencil >/dev/null 2>&1 || echo '⚠️  Stencil CLI no instalado. Instálalo: npm install -g @bigcommerce/stencil-cli'",
            'cat > README-BIGCOMMERCE.md <<\'PCREATIVE STUDIO_EOF\'\n'
            '# __PROJECT__ — BigCommerce Stencil Theme\n'
            '\n'
            'Cornerstone (theme oficial BigCommerce, MIT) como base. Handlebars +\n'
            'SCSS Citadel (Foundation 5.5) + Stencil CLI.\n'
            '\n'
            '## Setup\n'
            '\n'
            '```bash\n'
            'npm install -g @bigcommerce/stencil-cli   # primera vez\n'
            'npm install                               # deps del theme\n'
            'stencil init                              # config interactiva → .stencil\n'
            '#   - Pide la URL de tu store (https://store-xxxx.mybigcommerce.com)\n'
            '#   - Pide tu API token (BigCommerce Admin → Settings → API → New token)\n'
            'stencil start                             # local dev en https://localhost:3000\n'
            '```\n'
            '\n'
            '## Comandos Stencil\n'
            '\n'
            '| Comando | Para qué |\n'
            '|---|---|\n'
            '| `stencil init` | crea `.stencil` con tu store + token |\n'
            '| `stencil start` | dev server local con HMR (https) |\n'
            '| `stencil bundle` | empaqueta el theme a `.zip` |\n'
            '| `stencil push` | sube el bundle a tu store |\n'
            '| `stencil release` | combina bundle + push + bump version |\n'
            '\n'
            '## Estructura\n'
            '\n'
            '```\n'
            'templates/        — Handlebars pages (home, product, category, cart, …)\n'
            'assets/           — CSS source (SCSS Citadel) + JS (ES modules) + img\n'
            'lang/              — locales (en, es, fr, …)\n'
            'schema.json        — settings que el merchant ve en el Page Builder\n'
            'config.json        — theme metadata + variations + variation styles\n'
            '.stencil           — credentials del store (gitignored)\n'
            '```\n'
            '\n'
            '## BigCommerce Theme Store\n'
            '\n'
            '- Themes paid se distribuyen a través del Theme Store de BigCommerce\n'
            '  (~$150-300 por theme, ticket más alto que Shopify).\n'
            '- Cornerstone es la base oficial pero **NO se permite revender\n'
            '  Cornerstone tal cual** — hay que diferenciar (igual que Shopify Dawn\n'
            '  en Theme Store).\n'
            '- ThemeForest también vende BigCommerce themes (~900 themes).\n'
            'PCREATIVE STUDIO_EOF',
        ],
        "min_version": "Cornerstone 6.x / Stencil CLI 7.x / Node 22+",
        "skills": [],
        "ux_pack": "bigcommerce-stencil",
        "notes": "BigCommerce theme stack — Cornerstone (theme oficial MIT) + Stencil CLI. Handlebars + SCSS Citadel (Foundation 5.5). 2º theme store después de Shopify por volumen. Ticket más alto: themes $150-300. Para Theme Store oficial: NO puede ser derivado de Cornerstone (mismo gating que Dawn en Shopify Theme Store).",
    },
    "prestashop-theme": {
        "name": "PrestaShop 9 — tienda completa (Docker) + child theme",
        "category": "E-commerce",
        "language": "PHP + Smarty",
        "scaffold": [
            "echo '→ Provisionando PrestaShop 9 con Docker (MariaDB + PrestaShop, locale ES)…'",
            "TF_PORT=$(python3 -c \"import json,os;d=json.load(open(os.path.expanduser('~/.config/themeforge/ports.json')));print((d.get('__SLUG__') or {}).get('port') or 8080)\" 2>/dev/null || echo 8080)",
            "echo \"→ Puerto asignado: $TF_PORT\"",
            "mkdir -p themes/__SLUG__/config themes/__SLUG__/assets/css themes/__SLUG__/assets/js themes/__SLUG__/assets/img themes/__SLUG__/templates themes/__SLUG__/modules themes/__SLUG__/_dev",
            'cat > themes/__SLUG__/config/theme.yml <<\'PCREATIVE STUDIO_EOF\'\n'
            'name: __SLUG__\n'
            'display_name: "__PROJECT__"\n'
            'parent: classic\n'
            'version: 0.1.0\n'
            'author:\n'
            '  name: "you"\n'
            '  email: "support@example.com"\n'
            'meta:\n'
            '  compatibility: { from: 9.0.0, to: ~ }\n'
            '  available_layouts:\n'
            '    layout-full-width:   { name: "Full width", description: "Full width layout" }\n'
            '    layout-left-column:  { name: "Left column", description: "3 columns, sidebar left" }\n'
            '    layout-right-column: { name: "Right column", description: "3 columns, sidebar right" }\n'
            '    layout-both-columns: { name: "Both columns", description: "3 cols, sidebars both" }\n'
            'assets:\n'
            '  use_parent_assets: true\n'
            'global_settings:\n'
            '  configuration:\n'
            '    PS_QUICK_VIEW: true\n'
            '    PS_CATALOG_MODE: false\n'
            '  modules:\n'
            '    to_enable: []\n'
            '    to_disable: []\n'
            '    to_install: []\n'
            'theme_settings:\n'
            '  default_layout: layout-full-width\n'
            '  layouts:\n'
            '    category:     layout-left-column\n'
            '    best-sales:   layout-left-column\n'
            '    new-products: layout-left-column\n'
            '    prices-drop:  layout-left-column\n'
            '    sitemap:      layout-left-column\n'
            'PCREATIVE STUDIO_EOF',
            "touch themes/__SLUG__/preview.png",
            'cat > docker-compose.yml <<PCREATIVE STUDIO_EOF\n'
            'services:\n'
            '  db:\n'
            '    image: mariadb:11\n'
            '    environment:\n'
            '      MARIADB_ROOT_PASSWORD: prestashop\n'
            '      MARIADB_DATABASE: prestashop\n'
            '    volumes:\n'
            '      - ps-db:/var/lib/mysql\n'
            '    restart: unless-stopped\n'
            '  prestashop:\n'
            '    image: prestashop/prestashop:9\n'
            '    depends_on:\n'
            '      - db\n'
            '    ports:\n'
            '      - "${TF_PORT}:80"\n'
            '    environment:\n'
            '      DB_SERVER: db\n'
            '      DB_NAME: prestashop\n'
            '      DB_USER: root\n'
            '      DB_PASSWD: prestashop\n'
            '      PS_INSTALL_AUTO: 1\n'
            '      PS_ERASE_DB: 1\n'
            '      PS_DEV_MODE: 1\n'
            '      PS_DOMAIN: localhost:${TF_PORT}\n'
            '      PS_FOLDER_ADMIN: admin-dev\n'
            '      PS_LANGUAGE: es\n'
            '      PS_COUNTRY: es\n'
            '      ADMIN_MAIL: admin@__SLUG__.local\n'
            '      ADMIN_PASSWD: prestashop123\n'
            '    volumes:\n'
            '      - ps-app:/var/www/html\n'
            '      - ./themes/__SLUG__:/var/www/html/themes/__SLUG__\n'
            '    restart: unless-stopped\n'
            'volumes:\n'
            '  ps-db:\n'
            '  ps-app:\n'
            'PCREATIVE STUDIO_EOF',
            "echo '→ Levantando PrestaShop (docker compose up -d — la 1ª vez descarga ~1 GB)…'",
            'if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then '
            'docker compose up -d || echo "  ⚠️ docker compose up falló (revisa puertos/imágenes)"; '
            'echo "  ⏳ Esperando a que PrestaShop TERMINE de instalarse antes de seguir (hasta ~5 min la 1ª vez)…"; '
            'for i in $(seq 1 100); do '
            'if curl -fs -o /dev/null "http://localhost:$TF_PORT/"; then echo "  ✅ PrestaShop LISTO y respondiendo en http://localhost:$TF_PORT/"; break; fi; '
            'if [ $((i % 10)) -eq 0 ]; then echo "  …sigue instalando ($((i * 3))s transcurridos)"; fi; '
            'sleep 3; '
            'done; '
            'elif command -v docker >/dev/null 2>&1; then echo "  ⚠️ El daemon de Docker NO responde (parado, sin permisos, o kernel actualizado sin reiniciar). Arranca docker (sudo systemctl start docker; o reinicia si actualizaste el kernel) y luego: docker compose up -d"; '
            'else echo "  ⚠️ Docker no está instalado. Instálalo y luego: docker compose up -d"; fi',
            'echo ""',
            'echo "✅ Tienda PrestaShop provisionada — el setup continúa (autoskills, etc.)."',
            'echo "   🛒 Tienda: http://localhost:$TF_PORT/"',
            'echo "   🔑 Admin:  http://localhost:$TF_PORT/admin-dev/   (admin@__SLUG__.local / prestashop123)"',
            'echo "   📋 Logs:   docker compose logs -f prestashop"',
            'echo "   🤖 Gestión IA (opcional): instala el módulo PrestaShop MCP en el back-office (Módulos) → expone un MCP remoto HTTP+OAuth para el agente. Guía: docs.mcp.prestashop.com"',
            'cat > themes/__SLUG__/README-PRESTASHOP.md <<\'PCREATIVE STUDIO_EOF\'\n'
            '# __PROJECT__ — PrestaShop child theme\n'
            '\n'
            'Stack: **PrestaShop 9.x** + child theme heredando del **classic**.\n'
            'Licencia **OSL 3.0** (misma que PrestaShop core).\n'
            '\n'
            '## Tienda ya provisionada (Docker)\n'
            '\n'
            'Pcreative Studio ha levantado PrestaShop 9 + MariaDB con `docker-compose.yml`:\n'
            '\n'
            '- 🛒 Tienda:  `http://localhost:<puerto>/`\n'
            '- 🔑 Admin:   `http://localhost:<puerto>/admin-dev/`  (admin@__SLUG__.local / prestashop123)\n'
            '- Parar / arrancar:  `docker compose stop` · `docker compose up -d`\n'
            '- Logs:  `docker compose logs -f prestashop`\n'
            '- Consola PS:  `docker compose exec prestashop php bin/console …`\n'
            '- El child theme `themes/__SLUG__/` está montado como volumen: lo editas en local y se ve en la tienda.\n'
            '\n'
            '## Estructura generada\n'
            '\n'
            '```\n'
            'themes/__SLUG__/\n'
            '├── config/theme.yml    # parent: classic + layouts + settings\n'
            '├── preview.png         # 1080×640px recomendado\n'
            '├── assets/             # CSS/JS/img propios (si use_parent_assets:false)\n'
            '├── templates/          # .tpl Smarty overrides\n'
            '├── modules/            # overrides de templates de módulos\n'
            '└── _dev/               # source Sass/JS antes de compilar\n'
            '```\n'
            '\n'
            '## Activación\n'
            '\n'
            '```bash\n'
            'docker compose exec prestashop php bin/console prestashop:themes:enable __SLUG__\n'
            '# o desde Back Office: Design > Theme & Logo > Use this theme\n'
            '```\n'
            '\n'
            '## Override templates\n'
            '\n'
            '```bash\n'
            'cp themes/classic/templates/catalog/product.tpl themes/__SLUG__/templates/catalog/\n'
            '```\n'
            '\n'
            'Smarty busca primero en el child, luego en el parent.\n'
            '\n'
            '## Marketplaces\n'
            '\n'
            '- **PrestaShop Addons** — 2.000+ templates, €40-150.\n'
            '- **ThemeForest** — 900+ PrestaShop themes, $39-89.\n'
            'PCREATIVE STUDIO_EOF',
        ],
        "min_version": "PrestaShop 9.0+ / PHP 8.1+ / Smarty 4",
        "skills": ["anthropics/skills/frontend-design"],
        "ux_pack": "prestashop-theme",
        "notes": "Tienda PrestaShop 9 COMPLETA provisionada con Docker (docker-compose.yml: MariaDB + prestashop/prestashop:9, auto-install, locale ES, admin en /admin-dev/, admin@<slug>.local / prestashop123). El child theme `themes/<slug>/` (hereda de `classic`) va montado como volumen para editar en local. NO requiere PrestaShop preinstalado — el scaffold lo levanta. Para pagos (transferencia/contrarreembolso/Bizum) usa los módulos nativos de PrestaShop; para tarjeta de growshop NO uses Stripe (alto riesgo). Smarty para overrides de plantillas. Licencia OSL 3.0. 🤖 GESTIÓN POR IA — MCP oficial de PrestaShop (docs.mcp.prestashop.com): NO es un `npx`, es un MÓDULO que se instala en el back-office (Módulos → instalar 'PrestaShop MCP'; deps PrestaShop Account + EventBus + MCP Tools, vía MBO). Una vez instalado y con la cuenta PrestaShop conectada, da una URL de MCP REMOTO (transport Streamable HTTP + OAuth, scopes mcp.discover/mcp.read/mcp.write/email) que permite crear/editar productos, categorías, pedidos y configuración por API. Para usarlo: el usuario instala el módulo, copia la URL del MCP desde la config del módulo y la añade al cliente IA como servidor MCP remoto (type http). MIENTRAS NO esté disponible, gestiona la tienda con la consola: `docker compose exec prestashop php bin/console …` (p.ej. listar comandos, crear admin, limpiar caché) y/o el back-office.",
    },
    "opencart-theme": {
        "name": "OpenCart 4 theme extension (GPL)",
        "category": "E-commerce",
        "language": "PHP + Twig",
        "scaffold": [
            "echo '→ OpenCart 4 theme extension scaffold…'",
            "[ -d extension ] || echo '⚠️  /extension no existe. Asegúrate de tener OpenCart 4.x instalado.'",
            "mkdir -p extension/__SLUG__/admin/controller/startup extension/__SLUG__/admin/language/en-gb",
            "mkdir -p extension/__SLUG__/catalog/controller/startup extension/__SLUG__/catalog/language/en-gb",
            "mkdir -p extension/__SLUG__/catalog/view/template/common extension/__SLUG__/catalog/view/template/product extension/__SLUG__/catalog/view/template/checkout",
            "mkdir -p extension/__SLUG__/catalog/view/stylesheet extension/__SLUG__/catalog/view/javascript extension/__SLUG__/catalog/view/image",
            'cat > extension/__SLUG__/install.json <<\'PCREATIVE STUDIO_EOF\'\n'
            '{\n'
            '  "name": "__PROJECT__",\n'
            '  "version": "0.1.0",\n'
            '  "author": "you",\n'
            '  "link": "https://example.com",\n'
            '  "description": "Custom OpenCart 4 theme",\n'
            '  "code": "__SLUG__",\n'
            '  "compatibility": ">=4.0"\n'
            '}\n'
            'PCREATIVE STUDIO_EOF',
            'cat > extension/__SLUG__/catalog/controller/startup/theme.php <<\'PCREATIVE STUDIO_EOF\'\n'
            '<?php\n'
            'namespace Opencart\\Catalog\\Controller\\Extension\\__SLUG__\\Startup;\n'
            '\n'
            'class Theme extends \\Opencart\\System\\Engine\\Controller {\n'
            '    public function index(): void {\n'
            "        if (\\$this->config->get('config_theme') === '__SLUG__') {\n"
            "            \\$this->document->addStyle('extension/__SLUG__/catalog/view/stylesheet/__SLUG__.css');\n"
            '        }\n'
            '    }\n'
            '}\n'
            'PCREATIVE STUDIO_EOF',
            'cat > extension/__SLUG__/catalog/view/stylesheet/__SLUG__.css <<\'PCREATIVE STUDIO_EOF\'\n'
            ':root { --brand: #C56A4D; --brand-accent: #8FA68E; }\n'
            'body { font-family: system-ui, sans-serif; }\n'
            '.btn-primary, .btn-success { background: var(--brand); border-color: var(--brand); }\n'
            'PCREATIVE STUDIO_EOF',
            'cat > extension/__SLUG__/catalog/view/template/common/header.twig <<\'PCREATIVE STUDIO_EOF\'\n'
            '{# Custom header override #}\n'
            '<!DOCTYPE html>\n'
            '<html dir="{{ direction }}" lang="{{ lang }}">\n'
            '<head>\n'
            '  <meta charset="UTF-8">\n'
            '  <title>{{ title }}</title>\n'
            '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '  {% for style in styles %}<link rel="stylesheet" href="{{ style.href }}" media="{{ style.media }}">{% endfor %}\n'
            '  {% for script in scripts %}<script src="{{ script }}"></script>{% endfor %}\n'
            '</head>\n'
            '<body>\n'
            '  <header class="site-header">\n'
            '    <a href="{{ home }}" class="logo"><img src="{{ logo }}" alt="{{ name }}"></a>\n'
            '    {{ navigation }}\n'
            '  </header>\n'
            '  <main class="container">\n'
            'PCREATIVE STUDIO_EOF',
            'cat > extension/__SLUG__/README-OPENCART.md <<\'PCREATIVE STUDIO_EOF\'\n'
            '# __PROJECT__ — OpenCart 4 theme extension\n'
            '\n'
            'OpenCart 4 trata los themes como **extensions**. OCMod está obsoleto\n'
            '— solo events. Licencia **GPL**.\n'
            '\n'
            '## Prerequisites\n'
            '\n'
            '- OpenCart 4.0+ instalado.\n'
            '- PHP 8.0+ y MySQL 8 / MariaDB 10.5+.\n'
            '\n'
            '## Estructura\n'
            '\n'
            '```\n'
            'extension/__SLUG__/\n'
            '├── install.json\n'
            '├── admin/                                  # archivos del backoffice\n'
            '└── catalog/                                # archivos del storefront\n'
            '    ├── controller/startup/theme.php       # carga CSS del theme\n'
            '    └── view/\n'
            '        ├── template/                       # .twig overrides\n'
            '        ├── stylesheet/__SLUG__.css\n'
            '        ├── javascript/\n'
            '        └── image/\n'
            '```\n'
            '\n'
            '## Activación\n'
            '\n'
            '```bash\n'
            '# 1) Empaquetar\n'
            'cd extension && zip -r __SLUG__.ocmod.zip __SLUG__/\n'
            '\n'
            '# 2) Admin → Extensions > Installer → upload el .ocmod.zip\n'
            '# 3) Admin → Extensions > Extensions → Themes → install + activate\n'
            '# 4) Admin → Design > Theme → seleccionar el theme\n'
            '```\n'
            '\n'
            '## Twig overrides\n'
            '\n'
            'Copia el template original del core manteniendo la ruta:\n'
            '\n'
            '```bash\n'
            'cp catalog/view/template/common/header.twig \\\n'
            '   extension/__SLUG__/catalog/view/template/common/header.twig\n'
            '```\n'
            '\n'
            '## Distribución\n'
            '\n'
            '- **OpenCart Marketplace** — $30-150 por theme.\n'
            '- **ThemeForest** — 1.500+ OpenCart themes.\n'
            'PCREATIVE STUDIO_EOF',
        ],
        "min_version": "OpenCart 4.0+ / PHP 8.0+ / Twig 3",
        "skills": [],
        "ux_pack": "opencart-theme",
        "notes": "OpenCart 4 theme como extension (OC4 movió themes a extension/<vendor>/). Twig templates, OCMod obsoleto (solo events). Licencia GPL. Distribución: OpenCart Marketplace + ThemeForest (1.5k+ themes). Stack scaffoldea SOLO la extension — OpenCart 4.x ya debe estar instalado.",
    },
    "sylius": {
        "name": "Sylius 2.x + Symfony 7 (MIT)",
        "category": "E-commerce",
        "language": "PHP + Symfony + Twig",
        "scaffold": [
            "echo '→ Scaffolding Sylius 2.x (Symfony 7 + MIT)…'",
            "command -v composer >/dev/null || { echo '❌ composer no instalado'; exit 1; }",
            "composer create-project --no-interaction sylius/sylius-standard . || "
            "echo '⚠️ scaffold fallido — ejecuta a mano `composer create-project sylius/sylius-standard .`'",
            'cat > README-SYLIUS.md <<\'PCREATIVE STUDIO_EOF\'\n'
            '# __PROJECT__ — Sylius 2.x storefront\n'
            '\n'
            'Stack: **Sylius 2.x** (full e-commerce framework basado en\n'
            '**Symfony 7.4+** + **Doctrine ORM 3** + **Twig 3** + **Webpack\n'
            'Encore**). Licencia **MIT**.\n'
            '\n'
            '## Prerequisites\n'
            '\n'
            '- PHP 8.2+, ext-intl, ext-gd, ext-curl, ext-mbstring.\n'
            '- Composer 2.\n'
            '- PostgreSQL 14+ / MySQL 8.\n'
            '- Node 22 + Yarn (Webpack Encore).\n'
            '- Symfony CLI recomendado.\n'
            '\n'
            '## Setup\n'
            '\n'
            '```bash\n'
            'cp .env .env.local\n'
            '# edita .env.local con DATABASE_URL y MAILER_DSN\n'
            '\n'
            'php bin/console sylius:install   # crea BD + admin user + sample data\n'
            '\n'
            'yarn install\n'
            'yarn build\n'
            '\n'
            'symfony server:start\n'
            '# → http://127.0.0.1:8000/      (storefront)\n'
            '# → http://127.0.0.1:8000/admin (back office)\n'
            '```\n'
            '\n'
            '## Custom themes (SyliusThemeBundle ya preinstalado)\n'
            '\n'
            '```bash\n'
            'mkdir -p themes/__SLUG__/templates/SyliusShopBundle\n'
            'mkdir -p themes/__SLUG__/templates/SyliusAdminBundle\n'
            '```\n'
            '\n'
            'composer.json del theme:\n'
            '\n'
            '```json\n'
            '{\n'
            '  "name": "pcreative/sylius-__SLUG__",\n'
            '  "extra": {\n'
            '    "sylius-theme": {\n'
            '      "title": "__PROJECT__",\n'
            '      "authors": [{ "name": "you", "email": "support@example.com" }]\n'
            '    }\n'
            '  }\n'
            '}\n'
            '```\n'
            '\n'
            'Override Twig:\n'
            '\n'
            '```bash\n'
            'cp vendor/sylius/shop-bundle/templates/Product/show.html.twig \\\n'
            '   themes/__SLUG__/templates/SyliusShopBundle/Product/show.html.twig\n'
            '```\n'
            '\n'
            'Asignar el theme a un canal: Admin → Configuration > Channels →\n'
            'edit channel → Theme dropdown → selecciona `__PROJECT__`.\n'
            '\n'
            '## Stack profundo\n'
            '\n'
            '- **Sylius Core**: catálogo, channels, orders, customers, shipping,\n'
            '  payments, promotions, taxes.\n'
            '- **Symfony 7.4**: kernel, DI, EventDispatcher, Messenger.\n'
            '- **API Platform 3**: REST + GraphQL automáticos.\n'
            '- **Doctrine ORM 3**: entities + repositories.\n'
            '\n'
            '## Channels multi-store\n'
            '\n'
            'Multi-channel nativo (multi-currency, multi-locale, multi-theme,\n'
            'multi-tax). Cada channel: dominio + theme + idiomas + monedas.\n'
            '\n'
            '## Distribución\n'
            '\n'
            '- **Sylius Marketplace** (sylius.com/store).\n'
            '- **Packagist** — composer package.\n'
            'PCREATIVE STUDIO_EOF',
        ],
        "min_version": "Sylius 2.x / Symfony 7.4+ / PHP 8.2+",
        "skills": [],
        "ux_pack": "sylius",
        "notes": "Sylius 2.x — framework PHP full e-commerce sobre Symfony 7.4 + Doctrine ORM + Twig + API Platform 3. Multi-channel/multi-currency/multi-locale nativo. SyliusThemeBundle para themes custom. Licencia MIT. Scaffold con composer create-project sylius/sylius-standard.",
    },
    "html-tailwind": {
        "name": "HTML + Tailwind + Vite",
        "category": "Web · Static",
        "language": "HTML / JS",
        "scaffold": [
            "npm create vite@latest . -- --template vanilla-ts </dev/null",
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
            "npm create vite@latest . -- --template vanilla </dev/null",
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
            "npm create vite@latest . -- --template react-ts </dev/null",
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
            "npm create vite@latest . -- --template vue-ts </dev/null",
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
        "notes": "Android nativo: Kotlin + Jetpack Compose + Material 3. Pcreative Studio crea solo la carpeta — el scaffold real necesita Android Studio. Ideal para apps con UX 100% Material y mejor rendimiento que cross-platform.",
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
    "pcreative-commerce": {
        "name": "pcreative Commerce — Medusa 2 + Next.js (headless, multi-pasarela, IA, self-hosted)",
        "category": "E-commerce",
        "language": "TypeScript + Medusa + Next.js",
        "scaffold": [
            "echo '-> pcreative Commerce: backend Medusa + admin Aurora + storefront (animaciones)...'",
            # Logica en la plantilla privada templates/pcreative-commerce/scaffold.sh
            # (clona backend Medusa, copia admin Aurora + storefront Dulce Obrador,
            #  genera .env, docker pg+redis, migra, crea admin, instala deps). NO-fatal.
            'bash "__TFDIR__/templates/pcreative-commerce/scaffold.sh" || echo "  scaffold pcreative Commerce incompleto (revisa Node 20+/Docker/red)"',
            'python3 -c "import sys; sys.path.insert(0, \'__TFDIR__\'); import web_enhancements as we; we.ensure_mcps(\'./storefront\')" 2>/dev/null && echo "  MCPs cableados en storefront/.mcp.json" || true',
        ],
        "min_version": "Medusa 2 / Node 20+ / Next.js 15 / Postgres 16 (pgvector) / Redis 7",
        "skills": ["anthropics/skills/frontend-design", "vercel/skills/nextjs-best-practices"],
        "ux_pack": "pcreative-commerce",
        "notes": (
            "🏗️ pcreative Commerce = e-commerce PROPIO super-avanzado y super-seguro, productizado para la agencia: "
            "el CLIENTE LO POSEE, 0% comisión, self-hosted, headless (sirve web Y app móvil), con LIBERTAD TOTAL de "
            "pasarela (incluida alto riesgo cannabis/CBD que Stripe/Shopify rechazan) e IA nativa. Base: Medusa 2 "
            "(Node/TS, MIT) en `backend/` (dashboard de Medusa OFF) + **admin Aurora branded** en `admin/` (panel servido en /admin) + **storefront Vite/React con animaciones** (framer-motion, efectos, Quick View) en `storefront/`, Postgres(pgvector)+Redis por Docker. Arranca TODO con `bash start.sh` (unifica / + /admin + /medusa bajo un puerto, sin CORS).\n\n"
            "## 🔒 SEGURIDAD — OBLIGATORIO (es 'super seguro' o no es)\n"
            "- **PCI = SAQ-A:** la captura de tarjeta SIEMPRE en página alojada del proveedor por REDIRECT (no iframe, no server-to-server). NUNCA toques ni almacenes datos de tarjeta. El redirect además esquiva bugs del ciclo de pago server-to-server de Medusa.\n"
            "- **OWASP API #1 = BOLA:** autoriza POR OBJETO en cada endpoint (carrito/pedido/cliente) — comprueba propiedad, no basta con estar logueado.\n"
            "- **Recalcula SIEMPRE los totales en el servidor** (jamás confíes en precios/cantidades del cliente).\n"
            "- **Verifica la firma de TODOS los webhooks** de pasarela antes de marcar un pedido pagado.\n"
            "- Cabeceras **CSP + HSTS**, rate-limiting, secretos solo en `.env` (NUNCA al repo), validación de input (Zod), 2FA admin + RBAC, RGPD (consentimiento + derecho al olvido), audit log.\n\n"
            "## 💳 MULTI-PASARELA — cada método un payment provider de Medusa\n"
            "Implementa cada pasarela como un módulo que EXTIENDE `AbstractPaymentProvider` (`@medusajs/framework/utils`), registrado en `medusa-config.ts` bajo el módulo `@medusajs/payment`; cada método su propio provider id (initiatePayment/authorizePayment/capturePayment/refundPayment + identifier). Patrón probado (plugin Mollie de la comunidad).\n"
            "- **Tarjeta (REDIRECT alojado):** MONEI (acepta CBD/alto riesgo en ES; agrega tarjeta + Bizum + SEPA; condicional THC<0,2%, UE) y/o GreenexPay (cannabis/growshops/seedbanks; capa sobre Redsys/Stripe/Monei).\n"
            "- **Cripto:** BTCPay Server self-hosted (Greenfield REST API, no-custodial).\n"
            "- **Transferencia y Contrarreembolso:** providers 'offline' (autoriza en checkout, captura/liquida en entrega) + Bizum.\n"
            "- ⚠️ Para catálogos de ALTO RIESGO (growshop/CBD): NUNCA Stripe/Shopify Payments/Adyen (rechazan). MONEI/GreenexPay/cripto/transferencia/COD. Valida con alta real + transacción de prueba antes de lanzar (las páginas de MONEI/GreenexPay son marketing).\n\n"
            "## 🤖 IA NATIVA (el diferencial)\n"
            "- **Búsqueda semántica/vectorial + recomendaciones** con `pgvector` en el MISMO Postgres (texto→embedding→similitud coseno). Reusa backups/seguridad del Postgres. (pgvector escala bien ~1-10M vectores.)\n"
            "- **Generación de descripciones** de producto (LLM) e **imágenes** de producto (Runware, ya integrado en Pcreative Studio).\n"
            "- Opcional: asistente de compra / soporte con RAG agéntico.\n\n"
            "## 🌍 COMERCIO\n"
            "Multi-idioma + multi-moneda + IVA vía Regions de Medusa; promociones/cupones, inventario, envíos por zonas, carrito abandonado, reseñas. Admin de Medusa (+ widgets custom). API headless para web + la app móvil de Pcreative Studio.\n\n"
            "## 📦 LICENCIAS\n"
            "Integra el sistema de licencias pcreative (el cliente lo posee pero el producto va protegido/licenciado) siguiendo el patrón anti-nulled de la agencia (JWT RS256 + verify offline).\n\n"
            "Estructura: `backend/` (Medusa, dashboard OFF) + `admin/` (panel Aurora branded por env `NEXT_PUBLIC_STORE_*`) + `storefront/` (Vite/React con framer-motion + efectos) + `docker-compose.yml` + `start.sh`. El panel es **/admin** (admin@forge.local / forgecommerce123), NUNCA el dashboard de Medusa (/app está desactivado). El scaffold deja el sistema ENTERO corriendo y migrado. Tu trabajo: re-tematizar el storefront por nicho (theme.config.ts + demo data) + TODO lo de arriba (seguridad, multi-pasarela, IA, licencias).\n\n"
            "## 🎨 UI / DISEÑO (monorepo)\n"
            "El storefront `storefront/` es Vite/React y YA trae **framer-motion + efectos** (Quick View, transiciones de página, banner animado, catálogo) — aplica AHÍ todo lo de UI y **re-tematiza por nicho** (`storefront/client/src/lib/theme.config.ts` + demo data en `storefront/client/src/data/`). Los MCP **21st.dev (`magic`, `magicui`, `shadcn`)** están cableados en `storefront/.mcp.json`. El panel `admin/` (Aurora) ya es pro; su marca se cambia por env (`NEXT_PUBLIC_STORE_NAME`/`_TAGLINE`/`_ACCENT`, **hex ENTRECOMILLADO** o dotenv lo lee como comentario). El backend (`backend/`) no lleva UI propia (su dashboard está OFF)."
        ),
    },
    "pcreative-commerce-growshop": {
        "name": "pcreative Commerce Growshop — tienda cannabis (Medusa 2 + Next.js · alto riesgo · age-gate)",
        "category": "E-commerce",
        "language": "TypeScript + Medusa + Next.js",
        "scaffold": [
            "echo '→ pcreative Commerce Growshop: Medusa 2 + Next.js + Postgres(pgvector) + Redis…'",
            "echo '→ create-medusa-app (backend + storefront Next.js — descarga grande, varios min)…'",
            'npx --yes create-medusa-app@latest backend --db-url "postgres://medusa:medusa@localhost:5433/medusa" --with-nextjs-starter --no-migrations --no-browser --use-npm </dev/null || echo "  ⚠️ create-medusa-app falló (necesita Node 20+ y red)"',
            "echo '→ docker-compose: Postgres(pgvector) + Redis…'",
            'cat > docker-compose.yml <<PCREATIVE STUDIO_EOF\n'
            'services:\n'
            '  db:\n'
            '    image: pgvector/pgvector:pg16\n'
            '    environment:\n'
            '      POSTGRES_USER: medusa\n'
            '      POSTGRES_PASSWORD: medusa\n'
            '      POSTGRES_DB: medusa\n'
            '    ports:\n'
            '      - "5433:5432"\n'
            '    volumes:\n'
            '      - fc-db:/var/lib/postgresql/data\n'
            '    restart: unless-stopped\n'
            '  redis:\n'
            '    image: redis:7-alpine\n'
            '    ports:\n'
            '      - "6380:6379"\n'
            '    restart: unless-stopped\n'
            'volumes:\n'
            '  fc-db:\n'
            'PCREATIVE STUDIO_EOF',
            'if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then '
            'docker compose up -d || echo "  ⚠️ docker compose up falló"; '
            'echo "  ⏳ Esperando a Postgres…"; '
            'for i in $(seq 1 40); do if docker compose exec -T db pg_isready -U medusa >/dev/null 2>&1; then echo "  ✅ Postgres listo"; break; fi; sleep 2; done; '
            'docker compose exec -T db psql -U medusa -d medusa -c "CREATE EXTENSION IF NOT EXISTS vector;" >/dev/null 2>&1 && echo "  ✅ pgvector habilitado (búsqueda semántica IA)"; '
            'if [ -d backend ]; then echo "  → migraciones + admin…"; (cd backend && (npx medusa db:migrate || true) && (npx medusa user -e admin@forge.local -p forgecommerce123 || true)); fi; '
            'else echo "  ⚠️ Docker no disponible: arranca db/redis con docker compose up -d y luego (cd backend && npx medusa db:migrate && npx medusa user -e admin@forge.local -p forgecommerce123)"; fi',
            'python3 -c "import sys; sys.path.insert(0, \'__TFDIR__\'); import web_enhancements as we; we.ensure_mcps(\'.\')" 2>/dev/null && echo "  ✅ MCPs cableados en .mcp.json (magic, magicui, shadcn, fetch, playwright)" || echo "  ⚠️ no se pudo cablear .mcp.json"',
            'echo ""',
            'echo "✅ Base pcreative Commerce lista — el agente construye el GROWSHOP completo según CLAUDE.md."',
            'echo "   🧩 Backend Medusa:  cd backend && npm run dev  → admin http://localhost:9000/app  (admin@forge.local / forgecommerce123)"',
            'echo "   🛍  Storefront:      cd backend-storefront && npm run dev  → http://localhost:8000"',
            'echo "   🗄  Postgres+pgvector :5433 · Redis :6380 (Docker)"',
        ],
        "min_version": "Medusa 2 / Node 20+ / Next.js 15 / Postgres 16 (pgvector) / Redis 7",
        "skills": ["anthropics/skills/frontend-design", "vercel/skills/nextjs-best-practices"],
        "ux_pack": "pcreative-commerce",
        "notes": (
            "🌱 GROWSHOP COMPLETO sobre pcreative Commerce (Medusa 2 + Next.js, self-hosted, el cliente lo posee, 0% comisión). "
            "Construye la tienda ENTERA de una sentada, multipágina, con datos demo realistas, sin pedir confirmación. "
            "Base en `backend/` (Medusa) + `backend-storefront/` (Next.js).\n\n"
            "## 🛒 EL NEGOCIO (growshop en España — cultivo de cannabis)\n"
            "Vende a cultivadores (novatos y expertos) y adultos. **Categorías** (deja estructura + atributos lista; productos reales se cargan luego): "
            "(1) Cultivo — iluminación LED/HPS, armarios/tents, ventilación/extracción, control de clima, sustratos/macetas, riego; "
            "(2) Fertilizantes y aditivos; (3) **Semillas de cannabis** (artículo de COLECCIÓN / preservación genética); "
            "(4) **CBD y derivados** (flores, aceites, cosmética); (5) Vaporizadores, grinders, papeles y parafernalia; (6) Accesorios y control de plagas.\n\n"
            "## 🎨 TONO Y ESTÉTICA\n"
            "Profesional, moderno y de CONFIANZA: verde natural + oscuro elegante, NADA de estética 'stoner' cutre. Mobile-first, carga rápida, fotos grandes, transmite seriedad + envío DISCRETO + atención experta.\n\n"
            "## 📄 PÁGINAS\n"
            "Home (hero + categorías destacadas + novedades + más vendidos + sello envío discreto + reseñas), catálogo por categoría con FILTROS avanzados "
            "(semillas: banco/marca, indica/sativa/híbrida, feminizada/autofloreciente, %THC, %CBD, tiempo de floración, interior/exterior, dificultad; cultivo: marca, potencia, tamaño), "
            "ficha de producto (galería, genética/efectos/sabor/dificultad o specs técnicas, stock, relacionados, reseñas), carrito, checkout, cuenta cliente (pedidos/direcciones/wishlist), "
            "Blog/Guías de cultivo (SEO long-tail), Sobre nosotros, Contacto, FAQ, páginas legales.\n\n"
            "## ⚖️ CUMPLIMIENTO LEGAL (OBLIGATORIO)\n"
            "- **Age-gate 18+** al entrar (modal que bloquea hasta confirmar mayoría de edad, recordado por sesión).\n"
            "- **Disclaimers:** las SEMILLAS se venden como objeto coleccionable / preservación genética, NO para germinar/cultivar. El CBD es <0,2% THC.\n"
            "- Avisos legales, privacidad/RGPD (consentimiento + derecho al olvido), cookies, términos, política de envíos/devoluciones, y casilla 'soy mayor de edad y acepto los términos' en el checkout.\n\n"
            "## 💳 PAGOS — NO Stripe/Shopify (rechazan cannabis/CBD)\n"
            "Por defecto: **Transferencia bancaria + Contrarreembolso (recargo configurable + pedido mínimo) + Bizum**. Deja PREPARADOS pero desactivados (hasta alta del cliente) los providers de tarjeta de alto riesgo **MONEI / GreenexPay** (flujo REDIRECT alojado) y cripto **BTCPay**. Cada método = payment provider de Medusa (extiende `AbstractPaymentProvider`, registrado en medusa-config.ts). Muestra los métodos disponibles claros en el checkout.\n\n"
            "## 🤖 IA NATIVA\n"
            "**Búsqueda semántica con pgvector** que entienda lenguaje natural ('variedad fácil de cultivar en interior, efecto relajante, floración corta') → texto→embedding→similitud; recomendaciones; asistente/guía de cultivo básico (RAG). Descripciones por LLM e imágenes de producto con Runware.\n\n"
            "## 🔒 SEGURIDAD — OBLIGATORIO\n"
            "PCI **SAQ-A vía REDIRECT** (nunca toques datos de tarjeta; además esquiva bugs server-to-server de Medusa) · OWASP API #1 **BOLA** (autorización por objeto en carrito/pedido/cliente) · **recalcula totales en servidor** · **verifica firma de todos los webhooks** · CSP/HSTS · secretos solo en .env · rate-limiting · RBAC/2FA admin · RGPD · audit log.\n\n"
            "## 🌍 COMERCIO + LICENCIAS\n"
            "Multi-idioma (ES base) + multi-moneda + IVA vía Regions de Medusa; promos/cupones, inventario, envíos por zonas (transportistas con contrarreembolso), wishlist, newsletter, puntos/fidelización opcional. Admin de Medusa para que el cliente gestione productos/stock/pedidos. Integra el sistema de licencias pcreative (JWT RS256 + verify offline).\n\n"
            "El scaffold deja Medusa+Next.js+Postgres(pgvector)+Redis corriendo. Tu trabajo: construir TODO el growshop de arriba. Cuando el usuario te dé el NOMBRE del growshop, personaliza marca/eslogan/ciudad; mientras, usa un placeholder coherente.\n\n"
            "## 🎨 UI / DISEÑO (monorepo)\n"
            "Todo el diseño va en el storefront `backend-storefront/` (Next.js/React). Los MCP de diseño **21st.dev (`magic`, `magicui`, `shadcn`)** están cableados — úsalos para los componentes. **framer-motion** para animaciones: instálalo en el storefront (`cd backend-storefront && npm install framer-motion`); Pcreative Studio no lo auto-instala por estar en subcarpeta. Estética growshop: verde natural + oscuro elegante, mobile-first, micro-interacciones suaves (respeta `prefers-reduced-motion`)."
        ),
    },

    # ════════════════════════════════════════════════════════════════
    #  COMPONENT LIBRARIES
    # ════════════════════════════════════════════════════════════════
    "storybook-react": {
        "name": "Storybook + React + Vite",
        "category": "Component Lib",
        "language": "TypeScript",
        "scaffold": [
            "npm create vite@latest . -- --template react-ts </dev/null",
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
            "npm create vite@latest . -- --template react-ts </dev/null",
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
            "npm create vite@latest . -- --template vue-ts </dev/null",
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
            "npm create vite@latest . -- --template vanilla-ts </dev/null",
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
            "npm create vite@latest . -- --template react-ts </dev/null",
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
