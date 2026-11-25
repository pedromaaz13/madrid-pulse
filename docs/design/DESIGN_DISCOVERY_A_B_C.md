<!-- FUENTE IMPORTADA ÍNTEGRA — no editar el cuerpo. Solo esta cabecera es de gobernanza. -->
> **Nota de incorporación (2026-11-25).** Documento fuente recibido del propietario e incorporado sin alterar su contenido (todo lo que sigue a la primera línea `---` es el original byte a byte).
> - **Estatus:** ORDEN DE DISCOVERY HISTÓRICA (edición 2026-11-23), no iniciada; ver overrides vigentes en [DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md](DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md)
> - **Fuente:** `DESIGN_DISCOVERY_A_B_C.md` (paquete `MADRID_PULSE_ORCA_GOBERNANZA_MVP_LIVE_DESIGN`)
> - **SHA-256 del original:** `9cabcb4170eb253a72efb67d922f16f828be95aa74f0d2ce3729a74e2c91d413`
> - **Alcance:** discovery y prototipos aislados A/B/C (DES-00…DES-09). **Hoy esta orden histórica NO habilita ni discovery ni prototipos** (gate humano HG-DESIGN-START abierto), no autoriza rediseño productivo ni elección de propuesta (gate humano). Las adaptaciones vigentes (Terra sin navegador, etc.) están en DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md y mandan sobre el imperativo del cuerpo
> - **Regla:** importar este documento **no** convierte sus recomendaciones en decisiones aprobadas. Las decisiones viven en `docs/DECISIONS.md` y `docs/adr/`; el estado vigente, en `docs/STATUS.md` y `docs/governance/PROJECT_STATE.json` (si el cuerpo menciona PROJECT_STATE.yaml, el fichero real es el .json).
> - **Privacidad:** el cuerpo conserva por integridad la formulación original, incluida alguna ruta absoluta local; excepción **aceptada por el propietario (2026-11-25)**: el original se conserva sin modificar y la ruta no es operativa (ver el override).

---
# MADRID PULSE — ORCA / PRODUCT DESIGN DISCOVERY A–B–C

> **Edición 2026-11-23 — matriz de agentes actualizada.** Alcance: únicamente discovery, capturas reales y tres prototipos aislados. La selección e implementación posteriores requieren autorización humana.

## 0. Misión y límite de autorización

Claude, actúa como **orquestador principal** de Product Design para Madrid Pulse en Orca. **Tu configuración prevista es `claude-sonnet-5-5` · esfuerzo `medium`**; delega la dirección artística compleja en un worker `claude-opus-5-5` · `high`. Verifica ambos identificadores en la instalación real antes de despachar. Este encargo comienza **solo cuando haya terminado la auditoría adversarial AUD-00→AUD-09**. Su objetivo es evaluar la aplicación que ya existe, explorar tres direcciones visuales profesionales y entregarme **tres mockups de alta fidelidad, comparables y navegables**, para que **YO ELIJA**.

**Este encargo autoriza exclusivamente DISCOVERY y PROTOTIPADO AISLADO. NO autoriza implementar el rediseño sobre el frontend productivo, crear un nuevo hito de desarrollo, fusionar ramas, hacer push/PR ni escoger la propuesta final por mí.** Cuando entregues las propuestas A/B/C, **detente y solicita mi elección**. La implementación posterior necesitará una nueva autorización.

Repositorio: `/Users/matu/Documents/DATA/madrid-pulse`

No uses el antiguo `Madrid-Pulse-Premium-Design-Kit` como fuente estética ni reutilices sus mockups: han sido **expresamente rechazados** por el propietario. Sí puedes documentar por qué fracasaron (aspecto de dashboard genérico, iconos poco cuidados, mapas SVG ficticios).

## 1. Recupera el proyecto sin repetir la auditoría

