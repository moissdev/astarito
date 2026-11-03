"""Generador de mapas.

Parte 1 (cuevas y lajas): se prueba `_generate_once` directamente; cuando exista
`generate_map` (parte 3) las pruebas de mapas completos pasan a usarlo.
"""

import random

import pytest

from backend.agent.config import CAVES, HEIGHT, SLABS, WIDTH, StructureSpec
from backend.agent.generator import Grid, _generate_once, _place_structures
from backend.agent.materials import Material

SEEDS = range(50)


def grid_for(seed: int) -> Grid:
    return _generate_once(random.Random(seed))


def layers_with(grid: Grid, material: Material) -> set[int]:
    """Capas (base 1) donde aparece el material."""
    return {y + 1 for y, row in enumerate(grid) if material in row}


def count_in_layers(grid: Grid, material: Material, spec: StructureSpec) -> int:
    first, last = spec.layers
    return sum(row.count(material) for row in grid[first - 1 : last])


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
    assert layers_with(grid, Material.EMPTY) <= set(range(CAVES.layers[0], CAVES.layers[1] + 1))
    assert layers_with(grid, Material.STONE) <= set(range(SLABS.layers[0], SLABS.layers[1] + 1))


@pytest.mark.parametrize(("spec", "material"), [(CAVES, Material.EMPTY), (SLABS, Material.STONE)])
def test_coverage_is_reached_without_large_overshoot(spec: StructureSpec, material: Material) -> None:
    rows = spec.layers[1] - spec.layers[0] + 1
    target = spec.coverage * WIDTH * rows
    biggest = spec.width[1] * spec.height[1]          # lo más que agrega un rectángulo
    for seed in SEEDS:
        placed = count_in_layers(grid_for(seed), material, spec)
        assert target <= placed < target + biggest


@pytest.mark.parametrize("seed", SEEDS)
def test_slabs_do_not_overwrite_caves(seed: int) -> None:
    # Mismo generador, solo con cuevas: el aire debe quedar igual tras las lajas.
    rng = random.Random(seed)
    caves_only = [[Material.EARTH] * WIDTH for _ in range(HEIGHT)]
    _place_structures(caves_only, rng, CAVES, Material.EMPTY)
    full = grid_for(seed)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            assert (caves_only[y][x] is Material.EMPTY) == (full[y][x] is Material.EMPTY)


def test_only_earth_empty_and_stone_so_far() -> None:
    for seed in SEEDS:
        assert {m for row in grid_for(seed) for m in row} <= {
            Material.EARTH,
            Material.EMPTY,
            Material.STONE,
        }
