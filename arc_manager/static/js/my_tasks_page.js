// Lógica de Mis Tareas (migrada desde el template)
window.updateTaskStatus = function(taskId, status) {
    updateTaskStatusInstant(taskId, status);
};

function updateTaskStatusInstant(taskId, status) {
    updateTaskUIInstant(taskId, status);
    const url = `/projects/tasks/${taskId}/update_status/`;
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken') || ''
        },
        body: `status=${encodeURIComponent(status)}`
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            console.error('Error al actualizar tarea:', data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function updateTaskUIInstant(taskId, newStatus) {
    const taskCard = document.querySelector(`[data-task-id="${taskId}"]`);
    if (!taskCard) return;
    taskCard.dataset.status = newStatus;
    const statusBadge = taskCard.querySelector('.badge-status');
    if (statusBadge) {
        statusBadge.className = statusBadge.className.replace(/badge-\w+/g, '');
        statusBadge.classList.add('badge-status', `badge-${newStatus.toLowerCase()}`);
        const statusTexts = { 'TODO': 'Pendiente', 'IN_PROGRESS': 'En Progreso', 'PAUSED': 'Pausada', 'DONE': 'Completada' };
        statusBadge.textContent = statusTexts[newStatus] || newStatus;
    }
    updateTaskActions(taskCard, newStatus);
    updateCounters();
}

function updateTaskActions(taskCard, status) {
    const actionsContainer = taskCard.querySelector('.task-card-actions');
    if (!actionsContainer) return;
    const taskId = taskCard.dataset.taskId;
    const kanbanUrl = taskCard.querySelector('.action-kanban')?.href || '#';
    let actionsHTML = `
        <button type="button" class="action-btn action-view"
                data-modal-url="/projects/tasks/${taskId}/"
                data-modal-title="Detalles de la tarea"
                title="Ver detalles">
            <i class="fas fa-eye"></i>
        </button>
    `;
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
    actionsHTML += `
        <a href="${kanbanUrl}" 
           class="action-btn action-kanban"
           title="Ir al Kanban">
            <i class="fas fa-columns"></i>
        </a>
    `;
    actionsContainer.innerHTML = actionsHTML;
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('taskSearch');
    const clearSearch = document.getElementById('clearSearch');
    const statusFilter = document.getElementById('statusFilter');
    const priorityFilter = document.getElementById('priorityFilter');
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');

    function updateCounters() {
        const visibleTasks = document.querySelectorAll('.task-card-compact:not([style*="display: none"])');
        let counts = { total: visibleTasks.length, todo: 0, in_progress: 0, paused: 0, done: 0 };
        visibleTasks.forEach(task => {
            const status = task.dataset.status;
            if (status === 'TODO') counts.todo++;
            else if (status === 'IN_PROGRESS') counts.in_progress++;
            else if (status === 'PAUSED') counts.paused++;
            else if (status === 'DONE') counts.done++;
        });
        const setText = (sel, val) => { const el = document.querySelector(sel); if (el) el.textContent = val; };
        setText('.stat-total .stat-number', counts.total);
        setText('.stat-todo .stat-number', counts.todo);
        setText('.stat-progress .stat-number', counts.in_progress);
        setText('.stat-paused .stat-number', counts.paused);
        setText('.stat-done .stat-number', counts.done);
    }

    function filterTasks() {
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
            if (searchTerm && !taskTitle.includes(searchTerm) && !taskProject.includes(searchTerm)) show = false;
            if (statusValue && taskStatus !== statusValue) show = false;
            if (priorityValue && taskPriority !== priorityValue) show = false;
            task.style.display = show ? 'block' : 'none';
        });
        updateCounters();
    }

    window.clearAllFilters = function() {
        if (searchInput) searchInput.value = '';
        if (statusFilter) statusFilter.value = '';
        if (priorityFilter) priorityFilter.value = '';
        if (clearSearch) clearSearch.style.display = 'none';
        filterTasks();
    };

    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearSearch.style.display = this.value.length > 0 ? 'block' : 'none';
            filterTasks();
        });
    }
    if (clearSearch) {
        clearSearch.addEventListener('click', function() {
            if (searchInput) searchInput.value = '';
            this.style.display = 'none';
            filterTasks();
        });
    }
    if (statusFilter) statusFilter.addEventListener('change', filterTasks);
    if (priorityFilter) priorityFilter.addEventListener('change', filterTasks);
    if (clearFiltersBtn) clearFiltersBtn.addEventListener('click', window.clearAllFilters);

    updateCounters();
});

