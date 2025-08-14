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



---

# Prompt Técnico Avanzado - Análisis de Performance y Archivos

## Contexto
Necesito que analices mi proyecto ArcManager para implementar optimizaciones específicas para arquitectos mexicanos. Este es un análisis técnico complementario enfocado en performance, tipos de archivos pesados y costos operativos reales.

## Arquitectura de archivos específica para arquitectos

Debo soportar archivos típicos de estudios de arquitectura mexicanos:
- **AutoCAD (.dwg, .dxf)**: 5-50MB por archivo
- **Revit (.rvt)**: 100-500MB por archivo (MUY CRÍTICO)
- **SketchUp (.skp)**: 10-100MB por archivo  
- **PDFs de planos**: 5-20MB por archivo
- **Imágenes técnicas (.jpg, .png, .tiff)**: 2-15MB por archivo
- **Archivos comprimidos (.zip, .rar)**: Pueden contener múltiples planos

**Pregunta clave**: ¿Mi actual sistema de archivos (`apps/files`) puede manejar eficientemente archivos de 100-500MB sin impactar performance o disparar costos de Railway?

## Análisis de Performance Crítico

### 1. **Consultas que podrían ser costosas**
Analiza si estas consultas pueden causar problemas de RAM/CPU con mi esquema actual:

```sql
-- Suma de storage por organización (puede ser pesada)
SELECT organization_id, SUM(size_bytes) FROM project_files 
GROUP BY organization_id;

-- Listado de archivos con metadata (N+1 potential)
SELECT * FROM project_files pf 
JOIN projects p ON pf.project_id = p.id 
JOIN organizations o ON p.organization_id = o.id;

-- Búsqueda de archivos por tipo/tamaño
SELECT * FROM project_files 
WHERE file_type IN ('.dwg', '.rvt') 
ORDER BY size_bytes DESC;
```

### 2. **Upload de archivos grandes**
¿Necesito implementar upload chunking para archivos de 200-500MB o Django + Railway + R2 lo manejan nativamente sin problemas?

### 3. **Memory usage scenarios**
Con 50 usuarios subiendo/descargando archivos de 100MB simultáneamente, ¿mi configuración actual de Railway Hobby (8GB RAM) es suficiente?

## Admin Panel Operativo

Necesito monitorear desde Django Admin:

### Métricas críticas por organización:
- Storage usado vs límite (3GB)
- Archivos más pesados por org
- Organizaciones cerca del límite de storage
- Uploads fallidos (archivos muy grandes)
- Proyectos activos vs límite (6 máximo)

### Alertas operativas:
- Orgs usando >80% de su storage
- Archivos individuales >100MB
- Queries de BD >2 segundos
- RAM usage >6GB en Railway

¿Puedes revisar mi actual estructura de admin y sugerir los AdminModels específicos que necesito?

## Optimizaciones de Costos

### Railway Resource Usage:
Con archivos pesados, estas operaciones podrían disparar costos:
- **RAM spike** durante uploads grandes
- **CPU intensive** al procesar/validar archivos
- **I/O heavy** al transferir a R2

### Cloudflare R2 Scaling:
- Free tier: 10GB total
- Después: $0.015/GB/mes  
- Con 10 clientes usando 3GB c/u = 30GB = ~$8 MXN extra/mes

¿Mi código actual maneja eficientemente estas cargas sin desperdiciar recursos?

## Análisis Específico Requerido

### 1. **File Model Optimization**
Revisa `apps/files/models.py` y determina:
- ¿Faltan índices para consultas de storage por org?
- ¿El campo `size_bytes` se actualiza correctamente?
- ¿Las señales post_save/post_delete son eficientes?

### 2. **Upload Views Performance**
Analiza las vistas de upload:
- ¿Validan tamaño ANTES de procesar?
- ¿Usan streaming para archivos grandes?
- ¿Manejan timeouts correctamente?

### 3. **Storage Backend Integration**
¿La integración actual con archivos soporta:
- URLs firmadas para seguridad
- Upload directo a R2 (bypass Django)
- Compresión automática de imágenes
- Validación de tipos de archivo por extensión

