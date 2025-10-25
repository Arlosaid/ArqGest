# 🚂 Railway - Guía de Monitoreo de Logs

**Sistema:** Arc Manager  
**Plataforma:** Railway  
**Objetivo:** Monitorear logs optimizados y detectar problemas

---

## 📊 Comandos Útiles de Railway

### Ver Logs en Tiempo Real
```bash
# Ver logs en vivo
railway logs --follow

# Ver logs con timestamps
railway logs --follow --timestamps

# Ver últimas 100 líneas
railway logs --tail 100
```

### Filtrar por Severidad
```bash
# Solo errores y críticos
railway logs | grep -E "ERROR|CRITICAL"

# Solo warnings
railway logs | grep "WARNING"

# Excluir DEBUG (producción)
railway logs | grep -v "DEBUG"
```

### Analizar Eventos Específicos
```bash
# Login fallidos
railway logs | grep "login_failed"

# Login fallidos con detalles
railway logs | grep "login_failed" | jq '.'

# Contar intentos fallidos en última hora
railway logs --since 1h | grep "login_failed" | wc -l

# Ver IPs con múltiples intentos
railway logs | grep "login_failed" | grep -o '"ip":"[^"]*"' | sort | uniq -c | sort -rn
```

### Monitorear Upload
```bash
# Uploads en progreso (no debería haber muchos)
railway logs | grep "Upload progress"

# Uploads completados
railway logs | grep "Upload completado"

# Errores de upload
railway logs | grep "upload" | grep -E "ERROR|CRITICAL"
```

### Analizar Performance
```bash
# Logs de últimas 24 horas
railway logs --since 24h

# Contar logs por hora (verificar reducción)
railway logs --since 6h | awk '{print $1}' | cut -d: -f1 | sort | uniq -c

# Buscar logs duplicados (no debería haber)
railway logs | grep "LOGIN FALLIDO" | wc -l  # Debe ser 0
railway logs | grep "Intento de login" | wc -l  # Debe ser 0
```

---

## 🔍 Validar Deduplicación

### Test 1: Login Fallido
```bash
# Hacer 3 intentos fallidos en la app
# Luego verificar:
railway logs --tail 50 | grep -c "login_failed"
# Debe retornar: 3 (uno por intento)

railway logs --tail 50 | grep -c "FALLIDO"
# Debe retornar: 0 (eliminado)
```

### Test 2: AXES Verbosity
```bash
# Verificar que AXES no loguea cada intento
railway logs | grep "axes.watch_login" | grep "INFO"
# No debe retornar nada

railway logs | grep "axes.watch_login" | grep "WARNING"
# Solo cuando hay bloqueos
```

### Test 3: Upload Progress
```bash
# Subir archivo grande (>100MB)
# Verificar:
railway logs --tail 100 | grep "Upload progress"
# En producción debe ser 0 (solo DEBUG)
```

---

## 🎯 Formato de Logs Estructurados

### Login Fallido
```json
{
  "timestamp": "2025-10-25T10:30:00Z",
  "level": "WARNING",
  "logger": "apps.accounts",
  "event": "login_failed",
  "reason": "invalid_password",
  "user": "hash_user87",
  "ip": "189.237.35.85",
  "user_agent": "Chrome/141.0.0.0"
}
```

### Cambio de Estado de Tarea
```json
{
  "timestamp": "2025-10-25T10:30:00Z",
  "level": "INFO",
  "logger": "apps.projects",
  "event": "task_status_changed",
  "task_id": 123,
  "task_title": "Diseño de planos",
  "old_status": "TODO",
  "new_status": "IN_PROGRESS",
  "phase_id": 45
}
```

---

## 📈 Métricas a Monitorear

### Volumen de Logs
```bash
# Logs por minuto (antes vs después)
# Antes: ~50-100 logs/min
# Después: ~10-20 logs/min (reducción 80%)

railway logs --since 1h | wc -l
```

