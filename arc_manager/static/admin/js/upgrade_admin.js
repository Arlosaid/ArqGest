// JavaScript para hacer el admin de upgrades más amigable

document.addEventListener('DOMContentLoaded', function() {
    
    // Función para mostrar alertas amigables
    function showFriendlyAlert(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 5px;
            color: white;
            font-weight: bold;
            z-index: 9999;
            max-width: 400px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        `;
        
        switch(type) {
            case 'success':
                alertDiv.style.background = '#28a745';
                break;
            case 'warning':
                alertDiv.style.background = '#ffc107';
                alertDiv.style.color = '#333';
                break;
            case 'error':
                alertDiv.style.background = '#dc3545';
                break;
            default:
                alertDiv.style.background = '#17a2b8';
        }
        
        alertDiv.textContent = message;
        document.body.appendChild(alertDiv);
        
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
    
    // Detectar cambios en el campo de estado
    const statusField = document.querySelector('#id_status');
    if (statusField) {
        let originalStatus = statusField.value;
        
        statusField.addEventListener('change', function() {
            const newStatus = this.value;
            const statusTexts = {
                'pending': 'Pendiente de Aprobación',
                'approved': 'Aprobada - Pendiente de Pago',
                'payment_pending': 'Pago Reportado - En Verificación',
                'completed': 'Completada',
                'rejected': 'Rechazada',
                'cancelled': 'Cancelada'
            };
            
            if (newStatus !== originalStatus) {
                let message = '';
                let confirmMessage = '';
                
                if (originalStatus === 'pending' && newStatus === 'approved') {
                    message = '✅ Al guardar se enviará automáticamente un email al cliente con las instrucciones de pago bancario.';
                    confirmMessage = '¿Confirmas que quieres APROBAR esta solicitud? Se enviará un email automáticamente.';
                } else if (originalStatus === 'payment_pending' && newStatus === 'completed') {
                    message = '🎉 Al guardar se actualizará automáticamente el plan de la organización y se enviará email de confirmación.';
                    confirmMessage = '¿Confirmas que quieres COMPLETAR este upgrade? El plan se activará inmediatamente.';
                } else if (originalStatus === 'pending' && newStatus === 'rejected') {
                    message = 'Al guardar se enviará un email de rechazo al cliente.';
                    confirmMessage = '¿Confirmas que quieres RECHAZAR esta solicitud?';
                } else {
                    message = `🔄 Cambiarás el estado a: ${statusTexts[newStatus]}`;
                }
                
                showFriendlyAlert(message, 'warning');
                
                if (confirmMessage) {
                    if (!confirm(confirmMessage)) {
                        statusField.value = originalStatus;
                        return;
                    }
                }
            }
        });
    }
    
    // Mejorar el botón de guardar
    const saveButton = document.querySelector('input[type="submit"][name="_save"]');
    if (saveButton) {
        const originalText = saveButton.value;
        
        saveButton.addEventListener('click', function(e) {
            const statusField = document.querySelector('#id_status');
            if (statusField) {
                const status = statusField.value;
                
                if (status === 'approved') {
                    saveButton.value = '📧 Guardar y Enviar Email';
                    saveButton.style.background = '#28a745';
                } else if (status === 'completed') {
                    saveButton.value = '🎉 Guardar y Activar Plan';
                    saveButton.style.background = '#17a2b8';
                } else {
                    saveButton.value = '💾 Guardar Cambios';
                }
            }
        });
    }
    
    // Agregar tooltips a los botones de acción
    const editButtons = document.querySelectorAll('.field-edit_button a');
    editButtons.forEach(button => {
        button.title = 'Haz clic aquí para editar esta solicitud de upgrade';
    });
    
    // Resaltar el campo de estado al cargar la página
    if (statusField) {
        setTimeout(() => {
            statusField.focus();
            statusField.style.animation = 'pulse 2s infinite';
        }, 500);
    }
    
    // Agregar CSS de animación
    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(65, 118, 144, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(65, 118, 144, 0); }
            100% { box-shadow: 0 0 0 0 rgba(65, 118, 144, 0); }
        }
    `;
    document.head.appendChild(style);
    
    // Mostrar mensaje de bienvenida
    showFriendlyAlert('💡 Para cambiar el estado, modifica el dropdown y guarda los cambios', 'info');
}); 