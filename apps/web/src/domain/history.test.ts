import { describe, expect, it } from "vitest";
import fixture from "../__fixtures__/history-archive.json";
import type {
  HistoryCirculationDetail,
  HistoryCirculations,
  HistoryDays,
  HistoryLines,
  HistoryStations,
} from "./contract";
import {
  circulationCoverageLabel,
  COVERAGE_DETAILS,
  formatGtfsTime,
  formatHistoryOnTime,
  formatPctWithDenominator,
} from "./format";
import { circulationKey } from "./identity";

/**
 * Suite del cliente sobre una **grabación real** de `/api/v1/history/*`
 * (mismo criterio que la grabación de snapshot de MP-020): el contrato que
 * consume el frontend se comprueba contra lo que la API devolvió de verdad
 * sobre el archivo frío de dos días reales, no contra un objeto inventado a
 * mano que podría divergir del backend sin que nadie se enterase.
 *
 * Los dos días de la grabación son deliberadamente distintos entre sí:
 * `2026-11-20` tiene calendario y observaciones (cobertura parcial real) y
 * `2026-11-19` tiene observaciones pero **ningún** servicio programado en el
 * GTFS vigente, porque el ZIP oficial empieza su calendario el día 20. Es el
 * caso "observada fuera de programación" en datos reales.
 */
const days = fixture.days as unknown as HistoryDays;
const lines = fixture.lines as unknown as HistoryLines;
const observed = fixture.circulations_observed as unknown as HistoryCirculations;
const gaps = fixture.circulations_unobserved as unknown as HistoryCirculations;
const canceled = fixture.circulations_canceled as unknown as HistoryCirculations;
const detail = fixture.circulation_detail as unknown as HistoryCirculationDetail;
const canceledDetail = fixture.circulation_detail_canceled as unknown as HistoryCirculationDetail;
const stations = fixture.stations as unknown as HistoryStations;

describe("índice de días archivados", () => {
  it("los días vienen de más reciente a más antiguo", () => {
    const dates = days.days.map((day) => day.service_date);
    expect(dates).toEqual([...dates].sort().reverse());
  });

  it("las cinco categorías de cobertura particionan el día sin solaparse", () => {
    for (const day of days.days) {
      const scheduledAndObserved = day.circulations_observed - day.circulations_unscheduled;
      expect(scheduledAndObserved).toBeGreaterThanOrEqual(0);
      // Cada fila cae en exactamente una categoría, así que las cinco suman el total.
      expect(day.rows_total).toBe(
        scheduledAndObserved +
          day.circulations_canceled +
          day.circulations_operator_only +
          day.circulations_unobserved +
          day.circulations_unscheduled,
      );
      expect(day.rows_total).toBe(day.circulations_scheduled + day.circulations_unscheduled);
    }
  });

  it("las anuladas no se cuentan dentro del hueco de cobertura", () => {
    const day = days.days.find((item) => item.service_date === "2026-11-20")!;
    // Dato real: Renfe anuló 3 servicios ese día. Antes de la corrección
    // engordaban `circulations_unobserved` (1182) como si fueran un fallo de
    // captura nuestro; ahora son su propia categoría y el hueco real es 1179.
    expect(day.circulations_canceled).toBe(3);
    expect(day.circulations_unobserved).toBe(1179);
  });

  it("un día real con observaciones pero sin calendario se marca fuera de programación", () => {
    const day = days.days.find((item) => item.service_date === "2026-11-19");
    expect(day).toBeDefined();
    expect(day!.circulations_scheduled).toBe(0);
    expect(day!.circulations_unscheduled).toBeGreaterThan(0);
    // Y no se presenta como un día sin actividad:
    expect(day!.circulations_observed).toBe(day!.circulations_unscheduled);
    expect(day!.first_observed_at).not.toBeNull();
  });
});

describe("métricas por línea del archivo real", () => {
  it("ninguna cobertura excede su denominador", () => {
    for (const row of lines.lines) {
      expect(row.trips_with_delay_data).toBeLessThanOrEqual(row.trips_scheduled);
    }
  });

  it("sin muestra, la puntualidad es null y se presenta como «sin muestra»", () => {
    const withoutSample = lines.lines.filter((row) => row.trips_with_delay_data === 0);
    expect(withoutSample.length).toBeGreaterThan(0);
    for (const row of withoutSample) {
      expect(row.on_time_pct_of_covered).toBeNull();
      expect(
        formatPctWithDenominator(
          row.on_time_pct_of_covered,
          row.trips_with_delay_data,
          row.trips_with_delay_data,
        ),
      ).toBe("sin muestra");
    }
  });

  it("con muestra, el porcentaje se presenta junto a su fracción real", () => {
    const withSample = lines.lines.filter((row) => row.trips_with_delay_data > 0);
    expect(withSample.length).toBeGreaterThan(0);
    for (const row of withSample) {
      const rendered = formatPctWithDenominator(
        row.delay_coverage_pct,
        row.trips_with_delay_data,
        row.trips_scheduled,
      );
      expect(rendered).toContain(`/${row.trips_scheduled}`);
    }
  });
});

