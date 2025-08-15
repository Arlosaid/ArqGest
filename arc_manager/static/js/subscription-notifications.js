/**
 * SISTEMA DE NOTIFICACIONES AUTOMÁTICAS DE SUSCRIPCIÓN
 * Muestra advertencias sobre planes, límites y vencimientos
 */

class SubscriptionNotifications {
    constructor() {
        this.storageKey = 'arc_subscription_notifications';
        this.init();
    }

    init() {
        // Esperar a que el sistema de notificaciones esté disponible
        if (window.notifications) {
            this.checkSubscriptionStatus();
        } else {
            // Reintentar después de un momento
            setTimeout(() => {
                if (window.notifications) {
                    this.checkSubscriptionStatus();
                }
            }, 1000);
        }
    }

    /**
     * Verifica el estado de la suscripción y muestra notificaciones apropiadas
     */
    checkSubscriptionStatus() {
        // Obtener información de suscripción del DOM o hacer petición AJAX
        this.getSubscriptionInfo().then(info => {
            if (!info) return;

            // Verificar diferentes condiciones con sistema inteligente
            this.checkExpirationWarning(info);
            this.checkUserLimits(info);
            this.checkProjectLimits(info);
            this.checkGracePeriod(info);
        }).catch(error => {
            console.error('Error obteniendo información de suscripción:', error);
        });
    }

    /**
     * Verifica si ya se mostró una notificación específica hoy
     */
    shouldShowNotification(type, key) {
        const today = new Date().toDateString();
        const stored = this.getStoredNotifications();
        
        // Para notificaciones críticas (período de gracia), siempre mostrar
        if (type === 'grace_period') {
            return true;
        }
        
        // Para notificaciones de expiración muy próxima (1-2 días), mostrar más frecuentemente
        if (type === 'expiration_critical' && key <= 2) {
            const lastShown = stored[`${type}_${key}`];
            if (!lastShown) return true;
            
            // Mostrar cada 4 horas para casos críticos
            const hoursSinceShown = (Date.now() - lastShown) / (1000 * 60 * 60);
            return hoursSinceShown >= 4;
        }
        
        // Para otras notificaciones, mostrar solo una vez al día
        const notificationKey = `${type}_${key}`;
        const lastShown = stored[notificationKey];
        
        if (!lastShown) return true;
        
        const lastShownDate = new Date(lastShown).toDateString();
        return lastShownDate !== today;
    }

    /**
     * Marca una notificación como mostrada
     */
    markNotificationShown(type, key) {
        const stored = this.getStoredNotifications();
        const notificationKey = `${type}_${key}`;
        stored[notificationKey] = Date.now();
        
        // Limpiar notificaciones antiguas (más de 7 días)
        const weekAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
        Object.keys(stored).forEach(k => {
            if (stored[k] < weekAgo) {
                delete stored[k];
            }
        });
        
        localStorage.setItem(this.storageKey, JSON.stringify(stored));
    }

    /**
     * Obtiene las notificaciones almacenadas
     */
    getStoredNotifications() {
        try {
            const stored = localStorage.getItem(this.storageKey);
            return stored ? JSON.parse(stored) : {};
        } catch (e) {
            console.warn('Error leyendo notificaciones almacenadas:', e);
            return {};
        }
    }

