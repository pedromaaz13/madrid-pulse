# Hito 3 — Dossier para decisión de integración

## Estado de la cadena

| Tarea | Previsto | Entregado / evidencia | Estado |
|---|---|---|---|
| MP-016 | Fiabilidad realtime | SKIPPED, UTC, Live/Replay, salud separada; replay 119/121 y 49 SKIPPED | DONE |
| MP-017 | Catálogo Madrid | 12 líneas, 42 rutas, identidad, calendario, 24:xx, servicios programados | DONE |
| MP-018 | Corredores | 103 patrones; 28 validados, 3 parciales, 72 pendientes; raw/matched trazable | DONE |
| MP-019 | Snapshot/API | catálogo cacheable, revisión monotónica, raw/matched/rendered, tablero y ETA | DONE |
| MP-020 | Mapa/tablero | map-first, búsqueda, selección, seguimiento, móvil, teclado, sin WebGL | DONE |
| MP-021 | History/Explore | archivo idempotente, histórico por circulación, cobertura y huecos | DONE |
| MP-022 | Auditoría integral | matriz, replay, fixtures sintéticas, benchmark API/frames/memoria y recorrido navegador completo | DONE |

Las nueve puertas tienen evidencia, los dos hallazgos reales (sustitución
silenciosa de día en History; dos tests nuevos fuera de CI) están corregidos
con regresión, y Claude auditó el diff completo de forma independiente sin
hallazgos abiertos. **El Hito 3 está completo** — la cadena `MP-016`→`MP-022`
queda `DONE` en su totalidad. No hay push, PR ni merge efectuados por
agentes: la integración a `main` sigue siendo decisión exclusiva del
propietario.

## Cobertura de Madrid

La matriz canónica está en [`mp-022-coverage.csv`](mp-022-coverage.csv) y su
lectura humana en [`mp-022-coverage.md`](mp-022-coverage.md).

- Catálogo: 12 líneas / 42 rutas / 103 patrones.
- Día de servicio 2026-11-20: 1 299 instancias con `stop_times`; MP-021 conserva
  además 5 viajes programados huérfanos para que el denominador histórico sea
  1 304, sin inventarles horario.
- Corte 1533: 121 observaciones exactas, todas resueltas contra ruta programada.
- C4: 0 GPS en el corte; porcentaje `null`, 13 servicios programados, 5/5
  patrones geométricos validados. No se inventa ningún tren.
- Geometría total: 28/103 patrones map-matcheables. Los restantes mantienen
  catálogo/horario y, cuando hay GPS, posición raw etiquetada; no se proclama
  cobertura geométrica plena.
- `drawable_positions` no significa `matched_positions`: el CSV conserva
  ambas columnas para impedir esa confusión.

## Decisiones pendientes del propietario

### ADR propuestos

- **ADR-0014** — contrato temporal/snapshot. Sigue `Propuesto`; MP-022 no lo
  promueve a `Aceptado`.
- **ADR-0015** — archivo frío e histórico. Sigue `Propuesto`; la evidencia de
  idempotencia y recuperación no sustituye la decisión del propietario.

### DECs abiertas

- **DEC-033 (b):** umbral de puntualidad de 300 s sin histórico suficiente
  para calibración.
- **DEC-033 (c):** `data_quality_event.entity_ref` todavía no atribuye eventos
  a una parada.
- **DEC-038:** pool PostgreSQL; el benchmark vuelve a mostrar coste relevante
  de abrir conexiones, pero MP-022 no introduce una dependencia arquitectónica.
- **DEC-004:** retención definitiva. MP-021 midió ≈19 MB/día y ≈7 GB/año en
  Parquet ZSTD; la política final sigue siendo decisión del propietario.

## Operación y costes

No existe despliegue persistente ni «24/7 verificado». MP-021 midió 13 min 43 s
de operación supervisada y proyectó costes/volumen; MP-022 no convierte esa
ventana en una afirmación de 24/7. No se contrató ningún servicio de pago ni se
instaló un agente en la máquina del propietario.

## Roadmap explícitamente no iniciado

Según `docs/hitos/hito-03/SIGUIENTES-HITOS.md`, quedan fuera de esta autorización:

- AVE / Larga Distancia / Media Distancia;
- nuevos operadores y sus contratos/licencias;
- operación y monitorización 24/7 reales;
- despliegue público, cuentas, SQL Lab, broker u otra infraestructura
  distribuida.

Ninguno se presenta como trabajo parcial de Hito 3 ni como cobertura actual.

## Checklist del propietario

- [x] Revisor Claude inspeccionó el diff completo (dos rondas) y repitió las
  suites críticas dos veces contra PostgreSQL desechable propio (283/283
  Python, 89/89 frontend).
- [x] Revisor ejecutó recorrido integrado desktop y móvil 390 px con
  navegador real, teclado, reduced motion y fallback sin WebGL.
- [x] Revisor registró frames y memoria, separados de la animación continua;
  el endpoint legado de 1,6/2,1 s queda registrado fuera del camino frontend.
- [x] Revisor auditó la corrección del día no archivado y del hallazgo de CI
  (dos módulos de test fuera del workflow), sin hallazgos abiertos; MP-022
  cambiado a `DONE` en TASKS/STATUS/CHANGELOG el 2026-11-23. **Cierra la
  cadena completa del Hito 3.**
- [ ] Propietario decide ADR-0014/0015 y DECs abiertas.
- [ ] Solo el propietario realiza push, PR y merge (las siete ramas del hito
  están listas y encadenadas, ninguna fusionada).
