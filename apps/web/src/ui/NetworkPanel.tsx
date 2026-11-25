import type { CatalogIndex } from "../domain/catalogIndex";
import type { Snapshot, SnapshotVehicle } from "../domain/contract";
import { formatAge, formatDelay, methodStyle } from "../domain/format";
import { vehicleKey } from "../domain/identity";
import { lineColor } from "../domain/palette";

interface Props {
  index: CatalogIndex;
  colors: Map<string, string>;
  snapshot: Snapshot | null;
  vehicles: SnapshotVehicle[];
  activeLines: Set<string>;
  onOpenVehicle: (vehicle: SnapshotVehicle) => void;
  onOpenStation: (stationId: string) => void;
}

/**
 * Vista inicial: la red y lo que se está observando ahora mismo. También es
 * la lista con la que se puede seleccionar cualquier circulación con teclado
 * y la alternativa navegable cuando el mapa no está disponible.
 */
export function NetworkPanel({
  index,
  colors,
  snapshot,
  vehicles,
  activeLines,
  onOpenVehicle,
  onOpenStation,
}: Props) {
  const coverage = index.catalog.coverage;
  const shown = [...vehicles].sort((a, b) => {
    const lineOrder = (a.line ?? "zz").localeCompare(b.line ?? "zz", "es");
    return lineOrder !== 0 ? lineOrder : a.vehicle_id.localeCompare(b.vehicle_id);
  });

  return (
    <div className="panel-body">
      <p className="label">Red · {index.catalog.operator}</p>
      <h1>Cercanías Madrid</h1>
      <p className="meta">
        {index.catalog.lines.length} líneas y variantes · {coverage.total_patterns} patrones ·{" "}
        {index.catalog.stations.length} estaciones. GTFS {index.catalog.gtfs_version}, vigencia{" "}
        {index.catalog.gtfs_valid_from} a {index.catalog.gtfs_valid_until}.
      </p>
      <p className="meta">
        Trazado verificado en {coverage.validated} patrones; {coverage.partial} parcial y{" "}
        {coverage.pending} sin corredor cargado. Las circulaciones de un patrón sin corredor se
        dibujan con su GPS bruto etiquetado, no se proyectan sobre un trazado ajeno.
      </p>

      <h2>
        Circulaciones en el snapshot
        {activeLines.size > 0 && <small> · filtrado a {[...activeLines].sort().join(", ")}</small>}
      </h2>
      {snapshot === null ? (
        <p className="meta">Esperando el primer snapshot…</p>
      ) : shown.length === 0 ? (
        <p className="notice">
          Ninguna circulación coincide con el filtro. El snapshot trae{" "}
          {snapshot.counts.vehicles_total} en total.
        </p>
      ) : (
        <ul className="board">
          {shown.map((vehicle) => {
            const style = methodStyle(vehicle.rendered.rendering_method, vehicle.rendered.coordinate_space);
            return (
              <li key={vehicleKey(vehicle)}>
                <button type="button" className="row" onClick={() => onOpenVehicle(vehicle)}>
                  <span className="row__main">
                    <span
                      className="pill pill--static"
                      style={{ background: lineColor(colors, vehicle.line) }}
                    >
                      {vehicle.line ?? "—"}
                    </span>
                    <b>{vehicle.vehicle_id}</b>
                    <small>
                      {style.label}{vehicle.schedule_relationship === "CANCELED" ? " · Viaje cancelado" : ""} · {formatAge(vehicle.rendered.anchor_age_s)} ·{" "}
                      {formatDelay(vehicle.delay)}
                    </small>
                  </span>
                  <em className={`provenance-dot provenance-dot--${style.shape}`} aria-hidden="true" />
                </button>
              </li>
            );
          })}
        </ul>
      )}

      <details className="details">
        <summary>Estaciones del catálogo</summary>
        <ul className="station-list">
          {[...index.catalog.stations]
            .sort((a, b) => a.name.localeCompare(b.name, "es"))
            .map((station) => (
              <li key={station.station_id}>
                <button type="button" onClick={() => onOpenStation(station.station_id)}>
                  {station.name}
                  <small>{[...(index.linesByStation.get(station.station_id) ?? [])].sort().join(" · ")}</small>
                </button>
              </li>
            ))}
        </ul>
      </details>
    </div>
  );
}
