# DEPLOYMENT_OPTIONS.md — Comparativa de infraestructura

Fecha: 2026-11-24. Precios y límites leídos en documentación oficial el 2026-11-24 (enlaces al final); lo que no pude confirmar está marcado **(verificar)**. Supuestos de carga: colector 24/7 (≈19 MB de RSS), API de bajo tráfico, base caliente con purga (≈258 MB/día sin purga, proyección), Parquet ≈19 MB/día, bajada ≈0,9 GB/día (`docs/evidence/mp-021-coste-colector-continuo.md`).

| Criterio | 1. GitHub Pages + servicios externos | 2. Cloudflare Pages + Railway | 3. Render | 4. VPS + Docker Compose |
|---|---|---|---|---|
| Servicios | Pages (estático) + un host para API/colector/BD (= otra de las opciones) | Pages + Railway (API, colector, PostgreSQL) | web service (API) + worker (colector) + Postgres + frontend estático | 1 VPS: Caddy, API, colector, PostGIS, cron |
| MVP 0 (demo estático) | **Sí, 0 €**; sin servidor | Sí, 0 € | Sí (sitio estático) | Innecesario |
| MVP 1 conectado | Solo con un host externo y **CORS** (origen distinto) | Origen distinto: CORS o proxy; añade dos proveedores | Tres servicios de pago | **Mismo origen** (diseño del código), sin CORS |
| Colector continuo | Depende del host | Sí (servicio siempre activo) | Solo con worker **de pago**; el plan gratuito de web se duerme tras 15 min | Sí (`systemd`/`restart: always`; plantillas ya existentes) |
| PostgreSQL persistente | No aplica | Volumen (máx. 5 GB en Hobby); PostGIS: usar imagen propia/plantilla **(verificar)** | Postgres gratis **caduca a los 30 días** y 1 GB; de pago ≈6–7 USD/mes **(verificar importe)**; PostGIS **(verificar)** | Contenedor PostGIS del repo, volumen del VPS (40 GB típicos) |
| Adaptación de código | Dockerfiles, CORS, purga | Dockerfiles, CORS/proxy, purga | Dockerfiles, purga, worker | Dockerfiles, compose, purga |
| Coste mensual aprox. | 0 € (solo front) | Railway Hobby: 5 USD/mes con 5 USD de uso incluido; uso a 10 USD/GB·mes de RAM, 20 USD/vCPU·mes, 0,15 USD/GB·mes de volumen, 0,05 USD/GB de salida. Estimación: BD 0,5 GB + API 0,3 GB + colector 0,2 GB de RAM, ~0,2 vCPU y 3 GB de volumen ≈ 14–15 USD/mes. Pages 0 | web 7 USD + worker ≈7 USD + Postgres ≈7 USD ≈ 20–21 USD/mes **(verificar worker y Postgres)** | Hetzner CX22 ≈ 3,79 €/mes sin IVA según anuncio de 2024 **(verificar precio vigente)**; con copias de seguridad y margen: 5–8 €/mes. Dominio opcional aparte |
| Límites gratuitos | Pages: sitio ≤1 GB, ancho de banda 100 GB/mes (blando), 10 builds/h blandos (no aplican con Actions propio), despliegue ≤10 min | Pages: 20 000 ficheros, 25 MiB/fichero (plan gratuito) | Web gratis se duerme; Postgres gratis expira | — |
| Riesgo de suspensión | Bajo (estático) | Cuota de créditos: si se agota el uso incluido se factura el exceso; volumen de 5 GB se llena en ~19 días sin purga | Alto en gratuito (sueño, caducidad) | Bajo; depende de mantener el VPS |
| Observabilidad | Ninguna | Logs y métricas de la plataforma | Logs de la plataforma | Logs de Docker/journald; añadir monitor externo gratuito de disponibilidad |
| Seguridad | Estático | Red privada entre servicios; secretos en la plataforma | Igual | Firewall solo 22/443, BD sin puerto público, usuario no root, actualizaciones a cargo del propietario |
| Backups / recuperación | n/a | Copias de volumen: verificar si incluidas en Hobby **(verificar)**; `pg_dump` propio | Copias solo en planes de pago | `pg_dump` nocturno + copia externa; snapshots del proveedor (≈+20 %) **(verificar)** |
| CI/CD | Actions → Pages | Actions → Pages + deploy de Railway desde Git | Despliegue desde Git | Actions → SSH/`docker compose pull` |
| Mantenimiento | Mínimo | Bajo | Bajo-medio | Medio (parches, disco, TLS vía Caddy) |

## Recomendación
- **MVP 0: GitHub Pages**, despliegue por GitHub Actions desde el propio repositorio. 0 €, sin cuenta nueva ni procesos. Cloudflare Pages solo si se necesita cabeceras personalizadas o dominio gestionado.
- **MVP 1: VPS económico + Docker Compose + Caddy**, frontend y API bajo un mismo origen, copias externas. Es lo más barato, lo más fiel al diseño existente (proxy mismo origen, `systemd`/restart ya preparado) y el único sin riesgo de sueño ni caducidad. **Fallback con menos operación:** Railway (≈15 USD/mes) si prefieres no administrar un servidor; exige CORS o proxy y vigilar el volumen de 5 GB.
- Descartado: Render por coste y límites del plan gratuito para un colector continuo; Kubernetes/microservicios, innecesarios.
- Contratar cualquiera de ellos es decisión tuya (coste y cuenta).

## Fuentes
- [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)
- [Cloudflare Pages limits](https://developers.cloudflare.com/pages/platform/limits/) y [cambio a 100 000 ficheros en planes de pago](https://developers.cloudflare.com/changelog/post/2026-01-23-pages-file-limit-increase/)
- [Railway plans](https://docs.railway.com/pricing/plans) y [pricing](https://railway.com/pricing.md)
- [Render free tier](https://render.com/docs/free), [instancias Postgres](https://render.com/docs/postgresql-legacy-instance-types)
- [Hetzner Cloud](https://www.hetzner.com/cloud/regular-performance/) y [anuncio CX](https://www.hetzner.com/pressroom/new-cx-plans/)
- [Política de uso de teselas de OSM](https://wiki.openstreetmap.org/wiki/Tile_usage_policy)
