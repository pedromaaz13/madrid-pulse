# ADR-0004: Modelo de posición en cuatro estados

- **Estado:** Aceptado (principio y estados), umbrales **propuestos, pendientes de calibración real**
- **Fecha:** 2026-11-18
- **Decisores:** Propietario del repositorio, con fundamento en `docs/research/deep-research-report.md`

## Contexto

Los feeds GTFS-RT en vivo pueden ser demasiado discontinuos para animar directamente, y algunos puntos reportados pueden implicar velocidades físicamente implausibles. Presentar cualquier posición interpolada o estimada como si fuera una lectura GPS real sería engañoso para el usuario y contrario a los principios de transparencia del producto.

## Decisión

El motor de movimiento opera siempre en uno de cuatro estados explícitos, expuestos en el contrato de API (`docs/DATA_CONTRACTS.md`):

```text
OBSERVED    0–60 s        confidence alta
ESTIMATED   60–180 s      confidence decreciente
STALE       >180 s        dato obsoleto
SCHEDULED   sin datos      solo horario GTFS
```

Cada posición expone `position_mode`, `confidence`, `age_s` y `source`. Nunca se presenta una posición `estimated`/`scheduled` con la misma semántica visual que una `observed` en el frontend (MP-014).

Pipeline de cálculo: GPS reciente y plausible → map-match al track → localizar distancia acumulada sobre shape → estimar progreso esperado por horario → calcular offset temporal → interpolar hasta siguiente observación → limitar aceleración/velocidad/retrocesos imposibles.

## Alternativas consideradas

- **Interpolación lineal simple sin estados explícitos:** descartada — oculta al usuario cuándo el dato es una estimación en lugar de una observación real, contrario a la diferenciación transparencia que diferencia a Madrid Pulse de alternativas puramente visuales.
- **Solo dos estados (`live`/`no-data`):** descartada — pierde granularidad útil entre "dato reciente" y "dato viejo pero aún razonable como estimación".

## Consecuencias

- Los umbrales `60s`/`180s` son los propuestos por la investigación como punto de partida, **no verdad de diseño**: MP-012 debe calibrarlos contra datos reales de frecuencia de actualización medidos en MP-003.
- Todo endpoint de vehículo en vivo debe exponer estos campos sin excepción (ver `docs/DATA_CONTRACTS.md`).
