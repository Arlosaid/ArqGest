from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, View
from django.db.utils import IntegrityError
from django.db.models import Q
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied, ValidationError
from core.mixins import PageSizeMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Organization, Client
from .mixins import ClientOwnerMixin
from .forms import OrganizationForm, ClientForm
from core.structured_logging import log_error, log_info
import logging
import json

logger = logging.getLogger('apps.orgs')

# =============================================================================
# Vistas de Clientes
# =============================================================================

class ClientListView(LoginRequiredMixin, PageSizeMixin, ListView):
    model = Client
    template_name = 'orgs/client_list.html'
    context_object_name = 'clients'
    paginate_by = 6

    def get_queryset(self):
        """
        Return clients that belong to the user's organization with search functionality.
        """
        if hasattr(self.request.user, 'organization') and self.request.user.organization:
            queryset = Client.objects.filter(organization=self.request.user.organization)
            
            # Filtro de búsqueda
            search = self.request.GET.get('search', '')
            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search) |
                    Q(email__icontains=search) |
                    Q(phone_number__icontains=search)
                )
            
            return queryset.order_by('-created_at')
        return Client.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Pasar búsqueda al contexto
        context['search'] = self.request.GET.get('search', '')
        
        # Construir extra_params para el partial de paginación (preserva filtros)
        params = self.request.GET.copy()
        params.pop('page', None)
        extra_params = params.urlencode()
        if extra_params:
            extra_params = f"{extra_params}&"
        context['extra_params'] = extra_params

        # Agregar estadísticas de clientes
        if hasattr(self.request.user, 'organization') and self.request.user.organization:
            org = self.request.user.organization
            total_clients = org.clients.count()
            active_clients = org.clients.filter(is_active=True).count()
            inactive_clients = total_clients - active_clients
            
            context['total_clients'] = total_clients
            context['active_clients'] = active_clients
            context['inactive_clients'] = inactive_clients
        
        return context

class ClientDetailView(LoginRequiredMixin, ClientOwnerMixin, DetailView):
    model = Client
    template_name = 'orgs/client_detail.html'
    context_object_name = 'client'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.get_object()
        context['projects'] = client.projects.select_related('owner').order_by('-created_at')
        return context


