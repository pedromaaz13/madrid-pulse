# Madrid Pulse en Orca · Hito 3 — Kit consolidado (v2)

**Esta versión conserva íntegramente el material y las tareas del kit anterior.** Incluye los documentos nuevos para corregir trazabilidad de posición, movimiento entre polls, cobertura de todo Cercanías Madrid y criterios de cierre medibles.

## Uso en Orca

1. Descomprime `Madrid-Pulse-Orca-Hito3-v2.zip` junto al clon. No sustituyas a ciegas una instalación anterior ni copies los datos binarios a Git.
2. En el **mismo chat de Claude coordinador**, comparte la ruta absoluta de esta carpeta descomprimida y pega el texto completo de `docs/hitos/hito-03/PROMPT-UNICO-ORCA.md` (es el único prompt que autoriza MP-016→MP-022).
3. Claude leerá `PROMPTS.md` original y `PLAN-Y-ACEPTACION.md`, y aplicará también el nuevo anexo y matriz. Lanzará workers y revisores mediante Orca, sin que el propietario tenga que abrir chats individuales.
4. Al cerrar, recibe el dossier de auditoría local, rama y commits; el push, PR y merge quedan reservados para autorización posterior conforme a la política vigente.

## Documentos principales

| Ruta | Papel |
|---|---|
| `docs/hitos/hito-03/PROMPT-UNICO-ORCA.md` | **Única instrucción actualizada**, para copiar en Orca. |
| `docs/hitos/hito-03/PROMPTS.md` | Protocolo original detallado de orquestación y recuperación. |
| `docs/hitos/hito-03/PLAN-Y-ACEPTACION.md` | Reparto **original** MP-016→MP-022, modelos y dependencias. |
| `docs/hitos/hito-03/ANEXO-CRITICO-POSICION-Y-RELOJ.md` | Diferencia raw/matched/rendered, reloj de cliente, frescura y pruebas. |
| `docs/hitos/hito-03/MATRIZ-CIERRE-MADRID.md` | Requisitos verificables por tarea y gates de toda la red. |
| `docs/hitos/hito-03/SIGUIENTES-HITOS.md` | Plan posterior AV/LD/MD y despliegue, **no autorizado**. |
| `docs/hitos/hito-03/diseno/` | Prototipo, escritorio, móvil, estado sin señal y Explore, interacciones. |
| `docs/hitos/hito-03/referencia/` | Auditoría de live, experiencia y arquitectura analítica. |
| `data/hito-03/` | Replay 1532/1533, GTFS y parche original, fuera de Git. |
| `instalar.py` | Instalador conservador en worktree no-main (primero `--comprobar`). |

**Compatibilidad de actualización:** no se han cambiado los archivos instalados del kit anterior (`PROMPTS.md`, `PLAN-Y-ACEPTACION.md`, etc.). Los nuevos documentos son aditivos: el instalador puede copiar solo lo nuevo cuando el kit anterior ya está presente, preservando cualquier edición local y avisando de conflictos reales.
