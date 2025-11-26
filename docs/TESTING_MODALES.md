# 🧪 Guía de Pruebas - Homogeneización de Modales

## Checklist de Verificación Rápida

### ✅ 1. Eliminación de Archivos
**Ubicación:** Cualquier proyecto con archivos

- [ ] Ir a un proyecto con archivos
- [ ] Click en icono de papelera de un archivo
- [ ] **Verificar:** Modal centrado con título "Confirmar eliminación"
- [ ] **Verificar:** Muestra nombre del archivo
- [ ] **Verificar:** Muestra tamaño del archivo
- [ ] **Verificar:** Icono de archivo grande en el centro
- [ ] Click en "Eliminar archivo"
- [ ] **Verificar:** Archivo desaparece con animación
- [ ] **Verificar:** Toast de éxito

---

### ✅ 2. Eliminación de Tareas - Kanban Principal
**Ubicación:** `/projects/{id}/tasks/` (Vista Kanban)

- [ ] Ir al Kanban de un proyecto
- [ ] Hover sobre una tarjeta de tarea
- [ ] Click en icono de papelera (esquina superior derecha)
- [ ] **Verificar:** Modal muestra título de la tarea
- [ ] **Verificar:** Modal centrado y bonito
- [ ] Click en "Eliminar tarea"
- [ ] **Verificar:** Tarjeta desaparece con animación scale

---

### ✅ 3. Eliminación de Tareas - Modal de Edición
**Ubicación:** Modal de edición de tarea

- [ ] Abrir una tarea para editar
- [ ] Click en botón "Eliminar" (rojo, abajo)
- [ ] **Verificar:** Modal de confirmación aparece
- [ ] **Verificar:** Muestra título de la tarea
- [ ] Click en "Eliminar tarea"
- [ ] **Verificar:** Modal se cierra
- [ ] **Verificar:** Tarea desaparece de la lista

---

### ✅ 4. Eliminación de Tareas - Detalle de Proyecto
**Ubicación:** `/projects/{id}/` (Página de detalle)

- [ ] Ir al detalle de un proyecto
- [ ] En la sección de tareas, click en papelera de una tarea
- [ ] **Verificar:** Modal aparece centrado
- [ ] **Verificar:** Muestra título de la tarea
- [ ] Confirmar eliminación
- [ ] **Verificar:** Tarea desaparece con fade out

---

### ✅ 5. Eliminación de Proyectos
**Ubicación:** Lista de proyectos o detalle

- [ ] Ir a `/projects/`
- [ ] Click en "Eliminar" de un proyecto
- [ ] **Verificar:** Modal intercepta el enlace (NO va a otra página)
- [ ] **Verificar:** Modal muestra nombre del proyecto
- [ ] **Verificar:** Muestra estadísticas:
  - [ ] Número de fases
  - [ ] Número de tareas
  - [ ] Número de archivos
- [ ] **Verificar:** Iconos y contadores visibles
- [ ] Click en "Sí, eliminar proyecto"
- [ ] **Verificar:** Redirección a lista de proyectos
- [ ] **Verificar:** Toast de éxito

---

### ✅ 6. Eliminación de Pagos - Formulario
**Ubicación:** Edición de pago

- [ ] Editar un pago existente
- [ ] Click en botón "Eliminar Pago"
- [ ] **Verificar:** Modal muestra descripción del pago
- [ ] **Verificar:** Muestra monto y fecha
- [ ] Confirmar eliminación
- [ ] **Verificar:** Redirección

---

### ✅ 7. Eliminación de Pagos - Lista en Proyecto
**Ubicación:** Detalle de proyecto, sección financiera

- [ ] Ir a detalle de proyecto
- [ ] En sección de pagos, click en papelera
- [ ] **Verificar:** Modal aparece con info del pago
- [ ] Confirmar
- [ ] **Verificar:** Pago desaparece de la lista

---

### ✅ 8. Eliminación de Usuarios
**Ubicación:** `/users/` (Lista de usuarios)

- [ ] Ir a lista de usuarios (solo admins)
- [ ] Click en botón de eliminar (rojo)
- [ ] **Verificar:** Modal muestra nombre completo
- [ ] **Verificar:** Muestra email del usuario
- [ ] **Verificar:** Icono de usuario
- [ ] Confirmar
- [ ] **Verificar:** Redirección con mensaje de éxito

---

### ✅ 9. Eliminación de Clientes - Sin Proyectos
**Ubicación:** `/orgs/clients/`

- [ ] Cliente SIN proyectos asociados
- [ ] Click en eliminar
- [ ] **Verificar:** Modal básico sin advertencias
- [ ] **Verificar:** Muestra nombre del cliente
- [ ] Confirmar
- [ ] **Verificar:** Cliente desaparece de la lista

---

