// MP-024 · AC-15: equivalencia Python↔TypeScript de la envolvente.
//
// Evalúa el `progressAt` de PRODUCCIÓN (apps/web/src/domain/movement.ts,
// transpilado sin cambios a CommonJS con tsc, ver README) sobre el fixture
// que escribe `stop_state_comparison.py --fixture-out`, y lo compara con los
// valores que calculó `ProgressEnvelope.progress_at` de Python.
//
// - `ms`: instantes serializados en milisegundos (contrato propuesto §4.3 c).
// - `micro`: la misma envolvente con la referencia desplazada 0,7 ms y
//   serializada con microsegundos; `Date.parse` los trunca, así que aquí se
//   espera una discrepancia > 1e-6 m (demuestra por qué el contrato exige ms).
// - `phase`: la función de fase de §4.3 b es un PROTOTIPO (no existe todavía en
//   producción); se implementa aquí igual que en Python para comprobar que la
//   especificación da el mismo resultado en ambos lenguajes.
//
// Uso: node ts_equivalence.cjs <movement.js transpilado> <fixture.json>

"use strict";
const fs = require("fs");
const [, , modulePath, fixturePath] = process.argv;
const { progressAt } = require(modulePath);
const fixture = JSON.parse(fs.readFileSync(fixturePath, "utf8"));

function phase(item, atMs) {
  const env = item.envelope;
  const t0 = Date.parse(env.dwell_until ?? env.reference_at);
  if (env.speed_mps === 0 || atMs < t0) return `hold:${item.hold_reason}`;
  if (item.cap_reached_at !== null && atMs >= Date.parse(item.cap_reached_at)) return `cap:${item.cap_kind}`;
  return "moving";
}

let maxMs = 0;
let samplesMs = 0;
let phaseMismatch = 0;
for (const item of fixture.ms) {
  for (const s of item.samples) {
    samplesMs += 1;
    maxMs = Math.max(maxMs, Math.abs(progressAt(item.envelope, s.at_ms) - s.progress_m));
    if (phase(item, s.at_ms) !== s.phase) phaseMismatch += 1;
  }
}
let maxMicro = 0;
for (const item of fixture.micro) {
  for (const s of item.samples) {
    maxMicro = Math.max(maxMicro, Math.abs(progressAt(item.envelope, s.at_ms) - s.progress_m));
  }
}
const result = {
  envolventes_ms: fixture.ms.length,
  muestras_ms: samplesMs,
  max_abs_delta_ms_m: maxMs,
  ms_pasa_1e6: maxMs <= 1e-6,
  fases_distintas: phaseMismatch,
  envolventes_micro: fixture.micro.length,
  max_abs_delta_micro_m: maxMicro,
  micro_pasaria_1e6: maxMicro <= 1e-6,
};
console.log(JSON.stringify(result, null, 1));
process.exit(result.ms_pasa_1e6 && phaseMismatch === 0 ? 0 : 1);
