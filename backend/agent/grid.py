"""Mapa inmutable y consultas de vecindad.

Coordenadas (x, y) en base 0 con origen arriba a la izquierda; la capa de una
casilla es y + 1.
"""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from .materials import Material

Cell = tuple[int, int]             # (x, y)

# Orden fijo de vecinos (arriba, izquierda, derecha, abajo) para que todo
# recorrido sea determinista.
_OFFSETS: tuple[Cell, ...] = ((0, -1), (-1, 0), (1, 0), (0, 1))


@dataclass(frozen=True)
class GameMap:
    """Mapa del corte sagital. No se modifica después de crearse.

    El tamaño se toma de `cells`; el generador produce mapas de WIDTH × HEIGHT,
    pero las pruebas pueden usar mapas pequeños hechos a mano.
    """

    seed: int
    attempts: int                                  # intentos hasta aceptar la semilla
    cells: tuple[tuple[Material, ...], ...]        # cells[y][x]
    gold: frozenset[Cell]

    def __post_init__(self) -> None:
        if not self.cells or not self.cells[0]:
            raise ValueError("el mapa no puede estar vacío")
        if any(len(row) != self.width for row in self.cells):
            raise ValueError("todas las filas deben tener el mismo ancho")
        actual_gold = {
            (x, y)
            for y, row in enumerate(self.cells)
            for x, material in enumerate(row)
            if material is Material.GOLD
        }
        if actual_gold != self.gold:
            raise ValueError("`gold` no coincide con las casillas de oro del mapa")

    @classmethod
    def from_rows(cls, rows: Iterable[str], seed: int = 0, attempts: int = 1) -> "GameMap":
        """Construye un mapa desde cadenas de símbolos (una por fila).
        Es la operación inversa de `to_rows`; útil en pruebas."""
        cells = tuple(tuple(Material(symbol) for symbol in row) for row in rows)
        gold = frozenset(
            (x, y)
            for y, row in enumerate(cells)
            for x, material in enumerate(row)
            if material is Material.GOLD
        )
        return cls(seed=seed, attempts=attempts, cells=cells, gold=gold)

    @property
    def width(self) -> int:
        return len(self.cells[0])

    @property
    def height(self) -> int:
        return len(self.cells)

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def material(self, x: int, y: int) -> Material:
        """Material de la casilla. Lanza IndexError fuera del mapa
        (evita que un índice negativo lea en silencio el otro extremo)."""
        if not self.in_bounds(x, y):
            raise IndexError(f"casilla fuera del mapa: ({x}, {y})")
        return self.cells[y][x]

    def neighbors4(self, x: int, y: int) -> Iterator[Cell]:
        """Vecinos arriba, izquierda, derecha y abajo que están dentro del mapa."""
        for dx, dy in _OFFSETS:
            nx, ny = x + dx, y + dy
            if self.in_bounds(nx, ny):
                yield nx, ny

    def to_rows(self) -> list[str]:
        """Una cadena por fila, un carácter por material (formato de la API)."""
        return ["".join(material.value for material in row) for row in self.cells]
