/**
 * Phase Quick Actions - JavaScript para acciones rápidas desde tarjetas de fase
 * Permite crear tareas con fase pre-seleccionada desde cualquier vista de fases
 */

/**
 * Abre el modal de nueva tarea con la fase pre-seleccionada
 * @param {number} phaseId - ID de la fase
 * @param {string} phaseName - Nombre de la fase (para mostrar en UI)
 */
function openTaskModalWithPhase(phaseId, phaseName) {
    // Buscar el modal de agregar tarea
    const modal = document.getElementById('addTaskModal');
    if (!modal) {
        console.error('❌ Modal de tarea no encontrado');
        return;
    }
    
    // Buscar el select de fase
    const phaseSelect = modal.querySelector('#phase');
    if (!phaseSelect) {
        console.error('❌ Select de fase no encontrado');
        return;
    }
    
    // Pre-seleccionar la fase
    phaseSelect.value = phaseId;
    
    // Resetear el formulario excepto la fase
    const form = modal.querySelector('#taskForm');
    if (form) {
        // Guardar el valor de la fase
        const savedPhaseValue = phaseSelect.value;
        
        // Resetear formulario
        form.reset();
        
        // Restaurar la fase seleccionada
        phaseSelect.value = savedPhaseValue;
    }
    
    // Actualizar el título del modal para indicar la fase
    const modalTitle = modal.querySelector('.modal-title');
    if (modalTitle) {
        modalTitle.textContent = `Nueva Tarea - ${phaseName}`;
    }
    
    // Abrir el modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Focus en el campo de título después de que el modal esté visible
    modal.addEventListener('shown.bs.modal', function onShown() {
        const titleInput = modal.querySelector('#title');
        if (titleInput) {
            titleInput.focus();
        }
        // Remover el listener después de usarlo
        modal.removeEventListener('shown.bs.modal', onShown);
    });
}

/**
 * Abre el modal de subir archivo con la fase pre-seleccionada
 * @param {number} phaseId - ID de la fase
 * @param {string} phaseName - Nombre de la fase (para mostrar en UI)
 */
function openUploadModalWithPhase(phaseId, phaseName) {
    // Buscar el modal específico de la fase (si existe)
    const modal = document.getElementById(`uploadFileModal${phaseId}`);
    
    if (!modal) {
        console.warn('⚠️ Modal de subida de archivos no encontrado para fase', phaseId);
        // Fallback: redirigir a la pestaña de archivos
        const filesTab = document.querySelector('[data-bs-target="#files"]');
        if (filesTab) {
            filesTab.click();
            
            // Mostrar mensaje toast
            showToast('info', `Navega a la sección de archivos de "${phaseName}" para subir archivos`);
        }
        return;
    }
    
    // Abrir el modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

/**
 * Muestra un toast notification
 * @param {string} type - Tipo de toast (success, error, warning, info)
 * @param {string} message - Mensaje a mostrar
 */
function showToast(type, message) {
    // Si existe un sistema de toasts global, usarlo
    if (typeof window.showNotification === 'function') {
        window.showNotification(type, message);
        return;
    }
    
    // Fallback: usar console
    console.log(`[${type.toUpperCase()}]`, message);
}

// Log de inicialización
console.log('✅ Phase Quick Actions loaded');
