"""runware_images.py — generación de imágenes vía Runware (https://runware.ai).

Sistema de imágenes de ThemeForge para los templates: **API key, pay-as-you-go**
(NO suscripción) → encaja con el modelo de compliance. La key se guarda en el
mismo almacén que el resto (`~/.config/themeforge/keys.json`, chmod 0600) bajo el
id `runware`, o por env `RUNWARE_API_KEY`.

API: POST https://api.runware.ai/v1 con un array JSON de tareas; auth como primer
elemento `{taskType:"authentication", apiKey}`. Tarea `imageInference` con prompt,
modelo (AIR id), tamaño, etc. Devolvemos URL (y opcionalmente descargamos el PNG).

Solo stdlib (urllib) → reutilizable desde el MCP server y la GUI.
"""
from __future__ import annotations

import json
import os
import urllib.request
import uuid
from pathlib import Path

API_URL = "https://api.runware.ai/v1"
CONFIG_PATH = Path.home() / ".config" / "themeforge" / "runware.json"

# Modelos base conocidos (AIR ids de Runware). El resto (cientos) salen por
# búsqueda en vivo (search_models). Configurables por llamada.
MODELS = {
    "flux-dev": "runware:101@1",      # FLUX.1 [dev] — calidad, fotorrealista
    "flux-schnell": "runware:100@1",  # FLUX.1 [schnell] — rápido / drafts
}
DEFAULT_MODEL = MODELS["flux-dev"]

# Arquitecturas reales de Runware (verificadas vía modelSearch 2026-05-30).
ARCHITECTURES = ["flux1d", "flux1s", "sdxl", "sd1x", "sd3", "pony"]

# Categorías curadas por CASO DE USO para templates web: cada una define un
# término de búsqueda + arquitectura sugerida que alimenta el selector en vivo
# (search_models). Así el usuario elige por "para qué" y luego afina el modelo.
CATEGORIES = [
    {"key": "photoreal", "label": "📷 Fotorrealista (hero, secciones)",
     "search": "realistic photo", "architecture": "flux1d"},
    {"key": "illustration", "label": "🎨 Ilustración / arte",
     "search": "illustration art", "architecture": "sdxl"},
    {"key": "logo", "label": "🏷️ Logo / vector / flat",
     "search": "logo vector flat design", "architecture": "sdxl"},
    {"key": "anime", "label": "🌸 Anime / cartoon",
     "search": "anime", "architecture": "pony"},
    {"key": "3d", "label": "🧊 3D / render",
     "search": "3d render", "architecture": "sdxl"},
    {"key": "fast", "label": "⚡ Rápido (drafts)",
     "search": "schnell", "architecture": "flux1s"},
]


def load_config() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def get_default_model() -> str:
    return (load_config().get("default_model") or DEFAULT_MODEL)


def set_default_model(air: str) -> None:
    cfg = load_config()
    cfg["default_model"] = air
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    try:
        import platform_compat as pc
        pc.secure_file_chmod(CONFIG_PATH)
    except Exception:
        pass


def search_models(
    query: str = "",
    *,
    architecture: str = "",
    category: str = "checkpoint",
    limit: int = 30,
    api_key: str | None = None,
    timeout: int = 30,
) -> dict:
    """Busca en el catálogo de Runware (taskType modelSearch). Devuelve
    {ok, models:[{air,name,architecture,category,...}]}."""
    key = api_key or get_api_key()
    if not key:
        return {"ok": False, "error": "No hay API key de Runware."}
    task = {
        "taskType": "modelSearch",
        "taskUUID": str(uuid.uuid4()),
        "limit": max(1, min(100, limit)),
    }
    if query.strip():
        task["search"] = query.strip()
    if architecture:
        task["architecture"] = architecture
    if category:
        task["category"] = category
    body = json.dumps([{"taskType": "authentication", "apiKey": key}, task]).encode()
    req = urllib.request.Request(
        API_URL, data=body, method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}
    if isinstance(data, dict) and data.get("errors"):
        first = data["errors"][0]
        return {"ok": False, "error": first.get("message", str(first))}
    rows = (data.get("data") if isinstance(data, dict) else data) or []
    models = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        results = r.get("results") if isinstance(r.get("results"), list) else [r]
        for m in results:
            if isinstance(m, dict) and m.get("air"):
                models.append({
                    "air": m.get("air"), "name": m.get("name", m.get("air")),
                    "architecture": m.get("architecture", ""),
                    "category": m.get("category", ""),
                    "tags": m.get("tags", []),
                })
    return {"ok": True, "models": models}


