import { expect, test } from "vitest";
import fixture from "../../../../tests/fixtures/mp025a/frames.json";
import { phase, progressAt } from "./movement";
import type { ProgressEnvelope } from "./contract";

for (const item of fixture) {
  test(item.case, () => {
    const envelope = item.envelope as ProgressEnvelope;
    for (const [instant, progress, expectedPhase] of item.frames) {
      expect(Math.abs(progressAt(envelope, Number(instant)) - Number(progress))).toBeLessThanOrEqual(1e-6);
      expect(phase(envelope, Number(instant))).toBe(expectedPhase);
    }
  });
}

test("fase antes de la referencia sin causa inicial", () => {
  const envelope = fixture.find(item => item.envelope.speed_mps > 0 && item.envelope.hold_reason === null)!.envelope as ProgressEnvelope;
  expect(phase(envelope, Date.parse(envelope.reference_at) - 1)).toBe("hold:null");
});
