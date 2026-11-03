"""Reglas: casillas bloqueadas, metas y sucesores, sobre mapas hechos a mano.

La prueba "ninguna casilla de la capa 1 queda bloqueada" depende de mapas
generados y se agrega en test_generator.py.
"""

from backend.agent.grid import GameMap
from backend.agent.materials import MINING_COST, Material
from backend.agent.rules import blocked_cells, goal_cells, successors


def blocked_set(rows: list[str], relaxed: bool = False) -> set[tuple[int, int]]:
    """Casillas bloqueadas como conjunto de (x, y), más fácil de comparar."""
    blocked = blocked_cells(GameMap.from_rows(rows), relaxed=relaxed)
    return {(x, y) for y, row in enumerate(blocked) for x, value in enumerate(row) if value}


# --- Casillas bloqueadas ---------------------------------------------------

LAVA_MAP = [
    "EEEEE",
    "EEEEE",
    "EELEE",
    "EEEEE",
]


def test_lava_and_its_neighbors_are_blocked() -> None:
    assert blocked_set(LAVA_MAP) == {(2, 2), (2, 1), (1, 2), (3, 2), (2, 3)}


def test_relaxed_blocks_only_lava() -> None:
    assert blocked_set(LAVA_MAP, relaxed=True) == {(2, 2)}


# Cueva de 3 × 2 con una estalagmita en el piso.
CAVE_MAP = [
    "EEEEE",
    "EEEEE",
    "EAAAE",
    "EATAE",
    "ESSSE",
]


def test_cells_over_empty_or_stalagmite_are_blocked() -> None:
    # Fila 1: techo de la cueva. Fila 2: aire sobre aire o sobre la estalagmita.
    # El piso (fila 3) queda libre porque debajo hay piedra.
    assert blocked_set(CAVE_MAP) == {(1, 1), (2, 1), (3, 1), (1, 2), (2, 2), (3, 2)}


def test_relaxed_ignores_falls() -> None:
    assert blocked_set(CAVE_MAP, relaxed=True) == set()


def test_bottom_row_is_never_blocked_by_falls() -> None:
    assert blocked_set(["EE", "AA"]) == {(0, 0), (1, 0)}


# --- Metas -----------------------------------------------------------------

GOLD_MAP = [
    "EEEEE",
    "EEGEE",
    "EGGGE",
    "EEGEE",
]


def test_goals_surround_the_plus_without_gold() -> None:
    game_map = GameMap.from_rows(GOLD_MAP)
    goals = goal_cells(game_map, blocked_cells(game_map))
    assert goals == {(2, 0), (1, 1), (3, 1), (0, 2), (4, 2), (1, 3), (3, 3)}


def test_blocked_cells_are_not_goals() -> None:
    rows = ["EELEE", *GOLD_MAP[1:]]          # lava justo encima del oro
    game_map = GameMap.from_rows(rows)
    goals = goal_cells(game_map, blocked_cells(game_map))
    assert (2, 0) not in goals
    assert goals == {(1, 1), (3, 1), (0, 2), (4, 2), (1, 3), (3, 3)}


# --- Sucesores -------------------------------------------------------------

MIXED_MAP = [
    "EEEEEEE",
    "ESEEEEE",
    "EAAAELE",
    "EATAEEE",
    "ESSSEEE",
    "EEEGEEE",
    "EEGGGEE",
    "EEEGEEE",
]


def test_successors_order_and_costs() -> None:
    game_map = GameMap.from_rows(MIXED_MAP)
    blocked = blocked_cells(game_map)
    # Izquierda (tierra), Derecha (tierra), Abajo (tierra).
    assert list(successors(game_map, blocked, (4, 0))) == [((3, 0), 1), ((5, 0), 1), ((4, 1), 1)]


def test_blocked_destinations_are_skipped() -> None:
    game_map = GameMap.from_rows(MIXED_MAP)
    blocked = blocked_cells(game_map)
    # Abajo de (1, 0) está la piedra (1, 1), pero tiene aire debajo: bloqueada.
    assert [cell for cell, _ in successors(game_map, blocked, (1, 0))] == [(0, 0), (2, 0)]
    # Desde (4, 3): aire del piso a la izquierda (costo 0); a la derecha, una vecina de lava.
    assert list(successors(game_map, blocked, (4, 3))) == [((3, 3), 0), ((4, 4), 1)]


def test_cave_floor_is_walked_and_stalagmite_mined_sideways() -> None:
    game_map = GameMap.from_rows(MIXED_MAP)
    blocked = blocked_cells(game_map)
    # Desde el piso de la cueva: tierra a la izquierda, estalagmita a la derecha, piedra abajo.
    assert list(successors(game_map, blocked, (1, 3))) == [((0, 3), 1), ((2, 3), 2), ((1, 4), 3)]


def test_map_edges_limit_successors() -> None:
    game_map = GameMap.from_rows(MIXED_MAP)
    blocked = blocked_cells(game_map)
    assert [cell for cell, _ in successors(game_map, blocked, (0, 7))] == [(1, 7)]


def test_gold_is_never_entered() -> None:
    game_map = GameMap.from_rows(MIXED_MAP)
    blocked = blocked_cells(game_map)
    # Debajo de (3, 4) está el oro (3, 5).
    assert [cell for cell, _ in successors(game_map, blocked, (3, 4))] == [(2, 4), (4, 4)]


def test_successor_invariants_on_every_cell() -> None:
    game_map = GameMap.from_rows(MIXED_MAP)
    for relaxed in (False, True):
        blocked = blocked_cells(game_map, relaxed=relaxed)
        for y in range(game_map.height):
            for x in range(game_map.width):
                for (nx, ny), cost in successors(game_map, blocked, (x, y)):
                    assert ny >= y, "ningún sucesor sube"
                    assert abs(nx - x) + abs(ny - y) == 1
                    material = game_map.material(nx, ny)
                    assert material not in (Material.GOLD, Material.LAVA)
                    assert not blocked[ny][nx]
                    assert cost == MINING_COST[material]
