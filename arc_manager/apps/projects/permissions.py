"""
Módulo de permisos para el control de acceso a tareas.

Define decoradores y funciones de validación para asegurar que solo
los usuarios con los roles apropiados puedan realizar acciones específicas
en las tareas.
"""
from functools import wraps
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from .models import Task
import logging

logger = logging.getLogger('apps.projects')


def is_organization_admin(user):
    """Valida si el usuario es administrador de la organización."""
    return hasattr(user, 'is_org_admin') and user.is_org_admin


def is_task_assignee(user, task):
    """Valida si el usuario es el asignado de la tarea."""
    if not task.assigned_to_id:
        return False
    return task.assigned_to_id == user.id


def task_create_permission_required(view_func):
    """
    Decorador que requiere que el usuario sea admin de su organización
    para crear tareas.
    
    Los usuarios normales (non-admin) no pueden crear tareas.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.method == 'POST':
            if not is_organization_admin(request.user):
                logger.warning(
                    f"Usuario {request.user.email} intentó crear tarea sin permisos"
                )
                if 'application/json' in request.headers.get('Accept', ''):
                    return JsonResponse({
                        'success': False,
                        'error': 'No tienes permisos para crear tareas',
                        'error_code': 'TASK_CREATE_PERMISSION_DENIED'
                    }, status=403)
                # Para requests normales, retornar al view sin ejecutar
                from django.contrib import messages
                messages.error(request, _('No tienes permisos para crear tareas'))
                return redirect('projects:project-list')
        
        return view_func(request, *args, **kwargs)
    
    return login_required(wrapper)


def task_edit_permission_required(view_func):
    """
    Decorador que requiere que el usuario sea admin de la organización para editar tareas.
    
    Solo los admins pueden editar la información de las tareas (título, descripción, etc.).
    Los usuarios normales pueden subir archivos a sus tareas desde el modal de detalle.
    """
    @wraps(view_func)
    def wrapper(request, pk, *args, **kwargs):
        try:
            task = get_object_or_404(
                Task,
                pk=pk,
                phase__project__organization=request.user.organization
            )
        except Http404:
            logger.warning(
                f"Usuario {request.user.email} intentó acceder a tarea inexistente: {pk}"
            )
            raise
        
        # Solo admins pueden editar tareas
        is_admin = is_organization_admin(request.user)
        
        if not is_admin:
            logger.warning(
                f"Usuario {request.user.email} intentó editar tarea {pk} sin permisos (no es admin)"
            )
            if 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse({
                    'success': False,
                    'error': 'No tienes permisos para editar esta tarea',
                    'error_code': 'TASK_EDIT_PERMISSION_DENIED'
                }, status=403)
            
            from django.contrib import messages
            messages.error(request, _('No tienes permisos para editar esta tarea'))
            return redirect('projects:project-detail', pk=task.phase.project_id)
        
        return view_func(request, pk, *args, **kwargs)
    
    return wrapper


def task_assign_permission_required(view_func):
    """
    Decorador que requiere que el usuario sea admin de la organización
    para asignar tareas a otros usuarios.
    
    Solo los admins pueden asignar tareas.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_organization_admin(request.user):
            logger.warning(
                f"Usuario {request.user.email} intentó asignar tarea sin permisos"
            )
            if 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse({
                    'success': False,
                    'error': 'No tienes permisos para asignar tareas',
                    'error_code': 'TASK_ASSIGN_PERMISSION_DENIED'
                }, status=403)
            
            from django.contrib import messages
            messages.error(request, _('No tienes permisos para asignar tareas'))
            return redirect('projects:project-list')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def task_status_change_permission_required(view_func):
    """
    Decorador que permite cambiar estado de una tarea si:
    - El usuario es admin de la organización, O
    - El usuario es el asignado de la tarea
    
    Los usuarios normales pueden cambiar estado solo de sus tareas asignadas.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Obtener task_id de args o kwargs
        task_id = kwargs.get('task_pk') or kwargs.get('pk')
        if not task_id and len(args) > 0:
            task_id = args[0]
        
        try:
            task = get_object_or_404(
                Task,
                pk=task_id,
                phase__project__organization=request.user.organization
            )
        except Http404:
            logger.warning(
                f"Usuario {request.user.email} intentó cambiar estado de tarea inexistente: {task_id}"
            )
            raise
        
        is_admin = is_organization_admin(request.user)
        is_assignee = is_task_assignee(request.user, task)
        
        if not (is_admin or is_assignee):
            logger.warning(
                f"Usuario {request.user.email} intentó cambiar estado de tarea {task_id} sin permisos"
            )
            if 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse({
                    'success': False,
                    'error': 'No tienes permisos para cambiar el estado de esta tarea',
                    'error_code': 'TASK_STATUS_PERMISSION_DENIED'
                }, status=403)
            
            from django.contrib import messages
            messages.error(request, _('No tienes permisos para cambiar el estado de esta tarea'))
            return redirect('projects:project-list')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def task_move_permission_required(view_func):
    """
    Decorador que requiere que el usuario sea admin de la organización
    para mover una tarea entre fases.
    
    Solo los admins pueden mover tareas.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Obtener task_id
        task_id = kwargs.get('task_pk') or kwargs.get('pk')
        if not task_id and len(args) > 0:
            task_id = args[0]
        
        try:
            task = get_object_or_404(
                Task,
                pk=task_id,
                phase__project__organization=request.user.organization
            )
        except Http404:
            logger.warning(
                f"Usuario {request.user.email} intentó mover tarea inexistente: {task_id}"
            )
            raise
        
        if not is_organization_admin(request.user):
            logger.warning(
                f"Usuario {request.user.email} intentó mover tarea {task_id} sin permisos"
            )
            if 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse({
                    'success': False,
                    'error': 'No tienes permisos para mover tareas entre fases',
                    'error_code': 'TASK_MOVE_PERMISSION_DENIED'
                }, status=403)
            
            from django.contrib import messages
            messages.error(request, _('No tienes permisos para mover tareas entre fases'))
            return redirect('projects:project-list')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper
