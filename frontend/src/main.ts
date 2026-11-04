// Arranque. Vista provisional: controles mínimos, resumen en texto y el mapa en
// canvas. El deslizador de pasos sirve para revisar el dibujo de la búsqueda
// mientras llega la reproducción (checkpoint 13); los controles y paneles
// definitivos llegan en el checkpoint 14.
import "./styles/main.css";
import { MapCanvas } from "./render/MapCanvas";
import { getState, loadMap, setStep, solveFrom, subscribe, type AppState } from "./state/store";

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
  <label class="row" id="step-row" hidden>
    Paso <input id="step" type="range" min="0" value="0" />
    <output id="step-out"></output>
  </label>
  <p id="status" role="status"></p>
  <pre id="summary"></pre>
  <div id="map" class="map-frame" role="img" aria-label="Mapa del corte sagital"></div>
`;

const seedInput = app.querySelector<HTMLInputElement>("#seed")!;
const startSelect = app.querySelector<HTMLSelectElement>("#start")!;
const stepRow = app.querySelector<HTMLLabelElement>("#step-row")!;
const stepInput = app.querySelector<HTMLInputElement>("#step")!;
const stepOut = app.querySelector<HTMLOutputElement>("#step-out")!;
const statusLine = app.querySelector<HTMLParagraphElement>("#status")!;
const summaryBlock = app.querySelector<HTMLPreElement>("#summary")!;
const mapCanvas = new MapCanvas(app.querySelector<HTMLDivElement>("#map")!);

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
  // Sin reproducción todavía: al terminar se muestra la búsqueda completa.
  void solveFrom(Number(startSelect.value)).then(() => setStep(Infinity));
});
stepInput.addEventListener("input", () => setStep(stepInput.valueAsNumber));

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

  const total = state.solution?.expansions.length ?? 0;
  stepRow.hidden = total === 0;
  stepInput.max = String(total);
  stepInput.value = String(state.step);
  stepOut.textContent = `${state.step} / ${total}`;

  summaryBlock.textContent = state.solution ? summaryText(state) : "";
  mapCanvas.update(state);
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
