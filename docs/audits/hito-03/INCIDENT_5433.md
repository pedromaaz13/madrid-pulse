# Incidente PostgreSQL 5433 — investigación y propuesta (sin ejecución)

**Estado: RESUELTO por decisión del propietario (2026-11-24): CONSERVAR.** Investigado en solo lectura. **No se ha ejecutado ningún `DELETE`, `UPDATE` ni `INSERT`.**
**Fecha:** 2026-11-23 · **Investigó:** coordinador (Claude), solo consultas `SELECT`/`pg_dump`.

## 1. Qué es la base 5433
Contenedor Docker `madrid-pulse-postgres-1` (`postgis/postgis:17-3.5`, arrancado 2026-11-19, volumen persistente `madrid-pulse-postgres-data`). Es la base de **desarrollo local compartida por todo el proyecto**, no un entorno desechable. Contiene el histórico real del soak de MP-007 (línea base reverificada al cierre de cada tarea: `668/484/3/120/0`). No contiene datos de producción de terceros ni credenciales distintas de las locales por defecto.

## 2. Qué ocurrió
- AUD-06 (Codex `gpt-5.6-terra`, dispatch `ctx_cf7d40a866d7`) ejecutó un comando de diagnóstico del supervisor **sin la variable de entorno que aísla la base**. El colector real arrancó con su valor por defecto y completó **dos ciclos completos contra los feeds públicos de Renfe/CRTM**, insertando en 5433. El propio worker lo detuvo (18:05:40Z) y lo escaló sin que nadie se lo pidiera.
- **Causa raíz de diseño (hallazgo nuevo):** `services/collector/config.py:34` y `apps/api/config.py:34-35` tienen como valor por defecto `postgresql://…@127.0.0.1:5433/madrid_pulse`. Cualquier ejecución sin variable apunta a la base compartida. No hay guarda ni confirmación. Es un riesgo de proceso independiente del error del worker.

## 3. Alcance verificado (consultas de solo lectura)
Filas añadidas, todas con `started_at` entre 17:04:46Z y 17:05:18Z del 2026-11-23:

| Tabla | Antes | Ahora | Añadidas | Claves |
|---|---|---|---|---|
| `source_ingestion_run` | 120 | 126 | 6 | `id` 3090–3095 |
| `vehicle_position_observation` | 668 | 895 | 227 | `id` 6097–6323 (`ingestion_run_id` 3090 y 3093: 113+114) |
| `trip_update_observation` | 484 | 646 | 162 | `id` 1005–1166 (runs 3091 y 3094: 116+46) |
| `service_alert` | 3 | 8 | 5 | `id` 244–248 (run 3092) |
| `data_quality_event` | 0 | 8 | 8 | `id` 6148–6155, todos `implausible_speed`, `occurred_at` 17:05:17.721726Z |

- Las filas anteriores a la run 3090 siguen exactamente en `668/484/3/120/0`: la operación fue **solo aditiva**. `max(source_ingestion_run.id)` sigue siendo 3095, es decir, no ha habido escrituras posteriores (ni de AUD-06 ni de AUD-08).
- `pg_stat_user_tables.n_tup_upd = 0` en las cinco tablas: nunca ha habido `UPDATE`.
- **Dependencias:** nadie referencia las filas nuevas. Las FK existentes apuntan *hacia* `source_ingestion_run` desde `vehicle_position_observation`, `trip_update_observation` y `service_alert` (las filas nuevas de esas tres tablas cuelgan de las runs 3090–3095). `data_quality_event` no tiene FK ni run asociada. `trip_id` es `NULL` en las 227 posiciones nuevas (el colector no lo puebla: hallazgo ya registrado en AUD-06). `daily_line_metrics` y `station_daily_metrics` están vacías. Un único trigger no interno (`layer_integrity_checks` en `layer`), sin relación.
- Un `pg_dump -Fc` completo previo a cualquier decisión se guardó como evidencia fuera del repositorio: `<SCRATCHPAD>/madrid_pulse_5433_pre_decision.dump` (140 104 B, SHA-256 `e319e8e447cd1f4924bc3049d20c2ce3246bf9b89d7d41c4c39262009c4727d7`).

Dato adicional: los 8 eventos `implausible_speed` son datos reales de Renfe (entidades `19711`, `19712`, `20886`, `20297`, `20878`, `20883`, `20629`, `21244`) y ilustran en vivo el hallazgo AUD04-P2 (el evento se guarda en `data_quality_event` pero no llega al directo).

## 4. ¿Incumplió las restricciones de la auditoría?
**Sí, en dos sentidos:**
1. El encargo prohíbe "modificar … base de datos persistente" durante la auditoría y la spec de AUD-06 exigía contenedores propios. Hubo escritura real en una base persistente.
2. Fue **accidental, aditiva, no destructiva, detenida y comunicada por el propio ejecutor en minutos**; no se alteró ni borró ningún dato previo.

Su informe `BACKEND_OPERATIONS_AUDIT.md` decía inicialmente lo contrario (que no se tocó la base compartida); el revisor de AUD-08 lo detectó y se corrigió en `2d02227`.

