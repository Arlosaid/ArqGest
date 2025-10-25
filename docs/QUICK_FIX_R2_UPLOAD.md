# 🚀 Solución Rápida: Error de Upload a R2

## 🚨 Error Actual
```
Error en upload: Network error during upload
```

## ✅ Solución Inmediata

### Opción 1: Configurar CORS en R2 (Recomendado - 5 minutos)

1. **Ve a Cloudflare Dashboard**
   - URL: https://dash.cloudflare.com
   - R2 > [Tu Bucket] > Settings

2. **Agregar CORS Policy**
   
   Copia y pega esto en la configuración CORS:
   
   ```json
   [
     {
       "AllowedOrigins": ["https://app.arqgest.com"],
       "AllowedMethods": ["GET", "PUT", "HEAD"],
       "AllowedHeaders": ["Content-Type", "Content-Length"],
       "ExposeHeaders": ["ETag"],
       "MaxAgeSeconds": 3600
     }
   ]
   ```

3. **Guardar y esperar 1-2 minutos**

4. **Probar de nuevo**

### Opción 2: Fallback Automático (Ya implementado)

El código ahora automáticamente intenta usar el método alternativo (a través del servidor) si el upload directo falla.

**Limitaciones:**
- Archivos >100MB pueden causar timeout en Railway
- Más lento para archivos grandes
- Mayor uso de recursos del servidor

## 🔍 Diagnosticar el Problema

Ejecuta esto en la consola del navegador (F12):

```javascript
// En https://app.arqgest.com/projects/16/
R2Diagnostics.runFullDiagnostics(16, 26)
```

Reemplaza `16` y `26` con tu projectId y phaseId actual.

## 📊 Verificar si CORS está configurado

```javascript
// En la consola del navegador
fetch('https://c5bd3de23c243e64f2a92e4d69af055c.r2.cloudflarestorage.com/', {
  method: 'HEAD'
})
.then(res => {
  console.log('✅ CORS OK:', res.headers.get('access-control-allow-origin'));
})
.catch(err => {
  console.error('❌ CORS Error:', err);
});
```

## ⚙️ Configuración Completa de CORS

Para desarrollo + producción + staging:

```json
[
  {
    "AllowedOrigins": [
      "https://app.arqgest.com",
      "https://*.railway.app",
      "http://localhost:8000"
    ],
    "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag", "Content-Type", "Content-Length"],
    "MaxAgeSeconds": 3600
  }
]
```

## 🐛 Si sigue sin funcionar

1. **Verifica en DevTools:**
   - F12 > Network
   - Busca la petición PUT al dominio `r2.cloudflarestorage.com`
   - Ve el error específico

2. **Errores comunes:**

   | Error | Causa | Solución |
   |-------|-------|----------|
   | `No 'Access-Control-Allow-Origin'` | Falta dominio en AllowedOrigins | Agregar dominio exacto |
   | `Method PUT is not allowed` | PUT no está en AllowedMethods | Agregar "PUT" |
   | `Status 0` | Preflight falló | Configurar CORS completo |

3. **Contactar al equipo:**
   - Envía captura de DevTools > Network
   - Incluye el error exacto de la consola

## 📈 Monitoreo

Después de configurar CORS, los logs deberían mostrar:

```
✅ Upload a R2 exitoso: 200
✅ Upload completado exitosamente!
```

En lugar de:

```
❌ Network error durante upload a R2
💡 Tip: Este error suele indicar un problema de CORS.
```

## 🎯 Resultado Esperado

- Archivos <100MB: Upload normal (a través del servidor)
- Archivos >100MB: Upload directo a R2 (requiere CORS)
- Ambos métodos funcionan automáticamente

---

**Tiempo estimado de solución:** 5-10 minutos  
**Dificultad:** Fácil (solo copiar/pegar configuración)
