# AUD-02/AUD-03 — Catálogo ferroviario y geometría del Hito 3

**Ejecuta AUD-02:** OpenAI Codex (reconstrucción independiente)

**Revisa AUD-02:** Claude Sonnet · High (pendiente)

**Fecha:** 2026-11-23

**Fuente congelada:** `data/hito-03/replay/fomento_transit.zip`

**SHA-256:** `c5b40823c5cacbec6d9a21d88ec0530d9604a6d4331df98c330e608f0bacb11e`

## GTFS y catálogo

### Veredicto

Los cuatro recuentos del cierre **coinciden exactamente** si se usan las mismas
definiciones trazables al GTFS: 12 valores distintos de `route_short_name` del
núcleo `10`, 42 `route_id`, 103 pares distintos
`(route_id, secuencia no vacía de stop_id)` y 95 `stop_id` referenciados por
esas secuencias. La reconstrucción independiente y `packages.gtfs.catalog`
producen los mismos identificadores, secuencias y `trip_count`, no solo los
mismos totales.

| Magnitud | Cierre | CSV crudo, reconstrucción propia | `Catalog` | Veredicto |
|---|---:|---:|---:|---|
| líneas/denominaciones | 12 | 12 | 12 | coincide |
| `route_id` | 42 | 42 | 42 | coincide |
| patrones no vacíos ligados a `route_id` | 103 | 103 | 103 | coincide |
| estaciones referenciadas | 95 | 95 | 95 | coincide |

No obstante, esos totales son de **identidad de fuente**, no de recorridos
necesariamente animables: dos `route_id` (`10T0035C5` y `10T0097C8b`) aportan
121 trips sin ningún `stop_times`, y uno de los 103 patrones
(`10T0098C8b`) contiene una sola parada. Por tanto, el desglose honesto es
**42 IDs de ruta / 40 con al menos un patrón**, **103 patrones no vacíos /
102 con al menos dos paradas**, y **121 trips programados huérfanos**. El
código no inventa recorridos para los huérfanos y el histórico ya los conserva
sin horario, pero el lema corto «42 rutas / 103 patrones» oculta esta calidad.

El inventario adicional reconstruido directamente es: 36.097 trips Madrid,
537.899 filas de `stop_times`, 30 `service_id` diarios entre 2026-11-20 y
2026-12-19, cero referencias a estaciones/servicios/shapes ausentes y cero IDs
duplicados en `routes.txt`, `trips.txt` o `stops.txt`.

### Método independiente y límite OSM

La primera pasada usa solo `zipfile`, `csv` y tipos de la biblioteca estándar
en [`scratch/aud02_rebuild.py`](../../../scratch/aud02_rebuild.py): limpia los
encabezados rellenos con espacios del ZIP, filtra literalmente los `route_id`
que empiezan por `10`, ordena cada trip por `stop_sequence` y agrupa el par
`(route_id, tuple(stop_id))`. No importa `packages.gtfs` ni copia sus tipos.
Solo después se cargó el mismo ZIP con el parser del producto para comparar
conjuntos completos.

La identidad de los 103 patrones coincide también uno a uno con
`docs/evidence/mp-018-corridor-coverage.csv`: 28 constan como `validated`, 3
como `partial` y 72 como `pending`; no falta ni sobra ningún `pattern_id`, y
origen, destino y `trip_count` coinciden. Esto **no** revalida la geometría OSM:
la inspección independiente de relations/ways, continuidad y proyección queda
reservada a AUD-03 y se marca `NO VERIFICADO` abajo.

### Calendario, excepciones y horas extendidas

El ZIP no contiene `calendar_dates.txt`; la ausencia se comprobó tanto en el
listado del archivo como en el parser (`topology.calendar_dates == ()`). Los 30
`service_id` de Madrid son calendarios de un solo día, uno por fecha. Para cada
día del intervalo se compararon independientemente (a) el servicio activo por
weekday/rango y los trips con `stop_times` y (b)
`scheduled_service_ids_for_date`/`scheduled_trip_instances_for_date`: los 30
días coinciden exactamente. ADD (`exception_type=1`), REMOVE (`2`) y ausencia
del fichero pasan sus tres regresiones sintéticas; no existe una fila ADD/REMOVE
real de Renfe en este artefacto con la que hacer una prueba empírica.

En Madrid hay 742 trips con al menos una hora `>=24:00`, 4.469 filas y 8.912
valores arrival/departure extendidos; el máximo Madrid es `24:53:00`, por lo que
el horizonte calculado es 3.180 s. En el ZIP nacional completo son 9.243 filas,
18.392 valores (`18.196` en `24:xx`, `196` en `25:xx`) y máximo `25:09:00`.
Las regresiones de DEC-039 sobre `24:xx`, ambos cambios DST y ventanas de
tablero pasan. Se encontró, sin impacto en este ZIP, un caso GTFS permitido que
el fix no cubre: una hora `49:00` requiere mirar dos fechas de servicio atrás,
pero `service_dates_covering` empieza siempre en `fecha_civil - 1 día`.

### Inventario de las 42 variantes y servicios

`Servicios` se refiere a los `service_id` realmente presentes en trips de esa
variante. Los 30 IDs consecutivos `1023V`–`1052S` corresponden uno a uno a los
30 días del feed; cuando una variante no circula todos los días se enumeran
sus IDs o las exclusiones. `Huérfanos` significa trip presente en `trips.txt`
sin una sola fila en `stop_times.txt`.

| Línea | `route_id` | `route_long_name` crudo normalizado | Trips | Huérfanos | Patrones | Servicios |
|---|---|---|---:|---:|---:|---|
| C1 | `10T0001C1` | Principe Pio -Aeropuerto-T4 | 2131 | 0 | 2 | los 30 (`1023V`–`1052S`) |
| C1 | `10T0002C1` | Aeropuerto-T4 -Principe Pio | 2131 | 0 | 2 | los 30 (`1023V`–`1052S`) |
| C10 | `10T0003C10` | Villalba -Aeropuerto-T4 | 1100 | 0 | 4 | los 30 (`1023V`–`1052S`) |
| C10 | `10T0004C10` | Aeropuerto-T4 -Villalba | 1075 | 0 | 3 | los 30 (`1023V`–`1052S`) |
| C2 | `10T0005C2` | Guadalajara -Chamartín - Clara Campoamor | 1893 | 0 | 7 | los 30 (`1023V`–`1052S`) |
| C2 | `10T0006C2` | Chamartín - Clara Campoamor -Guadalajara | 1850 | 0 | 6 | los 30 (`1023V`–`1052S`) |
| C3 | `10T0007C3` | Chamartín - Clara Campoamor -Aranjuez | 1608 | 0 | 2 | los 30 (`1023V`–`1052S`) |
| C3 | `10T0008C3` | Aranjuez -Chamartín - Clara Campoamor | 1608 | 0 | 2 | los 30 (`1023V`–`1052S`) |
| C4 | `10T0011C4` | Chamartín - Clara Campoamor -Parla | 189 | 0 | 3 | los 30 (`1023V`–`1052S`) |
| C4 | `10T0012C4` | Parla -Chamartín - Clara Campoamor | 159 | 0 | 2 | los 30 (`1023V`–`1052S`) |
| C4a | `10T0013C4a` | Alcobendas-S.Sebast. de los Reyes -Parla | 1759 | 0 | 4 | los 30 (`1023V`–`1052S`) |
| C4a | `10T0014C4a` | Parla -Alcobendas-S.Sebast. de los Reyes | 1759 | 0 | 4 | los 30 (`1023V`–`1052S`) |
| C4b | `10T0015C4b` | Colmenar Viejo -Parla | 1740 | 0 | 4 | los 30 (`1023V`–`1052S`) |
| C4b | `10T0016C4b` | Parla -Colmenar Viejo | 1740 | 0 | 4 | los 30 (`1023V`–`1052S`) |
| C5 | `10T0017C5` | Mostoles el Soto -Humanes | 3932 | 0 | 5 | los 30 (`1023V`–`1052S`) |
| C5 | `10T0018C5` | Humanes -Mostoles el Soto | 3947 | 0 | 5 | los 30 (`1023V`–`1052S`) |
| C9 | `10T0025C9` | Cercedilla -Cotos | 32 | 0 | 2 | 2: `1033L`, `1034M` |
| C9 | `10T0026C9` | Cotos -Cercedilla | 32 | 0 | 2 | 2: `1033L`, `1034M` |
| C8a | `10T0027C8a` | Atocha -El Escorial | 18 | 0 | 1 | 18: `1023V`, `1027M`, `1028X`, `1029J`, `1030V`, `1033L`, `1034M`, `1035X`, `1036J`, `1037V`, `1042X`, `1043J`, `1044V`, `1047L`, `1048M`, `1049X`, `1050J`, `1051V` |
| C5 | `10T0035C5` | -Fuenlabrada | 7 | 7 | 0 | 7: `1023V`, `1033L`, `1034M`, `1035X`, `1036J`, `1037V`, `1042X` |
| C2 | `10T0037C2` | Alcala de Henares -Nuevos Ministerios | 1 | 0 | 1 | 1: `1026L` |
| C5 | `10T0047C5` | Atocha -Fuenlabrada | 214 | 0 | 2 | 7: `1024S`, `1025D`, `1039D`, `1040L`, `1041M`, `1042X`, `1052S` |
| C5 | `10T0048C5` | Fuenlabrada -Atocha | 210 | 0 | 2 | 6: `1024S`, `1025D`, `1039D`, `1040L`, `1041M`, `1052S` |
| C7 | `10T0051C7` | Principe Pio -Chamartín - Clara Campoamor | 997 | 0 | 4 | los 30 (`1023V`–`1052S`) |
| C7 | `10T0052C7` | Chamartín - Clara Campoamor -Principe Pio | 1033 | 0 | 4 | los 30 (`1023V`–`1052S`) |
| C7 | `10T0053C7` | Principe Pio -Atocha | 32 | 0 | 2 | 29; todos salvo `1026L` |
| C7 | `10T0054C7` | Atocha -Principe Pio | 33 | 0 | 2 | los 30 (`1023V`–`1052S`) |
| C7 | `10T0059C7` | Chamartín - Clara Campoamor -Alcala de Henares | 57 | 0 | 1 | los 30 (`1023V`–`1052S`) |
| C7 | `10T0060C7` | Alcala de Henares -Chamartín - Clara Campoamor | 8 | 0 | 1 | 4: `1027M`, `1028X`, `1029J`, `1030V` |
| C8a | `10T0061C8a` | El Escorial -Chamartín - Clara Campoamor | 660 | 0 | 3 | los 30 (`1023V`–`1052S`) |
| C8a | `10T0062C8a` | Chamartín - Clara Campoamor -El Escorial | 590 | 0 | 3 | los 30 (`1023V`–`1052S`) |
| C10 | `10T0064C10` | Principe Pio -El Escorial | 38 | 0 | 3 | los 30 (`1023V`–`1052S`) |
| C10 | `10T0075C10` | Torrelodones -Chamartín - Clara Campoamor | 959 | 0 | 1 | los 30 (`1023V`–`1052S`) |
| C10 | `10T0076C10` | Chamartín - Clara Campoamor -Torrelodones | 987 | 0 | 2 | los 30 (`1023V`–`1052S`) |
| C8a | `10T0085C8a` | -El Escorial | 74 | 0 | 1 | 28; todos salvo `1045S`, `1046D` |
| C8b | `10T0087C8b` | Chamartín - Clara Campoamor -Cercedilla | 566 | 0 | 2 | los 30 (`1023V`–`1052S`) |
| C8b | `10T0088C8b` | Cercedilla -Chamartín - Clara Campoamor | 566 | 0 | 1 | los 30 (`1023V`–`1052S`) |
| C8b | `10T0097C8b` | -Cercedilla | 114 | 114 | 0 | los 30 (`1023V`–`1052S`) |
| C8b | `10T0098C8b` | Cercedilla - | 54 | 0 | 1 | 25; todos salvo `1026L`, `1027M`, `1028X`, `1029J`, `1030V` |
| C8a | `10T0107C8a` | Las Matas -Las Rozas | 4 | 0 | 1 | 2: `1045S`, `1046D` |
| C9 | `10T0110C9` | Cercedilla -Cotos | 95 | 0 | 1 | 19: `1023V`, `1024S`, `1025D`, `1027M`, `1028X`, `1029J`, `1030V`, `1031S`, `1032D`, `1043J`, `1044V`, `1045S`, `1046D`, `1047L`, `1048M`, `1049X`, `1050J`, `1051V`, `1052S` |
| C9 | `10T0111C9` | Cotos -Cercedilla | 95 | 0 | 1 | 19: `1023V`, `1024S`, `1025D`, `1027M`, `1028X`, `1029J`, `1030V`, `1031S`, `1032D`, `1043J`, `1044V`, `1045S`, `1046D`, `1047L`, `1048M`, `1049X`, `1050J`, `1051V`, `1052S` |

### Los 103 patrones y su secuencia real

El sentido no se deduce del nombre comercial ni se inventa con `direction_id`
(esa columna no existe en el feed): se toma de la secuencia ordenada. El
`headsign` se reproduce tal cual; `∅` indica que Renfe lo deja vacío. La
columna OSM solo transcribe el estado enlazado a esa identidad y **no** sustituye
la auditoría física de AUD-03.

