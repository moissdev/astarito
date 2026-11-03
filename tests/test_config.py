"""Coherencia de las constantes del problema con la propuesta."""

import pytest

from backend.agent.config import (
    CAVES,
    GOLD_CENTER_COLUMNS,
    GOLD_CENTER_LAYERS,
    HEIGHT,
    LAKES,
    SLABS,
    STALAGMITE_LAYERS,
    WIDTH,
    StructureSpec,
)
from backend.agent.materials import MINING_COST, Material


def test_mining_costs() -> None:
    assert MINING_COST == {
        Material.EARTH: 1,
        Material.STONE: 3,
        Material.EMPTY: 0,
        Material.STALAGMITE: 2,
    }


def test_lava_and_gold_have_no_cost() -> None:
    assert Material.LAVA not in MINING_COST
    assert Material.GOLD not in MINING_COST


def test_material_symbols_are_unique_chars() -> None:
    symbols = [m.value for m in Material]
    assert all(len(s) == 1 for s in symbols)
    assert len(set(symbols)) == len(symbols)


@pytest.mark.parametrize("spec", [CAVES, SLABS, LAKES])
def test_structure_ranges_are_valid(spec: StructureSpec) -> None:
    low, high = spec.layers
    assert 1 <= low <= high <= HEIGHT
    assert 1 <= spec.width[0] <= spec.width[1] <= WIDTH
    assert 1 <= spec.height[0] <= spec.height[1]
    assert 0 < spec.coverage < 1


def test_structures_leave_layer_one_as_earth() -> None:
    # La capa 1 debe ser toda tierra para que cualquier inicio sea válido.
    for low, _ in (CAVES.layers, SLABS.layers, LAKES.layers, STALAGMITE_LAYERS):
        assert low > 1


def test_gold_plus_fits_in_map() -> None:
    # Centro en base 1; el "+" ocupa una casilla más en cada dirección.
    assert GOLD_CENTER_COLUMNS[0] - 1 >= 1
    assert GOLD_CENTER_COLUMNS[1] + 1 <= WIDTH
    assert GOLD_CENTER_LAYERS[0] - 1 >= 1
    assert GOLD_CENTER_LAYERS[1] + 1 <= HEIGHT
