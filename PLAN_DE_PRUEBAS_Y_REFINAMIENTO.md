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

## Fase 3: Pruebas de Rendimiento y Optimización (Repetir)

- **[ ]** **3.1. Análisis con Django Debug Toolbar** (con datos de prueba).
- **[ ]** **3.2. Verificación de la Caché** de Redis.
- **[ ]** **3.3. Optimización de Frontend** con Lighthouse.

---

## Fase 4: Pruebas Funcionales (E2E con Casos de Falla y Planes B)

### **4.1. Módulo de Cuentas, Usuarios y Organización**
- **[ ]** **Happy Paths:**
    - **[ ]** Flujo de registro de organización.
    - **[ ]** Flujo de Login / Logout.
    - **[ ]** Flujo de recuperación de contraseña exitoso (email recibido y link funcional).
- **[ ]** **Unhappy Paths & Casos Límite:**
    - **[ ]** **Registro:**
        - **[ ]** Intentar registrarse con un email ya existente.
        - **[ ]** Intentar registrarse con una contraseña que no cumple los validadores de Django (muy corta, muy común, etc.). Validar mensajes de error específicos.
    - **[ ]** **Login:**
        - **[ ]** Intentar iniciar sesión con un email no registrado.
        - **[ ]** Intentar iniciar sesión con contraseña incorrecta (verificar que `django-axes` funciona).
    - **[ ]** **Recuperación de Contraseña:**
        - **[ ]** Intentar recuperar contraseña para un email no registrado. La aplicación no debe confirmar si el email existe o no (medida de seguridad).
        - **[ ]** Usar un link de recuperación de contraseña por segunda vez después de haber sido utilizado. Debe mostrar un error.
        - **[ ]** Usar un link de recuperación de contraseña expirado (si aplica).
- **[ ]** **Plan B (Procedimientos Administrativos):**
    - **[ ]** **Cambio de Contraseña Forzado:** Un usuario no puede acceder. Acceder al Admin de Django, buscar al usuario y cambiar su contraseña manualmente. Documentar el procedimiento de comunicación con el usuario.
    - **[ ]** **Reenvío de Invitación / Activación:** Si un usuario no recibe su correo de bienvenida/activación, tener un botón en el Admin para "Reenviar email de bienvenida".

### **4.2. Módulo de Plantillas de Fases**
- **[ ]** **Happy Path:** CRUD completo.
- **[ ]** **Unhappy Paths & Casos Límite:**
    - **[ ]** Intentar crear una plantilla con el mismo nombre que otra ya existente en la misma organización.
    - **[ ]** Intentar crear una plantilla sin fases. El sistema debe permitirlo o mostrar un aviso claro.
    - **[ ]** Intentar guardar el formulario de edición de plantillas mientras se está procesando (doble click). El sistema debe manejarlo sin crear duplicados.
    - **[ ]** Crear una plantilla con un nombre muy largo o con caracteres especiales.

### **4.3. Módulo de Proyectos**
- **[ ]** **Happy Path:** Creación manual y desde plantilla, edición, eliminación.
- **[ ]** **Unhappy Paths & Casos Límite:**
    - **[ ]** Intentar crear un proyecto con un nombre duplicado dentro de la misma organización.
    - **[ ]** **Eliminación de dependencias:**
        - **[ ]** Eliminar un `Cliente` que tiene proyectos asociados. ¿Qué ocurre? El sistema debería impedirlo (`PROTECT`) o anonimizar el cliente en el proyecto (depende de la lógica de negocio definida en `on_delete`). Validar este comportamiento.
        - **[ ]** Eliminar una `Plantilla de Fases` ya utilizada. Los proyectos creados a partir de ella **no deben** ser afectados.
    - **[ ]** Intentar modificar la URL para acceder a la vista de creación de proyectos de otra organización.
- **[ ]** **Plan B (Procedimientos Administrativos):**
    - **[ ]** **Reasignación de Proyecto:** Un empleado deja la empresa. Desde el Admin de Django, poder cambiar el "propietario" o "responsable" de un proyecto a otro usuario de la misma organización.
    - **[ ]** **Recuperación de Proyecto:** Un usuario elimina un proyecto por error. Definir el procedimiento de recuperación (desde backup de BBDD, o si se usa `django-safedelete`, "des-eliminar" desde el Admin).

### **4.4. Módulo de Tareas y Kanban**
- **[ ]** **Happy Path:** CRUD de tareas, moverlas entre columnas.
- **[ ]** **Unhappy Paths & Casos Límite:**
    - **[ ]** **Acceso a Fases/Tareas de otro proyecto:** Desde la URL del Kanban (`/project/1/phase/3/kanban/`), intentar cambiar los IDs para acceder a fases de otros proyectos a los que no se tiene acceso. Validar error 404.
    - **[ ]** Intentar crear una tarea sin nombre o título.
    - **[ ]** Asignar una tarea a un usuario y luego eliminar a ese usuario de la organización. ¿Qué pasa con la tarea? ¿Queda sin asignar? ¿Se reasigna? Validar el comportamiento (`on_delete=SET_NULL`).
    - **[ ]** Probar el Kanban con una gran cantidad de tareas (~100) en una sola fase para detectar problemas de rendimiento en el renderizado.

### **4.5. Módulo de Archivos**
- **[ ]** **Happy Path:** Subir, descargar, eliminar.
- **[ ]** **Unhappy Paths & Casos Límite:**
    - **[ ]** Intentar subir un archivo con un nombre extremadamente largo o con caracteres que puedan ser problemáticos para el sistema de archivos (`/`, `\`, `*`). El sistema debe sanitizar el nombre.
    - **[ ]** Subir un archivo, y mientras se sube, cancelar la petición o perder la conexión. El sistema no debe dejar archivos corruptos o a medio subir.
    - **[ ]** Intentar eliminar un archivo mientras otro usuario lo está descargando.

### **4.6. Módulo "Mis Tareas" y Dashboard**
- **[ ]** **Happy Path:** Ver todas las tareas asignadas.
- **[ ]** **Casos Límite:**
    - **[ ]** Vista "Mis Tareas" para un usuario sin tareas asignadas (debe mostrar un mensaje amigable).
    - **[ ]** Vista del Dashboard para un usuario que acaba de unirse y no tiene proyectos ni actividad. La página debe presentarse de forma limpia, sin errores, y quizás con una guía de "primeros pasos".
    - **[ ]** Probar la paginación (si existe) en la lista de proyectos, tareas, etc., navegando a la primera, última y una página intermedia. Intentar acceder a una página que no existe (ej. `?page=999`).

---

## Fase 5: Revisión Final y Pase a Producción
- **[ ]** **5.1.** Ejecutar todas las pruebas una última vez.
- **[ ]** **5.2.** Backup de BBDD de producción.
- **[ ]** **5.3.** Merge de `release/pre-launch-testing` a `main`.
- **[ ]** **5.4.** Despliegue a producción.
- **[ ]** **5.5.** Monitorización intensiva de logs y rendimiento.
