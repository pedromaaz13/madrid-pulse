# Revisión crítica del plan UX — Decisiones de v3

Base: kit Madrid-Pulse-Orca-Hito3-v2 y MADRID_PULSE_PRODUCT_UX_PLAN_ORCA.md. Main remoto comprobado: 990c95dfa58cabcf664b905318a4a84fe1cecf19. No se ha inspeccionado el clon local del propietario ni ejecutado su aplicación en esta revisión.

## Conclusión

El informe mejora concreción de frontend e interacción, pero duplica tareas y prescribe algunas decisiones demasiado pronto. Se integra como enriquecimiento de MP-016→MP-022, conservando reparto/modelos, prototipo, replay, parche, alcance Madrid e histórico. Su tabla UX deja de ser un segundo backlog ejecutable.

| Propuesta del informe | Decisión | Integración |
|---|---|---|
| UX-01 auditoría | Mantener sin tarea nueva | MP-016 |
| UX-02 navegación | Mantener | Diseño incremental en MP-020, contrato MP-019 |
| UX-03 identidad/tiempo | Mantener | MP-017/019 y anexo |
| UX-04 estructura de carpetas | Modificar | Extraer responsabilidades cuando sea útil en MP-020; estructura orientativa |
| UX-05 adquisición | Mantener | MP-019/020; fallo parcial y single-flight |
| UX-06 objetos estables | Mantener | MP-020 y claves MP-017/019 |
| UX-07 plan temporal backend | Modificar | ADR MP-019; comparar alternativas antes de fijar formato |
| UX-08 animación/cámara | Mantener | MP-020; dependencia MP-018/019 |
| UX-09 ficha tren | Mantener | Contrato MP-019, UI MP-020 |
| UX-10 estación/línea | Mantener | MP-017/019/020 |
| UX-11 búsqueda/URL/favoritos | Dividir prioridad | Búsqueda/URL MP-020; favoritos opcionales |
| UX-12 renderer/capas | Modificar | Geometría MP-018 y UI MP-020; cambiar renderer según medida |
| UX-13 móvil/accesibilidad | Mantener transversal | MP-020/022, desde primer incremento |
| UX-14 Madrid | Mantener sin recortar | MP-017/018/022 |
| UX-15 aceptación | Mantener | MP-022; protocolo original de revisión |

## Cambios de criterio

- No hay quince tareas nuevas ni cambio del reparto Claude/Codex del kit. La tabla UX es material de referencia.
- No se impone un endpoint por tren, un contrato de puntos futuros o un store concreto. Resolver por ADR y prueba comparable.
- Se mantiene necesidad real de evolucionar el movimiento: el motor actual congela la observación reciente, por lo que un loop visual no basta.
- Una parada SKIPPED invalida su parada/ETA, no congela automáticamente la circulación completa.
- El informe denomina “revisión temporal” a controles que deben concretarse: un UUID/hash de snapshot no es un contador ordenable.
- La confianza heurística no se vende como probabilidad calibrada.
- Se preserva History/Explore mínimo del kit. Refactor frontend no justifica eliminarlo.
- Favoritos, efectos decorativos y sofisticación de símbolos no desplazan selección, tablero y movimiento verificable.
- Cinta de novedades con alternativa estática y pausa; evitar que sea requisito de animación decorativa.
- No se añaden tráfico, AV/LD, IA, cuentas, SQL Lab ni un cambio obligatorio a dbt.
- No se cambia AGENTS.md ni se aceptan ADR automáticamente.

## Fuentes de verdad

1. Instrucciones actuales del propietario y AGENTS.md del clon.
2. Seguimiento local TASKS/STATUS/CHANGELOG: implementación y autorizaciones reales.
3. PLAN-Y-ACEPTACION.md: alcance, reparto y dependencias del kit.
4. MEJORAS-PRODUCTO-VALIDADAS.md, anexo y matriz: aceptación complementaria.
5. diseno/: referencia sintética, no comportamiento productivo demostrado.
6. referencia/: investigación e históricos; no instrucciones alternativas de arranque.

Si hay divergencias del clon, registrar equivalencia/delta y conservar trabajo; no reescribir tareas aprobadas por seguir un documento congelado.

## Qué conserva este ZIP

Todo el material de v2, incluidos GTFS, JSON, manifest y parche, se conserva. Las revisiones de documentos operativos se archivan en referencia/historico-v2/. El informe UX original se conserva con aviso de precedencia. Un manifiesto final enumera hashes del paquete.

## Límites de la entrega

Se han revisado documentos y código publicado; se verifica el empaquetado, la sonda de replay y el instalador en repositorios temporales. Esas verificaciones no son tests de Madrid Pulse ni revisión cruzada Claude/Codex de una implementación.

## Complemento de consolidación v4

La revisión independiente del plan UX y del v3 confirma que no faltaba otro backlog de quince tareas. Se añaden únicamente tres matices con impacto de producto: enumeración explícita de todos los servicios programados, matriz completa de cobertura por línea y protocolo acotado de aprobación de workers. Ver `REVISION-FINAL-V4.md` para las decisiones y descartes. No se alteran roles ni secuencia MP-016→MP-022.
