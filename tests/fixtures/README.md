# Fixtures GTFS-RT de Renfe

Subconjuntos congelados de cuerpos JSON capturados directamente de los tres feeds
GTFS-RT de Renfe el 2026-11-18. No se guardan cookies ni cabeceras HTTP. Los
campos GTFS-RT son datos operativos públicos y no contienen datos personales.

Las capturas completas se redujeron a casos representativos para mantener el
repositorio ligero. `vehicle_positions.json` conserva C5 de Madrid y tres C5 de
otros núcleos para detectar filtros ambiguos; `trip_updates.json` conserva viajes
de Madrid programados y cancelados; `alerts.json` conserva la alerta C5 de Madrid
y dos alertas C9. `MANIFEST.md` documenta origen, recuentos y SHA-256.

## Tests

Se usa Python 3 y `unittest` (`test_parse_fixtures.py`) porque forma parte de la
biblioteca estándar y permite ejecutar la suite sin instalar dependencias ni
acceder a la red. La prueba carga únicamente ficheros locales, valida el esquema
observado en MP-003, verifica los hashes y demuestra que filtrar solo por la
etiqueta `C5` mezcla núcleos distintos.

```sh
python3 -m unittest discover -s tests/fixtures -p 'test_*.py' -v
```
