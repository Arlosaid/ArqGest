// Utilidades del tablero Kanban migradas desde el template
function clearFilters() { window.location.href = window.location.pathname; }
function refreshKanban() { location.reload(); }

// La función openTaskModal está definida globalmente en base.js

document.addEventListener('DOMContentLoaded', function() {
  const cards = document.querySelectorAll('.kanban-card');
  cards.forEach(card => {
    card.addEventListener('dragstart', handleDragStart);
    card.addEventListener('dragend', handleDragEnd);
  });
  const columns = document.querySelectorAll('.kanban-column-body');
  columns.forEach(column => {
    column.addEventListener('dragover', handleDragOver);
    column.addEventListener('drop', handleDrop);
  });
  
  // Listeners para eventos de actualización de tareas
  document.addEventListener('taskUpdated', function() {
    // Recargar el kanban cuando se actualiza una tarea
    setTimeout(() => location.reload(), 500);
  });
  
  document.addEventListener('taskCreated', function() {
    // Recargar el kanban cuando se crea una tarea
    setTimeout(() => location.reload(), 500);
  });
  
  // Manejador para eliminar tareas
  document.addEventListener('click', async function (e) {
    const btn = e.target.closest('[data-action="delete-task"][data-task-id]');
    if (!btn) return;
    e.preventDefault();
    const taskId = btn.getAttribute('data-task-id');
    if (!taskId) return;

    // Obtener información de la tarea para el modal
    const taskElement = document.querySelector(`[data-task-id="${taskId}"]`);
    const taskTitle = taskElement?.querySelector('.task-title')?.textContent?.trim() || 
                      taskElement?.textContent?.trim() || 
                      'esta tarea';

    // Mostrar modal de confirmación usando el sistema unificado
    ConfirmationModals.deleteTask({
        taskId: taskId,
        taskTitle: taskTitle,
        taskDescription: '',
        onConfirm: async () => {
            await performTaskDeletionFromKanban(taskId);
        }
    });
  });

  async function performTaskDeletionFromKanban(taskId) {
    try {
      const res = await fetch(`/projects/tasks/${taskId}/delete/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': (document.querySelector('[name=csrfmiddlewaretoken]')||{}).value || '' }
      });
      const ok = res.ok;
      if (ok) {
        // Buscar el elemento de tarea (puede ser tr, div, etc.)
        const taskElement = document.querySelector(`[data-task-id="${taskId}"]`);
        if (taskElement) {
          // Añadir animación de salida
          taskElement.style.transition = 'all 0.3s ease';
          taskElement.style.opacity = '0';
          taskElement.style.transform = 'scale(0.8)';
          setTimeout(() => {
            taskElement.remove();
            
            // Verificar si la columna está vacía y mostrar mensaje
            const column = taskElement.closest('.kanban-column-body');
            if (column && column.children.length === 0) {
              column.innerHTML = '<div class="empty-column"><div class="empty-state"><i class="fas fa-drafting-compass"></i><p>No hay tareas</p></div></div>';
            }
          }, 300);
        }
        
        // Disparar evento para que otras partes de la app se actualicen
        document.dispatchEvent(new CustomEvent('taskDeleted', { detail: { taskId } }));
        
        if (window.notifications) {
          window.notifications.success('Tarea eliminada correctamente');
        }
      } else {
        if (window.notifications) {
          window.notifications.error('Error al eliminar');
        }
      }
    } catch (err) {
      console.error(err);
      if (window.notifications) {
        window.notifications.error('Error al eliminar');
      }
    }
  }
});

function handleDragStart(e) { e.target.classList.add('dragging'); e.dataTransfer.setData('text/plain', e.target.dataset.taskId); }
function handleDragEnd(e) { e.target.classList.remove('dragging'); }
function handleDragOver(e) { e.preventDefault(); }
function handleDrop(e) { e.preventDefault(); const taskId = e.dataTransfer.getData('text/plain'); const newStatus = e.target.closest('.kanban-column-body').dataset.statusCode; updateTaskStatus(taskId, newStatus); }

function updateTaskStatus(taskId, newStatus) {
  const urlTemplate = document.body.dataset.updateTaskStatusUrlTemplate || '';
  const url = urlTemplate.replace('0', taskId);
  fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': (document.querySelector('[name=csrfmiddlewaretoken]')||{}).value || '' }, body: JSON.stringify({ status: newStatus }) })
    .then(r => r.json()).then(data => { 
      if (data.success) {
        location.reload();
      } else {
        if (window.notifications) {
          window.notifications.error('Error al actualizar la tarea');
        }
      }
    })
    .catch(() => {
      if (window.notifications) {
        window.notifications.error('Error al actualizar la tarea');
      }
    });
}
