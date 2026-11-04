// Controles: semilla y mapa nuevo, elección del inicio y reproducción.
// También instala los atajos de teclado de la reproducción.
import {
  SPEEDS,
  changeSpeed,
  play,
  seek,
  stepBy,
  toEnd,
  toStart,
  togglePlay,
} from "../playback/player";
import { getState, loadMap, solveFrom, type AppState } from "../state/store";

/** Resuelve desde una columna de la capa 1 y reproduce la búsqueda al llegar. */
export function solveAndPlay(startX: number): void {
  void solveFrom(startX).then(play);
}

const STATUS_TEXT: Record<AppState["status"], string> = {
  idle: "",
  "loading-map": "Generando mapa…",
  ready: "",
  solving: "Buscando ruta…",
  error: "",
};

export class Controls {
  readonly element: HTMLElement;
  private readonly seedInput: HTMLInputElement;
  private readonly startSelect: HTMLSelectElement;
  private readonly playback: HTMLElement;
  private readonly toggleButton: HTMLButtonElement;
  private readonly speedSelect: HTMLSelectElement;
  private readonly stepInput: HTMLInputElement;
  private readonly stepOut: HTMLOutputElement;
  private readonly status: HTMLParagraphElement;

  constructor() {
    this.element = document.createElement("section");
    this.element.className = "panel controls";
    this.element.setAttribute("aria-label", "Controles");
    this.element.innerHTML = `
      <form class="field" data-role="map-form">
        <label for="seed">Semilla</label>
        <div class="row">
          <input id="seed" type="number" min="0" step="1" inputmode="numeric" />
          <button type="submit">Cargar</button>
          <button type="button" data-role="random">Aleatorio</button>
        </div>
      </form>
      <form class="field" data-role="solve-form">
        <label for="start">Columna de inicio (capa 1)</label>
        <div class="row">
          <select id="start"></select>
          <button type="submit" class="primary">Resolver</button>
        </div>
        <p class="hint">También puedes hacer clic en la fila superior del mapa.</p>
      </form>
      <div class="field" data-role="playback" hidden>
        <span class="label">Reproducción</span>
        <div class="row">
          <button type="button" data-action="to-start" title="Ir al inicio (Inicio)" aria-label="Ir al inicio">⏮</button>
          <button type="button" data-action="back" title="Paso atrás (←)" aria-label="Paso atrás">◀</button>
          <button type="button" data-action="toggle" title="Reproducir o pausar (Espacio)" aria-label="Reproducir">▶</button>
          <button type="button" data-action="forward" title="Paso adelante (→)" aria-label="Paso adelante">▶|</button>
          <button type="button" data-action="to-end" title="Ir al final (Fin)" aria-label="Ir al final">⏭</button>
          <select data-role="speed" aria-label="Velocidad"></select>
        </div>
        <div class="row">
          <input type="range" min="0" value="0" data-role="step" aria-label="Paso de la reproducción" />
          <output data-role="step-out"></output>
        </div>
      </div>
      <p class="status" role="status"></p>
    `;

    const $ = <T extends Element>(selector: string) => this.element.querySelector<T>(selector)!;
    this.seedInput = $("#seed");
    this.startSelect = $("#start");
    this.playback = $("[data-role=playback]");
    this.toggleButton = $("[data-action=toggle]");
    this.speedSelect = $("[data-role=speed]");
    this.stepInput = $("[data-role=step]");
    this.stepOut = $("[data-role=step-out]");
    this.status = $(".status");

    // Columnas en base 1 para el usuario, base 0 para la API.
    this.startSelect.innerHTML = Array.from(
      { length: 25 },
      (_, x) => `<option value="${x}">${x + 1}</option>`,
    ).join("");
    this.speedSelect.innerHTML = SPEEDS.map(
      (v) => `<option value="${v}">${v} pasos/s</option>`,
    ).join("");

    $("[data-role=map-form]").addEventListener("submit", (event) => {
      event.preventDefault();
      const seed = this.seedInput.valueAsNumber;
      void loadMap(Number.isInteger(seed) && seed >= 0 ? seed : undefined);
    });
    $("[data-role=random]").addEventListener("click", () => void loadMap());
    $("[data-role=solve-form]").addEventListener("submit", (event) => {
      event.preventDefault();
      solveAndPlay(Number(this.startSelect.value));
    });

    const actions: Record<string, () => void> = {
      "to-start": toStart,
      back: () => stepBy(-1),
      toggle: togglePlay,
      forward: () => stepBy(1),
      "to-end": toEnd,
    };
    for (const button of this.element.querySelectorAll<HTMLButtonElement>("[data-action]")) {
      button.addEventListener("click", actions[button.dataset.action!]!);
    }
    this.speedSelect.addEventListener("change", () => changeSpeed(Number(this.speedSelect.value)));
    this.stepInput.addEventListener("input", () => seek(this.stepInput.valueAsNumber));

    document.addEventListener("keydown", onShortcut);
  }

  update(state: AppState): void {
    this.status.textContent = state.error ? `Error: ${state.error}` : STATUS_TEXT[state.status];
    this.status.classList.toggle("error", state.error !== null);

    const busy = state.status === "loading-map" || state.status === "solving";
    for (const control of this.element.querySelectorAll<HTMLButtonElement | HTMLSelectElement>(
      "button, select",
    )) {
      control.disabled = busy;
    }
    this.startSelect.disabled ||= !state.map;

    if (state.map && document.activeElement !== this.seedInput) {
      this.seedInput.value = String(state.map.seed);
    }
    if (state.startX !== null) this.startSelect.value = String(state.startX);

    const total = state.solution?.expansions.length ?? 0;
    this.playback.hidden = total === 0;
    this.toggleButton.textContent = state.playing ? "⏸" : "▶";
    this.toggleButton.setAttribute("aria-label", state.playing ? "Pausar" : "Reproducir");
    this.speedSelect.value = String(state.speed);
    this.stepInput.max = String(total);
    this.stepInput.value = String(state.step);
    this.stepOut.textContent = `${state.step} / ${total}`;
  }
}

/** Atajos de la reproducción; no actúan mientras se escribe en un campo. */
function onShortcut(event: KeyboardEvent): void {
  if (event.altKey || event.ctrlKey || event.metaKey) return;
  // El objetivo puede no ser un elemento (p. ej. el propio documento).
  const target = event.target instanceof Element ? event.target : null;
  if (target?.closest("input, select, textarea")) return;
  // Sobre un botón, Espacio ya lo activa por sí solo; no se duplica la acción.
  if (event.key === " " && target?.closest("button")) return;
  if (!getState().solution?.expansions.length) return;

  const handlers: Record<string, () => void> = {
    " ": togglePlay,
    ArrowLeft: () => stepBy(-1),
    ArrowRight: () => stepBy(1),
    Home: toStart,
    End: toEnd,
  };
  const handler = handlers[event.key];
  if (!handler) return;
  event.preventDefault();
  handler();
}
