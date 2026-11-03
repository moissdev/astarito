"""Generación del mapa por estructuras a partir de una semilla.

Durante la generación el mapa es una lista mutable `grid[y][x]`; al final se
congela en un `GameMap`. Toda la aleatoriedad sale de un único
`random.Random(seed)`, por lo que la misma semilla produce el mismo mapa.
"""

import random

from .config import CAVES, HEIGHT, SLABS, WIDTH, StructureSpec
from .materials import Material

Grid = list[list[Material]]

# Tope de rectángulos por estructura: evita un ciclo infinito si las capas se
# quedaran sin tierra antes de alcanzar la cobertura.
_MAX_PLACEMENTS = 10_000


def _generate_once(rng: random.Random) -> Grid:
    """Un intento de generación (pasos 1 a 3 de la sección 5)."""
    grid = [[Material.EARTH] * WIDTH for _ in range(HEIGHT)]
    _place_structures(grid, rng, CAVES, Material.EMPTY)
    _place_structures(grid, rng, SLABS, Material.STONE)
    return grid


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
