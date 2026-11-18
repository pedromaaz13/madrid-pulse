# ATTRIBUTION.md

Textos de atribución a mostrar en producto (UI) y documentación. **Estado: borrador, pendiente de confirmación de requisitos exactos en MP-002.**

## OpenStreetMap (obligatorio, ODbL)

Debe aparecer visible en cualquier vista de mapa:

```text
© OpenStreetMap contributors
```

Con enlace a `https://www.openstreetmap.org/copyright` cuando el medio lo permita (web).

## Renfe (CC BY 4.0 — a confirmar en MP-002)

Texto de atribución propuesto, a confirmar contra los requisitos exactos del portal Renfe Data:

```text
Datos de Cercanías: Renfe (data.renfe.com), bajo licencia Creative Commons Attribution 4.0.
Madrid Pulse no está respaldado ni patrocinado por Renfe.
```

## CRTM (a confirmar en MP-002)

Pendiente de texto exacto hasta verificar los requisitos de atribución de CRTM/Comunidad de Madrid en MP-002.

## Proyectos de referencia conceptual (no son fuentes de datos, pero se reconocen como inspiración de arquitectura)

```text
El diseño del motor de movimiento y la observabilidad de fuente de Madrid Pulse
están conceptualmente inspirados en los patrones públicos de Via Península y
Valfiguer, reimplementados de forma independiente. Madrid Pulse no reutiliza
su código ni sus APIs en producción.
```

Este reconocimiento es una buena práctica de transparencia, no una obligación legal derivada de licencia (salvo en el caso de Via Península si en el futuro se reutilizara código AGPL literal, lo cual no está autorizado actualmente — ver `LICENSE_MATRIX.md`).

## Dónde debe aparecer

- **UI del mapa** (MP-014): atribución OSM siempre visible, atribución Renfe/CRTM visible en la vista de datos en vivo o en un pie de página persistente.
- **README.md** del producto: referencia a `docs/legal/` para el detalle completo.
- **API** (MP-013): opcionalmente, un endpoint o campo de metadatos que incluya la atribución junto con los datos servidos.
