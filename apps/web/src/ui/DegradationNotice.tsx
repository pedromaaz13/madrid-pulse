import type { SnapshotDegradation } from "../domain/contract";
import { degradationText } from "../domain/format";

export function DegradationNotice({ item }: { item: SnapshotDegradation }) {
  return <p className="notice notice--warn" role={item.status === "error" ? "alert" : "status"}>
    {degradationText(item)}
  </p>;
}
