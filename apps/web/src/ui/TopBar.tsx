import type { Mode, Snapshot } from "../domain/contract";
import { formatClockSeconds, formatIsoClock } from "../domain/format";
import type { View } from "../hooks/useUrlState";

interface Props {
  mode: Mode | null;
  nowMs: number;
  snapshot: Snapshot | null;
  degradedCount: number;
  snapshotError: string | null;
  view: View;
  onChangeView: (view: View) => void;
}

const VIEW_LABELS: Record<View, string> = {
  live: "Live",
  history: "History",
  explore: "Explore",
};

const VIEW_TITLES: Record<View, string> = {
  live: "Mapa y tablero en tiempo real",
  history: "Circulaciones de un día ya archivado, con sus huecos de cobertura",
  explore: "Fiabilidad por línea y estación del archivo, con numerador y denominador",
};

/**
 * Barra superior. La etiqueta Live/Replay y el instante mostrado son
 * visibles siempre, como exige el anexo: nunca se presenta un replay como si
 * fuera directo.
 *
 * El reloj y el estado del snapshot pertenecen a Live: en History y Explore se
 * consulta un día **cerrado**, y mostrar ahí un reloj que avanza sugeriría que
 * ese dato se está actualizando. Por eso el indicador solo acompaña a Live.
 */
export function TopBar({
  mode,
  nowMs,
  snapshot,
  degradedCount,
  snapshotError,
  view,
  onChangeView,
}: Props) {
  const healthy = degradedCount === 0 && snapshotError === null;
  return (
    <header className="topbar">
      <span className="brand">
        <span className="brand__logo" aria-hidden="true">
          ∕∕
        </span>
        Madrid Pulse
      </span>
      <nav aria-label="Vistas">
        {(["live", "history", "explore"] as View[]).map((item) => (
          <button
            key={item}
            type="button"
            aria-current={item === view ? "page" : undefined}
            title={VIEW_TITLES[item]}
            onClick={() => onChangeView(item)}
          >
            {VIEW_LABELS[item]}
          </button>
        ))}
      </nav>
      {view === "live" ? (
        <span className={healthy ? "status" : "status status--warn"}>
          <i aria-hidden="true" />
          <b>{mode === "replay" ? "REPLAY" : mode === "live" ? "LIVE" : "—"}</b>
          <span className="mono">{formatClockSeconds(nowMs)}</span>
          {snapshot !== null && (
            <span className="mono status__snapshot">
              snapshot {formatIsoClock(snapshot.generated_at)}
            </span>
          )}
        </span>
      ) : (
        <span className="status status--archive">
          <i aria-hidden="true" />
          <b>ARCHIVO</b>
          <span>día cerrado, no se actualiza</span>
        </span>
      )}
    </header>
  );
}
