"""Constantes del problema y parámetros del generador de mapas.

Las capas y columnas de este módulo están en base 1 (capa = y + 1) e incluyen
ambos extremos, igual que en la propuesta. La conversión a coordenadas base 0
se hace en el generador.
"""

from dataclasses import dataclass

WIDTH, HEIGHT = 25, 75
BATTERY = 100                      # batería inicial, en puntos porcentuales

STALAGMITE_PROB = 0.35             # probabilidad por casilla de piso de cueva
STALAGMITE_LAYERS = (25, 70)
GOLD_CENTER_LAYERS = (71, 74)
GOLD_CENTER_COLUMNS = (2, 24)      # para que el "+" quepa en el mapa


@dataclass(frozen=True)
class StructureSpec:
    """Parámetros de una estructura rectangular del generador."""

    layers: tuple[int, int]        # capas donde puede generarse
    width: tuple[int, int]         # rango de ancho, en casillas
    height: tuple[int, int]        # rango de alto, en casillas
    coverage: float                # fracción objetivo de casillas de esas capas


CAVES = StructureSpec(layers=(15, 70), width=(3, 7), height=(1, 3), coverage=0.10)
SLABS = StructureSpec(layers=(5, 75), width=(3, 8), height=(1, 2), coverage=0.15)
LAKES = StructureSpec(layers=(35, 69), width=(2, 5), height=(1, 2), coverage=0.02)
