# Plan de Mejora y Refactorización de ArcManager (Versión Final)

**Objetivo:** Elevar la calidad, el rendimiento, la mantenibilidad y la experiencia de usuario de la aplicación a través de una serie de tareas de auditoría, limpieza de código, y rediseño estratégico antes de la fase de pruebas intensivas.

---

## Sección 1: Auditoría Profunda de Backend y Base de Datos

*El objetivo es asegurar que el núcleo de la aplicación sea lo más eficiente y limpio posible, optimizando flujos de datos y configuraciones.*

- **[X]** **1.1. Auditoría de `settings.py`:**
    - **[X]** Limpieza de variables y configuraciones no utilizadas.
    - **[X]** Validación del orden y necesidad de todas las `INSTALLED_APPS` y `MIDDLEWARE`.
    - **[X]** Asegurar que la configuración de `LOGGING` es robusta para producción.

- **[X]** **1.2. Optimización de Flujos y Base de Datos:**
    - **[X]** **Análisis de Modelos (`models.py`):**
        - **[X]** Revisar todos los modelos y sus campos. ¿Hay campos que no se usan? ¿Los `on_delete` tienen la estrategia correcta (`PROTECT`, `SET_NULL`, etc.)?
        - **[X]** Añadir índices de base de datos (`db_index=True`) a los campos que se usan frecuentemente en filtros (`filter()`) o búsquedas, como fechas, estados o claves foráneas.
    - **[X]** **Prevención de Consultas N+1:**
        - **[X]** Usar `django-debug-toolbar` para identificar y eliminar consultas duplicadas en las vistas más importantes (Kanban, Listas, etc.) mediante `select_related` y `prefetch_related`.
    - **[X]** **Revisión de Lógica de Negocio en Vistas:**
        - **[X]** Identificar si hay lógica de negocio compleja dentro de las vistas (`views.py`). Considerar moverla a "managers" de modelos personalizados o a archivos de servicios (ej. `services.py`) para hacer las vistas más limpias y reutilizar el código.

---

## Sección 2: Revisión de Middlewares y Comandos de Gestión

*El objetivo es asegurar que los componentes de lógica transversal (middlewares) y las tareas de automatización (comandos) sean robustos, seguros y sigan las mejores prácticas para un entorno de producción.*

- **[X]** **2.1. Auditoría y Refactorización de Middlewares:**
    - **[X]** Revisar todos los middlewares personalizados (`accounts`, `orgs`, `plans`).
    - **[X]** Confirmar que su lógica es eficiente y no introduce cuellos de botella.
    - **[X]** Verificar que el orden de los middlewares en `settings.py` es el correcto y está justificado.
    - **[X]** Simplificar o combinar middlewares si es posible para reducir la sobrecarga en cada petición.

- **[X]** **2.2. Optimización de Comandos de Gestión para Producción:**
    - **[X]** **Comando `setup_database`:**
        - **[X]** Modificar el comando para que sea **idempotente**: si se ejecuta varias veces, no debe crear duplicados ni fallar. Debe verificar si el superusuario ya existe antes de intentar crearlo.
        - **[X]** Integrar la ejecución de este comando en el script de entrada del contenedor Docker (`entrypoint.sh` o similar) para que se ejecute automáticamente al iniciar el servicio, asegurando que la base de datos siempre tenga los datos iniciales necesarios (como el admin).
        - **[X]** Asegurarse de que las credenciales del admin se tomen de variables de entorno (`os.environ.get()`) en lugar de estar hardcodeadas, por seguridad.
    - **[X]** **Revisión General de Comandos:**
        - **[X]** Auditar todos los comandos de gestión (`clean_data`, `create_organization`, etc.).
        - **[X]** Asegurarse de que emiten salidas claras y útiles (usando `self.stdout.write`).
        - **[X]** Añadir confirmaciones para operaciones destructivas (ej. "¿Estás seguro de que quieres borrar todos los datos de prueba?").

---

## Sección 3: Overhaul del Panel de Administración de Django

