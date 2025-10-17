from django.urls import path
from . import views

app_name = 'orgs'

urlpatterns = [
    # URLs de Clientes
    path('clients/', views.ClientListView.as_view(), name='client_list'),
    path('clients/new/', views.ClientCreateView.as_view(), name='client_create'),
    path('clients/<int:pk>/', views.ClientDetailView.as_view(), name='client_detail'),
    path('clients/<int:pk>/edit/', views.ClientUpdateView.as_view(), name='client_edit'),
    path('clients/<int:pk>/delete/', views.ClientDeleteView.as_view(), name='client_delete'),
    
    # AJAX endpoints de Clientes
    path('clients/<int:pk>/toggle-status/', views.ClientToggleStatusView.as_view(), name='client_toggle_status'),

    # URLs de Organización
    path('<int:pk>/', views.OrganizationDetailView.as_view(), name='organization_detail'),
    
    # Editar organización - DESHABILITADO
    # RAZÓN: Los org_admin no deberían poder editar campos críticos como:
    # - Nombre (afecta logs, emails, reportes)
    # - Estado activo (puede bloquear a todos los usuarios)
    # Solo superusers pueden hacer estos cambios desde el admin panel
    # path('<int:pk>/editar/', views.OrganizationUpdateView.as_view(), name='edit'),

    # Mi organización (vista para usuarios normales)
    path('mi-organizacion/', views.my_organization, name='my_organization'),
]
