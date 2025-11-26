"""
Tests de integración para la advertencia de pérdida de datos al reemplazar fases con plantilla.

TC-74: Verificar que se advierte al usuario antes de eliminar tareas al reemplazar fases.
"""
import pytest
import json
from django.urls import reverse
from tests.factories.accounts.account_factories import UserFactory, OrgAdminFactory
from tests.factories.orgs.org_factories import OrganizationFactory
from tests.factories.projects.project_factories import (
    ProjectFactory,
    PhaseFactory,
    TaskFactory,
    PhaseTemplateFactory
)
from tests.factories.plans import SubscriptionFactory


@pytest.mark.django_db
@pytest.mark.integration
class TestPhaseTemplateReplacementWarning:
    """Tests para validar advertencia de pérdida de datos al reemplazar fases"""
    
    def test_replace_phases_without_tasks_should_succeed_without_warning(self, client):
        """
        GIVEN: Un proyecto con fases sin tareas
        WHEN: Se intenta reemplazar fases con una plantilla
        THEN: La operación debe completarse sin requerir confirmación
        """
        # Setup
        org = OrganizationFactory()
        SubscriptionFactory(organization=org)
        user = OrgAdminFactory(organization=org)
        project = ProjectFactory(organization=org)
        phase1 = PhaseFactory(project=project, name='Fase 1')
        phase2 = PhaseFactory(project=project, name='Fase 2')
        
        template = PhaseTemplateFactory(
            organization=org,
            name='Plantilla Test',
            phases=[
                {'name': 'Nueva Fase 1', 'order': 0},
                {'name': 'Nueva Fase 2', 'order': 1}
            ]
        )
        
        client.force_login(user)
        url = reverse('projects:project-phases-edit', kwargs={'pk': project.pk})
        
        # Act
        response = client.post(
            url,
            data=json.dumps({'template_id': template.id, 'confirmed': False}),
            content_type='application/json',
            
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        
        # Verificar que las fases fueron reemplazadas
        project.refresh_from_db()
        assert project.phases.count() == 2
        assert project.phases.filter(name='Nueva Fase 1').exists()
        assert project.phases.filter(name='Nueva Fase 2').exists()
        assert not project.phases.filter(name='Fase 1').exists()
    
    def test_replace_phases_with_tasks_without_confirmation_should_fail(self, client):
        """
        TC-74: GIVEN: Un proyecto con fases que tienen tareas asociadas
        WHEN: Se intenta reemplazar fases SIN confirmación explícita
        THEN: La operación debe fallar y retornar información de las tareas a perder
        """
        # Setup
        org = OrganizationFactory()
        SubscriptionFactory(organization=org)
        user = OrgAdminFactory(organization=org)
        project = ProjectFactory(organization=org)
        phase1 = PhaseFactory(project=project, name='Diseño')
        phase2 = PhaseFactory(project=project, name='Construcción')
        
        # Crear tareas asociadas
        task1 = TaskFactory(phase=phase1, title='Tarea 1 Diseño')
        task2 = TaskFactory(phase=phase1, title='Tarea 2 Diseño')
        task3 = TaskFactory(phase=phase2, title='Tarea 1 Construcción')
        
        template = PhaseTemplateFactory(
            organization=org,
            name='Plantilla V2',
            phases=[
                {'name': 'Fase A', 'order': 0},
                {'name': 'Fase B', 'order': 1}
            ]
        )
        
        client.force_login(user)
        url = reverse('projects:project-phases-edit', kwargs={'pk': project.pk})
        
        # Act
        response = client.post(
            url,
            data=json.dumps({'template_id': template.id, 'confirmed': False}),
            content_type='application/json',
            
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        print(f"Response data: {data}")  # Debug
        assert data['success'] is False
        assert data['error'] == 'confirmation_required'
        assert 'data' in data
        assert data['data']['total_tasks'] == 3
        assert len(data['data']['affected_phases']) == 2
        
        # Verificar que NO se eliminaron las fases originales
        project.refresh_from_db()
        assert project.phases.count() == 2
        assert project.phases.filter(name='Diseño').exists()
        assert project.phases.filter(name='Construcción').exists()
        
        # Verificar que las tareas siguen existiendo
        assert phase1.tasks.count() == 2
        assert phase2.tasks.count() == 1
    
    def test_replace_phases_with_tasks_with_confirmation_should_succeed(self, client):
        """
        TC-74: GIVEN: Un proyecto con fases que tienen tareas asociadas
        WHEN: Se intenta reemplazar fases CON confirmación explícita
        THEN: La operación debe completarse y eliminar las tareas (CASCADE)
        """
        # Setup
        org = OrganizationFactory()
        SubscriptionFactory(organization=org)
        user = OrgAdminFactory(organization=org)
        project = ProjectFactory(organization=org)
        phase1 = PhaseFactory(project=project, name='Fase Original 1')
        phase2 = PhaseFactory(project=project, name='Fase Original 2')
        
        # Crear tareas asociadas
        task1 = TaskFactory(phase=phase1, title='Tarea 1')
        task2 = TaskFactory(phase=phase1, title='Tarea 2')
        task3 = TaskFactory(phase=phase2, title='Tarea 3')
        
        original_task_ids = [task1.id, task2.id, task3.id]
        
        template = PhaseTemplateFactory(
            organization=org,
            name='Plantilla Nueva',
            phases=[
                {'name': 'Fase Plantilla 1', 'order': 0},
                {'name': 'Fase Plantilla 2', 'order': 1}
            ]
        )
        
        client.force_login(user)
        url = reverse('projects:project-phases-edit', kwargs={'pk': project.pk})
        
        # Act
        response = client.post(
            url,
            data=json.dumps({'template_id': template.id, 'confirmed': True}),
            content_type='application/json',
            
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['tasks_deleted'] == 3
        
        # Verificar que las fases fueron reemplazadas
        project.refresh_from_db()
        assert project.phases.count() == 2
        assert project.phases.filter(name='Fase Plantilla 1').exists()
        assert project.phases.filter(name='Fase Plantilla 2').exists()
        assert not project.phases.filter(name='Fase Original 1').exists()
        
        # CRÍTICO: Verificar que las tareas fueron eliminadas (CASCADE)
        from arc_manager.apps.projects.models import Task
        for task_id in original_task_ids:
            assert not Task.objects.filter(id=task_id).exists()
    
    def test_affected_phases_data_is_accurate(self, client):
        """
        TC-74: Verificar que la información de fases afectadas es precisa
        """
        # Setup
        org = OrganizationFactory()
        SubscriptionFactory(organization=org)
        user = OrgAdminFactory(organization=org)
        project = ProjectFactory(organization=org)
        
        phase1 = PhaseFactory(project=project, name='Diseño', order=0)
        phase2 = PhaseFactory(project=project, name='Desarrollo', order=1)
        phase3 = PhaseFactory(project=project, name='Pruebas', order=2)
        
        # Fase 1: 5 tareas
        for i in range(5):
            TaskFactory(phase=phase1, title=f'Tarea Diseño {i+1}')
        
        # Fase 2: 3 tareas
        for i in range(3):
            TaskFactory(phase=phase2, title=f'Tarea Desarrollo {i+1}')
        
        # Fase 3: sin tareas
        
        template = PhaseTemplateFactory(organization=org, name='Plantilla')
        
        client.force_login(user)
        url = reverse('projects:project-phases-edit', kwargs={'pk': project.pk})
        
        # Act
        response = client.post(
            url,
            data=json.dumps({'template_id': template.id, 'confirmed': False}),
            content_type='application/json',
            
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data['data']['total_tasks'] == 8
        
        affected_phases = data['data']['affected_phases']
        assert len(affected_phases) == 2  # Solo fases con tareas
        
        phase_map = {p['name']: p['task_count'] for p in affected_phases}
        assert phase_map['Diseño'] == 5
        assert phase_map['Desarrollo'] == 3
    
    def test_non_admin_cannot_replace_phases(self, client):
        """
        Verificar que usuarios no admin no pueden reemplazar fases
        """
        # Setup
        org = OrganizationFactory()
        SubscriptionFactory(organization=org)
        user = UserFactory(organization=org, is_org_admin=False)  # No ADMIN
        project = ProjectFactory(organization=org)
        phase = PhaseFactory(project=project)
        template = PhaseTemplateFactory(organization=org)
        
        client.force_login(user)
        url = reverse('projects:project-phases-edit', kwargs={'pk': project.pk})
        
        # Act
        response = client.post(
            url,
            data=json.dumps({'template_id': template.id}),
            content_type='application/json',
            
        )
        
        # Assert
        # OrganizationAdminMixin debería bloquear el acceso
        assert response.status_code == 403
    
    def test_template_not_found_returns_404(self, client):
        """
        Verificar que usar un template_id inexistente retorna 404
        """
        # Setup
        org = OrganizationFactory()
        SubscriptionFactory(organization=org)
        user = OrgAdminFactory(organization=org)
        project = ProjectFactory(organization=org)
        
        client.force_login(user)
        url = reverse('projects:project-phases-edit', kwargs={'pk': project.pk})
        
        # Act
        response = client.post(
            url,
            data=json.dumps({'template_id': 99999}),
            content_type='application/json',
            
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data['error'] == 'template_not_found'


@pytest.mark.django_db
@pytest.mark.integration
class TestPhaseTemplateReplacementEdgeCases:
    """Tests de casos borde para el reemplazo de fases"""
    
    def test_replace_with_empty_template_phases(self, client):
        """
        Verificar comportamiento con plantilla que tiene phases vacío
        """
        org = OrganizationFactory()
        SubscriptionFactory(organization=org)
        user = OrgAdminFactory(organization=org)
        project = ProjectFactory(organization=org)
        phase = PhaseFactory(project=project)
        
        template = PhaseTemplateFactory(
            organization=org,
            name='Plantilla Vacía',
            phases=[]
        )
        
        client.force_login(user)
        url = reverse('projects:project-phases-edit', kwargs={'pk': project.pk})
        
        response = client.post(
            url,
            data=json.dumps({'template_id': template.id, 'confirmed': False}),
            content_type='application/json',
            
        )
        
        # Debería completarse (eliminar todas las fases)
        assert response.status_code == 200
        project.refresh_from_db()
        assert project.phases.count() == 0
    
    def test_replace_phases_logs_critical_operation(self, client, caplog):
        """
        Verificar que se registra log cuando se eliminan tareas
        """
        import logging
        
        org = OrganizationFactory()
        SubscriptionFactory(organization=org)
        user = OrgAdminFactory(organization=org)
        project = ProjectFactory(organization=org)
        phase = PhaseFactory(project=project)
        TaskFactory(phase=phase)
        TaskFactory(phase=phase)
        
        template = PhaseTemplateFactory(organization=org)
        
        client.force_login(user)
        url = reverse('projects:project-phases-edit', kwargs={'pk': project.pk})
        
        with caplog.at_level(logging.WARNING):
            response = client.post(
                url,
                data=json.dumps({'template_id': template.id, 'confirmed': True}),
                content_type='application/json',
                
            )
        
        assert response.status_code == 200
        
        # Verificar que se registró el log de operación crítica
        assert any('tasks were deleted' in record.message for record in caplog.records)
