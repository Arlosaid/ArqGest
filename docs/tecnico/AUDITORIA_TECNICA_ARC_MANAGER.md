## Auditoría Técnica y de Producto — Arc Manager

## 1. Estado General del Proyecto
- **Clasificación**: Beta (MVP avanzado). Ya hay separación por apps (`accounts`, `orgs`, `projects`, `plans`, `files`, `users`), middleware propio, servicios y plantillas.
- **Calidad del código**: En general clara y modular. Buen uso de `select_related/prefetch_related`, servicios en `plans`, y validaciones en modelos. Áreas a mejorar: evitar lógica duplicada en vistas antiguas y reducir trabajo innecesario en middlewares.
- **Dependencias críticas/riesgosas (estado actual)**:
  - `SECRET_KEY` y `ALLOWED_HOSTS` validados por entorno en producción.
  - `SESSION_SAVE_EVERY_REQUEST=False` aplicado.
  - Cliente Redis actualizado y `crispy-bootstrap5` con versión fija.
  - Logging a archivos en contenedor: aceptable para MVP; recomendable migrar a stdout/stderr como siguiente paso.

## 2. Rendimiento y Optimización
- **Cuellos de botella (estado actual)**:
  - Métricas en `ProjectDetailView` y Kanban optimizadas con agregaciones únicas y agrupación en memoria.
  - `LoginRequiredMiddleware` podría costar en todos los requests: monitorear y ajustar si se detecta impacto.
  - Conexiones persistentes (`CONN_MAX_AGE`) habilitadas por entorno.
- **Revisión de consultas y ciclos**:
  - Kanban ya agrupa con una sola consulta y usa `select_related/prefetch_related`.
  - Conexiones persistentes activas.
- **Optimización propuesta (concreta)**:
  - Agregar agregaciones en una sola consulta:
    ```python
    from django.db.models import Count, Q
    agg = tasks_qs.aggregate(
      total=Count('id'),
      todo=Count('id', filter=Q(status='TODO')),
      in_progress=Count('id', filter=Q(status='IN_PROGRESS')),
      paused=Count('id', filter=Q(status='PAUSED')),
      done=Count('id', filter=Q(status='DONE')),
      overdue=Count('id', filter=Q(due_date__lt=date.today())),
    )
    ```
  - En Kanban, traer `all_tasks.select_related('phase','assigned_to')` una vez y agrupar en Python o con agregaciones.
  - Mantener `SESSION_SAVE_EVERY_REQUEST = False` salvo requerimiento explícito.
  - Mantener `DATABASES['default']['CONN_MAX_AGE'] = int(os.environ.get('CONN_MAX_AGE','120'))`.

## 3. Seguridad
- **Vulnerabilidades/olvidos (estado actual)**:
  - Defaults inseguros mitigados: `SECRET_KEY` y `ALLOWED_HOSTS` obligatorios por entorno con `DEBUG=False`.
  - Cookies seguras/HSTS y redirección SSL activas cuando `DEBUG=False`.
  - Respuestas JSON saneadas en `update_task_status`/`move_task`.
  - Revisar onboarding para eliminar cualquier log de credenciales si persiste.
- **Mejoras recomendadas**:
  - Endurecer settings si `DEBUG=False` (SSL redirect, HSTS, cookies seguras, `X_FRAME_OPTIONS`, `REFERRER_POLICY`, `Content-Type nosniff`).
  - Prohibir defaults de `SECRET_KEY` y `ALLOWED_HOSTS`; obligar a variables de entorno.
  - En vistas JSON: loggear el error y responder mensaje genérico.
  - Cambiar onboarding a “establecer contraseña” con token en lugar de enviar credenciales; nunca loggear contraseñas temporales.
  - Añadir CSP y Permissions-Policy cuando se despliegue públicamente.

## 4. Escalabilidad y Viabilidad Técnica
- **Arquitectura para crecer**: La estructura por apps y el uso de Redis sientan buenas bases. Falta procesamiento asíncrono (emails, reportes) y estandarización de logging (stdout + agregador).
- **Puntos débiles**:
  - Agregaciones/queries ineficientes en vistas de alto uso (Kanban, detalle de proyecto).
  - Logging a archivos en contenedor; preferible stdout/stderr para orquestadores.
  - `redis` cliente antiguo y sin configuración de pool/compresión.
- **Viabilidad**: **Viable como MVP**. Con las optimizaciones y endurecimiento propuestos, pasa a **Viable para escalar**.

## 5. Experiencia de Usuario (UX) y Flujo
- **Intuitivo para arquitectos/despachos**: Flujos base de proyectos/fases/tareas están; falta un dashboard ejecutivo y filtros rápidos.
- **Mejoras**:
  - Dashboard con KPIs: tareas vencidas, progreso por proyecto, capacidad por usuario.
  - Filtros por cliente/estado/fecha y búsqueda global en listas.
  - Notificaciones in-app y correo (eventos de asignación, vencimientos próximos).
  - Estados visuales consistentes (badges) y vistas compactas para “Mis tareas”.
