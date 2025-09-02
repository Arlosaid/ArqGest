# 🗄️ Guía de Configuración - Cloudflare R2 para Arc Manager

## ¿Por qué R2 es crítico para el MVP?

Los estudios de arquitectura manejan archivos pesados (DWG, RVT, PDF de planos) de 50-500MB. Servir estos archivos desde tu servidor web sería costoso y lento. **R2 es obligatorio para un MVP profesional**.

---

## 🚀 Configuración Paso a Paso

### 1. Crear cuenta en Cloudflare R2

1. Ve a [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Ve a **R2 Object Storage** en el sidebar
3. **Crear bucket** con un nombre descriptivo: `arcmanager-files-prod`

### 2. Obtener credenciales R2

1. Ve a **R2** → **Manage R2 API tokens**
2. **Create API token** con permisos:
   - **Object Read and Write**: para tu bucket específico
   - **Object Delete**: para tu bucket específico
3. Copia el **Access Key ID** y **Secret Access Key**
4. Anota tu **Account ID** (aparece en la URL del dashboard)

### 3. Configurar variables de entorno

En tu archivo `.env` de producción:

```env
# Activar almacenamiento externo
ENABLE_STORAGES=true
DEFAULT_FILE_STORAGE=storages.backends.s3boto3.S3Boto3Storage

# Configuración R2
AWS_S3_ENDPOINT_URL=https://<TU_ACCOUNT_ID>.r2.cloudflarestorage.com
AWS_STORAGE_BUCKET_NAME=arcmanager-files-prod
AWS_ACCESS_KEY_ID=<TU_R2_ACCESS_KEY_ID>
AWS_SECRET_ACCESS_KEY=<TU_R2_SECRET_ACCESS_KEY>
AWS_S3_REGION_NAME=auto
AWS_S3_ADDRESSING_STYLE=virtual
AWS_S3_SIGNATURE_VERSION=s3v4
AWS_DEFAULT_ACL=

# Opcional: Dominio personalizado
# AWS_S3_CUSTOM_DOMAIN=arcmanager-files-prod.r2.dev
```

### 4. Configurar dominio público (opcional pero recomendado)

1. En tu bucket de R2, ve a **Settings** → **Public access**
2. **Allow Access** y anota el dominio: `https://arcmanager-files-prod.r2.dev`
3. Agrega a tu `.env`:
   ```env
   AWS_S3_CUSTOM_DOMAIN=arcmanager-files-prod.r2.dev
   ```

---

## 🧪 Verificar Configuración

### Prueba local con R2:

```bash
# 1. Activar entorno
.\venv\Scripts\activate.ps1

# 2. Configurar variables temporales para test
$env:ENABLE_STORAGES="true"
$env:AWS_S3_ENDPOINT_URL="https://tu-account.r2.cloudflarestorage.com"
$env:AWS_STORAGE_BUCKET_NAME="tu-bucket"
$env:AWS_ACCESS_KEY_ID="tu-key"
$env:AWS_SECRET_ACCESS_KEY="tu-secret"

# 3. Probar subida
python arc_manager/manage.py shell
```

En el shell de Django:
```python
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

# Probar subida
content = ContentFile(b"Test file content")
path = default_storage.save("test/archivo-prueba.txt", content)
print(f"Archivo guardado en: {path}")

# Probar URL
url = default_storage.url(path)
print(f"URL del archivo: {url}")

# Limpiar
default_storage.delete(path)
print("Archivo eliminado")
```

---

## 💰 Costos Estimados

**R2 es MUY económico:**
- **Almacenamiento**: $0.015/GB/mes
- **Egress (descarga)**: **GRATIS** (vs $0.09/GB en S3)
- **Operaciones**: $4.50/millón de requests

**Para 10 clientes con 2GB promedio cada uno:**
- Almacenamiento: 20GB × $0.015 = **$0.30/mes**
- Egress: **$0/mes** (gratis en R2)
- **Total: ~$1/mes** 🎉

---

## 🔧 Troubleshooting

### Error: "No module named 'boto3'"
```bash
# Ya está en requirements.txt, pero si falla:
pip install boto3 django-storages
```

### Error: "Access Denied"
- Verifica que el Access Key tenga permisos de **Object Read/Write/Delete**
- Confirma que el bucket name sea correcto
- Revisa que el Account ID en el endpoint sea correcto

### Error: "Bucket not found"
- Verifica que `AWS_STORAGE_BUCKET_NAME` coincida exactamente con el nombre del bucket
- Confirma que el bucket esté en la misma cuenta que las credenciales

### Los archivos no se ven en R2
- Django guarda en rutas como `files/2024/01/archivo.pdf`
- Busca en tu bucket con el prefijo `files/`

---

## 🚀 Para Producción

### Variables críticas en tu plataforma de despliegue:

```env
# Obligatorias
ENABLE_STORAGES=true
DEFAULT_FILE_STORAGE=storages.backends.s3boto3.S3Boto3Storage
AWS_S3_ENDPOINT_URL=https://tu-account.r2.cloudflarestorage.com
AWS_STORAGE_BUCKET_NAME=tu-bucket-prod
AWS_ACCESS_KEY_ID=tu-r2-key
AWS_SECRET_ACCESS_KEY=tu-r2-secret
AWS_S3_REGION_NAME=auto
AWS_S3_ADDRESSING_STYLE=virtual
AWS_S3_SIGNATURE_VERSION=s3v4
AWS_DEFAULT_ACL=

# Recomendadas
AWS_S3_CUSTOM_DOMAIN=tu-bucket-prod.r2.dev
MAX_FILE_SIZE_MB=600
ALLOWED_EXTENSIONS=PDF,JPG,JPEG,PNG,GIF,DWG,DXF,RVT,SKP,ZIP,RAR,TIFF,DOC,DOCX,XLS,XLSX
```

---

## ✅ Ventajas de R2 vs Almacenamiento Local

| Aspecto | Local (Malo) | R2 (Excelente) |
|---------|--------------|----------------|
| **Costo de egress** | Alto (ancho de banda) | **Gratis** |
| **Escalabilidad** | Limitada por disco | **Ilimitada** |
| **Velocidad** | Lenta para archivos grandes | **CDN global** |
| **Backup** | Manual | **Automático** |
| **Disponibilidad** | 1 servidor | **99.9%** |

**Con R2 configurado, tu MVP estará listo para manejar estudios de arquitectura reales con archivos de 100-500MB sin problemas.**
