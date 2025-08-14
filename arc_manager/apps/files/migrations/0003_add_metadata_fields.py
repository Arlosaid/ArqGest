from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectfile',
            name='size_bytes',
            field=models.BigIntegerField(db_index=True, default=0),
        ),
        migrations.AddField(
            model_name='projectfile',
            name='ext_upper',
            field=models.CharField(blank=True, db_index=True, max_length=16),
        ),
        migrations.AddField(
            model_name='projectfile',
            name='content_type',
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AddField(
            model_name='projectfile',
            name='checksum_sha256',
            field=models.CharField(blank=True, db_index=True, max_length=64),
        ),
        migrations.AddIndex(
            model_name='projectfile',
            index=models.Index(fields=['uploaded_at'], name='files_proj_uploaded_idx'),
        ),
        migrations.AddIndex(
            model_name='projectfile',
            index=models.Index(fields=['ext_upper', 'size_bytes'], name='files_proj_ext_size_idx'),
        ),
    ]


