// static/js/base.js

class BaseAnimation {
    static init() {
        // Animaciones base deshabilitadas
        // this.setupAnimations();
    }

    static setupAnimations() {
        // Configurar animaciones para elementos comunes
        this.animateElements('.page-container, .main-content-grid, .table-container, .info-card-sidebar');
    }

    static animateElements() { /* deshabilitada intencionalmente */ }

    static animateTableRow() { /* deshabilitada intencionalmente */ }

    static animateButton() { /* deshabilitada intencionalmente */ }

    static animateCard() { /* deshabilitada intencionalmente */ }
}

// Función global para abrir modal de tareas
window.openTaskModal = function(type, taskId) {
    const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('taskUniversalModal'));
    const modalContent = document.getElementById('taskUniversalContent');
    const modalTitle = document.getElementById('taskUniversalModalLabel');
    
    if (type === 'detail') {
        modalTitle.textContent = 'Detalles de la Tarea';
    } else if (type === 'edit') {
        modalTitle.textContent = 'Editar Tarea';
    }
    
    modalContent.innerHTML = '<div class="text-center p-4"><i class="fas fa-spinner fa-spin fa-2x text-primary"></i><p class="mt-2 text-muted">Cargando...</p></div>';
    modal.show();
    
    let url = '';
    try {
        if (type === 'detail') {
            url = (document.body.dataset.taskDetailUrlTemplate || '').replace('0', taskId);
        } else if (type === 'edit') {
            url = `/projects/tasks/${taskId}/edit/`;
        }
    } catch (error) {
        console.error('Error building URL:', error);
    }
    
    if (!url) {
        modalContent.innerHTML = '<div class="text-center p-4 text-danger"><i class="fas fa-exclamation-triangle fa-2x mb-3"></i><h5>Error</h5><p class="text-muted">No se pudo determinar la URL.</p></div>';
        return;
    }
    
    fetch(url)
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.text();
        })
        .then(html => {
            modalContent.innerHTML = html;
        })
        .catch(error => {
            console.error('Error loading modal content:', error);
            modalContent.innerHTML = '<div class="text-center p-4 text-danger"><i class="fas fa-exclamation-triangle fa-2x mb-3"></i><h5>Error al cargar</h5><p class="text-muted">No se pudo cargar el contenido. Inténtalo de nuevo.</p></div>';
        });
};

// Inicializar animaciones base cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar animaciones base
    BaseAnimation.init();

    // Activar los tooltips de Bootstrap en toda la aplicación
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Activar los popovers de Bootstrap
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});