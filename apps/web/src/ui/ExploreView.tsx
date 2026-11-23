import type {
  HistoryDays,
  HistoryLines,
  HistoryStations,
} from "../domain/contract";
import type { CatalogIndex } from "../domain/catalogIndex";
import { formatCount, formatIsoClock, formatPctWithDenominator } from "../domain/format";
import { lineColor } from "../domain/palette";

interface Props {
  index: CatalogIndex | null;
  colors: Map<string, string>;
  days: HistoryDays | null;
  daysError: string | null;
  serviceDate: string | null;
  lines: HistoryLines | null;
  linesError: string | null;
  linesLoading: boolean;
  stations: HistoryStations | null;
  stationsError: string | null;
  onPickDate: (serviceDate: string) => void;
  onOpenLineInHistory: (line: string) => void;
}

/**
 * Explore mínimo: fiabilidad por línea y actividad por estación de un día ya
 * archivado, más el índice del archivo completo.
 *
 * Deliberadamente **no** es un SQL Lab ni un constructor de consultas (el kit
 * de Hito 3 lo prohíbe de forma explícita): son dos agregados ya calculados
 * (`daily_line_metrics` y `station_daily_metrics`) presentados tal como los
 * publica el contrato. Toda métrica aparece con su numerador y su denominador;
 * una puntualidad sin muestra se escribe "sin muestra", nunca `0 %`.
 */
