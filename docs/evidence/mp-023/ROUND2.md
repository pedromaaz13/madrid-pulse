# MP-023 — Correcciones de la revisión

## Aislamiento registrado antes de ejecutar las pruebas

- Imagen local `postgis/postgis:17-3.5`, contenedor desechable propio
  `mp023-round2` en `127.0.0.1:5451`. El filtro de Docker para el puerto
  5451 no encontró contenedores antes del arranque.
- DSN con credencial ficticia
  `postgresql://mp023:mp023_local@127.0.0.1:5451/madrid_pulse`.
  Base `madrid_pulse`, esquema `public`, rol temporal `mp023` (propietario
  para inicializar PostGIS y aplicar las migraciones).
- El puerto 5433 se usa solo como dato de validación sin conexión.
  Las dos migraciones se aplican desde cero y se eliminan el contenedor
  propio y su volumen anónimo con `docker rm -fv mp023-round2`.

## Resultados sobre `6d1d360`

| Punto | Comprobación ejecutada | Resultado |
|---|---|---|
| A1 | `git grep -n -e 5433` con las cuatro rutas de datos y documentación excluidas | PASS. Solo las constantes autorizadas en `packages/database.py` y el arnés |
| A2 | `SafeConfigurationTests.test_reserved_port_is_rejected_for_every_host_without_connecting` | PASS. Rechazo en los cuatro entornos para los alias solicitados, el nombre del equipo, DNS remoto, IPv4 e IPv6. El diagnóstico remite a la guía y la prueba verifica la excepción de dev/live mediante el validador puro |
| A3 | `SafeConfigurationTests.test_replay_tools_report_missing_config_and_mark_without_traceback` y dos arranques de `python -m services.snapshotter 2026-11-19` | PASS. Ambas herramientas salieron con código 1 y mensaje legible con URL ausente, base sin marca y base no disponible. El snapshotter exportó Parquet en dev y live antes de aplicar la marca |
| A4 | Dos pruebas dirigidas del helper y suite de 28 módulos con `MADRID_PULSE_REQUIRE_DB=1` | PASS. Los fallos de configuración, marca y disponibilidad ya no producen skips en modo estricto. Suite con **283 casos, 18 skips**, salida 0. Los skips fueron 13 por el ZIP oficial ausente y 5 por los datos del soak histórico |
| A6 | `env -i <venv>/bin/python -m unittest -v apps.api.tests.test_history_contract apps.api.tests.test_api_contract.RuntimeModeTests` | PASS. 14 casos con el entorno vacío. Los tests bloquean cualquier intento de conexión. Los ejemplos de arranque y pruebas muestran la URL |
| A8 | Migraciones desde cero con `docker exec -i mp023-round2 psql`, verificación de la marca y comprobación del mensaje de rechazo en A2 | PASS. Procedimiento reproducido sin cliente `psql` en el host |
| A9 | `git grep` en los documentos de despliegue y operación y `git diff` en las rutas históricas y de seguimiento | PASS. La arquitectura usa la URL canónica y declara el entorno. La guía mantiene el nombre antiguo en su aviso de migración. Los documentos históricos y de seguimiento permanecen intactos |

RED contra `beb9434` volvió a fallar como se esperaba (3 casos, 16 fallos,
salida 1). El mismo arnés en GREEN pasó los 12 casos previos a la marca.
Después de aplicar la marca y ejecutar la suite con el modo estricto, la
ingesta real del colector y su lectura por HTTP en la API también pasaron.
[Comandos y salida de PostgreSQL, RED y GREEN](ROUND2_DB.log)

Ruff sobre los Python modificados, `git diff --check`, el verificador de
gobernanza y la limpieza del contenedor, el volumen y el worktree RED
pasaron. [Comprobaciones estáticas y limpieza](ROUND2_STATIC.log)

NO EJECUTADO en esta ronda GitHub Actions remoto ni captura en vivo.
