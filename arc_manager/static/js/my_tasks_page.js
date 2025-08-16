// ===== MIS TAREAS - FUNCIONALIDADES COMPLETAS =====

// Función optimizada para cambio de estado instantáneo sin notificaciones
window.updateTaskStatus = function(taskId, status) {
    updateTaskStatusInstant(taskId, status);
};

// Función instantánea sin notificaciones ni recargas
function updateTaskStatusInstant(taskId, status) {
    // Primero actualizar la UI inmediatamente
    updateTaskUIInstant(taskId, status);
    
    // Luego enviar al servidor en background
    const url = `/projects/tasks/${taskId}/update_status/`;
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken') || ''
        },
        body: `status=${status}`
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            // Solo si falla, revertir la UI y mostrar error discreto
            console.error('Error al actualizar tarea:', data.error);
            // Podrías revertir la UI aquí si quisieras
        }
    })
    .catch(error => {
        console.error('Error:', error);
        // Podrías revertir la UI aquí si quisieras
    });
}

// Función para actualizar la UI instantáneamente
function updateTaskUIInstant(taskId, newStatus) {
    const taskCard = document.querySelector(`[data-task-id="${taskId}"]`);
    if (!taskCard) return;
    
    // Actualizar el dataset
    taskCard.dataset.status = newStatus;
    
    // Actualizar el badge de estado
    const statusBadge = taskCard.querySelector('.badge-status');
    if (statusBadge) {
        // Remover clases anteriores
        statusBadge.className = statusBadge.className.replace(/badge-\w+/g, '');
        statusBadge.classList.add('badge-status', `badge-${newStatus.toLowerCase()}`);
        
        // Actualizar texto
        const statusTexts = {
            'TODO': 'Pendiente',
            'IN_PROGRESS': 'En Progreso',
            'PAUSED': 'Pausada',
            'DONE': 'Completada'
        };
        statusBadge.textContent = statusTexts[newStatus] || newStatus;
    }
    
    // Actualizar botones de acción
    updateTaskActions(taskCard, newStatus);
    
    // Actualizar contadores
    updateCounters();
}

// Función para actualizar los botones según el nuevo estado
function updateTaskActions(taskCard, status) {
    const actionsContainer = taskCard.querySelector('.task-card-actions');
    if (!actionsContainer) return;
    
    const taskId = taskCard.dataset.taskId;
    const kanbanUrl = taskCard.querySelector('.action-kanban')?.href || '#';
    
    // Mantener siempre el botón de ver y kanban
    let actionsHTML = `
        <button type="button" class="action-btn action-view"
                data-modal-url="/projects/tasks/${taskId}/"
                data-modal-title="Detalles de la tarea"
                title="Ver detalles">
            <i class="fas fa-eye"></i>
        </button>
    `;
    
    // Botones según estado
    if (status === 'TODO') {
        actionsHTML += `
            <button type="button" class="action-btn action-start" 
                    onclick="updateTaskStatus(${taskId}, 'IN_PROGRESS')"
                    title="Iniciar tarea">
                <i class="fas fa-play"></i>
            </button>
        `;
    } else if (status === 'IN_PROGRESS') {
        actionsHTML += `
            <button type="button" class="action-btn action-pause" 
                    onclick="updateTaskStatus(${taskId}, 'PAUSED')"
                    title="Pausar tarea">
                <i class="fas fa-pause"></i>
            </button>
            <button type="button" class="action-btn action-complete" 
                    onclick="updateTaskStatus(${taskId}, 'DONE')"
                    title="Completar tarea">
                <i class="fas fa-check"></i>
            </button>
        `;
    } else if (status === 'PAUSED') {
        actionsHTML += `
            <button type="button" class="action-btn action-resume" 
                    onclick="updateTaskStatus(${taskId}, 'IN_PROGRESS')"
                    title="Reanudar tarea">
                <i class="fas fa-play"></i>
            </button>
        `;
    }
    
    // Siempre agregar botón de kanban
    actionsHTML += `
        <a href="${kanbanUrl}" 
           class="action-btn action-kanban"
           title="Ir al Kanban">
            <i class="fas fa-columns"></i>
        </a>
    `;
    
    actionsContainer.innerHTML = actionsHTML;
}

