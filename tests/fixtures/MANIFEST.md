# Manifiesto de fixtures MP-004

Fecha de captura: `2026-11-18T16:01Z` (UTC; los `header.timestamp` de los feeds
corresponden a `16:01:47Z`–`16:01:49Z`). Cada fichero contiene solo el
cuerpo JSON, sin cabeceras HTTP, cookies ni credenciales. Los recuentos
"original" corresponden a la respuesta completa recién capturada; los recuentos
"fixture" corresponden al subconjunto versionado.

| Fichero | Endpoint origen | Entidades original → fixture | SHA-256 |
|---|---|---:|---|
| `vehicle_positions.json` | `https://gtfsrt.renfe.com/vehicle_positions.json` | 394 → 10 | `80af53436d5f94d18bd434caeefbf702391844846d3bc86c6ebf93d328da9883` |
| `trip_updates.json` | `https://gtfsrt.renfe.com/trip_updates.json` | 401 → 8 | `78974c8543a2315315acb036eb72d5a2c8d792b10bcd11d725aebb917dc77bd4` |
| `alerts.json` | `https://gtfsrt.renfe.com/alerts.json` | 76 → 3 | `cdd94af7bb7fa4d7a6fa894977abcf38cac2aed081a074d9b3377cc73750dfef` |

Selección aplicada:

- Posiciones: siete C5 de Madrid (`tripId` con prefijo `10`) y una C5 de cada
  prefijo `20`, `30` y `40`. La captura no contenía ninguna entidad sin
  `position`, por lo que ese caso observado en MP-003 no se fabricó.
- Actualizaciones: ocho viajes de Madrid, incluyendo C5 y otras líneas, tanto
  `SCHEDULED` como `CANCELED`.
- Alertas: las tres entidades que informaban rutas con prefijo Madrid `10`; la
  primera cubre simultáneamente las cinco variantes de ruta de C5 Madrid.
