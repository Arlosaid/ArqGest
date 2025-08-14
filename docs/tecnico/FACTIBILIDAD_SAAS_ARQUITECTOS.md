# Prompt para Análisis de Factibilidad - SaaS para Arquitectos

## Contexto del Proyecto
Desarrollador en México trabajando en un MVP de SaaS para gestión de proyectos arquitectónicos. Este documento analiza el código/proyecto actual de ArcManager y determina la factibilidad de implementar el modelo de negocio propuesto.

Referencias técnicas del repo: multiorganización (`apps/orgs`), planes/suscripciones (`apps/plans`), proyectos/fases/tareas (`apps/projects`), archivos (`apps/files`), configuración (`core/settings.py`).

## Análisis de Costos Reales Verificados (Agosto 2025)

### Infraestructura Mensual Confirmada
- **Railway Hobby Plan**: $90 MXN/mes
  - Incluye: App + Base de datos PostgreSQL
  - Recursos: 8GB RAM, 8 vCPU, 10GB storage, 5GB volumen
  - $5 USD de uso de recursos incluidos
- **Almacenamiento (Cloudflare R2)**: $0 MXN 
  - 10GB completamente gratis por mes
  - Egress (descargas) gratuito sin límite
- **Dominio**: $17 MXN/mes
- **Email transaccional (SendGrid)**: $0 MXN (free tier)
- **Herramientas básicas**: $50 MXN/mes

**COSTO TOTAL MENSUAL: ~$160 MXN**

## Modelo de Pricing Propuesto

### Plan Básico - $199 MXN/mes
**Límites técnicos a implementar:**
- 6 proyectos activos máximo
- 5 usuarios por proyecto máximo
- 3 GB almacenamiento máximo por organización
- Tareas ilimitadas (ventaja competitiva clave)
- Comentarios ilimitados

### Matemática del Negocio
- Break-even: 160 ÷ 199 ≈ 1 cliente
- ~100% margen sobre costos base: 320 ÷ 199 ≈ 2 clientes
- Con 10 clientes: $1,990 MXN ingresos - $160 MXN costos = $1,830 MXN ganancia neta

---

## 1) Factibilidad Técnica (Sí, con condiciones)

**Conclusión:** Sí, es técnicamente factible con la base actual, realizando ajustes puntuales para límites, almacenamiento en R2 y optimizaciones de consultas. El diseño multiorganización ya existe y el módulo de planes/suscripciones sirve como punto central para aplicar restricciones.

Puntos clave que habilitan la factibilidad:
- Multitenancy actual: `Organization` central y todas las entidades clave referencian a la organización (ver `docs/tecnico/ARQUITECTURA_BD.md`).
- Suscripciones/planes: `Plan` y `Subscription` ya existen; se requiere ampliar límites más allá de `max_users`.
- Proyectos/Tareas: modelos con FKs bien definidas e índices básicos (`status`, `priority`, `due_date`).
- Archivos: `ProjectFile` y rutas por organización/proyecto/fase. Falta integrar storage S3-compatible (R2) y contabilización de uso.

Condiciones necesarias:
- Añadir campos de límites a `Plan` y validaciones en `Organization`/servicios.
- Incorporar un modelo de membresía por proyecto para contar usuarios por proyecto (hoy no existe explícito).
- Integrar Cloudflare R2 vía `django-storages` y contabilizar bytes por organización.
- Paginación e índices para soportar tareas/comentarios ilimitados sin degradación (ya hay trabajo en rama `feature-pagination`).

---

## 2) Escalabilidad

- Con Railway Hobby (~$90 MXN) y una sola instancia Django + Postgres gestionado, es razonable soportar 50–100 usuarios activos (no concurrentes intensivos) si:
  - Listados grandes usan paginación y `select_related/prefetch_related`.
  - Hay índices en campos de filtro/orden en `Task`, `Project`, `ProjectFile`.
  - No se hacen agregaciones pesadas por petición (p. ej., sumar bytes de todos los archivos) sin caché/denormalización.
- Punto de upgrade probable:
  - Al superar 100–200 DAU con listados pesados y >10GB en R2, considerar:
    - Mover a plan superior o separar DB y app.
    - Activar caché Redis para vistas/queries costosas.
    - Programar tareas asíncronas ligeras (recuentos, emails) con un worker.
- Implementar límites sin afectar performance:
  - Usar contadores denormalizados por organización (usuarios/proyectos/bytes usados) actualizados en señales/servicios.
  - Validar en capa de servicio/middleware antes de hits costosos a la DB/Storage.

---

## 3) Implementación de Límites (cómo hacerlo)

