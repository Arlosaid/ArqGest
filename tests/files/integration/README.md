# Tests de Integración - Upload de Archivos

## 🎯 Objetivo

Estos tests validan el **flujo completo end-to-end** de upload y gestión de archivos, desde la petición HTTP hasta la persistencia en base de datos y generación de logs.

## 🚨 Por Qué Son Críticos

Los tests unitarios solo prueban componentes aislados (modelos, validators). Los tests de integración aseguran que **TODO el sistema funciona correctamente en conjunto**:

- ✅ Validaciones se ejecutan en el orden correcto
- ✅ Límites de storage del plan se respetan
- ✅ Tipos MIME inválidos se detectan
- ✅ Logs estructurados se generan correctamente
- ✅ Permisos cross-organization funcionan
- ✅ Usuarios reciben feedback apropiado

## 📋 Tests Incluidos

### 1. `TestFileUploadSuccess` - Uploads Exitosos

**Propósito:** Verificar que archivos válidos se suban correctamente.

```python
test_upload_pdf_file_successfully()
```
- ✅ Archivo PDF válido se guarda en DB
- ✅ Campos correctos (`filename`, `ext_upper`, `uploaded_by`)
- ✅ Log de éxito generado
- ✅ HTTP 200 con trigger JS

```python
test_upload_large_rar_file_successfully()
```
- ✅ Fix del bug: archivos RAR con MIME `application/x-rar` se aceptan
- ✅ Archivos grandes (>500MB) se procesan
- ✅ Sin rechazo por tipo MIME

### 2. `TestFileUploadStorageLimits` - Límites de Almacenamiento

**Propósito:** Asegurar que los límites del plan se respeten.

```python
test_upload_rejected_when_storage_limit_exceeded()
```
- ✅ Plan con límite de 1MB
- ✅ Upload de 2MB es **rechazado**
- ✅ HTTP 413 (Payload Too Large)
- ✅ Archivo NO se guarda en DB
- ✅ Log de advertencia generado

```python
test_upload_warning_when_storage_near_limit()
```
- ✅ Plan con 85% de uso
- ✅ Upload **exitoso** (hay espacio)
- ✅ WARNING log generado para monitoreo proactivo
- ✅ Administradores pueden actuar antes del límite

**Por Qué Importa:**
- Previene que usuarios excedan su plan
- Permite facturación correcta por tier
- Evita costos inesperados de almacenamiento

### 3. `TestFileUploadValidations` - Validaciones de Seguridad

**Propósito:** Prevenir uploads maliciosos o inválidos.

```python
test_upload_rejected_for_invalid_mime_type()
```
- ✅ Archivo `malware.pdf` con contenido ejecutable (MZ header)
- ✅ **Rechazado** aunque tenga extensión .pdf
- ✅ Protege contra ataques de MIME spoofing

```python
test_upload_rejected_for_dangerous_extension()
```
- ✅ Archivos .exe, .bat, .sh, .vbs son **bloqueados**
- ✅ SECURITY CRITICAL: previene ejecución de malware

```python
test_upload_rejected_for_file_too_large()
```
- ✅ Respeta `MAX_FILE_SIZE_MB`
- ✅ Archivo de 2MB rechazado si límite es 1MB

```python
test_upload_rejected_for_empty_file()
```
- ✅ Archivos de 0 bytes rechazados
- ✅ Previene datos corruptos

**Por Qué Importa:**
- Seguridad del servidor
- Integridad de datos
- Prevención de exploits

### 4. `TestFileUploadPermissions` - Seguridad Cross-Organization

**Propósito:** Asegurar aislamiento de datos entre organizaciones.

```python
test_upload_rejected_for_different_organization()
```
- ✅ Usuario de Org1 **NO puede** subir a proyecto de Org2
- ✅ HTTP 403 Forbidden
- ✅ Previene contaminación de datos
- ✅ CRÍTICO para compliance (GDPR, privacidad)

**Por Qué Importa:**
- Multi-tenancy seguro
- Compliance legal
- Confianza del cliente

### 5. `TestFileUploadLogging` - Logging Estructurado

**Propósito:** Verificar trazabilidad completa.

```python
test_structured_logging_on_successful_upload()
```
- ✅ Log JSON con campos requeridos
- ✅ `event`, `entity_type`, `action` presentes
- ✅ Formato correcto para búsqueda

```python
test_structured_logging_on_validation_failure()
```
- ✅ Nivel WARNING correcto
- ✅ Error code presente
- ✅ Información de debugging disponible

**Por Qué Importa:**
- Debugging rápido en producción
- Auditoría de operaciones
- Monitoreo proactivo

### 6. `TestFileDeleteViews` - Eliminación de Archivos

