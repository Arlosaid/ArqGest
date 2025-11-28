/**
 * Sistema Unificado de Modales de Confirmación
 * Diseño consistente, centrado y visualmente atractivo para toda la aplicación
 */

class ConfirmationModal {
    constructor(config) {
        this.config = {
            id: `confirmModal-${Date.now()}`,
            type: 'danger', // 'danger', 'warning', 'info'
            title: 'Confirmar acción',
            icon: 'fa-exclamation-triangle',
            message: '¿Estás seguro de que deseas continuar?',
            itemName: null,
            itemMeta: null,
            itemIcon: null,
            showStats: false,
            stats: [],
            affectedItems: [],
            confirmText: 'Confirmar',
            confirmIcon: 'fa-check',
            cancelText: 'Cancelar',
            cancelIcon: 'fa-times',
            onConfirm: null,
            onCancel: null,
            modalClass: '',
            ...config
        };
        
        this.modalElement = null;
        this.modalInstance = null;
        this.isProcessing = false;
    }

    /**
     * Crear y mostrar el modal
     */
    show() {
        // Limpiar modal anterior si existe
        this.cleanup();
        
        // Crear el modal
        this.create();
        
        // Mostrar el modal
        this.modalInstance = new bootstrap.Modal(this.modalElement);
        this.modalInstance.show();
        
        // Configurar event listeners
        this.setupEventListeners();
        
        return this;
    }

    /**
     * Crear el HTML del modal
     */
    create() {
        const modalHtml = `
        <div class="modal fade confirmation-modal ${this.config.modalClass}" 
             id="${this.config.id}" 
             tabindex="-1" 
             aria-labelledby="${this.config.id}Label" 
             aria-hidden="true"
             data-bs-backdrop="static"
             data-bs-keyboard="true">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    ${this.createHeader()}
                    ${this.createBody()}
                    ${this.createFooter()}
                </div>
            </div>
        </div>`;
        
        // Insertar en el DOM
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        this.modalElement = document.getElementById(this.config.id);
    }

    /**
     * Crear header del modal
     */
    createHeader() {
        const bgClass = this.config.type === 'warning' ? 'bg-warning' : 
                       this.config.type === 'info' ? 'bg-info' : 'bg-danger';
        
        const closeClass = this.config.type === 'warning' ? '' : 'btn-close-white';
        
        return `
        <div class="modal-header ${bgClass}">
            <h5 class="modal-title" id="${this.config.id}Label">
                <i class="fas ${this.config.icon}"></i>
                ${this.config.title}
            </h5>
            <button type="button" class="btn-close ${closeClass}" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>`;
    }

    /**
     * Crear body del modal
     */
    createBody() {
        let bodyContent = '';
        
        // Icono central decorativo
        if (this.config.icon) {
            const iconClass = this.config.type;
            bodyContent += `
            <div class="modal-icon-center ${iconClass}">
                <i class="fas ${this.config.icon}"></i>
            </div>`;
        }
        
        // Mensaje principal
        bodyContent += `<p class="confirmation-message">${this.config.message}</p>`;
        
        // Detalles del item (si existen)
        if (this.config.itemName) {
            bodyContent += this.createItemDetails();
        }
        
        // Estadísticas (si existen)
        if (this.config.showStats && this.config.stats.length > 0) {
            bodyContent += this.createStats();
        }
        
        // Items afectados (si existen)
        if (this.config.affectedItems.length > 0) {
            bodyContent += this.createAffectedItems();
        }
        
        // Advertencia final
        bodyContent += `
        <div class="final-warning">
            <div class="warning-icon">
                <i class="fas fa-exclamation-circle"></i>
            </div>
            <div class="warning-text">Esta acción no se puede deshacer</div>
            <p class="warning-subtext">¿Estás seguro de que deseas continuar?</p>
        </div>`;
        
        return `<div class="modal-body">${bodyContent}</div>`;
    }

    /**
     * Crear detalles del item
     */
    createItemDetails() {
        const icon = this.config.itemIcon || 'fa-file';
        const meta = this.config.itemMeta || '';
        
        return `
        <div class="item-details-card">
            <div class="d-flex align-items-center">
                <div class="item-icon">
                    <i class="fas ${icon}"></i>
                </div>
                <div class="flex-grow-1">
                    <div class="item-name">${this.config.itemName}</div>
                    ${meta ? `<div class="item-meta">${meta}</div>` : ''}
                </div>
            </div>
        </div>`;
    }

