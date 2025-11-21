"""
Management command para verificar la configuración de límites de archivos
"""
from django.core.management.base import BaseCommand
from apps.files.validators import FileValidator
from apps.main.models import SystemSettings


class Command(BaseCommand):
    help = 'Verifica la configuración de límites de archivos'

    def handle(self, *args, **options):
        # Verificar configuración en SystemSettings
        settings = SystemSettings.load()
        self.stdout.write(
            f"SystemSettings.max_file_size_mb: {settings.max_file_size_mb} MB"
        )

        # Verificar configuración en FileValidator
        validator = FileValidator()
        max_mb = validator.max_size_bytes / (1024 * 1024)
        self.stdout.write(
            f"FileValidator.max_size_bytes: {max_mb:.0f} MB"
        )

        # Verificar si el archivo de 875.97 MB sería aceptado
        test_file_size_mb = 875.97
        test_file_size_bytes = test_file_size_mb * 1024 * 1024

        if test_file_size_bytes <= validator.max_size_bytes:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✓ Archivo de {test_file_size_mb} MB: ACEPTADO"
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f"\n✗ Archivo de {test_file_size_mb} MB: RECHAZADO"
                )
            )
            self.stdout.write(
                f"  (Excede el límite por {test_file_size_mb - max_mb:.2f} MB)"
            )

        self.stdout.write(f"\nLímite efectivo: {max_mb:.0f} MB")


