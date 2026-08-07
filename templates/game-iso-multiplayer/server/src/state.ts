// Estado replicado (el CONTRATO cliente↔servidor). @colyseus/schema sincroniza
// solo los diffs automáticamente. Amplíalo con furni, look del avatar, etc.
import { Schema, MapSchema, ArraySchema, type } from "@colyseus/schema";

export class Player extends Schema {
  @type("string") name = "Guest";
  @type("number") tx = 2;
  @type("number") ty = 2;
  @type("number") dir = 4;        // 0..7 (N, NE, E, SE, S, SW, W, NW)
  @type("boolean") walking = false;
  @type("string") look = "default";
}

export class Furni extends Schema {
  @type("string") kind = "";
  @type("number") tx = 0;
  @type("number") ty = 0;
  @type("number") rot = 0;
}

export class HotelState extends Schema {
  @type({ map: Player }) players = new MapSchema<Player>();
  @type([Furni]) furni = new ArraySchema<Furni>();
  @type("number") width = 10;
  @type("number") height = 10;
}
