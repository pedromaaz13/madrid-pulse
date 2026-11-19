import type { PositionMode, Vehicle } from "./types";

export const MODE_LABELS: Record<PositionMode, { label: string; detail: string }> = {
  observed: { label: "Observada", detail: "Lectura reciente del vehículo" },
  estimated: { label: "Estimada", detail: "Avance calculado desde la última lectura" },
  stale: { label: "Obsoleta", detail: "Última posición conocida, ya antigua" },
  scheduled: { label: "Programada", detail: "Solo horario; sin posición observada" },
};

export function formatAge(seconds: number | null): string {
  if (seconds === null) return "edad desconocida";
  if (seconds < 60) return `hace ${Math.round(seconds)} s`;
  return `hace ${Math.round(seconds / 60)} min`;
}

export function formatDelay(vehicle: Vehicle): string {
  if (vehicle.delay.coverage === "missing" || vehicle.delay.seconds === null) {
    return "Sin dato de retraso";
  }
  if (vehicle.delay.seconds === 0) return "En hora";
  const minutes = Math.round(Math.abs(vehicle.delay.seconds) / 60);
  return vehicle.delay.seconds > 0 ? `+${minutes} min` : `${minutes} min de adelanto`;
}
