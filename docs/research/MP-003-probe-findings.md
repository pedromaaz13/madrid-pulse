# MP-003 — Hallazgos del probe real de feeds C5

Capturas realizadas el `2026-11-18` entre `15:28:08Z` y `15:31:12Z` (UTC) directamente contra los endpoints de Renfe, sin pasar por ninguna capa intermedia. Todo lo marcado `VERIFIED` aquí proviene de una respuesta HTTP real observada en esa ventana, no de la investigación previa.

## 1. Endpoints GTFS-RT — disponibilidad y formato

| Endpoint | Status | Content-Type | Cache-Control | Tamaño observado |
|---|---|---|---|---|
| `https://gtfsrt.renfe.com/vehicle_positions.json` | `200 OK` | `application/json` | `max-age=30` | ~155 KB |
| `https://gtfsrt.renfe.com/trip_updates.json` | `200 OK` | `application/json` | `max-age=30` | ~165 KB |
| `https://gtfsrt.renfe.com/alerts.json` | `200 OK` | `application/json` | `max-age=30` | ~74 KB |

**Hallazgo:** los tres feeds son JSON real (codificación JSON de GTFS-Realtime 2.0), no protobuf binario — contrario a lo que el nombre `.json` podría dejar ambiguo, está confirmado por `Content-Type` y por el cuerpo (`gtfsRealtimeVersion: "2.0"`). No se necesita un decodificador protobuf para MP-005/MP-007.

## 2. Frecuencia de actualización — medida, no asumida

Tres polls de `vehicle_positions.json` espaciados ~20 s:

| Poll | Hora UTC | `header.timestamp` | Δ respecto al anterior |
|---|---|---|---|
| 1 | 15:28:19 | `1795015685` | — |
| 2 | 15:28:40 | `1795015707` | +22 s |
| 3 | 15:29:00 | `1795015727` | +20 s |

**Resultado:** el contenido cambia realmente cada ~20–22 s, consistente con el `Cache-Control: max-age=30` del servidor. La hipótesis de la investigación previa (~20 s para posiciones) queda **confirmada empíricamente**, no solo citada. Pendiente: repetir la medición en otra franja horaria/día antes de fijarlo como SLA en `docs/DATA_QUALITY.md`.

**`trip_updates.json`** — 2 polls espaciados 30 s (comando: `curl -sS https://gtfsrt.renfe.com/trip_updates.json`, repetido tras `sleep 30`):

| Poll | Hora UTC | `header.timestamp` | Entidades |
|---|---|---|---|
| A | 15:42:58 | `1795016565` | 422 |
| B | 15:43:28 | `1795016607` | 420 |

Δ = 42 s. Más lento que `vehicle_positions` (~20–22 s); una sola medición, no fijar como SLA todavía.

**`alerts.json`** — 2 polls espaciados 30 s:

| Poll | Hora UTC | `header.timestamp` | Entidades |
|---|---|---|---|
| A | 15:43:34 | `1795016612` | 80 |
| B | 15:44:04 | `1795016632` | 80 |

Δ = 20 s. Verificado con el conjunto completo de `id` de alerta (no solo el recuento): los 80 `id` de la poll A son exactamente los mismos 80 de la poll B (`set(ids_a) == set(ids_b)` → `True`, sin elementos exclusivos en ninguno de los dos lados) — no hubo altas ni bajas de alertas en esta ventana de 30 s. Esta comparación de identificadores no demuestra por sí sola que el contenido completo de cada alerta permaneciera idéntico.

## 3. Hallazgo crítico: "C5" no es un identificador único en el feed nacional

El feed **no está limitado a Madrid** — es nacional, cubre todos los núcleos de Cercanías de España. Confirmado con los 3 polls (~400 entidades cada uno, 28 códigos de línea distintos: `C1`–`C10`, `R1`–`R16`, `RG1`, `RL4`, `T1`).

**Al menos tres núcleos tienen una línea llamada literalmente "C5":**

| Núcleo | Ejemplo real de `route_id` (GTFS estático) | Recorrido real |
|---|---|---|
| Madrid | `10T0047C5` | Atocha–Fuenlabrada (y 4 variantes más: `10T0017C5`, `10T0018C5`, `10T0035C5`, `10T0048C5`) |
| Asturias (Gijón) | `20T0011C5` | Gijón (Sanz Crespo)–Pola de Laviana |
| Andalucía (Sevilla) | `30T0009C5` | Jardines de Hércules–Benacazón |

**Esto invalida cualquier filtro que use solo el texto `"C5"` para aislar la línea de Madrid** (en `vehicle_positions`, el campo `vehicle.label` de un tren de Sevilla es literalmente `"C5-23823"`, indistinguible por texto de un tren de Madrid).

