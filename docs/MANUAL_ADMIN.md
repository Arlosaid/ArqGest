# 🏗️ ARC Manager - Manual del Panel de Administración

## 📋 Resumen
Este manual está diseñado para personal no técnico que necesite administrar el sistema ARC Manager desde el panel de administración de Django.

## 🔐 Acceso al Panel
- **URL:** `http://tudominio.com/admin/` (o `http://localhost:8000/admin/` en desarrollo)
- **Credenciales:** Solo superusuarios pueden acceder al panel de admin
- **Importante:** Los superusuarios NO pueden acceder a la aplicación principal, solo al admin

## 🏠 Dashboard Principal

Al acceder al admin verás:
- **📊 Estadísticas en tiempo real** del sistema con métricas financieras
- **🚀 Accesos rápidos** a las funciones más usadas
- **💰 Dashboard financiero** con ingresos y suscripciones
- **🚨 Alertas automáticas** para upgrades pendientes y suscripciones próximas a vencer
- **💡 Guía de soporte** para tareas comunes

## 👥 Gestión de Usuarios

### ➕ Crear Nuevo Usuario
1. Ve a "Usuarios" → "Agregar usuario"
2. Completa los campos:
   - **Email:** Obligatorio (será el username)
   - **Nombre:** Obligatorio
   - **Apellido:** Obligatorio
   - **Organización:** Selecciona de la lista
3. **La contraseña se genera automáticamente** y se envía por email
4. Haz clic en "Guardar"

### ✏️ Editar Usuario Existente
1. Ve a "Usuarios" y busca al usuario
2. Haz clic en su nombre/email
3. Puedes modificar:
   - Información personal
   - Estado activo/inactivo
   - Permisos (Admin de org, Staff, Superusuario)
   - Organización

### 🔧 Acciones Masivas en Usuarios
Selecciona varios usuarios y usa las acciones:
- **✅ Activar usuarios:** Habilita el acceso
- **❌ Desactivar usuarios:** Deshabilita el acceso (sin borrar)
- **👨‍💼 Hacer admin de org:** Concede permisos administrativos
- **👤 Quitar admin de org:** Quita permisos administrativos
- **🔑 Forzar cambio de contraseña:** Genera enlaces de reset
- **📧 Reenviar credenciales:** Envía nuevas credenciales por email

## 🏢 Gestión de Organizaciones

### ➕ Crear Nueva Organización
1. Ve a "Organizaciones" → "Agregar organización"
2. Completa:
   - **Nombre:** Obligatorio
   - **Descripción:** Opcional
   - **Estado:** Activa por defecto

### 📊 Ver Estado de Organización
En la lista de organizaciones verás:
- **Nombre y estado**
- **Número de usuarios**
- **Estado de suscripción** con colores:
  - 🟢 Activa: Funcionando normalmente
  - 🟡 En Gracia: Vencida pero con período de gracia
  - 🔴 Expirada: Vencida sin acceso
  - 🔵 Trial: Período de prueba

### 🔗 Gestionar Suscripción
Desde la organización, haz clic en:
- **📝 Gestionar suscripción:** Si ya existe
- **➕ Crear suscripción:** Si no existe

## 💳 Gestión de Suscripciones

### 🗓️ Extender Suscripción Manualmente
1. Ve a "Suscripciones"
2. Selecciona las suscripciones a extender
3. En "Acción" selecciona "🗓️ Extender suscripción manualmente"
4. Especifica número de días y razón
5. Haz clic en "Extender Suscripciones"

### 💰 Procesar Pago Recibido
1. Ve a "Suscripciones"
2. Selecciona las suscripciones pagadas
3. En "Acción" selecciona "💰 Procesar pago recibido y extender suscripción"
4. Automáticamente extiende por el período del plan

### 🔄 Cambiar Plan
1. Ve a "Suscripciones"
2. Selecciona las suscripciones
3. En "Acción" selecciona "🔄 Cambiar plan manualmente"
4. Selecciona el nuevo plan
5. Confirma el cambio

