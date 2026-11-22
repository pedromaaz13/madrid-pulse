import type { CatalogIndex } from "../domain/catalogIndex";
import type { SnapshotVehicle } from "../domain/contract";
import {
  ageSecondsAt,
  CIRCULATION_LABELS,
  formatAge,
  formatClockSeconds,
  formatDelay,
  formatIsoClock,
  METHOD_STYLES,
} from "../domain/format";
import type { CirculationId } from "../domain/identity";
import { lineColor } from "../domain/palette";

interface Props {
  index: CatalogIndex;
  colors: Map<string, string>;
  circulation: CirculationId;
  vehicle: SnapshotVehicle | null;
  /** Instante de presentación, refrescado a baja cadencia (no por fotograma). */
  nowMs: number;
  following: boolean;
  cameraReleased: boolean;
  onToggleFollow: () => void;
  onBackToCamera: () => void;
  onOpenStation: (stationId: string) => void;
  onOpenLine: (lineId: string) => void;
  onBack: (() => void) | null;
  backLabel: string | null;
}

/**
 * Ficha de circulación: línea, destino y próxima parada en primer plano;
 * el detalle técnico queda desplegable. El índice de confianza es heurístico
 * y **no calibrado**, así que no aparece como porcentaje en la vista
 * principal: solo en el detalle y nombrado como índice.
 */
