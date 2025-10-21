# Sistema de Recordatorios Automáticos

## ¿Cómo funciona?

El sistema envía automáticamente recordatorios de renovación **solo el día de vencimiento** para evitar spam.

## Configuración

### 1. Archivos creados:
- `scripts/send_renewal_reminders.sh` - Script que ejecuta el comando
- `scripts/crontab` - Configuración de tareas programadas
- Servicio `cron` en `docker-compose.yml`

### 2. Programación:
- **Todos los días a las 9:00 AM** se ejecuta automáticamente
- Solo envía correos a suscripciones que vencen ese día
- Logs se guardan en `/app/logs/cron.log`

## Uso

### Iniciar el sistema completo:
```bash
docker-compose up -d
```

### Ver logs del cron:
```bash
docker-compose logs cron
```

### Ejecutar manualmente (para pruebas):
```bash
docker-compose exec cron /app/scripts/send_renewal_reminders.sh
```

### Verificar que funciona:
```bash
# Ver logs de ejecución
docker-compose exec cron cat /app/logs/cron.log

# Ver configuración de cron
docker-compose exec cron crontab -l
```

## Ventajas de esta solución:

✅ **Súper simple** - Solo cron, sin dependencias complejas  
✅ **Automático** - Se ejecuta todos los días sin intervención  
✅ **Eficiente** - Solo envía correos el día de vencimiento  
✅ **Monitoreable** - Logs claros de cada ejecución  
✅ **Robusto** - Se reinicia automáticamente si falla  

## Monitoreo:

Los logs se guardan en:
- `logs/cron.log` - Ejecuciones del script
- `docker-compose logs cron` - Logs del contenedor

## Personalización:

Para cambiar la hora de ejecución, edita `scripts/crontab`:
```
# Ejemplo: cambiar a las 8:00 AM
0 8 * * * /app/scripts/send_renewal_reminders.sh
```