### ✅ Aprobar Solicitudes de Upgrade
1. Ve a "Upgrade requests"
2. Verás solicitudes pendientes con estado "Pendiente"
3. Opciones:
   - **Botón "Aprobar":** Aprueba y actualiza automáticamente
   - **Botón "Rechazar":** Rechaza la solicitud
   - **Acciones masivas:** Para múltiples solicitudes
4. **Dashboard financiero:** Acceso directo desde el panel principal para ver todas las solicitudes

### 💰 Dashboard Financiero
1. Accede desde el panel principal o ve a "Dashboard Financiero"
2. Verás:
   - **Ingresos totales** y del mes actual
   - **Desglose mensual** de los últimos 6 meses
   - **Solicitudes de upgrade** detalladas con botones de acción
   - **Alertas financieras** para suscripciones próximas a vencer

## 📋 Gestión de Proyectos

### 👁️ Ver Proyectos
En la lista de proyectos verás:
- **Información básica:** Nombre, organización, cliente
- **Propietario:** Con enlace al usuario
- **Progreso de fases:** Barra visual de progreso
- **Resumen de tareas:** Completadas, en progreso, pendientes

### 📊 Duplicar Proyectos
1. Selecciona proyectos
2. Acción "📋 Duplicar proyectos seleccionados"
3. Se crean copias con "(Copia)" en el nombre

### 🔧 Gestionar Fases
- **Estados posibles:** Pendiente, En Progreso, Completado
- **Acciones masivas:** Cambiar estado de múltiples fases
- **Progreso visual:** Ver tareas completadas/total

### ✅ Gestionar Tareas
- **Estados:** Por Hacer, En Progreso, En Pausa, Hecho
- **Prioridades:** Baja 🟢, Media 🟡, Alta 🟠
- **Acciones útiles:**
  - **✅ Marcar como completadas**
  - **🔄 Marcar como en progreso**
  - **⏳ Marcar como pendientes**
  - **👤 Asignarme estas tareas**

## 📁 Gestión de Archivos

### 👁️ Ver Archivos
Los archivos se muestran con:
- **Icono según tipo:** 📄 PDF, 📝 Word, 📊 Excel, 🖼️ Imágenes, etc.
- **Tamaño con colores:**
  - Verde: < 1MB
  - Naranja: 1-10MB
  - Rojo: > 10MB
- **Enlaces:** A fase y proyecto

### 📊 Calcular Almacenamiento
1. Selecciona archivos
2. Acción "📊 Calcular uso de almacenamiento"
3. Ve el total en GB usado

### 🔍 Funcionalidades Avanzadas de Archivos
- **Iconos por tipo:** 📄 PDF, 📝 Word, 📊 Excel, 🖼️ Imágenes, 📐 CAD
- **Colores por tamaño:**
  - Verde: < 1MB
  - Naranja: 1-10MB  
  - Rojo: > 10MB
- **Enlaces directos:** A fase y proyecto relacionados
- **Descarga directa:** Botones de descarga en cada archivo

## 🔧 Tareas de Soporte Comunes

### 🚨 Usuario No Puede Acceder
1. **Verificar estado:** Usuario activo
2. **Verificar organización:** Asignada correctamente
3. **Verificar suscripción:** Organización con suscripción activa
4. **Reenviar credenciales:** Si olvidó contraseña

### 🚨 Organización Sin Acceso
1. **Verificar suscripción:** Estado activo
2. **Verificar fechas:** No vencida
3. **Procesar pago:** Si recibieron pago
4. **Extender manualmente:** En casos especiales

### 🚨 Problemas con Proyectos
1. **Verificar propietario:** Usuario activo
2. **Verificar organización:** Activa con suscripción
3. **Revisar permisos:** Usuario con permisos correctos

## ⚠️ Códigos de Estado Importantes

