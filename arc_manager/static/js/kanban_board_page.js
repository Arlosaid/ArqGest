// Utilidades del tablero Kanban migradas desde el template
function clearFilters() { window.location.href = window.location.pathname; }
function refreshKanban() { location.reload(); }

function openTaskModal(type, taskId) {
  const modal = new bootstrap.Modal(document.getElementById('taskUniversalModal'));
  const modalContent = document.getElementById('taskUniversalContent');
  const modalTitle = document.getElementById('taskUniversalModalLabel');
  if (type === 'edit') modalTitle.textContent = 'Editar Tarea';
  else if (type === 'detail') modalTitle.textContent = 'Detalles de la Tarea';
  modalContent.innerHTML = '<div class="text-center p-4"><i class="fas fa-spinner fa-spin fa-2x text-primary"></i><p class="mt-2 text-muted">Cargando...</p></div>';
  modal.show();
  let url = '';
  try {
    if (type === 'edit') url = (document.body.dataset.taskEditUrlTemplate || '').replace('0', taskId);
    else if (type === 'detail') url = (document.body.dataset.taskDetailUrlTemplate || '').replace('0', taskId);
  } catch (_) {}
  if (!url) return;
  fetch(url).then(r => { if (!r.ok) throw new Error('Network response was not ok'); return r.text(); })
    .then(html => { modalContent.innerHTML = html; })
    .catch(() => { modalContent.innerHTML = '<div class="text-center p-4 text-danger"><i class="fas fa-exclamation-triangle fa-2x mb-3"></i><h5>Error al cargar</h5><p class="text-muted">No se pudo cargar el contenido. Inténtalo de nuevo.</p></div>'; });
}

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