*Transformar el panel de admin en un Centro de Control Administrativo completo, intuitivo y potente.*

- **[X]** **3.1. Mejora de la Visualización y Usabilidad (UI/UX):**
    - **[X]** Para **todos** los modelos importantes (`User`, `Organization`, `Project`, `Task`, `PlanSubscription`, etc.):
        - **[X]** Usar `list_display` para mostrar las columnas más relevantes.
        - **[X]** Usar `list_filter` para añadir filtros intuitivos (ej. filtrar usuarios por organización, proyectos por estado).
        - **[X]** Usar `search_fields` para permitir búsquedas eficientes (ej. buscar usuario por email, proyecto por nombre).
        - **[X]** Usar `readonly_fields` para mostrar información no editable (ej. `created_at`, `updated_at`).
        - **[X]** Usar `inlines` para gestionar modelos relacionados en la misma página (ej. ver y editar las tareas de un proyecto directamente desde la página del proyecto en el admin).

- **[ ]** **3.2. Implementación de Acciones Administrativas (Plan B):**
    - **[X]** **Gestión de Usuarios:**
        - **[X]** Crear una **acción de administrador** para "Forzar cambio de contraseña". Esta acción debería generar un enlace de reseteo de un solo uso y mostrarlo al admin para que pueda enviarlo manualmente al usuario.
        - **[X]** Crear una acción para "Reenviar correo de bienvenida/verificación".
    - **[ ]** **Gestión de Suscripciones (Planes):**
        - **[ ]** Crear una acción para "Extender suscripción", que permita a un admin añadir días a la fecha de expiración de un plan para una organización específica.
        - **[ ]** Crear una acción para "Cambiar plan manualmente" a una organización.
    - **[ ]** **Gestión de Datos:**
        - **[ ]** Implementar `django-import-export` para los modelos clave. Esto permitirá exportar datos a Excel/CSV y, más importante, realizar modificaciones masivas e importarlas de nuevo, una herramienta de gestión extremadamente potente.

---

## Sección 4: Refactorización y Mejora del Frontend
*Organizar, limpiar y mejorar la interfaz de usuario.*
- **[ ]** **4.1. Auditoría de la Arquitectura de Plantillas:** Confirmar herencia de `base.html` y uso de bloques.
- **[ ]** **4.2. Estructuración de CSS y JS:** Mover código específico de página a sus propios archivos.
- **[ ]** **4.3. Corrección de Estilos:** Arreglar componentes rotos o sin estilo.

---

## Sección 5: Rediseño de la Experiencia de Usuario (UX) y Flujos Clave
*Hacer la aplicación más intuitiva y agradable.*
- **[ ]** **5.1. Rediseño del Sidebar (Barra Lateral Contextual):** Hacer que la barra lateral cambie su contenido cuando se está dentro de un proyecto.
- **[ ]** **5.2. Mejora del Acceso al Kanban:** Acceso directo desde un dashboard mejorado y creación de una vista de "Kanban General" del proyecto.

---

## Sección 6: Sistema de Notificaciones
*Implementar un sistema de notificaciones moderno y funcional.*
- **[ ]** **6.1. Rediseño Estético y Funcional:** Integrar una librería como `Toastify.js` y estilizarla.
- **[ ]** **6.2. Revisión de la Lógica de Disparo (Triggers):** Configurar notificaciones para eventos clave.

---

## Sección 7: Auditoría de Estructura y Limpieza de Archivos
*El objetivo es simplificar el proyecto eliminando todo lo que no sea estrictamente necesario, reduciendo la complejidad y facilitando el mantenimiento futuro.*

- **[ ]** **7.1. Análisis del Árbol de Archivos:**
    - **[ ]** Revisar la estructura completa del proyecto. ¿Hay carpetas o archivos fuera de lugar? ¿Se puede simplificar la anidación de directorios?
    - **[ ]** Identificar y eliminar archivos de configuración obsoletos o duplicados.
