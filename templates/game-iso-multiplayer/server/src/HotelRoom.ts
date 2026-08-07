// Sala AUTORITATIVA (una Room = una sala de Habbo). El cliente manda intención
// ("muévete a X,Y"); aquí se valida, se calcula A* y se avanza al avatar paso a
// paso replicando el estado. NUNCA confíes en la posición del cliente.
import { Room, Client } from "@colyseus/core";
import EasyStar from "easystarjs";
import { HotelState, Player } from "./state.js";

function dirBetween(fx: number, fy: number, tx: number, ty: number) {
  const dx = Math.sign(tx - fx), dy = Math.sign(ty - fy);
  const t: Record<string, number> = {
    "0,-1": 0, "1,-1": 1, "1,0": 2, "1,1": 3,
    "0,1": 4, "-1,1": 5, "-1,0": 6, "-1,-1": 7,
  };
  return t[`${dx},${dy}`] ?? 4;
}

export class HotelRoom extends Room<HotelState> {
  maxClients = 50;
  private grid: number[][] = [];
  private easystar = new EasyStar.js();
  private paths = new Map<string, { x: number; y: number }[]>();
  private tick = 0;

  onCreate() {
    this.setState(new HotelState());
    const W = this.state.width, H = this.state.height;
    // 0 = transitable, 1 = bloqueado (paredes/furni sólido/otros avatares).
    this.grid = Array.from({ length: H }, () => Array.from({ length: W }, () => 0));
    this.easystar.setGrid(this.grid);
    this.easystar.setAcceptableTiles([0]);
    this.easystar.enableDiagonals();
    this.easystar.enableSync();

    this.onMessage("move", (client, msg: { tx: number; ty: number }) => this.requestMove(client, msg));
    this.onMessage("chat", (client, msg: { text: string }) => {
      const text = String(msg?.text ?? "").trim().slice(0, 200);
      if (text) this.broadcast("chat", { id: client.sessionId, text }); // TODO: rate-limit + saneo
    });

    // Bucle de simulación a 20 Hz; el movimiento avanza cada 4 ticks (~5 pasos/s).
    this.setSimulationInterval(() => this.update(), 1000 / 20);
  }

  onJoin(client: Client, opts: any) {
    const p = new Player();
    p.name = String(opts?.name ?? "Guest").slice(0, 20);
    p.look = String(opts?.look ?? "default").slice(0, 64);
    p.tx = 2; p.ty = 2;
    this.state.players.set(client.sessionId, p);
  }

  onLeave(client: Client) {
    this.state.players.delete(client.sessionId);
    this.paths.delete(client.sessionId);
  }

  private requestMove(client: Client, msg: { tx: number; ty: number }) {
    const p = this.state.players.get(client.sessionId);
    if (!p) return;
    const tx = msg?.tx | 0, ty = msg?.ty | 0;
    if (tx < 0 || ty < 0 || tx >= this.state.width || ty >= this.state.height) return;
    if (this.grid[ty][tx] !== 0) return; // baldosa bloqueada
    this.easystar.findPath(p.tx, p.ty, tx, ty, (path) => {
      if (path && path.length > 1) this.paths.set(client.sessionId, path.slice(1));
    });
    this.easystar.calculate();
  }

  private update() {
    if (++this.tick % 4 !== 0) return;
    for (const [id, p] of this.state.players) {
      const path = this.paths.get(id);
      if (path && path.length) {
        const next = path.shift()!;
        p.dir = dirBetween(p.tx, p.ty, next.x, next.y);
        p.tx = next.x; p.ty = next.y;
        p.walking = path.length > 0;
      } else if (p.walking) {
        p.walking = false;
      }
    }
  }
}