## 5. ¿Usa AUD-08 la misma base?
No. AUD-08 usó un contenedor propio (`aud08-postgis`, 5548); su revisor otro (5561); los revisores de AUD-05/AUD-06 contenedores desechables (5799 y otros). Verificado además por el hecho de que `max(id)=3095` no ha cambiado desde el incidente. Pero **un efecto colateral relevante**: la comprobación histórica "suite sin skips contra desarrollo" **ya no reproduce** contra 5433 (los recuentos que ciertos tests esperan, 668/484, cambiaron). Es una limitación de reproducibilidad que AUD-09 debe consignar.

Nota: el ejecutor de AUD-08 recibió la instrucción de no escribir en 5433. Cualquier futura necesidad de escritura debe usar un entorno desechable.

## 6. Propuesta (no ejecutada)
### Opción A — Conservar (recomendada si no hay motivo para restaurar el invariante)
Son datos reales, bien formados, trazables (`source_ingestion_run` 3090–3095) y no corrompen nada. Coste: la línea base `668/484/3/120/0` deja de ser el invariante de comprobación; habría que redefinirla como `895/646/8/126/8` en los documentos de cierre y en los tests que la citan. Riesgo: bajo.

### Opción B — Limpiar (restaura el invariante)
Alcance exacto: 6 runs + 227 + 162 + 5 + 8 filas. Orden: hijos antes que padres.
Prerrequisitos: (1) backup verificado (ya existe el `.dump`; repetir `pg_dump` inmediatamente antes y comprobar su SHA-256); (2) confirmar con `SELECT max(id) FROM source_ingestion_run` que sigue en 3095 (si no, **parar**: alguien ha escrito más); (3) ningún colector ni test corriendo contra 5433.

```sql
BEGIN;
-- Hijos de las runs del incidente
DELETE FROM vehicle_position_observation WHERE ingestion_run_id BETWEEN 3090 AND 3095;  -- esperado: 227
DELETE FROM trip_update_observation       WHERE ingestion_run_id BETWEEN 3090 AND 3095;  -- esperado: 162
DELETE FROM service_alert                 WHERE ingestion_run_id BETWEEN 3090 AND 3095;  -- esperado: 5
-- Eventos de calidad (sin FK): clave exacta, no por rango temporal amplio
DELETE FROM data_quality_event
 WHERE id BETWEEN 6148 AND 6155
   AND occurred_at = '2026-11-23 17:05:17.721726+00';                                     -- esperado: 8
-- Padres
DELETE FROM source_ingestion_run WHERE id BETWEEN 3090 AND 3095;                          -- esperado: 6

-- Verificación: si no coincide, ROLLBACK
DO $$
DECLARE vp int; tu int; al int; ru int; dq int;
BEGIN
  SELECT count(*) INTO vp FROM vehicle_position_observation;
  SELECT count(*) INTO tu FROM trip_update_observation;
  SELECT count(*) INTO al FROM service_alert;
  SELECT count(*) INTO ru FROM source_ingestion_run;
  SELECT count(*) INTO dq FROM data_quality_event;
  IF (vp,tu,al,ru,dq) <> (668,484,3,120,0) THEN
    RAISE EXCEPTION 'linea base no restaurada: % % % % %', vp,tu,al,ru,dq;
  END IF;
END $$;
COMMIT;
```
Pruebas de verificación posteriores: (a) recuentos `668/484/3/120/0`; (b) `max(source_ingestion_run.id)` ≤ 195 en las filas conservadas; (c) `pg_restore --list` del dump previo intacto; (d) reproducir `apps.api.tests.test_snapshot_contract` contra 5433 como antes.
Efecto residual: las secuencias `id` **no retroceden** (quedan huecos; inocuo). `VACUUM` opcional.
Ejecutable solo con tu aprobación expresa; no se ha ejecutado.

### Medida preventiva (independiente de A/B, para H4)
Quitar el valor por defecto que apunta a 5433 en `services/collector/config.py` y `apps/api/config.py` (fallar si falta la variable) o exigir confirmación explícita. No se implementa en esta auditoría.

## 7. Decisión del propietario (2026-11-24)
- **CONSERVAR** los datos añadidos por AUD-06. **No se autoriza** ningún `DELETE`, `TRUNCATE`, restauración ni modificación adicional sobre la base 5433. La "Opción B" de la sección 6 queda **descartada y no debe ejecutarse**; se conserva solo como registro.
- Se mantienen este documento, las claves de las filas afectadas (sección 3), la evidencia de procedencia y la copia de seguridad existente. **El dump no se incorpora al repositorio** (permanece fuera, en el scratchpad de la sesión).
- **Limitación de reproducibilidad conservada explícitamente:** la base 5433 **no debe usarse** para establecer resultados de pruebas reproducibles que dependan de su estado original. La verificación histórica "suite sin skips contra desarrollo" (`668/484/3/120/0`) **ya no es reproducible** contra 5433; la nueva línea base de esa base es `895/646/8/126/8`. Cualquier prueba reproducible debe usar un PostgreSQL desechable con migraciones desde cero.
- **Hito 4 (planificación autorizada, implementación no):** tarea específica para eliminar defaults peligrosos de PostgreSQL en `services/collector/config.py` y `apps/api/config.py` (configuración explícita por entorno, protección contra escrituras accidentales, aislamiento de tests, fallo seguro si falta configuración). Ejecutor propuesto `gpt-6.2-sol` Medium; revisor independiente `claude-sonnet-5-5` High (en Orca: `sonnet`); con pruebas de regresión y criterios de aceptación reproducibles. Debe verificarse la disponibilidad real del modelo al despachar.
