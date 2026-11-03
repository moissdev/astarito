"""Métricas: veredicto, batería restante y composición de la ruta."""

import pytest

from backend.agent.config import BATTERY
from backend.agent.generator import generate_map
from backend.agent.grid import GameMap
from backend.agent.materials import MINING_COST, Material
from backend.agent.metrics import summarize
from backend.agent.search import a_star

# Desde (1, 0): baja a tierra, cruza el piso de una cueva (aire), mina de lado
# la estalagmita, baja por piedra y llega a la tierra sobre el oro.
MIXED_PATH_MAP = [
    "SESS",
    "SEAT",
    "SSSS",
    "SSSE",
    "SSSG",
]


def test_composition_on_known_path() -> None:
    game_map = GameMap.from_rows(MIXED_PATH_MAP)
    result = a_star(game_map, 1)
    summary = summarize(game_map, result, BATTERY)
    # Tierra 1 + aire 0 + estalagmita 2 + piedra 3 + tierra 1 = 7.
    assert result.path == ((1, 0), (1, 1), (2, 1), (3, 1), (3, 2), (3, 3))
    assert summary.cost == 7
    assert summary.path_length == 5
    assert summary.composition == {
        Material.EARTH: 2,
        Material.STONE: 1,
        Material.EMPTY: 1,
        Material.STALAGMITE: 1,
    }
    assert summary.profitable and summary.battery_left == BATTERY - 7
    assert summary.expanded == len(result.expansions)


def test_exact_battery_is_profitable_with_zero_left() -> None:
    game_map = GameMap.from_rows(MIXED_PATH_MAP)
    summary = summarize(game_map, a_star(game_map, 1, battery=7), 7)
    assert summary.profitable and summary.battery_left == 0


def test_no_route_summary() -> None:
    game_map = GameMap.from_rows(MIXED_PATH_MAP)
    summary = summarize(game_map, a_star(game_map, 1, battery=6), 6)
    assert not summary.profitable
    assert summary.cost is None and summary.battery_left is None
    assert summary.path_length == 0
    assert set(summary.composition.values()) == {0}


def test_route_found_without_pruning_can_exceed_battery() -> None:
    game_map = GameMap.from_rows(MIXED_PATH_MAP)
    summary = summarize(game_map, a_star(game_map, 1, battery=None), 4)
    assert not summary.profitable
    assert summary.cost == 7 and summary.battery_left == -3


@pytest.mark.parametrize("seed", range(5))
def test_composition_adds_up_on_generated_maps(seed: int) -> None:
    game_map = generate_map(seed)
    for start_x in range(game_map.width):
        result = a_star(game_map, start_x)
        summary = summarize(game_map, result, BATTERY)
        assert set(summary.composition) == set(MINING_COST)
        assert sum(summary.composition.values()) == summary.path_length
        if summary.cost is not None:
            mined = sum(MINING_COST[m] * n for m, n in summary.composition.items())
            assert mined == summary.cost
            assert summary.profitable == (summary.cost <= BATTERY)