export function ExploreView({
  index,
  colors,
  days,
  daysError,
  serviceDate,
  lines,
  linesError,
  linesLoading,
  stations,
  stationsError,
  onPickDate,
  onOpenLineInHistory,
}: Props) {
  if (days === null) {
    return (
      <div className="panel-body">
        <p className="label">Explore</p>
        <h1>Archivo no disponible</h1>
        <p className="meta">{daysError ?? "Consultando los días archivados…"}</p>
      </div>
    );
  }
  if (days.days.length === 0) {
    return (
      <div className="panel-body">
        <p className="label">Explore</p>
        <h1>Todavía no hay días archivados</h1>
        <p className="notice">
          Sin archivo no hay nada que comparar. Ejecútese{" "}
          <code>python -m services.snapshotter &lt;fecha&gt;</code> para archivar un día.
        </p>
      </div>
    );
  }

  const day = days.days.find((item) => item.service_date === serviceDate) ?? days.days[0];
  const covered = lines?.lines.filter((row) => row.trips_with_delay_data > 0) ?? [];
  const totalScheduled = (lines?.lines ?? []).reduce((sum, row) => sum + row.trips_scheduled, 0);
  const totalCovered = (lines?.lines ?? []).reduce(
    (sum, row) => sum + row.trips_with_delay_data,
    0,
  );

  return (
    <div className="panel-body">
      <p className="label">Explore · fiabilidad del archivo</p>
      <h1>{day.service_date}</h1>
      <div className="pills" role="group" aria-label="Días archivados">
        {days.days.map((item) => (
          <button
            key={item.service_date}
            type="button"
            className={
              item.service_date === day.service_date ? "pill pill--active" : "pill pill--static"
            }
            aria-pressed={item.service_date === day.service_date}
            onClick={() => onPickDate(item.service_date)}
          >
            {item.service_date}
          </button>
        ))}
      </div>

      <h2>Cobertura del día</h2>
      <dl className="kv">
        <div>
          <dt>Viajes programados (denominador)</dt>
          <dd>{totalScheduled}</dd>
        </div>
        <div>
          <dt>Con dato de retraso</dt>
          <dd>
            {formatPctWithDenominator(
              totalScheduled === 0 ? null : (100 * totalCovered) / totalScheduled,
              totalCovered,
              totalScheduled,
            )}
          </dd>
        </div>
        <div>
          <dt>Circulaciones observadas</dt>
          <dd>
            {day.circulations_observed} de {day.circulations_scheduled} programadas
          </dd>
        </div>
        <div>
          <dt>Huecos de cobertura</dt>
          <dd>{day.circulations_unobserved}</dd>
        </div>
        <div>
          <dt>Anuladas por el operador</dt>
          <dd>
            {day.circulations_canceled}
            {day.circulations_canceled > 0 && " · el tren no circuló, no es un hueco de captura"}
          </dd>
        </div>
      </dl>
      <p className="meta">
        La cobertura de este día depende de cuánto tiempo estuvo el colector en marcha, no de la
        red:{" "}
        {day.first_observed_at === null
          ? "este día no tiene ninguna observación archivada."
          : `lo archivado va de ${formatIsoClock(day.first_observed_at)} a ${formatIsoClock(day.last_observed_at)}, y solo lo que circulaba en esa ventana puede haberse observado.`}{" "}
        Mide lo observado, no la calidad del servicio ferroviario.
      </p>

      <h2>Puntualidad por ruta</h2>
      {linesError !== null && (
        <p className="notice notice--warn" role="status">
          Las métricas por línea no se pudieron cargar ({linesError}).
        </p>
      )}
      {lines === null ? (
        <p className="meta">{linesLoading ? "Consultando el mart…" : "Sin métricas."}</p>
      ) : lines.lines.length === 0 ? (
        <p className="notice">
          El mart por línea de {day.service_date} no tiene ninguna fila: el GTFS cargado no programa
          ningún viaje ese día. No es una medición de cero puntualidad — es ausencia de calendario
          (el GTFS de Renfe no es retroactivo).
        </p>
      ) : (
        <>
          <p className="meta">
            {lines.lines.length} ruta(s) con viajes programados · {covered.length} con algún retraso
            reportado
          </p>
          <div className="table-scroll">
            <table className="metrics">
              <thead>
                <tr>
                  <th scope="col">Línea</th>
                  <th scope="col">Ruta</th>
                  <th scope="col">Programados</th>
                  <th scope="col">Cobertura de retraso</th>
                  <th scope="col">Puntualidad de lo cubierto</th>
                </tr>
              </thead>
              <tbody>
                {lines.lines.map((row) => (
                  <tr key={row.route_id}>
                    <th scope="row">
                      {row.line_short_name === "" ? (
                        <span className="meta">—</span>
                      ) : (
                        <button
                          type="button"
                          className="pill"
                          style={{ background: lineColor(colors, row.line_short_name) }}
                          onClick={() => onOpenLineInHistory(row.line_short_name)}
                        >
                          {row.line_short_name}
                        </button>
                      )}
                    </th>
                    <td className="mono">{row.route_id}</td>
                    <td>{row.trips_scheduled}</td>
                    <td>
                      {formatPctWithDenominator(
                        row.delay_coverage_pct,
                        row.trips_with_delay_data,
                        row.trips_scheduled,
                      )}
                    </td>
                    <td>
                      {formatPctWithDenominator(
                        row.on_time_pct_of_covered,
                        row.on_time_pct_of_covered === null
                          ? null
                          : Math.round(
                              (row.on_time_pct_of_covered * row.trips_with_delay_data) / 100,
                            ),
                        row.trips_with_delay_data,
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      <h2>Estaciones con más observaciones</h2>
      {stationsError !== null && (
        <p className="notice notice--warn" role="status">
          Las métricas por estación no se pudieron cargar ({stationsError}).
        </p>
      )}
      {stations === null || stations.stations.length === 0 ? (
        <p className="meta">Sin observaciones atribuidas a ninguna estación ese día.</p>
      ) : (
        <ul className="board">
          {stations.stations.slice(0, 12).map((row) => (
            <li key={row.station_id}>
              <span className="row row--static">
                <span className="row__main">
                  <b>{index?.stationsById.get(row.station_id)?.name ?? row.station_id}</b>
                  <small className="mono">{row.station_id}</small>
                </span>
                <em>{row.observations_count}</em>
              </span>
            </li>
          ))}
        </ul>
      )}
      <p className="meta">
        `station_daily_metrics` no incluye eventos de calidad por estación:
        `data_quality_event.entity_ref` nunca referencia una parada, así que atribuirlos exigiría un
        cruce no verificado (DEC-033).
      </p>

      <h2>Días archivados</h2>
      <ul className="board">
        {days.days.map((item) => (
          <li key={item.service_date}>
            <button type="button" className="row" onClick={() => onPickDate(item.service_date)}>
              <span className="row__main">
                <b>{item.service_date}</b>
                <small>
                  {item.circulations_observed} observadas · {item.circulations_unobserved} huecos ·{" "}
                  {formatCount(item.lines_present)} línea(s)
                </small>
                <small className="row__provenance">
                  {item.first_observed_at === null
                    ? "sin observaciones archivadas"
                    : `${formatIsoClock(item.first_observed_at)} → ${formatIsoClock(item.last_observed_at)}`}
                </small>
              </span>
              <em>{item.rows_total}</em>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
