# Generated migration to remove redundant SystemSettings fields

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_add_upload_configuration_settings'),
    ]

    operations = [
        # Remove default_max_users (redundant - use max_users_trial/basic directly)
        migrations.RemoveField(
            model_name='systemsettings',
            name='default_max_users',
        ),
        # Remove default_storage_gb (redundant - use storage_trial_gb/basic_gb directly)
        migrations.RemoveField(
            model_name='systemsettings',
            name='default_storage_gb',
        ),
        # Remove billing_cycle_days (belongs in Plan model, not global settings)
        migrations.RemoveField(
            model_name='systemsettings',
            name='billing_cycle_days',
        ),
        # Remove updated_by (not properly used, updated_at is sufficient)
        migrations.RemoveField(
            model_name='systemsettings',
            name='updated_by',
        ),
    ]
