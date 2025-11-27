/**
 * Sistema de Toggle de Estado (Activo/Inactivo/Archivado)
 * Maneja el cambio de estado de usuarios, clientes y proyectos de forma optimizada
 * Recarga la página al cambiar estado de proyectos cuando hay filtros activos
 * @version 2.1
 * @author ARC Manager
 */

class StatusToggleManager {
    constructor() {
        this.initializeToggles();
    }

    initializeToggles() {
        // Buscar todos los toggles en la página
        const toggles = document.querySelectorAll('[data-toggle-status]');
        
        toggles.forEach(toggle => {
            toggle.addEventListener('click', (e) => this.handleToggle(e, toggle));
        });
    }

    async handleToggle(event, toggle) {
        event.preventDefault();
        event.stopPropagation();

        // Prevenir clicks múltiples
        if (toggle.classList.contains('disabled') || toggle.hasAttribute('disabled')) {
            return;
        }

        const entityType = toggle.dataset.toggleStatus; // 'user', 'client' o 'project'
        const entityId = toggle.dataset.entityId;
        const currentStatus = toggle.dataset.currentStatus === 'true';
        const entityName = toggle.dataset.entityName || 'este elemento';

        // Deshabilitar temporalmente
        toggle.classList.add('disabled');
        toggle.style.pointerEvents = 'none';

        // Determinar acción
        const action = currentStatus ? 'desactivar' : 'activar';
        const newStatus = !currentStatus;

        try {
            // Mostrar confirmación si se está desactivando
            if (currentStatus && !await this.showConfirmation(entityType, entityName, action)) {
                toggle.classList.remove('disabled');
                toggle.style.pointerEvents = 'auto';
                return;
            }

            // Obtener URL del endpoint
            const url = this.getEndpointUrl(entityType, entityId);

            // Enviar petición
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    is_active: newStatus
                })
            });

            const data = await response.json();

            if (data.success) {
                // Actualizar UI
                this.updateToggleUI(toggle, newStatus);
                
                // Mostrar notificación de éxito
                const entityLabel = entityType === 'user' ? 'Usuario' : entityType === 'client' ? 'Cliente' : 'Proyecto';
                this.showNotification('success', data.message || `${entityLabel} ${action} correctamente`);
                
                // Actualizar contadores si existen
                this.updateCounters(data);
                
                // Si es un proyecto, manejar la visibilidad según los filtros actuales
                if (entityType === 'project') {
                    this.handleProjectVisibility(toggle, newStatus);
                }
                
            } else {
                // Mostrar error
                this.showNotification('error', data.error || 'Error al cambiar el estado');
            }

        } catch (error) {
            console.error('Error al cambiar estado:', error);
            this.showNotification('error', 'Error de conexión. Por favor intenta de nuevo.');
        } finally {
            // Rehabilitar el toggle
            toggle.classList.remove('disabled');
            toggle.style.pointerEvents = 'auto';
        }
    }

    async showConfirmation(entityType, entityName, action) {
        const messages = {
            user: {
                desactivar: `¿Estás seguro de desactivar al usuario <strong>${entityName}</strong>?<br><br>
                            <small>• No podrá iniciar sesión<br>
                            • Sus datos se mantendrán<br>
                            • Puedes reactivarlo después</small>`
            },
            client: {
                desactivar: `¿Desactivar el cliente <strong>${entityName}</strong>?<br><br>
                            <small>• No aparecerá en formularios<br>
                            • Sus proyectos se mantienen<br>
                            • Puedes reactivarlo después</small>`
            },
            project: {
                desactivar: `¿Archivar el proyecto <strong>${entityName}</strong>?<br><br>
                            <small>• Se marcará como archivado<br>
                            • Todas las tareas y fases se mantienen<br>
                            • Puedes reactivarlo después</small>`
            }
        };

        const message = messages[entityType]?.[action] || `¿${action.charAt(0).toUpperCase() + action.slice(1)} ${entityName}?`;

        return new Promise((resolve) => {
            // Crear modal de confirmación simple
            const modal = document.createElement('div');
            modal.className = 'status-toggle-modal';
            modal.innerHTML = `
                <div class="status-toggle-modal-overlay"></div>
                <div class="status-toggle-modal-content">
                    <div class="status-toggle-modal-header">
                        <h3>Confirmar acción</h3>
                    </div>
                    <div class="status-toggle-modal-body">
                        <p>${message}</p>
                    </div>
                    <div class="status-toggle-modal-footer">
                        <button class="btn-cancel">Cancelar</button>
                        <button class="btn-confirm">Confirmar</button>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);

            // Manejadores
            const btnCancel = modal.querySelector('.btn-cancel');
            const btnConfirm = modal.querySelector('.btn-confirm');
            const overlay = modal.querySelector('.status-toggle-modal-overlay');

            const closeModal = (confirmed) => {
                modal.classList.add('closing');
                setTimeout(() => {
                    document.body.removeChild(modal);
                    resolve(confirmed);
                }, 200);
            };

            btnCancel.addEventListener('click', () => closeModal(false));
            overlay.addEventListener('click', () => closeModal(false));
            btnConfirm.addEventListener('click', () => closeModal(true));

            // Mostrar modal con animación
            setTimeout(() => modal.classList.add('show'), 10);
        });
    }

    updateToggleUI(toggle, newStatus) {
        // Actualizar atributo de datos
        toggle.dataset.currentStatus = newStatus.toString();

        // Actualizar clases
        const switchElement = toggle.querySelector('.toggle-switch');
        const statusText = toggle.querySelector('.toggle-status-text');
        
        // Detectar si es un proyecto o usuario/cliente
        const entityType = toggle.dataset.toggleStatus;
        const inactiveText = entityType === 'project' ? 'Archivado' : 'Inactivo';
        const inactiveClass = entityType === 'project' ? 'status-archived' : 'status-inactive';
        const switchInactiveClass = entityType === 'project' ? 'archived' : 'inactive';

        if (switchElement) {
            if (newStatus) {
                switchElement.classList.remove('inactive', 'archived');
                switchElement.classList.add('active');
            } else {
                switchElement.classList.remove('active');
                switchElement.classList.add(switchInactiveClass);
            }
        }

        if (statusText) {
            statusText.textContent = newStatus ? 'Activo' : inactiveText;
            statusText.className = `toggle-status-text ${newStatus ? 'status-active' : inactiveClass}`;
        }

        // Si es un proyecto, actualizar el atributo data-status de la card
        if (entityType === 'project') {
            const projectCard = toggle.closest('.project-card');
            if (projectCard) {
                projectCard.dataset.status = newStatus ? 'active' : 'archived';
            }
        }

        // Animar el cambio
        toggle.classList.add('toggle-animation');
        setTimeout(() => toggle.classList.remove('toggle-animation'), 300);
    }

    handleProjectVisibility(toggle, newStatus) {
        const urlParams = new URLSearchParams(window.location.search);
        const currentFilter = urlParams.get('status');
        
        // Si no hay filtro de estado, no ocultamos nada
        if (!currentFilter) return;

        const projectCard = toggle.closest('.project-card');
        if (!projectCard) return;

        // Si el filtro es 'active' y el nuevo estado es false (archivado) -> Ocultar
        // Si el filtro es 'archived' y el nuevo estado es true (activo) -> Ocultar
        const shouldHide = (currentFilter === 'active' && !newStatus) || 
                          (currentFilter === 'archived' && newStatus);

        if (shouldHide) {
            // Animación de salida
            projectCard.style.transition = 'all 0.3s ease';
            projectCard.style.opacity = '0';
            projectCard.style.transform = 'scale(0.95)';
            
            setTimeout(() => {
                projectCard.style.display = 'none';
                this.checkEmptyState();
            }, 300);
        }
    }

    checkEmptyState() {
        const visibleProjects = document.querySelectorAll('.project-card:not([style*="display: none"])');
        const emptyState = document.querySelector('.empty-state');
        
        if (visibleProjects.length === 0) {
            if (emptyState) {
                emptyState.style.display = 'flex';
                // Asegurar que se vea con animación
                emptyState.style.opacity = '0';
                setTimeout(() => emptyState.style.opacity = '1', 10);
            } else {
                // Si no existe el empty state (porque había proyectos al cargar), recargar para mostrarlo
                // o podríamos inyectarlo dinámicamente, pero recargar aquí es un fallback aceptable
                window.location.reload();
            }
        }
    }

    updateCounters(data) {
        // Actualizar contadores en la página si existen
        if (data.stats) {
            // Contadores de Usuarios (por ID)
            const userElements = {
                total_users: document.getElementById('total-users-count'),
                active_users: document.getElementById('active-users-count'),
                inactive_users: document.getElementById('inactive-users-count'),
                percentage_active: document.getElementById('percentage-active')
            };

            Object.keys(userElements).forEach(key => {
                if (userElements[key] && data.stats[key] !== undefined) {
                    this.animateCounter(userElements[key], data.stats[key]);
                }
            });

            // Contadores de Proyectos (por Clase)
            const projectStatsMap = {
                'total_projects': '.stat-card-modern.total .stat-value',
                'active_projects': '.stat-card-modern.active-projects .stat-value',
                'completed_projects': '.stat-card-modern.completed .stat-value',
                'archived_projects': '.stat-card-modern.archived .stat-value'
            };

            Object.keys(projectStatsMap).forEach(key => {
                if (data.stats[key] !== undefined) {
                    const element = document.querySelector(projectStatsMap[key]);
                    if (element) {
                        this.animateCounter(element, data.stats[key]);
                    }
                }
            });
        }
    }

    animateCounter(element, newValue) {
        element.textContent = newValue;
        element.classList.add('counter-update');
        setTimeout(() => element.classList.remove('counter-update'), 500);
    }

    getEndpointUrl(entityType, entityId) {
        const endpoints = {
            user: `/users/${entityId}/toggle-status/`,
            client: `/organizations/clients/${entityId}/toggle-status/`,
            project: `/projects/${entityId}/toggle-status/`
        };

        return endpoints[entityType] || '#';
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                     document.querySelector('meta[name="csrf-token"]')?.content ||
                     this.getCookie('csrftoken');
        return token || '';
    }

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    showNotification(type, message) {
        // Usar sistema de notificaciones existente si está disponible
        if (window.notifications && typeof window.notifications[type] === 'function') {
            window.notifications[type](message);
            return;
        }

        // Fallback: notificación simple
        const notification = document.createElement('div');
        notification.className = `status-toggle-notification ${type}`;
        notification.innerHTML = `
            <span class="notification-icon">${type === 'success' ? '✓' : '✕'}</span>
            <span class="notification-message">${message}</span>
        `;

        document.body.appendChild(notification);

        setTimeout(() => notification.classList.add('show'), 10);
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => document.body.removeChild(notification), 300);
        }, 3000);
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.statusToggleManager = new StatusToggleManager();
});

// Reinicializar después de cargas dinámicas (HTMX, AJAX, etc.)
document.addEventListener('htmx:afterSwap', () => {
    if (window.statusToggleManager) {
        window.statusToggleManager.initializeToggles();
    }
});

