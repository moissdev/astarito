# CLAUDE.md — Astarito: robot minero con A* (Fundamentos de IA)

## Qué es este proyecto
Agente de búsqueda para la materia Fundamentos de IA. Un robot minero recorre un corte sagital de **25 columnas × 75 capas** con batería limitada (100 %) y traza la ruta de **menor consumo** hasta una casilla adyacente a una veta de oro. Algoritmo: **A\* (Weighted A\* con w=1)** con **heurística de problema relajado**. Frontend web que reproduce la búsqueda.

Especificación completa y fuente de verdad: `docs/propuesta.md` (léela bajo demanda; no la importes con `@`). Si algo de este archivo contradice la propuesta, gana la propuesta.

## Usuario
Moisés, estudiante de último año de Ing. en Software (México). Fuerte en frontend y UI/UX. Responder en español; identificadores de código en inglés; comentarios y docstrings en español.

## Decisiones cerradas (no reabrir sin que el usuario lo pida)
**Problema**
- Estado = `(x, y)`. La batería **no** está en el estado: `batería = 100 − g(s)`.
- Acciones: `Left`, `Right`, `Down` (nunca arriba). Costo = costo de minado de la casilla destino: tierra 1, piedra 3, estalagmita 2, vacío 0. Lava y oro nunca se pisan.
- La casilla inicial no se cobra. Éxito si costo ≤ 100 (llegar a 0 % exacto cuenta).
- Inicio: cualquiera de las 25 columnas de la capa 1 (elige el usuario).
- Meta: casilla (no bloqueada) adyacente por 4 vecinos a cualquiera de las 5 casillas de oro.
- **Casillas bloqueadas**: lava, vecinas (4) de lava, y toda casilla con vacío o estalagmita directamente debajo. Así no hay caídas ≥ 2 ni se simula gravedad; las cuevas se recorren por el piso y las estalagmitas se minan de lado.
- Entorno: totalmente observable, determinista, secuencial, estático, discreto, un agente, conocido.

**Generador de mapas** (por estructuras, con semilla; determinista)
- Cuevas: capas 15–70, 3–7 de ancho × 1–3 de alto, cobertura 10 %.
- Lajas de piedra: capas 5–75, 3–8 × 1–2, cobertura 15 %.
- Estalagmitas: sobre el piso de las cuevas, capas 25–70, 35 % por casilla de piso.
- Lagos de lava: capas 35–69, 2–5 × 1–2, solo sobre tierra/piedra, cobertura 2 %.
- Oro: "+" de 5 casillas, centro en capas 71–74 y columnas 2–24 (base 1); sobrescribe cualquier material.
- Los rectángulos se recortan a casillas de tierra. Se **rechaza la semilla** si no hay ruta técnica (ignorando batería) y se regenera. La condición es igual para cualquier inicio porque la capa 1 es toda tierra.
- Coordenadas base 0, origen arriba-izquierda; capa = `y + 1`.

**Algoritmo / heurística**
- A* con w=1; UCS (h=0) es la línea base. Poda sucesores con `g + h > batería`. Cerrados con mejor g; desempate por mayor g. `battery=None` desactiva la poda (costo mínimo real).
- `h(s)` = costo exacto en el problema relajado R (solo la lava es intransitable; mismos movimientos, costos y meta). Se calcula una vez por mapa con Dijkstra inverso desde las metas (predecesores: arriba, izquierda, derecha). Admisible y consistente (pruebas en la propuesta).
- Descartados: BFS/DFS/DLS/IDS (ignoran costos), voraz (no óptimo), IDA* (ventaja de memoria irrelevante con ≤ 1,875 estados), w>1 (pierde optimalidad y la conclusión exacta de "sin ruta rentable"), suma del mínimo por fila (cota débil).

**Arquitectura**
- Backend FastAPI; núcleo Python puro en `backend/agent` (sin dependencia del framework web). Frontend Vite + TypeScript con canvas.
- API **sin estado**: el mapa se regenera desde la semilla. `POST /api/solve` devuelve la traza completa y el navegador la reproduce (sin WebSockets). Endpoints: `GET /api/health`, `GET /api/map?seed`, `POST /api/solve`.
- Despliegue en **Vercel Hobby** (gratis, uso personal/no comercial): FastAPI detectado por dependencias, `[tool.vercel] entrypoint = "backend.api:app"` en `pyproject.toml`; frontend compilado en `public/`.
- **Sin validar aún**: FastAPI + estáticos en `public/` juntos, y la Deployment Protection por defecto. Hacer un despliegue mínimo de prueba al inicio y revisarlo en ventana de incógnito. Plan B: dos proyectos Vercel con CORS.

## Estructura
Ver el árbol y los esqueletos de módulos en la sección 12 de `docs/propuesta.md`. Resumen: `backend/{api,schemas}.py`, `backend/agent/{config,materials,grid,rules,heuristic,generator,search,metrics}.py`, `tests/`, `frontend/src/{api,state,render,playback,ui,styles}`, `public/` (salida de build).

## Flujo de trabajo: checkpoints, commits y tags
El proyecto se llama **Astarito** (juego de palabras A-Star-ito); repo `astarito`. Se construye por checkpoints; cada uno es un commit con sus pruebas en verde. Trabajar **un checkpoint a la vez** y no avanzar al siguiente sin que el usuario lo indique.