### 3.1 Proyectos activos (máx. 6 por organización)
- Extender `Plan` con `max_active_projects`.
- En `Organization`, agregar `get_active_project_count()` (consulta con `filter(status='ACTIVE')`).
- Validar en creación/cambio de estado de `Project` (servicio o `clean()`/signal `pre_save`): si `active_count >= plan.max_active_projects` → bloquear.
- Exponer decorador/mixin `check_project_limit` para vistas de creación/activación.

### 3.2 Usuarios por proyecto (máx. 5)
- Introducir `ProjectMembership(project, user, role)` para definir miembros y poder contarlos.
- Extender `Plan` con `max_users_per_project`.
- Validar en alta de membresías/invitaciones: si `members_count >= plan.max_users_per_project` → bloquear.
- Asegurar que solo usuarios de la misma `organization` puedan ser miembros.

### 3.3 Almacenamiento (3 GB por organización)
- Extender `Plan` con `storage_gb` (entero). Umbral en bytes: `storage_gb * 1024^3`.
- En `ProjectFile`, guardar `size_bytes` al subir (del archivo) y actualizar un contador denormalizado `Organization.storage_used_bytes` mediante señales (`post_save`/`post_delete`).
- Validar en subida: si `storage_used_bytes + new_file_size > storage_limit_bytes` → bloquear con mensaje amigable.
- Añadir vistas/widgets para mostrar consumo vs. límite.

### 3.4 Tareas y comentarios ilimitados sin impacto
- Asegurar índices en `Task(status, priority, due_date, phase_id)` y en joins frecuentes.
- Paginación server-side en listados (HTMX/SSR) y filtros con índices.
- En vistas, usar `select_related('phase__project')` y `prefetch_related` para listas.
- Considerar límites UI (p. ej., mostrar 50–100 por página) y filtros predefinidos.

---

## 4) Almacenamiento y Costos (Cloudflare R2)

