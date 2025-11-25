# Guía de Testing - Filtros de Archivos

## Problemas Resueltos

### Problema 1: Método de Filtrado
`htmx.ajax()` no está disponible en HTMX 1.9.12. He cambiado la implementación para usar `fetch()` que es compatible con todas las versiones.

### Problema 2: Timing de Carga (CRÍTICO)
Los elementos de filtros se cargan dinámicamente con HTMX dentro de accordions. El script se ejecutaba ANTES de que los elementos existieran en el DOM. Ahora escucha múltiples eventos:
- `htmx:afterSettle` - Cuando HTMX termina de cargar contenido
- `htmx:afterSwap` - Cuando HTMX hace swap de HTML
- `shown.bs.collapse` - Cuando se abre un accordion de Bootstrap

### Problema 3: Error de Sintaxis
Línea 165 de `validate-file-system.js` tenía comillas mal puestas en un template literal.

## Cambios Realizados

### 1. ✅ Método de Filtrado Actualizado
- **Antes:** Usaba `htmx.ajax()` (no disponible en HTMX 1.9.x)
- **Ahora:** Usa `fetch()` nativo de JavaScript (compatible con todo)

### 2. ✅ Emojis Removidos
- Se quitaron todos los emojis de los dropdowns de filtros [[memory:8677681]]
- Ahora los filtros son limpios y profesionales

### 3. ✅ Debugging Mejorado
- Logs claros en consola para ver qué está pasando
- Contadores de elementos encontrados
- Mensajes cuando se cambian los filtros

## Pasos para Probar

### 1. Limpiar Cache del Navegador
**IMPORTANTE:** Debes limpiar el cache del navegador para cargar la nueva versión:

**En Chrome/Edge:**
- Presiona `Ctrl + Shift + Delete` (Windows) o `Cmd + Shift + Delete` (Mac)
- Selecciona "Imágenes y archivos en caché"
- Haz clic en "Borrar datos"

**O simplemente:**
- Presiona `Ctrl + F5` (Windows) o `Cmd + Shift + R` (Mac) para recargar sin cache

### 2. Abrir la Consola del Navegador
1. Presiona `F12` para abrir DevTools
2. Ve a la pestaña "Console"

### 3. Verificar que Todo Está Cargado
Al cargar la página, deberías ver en la consola:

```
=== VERIFICACION DE FILTROS ===
setupFileFilters: function
applyFileFilters: function
clearFileFilters: function
Filtros de tipo encontrados: 1 (o más, dependiendo de cuántas fases tengas)
Filtros de fecha encontrados: 1 (o más)
Botones de limpiar encontrados: 1 (o más)
=== FIN VERIFICACION ===
```

### 4. Ir a la Pestaña de Archivos
1. Abre un proyecto que tenga archivos
2. Ve a la pestaña "Archivos" (Files)
3. Deberías ver los dropdowns de filtros

### 5. Probar los Filtros

#### Test 1: Filtro por Tipo
1. Selecciona un tipo de archivo en el dropdown (ej: "PDF")
2. Deberías ver en la consola:
   ```
   FILTRO DE TIPO CAMBIADO - Fase X, Valor: PDF
   Aplicando filtros para fase X: {type: "PDF", date: "", url: "..."}
   ```
3. Los archivos deberían filtrarse inmediatamente
4. Deberías ver un spinner de "Aplicando filtros..."

#### Test 2: Filtro por Fecha
1. Selecciona una fecha en el dropdown (ej: "Hoy")
2. Deberías ver en la consola:
   ```
   FILTRO DE FECHA CAMBIADO - Fase X, Valor: today
   Aplicando filtros para fase X: {type: "", date: "today", url: "..."}
   ```
3. Los archivos deberían filtrarse inmediatamente

#### Test 3: Combinar Filtros
1. Selecciona un tipo Y una fecha
2. Ambos filtros deberían aplicarse
3. En la consola verás la URL con ambos parámetros

#### Test 4: Limpiar Filtros
1. Haz clic en el botón "Limpiar"
2. Deberías ver en la consola:
   ```
   LIMPIANDO FILTROS - Fase X
   ```