describe("circulaciones observadas y huecos", () => {
  it("toda circulación observada trae su identidad completa", () => {
    expect(observed.returned).toBeGreaterThan(0);
    for (const row of observed.circulations) {
      expect(row.observed).toBe(true);
      expect(row.vehicle_id).not.toBeNull();
      expect(row.trip_id).not.toBe("");
      expect(row.service_date).toBe(observed.service_date);
      // La clave que usa Live se construye sin traducir nada:
      expect(
        circulationKey({
          vehicleId: row.vehicle_id!,
          tripId: row.trip_id,
          serviceDate: row.service_date,
        }),
      ).toBe(`${row.vehicle_id}|${row.trip_id}|${row.service_date}`);
    }
  });

  it("un hueco real llega con métricas nulas, nunca a cero", () => {
    expect(gaps.returned).toBeGreaterThan(0);
    for (const row of gaps.circulations) {
      expect(row.scheduled).toBe(true);
      expect(row.observed).toBe(false);
      expect(row.vehicle_id).toBeNull();
      expect(row.positions_count).toBeNull();
      expect(row.on_time).toBeNull();
      expect(row.delay_reported_count).toBeNull();
      expect(row.coverage).toBe("unobserved");
      expect(circulationCoverageLabel(row.coverage)).toBe("Programada sin ninguna señal");
      // Un hueco real no tiene ninguna señal: tampoco actualización de viaje.
      expect(row.trip_updates_count).toBeNull();
      expect(formatHistoryOnTime(row.on_time, row.latest_reported_delay_seconds, row.delay_reported_count)).toBe(
        "Sin dato de retraso",
      );
    }
  });

  it("el hueco conserva su horario previsto salvo que el GTFS no publique ninguno", () => {
    const withSchedule = gaps.circulations.filter(
      (row) => row.scheduled_first_departure_time !== null,
    );
    expect(withSchedule.length).toBeGreaterThan(0);
    for (const row of withSchedule) {
      // Se puede situar en el día: origen y hora previstos.
      expect(row.scheduled_first_stop_id).not.toBeNull();
      expect(formatGtfsTime(row.scheduled_first_departure_time)).toMatch(/^\d{2}:\d{2}$/);
    }
  });

  it("un viaje huérfano del GTFS real aparece sin horario, no desaparece", () => {
    // `1023V17707C5` es un viaje real del ZIP oficial cuyo `trip_id` está en
    // `trips.txt` con servicio activo pero no tiene ninguna fila en
    // `stop_times.txt`. Se conserva como fila con el horario explícitamente
    // ausente para que los dos marts del día cuenten el mismo denominador.
    const orphan = gaps.circulations.find((row) => row.scheduled_first_departure_time === null);
    expect(orphan).toBeDefined();
    expect(orphan!.scheduled).toBe(true);
    expect(orphan!.scheduled_first_stop_id).toBeNull();
    expect(formatGtfsTime(orphan!.scheduled_first_departure_time)).toBe("—");
  });
});

describe("circulaciones anuladas por el operador (hallazgo de la revisión)", () => {
  it("las tres anuladas reales se clasifican como anuladas, no como huecos", () => {
    expect(canceled.returned).toBe(3);
    expect(new Set(canceled.circulations.map((row) => row.trip_id))).toEqual(
      new Set(["1023V20865C5", "1023V21340C10", "1023V21748C2"]),
    );
    for (const row of canceled.circulations) {
      expect(row.coverage).toBe("canceled");
      expect(row.canceled).toBe(true);
      expect(row.scheduled).toBe(true);
      expect(row.observed).toBe(false);
    }
  });

  it("sin posición las métricas de posición son null; las del operador, ceros medidos", () => {
    for (const row of canceled.circulations) {
      // Posición: no se observó -> ausente, no cero.
      expect(row.positions_count).toBeNull();
      expect(row.first_observed_at).toBeNull();
      // Operador: SÍ hubo actualización -> recuento real, y un 0 que significa
      // «la actualización no traía retraso», no «no sabemos».
      expect(row.trip_updates_count).toBe(1);
      expect(row.delay_reported_count).toBe(0);
      // Y sin muestra de retraso no se emite veredicto.
      expect(row.on_time).toBeNull();
      expect(row.latest_reported_delay_seconds).toBeNull();
      expect(
        formatHistoryOnTime(row.on_time, row.latest_reported_delay_seconds, row.delay_reported_count),
      ).toBe("Sin dato de retraso");
    }
  });

  it("el detalle de una anulada trae su parte del operador y ninguna posición", () => {
    expect(canceledDetail.circulation.coverage).toBe("canceled");
    expect(canceledDetail.positions).toEqual([]);
    expect(canceledDetail.delays.length).toBeGreaterThan(0);
    expect(COVERAGE_DETAILS.canceled).toContain("no circuló");
  });
});

describe("detalle de una circulación real", () => {
  it("las observaciones llegan en orden temporal", () => {
    const stamps = detail.positions.map((position) => Date.parse(position.observed_at));
    expect(stamps.length).toBeGreaterThan(0);
    expect(stamps).toEqual([...stamps].sort((a, b) => a - b));
  });

  it("el recuento de posiciones del mart coincide con las observaciones devueltas", () => {
    expect(detail.circulation.positions_count).toBe(detail.positions.length);
  });

  it("el veredicto de puntualidad corresponde al último retraso reportado", () => {
    const reported = detail.delays.filter((row) => row.delay_coverage === "reported");
    expect(reported.length).toBe(detail.circulation.delay_reported_count);
    const latest = reported[reported.length - 1];
    expect(detail.circulation.latest_reported_delay_seconds).toBe(latest.delay_seconds);
  });
});

describe("métricas por estación", () => {
  it("vienen de más observada a menos", () => {
    const counts = stations.stations.map((row) => row.observations_count);
    expect(counts).toEqual([...counts].sort((a, b) => b - a));
  });
});
