# Fixture sintética derivada de MP-022

`sequence.json` **no es una captura de Renfe ni producción en vivo**. Define
un reloj y progresos sintéticos sobre el GTFS y la geometría OSM versionados
del repositorio para cubrir escenarios que los cortes congelados `1532/1533`
no pueden demostrar: recuperación después de estimación, límite físico,
agotamiento del horizonte y cambio de identidad.

La prueba consumidora es `tests/e2e/test_mp022_synthetic_derived.py`. Los
cortes `1532/1533` permanecen intactos y se validan aparte con
`data/hito-03/replay/comprobar.py` y
`apps.api.tools.replay_three_snapshots`.
