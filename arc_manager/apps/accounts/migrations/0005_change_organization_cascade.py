# Generated migration for CASCADE organization relationship

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_alter_user_first_name_alter_user_last_name'),
        ('orgs', '0001_initial'),
    ]

    operations = [
        # Primero eliminar la constraint antigua
        migrations.RemoveConstraint(
            model_name='user',
            name='users_must_have_org_or_be_superuser_or_inactive',
        ),
        # Cambiar el on_delete a CASCADE
        migrations.AlterField(
            model_name='user',
            name='organization',
            field=models.ForeignKey(
                blank=True,
                help_text='Los usuarios se eliminarán automáticamente al eliminar la organización',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='users',
                to='orgs.organization',
                verbose_name='Organización'
            ),
        ),
        # Añadir verbose names al Meta
        migrations.AlterModelOptions(
            name='user',
            options={
                'verbose_name': 'Usuario',
                'verbose_name_plural': 'Usuarios'
            },
        ),
    ]

