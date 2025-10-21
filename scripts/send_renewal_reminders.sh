#!/bin/bash

# Script para enviar recordatorios de renovación
# Se ejecuta diariamente a las 9:00 AM

cd /app
python manage.py send_renewal_reminders

# Log de ejecución
echo "$(date): Recordatorios de renovación ejecutados" >> /app/logs/cron.log
