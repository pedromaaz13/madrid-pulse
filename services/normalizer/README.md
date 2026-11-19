# services/normalizer

Capa de normalización: transforma el payload crudo capturado por `services/collector` al contrato canónico interno (`packages/contracts`), aplicando las reglas de `packages/quality`. Ver `docs/ARCHITECTURE.md` y `docs/DATA_QUALITY.md`.

**Vacío intencionadamente.** Su implementación se reparte entre **MP-005** (contrato canónico) y **MP-008** (quality engine) — este directorio aloja la capa de orquestación que las conecta, a definir en la tarea correspondiente. No añadir código aquí sin autorización — ver `docs/TASKS.md` y `docs/STATUS.md`.
