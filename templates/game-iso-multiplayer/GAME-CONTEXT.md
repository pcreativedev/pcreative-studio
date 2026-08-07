# 🎮 GAME-CONTEXT — Juego social isométrico multijugador (estilo Habbo Hotel)

> **LECTURA OBLIGATORIA antes de tocar código.** Este fichero es el blueprint del
> stack. Define la arquitectura, las matemáticas isométricas, el modelo de red y el
> flujo de pixel art. Síguelo; no reinventes la rueda con otra arquitectura.

Construyes un **juego social isométrico 2D multijugador en navegador** estilo *Habbo
Hotel*: salas isométricas donde avatares de varios jugadores **caminan en tiempo real**,
**chatean**, colocan **muebles (furni)**, tienen **inventario** y persisten su progreso.

---

## 1. Stack y arquitectura (NO la cambies)

Monorepo (`npm`/`pnpm workspaces`):

```
client/   Vite + TypeScript + PixiJS 8  → render isométrico + input + interpolación
server/   Colyseus 0.16 (Node + TS)     → servidor AUTORITATIVO: salas, estado, validación
prisma/   Prisma + PostgreSQL           → persistencia (cuentas, salas, furni, inventario)
```

- **PixiJS** = renderer 2D WebGL (NO es un engine completo: tú escribes la lógica). Ideal
  para sprites isométricos, ligero (~200 KB).
- **Colyseus** = framework multijugador con **Rooms** (una `Room` = una sala de Habbo),
  state sync por diffing automático (`@colyseus/schema`), matchmaking y SDK de cliente.
- **Regla de oro — SERVIDOR AUTORITATIVO**: el cliente NUNCA decide su posición. Manda
  *intención* ("quiero ir a la baldosa X,Y"), el servidor calcula el camino (A*), mueve
  paso a paso a **fixed timestep** y replica el estado. El cliente solo **renderiza e
  interpola**. Esto evita cheats y desincronización.
- **Separación de responsabilidades**: render/input en `client/`, lógica de juego y verdad
  en `server/`. Tipos compartidos en `@colyseus/schema` (el state ES el contrato).

## 2. Render isométrico (PixiJS)

- **Proyección 2:1** (dimétrica, como Habbo). Baldosa lógica `(tx, ty)` → pantalla:
  ```ts
  // TILE_W = 64, TILE_H = 32  (ancho:alto = 2:1)
  screenX = (tx - ty) * (TILE_W / 2)
  screenY = (tx + ty) * (TILE_H / 2)
  ```
  e inversa (pantalla → baldosa) para clicks. Ver `client/src/iso.ts`.
- **Depth sorting**: dibuja por `tx + ty` ascendente (las baldosas/objetos "más atrás"
  primero). Para sprites altos (avatares, furni) ordena por la baldosa que ocupan +
  offset. Usa un `Container` con `sortableChildren` y `zIndex = (tx + ty)`.
- **Cámara**: centra la sala; pan con drag, zoom con rueda (limita escala). El suelo es un
  `Container` con sprites de baldosa; los avatares y furni van en un container ordenable.
- **Tiles**: 64×32 px diamante. El suelo se compone de baldosas; las paredes son sprites
  altos en los bordes. Hover de baldosa = highlight (sprite semitransparente).

## 3. Pathfinding A* (easystarjs)

- La sala es una **rejilla lógica** `grid[ty][tx]` con 0 = transitable, 1 = bloqueado
  (paredes, furni sólido, otros avatares opcional). El render es isométrico pero la
  **lógica es una matriz 2D normal**.
- **easystarjs** calcula el camino A* sobre esa matriz. Permite diagonales
  (`enableDiagonals()`) como Habbo. **El cálculo va en el SERVIDOR** (autoritativo): el
  cliente clica una baldosa → manda `move {tx,ty}` → el servidor valida, hace A*, y avanza
  al avatar una baldosa por tick replicando `players[id].tx/ty` + dirección.
- El cliente **interpola** suavemente entre la baldosa anterior y la nueva (lerp de la
  posición de pantalla) y reproduce la animación de andar en la dirección correcta.

## 4. Red: Colyseus (Rooms + Schema)

- **State** (`@colyseus/schema`) = el contrato cliente↔servidor. Mínimo:
  ```ts
  class Player extends Schema { @type("string") name; @type("number") tx; @type("number") ty;
    @type("number") dir; @type("boolean") walking; @type("string") look; /* avatar */ }
  class Furni  extends Schema { @type("string") kind; @type("number") tx; @type("number") ty;
    @type("number") rot; }
  class HotelState extends Schema { @type({map:Player}) players = new MapSchema();
    @type([Furni]) furni = new ArraySchema(); @type("number") width; @type("number") height; }
  ```
- **Mensajes cliente→servidor** (todos VALIDADOS en servidor): `move {tx,ty}`,
  `chat {text}` (sanea + rate-limit), `placeFurni {kind,tx,ty,rot}`,
  `pickFurni {furniId}`, `sit`, `wave`, `dance`.
