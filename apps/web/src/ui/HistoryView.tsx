import type { CatalogIndex } from "../domain/catalogIndex";
import type {
  HistoryCirculation,
  HistoryCirculationDetail,
  HistoryCirculations,
  HistoryDay,
  HistoryDays,
  HistoryFilter,
} from "../domain/contract";
import {
  circulationCoverageLabel,
  COVERAGE_DETAILS,
  formatCount,
  formatGtfsTime,
  formatHistoryOnTime,
  formatIsoClock,
  HISTORY_FILTER_LABELS,
} from "../domain/format";
import type { CirculationId } from "../domain/identity";
import { lineColor } from "../domain/palette";

const FILTERS: HistoryFilter[] = [
  "all",
  "observed",
  "unobserved",
  "canceled",
  "operator_only",
  "unscheduled",
];

interface Props {
  index: CatalogIndex | null;
  colors: Map<string, string>;
  days: HistoryDays | null;
  daysError: string | null;
  daysLoading: boolean;
  serviceDate: string | null;
  line: string | null;
  filter: HistoryFilter;
  circulations: HistoryCirculations | null;
  circulationsError: string | null;
  circulationsLoading: boolean;
  selected: CirculationId | null;
  detail: HistoryCirculationDetail | null;
  detailError: string | null;
  detailLoading: boolean;
  /** `true` si la circulación seleccionada está ahora mismo en el snapshot. */
  selectedIsLiveNow: boolean;
  onPickDate: (serviceDate: string) => void;
  onPickLine: (line: string | null) => void;
  onPickFilter: (filter: HistoryFilter) => void;
  onOpenCirculation: (circulation: HistoryCirculation) => void;
  onBackToList: () => void;
  onOpenInLive: () => void;
}

function stationName(index: CatalogIndex | null, stationId: string | null): string {
  if (stationId === null) return "—";
  return index?.stationsById.get(stationId)?.name ?? stationId;
}

function DayPicker({
  days,
  serviceDate,
  onPickDate,
}: {
  days: HistoryDay[];
  serviceDate: string | null;
  onPickDate: (value: string) => void;
}) {
  return (
    <div className="pills" role="group" aria-label="Días archivados">
      {days.map((day) => (
        <button
          key={day.service_date}
          type="button"
          className={day.service_date === serviceDate ? "pill pill--active" : "pill pill--static"}
          aria-pressed={day.service_date === serviceDate}
          onClick={() => onPickDate(day.service_date)}
        >
          {day.service_date}
        </button>
      ))}
    </div>
  );
}

/**
 * Vista de histórico. Tres niveles: día archivado → circulaciones de ese día
 * (filtrables por línea y por cobertura) → detalle de una circulación, con
 * vuelta a Live por la **misma** identidad (vehículo + viaje + día de
 * servicio) cuando esa circulación sigue en el snapshot vigente.
 *
 * Regla que gobierna toda esta vista: ningún recuento ausente se presenta como
 * `0` y ningún porcentaje aparece sin su denominador. Un día que no está
 * archivado no se dibuja como un día vacío: se dice que no hay archivo (el
 * backend responde `404`, no un día con métricas a cero).
 */
