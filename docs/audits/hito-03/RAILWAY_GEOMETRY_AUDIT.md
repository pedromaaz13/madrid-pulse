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

<!-- AUD-03: sustituir este placeholder sin modificar la sección "GTFS y catálogo". -->

Pendiente de auditoría independiente de relations, ways, continuidad,
sentido y proyección de estaciones.
