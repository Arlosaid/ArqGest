# Generated manually on 2025-10-24
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_alter_filelimitssettings_max_upload_size_per_request_mb'),
    ]

    operations = [
        migrations.AlterField(
            model_name='systemsettings',
            name='max_file_size_mb',
            field=models.PositiveIntegerField(
                default=1500, 
                help_text='Tamaño máximo permitido por archivo individual. Se aplica inmediatamente al guardar.', 
                verbose_name='Tamaño máximo de archivo (MB)'
            ),
        ),
        migrations.AddField(
            model_name='systemsettings',
            name='data_upload_max_memory_mb',
            field=models.PositiveIntegerField(
                default=25, 
                help_text='Tamaño máximo de archivos que se procesan en memoria RAM (recomendado: 25 MB)', 
                verbose_name='Memoria máxima para uploads (MB)'
            ),
        ),
        migrations.AddField(
            model_name='systemsettings',
            name='max_checksum_size_mb',
            field=models.PositiveIntegerField(
                default=50, 
                help_text='Tamaño máximo de archivo para calcular checksums SHA256 (evita sobrecarga en archivos grandes)', 
                verbose_name='Tamaño máximo para checksum (MB)'
            ),
        ),
    ]