| Línea | `route_id` | Patrón | Sentido fuente | Viajes | Servicios | Secuencia real de estaciones | OSM declarado |
|---|---|---:|---|---:|---:|---|---|
| C1 | `10T0001C1` | 1 | Madrid-Chamartín-Clara Campoamor → Madrid-Aeropuerto T4; headsign ∅ (2101) | 2101 | 30 | `17000` Madrid-Chamartín-Clara Campoamor → `98003` Fuente de la Mora → `98304` Valdebebas → `98305` Madrid-Aeropuerto T4 | pending |
| C1 | `10T0001C1` | 2 | Madrid-Atocha Cercanías → Madrid-Aeropuerto T4; headsign ∅ (30) | 30 | 30 | `18000` Madrid-Atocha Cercanías → `18001` Madrid-Recoletos → `18002` Madrid-Nuevos Ministerios → `17000` Madrid-Chamartín-Clara Campoamor → `98003` Fuente de la Mora → `98304` Valdebebas → `98305` Madrid-Aeropuerto T4 | pending |
| C1 | `10T0002C1` | 1 | Madrid-Aeropuerto T4 → Madrid-Chamartín-Clara Campoamor; headsign ∅ (2101) | 2101 | 30 | `98305` Madrid-Aeropuerto T4 → `98304` Valdebebas → `98003` Fuente de la Mora → `17000` Madrid-Chamartín-Clara Campoamor | pending |
| C1 | `10T0002C1` | 2 | Madrid-Aeropuerto T4 → Madrid-Atocha Cercanías; headsign ∅ (30) | 30 | 30 | `98305` Madrid-Aeropuerto T4 → `98304` Valdebebas → `98003` Fuente de la Mora → `17000` Madrid-Chamartín-Clara Campoamor → `18002` Madrid-Nuevos Ministerios → `18001` Madrid-Recoletos → `18000` Madrid-Atocha Cercanías | pending |
| C10 | `10T0003C10` | 1 | Villalba de Guadarrama → Madrid-Nuevos Ministerios; headsign ∅ (13) | 13 | 13 | `10200` Villalba de Guadarrama → `10104` Galapagar-La Navata → `10103` Torrelodones → `10101` Las Matas → `10100` Pinar de las Rozas → `10005` Las Rozas → `10007` Majadahonda → `10010` El Barrial-Centro Comercial Pozuelo → `10002` Pozuelo → `10001` Aravaca → `10000` Madrid-Príncipe Pío → `18005` Pirámides → `18004` Delicias → `18003` Méndez Álvaro P.V. → `18000` Madrid-Atocha Cercanías → `18001` Madrid-Recoletos → `18002` Madrid-Nuevos Ministerios | pending |
| C10 | `10T0003C10` | 2 | Villalba de Guadarrama → Madrid-Chamartín-Clara Campoamor; headsign ∅ (1035) | 1035 | 30 | `10200` Villalba de Guadarrama → `10104` Galapagar-La Navata → `10103` Torrelodones → `10101` Las Matas → `10100` Pinar de las Rozas → `10005` Las Rozas → `10007` Majadahonda → `10010` El Barrial-Centro Comercial Pozuelo → `10002` Pozuelo → `10001` Aravaca → `10000` Madrid-Príncipe Pío → `18005` Pirámides → `18004` Delicias → `18003` Méndez Álvaro P.V. → `18000` Madrid-Atocha Cercanías → `18001` Madrid-Recoletos → `18002` Madrid-Nuevos Ministerios → `17000` Madrid-Chamartín-Clara Campoamor | pending |
| C10 | `10T0003C10` | 3 | El Escorial → Madrid-Chamartín-Clara Campoamor; headsign CIVIS (36) | 36 | 18 | `10203` El Escorial → `10202` Las Zorreras-Navalquejigo → `10201` San Yago → `10200` Villalba de Guadarrama → `10100` Pinar de las Rozas → `10005` Las Rozas → `10002` Pozuelo → `10001` Aravaca → `10000` Madrid-Príncipe Pío → `18005` Pirámides → `18004` Delicias → `18003` Méndez Álvaro P.V. → `18000` Madrid-Atocha Cercanías → `18001` Madrid-Recoletos → `18002` Madrid-Nuevos Ministerios → `17000` Madrid-Chamartín-Clara Campoamor | pending |
| C10 | `10T0003C10` | 4 | El Escorial → Madrid-Chamartín-Clara Campoamor; headsign ∅ (16) | 16 | 4 | `10203` El Escorial → `10202` Las Zorreras-Navalquejigo → `10201` San Yago → `10200` Villalba de Guadarrama → `10104` Galapagar-La Navata → `10103` Torrelodones → `10101` Las Matas → `10100` Pinar de las Rozas → `10005` Las Rozas → `10007` Majadahonda → `10010` El Barrial-Centro Comercial Pozuelo → `10002` Pozuelo → `10001` Aravaca → `10000` Madrid-Príncipe Pío → `18005` Pirámides → `18004` Delicias → `18003` Méndez Álvaro P.V. → `18000` Madrid-Atocha Cercanías → `18001` Madrid-Recoletos → `18002` Madrid-Nuevos Ministerios → `17000` Madrid-Chamartín-Clara Campoamor | pending |
| C10 | `10T0004C10` | 1 | Madrid-Chamartín-Clara Campoamor → Villalba de Guadarrama; headsign CIVIS (50) | 50 | 18 | `17000` Madrid-Chamartín-Clara Campoamor → `18002` Madrid-Nuevos Ministerios → `18001` Madrid-Recoletos → `18000` Madrid-Atocha Cercanías → `18003` Méndez Álvaro P.V. → `18004` Delicias → `18005` Pirámides → `10000` Madrid-Príncipe Pío → `10001` Aravaca → `10002` Pozuelo → `10005` Las Rozas → `10100` Pinar de las Rozas → `10200` Villalba de Guadarrama | pending |
| C10 | `10T0004C10` | 2 | Madrid-Chamartín-Clara Campoamor → Villalba de Guadarrama; headsign ∅ (1014) | 1014 | 30 | `17000` Madrid-Chamartín-Clara Campoamor → `18002` Madrid-Nuevos Ministerios → `18001` Madrid-Recoletos → `18000` Madrid-Atocha Cercanías → `18003` Méndez Álvaro P.V. → `18004` Delicias → `18005` Pirámides → `10000` Madrid-Príncipe Pío → `10001` Aravaca → `10002` Pozuelo → `10010` El Barrial-Centro Comercial Pozuelo → `10007` Majadahonda → `10005` Las Rozas → `10100` Pinar de las Rozas → `10101` Las Matas → `10103` Torrelodones → `10104` Galapagar-La Navata → `10200` Villalba de Guadarrama | pending |
| C10 | `10T0004C10` | 3 | Madrid-Atocha Cercanías → Villalba de Guadarrama; headsign ∅ (11) | 11 | 11 | `18000` Madrid-Atocha Cercanías → `18003` Méndez Álvaro P.V. → `18004` Delicias → `18005` Pirámides → `10000` Madrid-Príncipe Pío → `10001` Aravaca → `10002` Pozuelo → `10010` El Barrial-Centro Comercial Pozuelo → `10007` Majadahonda → `10005` Las Rozas → `10100` Pinar de las Rozas → `10101` Las Matas → `10103` Torrelodones → `10104` Galapagar-La Navata → `10200` Villalba de Guadarrama | pending |
| C2 | `10T0005C2` | 1 | Madrid-Atocha Cercanías → Madrid-Chamartín-Clara Campoamor; headsign ∅ (14) | 14 | 14 | `18000` Madrid-Atocha Cercanías → `18001` Madrid-Recoletos → `18002` Madrid-Nuevos Ministerios → `17000` Madrid-Chamartín-Clara Campoamor | pending |
| C2 | `10T0005C2` | 2 | Alcalá de Henares → Madrid-Chamartín-Clara Campoamor; headsign ∅ (14), CIVIS (14) | 28 | 14 | `70103` Alcalá de Henares → `70102` Torrejón de Ardoz → `70101` San Fernando de Henares → `98003` Fuente de la Mora → `17000` Madrid-Chamartín-Clara Campoamor | pending |
| C2 | `10T0005C2` | 3 | Alcalá de Henares → Madrid-Chamartín-Clara Campoamor; headsign ∅ (455) | 455 | 30 | `70103` Alcalá de Henares → `70111` La Garena → `70112` Soto del Henares → `70102` Torrejón de Ardoz → `70101` San Fernando de Henares → `70108` Coslada → `70100` Vicálvaro → `70109` Santa Eugenia → `70005` Vallecas → `70003` El Pozo → `70002` Asamblea de Madrid-Entrevías → `18000` Madrid-Atocha Cercanías → `18001` Madrid-Recoletos → `18002` Madrid-Nuevos Ministerios → `17000` Madrid-Chamartín-Clara Campoamor | pending |
| C2 | `10T0005C2` | 4 | Coslada → Madrid-Chamartín-Clara Campoamor; headsign ∅ (80) | 80 | 4 | `70108` Coslada → `70100` Vicálvaro → `70109` Santa Eugenia → `70005` Vallecas → `70003` El Pozo → `70002` Asamblea de Madrid-Entrevías → `18000` Madrid-Atocha Cercanías → `18001` Madrid-Recoletos → `18002` Madrid-Nuevos Ministerios → `17000` Madrid-Chamartín-Clara Campoamor | pending |
| C2 | `10T0005C2` | 5 | Guadalajara → Madrid-Chamartín-Clara Campoamor; headsign CIVIS (71), ∅ (28) | 99 | 15 | `70200` Guadalajara → `70105` Azuqueca → `70104` Meco → `70107` Alcalá de Henares-Universidad → `70103` Alcalá de Henares → `70102` Torrejón de Ardoz → `70101` San Fernando de Henares → `98003` Fuente de la Mora → `17000` Madrid-Chamartín-Clara Campoamor | pending |
| C2 | `10T0005C2` | 6 | Guadalajara → Madrid-Nuevos Ministerios; headsign ∅ (14) | 14 | 14 | `70200` Guadalajara → `70105` Azuqueca → `70104` Meco → `70107` Alcalá de Henares-Universidad → `70103` Alcalá de Henares → `70111` La Garena → `70112` Soto del Henares → `70102` Torrejón de Ardoz → `70101` San Fernando de Henares → `70108` Coslada → `70100` Vicálvaro → `70109` Santa Eugenia → `70005` Vallecas → `70003` El Pozo → `70002` Asamblea de Madrid-Entrevías → `18000` Madrid-Atocha Cercanías → `18001` Madrid-Recoletos → `18002` Madrid-Nuevos Ministerios | pending |
| C2 | `10T0005C2` | 7 | Guadalajara → Madrid-Chamartín-Clara Campoamor; headsign ∅ (1203) | 1203 | 30 | `70200` Guadalajara → `70105` Azuqueca → `70104` Meco → `70107` Alcalá de Henares-Universidad → `70103` Alcalá de Henares → `70111` La Garena → `70112` Soto del Henares → `70102` Torrejón de Ardoz → `70101` San Fernando de Henares → `70108` Coslada → `70100` Vicálvaro → `70109` Santa Eugenia → `70005` Vallecas → `70003` El Pozo → `70002` Asamblea de Madrid-Entrevías → `18000` Madrid-Atocha Cercanías → `18001` Madrid-Recoletos → `18002` Madrid-Nuevos Ministerios → `17000` Madrid-Chamartín-Clara Campoamor | pending |
| C2 | `10T0006C2` | 1 | Madrid-Chamartín-Clara Campoamor → Coslada; headsign ∅ (80) | 80 | 4 | `17000` Madrid-Chamartín-Clara Campoamor → `18002` Madrid-Nuevos Ministerios → `18001` Madrid-Recoletos → `18000` Madrid-Atocha Cercanías → `70002` Asamblea de Madrid-Entrevías → `70003` El Pozo → `70005` Vallecas → `70109` Santa Eugenia → `70100` Vicálvaro → `70108` Coslada | pending |
| C2 | `10T0006C2` | 2 | Madrid-Chamartín-Clara Campoamor → Alcalá de Henares; headsign ∅ (419) | 419 | 30 | `17000` Madrid-Chamartín-Clara Campoamor → `18002` Madrid-Nuevos Ministerios → `18001` Madrid-Recoletos → `18000` Madrid-Atocha Cercanías → `70002` Asamblea de Madrid-Entrevías → `70003` El Pozo → `70005` Vallecas → `70109` Santa Eugenia → `70100` Vicálvaro → `70108` Coslada → `70101` San Fernando de Henares → `70102` Torrejón de Ardoz → `70112` Soto del Henares → `70111` La Garena → `70103` Alcalá de Henares | pending |
| C2 | `10T0006C2` | 3 | Madrid-Chamartín-Clara Campoamor → Azuqueca; headsign ∅ (1) | 1 | 1 | `17000` Madrid-Chamartín-Clara Campoamor → `18002` Madrid-Nuevos Ministerios → `18001` Madrid-Recoletos → `18000` Madrid-Atocha Cercanías → `70002` Asamblea de Madrid-Entrevías → `70003` El Pozo → `70005` Vallecas → `70109` Santa Eugenia → `70100` Vicálvaro → `70108` Coslada → `70101` San Fernando de Henares → `70102` Torrejón de Ardoz → `70112` Soto del Henares → `70111` La Garena → `70103` Alcalá de Henares → `70107` Alcalá de Henares-Universidad → `70104` Meco → `70105` Azuqueca | pending |
| C2 | `10T0006C2` | 4 | Madrid-Chamartín-Clara Campoamor → Guadalajara; headsign ∅ (1261) | 1261 | 30 | `17000` Madrid-Chamartín-Clara Campoamor → `18002` Madrid-Nuevos Ministerios → `18001` Madrid-Recoletos → `18000` Madrid-Atocha Cercanías → `70002` Asamblea de Madrid-Entrevías → `70003` El Pozo → `70005` Vallecas → `70109` Santa Eugenia → `70100` Vicálvaro → `70108` Coslada → `70101` San Fernando de Henares → `70102` Torrejón de Ardoz → `70112` Soto del Henares → `70111` La Garena → `70103` Alcalá de Henares → `70107` Alcalá de Henares-Universidad → `70104` Meco → `70105` Azuqueca → `70200` Guadalajara | pending |
| C2 | `10T0006C2` | 5 | Madrid-Chamartín-Clara Campoamor → Guadalajara; headsign CIVIS (42), ∅ (28) | 70 | 14 | `17000` Madrid-Chamartín-Clara Campoamor → `98003` Fuente de la Mora → `70101` San Fernando de Henares → `70102` Torrejón de Ardoz → `70103` Alcalá de Henares → `70107` Alcalá de Henares-Universidad → `70104` Meco → `70105` Azuqueca → `70200` Guadalajara | pending |
| C2 | `10T0006C2` | 6 | Madrid-Nuevos Ministerios → Guadalajara; headsign ∅ (19) | 19 | 19 | `18002` Madrid-Nuevos Ministerios → `18001` Madrid-Recoletos → `18000` Madrid-Atocha Cercanías → `70002` Asamblea de Madrid-Entrevías → `70003` El Pozo → `70005` Vallecas → `70109` Santa Eugenia → `70100` Vicálvaro → `70108` Coslada → `70101` San Fernando de Henares → `70102` Torrejón de Ardoz → `70112` Soto del Henares → `70111` La Garena → `70103` Alcalá de Henares → `70107` Alcalá de Henares-Universidad → `70104` Meco → `70105` Azuqueca → `70200` Guadalajara | pending |
| C3 | `10T0007C3` | 1 | Madrid-Chamartín-Clara Campoamor → Aranjuez; headsign ∅ (1582) | 1582 | 30 | `17000` Madrid-Chamartín-Clara Campoamor → `18002` Madrid-Nuevos Ministerios → `18101` Sol → `18000` Madrid-Atocha Cercanías → `60100` Madrid-Villaverde Bajo → `60107` San Cristóbal de los Ángeles → `60101` San Cristóbal Industrial → `60109` El Casar → `60102` Getafe-Industrial → `60103` Pinto → `60104` Valdemoro → `60105` Ciempozuelos → `60200` Aranjuez | pending |
| C3 | `10T0007C3` | 2 | Madrid-Chamartín-Clara Campoamor → Aranjuez; headsign CIVIS (26) | 26 | 13 | `17000` Madrid-Chamartín-Clara Campoamor → `18002` Madrid-Nuevos Ministerios → `18101` Sol → `18000` Madrid-Atocha Cercanías → `60109` El Casar → `60103` Pinto → `60104` Valdemoro → `60105` Ciempozuelos → `60200` Aranjuez | pending |
| C3 | `10T0008C3` | 1 | Aranjuez → Madrid-Chamartín-Clara Campoamor; headsign ∅ (1569) | 1569 | 30 | `60200` Aranjuez → `60105` Ciempozuelos → `60104` Valdemoro → `60103` Pinto → `60102` Getafe-Industrial → `60109` El Casar → `60101` San Cristóbal Industrial → `60107` San Cristóbal de los Ángeles → `60100` Madrid-Villaverde Bajo → `18000` Madrid-Atocha Cercanías → `18101` Sol → `18002` Madrid-Nuevos Ministerios → `17000` Madrid-Chamartín-Clara Campoamor | pending |
| C3 | `10T0008C3` | 2 | Aranjuez → Madrid-Chamartín-Clara Campoamor; headsign CIVIS (39) | 39 | 13 | `60200` Aranjuez → `60105` Ciempozuelos → `60104` Valdemoro → `60103` Pinto → `60109` El Casar → `18000` Madrid-Atocha Cercanías → `18101` Sol → `18002` Madrid-Nuevos Ministerios → `17000` Madrid-Chamartín-Clara Campoamor | pending |
| C4 | `10T0011C4` | 1 | Madrid-Chamartín-Clara Campoamor → Parla; headsign ∅ (61) | 61 | 30 | `17000` Madrid-Chamartín-Clara Campoamor → `18002` Madrid-Nuevos Ministerios → `18101` Sol → `18000` Madrid-Atocha Cercanías → `60100` Madrid-Villaverde Bajo → `37001` Madrid-Villaverde Alto → `37010` Las Margaritas → `37002` Getafe-Centro → `37011` Getafe-Sector 3 → `37012` Parla | validated (rel. 9174510) |
| C4 | `10T0011C4` | 2 | Madrid-Atocha Cercanías → Parla; headsign ∅ (52) | 52 | 30 | `18000` Madrid-Atocha Cercanías → `60100` Madrid-Villaverde Bajo → `37001` Madrid-Villaverde Alto → `37010` Las Margaritas → `37002` Getafe-Centro → `37011` Getafe-Sector 3 → `37012` Parla | validated (rel. 9174510) |
| C4 | `10T0011C4` | 3 | Madrid-Villaverde Alto → Parla; headsign ∅ (76) | 76 | 19 | `37001` Madrid-Villaverde Alto → `37010` Las Margaritas → `37002` Getafe-Centro → `37011` Getafe-Sector 3 → `37012` Parla | validated (rel. 9174510) |
| C4 | `10T0012C4` | 1 | Parla → Madrid-Atocha Cercanías; headsign ∅ (18) | 18 | 18 | `37012` Parla → `37011` Getafe-Sector 3 → `37002` Getafe-Centro → `37010` Las Margaritas → `37001` Madrid-Villaverde Alto → `60100` Madrid-Villaverde Bajo → `18000` Madrid-Atocha Cercanías | validated (rel. 11332) |
| C4 | `10T0012C4` | 2 | Parla → Madrid-Chamartín-Clara Campoamor; headsign ∅ (141) | 141 | 30 | `37012` Parla → `37011` Getafe-Sector 3 → `37002` Getafe-Centro → `37010` Las Margaritas → `37001` Madrid-Villaverde Alto → `60100` Madrid-Villaverde Bajo → `18000` Madrid-Atocha Cercanías → `18101` Sol → `18002` Madrid-Nuevos Ministerios → `17000` Madrid-Chamartín-Clara Campoamor | validated (rel. 11332) |
| C4a | `10T0013C4a` | 1 | Alcobendas-San Sebastián de los Reyes → Madrid-Chamartín-Clara Campoamor; headsign ∅ (30) | 30 | 30 | `19003` Alcobendas-San Sebastián de los Reyes → `19002` Valdelasfuentes → `19001` Universidad Pontificia de Comillas → `17009` Universidad-Cantoblanco → `17001` Fuencarral → `17000` Madrid-Chamartín-Clara Campoamor | validated (rel. 9174510) |
| C4a | `10T0013C4a` | 2 | Alcobendas-San Sebastián de los Reyes → Madrid-Atocha Cercanías; headsign ∅ (139) | 139 | 30 | `19003` Alcobendas-San Sebastián de los Reyes → `19002` Valdelasfuentes → `19001` Universidad Pontificia de Comillas → `17009` Universidad-Cantoblanco → `17001` Fuencarral → `17000` Madrid-Chamartín-Clara Campoamor → `18002` Madrid-Nuevos Ministerios → `18101` Sol → `18000` Madrid-Atocha Cercanías | validated (rel. 9174510) |
| C4a | `10T0013C4a` | 3 | Alcobendas-San Sebastián de los Reyes → Getafe-Centro; headsign ∅ (18) | 18 | 18 | `19003` Alcobendas-San Sebastián de los Reyes → `19002` Valdelasfuentes → `19001` Universidad Pontificia de Comillas → `17009` Universidad-Cantoblanco → `17001` Fuencarral → `17000` Madrid-Chamartín-Clara Campoamor → `18002` Madrid-Nuevos Ministerios → `18101` Sol → `18000` Madrid-Atocha Cercanías → `60100` Madrid-Villaverde Bajo → `37001` Madrid-Villaverde Alto → `37010` Las Margaritas → `37002` Getafe-Centro | validated (rel. 9174510) |
| C4a | `10T0013C4a` | 4 | Alcobendas-San Sebastián de los Reyes → Parla; headsign ∅ (1572) | 1572 | 30 | `19003` Alcobendas-San Sebastián de los Reyes → `19002` Valdelasfuentes → `19001` Universidad Pontificia de Comillas → `17009` Universidad-Cantoblanco → `17001` Fuencarral → `17000` Madrid-Chamartín-Clara Campoamor → `18002` Madrid-Nuevos Ministerios → `18101` Sol → `18000` Madrid-Atocha Cercanías → `60100` Madrid-Villaverde Bajo → `37001` Madrid-Villaverde Alto → `37010` Las Margaritas → `37002` Getafe-Centro → `37011` Getafe-Sector 3 → `37012` Parla | validated (rel. 9174510) |
| C4a | `10T0014C4a` | 1 | Madrid-Chamartín-Clara Campoamor → Alcobendas-San Sebastián de los Reyes; headsign ∅ (1) | 1 | 1 | `17000` Madrid-Chamartín-Clara Campoamor → `17001` Fuencarral → `17009` Universidad-Cantoblanco → `19001` Universidad Pontificia de Comillas → `19002` Valdelasfuentes → `19003` Alcobendas-San Sebastián de los Reyes | validated (rel. 11332) |
| C4a | `10T0014C4a` | 2 | Madrid-Atocha Cercanías → Alcobendas-San Sebastián de los Reyes; headsign ∅ (78) | 78 | 30 | `18000` Madrid-Atocha Cercanías → `18101` Sol → `18002` Madrid-Nuevos Ministerios → `17000` Madrid-Chamartín-Clara Campoamor → `17001` Fuencarral → `17009` Universidad-Cantoblanco → `19001` Universidad Pontificia de Comillas → `19002` Valdelasfuentes → `19003` Alcobendas-San Sebastián de los Reyes | validated (rel. 11332) |
| C4a | `10T0014C4a` | 3 | Getafe-Centro → Alcobendas-San Sebastián de los Reyes; headsign ∅ (18) | 18 | 18 | `37002` Getafe-Centro → `37010` Las Margaritas → `37001` Madrid-Villaverde Alto → `60100` Madrid-Villaverde Bajo → `18000` Madrid-Atocha Cercanías → `18101` Sol → `18002` Madrid-Nuevos Ministerios → `17000` Madrid-Chamartín-Clara Campoamor → `17001` Fuencarral → `17009` Universidad-Cantoblanco → `19001` Universidad Pontificia de Comillas → `19002` Valdelasfuentes → `19003` Alcobendas-San Sebastián de los Reyes | validated (rel. 11332) |
| C4a | `10T0014C4a` | 4 | Parla → Alcobendas-San Sebastián de los Reyes; headsign ∅ (1662) | 1662 | 30 | `37012` Parla → `37011` Getafe-Sector 3 → `37002` Getafe-Centro → `37010` Las Margaritas → `37001` Madrid-Villaverde Alto → `60100` Madrid-Villaverde Bajo → `18000` Madrid-Atocha Cercanías → `18101` Sol → `18002` Madrid-Nuevos Ministerios → `17000` Madrid-Chamartín-Clara Campoamor → `17001` Fuencarral → `17009` Universidad-Cantoblanco → `19001` Universidad Pontificia de Comillas → `19002` Valdelasfuentes → `19003` Alcobendas-San Sebastián de los Reyes | validated (rel. 11332) |
| C4b | `10T0015C4b` | 1 | Colmenar Viejo → Madrid-Atocha Cercanías; headsign ∅ (60) | 60 | 30 | `17005` Colmenar Viejo → `17004` Tres Cantos → `17003` El Goloso → `17009` Universidad-Cantoblanco → `17001` Fuencarral → `17000` Madrid-Chamartín-Clara Campoamor → `18002` Madrid-Nuevos Ministerios → `18101` Sol → `18000` Madrid-Atocha Cercanías | validated (rel. 9174511) |
| C4b | `10T0015C4b` | 2 | Colmenar Viejo → Getafe-Centro; headsign ∅ (18) | 18 | 18 | `17005` Colmenar Viejo → `17004` Tres Cantos → `17003` El Goloso → `17009` Universidad-Cantoblanco → `17001` Fuencarral → `17000` Madrid-Chamartín-Clara Campoamor → `18002` Madrid-Nuevos Ministerios → `18101` Sol → `18000` Madrid-Atocha Cercanías → `60100` Madrid-Villaverde Bajo → `37001` Madrid-Villaverde Alto → `37010` Las Margaritas → `37002` Getafe-Centro | validated (rel. 9174511) |
| C4b | `10T0015C4b` | 3 | Colmenar Viejo → Parla; headsign ∅ (1651) | 1651 | 30 | `17005` Colmenar Viejo → `17004` Tres Cantos → `17003` El Goloso → `17009` Universidad-Cantoblanco → `17001` Fuencarral → `17000` Madrid-Chamartín-Clara Campoamor → `18002` Madrid-Nuevos Ministerios → `18101` Sol → `18000` Madrid-Atocha Cercanías → `60100` Madrid-Villaverde Bajo → `37001` Madrid-Villaverde Alto → `37010` Las Margaritas → `37002` Getafe-Centro → `37011` Getafe-Sector 3 → `37012` Parla | validated (rel. 9174511) |
| C4b | `10T0015C4b` | 4 | Colmenar Viejo → Parla; headsign ∅ (11) | 11 | 11 | `17005` Colmenar Viejo → `17004` Tres Cantos → `17003` El Goloso → `17009` Universidad-Cantoblanco → `17001` Fuencarral → `17000` Madrid-Chamartín-Clara Campoamor → `18101` Sol → `18000` Madrid-Atocha Cercanías → `60100` Madrid-Villaverde Bajo → `37001` Madrid-Villaverde Alto → `37010` Las Margaritas → `37002` Getafe-Centro → `37011` Getafe-Sector 3 → `37012` Parla | partial (rel. 9174511) |
| C4b | `10T0016C4b` | 1 | Madrid-Chamartín-Clara Campoamor → Colmenar Viejo; headsign ∅ (30) | 30 | 30 | `17000` Madrid-Chamartín-Clara Campoamor → `17001` Fuencarral → `17009` Universidad-Cantoblanco → `17003` El Goloso → `17004` Tres Cantos → `17005` Colmenar Viejo | pending |
| C4b | `10T0016C4b` | 2 | Madrid-Atocha Cercanías → Colmenar Viejo; headsign ∅ (60) | 60 | 30 | `18000` Madrid-Atocha Cercanías → `18101` Sol → `18002` Madrid-Nuevos Ministerios → `17000` Madrid-Chamartín-Clara Campoamor → `17001` Fuencarral → `17009` Universidad-Cantoblanco → `17003` El Goloso → `17004` Tres Cantos → `17005` Colmenar Viejo | pending |
| C4b | `10T0016C4b` | 3 | Getafe-Centro → Colmenar Viejo; headsign ∅ (18) | 18 | 18 | `37002` Getafe-Centro → `37010` Las Margaritas → `37001` Madrid-Villaverde Alto → `60100` Madrid-Villaverde Bajo → `18000` Madrid-Atocha Cercanías → `18101` Sol → `18002` Madrid-Nuevos Ministerios → `17000` Madrid-Chamartín-Clara Campoamor → `17001` Fuencarral → `17009` Universidad-Cantoblanco → `17003` El Goloso → `17004` Tres Cantos → `17005` Colmenar Viejo | pending |
| C4b | `10T0016C4b` | 4 | Parla → Colmenar Viejo; headsign ∅ (1632) | 1632 | 30 | `37012` Parla → `37011` Getafe-Sector 3 → `37002` Getafe-Centro → `37010` Las Margaritas → `37001` Madrid-Villaverde Alto → `60100` Madrid-Villaverde Bajo → `18000` Madrid-Atocha Cercanías → `18101` Sol → `18002` Madrid-Nuevos Ministerios → `17000` Madrid-Chamartín-Clara Campoamor → `17001` Fuencarral → `17009` Universidad-Cantoblanco → `17003` El Goloso → `17004` Tres Cantos → `17005` Colmenar Viejo | pending |
| C5 | `10T0017C5` | 1 | Madrid-Atocha Cercanías → Humanes; headsign ∅ (5) | 5 | 5 | `18000` Madrid-Atocha Cercanías → `18003` Méndez Álvaro P.V. → `35702` Doce de Octubre → `35703` Orcasitas → `35704` Puente Alcocer → `37001` Madrid-Villaverde Alto → `35009` Zarzaquemada → `35001` Leganés → `35011` Parque Polvoranca → `35010` La Serna-Fuenlabrada → `35002` Fuenlabrada → `35012` Humanes | validated (rel. 3418150) |
| C5 | `10T0017C5` | 2 | Móstoles-El Soto → Madrid-Atocha Cercanías; headsign ∅ (450) | 450 | 6 | `35607` Móstoles-El Soto → `35606` Móstoles → `35610` Las Retamas → `35605` Alcorcón → `35604` San José de Valderas → `35603` Cuatro Vientos → `35602` Las Águilas → `35601` Maestra Justa Freire-Polidep. Aluche → `35600` Aluche → `35608` Laguna → `35609` Embajadores → `18000` Madrid-Atocha Cercanías | validated (rel. 3418150) |
| C5 | `10T0017C5` | 3 | Móstoles-El Soto → Fuenlabrada; headsign ∅ (1329) | 1329 | 26 | `35607` Móstoles-El Soto → `35606` Móstoles → `35610` Las Retamas → `35605` Alcorcón → `35604` San José de Valderas → `35603` Cuatro Vientos → `35602` Las Águilas → `35601` Maestra Justa Freire-Polidep. Aluche → `35600` Aluche → `35608` Laguna → `35609` Embajadores → `18000` Madrid-Atocha Cercanías → `18003` Méndez Álvaro P.V. → `35702` Doce de Octubre → `35703` Orcasitas → `35704` Puente Alcocer → `37001` Madrid-Villaverde Alto → `35009` Zarzaquemada → `35001` Leganés → `35011` Parque Polvoranca → `35010` La Serna-Fuenlabrada → `35002` Fuenlabrada | validated (rel. 3418150) |
| C5 | `10T0017C5` | 4 | Móstoles-El Soto → Humanes; headsign ∅ (1900) | 1900 | 26 | `35607` Móstoles-El Soto → `35606` Móstoles → `35610` Las Retamas → `35605` Alcorcón → `35604` San José de Valderas → `35603` Cuatro Vientos → `35602` Las Águilas → `35601` Maestra Justa Freire-Polidep. Aluche → `35600` Aluche → `35608` Laguna → `35609` Embajadores → `18000` Madrid-Atocha Cercanías → `18003` Méndez Álvaro P.V. → `35702` Doce de Octubre → `35703` Orcasitas → `35704` Puente Alcocer → `37001` Madrid-Villaverde Alto → `35009` Zarzaquemada → `35001` Leganés → `35011` Parque Polvoranca → `35010` La Serna-Fuenlabrada → `35002` Fuenlabrada → `35012` Humanes | validated (rel. 3418150) |
| C5 | `10T0017C5` | 5 | Madrid-Villaverde Alto → Humanes; headsign ∅ (248) | 248 | 5 | `37001` Madrid-Villaverde Alto → `35009` Zarzaquemada → `35001` Leganés → `35011` Parque Polvoranca → `35010` La Serna-Fuenlabrada → `35002` Fuenlabrada → `35012` Humanes | validated (rel. 3418150) |
| C5 | `10T0018C5` | 1 | Madrid-Atocha Cercanías → Móstoles-El Soto; headsign ∅ (450) | 450 | 7 | `18000` Madrid-Atocha Cercanías → `35609` Embajadores → `35608` Laguna → `35600` Aluche → `35601` Maestra Justa Freire-Polidep. Aluche → `35602` Las Águilas → `35603` Cuatro Vientos → `35604` San José de Valderas → `35605` Alcorcón → `35610` Las Retamas → `35606` Móstoles → `35607` Móstoles-El Soto | validated (rel. 11331) |
| C5 | `10T0018C5` | 2 | Fuenlabrada → Móstoles-El Soto; headsign ∅ (1375) | 1375 | 27 | `35002` Fuenlabrada → `35010` La Serna-Fuenlabrada → `35011` Parque Polvoranca → `35001` Leganés → `35009` Zarzaquemada → `37001` Madrid-Villaverde Alto → `35704` Puente Alcocer → `35703` Orcasitas → `35702` Doce de Octubre → `18003` Méndez Álvaro P.V. → `18000` Madrid-Atocha Cercanías → `35609` Embajadores → `35608` Laguna → `35600` Aluche → `35601` Maestra Justa Freire-Polidep. Aluche → `35602` Las Águilas → `35603` Cuatro Vientos → `35604` San José de Valderas → `35605` Alcorcón → `35610` Las Retamas → `35606` Móstoles → `35607` Móstoles-El Soto | validated (rel. 11331) |
| C5 | `10T0018C5` | 3 | Humanes → Fuenlabrada; headsign ∅ (19) | 19 | 19 | `35012` Humanes → `35002` Fuenlabrada | validated (rel. 11331) |
| C5 | `10T0018C5` | 4 | Humanes → Madrid-Villaverde Alto; headsign ∅ (252) | 252 | 4 | `35012` Humanes → `35002` Fuenlabrada → `35010` La Serna-Fuenlabrada → `35011` Parque Polvoranca → `35001` Leganés → `35009` Zarzaquemada → `37001` Madrid-Villaverde Alto | validated (rel. 11331) |
| C5 | `10T0018C5` | 5 | Humanes → Móstoles-El Soto; headsign ∅ (1851) | 1851 | 26 | `35012` Humanes → `35002` Fuenlabrada → `35010` La Serna-Fuenlabrada → `35011` Parque Polvoranca → `35001` Leganés → `35009` Zarzaquemada → `37001` Madrid-Villaverde Alto → `35704` Puente Alcocer → `35703` Orcasitas → `35702` Doce de Octubre → `18003` Méndez Álvaro P.V. → `18000` Madrid-Atocha Cercanías → `35609` Embajadores → `35608` Laguna → `35600` Aluche → `35601` Maestra Justa Freire-Polidep. Aluche → `35602` Las Águilas → `35603` Cuatro Vientos → `35604` San José de Valderas → `35605` Alcorcón → `35610` Las Retamas → `35606` Móstoles → `35607` Móstoles-El Soto | validated (rel. 11331) |
| C9 | `10T0025C9` | 1 | Cercedilla → Puerto de Navacerrada; headsign ∅ (11) | 11 | 1 | `12006` Cercedilla → `12020` Puerto de Navacerrada | pending |
| C9 | `10T0025C9` | 2 | Cercedilla → Los Cotos; headsign ∅ (21) | 21 | 2 | `12006` Cercedilla → `12020` Puerto de Navacerrada → `12023` Los Cotos | pending |
| C9 | `10T0026C9` | 1 | Puerto de Navacerrada → Cercedilla; headsign ∅ (11) | 11 | 1 | `12020` Puerto de Navacerrada → `12006` Cercedilla | pending |
| C9 | `10T0026C9` | 2 | Los Cotos → Cercedilla; headsign ∅ (21) | 21 | 2 | `12023` Los Cotos → `12020` Puerto de Navacerrada → `12006` Cercedilla | pending |
| C8a | `10T0027C8a` | 1 | Santa María de la Alameda-Peguerinos → El Escorial; headsign ∅ (18) | 18 | 18 | `10206` Santa María de la Alameda-Peguerinos → `10205` Robledo de Chavela → `10204` Zarzalejo → `10203` El Escorial | pending |
| C2 | `10T0037C2` | 1 | Alcalá de Henares → Madrid-Nuevos Ministerios; headsign ∅ (1) | 1 | 1 | `70103` Alcalá de Henares → `70111` La Garena → `70112` Soto del Henares → `70102` Torrejón de Ardoz → `70101` San Fernando de Henares → `70108` Coslada → `70100` Vicálvaro → `70109` Santa Eugenia → `70005` Vallecas → `70003` El Pozo → `70002` Asamblea de Madrid-Entrevías → `18000` Madrid-Atocha Cercanías → `18001` Madrid-Recoletos → `18002` Madrid-Nuevos Ministerios | pending |
| C5 | `10T0047C5` | 1 | Madrid-Atocha Cercanías → Fuenlabrada; headsign ∅ (10) | 10 | 2 | `18000` Madrid-Atocha Cercanías → `37001` Madrid-Villaverde Alto → `35009` Zarzaquemada → `35001` Leganés → `35011` Parque Polvoranca → `35010` La Serna-Fuenlabrada → `35002` Fuenlabrada | partial (rel. 3418150) |
| C5 | `10T0047C5` | 2 | Madrid-Villaverde Alto → Fuenlabrada; headsign ∅ (204) | 204 | 5 | `37001` Madrid-Villaverde Alto → `35009` Zarzaquemada → `35001` Leganés → `35011` Parque Polvoranca → `35010` La Serna-Fuenlabrada → `35002` Fuenlabrada | validated (rel. 3418150) |
| C5 | `10T0048C5` | 1 | Fuenlabrada → Madrid-Villaverde Alto; headsign ∅ (200) | 200 | 4 | `35002` Fuenlabrada → `35010` La Serna-Fuenlabrada → `35011` Parque Polvoranca → `35001` Leganés → `35009` Zarzaquemada → `37001` Madrid-Villaverde Alto | validated (rel. 11331) |
| C5 | `10T0048C5` | 2 | Fuenlabrada → Madrid-Atocha Cercanías; headsign ∅ (10) | 10 | 2 | `35002` Fuenlabrada → `35010` La Serna-Fuenlabrada → `35011` Parque Polvoranca → `35001` Leganés → `35009` Zarzaquemada → `37001` Madrid-Villaverde Alto → `18000` Madrid-Atocha Cercanías | partial (rel. 11331) |
| C7 | `10T0051C7` | 1 | Madrid-Príncipe Pío → Madrid-Chamartín-Clara Campoamor; headsign ∅ (26) | 26 | 26 | `10000` Madrid-Príncipe Pío → `10001` Aravaca → `10002` Pozuelo → `10010` El Barrial-Centro Comercial Pozuelo → `10007` Majadahonda → `10005` Las Rozas → `97100` Pitis → `97200` Mirasierra-Paco de Lucía → `97201` Madrid-Ramón y Cajal → `17000` Madrid-Chamartín-Clara Campoamor | pending |
| C7 | `10T0051C7` | 2 | Madrid-Príncipe Pío → Madrid-Nuevos Ministerios; headsign ∅ (5) | 5 | 5 | `10000` Madrid-Príncipe Pío → `10001` Aravaca → `10002` Pozuelo → `10010` El Barrial-Centro Comercial Pozuelo → `10007` Majadahonda → `10005` Las Rozas → `97100` Pitis → `97200` Mirasierra-Paco de Lucía → `97201` Madrid-Ramón y Cajal → `17000` Madrid-Chamartín-Clara Campoamor → `18002` Madrid-Nuevos Ministerios | pending |
| C7 | `10T0051C7` | 3 | Madrid-Príncipe Pío → Alcalá de Henares; headsign ∅ (938) | 938 | 30 | `10000` Madrid-Príncipe Pío → `10001` Aravaca → `10002` Pozuelo → `10010` El Barrial-Centro Comercial Pozuelo → `10007` Majadahonda → `10005` Las Rozas → `97100` Pitis → `97200` Mirasierra-Paco de Lucía → `97201` Madrid-Ramón y Cajal → `17000` Madrid-Chamartín-Clara Campoamor → `18002` Madrid-Nuevos Ministerios → `18001` Madrid-Recoletos → `18000` Madrid-Atocha Cercanías → `70002` Asamblea de Madrid-Entrevías → `70003` El Pozo → `70005` Vallecas → `70109` Santa Eugenia → `70100` Vicálvaro → `70108` Coslada → `70101` San Fernando de Henares → `70102` Torrejón de Ardoz → `70112` Soto del Henares → `70111` La Garena → `70103` Alcalá de Henares | pending |
| C7 | `10T0051C7` | 4 | Madrid-Príncipe Pío → Guadalajara; headsign ∅ (28) | 28 | 4 | `10000` Madrid-Príncipe Pío → `10001` Aravaca → `10002` Pozuelo → `10010` El Barrial-Centro Comercial Pozuelo → `10007` Majadahonda → `10005` Las Rozas → `97100` Pitis → `97200` Mirasierra-Paco de Lucía → `97201` Madrid-Ramón y Cajal → `17000` Madrid-Chamartín-Clara Campoamor → `18002` Madrid-Nuevos Ministerios → `18001` Madrid-Recoletos → `18000` Madrid-Atocha Cercanías → `70002` Asamblea de Madrid-Entrevías → `70003` El Pozo → `70005` Vallecas → `70109` Santa Eugenia → `70100` Vicálvaro → `70108` Coslada → `70101` San Fernando de Henares → `70102` Torrejón de Ardoz → `70112` Soto del Henares → `70111` La Garena → `70103` Alcalá de Henares → `70107` Alcalá de Henares-Universidad → `70104` Meco → `70105` Azuqueca → `70200` Guadalajara | pending |
| C7 | `10T0052C7` | 1 | Madrid-Chamartín-Clara Campoamor → Madrid-Atocha Cercanías; headsign ∅ (14) | 14 | 14 | `17000` Madrid-Chamartín-Clara Campoamor → `18002` Madrid-Nuevos Ministerios → `18001` Madrid-Recoletos → `18000` Madrid-Atocha Cercanías | pending |
| C7 | `10T0052C7` | 2 | Madrid-Chamartín-Clara Campoamor → Madrid-Príncipe Pío; headsign ∅ (4) | 4 | 4 | `17000` Madrid-Chamartín-Clara Campoamor → `18002` Madrid-Nuevos Ministerios → `18001` Madrid-Recoletos → `18000` Madrid-Atocha Cercanías → `18003` Méndez Álvaro P.V. → `18004` Delicias → `18005` Pirámides → `10000` Madrid-Príncipe Pío | pending |
| C7 | `10T0052C7` | 3 | Alcalá de Henares → Madrid-Príncipe Pío; headsign ∅ (937) | 937 | 30 | `70103` Alcalá de Henares → `70111` La Garena → `70112` Soto del Henares → `70102` Torrejón de Ardoz → `70101` San Fernando de Henares → `70108` Coslada → `70100` Vicálvaro → `70109` Santa Eugenia → `70005` Vallecas → `70003` El Pozo → `70002` Asamblea de Madrid-Entrevías → `18000` Madrid-Atocha Cercanías → `18001` Madrid-Recoletos → `18002` Madrid-Nuevos Ministerios → `17000` Madrid-Chamartín-Clara Campoamor → `97201` Madrid-Ramón y Cajal → `97200` Mirasierra-Paco de Lucía → `97100` Pitis → `10005` Las Rozas → `10007` Majadahonda → `10010` El Barrial-Centro Comercial Pozuelo → `10002` Pozuelo → `10001` Aravaca → `10000` Madrid-Príncipe Pío | pending |
| C7 | `10T0052C7` | 4 | Guadalajara → Madrid-Príncipe Pío; headsign ∅ (78) | 78 | 19 | `70200` Guadalajara → `70105` Azuqueca → `70104` Meco → `70107` Alcalá de Henares-Universidad → `70103` Alcalá de Henares → `70111` La Garena → `70112` Soto del Henares → `70102` Torrejón de Ardoz → `70101` San Fernando de Henares → `70108` Coslada → `70100` Vicálvaro → `70109` Santa Eugenia → `70005` Vallecas → `70003` El Pozo → `70002` Asamblea de Madrid-Entrevías → `18000` Madrid-Atocha Cercanías → `18001` Madrid-Recoletos → `18002` Madrid-Nuevos Ministerios → `17000` Madrid-Chamartín-Clara Campoamor → `97201` Madrid-Ramón y Cajal → `97200` Mirasierra-Paco de Lucía → `97100` Pitis → `10005` Las Rozas → `10007` Majadahonda → `10010` El Barrial-Centro Comercial Pozuelo → `10002` Pozuelo → `10001` Aravaca → `10000` Madrid-Príncipe Pío | pending |
| C7 | `10T0053C7` | 1 | Madrid-Príncipe Pío → Madrid-Atocha Cercanías; headsign ∅ (29) | 29 | 29 | `10000` Madrid-Príncipe Pío → `10001` Aravaca → `10002` Pozuelo → `10010` El Barrial-Centro Comercial Pozuelo → `10007` Majadahonda → `10005` Las Rozas → `97100` Pitis → `97200` Mirasierra-Paco de Lucía → `97201` Madrid-Ramón y Cajal → `17000` Madrid-Chamartín-Clara Campoamor → `18002` Madrid-Nuevos Ministerios → `18001` Madrid-Recoletos → `18000` Madrid-Atocha Cercanías | pending |
| C7 | `10T0053C7` | 2 | Alcalá de Henares → Madrid-Atocha Cercanías; headsign ∅ (3) | 3 | 3 | `70103` Alcalá de Henares → `18000` Madrid-Atocha Cercanías | pending |
| C7 | `10T0054C7` | 1 | Madrid-Atocha Cercanías → Madrid-Príncipe Pío; headsign ∅ (30) | 30 | 30 | `18000` Madrid-Atocha Cercanías → `18001` Madrid-Recoletos → `18002` Madrid-Nuevos Ministerios → `17000` Madrid-Chamartín-Clara Campoamor → `97201` Madrid-Ramón y Cajal → `97200` Mirasierra-Paco de Lucía → `97100` Pitis → `10005` Las Rozas → `10007` Majadahonda → `10010` El Barrial-Centro Comercial Pozuelo → `10002` Pozuelo → `10001` Aravaca → `10000` Madrid-Príncipe Pío | pending |
| C7 | `10T0054C7` | 2 | Madrid-Atocha Cercanías → Alcalá de Henares; headsign ∅ (3) | 3 | 3 | `18000` Madrid-Atocha Cercanías → `70103` Alcalá de Henares | pending |
| C7 | `10T0059C7` | 1 | Madrid-Chamartín-Clara Campoamor → Alcalá de Henares; headsign ∅ (57) | 57 | 30 | `17000` Madrid-Chamartín-Clara Campoamor → `18002` Madrid-Nuevos Ministerios → `18001` Madrid-Recoletos → `18000` Madrid-Atocha Cercanías → `70002` Asamblea de Madrid-Entrevías → `70003` El Pozo → `70005` Vallecas → `70109` Santa Eugenia → `70100` Vicálvaro → `70108` Coslada → `70101` San Fernando de Henares → `70102` Torrejón de Ardoz → `70112` Soto del Henares → `70111` La Garena → `70103` Alcalá de Henares | pending |
| C7 | `10T0060C7` | 1 | Alcalá de Henares → Madrid-Chamartín-Clara Campoamor; headsign ∅ (8) | 8 | 4 | `70103` Alcalá de Henares → `70111` La Garena → `70112` Soto del Henares → `70102` Torrejón de Ardoz → `70101` San Fernando de Henares → `70108` Coslada → `70100` Vicálvaro → `70109` Santa Eugenia → `70005` Vallecas → `70003` El Pozo → `70002` Asamblea de Madrid-Entrevías → `18000` Madrid-Atocha Cercanías → `18001` Madrid-Recoletos → `18002` Madrid-Nuevos Ministerios → `17000` Madrid-Chamartín-Clara Campoamor | pending |
| C8a | `10T0061C8a` | 1 | Villalba de Guadarrama → Madrid-Chamartín-Clara Campoamor; headsign ∅ (31) | 31 | 2 | `10200` Villalba de Guadarrama → `10104` Galapagar-La Navata → `10103` Torrelodones → `10101` Las Matas → `10100` Pinar de las Rozas → `97100` Pitis → `97200` Mirasierra-Paco de Lucía → `97201` Madrid-Ramón y Cajal → `17000` Madrid-Chamartín-Clara Campoamor | pending |
| C8a | `10T0061C8a` | 2 | El Escorial → Madrid-Chamartín-Clara Campoamor; headsign ∅ (550) | 550 | 29 | `10203` El Escorial → `10202` Las Zorreras-Navalquejigo → `10201` San Yago → `10200` Villalba de Guadarrama → `10104` Galapagar-La Navata → `10103` Torrelodones → `10101` Las Matas → `10100` Pinar de las Rozas → `97100` Pitis → `97200` Mirasierra-Paco de Lucía → `97201` Madrid-Ramón y Cajal → `17000` Madrid-Chamartín-Clara Campoamor | pending |
| C8a | `10T0061C8a` | 3 | El Escorial → Santa María de la Alameda-Peguerinos; headsign ∅ (79) | 79 | 30 | `10203` El Escorial → `10204` Zarzalejo → `10205` Robledo de Chavela → `10206` Santa María de la Alameda-Peguerinos | pending |
| C8a | `10T0062C8a` | 1 | Santa María de la Alameda-Peguerinos → El Escorial; headsign ∅ (5) | 5 | 3 | `10206` Santa María de la Alameda-Peguerinos → `10205` Robledo de Chavela → `10204` Zarzalejo → `10203` El Escorial | pending |
| C8a | `10T0062C8a` | 2 | Madrid-Chamartín-Clara Campoamor → Villalba de Guadarrama; headsign ∅ (28) | 28 | 2 | `17000` Madrid-Chamartín-Clara Campoamor → `97201` Madrid-Ramón y Cajal → `97200` Mirasierra-Paco de Lucía → `97100` Pitis → `10100` Pinar de las Rozas → `10101` Las Matas → `10103` Torrelodones → `10104` Galapagar-La Navata → `10200` Villalba de Guadarrama | pending |
| C8a | `10T0062C8a` | 3 | Madrid-Chamartín-Clara Campoamor → El Escorial; headsign ∅ (557) | 557 | 29 | `17000` Madrid-Chamartín-Clara Campoamor → `97201` Madrid-Ramón y Cajal → `97200` Mirasierra-Paco de Lucía → `97100` Pitis → `10100` Pinar de las Rozas → `10101` Las Matas → `10103` Torrelodones → `10104` Galapagar-La Navata → `10200` Villalba de Guadarrama → `10201` San Yago → `10202` Las Zorreras-Navalquejigo → `10203` El Escorial | pending |
| C10 | `10T0064C10` | 1 | Madrid-Príncipe Pío → Madrid-Chamartín-Clara Campoamor; headsign ∅ (30) | 30 | 30 | `10000` Madrid-Príncipe Pío → `18005` Pirámides → `18004` Delicias → `18003` Méndez Álvaro P.V. → `18000` Madrid-Atocha Cercanías → `18001` Madrid-Recoletos → `18002` Madrid-Nuevos Ministerios → `17000` Madrid-Chamartín-Clara Campoamor | pending |
| C10 | `10T0064C10` | 2 | Madrid-Atocha Cercanías → El Escorial; headsign ∅ (4) | 4 | 4 | `18000` Madrid-Atocha Cercanías → `18003` Méndez Álvaro P.V. → `18004` Delicias → `18005` Pirámides → `10000` Madrid-Príncipe Pío → `10001` Aravaca → `10002` Pozuelo → `10010` El Barrial-Centro Comercial Pozuelo → `10007` Majadahonda → `10005` Las Rozas → `10100` Pinar de las Rozas → `10101` Las Matas → `10103` Torrelodones → `10104` Galapagar-La Navata → `10200` Villalba de Guadarrama → `10201` San Yago → `10202` Las Zorreras-Navalquejigo → `10203` El Escorial | pending |
| C10 | `10T0064C10` | 3 | Madrid-Nuevos Ministerios → El Escorial; headsign ∅ (4) | 4 | 4 | `18002` Madrid-Nuevos Ministerios → `18001` Madrid-Recoletos → `18000` Madrid-Atocha Cercanías → `18003` Méndez Álvaro P.V. → `18004` Delicias → `18005` Pirámides → `10000` Madrid-Príncipe Pío → `10001` Aravaca → `10002` Pozuelo → `10010` El Barrial-Centro Comercial Pozuelo → `10007` Majadahonda → `10005` Las Rozas → `10100` Pinar de las Rozas → `10101` Las Matas → `10103` Torrelodones → `10104` Galapagar-La Navata → `10200` Villalba de Guadarrama → `10201` San Yago → `10202` Las Zorreras-Navalquejigo → `10203` El Escorial | pending |
| C10 | `10T0075C10` | 1 | Pinar de las Rozas → Madrid-Chamartín-Clara Campoamor; headsign ∅ (959) | 959 | 30 | `10100` Pinar de las Rozas → `10005` Las Rozas → `10007` Majadahonda → `10010` El Barrial-Centro Comercial Pozuelo → `10002` Pozuelo → `10001` Aravaca → `10000` Madrid-Príncipe Pío → `18005` Pirámides → `18004` Delicias → `18003` Méndez Álvaro P.V. → `18000` Madrid-Atocha Cercanías → `18001` Madrid-Recoletos → `18002` Madrid-Nuevos Ministerios → `17000` Madrid-Chamartín-Clara Campoamor | pending |
| C10 | `10T0076C10` | 1 | Madrid-Chamartín-Clara Campoamor → Madrid-Atocha Cercanías; headsign ∅ (29) | 29 | 29 | `17000` Madrid-Chamartín-Clara Campoamor → `18002` Madrid-Nuevos Ministerios → `18001` Madrid-Recoletos → `18000` Madrid-Atocha Cercanías | pending |
| C10 | `10T0076C10` | 2 | Madrid-Chamartín-Clara Campoamor → Pinar de las Rozas; headsign ∅ (958) | 958 | 30 | `17000` Madrid-Chamartín-Clara Campoamor → `18002` Madrid-Nuevos Ministerios → `18001` Madrid-Recoletos → `18000` Madrid-Atocha Cercanías → `18003` Méndez Álvaro P.V. → `18004` Delicias → `18005` Pirámides → `10000` Madrid-Príncipe Pío → `10001` Aravaca → `10002` Pozuelo → `10010` El Barrial-Centro Comercial Pozuelo → `10007` Majadahonda → `10005` Las Rozas → `10100` Pinar de las Rozas | pending |
| C8a | `10T0085C8a` | 1 | Santa María de la Alameda-Peguerinos → El Escorial; headsign ∅ (74) | 74 | 28 | `10206` Santa María de la Alameda-Peguerinos → `10205` Robledo de Chavela → `10204` Zarzalejo → `10203` El Escorial | pending |
| C8b | `10T0087C8b` | 1 | Madrid-Chamartín-Clara Campoamor → Cercedilla; headsign ∅ (11) | 11 | 11 | `17000` Madrid-Chamartín-Clara Campoamor → `10200` Villalba de Guadarrama → `12001` Los Negrales → `12002` Alpedrete → `12004` Collado Mediano → `12005` Los Molinos-Guadarrama → `12006` Cercedilla | pending |
| C8b | `10T0087C8b` | 2 | Madrid-Chamartín-Clara Campoamor → Cercedilla; headsign ∅ (555) | 555 | 30 | `17000` Madrid-Chamartín-Clara Campoamor → `97201` Madrid-Ramón y Cajal → `97200` Mirasierra-Paco de Lucía → `97100` Pitis → `10100` Pinar de las Rozas → `10101` Las Matas → `10103` Torrelodones → `10104` Galapagar-La Navata → `10200` Villalba de Guadarrama → `12001` Los Negrales → `12002` Alpedrete → `12004` Collado Mediano → `12005` Los Molinos-Guadarrama → `12006` Cercedilla | pending |
| C8b | `10T0088C8b` | 1 | Cercedilla → Madrid-Chamartín-Clara Campoamor; headsign ∅ (566) | 566 | 30 | `12006` Cercedilla → `12005` Los Molinos-Guadarrama → `12004` Collado Mediano → `12002` Alpedrete → `12001` Los Negrales → `10200` Villalba de Guadarrama → `10104` Galapagar-La Navata → `10103` Torrelodones → `10101` Las Matas → `10100` Pinar de las Rozas → `97100` Pitis → `97200` Mirasierra-Paco de Lucía → `97201` Madrid-Ramón y Cajal → `17000` Madrid-Chamartín-Clara Campoamor | pending |
| C8b | `10T0098C8b` | 1 | Cercedilla → Cercedilla; headsign ∅ (54) | 54 | 25 | `12006` Cercedilla | pending |
| C8a | `10T0107C8a` | 1 | Las Matas → Las Rozas; headsign ∅ (4) | 4 | 2 | `10101` Las Matas → `10100` Pinar de las Rozas → `10005` Las Rozas | pending |
| C9 | `10T0110C9` | 1 | Cercedilla → Los Cotos; headsign ∅ (95) | 95 | 19 | `12006` Cercedilla → `12020` Puerto de Navacerrada → `12023` Los Cotos | pending |
| C9 | `10T0111C9` | 1 | Los Cotos → Cercedilla; headsign ∅ (95) | 95 | 19 | `12023` Los Cotos → `12020` Puerto de Navacerrada → `12006` Cercedilla | pending |

