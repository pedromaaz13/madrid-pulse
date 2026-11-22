import type { Mode, Snapshot } from "../domain/contract";
import { formatClockSeconds, formatIsoClock } from "../domain/format";

interface Props {
  mode: Mode | null;
  nowMs: number;
  snapshot: Snapshot | null;
  degradedCount: number;
  snapshotError: string | null;
}

/**
 * Barra superior. La etiqueta Live/Replay y el instante mostrado son
 * visibles siempre, como exige el anexo: nunca se presenta un replay como si
 * fuera directo.
 */
export function TopBar({ mode, nowMs, snapshot, degradedCount, snapshotError }: Props) {
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
        <button type="button" aria-current="page">
          Live
        </button>
        <button type="button" disabled title="Histórico y Explore se entregan en MP-021">
          History
        </button>
        <button type="button" disabled title="Histórico y Explore se entregan en MP-021">
          Explore
        </button>
      </nav>
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
    </header>
  );
}
