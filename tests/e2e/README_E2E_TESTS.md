# Tests E2E - Arc Manager

## Resumen

Este directorio contiene tests End-to-End (E2E) que simulan flujos completos de usuario utilizando Playwright para automatización de navegador.

## Estructura de Tests

```
tests/e2e/
├── conftest.py                  # Fixtures compartidos (usuarios, proyectos, archivos temporales)
├── test_login.py                # Tests de autenticación básica
├── test_project_flow.py         # Flujos de proyectos y tareas básicos
├── test_file_upload_e2e.py      # Subida y gestión de archivos
├── test_finance_flow.py         # Presupuestos y pagos básicos
├── test_user_management_e2e.py  # Gestión de usuarios
├── test_security_e2e.py         # Tests de seguridad
├── test_error_flows_e2e.py      # Manejo de errores
├── test_budget_flow.py          # 🆕 Flujo completo de presupuestos
├── test_payment_flow.py         # 🆕 Pagos con comprobantes adjuntos
├── test_kanban_flow.py          # 🆕 Tablero Kanban completo
├── test_client_template_flow.py # 🆕 Clientes y plantillas de fases
├── test_admin_panel.py          # 🆕 Panel de administración (superadmin)
├── test_limited_user_view.py    # 🆕 Vista de usuario limitado
└── screenshots/                 # Capturas en caso de fallo
```

## Categorías de Tests

### 🔐 Autenticación (`test_login.py`)
- Login exitoso/fallido
- Logout
- Campos vacíos

### 📁 Proyectos (`test_project_flow.py`)
- Listado de proyectos
- Creación de proyectos
- Detalle y pestañas
- Ciclo de vida completo
- Gestión de fases
- Tablero Kanban básico
- Tareas

### 📤 Archivos (`test_file_upload_e2e.py`)
- Subida de PDF e imágenes
- Validación de extensiones
- Archivos maliciosos rechazados
- Gestión de archivos
- Seguridad de archivos entre organizaciones

### 💰 Finanzas (`test_finance_flow.py`)
- Información de presupuesto
- Lista de pagos
- Creación de pagos básicos

### 💵 Presupuestos Completos (`test_budget_flow.py`) 🆕
- Configurar presupuesto desde cero
- Actualizar presupuesto existente
- Validación de valores negativos
- Dashboard de finanzas con múltiples proyectos
- Resumen de totales
- Detalle financiero de proyecto
- Cálculo de balance y progreso

### 💳 Pagos con Comprobantes (`test_payment_flow.py`) 🆕
- Crear pago desde dashboard de finanzas
- Crear pago desde detalle de proyecto
- Subir comprobante PDF adjunto
- Subir comprobante imagen (JPG) adjunto
- Editar pagos existentes
- Eliminar pagos
- Cálculo de totales de múltiples pagos
- Advertencia cuando pagos exceden presupuesto

### 📋 Kanban Completo (`test_kanban_flow.py`) 🆕
- Tablero Kanban con columnas de estado
- Tareas en columnas correctas
- Cambiar estado via selector
- Mover tareas entre fases
- Crear múltiples tareas
- Filtrar tareas por estado
- Vista "Mis Tareas" solo muestra asignadas
- Cambiar estado desde "Mis Tareas"
- Selector de proyecto para Kanban

### 👥 Usuarios (`test_user_management_e2e.py`)
- Cambio de contraseña obligatorio
- Gestión de usuarios por admin
- Reset de contraseña
- Perfil de usuario
- Gestión de sesión
- Permisos por rol

### 👤 Clientes y Plantillas (`test_client_template_flow.py`) 🆕
- Lista de clientes
- Crear nuevo cliente
- Editar cliente
- Toggle estado activo/inactivo
- Eliminar cliente
- Lista de plantillas de fases
- Crear plantilla de fases
- Ver detalle de plantilla
- Editar plantilla
- Eliminar plantilla
- Crear proyecto usando plantilla

### 🔧 Panel de Admin (`test_admin_panel.py`) 🆕
- Login de superadmin
- Usuario regular sin acceso al admin
- Ver solicitudes de upgrade pendientes
- Aprobar solicitud de upgrade
- Ver solicitudes de renovación
- Aprobar solicitud de renovación
- Ver lista de organizaciones
- Modificar almacenamiento extra de organización
- Activar/desactivar organización
- Ver lista de usuarios
- Crear usuario desde admin
- Ver y editar planes

### 👁️ Usuario Limitado (`test_limited_user_view.py`) 🆕
- Solo ve tareas asignadas a él
- Puede acceder al Kanban del proyecto
- Puede cambiar estado de sus tareas
- Puede completar sus tareas
- NO puede crear proyectos
- NO puede acceder a gestión de usuarios
- NO puede configurar presupuestos
- NO puede eliminar tareas
- Sidebar muestra opciones limitadas
- Puede ver su perfil
- Puede cambiar su contraseña

### 🛡️ Seguridad (`test_security_e2e.py`)
- Aislamiento de organizaciones (multi-tenant)
- Protección contra IDOR
- Tokens CSRF
- Validación de input (XSS, SQL injection)
- Rate limiting

### ⚠️ Errores (`test_error_flows_e2e.py`)
- Validación de formularios
- Errores de cuota/almacenamiento
- Estados de carga
- Manejo de operaciones fallidas
- Casos límite (caracteres especiales, Unicode)

## Ejecución

### Requisitos
- Docker y docker-compose
- Contenedor web corriendo

### Comandos

