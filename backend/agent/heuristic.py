"""Tabla de costo restante mediante Dijkstra inverso.

En lugar de buscar desde cada casilla hacia el oro, se busca una sola vez desde
todas las metas hacia atrás: así se obtiene el costo mínimo de *todas* las
casillas en una pasada.
"""

import heapq
import math

from .grid import Cell, GameMap
from .materials import MINING_COST, Material
from .rules import blocked_cells, goal_cells

# Una arista p -> s existe si s es sucesor de p. Los predecesores de s = (x, y)
# son la casilla de la derecha (que se movió a la Izquierda), la de la izquierda
# (que se movió a la Derecha) y la de arriba (que bajó).
_PREDECESSOR_OFFSETS: tuple[Cell, ...] = ((1, 0), (-1, 0), (0, -1))


def cost_to_go_table(game_map: GameMap, relaxed: bool) -> list[list[float]]:
    """Costo mínimo de cada casilla a una casilla meta (infinito si no hay ruta).
    Dijkstra inverso: parte de las casillas meta y recorre las aristas al revés
    (los predecesores de una casilla son la de arriba, la izquierda y la derecha).
    relaxed=True  -> tabla de la heurística h(s).
    relaxed=False -> costo óptimo real, para pruebas y para verificar la ruta técnica."""
    blocked = blocked_cells(game_map, relaxed=relaxed)
    table = [[math.inf] * game_map.width for _ in range(game_map.height)]

    frontier: list[tuple[int, Cell]] = []
    for x, y in goal_cells(game_map, blocked):
        table[y][x] = 0
        heapq.heappush(frontier, (0, (x, y)))

    while frontier:
        cost, (x, y) = heapq.heappop(frontier)
        if cost > table[y][x]:
            continue                       # entrada vieja: ya se encontró algo mejor
        # Toda arista que llega a (x, y) cuesta lo mismo: minar (x, y).
        step = MINING_COST[game_map.material(x, y)]
        for dx, dy in _PREDECESSOR_OFFSETS:
            px, py = x + dx, y + dy
            if not game_map.in_bounds(px, py) or blocked[py][px]:
                continue
            if game_map.material(px, py) is Material.GOLD:
                continue                   # el robot nunca está sobre el oro
            new_cost = cost + step
            if new_cost < table[py][px]:
                table[py][px] = new_cost
                heapq.heappush(frontier, (new_cost, (px, py)))
    return table
