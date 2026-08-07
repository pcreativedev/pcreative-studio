#!/usr/bin/env bash
# game-iso-multiplayer — scaffold de un juego social isométrico multijugador
# (estilo Habbo): monorepo client (Vite+PixiJS) + server (Colyseus) + Prisma.
# NO-fatal: cada paso avisa y sigue; el agente remata lo que falte siguiendo
# GAME-CONTEXT.md. NO-interactivo.
set +e
TPL="$(cd "$(dirname "$0")" && pwd)"   # templates/game-iso-multiplayer
TFDIR="$(cd "$TPL/../.." && pwd)"       # raíz de Pcreative Studio (para importar módulos)
PROJ="$(pwd)"                           # proyecto nuevo

echo "→ Juego isométrico multijugador (PixiJS + Colyseus)…"

# ── 1. Cliente: Vite + TypeScript (vanilla-ts) ───────────────────────────────
if [ ! -d client ]; then
  echo "  → scaffolding client (Vite vanilla-ts)…"
  npm create vite@latest client -- --template vanilla-ts </dev/null \
    || echo "  ⚠️ vite create falló (revisa Node 20+/red)"
fi
# Sustituye el entrypoint por el render isométrico + cliente Colyseus.
mkdir -p client/src
cp "$TPL/files/client-main.ts" client/src/main.ts 2>/dev/null && echo "  ✅ client/src/main.ts (render iso + net)"
cp "$TPL/files/client-iso.ts"  client/src/iso.ts  2>/dev/null && echo "  ✅ client/src/iso.ts (matemática isométrica)"
# index.html de Vite carga /src/main.ts por defecto; nos vale.

# ── 2. Servidor: Colyseus (autoritativo) ─────────────────────────────────────
[ ! -d server ] && cp -a "$TPL/server" ./server && echo "  ✅ server Colyseus (HotelRoom + A*)"

# ── 3. Persistencia: Prisma + raíz del monorepo ──────────────────────────────
[ ! -d prisma ] && cp -a "$TPL/prisma" ./prisma && echo "  ✅ prisma/schema.prisma"
cp "$TPL/files/root-package.json" package.json 2>/dev/null && echo "  ✅ package.json (workspaces + dev)"
cp "$TPL/GAME-CONTEXT.md" . 2>/dev/null && echo "  ✅ GAME-CONTEXT.md (blueprint — LÉELO)"

cat > .env <<'EOF'
# Servidor de juego (lo lee el cliente Vite y el server)
VITE_SERVER_URL=ws://localhost:2567
# Postgres para Prisma (ajusta o levanta uno con Docker)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/isogame
EOF
echo "  ✅ .env (VITE_SERVER_URL + DATABASE_URL)"

# ── 4. Dependencias (workspaces) — NO-fatal ──────────────────────────────────
echo "  → instalando dependencias (puede tardar)…"
npm install || echo "  ⚠️ npm install raíz incompleto"
# Deps de juego del cliente (PixiJS + cliente Colyseus + A*)
npm install -w client pixi.js colyseus.js easystarjs || echo "  ⚠️ deps de client incompletas"

# ── 5. MCPs relevantes para juego: fetch (docs PixiJS/Colyseus) + playwright
#    (probar el render en navegador) + aseprite (pixel art) SOLO si Aseprite está
#    instalado (si no, sería un server caído permanente). Si haces el HUD con
#    React, el wiring genérico ya añade magic/shadcn/reactbits al abrir el proyecto.
GAME_MCPS="fetch playwright"
ASEPRITE_BIN="$(command -v aseprite 2>/dev/null || command -v aseprite-bin 2>/dev/null)"
if [ -n "$ASEPRITE_BIN" ]; then
  GAME_MCPS="$GAME_MCPS aseprite"
  echo "  → Aseprite detectado ($ASEPRITE_BIN): añadiendo MCP de pixel art"
fi
TFDIR="$TFDIR" GAME_MCPS="$GAME_MCPS" python3 - <<'PY' 2>/dev/null && echo "  ✅ .mcp.json ($GAME_MCPS)"
import os, sys
sys.path.insert(0, os.environ["TFDIR"])
import web_enhancements as we
we.ensure_mcps(".", keys=os.environ["GAME_MCPS"].split())
PY

echo ""
echo "→ Listo. Arranca con:  npm run dev   (server :2567 + client Vite)"
echo "  Lee GAME-CONTEXT.md: arquitectura, isométrico, A*, Colyseus y pixel art."
