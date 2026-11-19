# ADR-0004: Modelo de posición en cuatro estados

- **Estado:** Aceptado (principio y estados); defaults calibrados en MP-012, todavía configurables
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

- MP-012 mantuvo `60s`/`180s` como defaults configurables después de calibrarlos: `vehicle_positions` se actualizó cada ~20–22 s en MP-003, de modo que representan aproximadamente 3 y 8 actualizaciones perdidas. No son verdad de fuente ni constantes ocultas; viven en `MovementThresholds`.
- El límite de interpolación física (`160 km/h`) es distinto del filtro de salto inutilizable del feed (`900 km/h`). MP-008 observó saltos crudos reales de 246–787 km/h y la validación map-matched de MP-012 midió 666,4 km/h; tratarlos como velocidad continua sería incorrecto, pero descartarlos con un corte ferroviario convencional también eliminaría observaciones reales.
- Todo endpoint de vehículo en vivo debe exponer estos campos sin excepción (ver `docs/DATA_CONTRACTS.md`).
