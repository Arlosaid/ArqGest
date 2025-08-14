# 📙 Guía de Usuario de ArcManager

Bienvenido a ArcManager. Esta guía te ayuda a trabajar día a día con la aplicación, sin tecnicismos. Incluye pasos detallados, flujos de trabajo, consejos, preguntas frecuentes y resolución de problemas.

## Índice
- Introducción y Acceso
- Navegación General de la App
- Roles y Permisos (qué puede hacer cada rol)
- Suscripción y Planes
- Proyectos y Tablero Kanban
- Tareas (creación, edición, seguimiento)
- Archivos (gestión por proyecto/fase)
- Usuarios (gestión de tu equipo)
- Clientes y Organización
- Notificaciones y Mensajes del Sistema
- Buenas Prácticas y Atajos
- Preguntas Frecuentes (FAQ)
- Troubleshooting (Resolución de Problemas)

---

## Introducción y Acceso
- URL de acceso: `http://localhost:8000/accounts/login/`.
- Ingresa tu correo y contraseña. Si olvidaste tu contraseña, usa “¿Olvidaste tu contraseña?” para recibir un correo de recuperación.
- Al iniciar sesión verás el panel principal con accesos a Proyectos, Mis Tareas, Usuarios, Clientes y Planes.

### Cierre de sesión
- En el menú superior, elige “Cerrar sesión”. La aplicación limpiará mensajes y tu sesión de manera segura.

---

## Navegación General de la App
- Menú izquierdo: acceso a módulos (Proyectos, Mis Tareas, Usuarios, Clientes, Planes).
- Contenido principal: vistas, listas, formularios y tableros.
- Sidebar contextual: acciones rápidas e información relacionada cuando aplique.

Consejo: Mantén el navegador actualizado. La app funciona en Chrome, Edge y Firefox recientes.

---

## Roles y Permisos
- Usuario estándar: puede ver y trabajar en los proyectos y tareas a los que tenga acceso en su organización.
- Administrador de organización (org_admin): además, puede gestionar usuarios de su organización, clientes y solicitar mejoras de plan.

Nota: Algunas acciones (crear usuarios, solicitar actualización de plan, editar datos de organización) requieren rol de administrador de organización.

---

## Suscripción y Planes
- Revisa el estado en Menú → Plans → “Mi Suscripción”.
- Verás el plan actual, días restantes, estado (activo, prueba, gracia o expirado) y uso de recursos.
- Si eres administrador de organización, puedes solicitar una actualización en “Solicitar actualización”.

Casos comunes:
- Si tu plan está en prueba y quedan pocos días, se mostrará un mensaje motivador para actualizar sin perder el ritmo de trabajo.
- Si hay una solicitud pendiente, verás su estado y próximos pasos.

Más detalles: consulta `docs/usuario/planes.md`.

---

## Proyectos y Tablero Kanban
- Crea un proyecto desde Proyectos → “Crear nuevo proyecto”.
- Dentro de un proyecto, encontrarás pestañas de Fases, Tareas, Archivos y el Tablero Kanban.
- En el tablero, arrastra y suelta tareas entre columnas para cambiar su fase/estado.

Más detalles: consulta `docs/usuario/proyectos.md`.

---

## Tareas (creación, edición, seguimiento)
- Crea tareas desde la pestaña Tareas del proyecto. Si no hay fases, se creará una fase inicial.
- Edita tareas desde el modal de detalle: título, descripción, responsable, prioridad, fechas y estado/fase.
- Reordena o mueve tareas en el tablero Kanban según el flujo del proyecto.

Más detalles: consulta `docs/usuario/tareas.md`.

---

## Archivos (gestión por proyecto/fase)
- En cada proyecto, pestaña Archivos: sube, lista y elimina archivos asociados a una fase.
- Usa nombres claros para facilitar la búsqueda.

---

## Usuarios (gestión de tu equipo)
- Menú → Users: lista de miembros de tu organización.
- Administradores de organización pueden crear, editar, desactivar o eliminar usuarios.
- Al crear un usuario, usa un correo válido para el envío de credenciales y recuperación.

Más detalles: consulta `docs/usuario/usuarios.md`.

---

## Clientes y Organización
- Menú → Organizations → Clients: gestiona clientes (crear, editar, eliminar).
- Menú → Organizations → Mi organización: consulta datos de tu empresa y tu plan.

Más detalles: consulta `docs/usuario/clientes_y_organizacion.md`.

---

## Notificaciones y Mensajes del Sistema
- Mensajes de éxito: confirmación de acciones realizadas.
- Advertencias: límites del plan, acciones restringidas o información importante.
- Errores: faltan datos, permisos insuficientes o problemas puntuales.

Sugerencia: lee siempre los mensajes mostrados en la parte superior o en el contexto de la vista.

---

## Buenas Prácticas y Atajos
- Proyectos: usa nombres y descripciones claras.
- Tareas: define prioridad y fecha; añade descripciones útiles.
- Kanban: revisa diariamente el flujo de tarjetas entre columnas.
- Búsqueda: usa los filtros de listas para encontrar más rápido.

---

## Preguntas Frecuentes (FAQ)
- No veo Proyectos o Usuarios: verifica tu rol; algunas acciones requieren ser administrador de organización.
- No puedo mover una tarea: asegúrate de tener permisos y que la tarea no esté bloqueada por reglas del flujo.
- No encuentro el tablero Kanban: abre el detalle del proyecto y la pestaña Kanban.
- No puedo solicitar actualización de plan: debes ser administrador de organización.

---

## Troubleshooting (Resolución de Problemas)
- No puedo iniciar sesión: verifica correo/contraseña. Si persiste, usa “Olvidé mi contraseña”.
- No llega el correo de recuperación: revisa SPAM y espera unos minutos; hay una limitación temporal por seguridad.
- Bucle de redirecciones: cierra sesión, limpia cookies del sitio y vuelve a iniciar.
- No puedo crear usuarios: valida tu rol y si tu plan alcanzó el límite de usuarios.

---

ArcManager · Guía de Usuario · Última actualización: 2025-08-13
