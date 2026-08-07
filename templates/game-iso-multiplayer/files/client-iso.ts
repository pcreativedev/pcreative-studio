// Matemática isométrica (proyección dimétrica 2:1, estilo Habbo).
// Baldosa lógica (tx, ty) ↔ pantalla (px, py). El origen (0,0) está arriba.
export const TILE_W = 64;
export const TILE_H = 32;

/** Baldosa (tx,ty) → punto de pantalla (centro de la baldosa). */
export function tileToScreen(tx: number, ty: number) {
  return {
    x: (tx - ty) * (TILE_W / 2),
    y: (tx + ty) * (TILE_H / 2),
  };
}

/** Punto de pantalla → baldosa (para clicks). Redondea a la baldosa pisada. */
export function screenToTile(px: number, py: number) {
  const a = px / (TILE_W / 2);
  const b = py / (TILE_H / 2);
  return {
    tx: Math.round((a + b) / 2),
    ty: Math.round((b - a) / 2),
  };
}

/** Profundidad para z-ordering: cuanto mayor (tx+ty), más "delante". */
export function depth(tx: number, ty: number) {
  return tx + ty;
}

/** Dirección 0..7 (N, NE, E, SE, S, SW, W, NW) entre dos baldosas adyacentes. */
export function dirBetween(fromX: number, fromY: number, toX: number, toY: number) {
  const dx = Math.sign(toX - fromX);
  const dy = Math.sign(toY - fromY);
  const table: Record<string, number> = {
    "0,-1": 0, "1,-1": 1, "1,0": 2, "1,1": 3,
    "0,1": 4, "-1,1": 5, "-1,0": 6, "-1,-1": 7,
  };
  return table[`${dx},${dy}`] ?? 4;
}