### Estados de Suscripción
- **🟢 Activa:** Funcionando normalmente
- **🟡 En Gracia:** Vencida pero con período de gracia (7 días)
- **🔴 Expirada:** Vencida, sin acceso
- **🔵 Trial:** Período de prueba

### Estados de Usuario
- **🔑 Superusuario:** Acceso total al admin (color rojo)
- **👔 Staff:** Acceso al admin limitado (color azul)
- **👨‍💼 Admin Org:** Administrador de organización (color verde)
- **👤 Usuario:** Usuario normal (color gris)

### Estados de Tareas
- **⏳ Por Hacer:** No iniciada (naranja)
- **🔄 En Progreso:** Trabajando en ella (azul)
- **⏸️ En Pausa:** Detenida temporalmente (rojo)
- **✅ Hecho:** Completada (verde)

## 🔍 Filtros y Búsquedas

### Filtros Útiles
- **Por organización:** En usuarios, proyectos, archivos
- **Por estado:** En suscripciones, tareas, fases
- **Por fecha:** En todas las entidades
- **Por prioridad:** En tareas
- **Por tipo de archivo:** En archivos (PDF, DWG, etc.)
- **Por método de pago:** En pagos

### Búsquedas
- **Usuarios:** Por nombre, email, organización
- **Proyectos:** Por nombre, cliente, descripción
- **Tareas:** Por título, descripción, asignado
- **Archivos:** Por nombre, proyecto, usuario
- **Pagos:** Por organización, método, estado

## 📊 Funcionalidades Avanzadas del Admin

### 🎯 Acciones Masivas Inteligentes
- **Selección múltiple:** Usa checkboxes para seleccionar varios elementos
- **Acciones en lote:** Aplicar cambios a múltiples registros
- **Confirmación:** Sistema de confirmación para acciones críticas

### 📈 Métricas y Estadísticas
- **Dashboard en tiempo real:** Métricas actualizadas automáticamente
- **Exportación de datos:** Funcionalidad Import/Export integrada
- **Reportes visuales:** Gráficos y estadísticas en el dashboard

### 🔗 Enlaces y Navegación
- **Enlaces cruzados:** Navegación rápida entre entidades relacionadas
- **Breadcrumbs:** Navegación clara en el admin
- **Accesos directos:** Botones de acción rápida en listas

## 📞 Contacto de Soporte

Si necesitas ayuda adicional:
- **Email:** soporte@tuempresa.com
- **Teléfono:** 55 1234 5678

## 🚀 Nuevas Funcionalidades del Panel Admin

### 💰 Dashboard Financiero Avanzado
- **Métricas en tiempo real:** Ingresos totales y mensuales
- **Desglose por meses:** Últimos 6 meses con gráficos
- **Solicitudes de upgrade:** Vista detallada con acciones rápidas
- **Alertas automáticas:** Suscripciones próximas a vencer

### 🎨 Interfaz Mejorada
- **Diseño moderno:** Interfaz visual atractiva y profesional
- **Iconos y colores:** Identificación rápida de estados y tipos
- **Navegación optimizada:** Accesos directos y breadcrumbs
- **Responsive:** Funciona en diferentes dispositivos

### ⚡ Acciones Masivas Optimizadas
- **Procesamiento en lote:** Múltiples operaciones simultáneas
- **Confirmaciones inteligentes:** Sistema de seguridad para acciones críticas
- **Feedback visual:** Confirmaciones y mensajes de estado
- **Exportación de datos:** Funcionalidad Import/Export integrada

### 🔍 Búsqueda y Filtros Avanzados
- **Filtros múltiples:** Combinación de criterios de búsqueda
- **Búsqueda global:** En todos los campos relevantes
- **Autocompletado:** Sugerencias inteligentes
- **Historial de búsquedas:** Acceso rápido a búsquedas frecuentes

---

*Manual actualizado para ARC Manager v1.0 - Panel de Administración Avanzado*
