/**
 * SISTEMA DE NOTIFICACIONES MODERNO PARA ARC MANAGER
 * Proporciona una API unificada para mostrar notificaciones elegantes y profesionales
 */

class NotificationManager {
    constructor() {
        this.container = null;
        this.notifications = new Map();
        this.defaultDuration = 5000; // 5 segundos
        this.maxNotifications = 5;
        this.init();
    }

    /**
     * Inicializa el sistema de notificaciones
     */
    init() {
        this.createContainer();
        this.bindEvents();
        
        // Convertir mensajes de Django automáticamente
        this.convertDjangoMessages();
        
        // Hacer disponible globalmente
        window.notifications = this;
        window.showNotification = (message, type, options) => this.show(message, type, options);
    }

    /**
     * Crea el contenedor de notificaciones
     */
    createContainer() {
        // Remover contenedor existente si existe
        const existingContainer = document.getElementById('notifications-container');
        if (existingContainer) {
            existingContainer.remove();
        }

        this.container = document.createElement('div');
        this.container.id = 'notifications-container';
        this.container.className = 'notifications-container';
        document.body.appendChild(this.container);
    }

    /**
     * Vincula eventos globales
     */
    bindEvents() {
        // Pausar auto-dismiss cuando el mouse está sobre el contenedor
        this.container.addEventListener('mouseenter', () => {
            this.pauseAllTimers();
        });

        this.container.addEventListener('mouseleave', () => {
            this.resumeAllTimers();
        });

        // Manejar visibilidad de la página
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseAllTimers();
            } else {
                this.resumeAllTimers();
            }
        });
    }

    /**
     * Convierte mensajes de Django existentes a notificaciones modernas
     */
    convertDjangoMessages() {
        const messagesContainer = document.querySelector('.messages-container');
        if (!messagesContainer) return;

        const alerts = messagesContainer.querySelectorAll('.alert');
        alerts.forEach(alert => {
            const message = alert.textContent.replace('×', '').trim();
            let type = 'info';
            
            if (alert.classList.contains('alert-success')) type = 'success';
            else if (alert.classList.contains('alert-warning')) type = 'warning';
            else if (alert.classList.contains('alert-danger')) type = 'error';
            else if (alert.classList.contains('alert-info')) type = 'info';

            // Mostrar la notificación moderna
            this.show(message, type, { duration: 6000 });
        });

        // Ocultar el contenedor original
        messagesContainer.style.display = 'none';
    }

    /**
     * Oculta los mensajes Django sin convertirlos
     */
    hideDjangoMessages() {
        const messagesContainer = document.querySelector('.messages-container');
        if (messagesContainer) {
            messagesContainer.style.display = 'none';
        }
    }

    /**
     * Muestra una notificación
     * @param {string} message - Mensaje a mostrar
     * @param {string} type - Tipo: 'success', 'error', 'warning', 'info'
     * @param {Object} options - Opciones adicionales
     */
    show(message, type = 'info', options = {}) {
        // Prevenir duplicados - verificar si hay una notificación similar reciente
        if (this.isDuplicateMessage(message, type)) {
            return null;
        }

        const config = {
            duration: options.duration || this.defaultDuration,
            title: options.title || this.getDefaultTitle(type),
            persistent: options.persistent || false,
            onClick: options.onClick || null,
            showProgress: options.showProgress !== false,
            ...options
        };

        // Limitar número de notificaciones
        this.limitNotifications();

        // Crear notificación
        const notification = this.createNotification(message, type, config);
        const id = this.generateId();
        
        // Guardar referencia
        this.notifications.set(id, {
            element: notification,
            config: config,
            timer: null,
            startTime: Date.now(),
            message: message,
            type: type
        });

        // Agregar al DOM
        this.container.appendChild(notification);

        // Animar entrada
        requestAnimationFrame(() => {
            notification.classList.add('show');
        });

        // Configurar auto-dismiss si no es persistente
        if (!config.persistent && config.duration > 0) {
            this.setAutoRemove(id, config.duration);
        }

        return id;
    }

    /**
     * Crea el elemento de notificación
     */
    createNotification(message, type, config) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        const iconClass = this.getIconClass(type);
        
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-icon">
                    <i class="${iconClass}"></i>
                </div>
                <div class="notification-body">
                    ${config.title ? `<div class="notification-title">${config.title}</div>` : ''}
                    <div class="notification-message">${message}</div>
                </div>
                <button class="notification-close" aria-label="Cerrar notificación">
                    ×
                </button>
            </div>
            ${config.showProgress ? '<div class="notification-progress"><div class="notification-progress-bar"></div></div>' : ''}
        `;

        // Agregar event listeners
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.remove(notification);
        });

        if (config.onClick) {
            notification.style.cursor = 'pointer';
            notification.addEventListener('click', config.onClick);
        }

        return notification;
    }

    /**
     * Configura la eliminación automática
     */
    setAutoRemove(id, duration) {
        const notificationData = this.notifications.get(id);
        if (!notificationData) return;

        const progressBar = notificationData.element.querySelector('.notification-progress-bar');
        
        if (progressBar) {
            progressBar.style.animation = `progressBar ${duration}ms linear`;
        }

        notificationData.timer = setTimeout(() => {
            this.remove(notificationData.element);
        }, duration);
    }

    /**
     * Remueve una notificación
     */
    remove(notification) {
        if (typeof notification === 'string') {
            // Si es un ID
            const notificationData = this.notifications.get(notification);
            if (notificationData) {
                notification = notificationData.element;
            } else {
                return;
            }
        }

        // Encontrar ID por elemento
        let notificationId = null;
        for (let [id, data] of this.notifications) {
            if (data.element === notification) {
                notificationId = id;
                break;
            }
        }

        if (notificationId) {
            const notificationData = this.notifications.get(notificationId);
            
            // Limpiar timer
            if (notificationData.timer) {
                clearTimeout(notificationData.timer);
            }

            // Animar salida
            notification.classList.add('hide');
            
            // Remover del DOM después de la animación
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
                this.notifications.delete(notificationId);
            }, 400);
        }
    }

    /**
     * Pausa todos los timers activos
     */
    pauseAllTimers() {
        this.notifications.forEach((data, id) => {
            if (data.timer && !data.config.persistent) {
                clearTimeout(data.timer);
                data.remainingTime = data.config.duration - (Date.now() - data.startTime);
                
                const progressBar = data.element.querySelector('.notification-progress-bar');
                if (progressBar) {
                    progressBar.style.animationPlayState = 'paused';
                }
            }
        });
    }

    /**
     * Reanuda todos los timers pausados
     */
    resumeAllTimers() {
        this.notifications.forEach((data, id) => {
            if (data.remainingTime && data.remainingTime > 0) {
                const progressBar = data.element.querySelector('.notification-progress-bar');
                if (progressBar) {
                    progressBar.style.animationPlayState = 'running';
                }
                
                data.timer = setTimeout(() => {
                    this.remove(data.element);
                }, data.remainingTime);
                
                data.startTime = Date.now();
                delete data.remainingTime;
            }
        });
    }

    /**
     * Verifica si el mensaje es un duplicado reciente
     */
    isDuplicateMessage(message, type) {
        const currentTime = Date.now();
        const duplicateWindow = 3000; // 3 segundos para considerar duplicado
        
        for (let [id, data] of this.notifications) {
            // Verificar si hay una notificación similar en los últimos 3 segundos
            if (data.message && data.type === type && 
                (currentTime - data.startTime) < duplicateWindow) {
                
                // Normalizar mensajes para comparación (remover puntuación y espacios extra)
                const normalizeMessage = (msg) => {
                    return msg.toLowerCase()
                              .replace(/[^\w\s]/g, '')
                              .replace(/\s+/g, ' ')
                              .trim();
                };
                
                const currentNormalized = normalizeMessage(message);
                const existingNormalized = normalizeMessage(data.message);
                
                // Si los mensajes son muy similares (>80% coincidencia)
                if (this.calculateSimilarity(currentNormalized, existingNormalized) > 0.8) {
                    return true;
                }
            }
        }
        
        return false;
    }
    
    /**
     * Calcula la similitud entre dos strings usando algoritmo simple
     */
    calculateSimilarity(str1, str2) {
        if (str1 === str2) return 1.0;
        
        const longer = str1.length > str2.length ? str1 : str2;
        const shorter = str1.length > str2.length ? str2 : str1;
        
        if (longer.length === 0) return 1.0;
        
        const distance = this.levenshteinDistance(longer, shorter);
        return (longer.length - distance) / longer.length;
    }
    
    /**
     * Calcula la distancia de Levenshtein entre dos strings
     */
    levenshteinDistance(str1, str2) {
        const matrix = [];
        
        for (let i = 0; i <= str2.length; i++) {
            matrix[i] = [i];
        }
        
        for (let j = 0; j <= str1.length; j++) {
            matrix[0][j] = j;
        }
        
        for (let i = 1; i <= str2.length; i++) {
            for (let j = 1; j <= str1.length; j++) {
                if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
                    matrix[i][j] = matrix[i - 1][j - 1];
                } else {
                    matrix[i][j] = Math.min(
                        matrix[i - 1][j - 1] + 1,
                        matrix[i][j - 1] + 1,
                        matrix[i - 1][j] + 1
                    );
                }
            }
        }
        
        return matrix[str2.length][str1.length];
    }

    /**
     * Limita el número de notificaciones visibles
     */
    limitNotifications() {
        if (this.notifications.size >= this.maxNotifications) {
            const oldestId = this.notifications.keys().next().value;
            this.remove(oldestId);
        }
    }

    /**
     * Genera un ID único para la notificación
     */
    generateId() {
        return 'notification_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * Obtiene el ícono apropiado para el tipo
     */
    getIconClass(type) {
        const icons = {
            success: 'fas fa-check',
            error: 'fas fa-times',
            warning: 'fas fa-exclamation',
            info: 'fas fa-info'
        };
        return icons[type] || icons.info;
    }

    /**
     * Obtiene el título por defecto para el tipo
     */
    getDefaultTitle(type) {
        const titles = {
            success: 'Éxito',
            error: 'Error',
            warning: 'Advertencia',
            info: 'Información'
        };
        return titles[type] || titles.info;
    }

    /**
     * Limpia todas las notificaciones
     */
    clear() {
        this.notifications.forEach((data, id) => {
            this.remove(id);
        });
    }

    /**
     * Métodos de conveniencia
     */
    success(message, options = {}) {
        return this.show(message, 'success', options);
    }

    error(message, options = {}) {
        return this.show(message, 'error', { duration: 7000, ...options });
    }

    warning(message, options = {}) {
        return this.show(message, 'warning', { duration: 6000, ...options });
    }

    info(message, options = {}) {
        return this.show(message, 'info', options);
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new NotificationManager();
});

// Funciones globales para compatibilidad con código existente
window.showGlobalNotification = function(message, type = 'info') {
    if (window.notifications) {
        window.notifications.show(message, type);
    }
};

window.showSuccessMessage = function(message) {
    if (window.notifications) {
        window.notifications.success(message);
    }
};

window.showErrorMessage = function(message) {
    if (window.notifications) {
        window.notifications.error(message);
    }
};

window.showWarningMessage = function(message) {
    if (window.notifications) {
        window.notifications.warning(message);
    }
};

window.showInfoMessage = function(message) {
    if (window.notifications) {
        window.notifications.info(message);
    }
};

// Exportar para módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NotificationManager;
}
