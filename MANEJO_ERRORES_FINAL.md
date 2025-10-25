# 🎯 SISTEMA DE MANEJO DE ERRORES - CONFIGURACIÓN FINAL

## 📋 Resumen por Tipo de Error

| Error | Método | Ubicación | Usuario Ve |
|-------|--------|-----------|------------|
| **400** | Notificación + Redirect | ErrorHandlingMiddleware | ⚠️ Notificación warning + redirect |
| **403** | Notificación + Redirect | ErrorHandlingMiddleware | ❌ Notificación error + redirect |
| **404** | Template | handler404 en urls.py | 📄 Página 404.html personalizada |
| **500** | Notificación + Redirect | ErrorHandlingMiddleware | ❌ Notificación error + redirect |

---

## 🔥 Error 400 - Bad Request

**Cuándo ocurre:** Datos inválidos en formulario, parámetros incorrectos, etc.

**Comportamiento:**
- ✅ Notificación warning: "La información enviada no es válida..."
- ✅ Redirect a página anterior (o dashboard si no hay referer)
- ✅ AJAX: Retorna JSON

**Dónde se maneja:**
- `ErrorHandlingMiddleware.process_response()` en `apps/accounts/middleware.py`

**Ejemplo:**
```
Usuario envía formulario con datos inválidos
    ↓
Middleware detecta status_code = 400
    ↓
messages.warning(request, "La información enviada no es válida...")
    ↓
return redirect(referer o dashboard)
    ↓
Usuario ve notificación amarilla y puede continuar
```

---

## 🚫 Error 403 - Forbidden

**Cuándo ocurre:** Usuario intenta acceder a recurso sin permisos

**Comportamiento:**
- ✅ Notificación error: "No tienes permisos para acceder a esta página..."
- ✅ Redirect a página anterior (o dashboard si no hay referer)
- ✅ AJAX: Retorna JSON

**Dónde se maneja:**
- `ErrorHandlingMiddleware.process_response()` en `apps/accounts/middleware.py`

**Ejemplo:**
```
Usuario intenta acceder a /admin/ sin ser staff
    ↓
Middleware detecta status_code = 403
    ↓
messages.error(request, "No tienes permisos...")
    ↓
return redirect(referer o dashboard)
    ↓
Usuario ve notificación roja y puede continuar
```

---

## 📄 Error 404 - Not Found

**Cuándo ocurre:** URL no existe, recurso eliminado, typo en URL, etc.

**Comportamiento:**
- ✅ Muestra template personalizado `404.html`
- ✅ Usuario puede navegar desde ahí
- ✅ AJAX: Retorna JSON
- ❌ NO usa notificaciones (porque los 404 son comunes y esperados)

**Por qué es diferente:**
Los 404 son **normales** en cualquier aplicación web:
- Enlaces rotos externos
- URLs antiguas guardadas
- Usuarios escribiendo URLs manualmente
- Recursos eliminados

**No son errores del servidor**, son recursos que no existen.

**Dónde se maneja:**
- `handler404 = 'core.error_handlers.custom_404_view'` en `urls.py`
- Template: `templates/404.html`

**Ejemplo:**
```
Usuario visita /pagina-que-no-existe/
    ↓
Django no encuentra la ruta
    ↓
handler404 se ejecuta
    ↓
return render(request, '404.html', status=404)
    ↓
Usuario ve página 404 bonita con opciones de navegación
```

---

## 💥 Error 500 - Internal Server Error

**Cuándo ocurre:** Excepción no manejada, error de código, problema de DB, etc.

**Comportamiento:**
- ✅ Notificación error: "Algo salió mal de nuestro lado..."
- ✅ Redirect a dashboard
- ✅ AJAX: Retorna JSON
- ✅ Backend loguea automáticamente el traceback completo

**Dónde se maneja:**
- `ErrorHandlingMiddleware.process_exception()` en `apps/accounts/middleware.py`

**Ejemplo:**
```
Error en código Python (ej: division by zero)
    ↓
Django lanza excepción
    ↓
ErrorHandlingMiddleware.process_exception() intercepta
    ↓
Django loguea el error automáticamente (con traceback)
    ↓
messages.error(request, "Algo salió mal de nuestro lado...")
    ↓
return redirect('main:dashboard')
    ↓
Usuario ve notificación roja en dashboard y puede continuar
```

---

## 🎨 Mensajes de Notificación

### Error 400:
```
⚠️ La información enviada no es válida. Por favor, verifica e intenta nuevamente.
```
**Tipo:** Warning (amarillo)

