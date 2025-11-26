# 🧪 Guía de Pruebas Manuales - Modales de Eliminación

## 📋 Resumen de Modales Implementados

Todos los modales del sistema están homogeneizados con un diseño consistente, centrado y visualmente atractivo.

---

## 1️⃣ Modal de Eliminación de ARCHIVOS

### 📍 **Ubicación:**
- Cualquier vista que muestre archivos (pestañas de Archivos en proyectos)
- Modal de carga de archivos

### 🎯 **Cómo Probar:**

1. **Ir a un proyecto**
   - Navega a: `Proyectos` → Selecciona un proyecto → Pestaña `Archivos`

2. **Subir un archivo de prueba**
   - Click en `Subir Archivos`
   - Selecciona cualquier archivo (PDF, imagen, etc.)
   - Espera a que termine la carga

3. **Eliminar el archivo**
   - Busca el archivo en la lista
   - Click en el icono de **basura** (🗑️)
   - **Debe aparecer:** Modal centrado mostrando:
     - ✅ Icono de archivo grande
     - ✅ Nombre del archivo
     - ✅ Tamaño del archivo
     - ✅ Tipo de archivo
     - ✅ Advertencia: "Esta acción no se puede deshacer"
     - ✅ Botones: "Cancelar" y "Eliminar archivo"

4. **Verificar funcionalidad:**
   - Click en "Cancelar" → Modal debe cerrarse
   - Click nuevamente en basura → Click en "Eliminar archivo"
   - **Debe:** Mostrar spinner → Cerrar modal → Archivo desaparece con animación → Toast de éxito

---

## 2️⃣ Modal de Eliminación de TAREAS

### 📍 **Ubicaciones:**
1. Vista Kanban principal
2. Modal de edición de tareas
3. Detalles de proyecto (pestaña Tareas)
4. Tablero Kanban alternativo
5. Mis Tareas (usa modal propio, diferente diseño)

### 🎯 **Cómo Probar:**

#### **Opción A: Desde Kanban**
1. Navega a: `Proyectos` → Selecciona un proyecto → `Gestionar Tareas`
2. Crea una tarea de prueba:
   - Click en "+ Nueva Tarea"
   - Título: "Tarea de Prueba para Eliminar"
   - Fase: Selecciona cualquiera
   - Click en "Crear Tarea"
3. **Eliminar la tarea:**
   - Busca la tarjeta de la tarea
   - Click en el icono de **basura** (🗑️)
   - **Debe aparecer:** Modal mostrando:
     - ✅ Título de la tarea
     - ✅ Descripción (si la tiene)
     - ✅ Icono de tareas (📋)
     - ✅ Mensaje de confirmación
     - ✅ Botones: "Cancelar" y "Eliminar tarea"

#### **Opción B: Desde Modal de Edición**
1. En el Kanban, click en una tarea para abrir detalles
2. Click en botón "Editar"
3. En el modal de edición, busca el botón "Eliminar tarea" (abajo)
4. Click en "Eliminar tarea"
5. **Debe aparecer:** El mismo modal de confirmación

#### **Opción C: Desde Mis Tareas**
1. Navega a: Menú lateral → `Mis Tareas`
2. Busca una tarea asignada a ti
3. Click en el icono de basura
4. **Nota:** Este usa un modal diferente (implementación anterior), pero debe funcionar

---

## 3️⃣ Modal de Eliminación de PROYECTOS ⭐ (RECIÉN ACTUALIZADO)

### 📍 **Ubicaciones:**
1. Lista de proyectos (botón de basura en cada tarjeta)
2. Detalle de proyecto (botón "Eliminar")

### 🎯 **Cómo Probar:**

#### **Preparación:**
1. Crea un proyecto de prueba con contenido:
   ```
   Nombre: "Proyecto de Prueba - Eliminar"
   Cliente: (cualquiera)
   ```
2. Agrega contenido al proyecto:
   - **Fases:** Crea 2-3 fases
   - **Tareas:** Crea 3-5 tareas en diferentes fases
   - **Archivos:** Sube 2-3 archivos
   - **Documentos:** Sube 1-2 PDFs o documentos

#### **Prueba desde Lista de Proyectos:**
1. Navega a: `Proyectos`
2. Busca la tarjeta del proyecto de prueba
3. Click en el icono de **basura** (🗑️) en la esquina
4. **Debe aparecer:** Modal centrado mostrando:
   - ✅ Título: "Confirmar eliminación de proyecto"
   - ✅ Nombre del proyecto resaltado
   - ✅ Mensaje: "Se eliminarán todos los elementos asociados:"
   - ✅ **Estadísticas visuales:**
     - 📊 X Fases
     - ✅ X Tareas
     - 📁 X Archivos
     - 📄 X Documentos
   - ✅ Advertencia: "Esta acción no se puede deshacer"
   - ✅ Botones: "Cancelar" y "Sí, eliminar proyecto"

