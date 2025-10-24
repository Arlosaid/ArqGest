# Generated migration to remove deprecated fields from SystemSettings
# Since this is a test environment with no real clients, we can safely remove these fields

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_filelimitssettings_planbillingsettings_and_more'),
    ]

    operations = [
        # Remove deprecated fields from SystemSettings
        migrations.RemoveField(
            model_name='systemsettings',
            name='max_upload_size_per_request_mb',
        ),
        migrations.RemoveField(
            model_name='systemsettings',
            name='max_projects_per_org',
        ),
        migrations.RemoveField(
            model_name='systemsettings',
            name='max_phases_per_project',
        ),
    ]