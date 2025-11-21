# 📦 Guía de Testing de Storage de Archivos

**Fecha:** 11 de Noviembre, 2025  
**Módulo:** FILES  
**Ambientes:** Local (FileSystemStorage) y Producción (Cloudflare R2)

---

## 🎯 RESUMEN

Tu proyecto soporta **DOS modos de storage**:

| Modo | Ubicación | Cuándo usarlo |
|------|-----------|---------------|
| **Local** | `media/organizations/` | Desarrollo, Tests, CI/CD |
| **R2 (Cloudflare)** | Bucket R2 en la nube | Staging, Producción |

---

## 🔧 CONFIGURACIÓN

### Modo LOCAL (FileSystemStorage)

```bash
# .env o docker-compose.yml
ENABLE_STORAGES=false  # ← Por defecto
```

**Archivos se guardan en:**
```
arc_manager/
└── media/
    └── organizations/
        └── {org_id}/
            └── projects/
                └── {project_id}/
                    └── phases/
                        └── {phase_id}/
                            └── archivo.pdf
```

### Modo R2 (Cloudflare)

```bash
# .env de producción
ENABLE_STORAGES=true
CLOUDFLARE_R2_ENDPOINT_URL=https://tu-account-id.r2.cloudflarestorage.com
CLOUDFLARE_R2_BUCKET_NAME=arc-manager-prod
CLOUDFLARE_R2_ACCESS_KEY_ID=tu_access_key
CLOUDFLARE_R2_SECRET_ACCESS_KEY=tu_secret_key
CLOUDFLARE_R2_REGION=auto
```

---

## ✅ ESTRATEGIA DE TESTING

### 1️⃣ Tests Unitarios (Automáticos)

**Qué:** Tests con mocks, no suben archivos reales  
**Dónde:** `tests/files/`  
**Ventajas:** Rápidos, no consumen storage, detectan bugs de lógica

```bash
# Ejecutar tests unitarios
docker-compose exec web pytest tests/files/ -v

# Solo tests de seguridad
docker-compose exec web pytest tests/files/security/ -v -m security

# Con cobertura
docker-compose exec web pytest tests/files/ --cov=apps.files --cov-report=html
```

**Estos tests usan:**
- Fixtures que fuerzan `FileSystemStorage` en memoria
- Mocks para operaciones de R2/S3
- Validaciones sin subir archivos reales

### 2️⃣ Testing Manual LOCAL

**Qué:** Probar subida/descarga con archivos reales localmente  
**Cuándo:** Después de cambios en storage o validaciones

**Pasos:**

```bash
# 1. Asegurar que está en modo local
docker-compose exec web python manage.py shell
>>> from django.conf import settings
>>> settings.STORAGES['default']['BACKEND']
'django.core.files.storage.FileSystemStorage'

# 2. Levantar el servidor
docker-compose up

# 3. Acceder a http://localhost:8000
# 4. Subir archivos desde la UI
# 5. Verificar que se guardaron

# Ver archivos guardados
docker-compose exec web ls -la media/organizations/

# Ver estructura completa
docker-compose exec web tree media/organizations/
```

**Probar:**
- ✅ Subir PDF, JPG, DWG, RVT
- ✅ Intentar subir .exe (debe fallar)
- ✅ Subir archivo >500MB (debe fallar o procesar según config)
- ✅ Descargar archivo subido
- ✅ Eliminar archivo
- ✅ Verificar que usuario solo ve archivos de su organización

### 3️⃣ Testing Manual en STAGING/R2

**Qué:** Probar con Cloudflare R2 real  
**Cuándo:** Antes de deploy a producción

**Configuración de Staging:**

```bash
# .env.staging
ENABLE_STORAGES=true
CLOUDFLARE_R2_ENDPOINT_URL=https://tu-account.r2.cloudflarestorage.com
CLOUDFLARE_R2_BUCKET_NAME=arc-manager-staging  # ← Bucket de staging
CLOUDFLARE_R2_ACCESS_KEY_ID=...
CLOUDFLARE_R2_SECRET_ACCESS_KEY=...
```

**Pasos:**

1. **Deploy a staging**
   ```bash
   # Tu proceso de deploy (Railway, Docker, etc.)
   ```

2. **Verificar configuración**
   ```bash
   # En el servidor
   python manage.py shell
   >>> from django.conf import settings
   >>> settings.STORAGES['default']['BACKEND']
   'storages.backends.s3boto3.S3Boto3Storage'
   >>> settings.AWS_S3_ENDPOINT_URL
   'https://tu-account.r2.cloudflarestorage.com'
   ```

3. **Subir archivo de prueba**
   - Ir a la UI de staging
   - Subir un archivo PDF pequeño
   - Verificar que se subió exitosamente

4. **Verificar en Dashboard de Cloudflare**
   - Ir a: https://dash.cloudflare.com/
   - Sección: R2 → Tu bucket
   - Buscar: `organizations/{org_id}/projects/{project_id}/phases/{phase_id}/`
   - Confirmar que el archivo está ahí

5. **Probar descarga**
   - Hacer clic en el archivo en la UI
   - Verificar que se descarga correctamente
   - Verificar que el contenido es correcto

6. **Probar eliminación**
   - Eliminar el archivo desde la UI
   - Verificar en dashboard de R2 que se eliminó

