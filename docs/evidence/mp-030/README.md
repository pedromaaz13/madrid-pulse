# MP-030: evidencia de implementación

Base `origin/main` 4bc86128d44a9b83f8f9747df5cf83ce593f0194. Ejecutor: Codex `gpt-6.1-terra`, esfuerzo `medium`, según `orca orchestration worker-show`. La fixture `apps/web/src/__fixtures__/snapshot-map-matched.json` está versionada; los casos modifican copias deterministas en memoria.

- [RED](RED.txt): extracción temporal de `origin/main` en `/tmp`, con los dos archivos de pruebas nuevos y el componente aislado de avisos copiados para poder ejecutarlos. Node 22.13.1, Vitest: 18 fallos y 13 éxitos. Siete fallos de rótulos se deben a que la función nueva `methodStyle` no existe en la base; los otros incluyen comportamiento ausente en panel y congelación. Los tres casos del componente de degradación pasan también en RED porque se copió ese componente; no prueban por sí solos la integración con `App`. La extracción temporal se eliminó.
- [GREEN](GREEN.txt): Node 22.13.1, `npm run lint && npm run typecheck && npm test && npm run build`: PASS, 131 pruebas en 12 archivos, incluyendo las 110 previas. El build avisa de chunks mayores de 500 kB y verifica el worker de MapLibre.
- La integración de degradaciones consume `snapshot.data.degraded` en `App`; no consulta `catalog.gtfs_status`. Los tests de degradación ejercitan el componente aislado, no un montaje integrado del sondeo o un catálogo cacheado.
- NOT RUN: navegador, inspección de escritorio, móvil a 390 px, capturas e interacciones reales. La accesibilidad y ausencia de desbordamiento visual quedan para la revisión independiente.
- El contrato publica los campos utilizados; no se ha identificado ningún campo ausente. En esta primera entrega la leyenda y los símbolos mantenían el vocabulario genérico por método; se corrigió en la ronda siguiente.

## Corrección tras revisión de `b799b7a`

| Hallazgo | Corrección |
|---|---|
| B1 | Los diez motivos tienen traducción; el test compara las claves con el enum de `apps/api/openapi.json` y prueba cada rótulo en ficha. |
| B2 | La observación bruta dice GPS publicado sin proyección; el ancla sobre corredor tiene rótulo y detalle propios. |
| A1 | Leyenda, símbolo y etiqueta del tren seleccionado usan el par método/espacio; forma y glifo distinguen categorías. |
| A2 | La extrapolación se llama «Extrapolada» y el ancla proyectada, «Observada sobre corredor». |
| A3 | `App.gtfs.test.tsx` monta `App` en jsdom con sondeo real y `fetch` controlado: `expiring`, `expired`, `not_yet_valid` y desaparición en `valid`, con revisiones crecientes, misma versión de catálogo y revalidación ETag; verifica que se conserva el catálogo anterior aunque el cuerpo nuevo cambie. Los eventos de degradación antiguos también se retiran de novedades. |
| A4 | Estado del operador y fuente traducidos, con nombre de estación si el catálogo lo contiene. |
| A5 | Fuente y motivos conocidos traducidos tanto en avisos como en novedades; GTFS aparece antes de filtros y los demás avisos se agrupan en un desplegable. |
| A6 | `anchor_version_changed` se presenta como «ancla disponible», sin afirmar que hubo un cambio de versión. |
| A7 | En móvil se coloca un resumen del tren seleccionado, su procedencia y retención/cancelación/congelación antes de búsqueda y filtros; el aviso GTFS también va delante. Verificación visual pendiente. |

- [RED sobre origin/main](review-RED-origin.txt): `App.gtfs.test.tsx` copiado a una extracción limpia; falla en la primera comprobación del aviso GTFS. No se copió código de producción nuevo.
- [RED sobre b799b7a](review-RED-b799.txt): las dos suites de rótulos copiadas a una extracción limpia producen 13 fallos y 15 éxitos; uno de los fallos se debe a la función nueva `degradationText` ausente, los demás incluyen las aserciones de traducción y procedencia.
- [GREEN](review-GREEN.txt): `npm run lint && npm run typecheck && npm test && npm run build`, Node 22.13.1; PASS, 140 tests en 14 archivos. Build verifica el worker MapLibre y avisa de chunks mayores de 500 kB.
- NOT RUN: inspección visual, navegador real, lector de pantalla y móvil a 390 px; jsdom no valida composición ni desbordamiento. Queda pendiente la revisión visual delta de Claude.
