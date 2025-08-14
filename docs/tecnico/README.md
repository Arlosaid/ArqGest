# 📘 Documentación Técnica por Módulo

Este espacio consolida documentación técnica exhaustiva por módulo, siguiendo la estructura del documento de implementación técnica del módulo de Planes.

## Índice de módulos

- Accounts → `docs/tecnico/accounts/IMPLEMENTACION_TECNICA.md`
- Main → `docs/tecnico/main/IMPLEMENTACION_TECNICA.md`
- Organizations (Orgs) → `docs/tecnico/orgs/IMPLEMENTACION_TECNICA.md`
- Users → `docs/tecnico/users/IMPLEMENTACION_TECNICA.md`
- Plans → `docs/tecnico/plans/IMPLEMENTACION_TECNICA.md`
- Projects → `docs/tecnico/projects/IMPLEMENTACION_TECNICA.md`
- Files → `docs/tecnico/files/IMPLEMENTACION_TECNICA.md`

## Arquitectura de Base de Datos
- Diagrama y explicación: `docs/tecnico/ARQUITECTURA_BD.md`
- DBML (dbdiagram.io): `docs/tecnico/er/arcmanager.dbml`
- PlantUML: `docs/tecnico/er/arcmanager.puml`

## Estructura recomendada de cada documento técnico

1. Arquitectura del Sistema (con diagrama)
2. Modelos de Datos Detallados
3. Lógica de Negocio (Services)
4. Vistas y Controllers (Views/Handlers)
5. Template Tags / Helpers
6. Sistema de Permisos (Mixins/Decoradores)
7. Endpoints y URLs
8. Frontend y JavaScript
9. Comandos de Gestión
10. Testing y Validación
11. Optimización y Performance
12. Seguridad (Autorización, rate-limits, Axes)
13. Configuración (settings, env)
14. Migraciones relevantes
15. Troubleshooting / Métricas / Observabilidad
16. Roadmap

### Notas del proyecto
- Nombres de tablas en inglés (preferencia del proyecto).
- Comandos `manage.py` se ejecutan dentro del contenedor Docker.
- Mantener el estilo de código simple y claro; evitar duplicación.
