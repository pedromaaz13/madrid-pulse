import type { CatalogIndex } from "../domain/catalogIndex";
import type { BoardEntry, StationBoard } from "../domain/contract";
import {
  boardEntryNote,
  destinationLabel,
  ETA_METHOD_LABELS,
  formatAge,
  formatEta,
  formatIsoClock,
} from "../domain/format";
import { lineColor } from "../domain/palette";

interface Props {
  index: CatalogIndex;
  colors: Map<string, string>;
  stationId: string;
  board: StationBoard | null;
  error: string | null;
  loading: boolean;
  onOpenEntry: (entry: BoardEntry) => void;
  onOpenLine: (lineId: string) => void;
}

/**
 * Tablero de estación. El backend lo calcula con calendario + horario + RT:
 * el cliente no ordena ni filtra por cercanía geográfica, solo presenta lo
 * que el contrato publica, incluidas sus limitaciones declaradas.
 */
export function StationPanel({
  index,
  colors,
  stationId,
  board,
  error,
  loading,
  onOpenEntry,
  onOpenLine,
}: Props) {
  const station = index.stationsById.get(stationId);
  const lines = [...(index.linesByStation.get(stationId) ?? [])].sort();
  const name = board?.name ?? station?.name ?? stationId;

  return (
    <div className="panel-body">
      <p className="label">Estación · {index.catalog.operator} · {stationId}</p>
      <h1>{name}</h1>
      <div className="pills">
        {lines.map((lineId) => (
          <button
            key={lineId}
            type="button"
            className="pill"
            style={{ background: lineColor(colors, lineId) }}
            onClick={() => onOpenLine(lineId)}
          >
            {lineId}
          </button>
        ))}
        {lines.length === 0 && <span className="meta">Sin línea catalogada en este GTFS</span>}
      </div>

      <h2>Próximas salidas</h2>
      {error !== null && (
        <p className="notice notice--warn" role="status">
          El tablero no se pudo actualizar ({error}).
          {board !== null && " Se muestra el último resultado válido, con su hora de cálculo."}
        </p>
      )}
      {board === null ? (
        <p className="meta">{loading ? "Consultando el tablero…" : "Sin tablero disponible."}</p>
      ) : (
        <>
          <p className="meta">
            Calculado {formatIsoClock(board.generated_at)} · días de servicio{" "}
            {board.service_dates_considered.join(", ")}
          </p>
          {board.entries.length === 0 ? (
            <p className="notice">
              Sin salidas registradas en la ventana consultada. No es lo mismo que una fuente sin
              conexión: el cálculo se realizó y devolvió cero llamadas.
            </p>
          ) : (
            <ul className="board">
              {board.entries.map((entry) => {
                const eta = entry.departure.method === "unavailable" ? entry.arrival : entry.departure;
                return (
                  <li key={`${entry.trip_id}|${entry.service_date}|${entry.stop_sequence}`}>
                    <button type="button" className="row" onClick={() => onOpenEntry(entry)}>
                      <span className="row__main">
                        <span
                          className="pill pill--static"
                          style={{ background: lineColor(colors, entry.line) }}
                        >
                          {entry.line ?? "—"}
                        </span>
                        <b>
                          {destinationLabel(
                            entry,
                            (id) => index.stationsById.get(id)?.name ?? null,
                          )}
                        </b>
                        <small>
                          {boardEntryNote(entry)} ·{" "}
                          {entry.circulation_source === "observed"
                            ? "Circulación observada"
                            : "Solo horario, sin observación"}
                        </small>
                        <small className="row__provenance">
                          {ETA_METHOD_LABELS[eta.method]}
                          {eta.delay_age_s !== null && ` · retraso ${formatAge(eta.delay_age_s)}`}
                          {eta.approximation !== null && " · aproximación de nivel viaje"}
                        </small>
                      </span>
                      <em>{formatEta(eta)}</em>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
          <details className="details">
            <summary>Cobertura y limitaciones del tablero</summary>
            <dl className="kv">
              <div>
                <dt>Llamadas programadas</dt>
                <dd>{board.coverage.scheduled_calls}</dd>
              </div>
              <div>
                <dt>Mostradas</dt>
                <dd>{board.coverage.returned}</dd>
              </div>
              <div>
                <dt>Circulaciones observadas</dt>
                <dd>{board.coverage.observed_circulations}</dd>
              </div>
              <div>
                <dt>ETA del operador</dt>
                <dd>{board.coverage.eta_from_operator}</dd>
              </div>
              <div>
                <dt>ETA del horario</dt>
                <dd>{board.coverage.eta_from_schedule}</dd>
              </div>
              <div>
                <dt>ETA no disponible</dt>
                <dd>{board.coverage.eta_unavailable}</dd>
              </div>
              <div>
                <dt>Cobertura de retraso</dt>
                <dd>
                  {board.coverage.operator_delay_coverage_pct === null
                    ? "sin muestra"
                    : `${board.coverage.operator_delay_coverage_pct.toFixed(1)} % (${board.coverage.with_operator_delay}/${board.coverage.returned})`}
                </dd>
              </div>
            </dl>
            <p className="meta">{board.calculated_from}</p>
            <ul className="limitations">
              {board.limitations.map((limitation) => (
                <li key={limitation}>{limitation}</li>
              ))}
            </ul>
          </details>
        </>
      )}
    </div>
  );
}
