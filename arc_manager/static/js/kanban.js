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

        // Verificar si el proyecto está archivado - desactivar drag & drop completamente
        const isProjectArchived = document.body.dataset.isProjectArchived === 'true';
        if (isProjectArchived) {
            this.cards.forEach(card => {
                card.draggable = false;
                card.style.cursor = 'default';
            });
            return;
        }

        // Solo activar drag and drop en desktop (pantallas >= 768px)
        if (window.innerWidth >= 768) {
            this.columns.forEach(column => {
                // Eventos simplificados y optimizados
                column.addEventListener('dragover', this.handleDragOver.bind(this));
                column.addEventListener('drop', this.handleDrop.bind(this));
                column.addEventListener('dragenter', this.handleDragEnter.bind(this));
                column.addEventListener('dragleave', this.handleDragLeave.bind(this));
            });

            this.cards.forEach(card => {
                card.addEventListener('dragstart', this.handleDragStart.bind(this));
                card.addEventListener('dragend', this.handleDragEnd.bind(this));
                card.draggable = true;
                card.style.cursor = 'grab';
                
                // Prevent click events from firing during drag operations
                card.addEventListener('mousedown', (e) => {
                    // Allow button clicks to pass through
                    if (e.target.closest('button') || e.target.closest('.btn')) {
                        return;
                    }
                    // Store drag start time to detect drag vs click
                    card.dataset.dragStartTime = Date.now();
                });
            });
        } else {
            // En móvil, desactivar drag and drop completamente
            this.cards.forEach(card => {
                card.draggable = false;
                card.style.cursor = 'default';
            });
        }

        // Escuchar cambios de tamaño de ventana para activar/desactivar drag and drop
        window.addEventListener('resize', this.handleWindowResize.bind(this));
    }

    initializeModals() {
        // Inicializar modales de Bootstrap si están disponibles
        if (typeof bootstrap !== 'undefined') {
            this.modals = {};

            // Solo inicializar modales que existen en el DOM
            if (this.addTaskModal) {
                this.modals.addTask = new bootstrap.Modal(this.addTaskModal);
            }

            if (this.taskModal) {
                this.modals.task = new bootstrap.Modal(this.taskModal);
            }
        }
    }

    // ===== DRAG & DROP HANDLERS =====

    handleDragStart(e) {
        if (this.isUpdating) {
            e.preventDefault();
            return;
        }

        // Verificar si el proyecto está archivado - bloquear drag & drop
        const isProjectArchived = document.body.dataset.isProjectArchived === 'true';
        if (isProjectArchived) {
            this.showNotification('Proyecto archivado - no se pueden mover tareas', 'warning');
            e.preventDefault();
            return;
        }

        // Verificar permisos: admins O usuarios asignados pueden hacer drag & drop
        const isOrgAdmin = document.body.dataset.isOrgAdmin === 'true';
        const currentUserId = parseInt(document.body.dataset.currentUserId || '0');
        const taskAssignedToId = parseInt(e.currentTarget.dataset.assignedToId || '0');

        // Permitir solo si es admin O si es el usuario asignado
        if (!isOrgAdmin && currentUserId !== taskAssignedToId) {
            this.showNotification('No tienes permiso para mover esta tarea', 'warning');
            e.preventDefault();
            return;
        }

        // Feedback visual mínimo y eficiente
        e.currentTarget.classList.add('dragging');
        e.dataTransfer.setData('text/plain', e.currentTarget.dataset.taskId);
        e.dataTransfer.effectAllowed = 'move';

        // Usar una imagen de arrastre más simple y pequeña
        const dragImage = document.createElement('div');
        dragImage.style.width = '200px';
        dragImage.style.height = '60px';
        dragImage.style.background = 'var(--arc-color-primary)';
        dragImage.style.borderRadius = '8px';
        dragImage.style.color = 'white';
        dragImage.style.display = 'flex';
        dragImage.style.alignItems = 'center';
        dragImage.style.justifyContent = 'center';
        dragImage.style.fontSize = '14px';
        dragImage.style.fontWeight = '600';
        dragImage.textContent = 'Moviendo tarea...';
        dragImage.style.boxShadow = '0 8px 20px rgba(0, 0, 0, 0.2)';
        dragImage.style.position = 'absolute';
        dragImage.style.top = '-1000px';
        dragImage.style.left = '-1000px';

        document.body.appendChild(dragImage);
        e.dataTransfer.setDragImage(dragImage, 100, 30);

        // Limpiar inmediatamente
        setTimeout(() => {
            if (document.body.contains(dragImage)) {
                document.body.removeChild(dragImage);
            }
        }, 10);
    }

    handleDragEnd(e) {
        e.currentTarget.classList.remove('dragging');
        this.removeDragOverClasses();
    }

    handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';

        // Detectar la columna más cercana de forma optimizada
        const column = this.getClosestColumn(e.clientX, e.clientY);
        if (column) {
            this.removeDragOverClasses();
            column.classList.add('drag-over');
        }
    }

    handleDragEnter(e) {
        e.preventDefault();
        const column = this.getClosestColumn(e.clientX, e.clientY);
        if (column) {
            this.removeDragOverClasses();
            column.classList.add('drag-over');
        }
    }

    handleDragLeave(e) {
        const column = e.target.closest('.kanban-column-body');
        if (column && !column.contains(e.relatedTarget)) {
            column.classList.remove('drag-over');
        }
    }

    // Función optimizada para encontrar la columna más cercana
    getClosestColumn(x, y) {
        const columns = document.querySelectorAll('.kanban-column-body');
        let closestColumn = null;
        let minDistance = Infinity;

        for (let col of columns) {
            const rect = col.getBoundingClientRect();

            // Verificar si está dentro del área de la columna (con margen de 100px)
            if (x >= rect.left - 100 &&
                x <= rect.right + 100 &&
                y >= rect.top - 100 &&
                y <= rect.bottom + 100) {

                const distance = Math.sqrt(
                    Math.pow(x - (rect.left + rect.width / 2), 2) +
                    Math.pow(y - (rect.top + rect.height / 2), 2)
                );

                if (distance < minDistance) {
                    minDistance = distance;
                    closestColumn = col;
                }
            }
        }

        return closestColumn;
    }

    handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        if (this.isUpdating) return;

        // Usar la función optimizada para encontrar la columna de destino
        const column = this.getClosestColumn(e.clientX, e.clientY);

        if (!column) return;

        const taskId = e.dataTransfer.getData('text/plain');
        const newStatus = column.closest('.kanban-column').dataset.status;

        // Limpiar todas las clases de drag-over
        this.removeDragOverClasses();

        // Actualizar el estado de la tarea
        this.updateTaskStatusSilently(taskId, newStatus);
    }

    removeDragOverClasses() {
        this.columns.forEach(column => {
            column.classList.remove('drag-over');
        });
    }

    // ===== RESPONSIVE HANDLING =====

    handleWindowResize() {
        // Debounce para evitar múltiples llamadas
        clearTimeout(this.resizeTimeout);
        this.resizeTimeout = setTimeout(() => {
            this.initializeDragAndDrop();
        }, 250);
    }

    // ===== TASK MANAGEMENT - ACTUALIZACIONES SILENCIOSAS =====

    async updateTaskStatusSilently(taskId, newStatus) {
        if (this.isUpdating) return;

        this.isUpdating = true;

        // Mover la tarjeta visualmente INMEDIATAMENTE para mejor UX
        this.moveCardVisually(taskId, newStatus);

        try {
            const response = await fetch(`/projects/tasks/${taskId}/update_status/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    status: newStatus
                })
            });

            // Check for redirects
            if (response.redirected && response.url.includes('/login/')) {
                window.location.href = response.url;
                return;
            }

            const contentType = response.headers.get("content-type");
            let success = false;
            let errorMsg = 'Error desconocido';

            if (response.ok && contentType && contentType.includes("application/json")) {
                const data = await response.json();
                if (data.success) {
                    success = true;
                } else {
                    errorMsg = data.error || 'Error del servidor';
                }
            } else {
                errorMsg = `Error ${response.status}`;
            }

            if (success) {
                // Actualizar estadísticas en segundo plano
                this.updateStatisticsSilently();

                // CRÍTICO: Broadcast el cambio a otras pestañas/ventanas (ej: Mis Tareas)
                this.broadcastTaskStatusChange(taskId, newStatus);
            } else {
                // Revertir el movimiento si falla
                this.showNotification('Error al actualizar estado: ' + errorMsg, 'error');
                setTimeout(() => location.reload(), 1000); // Recargar para sincronizar estado real
            }
        } catch (error) {
            this.showNotification('Error de conexión', 'error');
            setTimeout(() => location.reload(), 1000);
        } finally {
            this.isUpdating = false;
        }
    }

    // Función para broadcast cambios de estado a otras pestañas/ventanas
    broadcastTaskStatusChange(taskId, newStatus) {
        try {
            const event = {
                type: 'TASK_STATUS_UPDATED',
                taskId: taskId,
                status: newStatus,
                timestamp: Date.now(),
                source: 'kanban'
            };

            // Usar localStorage para comunicación entre pestañas
            localStorage.setItem('task_update_event', JSON.stringify(event));

            // Limpiar inmediatamente para permitir eventos duplicados
            setTimeout(() => {
                localStorage.removeItem('task_update_event');
            }, 100);
        } catch (error) {
            // Broadcast failed silently
        }
    }

    moveCardVisually(taskId, newStatus) {
        const card = document.querySelector(`[data-task-id="${taskId}"]`);
        if (!card) return;

        // Encontrar la columna de destino
        // targetColumn is the .kanban-column-body inside the column with data-status
        // The template structure is: .kanban-column[data-status] > .kanban-column-body
        const targetColumnWrapper = document.querySelector(`.kanban-column[data-status="${newStatus}"]`);
        if (!targetColumnWrapper) return;
        
        const targetColumn = targetColumnWrapper.querySelector('.kanban-column-body');
        if (!targetColumn) return;

        // Animación ultra rápida y simple
        card.style.transition = 'all 0.1s ease-out';
        card.style.opacity = '0.6';
        card.style.transform = 'scale(0.95)';

        // Mover inmediatamente sin animación compleja
        setTimeout(() => {
            targetColumn.appendChild(card);

            // Restaurar estilos
            card.style.opacity = '1';
            card.style.transform = 'none';
            card.style.transition = 'all 0.1s ease-out';

            // Actualizar botones de estado en la tarjeta (importante para móvil)
            this.updateCardStatusButtons(card, newStatus);

            // Actualizar contadores
            this.updateColumnCounts();
            
            // Verificar columnas vacías
            this.checkEmptyColumns();
        }, 100);
    }

    checkEmptyColumns() {
        document.querySelectorAll('.kanban-column').forEach(column => {
            const body = column.querySelector('.kanban-column-body');
            if (!body) return;
            
            const hasCards = body.querySelectorAll('.kanban-card').length > 0;
            const emptyState = body.querySelector('.empty-state');
            
            if (hasCards) {
                if (emptyState) emptyState.remove();
            } else {
                if (!emptyState) {
                    const status = column.dataset.status;
                    const emptyHtml = this.getEmptyStateHtml(status);
                    body.insertAdjacentHTML('beforeend', emptyHtml);
                }
            }
        });
    }

    getEmptyStateHtml(status) {
        let icon = 'fa-clipboard';
        let text = 'Sin tareas';
        
        switch(status) {
            case 'TODO':
                icon = 'fa-clipboard';
                text = 'Sin tareas';
                break;
            case 'IN_PROGRESS':
                icon = 'fa-running';
                text = 'Nada en curso';
                break;
            case 'PAUSED':
                icon = 'fa-clock';
                text = 'Sin pausas';
                break;
            case 'DONE':
                icon = 'fa-check-double';
                text = 'Sin finalizar';
                break;
        }
        
        return `
            <div class="text-center py-5 empty-state mt-2">
                <i class="far ${icon} fa-2x mb-2 opacity-50"></i>
                <p class="small mb-0 fw-medium">${text}</p>
            </div>
        `;
    }

    updateCardStatusButtons(card, newStatus) {
        // Buscar el contenedor de botones de estado en la tarjeta (Legacy/Desktop)
        const statusButtonsContainer = card.querySelector('.task-status-buttons');
        if (statusButtonsContainer) {
            // Generar los nuevos botones basados en el nuevo estado
            const newButtons = this.generateStatusButtons(card.dataset.taskId, newStatus);
            // Reemplazar el contenido HTML
            statusButtonsContainer.innerHTML = newButtons;
        }

        // Actualizar botones móviles (.mobile-actions)
        const mobileActions = card.querySelector('.mobile-actions');
        if (mobileActions) {
            // Mostrar todos los botones primero
            const buttons = mobileActions.querySelectorAll('button[class*="btn-status-"]');
            buttons.forEach(btn => btn.classList.remove('d-none'));

            // Ocultar el botón correspondiente al nuevo estado
            let btnToHide = null;
            switch (newStatus) {
                case 'TODO':
                    btnToHide = mobileActions.querySelector('.btn-status-todo');
                    break;
                case 'IN_PROGRESS':
                    btnToHide = mobileActions.querySelector('.btn-status-in-progress');
                    break;
                case 'PAUSED':
                    btnToHide = mobileActions.querySelector('.btn-status-paused');
                    break;
                case 'DONE':
                    btnToHide = mobileActions.querySelector('.btn-status-done');
                    break;
            }

            if (btnToHide) {
                btnToHide.classList.add('d-none');
            }
        }
    }

    generateStatusButtons(taskId, status) {
        // Generar los botones HTML basados en el estado actual
        switch (status) {
            case 'TODO':
                return `
                    <button class="btn btn-sm btn-primary" 
                            onclick="updateTaskStatus(${taskId}, 'IN_PROGRESS')"
                            title="Iniciar tarea">
                        <i class="fas fa-play"></i>
                    </button>
                `;
            case 'IN_PROGRESS':
                return `
                    <button class="btn btn-sm btn-warning" 
                            onclick="updateTaskStatus(${taskId}, 'PAUSED')"
                            title="Pausar tarea">
                        <i class="fas fa-pause"></i>
                    </button>
                    <button class="btn btn-sm btn-success" 
                            onclick="updateTaskStatus(${taskId}, 'DONE')"
                            title="Completar tarea">
                        <i class="fas fa-check"></i>
                    </button>
                `;
            case 'PAUSED':
                return `
                    <button class="btn btn-sm btn-primary" 
                            onclick="updateTaskStatus(${taskId}, 'IN_PROGRESS')"
                            title="Reanudar tarea">
                        <i class="fas fa-play"></i>
                    </button>
                `;
            case 'DONE':
                return `
                    <button class="btn btn-sm btn-info" 
                            onclick="updateTaskStatus(${taskId}, 'IN_PROGRESS')"
                            title="Volver a En Progreso">
                        <i class="fas fa-undo"></i>
                    </button>
                `;
            default:
                return '';
        }
    }

    updateColumnCounts() {
        const columns = document.querySelectorAll('.kanban-column');

        columns.forEach(column => {
            const columnBody = column.querySelector('.kanban-column-body');
            // Selector actualizado para coincidir con el template (badge-counter o task-count)
            const countElement = column.querySelector('.badge-counter') || column.querySelector('.task-count');

            if (columnBody && countElement) {
                const taskCount = columnBody.querySelectorAll('.kanban-card').length;
                
                // Actualizar solo el número si es un badge, o texto completo si es task-count
                if (countElement.classList.contains('badge-counter')) {
                    countElement.textContent = taskCount;
                } else {
                    if (taskCount === 1) {
                        countElement.textContent = '1 tarea';
                    } else {
                        countElement.textContent = `${taskCount} tareas`;
                    }
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
            // Statistics update failed silently
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

            // Check for redirects
            if (response.redirected && response.url.includes('/login/')) {
                window.location.href = response.url;
                return;
            }

            const contentType = response.headers.get('content-type') || '';
            
            if (response.ok) {
                if (contentType.includes('application/json')) {
                    const data = await response.json();
                    
                    if (data && data.success) {
                        // Cerrar modal inmediatamente
                        this.closeModal('addTask');
                        // Limpiar formulario
                        this.taskForm.reset();
                        // Mostrar notificación
                        this.showNotification('Tarea creada correctamente', 'success');
                        
                        // Detectar si estamos en la página del kanban (puede ser /tasks/ o /kanban/)
                        const isKanbanPage = window.location.pathname.includes('/kanban/') || 
                                            (window.location.pathname.includes('/tasks/') && document.querySelector('.kanban-board-grid'));
                        
                        // Si estamos en kanban y tenemos el HTML, insertar dinámicamente
                        if (isKanbanPage && data.task_html) {
                            const status = data.status || 'TODO';
                            // Buscar el wrapper de la columna por status, luego el body
                            const columnWrapper = document.querySelector(`.kanban-column[data-status="${status}"]`);
                            const column = columnWrapper ? columnWrapper.querySelector('.kanban-column-body') : null;
                            
                            if (column) {
                                // Remover empty state si existe
                                const emptyState = column.querySelector('.empty-state');
                                if (emptyState) {
                                    emptyState.remove();
                                }
                                
                                // Insertar al principio
                                column.insertAdjacentHTML('afterbegin', data.task_html);
                                
                                // Actualizar contadores
                                this.updateColumnCounts();
                                
                                // Re-inicializar drag events para la nueva tarjeta
                                const newCard = column.querySelector(`[data-task-id="${data.task_id}"]`);
                                
                                if (newCard && window.innerWidth >= 768) {
                                    newCard.addEventListener('dragstart', this.handleDragStart.bind(this));
                                    newCard.addEventListener('dragend', this.handleDragEnd.bind(this));
                                    newCard.draggable = true;
                                    newCard.style.cursor = 'grab';
                                    
                                    // Añadir a la lista de cards para futuras operaciones
                                    this.cards = document.querySelectorAll('.kanban-card');
                                }
                                
                                // Disparar evento para que otros componentes se actualicen
                                document.dispatchEvent(new CustomEvent('taskCreated', { detail: { taskId: data.task_id } }));
                            } else {
                                // Fallback si no encuentra columna
                                setTimeout(() => location.reload(), 1000);
                            }
                        } else {
                            // Disparar evento para que otros componentes se actualicen
                            document.dispatchEvent(new CustomEvent('taskCreated'));
                            // Recargar solo si estamos en la página del kanban
                            const isKanbanPage = window.location.pathname.includes('/kanban/') || 
                                                (window.location.pathname.includes('/tasks/') && document.querySelector('.kanban-board-grid'));
                            if (isKanbanPage) {
                                setTimeout(() => location.reload(), 1500);
                            }
                        }
                    } else {
                        this.showNotification((data && (data.message || data.error)) || 'Error al crear la tarea', 'error');
                    }
                } else {
                    // Fallback: servidor devolvió HTML.
                    // Si es un 200 OK HTML, podría ser la página de éxito renderizada.
                    // Pero para AJAX, esto suele ser un error de configuración o redirección mal manejada.
                    
                    // Intentar detectar si es la página de login o error
                    const text = await response.text();
                    if (text.includes('login') || text.includes('iniciar sesión')) {
                         window.location.reload(); // Forzar login
                         return;
                    }

                    // Asumir éxito si no parece error, pero con precaución
                    this.closeModal('addTask');
                    this.taskForm.reset();
                    this.showNotification('Tarea creada (respuesta HTML)', 'warning');
                    document.dispatchEvent(new CustomEvent('taskCreated'));
                    setTimeout(() => location.reload(), 500);
                }
            } else {
                let msg = 'Error al crear la tarea';
                try {
                    const data = contentType.includes('application/json') ? await response.json() : null;
                    msg = (data && (data.message || data.error)) || msg;
                } catch (_) { }
                this.showNotification(msg, 'error');
            }
        } catch (error) {
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
        // Obtener información de la tarea para el modal
        const taskCard = document.querySelector(`[data-task-id="${taskId}"]`);
        const taskTitle = taskCard ? taskCard.querySelector('.task-title')?.textContent?.trim() || 'esta tarea' : 'esta tarea';
        const taskDescription = taskCard ? taskCard.querySelector('.task-description')?.textContent?.trim() || '' : '';

        // Mostrar modal de confirmación usando el sistema unificado
        ConfirmationModals.deleteTask({
            taskId: taskId,
            taskTitle: taskTitle,
            taskDescription: taskDescription,
            onConfirm: async () => {
                await this.performTaskDeletion(taskId);
            }
        });
    }

    async performTaskDeletion(taskId) {
        try {
            const response = await fetch(`/projects/tasks/${taskId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            // Check for redirects (e.g. login page)
            if (response.redirected) {
                if (response.url.includes('/login/')) {
                    window.location.href = response.url;
                    return;
                }
            }

            const contentType = response.headers.get("content-type");
            if (response.ok) {
                // Verify JSON response
                if (contentType && contentType.includes("application/json")) {
                    const data = await response.json();
                    if (!data.success) {
                        this.showNotification(data.error || 'Error al eliminar la tarea', 'error');
                        return;
                    }
                } else {
                    // If we got HTML 200 OK, it might be a mistake (e.g. dashboard page)
                    // Silent fallback
                }

                // Buscar y eliminar la tarjeta del DOM
                const taskCard = document.querySelector(`[data-task-id="${taskId}"]`);
                if (taskCard) {
                    // Animación de salida
                    taskCard.style.transition = 'all 0.3s ease';
                    taskCard.style.opacity = '0';
                    taskCard.style.transform = 'scale(0.8)';

                    setTimeout(() => {
                        taskCard.remove();
                        
                        // Actualizar UI
                        this.checkEmptyColumns();
                        this.updateColumnCounts();
                    }, 300);
                }

                this.showNotification('Tarea eliminada correctamente', 'success');

                // Disparar evento para que otras partes de la app se actualicen
                document.dispatchEvent(new CustomEvent('taskDeleted', { detail: { taskId } }));
            } else {
                // Handle HTTP errors
                if (response.status === 403) {
                    this.showNotification('No tienes permisos para eliminar esta tarea', 'error');
                } else if (response.status === 404) {
                    this.showNotification('La tarea ya no existe', 'error');
                } else {
                    this.showNotification('Error al eliminar la tarea (' + response.status + ')', 'error');
                }
            }
        } catch (error) {
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
        // Intentar obtener del cookie primero
        const value = `; ${document.cookie}`;
        const parts = value.split(`; csrftoken=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        
        // Fallback: buscar en el DOM
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    showNotification(message, type = 'info') {
        // 1. Intentar usar el sistema de notificaciones global (window.notifications)
        if (window.notifications) {
            if (type === 'success' && typeof window.notifications.success === 'function') {
                window.notifications.success(message);
                return;
            } else if (type === 'error' && typeof window.notifications.error === 'function') {
                window.notifications.error(message);
                return;
            } else if (typeof window.notifications.show === 'function') {
                window.notifications.show(message, type);
                return;
            }
        }

        // 2. Fallback a toastr si existe (común en muchas apps)
        if (typeof toastr !== 'undefined') {
            toastr[type](message);
            return;
        }

        // 3. Fallback manual: Crear un toast de Bootstrap
        this.showFallbackToast(message, type);
    }

    showFallbackToast(message, type) {
        const toastContainer = document.querySelector('.toast-container') || this.createToastContainer();
        
        const toastId = 'toast-' + Date.now();
        const bgClass = type === 'success' ? 'bg-success' : (type === 'error' ? 'bg-danger' : 'bg-info');
        const icon = type === 'success' ? 'fa-check-circle' : (type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle');
        
        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="fas ${icon} me-2"></i> ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;
        
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = toastHtml.trim();
        const toastElement = tempDiv.firstChild;
        
        toastContainer.appendChild(toastElement);
        
        if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
            const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
            toast.show();
            
            toastElement.addEventListener('hidden.bs.toast', () => {
                toastElement.remove();
            });
        } else {
            // Fallback sin bootstrap JS
            toastElement.style.display = 'block';
            setTimeout(() => {
                toastElement.style.opacity = '0';
                setTimeout(() => toastElement.remove(), 500);
            }, 3000);
        }
    }

    createToastContainer() {
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            container.style.zIndex = '1070';
            document.body.appendChild(container);
        }
        return container;
    }

    // ===== STATISTICS UPDATE =====

    updateStatistics() {
        // Actualizar estadísticas en tiempo real si es necesario
        // Actualización visual deshabilitada
    }
}

// ===== INITIALIZATION =====

document.addEventListener('DOMContentLoaded', function () {
    // Inicializar KanbanManager
    window.kanbanManager = new KanbanManager();

    // Funciones globales para compatibilidad
    window.clearFilters = function () {
        window.kanbanManager.clearFilters();
    };

    window.refreshKanban = function () {
        window.kanbanManager.refreshKanban();
    };

    if (typeof window.showTaskDetails !== 'function') {
        window.showTaskDetails = function (taskId) {
            window.kanbanManager.viewTask(taskId);
        };
    }

    window.updateTaskStatus = function (taskId, newStatus) {
        window.kanbanManager.updateTaskStatusSilently(taskId, newStatus);
    };

    window.deleteKanbanTask = function (taskId) {
        window.kanbanManager.deleteTask(taskId);
    };

    // Función para mover tareas usando botones (alternativa al drag and drop)
    window.moveTaskToStatus = function (taskId, newStatus) {
        if (window.kanbanManager) {
            window.kanbanManager.updateTaskStatusSilently(taskId, newStatus);
        }
    };

    // Función mejorada para actualizar estado de tareas (compatible con Mis Tareas)
    window.updateTaskStatus = function (taskId, newStatus) {
        if (window.kanbanManager) {
            window.kanbanManager.updateTaskStatusSilently(taskId, newStatus);
        }
    };

    // CRÍTICO: Escuchar cambios de estado de tareas desde otras pestañas
    window.addEventListener('storage', function (e) {
        if (e.key === 'task_update_event' && e.newValue) {
            try {
                const event = JSON.parse(e.newValue);

                // Solo procesar eventos de actualización de tareas
                if (event.type === 'TASK_STATUS_UPDATED' && window.kanbanManager) {
                    // Actualizar la UI si la tarea está visible en esta página
                    window.kanbanManager.moveCardVisually(event.taskId, event.status);
                }
            } catch (error) {
                // Silent fail for storage event errors
            }
        }
    });
});

// ===== EXPORT FOR MODULE SYSTEMS =====

if (typeof module !== 'undefined' && module.exports) {
    module.exports = KanbanManager;
}

