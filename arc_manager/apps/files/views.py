from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import ProjectFile
from apps.projects.models import Phase

@login_required
@require_POST
def upload_file(request, project_id, phase_id):
    """Handles file upload and returns an updated file list for HTMX."""
    phase = get_object_or_404(Phase, id=phase_id, project_id=project_id)
    
    if request.user.organization != phase.project.organization:
        return HttpResponseForbidden(_("You do not have permission to access this resource."))

    if not request.FILES.getlist('files'):
        # This case might not be hit if the input is 'required', but it's good practice.
        messages.error(request, _("No files were selected."))
        return HttpResponse(status=400)

    for uploaded_file in request.FILES.getlist('files'):
        ProjectFile.objects.create(
            phase=phase,
            file=uploaded_file,
            uploaded_by=request.user
        )
    
    messages.success(request, _("File(s) uploaded successfully."))

    # Si es una petición HTMX, devolvemos solo la lista actualizada
    if request.headers.get('HX-Request') == 'true':
        files = phase.files.all()
        return render(request, 'projects/partials/file_list.html', {'files': files})

    # En formularios normales, redirigir al detalle del proyecto (pestaña Archivos)
    project_url = reverse('projects:project-detail', kwargs={'pk': phase.project_id})
    return redirect(f"{project_url}?tab=files#files")

@login_required
@require_POST
def delete_file(request, file_id):
    """Handles the deletion of a project file.

    - Si es HTMX, responde vacío (204) para que el frontend remueva el elemento.
    - Si es una llamada normal/fetch, responde JSON con success.
    """
    project_file = get_object_or_404(ProjectFile, id=file_id)
    
    if request.user.organization != project_file.phase.project.organization:
        return HttpResponseForbidden(_("You do not have permission to access this resource."))

    project_file.file.delete(save=False)
    project_file.delete()
    
    # HTMX: devolver 200 con cuerpo vacío para que outerHTML se reemplace por nada
    if request.headers.get('HX-Request') == 'true':
        return HttpResponse("")

    # Fetch/normal: JSON
    return JsonResponse({"success": True, "id": file_id})
