// Dibujo del mapa en canvas, en dos capas:
// - Base (fija por mapa): materiales, cuadrícula y casillas bloqueadas. Se pinta
//   una vez en un canvas fuera de pantalla y se copia en cada cuadro.
// - Búsqueda (cambia en cada paso): cerradas, frontera, nodo actual, ruta e inicio.
// Así la reproducción solo vuelve a pintar lo que cambia.
import type { Cell, MapResponse, MaterialSymbol, SolveResponse } from "../api/types";
import type { AppState } from "../state/store";
import { MATERIAL_COLORS, OVERLAY } from "./palette";
import { cellAt, cellCenter, cellOrigin, fitViewport, type Viewport } from "./viewport";

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
  /** Índice de la traza actual, para obtener la frontera de cualquier paso. */
  private trace: TraceIndex | null = null;

  constructor(private readonly container: HTMLElement) {
    this.element = document.createElement("canvas");
    this.element.className = "map-canvas";
    container.append(this.element);
    const ctx = this.element.getContext("2d");
    if (!ctx) throw new Error("El navegador no soporta canvas 2D.");
    this.ctx = ctx;

    // En la capa 1 el cursor indica que se puede elegir ahí el inicio.
    this.element.addEventListener("mousemove", (event) => {
      this.element.style.cursor = this.cellAtEvent(event)?.[1] === 0 ? "pointer" : "";
    });

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

  /** Llama a `handler` con la casilla bajo cada clic dentro del mapa. */
  onCellClick(handler: (cell: Cell) => void): void {
    this.element.addEventListener("click", (event) => {
      const cell = this.cellAtEvent(event);
      if (cell) handler(cell);
    });
  }

  private cellAtEvent(event: MouseEvent): Cell | null {
    if (!this.viewport) return null;
    const rect = this.element.getBoundingClientRect();
    return cellAt(this.viewport, event.clientX - rect.left, event.clientY - rect.top);
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
    // Espacio útil del contenedor: sin su relleno (padding).
    const style = getComputedStyle(this.container);
    const padX = parseFloat(style.paddingLeft) + parseFloat(style.paddingRight);
    const padY = parseFloat(style.paddingTop) + parseFloat(style.paddingBottom);
    const top = this.container.getBoundingClientRect().top + window.scrollY;
    const availHeight =
      window.innerHeight - Math.min(top, window.innerHeight / 3) - padY - BOTTOM_MARGIN;
    const vp = fitViewport(
      map.width,
      map.height,
      this.container.clientWidth - padX,
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

      // Frontera: casillas que ya entraron y aún no se expanden, con contorno.
      if (this.trace?.solution !== solution) this.trace = indexTrace(solution, state.map!);
      drawFrontier(ctx, vp, this.trace, shown);

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

/**
 * Para cada casilla (índice y * ancho + x): en qué paso entró a la frontera y en
 * qué paso se expandió; -1 si nunca. "Paso k" = ya se reprodujeron k expansiones,
 * así que lo que empuja la expansión i entra en el paso i + 1. El inicio está en
 * la frontera desde el paso 0.
 */
interface TraceIndex {
  solution: SolveResponse;
  width: number;
  enteredAt: Int32Array;
  expandedAt: Int32Array;
  /** Casillas que alguna vez estuvieron en la frontera, para no recorrer el mapa entero. */
  touched: number[];
}

function indexTrace(solution: SolveResponse, map: MapResponse): TraceIndex {
  const width = map.width;
  const enteredAt = new Int32Array(width * map.height).fill(-1);
  const expandedAt = new Int32Array(width * map.height).fill(-1);
  const touched: number[] = [];
  const enter = (index: number, step: number) => {
    if (enteredAt[index] !== -1) return;
    enteredAt[index] = step;
    touched.push(index);
  };

  solution.expansions.forEach((e, i) => {
    if (i === 0) enter(e.y * width + e.x, 0);
    expandedAt[e.y * width + e.x] = i + 1;
    for (const [x, y] of e.pushed) enter(y * width + x, i + 1);
  });
  return { solution, width, enteredAt, expandedAt, touched };
}

/** Contorno en las casillas que están en la frontera tras `step` expansiones. */
function drawFrontier(ctx: CanvasRenderingContext2D, vp: Viewport, trace: TraceIndex, step: number): void {
  const s = vp.cell;
  ctx.strokeStyle = OVERLAY.frontier;
  ctx.lineWidth = Math.max(1, s * 0.14);
  const inset = ctx.lineWidth / 2;
  ctx.beginPath();
  for (const index of trace.touched) {
    const entered = trace.enteredAt[index]!;
    const expanded = trace.expandedAt[index]!;
    if (entered > step || (expanded !== -1 && expanded <= step)) continue;
    const [left, top] = cellOrigin(vp, index % trace.width, Math.floor(index / trace.width));
    ctx.rect(left + inset, top + inset, s - 2 * inset, s - 2 * inset);
  }
  ctx.stroke();
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
