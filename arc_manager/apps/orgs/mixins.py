from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.contrib import messages

class OrganizationAdminMixin(AccessMixin):
    """
    Mixin que verifica que el usuario sea administrador de su organización.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_org_admin:
            messages.error(request, "No tienes permisos de administrador para realizar esta acción.")
            return redirect('main:dashboard')
        return super().dispatch(request, *args, **kwargs)

class ClientOwnerMixin(AccessMixin):
    """
    Mixin que verifica que el usuario pertenezca a la organización propietaria del cliente.
    Asegura que un usuario no pueda acceder/modificar clientes de otras organizaciones.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Se asume que la vista es una DetailView, UpdateView o DeleteView que tiene get_object()
        client = self.get_object()

        if client.organization != request.user.organization and not request.user.is_superuser:
            messages.error(request, "No tienes permiso para acceder a este cliente.")
            # Redirige a la lista de clientes de su propia organización
            return redirect('orgs:client_list')
            
        return super().dispatch(request, *args, **kwargs)