7. **Probar archivos grandes**
   - Subir archivo de 50MB+
   - Verificar que usa multipart upload
   - Verificar progreso en UI

**Checklist de Pruebas en R2:**

```
[ ] Subir PDF (< 10MB)
[ ] Subir imagen JPG (< 5MB)
[ ] Subir DWG/RVT (10-100MB)
[ ] Subir archivo grande (>100MB)
[ ] Descargar archivo
[ ] Eliminar archivo
[ ] Verificar path correcto en R2
[ ] Intentar subir .exe (debe fallar)
[ ] Verificar límites de storage de organización
[ ] Verificar que usuario solo ve sus archivos
[ ] Verificar logging de operaciones
```

### 4️⃣ Script de Testing Automático (Ambos Ambientes)

Voy a crear un script que puedes ejecutar:

**`tests/scripts/test_storage.py`** (próximo paso)

```bash
# Probar storage local
docker-compose exec web python tests/scripts/test_storage.py --local

# Probar storage R2
docker-compose exec web python tests/scripts/test_storage.py --r2

# Probar ambos
docker-compose exec web python tests/scripts/test_storage.py --all
```

---

## 🐛 TROUBLESHOOTING

### Problema: "Archivo no se sube"

**Local:**
```bash
# Verificar permisos del directorio media
docker-compose exec web ls -la media/
docker-compose exec web chmod -R 777 media/

# Ver logs
docker-compose logs -f web
```

**R2:**
```bash
# Verificar credenciales
docker-compose exec web python manage.py shell
>>> import boto3
>>> from django.conf import settings
>>> client = boto3.client(
...     's3',
...     endpoint_url=settings.AWS_S3_ENDPOINT_URL,
...     aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
...     aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
... )
>>> client.list_buckets()  # Debe mostrar tus buckets
```

### Problema: "ValidationError: Tipo de archivo no permitido"

```bash
# Ver extensiones permitidas
docker-compose exec web python manage.py shell
>>> import os
>>> os.environ.get('ALLOWED_EXTENSIONS')
'PDF,JPG,JPEG,PNG,GIF,DWG,DXF,RVT,...'
```

### Problema: "Storage limit exceeded"

```bash
# Ver uso de storage por organización
docker-compose exec web python manage.py shell
>>> from apps.files.models import ProjectFile
>>> from apps.orgs.models import Organization
>>> org = Organization.objects.first()
>>> usage = ProjectFile.objects.get_storage_usage_by_org(org.id)
>>> print(f"Archivos: {usage['total_files']}, Tamaño: {usage['total_size'] / 1024 / 1024:.2f} MB")
```

---

## 📊 MÉTRICAS A MONITOREAR

### En Tests
- ✅ Cobertura de tests de seguridad: >95%
- ✅ Tests de validación: todos pasan
- ✅ Tests de permisos: todos pasan

### En Producción (R2)
- 📊 Tamaño promedio de archivos
- 📊 Tiempo promedio de upload
- 📊 Tasa de errores de upload
- 📊 Uso de storage por organización
- 📊 Archivos grandes (>100MB)

**Dashboard de Cloudflare R2:**
- Operations: Subidas/Descargas por día
- Storage: Tamaño total usado
- Class A operations: Escrituras (cobradas)
- Class B operations: Lecturas (cobradas)

---

## 🔐 SEGURIDAD

### Validaciones que DEBEN funcionar en AMBOS ambientes:

1. **Extensiones peligrosas bloqueadas**
   ```python
   # .exe, .bat, .sh, .js, .php, etc.
   ```

2. **Path traversal prevenido**
   ```python
   # ../../../etc/passwd → sanitizado
   ```

3. **Límites de tamaño respetados**
   ```python
   # >500MB (configurable) → rechazado
   ```

4. **Acceso cross-org bloqueado**
   ```python
   # Usuario org A no ve archivos de org B
   ```

---

## 📝 LOGS A REVISAR

### Local
```bash
docker-compose logs -f web | grep FILE
```

### Producción
```bash
# En tu sistema de logging (CloudWatch, Datadog, etc.)
# Buscar: FILE_UPLOAD, FILE_DOWNLOAD, FILE_DELETE, FILE_ERROR
```

**Eventos importantes:**
- `FILE_UPLOAD_SUCCESS`: Archivo subido OK
- `FILE_UPLOAD_ERROR`: Error en subida
- `FILE_UPLOAD_INVALID_TYPE`: Extensión no permitida
- `FILE_UPLOAD_STORAGE_LIMIT`: Límite excedido
- `FILE_UPLOAD_PERMISSION_DENIED`: Sin permisos

---

## ✅ CHECKLIST ANTES DE PRODUCCIÓN

```
[ ] Tests unitarios pasan (pytest)
[ ] Tests de seguridad pasan (>80 tests)
[ ] Probado manualmente en local
[ ] Probado en staging con R2
[ ] Límites de storage configurados
[ ] Extensiones permitidas configuradas
[ ] Logging funcionando
[ ] Dashboard de R2 monitoreado
[ ] Backup strategy definida
[ ] Proceso de rollback documentado
```

---

**Última actualización:** 11 de Noviembre, 2025  
**Autor:** AI Assistant  
**Versión:** 1.0




