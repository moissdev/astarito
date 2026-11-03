"""Generador de mapas.

Partes 1 y 2 (cuevas, lajas, estalagmitas y lava): se prueba `_generate_once`
directamente; cuando exista `generate_map` (parte 3) las pruebas de mapas
completos pasan a usarlo.
"""

import copy
import random

import pytest

from backend.agent.config import (
    CAVES,
    HEIGHT,
    LAKES,
    SLABS,
    STALAGMITE_LAYERS,
    WIDTH,
    StructureSpec,
)
from backend.agent.generator import (
    Grid,
    _generate_once,
    _place_lava_lakes,
    _place_stalagmites,
    _place_structures,
)
from backend.agent.materials import Material

SEEDS = range(50)


def grid_for(seed: int) -> Grid:
    return _generate_once(random.Random(seed))


def stages(seed: int) -> dict[str, Grid]:
    """Repite los pasos de `_generate_once` y guarda una copia tras cada uno."""
    rng = random.Random(seed)
    grid = [[Material.EARTH] * WIDTH for _ in range(HEIGHT)]
    snapshots: dict[str, Grid] = {}
    _place_structures(grid, rng, CAVES, Material.EMPTY)
    snapshots["caves"] = copy.deepcopy(grid)
    _place_structures(grid, rng, SLABS, Material.STONE)
    snapshots["slabs"] = copy.deepcopy(grid)
    _place_stalagmites(grid, rng)
    snapshots["stalagmites"] = copy.deepcopy(grid)
    _place_lava_lakes(grid, rng)
    snapshots["lava"] = grid
    return snapshots


def cells_of(grid: Grid, material: Material) -> set[tuple[int, int]]:
    return {(x, y) for y, row in enumerate(grid) for x, m in enumerate(row) if m is material}


def layers_with(grid: Grid, material: Material) -> set[int]:
    """Capas (base 1) donde aparece el material."""
    return {y + 1 for _, y in cells_of(grid, material)}


def layer_range(layers: tuple[int, int]) -> set[int]:
    return set(range(layers[0], layers[1] + 1))


def count_in_layers(grid: Grid, material: Material, spec: StructureSpec) -> int:
    first, last = spec.layers
    return sum(row.count(material) for row in grid[first - 1 : last])


# --- Generales -------------------------------------------------------------

def test_stages_helper_matches_generator() -> None:
    # Si _generate_once cambia de orden, este ayudante de pruebas debe cambiar también.
    for seed in range(5):
        assert stages(seed)["lava"] == grid_for(seed)


def test_same_seed_same_grid() -> None:
    assert grid_for(42) == grid_for(42)
    assert grid_for(42) != grid_for(43)


def test_dimensions() -> None:
    grid = grid_for(0)
    assert len(grid) == HEIGHT and all(len(row) == WIDTH for row in grid)


@pytest.mark.parametrize("seed", SEEDS)
def test_layer_one_is_all_earth(seed: int) -> None:
    assert all(m is Material.EARTH for m in grid_for(seed)[0])


@pytest.mark.parametrize("seed", SEEDS)
def test_materials_stay_in_their_layers(seed: int) -> None:
    grid = grid_for(seed)
    assert layers_with(grid, Material.EMPTY) <= layer_range(CAVES.layers)
    assert layers_with(grid, Material.STONE) <= layer_range(SLABS.layers)
    assert layers_with(grid, Material.STALAGMITE) <= layer_range(STALAGMITE_LAYERS)
    assert layers_with(grid, Material.LAVA) <= layer_range(LAKES.layers)


# --- Cuevas y lajas --------------------------------------------------------

@pytest.mark.parametrize(
    ("spec", "material", "stage"),
    [(CAVES, Material.EMPTY, "caves"), (SLABS, Material.STONE, "slabs")],
)
def test_coverage_is_reached_without_large_overshoot(
    spec: StructureSpec, material: Material, stage: str
) -> None:
    # Se mide justo después del paso, antes de que estalagmitas o lava conviertan casillas.
    target = spec.coverage * WIDTH * (spec.layers[1] - spec.layers[0] + 1)
    biggest = spec.width[1] * spec.height[1]          # lo más que agrega un rectángulo
    for seed in SEEDS:
        placed = count_in_layers(stages(seed)[stage], material, spec)
        assert target <= placed < target + biggest


@pytest.mark.parametrize("seed", SEEDS)
def test_slabs_do_not_overwrite_caves(seed: int) -> None:
    snapshots = stages(seed)
    assert cells_of(snapshots["caves"], Material.EMPTY) == cells_of(snapshots["slabs"], Material.EMPTY)


# --- Estalagmitas ----------------------------------------------------------

@pytest.mark.parametrize("seed", SEEDS)
def test_stalagmites_only_on_cave_floor(seed: int) -> None:
    snapshots = stages(seed)
    before = snapshots["slabs"]
    for x, y in cells_of(snapshots["stalagmites"], Material.STALAGMITE):
        # Era aire de cueva con algo sólido debajo (nunca otra estalagmita).
        assert before[y][x] is Material.EMPTY
        assert before[y + 1][x] is not Material.EMPTY


def test_stalagmite_rate_is_close_to_target() -> None:
    first, last = STALAGMITE_LAYERS
    floors = converted = 0
    for seed in SEEDS:
        snapshots = stages(seed)
        before, after = snapshots["slabs"], snapshots["stalagmites"]
        for y in range(first - 1, last):
            for x in range(WIDTH):
                if before[y][x] is Material.EMPTY and before[y + 1][x] is not Material.EMPTY:
                    floors += 1
                    converted += after[y][x] is Material.STALAGMITE
    assert 0.30 < converted / floors < 0.40


# --- Lava ------------------------------------------------------------------

@pytest.mark.parametrize("seed", SEEDS)
def test_lava_only_over_earth_or_stone(seed: int) -> None:
    snapshots = stages(seed)
    before = snapshots["stalagmites"]
    for x, y in cells_of(snapshots["lava"], Material.LAVA):
        assert before[y][x] in (Material.EARTH, Material.STONE)


@pytest.mark.parametrize("seed", SEEDS)
def test_lava_does_not_touch_other_materials(seed: int) -> None:
    snapshots = stages(seed)
    before, after = snapshots["stalagmites"], snapshots["lava"]
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if after[y][x] is not Material.LAVA:
                assert after[y][x] is before[y][x]


def test_lava_coverage_is_reached() -> None:
    target = LAKES.coverage * WIDTH * (LAKES.layers[1] - LAKES.layers[0] + 1)
    biggest = LAKES.width[1] * LAKES.height[1]
    for seed in SEEDS:
        placed = count_in_layers(grid_for(seed), Material.LAVA, LAKES)
        assert target <= placed < target + biggest
