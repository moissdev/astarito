// Dibujo del mapa en canvas, en dos capas:
// - Base (fija por mapa): materiales, cuadrícula y casillas bloqueadas. Se pinta
//   una vez en un canvas fuera de pantalla y se copia en cada cuadro.
// - Búsqueda (cambia en cada paso): casillas cerradas, nodo actual, ruta e inicio.
// Así la reproducción solo vuelve a pintar lo que cambia.
import type { Cell, MapResponse, MaterialSymbol } from "../api/types";
import type { AppState } from "../state/store";
import { MATERIAL_COLORS, OVERLAY } from "./palette";
import { cellCenter, cellOrigin, fitViewport, type Viewport } from "./viewport";

/** Margen inferior que se deja libre al ajustar el mapa a la altura de la ventana. */
const BOTTOM_MARGIN = 16;
/** Tamaño de casilla a partir del cual se dibuja la cuadrícula. */
const GRID_MIN_CELL = 10;

export class MapCanvas {
  readonly element: HTMLCanvasElement;
  private readonly ctx: CanvasRenderingContext2D;
  private viewport: Viewport | null = null;
  private state: AppState | null = null;
  /** Capa base ya pintada y la clave (mapa + escala) con que se pintó. */
  private base: HTMLCanvasElement | null = null;
  private baseKey = "";

  constructor(private readonly container: HTMLElement) {
    this.element = document.createElement("canvas");
    this.element.className = "map-canvas";
    container.append(this.element);
    const ctx = this.element.getContext("2d");
    if (!ctx) throw new Error("El navegador no soporta canvas 2D.");
    this.ctx = ctx;

    const relayout = () => this.layout();
    new ResizeObserver(relayout).observe(container);
    window.addEventListener("resize", relayout);
  }

  /** Recibe el estado de la aplicación y vuelve a dibujar. */
  update(state: AppState): void {
    const mapChanged = state.map !== this.state?.map;
    this.state = state;
    if (mapChanged) this.layout();
    else this.draw();
  }

  /** Recalcula la escala según el espacio disponible y redimensiona el canvas. */
  private layout(): void {
    const map = this.state?.map;
    if (!map) {
      this.viewport = null;
      this.element.hidden = true;
      return;
    }
    this.element.hidden = false;
    const top = this.container.getBoundingClientRect().top + window.scrollY;
    const availHeight = window.innerHeight - Math.min(top, window.innerHeight / 3) - BOTTOM_MARGIN;
    const vp = fitViewport(
      map.width,
      map.height,
      this.container.clientWidth,
      availHeight,
      window.devicePixelRatio || 1,
    );
    this.viewport = vp;

    this.element.style.width = `${vp.width}px`;
    this.element.style.height = `${vp.height}px`;
    this.element.width = Math.round(vp.width * vp.dpr);
    this.element.height = Math.round(vp.height * vp.dpr);
    this.draw();
  }

  private draw(): void {
    const { viewport: vp, state } = this;
    if (!vp || !state?.map) return;
    const ctx = this.ctx;

    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, this.element.width, this.element.height);
    ctx.drawImage(this.baseLayer(state.map, vp), 0, 0);

    ctx.setTransform(vp.dpr, 0, 0, vp.dpr, 0, 0);
    this.drawSearch(ctx, vp, state);
  }

  /** Devuelve la capa base, repintándola solo si cambió el mapa o la escala. */
  private baseLayer(map: MapResponse, vp: Viewport): HTMLCanvasElement {
    const key = `${map.seed}:${vp.cell}:${vp.dpr}`;
    if (this.base && this.baseKey === key) return this.base;

    const canvas = this.base ?? document.createElement("canvas");
    canvas.width = this.element.width;
    canvas.height = this.element.height;
    const ctx = canvas.getContext("2d")!;
    ctx.setTransform(vp.dpr, 0, 0, vp.dpr, 0, 0);
    drawBase(ctx, vp, map);

    this.base = canvas;
    this.baseKey = key;
    return canvas;
  }

  /** Capa de la búsqueda hasta el paso actual de la reproducción. */
  private drawSearch(ctx: CanvasRenderingContext2D, vp: Viewport, state: AppState): void {
    const { solution, step, startX } = state;
    const s = vp.cell;

    if (solution) {
      const expansions = solution.expansions;
      const shown = Math.min(step, expansions.length);

      // Cerrados: todo lo expandido antes del paso actual.
      ctx.fillStyle = OVERLAY.closed;
      for (let i = 0; i < shown - 1; i++) {
        const e = expansions[i]!;
        const [left, top] = cellOrigin(vp, e.x, e.y);
        ctx.fillRect(left, top, s, s);
      }

      // Nodo actual: el último expandido, con contorno.
      const current = shown > 0 ? expansions[shown - 1] : undefined;
      if (current) {
        const [left, top] = cellOrigin(vp, current.x, current.y);
        ctx.fillStyle = OVERLAY.closed;
        ctx.fillRect(left, top, s, s);
        ctx.strokeStyle = OVERLAY.current;
        ctx.lineWidth = Math.max(1.5, s * 0.15);
        const inset = ctx.lineWidth / 2;
        ctx.strokeRect(left + inset, top + inset, s - 2 * inset, s - 2 * inset);
      }

      // Ruta: solo cuando la reproducción terminó.
      if (shown === expansions.length && solution.path.length > 1) {
        drawPath(ctx, vp, solution.path);
      }
    }

    if (startX !== null) {
      const [cx, cy] = cellCenter(vp, startX, 0);
      ctx.beginPath();
      ctx.arc(cx, cy, s * 0.32, 0, Math.PI * 2);
      ctx.fillStyle = OVERLAY.start;
      ctx.fill();
      ctx.lineWidth = Math.max(1, s * 0.1);
      ctx.strokeStyle = OVERLAY.pathOutline;
      ctx.stroke();
    }
  }
}