1. Comprueba el estado real de Orca, el Run de auditoría, worktrees, HEAD de MP-022 y sus posibles cambios posteriores. Lee las instrucciones vigentes `AGENTS.md`, `CLAUDE.md`, tareas, estado y ADR pertinentes.
2. **Consume** los informes ya elaborados por la auditoría, especialmente `FRONTEND_UX_AUDIT.md`, `FINDINGS_REGISTER.md`, `NEXT_STEPS_PROPOSAL.md`, `AUDIT_EXECUTIVE_DECISION.md` y los hallazgos sobre geometría/movimiento relevantes para la UI. No los vuelvas a investigar desde cero.
3. Confirma el HEAD que contiene el frontend real del Hito 3: **no presupongas que está en `main`**. No abras un segundo proceso que edite un worktree en uso.
4. Resume en una página: lo que realmente existe en Live/History/Explore, defectos visuales, limitaciones de fuentes, bloqueantes P0/P1 y restricciones arquitectónicas. Distingue hechos comprobados de opiniones estéticas.
5. Si la auditoría no ha terminado, **no compitas con ella**. Registra el estado y **no inicies este encargo**: el propietario lo lanzará una vez haya cerrado la auditoría. No prepares automatizaciones ni promesas de ejecución en segundo plano.

## 2. Levanta y captura el frontend existente

- Sigue los scripts, variables y puertos documentados en el repositorio: no inventes comandos ni bases de datos. Utiliza el entorno local seguro o replay, sin tocar volúmenes de datos ni ejecutar migraciones destructivas.
- Abre la aplicación mediante **Playwright en un navegador real**. Registra URL, HEAD, modo Live o Replay, snapshot y errores de consola/red.
- Obtén capturas actuales: Live general, Live con zoom, tren seleccionado/seguimiento, estación/tablero, History, Explore y los estados de loading/error/stale que puedan reproducirse sin alterar datos. Usa 1440×900, 1920×1080 y 390×844; añade 768×1024 si aporta hallazgos.
- Prueba **interacciones**, no únicamente screenshots: zoom, filtros, tren, seguimiento, volver al mapa, línea, estación, History y Explore. Haz al menos una grabación corta cuando permita constatar el movimiento o una anomalía visual.
- Si no puede arrancar, documenta el bloqueo, utiliza solo evidencias verdaderas disponibles y declara qué pantallas **no se observaron en navegador**; nunca suplas observaciones ausentes con mockups presentados como capturas del sistema.
- Entrega `BASELINE.md`, screenshots y tabla de defectos VISUAL / UX / FUNCIONAL con referencia a la auditoría previa. **No vuelvas a auditar backend, GTFS o geometría salvo la evidencia indispensable para no diseñar algo engañoso.**

## 3. SOLO tres fuentes de diseño — responsabilidades no solapadas

Estudia los **README y la documentación oficial actual** de las siguientes herramientas antes de invocarlas. Comprueba qué está instalado, versiones, licencias y compatibilidad con Orca/Claude Code/Codex. No introduzcas otros repositorios, frameworks ni un nuevo stack de UI en esta fase. No instales nada global ni ejecutes scripts de instalación, hooks o binarios descargados sin revisar exactamente sus efectos y la autorización aplicable.

**A. Anthropic `frontend-design` — dirección creativa principal**
- Fuente oficial: `https://github.com/anthropics/skills/tree/main/skills/frontend-design` (y plugin oficial `https://claude.com/plugins/frontend-design`).
- Lee `SKILL.md` de la versión disponible. Úsala para especificar concepto, composición, tipografía, materiales y criterios visuales, **antes de construir cada prototipo**.
- No atribuyas a Claude Code capacidades de Claude Design que Orca no tenga verificadas. Si Claude Design está accesible, puedes usarlo; si no, crea prototipos aislados y navegables en el entorno disponible sin simular esa integración.

