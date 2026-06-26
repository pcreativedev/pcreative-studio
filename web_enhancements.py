"""
web_enhancements.py — Mejoras visuales "pro" para las webs que genera/abre
Pcreative Studio:

  1) **framer-motion** (a.k.a. `motion`) — librería de animación para React/Next.
     Se instala en el setup de cada proyecto frontend y se le dan instrucciones
     a Claude para usarla bien (scroll reveal, micro-interacciones, etc).
  2) **21st.dev** — componentes de UI profesionales. Su integración oficial con
     agentes es el **MCP "Magic"** (`@21st-dev/magic`): Claude escribe componentes
     del registro 21st.dev con `/ui`. Se cablea vía `.mcp.json` (mcp_catalog).

Este módulo es la FUENTE ÚNICA: lo usan tanto `write_setup_script` (proyecto
nuevo) como `ProjectWindow` (tema abierto desde la Galería), para que funcione
en ambos casos.
"""
from __future__ import annotations

import json
from pathlib import Path

GUIDE_FILE = "UI-MOTION.md"

# Guía que se escribe en el proyecto y se referencia desde CLAUDE.md/contexto.
# Son INSTRUCCIONES PARA EL AGENTE (Claude) sobre cómo dejar la web "pro".
MOTION_UI_GUIDE = """# UI PRO + ANIMACIONES — LECTURA OBLIGATORIA (Pcreative Studio)

> 🎯 **MANDATO**: esta web debe quedar a nivel de **estudio de diseño**:
> profesional, moderna, animada y pulida — NO una plantilla básica. Tienes dos
> armas integradas y DEBES usarlas SIEMPRE, sin que el usuario lo pida:
> **21st.dev** (componentes top) + **React Bits** (componentes animados e
> interactivos) + **framer-motion** (animación).
> Esto aplica al crear desde cero, al recrear una referencia y al mejorar un
> proyecto existente.
>
> 📦 Para capacidades de DATOS (gráficos, tablas, mapas, editores rich-text, formularios,
> iconos) lee también **`STACK-PREMIUM.md`** — el stack recomendado por necesidad (verificado
> 2026). Juntas, estas dos guías = todo lo necesario para una web **estudio premium 2026**.

## 1) 21st.dev — componentes profesionales (MCP `magic`) — MODO AUTOMÁTICO

Si el MCP **`magic`** está *connected* (`/mcp`), úsalo para inspirarte de
componentes pro del registro de 21st.dev — **pero EN MODO AUTOMÁTICO, sin
bloquearte esperando al usuario**:

- ✅ **USA `21st_magic_component_inspiration`** (también `/21` o "fetch
  inspiration"): trae componentes + previews del registro 21st.dev **directo al
  chat, sin abrir navegador**. Para CADA sección, busca 2-3 referencias, **ELIGE
  TÚ la mejor** para este nicho, e impleméntala adaptando el código.
- ❌ **NO uses `21st_magic_component_builder` (`/ui`) de forma desatendida**: ese
  ABRE EL NAVEGADOR y SE QUEDA ESPERANDO a que el usuario elija una variante →
  cuelga la generación automática. Solo úsalo si el usuario te pide elegir él.
- Si `magic` no responde o no aporta, **NO te bloquees**: construye tú la sección
  al mismo nivel de estudio (sección 3).

Flujo por sección: (1) `inspiration` para ver referencias pro → (2) eliges la
mejor → (3) la rellenas con el **contenido REAL** del negocio (nada de
lorem/placeholder) → (4) la animas con framer-motion (sección 2). Compatible con
**Tailwind + shadcn/ui**.

## 1.b) React Bits — componentes ANIMADOS e interactivos (MCP `reactbits`)

**React Bits** (135+ componentes React animados, MIT, SIN API key) es tu segunda
fuente de UI — la mejor para **efectos y movimiento** (lo que 21st.dev cubre menos):

- **Text animations**: split/blur/shiny/gradient text, typewriter, scramble, count-up.
- **Backgrounds**: aurora, gradient mesh, beams, dots/grid, particles, waves, noise.
- **Efectos/interacción**: spotlight, magnet, tilt, glare, ripple, click-spark, dock,
  carousels y transiciones llamativas.

Cómo usarlo:
- Si el MCP **`reactbits`** está *connected* (`/mcp`): pídele el componente que quieras
  (busca por nombre/categoría) → trae **código + demo** al chat → adáptalo con el
  contenido real. Ideal para hero, fondos de sección, titulares y CTA.
- También por **CLI shadcn** (no necesita el MCP):
  `npx shadcn@latest add https://reactbits.dev/r/<Componente>-TS-TW`
  (variantes: `JS-CSS`, `JS-TW`, `TS-CSS`, `TS-TW`).

**Cuándo cada uno**: 21st.dev = secciones/bloques completos pro (hero, pricing, bento,
testimonios); **React Bits = el "wow" animado** (fondo del hero, texto animado, efectos
de interacción). Combínalos: bloque de 21st.dev + fondo/efecto de React Bits + framer-motion.

> **Animate UI** (animate-ui.com · github `imskyleen/animate-ui`, MIT) = otra colección de
> componentes React animados (Motion + Tailwind + Radix), complementaria a Magic UI/shadcn,
> centrada en componentes shadcn "con vida" (botones, tabs, switches, counters animados).
> NO tiene MCP propio: se instala **vía el MCP `shadcn` (ya cableado) o `npx shadcn@latest
> add <url-de-animate-ui>`**. Úsala cuando quieras los primitivos shadcn pero animados.
>
> **Animata** (github `codse/animata`, MIT) = otra cantera de animaciones/interacciones
> React + Tailwind + Framer Motion, **copy-paste** estilo shadcn (sin dep ni MCP — copias el
> código de la web). Más efectos/micro-interacciones para combinar con lo anterior.
>
> **shadcn Studio** (shadcnstudio.com · github `shadcnstudio/shadcn-studio`) = registro de
> componentes shadcn **mejorados** + bloques + templates + **theme generator** + motion
> variants. Se usa **vía el MCP `shadcn` (ya cableado)** añadiendo su registro a
> `components.json`, o por shadcn CLI v4. Buena cantera de bloques y temas listos sobre shadcn.
>
> **SmoothUI** (smoothui.dev · github `educlopez/smoothui`, MIT) = 50+ componentes React
> animados (Motion + Tailwind), **registro shadcn oficial** namespace `@smoothui`:
> `npx shadcn@latest add @smoothui/<comp>` o vía el MCP `shadcn`. Otra cantera de componentes
> "con vida" drop-in en cualquier proyecto shadcn.
>
> **Cult UI** (cult-ui.com · github `nolly-studio/cult-ui`, MIT) = componentes para "design
> engineers" (Tailwind + Framer Motion, shadcn-compatible): elementos animados + bloques de
> landing/SaaS (navbars, feature sections, testimonial carousels). `npx shadcn add
> @nolly-studio/<comp>` o vía el MCP `shadcn`.
>
> _(Animate UI · Animata · shadcn Studio · SmoothUI · Cult UI son TODOS registros shadcn de
> componentes animados → se acceden por el mismo MCP `shadcn`/CLI. Elige el componente que
> mejor encaje; no decidas "qué librería" — todos conviven en un proyecto shadcn.)_

## 1.c) Fuentes Tailwind SIN MCP (copy-paste / instalables)

Sin MCP — el agente las usa copiando markup o instalando el paquete. Ambas son Tailwind,
así que framer-motion / React Bits se montan encima:

- **Uiverse.io** (MIT) = **micro-elementos** (botones, loaders, toggles, checkboxes, inputs,
  tooltips) en CSS o Tailwind. Copy-paste desde uiverse.io o el repo `uiverse-io/galaxy`.
  Para los **detalles pulidos** que rematan la web (un botón con hover llamativo, un
  loader bonito, un toggle animado). NO para secciones grandes.
- **Preline UI** (preline.co · github `htmlstreamofficial/preline`, MIT) = set MÁS completo:
  **UI blocks y secciones enteras** (navbars, heros, pricing, footers, tablas) + **plugin JS
  interactivo** (dropdowns, modales, tabs, acordeones, carousels). Funciona en cualquier
  framework (React/Next/Vue/Astro/Laravel). Instala `npm install preline` + carga su JS y
  el `@source` en el CSS de Tailwind. Útil para montar **bloques sólidos rápido** cuando
  21st.dev/React Bits no aporten. Adapta colores a la paleta del tema.

## 1.d) Frameworks de componentes según el stack (HeroUI / Chakra) — MCPs

Si el stack del proyecto ES un framework de componentes concreto, tienes su MCP oficial
para consultar componentes, props, ejemplos e instalación:
- **HeroUI** (ex-NextUI, stack `nextjs-heroui`): MCP `heroui` (`@heroui/react-mcp`, SIN key).
  Es Tailwind v4 + React Aria → **React Bits / 21st.dev / framer-motion funcionan ENCIMA**
  sin conflicto. Si el proyecto es HeroUI, úsalo como base de componentes.
- **Chakra UI**: MCP `chakra-ui` (`@chakra-ui/react-mcp`). Es **ALTERNATIVA a Tailwind/shadcn**
  (NO se mezclan). SIN key lo básico (premium = `CHAKRA_PRO_API_KEY`).

En los temas **Tailwind + shadcn** por defecto, ignora estos dos y usa 21st.dev + React Bits.

## 2) framer-motion — el toolkit completo (úsalo TODO donde encaje)

`framer-motion` ya está instalado (en 2025 se renombró a `motion`, API idéntico;
usa el import `framer-motion`). En **Next.js**, todo archivo con `motion` lleva
`"use client"` arriba.

Aplica estas técnicas (con elegancia, sutil = profesional):

- **Reveal al scroll**: `whileInView` + `viewport={{ once:true, margin:"-80px" }}`, fade + slide-up.
- **Stagger** en listas/grids: `variants` con `staggerChildren` (0.06–0.1s) en el contenedor.
- **Micro-interacciones**: `whileHover` / `whileTap` en botones/cards (scale 1.02–1.05, lift y:-4, sombra).
- **Hero cinematográfico**: entrada fade + scale + blur-out; titular por palabras (stagger) o gradient animado.
- **Parallax / scroll-linked**: `useScroll` + `useTransform` para mover/escalar fondos e imágenes.
- **Tilt 3D** en cards al hover (`rotateX`/`rotateY` suave) cuando quede elegante.
- **Reveal de imágenes** con clip-path/mask (cortina) al entrar en viewport.
- **Count-up** de números/stats al verse.
- **Marquee infinito** para logos/"trusted by".
- **AnimatePresence** para FAQ/acordeón, modales, drawers, tabs (entrada/salida suaves).
- **Barra de progreso de scroll** + botón "volver arriba" con fade.
- **Smooth scrolling** global con `lenis` (instálalo si no está) para inercia.
- **Botones magnéticos** en los CTA principales (opcional, si encaja).

**Reglas de oro:**
- Respeta SIEMPRE `useReducedMotion()` (si está activo, reduce/desactiva).
- Anima SOLO `transform` y `opacity` (60fps); nunca `width`/`height`/`top`.
- En móvil, animaciones más discretas, sin layout shift ni tapar contenido.

```tsx
"use client";
import { motion, useReducedMotion } from "framer-motion";

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  show: (i = 0) => ({ opacity: 1, y: 0, transition: { delay: i * 0.08, duration: 0.5, ease: "easeOut" } }),
};

export function Reveal({ children, i = 0 }: { children: React.ReactNode; i?: number }) {
  const reduce = useReducedMotion();
  if (reduce) return <div>{children}</div>;
  return (
    <motion.div variants={fadeUp} custom={i} initial="hidden"
      whileInView="show" viewport={{ once: true, margin: "-80px" }}>
      {children}
    </motion.div>
  );
}
```

## 2.b) GSAP — animación AVANZADA (cuando framer-motion se queda corto)

**GSAP** (GreenSock) es la librería de animación más potente de la web y desde 2025 es
**100% GRATIS, todos los plugins incluidos** (Webflow) — sin Club, sin token, npm público.
Úsala cuando necesites más que framer-motion:

- **ScrollTrigger** — animaciones ligadas al scroll de nivel pro: pin de secciones, scrub,
  parallax complejo, reveal por timeline, horizontal scroll. (El estándar para scroll.)
- **SplitText** — animar texto por caracteres/palabras/líneas (titulares cinematográficos).
- **MorphSVG / DrawSVG** — morphing de formas e ilustraciones SVG animadas.
- **Timelines** — secuencias complejas y sincronizadas (lo que en framer-motion es engorroso).
- Flip, Draggable, Observer, MotionPath… todos gratis.

Instalación: `npm install gsap @gsap/react`. En **React** usa el hook **`useGSAP()`** de
`@gsap/react` (drop-in de useEffect con cleanup automático de animaciones/ScrollTriggers).
Registra los plugins: `gsap.registerPlugin(ScrollTrigger, SplitText)`.

> 🧠 GSAP publica **skills oficiales para agentes** (github `greensock/gsap-skills`): patrones
> y buenas prácticas. Si trabajas mucho con GSAP, consúltalas/instálalas en `.claude/skills/`.

**framer-motion vs GSAP**: framer-motion para animaciones de UI React declarativas (lo del
día a día, sección 2). **GSAP para lo cinematográfico/scroll avanzado** (hero con scroll-pin,
texto SplitText, morphing). Pueden convivir en el mismo proyecto. Respeta `prefers-reduced-motion`.

## 2.c) Otras librerías de animación — SOLO según el caso (no te disperses)

Por defecto **framer-motion (2) + GSAP (2.b)** cubren casi todo. Una sola librería de
animación PRINCIPAL por proyecto. Estas son alternativas para casos concretos — úsalas solo
si el proyecto ya las trae o el caso lo pide:

- **motion** (`motiondivision/motion`) = **ES framer-motion** (renombrado en 2025, mismo API).
  No es nada nuevo; usa el import `framer-motion`/`motion`.
- **react-spring** (`pmndrs`) = animación por **física de muelles**, ecosistema Poimandres
  (react-three-fiber/drei). Si el proyecto usa r3f o quieres movimiento físico natural.
- **moti** (`nandorojo`) = animación **universal / React Native** (sobre Reanimated, Expo).
  Para los proyectos MÓVILES (Capacitor/Expo), no en web pura.
- **anime.js** (animejs.com, MIT) = librería de animación JS **LIGERA** (~9kb) y
  framework-agnostic; v4 (2025) modular con timelines, scroll-linked, draggable y SVG. La
  alternativa ligera a GSAP cuando no necesitas sus plugins pesados (vanilla/React/Vue).
  `npm install animejs`.
- **scenejs** (`daybrush`) = timeline animation **framework-agnostic** (JS puro); alternativa
  a GSAP fuera de React.
- **animxyz** (`ingram-projects`) = animaciones **CSS composables** (clases utilitarias),
  framework-agnostic; para CSS simple sin JS.
- **cursify** (`ui-layouts`) = **efectos de cursor** React/Next (trail, spotlight, magnetic…,
  18+), copy-paste estilo shadcn; para el "wow" del cursor en landings.
- ⚠️ **react-motion** (`chenglou`) = **LEGACY/abandonado** → NO lo uses; su sucesor es react-spring.

GSAP y cursify se montan ENCIMA de la librería principal (para scroll cinematográfico y cursor).

## 2.d) 3D / WebGL — SOLO cuando el nicho lo pide (no por defecto)

El 3D es **conversion driver** en e-commerce 2026 (los configuradores suben el AOV y reducen
devoluciones), pero PESA. Úsalo solo en nichos que lo justifican — **joyería, gafas, sneakers,
muebles, relojes, tech/gadgets, automoción, alto ticket** — y para **configuradores de producto**
(girar/personalizar en vivo) o un hero 3D puntual. En panadería/growshop/ropa básica = **NO**
(ahí React Bits/GSAP dan el wow sin el coste).

**Stack (React):** `@react-three/fiber` (r3f) + `@react-three/drei` (helpers), ecosistema pmndrs.
Configuradores: + `valtio` (estado) + framer-motion. Alternativa **no-code**: **Spline**
(spline.design) → diseñas la escena y la exportas a React (mucho más rápido que Three.js a mano
para un hero 3D).

**Reglas de rendimiento (OBLIGATORIAS — si no, tumba el Lighthouse / la review de Envato):**
- **Lazy-load** la escena con `React.lazy` + `Suspense` → carga DESPUÉS del primer paint (protege LCP).
- **Poster/fallback** estático mientras carga y en móvil/low-power; respeta `prefers-reduced-motion`.
- Modelos **GLTF/GLB con compresión Draco**; texturas **KTX2/Basis** (no PNG/JPG). LOD con drei `<Detailed/>`.
- `frameloop="demand"` (on-demand render: pinta solo cuando cambia → batería/móvil).
- Mutaciones en `useFrame`, NO en React state. Draw calls < ~1000 (instancing para objetos repetidos).
- Moderno opcional: **WebGPURenderer** de `three/webgpu` (Safari 26+ lo soporta; fallback WebGL2 auto).

NO tiene MCP (es librería) → se instala y se codea. r3f es del mismo ecosistema que react-spring.

## 2.e) NIVEL AWWWARDS — el recipe WebGL premium

Para webs de **impacto máximo** (landings de marca premium, lanzamientos de producto, portfolios,
experiencias). **NO para e-commerce de conversión pura** — ahí un preloader o scroll pesado mata
ventas; usa 3D solo en hero/configurador (2.d). Las webs que ganan Awwwards combinan SIEMPRE
estas piezas (cada una hace lo suyo):

1. **Motor WebGL** — Three.js / **react-three-fiber** (3D completo) · **OGL** (ligero, ideal para
   galerías/efectos de imagen WebGL) · Pixi.js (2D WebGL).
2. **Shaders GLSL custom** — vertex (geometría) + fragment (color/luz). El alma de los efectos
   únicos: distorsión de imágenes al scroll/hover, transiciones líquidas, texto WebGL.
3. **Postprocessing** — efectos full-screen tras renderizar (bloom, depth of field, chromatic
   aberration, grain). En r3f → **`@react-three/postprocessing`** (EffectComposer). Da el look cine.
4. **Smooth scroll = Lenis** (Studio Freight) — EL estándar premium: interpola el scroll →
   sensación fluida/cinematográfica. `npm i lenis`. Se sincroniza con GSAP ScrollTrigger (Lenis
   maneja el FEEL del scroll, GSAP el QUÉ pasa al hacer scroll).
5. **GSAP + ScrollTrigger + SplitText + Flip** — timelines, reveal por scroll, texto
   cinematográfico, y **Flip** (transiciones de layout: los elementos "vuelan" a su nueva
   posición — el efecto premium clásico). Todos los plugins de GSAP son gratis.
   *Verificado por scraping: nymphaicosmetics.com (Shopify) carga GSAP full + Lenis;
   digitalists.at (WordPress) empaqueta Three.js + shaders GLSL + GSAP + Lenis + Barba.*
6. **Preloader / loading sequence** — pantalla de carga animada con barra de progreso REAL de los
   assets (texturas/modelos). Obligatorio si hay WebGL pesado.
7. **Transiciones de página** — entre rutas (View Transitions API / framer-motion AnimatePresence
   / barba.js en vanilla): continuidad sin recargas bruscas.
8. **Custom cursor** — cursor interactivo (magnético, con estados); React Bits/cursify ya lo dan.

Estudios de referencia (mira sus webs para calibrar el nivel): **Lusion · Studio Freight · Obys ·
Garden Eight · Refokus · Merci Michel**. Galería: awwwards.com/websites/3d.

⚠️ **Rendimiento**: aplica TODAS las reglas de 2.d (lazy-load, poster/fallback, Draco/KTX2, LOD,
on-demand render, reduced-motion). Una web Awwwards también es RÁPIDA — el wow nunca a costa de un
LCP roto en móvil.

## 3) Calidad de estudio (checklist mínimo)

- Tipografía con jerarquía (display serif/sans elegante + texto legible), buen tracking.
- Espaciado generoso y ritmo vertical consistente; grid bien alineado.
- Paleta coherente con el nicho + un acento; gradientes/sombras sutiles.
- Estados hover/focus/active en TODO lo interactivo (WCAG AA, focus visible).
- Imágenes reales optimizadas (`next/image`, alt, width/height, lazy below-fold).
- Responsive 360→1920 impecable. Dark mode si encaja.
- También aplica las skills de `.claude/skills/` (UI/UX Pro) si están.

**Objetivo**: que al primer `npm run dev` parezca hecho por un estudio, no por
una plantilla. Hazlo como parte de la primera versión, sin pedir permiso.
"""

