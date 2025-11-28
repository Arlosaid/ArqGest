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
        const formId = btn.getAttribute('data-form-id');
        const form = document.getElementById(formId);
        
        if (!form) {
            // Intentar encontrar el form hermano si el ID falla
            const siblingForm = btn.nextElementSibling;
            if (siblingForm && siblingForm.tagName === 'FORM') {
                this.processDelete(btn, siblingForm);
                return;
            }
            alert('Error: No se encontró el formulario de eliminación.');
            return;
        }
        
        this.processDelete(btn, form);
    }

    processDelete(btn, form) {
        const paymentId = btn.getAttribute('data-payment-id');
        const amount = btn.getAttribute('data-payment-amount') || 'Monto no especificado';
        const date = btn.getAttribute('data-payment-date') || '';
        const description = btn.getAttribute('data-payment-description') || `Pago de ${amount}`;

        // Verificar si ConfirmationModals está disponible
        if (typeof ConfirmationModals === 'undefined') {
            if (confirm(`¿Estás seguro de que deseas eliminar este pago?\n\n${description}\n${amount}`)) {
                form.submit();
            }
            return;
        }

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
        // Ensure trailing slash to avoid 301 redirects
        if (!deleteUrl.endsWith('/')) {
            deleteUrl += '/';
        }

        try {
            const response = await fetch(deleteUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            });

            // Check for redirects
            if (response.redirected && response.url.includes('/login/')) {
                window.location.href = response.url;
                return;
            }

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
        // 1. Try to get from meta tag (most reliable for SPA/AJAX)
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        if (metaToken && metaToken.content) {
            return metaToken.content;
        }
        
        // 2. Try to get from hidden input (standard Django form)
        const inputToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (inputToken && inputToken.value) {
            return inputToken.value;
        }

        // 3. Fallback to cookie (might fail with HttpOnly)
        const value = `; ${document.cookie}`;
        const parts = value.split(`; csrftoken=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        
        return '';
    }

    /**
     * Mostrar notificación
     */
    showNotification(message, type = 'info') {
        if (window.notifications) {
            if (type === 'success') {
                window.notifications.success(message);
            } else if (type === 'error') {
                window.notifications.error(message);
            } else {
                window.notifications.show(message, type);
            }
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
