# DEVELOPMENT.md

Qué se necesita en local y qué requiere un servicio cloud, y en qué fase se activa cada uno. Nada de esto está contratado ni configurado durante MP-001 — este documento es la referencia para cuando corresponda.

## Ahora (disponible/usable desde MP-001)

```text
GitHub (repositorio ya existente: pedromaaz13/madrid-pulse)
Orca IDE
Claude Code
OpenAI Codex
```

## Requisitos locales (a partir de MP-003/MP-006, no antes)

```text
Docker Desktop / Docker Engine
Python 3.12 (fijado en MP-007/DEC-019; sin gestor adicional: venv + requirements.txt)
Node.js 22.13.1 (fijada en CI y DEC-032)
PostgreSQL + PostGIS (local, vía docker-compose en infra/docker/)
DuckDB (embebido, sin servicio; versión fijada en MP-009/DEC-021, `requirements.txt`)
```

El colector (`services/collector/`, MP-007) es el primer componente que escribe en
PostgreSQL desde Python y necesita un entorno aislado:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Madrid Pulse puede desarrollarse **completamente en local** hasta el final de la validación del colector (MP-001 a MP-007), sin pagar nada.

## Después de validar el colector (post-MP-007)

```text
Cuenta Cloudflare
Bucket R2 (histórico frío)
```

Se activa solo cuando el volumen real de ingesta (medido en MP-007) confirme que el modelo de almacenamiento híbrido (ver `docs/DECISIONS.md`, DEC-011) es necesario y dimensionable.

## Antes de producción (post-MP-015, fuera del alcance actual)

```text
PostgreSQL gestionado (Supabase Pro u equivalente)
Hosting para FastAPI/collector (Render / Railway / Fly u equivalente)
Dominio propio
Monitorización
```

Ninguno de estos se ha contratado a 2026-11-25 (backlog MP-001 a MP-022); la elección de hosting es gate humano (`HG-HOSTING`, ver `docs/deployment/`). La estimación de coste orientativa de la investigación (no un presupuesto garantizado) es de **25–40 USD/mes** en operación 24/7 de producción: ~25 USD de Postgres gestionado, ~7 USD de un servicio Python pequeño, potencialmente 0 USD de R2 mientras se mantenga en el free tier.

## Principio de activación de servicios

No se contrata ni habilita ningún recurso externo sin:

1. Validación empírica previa de que es necesario (no por anticipación).
2. Autorización explícita del propietario del repositorio.
3. Registro de la decisión en `docs/DECISIONS.md` y, si implica arquitectura, un ADR en `docs/adr/`.

## Entorno de agentes

Claude Code y Codex operan dentro de Orca IDE con permisos potencialmente amplios por defecto — verificar los ajustes de autonomía antes de ejecutar comandos que toquen credenciales, red externa o infraestructura real. Ningún agente debe compartir credenciales ni datos privados; las pruebas contra feeds externos (MP-003) deben respetar los límites y condiciones de servicio documentados en `docs/legal/DATA_SOURCES.md`.
