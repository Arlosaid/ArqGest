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

// Función helper para limpiar backdrops y estados del modal
function cleanupModalBackdrops() {
    // Eliminar todos los backdrops huérfanos (sin modal asociado visible)
    const backdrops = document.querySelectorAll('.modal-backdrop');
    const openModals = document.querySelectorAll('.modal.show');
    
    // Solo limpiar si no hay modales abiertos
    if (openModals.length === 0) {
        backdrops.forEach(backdrop => backdrop.remove());
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    }
}

// Función global para abrir modal de tareas
window.openTaskModal = function(type, taskId) {
    const modalElement = document.getElementById('taskUniversalModal');
    if (!modalElement) return;
    
    const modalContent = document.getElementById('taskUniversalContent');
    const modalTitle = document.getElementById('taskUniversalModalLabel');
    
    if (!modalContent || !modalTitle) return;
    
    // Verificar si el modal ya está abierto (recarga de contenido)
    let existingModal = bootstrap.Modal.getInstance(modalElement);
    const modalWasOpen = modalElement.classList.contains('show');
    
    // Si no estaba abierto, limpiar y preparar
    if (!modalWasOpen) {
        cleanupModalBackdrops();
        if (existingModal) {
            try { existingModal.dispose(); } catch(e) {}
        }
    }
    
    // Actualizar título según el tipo
    modalTitle.textContent = type === 'detail' ? 'Detalles de la Tarea' : 'Editar Tarea';
    
    // Mostrar loading inmediatamente
    modalContent.innerHTML = '<div class="text-center p-5"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Cargando...</span></div></div>';
    
    // Si el modal NO está abierto, crear y mostrar uno nuevo
    if (!modalWasOpen) {
        const modal = new bootstrap.Modal(modalElement, {
            backdrop: true,
            keyboard: true,
            focus: true
        });
        modal.show();
    }
    
    // Construir URL según el tipo
    let url = '';
    if (type === 'detail') {
        url = (document.body.dataset.taskDetailUrlTemplate || '').replace('0', taskId);
    } else if (type === 'edit') {
        url = `/projects/tasks/${taskId}/edit/`;
    }
    
    if (!url) {
        modalContent.innerHTML = '<div class="text-center p-4 text-danger"><i class="fas fa-exclamation-triangle fa-2x mb-3"></i><p>Error: URL no disponible</p></div>';
        return;
    }
    
    // Cargar contenido
    fetch(url)
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.text();
        })
        .then(html => {
            // Insertar contenido
            modalContent.innerHTML = html;
            
            // Disparar evento para que TaskModalManager maneje la inicialización
            // Esto reemplaza la ejecución de scripts inline que causaba problemas de scope
            const event = new CustomEvent('taskModalLoaded', {
                detail: { type: type, taskId: taskId, container: modalContent }
            });
            document.dispatchEvent(event);
        })
        .catch(error => {
            console.error('Error cargando modal de tarea:', error);
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
    
    // Limpiar backdrops residuales cuando se cierra el modal
    const taskModal = document.getElementById('taskUniversalModal');
    if (taskModal) {
        taskModal.addEventListener('hidden.bs.modal', function(e) {
            // Limpiar backdrops huérfanos
            cleanupModalBackdrops();
            
            // Destruir la instancia del modal para empezar limpio la próxima vez
            const modalInstance = bootstrap.Modal.getInstance(taskModal);
            if (modalInstance) {
                try {
                    modalInstance.dispose();
                } catch(err) {
                    // Ignorar errores al destruir
                }
            }
        });
    }
});