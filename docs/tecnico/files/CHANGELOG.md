# 📝 Changelog — Módulo Files

Formato basado en Keep a Changelog. Versionado Semántico.

## [1.0.0] - 2025-08-13

### ✨ Agregado
- Documentación completa (`INDEX`, `README`, `API_ENDPOINTS`, `IMPLEMENTACION_TECNICA`).
- Endpoints `upload_file` y `delete_file` con soporte HTMX.
- Modelo `ProjectFile` con `filename`, `extension` y `size` helpers.
- Estructura de almacenamiento por organización/proyecto/fase.

### 🔄 Cambiado
- N/A

### 🐛 Corregido
- N/A

### 🔐 Seguridad
- Validación de organización en vistas de subida y eliminación.

### 🧰 Documentación
- Primera versión técnica del módulo Files.

---

Roadmap breve
- Registrar `ProjectFile` en admin con filtros y búsqueda.
- Validar extensiones y tamaños en backend.
- Añadir logs de auditoría para `upload`/`delete`.
- Previsualización y versionado de archivos.

Arc Manager · Files


