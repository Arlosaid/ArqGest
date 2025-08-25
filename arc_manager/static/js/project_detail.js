// Control robusto de pestañas y utilidades de Project Detail
document.addEventListener('DOMContentLoaded', function () {
  
  // Función para manejar el filtrado de archivos mejorado
  function setupFileFiltering() {
    const fileTypeFilters = document.querySelectorAll('[id^="fileTypeFilter-"]');
    const fileDateFilters = document.querySelectorAll('[id^="fileDateFilter-"]');
    const clearFilterButtons = document.querySelectorAll('[id^="clearFilters-"]');
    
    // Configurar filtros por tipo
    fileTypeFilters.forEach(filter => {
      const phaseId = filter.id.replace('fileTypeFilter-', '');
      setupFilterLogic(phaseId);
      filter.addEventListener('change', () => applyAllFilters(phaseId));
    });
    
    // Configurar filtros por fecha
    fileDateFilters.forEach(filter => {
      const phaseId = filter.id.replace('fileDateFilter-', '');
      filter.addEventListener('change', () => applyAllFilters(phaseId));
    });
    
    // Configurar botones de limpiar filtros
    clearFilterButtons.forEach(button => {
      const phaseId = button.id.replace('clearFilters-', '');
      button.addEventListener('click', () => clearAllFilters(phaseId));
    });
  }
  
  function setupFilterLogic(phaseId) {
    // Esta función se ejecuta una vez por fase para configurar la lógica
  }
  
  function applyAllFilters(phaseId) {
    const tableBody = document.getElementById(`filesTableBody-${phaseId}`);
    const typeFilter = document.getElementById(`fileTypeFilter-${phaseId}`);
    const dateFilter = document.getElementById(`fileDateFilter-${phaseId}`);
    
    if (!tableBody || !typeFilter || !dateFilter) return;
    
    const selectedTypes = typeFilter.value;
    const selectedDateFilter = dateFilter.value;
    const rows = tableBody.querySelectorAll('.file-row');
    
    // Obtener fechas para comparación
    const today = new Date();
    const startOfWeek = new Date(today);
    startOfWeek.setDate(today.getDate() - today.getDay());
    const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    
    rows.forEach(row => {
      const fileType = row.getAttribute('data-file-type');
      const fileDate = new Date(row.getAttribute('data-file-date'));
      let showRow = true;
      
      // Filtro por tipo
      if (selectedTypes && selectedTypes.trim() !== '') {
        const allowedTypes = selectedTypes.split(',').map(t => t.trim().toUpperCase());
        if (!allowedTypes.includes(fileType.toUpperCase())) {
          showRow = false;
        }
      }
      
      // Filtro por fecha
      if (showRow && selectedDateFilter && selectedDateFilter.trim() !== '') {
        switch (selectedDateFilter) {
          case 'today':
            showRow = fileDate.toDateString() === today.toDateString();
            break;
          case 'week':
            showRow = fileDate >= startOfWeek && fileDate <= today;
            break;
          case 'month':
            showRow = fileDate >= startOfMonth && fileDate <= today;
            break;
          case 'older':
            showRow = fileDate < startOfMonth;
            break;
        }
      }
      
      row.style.display = showRow ? '' : 'none';
    });
    
    // Actualizar contador de archivos visibles
    updateFileCounter(phaseId, rows, selectedTypes || selectedDateFilter);
  }
  
  function updateFileCounter(phaseId, rows, hasActiveFilter) {
    const badge = document.querySelector(`#fileTypeFilter-${phaseId}`).closest('.row').querySelector('.badge');
    if (!badge) return;
    
    const totalFiles = rows.length;
    const visibleFiles = Array.from(rows).filter(row => row.style.display !== 'none').length;
    
    if (hasActiveFilter && hasActiveFilter.trim() !== '') {
      badge.textContent = `${visibleFiles} de ${totalFiles} archivos`;
      badge.className = 'badge bg-info';
    } else {
      badge.textContent = `${totalFiles} archivo${totalFiles !== 1 ? 's' : ''}`;
      badge.className = 'badge bg-primary';
    }
  }
  
  function clearAllFilters(phaseId) {
    const typeFilter = document.getElementById(`fileTypeFilter-${phaseId}`);
    const dateFilter = document.getElementById(`fileDateFilter-${phaseId}`);
    const tableBody = document.getElementById(`filesTableBody-${phaseId}`);
    
    if (typeFilter) typeFilter.value = '';
    if (dateFilter) dateFilter.value = '';
    
    if (tableBody) {
      const rows = tableBody.querySelectorAll('.file-row');
      rows.forEach(row => {
        row.style.display = '';
      });
      
      // Actualizar contador
      updateFileCounter(phaseId, rows, '');
    }
  }
  
  // Ejecutar después de que la página se cargue completamente
  setTimeout(setupFileFiltering, 100);
  
  // También ejecutar cuando se actualice contenido HTMX
  document.body.addEventListener('htmx:afterSwap', setupFileFiltering);
  const tabContainer = document.getElementById('projectTab');
  const panes = Array.from(document.querySelectorAll('#projectTabContent .tab-pane'));
  if (!tabContainer || panes.length === 0) return;

  const showTabById = (paneId) => {
    tabContainer.querySelectorAll('.nav-link').forEach(b => b.classList.remove('active'));
    const btn = tabContainer.querySelector(`button[data-bs-target="#${paneId}"]`);
    if (btn) btn.classList.add('active');
    panes.forEach(p => p.classList.remove('show', 'active'));
    const pane = document.getElementById(paneId);
    if (pane) pane.classList.add('show', 'active');
  };

  let initial = 'details';
  try {
    const params = new URLSearchParams(window.location.search);
    const q = (params.get('tab') || '').toLowerCase();
    const h = (window.location.hash || '').replace('#', '').toLowerCase();
    initial = q || h || 'details';
  } catch (_) {}
  if (!['details', 'phases', 'kanban', 'files'].includes(initial)) initial = 'details';
  showTabById(initial);

  tabContainer.addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-bs-target]');
    if (!btn) return;
    const id = btn.getAttribute('data-bs-target').replace('#', '');
    showTabById(id);
  });

  tabContainer.addEventListener('shown.bs.tab', (e) => {
    const id = e.target?.getAttribute('data-bs-target')?.replace('#', '');
    if (id) showTabById(id);
  });

  const kanbanTab = document.getElementById('kanban-tab');
  if (kanbanTab) {
    kanbanTab.addEventListener('click', function () {
      showTabById('kanban');
    });
  }

  document.addEventListener('click', async function (e) {
    const btn = e.target.closest('[data-action="delete-task"][data-task-id]');
    if (!btn) return;
    e.preventDefault();
    const taskId = btn.getAttribute('data-task-id');
    if (!taskId) return;
    if (!confirm('¿Eliminar esta tarea?')) return;
    try {
      const res = await fetch(`/projects/tasks/${taskId}/delete/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': (document.querySelector('[name=csrfmiddlewaretoken]')||{}).value || '' }
      });
      const ok = res.ok;
      if (ok) {
        const row = document.querySelector(`tr[data-task-id="${taskId}"]`);
        if (row) row.remove();
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
  });

  const phaseFilter = document.getElementById('phaseFilter');
  if (phaseFilter) {
    phaseFilter.addEventListener('change', () => {
      const selected = phaseFilter.value;
      const cards = document.querySelectorAll('#compactTasksGrid .task-compact-card');
      cards.forEach(card => {
        const phaseId = card.getAttribute('data-phase-id');
        card.style.display = (!selected || selected === phaseId) ? '' : 'none';
      });
    });
  }
});

