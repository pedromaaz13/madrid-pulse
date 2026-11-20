# ATTRIBUTION.md

Textos de atribución verificados para producto, documentación y exportaciones. Fecha de verificación: `2026-11-18`.

## OpenStreetMap (`ODbL-1.0`)

En toda vista que use datos OSM debe aparecer, visible y legible:

```text
© OpenStreetMap contributors
```

En web, `OpenStreetMap` debe enlazar a `https://www.openstreetmap.org/copyright`, lo que identifica también la ODbL. En una distribución de datos, nombrar y enlazar directamente la licencia ODbL y ofrecer una base derivada conforme a sus términos. En mapas interactivos, seguir la [guía de atribución de la OSMF](https://osmfoundation.org/wiki/Licence/Attribution_Guidelines): crédito legible cerca del mapa o presentación inicial conforme a su *safe harbour*, y licencia siempre localizable.

**MP-011 — fixture de geometría ferroviaria (`tests/fixtures/osm_c5_real/`):** es una base de datos derivada de OSM en el sentido de la ODbL (extracto estructurado de nodos/`ways`/relación, no una imagen renderizada). Se distribuye bajo `ODbL-1.0` con la atribución de arriba, independientemente de la licencia de código del repositorio (`DEC-002`, todavía pendiente) — ver DEC-024 en `docs/DECISIONS.md` y `tests/fixtures/osm_c5_real/MANIFEST.md` para el detalle de fuente, fecha y checksums.

## Renfe Data (`CC BY 4.0` + condiciones del portal)

Texto base para UI o pie persistente:

```text
Origen de los datos: Renfe Operadora — [nombre del dataset],
Creative Commons Attribution 4.0. Última actualización de la fuente: [fecha, si se informa].
Datos [normalizados/modificados] por Madrid Pulse; Renfe no respalda ni patrocina este servicio.
```

En web, enlazar `Renfe Operadora` a `https://data.renfe.com/` y la licencia a `https://creativecommons.org/licenses/by/4.0/`. Deben preservarse los metadatos originales de actualización y condiciones de reutilización. Si no hubo cambios, sustituir `[normalizados/modificados]` por `reproducidos sin modificación`; nunca inventar una fecha ausente.

## CRTM (`CRTM-LDA`)

La licencia exige identificar datos brutos o explotados y, en plataformas digitales, mostrar `Powered by CRTM` con enlace oficial:

```text
Powered by CRTM — datos [brutos/explotados] de la oferta planificada de Cercanías Madrid.
Última actualización de la fuente: [fecha incluida en los metadatos].
Datos [normalizados/modificados] por Madrid Pulse; CRTM no respalda ni patrocina este servicio.
```

`Powered by CRTM` debe enlazar a `https://www.crtm.es/`. Se conservan los metadatos de fecha y condiciones de reutilización; la información mostrada debe mantenerse actualizada y no puede falsearse ni desnaturalizarse.

## Comunidad de Madrid — estadísticas 1923861 (`CC BY 4.0`)

```text
Fuente: Comunidad de Madrid; datos de origen del Observatorio del Ferrocarril de España (MITMS),
bajo Creative Commons Attribution 4.0. [Cambios realizados por Madrid Pulse, si los hay].
```

Enlazar el dataset y `https://creativecommons.org/licenses/by/4.0/`. Este texto solo aplica cuando se use el conjunto estadístico; no sustituye las atribuciones Renfe o CRTM de los feeds operativos.

## Valfiguer (solo si se reutilizan sus datos normalizados)

Madrid Pulse no usa Valfiguer como upstream de producción. Si una investigación o exportación reutiliza expresamente sus datos normalizados, su página oficial prescribe:

```text
Fuente: Renfe Data (data.renfe.com), CC BY 4.0.
Datos normalizados por trenes.valfiguer.com (Valfiguer).
```

La licencia de datos no implica una licencia del código de la aplicación, que no se ha podido verificar.

## Proyectos de referencia conceptual

Via Península, Valfiguer, Niltra/cercanias y atlas-ferroviario son referencias de investigación, no fuentes de código incorporado. Puede reconocerse su influencia conceptual en documentación, pero no debe afirmarse que patrocinan Madrid Pulse. No se ha copiado código, por lo que en este momento no se trasladan avisos AGPL/MIT al código propio.

Texto de transparencia opcional:

```text
Madrid Pulse estudió patrones públicos de Via Península, Valfiguer, Niltra/cercanias
y atlas-ferroviario, y los reimplementa de forma independiente sin reutilizar su código.
```

## Ubicación mínima

- **Mapa (MP-014):** OSM siempre visible; Renfe/CRTM visibles según la capa/dato mostrado.
- **Vistas Live/History/Explore:** fuente, licencia, frescura/última actualización y transformaciones accesibles sin ambigüedad.
- **Exportaciones/API (MP-013):** metadatos de `source_id`, publisher, licencia, URL y actualización junto al dato o en documentación enlazada estable.
- **README/documentación:** enlace a `docs/legal/` y reconocimiento conceptual separado de las atribuciones legales de datos.