STACK_FILE = "STACK-PREMIUM.md"

# Guía del STACK FUNCIONAL por capacidad (datos, mapas, editores, forms, iconos).
# Complementa UI-MOTION.md (componentes + animación + 3D). Para webs estudio premium 2026.
STACK_GUIDE = """# STACK PREMIUM 2026 — librerías por capacidad (Pcreative Studio)

> Complementa **UI-MOTION.md** (componentes + animación + 3D). Aquí el stack FUNCIONAL: datos,
> tablas, mapas, editores, formularios, iconos. Objetivo: webs hyper-avanzadas nivel **ESTUDIO
> PREMIUM**. Verificado 2026.
>
> **Regla de oro: instala SOLO lo que el proyecto necesita** — cada librería pesa. No metas un
> editor rich-text en una landing simple ni un mapa donde no hay tienda física.

## Gráficos / Data viz
- **Recharts** (DEFAULT) — declarativo, SVG, lo común de dashboards. `npm i recharts`.
- **Tremor** — para DASHBOARDS shadcn-style out-of-the-box (admin/analytics). Úsalo en los
  paneles de administración para que queden pro sin currártelos.
- Nivo (precioso pero ~500kB) / visx (low-level Airbnb, máximo control, mucho código) → especiales.
- 100k+ puntos → ECharts/Chart.js (canvas, más rápido que SVG).

## Tablas / Data grids
- **TanStack Table + shadcn/ui** (DEFAULT) — headless, MIT, ~30kB, máxima flexibilidad. Cubre el
  90% (listados de productos/pedidos/clientes). + `@tanstack/react-virtual` para miles de filas.
- AG Grid → solo Excel-like enterprise (pivot/copy-paste); sus features avanzadas son de PAGO.

## Editores rich-text
- **Plate** (recomendado con shadcn) — sobre Slate, componentes shadcn/ui + plugins. Para
  descripciones de producto ricas, blog/CMS del admin, páginas editables.
- **Tiptap** — la más popular/segura (ProseMirror, 50+ extensiones), framework-agnostic.
- Lexical (Meta, ~22kB, el más rápido) → documentos enormes / accesibilidad crítica.

## Mapas
- **MapLibre GL JS + react-map-gl** (DEFAULT) — WebGL, vector tiles, 3D, **SIN API key**, MIT.
  Para localizador de tiendas, "dónde estamos" (contacto), zonas de envío.
- Mapbox → solo si necesitas su servicio (50k loads/mes free). Leaflet → mapas simples sin WebGL.

## Iconos
- **Lucide** (DEFAULT) — de facto shadcn, bundle mínimo, 1500+. Primera opción.
- **Iconify** — COMODÍN: miles de iconos de todas las librerías (FontAwesome/Material/Heroicons…)
  en un paquete. Cuando Lucide no tenga el icono concreto del nicho.
- **Phosphor** (9000+, 6 pesos incl. duotone) → estados visuales/illustrativos. Tabler → dashboards.

## Formularios
- **react-hook-form + Zod** (DEFAULT 2026) — ~9kB, mejor TS inference, validación + tipos. Es EL
  estándar; úsalo siempre. ⚠️ **NO uses Formik** (maintenance mode, 3x más pesado).
- **autoform** — genera formularios shadcn DESDE un schema Zod (forms automáticos en el admin).
- TanStack Form → alternativa headless si quieres control total de la UI.

## 3D / WebGL · animación · componentes
→ ver **UI-MOTION.md** (r3f/drei/Spline + reglas de rendimiento · framer-motion/GSAP/anime.js ·
21st.dev/React Bits/shadcn-registries/Uiverse/Preline/HeroUI).

## Qué es "ESTUDIO PREMIUM 2026" (combínalo con criterio)
Componentes pro (21st.dev/React Bits) + animación CON INTENCIÓN (framer-motion + GSAP donde
sume) + datos bien visualizados (Recharts/Tremor) + microdetalles (Uiverse/cursify) + iconos
coherentes (Lucide/Iconify) + 3D **solo** donde el nicho lo pida (joyería/tech/configuradores).
**Rendimiento SIEMPRE** (lazy-load, LCP, `prefers-reduced-motion`, code-split). Contenido REAL
(nunca lorem). WCAG AA. Responsive 360→1920. Menos es más: cada efecto debe tener propósito.
"""

