# Documentación Técnica de ArcManager

Este documento sirve como una referencia central para los desarrolladores y administradores del sistema ArcManager. Se irá actualizando a medida que el proyecto evolucione.

## 1. Arquitectura del Backend

### 1.1. Configuración Principal (`settings.py`)

El archivo `arc_manager/core/settings.py` es el corazón de la configuración del proyecto Django. A continuación se detallan las secciones más importantes que fueron revisadas y refactorizadas.

#### `INSTALLED_APPS`

Las aplicaciones instaladas están organizadas en tres grupos para mayor claridad, siguiendo las mejores prácticas de Django:

1.  **Aplicaciones de Django:** Las apps que vienen por defecto con el framework.
2.  **Aplicaciones de Terceros:** Paquetes externos instalados.
    *   `axes`: Para controlar e impedir intentos de inicio de sesión por fuerza bruta.
    *   `crispy_forms` y `crispy_bootstrap5`: Para renderizar formularios de Django con estilos de Bootstrap 5 de forma automática y limpia.
3.  **Aplicaciones Locales:** Las aplicaciones propias del proyecto.
    *   `core`: Aplicación principal que contiene la configuración central.
    *   `apps.accounts`: Gestión de usuarios, autenticación, login/logout y reseteo de contraseñas.
    *   `apps.main`: Vistas principales como el dashboard.
    *   `apps.orgs`: Lógica de organizaciones y clientes.
    *   `apps.plans`: Sistema de suscripciones y pagos.
    *   `apps.projects`: Gestión de proyectos, fases y tareas.
    *   `apps.files`: Almacenamiento de archivos de proyectos.

#### `MIDDLEWARE`

El middleware procesa las peticiones y respuestas globalmente. El orden es crítico para la seguridad y funcionalidad.

- `SecurityMiddleware`: Proporciona varias mejoras de seguridad. Debe ir al principio.
- `WhiteNoiseMiddleware`: Sirve archivos estáticos de forma eficiente en producción.
- `SessionMiddleware`: Gestiona las sesiones de usuario.
- `AuthenticationMiddleware`: Asocia usuarios a las peticiones usando sesiones.
- `AxesMiddleware`: Se engancha después de la autenticación para monitorear intentos de acceso fallidos.
- `LoginRequiredMiddleware`: Middleware personalizado que requiere que el usuario esté autenticado para la mayoría de las vistas.
- `SuperuserRestrictMiddleware`: Impide que los superusuarios accedan a las vistas de la aplicación normal para evitar acciones accidentales.
- `OrganizationContextMiddleware`: Asegura que el contexto de la organización esté disponible en las peticiones.
- `ErrorHandlingMiddleware`: Un middleware final para capturar excepciones no manejadas y presentar páginas de error amigables.

#### `LOGGING`

La configuración de logging fue robustecida para producción con los siguientes principios:

- **Rotación de Archivos:** Se usa `RotatingFileHandler` para los archivos de log (`debug.log`, `errors.log`, etc.). Esto evita que los archivos crezcan indefinidamente, rotándolos cuando alcanzan un tamaño máximo (ej. 5MB) y manteniendo un número limitado de archivos antiguos.
- **Consola para Producción:** Se configuró un `handler` (`console_prod`) que permite enviar logs a la consola en entornos de producción (necesario para servicios como AWS CloudWatch), filtrando por `require_debug_false` para no ejecutarse en desarrollo.
- **Logger Raíz (`root`):** Se añadió un logger `root` para capturar cualquier advertencia o error que no sea manejado por un logger específico, asegurando que no se pierdan logs importantes y enviándolos a la consola de producción y al archivo de errores.

### 1.2. Optimización de Modelos y Base de Datos

Se realizó una revisión exhaustiva de todos los modelos para mejorar la integridad de los datos y el rendimiento de las consultas.

#### Estrategias de `on_delete`

Se ajustaron las políticas de eliminación en cascada para prevenir la pérdida de datos accidental:

-   **`User.organization`**: Se cambió de `CASCADE` a `SET_NULL`. Si una organización es eliminada, sus usuarios no se eliminarán, sino que su campo `organization` quedará nulo. Esto protege las cuentas de usuario.
-   **`Project.owner`**: Se cambió de `CASCADE` a `SET_NULL`. Si un usuario propietario es eliminado, los proyectos que le pertenecían no se eliminarán. Esto preserva los datos del proyecto como un activo de la organización. El código fue actualizado para manejar correctamente los casos donde un proyecto no tiene propietario.
-   **`UpgradeRequest.current_plan` y `requested_plan`**: Se cambió de `CASCADE` a `PROTECT`. Esto evita que un plan pueda ser eliminado si existe una solicitud de upgrade (incluso histórica) que lo referencie, manteniendo la integridad de los registros.

#### Índices de Base de Datos (`db_index=True`)

Se añadieron índices a las columnas que se utilizan frecuentemente en operaciones de filtrado (`filter`), ordenamiento (`order_by`) o búsqueda para acelerar las consultas a la base de datos.

-   **`Organization`**: Se indexaron `name` y `is_active`.
-   **`Plan`**: Se indexó `is_active`.
-   **`Subscription`**: Se indexaron `end_date` y `subscription_status`.
-   **`UpgradeRequest`**: Se indexó `status`.
-   **`Project`**: Se indexaron `name` y `status`.
-   **`Phase`**: Se indexó `status`.
-   **`Task`**: Se indexaron `status`, `priority` y `due_date`.

**Nota Importante:** Todos estos cambios requieren la creación y aplicación de una **nueva migración de base de datos** para que tengan efecto.

---
*Este documento se irá actualizando a medida que avancemos en la refactorización.*