**B. Hallmark — exploración formal y comprobaciones anti-genérico**
- `https://github.com/nutlope/hallmark`
- Lee README, catálogo y mecanismo de themes/custom. Úsalo para comparar materiales y composiciones y para revisar los prototipos en navegador real cuando sea posible; **no dejes que elegir un tema aleatorio sustituya el briefing**.
- Si se utiliza su auditoría, que se centre en patrones visuales genéricos y en preservar contenido/interacciones. **No ejecutar `redesign` contra el frontend real**.

**C. Impeccable — crítica, accesibilidad y refinamiento**
- `https://github.com/pbakaus/impeccable`
- Lee README, `critique`, `audit`, `shape`, `typeset`, `layout`, `adapt`, `polish` y el detector. Utilízalo **después** de una primera versión de cada propuesta para detectar defectos y pulir pantallas concretas; no dupliques el trabajo de Hallmark.
- **Precaución obligatoria:** su modo `live`/Apply puede iniciar CLI externos con aprobaciones y sandbox desactivados según su documentación. **No lo uses** en este encargo; tampoco hooks no revisados ni instalaciones con efectos globales. Para prototipos, usa edición controlada en carpeta aislada y capturas Playwright. Si no se puede usar con seguridad, realiza la crítica manual y documenta la limitación.

**Distribución explícita:** Anthropic define la dirección; Hallmark ayuda a diversificar y comprobar; Impeccable critica y mejora. Un único reporte de decisiones y defectos por propuesta. No multipliques agentes o herramientas para analizar lo mismo.

## 4. Brief visual de Madrid Pulse

No estamos diseñando una landing page, una fintech genérica ni un sistema de tarjetas estadísticas: **es una aplicación operacional cartográfica** sobre trenes, vías, estaciones, incidencias, tiempos y datos de distinta fiabilidad.

**Objetivo visual:** tecnología contemporánea, premium, precisa y rápida; neutros fríos, grafito/titanio, metal satinado/cerámica técnica si encaja, esquinas suavemente redondeadas, tipografía cuidada, microinteracciones funcionales. Palantir sirve de referencia a nivel de operaciones y densidad, **no de estética que copiar**. Valfiguer es referencia ferroviaria de interacción (mapa, tren, estación, seguimiento). Vía Península es referencia conceptual técnica, no guía visual obligatoria.

**Restricciones:** mapa real como protagonista; colores ferroviarios reconocibles; datos y edades honestos; sin 3D decorativo que comprometa FPS; sin gradients/glassmorphism gratuitos, cards repetitivas ni tema negro+lima por inercia. Distinción observada/matched/estimada/scheduled/stale. Iconos de tren premium, con orientación, selección y legibilidad por zoom; comparar SVG 2D, 2.5D y 3D ligero, con costes para MapLibre. No inventar GPS, ETAs, plataformas, métricas o recorridos.

## 5. Tres propuestas A/B/C realmente diferentes

Para **cada propuesta**, redacta primero un concepto breve con usuarios, objetivo principal, sistema de colores (4–6 tonos), tipografía, anatomía de pantalla y razones de cada decisión. Rechaza tu primera solución si es genérica. A continuación crea un **prototipo de alta fidelidad y navegable**, separado del producto. No acepto wireframes grises, SVG improvisados ni simples cambios de paleta.

**A — TITANIUM CONTROL:** carácter industrial-metalizado, materiales mates, neutralidad fría, controles de precisión, mayor densidad operacional. Organización basada en paneles de control discretos y datos verificables.

**B — IMMERSIVE RAIL MAP:** experiencia cartográfica de máxima superficie, navegación espacial, controles superpuestos mínimos, selección y seguimiento contextuales, motion refinado; paneles que no estrangulan el mapa.

**C — CONTEMPORARY SIGNAL:** producto tech más expresivo y reconocible, color más intencional, tipografía distintiva, composición editorial/operativa. Debe ser diferente también en layout y navegación, no solo más saturado.

