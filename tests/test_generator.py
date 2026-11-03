"""Generador de mapas.

Las pruebas de cada paso usan `stages`, que repite el primer intento de
`_generate_once` y guarda el mapa tras cada paso. Las propiedades de los mapas
aceptados se prueban sobre `generate_map`.
"""

import copy
import random

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
from backend.agent import generator
from backend.agent.generator import (
    Grid,
    MapGenerationError,
    _generate_once,
    _place_gold,
    _place_lava_lakes,
    _place_stalagmites,
    _place_structures,
    generate_map,
    has_technical_route,
)
from backend.agent.grid import GameMap
from backend.agent.materials import Material
from backend.agent.rules import blocked_cells

SEEDS = range(50)


def grid_for(seed: int) -> Grid:
    """Mapa del primer intento de la semilla (aceptado o no)."""
    grid, _ = _generate_once(random.Random(seed))
    return grid


def map_for(seed: int) -> GameMap:
    return generate_map(seed)


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
    snapshots["lava"] = copy.deepcopy(grid)
    _place_gold(grid, rng)
    snapshots["gold"] = grid
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
        assert stages(seed)["gold"] == grid_for(seed)


def test_same_seed_same_map() -> None:
    assert map_for(42) == map_for(42)
    assert map_for(42) != map_for(43)


def test_dimensions_and_metadata() -> None:
    game_map = map_for(0)
    assert (game_map.width, game_map.height) == (WIDTH, HEIGHT)
    assert game_map.seed == 0 and game_map.attempts >= 1


@pytest.mark.parametrize("seed", SEEDS)
def test_layer_one_is_all_earth(seed: int) -> None:
    assert all(m is Material.EARTH for m in map_for(seed).cells[0])


@pytest.mark.parametrize("seed", SEEDS)
def test_no_cell_of_layer_one_is_blocked(seed: int) -> None:
    assert not any(blocked_cells(map_for(seed))[0])


@pytest.mark.parametrize("seed", SEEDS)
def test_materials_stay_in_their_layers(seed: int) -> None:
    grid = [list(row) for row in map_for(seed).cells]
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


# --- Oro -------------------------------------------------------------------

@pytest.mark.parametrize("seed", SEEDS)
def test_gold_is_a_valid_plus(seed: int) -> None:
    game_map = map_for(seed)
    gold = game_map.gold
    assert len(gold) == 5
    # El centro es la única casilla con sus 4 vecinos de oro.
    centers = [(x, y) for x, y in gold if {(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)} <= gold]
    assert len(centers) == 1
    cx, cy = centers[0]
    assert GOLD_CENTER_COLUMNS[0] <= cx + 1 <= GOLD_CENTER_COLUMNS[1]
    assert GOLD_CENTER_LAYERS[0] <= cy + 1 <= GOLD_CENTER_LAYERS[1]


@pytest.mark.parametrize("seed", SEEDS)
def test_gold_overwrites_only_its_five_cells(seed: int) -> None:
    snapshots = stages(seed)
    before, after = snapshots["lava"], snapshots["gold"]
    changed = {(x, y) for y in range(HEIGHT) for x in range(WIDTH) if before[y][x] is not after[y][x]}
    assert changed <= cells_of(after, Material.GOLD)
    assert len(cells_of(after, Material.GOLD)) == 5


# --- Rechazo de semillas ---------------------------------------------------

@pytest.mark.parametrize("seed", SEEDS)
def test_accepted_maps_have_technical_route(seed: int) -> None:
    assert has_technical_route(map_for(seed))


def test_rejected_attempts_continue_the_same_rng() -> None:
    # Una semilla rechazada en el primer intento acepta un mapa distinto al primero.
    seed = next(s for s in range(2000) if map_for(s).attempts > 1)
    game_map = map_for(seed)
    first_try = grid_for(seed)
    assert [list(row) for row in game_map.cells] != first_try
    assert not has_technical_route(
        GameMap(
            seed=seed,
            attempts=1,
            cells=tuple(tuple(row) for row in first_try),
            gold=frozenset(cells_of(first_try, Material.GOLD)),
        )
    )


def test_rejection_rate_is_low() -> None:
    rejected = sum(map_for(seed).attempts > 1 for seed in range(500))
    assert rejected / 500 < 0.02


def test_raises_when_attempts_run_out(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(generator, "has_technical_route", lambda _: False)
    with pytest.raises(MapGenerationError):
        generate_map(0, max_attempts=3)