5. **Verificar datos:**
   - Los números deben coincidir con lo que creaste
   - Si no hay documentos, no debe aparecer ese contador

6. **Prueba de cancelación:**
   - Click en "Cancelar" → Modal se cierra, proyecto sigue ahí

7. **Prueba de eliminación:**
   - Click nuevamente en basura
   - Click en "Sí, eliminar proyecto"
   - **Debe:** Mostrar spinner → Modal se cierra → Proyecto desaparece → Redirección a lista de proyectos → Toast de éxito

#### **Prueba desde Detalle de Proyecto:**
1. Entra a cualquier proyecto
2. Click en botón "Eliminar" (arriba a la derecha)
3. Debe aparecer el mismo modal con las mismas estadísticas

---

## 4️⃣ Modal de Eliminación de PAGOS

### 📍 **Ubicaciones:**
1. Formulario de edición de pago
2. Detalle de proyecto (pestaña de finanzas/pagos)

### 🎯 **Cómo Probar:**

1. **Crear un pago:**
   - Navega a un proyecto con presupuesto configurado
   - Ir a la sección de Finanzas/Pagos
   - Crear un pago de prueba:
     ```
     Monto: $5000
     Descripción: "Anticipo de prueba"
     Fecha: (hoy)
     ```

2. **Eliminar desde lista de pagos:**
   - En la lista de pagos del proyecto
   - Click en icono de basura del pago
   - **Debe aparecer:** Modal mostrando:
     - ✅ Descripción del pago
     - ✅ Monto
     - ✅ Fecha
     - ✅ Icono de dólar ($)
     - ✅ Botones: "Cancelar" y "Eliminar pago"

3. **Eliminar desde formulario:**
   - Click en "Editar" un pago
   - En el formulario de edición, busca botón "Eliminar"
   - Click en "Eliminar"
   - Debe aparecer el mismo modal

---

## 5️⃣ Modal de Eliminación de USUARIOS

### 📍 **Ubicación:**
- Lista de usuarios (solo para administradores)

### 🎯 **Cómo Probar:**

1. **Requisito:** Debes ser administrador de la organización
2. Navega a: Menú → `Usuarios`
3. Busca un usuario que no seas tú (o crea uno de prueba)
4. Click en el icono de **basura** (🗑️)
5. **Debe aparecer:** Modal mostrando:
   - ✅ Nombre completo del usuario
   - ✅ Email del usuario
   - ✅ Icono de usuario (👤)
   - ✅ Badge/etiqueta
   - ✅ Botones: "Cancelar" y "Eliminar usuario"

---

## 6️⃣ Modal de Eliminación de CLIENTES

### 📍 **Ubicación:**
- Lista de clientes

### 🎯 **Cómo Probar:**

#### **Caso A: Cliente SIN proyectos**
1. Navega a: `Clientes`
2. Crea un cliente nuevo de prueba:
   ```
   Nombre: "Cliente Sin Proyectos"
   ```
3. Click en icono de basura del cliente
4. **Debe aparecer:** Modal mostrando:
   - ✅ Nombre del cliente
   - ✅ Icono de edificio (🏢)
   - ✅ Mensaje simple de confirmación
   - ✅ Sin estadísticas ni warnings
   - ✅ Botones: "Cancelar" y "Sí, eliminar cliente"

#### **Caso B: Cliente CON proyectos**
1. Crea otro cliente: "Cliente Con Proyectos"
2. Crea 2-3 proyectos asignados a este cliente
3. Vuelve a `Clientes`
4. Click en basura del cliente con proyectos
5. **Debe aparecer:** Modal mostrando:
   - ✅ Nombre del cliente
   - ✅ **Advertencia:** "Este cliente tiene X proyecto(s) asociado(s)"
   - ✅ **Contador visual:** "X Proyectos afectados"
   - ✅ Explicación: "Al eliminar el cliente, estos proyectos quedarán desvinculados"
   - ✅ Icono amarillo/warning
   - ✅ Botones: "Cancelar" y "Sí, eliminar cliente"

---

## 7️⃣ Modal de Eliminación de PLANTILLAS DE FASE

### 📍 **Ubicaciones:**
1. Lista de plantillas
2. Detalle de plantilla
3. Formulario de plantilla

### 🎯 **Cómo Probar:**

1. **Crear plantilla:**
   - Navega a: `Proyectos` → `Plantillas de Fase` (o similar)
   - Crear nueva plantilla:
     ```
     Nombre: "Plantilla de Prueba"
     Fases: Agrega 3-4 fases
     ```

2. **Eliminar desde lista:**
   - En la lista de plantillas
   - Click en icono de basura
   - **Debe aparecer:** Modal mostrando:
     - ✅ Nombre de la plantilla
     - ✅ Icono de capas (📚)
     - ✅ Contador: "X Fases en la plantilla"
     - ✅ Botones: "Cancelar" y "Eliminar plantilla"

