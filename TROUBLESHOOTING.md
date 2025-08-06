# Guía de Solución de Errores Comunes (Troubleshooting)

Este documento centraliza los errores comunes encontrados durante el desarrollo del proyecto ArcManager, sus causas y las soluciones aplicadas. El objetivo es acelerar la resolución de problemas futuros y compartir el conocimiento adquirido.

---

### 1. `ImportError` en Vistas de Django

-   **Error:** `ImportError: cannot import name 'NombreDeLaVista' from 'apps.mi_app.views'`

-   **Causa Raíz:** Ocurre cuando un archivo de URLs (`urls.py`) intenta importar una vista (ya sea una clase o una función) desde un archivo `views.py`, pero esa vista no se encuentra. Las razones más comunes son:
    -   La vista fue eliminada del archivo `views.py`.
    -   Se le cambió el nombre a la vista, pero no se actualizó la importación en `urls.py`.
    -   El archivo `views.py` no se guardó correctamente y los cambios no están presentes.

-   **Solución:**
    1.  Abrir el archivo `urls.py` que genera el error y revisar el nombre de la vista que se está importando.
    2.  Abrir el archivo `views.py` correspondiente y verificar si la vista realmente existe con ese nombre exacto.
    3.  Si no existe, se debe recrear la estructura básica de la vista. Si fue renombrada, se debe corregir el nombre en la importación de `urls.py`.

-   **¿Se volverá a presentar?** Sí. Es un error de desarrollo común. Puede ocurrir en cualquier momento que se refactoricen o modifiquen vistas y URLs. La prevención es ser metódico y verificar siempre que los `import` coincidan con las definiciones.

---

### 2. `SystemCheckError` en el Admin de Django

-   **Error:** `(admin.E108) The value of 'list_display[n]' refers to 'mi_campo', which is not a callable or attribute of 'MiModelo'`. Ocurre también con `readonly_fields`.

-   **Causa Raíz:** La configuración del panel de administración (`admin.py`) para un modelo hace referencia a un campo que no existe en la definición de ese modelo en `models.py`.

-   **Solución:**
    1.  Identificar el modelo (`MiModelo`) y el campo (`mi_campo`) que señala el error.
    2.  Abrir el archivo `apps/mi_app/models.py` y buscar la clase del modelo para verificar los nombres de todos sus campos.
    3.  Abrir `apps/mi_app/admin.py` y corregir las tuplas `list_display` y `readonly_fields` en la clase de admin correspondiente, eliminando o corrigiendo los nombres de los campos que no existen.

-   **¿Se volverá a presentar?** Sí. Al igual que el `ImportError`, es un error de desarrollo que aparece si se modifican los campos de un modelo sin actualizar su representación en el panel de administración.

---

### 3. `TypeError` por Incompatibilidad de Dependencias

-   **Error:** `TypeError: AbstractConnection.__init__() got an unexpected keyword argument 'CLIENT_CLASS'`

-   **Causa Raíz:** Este error tiene dos causas combinadas:
    1.  **Incompatibilidad de Versiones:** La versión de `django-redis` es incompatible con la versión de la librería `redis`.
    2.  **Configuración Incorrecta:** Se está utilizando el backend de caché nativo de Django (`django.core.cache.backends.redis.RedisCache`) pero con opciones (`CLIENT_CLASS`) que son específicas de `django-redis`.

-   **Solución:**
    1.  **Ajustar Versiones:** Modificar `requirements.txt` para usar versiones compatibles. En nuestro caso, se cambió `redis` a `3.5.3` que funciona con `django-redis==5.4.0`.
    2.  **Corregir `settings.py`:**
        - Cambiar el `BACKEND` de caché a `django_redis.cache.RedisCache`.
        - Eliminar la opción `CLIENT_CLASS` de la configuración de `CACHES`, ya que no es necesaria con las versiones actualizadas y el backend correcto.
    3.  **Reconstruir y Reiniciar:**
        - Reconstruir la imagen de Docker para instalar las dependencias correctas: `docker-compose build`.
        - Reiniciar los servicios para que tomen la nueva configuración: `docker-compose restart`.

-   **¿Se volverá a presentar?** Este error específico no debería volver a ocurrir mientras no se cambien las versiones en `requirements.txt`. Sin embargo, **errores de incompatibilidad de versiones pueden ocurrir siempre que se actualicen dependencias**. La mejor forma de prevenirlo es actualizar las librerías de una en una y probar la aplicación, o usar herramientas más avanzadas como `pip-tools` o `poetry` para gestionar las dependencias.

---

### 4. Fallo en la Construcción de Docker (`failed to execute bake`)

-   **Error:** Al ejecutar `docker-compose build` o `docker-compose up --build`, el proceso falla con el mensaje `failed to execute bake: read |0: file already closed`.

-   **Causa Raíz:** Generalmente es un bug o un estado inconsistente en el motor de Docker Desktop, y no un problema del código del proyecto. A menudo está relacionado con una característica de Docker llamada "BuildKit", especialmente en sistemas Windows.

-   **Solución:**
    1.  **Reiniciar Docker Desktop:** Es la solución más simple y efectiva. Haz clic derecho en el icono de la ballena de Docker en la bandeja del sistema y selecciona "Restart".
    2.  **Detener y limpiar:** Ejecutar `docker-compose down` para detener y eliminar los contenedores antes de intentar reconstruir.
    3.  **Desactivar BuildKit (si lo anterior falla):** Ejecutar el comando de construcción precedido por una variable de entorno.
        -   En PowerShell (Windows): `$env:DOCKER_BUILDKIT=0; docker-compose build`
        -   En Bash (Linux/macOS): `DOCKER_BUILDKIT=0 docker-compose build`

-   **¿Se volverá a presentar?** Posiblemente. Al ser un problema del entorno de Docker, puede reaparecer. Si ocurre con frecuencia, se puede considerar desactivar BuildKit de forma permanente en la configuración de Docker o investigar si hay una actualización de Docker Desktop que lo solucione.

---

### 5. Error 404 `Page Not Found` después del Login

-   **Error:** Después de un login exitoso, se redirige a una URL incorrecta como `/accounts/login/main/`, resultando en un error 404.

-   **Causa Raíz:** El `LoginRequiredMiddleware` estaba generando una URL de redirección con un parámetro `next` relativo (ej. `?next=main/`) en lugar de absoluto. La vista de Login de Django, al procesar esta ruta relativa, la concatena con la URL actual (`/accounts/login/`), creando una URL inválida.

-   **Solución:**
    1.  Modificar `apps/accounts/middleware.py`.
    2.  En la clase `LoginRequiredMiddleware`, cambiar la línea de redirección para que siempre anteponga una barra (`/`) al path, asegurando que el parámetro `next` sea siempre una ruta absoluta.
    3.  Línea modificada: `return redirect(f'{self.login_url}?next=/{path}')`
    4.  Reiniciar los servicios con `docker-compose restart` para que el cambio en el middleware sea aplicado.

-   **¿Se volverá a presentar?** No. La corrección en el middleware es robusta y previene que se generen rutas relativas en el futuro.
