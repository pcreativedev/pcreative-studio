"""
ThemeForge plugin loader.

User-defined plugins live at `~/.config/themeforge/plugins/*.py`. Each
plugin imports the registration helpers from this module and calls
them at import time to add custom stacks / template types / agents
without touching the ThemeForge repo.

Plugins load once at startup, BEFORE the form is built. Errors are
caught individually — a broken plugin logs a warning and the rest
keep loading.

Plugin files starting with `_` are ignored (convention for disabled).

Example: `~/.config/themeforge/plugins/my_custom_stacks.py`

    from themeforge_plugins import register_stack

    register_stack(
        key="vite-react-myorg",
        name="Vite React (my org preset)",
        category="Web · Frontend",
        language="TypeScript",
        min_version="latest",
        scaffold=[
            "npm create vite@latest . -- --template react-ts --yes",
            "npm install -D tailwindcss @my-org/preset",
        ],
        skills=[],
        notes="Vite + React + Tailwind + internal preset.",
    )
"""
from __future__ import annotations

import importlib.util
import sys
import traceback
from pathlib import Path

from platform_compat import app_config_dir

PLUGINS_DIR = app_config_dir() / "plugins"

_REQUIRED_STACK_FIELDS = {
    "name", "category", "language", "min_version", "scaffold",
}


def register_stack(key: str, **stack) -> None:
    """Registra un stack custom en el dict global STACKS.

    Args:
        key: identificador único (kebab-case, no espacios).
        name: nombre legible para la UI.
        category: categoría que agrupa stacks en el picker.
        language: lenguaje principal.
        min_version: versión mínima recomendada del runtime.
        scaffold: lista de comandos bash que se ejecutan al crear el
                  proyecto. Soporta placeholders `__SLUG__`,
                  `__PROJECT__`, `__PASCAL__`, `__ORG_ID__`.
        skills: lista opcional de skills (paquetes para `npx autoskills`).
        notes: nota corta mostrada en el picker.
    """
    import stacks as _s

    missing = _REQUIRED_STACK_FIELDS - set(stack.keys())
    if missing:
        raise ValueError(
            f"register_stack({key!r}): faltan campos requeridos {missing}"
        )
    if key in _s.STACKS:
        # Permitido (override del repo): es responsabilidad del plugin
        # autor saber lo que hace. Log a stderr para visibilidad.
        print(f"[plugins] override del stack '{key}' (estaba en STACKS)", file=sys.stderr)
    stack.setdefault("skills", [])
    stack.setdefault("notes", "")
    _s.STACKS[key] = stack


def register_template_type(name: str) -> None:
    """Añade un tipo de template al combobox (si no estaba ya)."""
    import stacks as _s
    if name not in _s.TEMPLATE_TYPES:
        _s.TEMPLATE_TYPES.append(name)


def register_agent(key: str, **agent) -> None:
    """Registra un agente AI alternativo. Útil para añadir variantes
    del propio CLI con flags distintos, o nuevos providers."""
    import stacks as _s

    required = {"name", "command", "context_file"}
    missing = required - set(agent.keys())
    if missing:
        raise ValueError(
            f"register_agent({key!r}): faltan campos requeridos {missing}"
        )
    agent.setdefault("autoskills_flag", None)
    _s.AGENTS[key] = agent


def load_user_plugins() -> tuple[int, list[str]]:
    """Carga todos los `*.py` de PLUGINS_DIR. Devuelve (loaded, errors)."""
    if not PLUGINS_DIR.is_dir():
        return 0, []
    errors: list[str] = []
    loaded = 0
    for plugin_path in sorted(PLUGINS_DIR.glob("*.py")):
        if plugin_path.name.startswith("_"):
            continue
        try:
            mod_name = f"themeforge_plugin_{plugin_path.stem}"
            spec = importlib.util.spec_from_file_location(mod_name, plugin_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                # Registrar en sys.modules para que el plugin pueda
                # importarse a sí mismo si lo necesita.
                sys.modules[mod_name] = module
                spec.loader.exec_module(module)
                loaded += 1
        except Exception as e:
            tb = traceback.format_exc(limit=3)
            errors.append(f"{plugin_path.name}: {e}\n{tb}")
    return loaded, errors


def list_loaded_plugins() -> list[str]:
    """Devuelve los plugins que están actualmente cargados (sus
    nombres de módulo)."""
    return [
        name.removeprefix("themeforge_plugin_")
        for name in sys.modules
        if name.startswith("themeforge_plugin_")
    ]