# Dependencias que detectan un proyecto frontend Node donde framer-motion aplica.
_FRONTEND_DEPS = ("react", "next", "vite", "@remix-run", "gatsby", "preact",
                  "solid-js", "astro")


def is_node_frontend(project_path: str | Path) -> bool:
    """¿Es un proyecto Node con React/Next/Vite/…? (donde framer-motion aplica)."""
    p = Path(project_path)
    # Busca package.json en la raíz o en sub-apps típicas de monorepo.
    candidates = [p / "package.json"]
    for sub in ("web", "app", "frontend", "site", "client", "apps", "src"):
        candidates.append(p / sub / "package.json")
    for pj in candidates:
        if not pj.is_file():
            continue
        try:
            data = json.loads(pj.read_text(encoding="utf-8"))
        except Exception:
            continue
        deps = {**(data.get("dependencies") or {}),
                **(data.get("devDependencies") or {})}
        low = " ".join(deps.keys()).lower()
        if any(d in low for d in _FRONTEND_DEPS):
            return True
    return False


def has_framer_motion(project_path: str | Path) -> bool:
    """¿Ya está framer-motion (o motion) en las deps?"""
    p = Path(project_path)
    for pj in (p.rglob("package.json")):
        if "node_modules" in pj.parts:
            continue
        try:
            data = json.loads(pj.read_text(encoding="utf-8"))
        except Exception:
            continue
        deps = {**(data.get("dependencies") or {}),
                **(data.get("devDependencies") or {})}
        if "framer-motion" in deps or "motion" in deps:
            return True
    return False


