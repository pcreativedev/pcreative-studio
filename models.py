"""
models.py — el catálogo de modelos de IA. Uno solo, para todo el programa.

── POR QUÉ EXISTE ────────────────────────────────────────────────────────

Los modelos estaban escritos a mano en cuatro sitios (`ai_providers.py`,
`cost_tracker.py`, `market_analyzer.py`, `hermes_panel.py`), en tres
convenciones distintas y sin ponerse de acuerdo. El resultado, medido sobre
las sesiones reales del usuario:

  · `claude-opus-5` era el segundo modelo más usado (13.424 eventos) y NO
    estaba en ninguna lista ni tenía precio.
  · `claude-haiku-4-5-20251001` no casaba con `claude-haiku-4-5` por el
    sufijo de fecha, así que se le aplicaba la tarifa de reserva: 15/75 en
    vez de 1/5. Quince veces de más.
  · Opus 4.6 y 4.7 estaban a 15/75 cuando cuestan 5/25. El triple.

En total, **8.835 $ de los ~16.000 $ que reportaba el panel de costes salían
de una tarifa inventada**. Más de la mitad.

── LAS DOS REGLAS ────────────────────────────────────────────────────────

1. **Nada de coincidencia exacta.** Los CLIs devuelven el identificador con
   sufijo de fecha, con marcas de ventana larga o con prefijo de proveedor.
   Todo eso entra por `normalizar()` antes de buscar nada.

2. **Los precios se copian de la documentación oficial, nunca se estiman.**
   Los de Anthropic están verificados contra platform.claude.com el
   2026-08-08. Los de OpenAI y Google vienen de la tabla anterior y NO se han
   podido verificar: van marcados como tales para que se note.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
import re


@dataclass(frozen=True)
class Modelo:
    """Un modelo. `id` es la forma canónica; todo lo demás resuelve a ella."""
    id: str
    etiqueta: str
    familia: str                      # "claude" | "openai" | "google"
    entrada: float                    # USD por millón de tokens
    salida: float
    cache_escritura: float = 0.0      # caché de 5 minutos
    cache_lectura: float = 0.0
    #: Lo ofrecemos en los desplegables. Los retirados siguen aquí para poder
    #: calcular el coste de sesiones viejas, pero no se eligen.
    elegible: bool = True
    #: Precio confirmado en la documentación oficial del proveedor.
    verificado: bool = True
    #: Otras formas en que este modelo aparece por ahí.
    alias: tuple[str, ...] = field(default_factory=tuple)


# ── Anthropic ────────────────────────────────────────────────────────────
# Verificado en platform.claude.com/docs/en/about-claude/pricing (2026-08-08).

_SONNET5_FIN_INTRO = date(2026, 8, 31)


def _sonnet5_precios() -> tuple[float, float, float, float]:
    """Sonnet 5 tiene precio de lanzamiento hasta el 31 de agosto de 2026.

    Se calcula al vuelo en vez de fijarlo: si esto se dejase clavado, el 1 de
    septiembre el panel empezaría a mentir por un tercio sin que nadie toque
    nada ni se entere.
    """
    if date.today() <= _SONNET5_FIN_INTRO:
        return (2.00, 10.00, 2.50, 0.20)
    return (3.00, 15.00, 3.75, 0.30)


CATALOGO: list[Modelo] = [
    # ── Claude 5 ──
    Modelo("claude-opus-5", "Opus 5 — el más capaz para código ($5/$25)",
           "claude", 5.00, 25.00, 6.25, 0.50),
    Modelo("claude-sonnet-5", "Sonnet 5 — equilibrado ($2/$10 hasta el 31-ago)",
           "claude", *_sonnet5_precios()),
    Modelo("claude-fable-5", "Fable 5 — escritura ($10/$50)",
           "claude", 10.00, 50.00, 12.50, 1.00),
    Modelo("claude-mythos-5", "Mythos 5 — disponibilidad limitada ($10/$50)",
           "claude", 10.00, 50.00, 12.50, 1.00, elegible=False),

    # ── Claude 4.x ──
    Modelo("claude-opus-4-8", "Opus 4.8 ($5/$25)", "claude", 5.00, 25.00, 6.25, 0.50),
    # Estos dos estaban a 15/75 en la tabla vieja. Son 5/25.
    Modelo("claude-opus-4-7", "Opus 4.7 ($5/$25)", "claude", 5.00, 25.00, 6.25, 0.50),
    Modelo("claude-opus-4-6", "Opus 4.6 ($5/$25)", "claude", 5.00, 25.00, 6.25, 0.50),
    Modelo("claude-opus-4-5", "Opus 4.5 ($5/$25)", "claude", 5.00, 25.00, 6.25, 0.50,
           elegible=False),
    Modelo("claude-sonnet-4-6", "Sonnet 4.6 ($3/$15)", "claude", 3.00, 15.00, 3.75, 0.30),
    Modelo("claude-sonnet-4-5", "Sonnet 4.5 ($3/$15)", "claude", 3.00, 15.00, 3.75, 0.30,
           elegible=False),
    Modelo("claude-haiku-4-5", "Haiku 4.5 — barato y rápido ($1/$5)",
           "claude", 1.00, 5.00, 1.25, 0.10),

    # ── Retirados: no se ofrecen, pero hay sesiones antiguas que valorar ──
    Modelo("claude-opus-4-1", "Opus 4.1 (retirado)", "claude", 15.00, 75.00, 18.75, 1.50,
           elegible=False),
    Modelo("claude-opus-4", "Opus 4 (retirado)", "claude", 15.00, 75.00, 18.75, 1.50,
           elegible=False),
    Modelo("claude-sonnet-4", "Sonnet 4 (retirado)", "claude", 3.00, 15.00, 3.75, 0.30,
           elegible=False),
    Modelo("claude-haiku-3-5", "Haiku 3.5 (retirado)", "claude", 0.80, 4.00, 1.00, 0.08,
           elegible=False, alias=("claude-3-5-haiku",)),
    Modelo("claude-3-5-sonnet", "Sonnet 3.5 (retirado)", "claude", 3.00, 15.00, 3.75, 0.30,
           elegible=False),
    Modelo("claude-3-opus", "Opus 3 (retirado)", "claude", 15.00, 75.00, 18.75, 1.50,
           elegible=False),
    Modelo("claude-3-haiku", "Haiku 3 (retirado)", "claude", 0.25, 1.25, 0.30, 0.03,
           elegible=False),

    # ── OpenAI ── precios HEREDADOS de la tabla anterior, sin verificar.
    Modelo("gpt-5.5", "GPT-5.5", "openai", 15.00, 60.00, 0.00, 1.50, verificado=False),
    Modelo("gpt-5.1", "GPT-5.1", "openai", 15.00, 60.00, 0.00, 1.50, verificado=False),
    Modelo("gpt-5", "GPT-5", "openai", 15.00, 60.00, 0.00, 1.50, verificado=False),
    Modelo("gpt-5-mini", "GPT-5 mini", "openai", 0.25, 2.00, 0.00, 0.05, verificado=False),
    Modelo("gpt-4o", "GPT-4o", "openai", 2.50, 10.00, 0.00, 1.25,
           elegible=False, verificado=False),
    Modelo("gpt-4o-mini", "GPT-4o mini", "openai", 0.15, 0.60, 0.00, 0.075,
           elegible=False, verificado=False),
    Modelo("o3", "o3", "openai", 15.00, 60.00, 0.00, 0.00,
           elegible=False, verificado=False),
    Modelo("o3-mini", "o3-mini", "openai", 1.10, 4.40, 0.00, 0.55,
           elegible=False, verificado=False),

    # ── Google ── ídem.
    Modelo("gemini-2.5-pro", "Gemini 2.5 Pro", "google", 1.25, 10.00, 0.00, 0.31,
           verificado=False),
    Modelo("gemini-2.5-flash", "Gemini 2.5 Flash", "google", 0.30, 2.50, 0.00, 0.075,
           verificado=False),
    Modelo("gemini-2.0-flash", "Gemini 2.0 Flash", "google", 0.10, 0.40, 0.00, 0.025,
           elegible=False, verificado=False),
]

_POR_ID: dict[str, Modelo] = {}


def _reindexar() -> None:
    _POR_ID.clear()
    for m in CATALOGO:
        _POR_ID[m.id] = m
        for a in m.alias:
            _POR_ID[a] = m


_reindexar()


# ── Fuente viva: models.dev ──────────────────────────────────────────────
#
# Un catálogo escrito a mano se queda atrás — es exactamente lo que pasó y por
# lo que existe este fichero. models.dev publica precios y modelos de 181
# proveedores en un solo JSON, y Hermes ya lo cachea en `~/.hermes`.
#
# Se usa así: la lista de arriba manda en el ORDEN, las ETIQUETAS y en qué se
# ofrece; models.dev manda en los PRECIOS y aporta los modelos que aún no
# están listados. Si no hay red ni caché, todo sigue funcionando con lo curado.

import json
import os
from pathlib import Path

_CACHE_PROPIA = Path(
    os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))
) / "pcreative-studio" / "models-dev.json"
_CACHE_HERMES = Path.home() / ".hermes" / "models_dev_cache.json"
_MAX_EDAD_S = 60 * 60 * 24 * 7  # una semana

_VENDEDOR_A_FAMILIA = {"anthropic": "claude", "openai": "openai", "google": "google"}


def _leer_cache() -> dict | None:
    """El JSON de models.dev más reciente que tengamos a mano."""
    candidatos = [p for p in (_CACHE_PROPIA, _CACHE_HERMES) if p.is_file()]
    if not candidatos:
        return None
    mejor = max(candidatos, key=lambda p: p.stat().st_mtime)
    try:
        return json.loads(mejor.read_text(encoding="utf-8"))
    except Exception:
        return None


def refrescar(timeout: float = 20.0) -> bool:
    """Baja models.dev y lo guarda. Devuelve si lo consiguió.

    Nunca lanza: quedarse sin actualizar es aceptable, tumbar el arranque del
    programa por un fallo de red no lo es.
    """
    import urllib.request
    try:
        req = urllib.request.Request(
            "https://models.dev/api.json", headers={"User-Agent": "pcreative-studio"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            datos = json.load(r)
        if not isinstance(datos, dict) or not datos:
            return False
        _CACHE_PROPIA.parent.mkdir(parents=True, exist_ok=True)
        _CACHE_PROPIA.write_text(json.dumps(datos), encoding="utf-8")
        aplicar_fuente_viva(datos)
        return True
    except Exception:
        return False


def cache_caducado() -> bool:
    """¿Toca refrescar? (No hay caché, o tiene más de una semana.)"""
    candidatos = [p for p in (_CACHE_PROPIA, _CACHE_HERMES) if p.is_file()]
    if not candidatos:
        return True
    import time
    return (time.time() - max(p.stat().st_mtime for p in candidatos)) > _MAX_EDAD_S


def aplicar_fuente_viva(datos: dict | None = None) -> int:
    """Corrige precios y añade modelos nuevos desde models.dev.

    Devuelve cuántas entradas ha tocado. Los modelos que llegan de aquí y no
    estaban se marcan `elegible=False`: aparecen para poder calcular su coste,
    pero no se cuelan solos en los desplegables sin que nadie los haya mirado.
    """
    datos = datos if datos is not None else _leer_cache()
    if not isinstance(datos, dict):
        return 0

    cambios = 0
    for vendedor, info in datos.items():
        familia = _VENDEDOR_A_FAMILIA.get(vendedor)
        if not familia or not isinstance(info, dict):
            continue
        for mid, m in (info.get("models") or {}).items():
            coste_ = (m or {}).get("cost") or {}
            if not coste_.get("input") and not coste_.get("output"):
                continue
            tarifas = (
                float(coste_.get("input") or 0),
                float(coste_.get("output") or 0),
                float(coste_.get("cache_write") or 0),
                float(coste_.get("cache_read") or 0),
            )
            canon = normalizar(mid)
            actual = _POR_ID.get(canon)
            if actual is None:
                CATALOGO.append(Modelo(
                    canon, m.get("name") or canon, familia, *tarifas,
                    elegible=False, verificado=True,
                ))
                cambios += 1
            elif (actual.entrada, actual.salida,
                  actual.cache_escritura, actual.cache_lectura) != tarifas:
                CATALOGO[CATALOGO.index(actual)] = Modelo(
                    actual.id, actual.etiqueta, actual.familia, *tarifas,
                    elegible=actual.elegible, verificado=True, alias=actual.alias,
                )
                cambios += 1
    if cambios:
        _reindexar()
    return cambios


# ── Normalización ────────────────────────────────────────────────────────

_FECHA = re.compile(r"-20\d{6}$")          # claude-haiku-4-5-20251001
_VENTANA = re.compile(r"\[[^\]]*\]$")      # claude-opus-4-7[1m]
_PREFIJO = re.compile(r"^(anthropic|openai|google|x-ai|meta-llama)/")


def normalizar(modelo: str) -> str:
    """Lleva cualquier forma del identificador a la canónica.

    Es la pieza que faltaba. Los CLIs no devuelven identificadores limpios:
      · Claude Code añade la fecha de publicación (`-20251001`).
      · La ventana de 1M viaja como sufijo entre corchetes (`[1m]`).
      · OpenRouter antepone el proveedor y usa puntos (`anthropic/claude-opus-4.8`).

    Sin esto, cada variante es un modelo desconocido con tarifa de reserva.
    """
    if not modelo:
        return ""
    m = modelo.strip().lower()
    m = _PREFIJO.sub("", m)
    m = _VENTANA.sub("", m)
    m = _FECHA.sub("", m)
    # Los puntos de las versiones se escriben con guion en la forma canónica,
    # pero NO los de Gemini (`gemini-2.5-pro`), donde el punto es parte del
    # nombre. Se decide probando: si la versión con guiones existe, esa gana.
    if m not in _POR_ID and "." in m:
        con_guiones = m.replace(".", "-")
        if con_guiones in _POR_ID:
            return con_guiones
    return m


def buscar(modelo: str) -> Modelo | None:
    """El modelo, o None si de verdad no lo conocemos."""
    return _POR_ID.get(normalizar(modelo))


# ── Precios ──────────────────────────────────────────────────────────────

#: Tarifa cuando el modelo no se reconoce. Deliberadamente cara: si aparece un
#: modelo nuevo, es mejor que el panel sobrestime y se note, a que abarate y
#: nadie se entere. Va siempre acompañada de `conocido=False`.
RESERVA = (15.00, 75.00, 18.75, 1.50)


def precios(modelo: str) -> tuple[tuple[float, float, float, float], bool]:
    """Devuelve ((entrada, salida, caché_escritura, caché_lectura), conocido)."""
    m = buscar(modelo)
    if m is None:
        return RESERVA, False
    return (m.entrada, m.salida, m.cache_escritura, m.cache_lectura), True


def coste(modelo: str, entrada: int = 0, salida: int = 0,
          cache_escritura: int = 0, cache_lectura: int = 0) -> tuple[float, bool]:
    """Coste en dólares de un uso concreto. Devuelve (coste, precio_conocido)."""
    (pe, ps, pcw, pcr), conocido = precios(modelo)
    total = (
        (entrada / 1_000_000) * pe
        + (salida / 1_000_000) * ps
        + (cache_escritura / 1_000_000) * pcw
        + (cache_lectura / 1_000_000) * pcr
    )
    return total, conocido


# ── Listas para los desplegables ─────────────────────────────────────────

#: Qué familia usa cada proveedor del programa. Los que van por OpenCode u
#: OpenRouter pueden con todas, así que se les ofrece el catálogo entero.
FAMILIA_POR_PROVEEDOR: dict[str, tuple[str, ...]] = {
    "claude": ("claude",),
    "claude-api": ("claude",),
    "codex": ("openai",),
    "codex-api": ("openai",),
    "gemini": ("google",),
    "opencode": ("claude", "openai", "google"),
    "openrouter": ("claude", "openai", "google"),
}

#: Texto de la opción "que decida el CLI". El valor vacío significa "no pasar
#: --model", que es lo único que funciona con cualquier plan o cuenta.
AUTO = ("", "Auto — el que traiga tu cuenta (recomendado)")


def para_proveedor(proveedor: str) -> list[tuple[str, str]]:
    """Opciones del desplegable de un proveedor: [(id, etiqueta), …]."""
    familias = FAMILIA_POR_PROVEEDOR.get(proveedor, ("claude",))
    return [AUTO] + [
        (m.id, m.etiqueta)
        for m in CATALOGO
        if m.elegible and m.familia in familias
    ]


def slug_openrouter(modelo: str) -> str:
    """La forma que espera OpenRouter: `anthropic/claude-opus-5`."""
    m = buscar(modelo)
    if m is None:
        return modelo
    vendedor = {"claude": "anthropic", "openai": "openai", "google": "google"}[m.familia]
    # OpenRouter escribe las versiones con punto, no con guion.
    ident = re.sub(r"-(\d)-(\d)$", r"-\1.\2", m.id)
    return f"{vendedor}/{ident}"


# Al importar se aplica lo que haya en caché — sin tocar la red, que aquí
# bloquearía el arranque del programa. La descarga se dispara aparte
# (`refrescar()`), y solo si `cache_caducado()`.
try:
    aplicar_fuente_viva()
except Exception:
    pass
