# tests/e2e

Replay end-to-end determinista (MP-015): un único test inyecta bytes de
fixtures reales (congeladas en MP-004, mismo esquema real observado en
MP-003) como respuesta del `fetcher` inyectable del colector, y recorre la
cadena completa sin tocar red en vivo: JSON crudo con forma de Renfe →
colector (parseo/normalización/calidad/persistencia) → PostgreSQL real →
resolución de topología GTFS → respuesta de API real (`apps.api.service`, la
misma capa que consume el frontend de MP-014).

Dos escenarios, ambos con datos reales, nunca mocks de la lógica de negocio:

1. La fixture de MP-004 tal cual: prueba que el pipeline nunca fabrica una
   resolución cuando el `trip_id` no existe en la GTFS cargada (igual que
   DEC-029 en producción).
2. Un payload sintético con la forma real exacta de MP-003, pero con un
   `trip_id`/`stopId` que sí existe en la GTFS reducida de MP-010: prueba la
   resolución positiva de extremo a extremo.

```sh
python3 -m unittest tests.e2e.test_replay -v   # requiere PostgreSQL local
```

Checklist de preparación de MVP: ver `docs/MVP_READINESS.md`.
