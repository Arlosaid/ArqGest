/**
 * TAREAS - JavaScript v1.0
 * Funcionalidades para el módulo de tareas
 * Consistente con el sistema de diseño de la aplicación
 */

class TaskManager {
    constructor() {
        this.currentFilters = {
            status: '',
            priority: '',
            project: '',
            search: ''
        };
        
        this.initializeElements();
        this.initializeFilters();
        this.initializeEventListeners();
        this.loadSavedFilters();
        this.applyFilters();
    }

    initializeElements() {
        this.statusFilter = document.getElementById('statusFilter');
        this.priorityFilter = document.getElementById('priorityFilter');
        this.projectFilter = document.getElementById('projectFilter');
        this.searchInput = document.getElementById('searchInput');
        this.tasksList = document.getElementById('tasksList') || document.getElementById('projectTasksList');
        this.clearFiltersBtn = document.querySelector('.clear-filters-btn');
        
        if (!this.tasksList) {
            console.warn('TaskManager: No se encontró la lista de tareas');
            return;
        }
    }

    initializeFilters() {
        // Inicializar filtros si existen y enlazar eventos
        if (this.statusFilter) {
            this.statusFilter.addEventListener('change', () => {
                this.currentFilters.status = this.statusFilter.value;
                this.saveFilters();
                this.applyFilters();
            });
        }
        if (this.priorityFilter) {
            this.priorityFilter.addEventListener('change', () => {
                this.currentFilters.priority = this.priorityFilter.value;
                this.saveFilters();
                this.applyFilters();
            });
        }
        if (this.projectFilter) {
            this.projectFilter.addEventListener('input', this.debounce(() => {
                this.currentFilters.project = (this.projectFilter.value || '').toLowerCase();
                this.saveFilters();
                this.applyFilters();
            }, 250));
        }
        if (this.searchInput) {
            this.searchInput.addEventListener('input', this.debounce(() => {
                this.currentFilters.search = this.searchInput.value;
                this.saveFilters();
                this.applyFilters();
            }, 300));
        }
        if (this.clearFiltersBtn) {
            this.clearFiltersBtn.addEventListener('click', () => this.clearFilters());
        }
    }

