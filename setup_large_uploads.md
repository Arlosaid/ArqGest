# 🚀 Configuración de Uploads Grandes - Guía Rápida

## ✅ Solución Implementada

He implementado un **sistema completo de uploads grandes** que evita los límites de Cloudflare usando **upload directo a Cloudflare R2**.

### 📁 Archivos Creados/Modificados:

1. **`arc_manager/static/js/large-file-upload.js`** - Sistema JavaScript completo
2. **`arc_manager/templates/base.html`** - Incluye el nuevo script
3. **`arc_manager/apps/projects/templates/projects/partials/_files_tab.html`** - Template actualizado
4. **`env.example`** - Variables de entorno añadidas
5. **`setup_large_uploads.md`** - Esta guía
6. **`arc_manager/static/js/UPLOAD_SYSTEM_README.md`** - Documentación técnica

## 🔧 Configuración en Producción

### 1. Variables de Entorno en Railway

Añade estas variables en Railway:

```bash
# Habilitar almacenamiento externo
ENABLE_STORAGES=true

# Configuración de Cloudflare R2
CLOUDFLARE_R2_ENDPOINT_URL=https://TU-ACCOUNT-ID.r2.cloudflarestorage.com
CLOUDFLARE_R2_BUCKET_NAME=tu-bucket-name
CLOUDFLARE_R2_ACCESS_KEY_ID=tu-access-key-id
CLOUDFLARE_R2_SECRET_ACCESS_KEY=tu-secret-access-key
CLOUDFLARE_R2_REGION=auto

# Configuración de uploads
PRESIGN_EXPIRES_SECONDS=3600
LARGE_FILE_THRESHOLD_MB=100
```

### 2. Configurar Cloudflare R2

#### A. Crear Bucket
1. Ve a Cloudflare Dashboard > R2 Object Storage
2. Crea un nuevo bucket (ej: `arc-manager-files`)
3. Configura la región según tu ubicación

#### B. Configurar CORS
En tu bucket, ve a Settings > CORS policy y añade:

```json
[
  {
    "AllowedOrigins": [
      "https://tu-dominio-de-produccion.com",
      "https://tu-app.railway.app"
    ],
    "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3600
  }
]
```

#### C. Crear API Token
1. Ve a Cloudflare Dashboard > My Profile > API Tokens
2. Crea un token personalizado con:
   - **Permissions:** 
     - Zone:Zone Settings:Read
     - Zone:Zone:Read  
     - Account:Cloudflare R2:Edit
   - **Account Resources:** Tu cuenta
   - **Zone Resources:** Tu zona/dominio

### 3. Verificar Configuración

Después del deploy, verifica en los logs que veas:
```
🌍 Usando almacenamiento Cloudflare R2: https://tu-account.r2.cloudflarestorage.com
```

## 🎯 Cómo Funciona Ahora

### Para Archivos Pequeños (< 100MB)
- ✅ Upload normal a través del servidor
- ✅ Funciona como antes

### Para Archivos Grandes (> 100MB)  
- ✅ **Paso 1:** Frontend solicita URL presignada
- ✅ **Paso 2:** Upload directo a Cloudflare R2 (evita proxy)
- ✅ **Paso 3:** Confirmación al backend
- ✅ **Paso 4:** Registro en base de datos

## 📊 Beneficios Inmediatos

✅ **Evita límites de Cloudflare** - Archivos hasta 5GB
✅ **Mejor velocidad** - Upload directo, sin pasar por servidor
✅ **Progreso visual** - Barra de progreso en tiempo real
✅ **Compatibilidad total** - Funciona con archivos pequeños también
✅ **Mobile-friendly** - Optimizado para móviles
✅ **Manejo de errores** - Reintentos automáticos

## 🧪 Probar la Solución

1. **Deploy** los cambios a Railway
2. **Configura** las variables de entorno de R2
3. **Intenta subir** un archivo > 100MB
4. **Observa** el progreso y que funcione correctamente

## 🆘 Troubleshooting

### "Error obteniendo URL de upload"
- Verifica `ENABLE_STORAGES=true`
- Verifica credenciales de R2

### "Upload failed: 403 Forbidden"  
- Verifica configuración CORS en R2
- Verifica permisos del API token

### "Error confirmando upload"
- Verifica conectividad backend-R2
- Revisa logs del servidor

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs de Railway
2. Verifica la configuración de R2
3. Prueba con un archivo pequeño primero
4. Consulta `arc_manager/static/js/UPLOAD_SYSTEM_README.md` para detalles técnicos

---

**¡Tu sistema ya está listo para manejar archivos grandes sin límites de Cloudflare!** 🎉