def write_guide(project_path: str | Path) -> Path:
    """Escribe UI-MOTION.md (UI/animación/3D) + STACK-PREMIUM.md (datos/mapas/editores/
    forms/iconos) en el proyecto. Instrucciones para el agente. Devuelve UI-MOTION.md."""
    p = Path(project_path)
    p.mkdir(parents=True, exist_ok=True)
    target = p / GUIDE_FILE
    target.write_text(MOTION_UI_GUIDE, encoding="utf-8")
    try:
        (p / STACK_FILE).write_text(STACK_GUIDE, encoding="utf-8")
    except Exception:
        pass
    return target


def has_21st_key() -> bool:
    """¿Hay API key de 21st.dev (env o credenciales)? Sin ella el MCP magic no
    arranca, así que no lo cableamos para no dejar un servidor roto."""
    import os
    if os.environ.get("TWENTYFIRST_API_KEY"):
        return True
    try:
        import ai_providers
        return bool(ai_providers.load_keys().get("twentyfirst"))
    except Exception:
        return False


# MCPs de UI/web que se cablean en CUALQUIER proyecto frontend. Todos SIN API
# key (salvo `magic`, que se salta si no hay key 21st.dev). `higgsfield` NO está
# aquí a propósito: es de pago, se activa a mano.
AUTO_MCP_KEYS = ("magic", "magicui", "shadcn", "reactbits", "fetch", "playwright")