### 4. **Database Query Optimization**
Identifica consultas que podrían ser lentas con:
- 1000+ archivos por organización
- Joins complejos para listados
- Agregaciones de storage en tiempo real

## Performance Benchmarks

¿Puedes estimar con mi código actual:

### Límites de concurrent users:
- **Uploads simultáneos**: ¿Cuántos archivos de 100MB simultáneos?
- **Downloads concurrentes**: ¿Impacto en Railway bandwidth?
- **Database connections**: ¿Límite con múltiples orgs activas?

### Memory usage projection:
```
Escenario: 20 organizaciones × 150 archivos promedio
= 3000 archivos totales × 50MB promedio = 150GB en R2
¿RAM usage en Django para listar/filtrar estos archivos?
```

## Security & Access Control

### File Access Permissions:
- ¿Solo miembros de la organización pueden descargar archivos?
- ¿Implementar URLs con expiración para archivos sensibles?
- ¿Logging de acceso a archivos por compliance?

## Output Esperado

### 1. **Diagnóstico de bottlenecks**
- Consultas específicas que serán problemáticas
- Vistas que necesitan optimización
- Modelos que requieren índices adicionales

### 2. **Implementaciones requeridas**
- Código específico para manejar archivos pesados
- Optimizaciones de admin panel
- Monitoring y alertas necesarias

### 3. **Roadmap de optimización**
```
Fase 1: Optimizaciones críticas (pre-lanzamiento)
Fase 2: Monitoring operativo (primeros clientes) 
Fase 3: Scaling avanzado (10+ clientes)
```

### 4. **Estimación de recursos**
- ¿Cuándo necesitaré upgrade de Railway Hobby?
- ¿Límite real de organizaciones con free tier R2?
- ¿Puntos de inflexión de costos?

### 5. **Código específico necesario**
- AdminModels para monitoring
- Middleware para tracking performance
- Optimizaciones de queries
- File validation utilities

## Pregunta Clave Final

**¿Mi actual stack (Django + PostgreSQL + Railway Hobby + R2) puede manejar profesionalmente estudios de arquitectura mexicanos con archivos pesados (Revit, AutoCAD) sin degradar performance o disparar costos inesperados?**

Si la respuesta es NO, ¿qué optimizaciones específicas debo implementar ANTES del lanzamiento?

---

*Analiza mi código actual y dame una evaluación técnica honesta sobre si estoy preparado para manejar las cargas de trabajo reales de arquitectos mexicanos.*

### Respuesta técnica integral al prompt (files pesados para estudios de arquitectura)

#### Diagnóstico general (estado actual del código)

- **Almacenamiento actual**: `MEDIA_ROOT` local (`core/settings.py`), sin integración S3/R2 ni URLs firmadas.
- **Modelo de archivos**: `apps/files/models.py` define `ProjectFile` con `FileField` y propiedades `size`, `filename`, `extension`, pero **no persiste** `size_bytes`, `extension` ni `content_type` en BD; no hay índices específicos ni señales para actualizar metadatos.
- **Subidas**: `apps/files/views.py::upload_file` guarda archivos directamente; no valida tamaño/extension en servidor; no hay chunking ni upload directo a R2; no maneja timeouts personalizados.
- **Descargas**: se sirven desde `MEDIA_URL` local; no hay URLs firmadas ni control de expiración.
- **Admin**: `apps/files/admin.py` no registra `ProjectFile`; no hay métricas operativas.
- **Optimización actual**: En `ProjectDetailView` hay `prefetch_related('files','files__uploaded_by')`, lo cual mitiga N+1 al listar.

Conclusión preliminar: **NO** está listo para `.rvt` 100–500MB en producción. Requiere integrar almacenamiento externo (R2/S3), validaciones, métricas y optimizaciones antes del lanzamiento.

---

### Análisis de Performance Crítico (respuestas directas)

