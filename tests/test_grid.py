"""Mapa inmutable: acceso, límites, vecindad y serialización."""

import dataclasses

import pytest

from backend.agent.grid import GameMap
from backend.agent.materials import Material

# Mapa de 4 × 3:
#   y=0  E E E E
#   y=1  E S A E
#   y=2  E G T L
ROWS = ["EEEE", "ESAE", "EGTL"]


@pytest.fixture
def game_map() -> GameMap:
    return GameMap.from_rows(ROWS, seed=7, attempts=2)


def test_dimensions_and_metadata(game_map: GameMap) -> None:
    assert (game_map.width, game_map.height) == (4, 3)
    assert (game_map.seed, game_map.attempts) == (7, 2)


def test_material_access_uses_x_y(game_map: GameMap) -> None:
    assert game_map.material(1, 1) is Material.STONE
    assert game_map.material(2, 1) is Material.EMPTY
    assert game_map.material(3, 2) is Material.LAVA


def test_gold_is_collected(game_map: GameMap) -> None:
    assert game_map.gold == frozenset({(1, 2)})


@pytest.mark.parametrize("cell", [(-1, 0), (0, -1), (4, 0), (0, 3)])
def test_out_of_bounds(game_map: GameMap, cell: tuple[int, int]) -> None:
    assert not game_map.in_bounds(*cell)
    with pytest.raises(IndexError):
        game_map.material(*cell)


def test_neighbors_in_the_middle(game_map: GameMap) -> None:
    assert list(game_map.neighbors4(1, 1)) == [(1, 0), (0, 1), (2, 1), (1, 2)]


def test_neighbors_in_corners(game_map: GameMap) -> None:
    assert list(game_map.neighbors4(0, 0)) == [(1, 0), (0, 1)]
    assert list(game_map.neighbors4(3, 2)) == [(3, 1), (2, 2)]


def test_rows_round_trip(game_map: GameMap) -> None:
    assert game_map.to_rows() == ROWS
    assert GameMap.from_rows(game_map.to_rows()) == GameMap.from_rows(ROWS)


def test_is_immutable(game_map: GameMap) -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        game_map.seed = 1  # type: ignore[misc]


def test_rejects_ragged_rows() -> None:
    with pytest.raises(ValueError):
        GameMap.from_rows(["EE", "E"])


def test_rejects_inconsistent_gold() -> None:
    cells = GameMap.from_rows(ROWS).cells
    with pytest.raises(ValueError):
        GameMap(seed=0, attempts=1, cells=cells, gold=frozenset())