    /**
     * Crear estadísticas
     */
    createStats() {
        const statsHtml = this.config.stats.map(stat => `
            <div class="deletion-stat">
                <span class="deletion-stat-value">${stat.value}</span>
                <span class="deletion-stat-label">
                    <i class="fas ${stat.icon}"></i> ${stat.label}
                </span>
            </div>
        `).join('');
        
        return `<div class="deletion-stats">${statsHtml}</div>`;
    }

    /**
     * Crear lista de items afectados
     */
    createAffectedItems() {
        const itemsHtml = this.config.affectedItems.map(item => 
            `<li><strong>${item.name}:</strong> ${item.description}</li>`
        ).join('');
        
        return `
        <div class="affected-items-list">
            <strong>Items afectados:</strong>
            <ul>${itemsHtml}</ul>
        </div>`;
    }

    /**
     * Crear footer del modal
     */
    createFooter() {
        const btnClass = this.config.type === 'warning' ? 'btn-warning' : 'btn-danger';
        
        return `
        <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                <i class="fas ${this.config.cancelIcon}"></i>
                ${this.config.cancelText}
            </button>
            <button type="button" class="btn ${btnClass}" id="${this.config.id}-confirm">
                <i class="fas ${this.config.confirmIcon}"></i>
                ${this.config.confirmText}
            </button>
        </div>`;
    }

    /**
     * Configurar event listeners
     */
    setupEventListeners() {
        const confirmBtn = document.getElementById(`${this.config.id}-confirm`);
        
        if (confirmBtn) {
            confirmBtn.addEventListener('click', () => this.handleConfirm());
        }
        
        // Guardar referencia al elemento que tenía el foco antes del modal
        this.previouslyFocusedElement = document.activeElement;
        
        // Manejar cierre del modal (tanto por cancelar como por ESC)
        this.modalElement.addEventListener('hide.bs.modal', () => {
            // Devolver foco al elemento anterior para evitar warning de aria-hidden
            if (this.previouslyFocusedElement && this.previouslyFocusedElement !== document.body) {
                // Usar setTimeout para asegurar que el modal se cierre primero
                setTimeout(() => {
                    this.previouslyFocusedElement.focus();
                }, 100);
            }
        });
        
        // Limpiar al cerrar completamente
        this.modalElement.addEventListener('hidden.bs.modal', () => {
            if (!this.isProcessing) {
                this.cleanup();
            }
        });
    }

    /**
     * Manejar confirmación
     */
    async handleConfirm() {
        if (this.isProcessing) return;
        
        const confirmBtn = document.getElementById(`${this.config.id}-confirm`);
        const originalHtml = confirmBtn.innerHTML;
        
        // Mostrar estado de carga
        confirmBtn.disabled = true;
        confirmBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Procesando...`;
        this.isProcessing = true;
        
        try {
            if (this.config.onConfirm) {
                await this.config.onConfirm();
            }
            
            // Cerrar modal
            this.hide();
        } catch (error) {
            // Restaurar botón
            confirmBtn.disabled = false;
            confirmBtn.innerHTML = originalHtml;
            this.isProcessing = false;
            
            // Mostrar error (puedes personalizar esto)
            this.showError(error.message || 'Error al procesar la acción');
        }
    }

    /**
     * Mostrar error en el modal
     */
    showError(message) {
        const modalBody = this.modalElement.querySelector('.modal-body');
        const errorHtml = `
        <div class="alert alert-danger alert-dismissible fade show mt-3" role="alert">
            <i class="fas fa-exclamation-circle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>`;
        
        modalBody.insertAdjacentHTML('beforeend', errorHtml);
    }

    /**
     * Ocultar modal
     */
    hide() {
        if (this.modalInstance) {
            this.modalInstance.hide();
        }
    }

