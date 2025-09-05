# 🏢 Arc Manager

Sistema de gestión organizacional con Django + PostgreSQL en Docker.

## 📋 Tabla de Contenidos
- [🚀 Configuración Inicial](#-configuración-inicial)
- [🐳 Comandos Docker](#-comandos-docker)
- [🔧 Comandos Git](#-comandos-git)
- [📁 Estructura del Proyecto](#-estructura-del-proyecto)
- [💻 Desarrollo Local](#-desarrollo-local)
- [📊 Comandos Django](#-comandos-django)
- [🗄️ Base de Datos](#️-base-de-datos)
- [🌐 Despliegue en Producción](#-despliegue-en-producción)
- [🔍 Troubleshooting](#-troubleshooting)

## 🚀 Configuración Inicial

### 1. Clonar el repositorio
```bash
git clone <url-del-repositorio>
cd arc_manager
```

### 2. Crear archivo de variables de entorno
```bash
cp env.example .env
```

### 3. Configurar variables de entorno (opcional)
```env
# .env
DEBUG=True
SECRET_KEY=tu-clave-secreta-aqui
POSTGRES_DB=arc_manager_dev
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_PORT=5432
WEB_PORT=8000
```

## 🐳 Comandos Docker

### Construir y ejecutar (primera vez)
```bash
# Construir e iniciar todos los servicios
docker-compose up --build

# Ejecutar en segundo plano
docker-compose up -d --build
```

### Comandos básicos
```bash
# Iniciar servicios
docker-compose up

# Iniciar en segundo plano
docker-compose up -d

# Detener servicios
docker-compose down

# Ver logs
docker-compose logs

# Ver logs en tiempo real
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs web
docker-compose logs db
```

### Comandos de desarrollo
```bash
# Acceder al contenedor web
docker-compose exec web bash

# Ejecutar comandos Django dentro del contenedor
docker-compose exec web python manage.py <comando>

# Reiniciar solo el servicio web
docker-compose restart web

# Reconstruir imagen
docker-compose build web

# Limpiar contenedores, imágenes y volúmenes
docker-compose down -v
docker system prune -a
```

## 🔧 Comandos Git

### Comandos básicos
```bash
# Ver estado del repositorio
git status

# Agregar archivos al staging
git add .
git add <archivo>

# Hacer commit
git commit -m "Descripción del cambio"

# Enviar cambios al repositorio remoto
git push origin <rama>

# Traer cambios del repositorio remoto
git pull origin <rama>
```

### Manejo de ramas
```bash
# Ver todas las ramas
git branch -a

# Crear nueva rama
git checkout -b nueva-rama

# Cambiar de rama
git checkout <rama>

# Mergear rama
git merge <rama>

# Eliminar rama local
git branch -d <rama>
```

### Comandos útiles
```bash
# Ver historial de commits
git log --oneline

# Deshacer último commit (mantener cambios)
git reset HEAD~1

# Deshacer cambios en archivo
git checkout -- <archivo>

# Ver diferencias
git diff
```

## 📁 Estructura del Proyecto

```
arc_manager/
├── arc_manager/                 # Aplicación Django principal
│   ├── apps/                    # Aplicaciones Django
│   │   ├── accounts/           # Autenticación y usuarios
│   │   ├── main/               # Aplicación principal
│   │   ├── orgs/               # Organizaciones
│   │   ├── plans/              # Planes de suscripción
│   │   └── users/              # Gestión de usuarios
│   ├── core/                   # Configuración Django
│   │   ├── settings.py         # Configuración principal
│   │   ├── urls.py             # URLs principales
│   │   └── wsgi.py             # WSGI para producción
│   ├── static/                 # Archivos estáticos (CSS, JS, imágenes)
│   ├── templates/              # Templates HTML
│   └── manage.py               # Script de gestión Django
├── docker-compose.yml          # Configuración Docker Compose
├── Dockerfile                  # Configuración imagen Docker
├── requirements.txt            # Dependencias Python
├── deploy.sh                   # Script de despliegue
└── README.md                   # Este archivo
```

## 💻 Desarrollo Local

### Opción 1: Con Docker (Recomendado)
```bash
# Iniciar proyecto completo
docker-compose up --build

# Acceder a la aplicación
http://localhost:8000
```

### Opción 2: Sin Docker
```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar base de datos (PostgreSQL debe estar instalado)
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Iniciar servidor
python manage.py runserver
```

## 📊 Comandos Django

### Comandos básicos (con Docker)
```bash
# Ejecutar migraciones
docker-compose exec web python manage.py migrate

# Crear migraciones
docker-compose exec web python manage.py makemigrations

# Crear superusuario
docker-compose exec web python manage.py createsuperuser

# Cargar datos de prueba
docker-compose exec web python manage.py setup_demo_data

# Ejecutar tests
docker-compose exec web python manage.py test

# Abrir shell de Django
docker-compose exec web python manage.py shell
```

### Comandos personalizados del proyecto
```bash
# Configurar base de datos completa
docker-compose exec web python manage.py setup_database --force

# Crear organización
docker-compose exec web python manage.py create_organization

# Crear usuario
docker-compose exec web python manage.py create_user

# Listar organizaciones
docker-compose exec web python manage.py list_orgs

# Configurar planes MVP
docker-compose exec web python manage.py setup_mvp_plans

# Limpiar datos de tenant
docker-compose exec web python manage.py clean_tenant_data
```

## 🗄️ Base de Datos

### Acceder a PostgreSQL
```bash
# Acceder al contenedor de base de datos
docker-compose exec db psql -U postgres -d arc_manager_dev

# Comandos SQL útiles
\l                    # Listar bases de datos
\dt                   # Listar tablas
\d <tabla>           # Describir tabla
\q                   # Salir
```

### Backup y restore
```bash
# Crear backup
docker-compose exec db pg_dump -U postgres arc_manager_dev > backup.sql

# Restaurar backup
docker-compose exec -T db psql -U postgres arc_manager_dev < backup.sql
```

## 🌐 Despliegue en Producción

### 🚀 Railway (Recomendado para MVP)

#### 1. Configuración inicial
```bash
# Instalar Railway CLI (opcional)
npm install -g @railway/cli

# Login
railway login

# Deploy desde GitHub (recomendado)
# 1. Conecta tu repositorio en railway.app
# 2. Railway detecta automáticamente Django
# 3. Agrega PostgreSQL y Redis desde el dashboard
```

#### 2. Variables de entorno (Railway Dashboard)
Configura estas variables en Railway > Settings > Variables:
```
DEBUG=False
SECRET_KEY=tu-clave-secreta-muy-segura
DATABASE_URL=postgresql://... # Auto-generada por Railway
ALLOWED_HOSTS=*.up.railway.app,tu-dominio.com
ENABLE_STORAGES=true
# ... configuración R2
```

#### 3. Deploy automático
```bash
# Cada push a main despliega automáticamente
git push origin main

# Ver logs en tiempo real
railway logs
```

#### 4. Comandos útiles Railway
```bash
# Ver estado del servicio
railway status

# Ejecutar comandos en producción
railway run python manage.py migrate
railway run python manage.py createsuperuser

# Abrir aplicación
railway open
```

### 🐳 Docker en servidor (VPS/Servidor propio)

#### 1. Preparar servidor
```bash
# Instalar Docker y Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 2. Configurar proyecto
```bash
# Clonar proyecto
git clone <repositorio>
cd arc_manager

# Configurar variables de entorno
cp env.example .env
# Editar .env con valores de producción
```

#### 3. Desplegar
```bash
# Iniciar en producción
docker-compose -f docker-compose.yml up -d --build

# Ver logs
docker-compose logs -f
```

### ☁️ Otras opciones de despliegue

#### Railway
```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login y desplegar
railway login
railway deploy
```

#### Alternativas (no recomendadas para MVP)
```bash
# Otras opciones más costosas:
# - Heroku: $7-31/mes + add-ons
# - DigitalOcean App Platform: $12+/mes
# - AWS/GCP: $20-50/mes + configuración compleja
```

### 📋 Checklist de despliegue

Antes de desplegar a producción:

- [ ] **Configurar variables de entorno seguras**
  - [ ] `SECRET_KEY` - Generar clave única
  - [ ] `DEBUG=False`
  - [ ] `ALLOWED_HOSTS` - Dominios permitidos
  - [ ] `DATABASE_URL` - Base de datos de producción

- [ ] **Configurar base de datos**
  - [ ] PostgreSQL en producción
  - [ ] Backup automatizado
  - [ ] Conexión SSL

- [ ] **Configurar archivos estáticos**
  - [ ] `STATIC_ROOT` configurado
  - [ ] `MEDIA_ROOT` configurado
  - [ ] CDN opcional

- [ ] **Seguridad**
  - [ ] SSL/HTTPS habilitado
  - [ ] Firewall configurado
  - [ ] Actualizaciones de seguridad

- [ ] **Monitoreo**
  - [ ] Logs centralizados
  - [ ] Health checks
  - [ ] Alertas de errores

### 💰 Costos estimados

**Railway (Recomendado):**
- Hobby Plan: $0-5/mes (incluye PostgreSQL + Redis)
- Pro Plan: $20/mes (para producción)
- Escalamiento automático

**Alternativas más caras:**
- VPS básico: $5-15/mes (requiere configuración manual)
- Heroku: $7-31/mes (más caro que Railway)
- DigitalOcean Apps: $12+/mes

**✅ Railway (Recomendado):**
- Hobby: $0-5/mes (incluye PostgreSQL + Redis)
- Pro: $20/mes (producción)

## 🔍 Troubleshooting

### Problemas comunes

**Error: Puerto 8000 ya está en uso**
```bash
# Encontrar proceso usando el puerto
netstat -tulpn | grep :8000
# Matar proceso
kill -9 <PID>
```

**Error: Base de datos no conecta**
```bash
# Verificar que PostgreSQL esté corriendo
docker-compose ps

# Reiniciar servicios
docker-compose restart db
```

**Error: Migraciones**
```bash
# Resetear migraciones (⚠️ PELIGRO: Borra datos)
docker-compose exec web python manage.py migrate --fake-initial

# Aplicar migraciones manualmente
docker-compose exec web python manage.py migrate <app_name>
```

### Limpiar todo y empezar de nuevo
```bash
# Detener y eliminar todo
docker-compose down -v

# Eliminar imágenes
docker system prune -a

# Reconstruir desde cero
docker-compose up --build
```

### Logs útiles
```bash
# Ver logs del servicio web
docker-compose logs web

# Ver logs en tiempo real
docker-compose logs -f web

# Ver logs de base de datos
docker-compose logs db
```

## 🌐 URLs Importantes

- **Aplicación**: http://localhost:8000
- **Admin Django**: http://localhost:8000/admin
- **API Health**: http://localhost:8000/health/

## 📝 Notas Adicionales

- El proyecto usa **Python 3.11** y **Django 5.2**
- La base de datos es **PostgreSQL 15**
- El sistema incluye gestión de organizaciones, usuarios y planes
- Para producción, usar siempre PostgreSQL (no SQLite)

---

**¡Listo para desarrollar!** 🚀 