export function HistoryView({
  index,
  colors,
  days,
  daysError,
  daysLoading,
  serviceDate,
  line,
  filter,
  circulations,
  circulationsError,
  circulationsLoading,
  selected,
  detail,
  detailError,
  detailLoading,
  selectedIsLiveNow,
  onPickDate,
  onPickLine,
  onPickFilter,
  onOpenCirculation,
  onBackToList,
  onOpenInLive,
}: Props) {
  if (days === null) {
    return (
      <div className="panel-body">
        <p className="label">Histórico</p>
        <h1>{daysLoading ? "Consultando el archivo" : "Archivo no disponible"}</h1>
        <p className="meta">
          {daysError ??
            "Leyendo los días ya archivados en Parquet por services/snapshotter."}
        </p>
      </div>
    );
  }

  if (days.days.length === 0) {
    return (
      <div className="panel-body">
        <p className="label">Histórico</p>
        <h1>Todavía no hay días archivados</h1>
        <p className="notice">
          El archivo frío consultado está vacío. No significa que no haya habido servicio: significa
          que nadie ha ejecutado todavía <code>python -m services.snapshotter &lt;fecha&gt;</code>
          sobre esos días.
        </p>
        <p className="meta mono">{days.archive_root}</p>
      </div>
    );
  }

  const day =
    serviceDate === null
      ? days.days[0]
      : days.days.find((item) => item.service_date === serviceDate);

  if (day === undefined) {
    return (
      <div className="panel-body">
        <p className="label">Histórico · archivo frío</p>
        <h1>Día no archivado</h1>
        <p className="notice" role="status">
          El día solicitado <span className="mono">{serviceDate}</span> no está disponible en este
          archivo. No se ha sustituido por otro día.
        </p>
        <p className="meta">Días archivados disponibles:</p>
        <DayPicker days={days.days} serviceDate={null} onPickDate={onPickDate} />
      </div>
    );
  }

  const availableLines = index === null ? [] : index.catalog.lines.map((item) => item.line_id);

  if (selected !== null) {
    return (
      <div className="panel-body">
        <button type="button" className="back" onClick={onBackToList}>
          ← Circulaciones de {day.service_date}
        </button>
        <p className="label">Circulación histórica · {day.service_date}</p>
        <h1>{selected.vehicleId === "" ? selected.tripId : selected.vehicleId}</h1>
        {detail === null ? (
          <p className="meta">
            {detailError ?? (detailLoading ? "Consultando el archivo…" : "Sin detalle disponible.")}
          </p>
        ) : (
          <>
            <p className="meta">
              {circulationCoverageLabel(detail.circulation.coverage)} · viaje{" "}
              <span className="mono">{detail.circulation.trip_id}</span>
            </p>
            <p className="meta">{COVERAGE_DETAILS[detail.circulation.coverage]}</p>
            <div className="pills">
              {detail.circulation.line_short_name !== "" && (
                <span
                  className="pill pill--static"
                  style={{ background: lineColor(colors, detail.circulation.line_short_name) }}
                >
                  {detail.circulation.line_short_name}
                </span>
              )}
              {selectedIsLiveNow ? (
                <button type="button" className="pill" onClick={onOpenInLive}>
                  Ver en Live
                </button>
              ) : (
                <span className="meta">
                  Esta circulación no está en el snapshot vigente: no se puede abrir en Live.
                </span>
              )}
            </div>

            <h2>Horario previsto</h2>
            {detail.circulation.scheduled &&
              detail.circulation.scheduled_first_departure_time === null && (
                <p className="notice" role="status">
                  El GTFS programa este viaje pero no publica ninguna parada para él
                  (<span className="mono">stop_times.txt</span> no lo incluye). Se conserva como
                  circulación programada —cuenta en el denominador del día— con el horario
                  explícitamente ausente.
                </p>
              )}
            <dl className="kv">
              <div>
                <dt>Origen</dt>
                <dd>
                  {stationName(index, detail.circulation.scheduled_first_stop_id)} ·{" "}
                  {formatGtfsTime(detail.circulation.scheduled_first_departure_time)}
                </dd>
              </div>
              <div>
                <dt>Destino</dt>
                <dd>
                  {stationName(index, detail.circulation.scheduled_last_stop_id)} ·{" "}
                  {formatGtfsTime(detail.circulation.scheduled_last_arrival_time)}
                </dd>
              </div>
            </dl>

            <h2>Qué se observó</h2>
            <dl className="kv">
              <div>
                <dt>Posiciones archivadas</dt>
                <dd>{formatCount(detail.circulation.positions_count)}</dd>
              </div>
              <div>
                <dt>Primera observación</dt>
                <dd>{formatIsoClock(detail.circulation.first_observed_at)}</dd>
              </div>
              <div>
                <dt>Última observación</dt>
                <dd>{formatIsoClock(detail.circulation.last_observed_at)}</dd>
              </div>
              <div>
                <dt>Paradas distintas</dt>
                <dd>{formatCount(detail.circulation.distinct_stops_observed)}</dd>
              </div>
              <div>
                <dt>Puntualidad</dt>
                <dd>
                  {formatHistoryOnTime(
                    detail.circulation.on_time,
                    detail.circulation.latest_reported_delay_seconds,
                    detail.circulation.delay_reported_count,
                  )}
                </dd>
              </div>
              <div>
                <dt>Actualizaciones del viaje</dt>
                <dd>
                  {formatCount(detail.circulation.trip_updates_count)} ·{" "}
                  {formatCount(detail.circulation.delay_reported_count)} con retraso reportado
                </dd>
              </div>
            </dl>

            {detail.positions.length === 0 ? (
              <p className="notice">
                {detail.circulation.coverage === "canceled"
                  ? "No hay ninguna posición porque el operador anuló este servicio: el tren no circuló. No es un hueco de captura."
                  : detail.circulation.coverage === "operator_only"
                    ? "El operador publicó una actualización de este viaje, pero nunca llegó una posición. Es un hueco de posición, no de información."
                    : "No llegó ni una señal de esta circulación: ni posición ni actualización de viaje. Es un hueco de cobertura real, no un cero."}
              </p>
            ) : (
              <>
                <h2>Observaciones archivadas</h2>
                <ul className="board">
                  {detail.positions.map((position) => (
                    <li key={`${position.observed_at}|${position.current_stop_id ?? ""}`}>
                      <span className="row row--static">
                        <span className="row__main">
                          <b>{formatIsoClock(position.observed_at)}</b>
                          <small>
                            {position.current_status ?? "estado no publicado"} ·{" "}
                            {stationName(index, position.current_stop_id)}
                          </small>
                          <small className="row__provenance mono">
                            {position.latitude === null || position.longitude === null
                              ? "sin coordenada publicada"
                              : `${position.latitude.toFixed(5)}, ${position.longitude.toFixed(5)}`}
                          </small>
                        </span>
                      </span>
                    </li>
                  ))}
                </ul>
              </>
            )}

            {detail.delays.length > 0 && (
              <details className="details">
                <summary>Actualizaciones de viaje archivadas ({detail.delays.length})</summary>
                <ul className="limitations">
                  {detail.delays.map((row) => (
                    <li key={`${row.observed_at}|${row.delay_coverage}`}>
                      {formatIsoClock(row.observed_at)} ·{" "}
                      {row.delay_coverage === "reported" && row.delay_seconds !== null
                        ? `${row.delay_seconds >= 0 ? "+" : "−"}${Math.round(Math.abs(row.delay_seconds) / 60)} min`
                        : "sin retraso reportado"}
                    </li>
                  ))}
                </ul>
                <p className="meta">
                  El operador publica el retraso contra el <b>viaje</b>, no contra el vehículo: se
                  listan tal cual, sin atribuirlos a un tren concreto.
                </p>
              </details>
            )}
          </>
        )}
      </div>
    );
  }

  return (
    <div className="panel-body">
      <p className="label">Histórico · archivo frío</p>
      <h1>{day.service_date}</h1>
      <DayPicker days={days.days} serviceDate={day.service_date} onPickDate={onPickDate} />

      <dl className="kv">
        <div>
          <dt>Programadas</dt>
          <dd>{day.circulations_scheduled}</dd>
        </div>
        <div>
          <dt>Observadas</dt>
          <dd>{day.circulations_observed}</dd>
        </div>
        <div>
          <dt>Huecos (sin ninguna señal)</dt>
          <dd>{day.circulations_unobserved}</dd>
        </div>
        <div>
          <dt>Anuladas por el operador</dt>
          <dd>{day.circulations_canceled}</dd>
        </div>
        <div>
          <dt>Solo parte del operador</dt>
          <dd>{day.circulations_operator_only}</dd>
        </div>
        <div>
          <dt>Fuera de programación</dt>
          <dd>{day.circulations_unscheduled}</dd>
        </div>
        <div>
          <dt>Observación</dt>
          <dd>
            {day.first_observed_at === null
              ? "ninguna"
              : `${formatIsoClock(day.first_observed_at)} → ${formatIsoClock(day.last_observed_at)}`}
          </dd>
        </div>
      </dl>
      {day.circulations_canceled > 0 && (
        <p className="notice" role="status">
          {day.circulations_canceled} circulación(es) de ese día están <b>anuladas</b> por el
          operador. No cuentan como hueco de cobertura: el tren no circuló y el feed lo dijo, así
          que atribuirlo a un fallo de captura sería culpar al colector de algo que no hizo.
        </p>
      )}
      {day.circulations_unscheduled > 0 && (
        <p className="notice notice--warn" role="status">
          {day.circulations_unscheduled} circulación(es) observada(s) ese día no figuran en el
          calendario del GTFS cargado. El GTFS de Renfe no es retroactivo: no se descartan, se
          marcan.
        </p>
      )}

      <h2>Circulaciones</h2>
      <div className="pills" role="group" aria-label="Filtro de cobertura">
        {FILTERS.map((value) => (
          <button
            key={value}
            type="button"
            className={value === filter ? "pill pill--active" : "pill pill--static"}
            aria-pressed={value === filter}
            onClick={() => onPickFilter(value)}
          >
            {HISTORY_FILTER_LABELS[value]}
          </button>
        ))}
      </div>
      <div className="pills" role="group" aria-label="Filtro de línea">
        <button
          type="button"
          className={line === null ? "pill pill--active" : "pill pill--static"}
          aria-pressed={line === null}
          onClick={() => onPickLine(null)}
        >
          Todas las líneas
        </button>
        {availableLines.map((lineId) => (
          <button
            key={lineId}
            type="button"
            className={lineId === line ? "pill pill--active" : "pill"}
            aria-pressed={lineId === line}
            style={lineId === line ? undefined : { background: lineColor(colors, lineId) }}
            onClick={() => onPickLine(lineId)}
          >
            {lineId}
          </button>
        ))}
      </div>

      {circulationsError !== null && (
        <p className="notice notice--warn" role="status">
          La lista no se pudo actualizar ({circulationsError}).
        </p>
      )}
      {circulations === null ? (
        <p className="meta">
          {circulationsLoading ? "Consultando el archivo…" : "Sin lista disponible."}
        </p>
      ) : circulations.circulations.length === 0 ? (
        <p className="notice">
          Ninguna circulación cumple este filtro en {day.service_date}. El archivo del día existe y
          la consulta devolvió cero filas: no es una fuente caída.
        </p>
      ) : (
        <>
          <p className="meta">
            {circulations.returned} fila(s)
            {circulations.truncated && " · lista recortada por el límite de consulta"}
          </p>
          <ul className="board">
            {circulations.circulations.map((circulation) => (
              <li key={`${circulation.trip_id}|${circulation.vehicle_id ?? "-"}`}>
                <button
                  type="button"
                  className="row"
                  onClick={() => onOpenCirculation(circulation)}
                >
                  <span className="row__main">
                    <span
                      className="pill pill--static"
                      style={{ background: lineColor(colors, circulation.line_short_name) }}
                    >
                      {circulation.line_short_name === "" ? "—" : circulation.line_short_name}
                    </span>
                    <b>
                      {circulation.vehicle_id ?? "Sin vehículo observado"} ·{" "}
                      {circulation.scheduled_first_departure_time === null
                        ? "sin horario publicado"
                        : formatGtfsTime(circulation.scheduled_first_departure_time)}
                    </b>
                    <small>
                      {circulationCoverageLabel(circulation.coverage)} ·{" "}
                      {formatCount(circulation.positions_count)} posición(es)
                    </small>
                    <small className="row__provenance">
                      {formatHistoryOnTime(
                        circulation.on_time,
                        circulation.latest_reported_delay_seconds,
                        circulation.delay_reported_count,
                      )}
                    </small>
                  </span>
                  <em className="mono">{circulation.trip_id}</em>
                </button>
              </li>
            ))}
          </ul>
        </>
      )}
      <p className="meta mono">{days.archive_root}</p>
    </div>
  );
}
