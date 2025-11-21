# Generated migration to update max_file_size_mb to 1500 MB

from django.db import migrations


def update_max_file_size(apps, schema_editor):
    """Actualizar max_file_size_mb a 1500 MB para archivos grandes de arquitectura"""
    SystemSettings = apps.get_model('main', 'SystemSettings')
    
    # Obtener o crear la configuración del sistema
    settings, created = SystemSettings.objects.get_or_create(pk=1)
    
    # Solo actualizar si el valor actual es menor a 1500 MB
    # Esto respeta cualquier configuración personalizada mayor
    if settings.max_file_size_mb < 1500:
        settings.max_file_size_mb = 1500
        settings.save()


def reverse_migration(apps, schema_editor):
    """Revertir a 500 MB si es necesario"""
    SystemSettings = apps.get_model('main', 'SystemSettings')
    
    try:
        settings = SystemSettings.objects.get(pk=1)
        if settings.max_file_size_mb == 1500:
            settings.max_file_size_mb = 500
            settings.save()
    except SystemSettings.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_remove_redundant_fields'),
    ]

    operations = [
        migrations.RunPython(update_max_file_size, reverse_migration),
    ]

