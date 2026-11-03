"""Generación del mapa por estructuras a partir de una semilla.

Durante la generación el mapa es una lista mutable `grid[y][x]`; al final se
congela en un `GameMap`. Toda la aleatoriedad sale de un único
`random.Random(seed)`, por lo que la misma semilla produce el mismo mapa.
"""

import math
import random

from .config import (
    CAVES,
    GOLD_CENTER_COLUMNS,
    GOLD_CENTER_LAYERS,
    HEIGHT,
    LAKES,
    SLABS,
    STALAGMITE_LAYERS,
    STALAGMITE_PROB,
    WIDTH,
    StructureSpec,
)
from .grid import Cell, GameMap
from .heuristic import cost_to_go_table
from .materials import Material

Grid = list[list[Material]]

# Tope de rectángulos por estructura: evita un ciclo infinito si las capas se
# quedaran sin tierra (o sin huecos válidos) antes de alcanzar la cobertura.
_MAX_PLACEMENTS = 10_000

# Materiales sobre los que puede asentarse un lago de lava.
_LAKE_GROUND = (Material.EARTH, Material.STONE)


class MapGenerationError(Exception):
    """Se agotaron los intentos sin obtener un mapa con ruta técnica."""


def generate_map(seed: int, max_attempts: int = 50) -> GameMap:
    """Genera mapas con un mismo generador sembrado hasta obtener uno con ruta
    técnica al oro. Es determinista: la misma semilla produce el mismo mapa.
    Lanza MapGenerationError si se agotan los intentos."""
    rng = random.Random(seed)
    for attempt in range(1, max_attempts + 1):
        grid, gold = _generate_once(rng)
        game_map = GameMap(
            seed=seed,
            attempts=attempt,
            cells=tuple(tuple(row) for row in grid),
            gold=gold,
        )
        if has_technical_route(game_map):
            return game_map
    raise MapGenerationError(f"semilla {seed}: sin ruta técnica tras {max_attempts} intentos")


def has_technical_route(game_map: GameMap) -> bool:
    """Verdadero si alguna casilla de la capa 1 tiene costo finito en la tabla exacta.
    Ignora la batería: solo importa que el oro sea alcanzable."""
    exact = cost_to_go_table(game_map, relaxed=False)
    return any(cost != math.inf for cost in exact[0])


def _generate_once(rng: random.Random) -> tuple[Grid, frozenset[Cell]]:
    """Un intento de generación (pasos 1 a 6 de la sección 5).
    El orden de los pasos fija el orden en que se consume `rng`."""
    grid = [[Material.EARTH] * WIDTH for _ in range(HEIGHT)]
    _place_structures(grid, rng, CAVES, Material.EMPTY)
    _place_structures(grid, rng, SLABS, Material.STONE)
    _place_stalagmites(grid, rng)
    _place_lava_lakes(grid, rng)
    gold = _place_gold(grid, rng)
    return grid, gold


def _place_structures(grid: Grid, rng: random.Random, spec: StructureSpec, material: Material) -> None:
    """Cuevas y lajas: rectángulos sobre casillas de tierra hasta la cobertura objetivo.
    Un rectángulo que se solapa con otro material solo se aplica sobre la tierra,
    por lo que las formas pueden resultar irregulares."""
    first, last = spec.layers[0] - 1, spec.layers[1] - 1      # filas base 0
    target = spec.coverage * WIDTH * (last - first + 1)
    placed = 0
    for _ in range(_MAX_PLACEMENTS):
        if placed >= target:
            break
        width = rng.randint(*spec.width)
        height = rng.randint(*spec.height)
        # El rectángulo completo queda dentro del mapa y de las capas permitidas.
        left = rng.randint(0, WIDTH - width)
        top = rng.randint(first, last - height + 1)
        for y in range(top, top + height):
            for x in range(left, left + width):
                if grid[y][x] is Material.EARTH:
                    grid[y][x] = material
                    placed += 1


def _place_stalagmites(grid: Grid, rng: random.Random) -> None:
    """Convierte casillas de piso de cueva (vacías con una casilla no vacía debajo)."""
    first, last = STALAGMITE_LAYERS[0] - 1, STALAGMITE_LAYERS[1] - 1
    # Primero se identifican todos los pisos y después se convierten: si se
    # convirtiera sobre la marcha, el aire encima de una estalagmita nueva
    # parecería piso y se apilarían.
    floor = [
        (x, y)
        for y in range(first, last + 1)
        for x in range(WIDTH)
        if grid[y][x] is Material.EMPTY and grid[y + 1][x] is not Material.EMPTY
    ]
    for x, y in floor:
        if rng.random() < STALAGMITE_PROB:
            grid[y][x] = Material.STALAGMITE


def _place_lava_lakes(grid: Grid, rng: random.Random) -> None:
    """Rectángulos cuya huella completa es tierra o piedra.
    A diferencia de cuevas y lajas, un lago no se recorta: si alguna casilla de
    su huella no es tierra ni piedra, se descarta completo y se elige otro."""
    first, last = LAKES.layers[0] - 1, LAKES.layers[1] - 1
    target = LAKES.coverage * WIDTH * (last - first + 1)
    placed = 0
    for _ in range(_MAX_PLACEMENTS):
        if placed >= target:
            break
        width = rng.randint(*LAKES.width)
        height = rng.randint(*LAKES.height)
        left = rng.randint(0, WIDTH - width)
        top = rng.randint(first, last - height + 1)
        footprint = [(x, y) for y in range(top, top + height) for x in range(left, left + width)]
        if all(grid[y][x] in _LAKE_GROUND for x, y in footprint):
            for x, y in footprint:
                grid[y][x] = Material.LAVA
            placed += len(footprint)


def _place_gold(grid: Grid, rng: random.Random) -> frozenset[Cell]:
    """Elige el centro de la veta y convierte en oro las 5 casillas del "+".
    El oro sobrescribe cualquier material previo."""
    cx = rng.randint(GOLD_CENTER_COLUMNS[0] - 1, GOLD_CENTER_COLUMNS[1] - 1)
    cy = rng.randint(GOLD_CENTER_LAYERS[0] - 1, GOLD_CENTER_LAYERS[1] - 1)
    gold = frozenset({(cx, cy), (cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)})
    for x, y in gold:
        grid[y][x] = Material.GOLD
    return gold
