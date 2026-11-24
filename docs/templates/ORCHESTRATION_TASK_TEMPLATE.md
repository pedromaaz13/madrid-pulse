# Plantilla de tarea para Orca (H4+)

Una tarea = un spec autocontenido. Rellena todos los campos; un campo vacío bloquea el despacho.

```yaml
id: H4-xx
titulo:
prioridad: P0|P1|P2          esfuerzo_relativo: S|M|L
hallazgos_que_cierra: [FR-xx]
worktree: path:<WORKTREES>/<nombre>   # rama desde el HEAD indicado
base_head: <sha>            # y baseline de regresión: beb9434
dependencias: [H4-xx]       # solo tareas ya aprobadas (APPROVED) o gates humanos listados
ejecutor:
  agente: claude|codex
  modelo: <id exacto del catálogo>          # p. ej. gpt-6.2-astra
  esfuerzo: low|medium|high                 # xhigh solo con motivo escrito
  motivo_de_escalado: ""                    # obligatorio si esfuerzo > high o si es Opus/Astra
revisor:                                    # proveedor CONTRARIO
  agente:  modelo:  esfuerzo:
  tiene_navegador: si|no                    # si la tarea tiene criterio visual
permisos:
  puede_editar: [rutas]
  no_puede: [push, PR, merge, git config, bases persistentes, 127.0.0.1:5433, instalar software, ajustes del sistema]
entorno_aislado:
  postgres: contenedor desechable propio, puerto <libre>, migraciones 0001+0002 desde cero, destruir al terminar
  dsn_verificado_antes_de_escribir: si
pruebas_de_aceptacion:                      # una por criterio, con comando
  - id: AC-1
    comando:
    resultado_esperado:
    falla_en_beb9434: si|no(justificar)     # regresión antes/después
validacion_de_arneses: constantes citadas archivo:línea; fixtures con SHA-256; usa funciones de producción
evidencia_exigida: [comandos+salida, commit, capturas/JSON si hay interacción visual]
limites_conocidos_a_declarar: []
```

## Preámbulo obligatorio del spec (copiar tal cual)
1. Identidad Git exclusiva `Pedro Matute <pedromaaz13@gmail.com>`, sin `Co-authored-by`; nunca `git push`/PR/merge; no cambies `git config`.
2. Antes de ejecutar nada con escritura, comprueba y escribe en tu informe: DSN, host, puerto, base y que NO es `127.0.0.1:5433`. Usa solo tu contenedor desechable.
3. No instales software ni cambies permisos del sistema; si falta una capacidad (p. ej. navegador), dilo y para.
4. Una interacción de navegador solo cuenta si la ejecutaste y guardaste el artefacto.
5. Si usas un script de diagnóstico, cita cada constante con `archivo:línea` de producción y confirma que coincide.

## Devolución (worker_done)
Qué hiciste · comandos reales y resultado (PASS/FAIL/NO EJECUTADO) · límites declarados · commit · modelo/esfuerzo que declara tu runtime (informativo) · qué debe verificar el revisor.

## Plantilla del dictamen del revisor
```
veredicto: APPROVED|CHANGES_REQUESTED|BLOCKED     head_revisado: <sha>
bloqueantes (B): [{id, evidencia, qué corregir}]
recomendaciones (A): [{id, texto}]
reproducido_por_mi: [comando → resultado]
no_pude_verificar: [..., motivo]                  # p. ej. sin navegador
```
Ronda 2: solo verificar la lista B de la ronda 1.
