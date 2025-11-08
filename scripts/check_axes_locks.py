#!/usr/bin/env python
"""
Script para verificar los registros de bloqueo de Django-Axes
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
sys.path.insert(0, '/app/arc_manager')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from axes.models import AccessAttempt
from django.conf import settings

print("=" * 80)
print("📊 REGISTROS DE BLOQUEO DE DJANGO-AXES")
print("=" * 80)
print(f"\n⚙️  Configuración actual:")
print(f"   - AXES_FAILURE_LIMIT: {settings.AXES_FAILURE_LIMIT}")
print(f"   - AXES_COOLOFF_TIME: {settings.AXES_COOLOFF_TIME} horas ({settings.AXES_COOLOFF_TIME * 60} minutos)")
print(f"   - AXES_RESET_ON_SUCCESS: {settings.AXES_RESET_ON_SUCCESS}")
print(f"   - AXES_LOCKOUT_BY_USER_OR_IP: {settings.AXES_LOCKOUT_BY_USER_OR_IP}")

attempts = AccessAttempt.objects.all().order_by('-attempt_time')
print(f"\n📋 Total de registros en BD: {attempts.count()}")

if attempts.count() > 0:
    print("\n🔍 Últimos 5 registros:\n")
    for attempt in attempts[:5]:
        time_since = datetime.now(attempt.attempt_time.tzinfo) - attempt.attempt_time
        cooloff_expired = time_since > timedelta(hours=float(settings.AXES_COOLOFF_TIME))
        status = "✅ EXPIRADO (desbloqueado)" if cooloff_expired else f"🔒 ACTIVO (faltan {timedelta(hours=float(settings.AXES_COOLOFF_TIME)) - time_since})"
        
        print(f"   Email: {attempt.username}")
        print(f"   IP: {attempt.ip_address}")
        print(f"   Intentos fallidos: {attempt.failures_since_start}")
        print(f"   Timestamp: {attempt.attempt_time}")
        print(f"   Tiempo transcurrido: {time_since}")
        print(f"   Estado: {status}")
        print(f"   User-Agent: {attempt.user_agent[:50]}...")
        print()
else:
    print("\n✅ No hay registros de bloqueo en este momento")

print("=" * 80)
print("\n💡 CÓMO FUNCIONA EL DESBLOQUEO AUTOMÁTICO:")
print("   1. Axes guarda timestamp del bloqueo en la BD")
print("   2. En cada login, AxesBackend calcula: tiempo_actual - timestamp_bloqueo")
print("   3. Si > COOLOFF_TIME → elimina el registro (desbloqueo automático)")
print("   4. Si < COOLOFF_TIME → rechaza el login con PermissionDenied")
print("\n   ⚡ NO se necesita cron job - es automático en cada intento de login")
print("=" * 80)
