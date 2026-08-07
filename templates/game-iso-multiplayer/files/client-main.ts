// Cliente del juego: PixiJS 8 renderiza la sala isométrica e interpola a los
// jugadores que llegan por Colyseus. Es un ESQUELETO de la Fase 1–2 del
// GAME-CONTEXT.md (suelo + click-to-move + multiplayer mínimo). El arte (sprites
// de avatar/furni), la animación de andar, el chat y el furni los añades tú
// siguiendo el blueprint. Funciona aunque el servidor no esté arrancado.
import { Application, Container, Graphics } from "pixi.js";
import { Client, type Room } from "colyseus.js";
import { tileToScreen, screenToTile, depth, TILE_W, TILE_H } from "./iso";

const W = 10;
const H = 10;
const COLORS = [0x6ee7b7, 0x93c5fd, 0xfca5a5, 0xfcd34d, 0xc4b5fd, 0xf9a8d4];

(async () => {
  const app = new Application();
  await app.init({ background: "#141b27", resizeTo: window, antialias: false });
  document.body.appendChild(app.canvas);

  // Mundo centrado en pantalla.
  const world = new Container();
  world.sortableChildren = true;
  app.stage.addChild(world);
  const recenter = () => { world.x = app.renderer.width / 2; world.y = app.renderer.height / 3; };
  recenter();
  window.addEventListener("resize", recenter);

  // Suelo de baldosas (diamantes).
  const floor = new Container();
  world.addChild(floor);
  const tileGfx: Graphics[] = [];
  for (let ty = 0; ty < H; ty++) {
    for (let tx = 0; tx < W; tx++) {
      const p = tileToScreen(tx, ty);
      const g = new Graphics()
        .poly([0, -TILE_H / 2, TILE_W / 2, 0, 0, TILE_H / 2, -TILE_W / 2, 0])
        .fill((tx + ty) % 2 ? 0x223047 : 0x1c2840)
        .stroke({ width: 1, color: 0x0d1422 });
      g.x = p.x; g.y = p.y;
      g.eventMode = "static";
      g.cursor = "pointer";
      g.on("pointerover", () => g.tint = 0x3b82f6);
      g.on("pointerout", () => g.tint = 0xffffff);
      g.on("pointertap", () => onTileClick(tx, ty));
      floor.addChild(g);
      tileGfx.push(g);
    }
  }

  // Avatares (placeholder = ficha de color). Sustitúyelos por sprites 8-dir.
  const avatars = new Map<string, Graphics>();
  function makeAvatar(color: number) {
    const g = new Graphics().circle(0, -16, 11).fill(color).stroke({ width: 2, color: 0x0d1422 });
    world.addChild(g);
    return g;
  }
  function placeAvatar(g: Graphics, tx: number, ty: number) {
    const p = tileToScreen(tx, ty);
    g.x = p.x; g.y = p.y;
    g.zIndex = depth(tx, ty) + 1;
  }

  // ── Red (Colyseus) — opcional: si el servidor no está, juegas el suelo solo ──
  let room: Room | null = null;
  try {
    const client = new Client(import.meta.env.VITE_SERVER_URL || "ws://localhost:2567");
    room = await client.joinOrCreate("hotel", { name: "Guest", look: "default" });

    room.state.players.onAdd((player: any, id: string) => {
      const g = makeAvatar(COLORS[avatars.size % COLORS.length]);
      avatars.set(id, g);
      placeAvatar(g, player.tx, player.ty);
      player.onChange(() => placeAvatar(g, player.tx, player.ty)); // TODO: interpolar
    });
    room.state.players.onRemove((_p: any, id: string) => {
      avatars.get(id)?.destroy(); avatars.delete(id);
    });
    console.log("[net] conectado a la sala");
  } catch (e) {
    console.warn("[net] sin servidor Colyseus (arranca `server`). Suelo en modo local.", e);
  }

  function onTileClick(tx: number, ty: number) {
    if (room) room.send("move", { tx, ty }); // el SERVIDOR valida + A* + replica
    else console.log("click baldosa", tx, ty);
  }
})();
