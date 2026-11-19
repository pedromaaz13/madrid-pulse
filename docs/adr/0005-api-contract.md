# ADR-0005: Contrato de API propio versionado

- **Estado:** Propuesto — lista de endpoints de trabajo sujeta a confirmación en MP-013
- **Fecha:** 2026-11-18
- **Decisores:** Propietario del repositorio, con fundamento en `docs/research/deep-research-report.md` y `docs/research/MADRID_PULSE_BRIEF_INICIAL.md`

## Contexto

El informe completo y el brief inicial proponen conjuntos de endpoints no idénticos (ver discrepancia detallada en `docs/DATA_CONTRACTS.md`). Ninguno de los dos debe copiarse de la estructura de Via Península ni de Valfiguer: Madrid Pulse define su propio contrato versionado.

## Decisión

Madrid Pulse expone una API propia bajo `/api/v1/*`, con la lista de endpoints de trabajo documentada en `docs/DATA_CONTRACTS.md` (fusión de las dos propuestas de la investigación). Todo cambio incompatible de contrato requiere una nueva versión (`/api/v2/`), nunca una mutación silenciosa de una versión existente. Toda respuesta de vehículo en vivo debe incluir campos de frescura/calidad (`position.mode`, `position.confidence`, `observation.age_s`, `delay.coverage`, `quality.flags`).

## Alternativas consideradas

- **Adoptar literalmente el contrato de Valfiguer o de Via Península:** descartada — impide evolucionar el contrato de forma independiente y mezcla la semántica de un tercero con las garantías propias de calidad que Madrid Pulse quiere ofrecer.
- **API sin versionado explícito en la ruta:** descartada — dificulta evolucionar el contrato sin romper consumidores.

## Consecuencias

- MP-013 debe resolver formalmente la discrepancia de nomenclatura (`vehicles` vs `trains`, fusión de `health` + `quality/feeds`) documentada en `docs/DATA_CONTRACTS.md` antes de implementar, y actualizar este ADR con la decisión final.
- Cualquier consumidor externo de la API (incluido el propio frontend) depende de `/api/v1/*` como contrato estable hasta que se publique una v2.
