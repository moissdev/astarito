// Panel de métricas: veredicto, costo, batería restante, expansiones,
// composición de la ruta y el nodo que se expande en el paso actual.
import type { MaterialSymbol, MinedMaterial } from "../api/types";
import { MATERIAL_NAMES, SWATCH_COLORS } from "../render/palette";
import type { AppState } from "../state/store";
import { BatteryBar } from "./BatteryBar";

/** Orden y símbolo de los materiales que aparecen en `composition`. */
const MINED: [MinedMaterial, MaterialSymbol][] = [
  ["earth", "E"],
  ["stone", "S"],
  ["stalagmite", "T"],
  ["empty", "A"],
];

export class MetricsPanel {
  readonly element: HTMLElement;
  private readonly body: HTMLElement;
  private readonly battery = new BatteryBar();

  constructor() {
    this.element = document.createElement("section");
    this.element.className = "panel metrics";
    this.element.setAttribute("aria-label", "Resultado");
    this.element.innerHTML = `<h2>Resultado</h2><div class="metrics-body"></div>`;
    this.body = this.element.querySelector(".metrics-body")!;
    this.element.insertBefore(this.battery.element, this.body);
  }

  update(state: AppState): void {
    const { solution, startX, step } = state;
    this.battery.element.hidden = !solution;
    if (!solution || startX === null) {
      this.body.innerHTML = `<p class="hint">Elige una columna de inicio y presiona Resolver para ver la búsqueda.</p>`;
      return;
    }
    this.battery.update(state);

    const total = solution.expansions.length;
    const done = step >= total;
    const current = step > 0 ? solution.expansions[step - 1] : undefined;

    // El veredicto se muestra al terminar la reproducción, para no adelantar el final.
    const verdict = !done
      ? `<p class="verdict searching">Buscando…</p>`
      : solution.profitable
        ? `<p class="verdict ok">Ruta rentable</p>`
        : solution.min_cost === null
          ? `<p class="verdict bad">Sin ruta técnica</p>`
          : `<p class="verdict bad">Sin ruta rentable</p>`;

    const rows: [string, string][] = [["Inicio", `columna ${startX + 1}, capa 1`]];
    if (done && solution.profitable) {
      rows.push(
        ["Costo de la ruta", `${solution.cost} %`],
        ["Batería restante", `${solution.battery_left} %`],
        ["Movimientos", String(solution.path.length - 1)],
      );
    }
    if (done && !solution.profitable && solution.min_cost !== null) {
      rows.push(["Costo mínimo real", `${solution.min_cost} % (supera la batería)`]);
    }
    rows.push(["Nodos expandidos", `${Math.min(step, total)} de ${solution.expanded}`]);
    if (current) {
      rows.push([
        "Nodo actual",
        `columna ${current.x + 1}, capa ${current.y + 1} · g ${current.g} · h ${current.h} · f ${current.f}`,
      ]);
    }

    const composition =
      done && solution.profitable
        ? `<h3>Composición de la ruta</h3>
           <ul class="composition">${MINED.map(
             ([key, symbol]) => `
             <li>
               <span class="swatch" style="background:${SWATCH_COLORS[symbol]}"></span>
               ${MATERIAL_NAMES[symbol]}
               <span class="count">${solution.composition[key]}</span>
             </li>`,
           ).join("")}</ul>`
        : "";

    this.body.innerHTML = `
      ${verdict}
      <dl>${rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("")}</dl>
      ${composition}
    `;
  }
}