3. **Eliminar desde detalle:**
   - Click en una plantilla para ver detalle
   - Click en botón "Eliminar"
   - Debe aparecer el mismo modal

---

## 8️⃣ Modal de Eliminación de FASES

### 📍 **Ubicación:**
- Edición de fases de un proyecto

### 🎯 **Cómo Probar:**

1. Navega a un proyecto
2. Click en "Editar Fases"
3. En la lista de fases, click en el icono de basura de cualquier fase
4. **Debe aparecer:** Modal mostrando:
   - ✅ Nombre de la fase
   - ✅ **Estadísticas:**
     - Tareas en la fase
     - Archivos asociados
   - ✅ Advertencia visual
   - ✅ Botones: "Cancelar" y "Eliminar"

**Nota:** Este modal ya existía previamente pero fue mejorado con los estilos unificados.

---

## ✅ Checklist General de Pruebas

Para cada modal, verifica:

### **Diseño Visual:**
- [ ] Modal aparece centrado vertical y horizontalmente
- [ ] Animación suave de entrada (fade in + scale)
- [ ] Header con gradiente (rojo para eliminaciones, amarillo para warnings)
- [ ] Icono grande y centrado (3rem)
- [ ] Texto legible y bien espaciado
- [ ] Tarjetas de detalles con sombra (si aplica)
- [ ] Estadísticas con iconos y números grandes (si aplica)
- [ ] Advertencia final destacada
- [ ] Botones con iconos

### **Funcionalidad:**
- [ ] Click en "Cancelar" cierra el modal sin hacer nada
- [ ] Click fuera del modal NO cierra (backdrop static)
- [ ] Tecla ESC cierra el modal
- [ ] Click en "X" cierra el modal
- [ ] Click en "Confirmar/Eliminar":
  - [ ] Botón muestra spinner
  - [ ] Botón dice "Procesando..."
  - [ ] Botón queda deshabilitado
  - [ ] Modal se cierra al completar
  - [ ] Elemento desaparece de la lista
  - [ ] Toast/notificación de éxito aparece
  - [ ] Redirección (si aplica)

### **Responsive:**
- [ ] **Desktop:** Modal ancho ~540px, bien espaciado
- [ ] **Tablet:** Modal se adapta al ancho disponible
- [ ] **Mobile:** Modal full-width con padding reducido

### **Errores:**
- [ ] Si hay error de red: Mensaje de error aparece
- [ ] Botón se reactiva para reintentar
- [ ] Modal permanece abierto para ver el error

---

## 🐛 Problemas Comunes y Soluciones

### **Modal no aparece:**
1. Abrir consola del navegador (F12)
2. Buscar errores en rojo
3. Verificar que `confirmation-modals.js` se cargó
4. Verificar que el script específico se cargó (ej: `project-delete.js`)

### **Modal aparece pero sin estilos:**
1. Verificar que `confirmation_modals.css` se cargó
2. Limpiar caché del navegador (Ctrl + Shift + R)
3. Verificar en Network tab que los archivos CSS se descargaron

### **Estadísticas incorrectas:**
1. El endpoint `/projects/{id}/stats/` debe funcionar
2. Verificar en Network tab la respuesta JSON
3. Números deben coincidir con la realidad del proyecto

### **Click no hace nada:**
1. Verificar que hiciste click en el icono de basura correcto
2. Verificar en consola si hay errores JavaScript
3. Verificar que el elemento tiene el atributo correcto (ej: `data-action="delete-task"`)

---

## 📊 Resumen de Archivos

### **CSS:**
- `arc_manager/static/css/confirmation_modals.css`

### **JavaScript:**
- `arc_manager/static/js/confirmation-modals.js` (clase base)
- `arc_manager/static/js/file-delete.js`
- `arc_manager/static/js/task-delete.js`
- `arc_manager/static/js/project-delete.js`
- `arc_manager/static/js/payment-delete.js`
- `arc_manager/static/js/client-delete.js`
- `arc_manager/static/js/template-delete.js`

### **Backend:**
- `arc_manager/apps/projects/views.py` → `get_project_stats()`
- `arc_manager/apps/projects/urls.py` → ruta `/projects/<pk>/stats/`

---

## 🎯 Prioridad de Pruebas

Si tienes tiempo limitado, prueba en este orden:

1. **ALTA PRIORIDAD:**
   - ✅ Proyectos (recién actualizado)
   - ✅ Tareas (más usado)
   - ✅ Archivos (funcionalidad crítica)

2. **MEDIA PRIORIDAD:**
   - ✅ Clientes (con y sin proyectos)
   - ✅ Usuarios
   - ✅ Pagos

3. **BAJA PRIORIDAD:**
   - ✅ Plantillas
   - ✅ Fases

---

**Última actualización:** 25/11/2025
**Estado:** ✅ Sistema completamente homogeneizado
