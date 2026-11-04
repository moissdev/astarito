// Reproducción de la traza: play, pausa, paso a paso y velocidad.
// El estado (paso, playing, speed) vive en el store; este módulo solo mueve el
// paso en el tiempo con requestAnimationFrame. Así cualquier vista que lea el
// store (canvas, deslizador, panel) se mantiene sincronizada sin conocer al player.
import { getState, setPlaying, setSpeed, setStep, subscribe } from "../state/store";

/** Velocidades ofrecidas, en expansiones por segundo. */
export const SPEEDS = [10, 30, 60, 150, 400] as const;

/** Tope de tiempo por cuadro: tras una pestaña en segundo plano no se salta de golpe. */
const MAX_FRAME_SECONDS = 0.1;

let frameId: number | null = null;
let lastTime: number | null = null;
/** Fracción de paso acumulada entre cuadros (a 10 pasos/s, un paso cada ~6 cuadros). */
let carry = 0;

/** Número de expansiones de la traza actual (0 si no hay solución). */
function total(): number {
  return getState().solution?.expansions.length ?? 0;
}

/** Inicia la reproducción; si ya estaba al final, vuelve a empezar. */
export function play(): void {
  if (total() === 0) return;
  if (getState().step >= total()) setStep(0);
  setPlaying(true);
}

export function pause(): void {
  setPlaying(false);
}

export function togglePlay(): void {
  if (getState().playing) pause();
  else play();
}

/** Avanza o retrocede un paso; detiene la reproducción automática. */
export function stepBy(delta: number): void {
  pause();
  setStep(getState().step + delta);
}

/** Salta a un paso concreto (deslizador); detiene la reproducción automática. */
export function seek(step: number): void {
  pause();
  setStep(step);
}

export function toStart(): void {
  seek(0);
}

export function toEnd(): void {
  seek(total());
}

export function changeSpeed(speed: number): void {
  setSpeed(speed);
}

function tick(now: number): void {
  const { playing, speed, step } = getState();
  if (!playing) return stopLoop();

  const elapsed = lastTime === null ? 0 : Math.min((now - lastTime) / 1000, MAX_FRAME_SECONDS);
  lastTime = now;
  carry += elapsed * speed;
  const advance = Math.floor(carry);
  carry -= advance;

  if (advance > 0) {
    const next = Math.min(step + advance, total());
    setStep(next);
    if (next >= total()) {
      setPlaying(false);
      return stopLoop();
    }
  }
  frameId = requestAnimationFrame(tick);
}

function startLoop(): void {
  if (frameId !== null) return;
  lastTime = null;
  carry = 0;
  frameId = requestAnimationFrame(tick);
}

function stopLoop(): void {
  if (frameId !== null) cancelAnimationFrame(frameId);
  frameId = null;
}

// El ciclo arranca o se detiene según `playing`, venga el cambio de donde venga
// (botón, fin de la traza o un mapa nuevo que reinicia el estado).
subscribe(({ playing }) => (playing ? startLoop() : stopLoop()));
