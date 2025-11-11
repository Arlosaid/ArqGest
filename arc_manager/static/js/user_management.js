// Gestión de Usuarios - JavaScript Moderno con UX Mejorado
class UserManagement {
    constructor() {
        // Solo inicializar si estamos en la página de gestión de usuarios
        if (!document.querySelector('.user-management-page')) {
            return;
        }
        
        this.searchInput = document.querySelector('.table-search-input');
        this.checkboxes = document.querySelectorAll('.checkbox');
        this.actionButtons = document.querySelectorAll('.action-btn');
        this.paginationButtons = document.querySelectorAll('.pagination-btn, .pagination-number');
        this.tooltipContainer = document.getElementById('tooltip-container');
        this.currentTooltip = null;
        this.tooltipTimeout = null;
        
        // Elementos de formulario
        this.userForm = document.getElementById('userForm');
        this.saveButton = document.getElementById('saveButton');
        this.loadingSpinner = document.getElementById('loadingSpinner');
        this.saveButtonText = document.getElementById('saveButtonText');
        this.successMessage = document.getElementById('successMessage');
        
        // Elementos de entrada para validación en tiempo real
        this.formInputs = document.querySelectorAll('.modern-input, .modern-select');
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupSearch();
        this.setupCheckboxes();
        this.setupTooltips();
        this.setupFormValidation();
        this.setupFormSubmission();
        // this.animateOnLoad(); // deshabilitado
        this.createTooltipContainer();
    }

    createTooltipContainer() {
        if (!this.tooltipContainer) {
            this.tooltipContainer = document.createElement('div');
            this.tooltipContainer.id = 'tooltip-container';
            document.body.appendChild(this.tooltipContainer);
        }
    }

    setupEventListeners() {
        // Búsqueda del servidor - enviar formulario automáticamente después de un delay
        if (this.searchInput) {
            this.searchInput.addEventListener('input', this.debounce(this.handleServerSearch.bind(this), 500));
        }

        // Botones de acción
        this.actionButtons.forEach(button => {
            button.addEventListener('click', this.handleActionClick.bind(this));
        });

        // Paginación
        this.paginationButtons.forEach(button => {
            button.addEventListener('click', this.handlePaginationClick.bind(this));
        });

        // Checkbox principal
        const mainCheckbox = document.querySelector('thead .checkbox');
        if (mainCheckbox) {
            mainCheckbox.addEventListener('change', this.handleSelectAll.bind(this));
        }

        // Event listeners globales para tooltips
        document.addEventListener('scroll', () => {
            this.hideTooltip();
        });

        window.addEventListener('resize', () => {
            this.hideTooltip();
        });
    }

    setupSearch() {
        // Animación del icono de búsqueda deshabilitada
        if (this.searchInput) {
            // listeners removidos para evitar animaciones
        }
    }

