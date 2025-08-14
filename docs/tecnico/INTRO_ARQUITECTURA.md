# Documentación Técnica de ArcManager

Este documento sirve como referencia central técnica (resumen). Para detalles por módulo, ver `docs/tecnico/*/`.

## 1. Arquitectura del Backend

### 1.1. Configuración Principal (`settings.py`)

Ver `arc_manager/core/settings.py`. Puntos destacados: apps (Django/Terceros/Locales), middlewares, logging robusto con rotación y consola prod.

### 1.2. Optimización de Modelos y Base de Datos

- on_delete ajustado (`SET_NULL`, `PROTECT`) en puntos críticos
- índices en campos de filtro frecuentes (Project.status, Task.status/priority/due_date, etc.)

---

Mantener actualizado conforme evolucione el proyecto.
