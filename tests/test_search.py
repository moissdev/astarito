"""A*: optimalidad frente al Dijkstra exacto, poda por batería y validez de la traza.

Se usan mapas aleatorios de prueba de 25 × 75 con poca lava (costos alrededor
de 100) y mapas del generador real.
"""

import math

import pytest

from backend.agent.generator import generate_map
from backend.agent.grid import GameMap
from backend.agent.heuristic import cost_to_go_table
from backend.agent.rules import blocked_cells, goal_cells, successors
from backend.agent.search import SearchResult, a_star

from .maps import SEARCH_WEIGHTS, random_map

SEEDS = range(8)
WIDTH, HEIGHT = 25, 75


def maps() -> list[GameMap]:
    random_maps = [random_map(seed, WIDTH, HEIGHT, SEARCH_WEIGHTS) for seed in SEEDS]
    return random_maps + [generate_map(seed) for seed in range(100, 106)]


def map_id(game_map: GameMap) -> str:
    kind = "gen" if game_map.seed >= 100 else "rand"
    return f"{kind}{game_map.seed}"


def assert_valid_path(game_map: GameMap, start_x: int, result: SearchResult) -> None:
    """Empieza en la capa 1, cada paso es un sucesor, termina en meta y suma el costo."""
    blocked = blocked_cells(game_map)
    path = result.path
    assert path[0] == (start_x, 0)
    assert path[-1] in goal_cells(game_map, blocked)
    total = 0
    for cell, nxt in zip(path, path[1:]):
        steps = dict(successors(game_map, blocked, cell))
        assert nxt in steps
        total += steps[nxt]
    assert total == result.cost


# --- Optimalidad -----------------------------------------------------------

@pytest.mark.parametrize("game_map", maps(), ids=map_id)
def test_a_star_matches_exact_dijkstra_on_all_columns(game_map: GameMap) -> None:
    exact = cost_to_go_table(game_map, relaxed=False)
    for start_x in range(WIDTH):
        result = a_star(game_map, start_x, battery=None)
        expected = exact[0][start_x]
        if expected == math.inf:
            assert not result.found and result.cost is None and result.path == ()
        else:
            assert result.found and result.cost == expected
            assert_valid_path(game_map, start_x, result)


@pytest.mark.parametrize("game_map", maps(), ids=map_id)
def test_battery_boundary(game_map: GameMap) -> None:
    # Con batería igual al costo óptimo hay ruta (llegar a 0 % cuenta);
    # con una unidad menos no la hay.
    exact = cost_to_go_table(game_map, relaxed=False)
    for start_x in range(WIDTH):
        cost = exact[0][start_x]
        if cost == math.inf:
            continue
        exact_fit = a_star(game_map, start_x, battery=int(cost))
        assert exact_fit.found and exact_fit.cost == cost
        assert_valid_path(game_map, start_x, exact_fit)
        if cost > 0:
            assert not a_star(game_map, start_x, battery=int(cost) - 1).found


def test_profitable_iff_cost_within_default_battery() -> None:
    verdicts = set()
    for game_map in maps():
        exact = cost_to_go_table(game_map, relaxed=False)
        for start_x in range(WIDTH):
            profitable = exact[0][start_x] <= 100
            assert a_star(game_map, start_x).found == profitable
            verdicts.add(profitable)
    assert verdicts == {True, False}, "los mapas deben cubrir ambos veredictos"


def test_ucs_finds_same_cost_and_expands_more() -> None:
    a_star_total = ucs_total = 0
    for game_map in maps():
        for start_x in range(WIDTH):
            informed = a_star(game_map, start_x, battery=None)
            uniform = a_star(game_map, start_x, battery=None, use_heuristic=False)
            assert informed.cost == uniform.cost
            a_star_total += len(informed.expansions)
            ucs_total += len(uniform.expansions)
    assert a_star_total < ucs_total


# --- Traza -----------------------------------------------------------------

@pytest.mark.parametrize("game_map", maps(), ids=map_id)
def test_trace_invariants(game_map: GameMap) -> None:
    for start_x in range(WIDTH):
        result = a_star(game_map, start_x, battery=None)
        cells = [(e.x, e.y) for e in result.expansions]
        assert len(cells) == len(set(cells)), "ningún estado se expande dos veces"
        fs = [e.f for e in result.expansions]
        assert fs == sorted(fs), "f no decrece con una heurística consistente"
        assert all(e.f == e.g + e.h for e in result.expansions)
        if result.found:
            last = result.expansions[-1]
            assert (last.x, last.y) == result.path[-1] and last.g == result.cost


def test_search_is_deterministic() -> None:
    game_map = random_map(3, WIDTH, HEIGHT, SEARCH_WEIGHTS)
    assert a_star(game_map, 12) == a_star(game_map, 12)


# --- Casos hechos a mano ---------------------------------------------------

# Bloque de piedra sobre el oro: conviene rodearlo aunque la ruta sea más larga.
DETOUR_MAP = [
    "EEEEE",
    "ESSSE",
    "ESSSE",
    "ESSSE",
    "EEGEE",
]


def test_prefers_cheaper_detour() -> None:
    game_map = GameMap.from_rows(DETOUR_MAP)
    result = a_star(game_map, 2)
    # Derecho hacia abajo: 3 + 3 + 3 = 9 (la meta es la piedra sobre el oro).
    # Rodeando por un costado: 7 casillas de tierra.
    assert result.cost == 7
    assert_valid_path(game_map, 2, result)


def test_start_without_enough_battery_expands_nothing() -> None:
    result = a_star(GameMap.from_rows(DETOUR_MAP), 2, battery=6)
    assert not result.found and result.expansions == ()