### Duplicaciones y coherencia física de las secuencias

No hay `trip_id`, `route_id` ni `stop_id` duplicados; tampoco hay patrones con
una parada repetida ni retrocesos inmediatos `A→B→A`. Aparecen seis grupos de
secuencia idéntica bajo IDs distintos:

| Secuencia compartida | `route_id` | Interpretación |
|---|---|---|
| Alcalá de Henares → Chamartín (15 paradas) | `10T0005C2`, `10T0060C7` | mismo corredor bajo C2/C7; el catálogo preserva la identidad comercial |
| Chamartín → Alcalá de Henares (15) | `10T0006C2`, `10T0059C7` | inverso del anterior, C2/C7 |
| Cercedilla → Cotos (3) | `10T0025C9`, `10T0110C9` | misma C9; servicios disjuntos (`1033L`/`1034M` frente a los otros 19) |
| Cotos → Cercedilla (3) | `10T0026C9`, `10T0111C9` | mismo reparto de calendario de C9 |
| `10206→10205→10204→10203` | `10T0027C8a`, `10T0062C8a`, `10T0085C8a` | subpatrón compartido por variantes C8a, sin colisión de `trip_id` |
| Chamartín → Atocha (4) | `10T0052C7`, `10T0076C10` | tronco compartido C7/C10 |

