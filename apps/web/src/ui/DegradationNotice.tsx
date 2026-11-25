import type { SnapshotDegradation } from "../domain/contract";

export function DegradationNotice({ item }: { item: SnapshotDegradation }) {
  return <p className="notice notice--warn" role={item.status === "error" ? "alert" : "status"}>
    {item.resource === "gtfs" ? `GTFS · ${item.status === "stale" ? "aviso" : item.status === "error" ? "error" : "vigencia desconocida"}: ${item.reason}` : `${item.resource}: ${item.reason}`}
  </p>;
}
