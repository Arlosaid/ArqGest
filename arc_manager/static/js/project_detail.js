// Control robusto de pestañas y utilidades de Project Detail
document.addEventListener('DOMContentLoaded', function () {
  
  // Función para manejar el filtrado de archivos mejorado (Server-side con HTMX)
  function setupFileFiltering() {
    const fileTypeFilters = document.querySelectorAll('[id^="fileTypeFilter-"]');
    const fileDateFilters = document.querySelectorAll('[id^="fileDateFilter-"]');
    const clearFilterButtons = document.querySelectorAll('[id^="clearFilters-"]');
    
    // Configurar filtros por tipo
    fileTypeFilters.forEach(filter => {
      if (filter.dataset.initialized) return;
      filter.dataset.initialized = "true";
      const phaseId = filter.id.replace('fileTypeFilter-', '');
      filter.addEventListener('change', () => reloadFilesWithFilters(phaseId));
    });
    
    // Configurar filtros por fecha
    fileDateFilters.forEach(filter => {
      if (filter.dataset.initialized) return;
      filter.dataset.initialized = "true";
      const phaseId = filter.id.replace('fileDateFilter-', '');
      filter.addEventListener('change', () => reloadFilesWithFilters(phaseId));
    });
    
    // Configurar botones de limpiar filtros
    // NOTA: El manejo principal está en files_filtering.js usando delegación de eventos
    // No agregamos listeners aquí para evitar conflictos
  }
  
  function reloadFilesWithFilters(phaseId) {
    const container = document.getElementById(`files-container-${phaseId}`);
    if (!container) return;
    
    const typeFilter = document.getElementById(`fileTypeFilter-${phaseId}`);
    const dateFilter = document.getElementById(`fileDateFilter-${phaseId}`);
    
    const typeValue = typeFilter ? typeFilter.value : '';
    const dateValue = dateFilter ? dateFilter.value : '';
    
    // Obtener URL base del atributo hx-get original
    let url = container.getAttribute('hx-get');
    if (url) {
        url = url.split('?')[0]; // Remover query params existentes
    } else {
        console.error('No hx-get attribute found on container');
        return;
    }
    
    // Construir nuevos parámetros
    const params = new URLSearchParams();
    params.append('offset', '0'); // Resetear a la primera página
    params.append('limit', '20');
    if (typeValue) params.append('type', typeValue);
    if (dateValue) params.append('date', dateValue);
    
    const finalUrl = `${url}?${params.toString()}`;
    
    // Usar HTMX para recargar
    if (window.htmx) {
        // Mostrar indicador de carga si existe
        const spinner = container.querySelector('.files-loading') || document.getElementById(`spinner-${phaseId}`);
        if (spinner) spinner.style.display = 'block';
        
        htmx.ajax('GET', finalUrl, {
            target: `#files-container-${phaseId}`,
            swap: 'innerHTML'
        });
    }
  }
  
  function clearAllFilters(phaseId) {
    const typeFilter = document.getElementById(`fileTypeFilter-${phaseId}`);
    const dateFilter = document.getElementById(`fileDateFilter-${phaseId}`);
    
    if (typeFilter) typeFilter.value = '';
    if (dateFilter) dateFilter.value = '';
    
    // Recargar sin filtros
    reloadFilesWithFilters(phaseId);
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
  if (!['details', 'phases', 'tasks', 'files'].includes(initial)) initial = 'details';
  showTabById(initial);

  tabContainer.addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-bs-target]');
    if (!btn) return;
    const id = btn.getAttribute('data-bs-target').replace('#', '');
    showTabById(id);
    
    // Actualizar URL sin recargar para mantener la pestaña activa al refrescar
    history.replaceState(null, null, `#${id}`);
  });

  tabContainer.addEventListener('shown.bs.tab', (e) => {
    const id = e.target?.getAttribute('data-bs-target')?.replace('#', '');
    if (id) showTabById(id);
  });

  const tasksTab = document.getElementById('tasks-tab');
  if (tasksTab) {
    tasksTab.addEventListener('click', function () {
      showTabById('tasks');
    });
  }

  // NOTA: La eliminación de tareas ahora es manejada por task-delete.js (sistema unificado)
  // No necesitamos un listener duplicado aquí que cause dobles modales

  // Configurar paginación de tareas responsive usando delegación de eventos
  function setupTasksPagination() {
    const tasksContainer = document.getElementById('tasksContainer');
    if (!tasksContainer) return;

    const projectId = tasksContainer.getAttribute('data-project-id');
    const paginatedUrl = tasksContainer.getAttribute('data-paginated-url');
    if (!projectId || !paginatedUrl) return;

    // Detectar si es móvil usando media query
    const isMobile = () => window.matchMedia('(max-width: 768px)').matches;
    
    // Función para cargar página (global para reutilizar)
    window.loadTasksPage = async function(page = 1, phaseFilter = '') {
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
        
      } catch (error) {
        console.error('Error cargando tareas:', error);
        if (window.notifications) {
          window.notifications.error('Error cargando las tareas');
        }
      }
    };

    // Configurar filtro de fase con paginación
    const phaseFilter = document.getElementById('phaseFilter');
    if (phaseFilter) {
      phaseFilter.addEventListener('change', () => {
        const selected = phaseFilter.value;
        window.loadTasksPage(1, selected); // Siempre volver a página 1 al filtrar
      });
    }

    // Recargar cuando cambie el tamaño de pantalla (responsive)
    let resizeTimeout;
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(() => {
        const currentPage = document.querySelector('.arc-pagination-current');
        const page = currentPage ? currentPage.textContent.trim() : '1';
        const phaseFilterValue = document.getElementById('phaseFilter')?.value || '';
        window.loadTasksPage(page, phaseFilterValue);
      }, 300);
    });
  }

  // Delegación de eventos para paginación de tareas (se ejecuta una sola vez)
  document.addEventListener('click', function(e) {
    const paginationLink = e.target.closest('#tasksContainer .arc-pagination [data-page]');
    if (paginationLink) {
      e.preventDefault();
      e.stopPropagation();
      const page = paginationLink.getAttribute('data-page');
      const phaseFilter = document.getElementById('phaseFilter')?.value || '';
      if (window.loadTasksPage) {
        window.loadTasksPage(page, phaseFilter);
      }
    }
  });

  // Ejecutar configuración de paginación
  setupTasksPagination();

  // También ejecutar cuando se actualice contenido HTMX o cuando se cree una nueva tarea
  document.body.addEventListener('htmx:afterSwap', setupTasksPagination);
  
  // Función para recargar tareas (reutilizable)
  function reloadTasks() {
    const tasksContainer = document.getElementById('tasksContainer');
    if (tasksContainer && window.loadTasksPage) {
      const phaseFilter = document.getElementById('phaseFilter')?.value || '';
      window.loadTasksPage(1, phaseFilter);
    }
  }

  // Recargar tareas después de crear una nueva tarea
  document.addEventListener('taskCreated', reloadTasks);
  
  // Recargar tareas después de actualizar una tarea
  document.addEventListener('taskUpdated', reloadTasks);
  
  // Recargar tareas después de eliminar una tarea
  document.addEventListener('taskDeleted', reloadTasks);
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
        const currentPage = document.querySelector('.arc-pagination-current');
        const page = currentPage ? currentPage.textContent.trim() : '1';
        
        // Usar la función global de paginación
        if (window.loadTasksPage) {
          window.loadTasksPage(page, phaseFilter);
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

