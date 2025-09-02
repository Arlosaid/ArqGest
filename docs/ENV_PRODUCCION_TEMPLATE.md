# 🚀 Variables de Entorno para Producción - Arc Manager MVP

## ⚠️ Template de .env para Producción

Crea un archivo `.env` en tu servidor/plataforma con estas variables:

```env
# ===========================================
# 🔒 SEGURIDAD CRÍTICA
# ===========================================
DEBUG=False
SECRET_KEY=GENERA-UNA-CLAVE-SUPER-SEGURA-DE-50-CARACTERES-AQUI
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com,tu-app.railway.app

# ===========================================
# 🗄️ BASE DE DATOS
# ===========================================
DATABASE_URL=postgresql://usuario:password@host:5432/database_name
CONN_MAX_AGE=120

# ===========================================
# 📧 EMAIL (Amazon SES)
# ===========================================
AWS_ACCESS_KEY_ID=tu_aws_access_key_para_ses
AWS_SECRET_ACCESS_KEY=tu_aws_secret_para_ses
AWS_SES_REGION=us-east-1
DEFAULT_FROM_EMAIL=noreply@tu-dominio.com
AWS_SES_CONFIGURATION_SET=

# ===========================================
# 🗂️ ALMACENAMIENTO (Cloudflare R2) - CRÍTICO
# ===========================================
ENABLE_STORAGES=true
DEFAULT_FILE_STORAGE=storages.backends.s3boto3.S3Boto3Storage
AWS_S3_ENDPOINT_URL=https://tu-account-id.r2.cloudflarestorage.com
AWS_STORAGE_BUCKET_NAME=arcmanager-files-prod
AWS_ACCESS_KEY_ID=tu_r2_access_key
AWS_SECRET_ACCESS_KEY=tu_r2_secret_key
AWS_S3_REGION_NAME=auto
AWS_S3_ADDRESSING_STYLE=virtual
AWS_S3_SIGNATURE_VERSION=s3v4
AWS_S3_CUSTOM_DOMAIN=arcmanager-files-prod.r2.dev
AWS_DEFAULT_ACL=

# ===========================================
# 📁 VALIDACIONES DE ARCHIVOS
# ===========================================
MAX_FILE_SIZE_MB=600
ALLOWED_EXTENSIONS=PDF,JPG,JPEG,PNG,GIF,DWG,DXF,RVT,SKP,ZIP,RAR,TIFF,DOC,DOCX,XLS,XLSX,IFC,3DM
MAX_CHECKSUM_MB=50

# ===========================================
# 🔄 CACHE (Opcional - Redis)
# ===========================================
# REDIS_URL=redis://usuario:password@host:6379/0

# ===========================================
# 🚀 PLATAFORMA (Railway/Heroku/AWS)
# ===========================================
# RAILWAY_ENVIRONMENT=production
# AWS_EXECUTION_ENV=AWS_ECS_FARGATE
PRODUCTION=true
```

---

## 🔐 Generadores de SECRET_KEY Seguros

### Opción 1: Django
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Opción 2: Online (usar solo una vez)
- https://djecrety.ir/
- https://miniwebtool.com/django-secret-key-generator/

### Opción 3: PowerShell
```powershell
[System.Web.Security.Membership]::GeneratePassword(50, 10)
```

---

## 🚀 Configuración por Plataforma

### Railway.app (Recomendado para MVP)

1. **Deploy desde GitHub**:
   - Conecta tu repositorio
   - Railway detecta automáticamente Django

2. **Variables de entorno** (una por una en el panel):
   ```
   DEBUG=False
   SECRET_KEY=tu-clave-generada
   ALLOWED_HOSTS=*.railway.app,tu-dominio.com
   ENABLE_STORAGES=true
   # ... resto de variables R2
   ```

3. **Base de datos**:
   - Railway incluye PostgreSQL gratis
   - La `DATABASE_URL` se genera automáticamente

### Heroku

```bash
# Configurar variables
heroku config:set DEBUG=False
heroku config:set SECRET_KEY=tu-clave-super-segura
heroku config:set ALLOWED_HOSTS=tu-app.herokuapp.com,tu-dominio.com
heroku config:set ENABLE_STORAGES=true
# ... resto de variables
```

### AWS Elastic Beanstalk

1. **Environment Properties** en el panel:
   - Agregar cada variable manualmente
   - O usar archivo `.ebextensions/environment.config`

---

## ✅ Checklist de Seguridad

### 🔒 Obligatorias
- [ ] `DEBUG=False` en producción
- [ ] `SECRET_KEY` única y de 50+ caracteres
- [ ] `ALLOWED_HOSTS` sin comodines (`*`)
- [ ] `DATABASE_URL` con SSL
- [ ] Credenciales R2 con permisos mínimos

### 🛡️ Recomendadas
- [ ] HTTPS forzado (automático en Railway/Heroku)
- [ ] Backup automático de BD
- [ ] Monitoreo de errores (Sentry)
- [ ] Firewall configurado
- [ ] Logs centralizados

---

## 🧪 Verificar Configuración

### Script de verificación local:
```bash
# Activar entorno
.\venv\Scripts\activate.ps1

# Cargar variables de prueba
$env:DEBUG="False"
$env:SECRET_KEY="test-key-for-verification"
$env:ALLOWED_HOSTS="localhost,127.0.0.1"

# Verificar configuración
python arc_manager/manage.py check --deploy
```

Esto debe mostrar **System check identified no issues**.

---

## 📊 Costos Estimados por Plataforma

| Plataforma | Costo/mes | BD incluida | SSL | Escalabilidad |
|------------|-----------|-------------|-----|---------------|
| **Railway** | $5-10 | ✅ PostgreSQL | ✅ | Excelente |
| **Heroku** | $7-25 | ❌ +$9 | ✅ | Buena |
| **DigitalOcean** | $10-20 | ❌ +$15 | ✅ | Buena |
| **AWS EB** | $15-30 | ❌ +$15 | ✅ | Excelente |

**Recomendación**: Empezar con **Railway** para el MVP.
