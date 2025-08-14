# 🔐 Seguridad — Autenticación, Autorización y Protección

## Autenticación
- Basada en Django Auth con usuario personalizado (`apps.accounts`).
- Recuperación de contraseña vía vistas estándar + templates propios.

## Autorización por rol
- `user.is_org_admin` habilita acciones administrativas a nivel de organización.
- Mixins y decoradores por módulo (ver documentos técnicos por módulo) para validar organización y permisos.

## Protección contra fuerza bruta
- `django-axes`: limita intentos fallidos y registra eventos de acceso.

## Middlewares relevantes
- `LoginRequiredMiddleware`: requiere sesión para la mayoría de vistas.
- `SuperuserRestrictMiddleware`: restringe vistas normales a superusuarios para evitar acciones accidentales.
- `OrganizationContextMiddleware`: asegura el contexto de organización en la petición.

## Permisos por Módulo (ejemplos)
- Plans: `OrgAdminRequiredMixin`, `ActiveSubscriptionRequiredMixin`, `plan_limit_check`.
- Projects: validaciones de pertenencia a organización en vistas de detalle/acción.

## Buenas prácticas
- Validar ownership de recursos por `organization` en cada operación.
- Usar `select_related/prefetch_related` para evitar filtrados incompletos por relaciones.
- Mensajes claros al usuario y manejo de errores centralizado.

## Logging y auditoría
- Handlers rotativos y salida a consola en producción.
- Registrar eventos críticos: cambios de plan, creación/eliminación de usuarios, movimientos de tareas.