Las **tres** deben preservar los mismos flujos de uso y mostrar suficiente contenido para compararlas en igualdad:
- Live desktop 1440×900 y móvil 390×844.
- Tren seleccionado, orientación, acción Seguir/Centrar, datos de origen y antigüedad.
- Estación seleccionada y próximas salidas (con disponibilidad real o datos claramente rotulados DEMO).
- Concepto de History con timeline y controles.
- Concepto de Explore con métricas y definiciones.
- Navegación entre vistas, filtros y búsqueda, estados loading/empty/stale.
- Set mínimo de iconos y variantes 2D/2.5D/3D ligero para tren; zoom aproximado y marcado de origen de posición.
- Al menos una transición funcional de menú/ficha/seguimiento; `prefers-reduced-motion` respetado.

Usa **capturas reales del mapa local o tiles/cartografía legítimos y disponibles** cuando sea viable. Si un mockup usa una ilustración de respaldo, rotúlala inequívocamente como ilustración. No simules el mapa de Cercanías con líneas geométricas inventadas y lo presentes como verdad ferroviaria.

## 6. Revisión de calidad antes de enseñármelas

- El revisor designado en **DES-08, Codex `gpt-6.1-terra` High**, con contexto de revisión independiente, evalúa las tres opciones: usabilidad, accesibilidad, responsive, factibilidad React/MapLibre, complejidad, rendimiento y semántica ferroviaria. No hace falta que vuelva a revisar toda la arquitectura ya auditada.
- Comprueba que los prototipos **abren realmente** en un navegador local y que sus enlaces, filtros simulados y controles de demostración responden. Los controles que no funcionen deben etiquetarse como concepto, nunca disfrazarse de implementación.
- Genera capturas reales de cada opción en escritorio/móvil con Playwright, asociadas al HEAD y al archivo del prototipo utilizado. Añade un vídeo breve de navegación si hay animación.
- Pasa una ronda de crítica/refinamiento proporcional usando Impeccable; Hallmark se usa solo para criterios complementarios, no una segunda auditoría redundante.
- Evalúa con una matriz común (puntuación 1–5 + evidencia): **map-first, coherencia ferroviaria, legibilidad, originalidad, calidad de iconos, interacción, móvil, accesibilidad, rendimiento estimado y coste de implementación**. Las puntuaciones de calidad visual son juicio profesional; los resultados de tests deben ser verificables.
- Si A/B/C no son sustancialmente distintas en **arquitectura de pantalla**, rediseña las alternativas antes de la entrega.

## 7. Orquestación y matriz vinculante de responsables (DES-00 → DES-09)

### 7.1. Catálogo informado por el propietario; verificación efectiva obligatoria

En esta sesión, el propietario comunica que Orca tiene los siguientes identificadores delegables. **Esta lista es una configuración comunicada, no autorización para inventar disponibilidad ni una validación independiente del catálogo público de los proveedores.** Antes del primer despacho, usa `orca status --json`, `orca skills get orchestration --full`, la ayuda del CLI de esta versión y la configuración efectiva para confirmar que `--model` y `--effort` aceptan exactamente los valores seleccionados. Registra modelo y esfuerzo *solicitados* y *efectivos* por worker. Si alguno falla, detén **solo ese despacho**, verifica alternativas equivalentes del mismo proveedor y registra la sustitución; nunca degradar una revisión decisiva en silencio.

