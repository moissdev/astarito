"""Capa de API: traduce peticiones HTTP a llamadas al núcleo del agente.

La API no guarda estado: cada petición regenera el mapa a partir de la semilla.
La caché de `_map_for` solo evita repetir trabajo; no cambia ninguna respuesta.
"""

import math
import random
from functools import lru_cache
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query

from .agent.config import BATTERY
from .agent.generator import MapGenerationError, generate_map
from .agent.grid import GameMap
from .agent.heuristic import cost_to_go_table
from .agent.metrics import summarize
from .agent.rules import blocked_cells
from .agent.search import a_star
from .schemas import MAX_SEED, ExpansionOut, MapResponse, SolveRequest, SolveResponse

app = FastAPI(title="Astarito")


@lru_cache(maxsize=32)
def _map_for(seed: int) -> GameMap:
    """Generación con caché en memoria; la API sigue siendo sin estado."""
    return generate_map(seed)


def _load_map(seed: int) -> GameMap:
    """Igual que `_map_for`, pero traduce el agotamiento de intentos a un 400."""
    try:
        return _map_for(seed)
    except MapGenerationError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/api/health")
def health() -> dict[str, str]:
    """Confirma que la función de Python responde."""
    return {"status": "ok"}


@app.get("/api/map", response_model=MapResponse)
def get_map(seed: Annotated[int | None, Query(ge=0, le=MAX_SEED)] = None) -> MapResponse:
    """Sin semilla, el servidor elige una al azar y la devuelve."""
    if seed is None:
        seed = random.randint(0, MAX_SEED)
    game_map = _load_map(seed)
    blocked = blocked_cells(game_map)
    return MapResponse(
        seed=seed,
        width=game_map.width,
        height=game_map.height,
        grid=game_map.to_rows(),
        blocked=["".join("1" if cell else "0" for cell in row) for row in blocked],
        gold=sorted(game_map.gold),
    )


@app.post("/api/solve", response_model=SolveResponse)
def solve(request: SolveRequest) -> SolveResponse:
    """Regenera el mapa, ejecuta A* con w = 1 y devuelve ruta, veredicto y traza.
    min_cost se obtiene de la tabla exacta (relaxed=False) para informar el costo
    real cuando la ruta no es rentable."""
    game_map = _load_map(request.seed)
    result = a_star(game_map, request.start_x, battery=BATTERY)
    summary = summarize(game_map, result, BATTERY)
    exact = cost_to_go_table(game_map, relaxed=False)[0][request.start_x]
    return SolveResponse(
        profitable=summary.profitable,
        cost=summary.cost,
        battery_left=summary.battery_left,
        min_cost=None if exact == math.inf else int(exact),
        path=list(result.path),
        expansions=[
            ExpansionOut(x=e.x, y=e.y, g=e.g, h=e.h, f=e.f) for e in result.expansions
        ],
        expanded=summary.expanded,
        # "earth", "stone", "empty", "stalagmite", como en el contrato de la API.
        composition={material.name.lower(): n for material, n in summary.composition.items()},
    )
