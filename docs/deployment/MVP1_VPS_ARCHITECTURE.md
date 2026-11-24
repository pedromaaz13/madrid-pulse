# MVP1_VPS_ARCHITECTURE.md — Servicio Live en VPS (diseño; sin contratar)

Fecha: 2026-11-24. Candidata preferida: VPS + Docker Compose + Caddy + FastAPI + collector + PostgreSQL/PostGIS + frontend estático.

## Diseño
```text
Internet ─443─► Caddy (TLS automático; HTTP→HTTPS)
                 ├─ /           → /srv/web (dist del frontend)
                 ├─ /tiles/*    → PMTiles propio (range requests) [opcional]
                 └─ /api/v1/*   → api:8000 (FastAPI, uvicorn, 2 workers)
red interna 'backend' (sin puertos publicados):
   api ──► postgres (PostGIS 17-3.5, volumen nombrado)
   collector ──► postgres ; collector ──HTTPS──► gtfsrt.renfe.com (30 s)
   archiver (cron del host o contenedor): snapshotter diario → /var/lib/madrid-pulse/parquet ; pg_dump nocturno → copia externa
Host: ufw solo 22/80/443; SSH por clave; usuario no root; unattended-upgrades.
```
Servicios Compose: `caddy`, `api`, `collector`, `postgres`, `archiver`. Secretos en `.env` del host (0600, fuera de Git); DSN sin valores por defecto (tarea MP-023). Reinicio: `restart: unless-stopped` (equivalente a las unidades `systemd` ya existentes en `infra/operate/`).

## Dimensionado de almacenamiento: reconciliación 258 MB/día vs 19 MB/día
No son dos datos distintos ni se suman: son **las mismas ≈405 000 filas/día** (`docs/evidence/mp-021-coste-colector-continuo.md`) en dos representaciones:

| | PostgreSQL caliente | Parquet ZSTD frío |
|---|---|---|
| Qué es | filas + índices + cargas útiles en almacenamiento por filas | columnar comprimido, particionado por día |
| Tamaño/día | ≈258 MB (≈640 B/fila) | ≈19 MB (≈47 B/fila) |
| Ratio | — | ≈13,6 : 1 (medido ≈13 : 1 en MP-009 y MP-021) |
| Vida | **transitoria**: se purga tras archivar | **permanente** (retención 12 meses propuesta, DEC-004) |

Ambas cifras son **proyecciones lineales de 21 ciclos** (~10 min) y probablemente un techo (tráfico nocturno menor). Se vuelven a medir con 24–72 h (D-18/H4-07) antes de fijar retención.

Presupuesto de disco (VPS de 40 GB), con supuestos explícitos:

| Concepto | Cálculo | GB |
|---|---|---|
| Sistema + imágenes Docker | estimación | 8 |
| BD caliente, 7 días | 258 MB × 7 ≈ 1,8 GB × 1,5 (índices extra, *bloat*, WAL) | 2,7 |
| Archivo frío, 12 meses | 19 MB × 365 | 6,9 |
| Copias locales | `pg_dump` comprimido + margen (**medir en D-16**) | 5 |
| **Total** | | **≈22,6 de 40 (margen ≈43 %)** |

Sin purga la BD crecería ≈7,5 GB/mes y llenaría el disco en pocos meses: **la purga (D-14) es obligatoria**. Descarga de datos ≈0,9 GB/día ≈27 GB/mes frente a ≥20 TB incluidos en Hetzner UE (verificar plan concreto). CPU ≤3 % de un núcleo y 19 MB de RSS en el colector.

## Backups y recuperación
`pg_dump` nocturno (+ archivo Parquet ya inmutable) a un almacenamiento externo (otro proveedor o bucket), retención 7 diarios + 4 semanales; **restauración probada** en BD vacía (criterio de D-16). Opcional: snapshots del proveedor (≈+20 % del precio del servidor; **verificar**). RPO ≈24 h; RTO objetivo ≈1 h con el compose versionado.

## Seguridad
Puertos 5432/8000 jamás publicados; Caddy único expuesto; rate limit por IP (Caddy `rate_limit` o plugin; **verificar** módulo) y `/docs` desactivado; cabeceras de seguridad; secretos solo en el host y en Actions; sin claves en `VITE_*`; actualizaciones automáticas de seguridad; monitor externo gratuito de disponibilidad sobre `/api/v1/health`; logs de Docker con rotación.

## Observabilidad y mantenimiento
Logs `json-file` rotados; `healthcheck` de Compose; alerta si `health` marca feeds caducados; revisión mensual de disco y parches (≈1 h/mes). Es la parte que sí cuesta tiempo frente a Railway.

## Coste (precios oficiales leídos el 2026-11-24; discrepancias marcadas)

| Concepto | VPS Hetzner + Compose | Railway Hobby |
|---|---|---|
| Cómputo | CX23 (2 vCPU/4 GB/40 GB) ≈ 5,99–6,49 €/mes sin IVA (**verificar**) → ≈7,3–7,9 € con 21 % IVA | 5 USD/mes con 5 USD de uso incluido; uso estimado BD 0,5 GB + API 0,3 + colector 0,2 + ≈0,2 vCPU = ≈14 USD + volumen 0,15 USD/GB |
| Almacenamiento | incluido (40 GB) | volumen **máx. 5 GB en Hobby**: el archivo frío (6,9 GB/año) no cabe → R2/otro |
| Copias | snapshots ≈+20 % (**verificar**) o copia externa ≈0–1 € | no confirmado (**verificar**); `pg_dump` propio |
| Tráfico | ≥20 TB incluidos (UE) | salida 0,05 USD/GB |
| Teselas | PMTiles propio: 0 € adicional (o 20–30 USD/mes si proveedor con clave) | ídem |
| Dominio | ≈10–15 €/año (supuesto) | ídem |
| **Total mensual aprox.** | **≈ 8–11 €** | **≈ 14–16 USD + almacenamiento frío externo** |

**Recomendación:** VPS + Compose. Ventajas: más barato, un solo origen (sin CORS), almacenamiento suficiente, colector sin cuotas. Coste: operarlo tú (parches, backups). Railway queda como alternativa si no quieres administrar un servidor, con el límite de 5 GB que obliga a sacar el archivo frío a un almacenamiento de objetos (cambio de código en `apps/api/history.py`).

No se contrata nada sin tu autorización.