    setupCheckboxes() {
        // Gestión de checkboxes individuales
        const bodyCheckboxes = document.querySelectorAll('tbody .checkbox');
        bodyCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', this.updateMainCheckbox.bind(this));
        });
    }

    setupTooltips() {
        // Tooltips mejorados para botones de acción
        this.actionButtons.forEach(button => {
            const tooltipText = button.getAttribute('data-tooltip');
            if (tooltipText) {
                button.addEventListener('mouseenter', (e) => {
                    this.showTooltip(e.target, tooltipText);
                });
                
                button.addEventListener('mouseleave', () => {
                    this.hideTooltip();
                });

                // Ocultar tooltip al hacer click
                button.addEventListener('click', () => {
                    this.hideTooltip();
                });

                // Ocultar tooltip si el elemento pierde el focus
                button.addEventListener('blur', () => {
                    this.hideTooltip();
                });
            }
        });
    }

    animateOnLoad() {
        // DESHABILITADO: animaciones de carga
        /*
        // Usar la clase base para animaciones
        BaseAnimation.animateElements('.stat-card-mini, .table-container, .info-card-sidebar', {
            stagger: 30,
            distance: 8
        });

        // Animar filas de la tabla
        const tableRows = document.querySelectorAll('.modern-table tbody tr');
        tableRows.forEach(row => {
            BaseAnimation.animateTableRow(row);
        });

        // Animar botones de acción
        const actionButtons = document.querySelectorAll('.action-btn');
        actionButtons.forEach(button => {
            BaseAnimation.animateButton(button);
        });
        */
    }

    handleServerSearch(event) {
        const searchTerm = event.target.value.trim();
        const form = event.target.closest('form');
        
        if (!form) {
            console.log('No se encontró formulario de búsqueda');
            return;
        }

        console.log('Enviando búsqueda de usuarios al servidor:', searchTerm);
        
        // Mostrar indicador de carga
        this.showSearchLoading();
        
        // Enviar formulario automáticamente
        form.submit();
    }

    showSearchLoading() {
        const searchInput = this.searchInput;
        const searchIcon = document.querySelector('.table-search-icon');
        
        if (searchInput) {
            searchInput.disabled = true;
        }
        
        if (searchIcon) {
            searchIcon.className = 'fas fa-spinner fa-spin table-search-icon';
        }
    }

    handleActionClick(event) {
        const button = event.currentTarget;
        const action = button.classList.contains('view') ? 'view' : 
                      button.classList.contains('edit') ? 'edit' : 'delete';
        
        // Ocultar tooltip inmediatamente
        this.hideTooltip();

        // Efecto visual deshabilitado

        // No manejar aquí los botones con onclick específico
        if (button.hasAttribute('onclick')) {
            return; // Dejar que el onclick maneje la acción
        }

        const row = button.closest('tr');
        const userName = row ? row.querySelector('.user-name').textContent : '';

        switch (action) {
            case 'view':
                this.showUserDetails(userName);
                break;
            case 'edit':
                this.editUser(userName);
                break;
            case 'delete':
                // Esta ruta ya no se usa porque los botones tienen onclick
                this.confirmDeleteUser(userName);
                break;
        }
    }

    handlePaginationClick(event) {
        const button = event.currentTarget;
        
        if (button.classList.contains('disabled')) return;

        // Remover clase active de todos los números
        document.querySelectorAll('.pagination-number').forEach(btn => {
            btn.classList.remove('active');
        });

        // Agregar clase active al botón clickeado si es un número
        if (button.classList.contains('pagination-number')) {
            button.classList.add('active');
        }

        // Si el elemento tiene href, dejamos que el navegador navegue normalmente
        const href = button.getAttribute('href');
        if (href) return;

        // Simular carga solo si no hay navegación
        this.showLoading();
        setTimeout(() => {
            this.hideLoading();
        }, 500);
    }

    handleSelectAll(event) {
        const isChecked = event.target.checked;
        const bodyCheckboxes = document.querySelectorAll('tbody .checkbox');
        
        bodyCheckboxes.forEach(checkbox => {
            checkbox.checked = isChecked;
            this.animateCheckbox(checkbox);
        });

        this.updateSelectedCount();
    }

    updateMainCheckbox() {
        const bodyCheckboxes = document.querySelectorAll('tbody .checkbox');
        const checkedBoxes = document.querySelectorAll('tbody .checkbox:checked');
        const mainCheckbox = document.querySelector('thead .checkbox');
        
        if (mainCheckbox) {
            mainCheckbox.checked = bodyCheckboxes.length === checkedBoxes.length;
            mainCheckbox.indeterminate = checkedBoxes.length > 0 && checkedBoxes.length < bodyCheckboxes.length;
        }

        this.updateSelectedCount();
    }

    updateSelectedCount() {
        const checkedBoxes = document.querySelectorAll('tbody .checkbox:checked');
        // Aquí podrías mostrar un contador de elementos seleccionados
        console.log(`${checkedBoxes.length} usuarios seleccionados`);
    }

    // El conteo de resultados ahora lo maneja el servidor

    showUserDetails(userName) {
        this.showNotification(`Mostrando detalles de ${userName}`, 'info');
    }

    editUser(userName) {
        this.showNotification(`Editando usuario ${userName}`, 'warning');
    }

    confirmDeleteUser(userName) {
        const confirmed = confirm(`¿Estás seguro de que deseas eliminar al usuario ${userName}?\n\nEsta acción no se puede deshacer.`);
        if (confirmed) {
            this.deleteUser(userName);
        }
    }

    deleteUser(userName) {
        // Simular eliminación
        this.showNotification(`Usuario ${userName} eliminado correctamente`, 'success');
        
        // Aquí harías la petición real al servidor
        // fetch('/api/users/delete', { method: 'DELETE', ... })
    }

    showNotification(message, type = 'info') {
        // Usar el sistema de notificaciones moderno
        if (window.notifications) {
            window.notifications.show(message, type);
        } else {
            // Fallback si el sistema no está disponible
            console.warn('Sistema de notificaciones no disponible:', message);
        }
    }

    showTooltip(element, text) {
        // Limpiar tooltip anterior y timeout
        this.hideTooltip();
        
        // Crear nuevo tooltip
        const tooltip = document.createElement('div');
        tooltip.className = 'custom-tooltip';
        tooltip.textContent = text;
        
        // Agregar al container
        this.tooltipContainer.appendChild(tooltip);
        
        // Posicionar el tooltip
        this.positionTooltip(element, tooltip);
        
        // Guardar referencia
        this.currentTooltip = tooltip;
        
        // Mostrar con delay
        this.tooltipTimeout = setTimeout(() => {
            if (this.currentTooltip) {
                this.currentTooltip.classList.add('show');
            }
        }, 200);
    }

    positionTooltip(element, tooltip) {
        const rect = element.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
        
        // Calcular posición inicial (arriba del elemento)
        let top = rect.top + scrollTop - tooltipRect.height - 10;
        let left = rect.left + scrollLeft + (rect.width / 2) - (tooltipRect.width / 2);
        
        // Ajustar si se sale de la pantalla por arriba
        if (top < scrollTop + 10) {
            top = rect.bottom + scrollTop + 10;
            // Cambiar la flecha hacia arriba
            tooltip.style.setProperty('--arrow-direction', 'up');
        }
        
        // Ajustar si se sale de la pantalla por los lados
        const viewportWidth = window.innerWidth;
        if (left < 10) {
            left = 10;
        } else if (left + tooltipRect.width > viewportWidth - 10) {
            left = viewportWidth - tooltipRect.width - 10;
        }
        
        // Aplicar posición
        tooltip.style.top = `${top}px`;
        tooltip.style.left = `${left}px`;
    }

    hideTooltip() {
        // Limpiar timeout
        if (this.tooltipTimeout) {
            clearTimeout(this.tooltipTimeout);
            this.tooltipTimeout = null;
        }
        
        // Ocultar tooltip actual
        if (this.currentTooltip) {
            this.currentTooltip.classList.remove('show');
            
            // Remover después de la animación
            setTimeout(() => {
                if (this.currentTooltip && this.currentTooltip.parentNode) {
                    this.tooltipContainer.removeChild(this.currentTooltip);
                }
                this.currentTooltip = null;
            }, 200);
        }
    }

    animateCheckbox(checkbox) {
        checkbox.style.transform = 'scale(1.2)';
        setTimeout(() => {
            checkbox.style.transform = 'scale(1)';
        }, 150);
    }

    showLoading() {
        const tableContainer = document.querySelector('.table-container');
        if (tableContainer) {
            tableContainer.classList.add('loading');
        }
    }

    hideLoading() {
        const tableContainer = document.querySelector('.table-container');
        if (tableContainer) {
            tableContainer.classList.remove('loading');
        }
    }

    // Utility function para debounce
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Método para limpiar tooltips al destruir la instancia
    destroy() {
        this.hideTooltip();
        if (this.tooltipContainer && this.tooltipContainer.parentNode) {
            document.body.removeChild(this.tooltipContainer);
        }
    }
}

