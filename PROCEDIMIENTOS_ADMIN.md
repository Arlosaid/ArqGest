# Guía de Procedimientos Administrativos de ArcManager

Este documento es una guía de referencia rápida para los administradores del sistema. Contiene instrucciones paso a paso sobre cómo realizar tareas de gestión comunes y resolver problemas específicos utilizando las herramientas del panel de administración de Django.

---

## Gestión de Usuarios

### ¿Cómo forzar el cambio de contraseña de un usuario?

Este procedimiento es útil si un usuario ha perdido el acceso a su correo o no puede completar el flujo de reseteo de contraseña por sí mismo.

1.  **Ir al Admin:** Accede al panel de administración (`/admin/`).
2.  **Navegar a "Usuarios":** En el menú de la izquierda, haz clic en "Users".
3.  **Seleccionar el Usuario:** Busca y selecciona al usuario que necesita el cambio de contraseña.
4.  **Ejecutar la Acción:**
    *   En la lista de usuarios, marca la casilla junto al usuario correspondiente.
    *   En el menú desplegable "Acción", selecciona **"🔑 Forzar cambio de contraseña"**.
    *   Haz clic en el botón "Ir".
5.  **Obtener y Enviar el Enlace:**
    *   El sistema mostrará un mensaje en la parte superior con un enlace de reseteo único para ese usuario.
    *   Copia este enlace y envíaselo al usuario de forma segura (por ejemplo, a través de un chat privado o un correo electrónico secundario). El enlace es de un solo uso.

---

## Gestión de Suscripciones y Planes

### ¿Cómo extender manualmente la suscripción de una organización?

Usa este procedimiento para añadir días a una suscripción existente, ya sea como bonificación, para corregir un error de pago o por cualquier otra razón administrativa.

1.  **Ir a "Suscripciones":** En el panel de administración, ve a la sección "Plans" -> "Suscripciones".
2.  **Seleccionar la Suscripción:** Busca y selecciona la suscripción de la organización que deseas extender.
3.  **Ejecutar la Acción:**
    *   Marca la casilla junto a la suscripción.
    *   En el menú "Acción", elige **"🗓️ Extender suscripción manualmente"**.
    *   Haz clic en "Ir".
4.  **Completar el Formulario:**
    *   Serás redirigido a una página intermedia.
    *   **Días a extender:** Introduce el número de días que deseas añadir.
    *   **Razón (Opcional):** Describe brevemente por qué estás extendiendo la suscripción. Esto quedará registrado para futuras referencias.
    *   Haz clic en **"Aplicar Extensión"**.
5.  **Verificación:** El sistema te devolverá a la lista de suscripciones con un mensaje de éxito. La fecha de vencimiento se habrá actualizado.

### ¿Cómo cambiar el plan de una organización?

Este procedimiento permite mover a una organización de un plan a otro (por ejemplo, de "Básico" a "Trial" o viceversa) de forma inmediata.

1.  **Ir a "Suscripciones":** Navega a la sección "Plans" -> "Suscripciones".
2.  **Seleccionar la Suscripción:** Marca la casilla de la suscripción cuyo plan quieres cambiar.
3.  **Ejecutar la Acción:**
    *   En el menú "Acción", selecciona **"🔄 Cambiar plan manualmente"**.
    *   Haz clic en "Ir".
4.  **Seleccionar el Nuevo Plan:**
    *   En la página intermedia, usa el menú desplegable para elegir el nuevo plan para la organización.
    *   Haz clic en **"Aplicar Cambio de Plan"**.
5.  **Verificación:** La suscripción se actualizará instantáneamente al nuevo plan, y sus fechas de inicio/fin se reiniciarán según la configuración del nuevo plan.

---

## Gestión Masiva de Datos (Importación y Exportación)

El sistema utiliza `django-import-export` para permitir la gestión de datos en bloque a través de archivos CSV, Excel, etc.

### ¿Cómo exportar datos?

1.  **Navegar al Modelo:** Ve a la lista de los datos que deseas exportar (ej. "Users", "Organizations", "Plans").
2.  **Hacer clic en "Exportar":** En la parte superior de la lista, verás un botón "Exportar".
3.  **Seleccionar Formato:** Elige el formato de archivo que prefieras (CSV es el más común) y haz clic en "Enviar". El archivo se descargará a tu ordenador.

### ¿Cómo importar datos (para crear o actualizar)?

La importación es una herramienta muy potente pero debe usarse con cuidado. Siempre se recomienda hacer una "Prueba de importación" (dry run) antes de aplicar los cambios reales.

1.  **Preparar el Archivo:** La forma más segura de preparar un archivo de importación es **exportar primero** los datos existentes. Esto te dará un archivo con las columnas y el formato correctos.
    *   Para **actualizar** registros, asegúrate de que la columna `id` esté presente y contenga los IDs correctos de los objetos que quieres modificar.
    *   Para **crear** nuevos registros, puedes dejar la columna `id` en blanco.
2.  **Navegar al Modelo:** Ve a la lista correspondiente (ej. "Users").
3.  **Hacer clic en "Importar":** En la parte superior, haz clic en el botón "Importar".
4.  **Subir el Archivo:** Selecciona tu archivo y el formato correcto.
5.  **Realizar Prueba de Importación (Dry Run):**
    *   **¡MUY IMPORTANTE!** Antes de importar, haz clic en el botón **"Prueba de importación"**.
    *   El sistema analizará el archivo y te mostrará una vista previa de los cambios (qué filas se crearán, actualizarán o se omitirán) sin aplicarlos. Revisa cuidadosamente esta vista previa para asegurarte de que todo es correcto.
6.  **Realizar Importación Real:**
    *   Si la prueba fue exitosa, vuelve a la página de importación y esta vez haz clic en **"Enviar"**. Los cambios se aplicarán a la base de datos.
