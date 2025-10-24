# 📁 Cómo Funciona el Límite de Tamaño de Archivos

## 🎯 Flujo Completo: Backend → Frontend

### 1️⃣ **Configuración en Admin Panel**
```
Django Admin → SystemSettings → 
  - max_file_size_mb = 1500 (Desktop/General)
  - upload_max_file_size_mobile_mb = 200 (Móviles)
```
- Se guarda en la base de datos
- No requiere reiniciar el servidor
- ✅ **Cambio inmediato en backend**

---

### 2️⃣ **Backend (Django) - Validación**

#### A. Context Processor (`core/context_processors.py`)
```python
def global_settings(request):
    system_settings = SystemSettings.load()
    max_file_size_mb = system_settings.max_file_size_mb  # Desktop: 1500MB
    max_file_size_mobile_mb = system_settings.upload_max_file_size_mobile_mb  # Mobile: 200MB
    
    return {
        'max_file_size_mb': max_file_size_mb,
        'max_file_size_mobile_mb': max_file_size_mobile_mb,
    }
```

#### B. Validadores (`apps/files/validators.py`)
```python
def validate_file_size(uploaded_file, max_size_mb=None):
    if max_size_mb is None:
        sys_settings = SystemSettings.load()
        max_size_mb = sys_settings.max_file_size_mb  # Lee de DB
    
    max_size_bytes = max_size_mb * 1024 * 1024
    # Validación...
```

✅ **Backend siempre lee el valor actual de la DB**

---

### 3️⃣ **Frontend (JavaScript) - Validación**

#### A. Meta Tags en HTML (`templates/base.html`)
```html
<meta name="max-file-size" content="{{ max_file_size_mb }}">
<meta name="max-file-size-mobile" content="{{ max_file_size_mobile_mb }}">
```
- Se generan **dinámicamente** cada vez que se carga la página
- Vienen del context processor
- ✅ **Se actualizan automáticamente al recargar la página**

#### B. JavaScript Lee de los Meta Tags
```javascript
// large-file-upload.js
const metaMaxSize = document.querySelector('meta[name="max-file-size"]')?.content;
const maxFileSize = metaMaxSize ? parseInt(metaMaxSize) : 500;

// mobile_upload_optimizer.js
const metaMaxSizeMobile = document.querySelector('meta[name="max-file-size-mobile"]')?.content;
const maxFileSizeMB = isMobile 
    ? (metaMaxSizeMobile ? parseInt(metaMaxSizeMobile) : 200)
    : (metaMaxSize ? parseInt(metaMaxSize) : 500);

// _files_tab.html
MAX_SIZE_MB: parseInt(document.querySelector('meta[name="max-file-size"]')?.content) || 500
MAX_SIZE_MOBILE_MB: parseInt(document.querySelector('meta[name="max-file-size-mobile"]')?.content) || 200
```

✅ **JavaScript siempre lee de los meta tags (que vienen del backend)**

---

## 🔄 ¿Cómo se Actualiza el Límite?

### Escenario: Cambias los límites en Admin

1. **En Admin Panel:**
   ```
   SystemSettings → 
     - max_file_size_mb = 1500 → Guardar
     - upload_max_file_size_mobile_mb = 300 → Guardar
   ```

2. **Backend (inmediato):**
   - ✅ Validación en `validators.py` usa los nuevos valores inmediatamente
   - ✅ Próxima request ya usará los nuevos valores

3. **Frontend (requiere recarga):**
   - ❌ Usuario con página abierta sigue viendo valores viejos
   - ✅ Usuario recarga página (F5) → ve los nuevos valores
   - ✅ Nuevo usuario que entra → ve los nuevos valores

---

## 🚀 ¿Por Qué No Cambia Inmediatamente en el Frontend?

### Problema: Caché del Navegador

```
Usuario → Meta tags viejos (caché) → JavaScript viejo → "máx: 500MB"
```

