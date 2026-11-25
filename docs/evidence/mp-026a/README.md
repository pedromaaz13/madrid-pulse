# MP-026a · Entrega para revisión independiente

## Ronda 2 · Correcciones sobre `fe0ea85`

Código y pruebas de la ronda en `fd8e43af40e3bcfdc3fe3522ca4fc5f1bb467a83`.

| Hallazgo | Corrección | Evidencia |
|---|---|---|
| B1 | Normalizar `at` a UTC y devolver 400 si la conversión desborda o la fecha queda fuera del intervalo operativo inclusivo del `0001-01-04` al `9999-12-28`. El margen de tres días en ambos extremos cubre el calendario de Madrid y la ventana del tablero. | Cuatro instantes extremos con UTC y offsets en las cuatro rutas. En ambos bordes incluidos el tablero devuelve 200 con la ventana máxima. [RED](ronda-2/red.txt), [GREEN](ronda-2/green.txt). |
| A1 | Aplicar el corte por inicio de ingesta al listado y al detalle de vehículos. Ambos usan el reloj real de la petición y la misma consulta de retrasos. | Antes se devolvía el segundo corte con HTTP 200. Ahora su vehículo exclusivo da 404 y listado y detalle coinciden en la observación y el retraso del primer corte. [RED](ronda-2/red.txt), [GREEN](ronda-2/green.txt). |
| A2 | Publicar `resource: "gtfs"` en `snapshot.degraded[]` con causa y fecha para `expiring`, `expired` y `not_yet_valid`. | La regresión verifica los tres avisos, sus campos de edad y feed a `null` y la ausencia del aviso para `valid`. [RED](ronda-2/red.txt), [GREEN](ronda-2/green.txt). |
| A3 | Indicar en `contract.ts` que la UI consume la vigencia del snapshot. `catalogIndex.ts` explica que los índices se reutilizan por `catalog_version`. | Solo comentarios en los dos ficheros web de esta ronda. [Lint, typecheck, tests y build](ronda-2/frontend.txt). |
| A4 | Documentar las excepciones de compatibilidad de `poll_age_s`, `feeds` y ETag. Subir los esquemas de snapshot y catálogo a `1.1` e incluir la versión del esquema en el ETag. | Los consumidores tipan `schema_version` como cadena. El literal `1.0` de las fixtures es un dato de prueba. El contrato congelado se regeneró y su comprobación pasó. [Contrato](../../DATA_CONTRACTS.md), [GREEN](ronda-2/green.txt). |
| A5 | Filtrar por `observed_at <= reloj` solo en replay. Live conserva las observaciones adelantadas de ingestas elegibles. | El mismo GPS y retraso adelantados quedan fuera de replay y aparecen en live en snapshot, tablero y rutas de vehículos. [RED](ronda-2/red.txt), [GREEN](ronda-2/green.txt). |
| A6 | Extender a health y catalog la prueba de rechazo de `at` en live y la regresión de B1. | El caso de preservación pasa tanto en `fe0ea85` como después. B1 pasa de 500 a 400 en las cuatro rutas. [RED](ronda-2/red.txt), [GREEN](ronda-2/green.txt). |

**Criterio de aceptación para MP-030.** Conservar un mismo
`catalog_version` en la caché del cliente y recibir snapshots del 18 y del 20
de diciembre con el ZIP del kit. La interfaz muestra primero que el GTFS
vence el 19 y después que venció el 19. El estado y el motivo visible
provienen de `snapshot.gtfs_status` y de la entrada `gtfs` de
`snapshot.degraded[]`. Al pasar a un snapshot `valid`, desaparece ese aviso.
Esta ronda verifica el contrato que alimenta el aviso mediante HTTP.

