/* 
 * Kanban Board Logic - Blueprint Theme
 * Handles drag & drop, filtering, and UI interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Initialize filters
    setupFilters();
});

/* --- Drag and Drop Logic --- */

function allowDrop(ev) {
    ev.preventDefault();
    ev.currentTarget.classList.add('drag-over');
}

function drag(ev) {
    ev.dataTransfer.setData("text", ev.target.dataset.taskId);
    ev.target.classList.add('dragging');
}

function drop(ev) {
    ev.preventDefault();
    var columnBody = ev.currentTarget;
    columnBody.classList.remove('drag-over');
    
    var taskId = ev.dataTransfer.getData("text");
    var newStatus = columnBody.parentElement.dataset.status;
    var card = document.querySelector(`.kanban-card[data-task-id="${taskId}"]`);
    
    if (card) {
        // Optimistic UI update
        columnBody.appendChild(card);
        updateTaskStatus(taskId, newStatus);
        updateColumnCounts();
        checkEmptyStates();
        
        // Update card style based on new column
        updateCardStyle(card, newStatus);
    }
}

/* --- Status Updates --- */

function updateTaskStatus(taskId, status) {
    const csrfToken = document.getElementById('csrfToken').value;
    const projectId = document.getElementById('projectId').value;
    
    // Map status to backend values if needed (e.g., 'in_progress' -> 'IN_PROGRESS')
    const backendStatus = status.toUpperCase();

    fetch(`/projects/${projectId}/tasks/${taskId}/update_status/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ status: backendStatus })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        console.log('Success:', data);
        // Optional: Show toast notification
    })
    .catch((error) => {
        console.error('Error:', error);
        alert('Error updating task status. Please refresh.');
        // Revert UI change if needed
    });
}

function updateCardStyle(card, status) {
    // Remove old status classes if any
    // Add specific styling logic if needed beyond CSS
}

/* --- UI Helpers --- */

function updateColumnCounts() {
    const columns = ['todo', 'in_progress', 'paused', 'done'];
    columns.forEach(status => {
        const count = document.querySelectorAll(`.kanban-column[data-status="${status}"] .kanban-card:not(.d-none)`).length;
        const badge = document.getElementById(`count-${status}`);
        if (badge) badge.textContent = count;
    });
    
    // Update total count
    const total = document.querySelectorAll('.kanban-card:not(.d-none)').length;
    const totalBadge = document.querySelector('.total-number');
    if (totalBadge) totalBadge.textContent = total;
}

function checkEmptyStates() {
    const columns = document.querySelectorAll('.kanban-column-body');
    columns.forEach(col => {
        const hasCards = col.querySelectorAll('.kanban-card:not(.d-none)').length > 0;
        const emptyState = col.querySelector('.empty-column');
        if (emptyState) {
            emptyState.style.display = hasCards ? 'none' : 'flex';
        }
    });
}

/* --- Filtering --- */

function setupFilters() {
    const phaseFilter = document.getElementById('phaseFilter');
    const userFilter = document.getElementById('userFilter');

    if (phaseFilter) phaseFilter.addEventListener('change', applyFilters);
    if (userFilter) userFilter.addEventListener('change', applyFilters);
}

function applyFilters() {
    const phaseId = document.getElementById('phaseFilter').value;
    const userId = document.getElementById('userFilter').value;
    
    const cards = document.querySelectorAll('.kanban-card');
    
    cards.forEach(card => {
        // Assuming we add data attributes to cards for filtering
        // You might need to add data-phase-id and data-user-id to your card template
        // For now, this is a placeholder logic
        let show = true;
        
        // Example logic (requires data attributes on cards)
        // if (phaseId !== 'all' && card.dataset.phaseId !== phaseId) show = false;
        // if (userId !== 'all' && card.dataset.userId !== userId) show = false;
        
        // Since we didn't add data attributes in the HTML template yet, 
        // we'll rely on server-side filtering for now or implement DOM inspection
        // For this demo, let's assume we reload or hide everything if not 'all'
        // Ideally, update HTML to include data-phase="{{ task.phase.id }}" etc.
        
        if (show) {
            card.classList.remove('d-none');
        } else {
            card.classList.add('d-none');
        }
    });
    
    updateColumnCounts();
    checkEmptyStates();
}

function clearFilters() {
    const btn = document.querySelector('button[onclick="clearFilters()"]');
    setLoadingState(btn, true);

    document.getElementById('phaseFilter').value = 'all';
    document.getElementById('userFilter').value = 'all';
    
    // Simulate delay for UX
    setTimeout(() => {
        applyFilters(); // Or reload page
        location.reload(); // Simplest way to clear server-side filters too
    }, 500);
}

/* --- Actions --- */

function refreshKanban() {
    const btn = document.querySelector('button[onclick="refreshKanban()"]');
    setLoadingState(btn, true);
    
    setTimeout(() => {
        location.reload();
    }, 500);
}

function setLoadingState(button, isLoading) {
    if (!button) return;
    
    if (isLoading) {
        const originalText = button.innerHTML;
        button.dataset.originalText = originalText;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        button.disabled = true;
    } else {
        button.innerHTML = button.dataset.originalText || 'Action';
        button.disabled = false;
    }
}
