# 📋 Arc Manager - Documentación Funcional Completa

> **Sistema de Gestión de Proyectos Arquitectónicos**  
> Versión MVP - Documentación de Usuario Final

---

## 📖 Índice

1. [Visión General](#-visión-general)
2. [Características Principales](#-características-principales)
3. [Guía de Usuario Completa](#-guía-de-usuario-completa)
4. [Flujos de Trabajo](#-flujos-de-trabajo)
5. [Gestión de Archivos](#-gestión-de-archivos)
6. [Administración](#-administración)
7. [Planes y Suscripciones](#-planes-y-suscripciones)
8. [Solución de Problemas](#-solución-de-problemas)

---

## 🎯 Visión General

### ¿Qué es Arc Manager?

Arc Manager es una **plataforma integral de gestión de proyectos** diseñada específicamente para **estudios de arquitectura y despachos profesionales**. Permite organizar, gestionar y colaborar en proyectos arquitectónicos de manera eficiente, desde la conceptualización hasta la entrega final.

### Casos de Uso Principales

- **Estudios de Arquitectura**: Gestión completa de proyectos residenciales, comerciales e institucionales
- **Despachos de Ingeniería**: Coordinación de proyectos de infraestructura y construcción
- **Consultoras de Construcción**: Seguimiento de múltiples proyectos y equipos
- **Arquitectos Independientes**: Organización personal de cartera de clientes

### Valor Diferencial

✅ **Especializado en Arquitectura**: Diseñado para las necesidades específicas del sector  
✅ **Gestión de Archivos Pesados**: Optimizado para DWG, RVT, PDF de planos (hasta 600MB)  
✅ **Flujo Kanban Visual**: Seguimiento intuitivo del progreso de proyectos  
✅ **Multiorganización**: Un sistema, múltiples estudios independientes  
✅ **Interfaz Profesional**: Diseño moderno y fácil de usar  

---

## 🚀 Características Principales

### 1. **Gestión de Organizaciones** 🏢

**¿Qué es?** Sistema multiteniente que permite que diferentes estudios de arquitectura usen la misma plataforma de forma completamente independiente.

**Funcionalidades:**
- Creación y configuración de organizaciones
- Gestión de información corporativa
- Control de acceso por organización
- Configuración de planes de suscripción

**Casos de Uso:**
- Estudio A gestiona sus 15 proyectos residenciales
- Estudio B maneja sus 8 proyectos comerciales
- Ambos usan la misma plataforma pero con datos completamente separados

### 2. **Gestión de Clientes** 👥

**¿Qué es?** Sistema completo para administrar la cartera de clientes de tu estudio.

**Funcionalidades:**
- **Registro de Clientes**: Datos completos de contacto y información corporativa
- **Historial de Proyectos**: Todos los trabajos realizados para cada cliente
- **Información de Contacto**: Emails, teléfonos, direcciones
- **Notas y Observaciones**: Preferencias, requerimientos especiales

**Casos de Uso:**
- Desarrolladora "Vista Real" con 5 proyectos activos
- Cliente particular "Familia García" con remodelación de casa
- Empresa "Tech Corp" con nuevo campus corporativo

### 3. **Gestión de Proyectos** 📋

**¿Qué es?** Núcleo del sistema que organiza todo el trabajo arquitectónico en proyectos estructurados.

**Funcionalidades:**
- **Crear Proyectos**: Con información detallada (cliente, fechas, descripción)
- **Estados de Proyecto**: ACTIVO, COMPLETADO, ARCHIVADO
- **Asignación de Responsables**: Propietarios y colaboradores
- **Métricas de Progreso**: Estadísticas automáticas de avance

**Estados del Proyecto:**
- **🟢 ACTIVO**: Proyectos en desarrollo
- **🔵 COMPLETADO**: Proyectos terminados y entregados
- **🟡 ARCHIVADO**: Proyectos pausados o cancelados

### 4. **Sistema de Fases** 🏗️

**¿Qué es?** Organización del trabajo en etapas lógicas según el proceso arquitectónico.

**Fases Típicas:**
1. **Programa Arquitectónico**: Análisis de necesidades y requerimientos
2. **Anteproyecto**: Propuesta conceptual y esquemas básicos
3. **Proyecto Ejecutivo**: Planos detallados y especificaciones
4. **Construcción**: Supervisión y administración de obra
5. **Entrega**: Finiquito y entrega de documentación

**Funcionalidades:**
- **Plantillas de Fases**: Reutilizar estructuras estándar
- **Fases Personalizadas**: Adaptadas a cada tipo de proyecto
- **Control de Progreso**: Seguimiento por fase
- **Orden Sequential**: Organización lógica del flujo de trabajo

### 5. **Gestión de Tareas con Kanban** 📊

**¿Qué es?** Sistema visual de gestión de tareas inspirado en metodologías ágiles, adaptado para arquitectura.

**Estados de Tareas:**
- **📝 TODO**: Tareas planificadas pendientes de iniciar
- **⚡ EN PROGRESO**: Tareas siendo trabajadas actualmente
- **⏸️ PAUSADO**: Tareas temporalmente detenidas
- **✅ COMPLETADO**: Tareas terminadas

**Funcionalidades Avanzadas:**
- **Drag & Drop**: Mover tareas entre estados arrastrando
- **Prioridades**: ALTA (🔴), MEDIA (🟡), BAJA (🟢)
- **Fechas de Vencimiento**: Control de deadlines
- **Asignación**: Responsables específicos para cada tarea
- **Métricas en Tiempo Real**: Estadísticas automáticas

**Ejemplo de Flujo:**
1. **TODO**: "Elaborar planos de planta baja"
2. **EN PROGRESO**: Arquitecto inicia el diseño en AutoCAD
3. **PAUSADO**: Esperando feedback del cliente
4. **COMPLETADO**: Planos aprobados y finalizados

### 6. **Gestión de Archivos Profesional** 📁

**¿Qué es?** Sistema optimizado para manejar archivos pesados típicos de la arquitectura.

**Tipos de Archivo Soportados:**
- **📐 Técnicos**: DWG, DXF, RVT (Revit), SKP (SketchUp), IFC, 3DM
- **📋 Documentos**: PDF, DOC, DOCX, XLS, XLSX
- **🖼️ Imágenes**: JPG, PNG, GIF, TIFF
- **📦 Comprimidos**: ZIP, RAR

**Características Técnicas:**
- **Tamaño Máximo**: Hasta 600MB por archivo
- **Almacenamiento Externo**: Cloudflare R2 para máximo rendimiento
- **Metadatos**: Tamaño, tipo, checksum para integridad
- **Organización**: Por fases de proyecto
- **URLs Firmadas**: Descarga segura y rápida

**Casos de Uso:**
- Subir archivo RVT de 450MB de modelo arquitectónico
- Cargar PDF de 15MB con especificaciones técnicas
- Almacenar DWG de 200MB con planos ejecutivos

### 7. **Gestión de Usuarios y Roles** 👨‍💼

**¿Qué es?** Sistema de permisos que define qué puede hacer cada miembro del equipo.

**Roles Disponibles:**
- **🔑 ADMIN ORGANIZACIÓN**: Control total de la organización
- **👨‍💼 ADMIN PROYECTO**: Gestión completa de proyectos específicos
- **👷 COLABORADOR**: Trabajo en tareas asignadas
- **👁️ VISUALIZADOR**: Solo lectura y consulta

**Permisos por Rol:**

| Funcionalidad | Admin Org | Admin Proyecto | Colaborador | Visualizador |
|---------------|-----------|----------------|-------------|--------------|
| Crear proyectos | ✅ | ✅ | ❌ | ❌ |
| Eliminar proyectos | ✅ | ✅ | ❌ | ❌ |
| Crear tareas | ✅ | ✅ | ✅ | ❌ |
| Editar tareas propias | ✅ | ✅ | ✅ | ❌ |
| Subir archivos | ✅ | ✅ | ✅ | ❌ |
| Ver reportes | ✅ | ✅ | ✅ | ✅ |

### 8. **Dashboard Ejecutivo** 📈

**¿Qué es?** Panel central con métricas y KPIs para toma de decisiones.

**Métricas Principales:**
- **Proyectos Activos**: Número y progreso
- **Tareas Vencidas**: Alertas de retrasos
- **Capacidad del Equipo**: Carga de trabajo por usuario
- **Progreso General**: Porcentaje de completitud
- **Archivos Recientes**: Últimas subidas

**Widgets Informativos:**
- Gráfico de tareas por estado
- Lista de proyectos próximos a vencer
- Actividad reciente del equipo
- Resumen de capacidad de almacenamiento

---

## 👨‍💻 Guía de Usuario Completa

### Primeros Pasos

#### 1. Acceso al Sistema
1. Ingresa a tu URL de Arc Manager
2. Introduce tus credenciales de acceso
3. Serás dirigido al dashboard principal

#### 2. Configuración Inicial
1. **Perfil Personal**: Completa tu información básica
2. **Organización**: Verifica datos de tu estudio
3. **Preferencias**: Configura idioma y notificaciones

### Flujo Básico de Trabajo

#### Crear un Nuevo Proyecto

1. **Navegación**: Ve a "Proyectos" → "Crear Nuevo"
2. **Información Básica**:
   - Nombre del proyecto: "Casa Moderna Los Altos"
   - Cliente: Seleccionar de lista o crear nuevo
   - Descripción: Resumen del alcance
   - Fechas: Inicio y entrega estimada

3. **Configuración de Fases**:
   - **Opción A**: Usar plantilla predefinida
   - **Opción B**: Crear fases personalizadas
   - **Opción C**: Empezar vacío (se crea "Backlog" automáticamente)

4. **Asignación**: 
   - Propietario: Arquitecto responsable
   - Colaboradores: Equipo de trabajo

#### Gestionar Tareas en Kanban

1. **Acceder al Kanban**: Proyecto → "Gestionar Tareas"
2. **Crear Tarea**:
   - Título: "Diseñar fachada principal"
   - Descripción: Detalles específicos
   - Fase: "Anteproyecto"
   - Prioridad: ALTA
   - Responsable: Miembro del equipo
   - Fecha límite: DD/MM/AAAA

3. **Mover Tareas**: Drag & drop entre columnas
   - TODO → EN PROGRESO (al empezar)
   - EN PROGRESO → PAUSADO (si hay bloqueos)
   - EN PROGRESO → COMPLETADO (al terminar)

4. **Actualizar Estado**: Clic en tarea para editar
   - Cambiar prioridad
   - Reasignar responsable
   - Actualizar descripción
   - Modificar fecha límite

#### Gestión de Archivos

1. **Subir Archivo**:
   - Ve a la pestaña "Archivos" del proyecto
   - Selecciona la fase correspondiente
   - Arrastra archivo o usa botón "Subir"
   - Agrega descripción

2. **Organización**:
   - Los archivos se organizan automáticamente por fase
   - Filtros por tipo de archivo
   - Búsqueda por nombre
   - Ordenar por fecha o tamaño

3. **Descargar**:
   - Clic en nombre del archivo
   - Descarga directa desde Cloudflare R2
   - URLs seguras con expiración

### Gestión de Clientes

#### Agregar Nuevo Cliente

1. **Navegación**: "Organizaciones" → "Clientes" → "Crear Nuevo"
2. **Información Básica**:
   - Nombre/Razón Social: "Desarrollos Vista Real S.A."
   - Tipo: Empresa/Particular
   - Email: contacto@vistareal.com
   - Teléfono: +52 55 1234 5678

3. **Información Adicional**:
   - Dirección: Ubicación física
   - Persona de contacto: Nombre del responsable
   - Notas: Preferencias y observaciones

#### Gestionar Cartera de Clientes

- **Lista Completa**: Todos los clientes con información resumida
- **Búsqueda**: Por nombre, email o teléfono
- **Filtros**: Activos, inactivos, tipo de cliente
- **Historial**: Proyectos realizados para cada cliente

### Gestión de Usuarios

#### Invitar Nuevo Usuario

1. **Acceso**: "Usuarios" → "Invitar Usuario" (solo admins)
2. **Información**:
   - Email: Dirección de correo electrónico
   - Nombre: Nombre completo
   - Rol: Seleccionar según responsabilidades

3. **Proceso**:
   - Sistema envía invitación por email
   - Usuario crea su contraseña
   - Acceso inmediato al sistema

#### Gestionar Equipo

- **Lista de Usuarios**: Todos los miembros con roles
- **Editar Permisos**: Cambiar roles según necesidades
- **Desactivar Usuarios**: Suspender acceso temporal
- **Estadísticas**: Carga de trabajo por usuario

---

## 🔄 Flujos de Trabajo

### Flujo Típico: Proyecto Residencial

#### Fase 1: Programa Arquitectónico (1-2 semanas)
**Tareas Típicas:**
- Levantamiento del terreno
- Análisis de requerimientos del cliente
- Estudio de reglamentos locales
- Definición de programa de necesidades

**Archivos Generados:**
- Levantamiento topográfico (DWG)
- Programa arquitectónico (PDF)
- Referencias e inspiraciones (JPG/PNG)

#### Fase 2: Anteproyecto (2-3 semanas)
**Tareas Típicas:**
- Esquemas conceptuales
- Zonificación básica
- Propuesta de distribución
- Renders preliminares

**Archivos Generados:**
- Plantas conceptuales (DWG)
- Esquemas de diseño (PDF)
- Renders de concepto (JPG)
- Presentación al cliente (PDF)

#### Fase 3: Proyecto Ejecutivo (4-6 semanas)
**Tareas Típicas:**
- Planos arquitectónicos detallados
- Especificaciones técnicas
- Detalles constructivos
- Memoria descriptiva

**Archivos Generados:**
- Plantas arquitectónicas (DWG)
- Cortes y fachadas (DWG)
- Detalles constructivos (DWG)
- Especificaciones (DOC/PDF)

#### Fase 4: Gestión de Construcción (Variable)
**Tareas Típicas:**
- Supervisión de obra
- Resolución de dudas técnicas
- Control de calidad
- Entrega de modificaciones

**Archivos Generados:**
- Minutas de obra (PDF)
- Planos modificados (DWG)
- Fotografías de avance (JPG)
- Reportes de supervisión (PDF)

### Flujo Colaborativo

#### Asignación de Tareas
1. **Arquitecto Principal**: Crea estructura del proyecto
2. **Equipo de Diseño**: Recibe tareas específicas
3. **Colaboradores**: Ejecutan trabajo asignado
4. **Revisiones**: Arquitecto principal valida resultados

#### Comunicación y Seguimiento
1. **Comentarios en Tareas**: Comunicación contextual
2. **Actualizaciones de Estado**: Progreso en tiempo real
3. **Notificaciones**: Alertas automáticas de cambios
4. **Reportes**: Resúmenes ejecutivos periódicos

---

## 📁 Gestión de Archivos

### Estrategia de Organización

#### Estructura Recomendada por Fases

**Programa Arquitectónico:**
- 01_LEVANTAMIENTOS/
  - Topograficos.dwg
  - Fotografias_sitio.zip
- 02_ANALISIS/
  - Programa_necesidades.pdf
  - Reglamentos.pdf

**Anteproyecto:**
- 01_CONCEPTOS/
  - Esquemas_iniciales.dwg
  - Referencias.pdf
- 02_PROPUESTA/
  - Plantas_concepto.dwg
  - Renders_preliminares.zip

**Proyecto Ejecutivo:**
- 01_ARQUITECTONICOS/
  - Plantas.dwg
  - Cortes.dwg
  - Fachadas.dwg
- 02_DETALLES/
  - Detalles_constructivos.dwg
  - Especificaciones.pdf

### Buenas Prácticas

#### Nomenclatura de Archivos
```
[FASE]_[CATEGORIA]_[DESCRIPCION]_[VERSION].[EXT]

Ejemplos:
- 02_ARQU_PLANTA_BAJA_v03.dwg
- 03_DETA_ESCALERA_PRINCIPAL_v01.dwg
- 01_PROG_MEMORIA_DESCRIPTIVA_v02.pdf
```

#### Control de Versiones
- **v01, v02, v03**: Versiones secuenciales
- **Descripción**: Cambios principales en comentarios
- **Archivo Final**: Versión aprobada claramente marcada

#### Optimización de Archivos
- **Comprimir imágenes**: Reducir tamaño sin perder calidad
- **Purgar DWG**: Limpiar elementos innecesarios
- **PDF Optimizado**: Comprimir para web cuando sea posible

### Seguridad de Archivos

#### Respaldo Automático
- **Cloudflare R2**: Redundancia automática
- **Versionado**: Historial de cambios
- **Acceso Seguro**: URLs firmadas con expiración

#### Control de Acceso
- **Por Proyecto**: Solo miembros del equipo
- **Por Fase**: Acceso granular según rol
- **Auditoria**: Registro de descargas

---

## ⚙️ Administración

### Panel de Administración Django

#### Acceso Administrativo
- **URL**: `/admin/`
- **Usuarios**: Solo superusuarios y staff
- **Funcionalidades**: Gestión completa del sistema

#### Funcionalidades Principales

**Gestión de Usuarios:**
- Crear/editar/eliminar usuarios
- Asignar roles y permisos
- Resetear contraseñas
- Ver estadísticas de uso

**Gestión de Organizaciones:**
- Configurar organizaciones
- Gestionar suscripciones
- Ver métricas de uso
- Control de límites

**Gestión de Proyectos:**
- Supervisar todos los proyectos
- Estadísticas generales
- Resolver problemas técnicos
- Migración de datos

**Gestión de Archivos:**
- Ver todos los archivos cargados
- Estadísticas de almacenamiento
- Archivos más pesados
- Limpieza de archivos huérfanos

### Monitoreo y Métricas

#### KPIs Operacionales
- **Usuarios Activos**: Diarios, semanales, mensuales
- **Proyectos Creados**: Nuevos proyectos por período
- **Archivos Subidos**: Volumen y tamaño total
- **Espacio Utilizado**: Por organización

#### Alertas del Sistema
- **Sobrecarga de Storage**: Límites de almacenamiento
- **Errores Críticos**: Fallos del sistema
- **Rendimiento**: Tiempos de respuesta altos
- **Seguridad**: Intentos de acceso sospechosos

### Mantenimiento

#### Tareas Rutinarias
- **Backup de BD**: Diario automático
- **Limpieza de Logs**: Semanal
- **Actualización de Seguridad**: Mensual
- **Optimización**: Trimestral

#### Resolución de Problemas
- **Logs Centralizados**: `/logs/` directory
- **Debug Mode**: Solo en desarrollo
- **Health Checks**: Endpoint `/health/`
- **Performance Monitoring**: Middleware incluido

---

## 💳 Planes y Suscripciones

### Estructura de Planes

#### Plan Básico
**Precio**: $99 USD/mes
**Incluye:**
- Hasta 5 usuarios
- 10 proyectos activos
- 10GB de almacenamiento
- Soporte por email

**Ideal para:**
- Arquitectos independientes
- Estudios pequeños (1-3 personas)
- Proyectos residenciales simples

#### Plan Profesional
**Precio**: $199 USD/mes
**Incluye:**
- Hasta 15 usuarios
- 50 proyectos activos
- 50GB de almacenamiento
- Soporte prioritario
- Reportes avanzados

**Ideal para:**
- Estudios medianos (4-10 personas)
- Proyectos comerciales
- Múltiples desarrollos simultáneos

#### Plan Empresarial
**Precio**: $399 USD/mes
**Incluye:**
- Usuarios ilimitados
- Proyectos ilimitados
- 200GB de almacenamiento
- Soporte 24/7
- Integración personalizada
- Reportes ejecutivos

**Ideal para:**
- Grandes despachos (10+ personas)
- Desarrolladoras inmobiliarias
- Proyectos institucionales

### Gestión de Suscripciones

#### Upgrade de Plan
1. **Navegación**: "Planes" → "Solicitar Actualización"
2. **Selección**: Nuevo plan deseado
3. **Justificación**: Razón del cambio
4. **Aprobación**: Revisión administrativa
5. **Activación**: Implementación inmediata

#### Facturación
- **Ciclo**: Mensual o anual
- **Métodos**: Transferencia bancaria, tarjeta
- **Facturación**: PDF automático
- **Historial**: Acceso completo a pagos

#### Límites y Restricciones
- **Usuarios**: Según plan contratado
- **Proyectos**: Límite por plan
- **Almacenamiento**: Alertas al 80%
- **Sobrecarga**: Restricción temporal

---

## 🛠️ Solución de Problemas

### Problemas Comunes

#### No Puedo Subir Archivos
**Posibles Causas:**
- Archivo mayor a 600MB
- Formato no soportado
- Límite de almacenamiento alcanzado
- Problemas de conexión

**Soluciones:**
1. Verificar tamaño del archivo
2. Confirmar formato soportado
3. Revisar espacio disponible
4. Intentar con conexión estable

#### Las Tareas No Se Mueven en Kanban
**Posibles Causas:**
- Permisos insuficientes
- JavaScript deshabilitado
- Problemas de red
- Cache del navegador

**Soluciones:**
1. Verificar rol de usuario
2. Habilitar JavaScript
3. Recargar página
4. Limpiar cache del navegador

#### No Recibo Notificaciones
**Posibles Causas:**
- Email en spam
- Configuración de notificaciones
- Email incorrecto
- Problemas del servidor

**Soluciones:**
1. Revisar carpeta spam
2. Verificar configuración
3. Actualizar email
4. Contactar soporte

### Contacto de Soporte

#### Canales de Soporte
- **Email**: soporte@arcmanager.com
- **Teléfono**: +52 55 1234 5678
- **Chat**: Disponible en horario laboral
- **Centro de Ayuda**: help.arcmanager.com

#### Información Necesaria
- **URL del problema**: Página específica
- **Usuario afectado**: Email de usuario
- **Descripción**: Pasos para reproducir
- **Screenshots**: Capturas de pantalla
- **Navegador**: Chrome, Firefox, Safari

#### Tiempos de Respuesta
- **Plan Básico**: 48 horas
- **Plan Profesional**: 24 horas
- **Plan Empresarial**: 4 horas

---

## 📊 Métricas y Reportes

### Reportes Disponibles

#### Reporte de Productividad
- **Tareas completadas por usuario**
- **Tiempo promedio por tarea**
- **Proyectos entregados a tiempo**
- **Eficiencia por fase**

#### Reporte de Proyectos
- **Estado de todos los proyectos**
- **Proyectos próximos a vencer**
- **Carga de trabajo por equipo**
- **Rentabilidad por proyecto**

#### Reporte de Archivos
- **Espacio utilizado por proyecto**
- **Tipos de archivo más comunes**
- **Crecimiento del almacenamiento**
- **Archivos más descargados**

### Exportación de Datos

#### Formatos Disponibles
- **PDF**: Reportes ejecutivos
- **Excel**: Datos para análisis
- **CSV**: Integración con otras herramientas
- **JSON**: Desarrollos personalizados

#### Programación Automática
- **Diario**: Reportes operacionales
- **Semanal**: Resúmenes de progreso
- **Mensual**: Análisis ejecutivo
- **Trimestral**: Evaluación estratégica

---

## 🚀 Próximas Funcionalidades

### Roadmap de Desarrollo

#### Fase 2 (Q1 2025)
- **Gantt Charts**: Diagramas de tiempo
- **Notificaciones Push**: Alertas en tiempo real
- **API Pública**: Integraciones externas
- **Reportes Avanzados**: Business Intelligence

#### Fase 3 (Q2 2025)
- **Integración BIM**: Conexión con Revit
- **Control de Costos**: Presupuestos por proyecto
- **App Móvil**: iOS y Android
- **Workflows Automatizados**: Procesos automáticos

#### Fase 4 (Q3 2025)
- **Inteligencia Artificial**: Sugerencias automáticas
- **Realidad Aumentada**: Visualización en sitio
- **Blockchain**: Certificación de entregas
- **IoT Integration**: Sensores en obra

---

**Arc Manager** - Transformando la gestión de proyectos arquitectónicos desde 2024  
© 2024 Arc Manager. Todos los derechos reservados.