| Resultado | Comando ejecutado | Evidencia |
|---|---|---|
| FAIL esperado | `python -m unittest apps.api.tests.test_temporal_replay -v` sobre `fe0ea85` con el módulo de la ronda 2 | 13 casos y 21 fallos al contar subtests. Se observan 16 respuestas 500 en B1, tres avisos ausentes en A2, el vehículo futuro de A1 y la observación live descartada de A5. [RED](ronda-2/red.txt). |
| PASS | `python -m unittest <29 módulos del job python de CI> -v` | 296 casos, los 292 anteriores y cuatro nuevos, con 18 skips previstos. Los hashes del módulo y de las fixtures coinciden con RED. [GREEN y comando completo](ronda-2/green.txt). |
| PASS | `npm run lint && npm run typecheck && npm test && npm run build` | Node 22.13.1, 89 tests web y build verificado. Vite informa del tamaño de chunks. [Frontend](ronda-2/frontend.txt). |
| PASS | `python scripts/governance/check_docs.py && python -m unittest tests.governance.test_governance -v` | 36 tests de gobernanza. [Gobernanza](ronda-2/governance.txt). |
| PASS | `comprobar.py` y `replay_real.py ingest` seguido de `replay_real.py probe` | Kit congelado verificado. Se mantienen los 6 s y 119 vehículos en el corte intermedio y los estados de vigencia de los tres endpoints con el ZIP real. [Comandos y hashes](ronda-2/replay-real.txt). |

DSN desechable `postgresql://mp026a_r2:mp026a_r2_local@127.0.0.1:5453/madrid_pulse`.
El primer intento de aplicar la migración 0001 precedió al arranque de
PostgreSQL. Tras verificar `pg_isready` se aplicaron ambas migraciones desde
cero y se comprobó la marca desechable. El contenedor, su volumen y el
checkout RED se eliminaron. [Aislamiento](ronda-2/database.txt).

Orca identifica el modelo de esta corrección como `gpt-6.2-sol` en la
proyección de `worker-show` para `ctx_229fd7e90c81`. La validación visual del
aviso queda para MP-030 y el dictamen de esta ronda para Claude Opus High.

## Primera ronda

Base de trabajo MP-023 `becaf7f`. Línea base de las regresiones `beb9434`.
Código y pruebas verificados en `83e474158ffa185c3d8e88e6bb454c149e7bd849`.
El commit posterior reúne la evidencia y aclara en el contrato escrito cómo
avanza la revisión durante el replay.

### Cambios

- FR-02. Health y snapshot comparten el corte inclusivo de ingestas
  `started_at <= reloj`. Snapshot y tablero lo aplican también a las
  posiciones, retrasos y revisión. La ausencia de ingesta elegible
  aparece como `unknown`, con edades `null` y causa
  `no_ingestion_at_or_before_clock`. Una marca de origen adelantada
  conserva su propio motivo y la edad del sondeo.
- FR-19. Health, catálogo y snapshot publican la vigencia GTFS y su causa
  según el reloj de la petición y la fecha de Madrid. El aviso por defecto
  es de siete días. Se conservan el HTTP 400 para `at` en live y el rechazo
  en el arranque live fuera de vigencia. La versión estática del catálogo
  sigue siendo el enlace con snapshot. El ETag incluye la vigencia y el modo.
  [Procedimiento de refresco](../../operations/GTFS_STATIC_REFRESH.md).
- Coordinación con MP-030. El único fichero web que cambia es
  `apps/web/src/domain/contract.ts`. Añade los metadatos opcionales para
  admitir las fixtures anteriores y refleja que `FeedHealth.poll_age_s`
  acepta `null`. El test anterior del ETag comprueba ahora la identidad
  completa de la respuesta y conserva la verificación de `304`.

### Comprobaciones

