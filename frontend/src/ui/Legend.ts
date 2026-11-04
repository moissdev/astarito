// Leyenda de materiales y de los estados de la búsqueda. Toma los colores de
// la paleta del canvas, así la leyenda nunca se desincroniza del dibujo.
import type { MaterialSymbol } from "../api/types";
import { MATERIAL_COLORS, MATERIAL_NAMES, OVERLAY, SWATCH_COLORS } from "../render/palette";

const MATERIALS: [MaterialSymbol, string][] = [
  ["E", "costo 1"],
  ["S", "costo 3"],
  ["T", "costo 2"],
  ["A", "costo 0"],
  ["L", "nunca se pisa"],
  ["G", "objetivo"],
];

/** Muestra CSS para cada estado; imita cómo se ve en el canvas. */
const STATES: [style: string, name: string, note: string][] = [
  [
    `background: repeating-linear-gradient(135deg, ${OVERLAY.blockedHatch} 0 2px, transparent 2px 5px), ${MATERIAL_COLORS.E}`,
    "Bloqueada",
    "junto a lava o sobre un hueco",
  ],
  [`background: ${OVERLAY.start}; border-radius: 50%`, "Inicio", "capa 1"],
  [`box-shadow: inset 0 0 0 2px ${OVERLAY.frontier}; background: ${MATERIAL_COLORS.E}`, "Frontera", "generada, sin expandir"],
  [`background: linear-gradient(${OVERLAY.closed}, ${OVERLAY.closed}), ${MATERIAL_COLORS.E}`, "Expandida", "conjunto cerrado"],
  [`box-shadow: inset 0 0 0 2px ${OVERLAY.current}; background: ${MATERIAL_COLORS.E}`, "Nodo actual", ""],
  [`background: ${OVERLAY.path}`, "Ruta", "menor consumo"],
];

export class Legend {
  readonly element: HTMLElement;

  constructor() {
    this.element = document.createElement("section");
    this.element.className = "panel legend";
    this.element.setAttribute("aria-label", "Leyenda");
    const item = (style: string, name: string, note: string) => `
      <li>
        <span class="swatch" style="${style}"></span>
        <span>${name}${note ? ` <small>${note}</small>` : ""}</span>
      </li>`;
    this.element.innerHTML = `
      <h2>Leyenda</h2>
      <ul class="legend-list">
        ${MATERIALS.map(([m, note]) => item(`background: ${SWATCH_COLORS[m]}`, MATERIAL_NAMES[m], note)).join("")}
      </ul>
      <ul class="legend-list">
        ${STATES.map(([style, name, note]) => item(style, name, note)).join("")}
      </ul>
    `;
  }
}
