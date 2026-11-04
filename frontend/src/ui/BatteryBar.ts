// Barra de batería durante la reproducción. La batería no es parte del estado
// del agente: en cada paso vale 100 − g del nodo que se está expandiendo.
// Al terminar una ruta rentable, el último nodo es la meta y g es el costo final.
import type { AppState } from "../state/store";

const BATTERY = 100;
/** Umbrales (en %) para pasar de verde a ámbar y de ámbar a rojo. */
const WARN_AT = 50;
const DANGER_AT = 20;

export class BatteryBar {
  readonly element: HTMLElement;
  private readonly meter: HTMLElement;
  private readonly fill: HTMLElement;
  private readonly value: HTMLElement;

  constructor() {
    this.element = document.createElement("div");
    this.element.className = "battery";
    this.element.innerHTML = `
      <div class="battery-head">
        <span class="label">Batería en el nodo actual</span>
        <span class="battery-value"></span>
      </div>
      <div class="battery-track" role="meter" aria-label="Batería" aria-valuemin="0" aria-valuemax="${BATTERY}">
        <div class="battery-fill"></div>
      </div>
    `;
    this.meter = this.element.querySelector(".battery-track")!;
    this.fill = this.element.querySelector(".battery-fill")!;
    this.value = this.element.querySelector(".battery-value")!;
  }

  update({ solution, step }: AppState): void {
    const current = solution && step > 0 ? solution.expansions[step - 1] : undefined;
    const battery = BATTERY - (current?.g ?? 0);
    const level = battery <= DANGER_AT ? "danger" : battery <= WARN_AT ? "warn" : "ok";

    this.fill.style.width = `${Math.max(0, battery)}%`;
    this.fill.dataset.level = level;
    this.value.textContent = `${battery} %`;
    this.meter.setAttribute("aria-valuenow", String(battery));
    this.meter.setAttribute("aria-valuetext", `${battery} por ciento`);
  }
}