def get_api_key() -> str | None:
    """Lee la key de Runware: env RUNWARE_API_KEY → keys.json (id 'runware')."""
    env = os.environ.get("RUNWARE_API_KEY")
    if env:
        return env.strip()
    try:
        import ai_providers as aip
        return (aip.load_keys().get("runware") or "").strip() or None
    except Exception:
        try:
            kp = Path.home() / ".config" / "themeforge" / "keys.json"
            return (json.loads(kp.read_text(encoding="utf-8")).get("runware")
                    or "").strip() or None
        except Exception:
            return None


def _round64(n: int) -> int:
    """Runware exige múltiplos de 64 (típico 128..2048)."""
    n = max(128, min(2048, int(n)))
    return (n // 64) * 64


def generate(
    prompt: str,
    *,
    width: int = 1024,
    height: int = 1024,
    model: str | None = None,
    number_results: int = 1,
    output_format: str = "WEBP",
    api_key: str | None = None,
    timeout: int = 120,
) -> dict:
    """Genera imagen(es) en Runware. Devuelve {ok, urls:[...]} o {ok:False,error}."""
    key = api_key or get_api_key()
    if not key:
        return {"ok": False, "error": "No hay API key de Runware. Añádela en "
                "Settings → 🔑 AI credentials (o env RUNWARE_API_KEY)."}
    if not (prompt or "").strip():
        return {"ok": False, "error": "prompt vacío."}

    tasks = [
        {"taskType": "authentication", "apiKey": key},
        {
            "taskType": "imageInference",
            "taskUUID": str(uuid.uuid4()),
            "positivePrompt": prompt.strip()[:1500],
            "model": model or get_default_model(),
            "width": _round64(width),
            "height": _round64(height),
            "numberResults": max(1, min(4, number_results)),
            "outputType": "URL",
            "outputFormat": (output_format or "WEBP").upper(),
        },
    ]
    body = json.dumps(tasks).encode("utf-8")
    req = urllib.request.Request(
        API_URL, data=body, method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:  # noqa: PERF203
        detail = ""
        try:
            detail = e.read().decode("utf-8")[:300]
        except Exception:
            pass
        return {"ok": False, "error": f"HTTP {e.code}: {detail or e.reason}"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}

    # Respuesta: {"data":[{"imageURL": "..."}], "errors":[...]}
    if isinstance(data, dict) and data.get("errors"):
        first = data["errors"][0]
        return {"ok": False, "error": first.get("message", str(first))}
    rows = (data.get("data") if isinstance(data, dict) else data) or []
    urls = [r.get("imageURL") for r in rows
            if isinstance(r, dict) and r.get("imageURL")]
    if not urls:
        return {"ok": False, "error": f"sin imágenes en la respuesta: {str(data)[:200]}"}
    return {"ok": True, "urls": urls}


def generate_to_file(
    prompt: str,
    dest: str | Path,
    *,
    width: int = 1024,
    height: int = 1024,
    model: str | None = None,
    output_format: str = "WEBP",
    timeout: int = 120,
) -> dict:
    """Genera UNA imagen y la descarga a `dest`. Devuelve {ok, path, url}."""
    res = generate(prompt, width=width, height=height, model=model,
                   number_results=1, output_format=output_format, timeout=timeout)
    if not res.get("ok"):
        return res
    url = res["urls"][0]
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            dest.write_bytes(r.read())
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"descarga falló: {e}", "url": url}
    return {"ok": True, "path": str(dest), "url": url}


if __name__ == "__main__":
    import sys
    p = sys.argv[1] if len(sys.argv) > 1 else "a modern dental clinic hero photo"
    print(generate(p))