// Funciones utilitarias adicionales
const Utils = {
    // Formatear fechas
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('es-ES', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    },

    // Generar avatar con iniciales
    generateAvatar(firstName, lastName) {
        const initials = (firstName?.charAt(0) || '') + (lastName?.charAt(0) || '');
        return initials.toUpperCase();
    },

    // Validar email
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },

    // Escapar HTML
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    // Detectar si el dispositivo es móvil
    isMobile() {
        return window.innerWidth <= 768;
    },

    // Throttle function
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        }
    }
};

// Variable global para la instancia
let userManagementInstance = null;

// Función global para notificaciones (usa el sistema moderno)
function showGlobalNotification(message, type = 'info') {
    if (window.notifications) {
        window.notifications.show(message, type);
    } else {
        // Fallback temporal hasta que el sistema se cargue
        setTimeout(() => {
            if (window.notifications) {
                window.notifications.show(message, type);
            } else {
                console.warn('Sistema de notificaciones no disponible:', message);
            }
        }, 100);
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    userManagementInstance = new UserManagement();
    
    // Agregar algunos event listeners globales
    document.addEventListener('keydown', (e) => {
        // Esc para cerrar modales o limpiar búsqueda
        if (e.key === 'Escape') {
            // Ocultar tooltips
            if (userManagementInstance) {
                userManagementInstance.hideTooltip();
            }
            
            // Limpiar búsqueda
            const searchInput = document.querySelector('.table-search-input');
            if (searchInput && searchInput.value) {
                searchInput.value = '';
                searchInput.dispatchEvent(new Event('input'));
            }
        }
        
        // Ctrl+F para enfocar búsqueda
        if (e.ctrlKey && e.key === 'f') {
            e.preventDefault();
            const searchInput = document.querySelector('.table-search-input');
            if (searchInput) {
                searchInput.focus();
            }
        }
    });
});

// Limpiar al cerrar la página
window.addEventListener('beforeunload', () => {
    if (userManagementInstance) {
        userManagementInstance.destroy();
    }
});

// ===== JAVASCRIPT EXTRAÍDO DE TEMPLATES =====

// Funciones para modal de eliminación
function openDeleteModal(userId) {
    // Buscar información del usuario en la tabla
    let userRow = null;
    const deleteButtons = document.querySelectorAll('button[onclick*="openDeleteModal"]');
    
    for (let btn of deleteButtons) {
        if (btn.onclick.toString().includes(userId)) {
            userRow = btn.closest('tr');
            if (!userRow) {
                userRow = btn.closest('.mobile-user-card');
            }
            break;
        }
    }
    
    if (!userRow) {
        console.error('No se encontró información del usuario');
        return;
    }
    
    // Poblar modal
    if (userRow.tagName === 'TR') {
        populateDeleteModalFromTable(userId, userRow);
    } else {
        populateDeleteModalFromMobile(userId, userRow);
    }
    
    // Mostrar modal manualmente
    const modalElement = document.getElementById('deleteUserModal');
    modalElement.style.display = 'block';
    modalElement.classList.add('show');
    document.body.classList.add('modal-open');
}

// Función para cerrar el modal
function closeDeleteModal() {
    const modalElement = document.getElementById('deleteUserModal');
    modalElement.style.display = 'none';
    modalElement.classList.remove('show');
    document.body.classList.remove('modal-open');
}

function populateDeleteModalFromTable(userId, row) {
    const userInfo = extractUserInfoFromTableRow(row);
    populateDeleteModal(userId, userInfo);
}

function populateDeleteModalFromMobile(userId, card) {
    const userInfo = extractUserInfoFromMobileCard(card);
    populateDeleteModal(userId, userInfo);
}

function extractUserInfoFromTableRow(row) {
    const userNameEl = row.querySelector('.user-name');
    const emailEl = row.querySelector('.email-link');
    const roleEl = row.querySelector('.role-badge');
    const statusEl = row.querySelector('.status-badge');
    
    return {
        fullName: userNameEl ? userNameEl.textContent.trim() : 'N/A',
        email: emailEl ? emailEl.textContent.trim() : 'N/A',
        role: roleEl ? roleEl.textContent.trim() : 'N/A',
        status: statusEl ? statusEl.textContent.trim() : 'N/A',
        initials: userNameEl ? getInitials(userNameEl.textContent) : 'NA'
    };
}

function extractUserInfoFromMobileCard(card) {
    const userNameEl = card.querySelector('.user-name');
    const emailEl = card.querySelector('.user-username');
    const roleEl = card.querySelector('.role-badge');
    const statusEl = card.querySelector('.status-badge');
    
    return {
        fullName: userNameEl ? userNameEl.textContent.trim() : 'N/A',
        email: emailEl ? emailEl.textContent.trim() : 'N/A',
        role: roleEl ? roleEl.textContent.trim() : 'N/A',
        status: statusEl ? statusEl.textContent.trim() : 'N/A',
        initials: userNameEl ? getInitials(userNameEl.textContent) : 'NA'
    };
}