Estas coincidencias no se colapsan: `route_id` es identidad GTFS y `Catalog`
agrupa las variantes por `(network_id, short_name)` conservándolas. El máximo
salto recto entre paradas consecutivas es 32.444 m (`17000→10200`, patrón
exprés de C8b); hay además dos saltos de 28.845 m en C7. Los tres son saltos
por omisión de paradas, mantienen orden sobre el shape GTFS de la línea y no
prueban teletransporte. La correspondencia con la vía OSM queda para AUD-03.

### Comparación exacta con `packages.gtfs.catalog.Catalog`

La igualdad no se limitó a `len(...)`:

- conjunto completo de `route_id`: igual;
- tuplas `(short_name, network_id, route_ids)`: iguales;
- diccionario completo `(route_id, stop_ids) → trip_count`: igual, 103/103;
- conjunto de 95 `stop_id`: igual;
- conjunto de 121 huérfanos: igual;
- servicios e instancias programadas válidas: iguales para cada uno de los 30
  días.

Por tanto, `Catalog` es una reconstrucción fiel de la convención declarada. No
convierte los huérfanos en patrones, pero sí admite el patrón de una sola
parada porque `validate_topology` solo exige secuencia no vacía y
`PatternIdentity` acepta «al menos una parada»; el motor de movimiento lo
rechaza después por tener menos de dos.

### Hallazgos

#### AUD02-P2-001 — Los totales correctos mezclan identidad de fuente con recorridos utilizables

- **Identificador:** `AUD02-P2-001`.
- **Componente:** catálogo GTFS y lenguaje de cierre del Hito 3.
- **Severidad:** **P2**.
- **Evidencia reproducible:** `python3 scratch/aud02_rebuild.py summary` devuelve
  42 rutas, 103 patrones y 121 huérfanos; el inventario muestra 7 huérfanos en
  `10T0035C5`, 114 en `10T0097C8b`, y 54 trips de `10T0098C8b` en el único
  patrón `12006` (Cercedilla → Cercedilla). La reconstrucción da 102 patrones
  con al menos dos paradas y 40 rutas con al menos uno.
- **Archivo/símbolo/dato:** `packages/gtfs/topology.py::validate_topology`,
  `packages/gtfs/catalog.py::build_catalog`, `trips.txt`, `stop_times.txt`,
  `route_id=10T0035C5|10T0097C8b|10T0098C8b`.
- **Riesgo:** interpretar «42 rutas/103 patrones» como 42 recorridos completos y
  103 trayectorias animables; el motor no puede construir horario para 121
  trips ni movimiento para el patrón de una parada.
- **Causa raíz:** el feed conserva fragmentos de bloque/cambio de ruta y trips
  sin horario; el recuento de catálogo mide identidad GTFS, mientras la frase
  de cierre omite la dimensión de usabilidad.
- **Alternativas:** (A) conservar los conteos de fuente y publicar al lado
  `routes_with_patterns`, `traversable_patterns` y `orphan_trips`; (B) excluir
  lo degenerado del catálogo, perdiendo fidelidad; (C) fabricar paradas, no
  aceptable.
- **Recomendación:** **A**. Mantener 12/42/103/95 como inventario bruto, pero
  presentar siempre 40/102/121 como calidad operacional asociada.
- **Prueba de cierre:** prueba sobre este SHA que exija simultáneamente
  `42/40`, `103/102`, `121`, y contrato/API/documentación que distinga
  `source_pattern` de `movement_usable` sin inventar topología.

#### AUD02-P2-002 — DEC-039 no cubre servicios que se prolongan dos o más fechas civiles

- **Identificador:** `AUD02-P2-002`.
- **Componente:** resolución de fecha de servicio tras medianoche.
- **Severidad:** **P2** (sin impacto en el ZIP auditado, cuyo máximo Madrid es
  `24:53`; defecto real de generalidad aceptada por el parser).