3. Todos los archivos deberían mostrarse de nuevo

## Debugging Manual

Si los filtros AÚN no funcionan, ejecuta esto en la consola:

```javascript
// Test 1: Verificar que las funciones existen
console.log('setupFileFilters:', typeof setupFileFilters);
console.log('applyFileFilters:', typeof window.applyFileFilters);
console.log('clearFileFilters:', typeof window.clearFileFilters);

// Test 2: Verificar elementos en el DOM
console.log('Filtros de tipo:', document.querySelectorAll('[id^="fileTypeFilter-"]'));
console.log('Filtros de fecha:', document.querySelectorAll('[id^="fileDateFilter-"]'));
console.log('Contenedores:', document.querySelectorAll('[id^="files-container-"]'));

// Test 3: Llamar manualmente al setup
if (typeof setupFileFilters === 'function') {
    setupFileFilters();
    console.log('Setup ejecutado manualmente');
}

// Test 4: Probar un filtro específico (reemplaza XX con el ID de tu fase)
// Ejemplo: window.applyFileFilters(123)
```

## Problemas Comunes y Soluciones

### ❌ "setupFileFilters is not defined"
**Solución:** El archivo `files_filtering.js` no está cargado. Verifica que:
1. El archivo existe en `arc_manager/static/js/files_filtering.js`
2. Limpiaste el cache del navegador
3. Recargaste la página con `Ctrl + F5`

### ❌ "Filtros de tipo encontrados: 0"
**Solución:** No estás en la pestaña de archivos o no hay archivos en el proyecto.
1. Ve a la pestaña "Archivos"
2. Asegúrate de que el proyecto tenga al menos una fase con archivos

### ❌ No aparece nada en la consola
**Solución:** 
1. Asegúrate de estar en la página de detalle de un proyecto (`/projects/XXX/`)
2. Asegúrate de que la consola esté abierta
3. Recarga la página con `F5`

### ❌ "Error al aplicar filtros"
**Solución:** Problema con el backend. Verifica:
1. Que el servidor esté corriendo
2. Que la URL de la API sea correcta
3. Revisa la pestaña "Network" en DevTools para ver el error exacto

## Test Rápido de 30 Segundos

1. Abre un proyecto con archivos
2. Ve a la pestaña "Archivos"
3. Abre la consola (F12)
4. Selecciona "PDF" en el dropdown de tipo
5. ¿Ves logs en la consola? ✅ FUNCIONA
6. ¿Los archivos se filtraron? ✅ TODO BIEN
7. ¿No pasa nada? ❌ Ejecuta el debugging manual arriba

## Ejecutar en Docker

Si estás usando Docker, asegúrate de:

```bash
# 1. Recopilar archivos estáticos
docker-compose exec web python manage.py collectstatic --no-input

# 2. Reiniciar el servidor
docker-compose restart web

# 3. Limpiar cache del navegador
# (Ctrl + F5 o Cmd + Shift + R)
```

## Contacto

Si después de seguir todos estos pasos los filtros AÚN no funcionan, proporciona:

1. Screenshot de la consola del navegador
2. Screenshot de la pestaña "Network" mostrando las peticiones
3. Versión del navegador que estás usando
4. ¿Estás en desarrollo local o en producción?

---

**Nota:** La versión del archivo JS se cambió de `v=1.1` → `v=1.2` → `v=1.3` para forzar la recarga del cache.

## Actualización Importante (v1.3)

**Cambio crítico:** El script ahora escucha eventos de carga dinámica de HTMX y Bootstrap. Cuando abras un accordion con archivos, deberías ver en la consola:

```
HTMX afterSettle detectado: collapse-56
Configurando filtros de archivos...
Encontrados 1 filtros de tipo
Encontrados 1 filtros de fecha
Encontrados 1 botones de limpiar
Filtros de archivos configurados exitosamente
```

**Si no ves estos logs cuando abres un accordion:**
1. Limpia el cache del navegador (Ctrl + Shift + R)
2. Recarga la página completamente
3. Abre la consola ANTES de abrir el accordion
4. Luego haz click en el accordion para expandirlo