function getInitials(name) {
    return name.split(' ').map(n => n[0]).join('').toUpperCase();
}

function populateDeleteModal(userId, userInfo) {
    document.getElementById('userInitials').textContent = userInfo.initials;
    document.getElementById('userFullName').textContent = userInfo.fullName;
    document.getElementById('userEmail').textContent = userInfo.email;
    // Note: userOrganization será interpolado en el template
    document.getElementById('userStatus').innerHTML = `<span class="badge ${userInfo.status.toLowerCase() === 'activo' ? 'bg-success' : 'bg-secondary'}">${userInfo.status}</span>`;
    
    // Configurar el botón de confirmación
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    confirmBtn.setAttribute('data-user-id', userId);
    
    // Resetear checkbox y botón
    const checkbox = document.getElementById('confirmUnderstand');
    checkbox.checked = false;
    confirmBtn.disabled = true;
    
    // Resetear spinner
    const spinner = confirmBtn.querySelector('.spinner-border');
    if (spinner) spinner.classList.add('d-none');
}

function deleteUser(userId) {
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    const spinner = confirmBtn.querySelector('.spinner-border');
    
    // Mostrar loading
    confirmBtn.disabled = true;
    if (spinner) spinner.classList.remove('d-none');
    
    // Realizar petición de eliminación con la URL correcta
    const formData = new FormData();
    formData.append('confirm_delete', 'yes');
    
    fetch(`/users/${userId}/delete-ajax/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Cerrar modal
            closeDeleteModal();
            
            // Obtener nombre del usuario para la notificación
            const userNameEl = document.getElementById('userFullName');
            const userName = userNameEl ? userNameEl.textContent : 'Usuario';
            
            // Mostrar notificación de éxito
            if (userManagementInstance) {
                userManagementInstance.showNotification(
                    `${userName} eliminado correctamente`, 
                    'success'
                );
            } else {
                // Fallback si no hay instancia
                showGlobalNotification(`${userName} eliminado correctamente`, 'success');
            }
            
            // Actualizar estadísticas si se proporcionaron
            if (data.stats) {
                updateUserStats(data.stats);
            }
            
            // Eliminar tarjeta del usuario con animación
            const userCard = document.querySelector(`[data-user-id="${userId}"]`);
            if (userCard) {
                userCard.style.transition = 'all 0.3s ease';
                userCard.style.transform = 'scale(0.8)';
                userCard.style.opacity = '0';
                
                setTimeout(() => {
                    userCard.remove();
                    
                    // Verificar si no quedan usuarios en la lista
                    const userCards = document.querySelectorAll('.user-card');
                    if (userCards.length === 0) {
                        showEmptyUserState();
                    }
                }, 300);
            }
        } else {
            throw new Error(data.error || 'Error al eliminar usuario');
        }
    })
    .catch(error => {
        // Restaurar botón
        confirmBtn.disabled = false;
        if (spinner) spinner.classList.add('d-none');
        
        // Mostrar notificación de error
        if (userManagementInstance) {
            userManagementInstance.showNotification(
                `Error al eliminar usuario: ${error.message}`, 
                'error'
            );
        } else {
            // Fallback si no hay instancia
            showGlobalNotification(`Error al eliminar usuario: ${error.message}`, 'error');
        }
        
        // Log en consola para debug
        console.error('Error al eliminar usuario:', error);
        
        // Cerrar modal 
        closeDeleteModal();
    });
}

// Función para actualizar las estadísticas de usuarios en tiempo real
function updateUserStats(stats) {
    // Actualizar contador total
    const totalUsersEl = document.getElementById('totalUsers');
    if (totalUsersEl) {
        totalUsersEl.textContent = stats.total_users;
    }
    
    // Actualizar usuarios activos
    const activeUsersEl = document.getElementById('activeUsers');
    if (activeUsersEl) {
        activeUsersEl.textContent = stats.active_users;
    }
    
    // Actualizar usuarios inactivos
    const inactiveUsersEl = document.getElementById('inactiveUsers');
    if (inactiveUsersEl) {
        inactiveUsersEl.textContent = stats.inactive_users;
    }
    
    // Actualizar porcentaje activo si existe
    const percentageEl = document.getElementById('percentageActive');
    if (percentageEl) {
        percentageEl.textContent = `${stats.percentage_active}%`;
    }
    
    // Actualizar barra de progreso si existe
    const progressBar = document.querySelector('.progress-bar');
    if (progressBar) {
        progressBar.style.width = `${stats.percentage_active}%`;
        progressBar.setAttribute('aria-valuenow', stats.percentage_active);
    }
    
    // Actualizar espacios disponibles si se proporcionó el max_users
    if (stats.max_users !== undefined) {
        const remainingSlotsEl = document.getElementById('remainingSlots');
        if (remainingSlotsEl) {
            const remaining = Math.max(0, stats.max_users - stats.total_users);
            remainingSlotsEl.textContent = remaining;
        }
    }
}

// Función para mostrar estado vacío cuando no hay usuarios
function showEmptyUserState() {
    const userListContainer = document.querySelector('.user-list-container');
    if (!userListContainer) return;
    
    userListContainer.innerHTML = `
        <div class="text-center py-5">
            <i class="bi bi-people" style="font-size: 4rem; color: var(--secondary-color); opacity: 0.3;"></i>
            <h4 class="mt-3">No hay usuarios</h4>
            <p class="text-muted">Crea tu primer usuario para comenzar.</p>
            <a href="/users/create/" class="btn btn-primary mt-3">
                <i class="bi bi-person-plus"></i> Crear Usuario
            </a>
        </div>
    `;
}



// Funciones de validación para formularios
const FormValidation = {
    validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },
    
    validateRequired(value) {
        return value && value.trim().length > 0;
    },
    
    validateName(name) {
        return name && name.trim().length >= 2;
    },
    
    showFieldError(field, message) {
        // Remover errores anteriores
        const existingError = field.parentNode.querySelector('.error-message');
        if (existingError) {
            existingError.remove();
        }
        
        // Agregar nuevo error
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${message}`;
        field.parentNode.appendChild(errorDiv);
        
        // Estilo del campo con error
        field.classList.add('is-invalid');
    },
    
    clearFieldError(field) {
        const existingError = field.parentNode.querySelector('.error-message');
        if (existingError) {
            existingError.remove();
        }
        field.classList.remove('is-invalid');
    }
};

