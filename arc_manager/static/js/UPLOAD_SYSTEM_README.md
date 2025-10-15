# 🚀 Sistema de Upload de Archivos Grandes

## Problema Resuelto

**Problema:** Cloudflare tiene límites estrictos para uploads HTTP:
- **100MB** en planes gratuitos/Pro
- **500MB** en planes Business/Enterprise  
- **Timeout de 100 segundos**

**Solución:** Upload directo a Cloudflare R2 usando URLs presignadas, evitando el proxy de Cloudflare.

## Cómo Funciona

### Para Archivos Pequeños (< 100MB)
- Upload tradicional a través del servidor Django
- Funciona normalmente con HTMX

### Para Archivos Grandes (> 100MB)
1. **Frontend** solicita URL presignada al backend
2. **Backend** genera URL presignada de Cloudflare R2
3. **Frontend** sube el archivo directamente a R2
4. **Frontend** confirma la subida al backend
5. **Backend** crea el registro en la base de datos

## Configuración Requerida

### Variables de Entorno en Producción

```bash
# Habilitar almacenamiento externo
ENABLE_STORAGES=true

# Configuración de Cloudflare R2
CLOUDFLARE_R2_ENDPOINT_URL=https://tu-account-id.r2.cloudflarestorage.com
CLOUDFLARE_R2_BUCKET_NAME=tu-bucket-name
CLOUDFLARE_R2_ACCESS_KEY_ID=tu-access-key
CLOUDFLARE_R2_SECRET_ACCESS_KEY=tu-secret-key
CLOUDFLARE_R2_REGION=auto

# Configuración de URLs presignadas
PRESIGN_EXPIRES_SECONDS=3600  # 1 hora
LARGE_FILE_THRESHOLD_MB=100   # Umbral para upload directo
```

### Configuración de Cloudflare R2

1. **Crear bucket en Cloudflare R2**
2. **Configurar CORS** para permitir uploads desde tu dominio:

```json
[
  {
    "AllowedOrigins": ["https://tu-dominio.com"],
    "AllowedMethods": ["GET", "PUT", "POST"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 3600
  }
]
```

3. **Crear API Token** con permisos de escritura al bucket

## Archivos del Sistema

### Frontend
- `large-file-upload.js` - Lógica principal del upload
- `_files_tab.html` - Template con formularios mejorados

### Backend  
- `files/views.py` - Endpoints para URLs presignadas
  - `get_presigned_upload()` - Genera URL presignada
  - `confirm_upload()` - Confirma upload exitoso

## Flujo de Upload Detallado

### 1. Detección de Archivo Grande
```javascript
const sizeInMB = file.size / (1024 * 1024);
if (sizeInMB > 100) {
    await this.handleLargeFileUpload(file, form);
} else {
    await this.handleRegularUpload(form);
}
```

### 2. Solicitar URL Presignada
```javascript
const presignedData = await fetch(`/projects/${projectId}/phases/${phaseId}/files/presigned-upload/`, {
    method: 'POST',
    body: JSON.stringify({
        filename: file.name,
        content_type: file.type,
        file_size: file.size
    })
});
```

### 3. Upload Directo a R2
```javascript
const xhr = new XMLHttpRequest();
xhr.open('PUT', presignedUrl);
xhr.setRequestHeader('Content-Type', file.type);
xhr.send(file);
```

### 4. Confirmar Upload
```javascript
await fetch('/files/confirm-upload/', {
    method: 'POST',
    body: JSON.stringify({
        key: key,
        project_id: projectId,
        phase_id: phaseId,
        size_bytes: sizeBytes,
        content_type: contentType
    })
});
```

## Beneficios

✅ **Evita límites de Cloudflare** - Upload directo a R2
✅ **Mejor rendimiento** - No pasa por el servidor Django
✅ **Progreso en tiempo real** - Barra de progreso visual
✅ **Manejo de errores** - Reintentos automáticos
✅ **Compatibilidad** - Funciona con archivos pequeños también
✅ **Mobile-friendly** - Optimizado para dispositivos móviles

## Troubleshooting

### Error: "Error obteniendo URL de upload"
- Verificar que `ENABLE_STORAGES=true`
- Verificar configuración de Cloudflare R2
- Verificar permisos del API token

### Error: "Upload failed: 403"
- Verificar configuración CORS en R2
- Verificar que la URL presignada no haya expirado

### Error: "Error confirmando upload"
- Verificar que el archivo se subió correctamente a R2
- Verificar conectividad del backend con R2

## Monitoreo

El sistema incluye logging detallado:
- `FILE_UPLOAD_ATTEMPT` - Inicio de upload
- `PRESIGNED_UPLOAD_SUCCESS` - URL presignada generada
- `CONFIRM_UPLOAD_SUCCESS` - Upload confirmado
- `FILE_UPLOAD_ERROR` - Errores durante el proceso

## Próximas Mejoras

- [ ] Upload por chunks para archivos > 1GB
- [ ] Resumable uploads para conexiones inestables
- [ ] Compresión automática de imágenes
- [ ] Preview de archivos antes del upload
