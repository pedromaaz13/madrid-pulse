import type { Coordinate } from "./contract";

const EARTH_RADIUS_M = 6371008.8;

/**
 * Misma fórmula que `packages/geo.haversine_m`, para que el progreso que
 * calcula el cliente caiga sobre la misma coordenada que publica el backend.
 */
export function haversineM(a: Coordinate, b: Coordinate): number {
  const phi1 = (a.lat * Math.PI) / 180;
  const phi2 = (b.lat * Math.PI) / 180;
  const deltaPhi = phi2 - phi1;
  const deltaLambda = ((b.lon - a.lon) * Math.PI) / 180;
  const h =
    Math.sin(deltaPhi / 2) ** 2 +
    Math.cos(phi1) * Math.cos(phi2) * Math.sin(deltaLambda / 2) ** 2;
  return 2 * EARTH_RADIUS_M * Math.asin(Math.sqrt(h));
}

/**
 * Índice de longitudes acumuladas de una polilínea, calculado una sola vez por
 * geometría para que el reloj de presentación no recorra 1.131 puntos por
 * fotograma y por tren.
 */
export interface PolylineIndex {
  points: Coordinate[];
  /** `cumulative[i]` = metros desde el inicio hasta `points[i]`. */
  cumulative: number[];
  lengthM: number;
}

export function indexPolyline(points: Coordinate[]): PolylineIndex {
  const cumulative: number[] = new Array(points.length);
  let total = 0;
  cumulative[0] = 0;
  for (let i = 1; i < points.length; i += 1) {
    total += haversineM(points[i - 1], points[i]);
    cumulative[i] = total;
  }
  return { points, cumulative, lengthM: total };
}

/**
 * Inversa de la longitud de arco: equivalente de `packages.geo.point_at_arc_length`.
 * Interpola **sobre la polilínea del corredor**, nunca en línea recta entre
 * estaciones. Fuera de rango se limita a los extremos, como el backend.
 */
export function pointAtArcLength(index: PolylineIndex, distanceM: number): Coordinate {
  const { points, cumulative } = index;
  if (points.length < 2) throw new Error("la polilínea necesita al menos dos puntos");
  const target = Math.max(0, distanceM);
  if (target >= index.lengthM) return points[points.length - 1];

  let low = 0;
  let high = points.length - 1;
  while (low + 1 < high) {
    const mid = (low + high) >> 1;
    if (cumulative[mid] <= target) low = mid;
    else high = mid;
  }
  const segmentM = cumulative[high] - cumulative[low];
  if (segmentM === 0) return points[low];
  const fraction = (target - cumulative[low]) / segmentM;
  return {
    lat: points[low].lat + fraction * (points[high].lat - points[low].lat),
    lon: points[low].lon + fraction * (points[high].lon - points[low].lon),
  };
}
