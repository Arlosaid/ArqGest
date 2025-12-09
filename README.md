# ArqGest

Sistema de gestion organizacional para estudios de arquitectura.

## Stack Tecnologico

- Python 3.11 / Django 5.2
- PostgreSQL 15
- Redis 7
- Docker / Docker Compose

## Instalacion

### Requisitos

- Docker y Docker Compose

### Configuracion

```bash
git clone <url-del-repositorio>
cd arc_manager
cp env.example .env
docker-compose up --build
```

La aplicacion estara disponible en `http://localhost:8000`.

### Variables de Entorno

Editar `.env` segun sea necesario:

```env
DEBUG=True
SECRET_KEY=<clave-secreta>
POSTGRES_DB=arc_manager_dev
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
```

## Desarrollo

### Comandos Docker

```bash
# Iniciar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f web

# Detener servicios
docker-compose down
```

### Comandos Django

```bash
# Migraciones
docker-compose exec web python manage.py migrate

# Crear superusuario
docker-compose exec web python manage.py createsuperuser

# Shell de Django
docker-compose exec web python manage.py shell

# Ejecutar tests
docker-compose exec web pytest
```

## Estructura del Proyecto

```
arc_manager/
├── arc_manager/
│   ├── apps/
│   │   ├── accounts/    # Autenticacion
│   │   ├── files/       # Gestion de archivos
│   │   ├── main/        # App principal
│   │   ├── orgs/        # Organizaciones
│   │   ├── plans/       # Planes de suscripcion
│   │   ├── projects/    # Proyectos
│   │   └── users/       # Usuarios
│   ├── core/            # Configuracion Django
│   ├── static/          # Archivos estaticos
│   └── templates/       # Plantillas HTML
├── tests/               # Suite de pruebas
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## URLs

| Endpoint | URL |
|----------|-----|
| Aplicacion | http://localhost:8000 |
| Admin | http://localhost:8000/admin |
| Health Check | http://localhost:8000/health/ |

## Despliegue

El proyecto esta configurado para desplegarse en Railway. Ver `railway.json` para la configuracion. 