- **Evidencia reproducible:** el comando sintético de la sección de comandos
  crea un trip de `48:30` a `49:00`, activo solo el 2026-11-20, y consulta el
  2026-11-22 a las 00:45. Resultado: horizonte `90000.0`, candidatos
  `('2026-11-21','2026-11-22')`, resuelto `2026-11-22`; esperado
  `2026-11-20`. La [referencia oficial GTFS](https://gtfs.org/documentation/schedule/reference/)
  exige valores mayores que `24:00:00` para horas posteriores a medianoche y
  no fija aquí un tope de 47:59.
- **Archivo/símbolo/dato:** `apps/api/service.py::service_dates_covering`
  (`first = _service_date(start) - timedelta(days=1)`) y
  `ServiceDateResolver.for_trip`.
- **Riesgo:** si Renfe u otro feed compatible publica un servicio de más de 48
  horas, snapshot y tablero lo asignan al día civil equivocado aunque el
  horizonte se calcule correctamente del dato.
- **Causa raíz:** el horizonte es dinámico, pero el número de fechas candidatas
  está codificado a una sola fecha anterior.
- **Alternativas:** (A) retroceder `ceil(extended_horizon_s / 86400)` fechas;
  (B) imponer y validar un límite documental `<48h`; (C) mantener la asunción
  silenciosa.
- **Recomendación:** **A**, con un límite defensivo explícito contra feeds
  patológicos si se considera necesario.
- **Prueba de cierre:** regresión con `49:00` que incluya `2026-11-20` en
  candidatos y resuelva el trip a esa fecha, manteniendo en verde las pruebas
  `24:xx`, lookback/lookahead y DST existentes.

#### AUD02-DESCARTADO-001 — No hay discrepancia entre el recuento manual y `Catalog`

- **Identificador:** `AUD02-DESCARTADO-001`.
- **Componente:** `packages.gtfs.catalog.Catalog`.
- **Severidad:** **DESCARTADO**.
- **Evidencia reproducible:** el bloque «comparación exacta» imprime
  `route_ids_equal True`, `lines_equal True`, `patterns_equal True manual 103
  code 103`, `stops_equal True 95 95`, `orphans_equal True` y
  `all_30_service_days_equal True`.
- **Archivo/símbolo/dato:** `packages/gtfs/parser.py::load_feed`,
  `packages/gtfs/topology.py::validate_topology`,
  `packages/gtfs/catalog.py::build_catalog`.
- **Riesgo:** hipótesis auditada: que el código colapsara variantes, perdiera
  estaciones o contara patrones de otro núcleo.
- **Causa raíz:** no aplica; no se reprodujo discrepancia.
- **Alternativas:** comparar solo totales (insuficiente) o comparar todas las
  claves y secuencias (método usado).
- **Recomendación:** conservar la comparación estructural y el SHA del ZIP como
  gate de futuros cierres.
- **Prueba de cierre:** ya satisfecha para este SHA; repetir la igualdad de
  diccionarios, no solo cuatro `len`, ante cada nueva versión del feed.

#### AUD02-DESCARTADO-002 — Las secuencias compartidas no son duplicados accidentales del catálogo

- **Identificador:** `AUD02-DESCARTADO-002`.
- **Componente:** agrupación por línea/variante/patrón.
- **Severidad:** **DESCARTADO**.
- **Evidencia reproducible:** `python3 scratch/aud02_rebuild.py anomalies`
  enumera los seis grupos de secuencia compartida; no hay IDs repetidos,
  estaciones repetidas dentro de un patrón ni `A→B→A`. C9 separa los mismos
  recorridos en conjuntos de servicio disjuntos y C2/C7/C10 comparten tramos
  bajo identidades comerciales diferentes.
- **Archivo/símbolo/dato:** `Topology.route_groups`, `Catalog.lines`, tabla de
  secuencias de este documento.
- **Riesgo:** colapsar por secuencia borraría `route_id`, línea comercial y
  calendario; no colapsar podría confundirse con duplicación si se presenta
  como «rutas físicas únicas».
- **Causa raíz:** la red comparte infraestructura y Renfe emite IDs de ruta
  distintos por variante/calendario.
- **Alternativas:** (A) preservar identidad GTFS y exponer equivalencias
  topológicas; (B) deduplicar destructivamente por `stop_ids`.
- **Recomendación:** **A**; llamar a 42 «`route_id` de fuente», no «42 trazados
  físicos distintos».
- **Prueba de cierre:** una regresión debe mantener los 42 IDs y, por separado,
  poder informar las 96 secuencias ordenadas únicas si se necesita una métrica
  de topología independiente de la identidad comercial.

#### AUD02-NO-VERIFICADO-001 — Correspondencia física OSM de 31 patrones no auditada en AUD-02

- **Identificador:** `AUD02-NO-VERIFICADO-001`.
- **Componente:** catálogo de corredores OSM de MP-018.
- **Severidad:** **NO VERIFICADO** (alcance explícito de AUD-03).
- **Evidencia reproducible:** el cruce de IDs confirma 103/103 filas y estados
  `28 validated / 3 partial / 72 pending`, pero AUD-02 no vuelve a encadenar
  ways ni a proyectar estaciones sobre las geometrías OSM.
- **Archivo/símbolo/dato:** `packages/geo/catalog.py`, fixtures OSM,
  `docs/evidence/mp-018-corridor-coverage.csv`.
- **Riesgo:** un `pattern_id` correcto puede apuntar a una relation incompleta,
  invertida o distante; el estado autodeclarado no es evidencia independiente.
- **Causa raíz:** separación deliberada de responsabilidades entre AUD-02
  (GTFS) y AUD-03 (OSM).
- **Alternativas:** duplicar la auditoría OSM aquí o mantener el gate dedicado.
- **Recomendación:** mantener el gate dedicado y no elevar `validated` a hecho
  auditado hasta que AUD-03 lo cierre.
- **Prueba de cierre:** AUD-03 debe reconstruir relations/ways desde las
  fixtures, verificar checksum, continuidad, sentido, orden de estaciones y
  distancia máxima para las 31 entradas no `pending`.

#### AUD02-NO-VERIFICADO-002 — ADD/REMOVE no puede contrastarse con una excepción real de este feed

- **Identificador:** `AUD02-NO-VERIFICADO-002`.
- **Componente:** `calendar_dates.txt`.
- **Severidad:** **NO VERIFICADO** contra dato real; **verificado sintéticamente**.
- **Evidencia reproducible:** `unzip -Z1 ... | rg calendar_dates` no encuentra
  el fichero; las tres pruebas focales ADD/REMOVE/ausencia pasan.
- **Archivo/símbolo/dato:** `packages/gtfs/parser.py::CalendarException`,
  `packages/gtfs/catalog.py::scheduled_service_ids_for_date`.
- **Riesgo:** una regresión de parseo con el formato real de un productor no se
  detectaría usando este ZIP de Renfe; la semántica de conjuntos sí está
  cubierta.
- **Causa raíz:** Renfe no publica `calendar_dates.txt` en el artefacto auditado.
- **Alternativas:** fixture sintética (actual), fixture mínima literal de otro
  feed oficial con licencia/procedencia, o esperar a que Renfe lo publique.
- **Recomendación:** mantener las regresiones actuales y, si entra una fuente
  real con excepciones, congelar una fixture trazable antes de declarar
  verificación empírica.
- **Prueba de cierre:** parsear una fixture atribuida con un ADD y un REMOVE y
  demostrar el cambio de instancias en sus dos fechas, además de las pruebas
  unitarias existentes.

### Comandos reproducibles ejecutados

Desde la raíz de este worktree:

```sh
shasum -a 256 data/hito-03/replay/fomento_transit.zip
unzip -l data/hito-03/replay/fomento_transit.zip
for f in routes.txt trips.txt stops.txt stop_times.txt shapes.txt calendar.txt; do
  printf '%s ' "$f"
  unzip -p data/hito-03/replay/fomento_transit.zip "$f" | wc -l
done
unzip -Z1 data/hito-03/replay/fomento_transit.zip | rg -x 'calendar_dates\.txt'

python3 scratch/aud02_rebuild.py summary
python3 scratch/aud02_rebuild.py routes
python3 scratch/aud02_rebuild.py patterns
python3 scratch/aud02_rebuild.py anomalies
```

Confirmación de que el patrón de una parada no es utilizable por el motor:

```sh
.venv/bin/python - <<'PY'
from packages.gtfs import load_feed
from packages.movement.schedule import build_trip_schedule
t=load_feed('data/hito-03/replay/fomento_transit.zip',network_id='10')
try:
    build_trip_schedule(t,None,'1023V17127C8b')
except Exception as error:
    print(type(error).__name__,str(error))
PY
# ValueError trip '1023V17127C8b' no tiene al menos dos stop_times
```

Comparación completa contra el producto:

```sh
python3 - <<'PY'
from pathlib import Path
from datetime import date, timedelta
import hashlib, importlib.util
from packages.gtfs import load_feed, build_catalog, scheduled_service_ids_for_date, scheduled_trip_instances_for_date
spec=importlib.util.spec_from_file_location('aud02','scratch/aud02_rebuild.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
p=Path('data/hito-03/replay/fomento_transit.zip')
routes,trips,by_trip,stops,calendar,calendar_dates,shapes=m.load(p)
manual=m.build_patterns(routes,trips,by_trip)
top=load_feed(p,network_id='10')
cat=build_catalog(top,gtfs_version='sha256:'+hashlib.sha256(p.read_bytes()).hexdigest())
manual_lines={}
for rid,r in routes.items(): manual_lines.setdefault(r['route_short_name'],[]).append(rid)
manual_patterns={(x['route_id'],x['stop_ids']):x['trip_count'] for x in manual}
code_patterns={(p.route_id,p.stop_ids):p.trip_count for line in cat.lines for p in line.patterns}
print('route_ids_equal', {r.route_id for r in top.routes} == set(routes))
print('lines_equal', {(x.short_name,x.network_id,x.route_ids) for x in cat.lines} == {(n,'10',tuple(sorted(ids))) for n,ids in manual_lines.items()})
print('patterns_equal', code_patterns == manual_patterns, 'manual',len(manual_patterns),'code',len(code_patterns))
print('stops_equal', {s.stop_id for s in top.stops} == set(stops), len(top.stops), len(stops))
print('orphans_equal', {t.trip_id for t in top.trips if not top.stop_times_for_trip(t.trip_id)} == (set(trips)-set(by_trip)))
weekdays=('monday','tuesday','wednesday','thursday','friday','saturday','sunday')
for d in (date(2026,11,20)+timedelta(days=i) for i in range(30)):
    manual_services={sid for sid,row in calendar.items() if row[weekdays[d.weekday()]]=='1' and row['start_date'] <= d.strftime('%Y%m%d') <= row['end_date']}
    code_services=set(scheduled_service_ids_for_date(top,d))
    manual_instances={tid for tid,t in trips.items() if t['service_id'] in manual_services and tid in by_trip}
    code_instances={x.trip_id for x in scheduled_trip_instances_for_date(top,d)}
    if manual_services != code_services or manual_instances != code_instances:
        print('MISMATCH',d,manual_services^code_services,len(manual_instances^code_instances)); break
else: print('all_30_service_days_equal',True)
PY
```

Regresiones temporal/calendario ejecutadas:

```sh
.venv/bin/python -m unittest \
  packages.gtfs.tests.test_catalog.ScheduledServiceIdsSyntheticTests.test_calendar_dates_exception_type_1_adds_a_service_outside_its_weekday \
  packages.gtfs.tests.test_catalog.ScheduledServiceIdsSyntheticTests.test_calendar_dates_exception_type_2_removes_a_service_within_its_weekday \
  packages.gtfs.tests.test_catalog.ScheduledServiceIdsSyntheticTests.test_absent_calendar_dates_behaves_exactly_like_calendar_only \
  apps.api.tests.test_snapshot_contract.ServiceDatesCoveringTests \
  packages.movement.tests.test_rendering.ServiceDayArithmeticTests -v
```

Reproducción del caso `49:00` no cubierto:

```sh
.venv/bin/python - <<'PY'
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from packages.gtfs import CalendarService, Route, Stop, StopTime, Topology, Trip
from apps.api.service import ServiceDateResolver, extended_service_horizon_s
MADRID=ZoneInfo('Europe/Madrid')
topology=Topology(
 routes=(Route('10T9999X','X','Sintética >48h',2,'000000','ffffff'),),
 trips=(Trip('10T9999X','FRIDAY','trip-49h','Destino',1,'','shape'),),
 stops=(Stop('A','A',40,-3,1),Stop('B','B',40.1,-3.1,1)),
 stop_times=(StopTime('trip-49h','48:30:00','48:30:00','A',1),StopTime('trip-49h','49:00:00','49:00:00','B',2)),
 shape_points=(),
 calendar=(CalendarService('FRIDAY',False,False,False,False,True,False,False,'20261120','20261120'),),
)
now=datetime(2026,11,22,0,45,tzinfo=MADRID).astimezone(timezone.utc)
h=extended_service_horizon_s(topology)
r=ServiceDateResolver(topology,now,extended_horizon_s=h)
print('horizon_s',h)
print('candidates',tuple(d.isoformat() for d in r.candidates))
print('resolved',r.for_trip('trip-49h').isoformat(),'expected','2026-11-20')
PY
```

Resultado de pruebas focales: **14/14 OK**. No se ejecutó ni se declara la
suite completa: esta tarea no modifica producto.

## Geometría OSM (AUD-03)

**Ejecuta AUD-03:** OpenAI Codex (auditoría adversarial)

**Revisa AUD-03:** Claude Opus · High — ronda 1 **CHANGES_REQUESTED**, ronda 2 **APPROVED** (ver las dos secciones de revisión al final de este documento)

**Fecha:** 2026-11-23

### Veredicto

Los 75 patrones no `validated` no son 75 ausencias independientes de vía en
OSM. El mecanismo de producto deja **72 patrones `pending` sin ejecutarles
ninguna prueba geométrica**: ninguno de sus `route_id` figura en un
`GeometrySourceSpec`. Los otros tres sí pasan la prueba geométrica y una
`PatternCaveat` manual los rebaja a `partial`.

La partición causal de esos 72 `pending`, que el `reason` uniforme del CSV no
conserva, es:

| Causa demostrada | Patrones | Circulaciones del feed | Llamadas a estación | Diagnóstico |
|---|---:|---:|---:|---|
| sin fuente congelada ni intento registrado, accionables por lote geométrico | 67 | 20.273 | 269.988 | insuficiencia de información congelada; **no** demuestra geometría ausente en OSM |
| C4b opuesta con dos `502` registrados | 4 | 1.740 | 25.434 | la vía ya existe en `9174511` invertida; falta resolver el sentido físico correcto |
| feed de origen truncado: patrón residual de una parada | 1 | 54 | 54 | no se arregla descargando geometría |
| `PatternCaveat` manual rebaja una geometría que sí pasa continuidad/distancia/orden | 3 | 31 | 294 | falso negativo del criterio; omitir paradas no prueba otra vía |
| **Total** | **75** | **22.098** | **295.770** | 3 `partial` + 72 `pending` |

El resultado operativo sigue siendo honesto: `can_map_match` solo es verdadero
para `validated` y `match_position` devuelve GPS `raw` etiquetado para
`partial`/`pending`; no encontré una proyección fabricada. El defecto es de
cobertura y de clasificación conservadora, no de presentar un punto estimado
como observado.

### Criterio exacto auditado

`PatternIdentity.from_pattern()` forma la identidad con
`route_id + "\0" + stop_ids ordenados`, aplica SHA-256 y conserva 20
hexadecimales. Origen/destino y `direction_key` salen de la primera y última
parada; no se usa un `direction_id` inexistente.

`build_corridor_catalog()` solo considera una fuente cuando el `route_id` del
patrón figura literalmente en `GeometrySourceSpec.route_ids`. Para cada fuente
admitida exige, por este orden: relación sin `ChainGap`, todas las paradas
presentes, distancia máxima de cada parada al eje `<=150 m` y arcos monótonos
en el sentido del patrón. Si no hay candidato ni fallo parcial, el patrón queda
`pending`. Si hay candidato válido, una entrada manual en `_known_caveats()`
todavía puede rebajarlo a `partial`. Por tanto:

- `pending` significa en los **72 casos** que ninguna fuente fue candidata por
  `route_id`, así que el código no ejecutó continuidad, distancia ni orden;
- dentro de esos 72, 67 son el cubo accionable por adquisición de geometría,
  cuatro son C4b con intento fallido registrado y uno procede de un feed
  truncado; esa refinación no existe en el estado del producto;
- el algoritmo asigna una relación completa por patrón: no compone tramos
  compartidos de varias relaciones ni valida solo la parte ya conocida;
- los tres `partial` actuales pasan el test geométrico automático y son
  `partial` exclusivamente por `PatternCaveat`;
- `PositionMatch` preserva `raw_lat/raw_lon`; solo crea `Projection`,
  `progress_m` y residuo cuando el estado es `validated`.

### Procedencia e integridad de las fixtures

Los siete JSON son extractos reales con estructura relation/ways/nodes, tags
`route=train`, `ref=C-4`/`C-5` y `network=Cercanías Madrid`. Todos los hashes
recalculados coinciden byte a byte con sus `MANIFEST.md`; las siete relaciones
encadenan con cero `ChainGap`. Las dos C5 truncadas se conservan como evidencia
real aunque MP-018 no las registre en `madrid_source_specs()`.

| Fixture | Relación | SHA-256 recalculado | `gaps` | longitud dirigida |
|---|---:|---|---:|---:|
| C5 | `11331` | `ec9d7decaf8d452b267df965d154c66abc7eb33d2e7cc4991db8f4dcbcab2948` | 0 | 45,284 km |
| C5 | `3418148` | `60416292689abedfe3ff20fee855c0e0bfad5e05b79cd54c8d22db1ee579cc8b` | 0 | 41,296 km |
| C5 | `3418149` | `4af4497190bbac1b08f924b8bb751294fd63698d2dcec5798a0d67bfb76bee93` | 0 | 41,286 km |
| C5 | `3418150` | `79f9966b2b7f3fdcebf1f41083d13ff58de39a496eca80caeb274c9b9f4d375a` | 0 | 45,186 km |
| C4 | `11332` | `0351d94fdb5fe70c7b61cf45e5550f6f115785ddcdadcd32f80b256b672a63d4` | 0 | 48,400 km |
| C4 | `9174510` | `e057b86b2b28a2d99d2e85f91657c6f34cb6f07295758b42e8ed643a326f1439` | 0 | 48,415 km |
| C4 | `9174511` | `986a41bfdd843fe674700abc53fd23d0c9742367d28b4f1fe162798315610e60` | 0 | 59,306 km |

La **existencia** de `9174512` está corroborada offline por
`tests/fixtures/osm_c4_real/MANIFEST.md` y `docs/STATUS.md:850-852`: el
descubrimiento de las cuatro relaciones C4 terminó y la descarga geométrica de
esa cuarta relación devolvió dos `502`. Las cifras vivas citadas en la primera
ronda —versión 42, timestamp `2026-09-11T19:22:39Z`, 59,440 km, 1.223 nodos,
111 ways, hash `03d87e1c…` y máximos 33,2–36,6 m— quedan **NO VERIFICADAS**:
proceden de una sola llamada del ejecutor, no están congeladas en el repo y no
se descargó nada durante la revisión independiente.

La conclusión C4b no depende de esas cifras. Sobre `9174511`, ya congelada y
con checksum, las 15 paradas de los cuatro patrones opuestos caen a un máximo
de **48,3 m** y sus arcos son monótonos decrecientes; tres secuencias son el
inverso exacto de patrones ya `validated` y la cuarta es una subsecuencia. El
bloqueo del código es exigir exclusivamente arcos crecientes. Reutilizar
`9174511` invertida cuesta cero descargas, pero no es una corrección física
neutra: el manifiesto documenta que las relaciones de sentidos opuestos usan
la otra vía de la plataforma doble y no necesariamente comparten `way_id`.

### Cobertura ponderada

El feed contiene **36.097 circulaciones** de la red 10. El catálogo solo
recibe 35.976 con al menos un `stop_time`; omite 121 huérfanas (114 de
`10T0097C8b` y 7 de `10T0035C5`). La primera ronda usó 35.976 sin hacer
explícita esa exclusión. Aquí se conserva ese subdenominador para medir estados
del catálogo y se añade el denominador completo para no borrar el defecto de
fuente. `Llamadas` pondera por `trip_count * stop_count`; los huérfanos no
tienen llamadas que sumar. Las estaciones únicas se solapan entre estados.

| Medida | `validated` | `partial` | `pending` | Fuera de catálogo | Denominador |
|---|---:|---:|---:|---:|---:|
| patrones catalogados | 28 (27,184 %) | 3 (2,913 %) | 72 (69,903 %) | — | 103 |
| circulaciones de red | 13.878 (38,446 %) | 31 (0,086 %) | 22.067 (61,133 %) | 121 (0,335 %) | 36.097 |
| circulaciones con `stop_times` | 13.878 (38,576 %) | 31 (0,086 %) | 22.067 (61,338 %) | excluidas explícitamente | 35.976 |
| llamadas programadas a estación | 242.129 (45,014 %) | 294 (0,055 %) | 295.476 (54,932 %) | 0: dato ausente | 537.899 |
| estaciones únicas tocadas | 39 (41,053 %) | 19 (20,000 %) | 72 (75,789 %) | — | 95; conjuntos solapados |
| suma de cuerdas entre paradas, sin ponderar | 746,849 km (21,261 %) | 87,980 km (2,505 %) | 2.677,877 km (76,234 %) | no calculable | 3.512,706 km catalogados |
| cuerdas entre paradas ponderadas por circulación | 537.052,699 km (36,201 %) | 930,800 km (0,063 %) | 945.533,615 km (63,736 %) | no calculable | 1.483.517,115 km catalogados |

La cuerda geodésica es una cota inferior reproducible, **no longitud de vía**.
El porcentaje de longitud ferroviaria OSM única queda `NO VERIFICADO`: AUD-02
no aporta un grafo físico completo y sumar los siete corredores (329,173 km)
duplica sentidos y tramos comunes. Como contraste adicional, 90/103 patrones
tienen un tramo medible sobre su `shape_id` a <=150 m; dentro de ese subconjunto
la geometría `validated` cubre 819,614/3.175,569 km-patrón (25,810 %), pero los
13 patrones cuyo shape no cubre/ordena todas sus paradas impiden elevarlo a
denominador global fiable.

Resolver el sentido C4b y retirar las tres caveats no sustentadas elevaría a
35/103 patrones, 15.649/35.976 circulaciones catalogadas (43,498 %) o
15.649/36.097 circulaciones de red (43,353 %), y 267.857/537.899 llamadas
(49,797 %). No cambia 39/95 estaciones únicas porque todas esas estaciones ya
aparecen en otros patrones validados; tampoco recupera las 121 circulaciones
con `stop_times` ausentes.

### No son 75 trabajos: lotes y tramos reutilizables

| Lote propuesto | Patrones | Circulaciones | Prioridad | Solución común |
|---|---:|---:|---|---|
| C1 | 4 | 4.262 | P1 | congelar ambos sentidos completos y validar los dos orígenes |
| C10 | 13 | 4.159 | P1 | dos sentidos del eje Chamartín–Príncipe Pío–Villalba/El Escorial |
| C2 | 14 | 3.744 | P1 | ambos sentidos Guadalajara/Alcalá–Chamartín y variantes cortas |
| C3 | 4 | 3.216 | P1 | ambos sentidos Chamartín–Aranjuez |
| C7 | 14 | 2.160 | P1 | componer los troncos este, centro y Príncipe Pío |
| C4b opuesta | 4 | 1.740 | P1 | congelar `9174512`; `9174511` invertida es alternativa offline provisional |
| C8a | 9 | 1.346 | P1 | eje Chamartín–El Escorial y subtramos occidentales |
| C8b utilizable | 3 | 1.132 | P1 | ambos sentidos Chamartín–Cercedilla |
| C9 | 6 | 254 | P2 | un corredor Cercedilla–Cotos sirve a seis patrones |
| feed C8b truncado | 1 patrón + 114 huérfanas | 168 | P2 | evento de calidad y corrección upstream; no consagrarlo como `non_traversable` |
| caveats C4b/C5 | 3 | 31 | P2 | sustituir la caveat por evidencia de bifurcación real, si existe |

Las fixtures ya contienen piezas reutilizables. Ignorando solo el allowlist de
`route_id`, `9174511` cubre `17000→18002` en 16 patrones/4.917 viajes y
`11332` cubre el inverso en 14 patrones/4.911 viajes de C1/C2/C7/C10. La C3
comparte con C4 los cinco stops `Chamartín–Nuevos Ministerios–Sol–Atocha–
Villaverde Bajo` (1.582 viajes) y su inverso (1.569). Para el C4b opuesto,
`11332` ya cubre 12/15 estaciones del patrón principal (1.632 viajes) antes de
la bifurcación a Colmenar. Las C5 parciales encajan 7/7 en sus corredores.
Esto favorece un catálogo de segmentos/nodos compartidos, o al menos descarga
por corredor físico, frente a repetir una relación completa por cada patrón.

### Matriz de los 75 patrones

Leyenda de causas/evidencias/soluciones:

- **C1 / E1 / S1-línea:** no hay fuente configurada para ese `route_id`; las
  cinco fixtures usadas no cubren el patrón completo. Descargar y congelar el
  lote direccional de la línea. No se afirma ausencia en OSM.
- **C2 / E2 / S2:** el intento de descargar `9174512` falló, pero `9174511`
  congelada contiene la misma secuencia en sentido inverso a <=48,3 m. Aceptar
  arcos decrecientes es coste cero, aunque puede situar el tren en la vía
  contigua equivocada; la solución física correcta sigue siendo congelar el
  sentido propio.
- **C3 / E3-distancia / S3:** el corredor configurado es continuo, monótono y
  todas las paradas están a la distancia máxima indicada; solo la caveat
  manual impide `validated`. No confundir parada omitida con bifurcación.
- **C4 / E4 / S4:** truncamiento del feed: los 54 trips conservan solo
  `12006` con `stop_sequence` 032/025, el extremo del nombre de ruta está en
  blanco y la ruta espejo tiene 114 trips sin ningún `stop_time`. Emitir
  calidad de dato y corregir el origen; ninguna descarga OSM lo resuelve.

| Línea | `route_id` | `pattern_id` | sentido | Estado | Causa | Evidencia | Circulaciones | Solución | Prioridad |
|---|---|---|---|---|---|---|---:|---|---|
| C1 | `10T0001C1` | `gtfs-pattern:ee12e9eb1a1224f4ac7f` | `17000>98305` | pending | C1 | E1 | 2101 | S1-C1 | **P1** |
| C1 | `10T0001C1` | `gtfs-pattern:4e5c013c758882160600` | `18000>98305` | pending | C1 | E1 | 30 | S1-C1 | **P1** |
| C1 | `10T0002C1` | `gtfs-pattern:c365d6201ef0bc55dfb4` | `98305>17000` | pending | C1 | E1 | 2101 | S1-C1 | **P1** |
| C1 | `10T0002C1` | `gtfs-pattern:14ecf4fae803a8d6a0a1` | `98305>18000` | pending | C1 | E1 | 30 | S1-C1 | **P1** |
| C10 | `10T0003C10` | `gtfs-pattern:35ae4619aea5c7f9a3de` | `10200>18002` | pending | C1 | E1 | 13 | S1-C10 | **P1** |
| C10 | `10T0003C10` | `gtfs-pattern:ead8d642689d07ca663d` | `10200>17000` | pending | C1 | E1 | 1035 | S1-C10 | **P1** |
| C10 | `10T0003C10` | `gtfs-pattern:81d383ed03be94a83290` | `10203>17000` | pending | C1 | E1 | 36 | S1-C10 | **P1** |
| C10 | `10T0003C10` | `gtfs-pattern:8992a542ef8e1dfb1584` | `10203>17000` | pending | C1 | E1 | 16 | S1-C10 | **P1** |
| C10 | `10T0004C10` | `gtfs-pattern:85d35496ac5c04d64df8` | `17000>10200` | pending | C1 | E1 | 50 | S1-C10 | **P1** |
| C10 | `10T0004C10` | `gtfs-pattern:4409c87fe76b4dbf61ef` | `17000>10200` | pending | C1 | E1 | 1014 | S1-C10 | **P1** |
| C10 | `10T0004C10` | `gtfs-pattern:a35fd85c3df19e2f8800` | `18000>10200` | pending | C1 | E1 | 11 | S1-C10 | **P1** |
| C10 | `10T0064C10` | `gtfs-pattern:c1d6f7376aa652314f0c` | `10000>17000` | pending | C1 | E1 | 30 | S1-C10 | **P1** |
| C10 | `10T0064C10` | `gtfs-pattern:58db9fec216bdb96b264` | `18000>10203` | pending | C1 | E1 | 4 | S1-C10 | **P1** |
| C10 | `10T0064C10` | `gtfs-pattern:02c721a4ca792906fc6d` | `18002>10203` | pending | C1 | E1 | 4 | S1-C10 | **P1** |
| C10 | `10T0075C10` | `gtfs-pattern:6f6542a6b514975d679a` | `10100>17000` | pending | C1 | E1 | 959 | S1-C10 | **P1** |
| C10 | `10T0076C10` | `gtfs-pattern:4e476bce27a86a616efb` | `17000>18000` | pending | C1 | E1 | 29 | S1-C10 | **P1** |
| C10 | `10T0076C10` | `gtfs-pattern:46b153560fc31eec0dbd` | `17000>10100` | pending | C1 | E1 | 958 | S1-C10 | **P1** |
| C2 | `10T0005C2` | `gtfs-pattern:77f078b7dcb1e2219c68` | `18000>17000` | pending | C1 | E1 | 14 | S1-C2 | **P1** |
| C2 | `10T0005C2` | `gtfs-pattern:82c46f245cedf52ad207` | `70103>17000` | pending | C1 | E1 | 28 | S1-C2 | **P1** |
| C2 | `10T0005C2` | `gtfs-pattern:0e0746ec63d6a0a06c2a` | `70103>17000` | pending | C1 | E1 | 455 | S1-C2 | **P1** |
| C2 | `10T0005C2` | `gtfs-pattern:afe0e8e7a27b5102d28f` | `70108>17000` | pending | C1 | E1 | 80 | S1-C2 | **P1** |
| C2 | `10T0005C2` | `gtfs-pattern:3ab68161404b6c8bbed6` | `70200>17000` | pending | C1 | E1 | 99 | S1-C2 | **P1** |
| C2 | `10T0005C2` | `gtfs-pattern:435db564be42a7b46972` | `70200>18002` | pending | C1 | E1 | 14 | S1-C2 | **P1** |
| C2 | `10T0005C2` | `gtfs-pattern:0e3114a0f692e9f96101` | `70200>17000` | pending | C1 | E1 | 1203 | S1-C2 | **P1** |
| C2 | `10T0006C2` | `gtfs-pattern:3c60b65138aeff87e8fe` | `17000>70108` | pending | C1 | E1 | 80 | S1-C2 | **P1** |
| C2 | `10T0006C2` | `gtfs-pattern:c30ef24469a619bb34f8` | `17000>70103` | pending | C1 | E1 | 419 | S1-C2 | **P1** |
| C2 | `10T0006C2` | `gtfs-pattern:7c47b452823ec2d11bdc` | `17000>70105` | pending | C1 | E1 | 1 | S1-C2 | **P1** |
| C2 | `10T0006C2` | `gtfs-pattern:da0c04c8de41dc1a95a1` | `17000>70200` | pending | C1 | E1 | 1261 | S1-C2 | **P1** |
| C2 | `10T0006C2` | `gtfs-pattern:2acd3dc86c0098a93c48` | `17000>70200` | pending | C1 | E1 | 70 | S1-C2 | **P1** |
| C2 | `10T0006C2` | `gtfs-pattern:52f68c811f69760c3dc0` | `18002>70200` | pending | C1 | E1 | 19 | S1-C2 | **P1** |
| C2 | `10T0037C2` | `gtfs-pattern:46e333a087272762de5a` | `70103>18002` | pending | C1 | E1 | 1 | S1-C2 | **P1** |
| C3 | `10T0007C3` | `gtfs-pattern:1e7106bd6a15584a8d57` | `17000>60200` | pending | C1 | E1 | 1582 | S1-C3 | **P1** |
| C3 | `10T0007C3` | `gtfs-pattern:a9734feb1f801e518f27` | `17000>60200` | pending | C1 | E1 | 26 | S1-C3 | **P1** |
| C3 | `10T0008C3` | `gtfs-pattern:90d9031bf80dba7580c7` | `60200>17000` | pending | C1 | E1 | 1569 | S1-C3 | **P1** |
| C3 | `10T0008C3` | `gtfs-pattern:c3cfe69314e5e1c10a62` | `60200>17000` | pending | C1 | E1 | 39 | S1-C3 | **P1** |
| C4b | `10T0015C4b` | `gtfs-pattern:cec92b20eec83ba3577a` | `17005>37012` | partial | C3 | E3-48,3 | 11 | S3 | **P2** |
| C4b | `10T0016C4b` | `gtfs-pattern:0e30aa9375f3971ffd8d` | `17000>17005` | pending | C2 | E2 | 30 | S2 | **P1** |
| C4b | `10T0016C4b` | `gtfs-pattern:eb14c27202bd7a1fe15b` | `18000>17005` | pending | C2 | E2 | 60 | S2 | **P1** |
| C4b | `10T0016C4b` | `gtfs-pattern:3d0e2a689cefd948df88` | `37002>17005` | pending | C2 | E2 | 18 | S2 | **P1** |
| C4b | `10T0016C4b` | `gtfs-pattern:3ca1c650c302d356a36c` | `37012>17005` | pending | C2 | E2 | 1632 | S2 | **P1** |
| C5 | `10T0047C5` | `gtfs-pattern:bffbd086a5199ea38342` | `18000>35002` | partial | C3 | E3-37,3 | 10 | S3 | **P2** |
| C5 | `10T0048C5` | `gtfs-pattern:2bc1cf546f0e8b6a52f6` | `35002>18000` | partial | C3 | E3-28,4 | 10 | S3 | **P2** |
| C7 | `10T0051C7` | `gtfs-pattern:69ad56964cee4a99bf03` | `10000>17000` | pending | C1 | E1 | 26 | S1-C7 | **P1** |
| C7 | `10T0051C7` | `gtfs-pattern:e282bfe6fe5751be0625` | `10000>18002` | pending | C1 | E1 | 5 | S1-C7 | **P1** |
| C7 | `10T0051C7` | `gtfs-pattern:25e204c3d59bad0ea0ca` | `10000>70103` | pending | C1 | E1 | 938 | S1-C7 | **P1** |
| C7 | `10T0051C7` | `gtfs-pattern:67e2e97984a8fb84942d` | `10000>70200` | pending | C1 | E1 | 28 | S1-C7 | **P1** |
| C7 | `10T0052C7` | `gtfs-pattern:6dd0894ae50db2f63550` | `17000>18000` | pending | C1 | E1 | 14 | S1-C7 | **P1** |
| C7 | `10T0052C7` | `gtfs-pattern:cbe03abcaf7c5ff0efda` | `17000>10000` | pending | C1 | E1 | 4 | S1-C7 | **P1** |
| C7 | `10T0052C7` | `gtfs-pattern:58314c69fb3b1b69c552` | `70103>10000` | pending | C1 | E1 | 937 | S1-C7 | **P1** |
| C7 | `10T0052C7` | `gtfs-pattern:68bac78acf1bfd2d7e1d` | `70200>10000` | pending | C1 | E1 | 78 | S1-C7 | **P1** |
| C7 | `10T0053C7` | `gtfs-pattern:e7696ec38b161b1c90e8` | `10000>18000` | pending | C1 | E1 | 29 | S1-C7 | **P1** |
| C7 | `10T0053C7` | `gtfs-pattern:dbc1a9bad1df4153786e` | `70103>18000` | pending | C1 | E1 | 3 | S1-C7 | **P1** |
| C7 | `10T0054C7` | `gtfs-pattern:4a6dab210e7e57c1ed6b` | `18000>10000` | pending | C1 | E1 | 30 | S1-C7 | **P1** |
| C7 | `10T0054C7` | `gtfs-pattern:2b21570a7ab4c0219880` | `18000>70103` | pending | C1 | E1 | 3 | S1-C7 | **P1** |
| C7 | `10T0059C7` | `gtfs-pattern:3c87e867d746837c08ba` | `17000>70103` | pending | C1 | E1 | 57 | S1-C7 | **P1** |
| C7 | `10T0060C7` | `gtfs-pattern:65eba9bd8f6b817f1d65` | `70103>17000` | pending | C1 | E1 | 8 | S1-C7 | **P1** |
| C8a | `10T0027C8a` | `gtfs-pattern:1be9550be3c2d5ad2130` | `10206>10203` | pending | C1 | E1 | 18 | S1-C8a | **P1** |
| C8a | `10T0061C8a` | `gtfs-pattern:b77fc4fc842dce6862db` | `10200>17000` | pending | C1 | E1 | 31 | S1-C8a | **P1** |
| C8a | `10T0061C8a` | `gtfs-pattern:1dbb00baccc5e3a00d9f` | `10203>17000` | pending | C1 | E1 | 550 | S1-C8a | **P1** |
| C8a | `10T0061C8a` | `gtfs-pattern:0720c40a47c5fcff3f09` | `10203>10206` | pending | C1 | E1 | 79 | S1-C8a | **P1** |
| C8a | `10T0062C8a` | `gtfs-pattern:23a5fbc1050d0d39003b` | `10206>10203` | pending | C1 | E1 | 5 | S1-C8a | **P1** |
| C8a | `10T0062C8a` | `gtfs-pattern:2911a37447d6aa980d18` | `17000>10200` | pending | C1 | E1 | 28 | S1-C8a | **P1** |
| C8a | `10T0062C8a` | `gtfs-pattern:547d33b828170d61d7f7` | `17000>10203` | pending | C1 | E1 | 557 | S1-C8a | **P1** |
| C8a | `10T0085C8a` | `gtfs-pattern:97f9caac022175204b64` | `10206>10203` | pending | C1 | E1 | 74 | S1-C8a | **P1** |
| C8a | `10T0107C8a` | `gtfs-pattern:f46ca1a0a986b44ec7e4` | `10101>10005` | pending | C1 | E1 | 4 | S1-C8a | **P1** |
| C8b | `10T0087C8b` | `gtfs-pattern:a4fa126ae6af0667dbee` | `17000>12006` | pending | C1 | E1 | 11 | S1-C8b | **P1** |
| C8b | `10T0087C8b` | `gtfs-pattern:2348c5eaadb44da2bb4c` | `17000>12006` | pending | C1 | E1 | 555 | S1-C8b | **P1** |
| C8b | `10T0088C8b` | `gtfs-pattern:7ead496e1732c678d8f6` | `12006>17000` | pending | C1 | E1 | 566 | S1-C8b | **P1** |
| C8b | `10T0098C8b` | `gtfs-pattern:574a2681305065df5673` | `12006>12006` | pending | C4 | E4 | 54 | S4 | **P2** |
| C9 | `10T0025C9` | `gtfs-pattern:a214fa6209608bbd032d` | `12006>12020` | pending | C1 | E1 | 11 | S1-C9 | **P2** |
| C9 | `10T0025C9` | `gtfs-pattern:13f722c0ba862f541da6` | `12006>12023` | pending | C1 | E1 | 21 | S1-C9 | **P2** |
| C9 | `10T0026C9` | `gtfs-pattern:c1d2ecc346ced29e0b46` | `12020>12006` | pending | C1 | E1 | 11 | S1-C9 | **P2** |
| C9 | `10T0026C9` | `gtfs-pattern:6b1fb0c2c7976b3e51af` | `12023>12006` | pending | C1 | E1 | 21 | S1-C9 | **P2** |
| C9 | `10T0110C9` | `gtfs-pattern:3b4f4505852fb3968d7f` | `12006>12023` | pending | C1 | E1 | 95 | S1-C9 | **P2** |
| C9 | `10T0111C9` | `gtfs-pattern:56544bc08bc28bc27ffb` | `12023>12006` | pending | C1 | E1 | 95 | S1-C9 | **P2** |

### Hallazgos

No se identificó ningún P0: el fallback `raw` evita fabricar posiciones y la
API/UI ya etiqueta la falta de map-matching. Los déficits son amplios, pero no
corrompen la procedencia del punto mostrado.

#### AUD03-P1-001 — Los 72 `pending` quedan sin prueba geométrica; 67 son el cubo accionable por adquisición

- **Identificador:** `AUD03-P1-001`.
- **Componente:** `packages/geo/madrid.py::madrid_source_specs` y
  `packages/geo/catalog.py::build_corridor_catalog`.
- **Severidad:** **P1**.
- **Evidencia reproducible:** los 72 `pending` tienen `route_id` fuera de los
  nueve IDs admitidos por todos los `GeometrySourceSpec`; por diseño, ninguno
  llega a continuidad/distancia/orden. `python3 scratch/aud03_geometry.py
  summary` refina después 67 patrones/20.273 circulaciones/269.988 llamadas
  como accionables por adquisición, cuatro C4b con intento fallido y un patrón
  procedente de feed truncado. El cruce sin allowlist encuentra además tramos
  comunes de miles de circulaciones en las fixtures C4/C5 ya presentes.
- **Archivo/símbolo/dato:** cinco specs usados (`11331`, `3418150`, `11332`,
  `9174510`, `9174511`), 67 filas C1/C2/C3/C7/C8a/C8b/C9/C10 de
  `docs/evidence/mp-018-corridor-coverage.csv`.
- **Riesgo:** el mapa conserva GPS bruto en 20.273/36.097 = 56,163 % de las
  circulaciones de red por el cubo accionable, además de los otros cinco
  patrones `pending`; la frase «Madrid completo» puede confundirse con cobertura
  geométrica completa si se omite el denominador ponderado y los 121 huérfanos.
- **Causa raíz:** MP-018 cerró con un alcance mínimo de C4+C5 y un allowlist por
  `route_id`; `pending` fue una salida honesta, pero el hito lo trató como
  cobertura de catálogo suficiente.
- **Alternativas:** (A) descargar relaciones completas por línea/sentido; (B)
  modelar un grafo de segmentos OSM reutilizables y componer corredores; (C)
  mantener GPS raw y el estado actual; (D) reutilizar una relación por nombre,
  inaceptable sin validación física.
- **Recomendación:** primero A por volumen (C1, C10, C2, C3, C7, C8a, C8b,
  C9); evaluar B mediante ADR antes de cambiar el modelo. Publicar siempre
  13.878/36.097 y las 121 circulaciones omitidas por fuente, no solo 28/103.
- **Prueba de cierre:** fixture atribuida y con checksum por cada lote; cero
  huecos, <=150 m, orden correcto y test de dirección; matriz regenerada con
  numerador de circulaciones y llamadas, no solo patrones.

#### AUD03-P1-002 — Cuatro patrones C4b siguen `pending` aunque su vía ya está congelada en sentido opuesto

- **Identificador:** `AUD03-P1-002`.
- **Componente:** inventario C4b de `madrid_source_specs`.
- **Severidad:** **P1**.
- **Evidencia reproducible:** `python3 scratch/aud03_geometry.py offline-c4b`
  proyecta los cuatro patrones `10T0016C4b` sobre `9174511` congelada: 15/15
  paradas a <=48,3 m y arcos monótonos decrecientes. Tres secuencias son
  inversos exactos de patrones `10T0015C4b` ya `validated`; la cuarta es una
  subsecuencia. Representan 1.740 viajes, incluido el principal de 1.632. La
  existencia de `9174512` consta en el manifiesto y STATUS; sus cifras vivas
  específicas quedan **NO VERIFICADAS** hasta congelarla.
- **Archivo/símbolo/dato:** `tests/fixtures/osm_c4_real/MANIFEST.md` documenta
  dos `502`; `packages/geo/madrid.py` omite `9174512`.
- **Riesgo:** 1.740/36.097 = 4,820 % de las circulaciones de red queda en raw y
  el sentido contrario de la misma línea tiene una asimetría artificial de
  calidad.
- **Causa raíz:** además de los `502` documentados, `build_corridor_catalog`
  solo acepta arcos crecientes y no sabe invertir un corredor ya verificado.
- **Alternativas:** (A) congelar `9174512`, sentido físico propio; (B) coste
  cero en descargas: aceptar arcos decrecientes o invertir `9174511`; (C)
  reintentar con backoff/espejo; (D) seguir raw. B demuestra topología y sirve
  como fallback provisional, pero puede dibujar el tren en la vía contigua
  equivocada porque sentidos opuestos no necesariamente comparten `way_id`.
- **Recomendación:** A como cierre físicamente correcto, conservando ODbL,
  atribución, fecha y SHA-256; B solo si el contrato explicita esa incertidumbre
  lateral; C para adquisiciones futuras.
- **Prueba de cierre:** los cuatro pattern IDs pasan a `validated`; la fuente
  propia congelada reproduce continuidad, <=150 m y orden, o el fallback
  invertido declara expresamente que no garantiza la vía direccional exacta;
  la cobertura ponderada sube en exactamente 1.740 circulaciones.

#### AUD03-P2-001 — Tres caveats confunden «no para» con «no pasa por esa vía»

- **Identificador:** `AUD03-P2-001`.
- **Componente:** `packages/geo/madrid.py::_known_caveats`.
- **Severidad:** **P2** por volumen (31 viajes), aunque el defecto conceptual
  afecta a futuras variantes exprés.
- **Evidencia reproducible:** al evaluar sin la caveat, C4b `17005>37012`
  encaja 14/14 sobre `9174511`, máximo 48,3 m; C5 `18000>35002` encaja 7/7
  sobre `3418150`, 37,3 m; el inverso encaja 7/7 sobre `11331`, 28,4 m. Los
  tres corredores son continuos y monótonos. La caveat es la única diferencia
  entre `partial` y `validated`.
- **Archivo/símbolo/dato:** dos condicionales por `route_id` y longitud de
  secuencia en `_known_caveats`; 3 filas `partial`.
- **Riesgo:** cualquier servicio sin parada comercial en una estación
  intermedia puede perder map-matching aunque use exactamente la misma vía.
- **Causa raíz:** se usó contigüidad de la lista de paradas como sustituto de
  topología física. Una parada omitida no demuestra bifurcación.
- **Alternativas:** (A) validar corredor continuo, distancia, orden y shape,
  permitiendo paradas saltadas; (B) exigir evidencia de bifurcación concreta;
  (C) conservar caveats manuales.
- **Recomendación:** A+B. La caveat solo debe bloquear si dos trazados físicos
  distintos satisfacen las mismas anclas o el shape contradice el corredor.
- **Prueba de cierre:** pruebas que distingan skip-stop sobre la misma vía de
  una bifurcación sintética/real; los tres patrones pasan a `validated` sin
  relajar 150 m, continuidad ni orden.

#### AUD03-P2-002 — El feed C8b llega truncado y el catálogo oculta parte del defecto

- **Identificador:** `AUD03-P2-002`.
- **Componente:** calidad del GTFS de origen, identidad de cobertura y
  denominadores.
- **Severidad:** **P2**.
- **Evidencia reproducible:** los 54 trips de
  `gtfs-pattern:574a2681305065df5673` conservan solo Cercedilla (`12006`) con
  `stop_sequence` **032** (43) o **025** (11), no 1; `route_long_name` termina
  con el destino en blanco y `shape_id=10_C8b_INV` sí existe. La ruta espejo
  `10T0097C8b` tiene 114 trips y cero `stop_times`, con el origen en blanco.
  Además hay 7 huérfanos de `10T0035C5`: 36.097 viajes de red frente a 35.976
  catalogados.
- **Archivo/símbolo/dato:** `trips.txt`, `stop_times.txt`, `routes.txt`,
  `route_id=10T0098C8b|10T0097C8b|10T0035C5`; `PatternIdentity` admite una
  parada y `packages.movement.schedule` exige al menos dos.
- **Riesgo:** `non_traversable` presentaría como propiedad legítima del
  servicio lo que es un horario incompleto del proveedor; además, 121
  circulaciones desaparecerían silenciosamente de cualquier denominador.
- **Causa raíz:** truncamiento del feed de origen. El consumidor convierte el
  único residuo no vacío en patrón y omite por completo los trips sin filas.
- **Alternativas:** (A) emitir evento/estado de calidad `source_truncated` por
  trip y excluirlo solo de métricas geométricas que exigen recorrido; (B)
  reclamar/regenerar el feed upstream; (C) marcarlo `non_traversable`, que
  consagra el defecto; (D) fabricar paradas, inaceptable.
- **Recomendación:** A+B. Publicar 36.097 circulaciones de fuente, 35.976 con
  secuencia no vacía, 121 huérfanas y 102 patrones con >=2 paradas junto a
  103 patrones de fuente.
- **Prueba de cierre:** validación que detecte secuencia residual iniciada en
  025/032, rutas con extremo en blanco y trips sin `stop_times`; el contrato
  los expone como defecto de fuente y ninguna descarga OSM se propone como
  remedio.

#### AUD03-DESCARTADO-001 — «Los 75 fallan porque OSM no tiene geometría»

- **Identificador:** `AUD03-DESCARTADO-001`.
- **Componente:** interpretación de `partial`/`pending`.
- **Severidad:** **DESCARTADO**.
- **Evidencia reproducible:** tres `partial` pasan las cinco comprobaciones
  geométricas; cuatro `pending` encajan offline sobre `9174511` en sentido
  inverso; decenas de patrones reutilizan tramos de C4/C5 ya congelados. Para
  los otros 67 no hay fuente completa local con la que afirmar presencia o
  ausencia.
- **Archivo/símbolo/dato:** `CorridorCoverage.reason`, `_known_caveats`, salida
  de `scratch/aud03_geometry.py`.
- **Riesgo:** buscar 75 trazados independientes desperdiciaría trabajo y podría
  duplicar vía compartida.
- **Causa raíz:** el texto `sin geometría OSM descargada` es correcto, pero se
  puede abreviar indebidamente como `sin geometría OSM`.
- **Alternativas:** ausencia física, fuente no adquirida, criterio conservador
  o feed truncado; la auditoría separa las cuatro.
- **Recomendación:** mantener esa separación en API, UI y documentación.
- **Prueba de cierre:** ninguna fila usa «geometría ausente en OSM» sin una
  consulta/fuente que lo demuestre.

#### AUD03-DESCARTADO-002 — Las fixtures C4/C5 versionadas están inventadas o corruptas

- **Identificador:** `AUD03-DESCARTADO-002`.
- **Componente:** procedencia OSM y carga de relaciones.
- **Severidad:** **DESCARTADO**.
- **Evidencia reproducible:** 7/7 SHA-256 coinciden con ambos manifiestos;
  7/7 payloads contienen el ID y tags documentados; 7/7 corredores tienen
  cero gaps; los tests focales ejecutados dan 19/19 OK.
- **Archivo/símbolo/dato:** `tests/fixtures/osm_c4_real/`,
  `tests/fixtures/osm_c5_real/`, sus `MANIFEST.md`.
- **Riesgo:** una fixture corrupta invalidaría toda conclusión de continuidad y
  distancia.
- **Causa raíz:** no aplica; la hipótesis no se reprodujo.
- **Alternativas:** confiar solo en el manifiesto o recalcular y contrastar la
  fuente; se hizo lo segundo.
- **Recomendación:** conservar checksum como gate obligatorio y verificar
  también helpers que lean la fixture fuera de `_load_source`.
- **Prueba de cierre:** ya satisfecha para estos bytes; repetir ante cualquier
  recaptura OSM.

#### AUD03-NO-VERIFICADO-001 — Longitud ferroviaria OSM única de todo Madrid

- **Identificador:** `AUD03-NO-VERIFICADO-001`.
- **Componente:** denominador físico de cobertura.
- **Severidad:** **NO VERIFICADO**.
- **Evidencia reproducible:** los siete corredores suman 329,173 km dirigidos,
  pero contienen ambos sentidos y tramos solapados; AUD-02 no construye un
  grafo de rail ways únicos para las 12 líneas. Los proxies por shape/cuerda se
  declaran aparte y no se renombran como vía.
- **Archivo/símbolo/dato:** fixtures C4/C5 y shapes GTFS.
- **Riesgo:** publicar un porcentaje de kilómetros aparentemente preciso pero
  duplicado por dirección o incompleto por línea.
- **Causa raíz:** falta de inventario OSM completo y de una definición de
  deduplicación física (way dirigido, way no dirigido o tramo operacional).
- **Alternativas:** (A) unión de IDs OSM `way` con longitud geodésica; (B) grafo
  de segmentos entre nodos; (C) proxy GTFS claramente etiquetado.
- **Recomendación:** A o B tras adquirir todas las fuentes; hasta entonces
  publicar `NO VERIFICADO` y los proxies honestos.
- **Prueba de cierre:** conjunto completo de ways, regla de deduplicación,
  numerador/denominador reproducibles y verificación de que los sentidos no
  duplican longitud física.

#### AUD03-NO-VERIFICADO-002 — Causa física individual de los otros 67 patrones

- **Identificador:** `AUD03-NO-VERIFICADO-002`.
- **Componente:** correspondencia completa GTFS/OSM fuera de C4/C5.
- **Severidad:** **NO VERIFICADO** en OSM; la causa de producto «fuente no
  configurada» sí está verificada.
- **Evidencia reproducible:** ninguna de las cinco fuentes usadas cubre el
  patrón completo; eso no permite distinguir geometría ausente, relación OSM
  disponible, bifurcación o error de secuencia fuera del tramo común.
- **Archivo/símbolo/dato:** 67 filas C1 de la matriz.
- **Riesgo:** inventar una causa física por patrón a partir de ausencia local,
  violando la regla de no asumir contratos externos.
- **Causa raíz:** el conjunto de evidencia congelada solo contiene C4/C5.
- **Alternativas:** adquirir relaciones reales por lotes, o dejar causa física
  como no verificada; no vale extrapolar por nombre comercial.
- **Recomendación:** adquirir en el orden ponderado de la tabla de lotes y
  reemplazar C1/E1 por una causa física solo después de esa prueba.
- **Prueba de cierre:** cada lote tiene fuente/hash y cada fila demuestra
  continuidad, distancia, orden, dirección y, cuando aplique, bifurcación.

### Comandos reproducibles ejecutados

```sh
shasum -a 256 tests/fixtures/osm_c4_real/*.json \
  tests/fixtures/osm_c5_real/*.json

.venv/bin/python scratch/aud03_geometry.py summary
.venv/bin/python scratch/aud03_geometry.py offline-c4b

.venv/bin/python -m unittest \
  packages.geo.tests.test_catalog \
  packages.geo.tests.test_real_feed -v
```

Resultado focal: **19/19 OK**. `compileall` del script y `git diff --check`
terminaron sin errores. No se modificó código de producto ni se declara la
suite completa.

---

## Revisión independiente de AUD-03

**Revisa:** Claude Opus · High · contexto nuevo (`task_5f1319cdd3c0`, `ctx_4db56fd6dd34`)

**Fecha:** 2026-11-23 · **Base:** rama `audit/hito-03-adversarial`, commit `1c28163`

**Veredicto: `CHANGES_REQUESTED`.** Los cuatro recuentos del veredicto reproducen
exactos, la matriz de 75 filas es consistente byte a byte con el CSV canónico y los
dos hallazgos P1 y el P2-001 quedan **confirmados con evidencia propia más fuerte que
la aportada**. Ninguna conclusión central se cae. Lo que exige corrección es el
diagnóstico de **AUD03-P2-002**: el patrón de una parada no es una secuencia
legítimamente degenerada que haya que clasificar, es un **truncamiento del feed de
origen**, y la solución recomendada (estado `non_traversable`) consagraría un defecto
de dato como estado de producto. Se añaden dos precisiones advisory.

### Método de la revisión (sin descargas externas)

No se descargó nada de Overpass ni de la API de OSM: la verificación de la relación
`9174512` se hizo por vía indirecta offline (abajo). Los recuentos **no** se tomaron de
`scratch/aud03_geometry.py` —el instrumento del ejecutor— sino recomputados contra el
catálogo de producto (`build_madrid_corridor_catalog`) y contra el ZIP GTFS crudo. El
script del ejecutor se ejecutó además una vez para comprobar que reproduce lo que el
informe cita.

### 1. Recuento de 67 / 103 — **CONFIRMADO**

Recomputado desde el catálogo de producto, sin pasar por la taxonomía de causas del
ejecutor:

| Medida | Recomputado | Informe |
|---|---:|---:|
| patrones totales | 103 | 103 |
| `validated` / `partial` / `pending` | 28 / 3 / 72 | 28 / 3 / 72 |
| bucket «sin fuente» (pending, ≥2 paradas, `route_id != 10T0016C4b`) | 67 patrones · 20.273 viajes · 269.988 llamadas | idénticos |
| C4b `10T0016C4b` | 4 · 1.740 · 25.434 | idénticos |
| caveats | 3 · 31 · 294 | idénticos |
| degenerado | 1 · 54 · 54 | idénticos |
| **suma** | **75 · 22.098 · 295.770** | idénticos |

La matriz de 75 filas del informe se cruzó fila a fila contra
`docs/evidence/mp-018-corridor-coverage.csv` en `line_id`, `route_id`,
`direction_key`, `status` y `trip_count`: **0 discrepancias**, y el conjunto de 75
`pattern_id` es exactamente el de los no-`validated` del CSV. Suma de viajes de la
matriz: 22.098. Verificadas también las derivadas: 20.273/35.976 = 56,351 %;
1.740/35.976 = 4,837 %; la proyección «tras congelar + retirar caveats» 35/103,
15.649/35.976 = 43,498 %, 267.857/537.899 = 49,797 %; y 819.614/3.175.569 = 25,810 %
sobre los 90 patrones con shape fiable. Los 19/19 tests focales dan **OK** aquí.

**Precisión que el informe debe incorporar (advisory).** El mecanismo de código no
afecta a 67 patrones sino a **72**: los 72 `pending` comparten un único `reason`
(`sin geometría OSM descargada para este patrón/sentido`) y **ninguno de los 72** tiene
un `route_id` presente en algún `GeometrySourceSpec` —los nueve `route_id` con fuente
son `10T0011C4`, `10T0012C4`, `10T0013C4a`, `10T0014C4a`, `10T0015C4b`, `10T0017C5`,
`10T0018C5`, `10T0047C5`, `10T0048C5`—. Es decir: a 72 de 103 patrones **no se les
aplicó nunca una prueba geométrica**. La partición en 67 + 4 + 1 es una refinación
*probatoria* legítima, no una distinción que el código haga. Si la pregunta es «cuántos
patrones nunca se contrastaron contra geometría», la respuesta es 72.

### 2. Los 4 patrones C4b y la relación `9174512` — **CONFIRMADO en sustancia; una cifra no re-verificada**

El test decisivo se puede hacer **sin descargar nada**, y el informe no lo hizo:
proyectar las paradas de los 4 patrones `10T0016C4b` sobre la relación **ya congelada**
`9174511` (C4b Colmenar→Parla, sentido opuesto, SHA-256 verificado, 0 huecos).

| Patrón | sentido | paradas | viajes | sobre `9174511` |
|---|---|---:|---:|---|
| `3ca1c650c302d356a36c` | `37012>17005` | 15 | 1.632 | máx **48,3 m**, todas ≤150 m, arcos **monótonos decrecientes** |
| `eb14c27202bd7a1fe15b` | `18000>17005` | 9 | 60 | máx 48,3 m, monótono decreciente |
| `3d0e2a689cefd948df88` | `37002>17005` | 13 | 18 | máx 48,3 m, monótono decreciente |
| `0e30aa9375f3971ffd8d` | `17000>17005` | 6 | 30 | máx 48,3 m, monótono decreciente |

Sobre las otras dos relaciones C4 congeladas (`11332`, `9174510`) las mismas paradas
caen a 1.383 m (El Goloso), 5.337 m (Tres Cantos) y 12.220 m (Colmenar Viejo): el ramal
de Colmenar no está en ellas, como es esperable. Es decir: **la vía física de las 15
paradas de esos 4 patrones ya está en el repositorio**, congelada y verificada; 3 de los
4 patrones son el **inverso exacto** de patrones `10T0015C4b` que el código ya valida, y
el cuarto es una subsecuencia. El bloqueo real en código es que
`build_corridor_catalog` exige arcos **crecientes** (`arcs != sorted(arcs)` → descarte).
Queda descartado sin margen que la causa sea geometría OSM ausente o un problema de
direccionalidad del dato: **AUD03-P1-002 confirmado**. Confirmado también que ningún
`PatternCaveat` aplica a `10T0016C4b`, así que una fuente con ese `route_id` que pase
los criterios los deja en `validated`, no en `partial`.

**Existencia de `9174512`:** corroborada por dos artefactos del repositorio escritos en
MP-018, anteriores e independientes de esta auditoría —
`tests/fixtures/osm_c4_real/MANIFEST.md` («las cuatro relaciones se publican con
`ref=C-4`»; nombra `9174512`, C4b Parla→Colmenar) y `docs/STATUS.md:850-852`. El
descubrimiento vía `find_route_relations` sí completó; lo que falló con `502` fue la
descarga de geometría.

**No re-verificado (y el informe debe marcarlo así):** las cifras vivas de P1-002 —
versión 42, timestamp, 59,440 km, 1.223 nodos, 111 ways, `sha256:03d87e1c…` y los
máximos de 33,2–36,6 m— descansan en **una sola llamada en vivo del ejecutor**, no
reproducible en esta revisión (descargas no autorizadas) y no congelada en el repo. La
conclusión no depende de ellas, pero su procedencia es de un solo punto y así debe
leerse hasta que la relación se congele con checksum.

**Alternativa omitida en P1-002 (advisory).** Las tres alternativas listadas (congelar
ahora / reintentar con backoff / seguir en raw) omiten la de **coste cero en descargas**:
aceptar arcos decrecientes, o construir el corredor inverso, sobre la `9174511` ya
congelada —que, como se ve arriba, encaja las 15 paradas a 48,3 m—. Hay un argumento
físico real para **no** hacerlo, y es del propio repositorio: `MANIFEST.md` documenta que
las relaciones del sentido opuesto «usan la otra vía de la plataforma doble y no
necesariamente comparten IDs de `way`». Reutilizar `9174511` invertida situaría los
trenes en la vía contigua equivocada. La recomendación (A) es por tanto la correcta,
pero la razón de descartar la opción barata merece quedar escrita, no omitida.

### 3. Los tres caveats manuales — **CONFIRMADO, con evidencia adicional**

Texto exacto de `packages/geo/madrid.py::_known_caveats` y su aplicación verificados:
dos condicionales que disparan por `route_id` + `len(stop_ids)`, y un emparejamiento
exacto por `(route_id, stop_ids)` en `build_corridor_catalog`. Los tres patrones tienen
candidato geométrico válido —`max_stop_distance_m` 48,3 / 37,3 / 28,4 m, continuidad y
orden correctos— y el caveat es la **única** diferencia respecto a `validated`.

Más allá de lo que aporta el informe, se contrastó la geometría declarada por el propio
operador (`shapes.txt`) contra el corredor OSM, recortada al tramo que usa cada patrón:

- **C4b 14 paradas (`cec92b20eec83ba3577a`)**: usa el **mismo `shape_id` `10_C4b`** que
  el patrón de 15 paradas que el código **sí valida** (1.651 viajes); los 584 puntos del
  shape van a ≤**97,3 m** del corredor `9174511`, **0 puntos** por encima de 150 m. Y
  sobre el tramo del patrón hay exactamente **una** estación del feed no servida:
  Nuevos Ministerios (`18002`), a 44,5 m del eje. El operador declara la misma
  geometría para la variante degradada que para la validada, y el caveat admite en su
  propio texto «vía real continua». Es un skip-stop sobre la misma vía: **falso negativo
  demostrado**.
- **C5 7 paradas (`bffbd086a5199ea38342`, `2bc1cf546f0e8b6a52f6`)**: el shape de línea
  (`10_C5` / `10_C5_INV`) se separa hasta 345/350 m del corredor congelado en el tramo
  Atocha–Villaverde Alto, **pero exactamente igual en los patrones que el código sí
  valida** (los de 12, 22 y 23 paradas de `10T0017C5`/`10T0018C5` dan los mismos 345,4 /
  350,4 m y el mismo número de puntos >150 m). El shape, por tanto, **no discrimina**: no
  aporta evidencia de bifurcación para la variante corta que no aporte igual contra
  patrones validados. Las 4 paradas omitidas (Méndez Álvaro P.V., Doce de Octubre,
  Orcasitas, Puente Alcocer) proyectan a **1,0–23,0 m** sobre el mismo corredor y dentro
  del tramo del propio patrón. No hay en el repositorio ninguna segunda geometría que
  ofrezca un trazado alternativo para ellas.

Conclusión: **AUD03-P2-001 confirmado en los tres**. Matiz de redacción: el caveat C5 no
afirma literalmente «otra vía» —dice «sin relación OSM propia; omite paradas
intermedias»—, y «sin relación OSM propia» es cierto pero no discrimina, porque **ningún**
patrón validado tiene relación propia: todos reutilizan la relación de línea. La crítica
del informe al criterio es justa; la atribución de la frase conviene precisarla.

Fragilidad adicional del generador (advisory): el disparador es
`len(pattern.stop_ids) == 7` sobre `10T0047C5`/`10T0048C5`. Hoy acierta porque existe
exactamente un patrón de 7 paradas en cada uno, pero cualquier variante futura de 7
paradas en esos `route_id` quedaría degradada en silencio. El emparejamiento posterior sí
es exacto por secuencia; la fragilidad está en el generador, no en el matcher.

### 4. El patrón degenerado de una parada — **DIAGNÓSTICO INCORRECTO; es un defecto del feed**

El patrón es `gtfs-pattern:574a2681305065df5673`, `route_id=10T0098C8b`, una sola parada
`12006` (Cercedilla), 54 viajes. Hasta aquí el informe acierta. Lo que no reporta, leído
del ZIP crudo (`fomento_transit.zip`, campos con relleno de espacios, por lo que hay que
`strip()` antes de cruzar `trip_id`):

- Los 54 `stop_times` de esos 54 viajes tienen **`stop_sequence` = `032` (43 viajes) y
  `025` (11 viajes)** — **no `1`**. Cercedilla es la parada nº 32 o nº 25 de secuencias
  más largas cuyas demás filas **faltan en el feed**. Un ramal corto legítimo tendría
  `stop_sequence` 1. Esto es concluyente.
- `arrival 12:19 / departure 12:32`: 13 minutos de parada en la posición 32, propio de un
  final de recorrido cuyas paradas anteriores se han perdido.
- `routes.txt` declara `route_long_name` = `"Cercedilla                              -"`
  — con el destino **en blanco**. La ruta espejo `10T0097C8b` declara `"-Cercedilla"`, con
  el origen en blanco, y tiene **114 viajes con CERO `stop_times`**.
- `trip_headsign` vacío en los 54; `shape_id` = `10_C8b_INV` **sí existe**: el operador
  publica geometría para ese sentido; lo que falta son los `stop_times`.

Es decir, el par C8b de Cercedilla está **roto en los dos sentidos** en el feed de
origen: un sentido pierde todos sus `stop_times` (y por eso desaparece por completo del
catálogo) y el otro conserva uno (y por eso aparece como patrón de una parada). No es
«secuencia insuficiente para definir desplazamiento» como propiedad del dato: es
**truncamiento del dato de origen**.

Consecuencias para el hallazgo, que debe reescribirse:

- La **causa raíz** declarada («el catálogo preserva fielmente cualquier secuencia no
  vacía») describe el síntoma en el consumidor, no el defecto en el origen.
- La **recomendación (A) «conservarlo con estado `non_traversable`»** convertiría un
  defecto de feed en un estado permanente de producto. Lo que corresponde es emitir un
  **evento de calidad de dato** por `trip` con `stop_sequence` inicial distinta de la
  primera de su secuencia o con `stop_times` incompletos, y que el estado de cobertura lo
  refleje como dato defectuoso, no como trazado imposible. La distinción importa porque
  `non_traversable` sugiere «este servicio no se puede animar» cuando lo correcto es
  «este horario llegó incompleto».
- Escala del mismo defecto, no cuantificada en el informe: en los `route_id` de la red 10
  el feed tiene **36.097 viajes**, de los que **35.976 entran al catálogo** y **121
  desaparecen**: 114 de `10T0097C8b` (cero `stop_times`) y 7 de `10T0035C5` (el huérfano
  ya documentado en DEC-025(c)). Esos 121 viajes **no están en ningún denominador** del
  informe ni del CSV. La crítica de P2-002 a los denominadores es acertada, pero apunta
  al lado pequeño: además del patrón degenerado que infla 103, hay 121 circulaciones
  reales que el denominador 35.976 **omite en silencio**. En todo el feed nacional:
  331 viajes con un solo `stop_time` y 430 sin ninguno.

Confirmado sí el dato auxiliar que cita el informe:
`packages/movement/schedule.py:155-156` exige ≥2 `stop_times`
(`no tiene al menos dos stop_times`), y `PatternIdentity.from_pattern` admite una sola
parada.

### 5. Relación con `AUD01-P0-002` — **lo refuerza y lo refina; no lo contradice**

La aritmética encaja sin residuo. P0-002 parte los 72 `pending` en **68 sin intento
documentado + 4 C4b con intento real fallido**. AUD-03 parte los 75 no-`validated` en
**67 + 4 + 3 + 1**. La identidad es exacta: **68 = 67 + 1**, donde el 1 es el patrón
degenerado de C8b, y los 4 de C4b son literalmente los mismos cuatro `pattern_id`. AUD-03
no desmiente a P0-002: le saca un patrón del cubo accionable.

Qué refuerza:

- El `reason` único compartido por los 72 queda confirmado tal como P0-002 lo denuncia
  («la distinción entre el límite externo de C4b y los 68 sin intento no es recuperable
  desde el artefacto canónico»): los 72 llevan la misma cadena, verificado en el CSV.
- La afirmación de P0-002 de que los 4 de C4b «necesitan un reintento contra Overpass, no
  una decisión de alcance» queda **elevada de grado**: esta revisión demuestra offline que
  la vía de esos 4 patrones ya está congelada en el repositorio a 48,3 m, invertida. No es
  solo que el reintento sea lo que falta: es que el dato necesario para descartar
  «geometría ausente» ya estaba dentro y no se usó.

Qué refina (y debe corregirse en `PRODUCT_AUDIT.md` cuando su ronda de corrección lo
permita — no se ha tocado ese fichero, está modificado por otra sesión):

- De los **68** «sin intento documentado», **67** son accionables descargando geometría.
  El 68º (`10T0098C8b`, 54 viajes) **no se arregla con ninguna descarga**: su horario
  llegó truncado del origen. Contarlo entre los que «nunca se intentaron descargar» hace
  que el trabajo pendiente parezca una unidad mayor de lo que es y atribuye a omisión del
  proyecto lo que es un defecto del proveedor.
- Precisión epistémica sobre «nunca se intentaron descargar»: lo verificable en el repo es
  que **no existe fuente congelada** para esos `route_id` y que **no hay intento
  registrado** en `STATUS`/`TASKS`/`MANIFEST`. Ausencia de registro es más débil que
  prueba de no-intento. Con el alcance deliberadamente mínimo de MP-018 («C5 + un ramal de
  C4») la conclusión se sostiene, pero la frase precisa es «sin fuente ni intento
  registrado», que es como P0-002 ya la redacta en su evidencia; conviene que el resumen
  no la abrevie a «nunca se intentaron».

### Correcciones solicitadas

1. **AUD03-P2-002 — reescribir diagnóstico, causa raíz y recomendación.** El patrón de
   una parada es un truncamiento del feed (`stop_sequence` 032/025, `route_long_name` con
   extremo en blanco, ruta espejo `10T0097C8b` con 114 viajes y cero `stop_times`), no una
   secuencia degenerada que haya que clasificar como `non_traversable`. Añadir los 121
   viajes de red 10 que el denominador 35.976 omite.
2. **AUD03-P1-002 — marcar como procedencia de un solo punto** las cifras vivas de
   `9174512` (versión 42, 59,440 km, 33,2–36,6 m, `sha256:03d87e1c…`), no reproducibles
   mientras la relación no esté congelada; e incorporar el test offline sobre `9174511`
   (48,3 m, monotonía inversa, 3/4 inversos exactos), que sostiene la conclusión sin red.
3. **AUD03-P1-002 — registrar la alternativa omitida** (reutilizar `9174511` invertida,
   cero descargas) junto con la razón física documentada para descartarla (vía contigua
   distinta, `MANIFEST.md`).
4. **Veredicto y AUD03-P1-001 — añadir la precisión 72 vs 67**: el mecanismo de código
   deja **72** patrones sin prueba geométrica alguna; 67 es la partición probatoria.
5. **AUD03-P2-001 — precisar la atribución** de la frase en el caveat C5 («sin relación
   OSM propia; omite paradas intermedias», no «otra vía») y añadir la evidencia de shape
   (mismo `shape_id` validado en C4b; no-discriminación del shape en C5).

Nada de esto altera el veredicto de fondo del informe —75 ≠ 75 ausencias de vía en OSM,
sin P0, y el fallback `raw` honesto— ni los recuentos, que reproducen exactos.

### Comandos reproducibles de esta revisión

```sh
.venv/bin/python scratch/aud03_geometry.py summary      # reproduce lo que el informe cita
.venv/bin/python -m unittest packages.geo.tests.test_catalog \
  packages.geo.tests.test_real_feed                     # 19/19 OK
```

Los cuatro análisis propios (recuento desde el catálogo de producto; proyección de los
patrones `10T0016C4b` sobre `9174511`; contraste `shapes.txt` vs corredor OSM recortado
al tramo de cada patrón; lectura del ZIP crudo con `strip()` de campos) son scripts de
revisión de un solo uso, no versionados: su salida está transcrita íntegra arriba y
cada uno es reconstruible a partir de `packages.geo` y `packages.gtfs` sin red.

---

## Revisión independiente de AUD-03 — ronda 2 (veredicto final)

**Revisa:** Claude Opus · High (`task_789f8d5e7a80`, `ctx_045f259f59a2`)

**Fecha:** 2026-11-23 · **Corrección evaluada:** commit `08ce3b8` sobre `2789ad2`

**Veredicto final: `APPROVED`.** Los cuatro puntos del `CHANGES_REQUESTED` están
resueltos, y dos de ellos mejor de lo pedido. La sección de la ronda 1 queda intacta
(`sha256` del bloque idéntico en `2789ad2` y en `08ce3b8`), la matriz conserva sus 75
filas con **0 discrepancias** contra `mp-018-corridor-coverage.csv`, el CSV canónico no
se tocó y los 19/19 tests focales siguen en verde aquí.

| Punto de la ronda 1 | Estado | Verificación propia |
|---|---|---|
| 1. P2-002 mal diagnosticado | **resuelto** | Retitulado «El feed C8b llega truncado…». Causa raíz ahora «truncamiento del feed de origen»; `non_traversable` pasa de recomendación (A) a alternativa (C) explícitamente rechazada («consagra el defecto»), y la recomendación es evento de calidad + corrección upstream. La evidencia cita `stop_sequence` **032 (43) / 025 (11)**, extremo de `route_long_name` en blanco y la ruta espejo con 114 viajes sin `stop_times`: coincide exactamente con lo que medí sobre el ZIP crudo. Los 121 huérfanos (114 + 7 de `10T0035C5`) están incorporados a denominadores, lotes y prueba de cierre. |
| 2. Cifras de `9174512` | **resuelto** | Versión 42, timestamp, 59,440 km, 1.223 nodos, 111 ways, `03d87e1c…` y 33,2–36,6 m marcados **NO VERIFICADAS** con la razón correcta (una sola llamada, no congelada). La existencia se sostiene sobre `MANIFEST.md` y `STATUS.md:850-852`. No queda ninguna mención de esas cifras fuera del marco NO VERIFICADO, y la conclusión ya no depende de ellas. |
| 3. Alternativa de coste cero en P1-002 | **resuelto** | Alternativas reescritas a (A) congelar `9174512` / (B) coste cero invirtiendo `9174511` / (C) backoff / (D) raw, con el riesgo físico citado del manifiesto (vía contigua de la plataforma doble, `way_id` no compartidos). Recomendación (A) con (B) solo si el contrato explicita esa incertidumbre lateral. La causa raíz añade el bloqueo real de código: `build_corridor_catalog` solo acepta arcos crecientes. |
| 4. Recuento 72 vs 67 | **resuelto** | Veredicto y «Criterio exacto auditado» dicen ahora **72 sin prueba geométrica alguna**, con 67 / 4 / 1 como refinación probatoria que el producto no conserva; P1-001 retitulado en consecuencia. |

**Mejora no pedida y bien hecha:** `scratch/aud03_geometry.py` sustituyó `live-c4b` por
`offline-c4b`, que reproduce la conclusión C4b **sin red**, contra la `9174511` ya
congelada. Ejecutado aquí da exactamente lo que medí de forma independiente en la ronda
1: 48,3 m en los cuatro patrones, `increasing False` / `decreasing True`, y
`exact_reverse True` en 3 de 4. `summary` añade además
`NETWORK_TRIPS 36097 / CATALOG_TRIPS 35976 / ORPHAN_TRIPS 121`, que confirma el hallazgo
de los huérfanos desde el propio instrumento. La auditoría ya no depende de ninguna
descarga en vivo.

**Aritmética nueva verificada** (las cifras nuevas son riesgo nuevo; todas cuadran):
13.878/36.097 = 38,446 %; 31/36.097 = 0,086 %; 22.067/36.097 = 61,133 %;
121/36.097 = 0,335 %; la fila suma 36.097 exacto; 20.273/36.097 = 56,163 %;
1.740/36.097 = 4,820 %; 15.649/36.097 = 43,353 % y 15.649/35.976 = 43,498 %;
267.857/537.899 = 49,797 %; 54 + 114 = 168 en la fila del lote C8b. Matriz: 75 filas,
22.098 viajes.

**Dos observaciones advisory, que no condicionan el `APPROVED`:**

1. `offline_c4b()` carga la fixture con `load_relation_geometry_json(source.path)` en vez
   de pasar por `_load_source(spec)`, así que **no comprueba el SHA-256** antes de usarla.
   Como toda la fuerza del argumento offline está en que la fuente es congelada *y con
   checksum*, el propio diagnóstico debería verificarlo. `summary` sí lo hace
   (`9174511 sha_ok True`), y lo verifiqué aparte, por lo que la evidencia es correcta;
   es la ergonomía del guion lo que cojea.
2. La celda «`0`: dato ausente» para las llamadas de los huérfanos resuelve bien el fondo
   (anotada, no silenciosa), pero la forma roza el principio «dato ausente ≠ cero» de
   `AGENTS.md`; un `—` sería más limpio que un `0` anotado.

Con esto, AUD-03 queda cerrado por la revisión: veredicto de fondo sostenido —75 ≠ 75
ausencias de vía en OSM, ningún P0, fallback `raw` honesto—, los cuatro recuentos
reproducidos exactos y los cuatro hallazgos con causa y recomendación que resisten
evidencia independiente.