// Función para obtener cookie CSRF
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

// Función para actualizar contadores
function updateCounters() {
    const allTasks = document.querySelectorAll('.task-card-compact');
    const visibleTasks = document.querySelectorAll('.task-card-compact:not([style*="display: none"])');
    
    let counts = {
        total: visibleTasks.length,
        todo: 0,
        in_progress: 0,
        paused: 0,
        done: 0
    };
    
    visibleTasks.forEach(task => {
        const status = task.dataset.status;
        if (status === 'TODO') counts.todo++;
        else if (status === 'IN_PROGRESS') counts.in_progress++;
        else if (status === 'PAUSED') counts.paused++;
        else if (status === 'DONE') counts.done++;
    });
    
    // Actualizar contadores en la UI
    const totalEl = document.querySelector('.stat-total .stat-number');
    const todoEl = document.querySelector('.stat-todo .stat-number');
    const progressEl = document.querySelector('.stat-progress .stat-number');
    const pausedEl = document.querySelector('.stat-paused .stat-number');
    const doneEl = document.querySelector('.stat-done .stat-number');
    
    if (totalEl) totalEl.textContent = counts.total;
    if (todoEl) todoEl.textContent = counts.todo;
    if (progressEl) progressEl.textContent = counts.in_progress;
    if (pausedEl) pausedEl.textContent = counts.paused;
    if (doneEl) doneEl.textContent = counts.done;
}

// Función para filtrar tareas
function filterTasks() {
    const searchInput = document.getElementById('taskSearch');
    const statusFilter = document.getElementById('statusFilter');
    const priorityFilter = document.getElementById('priorityFilter');
    
    const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
    const statusValue = statusFilter ? statusFilter.value : '';
    const priorityValue = priorityFilter ? priorityFilter.value : '';
    
    const tasks = document.querySelectorAll('.task-card-compact');
    
    tasks.forEach(task => {
        const taskTitle = task.querySelector('.task-title-compact').textContent.toLowerCase();
        const taskProject = task.dataset.project || '';
        const taskStatus = task.dataset.status || '';
        const taskPriority = task.dataset.priority || '';
        
        let show = true;
        
        // Filtro de búsqueda
        if (searchTerm && !taskTitle.includes(searchTerm) && !taskProject.includes(searchTerm)) {
            show = false;
        }
        
        // Filtro de estado
        if (statusValue && taskStatus !== statusValue) {
            show = false;
        }
        
        // Filtro de prioridad
        if (priorityValue && taskPriority !== priorityValue) {
            show = false;
        }
        
        task.style.display = show ? 'block' : 'none';
    });
    
    updateCounters();
}

// Función global para limpiar filtros
window.clearAllFilters = function() {
    const searchInput = document.getElementById('taskSearch');
    const statusFilter = document.getElementById('statusFilter');
    const priorityFilter = document.getElementById('priorityFilter');
    const clearSearch = document.getElementById('clearSearch');
    
    if (searchInput) searchInput.value = '';
    if (statusFilter) statusFilter.value = '';
    if (priorityFilter) priorityFilter.value = '';
    if (clearSearch) clearSearch.style.display = 'none';
    filterTasks();
};

// Inicialización cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('taskSearch');
    const clearSearch = document.getElementById('clearSearch');
    const statusFilter = document.getElementById('statusFilter');
    const priorityFilter = document.getElementById('priorityFilter');
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    
    // Event listeners para búsqueda
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            if (this.value.length > 0) {
                if (clearSearch) clearSearch.style.display = 'block';
            } else {
                if (clearSearch) clearSearch.style.display = 'none';
            }
            filterTasks();
        });
    }
    
    // Event listener para limpiar búsqueda
    if (clearSearch) {
        clearSearch.addEventListener('click', function() {
            if (searchInput) searchInput.value = '';
            this.style.display = 'none';
            filterTasks();
        });
    }
    
    // Event listeners para filtros
    if (statusFilter) {
        statusFilter.addEventListener('change', filterTasks);
    }
    
    if (priorityFilter) {
        priorityFilter.addEventListener('change', filterTasks);
    }
    
    // Event listener para botón de limpiar filtros
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', window.clearAllFilters);
    }
    
    // Inicializar contadores
    updateCounters();
});

