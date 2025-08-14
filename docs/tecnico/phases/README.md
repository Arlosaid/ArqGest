# Módulo de Fases – ArcManager

## Propósito

Estructurar los proyectos en fases ordenadas, con soporte para notas y archivos, y permitir la creación inicial de fases por plantilla o manual.

## Componentes

- Modelo `Phase` asociado a `Project`
- Plantillas de fases (`PhaseTemplate`) con lista JSON de fases
- Servicio de creación de fases por método: plantilla o manual
- Vista de detalle de fase con gestión de archivos y notas

## Flujo de usuario

1. Crear proyecto eligiendo método de fases (plantilla o manual).
2. Gestionar fases desde el detalle del proyecto o la vista de fase.
3. Usar plantillas para estandarizar fases por organización.

## Archivos clave

- `arc_manager/apps/projects/models.py` (Phase, PhaseTemplate)
- `arc_manager/apps/projects/forms.py` (ProjectForm, PhaseFormSet, PhaseTemplateForm)
- `arc_manager/apps/projects/services.py` (create_phases_for_project)
- `arc_manager/apps/projects/views.py` (PhaseDetailView, PhaseTemplate CRUD)
- `arc_manager/apps/projects/urls.py`

## Documentación relacionada

- `./IMPLEMENTACION_TECNICA.md`
- `./API_ENDPOINTS.md`
- `../projects/IMPLEMENTACION_TECNICA.md` (contexto del módulo de proyectos)