```python
test_delete_file_successfully()
```
- ✅ Archivo eliminado de DB
- ✅ Archivo físico eliminado
- ✅ Log de eliminación generado

```python
test_delete_rejected_for_different_organization()
```
- ✅ Cross-org delete **bloqueado**
- ✅ HTTP 403
- ✅ Archivo permanece intacto

## 🚀 Cómo Ejecutar

### Todos los tests de integración
```bash
docker-compose exec web python -m pytest tests/files/integration/ -v
```

### Suite específica
```bash
# Solo tests de storage limits
docker-compose exec web python -m pytest tests/files/integration/test_file_upload_views.py::TestFileUploadStorageLimits -v

# Solo tests de seguridad
docker-compose exec web python -m pytest tests/files/integration/test_file_upload_views.py::TestFileUploadPermissions -v
```

### Test individual
```bash
docker-compose exec web python -m pytest tests/files/integration/test_file_upload_views.py::TestFileUploadSuccess::test_upload_large_rar_file_successfully -v
```

### Con coverage
```bash
docker-compose exec web python -m pytest tests/files/integration/ --cov=apps.files.views --cov-report=html
```

## 🔍 Interpretando Resultados

### ✅ Test Pasó
```
tests/files/integration/test_file_upload_views.py::TestFileUploadSuccess::test_upload_pdf_file_successfully PASSED
```
**Significado:** El flujo completo funciona correctamente.

### ❌ Test Falló
```
tests/files/integration/test_file_upload_views.py::TestFileUploadStorageLimits::test_upload_rejected_when_storage_limit_exceeded FAILED
```
**Acción Requerida:**
1. Revisar logs del test: `assert response.status_code == 413` falló
2. Verificar configuración del plan en el test
3. Verificar lógica de `StorageService.can_upload_file()`
4. **NO ignorar este test** - es crítico para facturación

## 🐛 Por Qué Antes NO Fallaban

Los tests **antes NO existían**. Solo había tests unitarios que:
- Probaban modelos directamente (sin pasar por vistas)
- Probaban validadores aislados (sin integración completa)
- No probaban el flujo HTTP completo

**Resultado:** Los bugs en producción no se detectaban en tests:
- ✅ Bug de validación silenciosa: detectado ahora
- ✅ Bug de MIME type RAR: detectado ahora
- ✅ Logs excesivos en producción: detectado ahora

## 📊 Cobertura de Casos

| Caso | Unitario | Integración |
|------|----------|-------------|
| Modelo guarda archivo | ✅ | ✅ |
| Validación rechaza ejecutable | ✅ | ✅ |
| Storage limit excedido | ✅ | ✅ |
| Usuario recibe error HTTP 413 | ❌ | ✅ |
| Log estructurado correcto | ❌ | ✅ |
| Permisos cross-org | ⚠️ Parcial | ✅ |
| Flujo completo upload | ❌ | ✅ |

## 🎓 Mejores Prácticas

### 1. Ejecutar tests ANTES de deploy
```bash
# En CI/CD pipeline
docker-compose exec web python -m pytest tests/files/integration/ -v --maxfail=1
```

### 2. Si un test falla en producción
- ❌ NO ignorar o skip el test
- ✅ Reproducir el bug localmente
- ✅ Fix el código
- ✅ Verificar que el test pase
- ✅ Deploy con confianza

### 3. Agregar test cuando se encuentra un bug
- Bug de RAR 875MB → Test creado
- Bug futuro → Crear test primero (TDD)

## 🔗 Archivos Relacionados

- `arc_manager/apps/files/views.py` - Vista de upload (código bajo test)
- `arc_manager/apps/files/validators.py` - Validadores
- `arc_manager/apps/orgs/storage_service.py` - Lógica de storage
- `arc_manager/core/structured_logging.py` - Logging
- `tests/factories/files/` - Factories para crear objetos de test

## 🆘 Troubleshooting

### Test falla con `No module named 'pytest'`
```bash
docker-compose exec web pip install -r requirements.txt
```

### Test falla con `django.core.exceptions.ImproperlyConfigured`
```bash
# Verificar que estés usando use_local_storage fixture
def test_my_upload(self, use_local_storage):  # ← Importante
```

### Test pasa localmente pero falla en CI
- Verificar variables de entorno en CI
- Verificar que pytest esté instalado
- Verificar permisos de escritura en /tmp

## 📈 Próximos Tests a Agregar

- [ ] Upload de archivos ZIP con contenido malicioso
- [ ] Upload concurrente (race conditions)
- [ ] Upload con timeout de red
- [ ] Cleanup de archivos huérfanos
- [ ] Validación de checksums duplicados

