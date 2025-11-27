// ===== MIS TAREAS - FUNCIONALIDADES COMPLETAS =====

// Función para obtener cookie CSRF (debe estar primero)
function getCsrfToken() {
    // 1. Try to get from meta tag (most reliable for SPA/AJAX)
    const metaToken = document.querySelector('meta[name="csrf-token"]');
    if (metaToken && metaToken.content) {
        return metaToken.content;
    }
    
    // 2. Try to get from hidden input (standard Django form)
    const inputToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (inputToken && inputToken.value) {
        return inputToken.value;
    }

    // 3. Fallback to cookie (might fail with HttpOnly)
    const value = `; ${document.cookie}`;
    const parts = value.split(`; csrftoken=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    
    return '';
}

// Función para broadcast cambios de estado a otras pestañas/ventanas
function broadcastTaskStatusChange(taskId, newStatus) {
    try {
        const event = {
            type: 'TASK_STATUS_UPDATED',
            taskId: taskId,
            status: newStatus,
            timestamp: Date.now(),
            source: 'my_tasks'
        };

        // Usar localStorage para comunicación entre pestañas
        localStorage.setItem('task_update_event', JSON.stringify(event));

        // Limpiar inmediatamente para permitir eventos duplicados
        setTimeout(() => {
            localStorage.removeItem('task_update_event');
        }, 100);
    } catch (error) {
        console.error('Error broadcasting task update:', error);
    }
}

// Función para actualizar la UI instantáneamente
function updateTaskUIInstant(taskId, newStatus) {
    const taskCard = document.querySelector(`[data-task-id="${taskId}"]`);
    if (!taskCard) return;

    // Guardar el estado anterior
    const oldStatus = taskCard.dataset.status;

    // Actualizar el dataset
    taskCard.dataset.status = newStatus;

    // Actualizar el badge de estado
    const statusBadge = taskCard.querySelector('.task-compact-status');
    if (statusBadge) {
        // Remover clases de estado anteriores
        statusBadge.classList.remove('todo', 'in-progress', 'paused', 'done');
        
        // Mapear estado a clase CSS
        const statusClassMap = {
            'TODO': 'todo',
            'IN_PROGRESS': 'in-progress',
            'PAUSED': 'paused',
            'DONE': 'done'
        };
        
        // Agregar nueva clase
        const newClass = statusClassMap[newStatus];
        if (newClass) {
            statusBadge.classList.add(newClass);
        }

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

    // Actualizar contadores específicamente para este cambio de estado
    updateTaskStatusCounter(oldStatus, newStatus);
}

// Función para actualizar los botones según el nuevo estado
function updateTaskActions(taskCard, status) {
    const actionsContainer = taskCard.querySelector('.status-actions');
    if (!actionsContainer) return;

    const taskId = taskCard.dataset.taskId;

    // Guardar el botón de kanban antes de reemplazar
    const kanbanBtn = actionsContainer.querySelector('.action-kanban');
    const kanbanUrl = kanbanBtn?.href || '#';

    // Limpiar solo los botones de estado (no todos los botones)
    const stateButtons = actionsContainer.querySelectorAll('.action-start, .action-pause, .action-complete, .action-resume, .action-reopen');
    stateButtons.forEach(btn => btn.remove());

    // Crear nuevos botones según estado
    let newButtonsHTML = '';

    if (status === 'TODO') {
        newButtonsHTML = `
            <button type="button" class="btn-icon-action edit action-start" 
                    onclick="updateTaskStatus(${taskId}, 'IN_PROGRESS')"
                    title="Iniciar tarea">
                <i class="fas fa-play"></i>
            </button>
        `;
    } else if (status === 'IN_PROGRESS') {
        newButtonsHTML = `
            <button type="button" class="btn-icon-action edit action-pause" 
                    onclick="updateTaskStatus(${taskId}, 'PAUSED')"
                    title="Pausar tarea">
                <i class="fas fa-pause"></i>
            </button>
            <button type="button" class="btn-icon-action delete action-complete" 
                    onclick="updateTaskStatus(${taskId}, 'DONE')"
                    title="Completar tarea">
                <i class="fas fa-check"></i>
            </button>
        `;
    } else if (status === 'PAUSED') {
        newButtonsHTML = `
            <button type="button" class="btn-icon-action edit action-resume" 
                    onclick="updateTaskStatus(${taskId}, 'IN_PROGRESS')"
                    title="Reanudar tarea">
                <i class="fas fa-play"></i>
            </button>
        `;
    } else if (status === 'DONE') {
        newButtonsHTML = `
            <button type="button" class="btn-icon-action edit action-reopen" 
                    onclick="updateTaskStatus(${taskId}, 'IN_PROGRESS')"
                    title="Reabrir tarea">
                <i class="fas fa-undo"></i>
            </button>
        `;
    }

    // Insertar los nuevos botones antes del botón de kanban
    if (kanbanBtn) {
        kanbanBtn.insertAdjacentHTML('beforebegin', newButtonsHTML);
    } else {
        // Si no hay botón de kanban, agregar los botones de estado y recrear el botón de kanban
        actionsContainer.insertAdjacentHTML('beforeend', newButtonsHTML);
        actionsContainer.insertAdjacentHTML('beforeend', `
            <a href="${kanbanUrl}" 
               class="btn-icon-action view action-kanban"
               title="Ir al Kanban">
                <i class="fas fa-columns"></i>
            </a>
        `);
    }
}

// Función optimizada para cambio de estado instantáneo sin notificaciones
window.updateTaskStatus = function (taskId, status) {
    // Primero actualizar la UI inmediatamente
    updateTaskUIInstant(taskId, status);

    // Luego enviar al servidor en background
    const url = `/projects/tasks/${taskId}/update_status/`;

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCsrfToken()
        },
        body: `status=${status}`
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // CRÍTICO: Broadcast el cambio a otras pestañas/ventanas (ej: Kanban)
                broadcastTaskStatusChange(taskId, status);
            } else {
                // Solo si falla, mostrar error discreto
                console.error('Error al actualizar tarea:', data.error);
                // Podrías revertir la UI aquí si quisieras
            }
        })
        .catch(error => {
            console.error('Error:', error);
            // Podrías revertir la UI aquí si quisieras
        });
};

// Función global para confirmar eliminación de tareas
window.confirmDeleteTask = function (taskId, taskTitle) {
    // Crear modal de confirmación personalizado
    const modalHtml = `
        <div class="modal fade" id="deleteTaskModal" tabindex="-1" aria-labelledby="deleteTaskModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header bg-danger text-white">
                        <h5 class="modal-title" id="deleteTaskModalLabel">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            Confirmar eliminación
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="text-center mb-3">
                            <i class="fas fa-trash-alt text-danger" style="font-size: 3rem; opacity: 0.7;"></i>
                        </div>
                        <p class="mb-3">¿Estás seguro de que deseas eliminar la siguiente tarea?</p>
                        <div class="alert alert-light border">
                            <strong>"${taskTitle}"</strong>
                        </div>
                        <p class="text-muted small mb-0">
                            <i class="fas fa-info-circle me-1"></i>
                            Esta acción no se puede deshacer.
                        </p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            <i class="fas fa-times me-1"></i>
                            Cancelar
                        </button>
                        <button type="button" class="btn btn-danger" onclick="deleteTask(${taskId})">
                            <i class="fas fa-trash-alt me-1"></i>
                            Eliminar tarea
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Remover modal anterior si existe
    const existingModal = document.getElementById('deleteTaskModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Agregar modal al DOM
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Mostrar modal
    const modal = new bootstrap.Modal(document.getElementById('deleteTaskModal'));
    modal.show();

    // Limpiar modal después de cerrarlo
    document.getElementById('deleteTaskModal').addEventListener('hidden.bs.modal', function () {
        this.remove();
    });
};

// Función para eliminar la tarea
window.deleteTask = function (taskId) {
    const url = `/projects/tasks/${taskId}/delete/`;

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCsrfToken()
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Cerrar modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('deleteTaskModal'));
                if (modal) {
                    modal.hide();
                }

                // Remover tarjeta de la UI
                const taskCard = document.querySelector(`[data-task-id="${taskId}"]`);
                if (taskCard) {
                    // Animación de salida
                    taskCard.style.transition = 'all 0.3s ease';
                    taskCard.style.transform = 'scale(0.8)';
                    taskCard.style.opacity = '0';

                    setTimeout(() => {
                        taskCard.remove();

                        // Actualizar contadores
                        const taskStatus = taskCard.dataset.status;
                        updateTaskDeleteCounter(taskStatus);

                        // Verificar si no hay más tareas
                        const remainingTasks = document.querySelectorAll('.task-card-compact');
                        if (remainingTasks.length === 0) {
                            showEmptyState();
                        }
                    }, 300);
                }

                // Mostrar notificación de éxito
                showSuccessNotification('Tarea eliminada correctamente');
            } else {
                // Mostrar error
                showErrorNotification(data.error || 'Error al eliminar la tarea');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showErrorNotification('Error de conexión al eliminar la tarea');
        });
};

