"""
Example plugin: register a custom Vite + React stack with your
organisation's preset.

Copy to `~/.config/themeforge/plugins/my-custom-vite.py` and edit
`@my-org/preset` to your real package. Restart Pcreative Studio to load.
"""
from themeforge_plugins import register_stack, register_template_type


register_stack(
    key="vite-react-myorg",
    name="Vite React + my-org preset",
    category="Web · Frontend",
    language="TypeScript",
    min_version="latest",
    scaffold=[
        "npm create vite@latest . -- --template react-ts --yes",
        "npm install",
        # Your org's design system / utilities
        "npm install -D tailwindcss postcss autoprefixer",
        "npx tailwindcss init -p",
        # Replace with your real package:
        # "npm install @my-org/design-tokens @my-org/components",
        'echo "/** @type {import(\\"tailwindcss\\").Config} */ '
        'module.exports = { content: [\\"./src/**/*.{ts,tsx,html}\\"], theme: {}, plugins: [] };" > tailwind.config.js',
    ],
    skills=["anthropics/skills/frontend-design"],
    notes="Vite + React + Tailwind, ready for your org's preset.",
)

# Optionally add new categories to the Tipo dropdown
register_template_type("Internal · Admin")
register_template_type("Internal · Marketing landing")
