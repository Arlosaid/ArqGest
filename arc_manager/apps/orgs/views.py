from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, View
from django.db.utils import IntegrityError
from django.db.models import Q
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from core.mixins import PageSizeMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Organization, Client
from .mixins import ClientOwnerMixin
from .forms import OrganizationForm, ClientForm
import logging
import json

logger = logging.getLogger(__name__)

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
        """
        form.instance.organization = self.request.user.organization
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Cliente creado con éxito.")
            return response
        except IntegrityError:
            form.add_error('name', 'Ya existe un cliente con este nombre en tu organización.')
            return self.form_invalid(form)

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
            response = super().form_valid(form)
            messages.success(self.request, "Cliente actualizado con éxito.")
            return response
        except IntegrityError:
            form.add_error('name', 'Ya existe un cliente con este nombre en tu organización.')
            return self.form_invalid(form)

class ClientDeleteView(LoginRequiredMixin, ClientOwnerMixin, DeleteView):
    model = Client
    template_name = 'orgs/client_confirm_delete.html'
    success_url = reverse_lazy('orgs:client_list')

    def form_valid(self, form):
        messages.success(self.request, "Cliente eliminado con éxito.")
        return super().form_valid(form)


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
            
            # Cambiar estado
            client_to_toggle.is_active = new_status
            client_to_toggle.save()
            
            # Log del cambio
            action = "activado" if new_status else "desactivado"
            logger.info(
                f"Cliente {action}: {client_to_toggle.name} "
                f"(ID: {client_to_toggle.id}, por {request.user.email})"
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
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Datos inválidos'
            }, status=400)
        except Exception as e:
            logger.error(f"Error al cambiar estado de cliente: {str(e)}")
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