export function TrainPanel({
  index,
  colors,
  circulation,
  vehicle,
  nowMs,
  following,
  cameraReleased,
  onToggleFollow,
  onBackToCamera,
  onOpenStation,
  onOpenLine,
  onBack,
  backLabel,
}: Props) {
  if (vehicle === null) {
    return (
      <div className="panel-body">
        {onBack !== null && (
          <button type="button" className="back" onClick={onBack}>
            ← {backLabel}
          </button>
        )}
        <p className="label">Circulación {circulation.vehicleId}</p>
        <h1>Fuera del snapshot</h1>
        <p className="notice notice--warn">
          Esta circulación ({circulation.tripId}, día de servicio {circulation.serviceDate}) no
          aparece en el snapshot vigente. La selección se conserva por si vuelve; no se sustituye
          por otra circulación del mismo vehículo.
        </p>
      </div>
    );
  }

  const rendered = vehicle.rendered;
  const style = METHOD_STYLES[rendered.rendering_method];
  const pattern =
    vehicle.pattern_id === null ? null : (index.patternsById.get(vehicle.pattern_id) ?? null);
  const destinationId = pattern?.destination_stop_id ?? null;
  const destination =
    destinationId === null ? null : (index.stationsById.get(destinationId)?.name ?? destinationId);
  // La edad se recalcula contra el reloj de presentación: avanza aunque el
  // siguiente sondeo falle o no llegue nunca.
  const anchorAge = ageSecondsAt(rendered.anchor_observed_at, nowMs);
  const expired =
    rendered.valid_until !== null && nowMs > Date.parse(rendered.valid_until);

  return (
    <div className="panel-body">
      {onBack !== null && (
        <button type="button" className="back" onClick={onBack}>
          ← {backLabel}
        </button>
      )}
      <p className="label">
        Circulación {vehicle.vehicle_id} · {vehicle.service_date}
      </p>
      <h1>{destination ?? "Destino no catalogado"}</h1>

      <div className="pills">
        {vehicle.line !== null && (
          <button
            type="button"
            className="pill"
            style={{ background: lineColor(colors, vehicle.line) }}
            onClick={() => onOpenLine(vehicle.line as string)}
          >
            {vehicle.line}
          </button>
        )}
        <span className={`provenance provenance--${style.shape}`}>
          <i aria-hidden="true" />
          {style.label}
        </span>
      </div>

      <p className="meta">
        {style.detail}. Última lectura confirmada {formatIsoClock(rendered.last_confirmed_at ?? rendered.anchor_observed_at)} ·{" "}
        {formatAge(anchorAge)}.
      </p>
      {expired && (
        <p className="notice notice--warn">
          La vigencia de esta posición expiró ({formatIsoClock(rendered.valid_until)}). El símbolo
          queda congelado en su última posición autorizada; no se sigue avanzando.
        </p>
      )}
      {rendered.reason !== null && <p className="meta">{rendered.reason}</p>}

      <div className="actions">
        <button type="button" className="primary" onClick={onToggleFollow} aria-pressed={following}>
          {following ? "Dejar de seguir" : "Seguir tren"}
        </button>
        {cameraReleased && (
          <button type="button" className="secondary" onClick={onBackToCamera}>
            Volver al tren
          </button>
        )}
      </div>

      <dl className="kv kv--inline">
        <div>
          <dt>Estado</dt>
          <dd>{CIRCULATION_LABELS[vehicle.circulation_status]}</dd>
        </div>
        <div>
          <dt>Retraso</dt>
          <dd>{formatDelay(vehicle.delay)}</dd>
        </div>
        <div>
          <dt>Viaje</dt>
          <dd className="mono">{vehicle.trip_id}</dd>
        </div>
      </dl>

      {pattern === null ? (
        <p className="notice">
          El patrón de esta circulación no está catalogado en el GTFS cargado: no hay itinerario
          que mostrar y no se inventa uno.
        </p>
      ) : (
        <>
          <h2>Itinerario</h2>
          <p className="meta">
            Patrón {pattern.pattern_id.slice(-6)} · {pattern.geometry.status === "validated"
              ? "corredor validado"
              : `trazado ${pattern.geometry.status}: ${pattern.geometry.reason}`}
          </p>
          <ol className="route">
            {pattern.stations.map((station) => (
              <li key={`${station.station_id}-${station.stop_sequence}`}>
                <button type="button" onClick={() => onOpenStation(station.station_id)}>
                  {station.name}
                </button>
              </li>
            ))}
          </ol>
        </>
      )}

      <details className="details">
        <summary>Detalle técnico de la posición</summary>
        <dl className="kv">
          <div>
            <dt>Método de presentación</dt>
            <dd>{rendered.rendering_method}</dd>
          </div>
          <div>
            <dt>Espacio de la coordenada</dt>
            <dd>{rendered.coordinate_space ?? "ninguno"}</dd>
          </div>
          <div>
            <dt>Índice de confianza (heurístico, no calibrado)</dt>
            <dd>
              {rendered.confidence_index === null
                ? "sin base para estimarlo"
                : rendered.confidence_index.toFixed(3)}
            </dd>
          </div>
          <div>
            <dt>GPS publicado por la fuente</dt>
            <dd>
              {vehicle.raw.lat === null || vehicle.raw.lon === null
                ? "sin coordenada en el mensaje"
                : `${vehicle.raw.lat.toFixed(5)}, ${vehicle.raw.lon.toFixed(5)}`}
            </dd>
          </div>
          <div>
            <dt>Corrección al proyectar</dt>
            <dd>
              {vehicle.map_matched === null
                ? "sin proyección sobre corredor"
                : `${vehicle.map_matched.distance_from_raw_m.toFixed(1)} m`}
            </dd>
          </div>
          <div>
            <dt>Progreso sobre el patrón</dt>
            <dd>
              {rendered.progress_m === null ? "—" : `${Math.round(rendered.progress_m)} m`}
            </dd>
          </div>
          <div>
            <dt>Vigencia de la posición</dt>
            <dd>{formatIsoClock(rendered.valid_until)}</dd>
          </div>
          <div>
            <dt>GPS observado</dt>
            <dd>{formatIsoClock(vehicle.timestamps.gps_observed_at)}</dd>
          </div>
          <div>
            <dt>Publicado por el feed</dt>
            <dd>{formatIsoClock(vehicle.timestamps.feed_published_at)}</dd>
          </div>
          <div>
            <dt>Recibido</dt>
            <dd>{formatIsoClock(vehicle.timestamps.received_at)}</dd>
          </div>
          <div>
            <dt>Snapshot generado</dt>
            <dd>{formatIsoClock(vehicle.timestamps.snapshot_generated_at)}</dd>
          </div>
          <div>
            <dt>Instante dibujado</dt>
            <dd>{formatClockSeconds(nowMs)}</dd>
          </div>
          <div>
            <dt>Retraso del operador</dt>
            <dd>
              {vehicle.delay.coverage === "missing"
                ? "no publicado (no es cero)"
                : `${vehicle.delay.seconds} s · ${formatAge(vehicle.delay.age_s)}${vehicle.delay.expired ? " · caducado" : ""}`}
            </dd>
          </div>
          {vehicle.delay.approximation !== null && (
            <div>
              <dt>Aproximación declarada</dt>
              <dd>{vehicle.delay.approximation}</dd>
            </div>
          )}
          {vehicle.quality.flags.length > 0 && (
            <div>
              <dt>Anomalías del motor</dt>
              <dd>{vehicle.quality.flags.join(", ")}</dd>
            </div>
          )}
        </dl>
      </details>
    </div>
  );
}