class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'orgs/client_form.html'
    success_url = reverse_lazy('orgs:client_list')

    def get_form_kwargs(self):
        """Pass the organization to the form."""
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'organization'):
            kwargs['organization'] = self.request.user.organization
        return kwargs

    def form_valid(self, form):
        """
        Assign the organization from the logged-in user to the client.
        Handle both regular form submission and AJAX requests.
        """
        form.instance.organization = self.request.user.organization
        try:
            response = super().form_valid(form)
            
            # Log estructurado de creación de cliente
            log_info(
                event='CLIENT_CREATED',
                message=f"Cliente '{self.object.name}' creado exitosamente",
                logger_name='apps.orgs',
                client_id=self.object.id,
                client_name=self.object.name,
                organization_id=self.object.organization.id if self.object.organization else None,
                organization_name=self.object.organization.name if self.object.organization else None,
                email=self.object.email or '',
                is_active=self.object.is_active,
                created_by=self.request.user.email
            )
            
            # Handle AJAX requests (for quick client creation)
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'client': {
                        'id': self.object.id,
                        'name': self.object.name,
                        'email': self.object.email or '',
                        'phone_number': self.object.phone_number or '',
                    }
                })
            
            messages.success(self.request, "Cliente creado con éxito.")
            return response
            
        except IntegrityError as e:
            log_error(
                event='CLIENT_CREATE_FAILED',
                error_code='CLI002',
                error_message='Cliente duplicado - ya existe un cliente con este nombre',
                logger_name='apps.orgs',
                client_name=form.cleaned_data.get('name', 'Desconocido'),
                organization_id=self.request.user.organization.id if self.request.user.organization else None,
                created_by=self.request.user.email,
                exception_type=str(type(e).__name__)
            )
            
            # Handle AJAX requests
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Ya existe un cliente con este nombre en tu organización.'
                }, status=400)
            
            form.add_error('name', 'Ya existe un cliente con este nombre en tu organización.')
            return self.form_invalid(form)
            
        except Exception as e:
            log_error(
                event='CLIENT_CREATE_FAILED',
                error_code='CLI001',
                error_message=str(e),
                logger_name='apps.orgs',
                client_name=form.cleaned_data.get('name', 'Desconocido'),
                organization_id=self.request.user.organization.id if self.request.user.organization else None,
                created_by=self.request.user.email,
                exception_type=str(type(e).__name__)
            )
            
            # Handle AJAX requests
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Ha ocurrido un error inesperado al crear el cliente.'
                }, status=500)
            
            messages.error(self.request, "Ha ocurrido un error inesperado al crear el cliente. Por favor, contacta con soporte técnico.")
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Handle AJAX requests for invalid forms."""
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(e) for e in error_list]
            
            # Mensaje de error más específico
            error_message = 'Formulario inválido. Por favor, revisa los datos ingresados.'
            
            # Priorizar errores: primero errores generales, luego campos específicos
            priority_fields = ['__all__', 'name', 'email', 'phone_number', 'address']
            
            found_specific = False
            for field in priority_fields:
                if field in errors:
                    error_message = errors[field][0]
                    found_specific = True
                    break
            
            # Si no se encontró en los campos prioritarios, tomar el primer error disponible
            if not found_specific and errors:
                first_field = next(iter(errors))
                error_message = errors[first_field][0]
            
            return JsonResponse({
                'success': False,
                'error': error_message,
                'errors': errors
            }, status=400)
        return super().form_invalid(form)

class ClientUpdateView(LoginRequiredMixin, ClientOwnerMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'orgs/client_form.html'
    success_url = reverse_lazy('orgs:client_list')

    def get_form_kwargs(self):
        """Pass the request to the form."""
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'organization'):
            kwargs['organization'] = self.request.user.organization
        return kwargs
    
    def form_valid(self, form):
        try:
            # Capturar valores originales antes de guardar
            original_client = Client.objects.get(pk=self.object.pk)
            changes = []
            
            tracked_fields = {
                'name': 'Nombre',
                'email': 'Email',
                'phone_number': 'Teléfono',
                'is_active': 'Estado activo'
            }
            
            for field_name, field_label in tracked_fields.items():
                old_value = getattr(original_client, field_name)
                new_value = form.cleaned_data.get(field_name)
                
                if old_value != new_value:
                    changes.append({
                        'field': field_name,
                        'field_label': field_label,
                        'old': old_value,
                        'new': new_value
                    })
            
            response = super().form_valid(form)
            
            # Log solo si hubo cambios
            if changes:
                log_info(
                    event='CLIENT_UPDATED',
                    message=f"Cliente '{self.object.name}' actualizado con {len(changes)} cambio(s)",
                    logger_name='apps.orgs',
                    client_id=self.object.id,
                    client_name=self.object.name,
                    organization_id=self.object.organization.id if self.object.organization else None,
                    organization_name=self.object.organization.name if self.object.organization else None,
                    changes=changes,
                    updated_by=self.request.user.email
                )
                
                changes_text = ', '.join([c['field_label'] for c in changes])
                messages.success(self.request, f"Cliente actualizado con éxito. Cambios: {changes_text}")
            else:
                messages.info(self.request, "No se realizaron cambios.")
            
            return response
            
        except IntegrityError as e:
            log_error(
                event='CLIENT_UPDATE_FAILED',
                error_code='CLI004',
                error_message='Cliente duplicado - ya existe un cliente con este nombre',
                logger_name='apps.orgs',
                client_id=self.object.id,
                client_name=form.cleaned_data.get('name', 'Desconocido'),
                organization_id=self.request.user.organization.id if self.request.user.organization else None,
                updated_by=self.request.user.email,
                exception_type=str(type(e).__name__)
            )
            form.add_error('name', 'Ya existe un cliente con este nombre en tu organización.')
            return self.form_invalid(form)
            
        except Exception as e:
            log_error(
                event='CLIENT_UPDATE_FAILED',
                error_code='CLI003',
                error_message=str(e),
                logger_name='apps.orgs',
                client_id=self.object.id if hasattr(self, 'object') else None,
                client_name=form.cleaned_data.get('name', 'Desconocido'),
                organization_id=self.request.user.organization.id if self.request.user.organization else None,
                updated_by=self.request.user.email,
                exception_type=str(type(e).__name__)
            )
            messages.error(self.request, "Ha ocurrido un error inesperado al actualizar el cliente. Por favor, contacta con soporte técnico.")
            return self.form_invalid(form)

class ClientDeleteView(LoginRequiredMixin, ClientOwnerMixin, DeleteView):
    model = Client
    template_name = 'orgs/client_confirm_delete.html'
    success_url = reverse_lazy('orgs:client_list')

    def form_valid(self, form):
        try:
            # Capturar información antes de eliminar
            client_id = self.object.id
            client_name = self.object.name
            org_id = self.object.organization.id if self.object.organization else None
            org_name = self.object.organization.name if self.object.organization else None
            
            # Eliminar
            result = super().form_valid(form)
            
            # Log estructurado de eliminación
            log_info(
                event='CLIENT_DELETED',
                message=f"Cliente '{client_name}' eliminado exitosamente",
                logger_name='apps.orgs',
                client_id=client_id,
                client_name=client_name,
                organization_id=org_id,
                organization_name=org_name,
                deleted_by=self.request.user.email
            )
            
            messages.success(self.request, "Cliente eliminado con éxito.")
            return result
            
        except Exception as e:
            log_error(
                event='CLIENT_DELETE_FAILED',
                error_code='CLI005',
                error_message=str(e),
                logger_name='apps.orgs',
                client_id=self.object.id if hasattr(self, 'object') else None,
                client_name=self.object.name if hasattr(self, 'object') else 'Desconocido',
                organization_id=self.request.user.organization.id if self.request.user.organization else None,
                deleted_by=self.request.user.email,
                exception_type=str(type(e).__name__)
            )
            messages.error(self.request, "Ha ocurrido un error al eliminar el cliente. Por favor, contacta con soporte técnico.")
            return redirect(self.success_url)


class ClientDeleteAjaxView(LoginRequiredMixin, View):
    """Vista AJAX para eliminar un cliente"""
    
    def dispatch(self, request, *args, **kwargs):
        # Verificar si es una petición AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
                  request.content_type == 'application/x-www-form-urlencoded' or \
                  'fetch' in request.headers.get('Sec-Fetch-Mode', '')
        
        try:
            client_to_delete = get_object_or_404(Client, pk=kwargs['pk'])
        except:
            if is_ajax or request.method == 'POST':
                return JsonResponse({'success': False, 'error': 'Cliente no encontrado'}, status=404)
            raise
        
        current_user = request.user
        
        # Solo org_admin puede eliminar clientes de su organización
        if not (current_user.is_org_admin and current_user.organization and 
                client_to_delete.organization == current_user.organization):
            if is_ajax or request.method == 'POST':
                return JsonResponse({'success': False, 'error': 'No tienes permisos para eliminar este cliente'}, status=403)
            raise PermissionDenied("No tienes permisos para eliminar este cliente")
        
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, pk):
        """Obtener información del cliente para mostrar en el modal"""
        client_to_delete = get_object_or_404(Client, pk=pk)
        
        # Contar proyectos asociados
        project_count = client_to_delete.projects.count() if hasattr(client_to_delete, 'projects') else 0
        
        client_data = {
            'id': client_to_delete.id,
            'name': client_to_delete.name,
            'email': client_to_delete.email or '',
            'phone': client_to_delete.phone_number or '',
            'is_active': client_to_delete.is_active,
            'project_count': project_count,
        }
        
        return JsonResponse({
            'success': True,
            'client': client_data
        })
    
    def post(self, request, pk):
        """Procesar la eliminación del cliente"""
        client_to_delete = get_object_or_404(Client, pk=pk)
        
        try:
            # Capturar información antes de eliminar
            client_id = client_to_delete.id
            client_name = client_to_delete.name
            org_id = client_to_delete.organization.id if client_to_delete.organization else None
            org_name = client_to_delete.organization.name if client_to_delete.organization else None
            
            # Eliminar
            client_to_delete.delete()
            
            # Log estructurado de eliminación
            log_info(
                event='CLIENT_DELETED',
                message=f"Cliente '{client_name}' eliminado exitosamente via AJAX",
                logger_name='apps.orgs',
                client_id=client_id,
                client_name=client_name,
                organization_id=org_id,
                organization_name=org_name,
                deleted_by=request.user.email
            )
            
            return JsonResponse({
                'success': True,
                'message': f"Cliente '{client_name}' eliminado exitosamente"
            })
            
        except Exception as e:
            log_error(
                event='CLIENT_DELETE_FAILED',
                error_code='CLI005',
                error_message=str(e),
                logger_name='apps.orgs',
                client_id=pk,
                deleted_by=request.user.email,
                exception_type=str(type(e).__name__)
            )
            return JsonResponse({
                'success': False,
                'error': 'Ha ocurrido un error al eliminar el cliente'
            }, status=500)


class ClientToggleStatusView(LoginRequiredMixin, View):
    """Vista AJAX para cambiar el estado activo/inactivo de un cliente"""
    
    def dispatch(self, request, *args, **kwargs):
        client_to_toggle = get_object_or_404(Client, pk=kwargs['pk'])
        current_user = request.user
        
        # Solo org_admin puede cambiar estado de clientes de su organización
        if not (current_user.is_org_admin and current_user.organization and 
                client_to_toggle.organization == current_user.organization):
            raise PermissionDenied("No tienes permisos para modificar este cliente")
        
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, pk):
        """Cambiar estado del cliente"""
        client_to_toggle = get_object_or_404(Client, pk=pk)
        
        try:
            data = json.loads(request.body)
            new_status = data.get('is_active', False)
            old_status = client_to_toggle.is_active
            
            # Cambiar estado
            client_to_toggle.is_active = new_status
            client_to_toggle.save()
            
            # Log estructurado del cambio
            action = "activado" if new_status else "desactivado"
            log_info(
                event='CLIENT_STATUS_CHANGED',
                message=f"Cliente '{client_to_toggle.name}' {action}",
                logger_name='apps.orgs',
                client_id=client_to_toggle.id,
                client_name=client_to_toggle.name,
                organization_id=client_to_toggle.organization.id if client_to_toggle.organization else None,
                organization_name=client_to_toggle.organization.name if client_to_toggle.organization else None,
                old_status=old_status,
                new_status=new_status,
                changed_by=request.user.email
            )
            
            # Obtener estadísticas actualizadas para clientes
            org = request.user.organization
            total_clients = org.clients.count()
            active_clients = org.clients.filter(is_active=True).count()
            inactive_clients = total_clients - active_clients
            
            return JsonResponse({
                'success': True,
                'message': f"Cliente {action} correctamente",
                'new_status': new_status,
                'stats': {
                    'total_clients': total_clients,
                    'active_clients': active_clients,
                    'inactive_clients': inactive_clients
                }
            })
            
        except json.JSONDecodeError as e:
            log_error(
                event='CLIENT_STATUS_CHANGE_FAILED',
                error_code='CLI006',
                error_message='Datos JSON inválidos',
                logger_name='apps.orgs',
                client_id=client_to_toggle.id,
                client_name=client_to_toggle.name,
                changed_by=request.user.email,
                exception_type=str(type(e).__name__)
            )
            return JsonResponse({
                'success': False,
                'error': 'Datos inválidos'
            }, status=400)
            
        except Exception as e:
            log_error(
                event='CLIENT_STATUS_CHANGE_FAILED',
                error_code='CLI007',
                error_message=str(e),
                logger_name='apps.orgs',
                client_id=client_to_toggle.id,
                client_name=client_to_toggle.name,
                changed_by=request.user.email,
                exception_type=str(type(e).__name__)
            )
            return JsonResponse({
                'success': False,
                'error': 'Error al cambiar el estado del cliente'
            }, status=500)


# =============================================================================
# Vistas de Organización
# =============================================================================

@login_required
def my_organization(request):
    """Vista para que el usuario vea su propia organización"""
    if not request.user.organization:
        return redirect('main:dashboard')
    
    organization = request.user.organization
    
    return render(request, 'orgs/my_organization.html', {
        'organization': organization,
        'users': organization.users.all(),
        'admins': organization.get_admins(),
        'active_users': organization.users.filter(is_active=True),
    })

class OrganizationDetailView(LoginRequiredMixin, DetailView):
    """Vista para ver los detalles de una organización"""
    model = Organization
    template_name = 'orgs/my_organization.html'
    context_object_name = 'organization'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.get_object()
        
        context['users'] = organization.users.all()
        context['admins'] = organization.users.filter(is_org_admin=True)
        context['active_users'] = organization.users.filter(is_active=True)
        
        max_users = organization.get_max_users()
        context['percentage'] = int((organization.get_user_count() / max_users) * 100) if max_users > 0 else 0
        
        return context
    
    def dispatch(self, request, *args, **kwargs):
        org = self.get_object()
        if not (request.user.organization == org):
            messages.error(request, "No tienes permisos para ver esta organización.")
            return redirect('main:dashboard')
        return super().dispatch(request, *args, **kwargs)

class ClientDeleteAjaxView(LoginRequiredMixin, View):
    """Vista AJAX para eliminar clientes"""
    
    def dispatch(self, request, *args, **kwargs):
        # Verificar si es una petición AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
                  request.content_type == 'application/x-www-form-urlencoded' or \
                  'fetch' in request.headers.get('Sec-Fetch-Mode', '')
        
        try:
            client_to_delete = get_object_or_404(Client, pk=kwargs['pk'])
        except:
            if is_ajax or request.method == 'POST':
                return JsonResponse({'success': False, 'error': 'Cliente no encontrado'}, status=404)
            raise
        
        current_user = request.user
        
        # Solo org_admin puede eliminar clientes de su organización
        if not (current_user.is_org_admin and current_user.organization and 
                client_to_delete.organization == current_user.organization):
            if is_ajax or request.method == 'POST':
                return JsonResponse({'success': False, 'error': 'No tienes permisos para eliminar este cliente'}, status=403)
            raise PermissionDenied("No tienes permisos para eliminar este cliente")
        
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, pk):
        """Procesar la eliminación del cliente"""
        client_to_delete = get_object_or_404(Client, pk=pk)
        
        try:
            # Verificar que se confirmó la eliminación
            confirm_delete = request.POST.get('confirm_delete')
            if confirm_delete != 'yes':
                return JsonResponse({
                    'success': False,
                    'error': 'Confirmación requerida'
                })
            
            client_name = client_to_delete.name
            
            # Log importante para auditoría
            logger.info(f"Cliente eliminado: {client_name} por {request.user.email}")
            
            # Eliminar cliente
            client_to_delete.delete()
            
            # Obtener estadísticas actualizadas
            org = request.user.organization
            total_clients = Client.objects.filter(organization=org).count()
            active_clients = Client.objects.filter(organization=org, is_active=True).count()
            inactive_clients = total_clients - active_clients
            
            stats = {
                'total_clients': total_clients,
                'active_clients': active_clients,
                'inactive_clients': inactive_clients,
            }
            
            return JsonResponse({
                'success': True,
                'message': f'Cliente {client_name} eliminado exitosamente.',
                'stats': stats
            })
            
        except Exception as e:
            # Log detallado del error para desarrolladores
            logger.error(f"Error al eliminar cliente: {str(e)}")
            
            # Siempre respuesta amigable, nunca errores técnicos
            return JsonResponse({
                'success': False,
                'error': 'Error al eliminar el cliente. Por favor, contacta con soporte técnico.'
            }, status=500)
