"""Resumen del resultado de una búsqueda: veredicto, batería y composición de la ruta."""

from dataclasses import dataclass

from .grid import GameMap
from .materials import MINING_COST, Material
from .search import SearchResult


@dataclass(frozen=True)
class Summary:
    profitable: bool                   # hay ruta y su costo cabe en la batería
    cost: int | None
    battery_left: int | None           # batería - costo; negativo si la ruta no cabe
    path_length: int                   # pasos (casillas minadas); 0 sin ruta
    expanded: int
    composition: dict[Material, int]   # casillas minadas por material


def summarize(game_map: GameMap, result: SearchResult, battery: int) -> Summary:
    """Resume un `SearchResult`. La casilla de inicio no se mina ni se cobra,
    por lo que no cuenta en la composición ni en la longitud."""
    # Todos los materiales minables aparecen, aunque sea con 0, para que el
    # formato sea siempre el mismo.
    composition = {material: 0 for material in MINING_COST}
    for x, y in result.path[1:]:
        composition[game_map.material(x, y)] += 1

    if not result.found or result.cost is None:
        return Summary(
            profitable=False,
            cost=None,
            battery_left=None,
            path_length=0,
            expanded=len(result.expansions),
            composition=composition,
        )
    # Con la poda activa, `found` ya implica costo <= batería. Se vuelve a
    # comparar por si la búsqueda se hizo sin poda (battery=None).
    return Summary(
        profitable=result.cost <= battery,
        cost=result.cost,
        battery_left=battery - result.cost,
        path_length=len(result.path) - 1,
        expanded=len(result.expansions),
        composition=composition,
    )