### Disambiguador verificado: prefijo numérico de dos cifras = núcleo

El `route_id` (GTFS estático), el `service_id`/`trip_id` (ambos feeds) y las cabeceras `#Mad...`/`#Sev...` de `alerts.json` comparten un prefijo de núcleo consistente:

| Prefijo | Núcleo (confirmado por coordenadas reales) |
|---|---|
| `10` | Madrid |
| `20` | Asturias (Gijón/Oviedo) |
| `30`/`31`/`32` | Andalucía (Sevilla/Cádiz/Málaga) |
| `40`/`41`/`45` | Comunidad Valenciana / Murcia |
| `46`/`47` | Galicia / Cantabria |
| `51` | Cataluña (Barcelona) |
| `60`/`61`/`62` | País Vasco / Cantabria |
| `70` | Navarra |

Verificado cruzando: (a) agrupación por coordenadas lat/lon de `vehicle_positions` de los 3 polls, (b) `routeId` de `alerts.json` (p. ej. `10T0017C5` en una alerta con hashtag `#MadC5` en el texto), (c) `routes.txt`/`trips.txt` del GTFS estático descargado.

**Decisión de diseño que esto obliga (registrar como ADR antes de MP-005):** el contrato canónico interno de Madrid Pulse **no puede** identificar una línea solo por su `short_name` (`"C5"`); debe usar el `route_id` completo (p. ej. `10T0047C5`) o un campo `nucleo`/`network_id` explícito + `short_name`. Esto afecta directamente al modelo de `docs/DATA_MODEL.md` (`route.source_route_id` debe ser el `route_id` completo, no el código de línea) y es más estricto que lo que el modelo candidato actual asume implícitamente.

## 4. Esquema real observado — `vehicle_positions.json`

```json
{
  "id": "VP_C5-20869",
  "vehicle": {
    "trip": { "tripId": "1021X20869C5" },
    "position": { "latitude": 40.283237, "longitude": -3.7991464 },
    "currentStatus": "STOPPED_AT",
    "timestamp": "1795015685",
    "stopId": "35002",
    "vehicle": { "id": "20869", "label": "C5-20869-PLATF.(4)" }
  }
}
```

- `position` **puede estar ausente** (1 de 403 entidades en el poll 1: `VP_C3-26546`, solo `currentStatus`+`stopId`, sin lat/lon). El motor de movimiento (MP-012) debe tratar esto como "sin observación geográfica", no como error.
- `vehicle.label` a veces incluye el andén (`"...-PLATF.(4)"`) como texto libre — no parsear como parte del identificador de vehículo.
- `currentStatus` observado: `STOPPED_AT`, `INCOMING_AT`, `IN_TRANSIT_TO` (valores estándar GTFS-RT).

## 5. Esquema real observado — `trip_updates.json`

```json
{
  "id": "TUUPDATE_3021X23554C1",
  "tripUpdate": {
    "trip": { "tripId": "3021X23554C1", "scheduleRelationship": "SCHEDULED" },
    "stopTimeUpdate": [{ "arrival": { "delay": 120, "time": "1795016371" }, "stopId": "50602" }],
    "vehicle": { "wheelchairAccessible": "WHEELCHAIR_INACCESSIBLE" },
    "delay": 120
  }
}
```

**Hallazgo de cobertura (relevante para `docs/DATA_QUALITY.md`):** en el poll de `15:31:12Z`, de 302 `trip_updates` totales, **cero correspondían a Madrid** (prefijo `10`/`1021X`) — mientras que Barcelona (108), Valencia (37), San Sebastián (37) y otros núcleos sí tenían entradas. No se puede concluir todavía si esto es: (a) casualidad del instante (Madrid sin retrasos reportables en ese momento) o (b) un patrón sistemático de cobertura más baja para Madrid. **Queda `PENDING` una ventana de monitorización más larga (varias horas, distintas franjas) antes de fijar `delay_coverage` esperada para C5 en `docs/DATA_QUALITY.md` — no asumir por una sola muestra.**

## 6. Esquema real observado — `alerts.json`

82 alertas activas en el poll. Ejemplo real con línea C5 de Madrid:

```json
{
  "id": "AVISO_525129",
  "alert": {
    "activePeriod": [{ "start": "1794219780" }],
    "informedEntity": [
      { "routeId": "10T0017C5" }, { "routeId": "10T0018C5" },
      { "routeId": "10T0035C5" }, { "routeId": "10T0047C5" }, { "routeId": "10T0048C5" }
    ],
    "descriptionText": { "translation": [{ "text": "#MadC5 Por obras de mejora en la infraestructura, los días 14, 15, 21 y 22 de noviembre...", "language": "es" }] }
  }
}
```

