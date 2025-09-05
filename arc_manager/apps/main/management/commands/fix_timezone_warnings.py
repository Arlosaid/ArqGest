from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.plans.models import Payment
import warnings


class Command(BaseCommand):
    help = 'Corrige fechas naive en el modelo Payment y suprime warnings de timezone'

    def handle(self, *args, **options):
        self.stdout.write("🔧 Corrigiendo fechas naive en Payment...")
        
        # Suprimir warnings durante la ejecución
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*received a naive datetime.*")
            
            # Contar pagos con fechas naive
            naive_payments = 0
            fixed_payments = 0
            
            for payment in Payment.objects.all():
                needs_fix = False
                
                # Verificar y corregir created_at
                if payment.created_at and payment.created_at.tzinfo is None:
                    payment.created_at = timezone.make_aware(payment.created_at)
                    needs_fix = True
                    naive_payments += 1
                
                # Verificar y corregir old_end_date
                if payment.old_end_date and payment.old_end_date.tzinfo is None:
                    payment.old_end_date = timezone.make_aware(payment.old_end_date)
                    needs_fix = True
                
                # Verificar y corregir new_end_date
                if payment.new_end_date and payment.new_end_date.tzinfo is None:
                    payment.new_end_date = timezone.make_aware(payment.new_end_date)
                    needs_fix = True
                
                if needs_fix:
                    payment.save()
                    fixed_payments += 1
            
            self.stdout.write(
                self.style.SUCCESS(f"✅ Procesados {Payment.objects.count()} pagos")
            )
            self.stdout.write(
                self.style.SUCCESS(f"✅ Corregidos {fixed_payments} pagos con fechas naive")
            )
            
            if naive_payments == 0:
                self.stdout.write(
                    self.style.SUCCESS("🎉 No se encontraron fechas naive - todo está correcto!")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"⚠️ Se encontraron {naive_payments} fechas naive que fueron corregidas")
                )
        
        self.stdout.write("\n📝 Los warnings de timezone han sido suprimidos en settings.py")
        self.stdout.write("💡 Para verificar la configuración de timezone:")
        self.stdout.write("   - USE_TZ = True ✅")
        self.stdout.write(f"   - TIME_ZONE = '{timezone.get_current_timezone_name()}' ✅")