| Función | Identificador completo en Orca | Esfuerzo | Cuándo usarlo |
|---|---|---|---|
| Coordinador permanente | `claude-sonnet-5-5` | `medium` | Estado, dependencias, despachos, síntesis y cierre administrativo |
| Director creativo / diseño sénior | `claude-opus-5-5` | `high` | Brief, anatomía y decisiones A/B/C, coherencia visual, criterio artístico |
| Prototipador frontend aislado | `claude-sonnet-5-5` | `high` | Mockups navegables y componentes conceptuales, con skill `frontend-design` |
| Especialista browser/UX | `gpt-6.1-terra` | `high` | Playwright, capturas, comportamiento móvil, revisión visual independiente |
| Revisor de ingeniería y trazabilidad | `gpt-6.2-sol` | `medium` por defecto; `high` si un hallazgo lo exige | Inventarios, verificaciones técnicas, integridad del paquete, coste de implementar |
| Auxiliar mecánico opcional | `claude-haiku-5-5` | `low` | Metadatos, renombrados e índices; **no** crítica de diseño ni aceptación |

**Exclusiones deliberadas:** no despachar por defecto `claude-fable-5-2`, `gpt-6.2-astra`, `gpt-6-luna` ni versiones antiguas. Solo considerar `gpt-6.2-astra` (`high`, con Claude Opus High como revisor) ante un problema **concreto y demostrado** de factibilidad de renderizado MapLibre, geoespacial o rendimiento que Terra/Sol no resuelvan. `claude-fable-5-2` queda fuera de alcance salvo una futura autorización justificada. No utilizar `max`, `ultra`, `xhigh` ni modelos premium por inercia para tareas visuales.

### 7.2. Tabla de ejecución y revisión cruzada

Los identificadores **DES-00…DES-09 son subtareas internas de discovery**, no tareas MP del backlog ni autorización de Hito 4. Todos los revisores principales son de **proveedor distinto** al ejecutor. La revisión de propuestas se concentra al final de la construcción para evitar tres auditorías duplicadas.

| ID | Encargo, alcance y evidencia exigida | Ejecutor · modelo/esfuerzo | Revisor opuesto · modelo/esfuerzo | Dependencia |
|---|---|---|---|---|
| **DES-00** | Verificar cierre de auditoría, HEAD, worktrees, documentación y restricciones. Entregar `00_BASELINE/STATE.md` con fuentes reales; **no repetir AUD-00→AUD-09** | **Claude** `claude-sonnet-5-5` · `medium` | **Codex** `gpt-6.2-sol` · `medium` | Ninguna; gate de entrada |
| **DES-01** | Arrancar entorno seguro, inspeccionar React/MapLibre y generar capturas Playwright desktop/móvil de todas las vistas y flujos; consola y condiciones de datos registradas | **Codex** `gpt-6.1-terra` · `high` | **Claude** `claude-sonnet-5-5` · `high` | DES-00 |
| **DES-02** | Leer y comparar **solo** Anthropic `frontend-design`, Hallmark e Impeccable. Comprobar compatibilidad, versiones, hooks, permisos y documentación; decidir su uso **sin instalación insegura** | **Claude** `claude-sonnet-5-5` · `medium` | **Codex** `gpt-6.2-sol` · `medium` | DES-00; paralelo seguro con DES-01 |
| **DES-03** | Director de arte: redactar un único brief factual, tres conceptos de composición realmente diferentes (A/B/C), tipos, tokens, criterios anti-genérico y plan de prototipado | **Claude** `claude-opus-5-5` · `high` | **Codex** `gpt-6.1-terra` · `high` | DES-01 + DES-02 |
| **DES-04** | Concepto **A Titanium Control**: prototipo aislado navegable, Live desktop/móvil, ficha tren/estación, History/Explore, estados, variantes de icono y captura | **Claude** `claude-sonnet-5-5` · `high` | **Codex** `gpt-6.1-terra` · `high` **en revisión consolidada DES-08** | DES-03 |
| **DES-05** | Concepto **B Immersive Rail Map**: mismos flujos y fidelity, arquitectura map-first **distinta**, mockups/capturas aislados | **Claude** `claude-sonnet-5-5` · `high` | **Codex** `gpt-6.1-terra` · `high` **en DES-08** | DES-03 |
| **DES-06** | Concepto **C Contemporary Signal**: mismos flujos y fidelity, jerarquía/navegación realmente distintas, mockups/capturas aislados | **Claude** `claude-sonnet-5-5` · `high` | **Codex** `gpt-6.1-terra` · `high` **en DES-08** | DES-03 |
| **DES-07** | Comparar iconos ferroviarios vector 2D, 2.5D y 3D ligero, legibilidad en zoom, estados, orientación, FPS/MapLibre y coste de integración **sin tocar producción** | **Codex** `gpt-6.1-terra` · `high` | **Claude** `claude-opus-5-5` · `high` | DES-03; puede solaparse con prototipado sin editar archivos comunes |
| **DES-08** | Verificar **A/B/C** en navegador real: navegación, capturas, responsive, teclado, reduced motion y estados. Contrastar viabilidad MapLibre. Aplicar una crítica focalizada con Impeccable y controles anti-genérico de Hallmark, pedir y revalidar correcciones | **Codex** `gpt-6.1-terra` · `high` | **Claude** `claude-sonnet-5-5` · `high` | DES-04 + DES-05 + DES-06 + DES-07 |
| **DES-09** | Preparar `INDEX.html`, evidencias BASELINE/CONCEPT, matriz A/B/C, riesgos, plan de integración futura y recomendación. Reconciliar revisiones y **detenerse para elección humana** | **Claude** `claude-sonnet-5-5` · `medium` | **Codex** `gpt-6.2-sol` · `medium` (subir a `high` ante riesgo técnico abierto) | DES-08 |

