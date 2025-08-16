// ===== TASK EDIT MODAL - FUNCIONALIDADES =====

// Manejo de respuesta HTMX para cerrar el modal global y refrescar UI
document.addEventListener('htmx:afterOnLoad', function (e) {
  try {
    const xhr = e.detail.xhr;
    const contentType = xhr.getResponseHeader('Content-Type') || '';
    if (contentType.includes('application/json')) {
      const data = JSON.parse(xhr.responseText || '{}');
      if (data && data.success && data.task) {
        // Cerrar modal global si existe
        const appModalEl = document.getElementById('appModal');
        if (appModalEl && window.bootstrap) {
          const modal = bootstrap.Modal.getInstance(appModalEl) || new bootstrap.Modal(appModalEl);
          modal.hide();
        }
        // Actualizar tarjeta Kanban si está presente
        const card = document.querySelector('.kanban-card[data-task-id="' + data.task.id + '"]');
        if (card) {
          const titleEl = card.querySelector('.task-title');
          if (titleEl) titleEl.textContent = data.task.title;
          const assigneeEl = card.querySelector('.task-assignee span');
          if (assigneeEl) assigneeEl.textContent = data.task.assigned_to_name || assigneeEl.textContent;
          const phaseBadge = card.querySelector('.phase-badge');
          if (phaseBadge && data.task.phase_name) phaseBadge.textContent = data.task.phase_name;
        }
        // Actualizar item en "Mis Tareas" si está presente
        const listItem = document.querySelector('.task-item[data-task-id="' + data.task.id + '"]');
        if (listItem) {
          const title = listItem.querySelector('.task-title');
          if (title) title.textContent = data.task.title;
        }
      }
    }
  } catch (_) {}
});
