/**
 * Sistema de eliminación de clientes con modal de confirmación
 * Intercepta enlaces de eliminación y muestra modales visuales
 */

class ClientDeleteManager {
    constructor() {
        this.init();
    }

    init() {
        // Interceptar clicks en enlaces de eliminación
        document.addEventListener('click', (e) => {
            // Selector mejorado para detectar enlaces de eliminación de clientes
            // Busca enlaces que contengan "/delete/" y estén dentro de una tabla de clientes o tengan la clase delete
            const deleteLink = e.target.closest('a[href*="/clients/"][href*="/delete/"], a.action-btn.delete[href*="/delete/"]');
            
            // Verificar que estamos en contexto de clientes (para evitar falsos positivos)
            if (deleteLink && (document.querySelector('.client-management-page') || deleteLink.href.includes('client'))) {
                e.preventDefault();
                this.handleDeleteClick(deleteLink);
            }
        });
    }

    /**
     * Manejar click en enlace de eliminar
     */
    async handleDeleteClick(link) {
        const clientId = this.extractClientId(link.href);
        if (!clientId) {
            console.error('No se pudo extraer el ID del cliente');
            return;
        }

        // Extraer información del cliente del DOM
        const row = link.closest('tr, .mobile-client-card');
        if (!row) {
            console.error('No se encontró la fila del cliente');
            return;
        }

        const clientName = this.extractClientName(row);
        const projectCount = this.extractProjectCount(row);
        
        // Mostrar modal de confirmación
        this.showDeleteModal(clientId, clientName, projectCount, link.href);
    }

    /**
     * Extraer ID del cliente del URL
     */
    extractClientId(url) {
        const match = url.match(/\/client[s]?\/(\d+)\/delete/);
        return match ? match[1] : null;
    }

    /**
     * Extraer nombre del cliente
     */
    extractClientName(row) {
        const nameElement = row.querySelector('.client-name, .list-name, td:nth-child(2)');
        return nameElement ? nameElement.textContent.trim() : 'Cliente';
    }

    /**
     * Extraer cantidad de proyectos del cliente
     */
    extractProjectCount(row) {
        // Buscar en el badge de proyectos
        const projectBadge = row.querySelector('.project-count, [class*="project"]');
        if (projectBadge) {
            const match = projectBadge.textContent.match(/(\d+)/);
            return match ? parseInt(match[1]) : 0;
        }
        
        // Buscar en data attribute
        if (row.dataset.projects) {
            return parseInt(row.dataset.projects);
        }
        
        return 0;
    }

    /**
     * Mostrar modal de confirmación
     */
    showDeleteModal(clientId, clientName, projectCount, deleteUrl) {
        const modal = ConfirmationModals.deleteClient(clientName, projectCount);

        modal.config.onConfirm = async () => {
            await this.deleteClient(clientId, deleteUrl);
        };

        modal.show();
    }

    /**
     * Eliminar cliente vía POST
     */
    async deleteClient(clientId, deleteUrl) {
        try {
            const response = await fetch(deleteUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            });

            if (response.ok) {
                // Animación de salida y recarga
                const row = document.querySelector(`tr[data-client-id="${clientId}"], .mobile-client-card[data-client-id="${clientId}"]`);
                if (row) {
                    row.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                    row.style.opacity = '0';
                    row.style.transform = 'scale(0.95)';
                    
                    setTimeout(() => {
                        window.location.reload();
                    }, 300);
                } else {
                    window.location.reload();
                }
            } else {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.error || 'Error al eliminar el cliente');
            }
        } catch (error) {
            console.error('Error:', error);
            throw error; // Re-lanzar para que el modal maneje el error
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
        if (!window.clientDeleteManager) {
            window.clientDeleteManager = new ClientDeleteManager();
        }
    });
} else {
    if (!window.clientDeleteManager) {
        window.clientDeleteManager = new ClientDeleteManager();
    }
}
