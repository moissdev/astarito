// Arranque: arma el layout, monta los componentes y los conecta al store.
// Cada componente expone `element` y, si cambia con el estado, `update(state)`.
import "./styles/main.css";
import "./playback/player";
import { MapCanvas } from "./render/MapCanvas";
import { getState, loadMap, subscribe } from "./state/store";
import { Controls, solveAndPlay } from "./ui/Controls";
import { Legend } from "./ui/Legend";
import { MetricsPanel } from "./ui/MetricsPanel";

const app = document.querySelector<HTMLDivElement>("#app")!;
app.innerHTML = `
  <header class="app-header">
    <svg class="logo" viewBox="0 0 3 3" aria-hidden="true">
      <path d="M1 0h1v1h1v1H2v1H1V2H0V1h1z" />
    </svg>
    <div>
      <h1>Astarito</h1>
      <p>Un robot minero busca con A* la ruta de menor consumo hasta la veta de oro.</p>
    </div>
  </header>
  <main class="layout">
    <div class="map-frame" role="img" aria-label="Mapa del corte sagital, 25 columnas por 75 capas"></div>
  </main>
  <footer class="app-footer">
    Fundamentos de IA · A* (w = 1) con heurística de problema relajado ·
    la semilla en la URL permite compartir un mapa.
  </footer>
`;

// Los paneles son hijos directos de la cuadrícula: así el CSS puede ordenarlos
// distinto en escritorio (barra lateral) y en móvil (mapa justo tras los controles).
const layout = app.querySelector<HTMLElement>(".layout")!;
const controls = new Controls();
const metrics = new MetricsPanel();
const legend = new Legend();
layout.prepend(controls.element, metrics.element, legend.element);

const mapCanvas = new MapCanvas(app.querySelector<HTMLDivElement>(".map-frame")!);
// Clic en la capa 1: elige esa columna como inicio y resuelve.
mapCanvas.onCellClick(([x, y]) => {
  const { map, status } = getState();
  const busy = status === "loading-map" || status === "solving";
  if (y === 0 && map && !busy) solveAndPlay(x);
});

subscribe((state) => {
  controls.update(state);
  metrics.update(state);
  mapCanvas.update(state);
});

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
