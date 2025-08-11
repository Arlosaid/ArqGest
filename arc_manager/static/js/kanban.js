/**
 * KANBAN - FUNCIONALIDADES JAVASCRIPT
 * ===================================
 * 
 * Este archivo contiene todas las funcionalidades JavaScript específicas
 * para el tablero Kanban en ArcManager.
 */

class KanbanManager {
    constructor() {
        this.groupMode = document.querySelector('.kanban-board')?.dataset.groupBy || 'phase';
        this.init();
    }

    /**
     * Inicializa todas las funcionalidades del Kanban
     */
    init() {
        this.initDragAndDrop();
        this.initModals();
        this.initQuickAdd();
        this.initStatistics();
        this.initResponsiveBehavior();
        this.initAnimations();

        // Estado inicial de contadores y placeholders
        this.updateColumnCounters();
        this.syncEmptyStates();
    }

    /**
     * DRAG AND DROP
     * =============
     */
    initDragAndDrop() {
        const columns = document.querySelectorAll('.kanban-column-body');
        
        columns.forEach(column => {
            new Sortable(column, {
                group: 'kanban',
                animation: 150,
                ghostClass: 'kanban-card-ghost',
                chosenClass: 'kanban-card-chosen',
                dragClass: 'kanban-card-drag',
                onStart: (evt) => {
                    this.onDragStart(evt);
                },
                onEnd: (evt) => {
                    this.onDragEnd(evt);
                },
                onAdd: (evt) => {
                    this.onCardAdded(evt);
                },
                onRemove: (evt) => {
                    this.onCardRemoved(evt);
                }
            });
        });
    }

    /**
     * Evento cuando comienza el drag
     */
    onDragStart(evt) {
        evt.item.classList.add('dragging');
        
        // Agregar overlay de arrastre
        const overlay = document.createElement('div');
        overlay.className = 'drag-overlay';
        overlay.innerHTML = `
            <div class="drag-overlay-content">
                <i class="fas fa-grip-vertical"></i>
                <span>Arrastrando tarea...</span>
            </div>
        `;
        document.body.appendChild(overlay);
        
        // Posicionar overlay
        const rect = evt.item.getBoundingClientRect();
        overlay.style.left = rect.left + 'px';
        overlay.style.top = rect.top + 'px';
        overlay.style.width = rect.width + 'px';
        overlay.style.height = rect.height + 'px';
    }

    /**
     * Evento cuando termina el drag
     */
    onDragEnd(evt) {
        evt.item.classList.remove('dragging');
        
        // Remover overlay
        const overlay = document.querySelector('.drag-overlay');
        if (overlay) {
            overlay.remove();
        }
        
        // Actualizar contadores
        this.updateColumnCounters();
        
        // Si la tarea cambió de columna, actualizar en el servidor según modo
        const fromAttr = this.groupMode === 'status' ? 'statusCode' : 'phaseId';
        const toAttr = this.groupMode === 'status' ? 'statusCode' : 'phaseId';
        if (evt.from.dataset[fromAttr] !== evt.to.dataset[toAttr]) {
            if (this.groupMode === 'status') {
                this.updateTaskStatus(evt);
            } else {
                this.updateTaskPhase(evt);
            }
        }
    }

    /**
     * Evento cuando se agrega una tarjeta
     */
    onCardAdded(evt) {
        const card = evt.item;
        card.style.animation = 'slideIn 0.3s ease-out';
        
        // Actualizar contadores
        this.updateColumnCounters();
        this.syncEmptyStates();
    }

    /**
     * Evento cuando se remueve una tarjeta
     */
    onCardRemoved(evt) {
        // Actualizar contadores
        this.updateColumnCounters();
        this.syncEmptyStates();
    }