### Solución 1: **Forzar Recarga** (Usuario)
```
Ctrl + Shift + R  (Windows/Linux)
Cmd + Shift + R   (Mac)
```

### Solución 2: **Actualizar STATIC_VERSION** (Desarrollador)
```python
# core/settings.py
STATIC_VERSION = '2025-01-24-file-limit-fix'  # ← Cambiar esto
```

---

## ✅ Campos en SystemSettings

| Campo | Descripción | Valor Defecto | Aplica a |
|-------|-------------|---------------|----------|
| `max_file_size_mb` | Tamaño máximo general | 1500 MB | Desktop, Tablets |
| `upload_max_file_size_mobile_mb` | Tamaño máximo móviles | 200 MB | Smartphones |

### 📱 Detección de Móviles

El sistema detecta automáticamente si el usuario está en móvil:
```javascript
isMobile = /android|iphone|ipad|mobile|tablet/.test(navigator.userAgent)
```

- **Desktop/Tablet:** Usa `max_file_size_mb` (1500 MB)
- **Smartphone:** Usa `upload_max_file_size_mobile_mb` (200 MB)

---

## 📋 ¿Dónde se Cambian los Límites?

### En el Panel de Admin:

1. **Ir a:** `/admin/main/systemsettings/`
2. **Buscar sección:** "LÍMITES DE ARCHIVOS"
3. **Campos disponibles:**
   - **Tamaño máximo de archivo (MB):** 1500 ← Desktop/General
   - **Tamaño máximo móvil (MB):** 200 ← Solo móviles
4. **Guardar cambios**

### Captura de Pantalla del Admin:

```
┌─────────────────────────────────────────────┐
│ LÍMITES DE ARCHIVOS                         │
├─────────────────────────────────────────────┤
│ Tamaño máximo de archivo (MB)     [1500]   │
│ Tamaño máximo móvil (MB)          [ 200]   │
│                                              │
│ Memoria máxima para uploads (MB)  [  25]   │
│ Tamaño máximo para checksum (MB)  [  50]   │
└─────────────────────────────────────────────┘
```

---

## ⚠️ Archivos con Límites Específicos (Intencionales)

| Archivo | Límite | Razón |
|---------|--------|-------|
| `finance.js` | 5MB | Comprobantes de pago (deben ser pequeños) |

---

## 🧪 Cómo Verificar que Funciona

### 1. Verificar en el Navegador
```javascript
// Abrir DevTools (F12) → Console
document.querySelector('meta[name="max-file-size"]')?.content
// Desktop: "1500"

document.querySelector('meta[name="max-file-size-mobile"]')?.content
// Mobile: "200"
```

### 2. Verificar en el Backend
```bash
docker-compose exec web python manage.py shell
```
```python
from apps.main.models import SystemSettings
s = SystemSettings.load()
print(f"Desktop: {s.max_file_size_mb}MB")
print(f"Mobile: {s.upload_max_file_size_mobile_mb}MB")
```

### 3. Probar un Upload
- **Desktop:** Archivo de 1200MB → "Muy grande (máx: 1500MB)"
- **Mobile:** Archivo de 250MB → "Muy grande (máx: 200MB)"

---

## 📝 Resumen

| Acción | Backend | Frontend |
|--------|---------|----------|
| Cambias en Admin | ✅ Inmediato | ❌ Requiere recarga |
| Usuario recarga página | ✅ Nuevo valor | ✅ Nuevo valor |
| Usuario NO recarga | ✅ Nuevo valor | ❌ Valor viejo (caché) |

### 🎯 La Clave

**El sistema está 100% dinámico:**
- Backend lee de la DB siempre
- Frontend lee de los meta tags (que vienen del backend)
- Límites diferentes para Desktop (1500MB) y Mobile (200MB)
- **Solo el caché del navegador puede causar desfase**

### 🔧 Solución Definitiva

**Para usuarios:**
```
Ctrl + Shift + R (recarga completa)
```