// Variables globales para guardar los valores reales del servidor
let serverCounters = {
    total: 0,
    todo: 0,
    in_progress: 0,
    paused: 0,
    done: 0
};

// Función para inicializar contadores del servidor
function initializeServerCounters() {
    const totalEl = document.getElementById('stat-total');
    const todoEl = document.getElementById('stat-todo');
    const progressEl = document.getElementById('stat-in-progress');
    const pausedEl = document.getElementById('stat-paused');
    const doneEl = document.getElementById('stat-done');
    
    // Guardar los valores originales del servidor
    if (totalEl) serverCounters.total = parseInt(totalEl.textContent) || 0;
    if (todoEl) serverCounters.todo = parseInt(todoEl.textContent) || 0;
    if (progressEl) serverCounters.in_progress = parseInt(progressEl.textContent) || 0;
    if (pausedEl) serverCounters.paused = parseInt(pausedEl.textContent) || 0;
    if (doneEl) serverCounters.done = parseInt(doneEl.textContent) || 0;
}

// Función para actualizar un contador específico cuando cambia el estado de una tarea
function updateTaskStatusCounter(oldStatus, newStatus) {
    // Decrementar el contador anterior
    if (oldStatus === 'TODO') serverCounters.todo--;
    else if (oldStatus === 'IN_PROGRESS') serverCounters.in_progress--;
    else if (oldStatus === 'PAUSED') serverCounters.paused--;
    else if (oldStatus === 'DONE') serverCounters.done--;

    // Incrementar el nuevo contador
    if (newStatus === 'TODO') serverCounters.todo++;
    else if (newStatus === 'IN_PROGRESS') serverCounters.in_progress++;
    else if (newStatus === 'PAUSED') serverCounters.paused++;
    else if (newStatus === 'DONE') serverCounters.done++;

    // Actualizar la UI con los valores actualizados
    refreshCountersUI();
}

