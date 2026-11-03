"""Utilidades compartidas por las pruebas: mapas aleatorios y búsqueda de referencia.

Los mapas aleatorios no siguen las reglas del generador (eso se prueba aparte);
mezclan todos los materiales para ejercitar las reglas en muchos casos.
"""

import heapq
import math
import random

from backend.agent.grid import GameMap
from backend.agent.rules import blocked_cells, goal_cells, successors

# Material y su peso relativo en los mapas aleatorios. La mezcla por defecto
# tiene mucha lava para producir muchas casillas sin ruta.
DEFAULT_WEIGHTS = {"E": 55, "S": 20, "A": 12, "T": 6, "L": 7}
# Mezcla con poca lava: en 25 × 75 casi todas las columnas tienen ruta y los
# costos quedan alrededor de 100, útil para probar la poda por batería.
SEARCH_WEIGHTS = {"E": 62, "S": 22, "A": 8, "T": 4, "L": 2}


def random_map(
    seed: int,
    width: int = 9,
    height: int = 12,
    weights: dict[str, int] = DEFAULT_WEIGHTS,
) -> GameMap:
    """Mapa aleatorio con la capa 1 de tierra y una veta en "+" cerca del fondo."""
    rng = random.Random(seed)
    symbols, probs = zip(*weights.items())
    rows = [["E"] * width]
    for _ in range(height - 1):
        rows.append(rng.choices(symbols, probs, k=width))
    cx, cy = rng.randint(1, width - 2), rng.randint(height - 3, height - 2)
    for x, y in ((cx, cy), (cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
        rows[y][x] = "G"
    return GameMap.from_rows(("".join(row) for row in rows), seed=seed)


def forward_cost(game_map: GameMap, start: tuple[int, int]) -> float:
    """Costo mínimo real desde `start` con un Dijkstra hacia adelante.
    Implementación independiente de heuristic.py, usada como referencia."""
    blocked = blocked_cells(game_map)
    goals = goal_cells(game_map, blocked)
    best = {start: 0}
    frontier = [(0, start)]
    while frontier:
        cost, cell = heapq.heappop(frontier)
        if cell in goals:
            return cost
        if cost > best[cell]:
            continue
        for nxt, step in successors(game_map, blocked, cell):
            if cost + step < best.get(nxt, math.inf):
                best[nxt] = cost + step
                heapq.heappush(frontier, (cost + step, nxt))
    return math.inf