    /**
     * Obtiene información de suscripción del servidor
     */
    async getSubscriptionInfo() {
        try {
            // Primero intentar obtener del DOM (más rápido)
            const domInfo = this.getSubscriptionInfoFromDOM();
            if (domInfo) {
                return domInfo;
            }

            // Si no está en DOM, hacer petición AJAX
            const response = await fetch('/api/subscription-info/', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Error fetching subscription info:', error);
        }
        return null;
    }

    /**
     * Intenta obtener información de suscripción desde el DOM
     */
    getSubscriptionInfoFromDOM() {
        // Buscar información en elementos del DOM
        const subscriptionData = document.querySelector('[data-subscription-info]');
        if (subscriptionData) {
            try {
                return JSON.parse(subscriptionData.dataset.subscriptionInfo);
            } catch (e) {
                console.error('Error parsing subscription data from DOM:', e);
            }
        }

        // Buscar información en variables globales
        if (window.subscriptionInfo) {
            return window.subscriptionInfo;
        }

        // Extraer información de elementos visibles
        const daysElement = document.querySelector('.days-number');
        const planElement = document.querySelector('[data-plan-name]');
        
        if (daysElement && planElement) {
            return {
                days_remaining: parseInt(daysElement.textContent) || 0,
                plan_name: planElement.dataset.planName || '',
                is_trial: planElement.dataset.planName?.includes('trial') || false,
                expires_soon: parseInt(daysElement.textContent) <= 7,
                needs_attention: document.querySelector('.expired') !== null
            };
        }

        return null;
    }

    /**
     * Verifica y muestra advertencia de expiración próxima
     */
    checkExpirationWarning(info) {
        if (info.expires_soon && info.days_remaining > 0) {
            const days = info.days_remaining;
            const notificationType = days <= 2 ? 'expiration_critical' : 'expiration_warning';
            
            // Verificar si ya se mostró esta notificación
            if (!this.shouldShowNotification(notificationType, days)) {
                return;
            }
            
            const message = info.is_trial 
                ? `Tu prueba gratuita expira en ${days} día${days !== 1 ? 's' : ''}. ¡Actualiza ahora para no perder acceso!`
                : `Tu suscripción expira en ${days} día${days !== 1 ? 's' : ''}. Renueva para continuar sin interrupciones.`;

            window.notifications.warning(message, {
                title: 'Renovación Necesaria',
                duration: days <= 2 ? 10000 : 8000, // Más tiempo para casos críticos
                onClick: () => {
                    window.location.href = '/plans/request-upgrade/';
                }
            });
            
            // Marcar como mostrada
            this.markNotificationShown(notificationType, days);
        }
    }

    /**
     * Verifica límites de usuarios
     */
    checkUserLimits(info) {
        if (info.user_usage && info.user_limit) {
            const percentage = (info.user_usage / info.user_limit) * 100;
            
            if (percentage >= 90) {
                const remaining = info.user_limit - info.user_usage;
                const limitKey = `${info.user_usage}_${info.user_limit}`;
                
                // Verificar si ya se mostró esta notificación
                if (!this.shouldShowNotification('user_limit', limitKey)) {
                    return;
                }
                
                const message = remaining > 0 
                    ? `Solo puedes agregar ${remaining} usuario${remaining !== 1 ? 's' : ''} más. Considera actualizar tu plan.`
                    : 'Has alcanzado el límite de usuarios de tu plan. Actualiza para agregar más usuarios.';

                window.notifications.warning(message, {
                    title: 'Límite de Usuarios',
                    duration: 7000,
                    onClick: () => {
                        window.location.href = '/plans/request-upgrade/';
                    }
                });
                
                // Marcar como mostrada
                this.markNotificationShown('user_limit', limitKey);
            }
        }
    }

    /**
     * Verifica límites de proyectos
     */
    checkProjectLimits(info) {
        if (info.project_usage && info.project_limit) {
            const percentage = (info.project_usage / info.project_limit) * 100;
            
            if (percentage >= 90) {
                const remaining = info.project_limit - info.project_usage;
                const limitKey = `${info.project_usage}_${info.project_limit}`;
                
                // Verificar si ya se mostró esta notificación
                if (!this.shouldShowNotification('project_limit', limitKey)) {
                    return;
                }
                
                const message = remaining > 0 
                    ? `Solo puedes crear ${remaining} proyecto${remaining !== 1 ? 's' : ''} más. Considera actualizar tu plan.`
                    : 'Has alcanzado el límite de proyectos de tu plan. Actualiza para crear más proyectos.';

                window.notifications.warning(message, {
                    title: 'Límite de Proyectos',
                    duration: 7000,
                    onClick: () => {
                        window.location.href = '/plans/request-upgrade/';
                    }
                });
                
                // Marcar como mostrada
                this.markNotificationShown('project_limit', limitKey);
            }
        }
    }

    /**
     * Verifica si está en período de gracia
     */
    checkGracePeriod(info) {
        if (info.is_in_grace) {
            // Las notificaciones de período de gracia siempre se muestran (críticas)
            window.notifications.error('Tu suscripción ha expirado pero tienes acceso limitado. Renueva inmediatamente para evitar la suspensión.', {
                title: 'Suscripción Expirada',
                persistent: true,
                onClick: () => {
                    window.location.href = '/plans/request-upgrade/';
                }
            });
        }
    }

    /**
     * Obtiene el token CSRF
     */
    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    /**
     * Método público para forzar verificación
     */
    refresh() {
        this.checkSubscriptionStatus();
    }

    /**
     * Limpia el historial de notificaciones mostradas (para testing)
     */
    clearHistory() {
        localStorage.removeItem(this.storageKey);
        console.log('Historial de notificaciones limpiado');
    }

    /**
     * Muestra el estado actual del historial (para debugging)
     */
    showHistory() {
        const stored = this.getStoredNotifications();
        console.log('Historial de notificaciones:', stored);
        
        // Mostrar de forma legible
        Object.keys(stored).forEach(key => {
            const timestamp = new Date(stored[key]);
            console.log(`${key}: ${timestamp.toLocaleString()}`);
        });
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.subscriptionNotifications = new SubscriptionNotifications();
});

// Funciones globales para gestionar notificaciones
window.refreshSubscriptionNotifications = function() {
    if (window.subscriptionNotifications) {
        window.subscriptionNotifications.refresh();
    }
};

window.clearNotificationHistory = function() {
    if (window.subscriptionNotifications) {
        window.subscriptionNotifications.clearHistory();
    }
};

window.showNotificationHistory = function() {
    if (window.subscriptionNotifications) {
        window.subscriptionNotifications.showHistory();
    }
};

// Auto-refresh cada 5 minutos para captar cambios
setInterval(() => {
    if (window.subscriptionNotifications) {
        window.subscriptionNotifications.refresh();
    }
}, 5 * 60 * 1000); // 5 minutos

// Exportar para módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SubscriptionNotifications;
}
