# Plan de Acción - ArcManager (Evolución Continua)

## 1. Introducción y Filosofía Central

Este documento refleja la evolución constante de ArcManager. Nuestra meta es crear una herramienta intuitiva, flexible y potente que se adapte al flujo de trabajo real de un arquitecto.

**Filosofía Central: "El Proyecto como Hub Central"**
Hemos abandonado la idea de un único Kanban por proyecto. Ahora, cada proyecto funciona como un **hub centralizado** con pestañas, permitiendo una navegación clara y un acceso rápido a toda la información relevante: Detalles, Fases, Tareas y Archivos.

---

## 2. Flujo de Usuario Esencial (Visión Actual)

**Paso 1: Creación de Proyecto Flexible y Simplificada**
- **[✓] (COMPLETADO Y MEJORADO)**: El usuario crea un proyecto y tiene dos opciones claras para definir las fases:
    1.  **Usar una plantilla de fases**: Selecciona una de sus plantillas predefinidas.
    2.  **Definir fases manualmente**: Añade, elimina y reordena fases directamente en el formulario de creación del proyecto.
- **[✓] (COMPLETADO Y MEJORADO)**: La gestión de plantillas se ha rediseñado por completo. Ahora, desde una única e intuitiva interfaz, el arquitecto puede **crear, ver, editar y eliminar sus plantillas, añadiendo, eliminando y reordenando las fases de forma dinámica**.

**Paso 2: Navegación desde el Hub del Proyecto**
- Al entrar a un proyecto, el usuario aterriza en una vista con 4 pestañas:
    1.  **Detalles**: Información clave del proyecto (cliente, fechas, etc.).
    2.  **Fases**: Un listado de las fases del proyecto. Cada fase es un enlace a su propio tablero.
    3.  **Tareas**: Una lista completa de *todas* las tareas del proyecto, ideal para una visión general.
    4.  **Archivos**: Un repositorio central con todos los archivos del proyecto.

**Paso 3: Gestión de Fases con Kanban Dedicado**
- Al hacer clic en una fase específica, el usuario accede a un **tablero Kanban exclusivo para esa fase**.
- Este tablero muestra las tareas de la fase, organizadas por estado (Por Hacer, En Progreso, etc.), permitiendo una gestión detallada y enfocada del trabajo.

---

## 3. Funcionalidades Clave (Implementadas y Planificadas)

**A. Gestión de Proyectos**
- **[✓]** CRUD completo de Proyectos.
- **[✓]** Vista de "Hub de Proyecto" con pestañas.
- **[✓] (COMPLETADO Y MEJORADO)** Implementado un sistema de **plantillas de fases personalizables**, con una experiencia de usuario fluida y dinámica para el CRUD completo.

**B. Gestión de Fases y Tareas**
- **[✓]** **Kanban a nivel de Fase**: Cada fase tiene su propio tablero para gestionar el ciclo de vida de sus tareas.
- **[✓]** Gestión completa de tareas (crear, editar, asignar, etc.) dentro del contexto de su fase.

**C. Barra Lateral y Navegación**
- **[✓]** **Sidebar rediseñado**: La navegación principal ha sido simplificada para un acceso más rápido a las secciones clave (Dashboard, Proyectos, Mis Tareas, Administración).

**D. Internacionalización (i18n)**
- **[✓] (COMPLETADO)** Se ha traducido al español toda la interfaz de usuario visible en la aplicación de `projects`.
- **[✓] (COMPLETADO)** Se ha verificado que la aplicación de `orgs` ya se encontraba completamente traducida.
- **[✓] (COMPLETADO)** Todos los modelos, formularios y plantillas relevantes usan el sistema de traducción de Django para facilitar el soporte de múltiples idiomas.

---

## 4. Tareas de Desarrollo (Checklist de Evolución)

### Backend (Django)
- **[✓]** **Modelos de Datos:**
    - `Project`, `Phase`, `Task`, `File` (Modelos robustos).
    - **[✓] (SIMPLIFICADO)** `PhaseTemplate` ahora utiliza un campo `JSONField` para almacenar las fases, eliminando la necesidad de `DefaultPhase`.
- **[✓]** **Vistas:**
    - **[✓]** Vistas CRUD para Proyectos, Tareas y Fases.
    - **[✓]** `ProjectDetailView` actualizada para funcionar como hub.
    - **[✓]** **Implementada `PhaseKanbanView` para el tablero por fase.**
    - **[✓] (COMPLETADO Y MEJORADO)** Las vistas CRUD para `PhaseTemplate` ahora usan `formsets` para una gestión dinámica y unificada de las plantillas y sus fases.
    
### Frontend (Django Templates + HTMX)
- **[✓]** **UI/UX:**
    - **[✓]** **Implementada la interfaz de pestañas en la vista de detalle del proyecto.**
    - **[✓]** **Implementada la plantilla para el tablero Kanban a nivel de fase.**
    - **[✓]** **Rediseñada y simplificada la barra de navegación lateral.**
- **[✓] (COMPLETADO Y MEJORADO)** Creadas las plantillas y formularios para la nueva gestión de plantillas de fases (CRUD completo) y para la creación de proyectos, con lógica de JavaScript para una experiencia de usuario dinámica.
- **[✓] (COMPLETADO)** Se han implementado las etiquetas de traducción `{% trans "..." %}` en todas las plantillas para permitir la internacionalización.

---

## 5. Funcionalidades Futuras (Post-Evolución Actual)

Una vez completada la gestión de plantillas personalizables, podríamos explorar:

- Notificaciones y comentarios.
- Control de versiones de archivos.
- Exportación de reportes.
- Roles de usuario avanzados.
- Visor de PDF/DWG con anotaciones.
