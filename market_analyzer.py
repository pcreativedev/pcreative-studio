"""
market_analyzer — análisis de mercado de productos digitales con IA.

Llama directamente al endpoint HTTPS de OpenRouter (sin CLI) usando la
``OPENROUTER_API_KEY`` que el usuario ya tiene configurada en credenciales
(ver ``ai_providers.get_env('openrouter')``).

Tipos de análisis:
  - general:     mercado completo 2026 (best-sellers, stacks, gaps, tendencias).
  - niche:       deep-dive en UN nicho concreto.
  - compare:     comparativa de DOS nichos.
  - marketplace: análisis de UN marketplace (ThemeForest, Gumroad, etc.).
  - prediction:  proyección 2026 → 2027.

El histórico vive en ``~/.config/pcreative-studio/market_analyses/`` (gitignored).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "pcreative-studio"
ANALYSES_DIR = CONFIG_DIR / "market_analyses"

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Años dinámicos: los prompts se escribieron con "2026"/"2027" fijos; en build_request
# se sustituyen por el año actual y el siguiente para que nunca se queden viejos.
YEAR = datetime.now().year
NEXT_YEAR = YEAR + 1

# Por defecto un modelo con BÚSQUEDA WEB integrada → análisis con datos reales.
DEFAULT_MODEL = "perplexity/sonar-reasoning-pro"

# Modelos preseleccionados en el picker (todos vía OpenRouter, IDs verificados 2026-07).
# Los `perplexity/sonar*` traen web integrada; a los demás se les añade `:online`
# cuando el toggle "datos reales" está activo (ver call_openrouter).
MODELS = [
    "perplexity/sonar-reasoning-pro",   # web + razonamiento — RECOMENDADO para mercado
    "perplexity/sonar-deep-research",    # investigación profunda multi-fuente (más lento)
    "perplexity/sonar-pro",              # web rápido
    "anthropic/claude-opus-4.8",         # mejor razonamiento (usa :online con el toggle)
    "anthropic/claude-sonnet-4.6",
    "openai/gpt-5.1",
    "openai/gpt-5",
    "google/gemini-2.5-pro",
    "deepseek/deepseek-v3.2",
]

# Etiquetas legibles para el picker (id → texto).
MODEL_LABELS = {
    "perplexity/sonar-reasoning-pro": "Perplexity Sonar Reasoning Pro · web + razonamiento ⭐",
    "perplexity/sonar-deep-research": "Perplexity Deep Research · multi-fuente (lento)",
    "perplexity/sonar-pro": "Perplexity Sonar Pro · web rápido",
    "anthropic/claude-opus-4.8": "Claude Opus 4.8 · máximo razonamiento",
    "anthropic/claude-sonnet-4.6": "Claude Sonnet 4.6 · equilibrado",
    "openai/gpt-5.1": "GPT-5.1",
    "openai/gpt-5": "GPT-5",
    "google/gemini-2.5-pro": "Gemini 2.5 Pro",
    "deepseek/deepseek-v3.2": "DeepSeek v3.2 · barato",
}

# Modelos que YA traen búsqueda web integrada (no necesitan `:online`).
_WEB_NATIVE_PREFIXES = ("perplexity/",)

# Marketplaces para el botón «Por marketplace».
MARKETPLACES = [
    "ThemeForest (Envato)",
    "CodeCanyon (Envato)",
    "Gumroad",
    "Lemon Squeezy",
    "Creative Market",
    "Itch.io (games + assets)",
    "ArtStation (3D + game assets)",
    "GitHub Sponsors / OSS",
    "Shopify Theme Store",
    "WordPress.org (themes/plugins)",
]


# ─── Prompts ────────────────────────────────────────────────────────────


_SYSTEM = (
    "Eres un analista senior del mercado de productos digitales para "
    "desarrolladores y creators. Conoces a fondo ThemeForest, CodeCanyon, "
    "Gumroad, Lemon Squeezy, Creative Market, Itch.io, ArtStation, GitHub "
    "Sponsors, Shopify Theme Store y wp.org. Das datos concretos (cifras "
    "estimadas, rangos de precio, % de cuota, tendencias). NO te quedas en "
    "generalidades. Output en MARKDOWN bien estructurado, con tablas donde "
    "tenga sentido. Idioma: español neutro."
)

# Se añade al system prompt cuando el grounding web está activo.
_WEB_SUFFIX = (
    "\n\nTIENES BÚSQUEDA WEB ACTIVA: basa el análisis en DATOS REALES y ACTUALES "
    "que encuentres ahora mismo (bestsellers reales, nº de ventas, precios, reseñas, "
    "posts recientes, releases). Prioriza cifras verificadas sobre estimaciones; cuando "
    "estimes, márcalo como «estimado». Añade al final una sección «## Fuentes» con los "
    "enlaces reales consultados. No inventes cifras ni URLs."
)


def prompt_general() -> str:
    return """# Análisis exhaustivo del mercado de productos digitales — 2026

