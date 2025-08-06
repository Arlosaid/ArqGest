# Plan de Pruebas y Refinamiento (Versión Definitiva) - ArcManager

**Objetivo:** Garantizar que la aplicación ArcManager sea segura, estable, eficiente y funcionalmente correcta, prestando especial atención a los casos de error, flujos alternativos y la capacidad de recuperación ante fallos.

**Filosofía:** Este plan se ejecutará de manera secuencial. Cada sección debe completarse y validarse antes de pasar a la siguiente para asegurar que las pruebas se construyen sobre una base sólida.

---

## Fase 1: Configuración del Entorno de "Staging" (Réplica de Producción)

*El objetivo de esta fase es crear un entorno de pruebas que sea idéntico al de producción para que nuestras pruebas sean fiables.*

- **[ ]** **1.1. Duplicar la Configuración de Producción:** Crear `docker-compose.prod.yml` (con Gunicorn) y `.env.prod`.
- **[ ]** **1.2. Configurar Variables de Entorno de Producción:** `DEBUG=False`, `SECRET_KEY` segura, `ALLOWED_HOSTS` específico, credenciales seguras.
- **[ ]** **1.3. Desplegar el Entorno de Staging:** Levantar servicios e implementar proxy inverso con HTTPS.
- **[ ]** **1.4. Validar el Entorno:** Verificar HTTPS forzado y logs limpios.

---

## Fase 2: Pruebas de Seguridad y Resiliencia

*Validamos configuraciones críticas y probamos la resistencia del sistema a entradas maliciosas o inesperadas.*

- **[ ]** **2.1. Verificación de Configuraciones de Producción (`settings.py`):**
    - **[ ]** `DEBUG=False`, `ALLOWED_HOSTS`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`, `SECURE_SSL_REDIRECT`.
- **[ ]** **2.2. Pruebas de Autenticación y Autorización (Casos de Falla):**
    - **[ ]** **`django-axes`:** Probar bloqueo y reseteo del contador.
    - **[ ]** **Aislamiento de Datos (Tenant Isolation) - Prueba Crítica:** Validar que un usuario de `OrgB` **no puede acceder por URL** a ningún recurso (proyectos, fases, tareas, archivos, clientes) de `OrgA`. **Repetir para todas las vistas (detalle, edición, eliminación).**
- **[ ]** **2.3. Validación de Entradas y Formularios (Prueba de Robustez):**
    - **[ ]** **Validación de Campos:** Enviar formularios con campos requeridos en blanco, con formato incorrecto y excediendo `max_length`.
    - **[ ]** **Inyección de Scripts (XSS):** Introducir `<script>alert('XSS');</script>` en todos los campos de texto (`CharField`, `TextField`) y verificar que la salida es escapada (se muestra como texto, no se ejecuta).
    - **[ ]** **Inyección SQL (Básica):** En campos de búsqueda o filtros, introducir caracteres como `'` o `--`. La aplicación no debe crashear; debe manejar la entrada sin generar errores 500.

---

## Fase 2.5: Pruebas de Integridad de Datos (Post-Refactorización)

*Esta fase se enfoca en validar las nuevas reglas de negocio y optimizaciones aplicadas directamente en los modelos de la base de datos.*

- **[ ]** **2.5.1. Verificación de Índices de Base de Datos:**
    - **[ ]** Conectar a la base de datos del entorno de staging y usar comandos SQL (`\d nombre_tabla` en psql) para confirmar que los nuevos índices en `Organization`, `Plan`, `Subscription`, `Project`, `Phase` y `Task` fueron creados correctamente por la migración.
- **[ ]** **2.5.2. Pruebas de la Lógica `on_delete`:**
    - **[ ]** **Prueba `User.organization` (`SET_NULL`):**
        - **[ ]** Crear una Organización `OrgTest` y un Usuario `UserTest` asignado a ella.
        - **[ ]** Eliminar `OrgTest`.
        - **[ ]** **Verificar:** El `UserTest` **no** debe haber sido eliminado. Su campo `organization` debe ser `NULL`. El usuario debe poder seguir iniciando sesión.
    - **[ ]** **Prueba `Project.owner` (`SET_NULL`):**
        - **[ ]** Crear un Usuario `OwnerTest` y un Proyecto `ProjectTest` cuyo `owner` sea `OwnerTest`.
        - **[ ]** Eliminar al usuario `OwnerTest`.
        - **[ ]** **Verificar:** El `ProjectTest` **no** debe haber sido eliminado. Su campo `owner` debe ser `NULL`.
    - **[ ]** **Prueba `UpgradeRequest.plan` (`PROTECT`):**
        - **[ ]** Crear un `PlanTest`.
        - **[ ]** Crear una `UpgradeRequest` que referencie a `PlanTest`.
        - **[ ]** Intentar eliminar `PlanTest`.
        - **[ ]** **Verificar:** La operación debe fallar con un error `ProtectedError`.

    - **[ ]** **Prueba de Configuración de Caché (Redis):**
        - **[ ]** Crear una prueba unitaria o de integración que intente escribir y leer un valor simple del caché de `default` y `sessions`.
        - **[ ]** **Verificar:** La prueba debe pasar sin errores de conexión o `TypeError`, validando que `settings.py` y `requirements.txt` están alineados.

