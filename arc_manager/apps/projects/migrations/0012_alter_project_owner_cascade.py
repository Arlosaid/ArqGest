# Generated migration for CASCADE on project owner

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def delete_orphaned_projects(apps, schema_editor):
    """Eliminar proyectos sin owner antes de hacer el campo obligatorio"""
    Project = apps.get_model('projects', 'Project')
    orphaned = Project.objects.filter(owner__isnull=True)
    count = orphaned.count()
    if count > 0:
        orphaned.delete()
        print(f"Se eliminaron {count} proyecto(s) sin propietario")


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0011_rename_projects_pr_project_99f386_idx_payment_project_date_idx_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Primero eliminar proyectos huérfanos
        migrations.RunPython(delete_orphaned_projects, migrations.RunPython.noop),
        
        # Cambiar owner a CASCADE y eliminar null=True
        migrations.AlterField(
            model_name='project',
            name='owner',
            field=models.ForeignKey(
                help_text='El proyecto se eliminará si se elimina el propietario',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='owned_projects',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Propietario'
            ),
        ),
    ]

