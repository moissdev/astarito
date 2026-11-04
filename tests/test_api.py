"""Contrato de la API: esquemas, determinismo, validación y coincidencia con el núcleo."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from backend import api
from backend.agent.config import BATTERY, HEIGHT, WIDTH
from backend.agent.generator import MapGenerationError, generate_map
from backend.agent.heuristic import cost_to_go_table
from backend.agent.metrics import summarize
from backend.agent.rules import blocked_cells
from backend.agent.search import a_star
from backend.schemas import MAX_SEED, MapResponse, SolveResponse

client = TestClient(api.app)


@pytest.fixture(autouse=True)
def clear_map_cache() -> Iterator[None]:
    # Cada prueba empieza sin mapas en caché, para que no dependan del orden.
    api._map_for.cache_clear()
    yield
    api._map_for.cache_clear()


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# --- GET /api/map ----------------------------------------------------------

def test_map_follows_schema_and_matches_core() -> None:
    response = client.get("/api/map", params={"seed": 7})
    assert response.status_code == 200
    body = MapResponse.model_validate(response.json())
    game_map = generate_map(7)
    assert (body.seed, body.width, body.height) == (7, WIDTH, HEIGHT)
    assert body.grid == game_map.to_rows()
    assert len(body.blocked) == HEIGHT and all(len(row) == WIDTH for row in body.blocked)
    expected_blocked = blocked_cells(game_map)
    assert all(
        (body.blocked[y][x] == "1") == expected_blocked[y][x]
        for y in range(HEIGHT)
        for x in range(WIDTH)
    )
    assert set(body.gold) == game_map.gold and len(body.gold) == 5


def test_same_seed_returns_same_map() -> None:
    first = client.get("/api/map", params={"seed": 123}).json()
    api._map_for.cache_clear()                       # se regenera, no se lee de la caché
    second = client.get("/api/map", params={"seed": 123}).json()
    assert first == second


def test_map_without_seed_returns_a_reusable_seed() -> None:
    body = client.get("/api/map").json()
    assert 0 <= body["seed"] <= MAX_SEED
    again = client.get("/api/map", params={"seed": body["seed"]}).json()
    assert again == body


@pytest.mark.parametrize("seed", ["-1", str(MAX_SEED + 1), "abc"])
def test_map_rejects_invalid_seed(seed: str) -> None:
    assert client.get("/api/map", params={"seed": seed}).status_code == 422


# --- POST /api/solve -------------------------------------------------------

@pytest.mark.parametrize("start_x", [0, 12, WIDTH - 1])
def test_solve_matches_core(start_x: int) -> None:
    response = client.post("/api/solve", json={"seed": 7, "start_x": start_x})
    assert response.status_code == 200
    body = SolveResponse.model_validate(response.json())

    game_map = generate_map(7)
    result = a_star(game_map, start_x, battery=BATTERY)
    summary = summarize(game_map, result, BATTERY)
    exact = cost_to_go_table(game_map, relaxed=False)[0][start_x]

    assert body.profitable == summary.profitable
    assert body.cost == summary.cost
    assert body.battery_left == summary.battery_left
    assert body.min_cost == exact
    assert body.path == list(result.path)
    assert [(e.x, e.y, e.g, e.h, e.f, e.pushed) for e in body.expansions] == [
        (e.x, e.y, e.g, e.h, e.f, list(e.pushed)) for e in result.expansions
    ]
    assert body.expanded == len(result.expansions)
    assert body.composition == {
        material.name.lower(): n for material, n in summary.composition.items()
    }


def test_composition_uses_material_names() -> None:
    body = client.post("/api/solve", json={"seed": 7, "start_x": 12}).json()
    assert list(body["composition"]) == ["earth", "stone", "empty", "stalagmite"]


def test_unprofitable_start_reports_min_cost() -> None:
    # Busca una semilla y columna sin ruta rentable para comprobar ese caso real.
    for seed in range(200):
        exact = cost_to_go_table(generate_map(seed), relaxed=False)[0]
        start_x = next((x for x in range(WIDTH) if exact[x] > BATTERY), None)
        if start_x is not None:
            break
    else:
        pytest.fail("no se encontró un inicio no rentable en 200 semillas")
    body = client.post("/api/solve", json={"seed": seed, "start_x": start_x}).json()
    assert body["profitable"] is False
    assert body["cost"] is None and body["battery_left"] is None and body["path"] == []
    assert body["min_cost"] == exact[start_x] > BATTERY


@pytest.mark.parametrize(
    "payload",
    [
        {"seed": 7, "start_x": -1},
        {"seed": 7, "start_x": WIDTH},
        {"seed": -1, "start_x": 0},
        {"seed": 7},
        {"start_x": 0},
    ],
)
def test_solve_rejects_invalid_requests(payload: dict[str, int]) -> None:
    assert client.post("/api/solve", json=payload).status_code == 422


# --- Errores de generación -------------------------------------------------

def test_generation_failure_returns_400(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(seed: int) -> None:
        raise MapGenerationError(f"semilla {seed}: sin ruta técnica")

    monkeypatch.setattr(api, "generate_map", fail)
    assert client.get("/api/map", params={"seed": 1}).status_code == 400
    assert client.post("/api/solve", json={"seed": 1, "start_x": 0}).status_code == 400