| Resultado | Comando ejecutado | Evidencia |
|---|---|---|
| FAIL esperado | `python -m unittest apps.api.tests.test_temporal_replay -v` sobre `beb9434` | [RED](red.txt). Siete métodos reproducen comportamientos defectuosos, con 40 fallos al contar los subtests. Los dos casos de preservación pasan en ambas versiones porque el baseline ya rechazaba `at` para snapshot y tablero live y ya impedía el arranque live con GTFS vencido. |
| PASS | `python -m unittest <29 módulos de .github/workflows/ci.yml> -v` | [GREEN](green.txt). 292 casos = 283 previos + 9 nuevos. Se conservan los 18 skips previstos, 13 por ZIP completo ausente de su ruta de test y 5 por soak ausente de la base fresca. El resto pasa con `MADRID_PULSE_REQUIRE_DB=1`. El log contiene la lista exacta de módulos y el SHA-256 de las fixtures, igual que RED. |
| PASS | `npm run lint && npm run typecheck && npm test && npm run build` | [Frontend](frontend.txt), Node 22.13.1. Pasan 89 tests y el build verifica el worker de MapLibre. Vite informa de chunks superiores a 500 kB. |
| PASS | `python scripts/governance/check_docs.py` | [Gobernanza](governance.txt). |

Las transcripciones conservan las salidas y los códigos de retorno. Se
retiraron espacios al final de algunas líneas para versionarlas.

El primer pase integrado reveló que el colector confirmaba las inserciones
sintéticas cuando el test no abría una transacción exterior. Se corrigió
el arnés para revertirlas y se recreó desde cero el contenedor de la tarea
antes de repetir RED y GREEN. [Aislamiento y limpieza](database.txt).

### Reproducción con el kit local

[Transcripción y hashes](replay-real.txt). El arnés versionado llama al
colector y a los endpoints HTTP de producción. Toma las horas de
`CAP_1532` y `CAP_1533` de `apps/api/tools/replay_three_snapshots.py:43-44`
y el instante intermedio del hallazgo P0-1 de
`docs/audits/hito-03/FRONTEND_UX_AUDIT.md` §2. Obtiene la vigencia del
ZIP con `load_network` y usa los valores por defecto de producción,
siete días de aviso y 180 s de frescura (`apps/api/config.py:37,61`).
El colector usa la política del arnés de MP-019
(`apps/api/tools/replay_three_snapshots.py:42`) con lecturas locales.
Las capturas y el ZIP se leen del kit externo. El manifiesto lo valida
`comprobar.py`.

- A las `14:32:10Z` del 20 de noviembre, el baseline devolvió
  `unknown` con edades de −71 s y 468 entidades del corte `1533`.
  El cambio devuelve `ok` con ambas edades de 6 s y 463 entidades
  del corte `1532` en health y snapshot. Las 119 observaciones del snapshot
  habían llegado antes del instante de la petición.
- A las `14:32:03Z`, health y snapshot declaran ausencia con edades
  `null`. Snapshot contiene cero vehículos y revisión `null`.
- Con el ZIP real en un proceso live, health, catálogo y snapshot
  devolvieron `valid` el 10 de diciembre, `expiring` el 18 y
  `expired` el 20 con HTTP 200. La fecha final del ZIP es el 19.

### Entorno y límites

- DSN desechable `postgresql://mp026a:mp026a_local@127.0.0.1:5453/madrid_pulse`.
  PostgreSQL/PostGIS `postgis/postgis:17-3.5`, esquema `public`, rol local
  propietario, migraciones desde cero y marca `madrid-pulse:disposable`.
- Orca `worker-show --dispatch ctx_1a8cc12f1f97 --full --json` registra
  `gpt-6.2-sol` y esfuerzo `high` en `launch.requested` y
  `launch.effective`. El proceso local expone `app-server` en argv.
- NO EJECUTADO. Descarga operativa y despliegue. La comprobación HTTP
  utiliza `TestClient` con reloj simulado y el ZIP congelado.
- Commits de código y pruebas `64b083a`, `ad7b1ee` y `83e4741`.
  Pendiente el dictamen independiente de Claude Opus High sobre la entrega.