def ensure_mcps(project_path: str | Path, keys=AUTO_MCP_KEYS) -> list:
    """Asegura los MCPs dados en el .mcp.json del proyecto (sin pisar otros).
    Salta `magic` si no hay key 21st.dev. Devuelve los que añadió."""
    try:
        import mcp_catalog as mc
    except Exception:
        return []
    p = Path(project_path)
    f = p / ".mcp.json"
    data = {"mcpServers": {}}
    if f.is_file():
        try:
            data = json.loads(f.read_text(encoding="utf-8")) or {"mcpServers": {}}
        except Exception:
            data = {"mcpServers": {}}
    data.setdefault("mcpServers", {})
    added = []
    for key in keys:
        if key in data["mcpServers"]:
            continue
        if key == "magic" and not has_21st_key():
            continue
        entry = next((e for e in mc.CATALOG if e.key == key), None)
        if entry is None:
            continue
        built = mc.generate_mcp_json([entry], p)
        data["mcpServers"][key] = built["mcpServers"][key]
        added.append(key)
    if added:
        try:
            f.write_text(json.dumps(data, indent=2, ensure_ascii=False),
                         encoding="utf-8")
        except Exception:
            pass
    return added


def ensure_magic_mcp(project_path: str | Path) -> bool:
    """Compat: asegura el set de MCPs de UI (magic + magicui + shadcn + fetch)."""
    return bool(ensure_mcps(project_path))


