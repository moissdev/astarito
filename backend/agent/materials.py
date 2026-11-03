"""Materiales del mapa y su costo de minado."""

from enum import Enum


class Material(Enum):
    """Cada valor es el carácter con el que la API serializa la casilla."""

    EARTH = "E"
    STONE = "S"
    EMPTY = "A"                    # aire: cueva o casilla ya minada
    STALAGMITE = "T"
    LAVA = "L"
    GOLD = "G"


# Costo de entrar a la casilla, en puntos porcentuales de batería.
# La lava y el oro nunca se minan, por lo que no tienen costo definido.
MINING_COST: dict[Material, int] = {
    Material.EARTH: 1,
    Material.STONE: 3,
    Material.EMPTY: 0,
    Material.STALAGMITE: 2,
}
