import { useMediaQuery } from "./useMediaQuery";

/**
 * `prefers-reduced-motion`. Con movimiento reducido no hay animación
 * espacial automática: ni seguimiento continuo de cámara, ni rotación
 * automática de la cinta de novedades.
 */
export function useReducedMotion(): boolean {
  return useMediaQuery("(prefers-reduced-motion: reduce)");
}