**Para despliegues:**
```python
# Actualizar STATIC_VERSION en settings.py
STATIC_VERSION = '2025-01-24-nueva-version'
```

---

## ✨ Cambios Recientes (2025-01-24)

1. ✅ Agregados meta tags en `base.html` (global) para desktop y mobile
2. ✅ `context_processors.py` expone ambos límites
3. ✅ `mobile_upload_optimizer.js` usa límite específico para móviles
4. ✅ `_files_tab.html` valida correctamente según dispositivo
5. ✅ `STATIC_VERSION` actualizado para forzar recarga

**Ahora los límites se actualizan automáticamente en backend Y frontend al cambiar en Admin.**
(Solo requiere que el usuario recargue la página)

---

## 🔥 Preguntas Frecuentes

### ¿Por qué límites diferentes para móviles?

- **Conexión:** Móviles suelen tener conexiones más lentas/inestables
- **Batería:** Uploads grandes consumen mucha batería
- **Experiencia:** Mejor UX con archivos más pequeños en móvil
- **Recomendación:** Desktop para archivos grandes (DWG, RVT, etc.)

### ¿Puedo hacer que móviles usen el mismo límite que desktop?

Sí, simplemente configura en el admin:
```
upload_max_file_size_mobile_mb = 1500
```

### ¿Los cambios requieren reiniciar el servidor?

**No.** Los cambios en SystemSettings se aplican inmediatamente:
- Backend: ✅ Inmediato
- Frontend: ✅ Al recargar la página

### ¿Qué pasa si el usuario no recarga?

Seguirá viendo los límites antiguos hasta que:
1. Recargue la página manualmente
2. Navegue a otra página del sitio
3. Cierre y abra el navegador

---

## ⚠️ Archivos con Límites Específicos (Intencionales)

| Archivo | Límite | Razón |
|---------|--------|-------|
| `finance.js` | 5MB | Comprobantes de pago (deben ser pequeños) |

---

## 🧪 Cómo Verificar que Funciona

### 1. Verificar en el Navegador
```javascript
// Abrir DevTools (F12) → Console
document.querySelector('meta[name="max-file-size"]')?.content
// Debería mostrar: "1500"
```

### 2. Verificar en el Backend
```bash
docker-compose exec web python manage.py shell
```
```python
from apps.main.models import SystemSettings
s = SystemSettings.load()
print(f"Límite actual: {s.max_file_size_mb}MB")
```

### 3. Probar un Upload
- Seleccionar archivo de 1200MB
- Debería mostrar: "Muy grande (máx: 1500MB)"

---

## 📝 Resumen

| Acción | Backend | Frontend |
|--------|---------|----------|
| Cambias en Admin | ✅ Inmediato | ❌ Requiere recarga |
| Usuario recarga página | ✅ Nuevo valor | ✅ Nuevo valor |
| Usuario NO recarga | ✅ Nuevo valor | ❌ Valor viejo (caché) |

### 🎯 La Clave

**El sistema está 100% dinámico:**
- Backend lee de la DB siempre
- Frontend lee del meta tag (que viene del backend)
- **Solo el caché del navegador puede causar desfase**

### 🔧 Solución Definitiva

**Para usuarios:**
```
Ctrl + Shift + R (recarga completa)
```

**Para despliegues:**
```python
# Actualizar STATIC_VERSION en settings.py
STATIC_VERSION = '2025-01-24-nueva-version'
```

---

## ✨ Cambios Recientes (2025-01-24)

1. ✅ Agregado meta tag en `base.html` (global)
2. ✅ `mobile_upload_optimizer.js` ahora lee del meta tag
3. ✅ `_files_tab.html` usa límite del sistema para todos los dispositivos
4. ✅ `STATIC_VERSION` actualizado para forzar recarga

**Ahora el límite se actualiza automáticamente en backend Y frontend al cambiar en Admin.**
(Solo requiere que el usuario recargue la página)