**Regla de revisión:** DES-04/05/06 no se marcan `APPROVED` únicamente porque generen HTML o porque Claude los vea bonitos. Su revisión formal de proveedor contrario es **DES-08**, sobre artefactos reales. Si una opción falla, vuelve a su implementador; la revisión se repite sobre la versión corregida. DES-09 solo cierra cuando la aceptación de los tres prototipos esté sustentada en pruebas de navegador y dictamen contrario. Ningún worker declara su propia propuesta aprobada.

### 7.3. Orden y economía de tokens

1. **DES-00 primero**. Si AUD-00→AUD-09 sigue activa o no hay informe final, **no lanzar esta discovery** ni abrir worktrees que interfieran; informar del estado y esperar nueva instrucción de inicio. No simular espera autónoma en background.
2. **DES-01 y DES-02** pueden ejecutarse en paralelo si no comparten archivos editables. Captura la app **una sola vez** con dataset/replay documentado; reutiliza ese baseline para A/B/C.
3. **DES-03 antes de crear prototipos**; Opus define tres *arquitecturas de pantalla* y criterios de diferenciación. Terra revisa factibilidad y que A/B/C no sean el mismo dashboard recoloreado.
4. **DES-04/05/06**: cada propuesta trabaja en su carpeta independiente. Usa contextos de worker separados, cada uno con su propia dirección y el brief común, para evitar convergencia estética; no necesitan ejecutarse simultáneamente. Máximo **dos tareas visuales pesadas** a la vez si la máquina lo soporta.
5. **DES-07** comparte la evaluación de iconografía sin generar un segundo rediseño completo. Si el 3D no compensa, documentarlo y descartarlo expresamente.
6. **DES-08** ejecuta **una revisión comparativa real**, no tres rondas de auditoría general. Permite una ronda de cambios y una revalidación; si no converge, documenta defecto y bloqueo en vez de iterar indefinidamente.
7. **DES-09** prepara la exposición comparativa y los enlaces locales y **termina en gate humano**.

Toda tarea registra: nombre del worker, proveedor, modelo y esfuerzo solicitados/efectivos, HEAD, carpeta, comandos y pruebas reales, resultado `PASS/FAIL/SKIP/BLOCKED`, revisor contrario, correcciones y versión del artefacto. Una prueba no ejecutada se anota `NOT RUN`, no `PASS`.

### 7.4. Skills y límites de seguridad

