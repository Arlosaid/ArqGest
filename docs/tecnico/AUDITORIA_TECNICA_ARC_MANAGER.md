## Auditoría Técnica y de Producto — Arc Manager

## 1. Estado General del Proyecto
- **Clasificación**: Beta (MVP avanzado). Ya hay separación por apps (`accounts`, `orgs`, `projects`, `plans`, `files`, `users`), middleware propio, servicios y plantillas. Faltan endurecimientos de producción y algunas optimizaciones.
- **Calidad del código**: En general clara y modular. Buen uso de `select_related/prefetch_related`, servicios en `plans`, y validaciones en modelos. Áreas a mejorar: duplicación de lógica de conteos en vistas, manejo de errores JSON filtrando detalles, y algún acceso a atributos inexistentes.
- **Dependencias críticas/riesgosas**:
  - `SECRET_KEY` con default inseguro en `core/settings.py` y `ALLOWED_HOSTS='*'` en escenarios comunes.
  - `SESSION_SAVE_EVERY_REQUEST=True` (impacto de rendimiento).
  - `redis==3.5.3` (antigua) y logging a archivos dentro de contenedor (menos ideal en orquestadores).
  - `crispy-bootstrap5` sin versión fijada.

## 2. Rendimiento y Optimización
- **Cuellos de botella detectados**:
  - Conteos repetidos en `ProjectDetailView.get_context_data` y en Kanban (`projects/views.py`), generando múltiples consultas por métrica/estado.
  - `LoginRequiredMiddleware` hace `select_related('organization')` en cada request (puede ser costoso si no siempre se usa).
  - `SESSION_SAVE_EVERY_REQUEST=True` aumenta escrituras de sesión.
- **Revisión de consultas y ciclos**:
  - Kanban calcula `tasks_by_status` filtrando por estado en bucle; puede resolverse con una única agregación o agrupación en memoria tras una sola consulta.
  - Falta `CONN_MAX_AGE` para conexiones persistentes a DB.
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
  - Cambiar `SESSION_SAVE_EVERY_REQUEST = False` salvo requerimiento explícito.
  - `DATABASES['default']['CONN_MAX_AGE'] = int(os.environ.get('CONN_MAX_AGE','120'))`.

## 3. Seguridad
- **Vulnerabilidades/olvidos**:
  - `SECRET_KEY` por defecto y `ALLOWED_HOSTS=['*']` en condiciones relajadas.
  - `SESSION_COOKIE_SECURE=False` salvo AWS; debería activarse siempre que `DEBUG=False`.
  - Respuestas JSON con `str(e)` en `update_task_status`/`move_task` (filtran detalles internos).
  - En creación de usuario se loggea contraseña temporal en warning (riesgo de exposición en logs).
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
- **Tabla de prioridades y acciones**

| Prioridad | Hallazgo | Acción recomendada |
| --- | --- | --- |
| Alta | Defaults inseguros (`SECRET_KEY`, `ALLOWED_HOSTS`, cookies) | Forzar variables de entorno; activar SSL/HSTS/cookies seguras cuando `DEBUG=False` |
| Alta | Errores JSON exponen detalles | Loggear con `logger.error(..., exc_info=True)` y responder mensaje genérico |
| Alta | Queries redundantes en métricas/Kanban | Agregaciones en una sola consulta; agrupar en memoria tras `select_related/prefetch_related` |
| Alta | `SESSION_SAVE_EVERY_REQUEST=True` | Cambiar a `False` salvo necesidad |
| Media | Falta `CONN_MAX_AGE` | `DATABASES['default']['CONN_MAX_AGE']=120-300` |
| Media | Logging de contraseñas temporales | Eliminar logs de credenciales; usar set-password por token |
| Media | `crispy-bootstrap5` sin versión | Fijar versión (p. ej. `crispy-bootstrap5==2024.2`) |
| Media | Redis cliente antiguo/pool | Actualizar `redis` y configurar pool/compresión opcional |
| Baja | Logging a archivos en contenedor | Migrar a stdout/stderr y agregación centralizada |

- **Roadmap (3 fases)**
  - Fase 1: Seguridad y rendimiento (2 semanas)
    - Endurecer settings de producción y saneo de errores JSON.
    - `SESSION_SAVE_EVERY_REQUEST=False`, `CONN_MAX_AGE`, optimizaciones de consultas en vistas clave.
    - Fijar versiones críticas (`crispy-bootstrap5`), actualizar cliente `redis` y configuración básica de cache.
  - Fase 2: UX y escalabilidad (3-4 semanas)
    - Dashboard ejecutivo, filtros y notificaciones in-app/email.
    - Migrar logging a stdout/stderr; preparar stack de observabilidad.
    - Introducir Celery/RQ para emails/reportes; tareas programadas de mantenimiento (suscripciones).
  - Fase 3: Diferenciales de producto (4-6 semanas)
    - Cronogramas/Gantt, reportes automáticos y control de costos.
    - Integración inicial con BIM/Revit (import/export), webhooks y API pública básica.

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