def motion_install_cmd(pkg_manager: str = "npm") -> str:
    """Comando shell para instalar framer-motion con el gestor adecuado."""
    pm = (pkg_manager or "npm").lower()
    if pm == "pnpm":
        return "pnpm add framer-motion"
    if pm == "yarn":
        return "yarn add framer-motion"
    if pm == "bun":
        return "bun add framer-motion"
    return "npm install framer-motion"


def ensure_for_project(project_path: str | Path,
                       install_motion: bool = False) -> dict:
    """Aplica TODO lo barato (guía + MCP magic) y, si install_motion y es un
    frontend Node sin framer-motion, devuelve el comando de instalación para que
    el llamador lo ejecute en una terminal. No bloquea ni hace npm install aquí.

    Devuelve {guide, magic, needs_motion, install_cmd}."""
    p = Path(project_path)
    # La guía UI-MOTION (framer-motion) y el MCP magic (21st.dev → componentes
    # React/Tailwind/shadcn) SOLO aplican a frontends Node/React. En PHP/Smarty
    # (PrestaShop, Magento…), Ruby, etc. no se escriben para no meter ruido.
    node = is_node_frontend(p)
    guide = bool(write_guide(p)) if node else False
    magic = ensure_magic_mcp(p) if node else False
    needs_motion = (install_motion and node and not has_framer_motion(p))
    return {
        "guide": guide,
        "magic": magic,
        "needs_motion": needs_motion,
        "install_cmd": motion_install_cmd() if needs_motion else "",
    }


if __name__ == "__main__":
    # Uso desde el setup script: `python3 web_enhancements.py <project_dir>`
    # Escribe la guía + asegura el MCP magic. Imprime el comando de instalación
    # de framer-motion si hace falta (el bash que llama puede ejecutarlo).
    import sys
    _path = sys.argv[1] if len(sys.argv) > 1 else "."
    try:
        _res = ensure_for_project(_path, install_motion=True)
        print(_res.get("install_cmd", ""))
    except Exception as _e:
        print("", end="")
