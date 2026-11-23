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
const detail = fixture.circulation_detail as unknown as HistoryCirculationDetail;
const stations = fixture.stations as unknown as HistoryStations;

describe("índice de días archivados", () => {
  it("los días vienen de más reciente a más antiguo", () => {
    const dates = days.days.map((day) => day.service_date);
    expect(dates).toEqual([...dates].sort().reverse());
  });

  it("los recuentos de cada día cierran: nada se pierde ni se cuenta dos veces", () => {
    for (const day of days.days) {
      // Toda fila del mart es, o programada, o observada fuera de programación.
      expect(day.rows_total).toBe(day.circulations_scheduled + day.circulations_unscheduled);
      // Y de lo programado, lo que no se observó es exactamente el hueco.
      const scheduledAndObserved = day.circulations_observed - day.circulations_unscheduled;
      expect(day.circulations_scheduled).toBe(scheduledAndObserved + day.circulations_unobserved);
      expect(scheduledAndObserved).toBeGreaterThanOrEqual(0);
    }
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
      expect(circulationCoverageLabel(row.scheduled, row.observed)).toBe(
        "Programada sin observar",
      );
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
