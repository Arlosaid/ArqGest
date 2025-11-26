/**
 * Task Delete Manager
 * Sistema unificado para eliminación de tareas con modales visuales
 */

class TaskDeleteManager {
    constructor() {
        this.init();
    }

    init() {
        // Manejador global para botones de eliminar tarea
        document.addEventListener('click', (e) => {
            const deleteBtn = e.target.closest('[data-action="delete-task"]');
            if (deleteBtn) {
                // Ignorar si el botón está dentro del Kanban (kanban.js maneja su propia eliminación)
                const isInKanban = deleteBtn.closest('.kanban-board') || 
                                   deleteBtn.closest('.kanban-card') ||
                                   deleteBtn.closest('.kanban-column');
                
                if (isInKanban) {
                    // Dejar que kanban.js maneje la eliminación
                    return;
                }
                
                e.preventDefault();
                e.stopPropagation();
                
                const taskId = deleteBtn.dataset.taskId;
                const taskTitle = deleteBtn.dataset.taskTitle || 'esta tarea';
                const taskDescription = deleteBtn.dataset.taskDescription || '';
                
                this.confirmDelete(taskId, taskTitle, taskDescription);
            }
        });
    }

    confirmDelete(taskId, taskTitle, taskDescription = '') {
        ConfirmationModals.deleteTask({
            taskId: taskId,
            taskTitle: taskTitle,
            taskDescription: taskDescription,
            onConfirm: async () => {
                await this.deleteTask(taskId);
            }
        });
    }

    async deleteTask(taskId) {
        const url = `/projects/tasks/${taskId}/delete/`;

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });

            const data = await response.json();

            if (data.success) {
                // Intentar eliminar la tarea del DOM según el contexto
                this.removeTaskFromUI(taskId);
                
                // Mostrar mensaje de éxito
                this.showSuccessMessage('Tarea eliminada correctamente');

                // Si estamos en el kanban, actualizar
                if (typeof window.updateKanbanAfterDelete === 'function') {
                    window.updateKanbanAfterDelete(taskId);
                }

                // Si estamos en mis tareas, actualizar contadores
                if (typeof window.updateTaskDeleteCounter === 'function') {
                    const taskCard = document.querySelector(`[data-task-id="${taskId}"]`);
                    if (taskCard) {
                        const taskStatus = taskCard.dataset.status;
                        window.updateTaskDeleteCounter(taskStatus);
                    }
                }

                // Broadcast para sincronización entre pestañas
                this.broadcastTaskDeletion(taskId);

            } else {
                this.showErrorMessage(data.error || 'Error al eliminar la tarea');
            }

        } catch (error) {
            console.error('Error deleting task:', error);
            this.showErrorMessage('Error de conexión al eliminar la tarea');
        }
    }

    removeTaskFromUI(taskId) {
        // Buscar la tarea en diferentes contextos
        const taskSelectors = [
            `[data-task-id="${taskId}"]`,
            `#task-${taskId}`,
            `.task-card[data-task-id="${taskId}"]`,
            `.task-item[data-task-id="${taskId}"]`
        ];

        for (const selector of taskSelectors) {
            const taskElement = document.querySelector(selector);
            if (taskElement) {
                // Animación de salida
                taskElement.style.transition = 'all 0.3s ease';
                taskElement.style.transform = 'scale(0.8)';
                taskElement.style.opacity = '0';

                setTimeout(() => {
                    taskElement.remove();
                    this.checkEmptyState();
                }, 300);
                
                break;
            }
        }

        // Si estamos en el modal de edición de tarea, cerrarlo
        const taskModal = document.getElementById('taskEditModal');
        if (taskModal) {
            const modalInstance = bootstrap.Modal.getInstance(taskModal);
            if (modalInstance) {
                modalInstance.hide();
            }
        }
    }

    checkEmptyState() {
        // Verificar si quedan tareas
        const taskContainers = document.querySelectorAll('.kanban-column, #tasksList');
        
        taskContainers.forEach(container => {
            const tasks = container.querySelectorAll('[data-task-id]');
            if (tasks.length === 0) {
                // Mostrar estado vacío si es necesario
                if (container.id === 'tasksList' && typeof showEmptyState === 'function') {
                    showEmptyState();
                }
            }
        });
    }

    broadcastTaskDeletion(taskId) {
        try {
            const event = {
                type: 'TASK_DELETED',
                taskId: taskId,
                timestamp: Date.now()
            };

            localStorage.setItem('task_delete_event', JSON.stringify(event));
            
            setTimeout(() => {
                localStorage.removeItem('task_delete_event');
            }, 100);
        } catch (error) {
            console.error('Error broadcasting task deletion:', error);
        }
    }

    showSuccessMessage(message) {
        this.showToast(message, 'success');
    }

    showErrorMessage(message) {
        this.showToast(message, 'error');
    }

    showToast(message, type = 'success') {
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

        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '1055';
            document.body.appendChild(toastContainer);
        }

        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        const toastElement = toastContainer.lastElementChild;
        const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
        toast.show();

        toastElement.addEventListener('hidden.bs.toast', function () {
            this.remove();
        });
    }

    getCsrfToken() {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; csrftoken=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return '';
    }
}

// Inicializar automáticamente
document.addEventListener('DOMContentLoaded', () => {
    window.taskDeleteManager = new TaskDeleteManager();
});

// Escuchar eventos de eliminación de tareas desde otras pestañas
window.addEventListener('storage', (e) => {
    if (e.key === 'task_delete_event' && e.newValue) {
        try {
            const event = JSON.parse(e.newValue);
            if (event.type === 'TASK_DELETED') {
                // Eliminar la tarea de la UI si existe
                const taskElement = document.querySelector(`[data-task-id="${event.taskId}"]`);
                if (taskElement) {
                    taskElement.remove();
                }
            }
        } catch (error) {
            console.error('Error processing task deletion event:', error);
        }
    }
});
