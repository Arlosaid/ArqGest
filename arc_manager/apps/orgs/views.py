from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Organization, Client
from .mixins import ClientOwnerMixin
from .forms import OrganizationForm, ClientForm

# =============================================================================
# Vistas de Clientes
# =============================================================================

class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = 'orgs/client_list.html'
    context_object_name = 'clients'

    def get_queryset(self):
        """
        Return clients that belong to the user's organization.
        """
        if hasattr(self.request.user, 'organization') and self.request.user.organization:
            return Client.objects.filter(organization=self.request.user.organization)
        return Client.objects.none()

class ClientDetailView(LoginRequiredMixin, ClientOwnerMixin, DetailView):
    model = Client
    template_name = 'orgs/client_detail.html'
    context_object_name = 'client'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.get_object()
        context['projects'] = client.projects.all().order_by('-created_at')
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
        messages.success(self.request, "Cliente creado con éxito.")
        return super().form_valid(form)

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
        messages.success(self.request, "Cliente actualizado con éxito.")
        return super().form_valid(form)

class ClientDeleteView(LoginRequiredMixin, ClientOwnerMixin, DeleteView):
    model = Client
    template_name = 'orgs/client_confirm_delete.html'
    success_url = reverse_lazy('orgs:client_list')

    def form_valid(self, form):
        messages.success(self.request, "Cliente eliminado con éxito.")
        return super().form_valid(form)


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
