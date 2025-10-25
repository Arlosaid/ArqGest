# 🔧 Configuración CORS para Cloudflare R2

## 🚨 Problema Detectado

El error `"Network error during upload"` ocurre porque el navegador bloquea las peticiones PUT directas al bucket de R2 debido a la falta de configuración CORS.

## ✅ Solución: Configurar CORS en R2

### 1. Acceder a Cloudflare Dashboard

1. Ve a https://dash.cloudflare.com
2. Navega a **R2** en el menú lateral
3. Selecciona tu bucket de almacenamiento

### 2. Configurar CORS Policy

En la pestaña **Settings** del bucket, agrega esta configuración CORS:

```json
[
  {
    "AllowedOrigins": [
      "https://app.arqgest.com",
      "https://*.railway.app",
      "http://localhost:8000",
      "http://127.0.0.1:8000"
    ],
    "AllowedMethods": [
      "GET",
      "PUT",
      "POST",
      "DELETE",
      "HEAD"
    ],
    "AllowedHeaders": [
      "*"
    ],
    "ExposeHeaders": [
      "ETag",
      "Content-Type",
      "Content-Length"
    ],
    "MaxAgeSeconds": 3600
  }
]
```

### 3. Configuración Mínima (Producción)

Si solo necesitas producción:

```json
[
  {
    "AllowedOrigins": [
      "https://app.arqgest.com"
    ],
    "AllowedMethods": [
      "GET",
      "PUT",
      "HEAD"
    ],
    "AllowedHeaders": [
      "Content-Type",
      "Content-Length"
    ],
    "ExposeHeaders": [
      "ETag"
    ],
    "MaxAgeSeconds": 3600
  }
]
```

## 📝 Explicación de la Configuración

- **AllowedOrigins**: Dominios permitidos para hacer peticiones
  - `https://app.arqgest.com` - Tu dominio de producción
  - `https://*.railway.app` - Subdominios de Railway (staging/preview)
  - `http://localhost:8000` - Desarrollo local
  
- **AllowedMethods**: Métodos HTTP permitidos
  - `PUT` - **CRÍTICO** para uploads directos con presigned URLs
  - `GET` - Para descargar archivos
  - `HEAD` - Para verificar existencia de archivos
  
- **AllowedHeaders**: Headers que el navegador puede enviar
  - `*` permite todos (más permisivo)
  - O especificar: `["Content-Type", "Content-Length"]`
  
- **ExposeHeaders**: Headers que el navegador puede leer en la respuesta
  - `ETag` - Útil para verificar uploads
  
- **MaxAgeSeconds**: Tiempo de caché de la preflight request
  - `3600` = 1 hora

## 🧪 Verificar la Configuración

Después de aplicar la configuración CORS, verifica que funciona:

1. **Desde la consola del navegador:**
```javascript
// En https://app.arqgest.com
fetch('https://YOUR-ACCOUNT-ID.r2.cloudflarestorage.com/YOUR-BUCKET', {
  method: 'HEAD'
})
.then(res => console.log('CORS OK:', res.ok))
.catch(err => console.error('CORS Error:', err));
```

2. **Intentar subir un archivo pequeño** desde la aplicación

## 🔍 Diagnosticar Problemas CORS

Si sigue fallando, verifica en las DevTools del navegador:

1. Abre **DevTools** (F12)
2. Ve a la pestaña **Network**
3. Intenta subir un archivo
4. Busca la petición **OPTIONS** (preflight)
5. Revisa los headers de la respuesta:
   - `Access-Control-Allow-Origin`
   - `Access-Control-Allow-Methods`
   - `Access-Control-Allow-Headers`

## ⚠️ Errores Comunes

### Error: "CORS policy: No 'Access-Control-Allow-Origin' header"
**Causa**: El origen no está en `AllowedOrigins`
**Solución**: Agregar el dominio exacto a `AllowedOrigins`

### Error: "Method PUT is not allowed by Access-Control-Allow-Methods"
**Causa**: PUT no está en `AllowedMethods`
**Solución**: Agregar `"PUT"` a `AllowedMethods`

### Error: "Preflight request failed"
**Causa**: La petición OPTIONS no obtiene respuesta exitosa
**Solución**: Verificar que `AllowedHeaders` incluya los headers necesarios

## 🚀 Alternativa: Upload a través del Backend

Si no puedes configurar CORS en R2, puedes modificar el código para que los archivos grandes también pasen por el backend:

```python
# En arc_manager/apps/files/views.py
FORCE_BACKEND_UPLOAD = os.environ.get('FORCE_BACKEND_UPLOAD', 'false').lower() == 'true'
```

Esto deshabilitará los uploads directos a R2, pero puede causar timeouts en archivos muy grandes.

## 📚 Referencias

- [Cloudflare R2 CORS Documentation](https://developers.cloudflare.com/r2/api/s3/api/#cors)
- [MDN CORS Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
