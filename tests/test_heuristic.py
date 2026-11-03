"""Heurística relajada: exactitud del Dijkstra inverso, admisibilidad y consistencia.

Por ahora se usan mapas aleatorios de prueba; en el checkpoint 8 se agregan
mapas del generador real.
"""

import math

import pytest

from backend.agent.grid import GameMap
from backend.agent.heuristic import cost_to_go_table
from backend.agent.materials import Material
from backend.agent.rules import blocked_cells, goal_cells, successors

from .maps import forward_cost, random_map

SEEDS = range(25)


def real_states(game_map: GameMap) -> list[tuple[int, int]]:
    """Casillas donde el robot puede estar en el problema original."""
    blocked = blocked_cells(game_map)
    return [
        (x, y)
        for y in range(game_map.height)
        for x in range(game_map.width)
        if not blocked[y][x] and game_map.material(x, y) is not Material.GOLD
    ]


# Lava en (2, 1) y oro en (2, 3). La lava bloquea (3, 1) y (2, 2) en el problema real.
LAVA_MAP = [
    "EEEEE",
    "EELEE",
    "EEEEE",
    "EEGEE",
]


def test_known_values_relaxed_vs_exact() -> None:
    game_map = GameMap.from_rows(LAVA_MAP)
    h = cost_to_go_table(game_map, relaxed=True)
    exact = cost_to_go_table(game_map, relaxed=False)
    # En R se baja directo junto a la lava; en el real hay que rodearla.
    assert h[0][3] == 3
    assert exact[0][3] == 5
    assert h[1][2] == exact[1][2] == math.inf      # la lava misma


@pytest.mark.parametrize("seed", SEEDS)
def test_exact_table_matches_forward_dijkstra(seed: int) -> None:
    game_map = random_map(seed)
    exact = cost_to_go_table(game_map, relaxed=False)
    for x, y in real_states(game_map):
        assert exact[y][x] == forward_cost(game_map, (x, y))


@pytest.mark.parametrize("seed", SEEDS)
def test_h_is_zero_on_goals(seed: int) -> None:
    game_map = random_map(seed)
    h = cost_to_go_table(game_map, relaxed=True)
    for x, y in goal_cells(game_map, blocked_cells(game_map)):
        assert h[y][x] == 0


@pytest.mark.parametrize("seed", SEEDS)
def test_h_is_admissible(seed: int) -> None:
    game_map = random_map(seed)
    h = cost_to_go_table(game_map, relaxed=True)
    exact = cost_to_go_table(game_map, relaxed=False)
    for x, y in real_states(game_map):
        assert h[y][x] <= exact[y][x]


@pytest.mark.parametrize("seed", SEEDS)
def test_h_is_consistent(seed: int) -> None:
    game_map = random_map(seed)
    h = cost_to_go_table(game_map, relaxed=True)
    blocked = blocked_cells(game_map)
    for x, y in real_states(game_map):
        for (nx, ny), cost in successors(game_map, blocked, (x, y)):
            assert h[y][x] <= cost + h[ny][nx]


def test_random_maps_are_varied() -> None:
    # Protege a las pruebas anteriores de pasar en vacío: debe haber mapas con
    # ruta y casillas sin ruta, y algún caso donde h sea estrictamente menor.
    reachable = unreachable = strictly_lower = 0
    for seed in SEEDS:
        game_map = random_map(seed)
        h = cost_to_go_table(game_map, relaxed=True)
        exact = cost_to_go_table(game_map, relaxed=False)
        for x, y in real_states(game_map):
            if exact[y][x] == math.inf:
                unreachable += 1
            else:
                reachable += 1
                strictly_lower += h[y][x] < exact[y][x]
    assert reachable > 0 and unreachable > 0 and strictly_lower > 0
