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
                    console.log('🗑️ Intercepting delete click for project:', projectId);
                    e.preventDefault();
                    e.stopPropagation();
                    this.confirmDelete(projectId, deleteLink);
                } else {
                    console.warn('⚠️ Could not extract project ID from URL:', deleteLink.href);
                    // Do NOT prevent default here, let the link work as a fallback
                }
            }
        });
    }

    extractProjectId(url) {
        // Extraer ID desde URLs como /projects/123/delete/ o /projects/123/delete
        const match = url.match(/\/projects\/(\d+)\/delete\/?/);
        return match ? match[1] : null;
    }

    async confirmDelete(projectId, linkElement) {
        console.log('🎯 confirmDelete called with projectId:', projectId);
        
        // Verificar que ConfirmationModals esté disponible
        if (typeof ConfirmationModals === 'undefined') {
            console.error('❌ ConfirmationModals no está disponible');
            if (confirm('¿Estás seguro de que deseas eliminar este proyecto?')) {
                await this.deleteProject(projectId, linkElement.href);
            }
            return;
        }

        console.log('✅ ConfirmationModals está disponible');

        try {
            let stats;
            
            // OPTIMIZACIÓN: Intentar obtener datos desde data attributes primero (evita AJAX)
            const projectName = linkElement.getAttribute('data-project-name');
            const phaseCount = linkElement.getAttribute('data-phase-count');
            const taskCount = linkElement.getAttribute('data-task-count');
            const fileCount = linkElement.getAttribute('data-file-count');
            
            if (projectName && phaseCount !== null && taskCount !== null && fileCount !== null) {
                console.log('✅ Usando datos del atributo data-* (sin AJAX)');
                stats = {
                    name: projectName,
                    phase_count: parseInt(phaseCount) || 0,
                    task_count: parseInt(taskCount) || 0,
                    file_count: parseInt(fileCount) || 0
                };
                console.log('📊 Stats from data attributes:', stats);
            } else {
                // Fallback: Obtener estadísticas del proyecto via AJAX
                console.log('📊 Datos no disponibles en atributos, obteniendo vía AJAX...');
                stats = await this.getProjectStats(projectId);
                console.log('📈 Estadísticas recibidas:', stats);
            }
            
            // Verificar que los datos sean válidos
            if (!stats || typeof stats.name === 'undefined') {
                throw new Error('Datos de estadísticas inválidos');
            }
            
            // Mostrar modal de confirmación con estadísticas
            console.log('🎨 Creando modal con:', {
                projectName: stats.name,
                phaseCount: stats.phase_count,
                taskCount: stats.task_count,
                fileCount: stats.file_count
            });
            
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
            console.error('❌ Error getting project stats:', error);
            
            // Fallback: mostrar modal básico sin stats
            console.warn('⚠️ Usando modal de fallback');
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
        
        console.log('📡 Fetching project stats from:', url);
        console.log('📱 User agent:', navigator.userAgent.includes('Mobile') ? 'MOBILE' : 'DESKTOP');
        
        try {
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                },
                credentials: 'same-origin' // Asegurar que se envíen las cookies de sesión
            });

            console.log('📨 Response status:', response.status);
            console.log('📨 Response ok:', response.ok);
            console.log('📨 Response Content-Type:', response.headers.get('Content-Type'));

            if (!response.ok) {
                const errorText = await response.text();
                console.error('❌ Error response:', errorText);
                throw new Error(`Failed to fetch project stats: ${response.status}`);
            }

            const contentType = response.headers.get('Content-Type');
            if (!contentType || !contentType.includes('application/json')) {
                const htmlText = await response.text();
                console.error('❌ Received HTML instead of JSON:', htmlText.substring(0, 500));
                throw new Error('Server returned HTML instead of JSON. Check server logs.');
            }

            const data = await response.json();
            console.log('✅ Project stats received:', {
                name: data.name,
                phases: data.phase_count,
                tasks: data.task_count,
                files: data.file_count,
                rawData: data
            });
            
            // Validar que los datos tengan el formato esperado
            if (typeof data.name === 'undefined' || 
                typeof data.phase_count === 'undefined' ||
                typeof data.task_count === 'undefined' ||
                typeof data.file_count === 'undefined') {
                console.error('❌ Datos incompletos recibidos:', data);
                throw new Error('Incomplete data received from server');
            }
            
            return data;

        } catch (error) {
            console.error('❌ Error fetching project stats:', error);
            console.error('❌ Error stack:', error.stack);
            
            // Devolver stats vacías en caso de error
            const fallbackData = {
                name: 'el proyecto',
                phase_count: 0,
                task_count: 0,
                file_count: 0
            };
            console.warn('⚠️ Returning fallback data:', fallbackData);
            return fallbackData;
        }
    }

    async deleteProject(projectId, deleteUrl) {
        // Construct URL explicitly to ensure it's correct and has trailing slash
        // We ignore the passed deleteUrl to avoid issues with query params or missing slashes
        const finalUrl = `/projects/${projectId}/delete/`;
        console.log('🗑️ Attempting to delete project:', projectId, 'at URL:', finalUrl);

        try {
            const csrfToken = this.getCsrfToken();
            if (!csrfToken) {
                console.error('❌ CSRF token not found!');
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

            console.log('📨 Delete response status:', response.status);
            console.log('📨 Delete response URL:', response.url);

            // Check if we were redirected to the confirmation page (meaning it was treated as GET)
            if (response.url && response.url.includes('/delete/') && !response.url.includes('/login/')) {
                 console.error('❌ Redirected back to delete page, likely POST converted to GET');
                 this.showErrorMessage('Error: La solicitud de eliminación no se procesó correctamente.');
                 return;
            }

            if (response.ok) {
                console.log('✅ Project deleted successfully');
                this.showSuccessMessage('Proyecto eliminado correctamente');
                
                // Redirigir a la lista de proyectos después de un delay
                setTimeout(() => {
                    window.location.href = '/projects/';
                }, 1500);

            } else {
                console.error('❌ Delete failed with status:', response.status);
                const data = await response.json().catch(() => ({}));
                this.showErrorMessage(data.error || 'Error al eliminar el proyecto');
            }

        } catch (error) {
            console.error('❌ Error deleting project:', error);
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
