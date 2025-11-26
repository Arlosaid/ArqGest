/**
 * Sistema unificado de eliminación para plantillas de fases
 * Intercepta enlaces de eliminación y muestra modales visuales
 */

class TemplateDeleteManager {
    constructor() {
        this.init();
    }

    init() {
        // Interceptar clicks en enlaces de eliminación de plantillas
        document.addEventListener('click', (e) => {
            const deleteLink = e.target.closest('a[href*="phasetemplate"][href*="delete"], a[href*="defaultphase"][href*="delete"]');
            if (deleteLink) {
                e.preventDefault();
                this.handleDeleteClick(deleteLink);
            }
        });
        
        console.log('✅ TemplateDeleteManager inicializado');
    }

    /**
     * Manejar click en enlace de eliminar
     */
    async handleDeleteClick(link) {
        const deleteUrl = link.href;
        const isTemplate = deleteUrl.includes('phasetemplate');
        const isPhase = deleteUrl.includes('defaultphase');
        
        // Extraer información del elemento a eliminar
        const row = link.closest('tr, .template-card, .phase-card');
        if (!row) {
            console.error('No se encontró el elemento');
            return;
        }

        if (isTemplate) {
            await this.handleTemplateDelete(row, deleteUrl);
        } else if (isPhase) {
            await this.handlePhaseDelete(row, deleteUrl);
        }
    }

    /**
     * Manejar eliminación de plantilla
     */
    async handleTemplateDelete(row, deleteUrl) {
        const templateName = this.extractName(row);
        const phaseCount = this.extractPhaseCount(row);
        
        // Mostrar modal de confirmación
        const modal = ConfirmationModals.deleteTemplate(templateName, phaseCount);

        modal.config.onConfirm = async () => {
            await this.performDelete(deleteUrl);
        };

        modal.show();
    }

    /**
     * Manejar eliminación de fase predeterminada
     */
    async handlePhaseDelete(row, deleteUrl) {
        const phaseName = this.extractName(row);
        const templateName = this.extractTemplateName(row);
        
        // Usar modal genérico de eliminación
        const modal = new ConfirmationModal({
            type: 'danger',
            title: 'Eliminar Fase Predeterminada',
            icon: 'fa-exclamation-triangle',
            message: `¿Estás seguro de que quieres eliminar la fase "<strong>${phaseName}</strong>" de la plantilla "<strong>${templateName}</strong>"?`,
            confirmText: 'Sí, eliminar',
            confirmIcon: 'fa-trash-alt',
            modalClass: 'phase-delete-modal'
        });

        modal.config.onConfirm = async () => {
            await this.performDelete(deleteUrl);
        };

        modal.show();
    }

    /**
     * Extraer nombre del elemento
     */
    extractName(row) {
        const nameElement = row.querySelector('.template-name, .phase-name, .list-name, td:nth-child(2), strong');
        return nameElement ? nameElement.textContent.trim() : 'Elemento';
    }

    /**
     * Extraer cantidad de fases
     */
    extractPhaseCount(row) {
        const phaseElement = row.querySelector('.phases-count, [class*="phase"]');
        if (phaseElement) {
            const match = phaseElement.textContent.match(/(\d+)/);
            return match ? parseInt(match[1]) : 0;
        }
        return 0;
    }

    /**
     * Extraer nombre de la plantilla (para fases)
     */
    extractTemplateName(row) {
        const templateElement = row.querySelector('.template-name, [data-template-name]');
        if (templateElement) {
            return templateElement.dataset.templateName || templateElement.textContent.trim();
        }
        
        // Buscar en breadcrumbs o título de página
        const breadcrumb = document.querySelector('.breadcrumb-item.active, .page-title');
        return breadcrumb ? breadcrumb.textContent.trim() : 'Plantilla';
    }

    /**
     * Ejecutar eliminación vía POST
     */
    async performDelete(deleteUrl) {
        try {
            const response = await fetch(deleteUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            });

            if (response.ok) {
                // Intentar redirigir a la URL de success si es una respuesta redirect
                if (response.redirected) {
                    window.location.href = response.url;
                } else {
                    // Si no hay redirect, recargar o volver a la lista
                    const data = await response.json().catch(() => null);
                    if (data && data.redirect_url) {
                        window.location.href = data.redirect_url;
                    } else {
                        // Volver a la lista de plantillas
                        const isTemplate = deleteUrl.includes('phasetemplate');
                        if (isTemplate) {
                            window.location.href = '/projects/phase-templates/';
                        } else {
                            window.location.reload();
                        }
                    }
                }
            } else {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.error || 'Error al eliminar');
            }
        } catch (error) {
            console.error('Error:', error);
            throw error;
        }
    }

    /**
     * Obtener CSRF token
     */
    getCSRFToken() {
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfInput) return csrfInput.value;

        const csrfCookie = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='));
        
        return csrfCookie ? csrfCookie.split('=')[1] : '';
    }
}

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (!window.templateDeleteManager) {
            window.templateDeleteManager = new TemplateDeleteManager();
        }
    });
} else {
    if (!window.templateDeleteManager) {
        window.templateDeleteManager = new TemplateDeleteManager();
    }
}
