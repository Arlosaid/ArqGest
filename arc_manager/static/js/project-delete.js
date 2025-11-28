/**
 * Project Delete Manager
 * Sistema unificado para eliminación de proyectos con modales visuales y estadísticas
 */

class ProjectDeleteManager {
    constructor() {
        this.init();
    }

    init() {
        // Interceptar todos los enlaces de eliminación de proyecto
        document.addEventListener('click', (e) => {
            // Buscar el enlace de eliminación (puede ser el target o un ancestro)
            const deleteLink = e.target.closest('a[href*="/projects/"][href*="/delete/"]') || 
                              (e.target.tagName === 'A' && e.target.href.includes('/projects/') && e.target.href.includes('/delete/') ? e.target : null);
            
            if (deleteLink) {
                // Extraer ID del proyecto desde la URL
                const projectId = this.extractProjectId(deleteLink.href);
                
                if (projectId) {
                    e.preventDefault();
                    e.stopPropagation();
                    this.confirmDelete(projectId, deleteLink);
                }
                // Si no se puede extraer el ID, dejar que el enlace funcione normalmente
            }
        });
    }

    extractProjectId(url) {
        // Extraer ID desde URLs como /projects/123/delete/ o /projects/123/delete
        const match = url.match(/\/projects\/(\d+)\/delete\/?/);
        return match ? match[1] : null;
    }

    async confirmDelete(projectId, linkElement) {
        // Verificar que ConfirmationModals esté disponible
        if (typeof ConfirmationModals === 'undefined') {
            // Fallback a confirm nativo si no hay modales
            if (confirm('¿Estás seguro de que deseas eliminar este proyecto?')) {
                await this.deleteProject(projectId, linkElement.href);
            }
            return;
        }

        try {
            let stats;
            
            // OPTIMIZACIÓN: Intentar obtener datos desde data attributes primero (evita AJAX)
            const projectName = linkElement.getAttribute('data-project-name');
            const phaseCount = linkElement.getAttribute('data-phase-count');
            const taskCount = linkElement.getAttribute('data-task-count');
            const fileCount = linkElement.getAttribute('data-file-count');
            
            if (projectName && phaseCount !== null && taskCount !== null && fileCount !== null) {
                stats = {
                    name: projectName,
                    phase_count: parseInt(phaseCount) || 0,
                    task_count: parseInt(taskCount) || 0,
                    file_count: parseInt(fileCount) || 0
                };
            } else {
                // Fallback: Obtener estadísticas del proyecto via AJAX
                stats = await this.getProjectStats(projectId);
            }
            
            // Verificar que los datos sean válidos
            if (!stats || typeof stats.name === 'undefined') {
                throw new Error('Datos de estadísticas inválidos');
            }
            
            // Mostrar modal de confirmación con estadísticas
            ConfirmationModals.deleteProject({
                projectId: projectId,
                projectName: stats.name,
                phaseCount: stats.phase_count || 0,
                taskCount: stats.task_count || 0,
                fileCount: stats.file_count || 0,
                onConfirm: async () => {
                    await this.deleteProject(projectId, linkElement.href);
                }
            });

        } catch (error) {
            // Fallback: mostrar modal básico sin stats
            ConfirmationModals.deleteProject({
                projectId: projectId,
                projectName: 'este proyecto',
                phaseCount: 0,
                taskCount: 0,
                fileCount: 0,
                onConfirm: async () => {
                    await this.deleteProject(projectId, linkElement.href);
                }
            });
        }
    }

    async getProjectStats(projectId) {
        const url = `/projects/${projectId}/stats/`;
        
        try {
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error(`Failed to fetch project stats: ${response.status}`);
            }

            const contentType = response.headers.get('Content-Type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Server returned HTML instead of JSON');
            }

            const data = await response.json();
            
            // Validar que los datos tengan el formato esperado
            if (typeof data.name === 'undefined' || 
                typeof data.phase_count === 'undefined' ||
                typeof data.task_count === 'undefined' ||
                typeof data.file_count === 'undefined') {
                throw new Error('Incomplete data received from server');
            }
            
            return data;

        } catch (error) {
            // Devolver stats vacías en caso de error
            return {
                name: 'el proyecto',
                phase_count: 0,
                task_count: 0,
                file_count: 0
            };
        }
    }

    async deleteProject(projectId, deleteUrl) {
        const finalUrl = `/projects/${projectId}/delete/`;

        try {
            const csrfToken = this.getCsrfToken();
            if (!csrfToken) {
                this.showErrorMessage('Error de seguridad: Token CSRF no encontrado');
                return;
            }

            const response = await fetch(finalUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken
                }
            });

            // Check if we were redirected to the confirmation page
            if (response.url && response.url.includes('/delete/') && !response.url.includes('/login/')) {
                 this.showErrorMessage('Error: La solicitud de eliminación no se procesó correctamente.');
                 return;
            }

            if (response.ok) {
                this.showSuccessMessage('Proyecto eliminado correctamente');
                setTimeout(() => {
                    window.location.href = '/projects/';
                }, 1500);
            } else {
                const data = await response.json().catch(() => ({}));
                this.showErrorMessage(data.error || 'Error al eliminar el proyecto');
            }

        } catch (error) {
            this.showErrorMessage('Error de conexión al eliminar el proyecto');
        }
    }

    showSuccessMessage(message) {
        this.showToast(message, 'success');
    }

    showErrorMessage(message) {
        this.showToast(message, 'error');
    }

    showToast(message, type = 'success') {
        // Intentar usar el sistema de notificaciones global primero
        if (window.notifications) {
            if (type === 'success') {
                window.notifications.success(message);
            } else {
                window.notifications.error(message);
            }
            return;
        }

        if (typeof window.showToast === 'function') {
            window.showToast(message, type);
            return;
        }

        const toastHtml = `
            <div class="toast align-items-center text-white bg-${type === 'success' ? 'success' : 'danger'} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;

        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '1055';
            document.body.appendChild(toastContainer);
        }

        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        const toastElement = toastContainer.lastElementChild;
        const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
        toast.show();

        toastElement.addEventListener('hidden.bs.toast', function () {
            this.remove();
        });
    }

    getCsrfToken() {
        // 1. Intentar obtener del meta tag (método preferido y más seguro)
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        if (metaToken) {
            const token = metaToken.getAttribute('content');
            if (token && token.trim() !== '') return token;
        }

        // 2. Fallback: buscar en el DOM (input hidden generado por {% csrf_token %})
        // Esto funcionará gracias al div oculto agregado en base.html
        const input = document.querySelector('[name=csrfmiddlewaretoken]');
        if (input && input.value) return input.value;

        // 3. Intentar obtener del cookie (puede fallar si es HttpOnly)
        const value = `; ${document.cookie}`;
        const parts = value.split(`; csrftoken=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        
        return '';
    }
}

// Inicializar automáticamente
document.addEventListener('DOMContentLoaded', () => {
    window.projectDeleteManager = new ProjectDeleteManager();
});