Confirma que una alerta de Madrid C5 referencia las 5 variantes de `route_id` simultáneamente (ida/vuelta × 2 tramos + una variante corta), y usa el hashtag `#MadC5` en el texto — otra señal de que Renfe distingue internamente el núcleo Madrid, aunque el texto visible al usuario siga diciendo "C-5" sin más.

## 7. GTFS estático — descarga real

El recurso listado en `docs/legal/DATA_SOURCES.md` (`data.renfe.com/.../resource/...`) es una página HTML (CKAN), no el fichero — el enlace de descarga real embebido en esa página es:

```text
https://ssl.renfe.com/ftransit/Fichero_CER_FOMENTO/fomento_transit.zip
```

**Descarga verificada:** `200 OK`, `Content-Type: application/zip`, 15 735 594 bytes, `Last-Modified: 2026-11-18T12:15:43Z` (publicado hoy mismo). Contenido real:

```text
agency.txt          302 B
calendar.txt       68 101 B
routes.txt         42 077 B
shapes.txt      4 201 535 B
stop_times.txt 273 839 104 B   ← fichero dominante, 273 MB
stops.txt         176 708 B
transfers.txt       3 020 B
trips.txt      19 817 542 B
```

**No incluye `calendar_dates.txt` ni `fare_*.txt`** — el conjunto es mínimo pero funcional para rutas/paradas/horarios/calendario/geometría (`shapes.txt` **sí está incluido**, ver tabla arriba — corrección: una versión anterior de este documento afirmaba erróneamente lo contrario).

Cruce de identificadores confirmado: el `stop_id` del GTFS estático (p. ej. `35011` = "Parque Polvoranca", `35607` = "Móstoles-El Soto") **coincide exactamente** con el `stopId` observado en `vehicle_positions.json` en vivo, y sus coordenadas (40.31,-3.78 / 40.33,-3.88) coinciden con las posiciones reales capturadas.

**Corrección (hallazgo bloqueante de la revisión de Codex, verificado independientemente):** una versión anterior de este documento afirmaba que el `trip_id` del feed en vivo NO coincidía literalmente con `trips.txt` y que había que resolverlo por `(service_id, vehículo, línea)`. **Eso era incorrecto** — el error venía de un `grep` mal anclado (`^1021X20869C5,`) que asumía que `trip_id` era el primer campo de `trips.txt`, cuando en realidad es el **tercer** campo (`route_id,service_id,trip_id,...`). Verificado con una comparación de conjuntos completa:

```text
$ cut -d, -f3 trips.txt | sed 's/[[:space:]]*$//' | sort -u > static_tripids.txt
$ <extraer trip_id de las 403 entidades de vehicle_positions.json> | sort -u > live_tripids.txt
$ comm -12 live_tripids.txt static_tripids.txt | wc -l   # coinciden
403
$ comm -23 live_tripids.txt static_tripids.txt | wc -l   # solo en vivo, sin match
0
```

**Resultado correcto: el `trip_id` del feed en vivo coincide literalmente, carácter a carácter, con el campo `trip_id` de `trips.txt` — 403/403 en esta muestra.** Es un `JOIN` directo por igualdad de cadena, sin necesidad de reconstrucción por `(service_id, vehículo, línea)`. Esta regla de resolución (correcta) debe documentarse en `packages/contracts/` (MP-005).

## 8. Actualización de `docs/legal/DATA_SOURCES.md`

Las filas marcadas `Disponibilidad y contrato: PENDING MP-003` para los tres feeds GTFS-RT y el GTFS estático quedan `VERIFIED 2026-11-18` para disponibilidad/esquema (no para licencia, ya verificada en MP-002). El fallo histórico de SSL/descarga mencionado en MP-002 **no se reprodujo** en esta prueba — la descarga fue exitosa vía el enlace real `ssl.renfe.com`, distinto del enlace de portal que mostraba el fallo.

## 9. Pendiente explícito (no resuelto en esta tarea)

- Cobertura real de `trip_updates` para Madrid en ventanas más largas que las aquí medidas (ver §5) — una sola comparación de 2 polls no basta para concluir un patrón de cobertura.
- Validación de `shapes.txt`/`stop_times.txt` específicos de las 5 variantes de `route_id` de C5 Madrid (se confirmó que existen y tienen volumen, no se validó su contenido detallado — corresponde a MP-010).
- Comportamiento en cambio de día de servicio (medianoche) — no se probó en esta ventana de captura.
