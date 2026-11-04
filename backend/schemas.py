"""Modelos de petición y respuesta de la API (Pydantic)."""

from pydantic import BaseModel, Field

from .agent.config import WIDTH

# Las semillas viajan como número en JSON; el navegador solo representa enteros
# exactos hasta 2**53 - 1, así que se acotan para que la semilla de vuelta sea
# la misma que generó el mapa.
MAX_SEED = 2**53 - 1


class MapResponse(BaseModel):
    seed: int
    width: int
    height: int
    grid: list[str]                  # una cadena por fila, un carácter por material
    blocked: list[str]               # "1" bloqueada, "0" libre (misma forma que grid)
    gold: list[tuple[int, int]]


class SolveRequest(BaseModel):
    seed: int = Field(ge=0, le=MAX_SEED)
    start_x: int = Field(ge=0, lt=WIDTH)


class ExpansionOut(BaseModel):
    x: int
    y: int
    g: int
    h: int
    f: int
    pushed: list[tuple[int, int]]    # casillas que entraron a la frontera en este paso


class SolveResponse(BaseModel):
    profitable: bool
    cost: int | None
    battery_left: int | None
    min_cost: int | None             # costo mínimo real, sin límite de batería
    path: list[tuple[int, int]]
    expansions: list[ExpansionOut]
    expanded: int
    composition: dict[str, int]      # casillas minadas por material
