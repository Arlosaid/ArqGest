/**
 * Kanban Board JavaScript - ArcManager
 * Maneja la funcionalidad del tablero kanban para gestión de tareas
 */

class KanbanManager {
    constructor() {
        this.initializeElements();
        this.bindEvents();
        this.initializeDragAndDrop();
        this.initializeModals();
        this.isUpdating = false; // Flag para evitar actualizaciones múltiples
    }

    initializeElements() {
        this.board = document.querySelector('.kanban-board');
        this.columns = document.querySelectorAll('.kanban-column-body');
        this.cards = document.querySelectorAll('.kanban-card');
        this.addTaskModal = document.getElementById('addTaskModal');
        this.taskModal = document.getElementById('taskModal');
        this.taskForm = document.getElementById('taskForm');
    }

    bindEvents() {
        // Eventos de filtros
        this.bindFilterEvents();
        
        // Eventos de formularios
        this.bindFormEvents();
        
        // Eventos de modales
        this.bindModalEvents();
        
        // Eventos de botones de acción
        this.bindActionEvents();
    }

    bindFilterEvents() {
        const phaseFilter = document.querySelector('select[name="phase_id"]');
        if (phaseFilter) {
            phaseFilter.addEventListener('change', (e) => {
                this.applyPhaseFilter(e.target.value);
            });
        }

        // Botón de limpiar filtros
        const clearFiltersBtn = document.querySelector('button[onclick="clearFilters()"]');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.clearFilters();
            });
        }

        // Botón de actualizar
        const refreshBtn = document.querySelector('button[onclick="refreshKanban()"]');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.refreshKanban();
            });
        }
    }

    bindFormEvents() {
        if (this.taskForm) {
            this.taskForm.addEventListener('submit', (e) => {
                this.handleTaskSubmit(e);
            });
        }
    }

    bindModalEvents() {
        // Modal de nueva tarea
        if (this.addTaskModal) {
            this.addTaskModal.addEventListener('show.bs.modal', () => {
                this.resetTaskForm();
            });
        }

        // Modal de editar tarea
        if (this.taskModal) {
            this.taskModal.addEventListener('show.bs.modal', () => {
                this.prepareEditModal();
            });
        }
    }

    bindActionEvents() {
        // Botones de acción en las tarjetas
        document.addEventListener('click', (e) => {
            if (e.target.closest('.task-actions .btn')) {
                const btn = e.target.closest('.task-actions .btn');
                const action = btn.getAttribute('data-action');
                const taskId = btn.closest('.kanban-card').dataset.taskId;
                
                if (action === 'edit') {
                    this.editTask(taskId);
                } else if (action === 'view') {
                    this.viewTask(taskId);
                } else if (action === 'delete') {
                    this.deleteTask(taskId);
                }
            }
        });
    }

    initializeDragAndDrop() {
        if (!this.columns.length) return;

        this.columns.forEach(column => {
            column.addEventListener('dragover', this.handleDragOver.bind(this));
            column.addEventListener('drop', this.handleDrop.bind(this));
            column.addEventListener('dragenter', this.handleDragEnter.bind(this));
            column.addEventListener('dragleave', this.handleDragLeave.bind(this));
        });

        this.cards.forEach(card => {
            card.addEventListener('dragstart', this.handleDragStart.bind(this));
            card.addEventListener('dragend', this.handleDragEnd.bind(this));
        });
    }

    initializeModals() {
        // Inicializar modales de Bootstrap si están disponibles
        if (typeof bootstrap !== 'undefined') {
            this.modals = {
                addTask: new bootstrap.Modal(this.addTaskModal),
                task: new bootstrap.Modal(this.taskModal)
            };
        }
    }

    // ===== DRAG & DROP HANDLERS =====

    handleDragStart(e) {
        if (this.isUpdating) {
            e.preventDefault();
            return;
        }
        
        e.target.classList.add('dragging');
        e.dataTransfer.setData('text/plain', e.target.dataset.taskId);
        e.dataTransfer.effectAllowed = 'move';
    }

    handleDragEnd(e) {
        e.target.classList.remove('dragging');
        this.removeDragOverClasses();
    }

    handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    }

    handleDragEnter(e) {
        e.preventDefault();
        const column = e.target.closest('.kanban-column-body');
        if (column) {
            column.classList.add('drag-over');
        }
    }

    handleDragLeave(e) {
        const column = e.target.closest('.kanban-column-body');
        if (column && !column.contains(e.relatedTarget)) {
            column.classList.remove('drag-over');
        }
    }

    handleDrop(e) {
        e.preventDefault();
        if (this.isUpdating) return;
        
        const column = e.target.closest('.kanban-column-body');
        if (!column) return;

        const taskId = e.dataTransfer.getData('text/plain');
        const newStatus = column.dataset.statusCode;
        
        column.classList.remove('drag-over');
        this.updateTaskStatusSilently(taskId, newStatus);
    }

    removeDragOverClasses() {
        this.columns.forEach(column => {
            column.classList.remove('drag-over');
        });
    }

    // ===== TASK MANAGEMENT - ACTUALIZACIONES SILENCIOSAS =====

    async updateTaskStatusSilently(taskId, newStatus) {
        if (this.isUpdating) return;
        
        this.isUpdating = true;
        
        try {
            const response = await fetch(`/projects/tasks/${taskId}/update_status/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    status: newStatus
                })
            });

            const data = await response.json();
            
            if (data.success) {
                // Actualización silenciosa - solo mover la tarjeta visualmente
                this.moveCardVisually(taskId, newStatus);
                
                // Actualizar estadísticas sin recargar
                this.updateStatisticsSilently();
            } else {
                // Solo mostrar error si algo falla
                console.error('Error al actualizar tarea:', data.error);
            }
        } catch (error) {
            console.error('Error:', error);
        } finally {
            this.isUpdating = false;
        }
    }

    moveCardVisually(taskId, newStatus) {
        const card = document.querySelector(`[data-task-id="${taskId}"]`);
        if (!card) return;

        // Encontrar la columna de destino
        const targetColumn = document.querySelector(`[data-status-code="${newStatus}"]`);
        if (!targetColumn) return;

        // Mover la tarjeta visualmente
        targetColumn.appendChild(card);
        
        // Sin animaciones al mover
        card.style.opacity = '1';
        card.style.transform = 'none';

        // Actualizar contadores de columnas
        this.updateColumnCounts();
    }

    updateColumnCounts() {
        const columns = document.querySelectorAll('.kanban-column');
        
        columns.forEach(column => {
            const columnBody = column.querySelector('.kanban-column-body');
            const countElement = column.querySelector('.task-count');
            
            if (columnBody && countElement) {
                const taskCount = columnBody.querySelectorAll('.kanban-card').length;
                const statusCode = columnBody.dataset.statusCode;
                
                // Actualizar el contador
                if (taskCount === 1) {
                    countElement.textContent = '1 tarea';
                } else {
                    countElement.textContent = `${taskCount} tareas`;
                }
            }
        });
    }

    updateStatisticsSilently() {
        // Actualizar estadísticas en tiempo real sin recargar
        const statCards = document.querySelectorAll('.stat-card');
        
        // Efectos de actualización deshabilitados
        
        // Actualizar números reales de las estadísticas
        this.updateStatisticsInRealTime();
    }

    async updateStatisticsInRealTime() {
        try {
            // Obtener estadísticas actualizadas del servidor
            const projectId = this.getProjectIdFromUrl();
            const response = await fetch(`/projects/${projectId}/statistics/`);
            const data = await response.json();
            
            if (data.success) {
                // Actualizar cada tarjeta de estadística con los nuevos números
                this.updateStatCard('total-tasks', data.total_tasks);
                this.updateStatCard('in-progress', data.in_progress_tasks);
                this.updateStatCard('completed', data.completed_tasks);
                this.updateStatCard('paused', data.paused_tasks);
            }
        } catch (error) {
            console.error('Error al actualizar estadísticas:', error);
        }
    }

    updateStatCard(cardType, newValue) {
        const statCard = document.querySelector(`.stat-card.${cardType}`);
        if (!statCard) return;

        const numberElement = statCard.querySelector('.stat-number');
        if (!numberElement) return;

        // Actualizar número sin animación
        numberElement.textContent = newValue;
    }

    animateNumberChange() { /* deshabilitada intencionalmente */ }

    getProjectIdFromUrl() {
        // Extraer el ID del proyecto de la URL actual
        const urlParts = window.location.pathname.split('/');
        const projectIndex = urlParts.findIndex(part => part === 'projects');
        if (projectIndex !== -1 && urlParts[projectIndex + 1]) {
            return urlParts[projectIndex + 1];
        }
        return null;
    }

    async handleTaskSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(this.taskForm);
        // El botón de submit está fuera del <form> (usa atributo form="taskForm").
        // Buscar primero por el botón vinculado al form y, si no existe, buscar dentro del form.
        const submitBtn = document.querySelector('button[type="submit"][form="taskForm"]') || this.taskForm.querySelector('button[type="submit"]');
        const originalHTML = submitBtn ? submitBtn.innerHTML : null;
        
        // Deshabilitar botón y mostrar loading (si existe)
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creando...';
        }
        
        try {
            const response = await fetch(this.taskForm.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                }
            });

            const contentType = response.headers.get('content-type') || '';
            if (response.ok) {
                if (contentType.includes('application/json')) {
                    const data = await response.json();
                    if (data && data.success) {
                        this.showNotification('Tarea creada correctamente', 'success');
                        this.closeModal('addTask');
                        setTimeout(() => location.reload(), 600);
                    } else {
                        this.showNotification((data && (data.message || data.error)) || 'Error al crear la tarea', 'error');
                    }
                } else {
                    // Fallback: servidor devolvió HTML por redirección; considerarlo éxito
                    this.showNotification('Tarea creada correctamente', 'success');
                    this.closeModal('addTask');
                    setTimeout(() => location.reload(), 600);
                }
            } else {
                let msg = 'Error al crear la tarea';
                try {
                    const data = contentType.includes('application/json') ? await response.json() : null;
                    msg = (data && (data.message || data.error)) || msg;
                } catch (_) {}
                this.showNotification(msg, 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showNotification('Error de conexión', 'error');
        } finally {
            // Restaurar botón si existe
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalHTML;
            }
        }
    }

    editTask(taskId) {
        // Cargar datos de la tarea para edición
        fetch(`/projects/tasks/${taskId}/edit/`)
            .then(response => response.text())
            .then(html => {
                document.getElementById('taskModalContent').innerHTML = html;
                this.openModal('task');
            })
            .catch(error => {
                console.error('Error:', error);
                this.showNotification('Error al cargar la tarea', 'error');
            });
    }

    viewTask(taskId) {
        // Abrir modal global si existe, como fallback usa navegación
        if (typeof window.openAppModal === 'function') {
            window.openAppModal(`/projects/tasks/${taskId}/`, 'Detalles de la Tarea');
            return;
        }
        // Fallback
        window.location.href = `/projects/tasks/${taskId}/`;
    }

    async deleteTask(taskId) {
        if (!confirm('¿Estás seguro de que quieres eliminar esta tarea?')) {
            return;
        }

        try {
            const response = await fetch(`/projects/tasks/${taskId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (response.ok) {
                // Buscar y eliminar la tarjeta del DOM
                const taskCard = document.querySelector(`[data-task-id="${taskId}"]`);
                if (taskCard) {
                    // Animación de salida
                    taskCard.style.transition = 'all 0.3s ease';
                    taskCard.style.opacity = '0';
                    taskCard.style.transform = 'scale(0.8)';
                    
                    setTimeout(() => {
                        taskCard.remove();
                        
                        // Verificar si la columna está vacía y mostrar mensaje
                        const column = taskCard.closest('.kanban-column-body');
                        if (column && column.children.length === 0) {
                            column.innerHTML = '<div class="empty-column"><div class="empty-state"><i class="fas fa-drafting-compass"></i><p>No hay tareas</p></div></div>';
                        }
                    }, 300);
                }
                
                this.showNotification('Tarea eliminada correctamente', 'success');
                
                // Disparar evento para que otras partes de la app se actualicen
                document.dispatchEvent(new CustomEvent('taskDeleted', { detail: { taskId } }));
            } else {
                this.showNotification('Error al eliminar la tarea', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showNotification('Error de conexión', 'error');
        }
    }

    // ===== FILTERS AND UTILITIES =====

    applyPhaseFilter(phaseId) {
        const url = new URL(window.location);
        if (phaseId) {
            url.searchParams.set('phase_id', phaseId);
        } else {
            url.searchParams.delete('phase_id');
        }
        window.location.href = url.toString();
    }

    clearFilters() {
        window.location.href = window.location.pathname;
    }

    refreshKanban() {
        location.reload();
    }

    resetTaskForm() {
        if (this.taskForm) {
            this.taskForm.reset();
        }
    }

    prepareEditModal() {
        // Preparar modal de edición si es necesario
    }

    // ===== MODAL MANAGEMENT =====

    openModal(modalName) {
        if (this.modals && this.modals[modalName]) {
            this.modals[modalName].show();
        }
    }

    closeModal(modalName) {
        if (this.modals && this.modals[modalName]) {
            this.modals[modalName].hide();
        }
    }

    // ===== UTILITIES =====

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    showNotification(message, type = 'info') {
        // Usar el sistema de notificaciones moderno
        if (window.notifications) {
            // Solo mostrar notificaciones para acciones importantes
            if (type === 'error' || type === 'success') {
                window.notifications.show(message, type);
            }
        } else {
            console.warn('Sistema de notificaciones no disponible:', message);
        }
    }

    // ===== STATISTICS UPDATE =====

    updateStatistics() {
        // Actualizar estadísticas en tiempo real si es necesario
        // Actualización visual deshabilitada
    }
}

// ===== INITIALIZATION =====

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar KanbanManager
    window.kanbanManager = new KanbanManager();
    
    // Funciones globales para compatibilidad
    window.clearFilters = function() {
        window.kanbanManager.clearFilters();
    };
    
    window.refreshKanban = function() {
        window.kanbanManager.refreshKanban();
    };
    
    if (typeof window.showTaskDetails !== 'function') {
        window.showTaskDetails = function(taskId) {
            window.kanbanManager.viewTask(taskId);
        };
    }
    
    window.updateTaskStatus = function(taskId, newStatus) {
        window.kanbanManager.updateTaskStatusSilently(taskId, newStatus);
    };
    
    window.deleteKanbanTask = function(taskId) {
        window.kanbanManager.deleteTask(taskId);
    };
});

// ===== EXPORT FOR MODULE SYSTEMS =====

if (typeof module !== 'undefined' && module.exports) {
    module.exports = KanbanManager;
}
