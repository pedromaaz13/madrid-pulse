import type { SnapshotVehicle } from "./contract";

/**
 * Identidad de una circulación conforme a MP-017: `vehicle_id` **no** es
 * identidad de viaje. Un mismo vehículo encadena servicios distintos, así que
 * la selección se ancla a vehículo + viaje + día de servicio y sobrevive al
 * polling sin saltar a otra circulación del mismo tren.
 */
export interface CirculationId {
  vehicleId: string;
  tripId: string;
  serviceDate: string;
}

export function circulationKey(id: CirculationId): string {
  return `${id.vehicleId}|${id.tripId}|${id.serviceDate}`;
}

export function circulationOf(vehicle: SnapshotVehicle): CirculationId {
  return {
    vehicleId: vehicle.vehicle_id,
    tripId: vehicle.trip_id,
    serviceDate: vehicle.service_date,
  };
}

export function vehicleKey(vehicle: SnapshotVehicle): string {
  return circulationKey(circulationOf(vehicle));
}

export function sameCirculation(a: CirculationId, b: CirculationId): boolean {
  return a.vehicleId === b.vehicleId && a.tripId === b.tripId && a.serviceDate === b.serviceDate;
}

export type Selection =
  | { kind: "none" }
  | { kind: "station"; stationId: string }
  | { kind: "train"; circulation: CirculationId };

export function selectionKey(selection: Selection): string {
  switch (selection.kind) {
    case "none":
      return "none";
    case "station":
      return `station:${selection.stationId}`;
    case "train":
      return `train:${circulationKey(selection.circulation)}`;
  }
}
