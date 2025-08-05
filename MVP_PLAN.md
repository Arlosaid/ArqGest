# Plan de Acción para el MVP - ArcManager

## 1. Introducción y Filosofía Central

Tras analizar las excelentes ideas propuestas, este documento define un plan de acción unificado y simplificado para el **Producto Mínimo Viable (MVP)**. El objetivo es lanzar una herramienta funcional, intuitiva y de alto valor que resuelva los problemas centrales del arquitecto.

**Filosofía Central: "El Proyecto es el Universo"**
Toda la lógica de la aplicación debe girar en torno al proyecto. Un arquitecto no gestiona tareas o archivos aislados, sino que los organiza dentro del contexto de un proyecto específico (Ej: "Casa López"). La interfaz y el flujo deben reflejar esta mentalidad.

---

## 2. Flujo de Usuario Esencial para el MVP

Este es el recorrido principal, optimizado para ser lo más simple y efectivo posible.

**Paso 1: Creación de Proyecto Simplificada**
- El usuario inicia sesión y ve un **Dashboard** limpio, inicialmente vacío, con un llamado a la acción claro: **[+ Crear Nuevo Proyecto]**.
- Al hacer clic, aparece un formulario simple:
    1.  **Nombre del Proyecto** (Campo de texto, obligatorio).
    2.  **Cliente** (Campo de texto, opcional).
    3.  **Plantilla de Fases (Feature Clave)**: Un selector para elegir una estructura predefinida.
        - Opciones: `[Diseño Residencial]`, `[Remodelación]`, `[Proyecto Ejecutivo]`, `[En Blanco]`.
- Al crear el proyecto, se redirige automáticamente a la **Vista de Proyecto**.

**Paso 2: Dashboard Principal**
- Es la pantalla de inicio una vez que existen proyectos.
- Muestra una lista o tarjetas de los proyectos existentes.
- Cada "tarjeta" de proyecto debe mostrar:
    - Nombre del Proyecto.
    - Cliente.
    - Un indicador de progreso simple (ej: "Fase 2 de 5: Anteproyecto").
- Un botón flotante `[+]` siempre visible para crear nuevos proyectos.

**Paso 3: Vista de Proyecto (El Hub Central)**
- Esta es la pantalla más importante. Debe ser limpia y organizada. Se usará una **interfaz de pestañas** para separar contextos y mantener la simplicidad.
- **Header:** Nombre del proyecto siempre visible.
- **Pestañas:**
    - **📁 Fases:** Una lista vertical o timeline simple de las fases del proyecto. Permite ver el macro-progreso.
    - **✅ Tareas (Kanban):** La vista de trabajo principal para el día a día.
    - **🧷 Archivos:** Un repositorio central para todos los documentos del proyecto.

---

## 3. Funcionalidades Clave Detalladas (MVP)

**A. Gestión de Proyectos y Fases (Pestaña `Fases`)**
- Crear/Editar/Eliminar proyectos.
- Lógica para aplicar plantillas de fases al crear un proyecto.
- En la pestaña `Fases`, el usuario puede:
    - Ver la lista de fases.
    - Marcar una fase como: `No Iniciada`, `En Progreso`, `Completada`.
    - Añadir nuevas fases manualmente.

**B. Tablero Kanban de Tareas (Pestaña `Tareas`)**
- Columnas fijas para el MVP: **`Por Hacer`**, **`En Proceso`**, **`Hecho`**.
- Las tareas son tarjetas que se pueden arrastrar y soltar (Drag & Drop) entre columnas.
- Al hacer clic en una tarea, se abre un modal con sus detalles:
    - Título.
    - Descripción.
    - **Fase asociada** (selector para vincular la tarea a una fase).
    - **Archivos adjuntos** a la tarea.
- Un botón `[+ Nueva Tarea]` en la columna "Por Hacer".

**C. Gestión de Archivos (Pestaña `Archivos`)**
- Una galería visual (grid con miniaturas) para todos los archivos del proyecto. Los arquitectos son visuales.
- Funcionalidad para **subir archivos**, idealmente con Drag & Drop desde el escritorio.
- Al subir un archivo, se puede asociar opcionalmente a una **fase**.
- Filtro para ver archivos por fase.

---

## 4. Tareas de Desarrollo (Checklist para el MVP)

Este es el desglose técnico de las tareas necesarias para construir el MVP.

### Backend (Django)
- [ ] **Autenticación:** Sistema de registro y login de usuarios.
- [ ] **Modelos de Datos:**
    - `Project(name, client, owner)`
    - `Phase(name, project, status, order)`
    - `Task(name, description, phase, status)`
    - `File(project, phase, task, uploaded_file)`
- [ ] **APIs (DRF):**
    - [ ] Endpoints CRUD para Proyectos.
    - [ ] Endpoints CRUD para Fases (incluyendo cambio de estado).
    - [ ] Endpoints CRUD para Tareas (incluyendo cambio de estado por D&D).
    - [ ] Endpoint para subida de Archivos.
- [ ] **Lógica de Negocio:**
    - [ ] Implementar la creación de fases a partir de las plantillas predefinidas.

### Frontend (React/Vue/HTMX - a definir)
- [ ] **UI/UX Base:**
    - [ ] Definir paleta de colores (neutros + acento), tipografía e iconografía.
    - [ ] Estructura general: Layout con sidebar/navbar y área de contenido.
- [ ] **Componentes Principales:**
    - [ ] **Página de Login/Registro.**
    - [ ] **Componente: Dashboard de Proyectos** (vista de tarjetas).
    - [ ] **Componente: Formulario de Creación de Proyecto** (con selector de plantillas).
    - [ ] **Componente: Vista de Proyecto** (contenedor con las 3 pestañas).
    - [ ] **Componente: Pestaña Fases** (lista de fases y estados).
    - [ ] **Componente: Tablero Kanban** (columnas, tareas, D&D, modal de detalle).
    - [ ] **Componente: Pestaña Archivos** (grid de archivos, subida con D&D, filtros).

---

## 5. Funcionalidades Post-MVP (Aparcadas para el Futuro)

Para mantener el MVP simple, estas excelentes ideas se dejan para futuras versiones:

- **Visor de PDF/DWG con anotaciones:** Muy potente, pero complejo.
- **Control de versiones de archivos:** (v1, v2, etc.).
- **Comentarios y menciones (`@user`):** Fomenta la colaboración pero no es esencial para el flujo básico.
- **Exportación de reportes en PDF.**
- **Roles de usuario avanzados** (Cliente, Colaborador, Admin).
- **Notificaciones.**
- **Funciones "Wow" complejas:** Escaneo de planos, modo maqueta 3D, etc.