- **Componentes visuales sugeridos**: panel de control, sistema de notificaciones, filtros/segmentación, quick-actions en tarjetas de tarea, indicadores de capacidad de equipo.

## 6. Funcionalidades y Valor de Producto
- **Esenciales para competir**:
  - Cronogramas (Gantt simple por fases/tareas), carga/gestión de planos, gestión de tareas/kanban, control de versiones de archivos, permisos por rol, reportes básicos.
  - Ya existen: proyectos/fases/tareas, carga de archivos por fase (en `files`), y suscripciones básicas.
- **Diferenciales recomendados**:
  - Control de costos por proyecto/fase, reportes automáticos (PDF/Excel), plantillas de proyectos/fases (ya hay `PhaseTemplate`), integración con BIM/Revit (export/import), vistas de recursos/capacidad.
- **Preparación del código**: Modular y con buenas relaciones; no hay integración BIM aún, pero la separación por apps facilita añadir servicios externos y webhooks.

## 7. Riesgos Técnicos
- **Críticos**:
  - Defaults inseguros (`SECRET_KEY`, `ALLOWED_HOSTS`), cookies no seguras salvo AWS, exposición de errores en JSON, logging de contraseñas temporales.
  - Consultas redundantes en vistas críticas (rendimiento bajo carga).
- **Altos**:
  - `SESSION_SAVE_EVERY_REQUEST=True`, falta `CONN_MAX_AGE`, logging a archivos en contenedores.
  - `crispy-bootstrap5` sin fijar versión; `redis` cliente antiguo.
- **Medios**:
  - Middleware potencialmente costoso en todos los requests; falta de colas asíncronas.
- **Mitigación**:
  - Endurecer settings de prod, sanear respuestas JSON, eliminar logging de credenciales, optimizar consultas, fijar versiones y modernizar cliente Redis, introducir Celery/RQ.

## 8. Informe Final
- **Tabla de prioridades y acciones (ajustada al estado actual)**

| Prioridad | Hallazgo | Acción recomendada |
| --- | --- | --- |
| Alta | Defaults inseguros (`SECRET_KEY`, `ALLOWED_HOSTS`, cookies) | Ya aplicado; mantener validaciones por entorno |
| Alta | Errores JSON exponen detalles | Ya saneado en vistas críticas; mantener patrón |
| Alta | Queries redundantes en métricas/Kanban | Ya optimizado con agregaciones y `select_related/prefetch_related` |
| Alta | Persistencia de archivos en servidor | Activar R2/S3 con `django-storages` para producción del MVP |
| Media | CONN_MAX_AGE | Ya aplicado; ajustar por entorno (120–300) |
| Media | Logging de contraseñas temporales | Verificar y eliminar si existe; migrar a set-password por token |
| Baja | Logging a archivos en contenedor | Planear migración a stdout/stderr en siguientes pasos |

**Roadmap enfocado al MVP**

- Fase 1 (crítica para el MVP) — Seguridad, rendimiento y archivos
  - Endurecer settings de producción y saneo de errores JSON. (aplicado)
  - `SESSION_SAVE_EVERY_REQUEST=False`, `CONN_MAX_AGE`, optimizaciones en vistas clave. (aplicado)
  - Versionado de dependencias críticas (crispy, redis) actualizado. (aplicado)
  - Soporte de almacenamiento externo (R2/S3) listo con endpoints de URLs firmadas; activar en producción mediante variables de entorno. (pendiente de configuración)
  - Ver documento consolidado: `docs/tecnico/MEJORAS_BACKEND_FASE_1.md`.

- Siguientes pasos (no críticos para salir el MVP)
  - UX y escalabilidad: dashboard ejecutivo, filtros avanzados, notificaciones in-app/email.
  - Observabilidad: migrar logging a stdout/stderr y preparar stack de monitoreo.
  - Procesamiento asíncrono: Celery/RQ para emails/reportes; tareas programadas de mantenimiento.
  - Diferenciales: Gantt/reportes de costos; integración BIM/Revit (import/export), webhooks y API pública básica.

---

Anexos útiles
- Conexiones persistentes a DB:
```python
# settings.py
DATABASES['default']['CONN_MAX_AGE'] = int(os.environ.get('CONN_MAX_AGE', '120'))
```
- Endurecimiento en producción:
```python
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
```
- Sanitización de errores JSON:
```python
except Exception:
    logger.error('operation failed', exc_info=True)
    return JsonResponse({'success': False, 'error': 'Unexpected error'})
```
