"""A* (Weighted A* con weight = 1) con poda por batería y traza de expansiones."""

import heapq
import itertools
import math
from dataclasses import dataclass

from .config import BATTERY
from .grid import Cell, GameMap
from .heuristic import cost_to_go_table
from .rules import blocked_cells, goal_cells, successors


@dataclass(frozen=True)
class Expansion:
    """Un estado al salir de la frontera, en el orden en que se expandió."""

    x: int
    y: int
    g: int                         # costo acumulado desde el inicio
    h: int                         # costo restante estimado
    f: int                         # g + h


@dataclass(frozen=True)
class SearchResult:
    found: bool                      # hay ruta con costo <= batería
    path: tuple[Cell, ...]           # del inicio a la casilla meta
    cost: int | None
    expansions: tuple[Expansion, ...]  # en orden de expansión


def a_star(
    game_map: GameMap,
    start_x: int,
    battery: int | None = BATTERY,
    weight: float = 1.0,
    use_heuristic: bool = True,
) -> SearchResult:
    """A* (Weighted A* con weight = 1) desde (start_x, 0).
    - Frontera: heap por f = g + weight * h; desempate por mayor g.
    - Cerrados: menor g conocido por estado.
    - Poda: se descarta todo sucesor con g + h > battery.
    - battery=None desactiva la poda y devuelve el costo mínimo real.
    - use_heuristic=False usa h = 0: búsqueda de costo uniforme (línea base)."""
    blocked = blocked_cells(game_map)
    goals = goal_cells(game_map, blocked)
    if use_heuristic:
        h_table = cost_to_go_table(game_map, relaxed=True)
    else:
        h_table = [[0] * game_map.width for _ in range(game_map.height)]

    def can_still_reach(g: int, cell: Cell) -> bool:
        """Falso si desde `cell` ya no se puede llegar a una meta con la batería.
        h = infinito significa que ni en el problema relajado hay ruta."""
        h = h_table[cell[1]][cell[0]]
        if h == math.inf:
            return False
        return battery is None or g + h <= battery

    start = (start_x, 0)
    best_g: dict[Cell, int] = {start: 0}
    parent: dict[Cell, Cell] = {}
    closed: set[Cell] = set()
    expansions: list[Expansion] = []
    # El contador rompe empates restantes por orden de inserción, así la
    # traza es siempre la misma para el mismo mapa e inicio.
    counter = itertools.count()
    frontier: list[tuple[float, int, int, Cell]] = []

    if not blocked[0][start_x] and can_still_reach(0, start):
        h0 = int(h_table[0][start_x])
        heapq.heappush(frontier, (weight * h0, 0, next(counter), start))

    while frontier:
        _, neg_g, _, cell = heapq.heappop(frontier)
        g = -neg_g
        if cell in closed or g > best_g[cell]:
            continue                       # entrada vieja de la frontera
        closed.add(cell)
        x, y = cell
        h = int(h_table[y][x])
        expansions.append(Expansion(x=x, y=y, g=g, h=h, f=g + h))

        # La prueba de meta se hace al expandir, no al generar: así la primera
        # meta que sale de la frontera es la de menor costo.
        if cell in goals:
            return SearchResult(
                found=True,
                path=_reconstruct(parent, cell),
                cost=g,
                expansions=tuple(expansions),
            )

        for nxt, step in successors(game_map, blocked, cell):
            new_g = g + step
            if nxt in closed or not can_still_reach(new_g, nxt):
                continue
            if new_g < best_g.get(nxt, math.inf):
                best_g[nxt] = new_g
                parent[nxt] = cell
                nh = h_table[nxt[1]][nxt[0]]
                # Prioridad (f, -g): menor f primero y, a igual f, mayor g.
                heapq.heappush(frontier, (new_g + weight * nh, -new_g, next(counter), nxt))

    return SearchResult(found=False, path=(), cost=None, expansions=tuple(expansions))


def _reconstruct(parent: dict[Cell, Cell], goal: Cell) -> tuple[Cell, ...]:
    """Sigue los padres desde la meta hasta el inicio y devuelve la ruta en orden."""
    path = [goal]
    while path[-1] in parent:
        path.append(parent[path[-1]])
    return tuple(reversed(path))
