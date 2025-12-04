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
    // Eliminar todos los backdrops
    const backdrops = document.querySelectorAll('.modal-backdrop');
    backdrops.forEach(backdrop => backdrop.remove());
    
    // Limpiar clases del body
    document.body.classList.remove('modal-open');
    document.body.style.overflow = '';
    document.body.style.paddingRight = '';
}

// Función global para abrir modal de tareas
window.openTaskModal = function(type, taskId) {
    const modalElement = document.getElementById('taskUniversalModal');
    if (!modalElement) return;
    
    const modalContent = document.getElementById('taskUniversalContent');
    const modalTitle = document.getElementById('taskUniversalModalLabel');
    
    if (!modalContent || !modalTitle) return;
    
    // Construir URL según el tipo
    let url = '';
    try {
        if (type === 'detail') {
            url = (document.body.dataset.taskDetailUrlTemplate || '').replace('0', taskId);
        } else if (type === 'edit') {
            url = `/projects/tasks/${taskId}/edit/`;
        }
    } catch (error) {
        // Ignorar errores
    }
    
    if (!url) {
        console.error('No se pudo determinar la URL para el modal de tarea');
        return;
    }
    
    // Cargar contenido PRIMERO (antes de mostrar el modal)
    fetch(url)
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.text();
        })
        .then(html => {
            // Limpiar completamente cualquier estado previo del modal
            cleanupModalBackdrops();
            
            // Destruir instancia existente si hay alguna
            let existingModal = bootstrap.Modal.getInstance(modalElement);
            if (existingModal) {
                try {
                    existingModal.dispose();
                } catch(e) {
                    // Ignorar errores
                }
            }
            
            // Actualizar título según el tipo
            if (type === 'detail') {
                modalTitle.textContent = 'Detalles de la Tarea';
            } else if (type === 'edit') {
                modalTitle.textContent = 'Editar Tarea';
            }
            
            // Insertar contenido
            modalContent.innerHTML = html;
            
            // Crear una nueva instancia limpia
            const modal = new bootstrap.Modal(modalElement, {
                backdrop: true,
                keyboard: true,
                focus: true
            });
            
            // Mostrar el modal (ya con contenido cargado)
            modal.show();
            
            // Ejecutar scripts que vienen en el HTML
            const scripts = modalContent.querySelectorAll('script');
            scripts.forEach(script => {
                const newScript = document.createElement('script');
                Array.from(script.attributes).forEach(attr => {
                    newScript.setAttribute(attr.name, attr.value);
                });
                newScript.appendChild(document.createTextNode(script.innerHTML));
                script.parentNode.replaceChild(newScript, script);
            });
        })
        .catch(error => {
            console.error('Error cargando modal de tarea:', error);
            // En caso de error, mostrar modal con mensaje de error
            cleanupModalBackdrops();
            
            let existingModal = bootstrap.Modal.getInstance(modalElement);
            if (existingModal) {
                try { existingModal.dispose(); } catch(e) {}
            }
            
            modalContent.innerHTML = '<div class="text-center p-4 text-danger"><i class="fas fa-exclamation-triangle fa-2x mb-3"></i><h5>Error al cargar</h5><p class="text-muted">No se pudo cargar el contenido. Inténtalo de nuevo.</p></div>';
            
            const modal = new bootstrap.Modal(modalElement, {
                backdrop: true,
                keyboard: true,
                focus: true
            });
            modal.show();
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
            // Forzar limpieza completa
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