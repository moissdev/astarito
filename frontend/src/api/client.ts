// Cliente de la API. Rutas relativas: en producción la API y el frontend
// comparten dominio, y en desarrollo Vite reenvía /api a uvicorn.
import type { MapResponse, SolveRequest, SolveResponse } from "./types";

/** Error de la API con el código HTTP y el mensaje que devolvió FastAPI. */
export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    throw new ApiError(response.status, await errorMessage(response));
  }
  return (await response.json()) as T;
}

/** Extrae `detail` de una respuesta de error de FastAPI (texto en 400, lista en 422). */
async function errorMessage(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();
    if (body && typeof body === "object" && "detail" in body) {
      const { detail } = body as { detail: unknown };
      if (typeof detail === "string") return detail;
      if (Array.isArray(detail)) {
        return detail.map((item) => (item as { msg?: string }).msg ?? "").join("; ");
      }
    }
  } catch {
    // El cuerpo no era JSON; se usa el texto de estado.
  }
  return `${response.status} ${response.statusText}`;
}

/** Sin semilla, el servidor elige una al azar y la devuelve en la respuesta. */
export function fetchMap(seed?: number): Promise<MapResponse> {
  const query = seed === undefined ? "" : `?seed=${seed}`;
  return request<MapResponse>(`/api/map${query}`);
}

export function solve(seed: number, startX: number): Promise<SolveResponse> {
  const body: SolveRequest = { seed, start_x: startX };
  return request<SolveResponse>("/api/solve", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
