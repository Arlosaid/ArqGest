# 🚀 Guía de Cache Busting para ArcManager

## ¿Qué es Cache Busting?

Cache busting es una técnica que resuelve el problema de actualización de archivos estáticos (CSS, JS) en producción sin necesidad de que los usuarios borren su caché.

## ✅ Cómo funciona en ArcManager

### 1. **Desarrollo (DEBUG=True)**
```
styles.css  → styles.css  (sin cambios)
script.js   → script.js   (sin cambios)
```
- Los archivos mantienen su nombre original
- Facilita el desarrollo y debugging

### 2. **Producción (DEBUG=False)**
```
styles.css  → styles.7f8c2a.css  (con hash)
script.js   → script.b4d6e1.js   (con hash)
```
- Cada archivo tiene un hash único basado en su contenido
- Cuando cambias el CSS, el hash cambia automáticamente
- Los navegadores ven un "nuevo archivo" y lo descargan

## 🛠️ Comandos útiles

### Deployment normal
```bash
docker-compose exec web python manage.py deploy_static
```

### Deployment forzado (limpia todo)
```bash
docker-compose exec web python manage.py deploy_static --force
```

### Probar cache busting en desarrollo
```bash
docker-compose exec web python manage.py deploy_static --test
```

## 📊 Configuración de Cache

### Headers automáticos en producción:
- **Archivos con hash**: `Cache-Control: max-age=31536000, immutable` (1 año)
- **HTML**: `Cache-Control: max-age=0, no-cache` (sin caché)

## 🎯 Beneficios

### ✅ Para usuarios:
- **Velocidad**: Los archivos CSS/JS se cargan desde caché local
- **Actualización automática**: Nuevas versiones se descargan sin intervención
- **Sin problemas**: No necesitan borrar caché manualmente

### ✅ Para desarrolladores:
- **Deploy sin estrés**: No más "abran en incógnito"
- **Rendimiento óptimo**: Cache largo + actualización automática
- **SEO mejorado**: Páginas cargan más rápido

## 🔧 Troubleshooting

### Si los cambios no se ven:
1. Verificar que estés en producción (`DEBUG=False`)
2. Ejecutar: `python manage.py deploy_static --force`
3. Verificar que existe `staticfiles.json`

### Si falla el collectstatic:
1. Verificar que todos los archivos CSS/JS son válidos
2. Revisar permisos en el directorio `staticfiles/`
3. Usar `--force` para limpiar archivos corruptos

## 📝 Archivos importantes

- **Configuración**: `core/settings.py` (líneas 255-282)
- **Manifest**: `staticfiles/staticfiles.json` (generado automáticamente)
- **Comando**: `apps/main/management/commands/deploy_static.py`

## 🚀 Deploy en producción

1. **Hacer cambios en CSS/JS**
2. **Ejecutar**: `python manage.py deploy_static`
3. **Verificar**: El manifest se actualiza con nuevos hashes
4. **Deploy**: Los usuarios automáticamente obtienen la nueva versión

¡No más problemas de caché! 🎉
