// Backdrop translúcido con efecto de desenfoque para todos los modales via CSS-injected class
(function applyModalBackdropStyles() {
  const style = document.createElement('style');
  style.textContent = `
    .modal-backdrop {
      background-color: rgba(255, 255, 255, 0.18) !important;
      backdrop-filter: blur(8px) saturate(120%);
      -webkit-backdrop-filter: blur(8px) saturate(120%);
    }
    .modal-backdrop.show { opacity: 1 !important; }
  `;
  document.head.appendChild(style);
})();

// Helper global para abrir el modal con contenido remoto
window.openAppModal = async function(url, title = '') {
  try {
    const modalEl = document.getElementById('appModal');
    const bodyEl = document.getElementById('appModalBody');
    const titleEl = document.getElementById('appModalTitle');
    if (!modalEl || !bodyEl) return;
    titleEl.textContent = title || '';
    bodyEl.innerHTML = '<div class="text-center p-4"><i class="fas fa-spinner fa-spin fa-2x"></i><p class="mt-2">Cargando...</p></div>';
    const res = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
    const html = await res.text();
    bodyEl.innerHTML = html;
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();
  } catch (e) {
    console.error(e);
    const bodyEl = document.getElementById('appModalBody');
    if (bodyEl) bodyEl.innerHTML = '<div class="text-center p-4 text-danger"><i class="fas fa-exclamation-triangle fa-2x"></i><p class="mt-2">Error al cargar</p></div>';
  }
}

// Delegación de clicks para cualquier elemento con data-modal-url
document.addEventListener('click', function(e) {
  const trigger = e.target.closest('[data-modal-url]');
  if (!trigger) return;
  e.preventDefault();
  const url = trigger.getAttribute('data-modal-url');
  const title = trigger.getAttribute('data-modal-title') || '';
  if (url) {
    // Si la URL es de tareas, usar el modal universal de tareas
    if (url.includes('/projects/tasks/') && (url.endsWith('/') || url.includes('/edit/'))) {
      const taskIdMatch = url.match(/\/projects\/tasks\/(\d+)\//);
      if (taskIdMatch) {
        const taskId = taskIdMatch[1];
        const type = url.includes('/edit/') ? 'edit' : 'detail';
        window.openTaskModal(type, taskId);
        return;
      }
    }
    // Para otras URLs, usar el modal general
    window.openAppModal(url, title);
  }
});