---

## Fase 3: Pruebas de Rendimiento y Optimización (Repetir)

- **[ ]** **3.1. Análisis con Django Debug Toolbar** (con datos de prueba).
    - **[ ]** Navegar a las vistas de listas (`/projects/`, `/users/`, `/organizations/`) y al detalle de un proyecto.
    - **[ ]** **Verificar:** El número de consultas SQL debe ser bajo (idealmente < 15-20 para listas y < 10 para detalles). No debe haber consultas duplicadas.
- **[ ]** **3.2. Verificación de la Caché de Suscripción:**
    - **[ ]** Activar el logging de consultas SQL.
    - **[ ]** En la shell de Django, obtener una organización y acceder a `.subscription` varias veces.
    - **[ ]** **Verificar:** La consulta a la tabla `plans_subscription` para esa organización solo debe ejecutarse una vez.
- **[ ]** **3.3. Optimización de Frontend** con Lighthouse (auditoría de rendimiento, SEO, mejores prácticas).

---

## Fase 4: Pruebas Funcionales (E2E con Casos de Falla y Planes B)

### **4.1. Módulo de Cuentas, Usuarios y Organización**
- **[ ]** **Happy Paths:**
    - **[ ]** Flujo de registro, Login/Logout, recuperación de contraseña.
- **[ ]** **Unhappy Paths & Casos Límite:**
    - **[ ]** Intentar registrarse con email existente, contraseña débil, etc.
    - **[ ]** Intentar login con credenciales incorrectas (verificar `django-axes`).
    - **[ ]** Usar link de recuperación de contraseña por segunda vez.
- **[ ]** **Plan B (Procedimientos Administrativos):**
    - **[ ]** **Forzar Cambio de Contraseña:**
        - **[ ]** Desde el Admin, seleccionar un usuario y usar la acción "Forzar cambio de contraseña".
        - **[ ]** **Verificar:** Se debe mostrar un mensaje con un enlace de reseteo único y funcional.
    - **[ ]** **Reenviar Correo de Bienvenida:**
        - **[ ]** Desde el Admin, seleccionar un usuario y usar la acción "Reenviar correo de bienvenida".
        - **[ ]** **Verificar:** El usuario debe recibir un correo de bienvenida/recordatorio (sin credenciales).

### **4.2. Módulo de Comandos de Gestión**
- **[ ]** **Prueba de Idempotencia:**
    - **[ ]** Ejecutar `python manage.py setup_database` dos veces seguidas.
    - **[ ]** **Verificar:** La segunda ejecución no debe crear un superusuario duplicado ni fallar.
- **[ ]** **Prueba de Seguridad de Credenciales:**
    - **[ ]** Ejecutar `setup_database` sin las variables de entorno `DJANGO_SUPERUSER_EMAIL` y `DJANGO_SUPERUSER_PASSWORD`.
    - **[ ]** **Verificar:** El comando debe advertir que no se creará el superusuario, pero no debe fallar.
- **[ ]** **Prueba de Confirmación Interactiva:**
    - **[ ]** Ejecutar `python manage.py clean_data`.
    - **[ ]** **Verificar:** El comando debe detenerse y pedir confirmación. Probar cancelar la operación.
    - **[ ]** Repetir para `clean_tenant_data` y `clean_upgrade_requests`.

### **4.3. Módulo de Plantillas de Fases**
- **[ ]** **Happy Path:** CRUD completo.
- **[ ]** **Unhappy Paths:** Crear plantillas con nombres duplicados o sin fases.

### **4.4. Módulo de Proyectos**
- **[ ]** **Happy Path:** Creación manual y desde plantilla, edición, eliminación.
- **[ ]** **Unhappy Paths:**
    - **[ ]** Crear proyecto con nombre duplicado.
    - **[ ]** Eliminar un `Cliente` con proyectos asociados (validar `on_delete`).

### **4.5. Módulo de Tareas y Kanban**
- **[ ]** **Happy Path:** CRUD de tareas, moverlas entre columnas.
- **[ ]** **Unhappy Paths:**
    - **[ ]** Acceder a fases/tareas de otro proyecto por URL.
    - **[ ]** Probar el Kanban con ~100 tareas para detectar problemas de rendimiento.

### **4.6. Módulo de Archivos**
- **[ ]** **Happy Path:** Subir, descargar, eliminar.
- **[ ]** **Unhappy Paths:** Subir archivos con nombres problemáticos, cancelar subida.

### **4.7. Módulo "Mis Tareas" y Dashboard**
- **[ ]** **Happy Path:** Ver todas las tareas asignadas.
- **[ ]** **Casos Límite:** Vista para usuario sin tareas o sin proyectos.

---

## Fase 5: Revisión Final y Pase a Producción
- **[ ]** **5.1.** Ejecutar todas las pruebas una última vez.
- **[ ]** **5.2.** Backup de BBDD de producción.
- **[ ]** **5.3.** Merge de `release/pre-launch-testing` a `main`.
- **[ ]** **5.4.** Despliegue a producción.
- **[ ]** **5.5.** Monitorización intensiva de logs y rendimiento.