- **Anthropic `frontend-design`:** usar sobre el brief de DES-03 y al crear los prototipos en DES-04/05/06. Si Orca no ofrece integración real con **Claude Design**, no afirmar que se usó: producir prototipos HTML/React **aislados**, documentando exactamente qué habilidad se invocó.
- **Hallmark:** extraer principios de themes/materiales y usar `audit` o lint sobre **prototipos aislados** si la instalación es segura; no lanzar `redesign` sobre `apps/web`.
- **Impeccable:** preferir crítica `critique`, `audit`, `adapt`, `polish` y `detect` sobre los prototipos. **No usar `live`/Apply, hooks no revisados, ni instaladores que desactiven approvals o sandbox.** El README advierte que ciertos flujos de Apply pueden ejecutar CLI en modo bypass. Si no puede usarse sin esos efectos, seguir su metodología pública sin instalar y etiquetar la limitación.
- **Sin instalaciones globales ni modificaciones de permisos.** Revisa también las licencias y el impacto de ejecutar binarios/scripts. Los mocks antiguos rechazados no son fuentes de diseño.

## 8. Entregables y ubicación

Trabaja en **una carpeta de prototipos aislada fuera del árbol productivo** o un worktree de documentación dedicado, sin interferir con la auditoría. Produce al menos:

```text
MADRID_PULSE_DESIGN_DISCOVERY/
  00_BASELINE/              capturas reales + BASELINE.md
  01_DESIGN_BRIEF.md        requisitos visuales y restricciones
  02_TOOL_DECISIONS.md     versiones/licencias/uso real de las tres skills
  A_TITANIUM_CONTROL/      prototipo + desktop/mobile + decisiones
  B_IMMERSIVE_RAIL_MAP/   prototipo + desktop/mobile + decisiones
  C_CONTEMPORARY_SIGNAL/  prototipo + desktop/mobile + decisiones
  03_TRAIN_ICON_STUDY.md  iconos por zoom, coste 2D/2.5D/3D
  04_DESIGN_REVIEW.md      crítica Codex + mejoras Impeccable
  05_COMPARISON.md         matriz A/B/C y recomendación explicada
  06_IMPLEMENTATION_PLAN.md integración futura con componentes React existentes
  07_DISPATCH_REVIEW_LOG.md matriz DES, modelos/esfuerzos reales y pruebas
  INDEX.html                galería local para comparar A/B/C lado a lado
```

El índice deberá enlazar cada propuesta y permitir abrir los prototipos y sus capturas. No publiques imágenes o archivos a GitHub sin aprobación. No declares que existe un archivo sin crearlo ni comprobarlo. Las capturas del producto y de las alternativas deben estar etiquetadas **BASELINE** y **CONCEPT**, respectivamente.

## 9. Gate humano irrevocable

Cuando A/B/C estén listas, entrégame **un resumen conciso con enlaces locales y capturas de las tres**, la comparativa y tu recomendación. **Después DETENTE.**

**Yo decidiré A, B, C o una combinación concreta.** No interpretes el silencio como aprobación. No modifiques `apps/web`, backend, contratos, ramas de implementación, ni inicies el siguiente hito. No hagas push, PR, merge, despliegue, nuevas contrataciones, instalaciones globales o cambios de permisos. No modifiques la política histórica en `docs/audits/hito-03/BASELINE.md`: preserva qué modelos ejecutaron realmente la auditoría GPT-5.6; el catálogo nuevo se documenta como **política futura del diseño** en este discovery, sin reescribir evidencia anterior. Ante bloqueos, documenta hechos y entrega lo que esté verificablemente terminado.

**Primera acción:** confirma el cierre de AUD-00→AUD-09, localiza el HEAD correcto, consume `FRONTEND_UX_AUDIT.md`, arranca el frontend del Hito 3 y captura su estado real. Luego genera A/B/C; **solicita mi elección antes de cualquier desarrollo productivo**.