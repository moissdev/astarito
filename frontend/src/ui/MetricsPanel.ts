// Panel de métricas: veredicto, costo, batería restante, expansiones,
// composición de la ruta y el nodo que se expande en el paso actual.
// Durante la reproducción se actualiza en cada cuadro, así que no se repinta
// entero: la estructura se arma una vez y solo se cambia el texto que varía.
import type { MaterialSymbol, MinedMaterial, SolveResponse } from "../api/types";
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

type Verdict = { text: string; tone: "ok" | "bad" | "searching" };

export class MetricsPanel {
  readonly element: HTMLElement;
  private readonly hint: HTMLElement;
  private readonly result: HTMLElement;
  private readonly verdict: HTMLElement;
  private readonly list: HTMLDListElement;
  private readonly composition: HTMLElement;
  private readonly battery = new BatteryBar();

  /** Etiquetas de las filas actuales y sus celdas de valor, para reusarlas. */
  private rowKeys = "";
  private values: HTMLElement[] = [];
  /** Solución con la que se armó la composición (null si está oculta). */
  private compositionFor: SolveResponse | null = null;

  constructor() {
    this.element = document.createElement("section");
    this.element.className = "panel metrics";
    this.element.setAttribute("aria-label", "Resultado");
    this.element.innerHTML = `
      <h2>Resultado</h2>
      <p class="hint">Elige una columna de inicio y presiona Resolver para ver la búsqueda.</p>
      <div class="metrics-result" hidden>
        <p class="verdict"></p>
        <dl></dl>
        <div class="metrics-composition" hidden></div>
      </div>
    `;
    const $ = <T extends Element>(selector: string) => this.element.querySelector<T>(selector)!;
    this.hint = $(".hint");
    this.result = $(".metrics-result");
    this.verdict = $(".verdict");
    this.list = $("dl");
    this.composition = $(".metrics-composition");
    this.result.prepend(this.battery.element);
  }

  update(state: AppState): void {
    const { solution, startX, step } = state;
    const visible = solution !== null && startX !== null;
    this.hint.hidden = visible;
    this.result.hidden = !visible;
    if (!visible) {
      this.compositionFor = null;
      return;
    }
    this.battery.update(state);

    const total = solution.expansions.length;
    const done = step >= total;
    const verdict = verdictOf(solution, done);
    setText(this.verdict, verdict.text);
    this.verdict.dataset.tone = verdict.tone;

    this.renderRows(rowsOf(solution, startX, step, done));
    this.renderComposition(done && solution.profitable ? solution : null);
  }

  /** Reusa las filas si las etiquetas no cambiaron; si cambiaron, las rearma. */
  private renderRows(rows: [string, string][]): void {
    const keys = rows.map(([label]) => label).join("|");
    if (keys !== this.rowKeys) {
      this.list.replaceChildren();
      this.values = rows.map(([label]) => {
        const dt = document.createElement("dt");
        const dd = document.createElement("dd");
        dt.textContent = label;
        this.list.append(dt, dd);
        return dd;
      });
      this.rowKeys = keys;
    }
    rows.forEach(([, value], i) => setText(this.values[i]!, value));
  }

  /** La composición solo cambia con la solución, no en cada paso. */
  private renderComposition(solution: SolveResponse | null): void {
    if (solution === this.compositionFor) return;
    this.compositionFor = solution;
    this.composition.hidden = solution === null;
    if (!solution) return;
    this.composition.innerHTML = `
      <h3>Composición de la ruta</h3>
      <ul class="composition">${MINED.map(
        ([key, symbol]) => `
        <li>
          <span class="swatch" style="background:${SWATCH_COLORS[symbol]}"></span>
          ${MATERIAL_NAMES[symbol]}
          <span class="count">${solution.composition[key]}</span>
        </li>`,
      ).join("")}</ul>
    `;
  }
}

/** El veredicto se muestra al terminar la reproducción, para no adelantar el final. */
function verdictOf(solution: SolveResponse, done: boolean): Verdict {
  if (!done) return { text: "Buscando…", tone: "searching" };
  if (solution.profitable) return { text: "Ruta rentable", tone: "ok" };
  if (solution.min_cost === null) return { text: "Sin ruta técnica", tone: "bad" };
  return { text: "Sin ruta rentable", tone: "bad" };
}

function rowsOf(
  solution: SolveResponse,
  startX: number,
  step: number,
  done: boolean,
): [string, string][] {
  const total = solution.expansions.length;
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
  const current = step > 0 ? solution.expansions[step - 1] : undefined;
  if (current) {
    rows.push(
      ["Nodo actual", `columna ${current.x + 1}, capa ${current.y + 1}`],
      ["g · h · f", `${current.g} · ${current.h} · ${current.f}`],
    );
  }
  return rows;
}

/** Cambia el texto solo si es distinto, para no tocar el DOM sin necesidad. */
function setText(element: HTMLElement, text: string): void {
  if (element.textContent !== text) element.textContent = text;
}
