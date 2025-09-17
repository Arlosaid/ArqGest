/**
 * Manejador global de errores HTMX para toda la aplicación
 * Captura errores HTTP y los muestra como notificaciones en lugar de páginas de error
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // Manejador global de errores HTMX
    document.body.addEventListener('htmx:responseError', function(evt) {
        const target = evt.target;
        let errorMessage = 'Error en la operación';
        
        try {
            // Intentar parsear la respuesta JSON del error
            const response = evt.detail.xhr.response;
            if (response) {
                const errorData = JSON.parse(response);
                if (errorData.error) {
                    errorMessage = errorData.error;
                } else if (errorData.message) {
                    errorMessage = errorData.message;
                }
            }
        } catch (e) {
            // Si no se puede parsear JSON, usar el status text o status
            if (evt.detail.xhr.statusText) {
                errorMessage = evt.detail.xhr.statusText;
            } else {
                const status = evt.detail.xhr.status;
                switch (status) {
                    case 400:
                        errorMessage = 'Solicitud incorrecta';
                        break;
                    case 401:
                        errorMessage = 'No autorizado';
                        break;
                    case 403:
                        errorMessage = 'Acceso prohibido';
                        break;
                    case 404:
                        errorMessage = 'Recurso no encontrado';
                        break;
                    case 413:
                        errorMessage = 'Archivo demasiado grande';
                        break;
                    case 500:
                        errorMessage = 'Error interno del servidor';
                        break;
                    default:
                        errorMessage = `Error ${status}`;
                }
            }
        }
        
        // Mostrar notificación de error
        showGlobalNotification(errorMessage, 'error');
        
        // Resetear formularios si es apropiado
        if (target.tagName === 'FORM') {
            // No resetear formularios de eliminación o que no sean de entrada de datos
            if (!target.action.includes('delete') && !target.action.includes('update_status')) {
                target.reset();
            }
        }
    });

    // Función global para mostrar notificaciones usando el sistema personalizado
    window.showGlobalNotification = function(message, type = 'info') {
        // Usar el sistema de notificaciones personalizado si está disponible
        if (window.notifications) {
            window.notifications.show(message, type);
        } else {
            // Fallback: crear notificación simple si el sistema no está disponible
            console.warn('Sistema de notificaciones personalizado no disponible, usando fallback');
            
            // Crear elemento de notificación simple
            const notification = document.createElement('div');
            notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
            notification.style.cssText = `
                top: 20px;
                right: 20px;
                z-index: 9999;
                min-width: 300px;
                max-width: 500px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            `;
            
            notification.innerHTML = `
                <div class="d-flex align-items-center">
                    <i class="fas fa-${type === 'error' ? 'exclamation-triangle' : type === 'success' ? 'check-circle' : 'info-circle'} me-2"></i>
                    <span>${message}</span>
                    <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            `;
            
            document.body.appendChild(notification);
            
            // Auto-ocultar después de 5 segundos
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 5000);
            
            notification.addEventListener('click', function(e) {
                if (e.target.classList.contains('btn-close')) {
                    notification.remove();
                }
            });
        }
    };

    // Función para mostrar notificaciones en contenedores específicos
    window.showNotificationInContainer = function(message, type = 'info', containerId = 'message-container') {
        const container = document.getElementById(containerId);
        if (!container) {
            // Fallback a notificación global
            window.showGlobalNotification(message, type);
            return;
        }
        
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        container.innerHTML = '';
        container.appendChild(notification);
        
        // Auto-ocultar después de 5 segundos
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    };

    // Log de inicialización (solo en desarrollo)
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        console.log('HTMX Error Handler inicializado');
    }
});
