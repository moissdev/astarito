// Estado de la aplicación: semilla y mapa, columna de inicio, traza y paso actual.
// Un store mínimo (sin dependencias): las vistas se suscriben y vuelven a dibujar.
import { fetchMap, solve } from "../api/client";
import type { MapResponse, SolveResponse } from "../api/types";

export type Status = "idle" | "loading-map" | "ready" | "solving" | "error";

export interface AppState {
  status: Status;
  map: MapResponse | null;
  /** Columna de inicio en la capa 1 (base 0), o null si no se ha elegido. */
  startX: number | null;
  solution: SolveResponse | null;
  /** Expansiones ya reproducidas (0 = ninguna). Lo usa la reproducción. */
  step: number;
  /** Si la reproducción avanza sola. */
  playing: boolean;
  /** Velocidad de la reproducción, en expansiones por segundo. */
  speed: number;
  error: string | null;
}

type Listener = (state: AppState) => void;

let state: AppState = {
  status: "idle",
  map: null,
  startX: null,
  solution: null,
  step: 0,
  playing: false,
  speed: 60,
  error: null,
};
const listeners = new Set<Listener>();

// Cada petición recibe un número; si al responder ya hay una más reciente, se
// descarta. Así un clic rápido en otro mapa no deja ver una respuesta vieja.
let latestRequest = 0;

export function getState(): AppState {
  return state;
}

export function subscribe(listener: Listener): () => void {
  listeners.add(listener);
  listener(state);
  return () => listeners.delete(listener);
}

function setState(patch: Partial<AppState>): void {
  state = { ...state, ...patch };
  for (const listener of listeners) listener(state);
}

function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

/** Carga un mapa; sin semilla, el servidor elige una. Reinicia inicio y traza. */
export async function loadMap(seed?: number): Promise<void> {
  const id = ++latestRequest;
  setState({ status: "loading-map", startX: null, solution: null, step: 0, playing: false, error: null });
  try {
    const map = await fetchMap(seed);
    if (id !== latestRequest) return;
    setState({ status: "ready", map });
  } catch (error) {
    if (id !== latestRequest) return;
    setState({ status: "error", error: messageOf(error) });
  }
}

/** Ejecuta A* desde la columna elegida del mapa actual. */
export async function solveFrom(startX: number): Promise<void> {
  const { map } = state;
  if (!map) return;
  const id = ++latestRequest;
  setState({ status: "solving", startX, solution: null, step: 0, playing: false, error: null });
  try {
    const solution = await solve(map.seed, startX);
    if (id !== latestRequest) return;
    setState({ status: "ready", solution });
  } catch (error) {
    if (id !== latestRequest) return;
    setState({ status: "error", error: messageOf(error) });
  }
}

/** Inicia o detiene la reproducción automática. */
export function setPlaying(playing: boolean): void {
  if (playing !== state.playing) setState({ playing });
}

/** Cambia la velocidad de la reproducción (expansiones por segundo). */
export function setSpeed(speed: number): void {
  setState({ speed });
}

/** Fija el paso de la reproducción, acotado a la longitud de la traza. */
export function setStep(step: number): void {
  const total = state.solution?.expansions.length ?? 0;
  setState({ step: Math.max(0, Math.min(step, total)) });
}
