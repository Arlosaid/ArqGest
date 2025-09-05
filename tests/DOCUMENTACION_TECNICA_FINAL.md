# 🔧 Arc Manager - Documentación Técnica Completa

> **Sistema de Gestión de Proyectos Arquitectónicos**  
> Versión MVP - Documentación Técnica Final

---

## 📖 Índice

1. [Arquitectura del Sistema](#-arquitectura-del-sistema)
2. [Stack Tecnológico](#-stack-tecnológico)
3. [Estructura del Proyecto](#-estructura-del-proyecto)
4. [Módulos y Componentes](#-módulos-y-componentes)
5. [Base de Datos](#-base-de-datos)
6. [Configuración y Despliegue](#-configuración-y-despliegue)
7. [Seguridad](#-seguridad)
8. [Performance y Optimización](#-performance-y-optimización)
9. [APIs y Endpoints](#-apis-y-endpoints)
10. [Testing y Calidad](#-testing-y-calidad)
11. [Monitoreo y Logging](#-monitoreo-y-logging)
12. [Guía de Desarrollo](#-guía-de-desarrollo)

---

## 🏗️ Arquitectura del Sistema

### Arquitectura General

Arc Manager sigue una **arquitectura monolítica modular** basada en Django, optimizada para escalabilidad y mantenimiento. El sistema está diseñado con separación clara de responsabilidades y principios de arquitectura limpia.

```mermaid
graph TB
    subgraph "Frontend Layer"
        A[Templates HTML]
        B[CSS/JavaScript]
        C[Bootstrap 5]
    end

    subgraph "Application Layer"
        D[Django Views]
        E[Forms & Validation]
        F[Services Layer]
        G[Template Tags]
        H[Middleware Stack]
    end

    subgraph "Business Logic"
        I[Models]
        J[Signals]
        K[Management Commands]
        L[Custom Validators]
    end

    subgraph "Data Layer"
        M[(PostgreSQL 15)]
        N[(Redis Cache)]
        O[(Cloudflare R2)]
    end

    A --> D
    B --> D
    C --> A
    D --> E
    E --> F
    F --> I
    I --> M
    G --> A
    H --> D
    J --> I
    K --> F
    N --> F
    O --> F
```

### Principios Arquitectónicos

#### 1. **Separation of Concerns**
- **Models**: Lógica de datos y reglas de negocio
- **Views**: Controladores de presentación
- **Services**: Lógica de negocio compleja
- **Templates**: Presentación y UI

#### 2. **Multi-Tenant Architecture**
- **Organization-based**: Separación por organización
- **Middleware**: `OrganizationContextMiddleware` para contexto automático
- **QuerySets**: Filtrado automático por organización
- **Security**: Aislamiento completo de datos

#### 3. **Scalable File Management**
- **External Storage**: Cloudflare R2 para archivos grandes
- **Metadata Persistence**: Información en BD para búsquedas rápidas
- **Signed URLs**: Acceso seguro y eficiente
- **Progressive Upload**: Soporte para archivos de 600MB+

#### 4. **Performance First**
- **Database Optimization**: `select_related`, `prefetch_related`
- **Caching Strategy**: Redis para sesiones y cache
- **Connection Pooling**: `CONN_MAX_AGE` configurado
- **Static Files**: WhiteNoise para servir estáticos

---

## 💻 Stack Tecnológico

### Backend Core

#### Django 5.2
```python
# Características utilizadas:
- Model-View-Template (MVT) pattern
- Django ORM con PostgreSQL
- Authentication & Authorization
- Admin Interface personalizado
- Management Commands
- Signals para hooks automáticos
- Middleware personalizado
```

#### PostgreSQL 15
```sql
-- Características avanzadas utilizadas:
- Transacciones ACID
- Índices compuestos para performance
- Foreign Keys con CASCADE/SET_NULL
- JSON fields para configuraciones flexibles
- Full-text search capabilities
- Connection pooling
```

#### Redis 7
```python
# Uso en el sistema:
- Session storage
- Cache backend
- Próximamente: Task queue (Celery)
```

### Frontend Stack

#### Bootstrap 5 + CSS Custom
```css
/* Sistema de diseño unificado */
:root {
    --arc-color-primary: #3b82f6;
    --arc-color-secondary: #64748b;
    --arc-spacing-sm: 0.75rem;
    --arc-border-radius-sm: 0.5rem;
}

/* Componentes reutilizables */
.header-section { /* Estilo unificado */ }
.kanban-board { /* Drag & drop interface */ }
.file-uploader { /* Componente de subida */ }
```

#### JavaScript Vanilla
```javascript
// Componentes principales:
- KanbanManager: Drag & drop functionality
- FileUploader: Ajax file uploads
- TaskModal: HTMX integration
- NotificationManager: User feedback
```

### Infrastructure & DevOps

#### Docker + Docker Compose
```yaml
# Servicios containerizados:
services:
  web:      # Django application
  db:       # PostgreSQL database
  redis:    # Cache and sessions
```

#### Cloudflare R2
```python
# Configuración S3-compatible:
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_S3_ENDPOINT_URL = 'https://account.r2.cloudflarestorage.com'
```

### Dependencies Overview

```python
# requirements.txt principales:
Django==5.2                    # Framework web
psycopg[binary]==3.1.18       # PostgreSQL adapter
redis==5.0.3                  # Cache backend
django-redis==5.4.0           # Django-Redis integration
boto3==1.34.0                 # AWS SDK (para R2)
django-storages==1.14.2       # Storage backends
gunicorn==21.2.0              # WSGI server
whitenoise==6.6.0             # Static files serving
django-axes==6.1.1            # Security (brute force protection)
crispy-bootstrap5==2024.2     # Form rendering
```

---

## 📁 Estructura del Proyecto

### Organización de Directorios

```
arc_manager/
├── arc_manager/                    # Proyecto Django principal
│   ├── core/                       # Configuración central
│   │   ├── settings.py             # Configuración Django
│   │   ├── urls.py                 # URL routing principal
│   │   ├── wsgi.py                 # WSGI application
│   │   └── mixins.py               # Mixins reutilizables
│   │
│   ├── apps/                       # Aplicaciones Django
│   │   ├── accounts/               # Autenticación y usuarios
│   │   │   ├── models.py           # Modelo User personalizado
│   │   │   ├── views.py            # Login, logout, reset
│   │   │   ├── middleware.py       # Login required, org context
│   │   │   ├── forms.py            # Formularios de auth
│   │   │   └── templates/          # Templates de autenticación
│   │   │
│   │   ├── orgs/                   # Organizaciones y clientes
│   │   │   ├── models.py           # Organization, Client
│   │   │   ├── views.py            # CRUD organizaciones
│   │   │   ├── middleware.py       # Contexto organizacional
│   │   │   └── templates/          # UI de organizaciones
│   │   │
│   │   ├── users/                  # Gestión de usuarios
│   │   │   ├── models.py           # Extensiones de User
│   │   │   ├── views.py            # CRUD usuarios
│   │   │   ├── forms.py            # User creation/edit
│   │   │   └── templates/          # UI de usuarios
│   │   │
│   │   ├── projects/               # Proyectos, fases y tareas
│   │   │   ├── models.py           # Project, Phase, Task, PhaseTemplate
│   │   │   ├── views.py            # CRUD + Kanban + estadísticas
│   │   │   ├── services.py         # Lógica de negocio de fases
│   │   │   ├── forms.py            # Formularios y formsets
│   │   │   ├── templatetags/       # Template tags personalizados
│   │   │   └── templates/          # UI de proyectos y kanban
│   │   │
│   │   ├── files/                  # Gestión de archivos
│   │   │   ├── models.py           # ProjectFile con metadatos
│   │   │   ├── views.py            # Upload, download, delete
│   │   │   ├── admin.py            # Admin interface para archivos
│   │   │   └── migrations/         # Migraciones de metadatos
│   │   │
│   │   ├── plans/                  # Planes y suscripciones
│   │   │   ├── models.py           # Plan, Subscription, Payment
│   │   │   ├── views.py            # Dashboard de planes
│   │   │   ├── services.py         # Lógica de upgrade/billing
│   │   │   └── templates/          # UI de suscripciones
│   │   │
│   │   └── main/                   # Dashboard principal
│   │       ├── views.py            # Dashboard y métricas
│   │       └── templates/          # UI del dashboard
│   │
│   ├── static/                     # Archivos estáticos
│   │   ├── css/                    # Estilos personalizados
│   │   │   ├── base.css            # Estilos globales
│   │   │   ├── kanban.css          # Estilos del kanban
│   │   │   ├── projects.css        # Estilos de proyectos
│   │   │   └── dashboard.css       # Estilos del dashboard
│   │   ├── js/                     # JavaScript
│   │   │   ├── kanban.js           # Funcionalidad kanban
│   │   │   ├── projects.js         # Interacciones de proyectos
│   │   │   └── file-upload.js      # Subida de archivos
│   │   └── images/                 # Imágenes y assets
│   │
│   ├── templates/                  # Templates globales
│   │   ├── base.html               # Template base
│   │   ├── includes/               # Componentes reutilizables
│   │   └── partials/               # Fragmentos de UI
│   │
│   ├── logs/                       # Archivos de log
│   │   ├── debug.log               # Logs de debugging
│   │   ├── errors.log              # Logs de errores
│   │   └── security.log            # Logs de seguridad
│   │
│   └── manage.py                   # Script de gestión Django
│
├── docs/                           # Documentación
│   ├── tecnico/                    # Documentación técnica detallada
│   ├── usuario/                    # Manuales de usuario
│   └── *.md                        # Guías y referencias
│
├── docker-compose.yml              # Configuración Docker Compose
├── Dockerfile                      # Imagen Docker del proyecto
├── requirements.txt                # Dependencias Python
├── .env.example                    # Template de variables de entorno
└── README.md                       # Documentación principal
```

### Convenciones de Código

#### Naming Conventions
```python
# Models: PascalCase
class ProjectFile(models.Model):
    pass

# Views: snake_case functions, PascalCase classes
def project_kanban(request, pk):
    pass

class ProjectListView(ListView):
    pass

# URLs: kebab-case con namespace
# projects:project-detail
# users:user-list
```

#### File Organization
```python
# models.py: Un modelo por clase, relacionados juntos
# views.py: Agrupados por funcionalidad
# forms.py: Un formulario por modelo principal
# admin.py: Configuración de admin por modelo
```

---

## 🧩 Módulos y Componentes

### Módulo Accounts (Autenticación)

#### Funcionalidades Principales
```python
# apps/accounts/models.py
class User(AbstractUser):
    """Usuario personalizado con organización y roles"""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    password_change_required = models.BooleanField(default=False)
    
    @property
    def is_org_admin(self):
        return self.role == 'ORG_ADMIN'
```

#### Middleware Stack
```python
# Login requerido en toda la app
class LoginRequiredMiddleware:
    """Requiere autenticación excepto en URLs específicas"""
    
# Cambio de contraseña forzado
class PasswordChangeRequiredMiddleware:
    """Fuerza cambio de contraseña en primer login"""
    
# Contexto organizacional automático
class OrganizationContextMiddleware:
    """Agrega organización al request automáticamente"""
```

#### Seguridad Implementada
```python
# django-axes para protección de fuerza bruta
AXES_FAILURE_LIMIT = 10
AXES_COOLOFF_TIME = 0.25  # 15 minutos
AXES_LOCKOUT_BY_USER_OR_IP = True

# URLs exentas de login obligatorio
LOGIN_EXEMPT_URLS = [
    r'^accounts/login/?$',
    r'^accounts/logout/?$',
    r'^accounts/password_reset/?$',
    # ... más patrones
]
```

### Módulo Organizations (Multitenancy)

#### Modelo Organizacional
```python
class Organization(models.Model):
    """Organización principal (estudio, despacho)"""
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_subscription_limits(self):
        """Retorna límites actuales de la suscripción"""
        # Implementación de límites por plan
        pass

class Client(models.Model):
    """Cliente de la organización"""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    contact_person = models.CharField(max_length=255)
```

#### Context Middleware
```python
class OrganizationContextMiddleware:
    """Inyecta contexto organizacional en cada request"""
    
    def __call__(self, request):
        if request.user.is_authenticated:
            request.organization = request.user.organization
        response = self.get_response(request)
        return response
```

### Módulo Projects (Core Business)

#### Modelos Principales
```python
class Project(models.Model):
    """Proyecto arquitectónico"""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'created_at']),
        ]

class Phase(models.Model):
    """Fase de proyecto (Programa, Anteproyecto, etc.)"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='phases')
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, db_index=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'name']

class Task(models.Model):
    """Tarea individual dentro de una fase"""
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, db_index=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, db_index=True)
    due_date = models.DateField(null=True, blank=True, db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['phase', 'status']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['due_date']),
        ]
```

#### Services Layer
```python
# apps/projects/services.py
def create_phases_for_project(project, creation_method, **kwargs):
    """Crea fases para un proyecto según el método especificado"""
    
    if creation_method == 'template':
        template = kwargs.get('phase_template')
        phases_data = template.phases  # JSON field
        for phase_data in phases_data:
            Phase.objects.create(
                project=project,
                name=phase_data['name'],
                order=phase_data.get('order', 0)
            )
    
    elif creation_method == 'manual':
        formset = kwargs.get('phase_formset')
        for form in formset:
            if form.cleaned_data:
                Phase.objects.create(project=project, **form.cleaned_data)
    
    else:  # empty
        Phase.objects.create(
            project=project,
            name='Backlog',
            order=0
        )
```

#### Kanban Implementation
```python
# apps/projects/views.py
@login_required
def project_kanban(request, pk):
    """Vista principal del tablero Kanban"""
    project = get_object_or_404(
        Project.objects.select_related('client', 'owner'),
        pk=pk,
        organization=request.user.organization
    )
    
    # Optimización: una sola query con prefetch
    phases = project.phases.prefetch_related(
        models.Prefetch(
            'tasks',
            queryset=Task.objects.select_related('assigned_to').order_by('created_at')
        )
    ).order_by('order')
    
    # Métricas en una sola query agregada
    tasks_stats = project.phases.aggregate(
        total_tasks=models.Count('tasks'),
        todo_count=models.Count('tasks', filter=models.Q(tasks__status='TODO')),
        in_progress_count=models.Count('tasks', filter=models.Q(tasks__status='IN_PROGRESS')),
        paused_count=models.Count('tasks', filter=models.Q(tasks__status='PAUSED')),
        done_count=models.Count('tasks', filter=models.Q(tasks__status='DONE')),
    )
    
    return render(request, 'projects/project_kanban.html', {
        'project': project,
        'phases': phases,
        'tasks_stats': tasks_stats,
    })
```

### Módulo Files (Gestión de Archivos)

#### Modelo con Metadatos
```python
class ProjectFile(models.Model):
    """Archivo asociado a una fase de proyecto"""
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='project_files/%Y/%m/')
    original_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Metadatos para performance y búsqueda
    size_bytes = models.BigIntegerField(null=True, blank=True)
    ext_upper = models.CharField(max_length=10, blank=True, db_index=True)
    content_type = models.CharField(max_length=100, blank=True)
    checksum_sha256 = models.CharField(max_length=64, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['phase', 'uploaded_at']),
            models.Index(fields=['uploaded_by', 'uploaded_at']),
            models.Index(fields=['ext_upper']),
            models.Index(fields=['size_bytes']),
        ]
```

#### Upload Optimization
```python
# apps/files/views.py
@login_required
def upload_file(request):
    """Subida optimizada de archivos con validaciones"""
    
    if request.method == 'POST':
        file = request.FILES.get('file')
        phase_id = request.POST.get('phase')
        
        # Validaciones del lado servidor
        if file.size > settings.MAX_FILE_SIZE_BYTES:
            return JsonResponse({
                'success': False, 
                'error': f'Archivo muy grande. Máximo: {settings.MAX_FILE_SIZE_MB}MB'
            })
        
        # Verificar extensión
        ext = file.name.split('.')[-1].upper()
        if ext not in settings.ALLOWED_EXTENSIONS:
            return JsonResponse({
                'success': False,
                'error': f'Tipo de archivo no permitido: {ext}'
            })
        
        # Crear registro con metadatos
        project_file = ProjectFile.objects.create(
            phase_id=phase_id,
            file=file,
            original_name=file.name,
            uploaded_by=request.user,
            size_bytes=file.size,
            ext_upper=ext,
            content_type=file.content_type,
        )
        
        # Calcular checksum de forma asíncrona (opcional)
        if file.size <= settings.MAX_CHECKSUM_BYTES:
            project_file.checksum_sha256 = calculate_file_checksum(file)
            project_file.save()
        
        return JsonResponse({'success': True, 'file_id': project_file.id})
```

#### Storage Configuration
```python
# settings.py - Configuración S3/R2
if os.environ.get('ENABLE_STORAGES', 'false').lower() == 'true':
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_S3_ENDPOINT_URL = os.environ.get('AWS_S3_ENDPOINT_URL')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_S3_REGION_NAME = 'auto'
    AWS_S3_ADDRESSING_STYLE = 'virtual'
    AWS_S3_SIGNATURE_VERSION = 's3v4'
    AWS_DEFAULT_ACL = None
```

---

## 🗄️ Base de Datos

### Esquema ER Simplificado

```mermaid
erDiagram
    Organization ||--o{ User : contains
    Organization ||--o{ Client : has
    Organization ||--o{ Project : owns
    Organization ||--o{ Plan : subscribes
    
    User ||--o{ Project : owns
    User ||--o{ Task : assigned_to
    User ||--o{ ProjectFile : uploads
    
    Client ||--o{ Project : client_of
    
    Project ||--o{ Phase : contains
    Phase ||--o{ Task : contains
    Phase ||--o{ ProjectFile : stores
    
    Plan ||--o{ Subscription : has
    Subscription ||--o{ Payment : generates
    
    Organization {
        id PK
        name VARCHAR
        description TEXT
        is_active BOOLEAN
        created_at TIMESTAMP
    }
    
    User {
        id PK
        username VARCHAR
        email VARCHAR
        organization_id FK
        role VARCHAR
        password_change_required BOOLEAN
    }
    
    Project {
        id PK
        organization_id FK
        name VARCHAR
        description TEXT
        client_id FK
        owner_id FK
        status VARCHAR
        created_at TIMESTAMP
    }
    
    Phase {
        id PK
        project_id FK
        name VARCHAR
        status VARCHAR
        order INTEGER
    }
    
    Task {
        id PK
        phase_id FK
        title VARCHAR
        description TEXT
        assigned_to_id FK
        status VARCHAR
        priority VARCHAR
        due_date DATE
    }
    
    ProjectFile {
        id PK
        phase_id FK
        file FILEPATH
        original_name VARCHAR
        uploaded_by_id FK
        size_bytes BIGINT
        ext_upper VARCHAR
        content_type VARCHAR
        checksum_sha256 VARCHAR
    }
```

### Índices Estratégicos

#### Performance Indexes
```sql
-- Índices para queries frecuentes
CREATE INDEX idx_project_org_status ON projects_project(organization_id, status);
CREATE INDEX idx_task_phase_status ON projects_task(phase_id, status);
CREATE INDEX idx_task_assigned_status ON projects_task(assigned_to_id, status);
CREATE INDEX idx_file_phase_date ON files_projectfile(phase_id, uploaded_at);

-- Índices compuestos para queries de métricas
CREATE INDEX idx_task_metrics ON projects_task(phase_id, status, created_at);
CREATE INDEX idx_file_search ON files_projectfile(ext_upper, size_bytes);
```

#### Constraints y Foreign Keys
```sql
-- Integridad referencial con cascade apropiado
ALTER TABLE projects_project 
ADD CONSTRAINT fk_project_organization 
FOREIGN KEY (organization_id) REFERENCES orgs_organization(id) ON DELETE CASCADE;

ALTER TABLE projects_task 
ADD CONSTRAINT fk_task_assigned_to 
FOREIGN KEY (assigned_to_id) REFERENCES accounts_user(id) ON DELETE SET NULL;

-- Check constraints para validación de datos
ALTER TABLE projects_task 
ADD CONSTRAINT chk_task_status 
CHECK (status IN ('TODO', 'IN_PROGRESS', 'PAUSED', 'DONE'));
```

### Queries Optimizadas

#### Kanban Data Fetching
```python
# Single query con prefetch para evitar N+1
def get_kanban_data(project_id, user_org):
    return Project.objects.select_related(
        'client', 'owner'
    ).prefetch_related(
        models.Prefetch(
            'phases',
            queryset=Phase.objects.prefetch_related(
                models.Prefetch(
                    'tasks',
                    queryset=Task.objects.select_related('assigned_to')
                )
            ).order_by('order')
        )
    ).get(id=project_id, organization=user_org)
```

#### Aggregated Metrics
```python
# Métricas en una sola query agregada
def get_project_metrics(project_id):
    return Task.objects.filter(
        phase__project_id=project_id
    ).aggregate(
        total=Count('id'),
        todo=Count('id', filter=Q(status='TODO')),
        in_progress=Count('id', filter=Q(status='IN_PROGRESS')),
        paused=Count('id', filter=Q(status='PAUSED')),
        done=Count('id', filter=Q(status='DONE')),
        overdue=Count('id', filter=Q(due_date__lt=timezone.now().date())),
        high_priority=Count('id', filter=Q(priority='HIGH')),
    )
```

### Migrations Strategy

#### Custom Migrations
```python
# apps/files/migrations/0003_add_metadata_fields.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('files', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectfile',
            name='size_bytes',
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='projectfile',
            name='ext_upper',
            field=models.CharField(blank=True, db_index=True, max_length=10),
        ),
        # ... más campos de metadatos
        migrations.AddIndex(
            model_name='projectfile',
            index=models.Index(fields=['ext_upper'], name='files_ext_idx'),
        ),
    ]
```

---

## ⚙️ Configuración y Despliegue

### Environment Configuration

#### Development Settings
```python
# Local development (.env)
DEBUG=True
SECRET_KEY=dev-insecure-key
DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/arc_manager_dev
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
REDIS_URL=redis://localhost:6379/0
ENABLE_STORAGES=false
```

#### Production Settings
```python
# Production environment
DEBUG=False
SECRET_KEY=super-secure-50-character-random-key
DATABASE_URL=postgresql://user:pass@host:5432/production_db
ALLOWED_HOSTS=arcmanager.com,www.arcmanager.com
REDIS_URL=redis://redis-host:6379/0

# R2/S3 Storage
ENABLE_STORAGES=true
DEFAULT_FILE_STORAGE=storages.backends.s3boto3.S3Boto3Storage
AWS_S3_ENDPOINT_URL=https://account-id.r2.cloudflarestorage.com
AWS_STORAGE_BUCKET_NAME=arcmanager-files-prod
AWS_ACCESS_KEY_ID=r2-access-key
AWS_SECRET_ACCESS_KEY=r2-secret-key
```

#### Security Hardening
```python
# settings.py - Production security
if not DEBUG:
    # SSL/HTTPS
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # Cookies security
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
    # HSTS
    SECURE_HSTS_SECONDS = 31536000  # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Content security
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    X_FRAME_OPTIONS = 'DENY'
```

### Docker Configuration

#### Dockerfile
```dockerfile
FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

# Application
COPY arc_manager/ /app/arc_manager/
WORKDIR /app/arc_manager

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python manage.py check || exit 1

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "core.wsgi:application"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-arc_manager_dev}
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres123}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "${POSTGRES_PORT:-5432}:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "${REDIS_PORT:-6379}:6379"

  web:
    build: .
    command: >
      sh -c "
        python manage.py migrate --noinput &&
        python manage.py collectstatic --noinput &&
        gunicorn --bind 0.0.0.0:8000 core.wsgi:application
      "
    volumes:
      - static_volume:/app/arc_manager/staticfiles
      - media_volume:/app/arc_manager/media
    ports:
      - "${WEB_PORT:-8000}:8000"
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=${DATABASE_URL:-postgresql://postgres:postgres123@db:5432/arc_manager_dev}
      - REDIS_URL=${REDIS_URL:-redis://redis:6379/0}

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

### Deployment Strategies

#### Railway.app (Recommended for MVP)
```bash
# 1. Connect GitHub repository
# 2. Configure environment variables in Railway dashboard
# 3. Auto-deploy on git push

# Environment variables to set:
DEBUG=False
SECRET_KEY=generated-secure-key
DATABASE_URL=postgresql://... # Auto-provided by Railway
ALLOWED_HOSTS=*.railway.app,yourdomain.com
ENABLE_STORAGES=true
# ... R2 configuration
```

#### Railway Deployment
```bash
# Deployment automático desde GitHub
# 1. Conecta repositorio en railway.app
# 2. Configura variables de entorno
# 3. Deploy automático en cada push

# Variables de entorno necesarias:
DEBUG=False
SECRET_KEY=generated-key
DATABASE_URL=postgresql://... # Auto-generada
ENABLE_STORAGES=true
AWS_S3_ENDPOINT_URL=https://account.r2.cloudflarestorage.com
```

### Estructura de Costos Optimizada

#### Railway + Cloudflare R2
```bash
# Costos mensuales estimados:
# MVP (0-10 clientes): $80-180 MXN
# Crecimiento (10-50 clientes): $800-1,000 MXN
# Escalamiento (50+ clientes): $1,300-2,100 MXN
```

---

## 🔒 Seguridad

### Authentication & Authorization

#### Custom User Model
```python
class User(AbstractUser):
    """Extended user with organization and role-based access"""
    
    ROLE_CHOICES = [
        ('ORG_ADMIN', 'Administrador de Organización'),
        ('PROJECT_ADMIN', 'Administrador de Proyecto'),
        ('COLLABORATOR', 'Colaborador'),
        ('VIEWER', 'Visualizador'),
    ]
    
    organization = models.ForeignKey('orgs.Organization', on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='COLLABORATOR')
    password_change_required = models.BooleanField(default=False)
    
    def has_project_access(self, project):
        """Check if user can access specific project"""
        return (
            project.organization == self.organization and
            (self.is_org_admin or 
             project.owner == self or 
             project.collaborators.filter(id=self.id).exists())
        )
```

#### Permission Mixins
```python
class OrganizationRequiredMixin:
    """Ensure user belongs to an organization"""
    
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'organization'):
            return redirect('accounts:setup-organization')
        return super().dispatch(request, *args, **kwargs)

class ProjectAccessMixin:
    """Ensure user has access to the project"""
    
    def get_object(self):
        obj = super().get_object()
        if not self.request.user.has_project_access(obj):
            raise PermissionDenied
        return obj
```

### Brute Force Protection

#### Django Axes Configuration
```python
# settings.py
AXES_ENABLED = True
AXES_FAILURE_LIMIT = 10
AXES_COOLOFF_TIME = 0.25  # 15 minutes
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_BY_USER_OR_IP = True
AXES_LOCKOUT_URL = '/accounts/login/?locked=1'

# Custom lockout handling
AXES_LOCKOUT_CALLABLE = 'apps.accounts.utils.lockout_response'
```

### Input Validation & Sanitization

#### Form Validation
```python
class ProjectForm(forms.ModelForm):
    """Secure project creation form"""
    
    class Meta:
        model = Project
        fields = ['name', 'description', 'client']
    
    def clean_name(self):
        """Validate and sanitize project name"""
        name = self.cleaned_data['name']
        
        # Length validation
        if len(name) < 3:
            raise ValidationError('El nombre debe tener al menos 3 caracteres')
        
        # Character validation
        if not re.match(r'^[\w\s\-\.]+$', name):
            raise ValidationError('El nombre contiene caracteres no válidos')
        
        # Duplicate validation within organization
        if Project.objects.filter(
            organization=self.organization,
            name__iexact=name
        ).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Ya existe un proyecto con este nombre')
        
        return name.strip()
```

#### File Upload Security
```python
def validate_file_upload(file):
    """Comprehensive file validation"""
    
    # Size validation
    if file.size > settings.MAX_FILE_SIZE_BYTES:
        raise ValidationError(f'Archivo muy grande: {file.size} bytes')
    
    # Extension validation
    ext = file.name.split('.')[-1].upper()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise ValidationError(f'Extensión no permitida: {ext}')
    
    # MIME type validation
    if file.content_type not in settings.ALLOWED_MIME_TYPES:
        raise ValidationError(f'Tipo MIME no permitido: {file.content_type}')
    
    # File content validation (basic magic number check)
    file.seek(0)
    header = file.read(512)
    if not is_valid_file_header(header, ext):
        raise ValidationError('El contenido del archivo no coincide con su extensión')
    
    file.seek(0)  # Reset for normal processing
    return True
```

### Data Protection

#### Query Filtering by Organization
```python
class OrganizationQuerySetMixin:
    """Automatically filter by organization"""
    
    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.request.user, 'organization'):
            return qs.filter(organization=self.request.user.organization)
        return qs.none()

class ProjectListView(OrganizationQuerySetMixin, ListView):
    """Projects automatically filtered by user's organization"""
    model = Project
```

#### Sensitive Data Handling
```python
# Password handling
class User(AbstractUser):
    def set_temporary_password(self):
        """Generate secure temporary password"""
        temp_password = get_random_string(12)
        self.set_password(temp_password)
        self.password_change_required = True
        # NEVER log the actual password
        logger.info(f'Temporary password set for user {self.username}')
        return temp_password

# API key handling
def generate_api_key():
    """Generate cryptographically secure API key"""
    return get_random_string(40, allowed_chars='abcdefghijklmnopqrstuvwxyz0123456789')
```

---

## ⚡ Performance y Optimización

### Database Optimization

#### Query Optimization Patterns (✅ EXCELENTE)
```python
# 🏆 PATRONES PROFESIONALES IDENTIFICADOS:

# 1. Select Related CORRECTAMENTE USADO
projects = Project.objects.select_related(
    'organization', 'client', 'owner'  # ✅ Evita N+1 queries
).filter(organization=user.organization)

# 2. Prefetch Related OPTIMIZADO
projects = Project.objects.prefetch_related(
    'phases__tasks__assigned_to'  # ✅ Carga eficiente de relaciones
).filter(organization=user.organization)

# 3. Prefetch with custom QuerySet - 🏆 AVANZADO
projects = Project.objects.prefetch_related(
    Prefetch(
        'phases',
        queryset=Phase.objects.select_related('project').order_by('order')
    )  # ✅ Control total sobre las queries relacionadas
)

# 4. Aggregation PROFESIONAL para métricas
task_stats = Task.objects.filter(
    phase__project=project
).aggregate(
    total=Count('id'),
    completed=Count('id', filter=Q(status='DONE')),
    in_progress=Count('id', filter=Q(status='IN_PROGRESS')),
    # 🏆 Cálculos complejos en BD (no en Python)
    avg_completion_days=Avg(
        Extract(models.F('updated_at') - models.F('created_at'), 'day'),
        filter=Q(status='DONE')
    )
)

# 📊 RESULTADO: Queries optimizadas, latencia mínima
```

#### Connection Pooling
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DATABASE_NAME'),
        'CONN_MAX_AGE': int(os.environ.get('CONN_MAX_AGE', '120')),
        'OPTIONS': {
            'MAX_CONNS': 20,
            'MIN_CONNS': 5,
        }
    }
}
```

### Caching Strategy

#### Redis Configuration
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        },
        'KEY_PREFIX': 'arc_manager',
        'TIMEOUT': 300,
    },
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'arc_sessions',
        'TIMEOUT': 86400,  # 24 hours
    }
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'
SESSION_SAVE_EVERY_REQUEST = False  # Performance improvement
```

#### Cache Usage Patterns
```python
# View-level caching
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # 15 minutes
def project_statistics(request, project_id):
    """Cached project statistics"""
    pass

# Template fragment caching
{% load cache %}
{% cache 300 project_metrics project.id %}
    <!-- Expensive metrics calculation -->
{% endcache %}

# Low-level cache API
from django.core.cache import cache

def get_organization_stats(org_id):
    cache_key = f'org_stats_{org_id}'
    stats = cache.get(cache_key)
    
    if stats is None:
        stats = calculate_expensive_stats(org_id)
        cache.set(cache_key, stats, 600)  # 10 minutes
    
    return stats
```

### Frontend Optimization

#### Static Files Optimization
```python
# settings.py
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Compression and caching
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = DEBUG

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
```

#### JavaScript Performance
```javascript
// Lazy loading for large components
document.addEventListener('DOMContentLoaded', function() {
    // Only load Kanban on Kanban pages
    if (document.querySelector('.kanban-board')) {
        import('./modules/kanban.js').then(module => {
            new module.KanbanManager();
        });
    }
});

// Debounced search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

const debouncedSearch = debounce(performSearch, 300);
```

### Performance Monitoring

#### Custom Middleware
```python
class PerformanceMiddleware:
    """Monitor request performance"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        duration = time.time() - start_time
        
        # Log slow requests
        if duration > 2.0:  # 2 seconds threshold
            logger.warning(
                f'Slow request: {request.path} took {duration:.2f}s',
                extra={
                    'duration': duration,
                    'path': request.path,
                    'method': request.method,
                    'user': getattr(request, 'user', None),
                }
            )
        
        # Add performance header
        response['X-Response-Time'] = f'{duration:.3f}s'
        
        return response
```

---

## 🔗 APIs y Endpoints

### RESTful Endpoints

#### Project Management API
```python
# apps/projects/urls.py
urlpatterns = [
    # Project CRUD
    path('', ProjectListView.as_view(), name='project-list'),
    path('<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    path('new/', ProjectCreateView.as_view(), name='project-create'),
    path('<int:pk>/edit/', ProjectUpdateView.as_view(), name='project-update'),
    path('<int:pk>/delete/', ProjectDeleteView.as_view(), name='project-delete'),
    
    # Kanban and Task Management
    path('<int:pk>/tasks/', project_kanban, name='project-kanban'),
    path('<int:pk>/statistics/', project_statistics, name='project-statistics'),
    
    # AJAX endpoints
    path('tasks/<int:task_pk>/update_status/', update_task_status, name='update-task-status'),
    path('tasks/<int:task_pk>/move/', move_task, name='task-move'),
    path('tasks/<int:pk>/edit/', task_edit, name='task-edit'),
    
    # Phase management
    path('<int:project_pk>/phases/create/', phase_create, name='phase-create'),
    path('<int:project_id>/phases/<int:phase_id>/files/', phase_files_paginated, name='phase-files-paginated'),
]
```

#### AJAX Response Format
```python
# Standardized JSON responses
def update_task_status(request, task_pk):
    """Update task status via AJAX"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    try:
        task = get_object_or_404(
            Task.objects.select_related('phase__project'),
            pk=task_pk,
            phase__project__organization=request.user.organization
        )
        
        new_status = request.POST.get('status')
        if new_status not in ['TODO', 'IN_PROGRESS', 'PAUSED', 'DONE']:
            return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
        
        task.status = new_status
        task.save()
        
        return JsonResponse({
            'success': True,
            'task': {
                'id': task.id,
                'title': task.title,
                'status': task.status,
                'updated_at': task.updated_at.isoformat(),
            }
        })
        
    except Exception as e:
        logger.error(f'Error updating task status: {e}', exc_info=True)
        return JsonResponse({'success': False, 'error': 'Internal server error'}, status=500)
```

### File Management API

#### Upload Endpoints
```python
# apps/files/urls.py
urlpatterns = [
    path('upload/', upload_file, name='upload_file'),
    path('presign_upload/', presign_upload, name='presign_upload'),
    path('confirm_upload/', confirm_upload, name='confirm_upload'),
    path('<int:file_id>/delete/', delete_file, name='delete_file'),
]

# Direct upload implementation
@login_required
@require_http_methods(['POST'])
def upload_file(request):
    """Direct file upload to storage backend"""
    
    file = request.FILES.get('file')
    phase_id = request.POST.get('phase')
    description = request.POST.get('description', '')
    
    # Validation
    try:
        validate_file_upload(file)
        phase = get_object_or_404(
            Phase.objects.select_related('project'),
            pk=phase_id,
            project__organization=request.user.organization
        )
    except ValidationError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    # Create file record
    project_file = ProjectFile.objects.create(
        phase=phase,
        file=file,
        original_name=file.name,
        description=description,
        uploaded_by=request.user,
        size_bytes=file.size,
        ext_upper=file.name.split('.')[-1].upper(),
        content_type=file.content_type,
    )
    
    # Calculate checksum for smaller files
    if file.size <= settings.MAX_CHECKSUM_BYTES:
        project_file.checksum_sha256 = calculate_file_checksum(file)
        project_file.save()
    
    return JsonResponse({
        'success': True,
        'file': {
            'id': project_file.id,
            'name': project_file.original_name,
            'size': project_file.size_bytes,
            'url': project_file.file.url,
            'uploaded_at': project_file.uploaded_at.isoformat(),
        }
    })
```

#### Presigned URLs (for large files)
```python
@login_required
@require_http_methods(['POST'])
def presign_upload(request):
    """Generate presigned URL for direct upload to R2/S3"""
    
    if not settings.ENABLE_STORAGES:
        return JsonResponse({'success': False, 'error': 'Direct upload not enabled'}, status=400)
    
    filename = request.POST.get('filename')
    content_type = request.POST.get('content_type')
    phase_id = request.POST.get('phase_id')
    
    # Validation
    phase = get_object_or_404(
        Phase,
        pk=phase_id,
        project__organization=request.user.organization
    )
    
    # Generate unique key
    file_key = f'project_files/{timezone.now().year}/{timezone.now().month}/{uuid.uuid4()}/{filename}'
    
    # Generate presigned POST
    s3_client = boto3.client(
        's3',
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )
    
    presigned_post = s3_client.generate_presigned_post(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=file_key,
        Fields={'Content-Type': content_type},
        Conditions=[
            {'Content-Type': content_type},
            ['content-length-range', 1, settings.MAX_FILE_SIZE_BYTES],
        ],
        ExpiresIn=3600  # 1 hour
    )
    
    # Store pending upload
    PendingUpload.objects.create(
        user=request.user,
        phase=phase,
        file_key=file_key,
        original_name=filename,
        content_type=content_type,
        expires_at=timezone.now() + timedelta(hours=1)
    )
    
    return JsonResponse({
        'success': True,
        'upload_url': presigned_post['url'],
        'fields': presigned_post['fields'],
        'file_key': file_key,
    })
```

### Health Check & Monitoring

#### Health Check Endpoint
```python
# apps/main/views.py
def health_check(request):
    """System health check endpoint"""
    
    checks = {
        'database': False,
        'redis': False,
        'storage': False,
        'timestamp': timezone.now().isoformat(),
    }
    
    # Database check
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks['database'] = True
    except Exception:
        pass
    
    # Redis check
    try:
        from django.core.cache import cache
        cache.set('health_check', 'ok', 10)
        checks['redis'] = cache.get('health_check') == 'ok'
    except Exception:
        pass
    
    # Storage check
    try:
        from django.core.files.storage import default_storage
        checks['storage'] = default_storage.exists('.')
    except Exception:
        pass
    
    all_healthy = all(checks[k] for k in ['database', 'redis', 'storage'])
    status_code = 200 if all_healthy else 503
    
    return JsonResponse({
        'status': 'healthy' if all_healthy else 'unhealthy',
        'checks': checks,
        'version': '1.0.0',
    }, status=status_code)
```

---

## 🧪 Testing y Calidad

### Testing Strategy

#### Unit Tests
```python
# apps/projects/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.orgs.models import Organization
from apps.projects.models import Project, Phase, Task

User = get_user_model()

class ProjectModelTest(TestCase):
    """Test Project model functionality"""
    
    def setUp(self):
        self.organization = Organization.objects.create(
            name='Test Studio',
            description='Test architecture studio'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            organization=self.organization
        )
    
    def test_project_creation(self):
        """Test basic project creation"""
        project = Project.objects.create(
            organization=self.organization,
            name='Test Project',
            description='Test project description',
            owner=self.user,
            status='ACTIVE'
        )
        
        self.assertEqual(project.name, 'Test Project')
        self.assertEqual(project.organization, self.organization)
        self.assertEqual(project.owner, self.user)
        self.assertEqual(project.status, 'ACTIVE')
    
    def test_project_str_representation(self):
        """Test project string representation"""
        project = Project.objects.create(
            organization=self.organization,
            name='Test Project',
            owner=self.user
        )
        
        self.assertEqual(str(project), 'Test Project')
    
    def test_phase_creation_with_project(self):
        """Test phase creation within project"""
        project = Project.objects.create(
            organization=self.organization,
            name='Test Project',
            owner=self.user
        )
        
        phase = Phase.objects.create(
            project=project,
            name='Test Phase',
            status='PENDING'
        )
        
        self.assertEqual(phase.project, project)
        self.assertEqual(phase.name, 'Test Phase')
        self.assertIn(phase, project.phases.all())
```

#### Integration Tests
```python
class ProjectIntegrationTest(TestCase):
    """Test project workflows end-to-end"""
    
    def setUp(self):
        self.organization = Organization.objects.create(name='Test Studio')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            organization=self.organization,
            role='ORG_ADMIN'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_complete_project_workflow(self):
        """Test complete project creation workflow"""
        
        # 1. Create project
        response = self.client.post('/projects/new/', {
            'name': 'Integration Test Project',
            'description': 'Full workflow test',
            'creation_method': 'empty',
        })
        
        self.assertEqual(response.status_code, 302)
        project = Project.objects.get(name='Integration Test Project')
        
        # 2. Verify default phase creation
        self.assertTrue(project.phases.filter(name='Backlog').exists())
        backlog_phase = project.phases.get(name='Backlog')
        
        # 3. Create task
        response = self.client.post(f'/projects/{project.id}/tasks/create/', {
            'title': 'Test Task',
            'description': 'Integration test task',
            'phase': backlog_phase.id,
            'priority': 'HIGH',
        })
        
        self.assertEqual(response.status_code, 302)
        task = Task.objects.get(title='Test Task')
        
        # 4. Update task status
        response = self.client.post(f'/projects/tasks/{task.id}/update_status/', {
            'status': 'IN_PROGRESS'
        })
        
        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.status, 'IN_PROGRESS')
        
        # 5. Verify kanban view
        response = self.client.get(f'/projects/{project.id}/tasks/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Task')
        self.assertContains(response, 'IN_PROGRESS')
```

#### API Tests
```python
class APITestCase(TestCase):
    """Test AJAX/API endpoints"""
    
    def setUp(self):
        self.organization = Organization.objects.create(name='Test Studio')
        self.user = User.objects.create_user(
            username='apiuser',
            email='api@example.com',
            password='apipass123',
            organization=self.organization
        )
        
        self.project = Project.objects.create(
            organization=self.organization,
            name='API Test Project',
            owner=self.user
        )
        
        self.phase = Phase.objects.create(
            project=self.project,
            name='API Test Phase'
        )
        
        self.task = Task.objects.create(
            phase=self.phase,
            title='API Test Task',
            status='TODO'
        )
    
    def test_task_status_update_api(self):
        """Test task status update via AJAX"""
        self.client.login(username='apiuser', password='apipass123')
        
        response = self.client.post(
            f'/projects/tasks/{self.task.id}/update_status/',
            {'status': 'IN_PROGRESS'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(data['task']['status'], 'IN_PROGRESS')
        
        # Verify database update
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'IN_PROGRESS')
    
    def test_invalid_status_update(self):
        """Test invalid status update handling"""
        self.client.login(username='apiuser', password='apipass123')
        
        response = self.client.post(
            f'/projects/tasks/{self.task.id}/update_status/',
            {'status': 'INVALID_STATUS'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        
        # Verify no database change
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'TODO')
```

### Code Quality Tools

#### Testing Configuration
```python
# settings/test.py
from .base import *

# Use in-memory SQLite for faster tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Test-specific settings
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',  # Faster for tests
]

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
CELERY_TASK_ALWAYS_EAGER = True
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
```

#### Coverage Configuration
```ini
# .coveragerc
[run]
source = arc_manager
omit = 
    */migrations/*
    */tests/*
    */venv/*
    */settings/*
    manage.py
    */wsgi.py
    */asgi.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
```

### Performance Testing

#### Load Testing with Locust
```python
# locustfile.py
from locust import HttpUser, task, between

class ArcManagerUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login before starting tests"""
        self.client.post('/accounts/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
    
    @task(3)
    def view_dashboard(self):
        """Test dashboard performance"""
        self.client.get('/main/')
    
    @task(2)
    def view_projects(self):
        """Test project list performance"""
        self.client.get('/projects/')
    
    @task(1)
    def view_kanban(self):
        """Test kanban performance"""
        response = self.client.get('/projects/')
        # Extract project ID from response and test kanban
        # Implementation depends on actual response structure
        self.client.get('/projects/1/tasks/')
    
    @task(1)
    def update_task_status(self):
        """Test AJAX task updates"""
        self.client.post('/projects/tasks/1/update_status/', {
            'status': 'IN_PROGRESS'
        })
```

---

## 📊 Monitoreo y Logging

### Logging Configuration

#### Structured Logging Setup
```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} [{process:d}:{thread:d}] {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'json': {
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file_debug': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'debug.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'file_error': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'errors.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
            'level': 'ERROR',
        },
        'security': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 10,
            'formatter': 'json',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file_debug'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.security': {
            'handlers': ['security'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file_debug'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': True,
        },
        'arc_manager': {
            'handlers': ['console', 'file_debug', 'file_error'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': True,
        },
    },
}
```

#### Custom Logging Usage
```python
# apps/projects/views.py
import logging

logger = logging.getLogger(__name__)

@login_required
def project_kanban(request, pk):
    """Kanban view with comprehensive logging"""
    
    # Log access attempt
    logger.info(
        'Kanban access attempt',
        extra={
            'user_id': request.user.id,
            'username': request.user.username,
            'project_id': pk,
            'organization_id': request.user.organization.id,
            'ip_address': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT'),
        }
    )
    
    try:
        project = get_object_or_404(
            Project.objects.select_related('client', 'owner'),
            pk=pk,
            organization=request.user.organization
        )
        
        # Log successful access
        logger.info(
            'Kanban accessed successfully',
            extra={
                'user_id': request.user.id,
                'project_id': project.id,
                'project_name': project.name,
            }
        )
        
        # ... view logic
        
    except Project.DoesNotExist:
        # Log security event
        logger.warning(
            'Unauthorized kanban access attempt',
            extra={
                'user_id': request.user.id,
                'requested_project_id': pk,
                'user_organization_id': request.user.organization.id,
                'ip_address': request.META.get('REMOTE_ADDR'),
            }
        )
        raise Http404
    
    except Exception as e:
        # Log error with context
        logger.error(
            'Kanban view error',
            extra={
                'user_id': request.user.id,
                'project_id': pk,
                'error': str(e),
                'traceback': traceback.format_exc(),
            }
        )
        raise
```

### Performance Monitoring

#### Custom Metrics Collection
```python
# apps/core/monitoring.py
import time
from django.core.cache import cache
from django.db import connection

class MetricsCollector:
    """Collect and store application metrics"""
    
    @staticmethod
    def record_request_time(view_name, duration):
        """Record request duration for performance analysis"""
        cache_key = f'metrics:request_time:{view_name}'
        
        # Get existing data or initialize
        data = cache.get(cache_key, {'count': 0, 'total': 0, 'max': 0})
        
        data['count'] += 1
        data['total'] += duration
        data['max'] = max(data['max'], duration)
        data['avg'] = data['total'] / data['count']
        
        cache.set(cache_key, data, 3600)  # 1 hour
    
    @staticmethod
    def record_db_queries(view_name, query_count):
        """Record database query count per view"""
        cache_key = f'metrics:db_queries:{view_name}'
        
        data = cache.get(cache_key, {'count': 0, 'total_queries': 0})
        data['count'] += 1
        data['total_queries'] += query_count
        data['avg_queries'] = data['total_queries'] / data['count']
        
        cache.set(cache_key, data, 3600)
    
    @staticmethod
    def get_performance_report():
        """Generate performance report"""
        return {
            'request_times': cache.get_many(cache.keys('metrics:request_time:*')),
            'db_queries': cache.get_many(cache.keys('metrics:db_queries:*')),
            'timestamp': time.time(),
        }

# Decorator for automatic metrics collection
def monitor_performance(view_func):
    """Decorator to automatically monitor view performance"""
    
    def wrapper(request, *args, **kwargs):
        start_time = time.time()
        initial_queries = len(connection.queries)
        
        try:
            response = view_func(request, *args, **kwargs)
            
            # Record metrics
            duration = time.time() - start_time
            query_count = len(connection.queries) - initial_queries
            
            view_name = f"{view_func.__module__}.{view_func.__name__}"
            MetricsCollector.record_request_time(view_name, duration)
            MetricsCollector.record_db_queries(view_name, query_count)
            
            return response
            
        except Exception as e:
            # Record error metrics
            logger.error(f'View error in {view_func.__name__}: {e}')
            raise
    
    return wrapper
```

### Error Tracking

#### Sentry Integration (Optional)
```python
# settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

if not DEBUG and os.environ.get('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.environ.get('SENTRY_DSN'),
        integrations=[
            DjangoIntegration(
                transaction_style='url',
                middleware_spans=True,
                signals_spans=True,
            ),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment=os.environ.get('ENVIRONMENT', 'production'),
    )
```

#### Custom Error Handling
```python
# apps/core/error_handlers.py
from django.http import JsonResponse
from django.shortcuts import render
import logging

logger = logging.getLogger(__name__)

def handle_ajax_error(request, exception):
    """Handle AJAX request errors consistently"""
    
    logger.error(
        'AJAX error occurred',
        extra={
            'user_id': getattr(request.user, 'id', None),
            'path': request.path,
            'method': request.method,
            'error': str(exception),
        }
    )
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False,
            'error': 'Se produjo un error inesperado. Por favor, intenta de nuevo.',
        }, status=500)
    
    return render(request, '500.html', status=500)

def custom_404_view(request, exception):
    """Custom 404 handler with logging"""
    
    logger.warning(
        '404 error',
        extra={
            'path': request.path,
            'method': request.method,
            'user_id': getattr(request.user, 'id', None),
            'referer': request.META.get('HTTP_REFERER'),
        }
    )
    
    return render(request, '404.html', status=404)
```

---

## 📋 Lo que Falta para Desplegar el MVP

### ✅ Estado Actual (Completado)

**✅ Funcionalidades Core Implementadas:**
- Sistema de autenticación completo con roles
- Gestión multiorganización funcionando
- CRUD completo de proyectos, fases y tareas
- Tablero Kanban con drag & drop
- Sistema de archivos con metadatos
- Panel de administración operativo
- Seguridad endurecida para producción
- Performance optimizada con agregaciones
- Docker containerizado

**✅ Configuración Técnica Lista:**
- Variables de entorno configuradas
- Migraciones aplicadas
- Base de datos PostgreSQL funcionando
- Redis configurado para cache y sesiones
- Almacenamiento externo preparado (R2/S3)
- Scripts de despliegue listos

### 🔶 Tareas Críticas Restantes (1-2 días)

#### 1. **Configurar Cloudflare R2 (CRÍTICO)**
```bash
# Pasos obligatorios:
1. Crear cuenta en Cloudflare R2
2. Crear bucket: arcmanager-files-prod
3. Generar API tokens con permisos Object Read/Write/Delete
4. Configurar variables de entorno en producción:
   - ENABLE_STORAGES=true
   - AWS_S3_ENDPOINT_URL=https://account-id.r2.cloudflarestorage.com
   - AWS_STORAGE_BUCKET_NAME=arcmanager-files-prod
   - AWS_ACCESS_KEY_ID=tu-r2-key
   - AWS_SECRET_ACCESS_KEY=tu-r2-secret

# Sin esto, los archivos grandes NO funcionarán en producción
```

#### 2. **Variables de Entorno de Producción**
```env
# Variables obligatorias para producción:
DEBUG=False
SECRET_KEY=clave-super-segura-de-50-caracteres-generada
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com,*.railway.app
DATABASE_URL=postgresql://usuario:password@host:5432/database
PRODUCTION=true

# Variables críticas de R2:
ENABLE_STORAGES=true
AWS_S3_ENDPOINT_URL=https://account-id.r2.cloudflarestorage.com
AWS_STORAGE_BUCKET_NAME=bucket-name
AWS_ACCESS_KEY_ID=r2-access-key
AWS_SECRET_ACCESS_KEY=r2-secret-key

# Variables opcionales pero recomendadas:
CONN_MAX_AGE=120
MAX_FILE_SIZE_MB=600
ALLOWED_EXTENSIONS=PDF,JPG,JPEG,PNG,GIF,DWG,DXF,RVT,SKP,ZIP,RAR,TIFF
```

#### 3. **Despliegue en Plataforma**
```bash
# Opción A: Railway (Recomendado)
1. Conectar repositorio GitHub a Railway
2. Configurar variables de entorno en dashboard
3. Deploy automático

# Opción B: Heroku
heroku create tu-app-arcmanager
heroku config:set DEBUG=False
heroku config:set SECRET_KEY=tu-clave-super-segura
# ... más variables
git push heroku main

# Opción C: VPS con Docker
docker compose -f docker-compose.prod.yml up -d --build
```

### 🔧 Tareas Opcionales (Mejoras Post-MVP)

#### 1. **Email Configurado (No crítico)**
```env
# Para notificaciones por email (opcional):
AWS_ACCESS_KEY_ID=ses-key
AWS_SECRET_ACCESS_KEY=ses-secret
AWS_SES_REGION=us-east-1
DEFAULT_FROM_EMAIL=noreply@tu-dominio.com
```

#### 2. **Dominio Personalizado**
```bash
# Configurar DNS para apuntar a tu plataforma
# Ejemplo para Railway:
CNAME: www.tu-dominio.com -> tu-app.railway.app
```

#### 3. **Monitoreo Avanzado**
```env
# Sentry para tracking de errores (opcional):
SENTRY_DSN=https://tu-sentry-dsn@sentry.io/proyecto
```

### 📋 Checklist Final de Despliegue

#### Pre-Deploy ✅
- [x] Código en GitHub/repositorio
- [x] Variables de entorno documentadas
- [x] Docker configurado y funcionando
- [x] Migraciones aplicadas en local
- [x] Tests básicos pasando

#### Deploy Crítico 🚨
- [ ] **Configurar Cloudflare R2**
- [ ] **Generar SECRET_KEY segura**
- [ ] **Configurar variables de entorno en plataforma**
- [ ] **Aplicar migraciones en producción**
- [ ] **Verificar subida de archivos**

#### Post-Deploy ✅
- [ ] Crear primer usuario admin
- [ ] Smoke test completo
- [ ] Verificar que archivos se suben a R2
- [ ] Confirmar que URLs de descarga funcionan
- [ ] Test de rendimiento básico

### 🚀 Estimación de Tiempo

**Para tener MVP funcionando en producción:**
- ⏱️ **2-4 horas**: Configurar R2 y variables de entorno
- ⏱️ **1-2 horas**: Deploy y configuración inicial
- ⏱️ **1 hora**: Testing y verificación
- ⏱️ **Total: 4-7 horas de trabajo efectivo**

### 💰 Costos Estimados

**Mensual para MVP:**
- **Railway**: $5-10/mes (incluye PostgreSQL)
- **Cloudflare R2**: ~$1/mes (10GB almacenamiento)
- **Dominio**: $10-15/año
- **Total: ~$6-12/mes**

### 🎯 Conclusión

**¡Tu MVP está 95% listo!** Solo necesitas:

1. **2-4 horas** para configurar R2 y hacer deploy
2. **Cloudflare R2** es lo único crítico que falta
3. **Todo el código ya está preparado** para producción

**¡Puedes lanzar con confianza en cuanto configures el almacenamiento!** 🚀

---

**Arc Manager - Documentación Técnica Completa**  
© 2024 Arc Manager. Sistema listo para MVP.
