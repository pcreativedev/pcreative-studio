"""
licensing_config.py — config opcional para el sistema de licencias.

Lee URLs y endpoints sensibles de un archivo privado del usuario
(`~/.config/themeforge/licensing.json`) en vez de hardcodearlos en el
código público. Si el archivo no existe se devuelven placeholders
genéricos que el usuario debe sustituir al usar el sistema.

Formato esperado de licensing.json:

    {
      "license_api_url": "https://your-domain.com/api/license/verify",
      "panel_base":      "https://your-domain.com/admin",
      "panel_proxy_url": "https://your-domain.com/api/plesk/proxy.php",
      "panel_label":     "tu panel admin"
    }

Tu copia privada queda fuera del repo (bloqueada por .gitignore).
"""
from __future__ import annotations

import json
from pathlib import Path

from platform_compat import app_config_dir

CONFIG_PATH = app_config_dir() / "licensing.json"

# Placeholders públicos. Se inyectan a templates/tooltips si el archivo
# privado no existe. URLs públicas HTTPS por defecto — el usuario
# externo despliega como prefiera.
PLACEHOLDERS = {
    "license_api_url": "https://YOUR_DOMAIN/api/license/verify",
    "panel_base": "https://YOUR_DOMAIN/admin",
    "panel_proxy_url": "https://YOUR_DOMAIN/api/plesk/proxy.php",
    "panel_label": "tu panel admin",
    # Organización GitHub para los repos privados generados por el botón
    # "📦 GitHub" / Phase 3. Si vacío → se usa la cuenta personal del
    # usuario gh.
    "github_org": "",
    # Identifier para Java/Kotlin/Flutter/Tauri/Spring/Ktor (estilo
    # com.empresa.app). Se sustituye en stacks.py como __ORG_ID__.
    "org_id": "com.example",
}


def load() -> dict[str, str]:
    """Devuelve el dict de config (privada si existe, placeholders si no)."""
    if not CONFIG_PATH.is_file():
        return dict(PLACEHOLDERS)
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        merged = dict(PLACEHOLDERS)
        if isinstance(data, dict):
            merged.update({k: str(v) for k, v in data.items() if v})
        return merged
    except Exception:
        return dict(PLACEHOLDERS)


def is_configured() -> bool:
    """¿El usuario tiene config privada con valores reales? Útil para
    decidir si mostrar el panel admin o no en la UI."""
    return CONFIG_PATH.is_file()
