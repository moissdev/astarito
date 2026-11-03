// Arranque. Vista provisional del checkpoint 11: muestra el mapa en crudo (un
// carácter por casilla) para comprobar el cliente y el estado de punta a punta.
// El canvas, la reproducción y los controles definitivos llegan en los
// checkpoints 12 a 14.
import "./styles/main.css";
import { getState, loadMap, solveFrom, subscribe, type AppState } from "./state/store";

const app = document.querySelector<HTMLDivElement>("#app")!;
app.innerHTML = `
  <h1>Astarito</h1>
  <form id="map-form" class="row">
    <label>Semilla <input id="seed" type="number" min="0" step="1" inputmode="numeric" /></label>
    <button type="submit">Cargar</button>
    <button type="button" id="random">Mapa aleatorio</button>
  </form>
  <form id="solve-form" class="row">
    <label>Columna de inicio <select id="start"></select></label>
    <button type="submit">Resolver</button>
  </form>
  <p id="status" role="status"></p>
  <pre id="summary"></pre>
  <pre id="grid" aria-label="Mapa en crudo"></pre>
`;

const seedInput = app.querySelector<HTMLInputElement>("#seed")!;
const startSelect = app.querySelector<HTMLSelectElement>("#start")!;
const statusLine = app.querySelector<HTMLParagraphElement>("#status")!;
const summaryBlock = app.querySelector<HTMLPreElement>("#summary")!;
const gridBlock = app.querySelector<HTMLPreElement>("#grid")!;

// Columnas en base 1 para el usuario, base 0 para la API.
startSelect.innerHTML = Array.from(
  { length: 25 },
  (_, x) => `<option value="${x}">${x + 1}</option>`,
).join("");

app.querySelector("#map-form")!.addEventListener("submit", (event) => {
  event.preventDefault();
  const seed = seedInput.valueAsNumber;
  void loadMap(Number.isInteger(seed) && seed >= 0 ? seed : undefined);
});
app.querySelector("#random")!.addEventListener("click", () => void loadMap());
app.querySelector("#solve-form")!.addEventListener("submit", (event) => {
  event.preventDefault();
  void solveFrom(Number(startSelect.value));
});

const STATUS_TEXT: Record<AppState["status"], string> = {
  idle: "",
  "loading-map": "Generando mapa…",
  ready: "",
  solving: "Buscando ruta…",
  error: "",
};

subscribe(render);

function render(state: AppState): void {
  statusLine.textContent = state.error ? `Error: ${state.error}` : STATUS_TEXT[state.status];
  const busy = state.status === "loading-map" || state.status === "solving";
  for (const button of app.querySelectorAll("button")) button.disabled = busy;
  startSelect.disabled = busy || !state.map;

  if (state.map && document.activeElement !== seedInput) {
    seedInput.value = String(state.map.seed);
  }
  gridBlock.textContent = state.map ? rawGrid(state) : "";
  summaryBlock.textContent = state.solution ? summaryText(state) : "";
}

/** Una línea por capa; la ruta se marca con "*" y el inicio con "@". */
function rawGrid({ map, solution }: AppState): string {
  if (!map) return "";
  const rows = map.grid.map((row) => row.split(""));
  for (const [x, y] of solution?.path ?? []) rows[y]![x] = "*";
  const start = solution?.path[0];
  if (start) rows[start[1]]![start[0]] = "@";
  return rows.map((row, y) => `${String(y + 1).padStart(2)} ${row.join("")}`).join("\n");
}

function summaryText({ solution, startX }: AppState): string {
  if (!solution || startX === null) return "";
  const lines = [
    `Inicio: columna ${startX + 1}`,
    solution.profitable
      ? `Ruta rentable: costo ${solution.cost} %, batería restante ${solution.battery_left} %`
      : `Sin ruta rentable. Costo mínimo real: ${solution.min_cost ?? "sin ruta técnica"}`,
    `Nodos expandidos: ${solution.expanded}`,
    `Composición: ${JSON.stringify(solution.composition)}`,
  ];
  return lines.join("\n");
}

// Semilla inicial desde ?seed=… para poder compartir un mapa concreto.
// Ojo: Number(null) es 0, por eso se revisa primero que el parámetro exista.
const rawSeed = new URLSearchParams(location.search).get("seed");
const urlSeed = rawSeed === null || rawSeed === "" ? NaN : Number(rawSeed);
void loadMap(Number.isInteger(urlSeed) && urlSeed >= 0 ? urlSeed : undefined);
// Mantiene la URL sincronizada con la semilla mostrada.
subscribe(({ map }) => {
  if (map && getState().status === "ready") {
    history.replaceState(null, "", `?seed=${map.seed}`);
  }
});