/** Materiales, cuadrícula y rayado de bloqueadas. */
function drawBase(ctx: CanvasRenderingContext2D, vp: Viewport, map: MapResponse): void {
  const s = vp.cell;

  for (let y = 0; y < map.height; y++) {
    const row = map.grid[y]!;
    for (let x = 0; x < map.width; x++) {
      const material = row[x] as MaterialSymbol;
      const [left, top] = cellOrigin(vp, x, y);
      ctx.fillStyle = MATERIAL_COLORS[material];
      ctx.fillRect(left, top, s, s);
      if (material === "T") drawStalagmite(ctx, left, top, s);
      if (material === "G") drawGoldShine(ctx, left, top, s);
    }
  }

  // Cuadrícula: líneas finas en los bordes de cada casilla. Con casillas chicas
  // solo agregan ruido, así que se omiten.
  if (s >= GRID_MIN_CELL) drawGrid(ctx, vp, map);

  // Bloqueadas: rayado diagonal. La lava no se raya; su color ya la distingue.
  ctx.strokeStyle = OVERLAY.blockedHatch;
  ctx.lineWidth = Math.max(1, s * 0.12);
  ctx.beginPath();
  for (let y = 0; y < map.height; y++) {
    const row = map.blocked[y]!;
    for (let x = 0; x < map.width; x++) {
      if (row[x] !== "1" || map.grid[y]![x] === "L") continue;
      const [left, top] = cellOrigin(vp, x, y);
      ctx.moveTo(left, top + s / 2);
      ctx.lineTo(left + s / 2, top);
      ctx.moveTo(left, top + s);
      ctx.lineTo(left + s, top);
      ctx.moveTo(left + s / 2, top + s);
      ctx.lineTo(left + s, top + s / 2);
    }
  }
  ctx.stroke();
}

/** Líneas finas en los bordes de cada casilla. */
function drawGrid(ctx: CanvasRenderingContext2D, vp: Viewport, map: MapResponse): void {
  const s = vp.cell;
  ctx.strokeStyle = OVERLAY.gridLine;
  ctx.lineWidth = 1 / vp.dpr;
  ctx.beginPath();
  for (let x = 1; x < map.width; x++) {
    ctx.moveTo(x * s, 0);
    ctx.lineTo(x * s, vp.height);
  }
  for (let y = 1; y < map.height; y++) {
    ctx.moveTo(0, y * s);
    ctx.lineTo(vp.width, y * s);
  }
  ctx.stroke();
}

/** Punta triangular que sube desde el piso de la casilla. */
function drawStalagmite(ctx: CanvasRenderingContext2D, left: number, top: number, s: number): void {
  ctx.fillStyle = OVERLAY.stalagmite;
  ctx.beginPath();
  ctx.moveTo(left + s * 0.2, top + s);
  ctx.lineTo(left + s * 0.5, top + s * 0.15);
  ctx.lineTo(left + s * 0.8, top + s);
  ctx.closePath();
  ctx.fill();
}

/** Destello pequeño para que el oro se lea como pepita y no como color plano. */
function drawGoldShine(ctx: CanvasRenderingContext2D, left: number, top: number, s: number): void {
  ctx.fillStyle = OVERLAY.goldShine;
  ctx.fillRect(left + s * 0.2, top + s * 0.2, s * 0.25, s * 0.25);
}

/** Línea por los centros de las casillas de la ruta, con borde oscuro. */
function drawPath(ctx: CanvasRenderingContext2D, vp: Viewport, path: Cell[]): void {
  ctx.beginPath();
  path.forEach(([x, y], i) => {
    const [cx, cy] = cellCenter(vp, x, y);
    if (i === 0) ctx.moveTo(cx, cy);
    else ctx.lineTo(cx, cy);
  });
  ctx.lineJoin = "round";
  ctx.lineCap = "round";
  ctx.strokeStyle = OVERLAY.pathOutline;
  ctx.lineWidth = vp.cell * 0.45;
  ctx.stroke();
  ctx.strokeStyle = OVERLAY.path;
  ctx.lineWidth = vp.cell * 0.28;
  ctx.stroke();
}
