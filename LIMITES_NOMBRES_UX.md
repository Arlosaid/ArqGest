# Sistema de Límites de Caracteres - Mejores Prácticas UX/UI

## 📋 Resumen

Se ha implementado un sistema completo de límites de caracteres para nombres en la aplicación, siguiendo las mejores prácticas de UX/UI. Este sistema incluye validación en backend, feedback visual en tiempo real y mensajes de error claros.

## 🎯 Límites Implementados

### Límites por Entidad

| Entidad | Campo | Límite Anterior | Nuevo Límite | Razón |
|---------|-------|----------------|--------------|-------|
| **Proyectos** | Nombre | 255 caracteres | **100 caracteres** | Nombres concisos y descriptivos |
| **Tareas** | Título | 255 caracteres | **120 caracteres** | Balance entre descripción y brevedad |
| **Clientes** | Nombre | 255 caracteres | **100 caracteres** | Suficiente para nombres de empresas |
| **Usuarios** | Nombre | 150 caracteres | **50 caracteres** | Nombres personales estándar |
| **Usuarios** | Apellido | 150 caracteres | **50 caracteres** | Apellidos estándar |
| **Organizaciones** | Nombre | 200 caracteres | **100 caracteres** | Nombres de empresas/organizaciones |
| **Fases** | Nombre | 255 caracteres | **100 caracteres** | Nombres de fases del proyecto |
| **Plantillas de Fase** | Nombre | 100 caracteres | **100 caracteres** | Sin cambios (ya era óptimo) |

## 🔧 Componentes Implementados

### 1. Validadores Backend (`core/validators.py`)

Validadores personalizados que verifican:
- ✅ Longitud máxima
- ✅ Contenido no vacío
- ✅ Caracteres permitidos (letras, números, espacios, caracteres especiales básicos)
- ✅ No múltiples espacios consecutivos

**Validadores disponibles:**
- `validate_project_name()` - Para nombres de proyectos
- `validate_task_title()` - Para títulos de tareas
- `validate_client_name()` - Para nombres de clientes
- `validate_organization_name()` - Para nombres de organizaciones
- `validate_user_name()` - Para nombres de usuarios (más restrictivo)
- `validate_phase_name()` - Para nombres de fases

### 2. Contador de Caracteres JavaScript (`static/js/char-counter.js`)

**Características:**
- ✅ Inicialización automática en campos con `data-char-counter="true"`
- ✅ Actualización en tiempo real mientras el usuario escribe
- ✅ Feedback visual progresivo según el porcentaje usado
- ✅ Soporte para contenido dinámico (modales, AJAX)
- ✅ Observador de mutaciones para detectar nuevos campos
- ✅ Accesibilidad mejorada con `aria-live`

**Estados del contador:**
- 🟢 **Normal** (0-74%): Texto gris discreto
- 🔵 **Info** (75-89%): Texto azul claro
- 🟡 **Warning** (90-99%): Texto amarillo, fuente más destacada
- 🔴 **Error** (100%+): Texto rojo con animación sutil

### 3. Estilos CSS (`static/css/char-counter.css`)

**Características:**
- ✅ Transiciones suaves
- ✅ Animaciones sutiles para estados de error
- ✅ Soporte para modo oscuro
- ✅ Diseño responsive
- ✅ Integración con Bootstrap 5
- ✅ Cumplimiento WCAG AA para contraste

## 📝 Uso en Formularios

### Configuración Automática

Los formularios ya están configurados con los atributos necesarios:

```html
<!-- Ejemplo automático -->
<input type="text" 
       data-char-counter="true" 
       data-max-length="100"
       class="form-control">
```

### Formularios Actualizados

Los siguientes formularios ya incluyen contadores de caracteres:

#### Proyectos (`apps/projects/forms.py`)
- ✅ `ProjectForm` - Nombre del proyecto
- ✅ `TaskForm` - Título de la tarea
- ✅ `PhaseForm` - Nombre de la fase
- ✅ `PhaseTemplateForm` - Nombre de plantilla

#### Organizaciones y Clientes (`apps/orgs/forms.py`)
- ✅ `OrganizationForm` - Nombre de organización
- ✅ `ClientForm` - Nombre de cliente

#### Usuarios (`apps/users/forms.py`)
- ✅ `SimpleUserCreateForm` - Nombre y apellido
- ✅ `SimpleUserEditForm` - Nombre y apellido

## 🎨 Mejores Prácticas de UX Implementadas

### 1. **Feedback Visual Progresivo**
- El contador solo aparece cuando el usuario empieza a escribir
- Cambia de color gradualmente según se acerca al límite
- Desaparece suavemente si el campo queda vacío

### 2. **Mensajes Claros y Accionables**
```
Ejemplos de mensajes:
- "50 / 100 caracteres" (estado normal)
- "95 / 100 caracteres" (cerca del límite)
- "Excedido por 5 caracteres" (sobre el límite)
```