### 4.1 Integración con el stack actual
- Dependencias: `django-storages[boto3]`.
- Configuración (S3 compatible): `DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'`, `AWS_S3_ENDPOINT_URL` a R2, `AWS_STORAGE_BUCKET_NAME`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_S3_REGION_NAME='auto'`, y `AWS_S3_ADDRESSING_STYLE='virtual'`.
- Reubicar `MEDIA_URL` a la CDN de R2 (o usar Signed URLs si se requiere control fino).

### 4.2 Estrategia de subida/descarga
- Mantener rutas multi-tenant: `organizations/<org_id>/projects/<project_id>/phases/<phase_id>/...`.
- Validar límites antes de subir; almacenar `size_bytes` y actualizar contador.
- Descarga via URL pública o firmada desde R2; registrar métricas básicas (opcional).

### 4.3 Monitoreo de uso de almacenamiento
- Campo denormalizado `Organization.storage_used_bytes` y job periódico de reconciliación que calcule `SUM(size_bytes)` por organización.
- Panel por organización mostrando porcentaje usado.
- Alertas suaves al 80/90/100% del límite.

Nota: Con 3 GB por organización, el free tier (10 GB) de R2 se agota con 4 orgs si todas usan el tope. Planificar pasar a pago cuando el uso agregado supere 10 GB.

---

## 5) Base de Datos y Performance

### 5.1 Multitenancy
- El esquema actual soporta multitenancy por foreign keys a `Organization`. Es eficiente si todas las consultas filtran por `organization` y los índices incluyen ese filtro cuando aplique.

### 5.2 Optimizaciones sugeridas
- Índices:
  - `Project(organization_id, status, created_at)`
  - `Task(phase_id, status, priority, due_date)`
  - `ProjectFile(phase_id, uploaded_at)` y/o `ProjectFile(phase_id, uploaded_by_id)`
- Denormalización:
  - `Organization.storage_used_bytes`
  - (Opcional) `Organization.active_projects_count`
- Consultas:
  - Asegurar `select_related`/`prefetch_related` en listados.
  - Evitar N+1 en templates.

---

## 6) Cambios requeridos en el código (lista concreta)

1. `apps/plans/models.py` (modelo `Plan`): añadir campos
   - `max_active_projects: PositiveIntegerField(default=6)`
   - `max_users_per_project: PositiveIntegerField(default=5)`
   - `storage_gb: PositiveIntegerField(default=3)`
2. `apps/projects/models.py`: introducir `ProjectMembership(project, user, role)` y servicios para alta/baja.
3. `apps/files/models.py`:
   - Añadir `size_bytes: BigIntegerField` en `ProjectFile` y setearlo al guardar.
   - Señales `post_save`/`post_delete` para actualizar `Organization.storage_used_bytes`.
4. `apps/orgs/models.py` (`Organization`):
   - Métodos `get_active_project_count()`, `get_storage_usage_bytes()` (fallback), `can_create_project()`, `can_upload_file(size_bytes)`.
5. `apps/orgs/decorators.py` o `core/mixins.py`:
   - `check_project_limit`, `check_storage_limit`, `check_project_user_limit`.
6. `core/settings.py`:
   - Configurar `django-storages` con R2 como `DEFAULT_FILE_STORAGE` y variables de entorno.
7. Vistas/Templates:
   - Paginación y filtros en listados de tareas/archivos.
   - Mensajería de “límite alcanzado” y UI de uso de almacenamiento.
8. Migraciones y comandos de datos:
   - Migrar nuevos campos/tablas; comando para backfill de `size_bytes` y `storage_used_bytes`.

Nota: Mantener nombres/identificadores en inglés en BD/tablas y código para consistencia y buenas prácticas [[memory:5285757]]. En la documentación/UI, usar español.

---

## 7) Roadmap técnico (priorizado)

1. Límites de plan (backend)
   - Extender `Plan` con `max_active_projects`, `max_users_per_project`, `storage_gb`.
   - Añadir métodos en `Organization` y decoradores/mixins de validación.
2. Membresías por proyecto
   - Crear `ProjectMembership` y flujos de alta/baja; contar miembros.
3. Storage R2 + Contabilización
   - Integrar `django-storages` (R2), mover `ProjectFile` a R2.
   - Añadir `size_bytes` + señales y `Organization.storage_used_bytes`.
4. Performance tareas/comentarios ilimitados
   - Índices, `select_related/prefetch_related`, paginación.
5. UI de límites y alertas
   - Barra/indicador de uso por organización, mensajes de restricción.
6. Observabilidad ligera
   - Logs de límites denegados, métricas básicas (conteos) y job de reconciliación nocturno.

Entrega continua: activar los límites apenas cada pieza esté lista (feature flags simples por settings).

---

## 8) Puntos de riesgo técnicos

- Free tier de R2 (10 GB) insuficiente si >3–4 organizaciones alcanzan 3 GB. Mitigar con monitoreo y plan de upgrade.
- Cálculo de almacenamiento: evitar `SUM(..)` en caliente; usar denormalización + reconciliación.
- Introducción de `ProjectMembership`: migración de datos y adaptación de vistas.
- Validaciones en concurrencia (doble click/condiciones de carrera): reforzar en capa de servicio/DB (locks ligeros o re-chequeo transaccional).
- Límite de proyectos “activos”: definir claramente estados y transiciones para no bloquear cierres/archivos.

---

## 9) Estimación de tiempo (MVP de límites)

- Extender `Plan` + migraciones: 0.5 día
- `ProjectMembership` (modelo, admin, endpoints básicos): 1–1.5 días
- Límite de proyectos activos (validaciones + UI): 0.5 día
- Integración R2 + settings + pruebas: 0.5–1 día
- `size_bytes` + señales + contador por organización + backfill: 1 día
- Índices, paginación, `select_related/prefetch_related`: 0.5 día
- QA/pruebas básicas y ajustes: 0.5 día

**Total estimado:** 3.5–5 días hábiles

---

## 10) Respuesta a la Pregunta Clave

Sí, es técnicamente factible crear un MVP rentable con ~$160 MXN/mes de costos base que genere $1,990+ MXN con 10 clientes, siempre que:
- Se implementen los límites de plan descritos y se controle el uso de almacenamiento por organización.
- Se integre R2 adecuadamente y se monitoree el consumo para anticipar costos al exceder 10 GB globales.
- Se mantenga paginación/índices para listas de tareas/comentarios.

---

## 11) Anexos (operativos)

### 11.1 Variables de entorno sugeridas (R2)
```
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
AWS_S3_ENDPOINT_URL=https://<accountid>.r2.cloudflarestorage.com
AWS_S3_REGION_NAME=auto
AWS_S3_ADDRESSING_STYLE=virtual
```

### 11.2 Dependencias
```
django-storages[boto3]==1.14.4
boto3==1.34.0
```

### 11.3 Migraciones/Comandos
- Ejecutar migraciones y comandos dentro del contenedor Docker cuando aplique [[memory:4971492]].
```
docker-compose exec web python manage.py makemigrations | cat
docker-compose exec web python manage.py migrate | cat
```

---

Nota editorial: Código y nombres de modelos/campos se mantienen en inglés; los textos visibles al usuario final en español [[memory:5285752]].