// Función para actualizar contadores cuando se elimina una tarea
function updateTaskDeleteCounter(taskStatus) {
    // Decrementar el total
    serverCounters.total--;

    // Decrementar el contador específico
    if (taskStatus === 'TODO') serverCounters.todo--;
    else if (taskStatus === 'IN_PROGRESS') serverCounters.in_progress--;
    else if (taskStatus === 'PAUSED') serverCounters.paused--;
    else if (taskStatus === 'DONE') serverCounters.done--;

    // Actualizar la UI
    refreshCountersUI();
}

// Función para refrescar la UI con los contadores actuales
function refreshCountersUI() {
    const totalEl = document.getElementById('stat-total');
    const todoEl = document.getElementById('stat-todo');
    const progressEl = document.getElementById('stat-in-progress');
    const pausedEl = document.getElementById('stat-paused');
    const doneEl = document.getElementById('stat-done');

    if (totalEl) totalEl.textContent = serverCounters.total;
    if (todoEl) todoEl.textContent = serverCounters.todo;
    if (progressEl) progressEl.textContent = serverCounters.in_progress;
    if (pausedEl) pausedEl.textContent = serverCounters.paused;
    if (doneEl) doneEl.textContent = serverCounters.done;
}

// Función legacy para compatibilidad (ahora no hace nada)
function updateCounters() {
    // No hacer nada - preservar los valores del servidor
    // Solo se actualizan cuando cambia específicamente el estado de una tarea
}

