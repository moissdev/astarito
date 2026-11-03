"""Reglas del problema: casillas bloqueadas, casillas meta y sucesores.

Las tablas de bloqueo se indexan como `blocked[y][x]`, igual que `GameMap.cells`.
"""

from collections.abc import Iterator

from .grid import Cell, GameMap
from .materials import MINING_COST, Material

# Acciones Izquierda, Derecha y Abajo. Nunca hay un desplazamiento hacia arriba.
_MOVES: tuple[Cell, ...] = ((-1, 0), (1, 0), (0, 1))

# Materiales que, si están directamente debajo, provocarían una caída.
_UNSUPPORTED = (Material.EMPTY, Material.STALAGMITE)


def blocked_cells(game_map: GameMap, relaxed: bool = False) -> list[list[bool]]:
    """Casillas bloqueadas (sección 6).
    relaxed=False: lava, vecinas de lava y casillas sobre un vacío o una estalagmita.
    relaxed=True: solo la lava (problema relajado de la heurística)."""
    blocked = [[False] * game_map.width for _ in range(game_map.height)]
    for y in range(game_map.height):
        for x in range(game_map.width):
            if game_map.material(x, y) is not Material.LAVA:
                continue
            # Regla 1: la lava misma.
            blocked[y][x] = True
            if not relaxed:
                # Regla 2: sus vecinas, para no liberarla ni caer en ella.
                for nx, ny in game_map.neighbors4(x, y):
                    blocked[ny][nx] = True
    if not relaxed:
        # Regla 3: no quedar nunca sobre un vacío o una estalagmita.
        for y in range(game_map.height - 1):
            for x in range(game_map.width):
                if game_map.material(x, y + 1) in _UNSUPPORTED:
                    blocked[y][x] = True
    return blocked


def goal_cells(game_map: GameMap, blocked: list[list[bool]]) -> frozenset[Cell]:
    """Casillas no bloqueadas adyacentes (4 vecinos) a alguna casilla de oro."""
    goals: set[Cell] = set()
    for gx, gy in game_map.gold:
        for x, y in game_map.neighbors4(gx, gy):
            # Las otras casillas del "+" son vecinas del centro, pero son oro.
            if not blocked[y][x] and game_map.material(x, y) is not Material.GOLD:
                goals.add((x, y))
    return frozenset(goals)


def successors(
    game_map: GameMap, blocked: list[list[bool]], cell: Cell
) -> Iterator[tuple[Cell, int]]:
    """Genera (destino, costo) para Izquierda, Derecha y Abajo.
    Excluye casillas fuera del mapa, bloqueadas y de oro.
    El costo es el de minar la casilla destino; la batería la controla la búsqueda."""
    x, y = cell
    for dx, dy in _MOVES:
        nx, ny = x + dx, y + dy
        if not game_map.in_bounds(nx, ny) or blocked[ny][nx]:
            continue
        material = game_map.material(nx, ny)
        if material is Material.GOLD:
            continue
        yield (nx, ny), MINING_COST[material]
