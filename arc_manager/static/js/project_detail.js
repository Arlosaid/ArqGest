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

  // NOTA: La eliminación de tareas ahora es manejada por task-delete.js (sistema unificado)
  // No necesitamos un listener duplicado aquí que cause dobles modales

  // Configurar paginación de tareas responsive
  function setupTasksPagination() {
    const tasksContainer = document.getElementById('tasksContainer');
    if (!tasksContainer) return;

    const projectId = tasksContainer.getAttribute('data-project-id');
    const paginatedUrl = tasksContainer.getAttribute('data-paginated-url');
    if (!projectId || !paginatedUrl) return;

    // Detectar si es móvil usando media query
    const isMobile = () => window.matchMedia('(max-width: 768px)').matches;
    
    // Función para cargar página
    async function loadTasksPage(page = 1, phaseFilter = '') {
      const perPage = isMobile() ? 6 : 12;
      const params = new URLSearchParams({
        page: page,
        per_page: perPage,
        phase: phaseFilter
      });

      try {
        const response = await fetch(`${paginatedUrl}?${params}`);
        if (!response.ok) throw new Error('Error en la respuesta');
        
        const html = await response.text();
        
        // Verificar que tasksContainer existe antes de actualizar
        const container = document.getElementById('tasksContainer');
        if (container) {
          container.innerHTML = html;
        }
        
        // Re-configurar event listeners después de cargar contenido
        setupPaginationEvents();
        
      } catch (error) {
        console.error('Error cargando tareas:', error);
        if (window.notifications) {
          window.notifications.error('Error cargando las tareas');
        }
      }
    }

    // Configurar event listeners de paginación
    function setupPaginationEvents() {
      // Enlaces de paginación
      tasksContainer.querySelectorAll('.pagination .page-link[data-page]').forEach(link => {
        link.addEventListener('click', (e) => {
          e.preventDefault();
          const page = link.getAttribute('data-page');
          const phaseFilter = document.getElementById('phaseFilter')?.value || '';
          loadTasksPage(page, phaseFilter);
        });
      });
    }

    // Configurar filtro de fase con paginación
    const phaseFilter = document.getElementById('phaseFilter');
    if (phaseFilter) {
      phaseFilter.addEventListener('change', () => {
        const selected = phaseFilter.value;
        loadTasksPage(1, selected); // Siempre volver a página 1 al filtrar
      });
    }

    // Recargar cuando cambie el tamaño de pantalla (responsive)
    let resizeTimeout;
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(() => {
        const currentPage = document.querySelector('.pagination .page-item.active .page-link');
        const page = currentPage ? currentPage.textContent.trim() : '1';
        const phaseFilterValue = document.getElementById('phaseFilter')?.value || '';
        loadTasksPage(page, phaseFilterValue);
      }, 300);
    });

    // Configurar eventos iniciales
    setupPaginationEvents();
  }

  // Ejecutar configuración de paginación
  setupTasksPagination();

  // También ejecutar cuando se actualice contenido HTMX o cuando se cree una nueva tarea
  document.body.addEventListener('htmx:afterSwap', setupTasksPagination);
  
  // Función para recargar tareas (reutilizable)
  function reloadTasks() {
    const tasksContainer = document.getElementById('tasksContainer');
    if (tasksContainer) {
      const phaseFilter = document.getElementById('phaseFilter')?.value || '';
      const projectId = tasksContainer.getAttribute('data-project-id');
      const paginatedUrl = tasksContainer.getAttribute('data-paginated-url');
      if (projectId && paginatedUrl) {
        // Recargar primera página
        const isMobile = () => window.matchMedia('(max-width: 768px)').matches;
        const perPage = isMobile() ? 6 : 12;
        const params = new URLSearchParams({
          page: 1,
          per_page: perPage,
          phase: phaseFilter
        });
        
        fetch(`${paginatedUrl}?${params}`)
          .then(response => response.text())
          .then(html => {
            // Verificar que tasksContainer existe antes de actualizar
            const container = document.getElementById('tasksContainer');
            if (container) {
              container.innerHTML = html;
              setupTasksPagination();
            }
          })
          .catch(error => console.error('Error recargando tareas:', error));
      }
    }
  }

  // Recargar tareas después de crear una nueva tarea
  document.addEventListener('taskCreated', reloadTasks);
  
  // Recargar tareas después de actualizar una tarea
  document.addEventListener('taskUpdated', reloadTasks);
});

// Función global para actualizar el estado de las tareas
async function updateTaskStatus(taskId, newStatus) {
  try {
    const response = await fetch(`/projects/tasks/${taskId}/update-status/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
      },
      body: JSON.stringify({ status: newStatus })
    });

    if (response.ok) {
      // Recargar las tareas para mostrar el cambio
      const tasksContainer = document.getElementById('tasksContainer');
      if (tasksContainer) {
        const phaseFilter = document.getElementById('phaseFilter')?.value || '';
        const projectId = tasksContainer.getAttribute('data-project-id');
        const paginatedUrl = tasksContainer.getAttribute('data-paginated-url');
        
        if (projectId && paginatedUrl) {
          const isMobile = () => window.matchMedia('(max-width: 768px)').matches;
          const perPage = isMobile() ? 6 : 12;
          const currentPage = document.querySelector('.pagination .page-item.active .page-link');
          const page = currentPage ? currentPage.textContent.trim() : '1';
          
          const params = new URLSearchParams({
            page: page,
            per_page: perPage,
            phase: phaseFilter
          });
          
          const reloadResponse = await fetch(`${paginatedUrl}?${params}`);
          if (reloadResponse.ok) {
            const html = await reloadResponse.text();
            
            // Verificar que tasksContainer existe antes de actualizar
            const container = document.getElementById('tasksContainer');
            if (container) {
              container.innerHTML = html;
            }
            
            // Re-configurar event listeners después de cargar contenido
            const setupPaginationEvents = () => {
              tasksContainer.querySelectorAll('.pagination .page-link[data-page]').forEach(link => {
                link.addEventListener('click', (e) => {
                  e.preventDefault();
                  const page = link.getAttribute('data-page');
                  const phaseFilter = document.getElementById('phaseFilter')?.value || '';
                  loadTasksPage(page, phaseFilter);
                });
              });
            };
            setupPaginationEvents();
          }
        }
      }
      
      // Mostrar notificación de éxito
      if (window.notifications) {
        window.notifications.success('Estado de tarea actualizado correctamente');
      }
    } else {
      if (window.notifications) {
        window.notifications.error('Error al actualizar el estado de la tarea');
      }
    }
  } catch (error) {
    console.error('Error actualizando estado de tarea:', error);
    if (window.notifications) {
      window.notifications.error('Error al actualizar el estado de la tarea');
    }
  }
}

