# 🔧 Implementación Técnica — Módulo Users

## 📋 Tabla de Contenidos
1. Arquitectura del Sistema
2. Modelos de Datos
3. Vistas y Controllers
4. Formularios
5. Seguridad y Permisos
6. Endpoints y URLs
7. Frontend
8. Testing

---

## 🏗️ Arquitectura del Sistema
- CRUD de usuarios de la organización.

## 🗃️ Modelos de Datos
- `User` (custom) con `organization` opcional (por políticas de `SET_NULL`).

## 🎮 Vistas y Controllers
- Lista, crear (simple create), detalle, editar, eliminar vía AJAX.

## 📝 Formularios
- Formularios validados y estilizados con Crispy Forms.

## 🔐 Seguridad y Permisos
- Acciones de creación/edición/eliminación solo para `user.is_org_admin`.

## 🌐 Endpoints y URLs
- `/users/` (GET)
- `/users/create/` (GET/POST)
- `/users/<id>/` (GET)
- `/users/<id>/edit/` (GET/POST)
- `/users/<id>/delete-ajax/` (POST)

## 🎨 Frontend
- Templates en `templates/users/`.
- Estilos en `static/css/user_management.css` y JS en `static/js/user_management.js`.

## 🧪 Testing
- Cobertura de permisos y respuestas AJAX.