1) Consultas costosas (con el esquema actual):
- `SUM(size_bytes) BY organization`: hoy no es posible en BD porque `size_bytes` no está persistido. Requiere agregar campo `size_bytes` y denormalizar `organization_id` o usar joins con `Phase→Project→Organization`.
- Listados con metadata (posible N+1): mitigado parcialmente en `ProjectDetailView` con `prefetch_related`. Aún conviene `select_related('phase','uploaded_by','phase__project')` donde aplique.
- Búsquedas por tipo/tamaño: hoy solo existe `extension` como propiedad. Para filtrar/ordenar eficientemente se debe persistir `extension` y `content_type` con índices.

2) Upload de archivos grandes (200–500MB):
- Django maneja archivos grandes como `TemporaryUploadedFile` en disco, pero **tu servidor** hace I/O pesado y egress al servirlos. Para costos/performance, debes implementar **upload directo a R2 (presigned POST/PUT)**. Chunking del lado servidor no es necesario si subes directo al object storage; chunking HTTP puede delegarse al cliente (p. ej. Uppy/Tus, opcional).

3) Escenario de memoria (50 usuarios × 100MB):
- Con el enfoque actual (subida a `MEDIA_ROOT`): alto I/O y uso de disco; memoria moderada (Django streamea a temp files), pero riesgo de saturar **CPU/I/O** y tiempo de respuesta.
- Con **upload directo a R2**: el backend solo firma URLs y guarda metadatos; memoria y CPU del backend permanecen **bajas** incluso con alta concurrencia.

---

### Admin Panel Operativo propuesto

- **Métricas por organización**:
  - Storage usado vs límite (3GB): `SUM(size_bytes)` por `organization_id`.
  - Archivos más pesados por organización.
  - Organizaciones >80% del límite.
  - Uploads fallidos recientes (logueados o registrados en una tabla simple).
  - Proyectos activos vs límite.
- **Alertas**:
  - Señales/cron que marquen alertas si: uso >80%, archivo >100MB, consultas >2s, RAM >6GB (log + notificación).

---

### Optimizaciones de Costos

- **Railway**: evita servir archivos desde el dyno. Usa **R2** para egress y cache vía Cloudflare. El backend solo gestiona metadatos/firmas.
- **R2**:
  - Free tier: 10GB. A partir de ahí $0.015/GB/mes. Con 10 clientes × 3GB ≈ 30GB ≈ ~$0.45 USD/mes (≈ $8–9 MXN) en almacenamiento, sin contar egress.
  - Minimiza egress sirviendo descargas directamente desde R2 con URLs firmadas y usando CDN de Cloudflare.

---

### Implementaciones Requeridas (código sugerido)

1) Modelo y metadatos persistentes

```python
# apps/files/models.py
class ProjectFile(models.Model):
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name='files', verbose_name=_('Phase'))
    file = models.FileField(_('File'), upload_to=project_file_path)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Uploaded By'))
    uploaded_at = models.DateTimeField(_('Upload Date'), auto_now_add=True)

    # NUEVOS CAMPOS PARA PERFORMANCE/FILTROS
    size_bytes = models.BigIntegerField(default=0, db_index=True)
    extension = models.CharField(max_length=16, db_index=True)
    content_type = models.CharField(max_length=128, blank=True)
    checksum_sha256 = models.CharField(max_length=64, blank=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['uploaded_at']),
            models.Index(fields=['extension', 'size_bytes']),
        ]

    def save(self, *args, **kwargs):
        if self.file and hasattr(self.file, 'size'):
            self.size_bytes = getattr(self.file, 'size', 0) or 0
        name = (self.file.name if self.file else '')
        self.extension = os.path.splitext(name)[1].replace('.', '').upper() if name else ''
        super().save(*args, **kwargs)
```

2) Validaciones de subida en servidor (solo si no hay upload directo aún)

```python
# apps/files/views.py (dentro de upload_file)
MAX_FILE_SIZE_MB = 600  # permitir .rvt grandes si es indispensable
ALLOWED_EXTENSIONS = { 'PDF','JPG','JPEG','PNG','GIF','DWG','DXF','RVT','SKP','ZIP','RAR' }

for uploaded_file in request.FILES.getlist('files'):
    size_mb = (uploaded_file.size or 0) / (1024*1024)
    ext = os.path.splitext(uploaded_file.name)[1].replace('.', '').upper()
    if ext not in ALLOWED_EXTENSIONS:
        messages.error(request, _("Tipo de archivo no permitido: %s") % ext)
        return HttpResponse(status=400)
    if size_mb > MAX_FILE_SIZE_MB:
        messages.error(request, _("Archivo excede el límite (%s MB)") % MAX_FILE_SIZE_MB)
        return HttpResponse(status=413)
    ProjectFile.objects.create(phase=phase, file=uploaded_file, uploaded_by=request.user)
```