| # | Commit | Contenido | Verificación |
|---|---|---|---|
| 0 | `docs: documentación inicial` | README, `CLAUDE.md`, `docs/propuesta.md`, `.gitignore` | — |
| 1 | `chore: esqueleto del proyecto` | `pyproject.toml`, `.python-version`, carpetas, pytest | `pytest` corre sin pruebas |
| 2 | `feat(api): health check mínimo` | `backend/api.py` solo con `/api/health` + `public/index.html` de prueba | **Despliegue de prueba en Vercel** |
| 3 | `feat(agent): config y materiales` | `config.py`, `materials.py` | Constantes |
| 4 | `feat(agent): mapa inmutable` | `grid.py` | Vecindad y límites |
| 5 | `feat(agent): reglas de bloqueo y sucesores` | `rules.py`, `test_rules.py` | Ver "Pruebas obligatorias" (reglas) |
| 6 | `feat(agent): heurística relajada` | `heuristic.py`, `test_heuristic.py` | Admisible, consistente, h=0 en metas |
| 7 | `feat(agent): A* con poda por batería` | `search.py` | A* = Dijkstra exacto en las 25 columnas |
| 8 | `feat(agent): generador de mapas` | `generator.py`, `test_generator.py` | Ver "Pruebas obligatorias" (generador). Puede dividirse: estructuras → estalagmitas y lava → oro y rechazo |
| 9 | `feat(agent): métricas` | `metrics.py` | Composición de la ruta |
| 10 | `feat(api): mapa y solve` | `schemas.py`, endpoints, `test_api.py` | Contrato de la API; **despliegue y prueba en producción** |
| 11 | `feat(web): cliente y estado` | `api/`, `state/`, `index.html`, Vite | Muestra el mapa en crudo; **verificar que el build llegue a `public/` en Vercel** |
| 12 | `feat(web): render del mapa` | `MapCanvas`, `palette`, `viewport` | Revisión visual |
| 13 | `feat(web): reproducción` | `player.ts` | Play, pausa, paso a paso |
| 14 | `feat(web): panel y controles` | `Controls`, `MetricsPanel`, `BatteryBar`, `Legend` | Flujo completo |
| 15 | `style(web): pulido de interfaz` | CSS y detalles | Revisión visual |
| 16 | `docs: README final` | Capturas, instrucciones, enlace al despliegue | — |

**Tags** (anotados, `git tag -a`): `v0.1-core` tras el checkpoint 9 (agente completo sin servidor); `v0.2-api` tras el 10; `v1.0` tras el 16.

**Convención de mensajes**: Conventional Commits, tipo en inglés y descripción en español (`feat(agent): agrega A* con poda por batería`). Un commit por checkpoint, sin mezclar cambios de otros. El trailer de coautoría está permitido y se agrega al final del mensaje cuando la sesión lo indique.

**Seguridad en commits, tags y push (obligatorio)**
1. Antes de cada commit: ejecutar las pruebas del checkpoint, mostrar `git status` y `git diff --staged` y **esperar la aprobación explícita del usuario**. Agregar archivos por nombre, nunca `git add -A` a ciegas.
2. Nunca versionar secretos ni archivos locales (`.env`, `.vercel/`, `node_modules/`, `__pycache__/`, `.venv/`).
3. **Nunca hacer `git push` sin autorización explícita en ese momento**; la aprobación de un commit no autoriza el push. Tampoco `--force`, `reset --hard`, reescritura de historia ni borrado de ramas o tags.
4. Crear un tag solo cuando el usuario lo pida o confirme, y empujarlo solo con su autorización.
5. Si fallan las pruebas, no commitear: explicar el fallo y proponer la corrección.

**Despliegue en Vercel (cuándo)**
- **Checkpoint 2**: primer despliegue mínimo (`/api/health` + página estática) para validar el layout FastAPI + `public/` y la Deployment Protection (revisar en ventana de incógnito). Si falla, aplicar el plan B (dos proyectos con CORS) antes de seguir.
- **Checkpoint 10**: probar `/api/map` y `/api/solve` en producción; medir el tiempo de la primera petición (arranque en frío).
- **Checkpoint 11**: decidir si `public/` se versiona o lo construye Vercel con `npm run build` (probar primero la segunda; si da problemas, versionarlo).
- **Antes de `v1.0`**: pasada completa en producción desde incógnito, escritorio y móvil.
- Los despliegues y vincular el repo a Vercel los hace el usuario o requieren su autorización; no ejecutar comandos de despliegue por cuenta propia.

## Pruebas obligatorias
- A* coincide con el Dijkstra inverso exacto para las 25 columnas de inicio en varios mapas.
- Heurística admisible y consistente; h = 0 en metas.
- Generador: mismo seed → mismo mapa; capa 1 solo tierra; cada material dentro de sus capas; estalagmitas solo sobre piso de cuevas; lava solo sobre tierra/piedra; oro = "+" válido; todo mapa aceptado tiene ruta técnica.
- Reglas: bloqueadas correctas, nunca se entra a oro/lava, ningún sucesor sube.

## Valores de referencia (aprox., de un prototipo; solo para sanity checks)
Rechazo de semillas ≈ 0.1–0.2 %; ≈ 97 % de inicios rentables; costo mínimo mediano ≈ 84–87 %; A* expande ≈ 24 % menos nodos que UCS. **No incluir estas cifras en la propuesta** (el usuario decidió dejarlas fuera). Si el generador real se desvía mucho, revisar antes de ajustar parámetros.

## Comandos
- Pruebas: `pytest` (antes de cada commit)
- API local: `uvicorn backend.api:app --reload`
- Frontend: `cd frontend && npm install && npm run dev` / `npm run build` (salida en `../public`)

## Convenciones
- Python 3.12, tipado estático, `dataclass(frozen=True)` para estructuras de datos.
- El núcleo solo usa la biblioteca estándar (`heapq`, `random`, `dataclasses`, `enum`).
- No agregar mecánicas fuera de la propuesta (recarga, subir, diagonales) sin consultarlo.
