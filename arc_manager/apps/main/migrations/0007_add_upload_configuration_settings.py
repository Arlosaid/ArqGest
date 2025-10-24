# Generated manually on 2025-10-24
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_add_technical_upload_settings'),
    ]

    operations = [
        # Configuración de uploads para Desktop/Broadband
        migrations.AddField(
            model_name='systemsettings',
            name='upload_chunk_size_mb',
            field=models.PositiveIntegerField(
                default=50,
                help_text='Tamaño de cada chunk al subir archivos grandes. Mayor = más rápido pero más memoria',
                verbose_name='Tamaño de chunk (MB)'
            ),
        ),
        migrations.AddField(
            model_name='systemsettings',
            name='upload_max_concurrency',
            field=models.PositiveIntegerField(
                default=15,
                help_text='Número de chunks que se suben simultáneamente. Mayor = más rápido pero más ancho de banda',
                verbose_name='Concurrencia máxima'
            ),
        ),
        migrations.AddField(
            model_name='systemsettings',
            name='upload_retry_attempts',
            field=models.PositiveIntegerField(
                default=3,
                help_text='Número de reintentos si falla un chunk',
                verbose_name='Intentos de retry'
            ),
        ),
        migrations.AddField(
            model_name='systemsettings',
            name='upload_timeout_minutes',
            field=models.PositiveIntegerField(
                default=30,
                help_text='Tiempo máximo para completar un upload antes de cancelar',
                verbose_name='Timeout de upload (minutos)'
            ),
        ),
        
        # Configuración específica para móviles
        migrations.AddField(
            model_name='systemsettings',
            name='upload_chunk_size_mobile_mb',
            field=models.PositiveIntegerField(
                default=10,
                help_text='Tamaño de chunk para dispositivos móviles (más pequeño = más estable)',
                verbose_name='Tamaño de chunk móvil (MB)'
            ),
        ),
        migrations.AddField(
            model_name='systemsettings',
            name='upload_max_concurrency_mobile',
            field=models.PositiveIntegerField(
                default=2,
                help_text='Concurrencia para móviles (menor = más estable en conexiones lentas)',
                verbose_name='Concurrencia móvil'
            ),
        ),
        migrations.AddField(
            model_name='systemsettings',
            name='upload_max_file_size_mobile_mb',
            field=models.PositiveIntegerField(
                default=200,
                help_text='Tamaño máximo de archivo para uploads desde móvil',
                verbose_name='Tamaño máximo móvil (MB)'
            ),
        ),
    ]
