// Tipos del contrato de la API (backend/schemas.py). Coordenadas (x, y) en
// base 0 con origen arriba a la izquierda; la capa de una casilla es y + 1.

/** Un carácter por material, como en `Material` del backend. */
export type MaterialSymbol = "E" | "S" | "A" | "T" | "L" | "G";

/** Materiales que se pueden minar (los que aparecen en `composition`). */
export type MinedMaterial = "earth" | "stone" | "empty" | "stalagmite";

export type Cell = [x: number, y: number];

export interface MapResponse {
  seed: number;
  width: number;
  height: number;
  /** Una cadena por fila, un carácter por material. */
  grid: string[];
  /** "1" bloqueada, "0" libre; misma forma que `grid`. */
  blocked: string[];
  gold: Cell[];
}

export interface SolveRequest {
  seed: number;
  start_x: number;
}

export interface Expansion {
  x: number;
  y: number;
  g: number;
  h: number;
  f: number;
  /** Casillas que este paso metió a la frontera (nuevas o con mejor g). */
  pushed: Cell[];
}

export interface SolveResponse {
  profitable: boolean;
  cost: number | null;
  battery_left: number | null;
  /** Costo mínimo real sin límite de batería; null si no hay ruta técnica. */
  min_cost: number | null;
  path: Cell[];
  expansions: Expansion[];
  expanded: number;
  composition: Record<MinedMaterial, number>;
}