// Función para mostrar estado vacío
function showEmptyState() {
    const tasksGrid = document.getElementById('tasksList');
    if (tasksGrid) {
        tasksGrid.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1;">
                <div class="empty-icon">
                    <i class="fas fa-clipboard-check"></i>
                </div>
                <h3>No tienes tareas asignadas</h3>
                <p>¡Perfecto! No tienes tareas pendientes en este momento.</p>
                <a href="/projects/" class="btn-explore">
                    <i class="fas fa-search"></i> Explorar Proyectos
                </a>
            </div>
        `;
    }
}

// Funciones de notificación
function showSuccessNotification(message) {
    showNotification(message, 'success');
}

function showErrorNotification(message) {
    showNotification(message, 'error');
}

function showNotification(message, type = 'success') {
    // Crear notificación toast
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type === 'success' ? 'success' : 'danger'} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;

    // Buscar o crear contenedor de toasts
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1055';
        document.body.appendChild(toastContainer);
    }

    // Agregar toast
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);

    // Mostrar toast
    const toastElement = toastContainer.lastElementChild;
    const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
    toast.show();

    // Limpiar después de ocultar
    toastElement.addEventListener('hidden.bs.toast', function () {
        this.remove();
    });
}

// Las funciones de filtros ya no necesitan manejar paginación
// porque ahora se hace en el servidor

// Función para filtrar tareas - ahora redirige al servidor con parámetros GET
function filterTasks() {
    const searchInput = document.getElementById('taskSearch');
    const statusFilter = document.getElementById('statusFilter');
    const priorityFilter = document.getElementById('priorityFilter');

    const searchTerm = searchInput ? searchInput.value.trim() : '';
    const statusValue = statusFilter ? statusFilter.value : '';
    const priorityValue = priorityFilter ? priorityFilter.value : '';

    // Construir URL con parámetros de filtro
    const currentUrl = new URL(window.location);
    const params = new URLSearchParams();

    if (searchTerm) {
        params.set('search', searchTerm);
    }

    if (statusValue) {
        params.set('status', statusValue);
    }

    if (priorityValue) {
        params.set('priority', priorityValue);
    }

    // Navegar a la nueva URL con filtros
    const newUrl = currentUrl.pathname + (params.toString() ? '?' + params.toString() : '');

    // Si no hay cambios en la URL, no recargar
    if (newUrl !== window.location.pathname + window.location.search) {
        window.location.href = newUrl;
    }
}

// Función global para limpiar filtros
window.clearAllFilters = function () {
    // Simplemente redirigir a la URL base sin parámetros
    window.location.href = window.location.pathname;
};

// Función para establecer valores de filtros desde URL
function setFiltersFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    const searchInput = document.getElementById('taskSearch');
    const statusFilter = document.getElementById('statusFilter');
    const priorityFilter = document.getElementById('priorityFilter');
    const clearSearch = document.getElementById('clearSearch');

    // Establecer valor de búsqueda
    const searchValue = urlParams.get('search') || '';
    if (searchInput) {
        searchInput.value = searchValue;
        if (searchValue && clearSearch) {
            clearSearch.style.display = 'block';
        }
    }

    // Establecer filtro de estado
    const statusValue = urlParams.get('status') || '';
    if (statusFilter) {
        statusFilter.value = statusValue;
    }

    // Establecer filtro de prioridad
    const priorityValue = urlParams.get('priority') || '';
    if (priorityFilter) {
        priorityFilter.value = priorityValue;
    }
}

// Función para añadir debounce a la búsqueda
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Inicialización cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('taskSearch');
    const clearSearch = document.getElementById('clearSearch');
    const statusFilter = document.getElementById('statusFilter');
    const priorityFilter = document.getElementById('priorityFilter');
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');

    // Establecer valores de filtros desde URL
    setFiltersFromURL();

    // Event listeners para búsqueda con debounce
    if (searchInput) {
        const debouncedFilter = debounce(filterTasks, 500);

        searchInput.addEventListener('input', function () {
            if (this.value.length > 0) {
                if (clearSearch) clearSearch.style.display = 'block';
            } else {
                if (clearSearch) clearSearch.style.display = 'none';
            }
            debouncedFilter();
        });
    }

    // Event listener para limpiar búsqueda
    if (clearSearch) {
        clearSearch.addEventListener('click', function () {
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

    // Inicializar contadores del servidor (preservar valores originales)
    initializeServerCounters();

    // CRÍTICO: Escuchar cambios de estado de tareas desde otras pestañas
    window.addEventListener('storage', function (e) {
        if (e.key === 'task_update_event' && e.newValue) {
            try {
                const event = JSON.parse(e.newValue);

                // Solo procesar eventos de actualización de tareas
                if (event.type === 'TASK_STATUS_UPDATED') {
                    // Actualizar la UI si la tarea está visible en esta página
                    updateTaskUIInstant(event.taskId, event.status);

                    console.log(`[Sync] Task ${event.taskId} updated to ${event.status} from ${event.source}`);
                }
            } catch (error) {
                console.error('Error processing storage event:', error);
            }
        }
    });
});

