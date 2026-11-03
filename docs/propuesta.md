# Propuesta de proyecto: Astarito, robot minero con A\* y heurística relajada

Nov 2, 2026 · @Moisés Pérez

## 1. Título

*Agente minero con A\* y heurística de problema relajado para trazar la ruta de menor consumo de batería hacia una veta de oro.*

Escenario: corte sagital del subsuelo de 25 columnas por 75 capas, con gravedad, batería limitada y obstáculos distribuidos por profundidad.

## 2. Descripción del problema y alcance

Una empresa minera requiere conocer la ruta más económica desde la superficie hasta una veta de oro antes de enviar a sus mineros. Un robot minero recorre un corte sagital del terreno (cuadrícula de 25 columnas por 75 capas, con la capa 1 en la superficie) y traza esa ruta con un taladro cuya batería inicia al 100 %.

Cada casilla que el robot mina consume un porcentaje de batería según su material. El robot solo puede moverse a la izquierda, a la derecha o hacia abajo, nunca hacia arriba, por lo que la decisión central del agente es *atravesar un obstáculo costoso (piedra) o rodearlo por tierra más barata*.

Si la ruta de menor costo supera el 100 % de la batería, se concluye que *no existe una ruta rentable*, aunque la veta sea técnicamente alcanzable. El objetivo es trazar la ruta y no extraer el oro: el robot se detiene al llegar a una casilla adyacente a cualquiera de las cinco casillas de oro.

### Alcance de la propuesta

- Mapa de tamaño fijo (25 × 75) y batería fija (100 %), con un solo robot y un mapa completamente conocido.
- Flujo de uso: se genera el mapa a partir de una semilla, el usuario elige la casilla de inicio en la capa 1 y se ejecuta la búsqueda.
- Un único algoritmo: A\* (Weighted A\* con w = 1) y una heurística de problema relajado.
- Agente implementado en Python, con un frontend web que visualiza el proceso de búsqueda y la ruta resultante.

## 3. PEAS

El agente se describe mediante cuatro elementos: medida de rendimiento, entorno, actuadores y sensores.

| Elemento | Definición |
| --- | --- |
| **P** (Rendimiento) | Minimizar el consumo acumulado de batería hasta llegar a una casilla adyacente al oro. La ruta es exitosa si el consumo es ≤ 100 %. Restricción dura: no entrar a casillas bloqueadas (lava, vecinas de lava y casillas sobre un vacío o una estalagmita). Métrica secundaria: nodos expandidos. |
| **E** (Entorno) | Cuadrícula de 25 columnas × 75 capas (corte sagital; la capa 1 es la superficie y el eje Y es la profundidad). Cada casilla contiene tierra, piedra, vacío, estalagmita, lava u oro. El oro forma una única veta en "+" de 5 casillas. |
| **A** (Actuadores) | `Izquierda`, `Derecha` y `Abajo`. Cada acción mina la casilla de destino (la deja vacía) y mueve al robot a ella. No existe la acción de subir. |
| **S** (Sensores) | Posición actual (x, y), batería restante y material de cada casilla del mapa, incluida la ubicación del oro (el mapa es completamente conocido). |

## 4. Características del entorno

El entorno es totalmente observable, determinista, secuencial, estático, discreto y de un solo agente.

| Propiedad | Valor | Justificación |
| --- | --- | --- |
| Observabilidad | **Totalmente observable** | El mapa completo se conoce antes de iniciar la búsqueda. |
| Determinismo | **Determinista** | Cada acción produce un único estado sucesor y un costo fijo. |
| Episodios | **Secuencial** | La batería consumida en cada paso condiciona las rutas posibles después. |
| Dinamismo | **Estático** | El mapa no cambia durante la planeación. Las casillas que el robot vacía quedan siempre detrás o encima de su posición y no afectan a las casillas por las que aún puede pasar. |
| Discreto o continuo | **Discreto** | Casillas, materiales, acciones y estados son finitos. |
| Agentes | **Un solo agente** | No hay otros agentes que modifiquen el entorno. |
| Conocimiento | **Conocido** | Las reglas de transición y los costos de minado están definidos. |

*Nota:* los costos son siempre mayores o iguales a 0 (las casillas vacías cuestan 0 %), por lo que son posibles ciclos de costo cero en las cuevas y la búsqueda requiere una lista de estados cerrados.

## 5. Materiales y generación del mapa