### Eventos Críticos
```bash
# Login fallidos (seguridad)
railway logs --since 24h | grep "login_failed" | wc -l

# Errores de aplicación
railway logs --since 24h | grep "ERROR" | wc -l

# Errores críticos (requieren acción inmediata)
railway logs --since 24h | grep "CRITICAL" | wc -l
```

---

## 🚨 Alertas Recomendadas

### Configurar en Railway:

1. **Login Fallidos Masivos**
   - Condición: >10 login_failed en 5 minutos
   - Acción: Notificación + revisar IP

2. **Errores Críticos**
   - Condición: Cualquier log CRITICAL
   - Acción: Notificación inmediata

3. **Errores de Base de Datos**
   - Condición: "database" + "ERROR"
   - Acción: Revisar conexiones

---

## 🔧 Troubleshooting

### Problema: Logs Duplicados
```bash
# Buscar patrones duplicados
railway logs | grep "login" | sort | uniq -d

# Si encuentras duplicados:
# 1. Revisar qué archivo genera el log
# 2. Aplicar patrón: 1 evento = 1 log
```

### Problema: Demasiados Logs DEBUG
```bash
# Verificar variable de entorno
railway variables

# DEBUG debe ser False en producción
# Si está True, cambiar:
railway variables set DEBUG=False
```

### Problema: AXES Muy Verboso
```bash
# Verificar configuración
railway logs | grep "axes" | head -20

# Si loguea cada intento:
# Verificar en settings.py que AXES_VERBOSE=False
```

---

## 📊 Análisis Avanzado

### Exportar Logs para Análisis
```bash
# Exportar últimas 24 horas
railway logs --since 24h > logs_24h.json

# Analizar con jq
cat logs_24h.json | jq 'select(.event == "login_failed")'

# Contar eventos por tipo
cat logs_24h.json | jq -r '.event' | sort | uniq -c | sort -rn
```

### Detectar Patrones de Ataque
```bash
# IPs con más de 5 intentos fallidos
railway logs --since 1h | grep "login_failed" | \
  grep -o '"ip":"[^"]*"' | sort | uniq -c | \
  awk '$1 > 5 {print}'

# Usuarios más atacados
railway logs --since 24h | grep "login_failed" | \
  grep -o '"user":"[^"]*"' | sort | uniq -c | sort -rn | head -10
```

---

## ✅ Checklist de Producción

### Post-Deploy:
- [ ] Verificar que DEBUG=False
- [ ] Confirmar AXES_VERBOSE=False
- [ ] Contar logs por minuto (debe ser <50% del anterior)
- [ ] Buscar "login_failed" (debe ser formato JSON)
- [ ] Buscar "LOGIN FALLIDO" (debe ser 0 resultados)
- [ ] Verificar que no hay logs DEBUG en producción
- [ ] Configurar alertas para eventos críticos

### Monitoreo Continuo:
- [ ] Revisar logs cada día
- [ ] Analizar patrones de login_failed semanalmente
- [ ] Verificar volumen de logs mensualmente
- [ ] Optimizar según patrones encontrados

---

## 💡 Tips de Performance

1. **Usar Filtros Específicos**
   ```bash
   # Mejor
   railway logs | grep "login_failed"
   
   # Evitar
   railway logs | grep "login"  # Muy amplio
   ```

2. **Limitar Timeframe**
   ```bash
   # Mejor
   railway logs --since 1h
   
   # Evitar
   railway logs  # Todos los logs
   ```

3. **Exportar para Análisis Pesado**
   ```bash
   # Para búsquedas complejas, exportar primero
   railway logs --since 24h > temp.log
   grep "pattern" temp.log
   ```

---

## 📞 Soporte

- **Documentación Railway:** https://docs.railway.app/
- **Railway CLI:** https://docs.railway.app/develop/cli
- **Logs Estructurados:** Ver `LOGGING_DEDUPLICATION_APPLIED.md`

---

**Resultado Esperado:** Logs limpios, estructurados y fáciles de analizar en Railway con 87% menos volumen.