    initializeEventListeners() {
        // Agregar event listeners para ver detalles de tarea
        if (this.tasksList) {
            this.tasksList.addEventListener('click', (e) => {
                if (e.target.classList.contains('task-detail-btn') || 
                    e.target.closest('.task-detail-btn')) {
                    e.preventDefault();
                    const taskItem = e.target.closest('.task-item');
                    if (taskItem) {
                        this.showTaskDetails(taskItem);
                    }
                }
            });
        }
        
        // Cerrar modal con Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeTaskDetails();
            }
        });
        
        // Cerrar modal haciendo clic fuera
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('task-detail-modal')) {
                this.closeTaskDetails();
            }
        });
    }

    showTaskDetails(taskItem) {
        const taskData = this.extractTaskData(taskItem);
        const modal = this.createTaskDetailModal(taskData);
        
        // Agregar modal al DOM
        document.body.appendChild(modal);
        
        // Mostrar modal sin animaciones costosas
        modal.classList.add('show');
        
        // Enfocar el modal para accesibilidad
        const closeBtn = modal.querySelector('.task-detail-close');
        if (closeBtn) {
            closeBtn.focus();
        }
    }

    extractTaskData(taskItem) {
        return {
            id: taskItem.dataset.taskId || taskItem.getAttribute('data-task-id'),
            title: taskItem.querySelector('.task-title')?.textContent || 'Sin título',
            description: taskItem.querySelector('.task-description')?.textContent || 'Sin descripción',
            status: taskItem.dataset.status || 'TODO',
            priority: taskItem.dataset.priority || 'MEDIUM',
            phase: taskItem.dataset.phase || 'Sin fase',
            assignedTo: taskItem.querySelector('.task-assigned span')?.textContent || 'Sin asignar',
            dueDate: taskItem.querySelector('.task-due-date span')?.textContent || 'Sin fecha',
            project: taskItem.dataset.project || 'Sin proyecto'
        };
    }

    createTaskDetailModal(taskData) {
        const modal = document.createElement('div');
        modal.className = 'task-detail-modal';
        modal.innerHTML = `
            <div class="task-detail-content">
                <div class="task-detail-header">
                    <h3>${taskData.title}</h3>
                    <p class="task-detail-subtitle">${taskData.project} - ${taskData.phase}</p>
                    <button class="task-detail-close" aria-label="Cerrar">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                
                <div class="task-detail-body">
                    <div class="task-detail-section">
                        <h4 class="task-detail-section-title">Descripción</h4>
                        <div class="task-detail-description">${taskData.description}</div>
                    </div>
                    
                    <div class="task-detail-section">
                        <h4 class="task-detail-section-title">Información de la Tarea</h4>
                        <div class="task-detail-grid">
                            <div class="task-detail-item">
                                <span class="task-detail-label">Estado</span>
                                <span class="task-detail-value">
                                    <span class="task-status-badge ${this.getStatusClass(taskData.status)}">
                                        ${this.getStatusDisplay(taskData.status)}
                                    </span>
                                </span>
                            </div>
                            <div class="task-detail-item">
                                <span class="task-detail-label">Prioridad</span>
                                <span class="task-detail-value">
                                    <span class="task-priority-badge ${this.getPriorityClass(taskData.priority)}">
                                        ${this.getPriorityDisplay(taskData.priority)}
                                    </span>
                                </span>
                            </div>
                            <div class="task-detail-item">
                                <span class="task-detail-label">Fase</span>
                                <span class="task-detail-value">${taskData.phase}</span>
                            </div>
                            <div class="task-detail-item">
                                <span class="task-detail-label">Asignado a</span>
                                <span class="task-detail-value">${taskData.assignedTo}</span>
                            </div>
                            <div class="task-detail-item">
                                <span class="task-detail-label">Fecha de vencimiento</span>
                                <span class="task-detail-value">${taskData.dueDate}</span>
                            </div>
                            <div class="task-detail-item">
                                <span class="task-detail-label">Proyecto</span>
                                <span class="task-detail-value">${taskData.project}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="task-detail-section">
                        <h4 class="task-detail-section-title">Acciones</h4>
                        <div class="task-detail-actions">
                            ${this.generateActionButtons(taskData)}
                        </div>
                    </div>
                </div>
                
                <div class="task-detail-footer">
                    <div class="task-detail-meta">
                        <span><i class="fas fa-clock"></i> Última actualización: ${new Date().toLocaleDateString()}</span>
                    </div>
                    <button class="task-action-btn secondary" onclick="this.closest('.task-detail-modal').remove()">
                        <i class="fas fa-times"></i> Cerrar
                    </button>
                </div>
            </div>
        `;
        
        // Agregar event listener para cerrar
        const closeBtn = modal.querySelector('.task-detail-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeTaskDetails());
        }
        
        return modal;
    }

    generateActionButtons(taskData) {
        let buttons = '';
        
        // Botón de editar (siempre disponible)
        buttons += `
            <a href="/projects/tasks/${taskData.id}/edit/" class="task-action-btn secondary">
                <i class="fas fa-edit"></i> Editar
            </a>
        `;
        
        // Botones de estado según el estado actual
        switch (taskData.status) {
            case 'TODO':
                buttons += `
                    <button type="button" class="task-action-btn primary" onclick="window.taskManager.updateTaskStatus('${taskData.id}','IN_PROGRESS')">
                        <i class="fas fa-play"></i> Iniciar
                    </button>
                `;
                break;
            case 'IN_PROGRESS':
                buttons += `
                    <button type="button" class="task-action-btn warning" onclick="window.taskManager.updateTaskStatus('${taskData.id}','PAUSED')">
                        <i class="fas fa-pause"></i> Pausar
                    </button>
                    <button type="button" class="task-action-btn success" onclick="window.taskManager.updateTaskStatus('${taskData.id}','DONE')">
                        <i class="fas fa-check"></i> Completar
                    </button>
                `;
                break;
            case 'PAUSED':
                buttons += `
                    <button type="button" class="task-action-btn primary" onclick="window.taskManager.updateTaskStatus('${taskData.id}','IN_PROGRESS')">
                        <i class="fas fa-play"></i> Reanudar
                    </button>
                `;
                break;
        }
        
        return buttons;
    }

    getStatusClass(status) {
        const statusClasses = {
            'TODO': 'todo',
            'IN_PROGRESS': 'in-progress',
            'PAUSED': 'paused',
            'DONE': 'done'
        };
        return statusClasses[status] || 'todo';
    }

    getStatusDisplay(status) {
        const statusDisplay = {
            'TODO': 'Pendiente',
            'IN_PROGRESS': 'En Progreso',
            'PAUSED': 'Pausada',
            'DONE': 'Completada'
        };
        return statusDisplay[status] || 'Pendiente';
    }

    getPriorityClass(priority) {
        const priorityClasses = {
            'LOW': 'low',
            'MEDIUM': 'medium',
            'HIGH': 'high'
        };
        return priorityClasses[priority] || 'medium';
    }

    getPriorityDisplay(priority) {
        const priorityDisplay = {
            'LOW': 'Baja',
            'MEDIUM': 'Media',
            'HIGH': 'Alta'
        };
        return priorityDisplay[priority] || 'Media';
    }

    closeTaskDetails() {
        const modal = document.querySelector('.task-detail-modal');
        if (modal) {
            modal.classList.remove('show');
            setTimeout(() => {
                modal.remove();
            }, 300);
        }
    }

    /**
     * Vincula los eventos a los elementos
     */
    bindEvents() {
        // Filtros
        if (this.statusFilter) {
            this.statusFilter.addEventListener('change', (e) => {
                this.currentFilters.status = e.target.value;
                this.applyFilters();
            });
        }

        if (this.priorityFilter) {
            this.priorityFilter.addEventListener('change', (e) => {
                this.currentFilters.priority = e.target.value;
                this.applyFilters();
            });
        }

        // Búsqueda con debounce
        if (this.searchInput) {
            this.searchInput.addEventListener('input', this.debounce((e) => {
                this.currentFilters.search = e.target.value.toLowerCase();
                this.applyFilters();
            }, 300));
        }

        // Eventos de las tareas
        this.bindTaskEvents();
    }

    /**
     * Vincula eventos a las tareas individuales
     */
    bindTaskEvents() {
        if (!this.tasksList) return;

        // Eventos de hover para las tareas
        const taskItems = this.tasksList.querySelectorAll('.task-item');
        taskItems.forEach(taskItem => {
            // Desactivar micro-animaciones de hover para mejorar rendimiento

            // Eventos para los botones de acción
            const actionButtons = taskItem.querySelectorAll('.task-action-btn');
            actionButtons.forEach(button => {
                // Sin efecto de click
                button.addEventListener('click', () => {});
            });
        });
    }

    /**
     * Inicializa los filtros con valores por defecto
     */
    loadSavedFilters() {
        // Restaurar filtros guardados en localStorage si existen
        const savedFilters = localStorage.getItem('taskFilters');
        if (savedFilters) {
            try {
                this.currentFilters = JSON.parse(savedFilters);
                this.applySavedFilters();
            } catch (e) {
                console.warn('Error al restaurar filtros guardados:', e);
            }
        }
    }

    /**
     * Aplica los filtros guardados
     */
    applySavedFilters() {
        if (this.statusFilter && this.currentFilters.status) {
            this.statusFilter.value = this.currentFilters.status;
        }
        if (this.priorityFilter && this.currentFilters.priority) {
            this.priorityFilter.value = this.currentFilters.priority;
        }
        if (this.projectFilter && this.currentFilters.project) {
            this.projectFilter.value = this.currentFilters.project;
        }
        if (this.searchInput && this.currentFilters.search) {
            this.searchInput.value = this.currentFilters.search;
        }
    }

    /**
     * Aplica los filtros actuales a las tareas
     */
    applyFilters() {
        if (!this.tasksList) return;
        
        const taskItems = this.tasksList.querySelectorAll('.task-item');
        let visibleCount = 0;
        let hiddenCount = 0;
        
        taskItems.forEach(taskItem => {
            const shouldShow = this.taskMatchesFilters(taskItem);
            
            if (shouldShow) {
                taskItem.style.display = '';
                visibleCount++;
            } else {
                taskItem.style.display = 'none';
                hiddenCount++;
            }
        });
        
        this.updateTaskCounters(visibleCount, hiddenCount);
        this.updateFiltersVisualIndicator();
        this.showNoResultsMessage(visibleCount === 0);
    }

    /**
     * Verifica si una tarea coincide con los filtros actuales
     */
    taskMatchesFilters(taskItem) {
        const status = taskItem.dataset.status;
        const priority = taskItem.dataset.priority;
        const project = (taskItem.dataset.project || '').toLowerCase();
        const title = taskItem.querySelector('.task-title')?.textContent.toLowerCase() || '';
        const description = taskItem.querySelector('.task-description')?.textContent.toLowerCase() || '';
        
        // Filtro por estado
        if (this.currentFilters.status && status !== this.currentFilters.status) {
            return false;
        }
        
        // Filtro por prioridad
        if (this.currentFilters.priority && priority !== this.currentFilters.priority) {
            return false;
        }
        
        // Filtro por proyecto
        if (this.currentFilters.project) {
            // Coincidencia por incluye para el buscador de proyecto
            if (!project.includes(this.currentFilters.project)) {
                return false;
            }
        }
        
        // Filtro de búsqueda
        if (this.currentFilters.search) {
            const searchTerm = this.currentFilters.search.toLowerCase();
            const matchesTitle = title.includes(searchTerm);
            const matchesDescription = description.includes(searchTerm);
            
            if (!matchesTitle && !matchesDescription) {
                return false;
            }
        }
        
        return true;
    }

    /**
     * Guarda los filtros en localStorage
     */
    saveFilters() {
        try {
            localStorage.setItem('taskFilters', JSON.stringify(this.currentFilters));
        } catch (e) {
            console.warn('No se pudieron guardar los filtros:', e);
        }
    }

    /**
     * Actualiza los contadores de tareas
     */
    updateTaskCounters(visibleCount, hiddenCount) {
        const totalTasks = document.querySelectorAll('.task-item').length;
        const visibleTasks = visibleCount;
        this.showFilteredResultsCounter(visibleTasks, totalTasks - visibleTasks);
        if (!this.hasActiveFilters()) {
            this.updateHeaderStats(totalTasks);
        } else {
            this.updateFilteredStats(visibleTasks);
        }
    }

    /**
     * Muestra el contador de resultados filtrados
     */
    showFilteredResultsCounter(visibleCount, hiddenCount) {
        let counter = document.querySelector('.filtered-results-counter');
        
        if (!counter) {
            counter = document.createElement('div');
            counter.className = 'filtered-results-counter';
            const filtersContainer = document.querySelector('.tasks-filters');
            if (filtersContainer) {
                filtersContainer.appendChild(counter);
            }
        }
        
        if (this.hasActiveFilters() && hiddenCount > 0) {
            counter.textContent = `Filtrado: ${visibleCount} de ${visibleCount + hiddenCount} tareas`;
            counter.style.display = 'block';
        } else {
            counter.style.display = 'none';
        }
    }

    /**
     * Muestra mensaje cuando no hay resultados
     */
    showNoResultsMessage(noResults) {
        let noResultsElement = document.querySelector('.no-results-message');
        
        if (noResults && !noResultsElement) {
            noResultsElement = document.createElement('div');
            noResultsElement.className = 'no-results-message';
            noResultsElement.innerHTML = `
                <div class="tasks-empty">
                    <i class="fas fa-search tasks-empty-icon"></i>
                    <h3 class="tasks-empty-title">No se encontraron tareas</h3>
                    <p class="tasks-empty-text">Intenta ajustar los filtros o términos de búsqueda.</p>
                    <button type="button" class="task-action-btn secondary" onclick="taskManager.clearFilters()">
                        <i class="fas fa-times"></i> Limpiar Filtros
                    </button>
                </div>
            `;
            
            if (this.tasksList) {
                this.tasksList.appendChild(noResultsElement);
            }
        } else if (!noResults && noResultsElement) {
            noResultsElement.remove();
        }
    }

    /**
     * Verifica si hay filtros activos
     */
    hasActiveFilters() {
        return this.currentFilters.status || 
               this.currentFilters.priority || 
               this.currentFilters.project ||
               (this.currentFilters.search && this.currentFilters.search.trim() !== '');
    }

    /**
     * Actualiza las estadísticas del header
     */
    updateHeaderStats(totalTasks) {
        const taskItems = document.querySelectorAll('.task-item');
        let todoCount = 0;
        let inProgressCount = 0;
        let doneCount = 0;
        let pausedCount = 0;

        taskItems.forEach(taskItem => {
            const status = taskItem.dataset.status;
            switch (status) {
                case 'TODO': todoCount++; break;
                case 'IN_PROGRESS': inProgressCount++; break;
                case 'DONE': doneCount++; break;
                case 'PAUSED': pausedCount++; break;
            }
        });

        // Soporta estadísticas en .task-stat (antiguo) o tarjetas .stat-card-advanced
        const stats = document.querySelectorAll('.task-stat');
        if (stats.length >= 4) {
            stats[0].querySelector('.task-stat-number').textContent = totalTasks;
            stats[1].querySelector('.task-stat-number').textContent = todoCount;
            stats[2].querySelector('.task-stat-number').textContent = inProgressCount;
            stats[3].querySelector('.task-stat-number').textContent = doneCount;
        }
        const advancedCards = document.querySelectorAll('.stat-card-advanced');
        if (advancedCards.length >= 4) {
            const byKey = (key) => Array.from(advancedCards).find(c => c.dataset.stat === key)?.querySelector('.stat-value-advanced');
            const totalEl = byKey('total');
            const todoEl = byKey('todo');
            const inProgEl = byKey('in_progress');
            const doneEl = byKey('done');
            if (totalEl) totalEl.textContent = totalTasks;
            if (todoEl) todoEl.textContent = todoCount;
            if (inProgEl) inProgEl.textContent = inProgressCount;
            if (doneEl) doneEl.textContent = doneCount;
        }
        this.updateFilteredStatsIndicator(false);
    }

    /**
     * Actualiza las estadísticas filtradas
     */
    updateFilteredStats(visibleCount) {
        const visibleTaskItems = Array.from(document.querySelectorAll('.task-item')).filter(item => 
            item.style.display !== 'none'
        );
        
        let todoCount = 0;
        let inProgressCount = 0;
        let doneCount = 0;
        let pausedCount = 0;

        visibleTaskItems.forEach(taskItem => {
            const status = taskItem.dataset.status;
            switch (status) {
                case 'TODO': todoCount++; break;
                case 'IN_PROGRESS': inProgressCount++; break;
                case 'DONE': doneCount++; break;
                case 'PAUSED': pausedCount++; break;
            }
        });

        const stats = document.querySelectorAll('.task-stat');
        if (stats.length >= 4) {
            stats[0].querySelector('.task-stat-number').textContent = visibleCount;
            stats[1].querySelector('.task-stat-number').textContent = todoCount;
            stats[2].querySelector('.task-stat-number').textContent = inProgressCount;
            stats[3].querySelector('.task-stat-number').textContent = doneCount;
        }
        const advancedCards = document.querySelectorAll('.stat-card-advanced');
        if (advancedCards.length >= 4) {
            const byKey = (key) => Array.from(advancedCards).find(c => c.dataset.stat === key)?.querySelector('.stat-value-advanced');
            const totalEl = byKey('total');
            const todoEl = byKey('todo');
            const inProgEl = byKey('in_progress');
            const doneEl = byKey('done');
            if (totalEl) totalEl.textContent = visibleCount;
            if (todoEl) todoEl.textContent = todoCount;
            if (inProgEl) inProgEl.textContent = inProgressCount;
            if (doneEl) doneEl.textContent = doneCount;
        }
        this.updateFilteredStatsIndicator(true);
    }

    /**
     * Actualiza el indicador visual de estadísticas filtradas
     */
    updateFilteredStatsIndicator(isFiltered) {
        const headerContainer = document.querySelector('.tasks-header');
        if (headerContainer) {
            if (isFiltered) {
                headerContainer.classList.add('has-filtered-stats');
            } else {
                headerContainer.classList.remove('has-filtered-stats');
            }
        }
    }

    /**
     * Actualiza el indicador visual de filtros activos
     */
    updateFiltersVisualIndicator() {
        const filtersContainer = document.querySelector('.tasks-filters');
        if (filtersContainer) {
            if (this.hasActiveFilters()) {
                filtersContainer.classList.add('has-active-filters');
            } else {
                filtersContainer.classList.remove('has-active-filters');
            }
        }
    }

    /**
     * Limpia todos los filtros
     */
    clearFilters() {
        this.currentFilters = {
            status: '',
            priority: '',
            project: '',
            search: ''
        };
        
        if (this.statusFilter) this.statusFilter.value = '';
        if (this.priorityFilter) this.priorityFilter.value = '';
        if (this.projectFilter) this.projectFilter.value = '';
        if (this.searchInput) this.searchInput.value = '';
        
        this.saveFilters();
        this.applyFilters();
    }

    /**
     * Función de debounce para optimizar la búsqueda
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
     * Actualiza el estado de una tarea
     */
    updateTaskStatus(taskId, status) {
        const url = `/projects/tasks/${taskId}/update-status/`;
        
        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: `status=${status}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showSuccessMessage('Tarea actualizada correctamente');
                setTimeout(() => {
                    location.reload();
                }, 1000);
            } else {
                this.showErrorMessage('Error al actualizar la tarea: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            this.showErrorMessage('Error al actualizar la tarea');
        });
    }

    /**
     * Obtiene el token CSRF
     */
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
    }

    /**
     * Muestra mensaje de éxito
     */
    showSuccessMessage(message) {
        this.showMessage(message, 'success');
    }

    /**
     * Muestra mensaje de error
     */
    showErrorMessage(message) {
        this.showMessage(message, 'error');
    }

    /**
     * Muestra un mensaje temporal
     */
    showMessage(message, type = 'info') {
        const messageElement = document.createElement('div');
        messageElement.className = `task-message task-message-${type}`;
        messageElement.textContent = message;
        messageElement.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            border-radius: var(--task-radius);
            color: white;
            font-weight: 600;
            z-index: 9999;
            animation: slideInRight 0.3s ease-out;
            max-width: 300px;
            word-wrap: break-word;
        `;

        // Colores según el tipo
        if (type === 'success') {
            messageElement.style.background = 'var(--task-success)';
        } else if (type === 'error') {
            messageElement.style.background = 'var(--task-error)';
        } else {
            messageElement.style.background = 'var(--task-primary)';
        }

        document.body.appendChild(messageElement);

        // Remover después de 3 segundos
        setTimeout(() => {
            messageElement.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => {
                if (messageElement.parentNode) {
                    messageElement.parentNode.removeChild(messageElement);
                }
            }, 300);
        }, 3000);
    }

    /**
     * Inicializa funcionalidades adicionales
     */
    initializeAdditionalFeatures() {
        // Tooltips para las tareas
        this.initializeTooltips();
        
        // Drag and drop para reordenar tareas (futuro)
        this.initializeDragAndDrop();
        
        // Keyboard shortcuts
        this.initializeKeyboardShortcuts();
    }

    /**
     * Inicializa tooltips
     */
    initializeTooltips() {
        const taskItems = document.querySelectorAll('.task-item');
        taskItems.forEach(taskItem => {
            const title = taskItem.querySelector('.task-title').textContent;
            const description = taskItem.querySelector('.task-description')?.textContent || '';
            
            if (description) {
                taskItem.setAttribute('title', `${title}\n\n${description}`);
            }
        });
    }

    /**
     * Inicializa drag and drop (placeholder para futuro)
     */
    initializeDragAndDrop() {
        // TODO: Implementar drag and drop para reordenar tareas
        console.log('Drag and drop feature ready for future implementation');
    }

    /**
     * Inicializa atajos de teclado
     */
    initializeKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + F para buscar
            if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
                e.preventDefault();
                if (this.searchInput) {
                    this.searchInput.focus();
                    this.searchInput.select();
                }
            }
            
            // Escape para limpiar filtros
            if (e.key === 'Escape') {
                this.clearFilters();
            }
        });
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.taskManager = new TaskManager();
    
    // Inicializar funcionalidades adicionales
    if (window.taskManager) {
        window.taskManager.initializeAdditionalFeatures();
    }
});

// Exportar para uso en otros módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TaskManager;
}