Cubre con datos concretos TODOS los marketplaces principales: ThemeForest, CodeCanyon, Gumroad, Lemon Squeezy, Creative Market, Itch.io, ArtStation, GitHub Sponsors/OSS, Shopify Theme Store, WordPress.org, Unity Asset Store, Figma Community paid templates.

Quiero un análisis que me sirva para decidir QUÉ producto crear esta semana. Si no tienes datos exactos, da rangos razonables y márcalos como "estimado". NO te quedes en generalidades — cifras concretas.

## 1. Top 15 nichos más vendidos en 2026
Tabla: nicho · marketplace dominante · volumen mensual estimado (#ventas y $) · rango de precio · tendencia (📈/➡️/📉) · saturación (1-10) · ticket medio.

## 2. Sub-nichos emergentes (creciendo fuerte en 2026)
Mínimo 15 sub-nichos con tendencia 📈 y poca competencia. Cubre explícitamente:
- **Gaming**: indie game devs · mobile games · esports infra · streamers · asset shops · game studios · tournament platforms · browser games · game launchers/storefronts · Roblox/Fortnite creator tooling.
- **AI/LLM**: agentes, MCP servers, plugins de IA para WP/Shopify, AI image/video tooling, prompt marketplaces.
- **Web3/crypto** maduro (DeFi tooling, no NFT).
- **Health/wellness** (coaching, nutrición, mental health, fertility).
- **No-code/low-code** templates (Bubble, Webflow, Framer).
- **Creator economy** (cursos, membresías, newsletters, paid podcasts).
- **B2B vertical SaaS** (legaltech, agritech, proptech, foodtech).
- **Privacy/security** (E2EE messengers, password managers, VPN).

## 3. Stack tecnológico ganador POR nicho
Para cada nicho del top 15, lista los stacks que están vendiendo MÁS. **MÍNIMO 7-10 stacks distintos por nicho**. Incluye TODO el mapa:
- Frontend SSG/SSR: Next.js, Astro, Nuxt, SvelteKit, Remix, Vite+Vue, Vite+React, Qwik, SolidStart, Eleventy, Hugo.
- WordPress: FSE puro, Bricks, Elementor (free + Pro), Divi, Breakdance, classic+ACF, Hello+Pro, Spectra-driven.
- Shopify: Liquid + sections, Hydrogen (Remix), Online Store 2.0.
- Mobile: Expo/React Native, Flutter, Kotlin Compose, SwiftUI, Capacitor, Ionic.
- Backend/full-stack: Laravel+Inertia, Laravel+Livewire, NestJS+Prisma, FastAPI, Django+HTMX, t3-stack, RedwoodJS, Rails 8, Phoenix LiveView.
- Game engines / tooling: Godot, Unity asset bundles, GameMaker, Construct 3, RPG Maker, GDevelop, Cocos Creator, Phaser.
- 3D/AR: Three.js, R3F (React Three Fiber), Babylon.js, A-Frame, model-viewer.
- AI tooling: LangChain/LlamaIndex apps, Claude Skills, MCP servers, OpenAI Realtime API, Vercel AI SDK.

## 4. Stack adoption matrix 2026 (DEEP-DIVE)
Para CADA uno de los stacks anteriores, dame en tabla:
- Cuota estimada del mercado (de productos vendidos) en 2026.
- Crecimiento YoY (% vs 2025) — 📈/➡️/📉.
- Niches donde domina vs niches donde pierde.
- Coste/curva de aprendizaje (1-10).
- Tipo de product fit (landing / app / theme / mobile / game / SaaS).
- Buyer persona típico (no-dev / dev solo / equipo).
- Verdict comercial: ¿hay que apostar por él en 2026?

Sé exhaustivo: quiero saber el mapa COMPLETO, no solo los top 5.

## 5. Tendencias generales 2026 (con cifras)
- **Builders WP**: cuota Bricks vs Elementor vs FSE vs Divi vs Breakdance, con números — quién lidera, quién pierde, en qué países.
- **Mobile**: Expo vs Flutter vs Kotlin Compose vs SwiftUI por geografía y vertical.
- **Backend**: Laravel/Nest/FastAPI/Django/Rails/Phoenix — adopción real.
- **AI/LLM products**: el boom — qué tipo de producto vende más ($, no hype): plugins, agentes, MCPs, integraciones.
- **Performance**: Core Web Vitals como diferenciador comercial — qué % de buyers paga premium por velocidad.
- **Pricing power**: precios medios subiendo/bajando por categoría.

## 6. Top 10 productos más vendidos del año (ejemplos concretos)
Si recuerdas nombres/ítems específicos (Flatsome, Woodmart, Avada, etc.), nómbralos con: precio, ventas estimadas, qué hacen bien.

## 7. Top creators / brands a estudiar
10-15 nombres concretos de autores con cifras de revenue (ThemeForest authors, top Gumroad sellers, etc.) — el "who's who" del mercado de 2026.

## 8. Gap analysis — 15 huecos REALES en el mercado
Combinaciones (nicho × stack × marketplace) con ALTA demanda + BAJA competencia. Para cada uno: estimación de mercado, esfuerzo de creación (h), precio sugerido, USP propuesto.

## 9. Distribución / marketing channels que están funcionando
- SEO interno de marketplaces (qué premia ThemeForest/Gumroad en 2026).
- Comunidades (Reddit, Discord, Twitter/X, BlueSky, Threads, dev.to).
- Paid ads (Meta, Google, Reddit, X).
- Influencers / partnerships.

## 10. Recomendación final — qué crearía YO esta semana
Top 5 productos concretos que un solo creador podría lanzar **en 2-4 semanas** y vender bien. Para cada uno: nicho + stack + tipo + precio + esfuerzo (horas) + revenue mensual esperado primer trimestre.

Markdown rigurosamente estructurado, tablas donde aporten. Idioma español neutro. Sé exhaustivo — quiero el mapa COMPLETO del mercado, no un resumen."""


def prompt_stacks() -> str:
    return """# Análisis profundo del MERCADO DE STACKS — 2026

Solo stacks tecnológicos. Quiero el mapa exhaustivo de qué stacks se están usando para crear productos digitales que se venden HOY (themes, templates, apps, plugins, mobile, games), independientemente del nicho.

## 1. Adopción 2026 — tabla maestra de TODOS los stacks
Para cada stack, fila con:
- **Nombre del stack** (versión actual donde aplique).
- **Cuota** de productos vendidos 2026 (%).
- **Crecimiento YoY** vs 2025.
- **Donde domina** (tipos de productos / marketplaces).
- **Donde pierde** (qué lo está canibalizando).
- **Buyer fit** (no-dev / dev solo / equipo).
- **Aprendizaje** (1-10).
- **Salario medio dev** (proxy de coste).
- **Veredicto** (apostar / esperar / evitar).

Cubre TODO el mapa — mínimo 30-40 stacks:

### Frontend / static / SSR
Next.js (App Router), Astro, Nuxt, SvelteKit, Remix, Vite+React, Vite+Vue, Qwik, SolidStart, Eleventy, Hugo, Jekyll, Gatsby (¿muerto?), Angular, Vue puro CDN.

### WordPress
FSE puro, Bricks Builder, Elementor (free), Elementor Pro, Divi, Breakdance, Beaver Builder, Oxygen, classic theme+ACF, Hello Elementor child, Generate Press + GenerateBlocks, Astra, Kadence.

### Shopify
Liquid + sections + OS 2.0, Hydrogen (Remix).

### Mobile
Expo/React Native, Flutter, Kotlin Compose, SwiftUI, native Android (Java/Kotlin), native iOS (Swift), Capacitor + Vue/React, Ionic.

### Backend / full-stack
Laravel + Inertia, Laravel + Livewire, NestJS + Prisma, FastAPI, Django + HTMX, t3-stack, RedwoodJS, Rails 8 + Hotwire, Phoenix LiveView, Go (Gin/Echo), Nest + GraphQL, Hono, Bun.

### Game engines / tooling
Godot, Unity asset bundles, GameMaker, Construct 3, RPG Maker, GDevelop, Cocos Creator, Phaser, Bevy, Defold.

### 3D / AR
Three.js, R3F, Babylon.js, A-Frame, model-viewer, Spline.

### AI tooling
LangChain/LlamaIndex apps, Claude Skills, MCP servers, OpenAI Realtime API, Vercel AI SDK, custom RAG pipelines.

### No-code / low-code (vendibles)
Bubble, Webflow, Framer, Glide, Softr templates.

## 2. Ranking comercial 2026 (top 15)
Los 15 stacks con MEJOR ROI tiempo→ventas en 2026. Justifica cada uno.

## 3. Stacks crecimiento explosivo
5-10 stacks creciendo >100% YoY en 2026 — los que serán mainstream en 2027.

## 4. Stacks moribundos
5-8 stacks en declive — evítalos para producto nuevo.

## 5. Por marketplace: qué stack vende más
Para cada marketplace (ThemeForest, CodeCanyon, Gumroad, Itch.io, Shopify, wp.org, Unity Asset Store), top 5 stacks por revenue/ventas.

## 6. Por buyer-persona
- **No-dev / pequeño negocio**: top stacks que NO requieren tocar código.
- **Dev solo / freelancer**: top stacks con time-to-market < 1 semana.
- **Equipo / agencia**: top stacks con buen DX y escalabilidad.

## 7. Decisión: si arrancara hoy un negocio de productos digitales en 2026
Top 3 stacks que escogería + justificación con cifras.

Markdown estructurado, tablas siempre que se pueda. Sé exhaustivo."""


def prompt_niche(niche: str) -> str:
    return f"""# Deep-dive de mercado — nicho: «{niche}» (2026)

Analiza este nicho específico en profundidad. Dame:

1. **Tamaño y volumen**: ¿cuánto se mueve aquí? Marketplaces principales y ventas mensuales estimadas.
2. **Top 10 productos vendidos** en 2026 (nombre / autor si lo recuerdas / precio / ventas / por qué venden).
3. **Stacks tecnológicos más vendidos** para este nicho — MÍNIMO 7 opciones distintas con pros/contras comerciales (no técnicos).
4. **Sub-nichos calientes** dentro de este vertical.
5. **Tendencias 2026**: qué pide la gente, qué se queda anticuado.
6. **Pricing strategy**: rangos de precio, qué justifica precios premium ($79-149), qué se vende mejor en bajo precio ($19-39).
7. **Marketing / SEO hooks** que están funcionando este año en este nicho.
8. **Competidores top a estudiar** (3-5 nombres concretos) y qué hace cada uno bien/mal.
9. **Gap analysis**: ángulos infraexplotados — dónde entrar a competir con ventaja.
10. **Plan de ataque para 2026**: si lanzara un producto hoy en este nicho, ¿qué exactamente debería sacar (formato, stack, precio, USP)?

Markdown bien estructurado, tablas donde aporte."""


def prompt_compare(niche_a: str, niche_b: str) -> str:
    return f"""# Comparativa de mercado: «{niche_a}» vs «{niche_b}» (2026)

Comparativa lado a lado de ambos nichos para decidir cuál atacar.

## Tabla comparativa
| Métrica | {niche_a} | {niche_b} |
|---|---|---|
| Volumen mensual de ventas | … | … |
| Precio medio | … | … |
| Saturación (1-10) | … | … |
| Tendencia 2026 | … | … |
| ROI tiempo→ventas | … | … |
| Marketplace dominante | … | … |
| Stacks top (3) | … | … |
| Esfuerzo de creación (h) | … | … |

## Análisis cualitativo
- ¿Quién paga mejor en cada nicho?
- ¿Cuál crece más rápido?
- ¿Cuál tiene mayor lifetime value (upsells, updates)?
- ¿Cuál es más resistente a cambios de marketplace algorithm?

## Recomendación
Sé claro: si tuvieras que elegir UNO de los dos para lanzar en 30 días con presupuesto limitado, ¿cuál y por qué? Justifica con datos."""


def prompt_marketplace(marketplace: str) -> str:
    return f"""# Análisis profundo de marketplace — «{marketplace}» (2026)

Concéntrate solo en este marketplace.

1. **Salud del marketplace en 2026**: tráfico, ventas totales aproximadas, crecimiento YoY.
2. **Categorías más vendidas** este año (top 10) con cuota y precio medio.
3. **Top sellers/items 2026** (con cifras estimadas).
4. **Algorithm/discoverability**: cómo se posiciona arriba en 2026 (SEO interno, ratings, refreshes, tags…).
5. **Pricing tiers que más venden** y por qué.
6. **Requisitos de calidad/aprobación** (si aplica).
7. **Comisiones / split** vigente.
8. **Tendencias que premian** vs lo que castiga el algoritmo.
9. **Tipos de producto infraexplotados** con potencial alto.
10. **Estrategia ganadora** para entrar nuevo en este marketplace en 2026: primeros 90 días, qué publicar, cómo escalar.

Markdown con tablas."""


def prompt_prediction() -> str:
    return """# Predicción de mercado 2027 — productos digitales

Mira a 12 meses vista. Argumenta con datos y tendencias actuales (2026).

## 1. Nichos que van a EXPLOTAR en 2027
Top 10, con justificación de por qué crecerán.

## 2. Nichos que van a DECRECER
Top 8, con qué los está canibalizando.

## 3. Stacks ganadores en 2027
- Frontend / WP / mobile / backend / AI tooling.
- Qué va a desplazar a los líderes actuales.

## 4. Tipos de producto nuevos que aparecerán
- Categorías que hoy no existen como tal y que serán mainstream en 2027.

## 5. Riesgos de mercado
- Marketplaces que podrían perder cuota.
- Cambios algorítmicos que castigarán a quién.
- Saturación inminente.

## 6. Plan de inversión de tiempo (mío) para 2026-2027
Si tuviera que dedicar mis próximos 6 meses a crear productos digitales que se vendan en 2027, ¿exactamente qué crearía? Lista priorizada con esfuerzo estimado y revenue esperado por ítem.

Markdown bien estructurado, sé concreto."""


# ─── Modo Oportunidades (scoring estructurado + stack recomendado) ───────


def _stacks_catalog() -> str:
    """Lista compacta de stacks reales (id · nombre · categoría) para el prompt."""
    try:
        import stacks
        rows = []
        for sid, s in stacks.STACKS.items():
            if sid == "none":
                continue
            rows.append(f"- {sid} · {s.get('name','')} ({s.get('category','')})")
        return "\n".join(rows)
    except Exception:
        return "- nextjs-tailwind · Next.js + Tailwind\n- astro-tailwind · Astro + Tailwind"


def prompt_opportunities(params: dict | None = None) -> str:
    params = params or {}
    n = int(params.get("n", 8))
    focus = params.get("focus", "").strip()
    catalog = _stacks_catalog()
    focus_line = f"\nEnfócate en: **{focus}**.\n" if focus else ""
    return f"""Eres un cazador de oportunidades de productos digitales. Detecta las **{n} mejores oportunidades para crear y vender ESTA SEMANA**, basándote en los DATOS REALES de Envato de arriba y en la búsqueda web.{focus_line}

Para cada oportunidad puntúa de 0 a 100:
- **demanda**: cuánta gente lo busca/compra (mayor = mejor).
- **competencia**: nivel de saturación (0 = hueco vacío, 100 = saturadísimo).
- **dificultad**: lo difícil que es construirlo bien (0 = fácil, 100 = muy difícil).
- **ingresos**: potencial de ingresos (mayor = mejor).
- **oportunidad**: score GLOBAL (mayor = mejor). Combina lo anterior: premia demanda+ingresos, penaliza competencia+dificultad.

Recomienda para cada una un **stack** usando el ID EXACTO de este catálogo (no inventes ids):
{catalog}

Responde **SOLO con JSON válido** (sin markdown, sin texto antes/después), con esta forma EXACTA:
{{
  "titulo": "Top {n} oportunidades — <mes año>",
  "oportunidades": [
    {{
      "nombre": "nombre corto del producto/nicho",
      "pitch": "una frase de por qué es oportunidad ahora",
      "marketplace": "ThemeForest | CodeCanyon | Gumroad | ...",
      "precio": "rango de precio sugerido, ej. $29–59",
      "scores": {{"demanda": 0, "competencia": 0, "dificultad": 0, "ingresos": 0, "oportunidad": 0}},
      "evidencia": "dato REAL que lo respalda (ventas/precio de Envato o web)",
      "stack": "id-exacto-del-catalogo",
      "como_proceder": ["paso 1 concreto", "paso 2", "paso 3", "paso 4"]
    }}
  ]
}}

Ordena las oportunidades de mayor a menor "oportunidad". Usa cifras reales. No inventes datos ni ids de stack."""


def parse_opportunities(content: str) -> dict | None:
    """Extrae el JSON de oportunidades de la respuesta (tolera fences y prosa)."""
    if not content:
        return None
    txt = content.strip()
    # quitar fences ```json ... ```
    if "```" in txt:
        import re as _re
        m = _re.search(r"```(?:json)?\s*(\{.*?\})\s*```", txt, _re.DOTALL)
        if m:
            txt = m.group(1)
    # quitar citas tipo [1] de perplexity y recortar al primer/último llave
    start, end = txt.find("{"), txt.rfind("}")
    if start < 0 or end <= start:
        return None
    blob = txt[start:end + 1]
    try:
        data = json.loads(blob)
    except Exception:
        # segundo intento: quitar marcadores de cita [n]
        import re as _re
        blob2 = _re.sub(r"\[\d+\]", "", blob)
        try:
            data = json.loads(blob2)
        except Exception:
            return None
    if isinstance(data, dict) and isinstance(data.get("oportunidades"), list):
        return data
    return None


# ─── Engine ─────────────────────────────────────────────────────────────


@dataclass
class AnalysisRequest:
    kind: str           # general | niche | compare | marketplace | prediction
    params: dict        # {niche: ...} | {a:..., b:...} | {marketplace:...}
    model: str          # ID OpenRouter
    user_prompt: str    # ya renderizado
    web: bool = True    # grounding con búsqueda web (datos reales)


def build_request(kind: str, model: str, params: dict | None = None, web: bool = True) -> AnalysisRequest:
    params = params or {}
    if kind == "general":
        p = prompt_general()
    elif kind == "stacks":
        p = prompt_stacks()
    elif kind == "niche":
        p = prompt_niche(params.get("niche", ""))
    elif kind == "compare":
        p = prompt_compare(params.get("a", ""), params.get("b", ""))
    elif kind == "marketplace":
        p = prompt_marketplace(params.get("marketplace", ""))
    elif kind == "prediction":
        p = prompt_prediction()
    elif kind == "opportunities":
        p = prompt_opportunities(params)
    else:
        raise ValueError(f"kind desconocido: {kind}")
    # Años dinámicos: los prompts llevan 2025/2026/2027 fijos → año anterior, actual
    # y siguiente. Orden descendente para no re-sustituir en cascada.
    p = (p.replace("2027", str(NEXT_YEAR))
          .replace("2026", str(YEAR))
          .replace("2025", str(YEAR - 1)))
    return AnalysisRequest(kind=kind, params=params, model=model, user_prompt=p, web=web)


def _envato_preamble(kind: str, params: dict) -> str:
    """Bloque de DATOS REALES de Envato para anteponer al prompt (si hay token).
    Se ejecuta en el worker thread (hace HTTP). Tolerante a fallos → "" si no puede."""
    try:
        import envato_api as ev
    except Exception:
        return ""
    if not ev.has_token():
        return ""
    params = params or {}
    blocks: list[str] = []
    try:
        if kind == "niche":
            blocks.append(ev.market_snapshot("themeforest", term=params.get("niche", "")))
        elif kind == "compare":
            blocks.append(ev.market_snapshot("themeforest", term=params.get("a", "")))
            blocks.append(ev.market_snapshot("themeforest", term=params.get("b", "")))
        elif kind == "marketplace":
            mp = (params.get("marketplace", "") or "").lower()
            if "codecanyon" in mp:
                blocks.append(ev.market_snapshot("codecanyon"))
            elif "themeforest" in mp:
                blocks.append(ev.market_snapshot("themeforest"))
        else:  # general | stacks | prediction
            blocks.append(ev.market_snapshot("themeforest"))
            blocks.append(ev.market_snapshot("codecanyon"))
    except Exception:
        return ""
    blocks = [b for b in blocks if b]
    if not blocks:
        return ""
    return "\n\n".join(blocks) + "\n\n---\n\n"


def call_openrouter(req: AnalysisRequest, api_key: str, timeout: int = 240) -> str:
    """Llama a OpenRouter chat/completions con el prompt y devuelve el
    contenido del mensaje. Lanza RuntimeError con mensaje legible si falla."""
    if not api_key:
        raise RuntimeError("Falta OPENROUTER_API_KEY (configura la credencial de OpenRouter en Settings).")

    # Grounding web: perplexity/sonar* ya buscan; a los demás les añadimos ":online"
    # (OpenRouter ejecuta búsqueda web con Exa y devuelve citas).
    model = req.model
    web = getattr(req, "web", False)
    if web and not model.startswith(_WEB_NATIVE_PREFIXES) and not model.endswith(":online"):
        model = model + ":online"
    system = _SYSTEM + (_WEB_SUFFIX if web else "")

    # Grounding con datos REALES de Envato (bestsellers/ventas/precios) si hay token.
    user_content = req.user_prompt
    if web:
        pre = _envato_preamble(req.kind, req.params)
        if pre:
            user_content = pre + user_content

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.4,
    }
    data = json.dumps(body).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        # OpenRouter recomienda estos headers para aparecer en su leaderboard.
        "HTTP-Referer": "https://github.com/pcreativedev/pcreative-studio",
        "X-Title": "Pcreative Studio - Market Analyzer",
    }
    request = urllib.request.Request(OPENROUTER_URL, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as r:
            payload = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read().decode("utf-8"))
            raise RuntimeError(f"OpenRouter {e.code}: {err.get('error', {}).get('message') or err}")
        except Exception:
            raise RuntimeError(f"OpenRouter HTTP {e.code}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Sin conexión a OpenRouter: {e.reason}")
    try:
        return payload["choices"][0]["message"]["content"]
    except Exception:
        raise RuntimeError(f"Respuesta inesperada de OpenRouter: {str(payload)[:300]}")


# ─── Histórico ──────────────────────────────────────────────────────────


def _ensure_dir() -> None:
    ANALYSES_DIR.mkdir(parents=True, exist_ok=True)


def save_analysis(req: AnalysisRequest, content: str) -> Path:
    _ensure_dir()
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    slug = req.kind
    if req.kind == "niche":
        slug = f"niche-{_slugify(req.params.get('niche',''))}"
    elif req.kind == "compare":
        slug = f"compare-{_slugify(req.params.get('a',''))}-vs-{_slugify(req.params.get('b',''))}"
    elif req.kind == "marketplace":
        slug = f"marketplace-{_slugify(req.params.get('marketplace',''))}"
    fn = ANALYSES_DIR / f"{ts}__{slug}.md"
    header = (
        f"<!-- pcreative-studio-market-analyzer\n"
        f"kind: {req.kind}\n"
        f"params: {json.dumps(req.params, ensure_ascii=False)}\n"
        f"model: {req.model}\n"
        f"date:  {datetime.now().isoformat(timespec='seconds')}\n"
        f"-->\n\n"
    )
    fn.write_text(header + content, encoding="utf-8")
    return fn


def _slugify(s: str) -> str:
    out = []
    for ch in s.lower():
        if ch.isalnum():
            out.append(ch)
        elif out and out[-1] != "-":
            out.append("-")
    return ("".join(out)).strip("-")[:40] or "x"


def list_analyses() -> list[Path]:
    _ensure_dir()
    return sorted(ANALYSES_DIR.glob("*.md"), reverse=True)


def load_analysis(p: Path) -> tuple[dict, str]:
    """Devuelve (metadata, contenido). metadata lleva kind/params/model/date."""
    txt = p.read_text(encoding="utf-8")
    meta: dict = {}
    body = txt
    if txt.startswith("<!-- pcreative-studio-market-analyzer"):
        try:
            end = txt.index("-->")
            head = txt[:end]
            body = txt[end + 3:].lstrip("\n")
            for line in head.splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    meta[k.strip()] = v.strip()
        except Exception:
            pass
    return meta, body


# ─── Util para resolver la API key ──────────────────────────────────────


def get_openrouter_key() -> str:
    """Obtiene la key de OPENROUTER. Primero ai_providers.get_env, luego
    ENV directo, luego ~/.config/pcreative-studio/credentials.json si existiera."""
    try:
        import ai_providers as aip
        env = aip.get_env("openrouter") or {}
        if env.get("OPENROUTER_API_KEY"):
            return env["OPENROUTER_API_KEY"]
    except Exception:
        pass
    if os.environ.get("OPENROUTER_API_KEY"):
        return os.environ["OPENROUTER_API_KEY"]
    return ""