    /**
     * Limpiar modal del DOM
     */
    cleanup() {
        const existingModal = document.getElementById(this.config.id);
        if (existingModal) {
            // Eliminar instancia de Bootstrap si existe
            const instance = bootstrap.Modal.getInstance(existingModal);
            if (instance) {
                instance.dispose();
            }
            existingModal.remove();
        }
        
        // Limpiar backdrops huérfanos
        document.querySelectorAll('.modal-backdrop').forEach(backdrop => backdrop.remove());
        
        // Restaurar estado del body solo si no hay otros modales abiertos
        const openModals = document.querySelectorAll('.modal.show');
        if (openModals.length === 0) {
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
        }
    }
}

/**
 * Factory functions para tipos comunes de modales
 */

const ConfirmationModals = {
    /**
     * Modal de eliminación estándar
     */
    delete: (config) => {
        const modal = new ConfirmationModal({
            type: 'danger',
            title: 'Confirmar eliminación',
            icon: 'fa-exclamation-triangle',
            message: '¿Estás seguro de que deseas eliminar este elemento?',
            confirmText: 'Sí, eliminar',
            confirmIcon: 'fa-trash-alt',
            ...config
        });
        modal.show();
        return modal;
    },

    /**
     * Modal de eliminación de archivo
     */
    deleteFile: (fileName, fileMeta, fileIcon) => {
        const modal = new ConfirmationModal({
            type: 'danger',
            title: 'Confirmar eliminación',
            icon: 'fa-exclamation-triangle',
            message: '¿Estás seguro de que deseas eliminar el siguiente archivo?',
            itemName: fileName,
            itemMeta: fileMeta,
            itemIcon: fileIcon || 'fa-file',
            confirmText: 'Eliminar archivo',
            confirmIcon: 'fa-trash-alt',
            modalClass: 'file-delete-modal'
        });
        modal.show();
        return modal;
    },

    /**
     * Modal de eliminación de tarea
     */
    deleteTask: (config) => {
        const taskConfig = {
            type: 'danger',
            title: 'Confirmar eliminación de tarea',
            icon: 'fa-exclamation-triangle',
            message: '¿Estás seguro de que deseas eliminar la siguiente tarea?',
            itemName: config.taskTitle || 'esta tarea',
            itemMeta: config.taskDescription || null,
            itemIcon: 'fa-tasks',
            confirmText: 'Eliminar tarea',
            confirmIcon: 'fa-trash-alt',
            modalClass: 'task-delete-modal',
            onConfirm: config.onConfirm
        };

        const modal = new ConfirmationModal(taskConfig);
        modal.show();
        return modal;
    },

    /**
     * Modal de eliminación de pago
     */
    deletePayment: (paymentInfo) => {
        // Construir nombre compuesto: "Descripción de Monto"
        // Ej: "Pago de $5,000.00" o "Anticipo de $5,000.00"
        let name = paymentInfo.description || 'Pago';
        if (paymentInfo.amount && paymentInfo.amount !== 'Monto no especificado') {
            // Evitar duplicar si la descripción ya contiene el monto
            if (!name.includes(paymentInfo.amount)) {
                name = `${name} de ${paymentInfo.amount}`;
            }
        }

        // Meta solo con la fecha
        const meta = paymentInfo.date ? `Fecha: ${paymentInfo.date}` : null;

        const modal = new ConfirmationModal({
            type: 'danger',
            title: 'Confirmar eliminación de pago',
            icon: 'fa-exclamation-triangle',
            message: '¿Estás seguro de que deseas eliminar este pago?',
            itemName: name,
            itemMeta: meta,
            itemIcon: 'fa-dollar-sign',
            confirmText: 'Eliminar pago',
            confirmIcon: 'fa-trash-alt',
            modalClass: 'payment-delete-modal'
        });
        modal.show();
        return modal;
    },

    /**
     * Modal de eliminación de usuario
     */
    deleteUser: (userInfo) => {
        const modal = new ConfirmationModal({
            type: 'danger',
            title: 'Confirmar eliminación de usuario',
            icon: 'fa-exclamation-triangle',
            message: '¿Estás seguro de que deseas eliminar este usuario?',
            itemName: userInfo.fullName || userInfo.username,
            itemMeta: userInfo.email,
            itemIcon: 'fa-user',
            confirmText: 'Eliminar usuario',
            confirmIcon: 'fa-trash-alt',
            modalClass: 'user-delete-modal'
        });
        modal.show();
        return modal;
    },

    /**
     * Modal de eliminación de proyecto
     */
    deleteProject: (config) => {
        const projectConfig = {
            type: 'danger',
            title: 'Confirmar eliminación de proyecto',
            icon: 'fa-exclamation-triangle',
            message: `¿Estás seguro de que deseas eliminar el proyecto "<strong>${config.projectName}</strong>"?`,
            // NO mostrar itemName para evitar redundancia (ya está en el mensaje)
            itemName: null,
            itemIcon: null,
            confirmText: 'Sí, eliminar proyecto',
            confirmIcon: 'fa-trash-alt',
            modalClass: 'project-delete-modal',
            onConfirm: config.onConfirm
        };

        // Agregar estadísticas si están disponibles
        const stats = [];
        if (config.phaseCount > 0) {
            stats.push({
                value: config.phaseCount,
                icon: 'fa-list-ul',
                label: config.phaseCount === 1 ? 'Fase' : 'Fases'
            });
        }
        if (config.taskCount > 0) {
            stats.push({
                value: config.taskCount,
                icon: 'fa-tasks',
                label: config.taskCount === 1 ? 'Tarea' : 'Tareas'
            });
        }
        // Siempre mostrar archivos (incluso si es 0) para que el usuario sepa
        if (config.fileCount !== undefined) {
            stats.push({
                value: config.fileCount,
                icon: 'fa-file',
                label: config.fileCount === 1 ? 'Archivo' : 'Archivos'
            });
        }

        if (stats.length > 0) {
            projectConfig.stats = stats;
            projectConfig.showStats = true;
            projectConfig.message += '<br><small class="text-muted">Se eliminarán todos los elementos asociados:</small>';
        }

        const modal = new ConfirmationModal(projectConfig);
        modal.show();
        return modal;
    },

    /**
     * Modal de eliminación de cliente
     */
    deleteClient: (clientName, projectCount) => {
        const config = {
            type: 'danger',
            title: 'Confirmar eliminación de cliente',
            icon: 'fa-exclamation-triangle',
            itemName: clientName,
            itemIcon: 'fa-building',
            confirmText: 'Sí, eliminar cliente',
            confirmIcon: 'fa-trash-alt',
            modalClass: 'client-delete-modal'
        };

        if (projectCount > 0) {
            config.message = `Este cliente tiene <strong>${projectCount} proyecto(s)</strong> asociado(s). Al eliminar el cliente, estos proyectos quedarán desvinculados (sin cliente asignado).`;
            config.stats = [{
                value: projectCount,
                icon: 'fa-project-diagram',
                label: 'Proyectos afectados'
            }];
            config.showStats = true;
        } else {
            config.message = '¿Estás seguro de que deseas eliminar este cliente?';
        }

        const modal = new ConfirmationModal(config);
        modal.show();
        return modal;
    },

    /**
     * Modal de eliminación de plantilla
     */
    deleteTemplate: (templateName, phaseCount) => {
        const modal = new ConfirmationModal({
            type: 'danger',
            title: 'Confirmar eliminación de plantilla',
            icon: 'fa-exclamation-triangle',
            message: `¿Estás seguro de que deseas eliminar la plantilla "<strong>${templateName}</strong>"?`,
            itemName: templateName,
            itemIcon: 'fa-layer-group',
            stats: phaseCount ? [{
                value: phaseCount,
                icon: 'fa-list-ul',
                label: 'Fases en la plantilla'
            }] : [],
            showStats: phaseCount > 0,
            confirmText: 'Eliminar plantilla',
            confirmIcon: 'fa-trash-alt',
            modalClass: 'template-delete-modal'
        });
        modal.show();
        return modal;
    },

    /**
     * Modal de advertencia (no destructivo)
     */
    warning: (config) => {
        const modal = new ConfirmationModal({
            type: 'warning',
            title: 'Advertencia',
            icon: 'fa-exclamation-triangle',
            confirmText: 'Continuar',
            confirmIcon: 'fa-check',
            ...config
        });
        modal.show();
        return modal;
    }
};

// Exportar para uso global
if (typeof window !== 'undefined') {
    window.ConfirmationModal = ConfirmationModal;
    window.ConfirmationModals = ConfirmationModals;
}
