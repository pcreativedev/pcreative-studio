"""
web_enhancements.py — Mejoras visuales "pro" para las webs que genera/abre
ThemeForge:

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
MOTION_UI_GUIDE = """# UI PRO + ANIMACIONES — LECTURA OBLIGATORIA (ThemeForge)

> 🎯 **MANDATO**: esta web debe quedar a nivel de **estudio de diseño**:
> profesional, moderna, animada y pulida — NO una plantilla básica. Tienes dos
> armas integradas y DEBES usarlas SIEMPRE, sin que el usuario lo pida:
> **21st.dev** (componentes top vía `/ui`) + **framer-motion** (animación).
> Esto aplica al crear desde cero, al recrear una referencia y al mejorar un
> proyecto existente.

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
    """Escribe UI-MOTION.md en el proyecto (instrucciones para el agente)."""
    p = Path(project_path)
    p.mkdir(parents=True, exist_ok=True)
    target = p / GUIDE_FILE
    target.write_text(MOTION_UI_GUIDE, encoding="utf-8")
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
AUTO_MCP_KEYS = ("magic", "magicui", "shadcn", "fetch", "playwright")


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
