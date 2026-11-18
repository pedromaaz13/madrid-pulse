# ADR-0001: Alcance del MVP limitado a la línea C5

- **Estado:** Aceptado
- **Fecha:** 2026-11-18
- **Decisores:** Propietario del repositorio, con fundamento en `docs/research/deep-research-report.md`

## Contexto

Madrid Pulse aspira a cubrir toda la red de Cercanías Madrid y, después, el resto de España. Construir eso directamente implica validar simultáneamente identificación de trenes, cobertura de geometría, calidad de datos y contratos de API sobre una superficie grande, con mayor riesgo de encontrar problemas de escala antes de validar lo fundamental.

## Decisión

El MVP se limita a la línea **C5** de Cercanías Madrid. Ninguna tarea de MP-001 a MP-015 implementa otra línea. La ampliación a toda la red Madrid (Fase F10 en `docs/PLAN.md`) y después a España es posterior y explícitamente fuera de alcance del backlog actual.

## Alternativas consideradas

- **Toda la red de Cercanías Madrid desde el inicio:** descartada — mayor superficie de validación de datos sin beneficio adicional para probar la arquitectura.
- **Otra línea distinta a la C5:** no evaluada en profundidad; C5 se adopta como preferencia explícita del brief inicial sin que se documenten alternativas comparadas.

## Consecuencias

- Los contratos de datos y el modelo deben ser extensibles a más líneas sin rediseño (`network`/`route` como entidades desde el día uno en `docs/DATA_MODEL.md`), aunque solo se pueble con C5.
- MP-010/MP-011 (topología y geometría) se acotan a C5; extender a otra línea repite ese trabajo, no lo generaliza automáticamente.
