# MP-030: evidencia de implementación

Base `origin/main` 4bc86128d44a9b83f8f9747df5cf83ce593f0194. Ejecutor: Codex `gpt-6.1-terra`, esfuerzo `medium`, según `orca orchestration worker-show`. La fixture `apps/web/src/__fixtures__/snapshot-map-matched.json` está versionada; los casos modifican copias deterministas en memoria.

- [RED](RED.txt): extracción temporal de `origin/main` en `/tmp`, con los dos archivos de pruebas nuevos y el componente aislado de avisos copiados para poder ejecutarlos. Node 22.13.1, Vitest: 18 fallos y 13 éxitos. Siete fallos de rótulos se deben a que la función nueva `methodStyle` no existe en la base; los otros incluyen comportamiento ausente en panel y congelación. Los tres casos del componente de degradación pasan también en RED porque se copió ese componente; no prueban por sí solos la integración con `App`. La extracción temporal se eliminó.
- [GREEN](GREEN.txt): Node 22.13.1, `npm run lint && npm run typecheck && npm test && npm run build`: PASS, 131 pruebas en 12 archivos, incluyendo las 110 previas. El build avisa de chunks mayores de 500 kB y verifica el worker de MapLibre.
- La integración de degradaciones consume `snapshot.data.degraded` en `App`; no consulta `catalog.gtfs_status`. Los tests de degradación ejercitan el componente aislado, no un montaje integrado del sondeo o un catálogo cacheado.
- NOT RUN: navegador, inspección de escritorio, móvil a 390 px, capturas e interacciones reales. La accesibilidad y ausencia de desbordamiento visual quedan para la revisión independiente.
- El contrato publica los campos utilizados; no se ha identificado ningún campo ausente. La leyenda y los símbolos del mapa mantienen el vocabulario genérico por método; la ficha y lista usan además el espacio para distinguir el ancla proyectada.