3) Integración con Cloudflare R2 (django-storages)

```bash
pip install boto3 django-storages
```

```python
# core/settings.py
INSTALLED_APPS += ['storages']
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_S3_ENDPOINT_URL = os.environ.get('AWS_S3_ENDPOINT_URL')  # p.ej. https://<accountid>.r2.cloudflarestorage.com
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_ACCESS_KEY_ID = os.environ.get('R2_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('R2_SECRET_ACCESS_KEY')
AWS_S3_REGION_NAME = 'auto'
AWS_S3_ADDRESSING_STYLE = 'virtual'
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_DEFAULT_ACL = None
```

4) Upload/Download directo con URLs firmadas (recomendado)

```python
# apps/files/views_signed.py
import boto3, datetime
from django.views.decorators.http import require_http_methods

session = boto3.session.Session(
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME,
)
s3 = session.client('s3', endpoint_url=settings.AWS_S3_ENDPOINT_URL)

@login_required
@require_http_methods(["POST"])  # client solicita URL para subir
def get_presigned_upload(request, project_id, phase_id):
    phase = get_object_or_404(Phase, id=phase_id, project_id=project_id)
    if request.user.organization != phase.project.organization:
        return HttpResponseForbidden()
    key = project_file_path(ProjectFile(phase=phase), request.POST['filename'])
    content_type = request.POST.get('content_type', 'application/octet-stream')
    expires = 3600
    url = s3.generate_presigned_url(
        'put_object',
        Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': key, 'ContentType': content_type},
        ExpiresIn=expires,
    )
    return JsonResponse({'url': url, 'key': key})

@login_required
@require_http_methods(["POST"])  # client confirma subida exitosa
def confirm_upload(request):
    # Guardar registro ProjectFile con key ya subido a R2
    # Validar org, tamaño declarado y extensión antes de persistir
    ...
```

5) Admin para métricas y monitoreo

```python
# apps/files/admin.py
from django.contrib import admin
from django.db.models import Sum
from .models import ProjectFile

@admin.register(ProjectFile)
class ProjectFileAdmin(admin.ModelAdmin):
    list_display = ("filename_display", "extension", "size_h", "phase", "uploaded_by", "uploaded_at")
    list_filter = ("extension", "uploaded_at")
    search_fields = ("file", "uploaded_by__first_name", "uploaded_by__last_name", "phase__project__name")
    date_hierarchy = "uploaded_at"
    ordering = ("-uploaded_at",)

    def filename_display(self, obj):
        return obj.filename
    def size_h(self, obj):
        from django.template.defaultfilters import filesizeformat
        return filesizeformat(obj.size_bytes or 0)

    change_list_template = "admin/files/projectfile_changelist.html"  # para panel de métricas
```

```python
# Ejemplos de consultas para métricas (usar en admin view/panel)
from apps.files.models import ProjectFile
from django.db.models import Sum

usage_by_org = (
    ProjectFile.objects
    .values("phase__project__organization")
    .annotate(total_bytes=Sum("size_bytes"))
    .order_by("-total_bytes")
)

heavy_files = ProjectFile.objects.order_by("-size_bytes")[:50]
```

6) Middleware de performance (latencia y consultas >2s)

```python
# core/perf_middleware.py
import time, logging
from django.db import connection

logger = logging.getLogger("apps")

class PerformanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.perf_counter()
        response = self.get_response(request)
        elapsed = (time.perf_counter() - start) * 1000
        if elapsed > 2000:
            logger.warning(f"Slow request {request.path} took {elapsed:.1f}ms")
        # opcional: registrar queries si DEBUG
        return response
```

---

### Optimización de Consultas y Esquema