El mapa de 25 × 75 casillas se genera a partir de una semilla colocando estructuras (lajas, cuevas, estalagmitas y lagos de lava) dentro de rangos de profundidad; el costo de minado es el porcentaje de batería que consume entrar a la casilla.

| Material | Costo de minado | Capas de generación | Forma y cantidad |
| --- | --- | --- | --- |
| Tierra | 1 % | 1 a 75 | Material base: ocupa toda casilla que no recibe otro material. |
| Piedra | 3 % | 5 a 75 | *Lajas* horizontales de 3 a 8 casillas de ancho y 1 a 2 de grosor, hasta cubrir 15 % de las casillas de esas capas. |
| Vacía (aire) | 0 % | 15 a 70 | *Cuevas* de 3 a 7 casillas de ancho y 1 a 3 de alto, hasta cubrir 10 % de las casillas de esas capas. |
| Estalagmita | 2 % | 25 a 70 | Sobre el *piso de las cuevas*: cada casilla de piso (vacía con una casilla no vacía debajo) tiene 35 % de probabilidad de ser estalagmita. |
| Lava | Infinito (intransitable) | 35 a 69 | *Lagos* de 2 a 5 casillas de ancho y 1 a 2 de alto, solo sobre tierra o piedra (nunca dentro de una cueva), hasta cubrir 2 % de las casillas de esas capas. |
| Oro | 0 % | Centro en capas 71 a 74 | Una única veta en "+" de 5 casillas. |

### Procedimiento de generación

1. Se inicializa todo el mapa con tierra.
2. *Cuevas:* se colocan rectángulos aleatorios sobre casillas de tierra dentro de las capas 15 a 70 hasta alcanzar la cobertura indicada. Si un rectángulo se solapa con material ya colocado, solo se aplica sobre las casillas de tierra, por lo que las formas pueden resultar irregulares.
3. *Lajas:* se colocan rectángulos aleatorios sobre casillas de tierra dentro de las capas 5 a 75 con el mismo criterio.
4. *Estalagmitas:* cada casilla del piso de una cueva, entre las capas 25 y 70, se convierte en estalagmita con 35 % de probabilidad.
5. *Lagos de lava:* se colocan rectángulos aleatorios dentro de las capas 35 a 69, solo si toda su huella es tierra o piedra, hasta alcanzar la cobertura indicada.
6. *Veta de oro:* se elige al azar el centro entre las capas 71 a 74 y las columnas 2 a 24, para que las cinco casillas del "+" quepan en el mapa. Esas casillas se convierten en oro sin importar el material previo.
7. Se calcula el conjunto de casillas bloqueadas (sección 6).
8. Se verifica que exista una ruta técnica hasta el oro, sin considerar la batería. Si no existe, se descarta la semilla y se genera otra. Como la capa 1 es todo tierra y ninguna de sus casillas queda bloqueada, esta condición es la misma para cualquier casilla de inicio.

Los rangos de cuevas, estalagmitas y lagos terminan en las capas 70 y 69, justo antes de la zona del oro, pero esto no garantiza que la veta sea accesible: las casillas bloqueadas pueden cerrar todos los pasos en algunos mapas. Por eso se aplica la verificación del paso 8.

## 6. Espacio de estados

Un estado es la posición del robot, s = (x, y), con 1 ≤ x ≤ 25 y 1 ≤ y ≤ 75, por lo que existen a lo sumo 1,875 estados.

- **Estado inicial:** (x₀, 1), donde x₀ es la columna de la capa 1 elegida por el usuario. Esa casilla no se cobra, y la batería inicia en 100 %.
- **Prueba de meta:** la casilla es adyacente (arriba, abajo, izquierda o derecha) a alguna de las cinco casillas de oro. El robot nunca entra a una casilla de oro.
- **Factor de ramificación:** a lo sumo 3 (izquierda, derecha y abajo).
- **Batería:** no forma parte del estado. Como los costos son aditivos y no hay recarga, la batería restante es 100 − g(s), donde g(s) es el costo mínimo acumulado hasta s.

### Casillas bloqueadas

Una casilla está *bloqueada* (el robot no puede minarla ni entrar a ella) en cualquiera de estos casos:

1. Es lava.
2. Es adyacente (4 vecinos) a una casilla de lava, para no liberar la lava ni caer en ella.
3. Tiene directamente debajo una casilla vacía o una estalagmita.

La regla 3 evita caídas de más de una casilla: si el robot mina hacia abajo y la casilla siguiente fuera un vacío, caería dos o más casillas y se dañaría. Con esta regla, el robot nunca queda sobre un vacío ni sobre una estalagmita, por lo que no es necesario simular la gravedad ni el daño por caídas. Una consecuencia es que las cuevas solo se recorren por su piso (de lado a lado) y las estalagmitas solo se minan desde los costados.

