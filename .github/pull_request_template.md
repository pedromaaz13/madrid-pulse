## Tarea

`MP-0XX` — <nombre de la tarea, igual que en `docs/TASKS.md`>

## Resumen

<qué hace este PR, en relación con el entregable definido en `docs/TASKS.md`>

## Agente ejecutor / revisor

- Ejecutor: Claude Code / OpenAI Codex
- Revisor asignado: el agente contrario (ver `docs/TASKS.md`)

## Checklist antes de pedir revisión

- [ ] Tests relevantes ejecutados realmente (no solo "deberían pasar") — adjuntar salida o referencia al log.
- [ ] Lint y typecheck en verde.
- [ ] Migraciones validadas (aplicación + rollback), si aplica.
- [ ] Verificación de licencia/fuente de datos, si el cambio toca ingestión, contratos o atribución.
- [ ] `docs/TASKS.md` actualizado (estado + evidencia).
- [ ] `docs/STATUS.md` actualizado (checklist + bitácora).
- [ ] `docs/CHANGELOG.md` actualizado con lo realmente implementado.
- [ ] Si hay cambio de arquitectura: ADR nuevo o actualizado en `docs/adr/`, y reflejado en `docs/DECISIONS.md`.
- [ ] Sin commits con `Co-authored-by` de agentes de IA (ver `AGENTS.md`).

## Evidencia de verificación

<pegar salida de tests/comandos relevantes, o enlazar al artefacto de evidencia>

## Notas para el revisor

<qué casos límite revisar con especial atención, qué no se cubrió y por qué>
