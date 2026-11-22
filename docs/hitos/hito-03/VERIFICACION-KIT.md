# Verificación real del kit definitivo v4

**Fecha:** 2026-11-22. Este documento registra únicamente tests del paquete y una reproducción del replay congelado. No constituye prueba de integración de la aplicación local en Orca, ni autoría/revisión cruzada del Hito 3.

## Herencia

Se preservan byte a byte las fuentes de replay, GTFS, parche de referencia, cuatro PNG y prototipo de v3. Documentos v3 originales archivados en `referencia/historico-v3/`; las revisiones v2 ya estaban archivadas en `referencia/historico-v2/`. La conversión de 15 tareas UX en siete MP del v3 se mantiene.

## Pruebas de paquete

- Verificar_integridad.py comprueba hashes de todos los archivos contra MANIFEST-SHA256.json (sin el propio manifiesto).
- verificar_instalador.py prueba rama main protegida, datos excluidos, conflictos con ediciones, symlinks, dry-run, idempotencia, actualización v2 y v3, y solo-datos.
- `data/hito-03/replay/comprobar.py` reproduce datos congelados, no feeds actuales.

Resultados efectivamente reproducidos en este entorno:

- **8 pruebas del instalador: OK** (incluida la actualización v2 y v3 por hash).
- **Replay congelado: OK**: catálogo de 42 rutas, 12 denominaciones/variantes y 36.097 viajes; corte `1532`: 119 vehículos Madrid con 119 matches y 49 paradas SKIPPED sin arrival; corte `1533`: 121 con 121 matches y 49 SKIPPED. Son conteos de fixtures, no del Live actual.
- **Verificación SHA-256: OK** sobre todos los archivos incluidos en el manifiesto.
- **ZIP extraído y vuelto a verificar** en directorio temporal: OK (comprobación final de empaquetado).

## Lo que NO se ejecuta aquí

- No se inició un servidor web de Madrid Pulse ni el colector del usuario.
- No se verificó un replay de la red real en frontend, mapas, WebGL ni 60 s de movimiento.
- No se modificó el clon del usuario, su licencia, servicios ni git config.
- No se garantiza que la configuración nocturna de permisos esté disponible en su versión instalada.