- **[ ]** **7.2. Eliminación de Código Muerto y Archivos No Utilizados:**
    - **[ ]** **Vistas y URLs:** Rastrear todas las URLs para asegurarse de que apuntan a vistas que se utilizan. Eliminar vistas y rutas huérfanas.
    - **[ ]** **Templates:** Buscar plantillas (`.html`) que no son renderizadas por ninguna vista.
    - **[ ]** **Archivos Estáticos:** Identificar archivos CSS, JS o imágenes que no se cargan en ninguna plantilla. Herramientas de navegador pueden ayudar a identificar recursos no utilizados en las páginas más visitadas.
    - **[ ]** **Módulos y Funciones de Python:** Utilizar herramientas de análisis estático para encontrar funciones, clases o módulos enteros que no son importados ni llamados en ninguna parte del código.

---

## Sección 8: Creación de Documentación Técnica y de Usuario
*El objetivo es crear una base de conocimiento sólida que facilite la incorporación de nuevos desarrolladores, la gestión de la aplicación por parte de los administradores y el uso diario por parte de los usuarios finales.*

- **[ ]** **8.1. Documentación Técnica:**
    - **[ ]** **Diagrama de Entidad-Relación (DER):** Crear un diagrama visual del esquema de la base de datos que muestre los modelos y sus relaciones.
    - **[ ]** **Diagrama de Arquitectura General:** Ilustrar los componentes principales de la aplicación (e.g., Nginx, Gunicorn, Django, Base de Datos) y cómo interactúan.
    - **[ ]** **Documentación de Código (`Docstrings`):**
        - **[ ]** Añadir `docstrings` explicativos a todos los modelos, detallando el propósito de cada uno.
        - **[ ]** Documentar los servicios (`services.py`), funciones complejas y `managers` personalizados, explicando qué hacen, sus parámetros y lo que retornan.
    - **[ ]** **Guía de Configuración para Desarrolladores (`README.md`):**
        - **[ ]** Mejorar el `README.md` actual para incluir instrucciones paso a paso sobre cómo clonar el repositorio, configurar el entorno de desarrollo con Docker (`docker-compose up`), ejecutar migraciones, crear un superusuario y ejecutar tests.
        - **[ ]** Listar todas las variables de entorno necesarias (`env.example`) con una explicación de cada una.
    - **[ ]** **Documentación de Comandos de Gestión:** Crear un documento (`MANAGEMENT_COMMANDS.md`) que explique el propósito y uso de cada comando personalizado.

- **[ ]** **8.2. Documentación No Técnica (Para el Usuario/Cliente):**
    - **[ ]** **Manual de Usuario Final:**
        - **[ ]** Crear una guía paso a paso (en Markdown o en la propia app) que explique los flujos principales para un usuario normal: crear un proyecto, gestionar tareas, invitar a miembros, etc.
        - **[ ]** Usar capturas de pantalla para ilustrar los pasos.
    - **[ ]** **Manual de Administración de la Organización:**
        - **[ ]** Detallar las funcionalidades disponibles para el dueño o administrador de una organización: gestión de miembros, detalles de la suscripción, configuración, etc.
    - **[ ]** **Guía de Administración del Sistema (Ampliando `PROCEDIMIENTOS_ADMIN.md`):**
        - **[ ]** Expandir el documento existente para que no solo cubra las acciones del admin, sino también los "qué hacer si..." (ej. "Qué hacer si un usuario no recibe el correo de bienvenida", "Cómo extender manualmente una suscripción").

---

## Sección 9: Tareas Críticas Adicionales
*Recomendaciones finales de alto impacto.*
- **[ ]** **9.1. Implementación de Páginas de Error Personalizadas:** Crear plantillas para errores 404 y 500.
- **[ ]** **9.2. Documentación de Procedimientos:** Crear un documento interno simple (`PROCEDIMIENTOS_ADMIN.md`) que explique cómo usar las nuevas acciones del panel de admin. Esto es vital para no olvidar cómo resolver problemas en el futuro.
