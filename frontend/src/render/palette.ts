// Colores del mapa. Los materiales usan tonos de tierra y el oro y la lava
// resaltan; las capas de la búsqueda (cerrados, nodo actual y ruta) usan colores
// fríos para no confundirse con ningún material.
import type { MaterialSymbol } from "../api/types";

/** Relleno de cada casilla según su material. */
export const MATERIAL_COLORS: Record<MaterialSymbol, string> = {
  E: "#8a5a32", // tierra
  S: "#6e7179", // piedra
  A: "#1d1813", // vacío (interior de cueva)
  T: "#1d1813", // estalagmita: fondo de cueva; la punta se dibuja encima
  L: "#e4531c", // lava
  G: "#f3c431", // oro
};

/** Elementos que se dibujan sobre los materiales. */
export const OVERLAY = {
  /** Punta de la estalagmita. */
  stalagmite: "#b9ab92",
  /** Brillo interior del oro. */
  goldShine: "#fff1a8",
  /** Líneas de la cuadrícula. */
  gridLine: "rgba(0, 0, 0, 0.18)",
  /** Rayado de las casillas bloqueadas. */
  blockedHatch: "rgba(0, 0, 0, 0.55)",
  /** Casillas ya expandidas (conjunto cerrado). */
  closed: "rgba(86, 204, 242, 0.5)",
  /** Contorno del nodo que se expande en el paso actual. */
  current: "#ffffff",
  /** Ruta final. */
  path: "#4ade80",
  /** Borde de la ruta, para que destaque sobre cualquier material. */
  pathOutline: "rgba(0, 0, 0, 0.6)",
  /** Casilla de inicio. */
  start: "#ffffff",
} as const;