    /**
     * Actualiza la fase de una tarea en el servidor
     */
    updateTaskPhase(evt) {
        const taskCard = evt.item;
        const taskId = taskCard.dataset.taskId;
        const toPhaseId = evt.to.dataset.phaseId;
        
        if (!taskId || !toPhaseId) return;
        
        const moveUrl = `/projects/tasks/${taskId}/move/`;
        
        fetch(moveUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken(),
                'Accept': 'application/json'
            },
            credentials: 'same-origin',
            body: JSON.stringify({ 'phase_id': toPhaseId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showNotification('Tarea movida correctamente', 'success');
                this.updateStatistics();
                this.syncEmptyStates();
            } else {
                this.showNotification('Error al mover la tarea', 'error');
                // Revertir el movimiento
                evt.from.appendChild(taskCard);
                this.updateColumnCounters();
                this.syncEmptyStates();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            this.showNotification('Error al mover la tarea', 'error');
            // Revertir el movimiento
            evt.from.appendChild(taskCard);
            this.updateColumnCounters();
            this.syncEmptyStates();
        });
    }

    /**
     * Actualiza el estado de una tarea en el servidor (modo group_by = status)
     */
    updateTaskStatus(evt) {
        const taskCard = evt.item;
        const taskId = taskCard.dataset.taskId;
        const toStatus = evt.to.dataset.statusCode;

        if (!taskId || !toStatus) return;

        const url = `/projects/tasks/${taskId}/update_status/`;

        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken(),
                'Accept': 'application/json'
            },
            body: JSON.stringify({ status: toStatus })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showNotification('Estado actualizado', 'success');
                this.updateStatistics();
                this.syncEmptyStates();
            } else {
                this.showNotification('Error al actualizar estado', 'error');
                // Revertir movimiento
                evt.from.appendChild(taskCard);
                this.updateColumnCounters();
                this.syncEmptyStates();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            this.showNotification('Error al actualizar estado', 'error');
            // Revertir movimiento
            evt.from.appendChild(taskCard);
            this.updateColumnCounters();
            this.syncEmptyStates();
        });
    }

    /**
     * MODALES
     * =======
     */
    initModals() {
        // Modal para editar tarea
        this.initTaskEditModal();
        
        // Modal para agregar tarea
        this.initAddTaskModal();
        
        // Event listeners para modales
        this.initModalEventListeners();
    }

    /**
     * Inicializa modal de edición de tarea
     */
    initTaskEditModal() {
        const taskModal = document.getElementById('taskModal');
        if (!taskModal) return;

        // Event listener para cuando se carga contenido en el modal
        taskModal.addEventListener('show.bs.modal', (event) => {
            const button = event.relatedTarget;
            // Si viene desde un botón o desde apertura programática, detectar el taskId
            let taskId = null;
            if (button) {
                taskId = button.closest('.kanban-card')?.dataset.taskId || button?.dataset?.taskId;
            }
            if (!taskId && taskModal.dataset.taskId) {
                taskId = taskModal.dataset.taskId;
            }
            
            if (taskId) {
                const editUrl = `/projects/tasks/${taskId}/edit/`;
                this.loadModalContent(taskModal, editUrl);
            }
        });

        // Delegación: eliminar tarea desde el modal
        document.addEventListener('click', (e) => {
            const deleteBtn = e.target.closest('#deleteTaskBtn');
            if (!deleteBtn) return;
            const taskId = deleteBtn.getAttribute('data-task-id');
            if (!taskId) return;
            this.handleDeleteTask(taskId);
        });
    }

    /**
     * Hacer las tarjetas clicables para editar
     */
    initCardClickEdit() {
        const cards = document.querySelectorAll('.kanban-card');
        const taskModal = document.getElementById('taskModal');
        if (!taskModal) return;

        cards.forEach(card => {
            card.addEventListener('click', (e) => {
                // Evitar conflicto si en el futuro hay botones internos
                if (e.target.closest('button, a, .btn')) return;
                const taskId = card.dataset.taskId;
                if (!taskId) return;
                // Guardar taskId en el modal para que show.bs.modal lo detecte
                taskModal.dataset.taskId = taskId;
                const modal = new bootstrap.Modal(taskModal);
                modal.show();
            });
        });
    }

    /**
     * Inicializa modal para agregar tarea
     */
    initAddTaskModal() {
        const addTaskModal = document.getElementById('addTaskModal');
        if (!addTaskModal) return;

        addTaskModal.addEventListener('show.bs.modal', (event) => {
            const button = event.relatedTarget;
            const phaseId = button ? button.getAttribute('data-phase') : null;
            
            if (phaseId) {
                const phaseSelect = addTaskModal.querySelector('#task-phase');
                if (phaseSelect) {
                    phaseSelect.value = phaseId;
                }
            } else {
                // Si no viene phaseId, preseleccionar la primera opción disponible
                const phaseSelect = addTaskModal.querySelector('#task-phase');
                if (phaseSelect && !phaseSelect.value && phaseSelect.options.length > 0) {
                    phaseSelect.selectedIndex = 0;
                }
            }
        });

        // El envío del formulario lo maneja tasks.js de forma unificada
    }

    /**
     * Inicializa event listeners para modales
     */
    initModalEventListeners() {
        // Cerrar modal con Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const openModal = document.querySelector('.modal.show');
                if (openModal) {
                    const modal = bootstrap.Modal.getInstance(openModal);
                    if (modal) {
                        modal.hide();
                    }
                }
            }
        });

        // Cerrar modal al hacer clic fuera
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                const modal = bootstrap.Modal.getInstance(e.target);
                if (modal) {
                    modal.hide();
                }
            }
        });
    }

    /**
     * Carga contenido en un modal
     */
    loadModalContent(modal, url) {
        const modalContent = modal.querySelector('.modal-content');
        
        fetch(url)
            .then(response => response.text())
            .then(html => {
                modalContent.innerHTML = html;
            })
            .catch(error => {
                console.error('Error loading modal content:', error);
                modalContent.innerHTML = `
                    <div class="modal-header">
                        <h5 class="modal-title">Error</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>Error al cargar el contenido.</p>
                    </div>
                `;
            });
    }

    /**
     * Maneja la creación de una nueva tarea
     */
    handleAddTask(event, form) {
        event.preventDefault();
        
        const formData = new FormData(form);
        const submitButton = form.querySelector('button[type="submit"]');
        const originalText = submitButton.innerHTML;
        
        // Mostrar estado de carga
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creando...';
        
        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': this.getCSRFToken(),
                'Accept': 'application/json'
            },
            credentials: 'same-origin'
        })
        .then(response => {
            // Permitir fallback a texto/redirect si el backend aun no devuelve JSON
            const contentType = response.headers.get('Content-Type') || '';
            if (contentType.includes('application/json')) {
                return response.json();
            }
            if (response.ok) {
                return { success: true };
            }
            throw new Error('Bad response');
        })
        .then(data => {
            if (data && data.success) {
                this.showNotification('Tarea creada correctamente', 'success');
                
                // Cerrar modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('addTaskModal'));
                modal.hide();
                
                // Recargar página para mostrar la nueva tarea
                setTimeout(() => {
                    location.reload();
                }, 500);
            } else {
                this.showNotification('Error al crear la tarea', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            this.showNotification('Error al crear la tarea', 'error');
        })
        .finally(() => {
            // Restaurar botón
            submitButton.disabled = false;
            submitButton.innerHTML = originalText;
        });
    }

    /**
     * AGREGAR TAREA RÁPIDA
     * =====================
     */
    initQuickAdd() {
        const quickAddForms = document.querySelectorAll('.add-task-form');
        
        quickAddForms.forEach(form => {
            form.addEventListener('submit', (e) => {
                this.handleQuickAdd(e, form);
            });
        });
    }

    /**
     * Maneja la agregación rápida de tareas
     */
    handleQuickAdd(event, form) {
        event.preventDefault();
        
        const input = form.querySelector('input[name="title"]');
        const title = input.value.trim();
        
        if (!title) {
            input.focus();
            return;
        }
        
        const formData = new FormData(form);
        const submitButton = form.querySelector('button[type="submit"]');
        const originalHTML = submitButton.innerHTML;
        
        // Mostrar estado de carga
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        
        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': this.getCSRFToken(),
                'Accept': 'application/json'
            }
        })
        .then(response => {
            const contentType = response.headers.get('Content-Type') || '';
            if (contentType.includes('application/json')) {
                return response.json();
            }
            if (response.ok) {
                return { success: true };
            }
            throw new Error('Bad response');
        })
        .then(data => {
            if (data && data.success) {
                // Limpiar input
                input.value = '';
                
                // Mostrar notificación
                this.showNotification('Tarea agregada correctamente', 'success');
                
                // Recargar página para mostrar la nueva tarea
                setTimeout(() => {
                    location.reload();
                }, 300);
            } else {
                this.showNotification('Error al agregar la tarea', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            this.showNotification('Error al agregar la tarea', 'error');
        })
        .finally(() => {
            // Restaurar botón
            submitButton.disabled = false;
            submitButton.innerHTML = originalHTML;
        });
    }

    /**
     * ESTADÍSTICAS
     * ============
     */
    initStatistics() {
        this.updateStatistics();
        
        // Actualizar estadísticas cada 30 segundos
        setInterval(() => {
            this.updateStatistics();
        }, 30000);
    }

    /**
     * Actualiza las estadísticas del proyecto
     */
    updateStatistics() {
        const projectId = this.getProjectId();
        if (!projectId) return;
        
        fetch(`/projects/${projectId}/statistics/`)
            .then(response => response.json())
            .then(data => {
                this.updateStatisticsDisplay(data);
            })
            .catch(error => {
                console.error('Error updating statistics:', error);
            });
    }

    /**
     * Actualiza la visualización de estadísticas
     */
    updateStatisticsDisplay(data) {
        const statCards = document.querySelectorAll('.stat-card');
        
        statCards.forEach(card => {
            const numberElement = card.querySelector('.stat-number');
            const labelElement = card.querySelector('.stat-label');
            
            if (numberElement && labelElement) {
                const label = labelElement.textContent.toLowerCase();
                
                if (label.includes('total')) {
                    numberElement.textContent = data.total_tasks || 0;
                } else if (label.includes('completadas')) {
                    numberElement.textContent = data.completed_tasks || 0;
                } else if (label.includes('progreso')) {
                    numberElement.textContent = data.in_progress_tasks || 0;
                } else if (label.includes('pausadas')) {
                    numberElement.textContent = data.paused_tasks || 0;
                }
            }
        });
    }

    /**
     * COMPORTAMIENTO RESPONSIVE
     * =========================
     */
    initResponsiveBehavior() {
        this.adjustKanbanLayout();
        
        window.addEventListener('resize', this.debounce(() => {
            this.adjustKanbanLayout();
        }, 250));
    }

    /**
     * Ajusta el layout del Kanban según el tamaño de pantalla
     */
    adjustKanbanLayout() {
        const width = window.innerWidth;
        const kanbanBoard = document.querySelector('.kanban-board');
        
        if (!kanbanBoard) return;
        
        if (width < 768) {
            kanbanBoard.style.gap = '1rem';
        } else if (width < 1200) {
            kanbanBoard.style.gap = '1.5rem';
        } else {
            kanbanBoard.style.gap = '2rem';
        }
    }

    /**
     * ANIMACIONES
     * ===========
     */
    initAnimations() {
        this.animateCards();
        this.initScrollAnimations();
    }

    /**
     * Anima las tarjetas al cargar
     */
    animateCards() {
        const cards = document.querySelectorAll('.kanban-card');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry, index) => {
                if (entry.isIntersecting) {
                    entry.target.style.animationDelay = `${index * 0.1}s`;
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });

        cards.forEach(card => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            observer.observe(card);
        });
    }

    /**
     * Inicializa animaciones de scroll
     */
    initScrollAnimations() {
        const columns = document.querySelectorAll('.kanban-column-body');
        
        columns.forEach(column => {
            column.addEventListener('scroll', this.debounce(() => {
                this.handleColumnScroll(column);
            }, 100));
        });
    }

    /**
     * Maneja el scroll de las columnas
     */
    handleColumnScroll(column) {
        const cards = column.querySelectorAll('.kanban-card');
        
        cards.forEach(card => {
            const rect = card.getBoundingClientRect();
            const isVisible = rect.top < window.innerHeight && rect.bottom > 0;
            
            if (isVisible) {
                card.classList.add('visible');
            }
        });
    }

    /**
     * UTILIDADES
     * ==========
     */
    
    /**
     * Actualiza los contadores de las columnas
     */
    updateColumnCounters() {
        document.querySelectorAll('.kanban-column').forEach(column => {
            const body = column.querySelector('.kanban-column-body');
            const counter = column.querySelector('.task-count');
            
            if (body && counter) {
                const taskCount = body.querySelectorAll('.kanban-card').length;
                const label = taskCount === 1 ? '1 tarea' : `${taskCount} tareas`;
                counter.textContent = label;
            }
        });
    }

    /**
     * Sincroniza los placeholders vacíos (casco) por columna
     */
    syncEmptyStates() {
        document.querySelectorAll('.kanban-column-body').forEach(body => {
            const cards = body.querySelectorAll('.kanban-card');
            const empty = body.querySelector('.empty-column');
            if (cards.length === 0) {
                if (!empty) {
                    const emptyEl = document.createElement('div');
                    emptyEl.className = 'empty-column';
                    emptyEl.innerHTML = `
                        <div class="empty-icon"><i class="fas fa-helmet-safety"></i></div>
                        <p class="empty-text">Sin tareas</p>
                    `;
                    body.appendChild(emptyEl);
                }
            } else {
                if (empty) empty.remove();
            }
        });
    }

    /**
     * Obtiene el ID del proyecto desde la URL
     */
    getProjectId() {
        const path = window.location.pathname;
        const match = path.match(/\/projects\/(\d+)\/kanban/);
        return match ? match[1] : null;
    }

    /**
     * Obtiene el token CSRF
     */
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1] || '';
    }

    /**
     * Función debounce para optimizar eventos
     */
    debounce(func, wait) {
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

    /**
     * Muestra notificaciones
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type} kanban-notification`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;

        document.body.appendChild(notification);
        
        // Mostrar con animación
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);

        // Auto-ocultar después de 3 segundos
        setTimeout(() => {
            this.hideNotification(notification);
        }, 3000);

        // Cerrar manualmente
        notification.querySelector('.notification-close').addEventListener('click', () => {
            this.hideNotification(notification);
        });
    }

    /**
     * Elimina una tarea por ID (desde el modal). Actualiza UI sin recargar.
     */
    handleDeleteTask(taskId) {
        if (!confirm('¿Eliminar esta tarea? Esta acción no se puede deshacer.')) return;
        fetch(`/projects/tasks/${taskId}/delete/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken(),
                'Accept': 'application/json'
            }
        })
        .then(r => r.json())
        .then(data => {
            if (data && data.success) {
                // Cerrar modal
                const taskModal = document.getElementById('taskModal');
                if (taskModal) {
                    const modal = bootstrap.Modal.getInstance(taskModal) || new bootstrap.Modal(taskModal);
                    modal.hide();
                }
                // Quitar tarjeta
                const card = document.querySelector(`.kanban-card[data-task-id="${taskId}"]`);
                if (card) card.remove();
                this.updateColumnCounters();
                this.syncEmptyStates();
                this.showNotification('Tarea eliminada', 'success');
            } else {
                this.showNotification('No se pudo eliminar la tarea', 'error');
            }
        })
        .catch(() => this.showNotification('Error al eliminar la tarea', 'error'));
    }

    /**
     * Oculta notificación
     */
    hideNotification(notification) {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }

    /**
     * Exporta datos del Kanban
     */
    exportKanbanData() {
        const projectId = this.getProjectId();
        if (!projectId) return;
        
        fetch(`/projects/${projectId}/export/`)
            .then(response => response.blob())
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `proyecto-${projectId}-kanban.xlsx`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            })
            .catch(error => {
                console.error('Error exporting data:', error);
                this.showNotification('Error al exportar datos', 'error');
            });
    }

    /**
     * Imprime el tablero Kanban
     */
    printKanban() {
        window.print();
    }

    /**
     * Comparte el tablero Kanban
     */
    shareKanban() {
        const url = window.location.href;
        
        if (navigator.share) {
            navigator.share({
                title: 'Tablero Kanban - ArcManager',
                url: url
            });
        } else {
            // Fallback: copiar al portapapeles
            navigator.clipboard.writeText(url).then(() => {
                this.showNotification('URL copiada al portapapeles', 'success');
            }).catch(() => {
                this.showNotification('Error al copiar URL', 'error');
            });
        }
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new KanbanManager();
});

// Exportar para uso global si es necesario
window.KanbanManager = KanbanManager;

window.KanbanManager = KanbanManager;
