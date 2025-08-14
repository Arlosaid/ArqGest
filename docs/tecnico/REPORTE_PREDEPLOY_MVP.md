## Reporte Pre-Deploy MVP — Arc Manager

### 1) Estado general (listo para MVP con ajustes menores)

- Autenticación y multiorganización: estable. Middlewares de acceso y contexto de organización operativos.
- Proyectos/Fases/Tareas: vistas con `select_related/prefetch_related`, agregaciones y paginación. Kanban optimizado.
- Archivos: metadatos persistentes (`size_bytes`, `ext_upper`, `content_type`, `checksum_sha256`), validaciones básicas en servidor, endpoints para URLs firmadas (opcional R2/S3) y Admin con columnas útiles.
- Seguridad: endurecimiento activado con `DEBUG=False` (HSTS, cookies seguras, SSL redirect, etc.). Manejo de errores JSON saneado.
- Rendimiento: `CONN_MAX_AGE`, `SESSION_SAVE_EVERY_REQUEST=False`, cache Redis configurada (opcional), middleware de performance.

### 2) Cambios recientes relevantes (esta rama)

- `apps/files`:
  - Modelo `ProjectFile`: metadatos e índices agregados. Migraciones `0003` y `0004` incluidas.
  - Vistas: validación de tamaño/tipo, cálculo opcional de checksum limitado, endpoints `presign` y `confirm_upload` para R2/S3 bajo `ENABLE_STORAGES=true`.
  - Admin: `ProjectFileAdmin` registrado con filtros, búsqueda y columnas de tamaño.
- `projects/views.py`: corrección en `ProjectKanbanSelectorView` para obtener proyectos por tareas asignadas cuando no es admin.
- `core/settings.py`: activación condicional de `django-storages` y configuración segura por entorno.
- `Dockerfile`: script de inicio ahora migra y arranca con Gunicorn; se elimina comando inexistente `create_database`.

### 3) Posibles issues/bugs y acciones

- Almacenamiento externo (R2/S3): listo en código pero desactivado por defecto. Acción: configurar variables de entorno y/o `DEFAULT_FILE_STORAGE` en prod.
- Migraciones pendientes: aplicar `apps/files` 0003 y 0004 en prod.
- Cálculo de checksum: limitado por `MAX_CHECKSUM_MB` para no impactar CPU; para archivos >50MB no se calcula (diseño intencional).
- `orgs/models.Organization.get_subscription_limits`: placeholders para proyectos/storage. No bloquea MVP, pero pendientes para límites duros.
- URL raíz: `core/urls.py` incluye `files.urls` en `''`. Revisado: rutas no colisionan con `root_redirect`. OK.
- Redis opcional: si no hay Redis, ajustar `REDIS_URL` o deshabilitar cache de sesiones en entornos sin Redis.

### 4) Checklist de despliegue a producción

1. Variables de entorno (mínimas)
   - `DEBUG=False`
   - `SECRET_KEY` (no vacío)
   - `ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com`
   - `DATABASE_URL=postgresql://...`
   - `CONN_MAX_AGE=120`
   - Correo (si se usa SES): `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SES_REGION`, `DEFAULT_FROM_EMAIL`
   - Redis (opcional): `REDIS_URL`
   - R2/S3 (opcional):
     - `ENABLE_STORAGES=true`
     - `DEFAULT_FILE_STORAGE=storages.backends.s3boto3.S3Boto3Storage`
     - `AWS_S3_ENDPOINT_URL=https://<accountid>.r2.cloudflarestorage.com`
     - `AWS_STORAGE_BUCKET_NAME=...`
     - `AWS_ACCESS_KEY_ID`/`R2_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`/`R2_SECRET_ACCESS_KEY`
     - `AWS_S3_REGION_NAME=auto`, `AWS_S3_ADDRESSING_STYLE=virtual`, `AWS_S3_SIGNATURE_VERSION=s3v4`
   - Validaciones de archivos (opcional): `MAX_FILE_SIZE_MB`, `ALLOWED_EXTENSIONS`

2. Build y arranque (Docker)
   - `docker compose build --no-cache`
   - `docker compose up -d`

3. Migraciones (dentro del contenedor)
   - `python manage.py migrate --noinput`
   - `python manage.py collectstatic --noinput`

4. Smoke tests
   - Login/logout.
   - Crear proyecto/fases/tareas; mover tareas en kanban.
   - Subir archivos 10–100MB; verificar en Admin y listado por fase.
   - Revisar paginación en listas grandes.

### 5) Recomendaciones para día 1 de producción

- Activar R2/S3 inmediatamente para evitar servir archivos desde el dyno.
- Monitoreo liviano: revisar logs de `PerformanceMiddleware` (>2s) y errores.
- Panel Admin: usar filtros/columnas en `ProjectFile` para ver archivos pesados.

### 6) Roadmap corto post-MVP

- Límites de plan: `max_active_projects`, `max_users_per_project`, `storage_gb` con validaciones.
- Membresías por proyecto (`ProjectMembership`) para conteo real de miembros.
- Contador denormalizado `Organization.storage_used_bytes` + reconciliación nocturna.
- URLs firmadas para descarga y subida directa (frontend) con confirmación.

---

Conclusión: El código está listo para despliegue de MVP, siempre que se apliquen migraciones de `files`, se configuren variables de entorno seguras y se habilite almacenamiento externo en producción. La UX principal (proyectos/fases/tareas/archivos) funciona con validaciones y paginación; seguridad y rendimiento endurecidos para prod.