- **Servidor→cliente**: vía el state sync automático + `broadcast` para chat/efectos.
- **Tick**: `setSimulationInterval(dt => this.update(dt), 1000/20)` (20 Hz). Cada tick
  avanza los avatares en movimiento una baldosa cuando toca, según su camino A*.
- **Cliente**: `client.joinOrCreate("hotel", {name, look})`; escucha `room.state.players`
  (`onAdd/onRemove/onChange`) para crear/mover/quitar sprites; `room.send("move", ...)`.
- **Anti-cheat básico**: el servidor ignora moves a baldosas no adyacentes-alcanzables,
  limita el rate de chat, valida que el furni colocado esté en inventario y la baldosa
  libre. NUNCA confíes en datos del cliente.

## 5. 🎨 Pixel art (lo que hace que parezca Habbo)

- **Estética**: pixel art isométrico, paleta limitada y cohesiva, outline oscuro, dithering
  suave para sombras. Sprites a 32–64 px. Sin antialiasing: en PixiJS pon
  `texture.source.scaleMode = "nearest"` y `roundPixels = true`.
- **Avatares**: spritesheet con **8 direcciones** (N, NE, E, SE, S, SW, W, NW) × estados
  (idle, walk, sit, wave). El `dir` del state elige el frame. Mantén un punto de anclaje
  consistente (pies en el centro de la baldosa).
- **Furni**: cada mueble = sprite (o spritesheet si anima/rota) con su footprint en baldosas
  y su offset de altura. Define `furni/<kind>.json` con {size, sprite, solid, sittable}.
- **MCP `aseprite` / `pixel-art`** (si está conectado, `/mcp`): pídele crear/editar sprites
  por lenguaje natural — paletas retro, dithering, shading, **export a spritesheet**. Es la
  forma rápida de generar avatares/furni/tiles coherentes. Si no hay Aseprite, usa assets
  CC0 (ver abajo) o genera tiles por código (Graphics) como placeholder.
- **Assets libres mientras desarrollas** (CC0, atribución en `CREDITS.md`):
  Kenney.nl (isometric tiles/characters), OpenGameArt, itch.io (filtra CC0). NO uses
  assets de Habbo/Sulake (copyright). El arte final debe ser **propio**.

## 6. Persistencia (Prisma + Postgres)

Modelos mínimos (`prisma/schema.prisma`): `User` (auth, look del avatar, créditos),
`Room` (dueño, layout/grid JSON, modelo de suelo), `Furni` (catálogo) +
`UserFurni`/`Inventory` (lo que posee el usuario), `RoomFurni` (lo colocado en cada sala),
`ChatLog` (opcional/moderación). El servidor Colyseus carga el layout de la sala al crear
la Room y persiste cambios (furni colocado, créditos) en `onLeave`/periódicamente.

## 7. Roadmap por fases (constrúyelo en este orden)

1. **Render base**: pinta una sala isométrica (suelo de baldosas + paredes) con
   `iso.ts`. Hover y click → baldosa correcta. Cámara con pan/zoom.
2. **Multiplayer mínimo**: Colyseus `HotelRoom` con `players`; conecta el cliente,
   aparece un avatar (placeholder), click-to-move con A* en el servidor, otros jugadores
   se ven moverse en tiempo real. **Esto debe funcionar al primer `npm run dev`.**
3. **Avatares con sprites** 8-dir + animación de andar + interpolación cliente.
4. **Chat** (burbujas sobre el avatar + log) con rate-limit y saneo.
5. **Furni**: colocar/recoger/rotar, footprint, sólidos bloquean el pathfinding, sentarse.
6. **Inventario + economía** (créditos) + **catálogo/tienda**.
7. **Persistencia** (Prisma): cuentas, salas guardadas, inventario.
8. **Navegador de salas** (lobby), crear/entrar salas, aforo.
9. Pulido: emotes (wave/dance), efectos, sonido, moderación, escala (Redis presence).

## 8. MCPs y skills recomendados

- MCPs (`/mcp` debe mostrarlos *connected*): **`aseprite`/`pixel-art`** (sprites),
  **`playwright`** (probar el render/jugabilidad en navegador headless, capturas),
  **`fetch`** (docs de PixiJS/Colyseus). magic/magicui/shadcn/reactbits aplican al **HUD/
  menús** (login, tienda, inventario) si los haces con React.
- Skills: `frontend-design` (HUD), patrones de TypeScript. Para PixiJS/Colyseus apóyate en
  sus docs oficiales (vía `fetch`): pixijs.com, docs.colyseus.io.

## 9. Rendimiento y a11y

- `roundPixels: true`, `scaleMode: "nearest"`, culling de lo fuera de cámara, sprite pooling
  para avatares/furni, `ParticleContainer` para multitudes. Limita el tick a 20 Hz e
  interpola en cliente a 60 fps. Respeta `prefers-reduced-motion` en el HUD.
- Validación 100% server-side. Rate-limit de mensajes. Sanea el chat (XSS en burbujas).

> Recuerda: **servidor autoritativo, lógica en rejilla 2D, render isométrico, A* en el
> servidor, arte pixel propio.** Empieza por la Fase 1–2 hasta tener avatares moviéndose en
> red, y a partir de ahí itera.
