Origen de los datos: Renfe Operadora, posiciones de vehículos de Cercanías
y GTFS estático de Renfe Data del 20 de noviembre de 2026. Madrid Pulse
redujo ambos cortes a los 44 pares con corredor validado y filtró las tablas
estáticas a sus viajes, estaciones, servicios, rutas y shapes. Renfe no
respalda ni patrocina este servicio. [Renfe Data](https://data.renfe.com/) ·
[Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).

manifest.json conserva las huellas SHA-256 del origen y del extracto.
synthetic.json recoge los casos S1–S16 y los resultados del prototipo MP-024.
Los progresos sintéticos derivados de geometría OSM conservan su atribución.
© OpenStreetMap contributors. [ODbL](https://www.openstreetmap.org/copyright).

frames.json contiene resultados del evaluador Python de producción, con los
instantes de entrada desplazados 0,7 ms. Para regenerar desde la raíz:

```sh
python -c 'import json; from packages.movement.tests.test_stop_state import DATA,samples; (DATA/"frames.json").write_text(json.dumps(samples(),indent=1)+"\n")'
```