### ✅ 10. Eliminación de Clientes - Con Proyectos
**Ubicación:** `/orgs/clients/`

- [ ] Cliente CON proyectos asociados
- [ ] Click en eliminar
- [ ] **Verificar:** Modal muestra advertencia
- [ ] **Verificar:** Contador de proyectos afectados
- [ ] **Verificar:** Mensaje sobre desvinculación
- [ ] Confirmar
- [ ] **Verificar:** Cliente eliminado, proyectos quedan sin cliente

---

### ✅ 11. Eliminación de Plantillas de Fase
**Ubicación:** `/projects/phase-templates/`

- [ ] Lista de plantillas
- [ ] Click en eliminar plantilla
- [ ] **Verificar:** Modal muestra nombre de la plantilla
- [ ] **Verificar:** Contador de fases en la plantilla
- [ ] Confirmar
- [ ] **Verificar:** Plantilla desaparece

---

### ✅ 12. Eliminación de Fases
**Ubicación:** Edición de fases del proyecto

- [ ] Ir a editar fases de un proyecto
- [ ] Click en eliminar una fase
- [ ] **Verificar:** Modal muestra nombre de la fase
- [ ] **Verificar:** Muestra cantidad de tareas
- [ ] **Verificar:** Muestra cantidad de archivos
- [ ] Confirmar
- [ ] **Verificar:** Fase desaparece

---

## 🎨 Aspectos Visuales a Verificar en TODOS los Modales

### Centrado
- [ ] Modal aparece en el centro de la pantalla (vertical y horizontal)
- [ ] No está pegado arriba ni a un lado

### Header
- [ ] Header con gradiente rojo (tipo danger)
- [ ] Icono de advertencia visible
- [ ] Título claro y legible
- [ ] Botón X en la esquina funciona

### Contenido
- [ ] Icono central grande (3rem) con opacidad
- [ ] Mensaje principal claro
- [ ] Tarjeta de detalles bien formateada (si aplica)
- [ ] Estadísticas con iconos (si aplica)

### Animaciones
- [ ] Modal aparece con fade in
- [ ] Item eliminado desaparece con scale/fade out
- [ ] Transiciones suaves (0.3s)

### Botones
- [ ] Botón "Cancelar" (gris, secundario)
- [ ] Botón "Eliminar" (rojo, con icono)
- [ ] Hover muestra feedback visual
- [ ] Focus visible con outline

### Responsive
- [ ] En desktop: modal ancho adecuado
- [ ] En mobile: modal se adapta al ancho
- [ ] Padding y espaciado correcto

---

## 🐛 Problemas Comunes a Buscar

### ❌ Problemas que NO deberían ocurrir:
- [ ] ~~Modal no centrado~~ - Debe estar perfectamente centrado
- [ ] ~~Aparece `window.confirm()` del navegador~~ - Debe usar modal custom
- [ ] ~~Modal sin animación~~ - Debe tener fade in
- [ ] ~~Falta icono central~~ - Debe mostrar icono grande
- [ ] ~~No muestra información del item~~ - Debe mostrar nombre/título
- [ ] ~~Botones sin iconos~~ - Deben tener iconos FontAwesome
- [ ] ~~Modal sin gradiente en header~~ - Header debe tener gradiente rojo

### ✅ Si encuentras alguno de estos problemas:
1. Verificar que la template incluya los scripts:
   - `confirmation-modals.js`
   - El script específico (`task-delete.js`, `project-delete.js`, etc.)
2. Verificar que base.html incluya `confirmation_modals.css`
3. Revisar consola del navegador por errores JS
4. Verificar que el data-attribute esté correcto (`data-action="delete-task"`)

---

## 📊 Resumen de Cobertura

| Elemento | Ubicaciones | Estado |
|----------|-------------|--------|
| **Archivos** | Vista de archivos | ✅ |
| **Tareas** | Kanban, Modal edición, Detalle proyecto, Mis tareas | ✅ |
| **Proyectos** | Lista, Detalle | ✅ |
| **Pagos** | Formulario, Lista en proyecto | ✅ |
| **Usuarios** | Lista de usuarios | ✅ |
| **Clientes** | Lista de clientes | ✅ |
| **Plantillas** | Lista, Detalle, Formulario | ✅ |
| **Fases** | Edición de fases | ✅ |

---

## ⚡ Prueba Rápida (5 minutos)

Si tienes poco tiempo, prueba estos 5 casos críticos:

1. **Eliminar tarea desde Kanban** (más usado)
2. **Eliminar proyecto** (con estadísticas)
3. **Eliminar archivo** (funcionalidad nueva)
4. **Eliminar cliente con proyectos** (con advertencia)
5. **Eliminar fase con contenido** (con contadores)

---

**¡Listo para probar! 🚀**
