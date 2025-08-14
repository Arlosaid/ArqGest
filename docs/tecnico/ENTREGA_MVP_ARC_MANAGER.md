## Entrega MVP — Arc Manager

### Resumen ejecutivo

- **Estado**: Listo para MVP con foco en seguridad, rendimiento y manejo de archivos pesados. Solo falta activar almacenamiento externo (R2/S3) en producción y aplicar migraciones recientes de `files`.
- **Qué se entrega**: Multiorganización, proyectos/fases/tareas, subida de archivos por fase, panel de administración funcional, optimizaciones de queries críticas, endurecimiento de settings de prod.
- **Qué NO es crítico para salir**: Dashboard ejecutivo, notificaciones, Celery, Gantt, reportes de costos, integraciones BIM/API. Se listan como siguientes pasos.

---

## Alcance del MVP (funcionalidades actuales)

- **Organizaciones**: Contexto multitenant por `Organization`.
- **Proyectos y fases**: CRUD completo, plantillas de fases, kanban optimizado.
- **Tareas**: Creación, edición, movimiento entre fases, métricas por estado en detalle de proyecto y kanban.
- **Archivos**: Subida y listado por fase; metadatos persistidos (`size_bytes`, `ext_upper`, `content_type`, `checksum_sha256`), filtros y columnas útiles en Admin.
- **Planes y suscripciones**: Base funcional (sin límites estrictos aún).
- **Seguridad**: Endurecimiento en prod (`DEBUG=False`): SSL/HSTS/cookies seguras, `SECRET_KEY`/`ALLOWED_HOSTS` por entorno, saneo de errores JSON.
- **Rendimiento**: Agregaciones únicas para métricas/kanban, `CONN_MAX_AGE`, `SESSION_SAVE_EVERY_REQUEST=False`, paginación.

---

## Requisitos críticos para lanzamiento (Fase 1)

- **Almacenamiento externo (producción)**
  - Activar `django-storages` con backend S3-compat (Cloudflare R2 recomendado).
  - Ya existen endpoints para URLs firmadas de subida/confirmación; pueden habilitarse después. Para el MVP es suficiente con servir/guardar directo en R2 via `DEFAULT_FILE_STORAGE`.

- **Migraciones de archivos**
  - Aplicar migraciones nuevas en `apps/files` (metadatos e índices): `0003_add_metadata_fields.py` y `0004_rename_*`.

- **Seguridad**
  - `SECRET_KEY` y `ALLOWED_HOSTS` definidos; `DEBUG=False` en prod; cookies seguras/HSTS activas.
  - Respuestas JSON genéricas en errores; logging sin exponer detalles sensibles.

- **Rendimiento**
  - Persistir `CONN_MAX_AGE` (120–300) por entorno.
  - Mantener `SESSION_SAVE_EVERY_REQUEST=False`.

- **Admin operativo**
  - `ProjectFileAdmin` con filtros/búsqueda/columnas para monitorear archivos y tamaños.

---

## Checklist de salida (Go-Live)

- Variables de entorno (producción):

```env
DEBUG=False
SECRET_KEY=...
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com

# Base de datos
DATABASE_URL=postgresql://user:pass@host:5432/db
CONN_MAX_AGE=120

# Almacenamiento (Cloudflare R2 o S3 compatible)
DEFAULT_FILE_STORAGE=storages.backends.s3boto3.S3Boto3Storage
AWS_S3_ENDPOINT_URL=https://<accountid>.r2.cloudflarestorage.com
AWS_STORAGE_BUCKET_NAME=...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_REGION_NAME=auto
AWS_S3_ADDRESSING_STYLE=virtual
AWS_S3_SIGNATURE_VERSION=s3v4

# Validaciones de archivos (opcional)
MAX_FILE_SIZE_MB=600
ALLOWED_EXTENSIONS=PDF,JPG,JPEG,PNG,GIF,DWG,DXF,RVT,SKP,ZIP,RAR,TIFF
```

- Build y arranque (Docker):

```bash
docker compose build --no-cache
docker compose up -d
```

- Comprobaciones y migraciones dentro del contenedor Docker:

```bash
docker compose exec web python manage.py check | cat
docker compose exec web python manage.py migrate --noinput | cat
docker compose exec web python manage.py collectstatic --noinput | cat
```

- Smoke tests funcionales (manuales rápidos):
  - Login/logout.
  - Crear proyecto y tareas; mover tareas en kanban.
  - Subir archivos (10–100MB) y verificarlos en Admin.
  - Navegar listados paginados sin errores.

---

## Operación inicial (Runbook mínimo)

- Acceso admin: validar usuario superusuario y correo de soporte.
- Monitoreo de latencia: revisar warnings de `PerformanceMiddleware` (>2s por request) en logs.
- Monitoreo de almacenamiento: usar Admin para ver `size_bytes` y archivos más pesados por proyecto/fase.
- Backups base de datos: programar snapshots del proveedor (Railway/Postgres gestionado).

---

## KPIs mínimos y monitoreo ligero

- Salud de app: tasa de errores 5xx, latencia P95 de vistas core (kanban, detalle de proyecto, subida de archivos).
- Productividad: tareas creadas/semana, tareas terminadas/semana.
- Operación de archivos: tamaño total por organización, archivos >100MB, top 50 archivos por tamaño.

---

## Riesgos conocidos y mitigaciones

- Servir archivos desde el backend: mitigado al activar R2/S3 (egress fuera del dyno).
- Cálculo de `checksum_sha256` en archivos muy grandes: limitado por `MAX_CHECKSUM_MB`.
- Middlewares que consultan organización en cada request: monitorear y optimizar si aparece en perfiles.
- Logging a archivos dentro del contenedor: aceptable en MVP; planear migración a stdout/stderr.

---

## Siguientes pasos (no críticos para el MVP)

- UX y escalabilidad:
  - Dashboard ejecutivo con KPIs, filtros avanzados y búsqueda global.
  - Notificaciones in-app/email.

- Observabilidad:
  - Migrar logging a stdout/stderr y agregar agregador (p. ej., Loki/ELK).
  - Métricas de requests y DB (tracing ligero).

- Procesamiento asíncrono:
  - Celery/RQ para emails y reportes; tareas programadas (suscripciones, reconciliación de storage).

- Diferenciales de producto:
  - Gantt simple, reportes automáticos de progreso/costos.
  - Integración inicial BIM/Revit (import/export), webhooks y API pública básica.

---

## Anexos

- Referencias:
  - `docs/tecnico/AUDITORIA_TECNICA_ARC_MANAGER.md` (ajustado a MVP y siguientes pasos)
  - `docs/tecnico/MEJORAS_BACKEND_FASE_1.md` (detalle de cambios aplicados)

- Endpoints relacionados con archivos (ya implementados):
  - `POST files:upload_file` (subida estándar)
  - `POST files:presign_upload` y `POST files:confirm_upload` (URLs firmadas; habilitar cuando se requiera subida directa cliente→R2)

- Notas de configuración:
  - Mantener `CONN_MAX_AGE` entre 120–300 según el entorno.
  - `SESSION_SAVE_EVERY_REQUEST=False` por defecto.