## 7. Transiciones y costos

Cada acción mueve al robot a una casilla vecina y cuesta el porcentaje de minado del material de esa casilla.

| Acción | Transición | Costo c(s, s') |
| --- | --- | --- |
| `Izquierda` | (x, y) → (x − 1, y) | Costo del material de (x − 1, y) |
| `Derecha` | (x, y) → (x + 1, y) | Costo del material de (x + 1, y) |
| `Abajo` | (x, y) → (x, y + 1) | Costo del material de (x, y + 1) |

**Precondiciones** (una acción es aplicable solo si cumple las tres):

1. La casilla de destino está dentro del mapa y no es de oro.
2. La casilla de destino no está bloqueada (sección 6).
3. La batería alcanza: g(s) + c(s, s') ≤ 100.

**Costos de minado:** tierra 1, piedra 3, estalagmita 2 y vacía 0 (en puntos porcentuales de batería).

**Efecto:** la casilla de destino queda vacía y el robot se ubica en ella. El descenso de una casilla al minar hacia abajo es la única "caída" posible, y es segura porque la casilla inferior del destino nunca es un vacío ni una estalagmita.

*Ejemplo:* desde (x, y) con g = 40, la acción `Derecha` hacia una piedra produce el estado (x + 1, y) con g = 43 y batería restante de 57 %.

## 8. Rendimiento y evaluación

El rendimiento del agente es el costo g(meta) de la ruta encontrada, en puntos porcentuales de batería; una ruta es rentable si g(meta) ≤ 100 y la mejor ruta es la de menor costo.

### Métricas

1. **Costo de la ruta** y batería restante (100 − g).
2. **Veredicto:** ruta rentable o "sin ruta rentable" (costo mínimo mayor a 100 %).
3. **Nodos expandidos** por la búsqueda.
4. **Composición de la ruta:** casillas minadas por material y longitud en pasos.
5. **Corrección:** el costo de A\* debe coincidir con el de un Dijkstra inverso exacto en cada mapa.

## 9. Algoritmo y heurística

Se emplea A\* (Weighted A\* con w = 1) con una heurística obtenida al relajar las reglas de bloqueo, porque ambos garantizan la ruta de menor costo.

### Algoritmo: A\* con w = 1

```latex
f(s) = g(s) + w \cdot h(s), \qquad w = 1
```

La frontera se ordena por f(s). Se mantiene el menor g conocido por estado y se descarta todo sucesor con g + h > 100, ya que no puede alcanzar la meta con la batería disponible.

Justificación frente a las demás opciones:

- **Optimalidad:** el objetivo es la ruta rentable *más barata*. Con w = 1 y una heurística consistente, la primera meta extraída de la frontera es óptima y cada estado se expande una sola vez. Con w > 1 se perdería esa garantía.
- **Conclusión exacta de "sin ruta rentable":** si el óptimo supera 100 %, ninguna ruta es rentable. Un algoritmo no óptimo no permitiría afirmarlo.
- **Costos no uniformes:** BFS, DFS, DLS e IDS ignoran los costos de minado. La búsqueda voraz tampoco es óptima.
- **UCS** equivale a A\* con h = 0 y sirve de línea base.
- **IDA\*** ahorra memoria, ventaja irrelevante con a lo sumo 1,875 estados.

### Heurística: costo exacto en el problema relajado

Sea R el mismo problema sin las reglas de bloqueo 2 y 3 (casillas vecinas de lava y casillas sobre un vacío o una estalagmita). En R solo la lava es intransitable; las acciones, los costos y la prueba de meta son los mismos.

```latex
h(s) = c^{*}_{R}(s) = \text{costo mínimo de } s \text{ a una casilla adyacente al oro en } R
```

Se calcula una sola vez por mapa con un Dijkstra inverso (de las casillas meta hacia atrás) y se almacena en una tabla de 25 × 75 valores.

**Admisibilidad.** Todo camino legal del problema original también es legal en R, con los mismos costos, porque R bloquea un subconjunto de las casillas bloqueadas originales, y toda meta original es meta en R. Por tanto, c\*\_R(s) ≤ c\*(s) para todo estado s: la heurística nunca sobrestima el costo restante real.

**Consistencia.** Para toda transición legal s → s' de costo c(s, s'), esa transición también existe en R. Como c\*\_R es una distancia de camino mínimo, cumple la desigualdad triangular:

```latex
h(s) \le c(s, s') + h(s'), \qquad h(\text{meta}) = 0
```

Con una heurística consistente, f no decrece a lo largo de un camino y no se reabren estados cerrados.

**Valor informativo.** Es la técnica estándar de relajación de problemas: al conservar movimientos y costos y eliminar solo las reglas de seguridad, h se aproxima al costo real y reduce las expansiones frente a UCS (h = 0). Se descartó la suma del costo mínimo por fila, también admisible, por ser una cota demasiado débil.

## 10. Supuestos y limitaciones

La propuesta descansa en los siguientes supuestos, que conviene declarar de forma explícita:

- **Adyacencia:** se considera adyacente a las cuatro casillas ortogonales (sin diagonales), tanto para la lava como para el oro.
- **Casilla de inicio:** el usuario puede elegir cualquiera de las 25 columnas de la capa 1.
- **Formas de los obstáculos:** lajas, cuevas y lagos son rectángulos que se recortan al solaparse con otro material; no se modelan cuevas conectadas entre sí ni lagos de forma irregular.
- **Cantidades:** piedra, vacío y lava se colocan hasta alcanzar la cobertura indicada para sus capas. Las estalagmitas no tienen cobertura fija, ya que dependen de cuántas casillas de piso existan en las cuevas.
- **Éxito con 0 %:** una ruta que termina con la batería exactamente en 0 % se considera exitosa.
- **Costo de la heurística:** el Dijkstra inverso que la calcula recorre el mapa completo; esas expansiones no se incluyen en el conteo de nodos expandidos de A\*.
- **Escala del problema:** con a lo sumo 1,875 estados, UCS ya resuelve el problema en un instante. La justificación de A\* descansa en la optimalidad y en el principio de relajación, no en la velocidad.

## 11. Arquitectura general del programa

El programa se divide en un backend en Python que contiene todo el agente y un frontend web que solo visualiza, y ambos se despliegan en un único proyecto.

- **Backend (Python):** genera el mapa, calcula las casillas bloqueadas y la heurística, ejecuta A\* y devuelve la ruta junto con la traza de expansiones. El núcleo (`backend/agent`) es Python puro, sin dependencia del framework web, por lo que se puede ejecutar y probar sin servidor.
- **Frontend (web):** dibuja la cuadrícula de 25 × 75 en un canvas, permite elegir la casilla de inicio y reproduce la traza paso a paso. No contiene lógica del agente.
- **API sin estado:** en cada petición el servidor regenera el mapa a partir de la semilla. No hay base de datos ni sesiones.

### Flujo de una ejecución

1. El frontend solicita `GET /api/map`, con una semilla opcional.
2. El backend genera el mapa (descartando semillas sin ruta técnica) y devuelve la cuadrícula, las casillas bloqueadas, las casillas de oro y la semilla utilizada.
3. El usuario elige una columna de la capa 1 como casilla de inicio.
4. El frontend envía `POST /api/solve` con la semilla y la columna elegida.
5. El backend regenera el mapa, calcula la tabla de la heurística, ejecuta A\* con w = 1 y responde con la ruta, el costo, el veredicto (rentable o no) y las expansiones en orden.
6. El frontend reproduce las expansiones y dibuja la ruta, con controles de velocidad, pausa y avance paso a paso.

### Decisiones de diseño

- **Respuesta completa en lugar de transmisión continua:** con a lo sumo 1,875 estados, la traza es del orden de decenas de KB y se calcula en una fracción de segundo, por lo que no se requieren WebSockets.
- **Reproducibilidad:** la misma semilla produce siempre el mismo mapa, lo que permite repetir y comparar ejecuciones.
- **Separación del núcleo:** el agente no conoce HTTP ni JSON; la capa de API solo traduce entre solicitudes y llamadas al agente.
- **Coordenadas:** (x, y) con origen en la esquina superior izquierda y base 0; la capa de una casilla es y + 1.

## 12. Estructura del backend en Python

El backend se compone de un núcleo del agente en Python puro (`backend/agent`) y una capa delgada de API (`api.py`, `schemas.py`) que lo expone por HTTP.

### Árbol de archivos del proyecto

```text
astarito/
├─ README.md                 # descripción, instalación y ejecución local
├─ CLAUDE.md                 # decisiones y convenciones del proyecto para Claude Code
├─ .gitignore
├─ pyproject.toml            # dependencias y punto de entrada del despliegue
├─ .python-version           # versión de Python (3.12)
├─ docs/
│  └─ propuesta.md           # exportación de este documento de la propuesta
├─ backend/
│  ├─ __init__.py
│  ├─ api.py                 # aplicación FastAPI y endpoints
│  ├─ schemas.py             # modelos de petición y respuesta
│  └─ agent/                 # núcleo del agente, sin dependencia del framework web
│     ├─ __init__.py
│     ├─ config.py           # constantes del problema
│     ├─ materials.py        # materiales y costos de minado
│     ├─ grid.py             # mapa inmutable y consultas de vecindad
│     ├─ rules.py            # casillas bloqueadas, metas y sucesores
│     ├─ heuristic.py        # Dijkstra inverso (relajado o exacto)
│     ├─ generator.py        # generación por estructuras con semilla
│     ├─ search.py           # A* con traza de expansiones
│     └─ metrics.py          # resumen del resultado
├─ tests/                    # pruebas del backend (pytest)
│  ├─ test_generator.py
│  ├─ test_rules.py
│  ├─ test_heuristic.py
│  ├─ test_search.py
│  └─ test_api.py
├─ frontend/                 # aplicación web (Vite + TypeScript, dibujo en canvas)
│  ├─ index.html
│  ├─ package.json
│  ├─ tsconfig.json
│  ├─ vite.config.ts         # salida hacia ../public y proxy de /api en desarrollo
│  └─ src/
│     ├─ main.ts             # arranque y conexión de los módulos
│     ├─ api/
│     │  ├─ client.ts        # fetchMap() y solve()
│     │  └─ types.ts         # tipos de MapResponse y SolveResponse
│     ├─ state/
│     │  └─ store.ts         # semilla, columna de inicio, traza y paso actual
│     ├─ render/
│     │  ├─ MapCanvas.ts     # cuadrícula, bloqueadas, frontera, cerrados y ruta
│     │  ├─ palette.ts       # colores por material
│     │  └─ viewport.ts      # escala y desplazamiento del mapa de 25 × 75
│     ├─ playback/
│     │  └─ player.ts        # reproducción: play, pausa, paso a paso y velocidad
│     ├─ ui/
│     │  ├─ Controls.ts      # semilla, nuevo mapa, elección de inicio y reproducción
│     │  ├─ MetricsPanel.ts  # costo, batería restante, expansiones y composición
│     │  ├─ BatteryBar.ts    # barra de batería durante la reproducción
│     │  └─ Legend.ts        # leyenda de materiales y estados
│     └─ styles/
│        └─ main.css
└─ public/                   # salida de la compilación del frontend (npm run build)
```

### Módulos y dependencias

| Archivo | Responsabilidad | Depende de |
| --- | --- | --- |
| `config.py` | Tamaño del mapa, batería, rangos de capas y parámetros de las estructuras | Ninguno |
| `materials.py` | Enumeración de materiales y costos de minado | Ninguno |
| `grid.py` | Mapa inmutable, acceso a casillas y vecindad de 4 direcciones | `materials` |
| `rules.py` | Casillas bloqueadas, casillas meta y sucesores de un estado | `grid`, `materials` |
| `heuristic.py` | Tabla de costo restante mediante Dijkstra inverso | `rules`, `grid` |
| `generator.py` | Generación del mapa a partir de una semilla, con rechazo de mapas sin ruta técnica | `config`, `rules`, `heuristic` |
| `search.py` | A\* con poda por batería y registro de expansiones | `rules`, `heuristic` |
| `metrics.py` | Composición de la ruta, batería restante y veredicto | `search` |
| `schemas.py` | Modelos Pydantic de la API | `config` |
| `api.py` | Endpoints HTTP | Todos los anteriores |

El núcleo solo utiliza la biblioteca estándar (`heapq`, `random`, `dataclasses`, `enum`). FastAPI y Pydantic se limitan a la capa de API.

### Núcleo del agente: esqueleto de los módulos

**`config.py` y `materials.py`**

```python
# config.py
from dataclasses import dataclass

WIDTH, HEIGHT = 25, 75
BATTERY = 100
STALAGMITE_PROB = 0.35
STALAGMITE_LAYERS = (25, 70)
GOLD_CENTER_LAYERS = (71, 74)      # base 1
GOLD_CENTER_COLUMNS = (2, 24)      # base 1, para que el "+" quepa

@dataclass(frozen=True)
class StructureSpec:
    layers: tuple[int, int]        # capas donde puede generarse (base 1)
    width: tuple[int, int]         # rango de ancho, en casillas
    height: tuple[int, int]        # rango de alto, en casillas
    coverage: float                # fracción objetivo de casillas de esas capas

CAVES = StructureSpec(layers=(15, 70), width=(3, 7), height=(1, 3), coverage=0.10)
SLABS = StructureSpec(layers=(5, 75), width=(3, 8), height=(1, 2), coverage=0.15)
LAKES = StructureSpec(layers=(35, 69), width=(2, 5), height=(1, 2), coverage=0.02)
```

```python
# materials.py
from enum import Enum

class Material(Enum):
    EARTH = "E"
    STONE = "S"
    EMPTY = "A"
    STALAGMITE = "T"
    LAVA = "L"
    GOLD = "G"

# La lava y el oro nunca se minan, por lo que no tienen costo definido.
MINING_COST: dict[Material, int] = {
    Material.EARTH: 1,
    Material.STONE: 3,
    Material.EMPTY: 0,
    Material.STALAGMITE: 2,
}
```

**`grid.py`**

```python
from dataclasses import dataclass
from typing import Iterator
from .materials import Material

Cell = tuple[int, int]             # (x, y), base 0, origen arriba a la izquierda

@dataclass(frozen=True)
class GameMap:
    seed: int
    attempts: int                                  # intentos hasta aceptar la semilla
    cells: tuple[tuple[Material, ...], ...]        # cells[y][x]
    gold: frozenset[Cell]

    def material(self, x: int, y: int) -> Material: ...
    def in_bounds(self, x: int, y: int) -> bool: ...
    def neighbors4(self, x: int, y: int) -> Iterator[Cell]: ...
    def to_rows(self) -> list[str]: ...            # una cadena por fila, para la API
```

**`rules.py`**

```python
from typing import Iterator
from .grid import Cell, GameMap

def blocked_cells(game_map: GameMap, relaxed: bool = False) -> list[list[bool]]:
    """Casillas bloqueadas (sección 6).
    relaxed=False: lava, vecinas de lava y casillas sobre un vacío o una estalagmita.
    relaxed=True: solo la lava (problema relajado de la heurística)."""

def goal_cells(game_map: GameMap, blocked: list[list[bool]]) -> frozenset[Cell]:
    """Casillas no bloqueadas adyacentes (4 vecinos) a alguna casilla de oro."""

def successors(game_map: GameMap, blocked: list[list[bool]], cell: Cell) -> Iterator[tuple[Cell, int]]:
    """Genera (destino, costo) para Izquierda, Derecha y Abajo.
    Excluye casillas fuera del mapa, bloqueadas y de oro."""
```

**`heuristic.py`**

```python
from .grid import GameMap

def cost_to_go_table(game_map: GameMap, relaxed: bool) -> list[list[float]]:
    """Costo mínimo de cada casilla a una casilla meta (infinito si no hay ruta).
    Dijkstra inverso: parte de las casillas meta y recorre las aristas al revés
    (los predecesores de una casilla son la de arriba, la izquierda y la derecha).
    relaxed=True  -> tabla de la heurística h(s).
    relaxed=False -> costo óptimo real, para pruebas y para verificar la ruta técnica."""
```

**`generator.py`**

```python
import random
from .config import StructureSpec
from .grid import Cell, GameMap
from .materials import Material

class MapGenerationError(Exception): ...

def generate_map(seed: int, max_attempts: int = 50) -> GameMap:
    """Genera mapas con un mismo generador sembrado hasta obtener uno con ruta
    técnica al oro. Es determinista: la misma semilla produce el mismo mapa.
    Lanza MapGenerationError si se agotan los intentos."""

def _generate_once(rng: random.Random) -> list[list[Material]]: ...
def _place_structures(grid, rng, spec: StructureSpec, material: Material) -> None:
    """Cuevas y lajas: rectángulos sobre casillas de tierra hasta la cobertura objetivo."""
def _place_stalagmites(grid, rng) -> None:
    """Convierte casillas de piso de cueva (vacías con una casilla no vacía debajo)."""
def _place_lava_lakes(grid, rng) -> None:
    """Rectángulos cuya huella completa es tierra o piedra."""
def _place_gold(grid, rng) -> frozenset[Cell]:
    """Elige el centro de la veta y convierte en oro las 5 casillas del \"+\"."""
def has_technical_route(game_map: GameMap) -> bool:
    """Verdadero si alguna casilla de la capa 1 tiene costo finito en la tabla exacta."""
```

**`search.py`**

```python
from dataclasses import dataclass
from .config import BATTERY
from .grid import Cell, GameMap

@dataclass(frozen=True)
class Expansion:
    x: int
    y: int
    g: int
    h: int
    f: int

@dataclass(frozen=True)
class SearchResult:
    found: bool                      # hay ruta con costo <= batería
    path: tuple[Cell, ...]           # del inicio a la casilla meta
    cost: int | None
    expansions: tuple[Expansion, ...]  # en orden de expansión

def a_star(game_map: GameMap, start_x: int, battery: int | None = BATTERY,
           weight: float = 1.0) -> SearchResult:
    """A* (Weighted A* con weight = 1) desde (start_x, 0).
    - Frontera: heap por f = g + weight * h; desempate por mayor g.
    - Cerrados: menor g conocido por estado.
    - Poda: se descarta todo sucesor con g + h > battery.
    - battery=None desactiva la poda y devuelve el costo mínimo real."""
```

**`metrics.py`**

```python
from dataclasses import dataclass
from .grid import GameMap
from .materials import Material
from .search import SearchResult

@dataclass(frozen=True)
class Summary:
    profitable: bool
    cost: int | None
    battery_left: int | None
    path_length: int
    expanded: int
    composition: dict[Material, int]   # casillas minadas por material

def summarize(game_map: GameMap, result: SearchResult, battery: int) -> Summary: ...
```

### Capa de API: esqueleto

**`schemas.py`**

```python
from pydantic import BaseModel, Field
from .agent.config import WIDTH

class MapResponse(BaseModel):
    seed: int
    width: int
    height: int
    grid: list[str]                  # una cadena por fila, un carácter por material
    blocked: list[str]               # "1" bloqueada, "0" libre (misma forma que grid)
    gold: list[tuple[int, int]]

class SolveRequest(BaseModel):
    seed: int
    start_x: int = Field(ge=0, lt=WIDTH)

class ExpansionOut(BaseModel):
    x: int
    y: int
    g: int
    h: int
    f: int

class SolveResponse(BaseModel):
    profitable: bool
    cost: int | None
    battery_left: int | None
    min_cost: int | None             # costo mínimo real, sin límite de batería
    path: list[tuple[int, int]]
    expansions: list[ExpansionOut]
    expanded: int
    composition: dict[str, int]      # casillas minadas por material
```

**`api.py`**

```python
from functools import lru_cache
from fastapi import FastAPI
from .agent.grid import GameMap
from .agent.generator import generate_map
from .schemas import MapResponse, SolveRequest, SolveResponse

app = FastAPI(title="Astarito")

@lru_cache(maxsize=32)
def _map_for(seed: int) -> GameMap:
    """Generación con caché en memoria; la API sigue siendo sin estado."""
    return generate_map(seed)

@app.get("/api/health")
def health() -> dict[str, str]: ...

@app.get("/api/map", response_model=MapResponse)
def get_map(seed: int | None = None) -> MapResponse:
    """Sin semilla, el servidor elige una al azar y la devuelve."""

@app.post("/api/solve", response_model=SolveResponse)
def solve(request: SolveRequest) -> SolveResponse:
    """Regenera el mapa, ejecuta A* con w = 1 y devuelve ruta, veredicto y traza.
    min_cost se obtiene de la tabla exacta (relaxed=False) para informar el costo
    real cuando la ruta no es rentable."""
```

### Contrato de la API

| Método y ruta | Entrada | Respuesta | Errores |
| --- | --- | --- | --- |
| `GET /api/health` | Ninguna | `{"status": "ok"}` | Ninguno |
| `GET /api/map` | `seed` opcional (consulta) | `MapResponse` | 400 si la generación agota los intentos |
| `POST /api/solve` | `SolveRequest` (JSON) | `SolveResponse` | 422 por validación; 400 si la generación agota los intentos |

*Ejemplo ilustrativo (abreviado) de la respuesta de `POST /api/solve`:*

```json
{
  "profitable": true,
  "cost": 90,
  "battery_left": 10,
  "min_cost": 90,
  "path": [[12, 0], [12, 1], [12, 2]],
  "expansions": [{"x": 12, "y": 0, "g": 0, "h": 78, "f": 78}],
  "expanded": 1000,
  "composition": {"earth": 66, "stone": 8, "empty": 5, "stalagmite": 0}
}
```

### Pruebas automatizadas

| Archivo | Verificaciones |
| --- | --- |
| `test_generator.py` | La misma semilla produce el mismo mapa. La capa 1 es solo tierra. Cada material aparece dentro de sus capas. Las estalagmitas solo están sobre el piso de una cueva. Los lagos de lava solo ocupan tierra o piedra. La veta es un "+" de 5 casillas con centro en las capas 71 a 74 y columnas 2 a 24. Todo mapa aceptado tiene ruta técnica. |
| `test_rules.py` | La lava y sus vecinas están bloqueadas. Una casilla sobre un vacío o una estalagmita está bloqueada. Ningún sucesor sube. El costo del sucesor es el del material de destino. Nunca se entra a una casilla de oro. Ninguna casilla de la capa 1 queda bloqueada. |
| `test_heuristic.py` | En varias semillas, h(s) no supera el costo real exacto (admisibilidad), h(s) ≤ c(s, s') + h(s') en toda transición (consistencia) y h vale 0 en las casillas meta. |
| `test_search.py` | Para las 25 columnas de inicio, el costo de A\* coincide con el de la tabla exacta. El veredicto "rentable" equivale a costo ≤ 100. La ruta es válida: empieza en la capa 1, cada paso es un sucesor, termina en una casilla meta y la suma de costos es igual al costo reportado. El valor de f no decrece y ningún estado se expande dos veces. |
| `test_api.py` | Las respuestas cumplen el esquema. La misma semilla devuelve el mismo mapa. Un `start_x` fuera de rango devuelve 422. `POST /api/solve` coincide con la ejecución directa del núcleo. |

## 13. Despliegue en Vercel

El proyecto se despliega en el plan gratuito (Hobby) de Vercel: la aplicación FastAPI se ejecuta como una función y el frontend compilado se sirve como archivos estáticos.

### Configuración

Vercel detecta FastAPI a partir de las dependencias y ejecuta la aplicación completa como una sola función, sin comando de compilación para el backend. Como el módulo no se llama `app.py` ni está en la raíz, el punto de entrada se declara en `pyproject.toml`:

```toml
[project]
name = "astarito"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["fastapi"]          # solo dependencias de ejecución

[project.optional-dependencies]
dev = ["pytest", "httpx", "uvicorn"]

[tool.vercel]
entrypoint = "backend.api:app"
```

- **Versión de Python:** 3.12, fijada con el archivo `.python-version`.
- **Frontend:** se compila hacia el directorio `public/`, desde donde Vercel sirve los archivos estáticos mediante su CDN. No se usa `app.mount` para ese directorio.
- **Tamaño:** Python no aplica *tree-shaking*, por lo que se incluye todo lo alcanzable. Si el tamaño llegara a importar, se excluyen pruebas y el código del frontend con `excludeFiles`.
- **Desarrollo local:** `uvicorn backend.api:app --reload` para la API y `pytest` para las pruebas.

### Límites del plan Hobby aplicables

| Aspecto | Límite | Situación del proyecto |
| --- | --- | --- |
| Duración de una función | 300 s | Una ejecución tarda una fracción de segundo. |
| Memoria | 2 GB | Suficiente para un mapa de 1,875 casillas. |
| Tamaño del paquete de Python | 500 MB sin comprimir | El núcleo solo usa la biblioteca estándar. |
| Tamaño de la respuesta | 4.5 MB | La traza es del orden de decenas de KB. |
| Invocaciones incluidas | 1,000,000 por mes | Uso académico muy inferior. |
| Uso permitido | Personal y no comercial | Proyecto escolar. |

Si se excedieran los límites de uso, la función queda en pausa hasta que pasen 30 días, un escenario improbable con este volumen de tráfico.

### Validación previa

La combinación de FastAPI con un frontend estático en `public/` debe comprobarse con un despliegue de prueba al inicio del desarrollo:

1. Desplegar un `/api/health` mínimo junto con una página de prueba en `public/`.
2. Confirmar que `/` entrega la página y que `/api/health` responde.
3. Abrir la dirección de producción en una ventana de incógnito para comprobar que la protección de despliegues no exige iniciar sesión a quien califique el proyecto.

Si la combinación no funciona, la alternativa es crear dos proyectos de Vercel (frontend estático y backend FastAPI) enlazados por URL, con CORS habilitado en la API.

### Fuentes

Consultadas el 3 de noviembre de 2026.

- [Ship a FastAPI app on Vercel](https://vercel.com/kb/guide/ship-a-fastapi-app-on-vercel)
- [Vercel Hobby Plan](https://vercel.com/docs/plans/hobby)
- [Vercel Functions Limits](https://vercel.com/docs/functions/limitations)
