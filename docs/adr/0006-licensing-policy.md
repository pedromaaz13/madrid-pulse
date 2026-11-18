# ADR-0006: Política de licenciamiento frente a proyectos de referencia

- **Estado:** Aceptado (política), licencia del código propio **pendiente** (ver DEC-002)
- **Fecha:** 2026-11-18
- **Decisores:** Propietario del repositorio, con fundamento en `docs/research/deep-research-report.md`

## Contexto

Via Península está publicado bajo AGPL-3.0, licencia diseñada para que las modificaciones de software accesible por red ofrezcan también el código fuente de la obra derivada. Estudiar su arquitectura es legítimo; copiar o derivar directamente su implementación dentro de Madrid Pulse impondría obligaciones AGPL sobre la obra derivada, lo cual puede ser incompatible con la licencia que el propietario elija para el código propio (DEC-002, todavía pendiente).

## Decisión

**Clean-room conceptual.** Madrid Pulse puede leer y estudiar Via Península (README, ADRs, código publicado) para entender problemas, interfaces, edge cases y arquitectura. La implementación propia se escribe desde cero basándose en especificaciones propias, GTFS, GTFS-RT y OSM — **nunca copiando código fuente de Via Península**.

Si en el futuro se quisiera incorporar código literal de Via Península, eso requiere un ADR específico nuevo que evalúe explícitamente las obligaciones AGPL-3.0 resultantes y sea aprobado por el propietario antes de proceder. Por defecto, esto **no está autorizado**.

Valfiguer se trata de forma distinta: no hay evidencia de que su implementación sea un repositorio público verificado, por lo que se usa solo como referencia de producto/funcionalidad (benchmark), nunca como fuente de código ni como dependencia de API en producción.

## Alternativas consideradas

- **Adoptar AGPL-3.0 para Madrid Pulse y reutilizar código de Via Península donde convenga:** no descartada de forma permanente, pero no es la decisión actual — requeriría que DEC-002 (licencia propia) se resolviera en esa dirección explícitamente, lo cual no ha ocurrido.
- **Ignorar la licencia y copiar igualmente:** rechazada — riesgo legal y reputacional para un proyecto que aspira a ser open source serio.

## Consecuencias

- Ningún agente (Claude Code, Codex) debe copiar código de Via Península bajo ninguna circunstancia sin este ADR actualizado.
- `AGENTS.md` y `CLAUDE.md` deben reflejar esta restricción como regla operativa (ya lo hacen).
- La licencia final del código propio de Madrid Pulse (DEC-002) debe considerar esta restricción si en algún momento se evalúa reutilizar código de Via Península.