- Agregar `size_bytes`, `extension`, `content_type` e índices.
- Crear vistas/listados usando `select_related('phase','uploaded_by','phase__project')` y paginación.
- Cálculos por organización con `.values('phase__project__organization').annotate(Sum('size_bytes'))`.
- Si necesitas reportes muy frecuentes, considerar denormalizar un contador en `Organization` (campo `storage_used_bytes`) actualizado por señales o tareas periódicas.

---

### Benchmarks/Estimaciones (aproximadas)

- **Uploads simultáneos** (100MB):
  - Con upload directo a R2: backend puede manejar **decenas a cientos** de subidas simultáneas porque solo firma URLs y persiste metadatos.
  - Sin R2: limitado por I/O del contenedor; riesgo de timeouts y disco.
- **Downloads concurrentes**: con URLs firmadas R2, el egress no pasa por el backend; el impacto en Railway es mínimo.
- **Conexiones a BD**: el módulo de archivos es liviano en DB salvo listados/agrupaciones; usa paginación e índices para 1000+ archivos por organización.
- **Memoria al listar 3000 archivos (50MB promedio)**: el backend no carga archivos en memoria; el peligro es renderizar listados gigantes. Usar paginación/scroll y evitar `.all()` sin límites.

---

### Seguridad y Control de Acceso

- Solo miembros de la organización pueden obtener URLs firmadas de subida/descarga.
- **URLs firmadas con expiración** corta (p. ej. 15–60 minutos).
- Registra auditoría de accesos a archivos sensibles (tabla o logs con `user_id`, `org_id`, `file_id`, `action`, `ip`, `timestamp`).

---

### Roadmap de Optimización

- Fase 1 (crítico pre-lanzamiento):
  - Integrar R2 (django-storages) o presigned URLs para upload/download.
  - Añadir `size_bytes`, `extension`, índices e implementar validaciones de tamaño/tipo.
  - Registrar `ProjectFile` en Admin con métricas básicas y paginación.
  - Middleware de performance y logs de uploads fallidos.

- Fase 2 (monitoring operativo):
  - Panel de métricas en admin: uso por organización, top archivos pesados, alertas >80%.
  - Tarea diaria (management command/cron) para recalcular storage y enviar alertas.
  - URLs firmadas con expiración adaptativa según sensibilidad del archivo.

- Fase 3 (scaling 10+ clientes):
  - CDN de Cloudflare delante de R2 para descargas recurrentes.
  - Thumbnails/derivados en background para imágenes.
  - Opcional: antivirus a la subida y validación de MIME en servidor.

---

### Estimación de Recursos y Costos

- ¿Cuándo actualizar Railway Hobby?:
  - Si sirves archivos desde el backend: inmediatamente. Con R2 directo, Hobby puede rendir bien mientras la lógica de negocio sea ligera y el tráfico de páginas no sea masivo.
  - Señales de upgrade: CPU sostenida alta, latencias >1–2s en endpoints core, necesidades de workers background.
- Límite real free tier R2: 10GB. Con 20 orgs × 3GB = 60GB, almacenamiento ≈ $0.90 USD/mes (sin egress). Egress dependerá de descargas; mitiga con CDN.
- Puntos de inflexión de costos: picos de egress (descargas frecuentes), generación de previews, antivirus.

---

### Respuesta a la Pregunta Clave

**Hoy: NO.** Con `MEDIA_ROOT` local, sin validaciones ni R2, el riesgo de performance/costos es alto con `.rvt`/`.dwg` pesados.

**Qué implementar ANTES del lanzamiento:**
- Almacenamiento en R2 con URLs firmadas (upload y download directos).
- Persistir `size_bytes`, `extension`, `content_type` con índices; validaciones en servidor.
- Admin con métricas por organización y alertas >80% de storage.
- Middleware de performance y registros de auditoría de accesos.
- Paginación consistente en listados de archivos.

Con estas optimizaciones, el stack Django + PostgreSQL + Railway Hobby + R2 **sí puede** manejar profesionalmente flujos de estudios de arquitectura mexicanos sin degradar performance ni disparar costos inesperados.