// Inicialización específica para modal de eliminación
document.addEventListener('DOMContentLoaded', function() {
    // Configurar modal de eliminación
    const confirmCheckbox = document.getElementById('confirmUnderstand');
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    
    if (confirmCheckbox && confirmBtn) {
        confirmCheckbox.addEventListener('change', function() {
            confirmBtn.disabled = !this.checked;
        });
        
        // Manejar click del botón de eliminar
        confirmBtn.addEventListener('click', function() {
            const userId = this.getAttribute('data-user-id');
            if (userId && confirmCheckbox.checked) {
                deleteUser(userId);
            }
        });
    }
    

    
    // Configurar validación en tiempo real para formularios
    const formInputs = document.querySelectorAll('.modern-input, .modern-select');
    formInputs.forEach(input => {
        input.addEventListener('blur', function() {
            FormValidation.clearFieldError(this);
            
            // Validaciones específicas según el tipo de campo
            if (this.type === 'email' && this.value) {
                if (!FormValidation.validateEmail(this.value)) {
                    FormValidation.showFieldError(this, 'Por favor, ingresa un email válido');
                }
            }
            
            if (this.required && !FormValidation.validateRequired(this.value)) {
                FormValidation.showFieldError(this, 'Este campo es obligatorio');
            }
        });
        
        // Limpiar errores al escribir
        input.addEventListener('input', function() {
            if (this.classList.contains('is-invalid')) {
                FormValidation.clearFieldError(this);
            }
        });
    });
});

// ===== MEJORAS DE UX PARA FORMULARIOS =====

