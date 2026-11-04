// Escala del mapa: cuántos píxeles CSS mide cada casilla y cómo se convierten
// coordenadas de píxel a casilla y viceversa.
import type { Cell } from "../api/types";

/** Tamaño mínimo de casilla; por debajo, el contenedor se desplaza. */
export const MIN_CELL = 6;
/** Tamaño máximo de casilla, para que el mapa no crezca sin límite. */
export const MAX_CELL = 20;

export interface Viewport {
  cols: number;
  rows: number;
  /** Lado de una casilla en píxeles CSS (entero, para bordes nítidos). */
  cell: number;
  /** Tamaño del mapa en píxeles CSS. */
  width: number;
  height: number;
  /** Píxeles físicos por píxel CSS (pantallas de alta densidad). */
  dpr: number;
}

/** Casilla más grande que cabe completa en el espacio disponible. */
export function fitViewport(
  cols: number,
  rows: number,
  availWidth: number,
  availHeight: number,
  dpr: number,
): Viewport {
  const fit = Math.floor(Math.min(availWidth / cols, availHeight / rows));
  const cell = Math.max(MIN_CELL, Math.min(MAX_CELL, fit));
  return { cols, rows, cell, width: cell * cols, height: cell * rows, dpr };
}

/** Esquina superior izquierda de una casilla, en píxeles CSS. */
export function cellOrigin(vp: Viewport, x: number, y: number): [left: number, top: number] {
  return [x * vp.cell, y * vp.cell];
}

/** Centro de una casilla, en píxeles CSS. */
export function cellCenter(vp: Viewport, x: number, y: number): [cx: number, cy: number] {
  return [(x + 0.5) * vp.cell, (y + 0.5) * vp.cell];
}

/** Casilla bajo un punto relativo al canvas, o null si cae fuera del mapa. */
export function cellAt(vp: Viewport, px: number, py: number): Cell | null {
  const x = Math.floor(px / vp.cell);
  const y = Math.floor(py / vp.cell);
  if (x < 0 || y < 0 || x >= vp.cols || y >= vp.rows) return null;
  return [x, y];
}
