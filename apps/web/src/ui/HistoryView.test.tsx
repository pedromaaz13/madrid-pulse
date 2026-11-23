import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import type { HistoryDays } from "../domain/contract";
import { HistoryView } from "./HistoryView";

const archivedDays: HistoryDays = {
  schema_version: "1",
  archive_root: "data/parquet",
  days: [
    {
      service_date: "2026-11-20",
      circulations_scheduled: 1,
      circulations_observed: 1,
      circulations_unobserved: 0,
      circulations_canceled: 0,
      circulations_operator_only: 0,
      circulations_unscheduled: 0,
      lines_present: 1,
      rows_total: 1,
      first_observed_at: "2026-11-20T11:00:00Z",
      last_observed_at: "2026-11-20T12:00:00Z",
    },
  ],
};

describe("HistoryView", () => {
  it("no sustituye silenciosamente un día solicitado que no está archivado", () => {
    const markup = renderToStaticMarkup(
      <HistoryView
        index={null}
        colors={new Map()}
        days={archivedDays}
        daysError={null}
        daysLoading={false}
        serviceDate="2026-11-23"
        line={null}
        filter="all"
        circulations={null}
        circulationsError={null}
        circulationsLoading={false}
        selected={{ vehicleId: "19656", tripId: "trip-1", serviceDate: "2026-11-23" }}
        detail={null}
        detailError="404"
        detailLoading={false}
        selectedIsLiveNow={false}
        onPickDate={vi.fn()}
        onPickLine={vi.fn()}
        onPickFilter={vi.fn()}
        onOpenCirculation={vi.fn()}
        onBackToList={vi.fn()}
        onOpenInLive={vi.fn()}
      />,
    );

    expect(markup).toContain("Día no archivado");
    expect(markup).toContain("2026-11-23");
    expect(markup).toContain("No se ha sustituido por otro día");
    expect(markup).toContain("Días archivados disponibles");
    expect(markup).not.toContain("Circulación histórica · 2026-11-20");
    expect(markup).not.toContain("Circulaciones de 2026-11-20");
  });
});