### 3. **Validación No Intrusiva**
- El contador no bloquea el tipeo
- Permite exceder el límite temporalmente
- La validación real ocurre al enviar el formulario

### 4. **Accesibilidad**
- Uso de `aria-live="polite"` para lectores de pantalla
- Contraste de colores conforme a WCAG AA
- Mensajes de error descriptivos

### 5. **Rendimiento Optimizado**
- Observador de mutaciones para contenido dinámico
- Prevención de inicializaciones duplicadas
- Transiciones CSS en lugar de animaciones JavaScript

## 🔄 Migraciones de Base de Datos

Se han creado las siguientes migraciones:

### Proyectos
```
apps/projects/migrations/0010_alter_phase_name_alter_phasetemplate_name_and_more.py
```
- Actualiza `Project.name` a max_length=100
- Actualiza `Phase.name` a max_length=100
- Actualiza `Task.title` a max_length=120
- Actualiza `PhaseTemplate.name` a max_length=100

### Organizaciones
```
apps/orgs/migrations/0005_alter_client_name_alter_organization_name.py
```
- Actualiza `Organization.name` a max_length=100
- Actualiza `Client.name` a max_length=100

### Usuarios
```
apps/accounts/migrations/0004_alter_user_first_name_alter_user_last_name.py
```
- Actualiza `User.first_name` a max_length=50
- Actualiza `User.last_name` a max_length=50

## 🚀 Aplicar los Cambios

### 1. Aplicar migraciones
```bash
python manage.py migrate projects
python manage.py migrate orgs
python manage.py migrate accounts
```

### 2. Recolectar archivos estáticos (si es necesario)
```bash
python manage.py collectstatic --noinput
```

### 3. Reiniciar el servidor
```bash
python manage.py runserver
```

## 📱 Compatibilidad

### Navegadores Soportados
- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Opera 76+

### Dispositivos
- ✅ Desktop (Windows, macOS, Linux)
- ✅ Tablets (iOS, Android)
- ✅ Móviles (iOS, Android)

## 🧪 Pruebas Recomendadas

### Casos de Prueba

1. **Prueba básica de contador**
   - Escribir en un campo y verificar que el contador aparece
   - Verificar que muestra el conteo correcto

2. **Prueba de estados de color**
   - Llenar campo al 50% → debe ser gris
   - Llenar campo al 80% → debe ser azul
   - Llenar campo al 95% → debe ser amarillo
   - Exceder el límite → debe ser rojo

3. **Prueba de validación**
   - Intentar enviar formulario con campo excedido
   - Verificar mensaje de error del servidor

4. **Prueba de contenido dinámico**
   - Abrir modal con formulario
   - Verificar que el contador funciona

5. **Prueba de caracteres especiales**
   - Intentar usar caracteres no permitidos
   - Verificar mensaje de error

## 🔍 Solución de Problemas

### El contador no aparece
**Causa:** El archivo JS no está cargado o el atributo no está presente
**Solución:** 
- Verificar que `char-counter.js` está en `static/js/`
- Verificar que el campo tiene `data-char-counter="true"`
- Abrir consola del navegador para ver errores

### El contador no desaparece al borrar
**Causa:** JavaScript no detecta el cambio
**Solución:**
- Verificar que el evento `input` se dispara
- Llamar manualmente a `window.reinitCharCounters()` si es necesario

### Los estilos no se aplican
**Causa:** CSS no cargado o conflicto de estilos
**Solución:**
- Verificar que `char-counter.css` está en `static/css/`
- Ejecutar `python manage.py collectstatic`
- Limpiar caché del navegador

## 📚 Referencias y Estándares

- **Material Design** - Input character counter guidelines
- **WCAG 2.1** - Accessibility standards (Level AA)
- **Nielsen Norman Group** - Form usability best practices
- **Bootstrap 5** - Form validation patterns

## 💡 Mejoras Futuras (Opcional)

- [ ] Agregar sugerencias cuando se excede el límite
- [ ] Implementar truncado automático con confirmación
- [ ] Agregar indicador visual en el input mismo (barra de progreso)
- [ ] Soporte para límites variables según tipo de usuario
- [ ] Analytics de qué campos exceden más frecuentemente

## 📄 Archivos Modificados

### Nuevos Archivos
- `core/validators.py` - Validadores personalizados
- `static/js/char-counter.js` - Contador de caracteres
- `static/css/char-counter.css` - Estilos del contador

### Archivos Modificados
- `apps/projects/models.py` - Límites actualizados
- `apps/projects/forms.py` - Validadores y atributos
- `apps/orgs/models.py` - Límites actualizados
- `apps/orgs/forms.py` - Validadores y atributos
- `apps/accounts/models.py` - Límites actualizados
- `apps/users/forms.py` - Validadores y atributos
- `templates/base.html` - Inclusión de CSS y JS

---

**Versión:** 1.0  
**Fecha:** 16 de Octubre, 2025  
**Autor:** Sistema Arc Manager

