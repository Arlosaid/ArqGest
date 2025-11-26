/**
 * Sistema de eliminación de pagos con modal de confirmación
 * Mejora la UX reemplazando window.confirm() por modales visuales
 */

class PaymentDeleteManager {
    constructor() {
        this.init();
    }

    init() {
        // Configurar event delegation para botones de eliminar pagos
        document.addEventListener('click', (e) => {
            // Para enlaces con clase específica
            const deleteLink = e.target.closest('.payment-delete-link, a[href*="payment-delete"]');
            if (deleteLink && deleteLink.hasAttribute('data-payment-id')) {
                e.preventDefault();
                this.handleDeleteClick(deleteLink);
            }
            
            // Para botones que triggean el form
            const deleteBtn = e.target.closest('.delete-payment-btn');
            if (deleteBtn) {
                e.preventDefault();
                this.handleDeleteButtonClick(deleteBtn);
            }
        });
        
        console.log('✅ PaymentDeleteManager inicializado');
    }

    /**
     * Manejar click en enlace de eliminar
     */
    handleDeleteClick(link) {
        const paymentId = link.dataset.paymentId;
        const amount = link.dataset.paymentAmount || 'Monto no especificado';
        const date = link.dataset.paymentDate || '';
        const description = link.dataset.paymentDescription || `Pago de ${amount}`;
        const deleteUrl = link.href;
        
        this.showDeleteModal({
            paymentId,
            amount,
            date,
            description,
            deleteUrl
        });
    }

    /**
     * Manejar click en botón que dispara un form
     */
    handleDeleteButtonClick(btn) {
        const formId = btn.dataset.formId;
        const form = document.getElementById(formId);
        
        if (!form) {
            console.error('Form no encontrado:', formId);
            return;
        }
        
        const paymentId = btn.dataset.paymentId;
        const amount = btn.dataset.paymentAmount || 'Monto no especificado';
        const date = btn.dataset.paymentDate || '';
        const description = btn.dataset.paymentDescription || `Pago de ${amount}`;
        
        this.showDeleteModal({
            paymentId,
            amount,
            date,
            description,
            form
        });
    }

    /**
     * Mostrar modal de confirmación
     */
    showDeleteModal(paymentInfo) {
        const modal = ConfirmationModals.deletePayment({
            description: paymentInfo.description,
            amount: paymentInfo.amount,
            date: paymentInfo.date
        });

        modal.config.onConfirm = async () => {
            if (paymentInfo.form) {
                // Enviar form existente
                paymentInfo.form.submit();
            } else if (paymentInfo.deleteUrl) {
                // Hacer petición POST al URL de eliminación
                await this.deletePayment(paymentInfo.paymentId, paymentInfo.deleteUrl);
            }
        };

        modal.show();
    }

    /**
     * Eliminar pago vía AJAX
     */
    async deletePayment(paymentId, deleteUrl) {
        try {
            const response = await fetch(deleteUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            });

            if (response.ok) {
                // Redirigir a la página de éxito
                window.location.reload();
            } else {
                throw new Error('Error al eliminar el pago');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showNotification('Error al eliminar el pago', 'error');
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

    /**
     * Mostrar notificación
     */
    showNotification(message, type = 'info') {
        if (window.notifications) {
            window.notifications[type](message);
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }
}

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (!window.paymentDeleteManager) {
            window.paymentDeleteManager = new PaymentDeleteManager();
        }
    });
} else {
    if (!window.paymentDeleteManager) {
        window.paymentDeleteManager = new PaymentDeleteManager();
    }
}