// Mejorar experiencia de envío de formularios
document.addEventListener('DOMContentLoaded', function() {
    const userForm = document.getElementById('userForm');
    const saveButton = document.getElementById('saveButton');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const saveButtonText = document.getElementById('saveButtonText');
    
    if (userForm && saveButton) {
        userForm.addEventListener('submit', function(e) {
            // Mostrar estado de carga
            if (loadingSpinner) {
                loadingSpinner.style.display = 'inline-block';
            }
            if (saveButtonText) {
                saveButtonText.style.opacity = '0.7';
            }
            saveButton.disabled = true;
            
            // Validar formulario antes de enviar
            const requiredFields = userForm.querySelectorAll('[required]');
            let allValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    allValid = false;
                    field.classList.add('error');
                    FormValidation.showFieldError(field, 'Este campo es obligatorio');
                } else {
                    field.classList.remove('error');
                    FormValidation.clearFieldError(field);
                }
            });
            
            if (!allValid) {
                e.preventDefault();
                // Restaurar estado del botón
                if (loadingSpinner) {
                    loadingSpinner.style.display = 'none';
                }
                if (saveButtonText) {
                    saveButtonText.style.opacity = '1';
                }
                saveButton.disabled = false;
                
                // Mostrar mensaje de error
                showFormNotification('Por favor, completa todos los campos obligatorios', 'error');
                return;
            }
        });
    }
});

// Función para mostrar notificaciones en formularios - DEPRECATED
// Usar window.notifications en su lugar
function showFormNotification(message, type = 'info') {
    console.warn('showFormNotification está obsoleto, usar window.notifications en su lugar');
    if (window.notifications) {
        window.notifications.show(message, type);
    }
}

// Mejorar validación de email en tiempo real
function setupAdvancedEmailValidation() {
    const emailInputs = document.querySelectorAll('input[type="email"]');
    
    emailInputs.forEach(input => {
        let validationTimeout;
        
        input.addEventListener('input', function() {
            clearTimeout(validationTimeout);
            
            // Debounce la validación
            validationTimeout = setTimeout(() => {
                const email = this.value.trim();
                if (email) {
                    if (FormValidation.validateEmail(email)) {
                        this.classList.add('valid');
                        this.classList.remove('error');
                        FormValidation.clearFieldError(this);
                    } else {
                        this.classList.add('error');
                        this.classList.remove('valid');
                        FormValidation.showFieldError(this, 'Formato de email inválido');
                    }
                } else {
                    this.classList.remove('valid', 'error');
                    FormValidation.clearFieldError(this);
                }
            }, 500);
        });
    });
}

// Animaciones suaves para elementos del formulario
function setupFormAnimations() {
    const formSections = document.querySelectorAll('.form-section');
    
    // Animación de entrada para las secciones
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, {
        threshold: 0.1
    });
    
    formSections.forEach(section => {
        section.style.opacity = '0';
        section.style.transform = 'translateY(20px)';
        section.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(section);
    });
}

// Mejorar accesibilidad del formulario
function setupAccessibilityFeatures() {
    // Agregar indicadores visuales para campos requeridos
    const requiredFields = document.querySelectorAll('[required]');
    requiredFields.forEach(field => {
        const label = document.querySelector(`label[for="${field.id}"]`);
        if (label && !label.querySelector('.required')) {
            const requiredIndicator = document.createElement('span');
            requiredIndicator.className = 'required';
            requiredIndicator.textContent = ' *';
            requiredIndicator.setAttribute('aria-label', 'campo obligatorio');
            label.appendChild(requiredIndicator);
        }
    });
    
    // Mejorar navegación con teclado
    const formInputs = document.querySelectorAll('.modern-input, .modern-select');
    formInputs.forEach((input, index) => {
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && this.tagName !== 'TEXTAREA') {
                e.preventDefault();
                const nextInput = formInputs[index + 1];
                if (nextInput) {
                    nextInput.focus();
                } else {
                    // Si es el último campo, enviar formulario
                    const submitButton = document.querySelector('button[type="submit"]');
                    if (submitButton) {
                        submitButton.click();
                    }
                }
            }
        });
    });
}

// Inicializar todas las mejoras de UX
document.addEventListener('DOMContentLoaded', function() {
    setupAdvancedEmailValidation();
    setupFormAnimations();
    setupAccessibilityFeatures();
});

// ===== FIN DEL ARCHIVO =====