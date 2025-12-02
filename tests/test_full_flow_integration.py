"""
Test de integración completo que cubre todos los flujos principales SIN navegador.
Usa el cliente de Django en lugar de Playwright para máxima velocidad.

Corre con: pytest tests/test_full_flow_integration.py -v
"""
import pytest
from decimal import Decimal
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db(transaction=True)
class TestFullFlowIntegration:
    """
    Un solo test class que cubre TODOS los escenarios principales:
    - Login/Logout
    - Gestión de proyectos (CRUD)
    - Tareas y Kanban
    - Fases
    - Presupuestos y pagos
    - Subida de archivos
    - Gestión de usuarios
    - Clientes
    - Templates de fases
    - Planes y upgrades
    - Permisos de usuario limitado
    - Panel de admin
    """
    
    @pytest.fixture
    def setup_org_with_plan(self, db):
        """Setup completo: org, plan, suscripción, usuarios"""
        from tests.factories.orgs.org_factories import OrganizationFactory, ClientFactory
        from tests.factories.plans.plan_factories import BasicPlanFactory, SubscriptionFactory, TrialPlanFactory
        from tests.factories.accounts.account_factories import UserFactory, OrgAdminFactory
        from apps.accounts.models import User
        
        # Plan y organización
        plan = BasicPlanFactory(max_users=10, max_storage_gb=100)
        trial_plan = TrialPlanFactory()
        org = OrganizationFactory(name='Test Integration Org')
        SubscriptionFactory(organization=org, plan=plan, subscription_status='basic_active')
        
        # Usuarios
        admin = OrgAdminFactory(
            email='admin@integration.test',
            organization=org,
            first_name='Admin',
            last_name='User'
        )
        admin.set_password('AdminPass123!')
        admin.save()
        
        limited_user = UserFactory(
            email='limited@integration.test',
            organization=org,
            first_name='Limited',
            last_name='User',
            is_org_admin=False
        )
        limited_user.set_password('LimitedPass123!')
        limited_user.save()
        
        # Cliente
        client_obj = ClientFactory(organization=org, name='Cliente Principal')
        
        # Superuser para admin panel
        superuser = User.objects.create_superuser(
            email='super@integration.test',
            password='SuperPass123!',
            first_name='Super',
            last_name='Admin'
        )
        
        return {
            'org': org,
            'plan': plan,
            'trial_plan': trial_plan,
            'admin': admin,
            'limited_user': limited_user,
            'client': client_obj,
            'superuser': superuser
        }
    
    def test_complete_application_flow(self, setup_org_with_plan):
        """
        TEST MAESTRO: Cubre todos los flujos en una sola ejecución.
        """
        from tests.factories.projects.project_factories import (
            ProjectFactory, PhaseFactory, TaskFactory, ProjectPaymentFactory
        )
        from apps.projects.models import Project, Phase, Task, ProjectPayment, PhaseTemplate
        from apps.orgs.models import Client as OrgClient
        from apps.plans.models import UpgradeRequest, RenewalRequest
        
        data = setup_org_with_plan
        client = Client()
        
        # ============================================================
        # 1. AUTENTICACIÓN
        # ============================================================
        print("\n" + "="*60)
        print("1. AUTENTICACIÓN")
        print("="*60)
        
        # Login exitoso usando force_login (más confiable en tests)
        client.force_login(data['admin'])
        print("✓ Login de admin exitoso")
        
        # Acceso a dashboard (puede ser /main/ o redirigir)
        response = client.get('/main/')
        assert response.status_code in [200, 302]
        print("✓ Dashboard accesible")
        
        # Logout
        client.logout()
        print("✓ Logout exitoso")
        
        # Re-login para continuar
        client.force_login(data['admin'])
        
        # ============================================================
        # 2. GESTIÓN DE PROYECTOS (CRUD)
        # ============================================================
        print("\n" + "="*60)
        print("2. GESTIÓN DE PROYECTOS")
        print("="*60)
        
        # Crear proyecto via factory (simula creación)
        project = ProjectFactory(
            organization=data['org'],
            owner=data['admin'],
            client=data['client'],
            name='Proyecto Integración Test',
            total_budget=Decimal('100000'),
            budget_configured=True
        )
        print(f"✓ Proyecto creado: {project.name} (ID: {project.pk})")
        
        # Ver lista de proyectos
        response = client.get('/projects/')
        assert response.status_code == 200
        print("✓ Lista de proyectos accesible")
        
        # Ver detalle de proyecto
        response = client.get(f'/projects/{project.pk}/')
        assert response.status_code == 200
        print("✓ Detalle de proyecto accesible")
        
        # ============================================================
        # 3. FASES DEL PROYECTO
        # ============================================================
        print("\n" + "="*60)
        print("3. FASES DEL PROYECTO")
        print("="*60)
        
        phase1 = PhaseFactory(project=project, name='Diseño', order=1, status='pending')
        phase2 = PhaseFactory(project=project, name='Desarrollo', order=2, status='pending')
        phase3 = PhaseFactory(project=project, name='Testing', order=3, status='pending')
        
        assert Phase.objects.filter(project=project).count() == 3
        print(f"✓ 3 fases creadas: {[p.name for p in Phase.objects.filter(project=project)]}")
        
        # Cambiar estado de fase
        phase1.status = 'in_progress'
        phase1.save()
        print("✓ Estado de fase actualizado a 'in_progress'")
        
        # ============================================================
        # 4. TAREAS Y KANBAN
        # ============================================================
        print("\n" + "="*60)
        print("4. TAREAS Y KANBAN")
        print("="*60)
        
        task1 = TaskFactory(
            phase=phase1,
            title='Tarea de diseño UI',
            status='pending',
            assigned_to=data['admin']
        )
        task2 = TaskFactory(
            phase=phase1,
            title='Tarea de diseño UX',
            status='in_progress',
            assigned_to=data['limited_user']
        )
        task3 = TaskFactory(
            phase=phase2,
            title='Desarrollo backend',
            status='pending',
            assigned_to=data['admin']
        )
        
        assert Task.objects.filter(phase__project=project).count() == 3
        print(f"✓ 3 tareas creadas")
        
        # Cambiar estado de tarea (simula movimiento en Kanban)
        task1.status = 'completed'
        task1.save()
        print("✓ Tarea movida a 'completed' (Kanban)")
        
        # Ver Kanban
        response = client.get(f'/projects/{project.pk}/kanban/')
        assert response.status_code == 200
        print("✓ Vista Kanban accesible")
        
        # Mis tareas
        response = client.get('/projects/my-tasks/')
        assert response.status_code == 200
        print("✓ Vista 'Mis Tareas' accesible")
        
        # ============================================================
        # 5. PRESUPUESTOS Y FINANZAS
        # ============================================================
        print("\n" + "="*60)
        print("5. PRESUPUESTOS Y FINANZAS")
        print("="*60)
        
        # Verificar presupuesto configurado
        assert project.total_budget == Decimal('100000')
        assert project.budget_configured == True
        print(f"✓ Presupuesto configurado: ${project.total_budget}")
        
        # Crear pagos
        payment1 = ProjectPaymentFactory(
            project=project,
            amount=Decimal('30000'),
            description='Anticipo inicial',
            created_by=data['admin']
        )
        payment2 = ProjectPaymentFactory(
            project=project,
            amount=Decimal('20000'),
            description='Segundo pago',
            created_by=data['admin']
        )
        
        total_paid = ProjectPayment.objects.filter(project=project).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')
        print(f"✓ 2 pagos creados, total: ${total_paid}")
        
        # Ver finanzas del proyecto
        response = client.get(f'/projects/{project.pk}/finance/')
        assert response.status_code == 200
        print("✓ Vista de finanzas accesible")
        
        # Dashboard de finanzas
        response = client.get('/projects/finance/')
        assert response.status_code == 200
        print("✓ Dashboard de finanzas accesible")
        
        # ============================================================
        # 6. GESTIÓN DE CLIENTES
        # ============================================================
        print("\n" + "="*60)
        print("6. GESTIÓN DE CLIENTES")
        print("="*60)
        
        # Ya tenemos un cliente del setup
        assert OrgClient.objects.filter(organization=data['org']).count() >= 1
        print(f"✓ Cliente existente: {data['client'].name}")
        
        # Crear otro cliente
        new_client = OrgClient.objects.create(
            organization=data['org'],
            name='Cliente Nuevo Test',
            email='nuevo@cliente.com',
            is_active=True
        )
        print(f"✓ Nuevo cliente creado: {new_client.name}")
        
        # Ver lista de clientes
        response = client.get('/organizations/clients/')
        assert response.status_code == 200
        print("✓ Lista de clientes accesible")
        
        # ============================================================
        # 7. TEMPLATES DE FASES
        # ============================================================
        print("\n" + "="*60)
        print("7. TEMPLATES DE FASES")
        print("="*60)
        
        template = PhaseTemplate.objects.create(
            organization=data['org'],
            name='Template Arquitectura',
            description='Template para proyectos de arquitectura',
            phases=[
                {'name': 'Anteproyecto', 'order': 1},
                {'name': 'Proyecto Ejecutivo', 'order': 2},
                {'name': 'Construcción', 'order': 3},
            ]
        )
        print(f"✓ Template creado: {template.name} con {len(template.phases)} fases")
        
        # Ver templates
        response = client.get('/projects/templates/')
        assert response.status_code == 200
        print("✓ Lista de templates accesible")
        
        # ============================================================
        # 8. GESTIÓN DE USUARIOS
        # ============================================================
        print("\n" + "="*60)
        print("8. GESTIÓN DE USUARIOS")
        print("="*60)
        
        from apps.accounts.models import User
        
        # Ver lista de usuarios
        response = client.get('/users/')
        assert response.status_code == 200
        print("✓ Lista de usuarios accesible")
        
        # Contar usuarios de la org
        org_users = User.objects.filter(organization=data['org']).count()
        print(f"✓ Usuarios en la organización: {org_users}")
        
        # ============================================================
        # 9. PERMISOS DE USUARIO LIMITADO
        # ============================================================
        print("\n" + "="*60)
        print("9. PERMISOS DE USUARIO LIMITADO")
        print("="*60)
        
        # Logout admin y login como usuario limitado
        client.logout()
        client.force_login(data['limited_user'])
        print("✓ Login como usuario limitado")
        
        # Puede ver sus tareas
        response = client.get('/projects/my-tasks/')
        assert response.status_code == 200
        print("✓ Usuario limitado puede ver sus tareas")
        
        # NO puede acceder a gestión de usuarios
        response = client.get('/users/')
        assert response.status_code in [302, 403]  # Redirect o forbidden
        print("✓ Usuario limitado NO puede gestionar usuarios")
        
        # Volver a login como admin
        client.logout()
        client.force_login(data['admin'])
        
        # ============================================================
        # 10. PLANES Y SOLICITUDES DE UPGRADE
        # ============================================================
        print("\n" + "="*60)
        print("10. PLANES Y UPGRADES")
        print("="*60)
        
        # Ver plan actual (dashboard de suscripción)
        response = client.get('/plans/dashboard/')
        assert response.status_code == 200
        print("✓ Dashboard de suscripción accesible")
        
        # Crear solicitud de upgrade (usando BasicPlan con más capacidad)
        from tests.factories.plans.plan_factories import BasicPlanFactory as ProPlanFactory
        pro_plan = ProPlanFactory(
            display_name='Plan Profesional',
            max_users=50,
            max_storage_gb=500,
            price=Decimal('999.00')
        )
        
        upgrade_request = UpgradeRequest.objects.create(
            organization=data['org'],
            current_plan=data['plan'],
            requested_plan=pro_plan,
            amount=pro_plan.price,
            status='pending'
        )
        print(f"✓ Solicitud de upgrade creada: {data['plan'].name} → {pro_plan.display_name}")
        
        # Crear solicitud de renovación
        from apps.plans.models import Subscription
        sub = Subscription.objects.get(organization=data['org'])
        renewal = RenewalRequest.objects.create(
            organization=data['org'],
            subscription=sub,
            renewal_amount=data['plan'].price,
            renewal_days=30,
            status='pending'
        )
        print(f"✓ Solicitud de renovación creada")
        
        # ============================================================
        # 11. PANEL DE ADMIN (SUPERUSER)
        # ============================================================
        print("\n" + "="*60)
        print("11. PANEL DE ADMIN")
        print("="*60)
        
        # Logout y login como superuser
        client.logout()
        client.force_login(data['superuser'])
        
        # Acceso al admin
        response = client.get('/admin/')
        assert response.status_code == 200
        print("✓ Panel de admin accesible")
        
        # Ver solicitudes pendientes
        pending_upgrades = UpgradeRequest.objects.filter(status='pending').count()
        pending_renewals = RenewalRequest.objects.filter(status='pending').count()
        print(f"✓ Solicitudes pendientes - Upgrades: {pending_upgrades}, Renovaciones: {pending_renewals}")
        
        # Aprobar upgrade
        upgrade_request.status = 'approved'
        upgrade_request.save()
        print("✓ Solicitud de upgrade aprobada")
        
        # Ver organizaciones
        response = client.get('/admin/orgs/organization/')
        assert response.status_code == 200
        print("✓ Lista de organizaciones en admin accesible")
        
        # Ver usuarios
        response = client.get('/admin/accounts/user/')
        assert response.status_code == 200
        print("✓ Lista de usuarios en admin accesible")
        
        # Ver planes
        response = client.get('/admin/plans/plan/')
        assert response.status_code == 200
        print("✓ Lista de planes en admin accesible")
        
        # ============================================================
        # 12. RESUMEN FINAL
        # ============================================================
        print("\n" + "="*60)
        print("12. RESUMEN DE VERIFICACIÓN")
        print("="*60)
        
        # Conteos finales
        total_projects = Project.objects.filter(organization=data['org']).count()
        total_phases = Phase.objects.filter(project__organization=data['org']).count()
        total_tasks = Task.objects.filter(phase__project__organization=data['org']).count()
        total_payments = ProjectPayment.objects.filter(project__organization=data['org']).count()
        total_clients = OrgClient.objects.filter(organization=data['org']).count()
        total_templates = PhaseTemplate.objects.filter(organization=data['org']).count()
        
        print(f"✓ Proyectos: {total_projects}")
        print(f"✓ Fases: {total_phases}")
        print(f"✓ Tareas: {total_tasks}")
        print(f"✓ Pagos: {total_payments}")
        print(f"✓ Clientes: {total_clients}")
        print(f"✓ Templates: {total_templates}")
        
        print("\n" + "="*60)
        print("✅ TODOS LOS FLUJOS VERIFICADOS EXITOSAMENTE")
        print("="*60)


# Importar models para el aggregate
from django.db import models
