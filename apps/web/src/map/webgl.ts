/**
 * Detección de WebGL. MapLibre 6 ya no exporta `supported()`, así que se
 * comprueba lo mismo que necesita el renderer. Sin WebGL la aplicación no
 * muestra un mapa roto: sirve la alternativa de lista y tablero.
 */
export function hasWebGL(): boolean {
  if (typeof document === "undefined") return false;
  try {
    const canvas = document.createElement("canvas");
    const context =
      canvas.getContext("webgl2") ??
      canvas.getContext("webgl") ??
      canvas.getContext("experimental-webgl");
    return context !== null;
  } catch {
    return false;
  }
}