```bash
# Ejecutar todos los tests E2E
docker-compose exec web python -m pytest tests/e2e/ -v

# Ver el navegador mientras ejecuta (modo headed)
docker-compose exec web python -m pytest tests/e2e/ -v --headed

# Ejecutar un archivo específico
docker-compose exec web python -m pytest tests/e2e/test_login.py -v

# Ejecutar una clase específica
docker-compose exec web python -m pytest tests/e2e/test_security_e2e.py::TestOrganizationIsolation -v

# Ejecutar un test específico
docker-compose exec web python -m pytest tests/e2e/test_login.py::TestLoginFlow::test_login_success -v

# Solo recolectar tests (ver qué ejecutaría)
docker-compose exec web python -m pytest tests/e2e/ --collect-only

# Ejecutar con límite de fallos
docker-compose exec web python -m pytest tests/e2e/ -v --maxfail=5

# 🆕 Ejecutar tests de presupuestos
docker-compose exec web python -m pytest tests/e2e/test_budget_flow.py -v

# 🆕 Ejecutar tests de pagos con comprobantes
docker-compose exec web python -m pytest tests/e2e/test_payment_flow.py -v

# 🆕 Ejecutar tests de Kanban completo
docker-compose exec web python -m pytest tests/e2e/test_kanban_flow.py -v

# 🆕 Ejecutar tests de clientes y plantillas
docker-compose exec web python -m pytest tests/e2e/test_client_template_flow.py -v

# 🆕 Ejecutar tests del panel de admin
docker-compose exec web python -m pytest tests/e2e/test_admin_panel.py -v

# 🆕 Ejecutar tests de usuario limitado
docker-compose exec web python -m pytest tests/e2e/test_limited_user_view.py -v
```

## Fixtures Disponibles

### Usuarios
- `e2e_user` - Usuario principal con organización y suscripción activa (org_admin)
- `e2e_admin` - Superusuario para tests del admin de Django
- `e2e_second_user` - Segundo usuario en la misma organización
- `e2e_other_org_user` - Usuario de otra organización (para tests de aislamiento)
- `limited_user` - 🆕 Usuario limitado sin permisos de admin

### Sesión
- `logged_in_page` - Página de Playwright con sesión iniciada (org_admin)
- `admin_page` - Página autenticada como superadmin en Django Admin
- `logged_in_other_org_page` - Página con usuario de otra organización
- `logged_in_limited_page` - 🆕 Página con usuario limitado

### Datos
- `e2e_client` - Cliente asociado a la organización
- `e2e_project_with_phases` - Proyecto con fases y tareas

### Archivos Temporales
- `temp_pdf_file` - PDF de prueba
- `temp_image_file` - Imagen JPG de prueba
- `temp_png_file` - Imagen PNG de prueba
- `temp_malicious_file` - Archivo con extensión peligrosa
- `temp_large_file` - Archivo de 5MB
- `temp_receipt_pdf` - 🆕 PDF simulando comprobante de pago
- `temp_receipt_image` - 🆕 Imagen simulando comprobante de pago

### Helpers
- `upload_file_helper` - Función para subir archivos en tests
- `wait_for_toast` - Esperar y verificar mensajes toast/notificaciones

## Notas de Implementación

### Screenshots
Los tests automáticamente guardan screenshots cuando fallan en `tests/e2e/screenshots/`.

### Base de datos
Los tests usan `@pytest.mark.django_db(transaction=True)` para aislamiento.

### Timeouts
- Default timeout: 30 segundos
- Para operaciones lentas usar `page.wait_for_timeout(ms)`

### Selectores
Los tests usan selectores robustos que manejan:
- IDs específicos cuando existen (`#id_name`)
- Clases de Bootstrap (`.btn-primary`, `.modal`)
- Atributos data (`[data-bs-target]`)
- Texto visible (`text=Guardar`)

### PIL/Pillow (Opcional)
El fixture de imágenes funciona con o sin Pillow instalado, usando bytes raw como fallback.

## Estado Actual (Diciembre 2024)

- **Total tests**: ~150+ (88 originales + 60+ nuevos)
- **Archivos de test**: 13
- **Cobertura de flujos**: 
  - ✅ Autenticación y login
  - ✅ Proyectos y fases
  - ✅ Tareas y Kanban completo
  - ✅ Presupuestos y configuración financiera
  - ✅ Pagos con comprobantes adjuntos
  - ✅ Subida y gestión de archivos
  - ✅ Clientes y plantillas
  - ✅ Gestión de usuarios
  - ✅ Panel de admin (superadmin)
  - ✅ Vista de usuario limitado
  - ✅ Seguridad multi-tenant
  - ✅ Manejo de errores

## Flujos Completos Cubiertos 🆕

### Flujo de Presupuesto y Pagos
1. Crear proyecto sin presupuesto
2. Ir a dashboard de finanzas
3. Configurar presupuesto inicial
4. Crear pagos con comprobantes (PDF/imagen)
5. Ver balance y porcentaje de avance
6. Editar y eliminar pagos
7. Verificar cálculos de totales

### Flujo de Kanban Completo
1. Ver tablero con columnas (Todo, En Progreso, Hecho)
2. Crear múltiples tareas
3. Mover tareas entre estados
4. Filtrar por fase/asignado
5. Vista "Mis Tareas" para usuario

### Flujo de Usuario Limitado
1. Login como usuario no-admin
2. Solo ver tareas asignadas
3. Cambiar estado de tareas propias
4. Acceso restringido a secciones admin
5. No puede crear proyectos/usuarios

### Flujo de Admin Panel
1. Login como superadmin
2. Ver solicitudes pendientes (upgrades/renovaciones)
3. Aprobar/rechazar solicitudes
4. Gestionar organizaciones
5. Modificar límites de planes

## Mantenimiento

Al modificar la UI:
1. Verificar que los selectores CSS siguen siendo válidos
2. Actualizar fixtures si cambian los modelos
3. Revisar screenshots de tests fallidos para diagnóstico