### Error 403:
```
❌ No tienes permisos para acceder a esta página. Si crees que esto es un error, contacta con tu administrador.
```
**Tipo:** Error (rojo)

### Error 404:
```
(Sin notificación - muestra template 404.html)
```
**Tipo:** Template personalizado

### Error 500:
```
❌ Algo salió mal de nuestro lado. Ya estamos trabajando en solucionarlo. Por favor, intenta nuevamente en unos momentos.
```
**Tipo:** Error (rojo)

---

## 🔄 Flujo de Ejecución

### Request Normal → Error 400/403:
```
Request
    ↓
Middlewares de entrada
    ↓
Vista retorna HttpResponseBadRequest (400) o HttpResponseForbidden (403)
    ↓
ErrorHandlingMiddleware.process_response() ← INTERCEPTA AQUÍ
    ↓
Convierte en notificación + redirect
    ↓
Usuario ve notificación
```

### Request Normal → Error 404:
```
Request
    ↓
Middlewares de entrada
    ↓
Django no encuentra la ruta
    ↓
handler404 en urls.py ← SE EJECUTA AQUÍ
    ↓
render(request, '404.html')
    ↓
Usuario ve template 404
```

### Request Normal → Error 500:
```
Request
    ↓
Middlewares de entrada
    ↓
Vista lanza excepción
    ↓
ErrorHandlingMiddleware.process_exception() ← INTERCEPTA AQUÍ
    ↓
Django loguea automáticamente
    ↓
Middleware convierte en notificación + redirect
    ↓
Usuario ve notificación
```

---

## 🧪 Testing

### Probar cada tipo de error:

**400 - Bad Request:**
```python
# En cualquier vista
from django.http import HttpResponseBadRequest
return HttpResponseBadRequest()
# → Verás notificación warning + redirect
```

**403 - Forbidden:**
```python
# En cualquier vista
from django.http import HttpResponseForbidden
return HttpResponseForbidden()
# → Verás notificación error + redirect
```

**404 - Not Found:**
```bash
# Visitar: http://localhost:8000/pagina-inexistente/
# → Verás template 404.html
```

**500 - Internal Server Error:**
```python
# En cualquier vista
raise Exception("Test error 500")
# → Verás notificación error + redirect
```

O usar las rutas de test (solo en desarrollo):
```bash
http://localhost:8000/test-400/
http://localhost:8000/test-403/
http://localhost:8000/test-404/
http://localhost:8000/test-500/
```

---

## 📝 Archivos Involucrados

### Middleware:
- `arc_manager/apps/accounts/middleware.py`
  - `ErrorHandlingMiddleware.process_exception()` - Maneja 500
  - `ErrorHandlingMiddleware.process_response()` - Maneja 400, 403

### Handlers:
- `arc_manager/core/urls.py`
  - Define handler400, handler403, handler404, handler500

- `arc_manager/core/error_handlers.py`
  - `custom_400_view()` - Fallback para 400
  - `custom_403_view()` - Fallback para 403
  - `custom_404_view()` - Maneja 404 con template
  - `custom_500_view()` - Fallback para 500

### Templates:
- `arc_manager/templates/404.html` - Página 404 personalizada
- `arc_manager/templates/500.html` - Ya no se usa (reemplazado por notificaciones)

---

## ✅ Ventajas del Sistema Actual

### Para Error 500:
- ✅ Usuario no queda "varado" en página de error
- ✅ Puede seguir trabajando inmediatamente
- ✅ Mensaje tranquilizador y profesional
- ✅ Backend tiene logs completos para debugging

### Para Error 400/403:
- ✅ Feedback inmediato al usuario
- ✅ No interrumpe el flujo de trabajo
- ✅ Redirige inteligentemente (referer o dashboard)

### Para Error 404:
- ✅ Template personalizado con branding
- ✅ Opciones de navegación clara
- ✅ No es invasivo (404 son comunes)
- ✅ Experiencia coherente con el resto de la app

---

## 🎯 Filosofía de Diseño

**Errores del Usuario (400, 404):**
- Son **esperados** y **comunes**
- No asustan al usuario
- Proporcionan ayuda para recuperarse

**Errores de Permisos (403):**
- Son **intencionales** (protección)
- Mensaje claro sobre qué pasó
- Indican cómo resolver (contactar admin)

**Errores del Servidor (500):**
- Son **inesperados** y **críticos**
- Minimizar impacto en usuario
- Mensaje tranquilizador
- Logs detallados para developers

---

## 📅 Fecha de Configuración
**25 de Octubre de 2025**

## ✅ Estado
**CONFIGURADO Y FUNCIONANDO CORRECTAMENTE**
