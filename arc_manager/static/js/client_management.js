// Gestión de Clientes - JavaScript con búsqueda del servidor
class ClientManagement {
    constructor() {
        // Solo inicializar si estamos en la página de gestión de clientes
        if (!document.querySelector('.client-management-page')) {
            return;
        }
        
        // Verificar elementos necesarios
        if (!document.querySelector('.table-search-input')) {
            return;
        }
        
        this.searchInput = document.querySelector('.table-search-input');
        this.actionButtons = document.querySelectorAll('.action-btn');
        this.paginationButtons = document.querySelectorAll('.pagination-btn, .pagination-number');
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupSearch();
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
    }

    setupSearch() {
        // Configuración adicional para búsqueda si es necesaria
        if (this.searchInput) {
            // Focus automático con Ctrl+F
            document.addEventListener('keydown', (e) => {
                if (e.ctrlKey && e.key === 'f') {
                    e.preventDefault();
                    this.searchInput.focus();
                }
                
                // Limpiar búsqueda con Escape
                if (e.key === 'Escape' && this.searchInput.value) {
                    this.searchInput.value = '';
                    // Enviar formulario para limpiar la búsqueda
                    const form = this.searchInput.closest('form');
                    if (form) form.submit();
                }
            });
        }
    }

    handleServerSearch(event) {
        const searchTerm = event.target.value.trim();
        const form = event.target.closest('form');
        
        if (!form) {
            return;
        }
        
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
        
        // No manejar aquí los botones que ya tienen href
        if (button.hasAttribute('href')) {
            return; // Dejar que el navegador maneje la navegación
        }

        const action = button.classList.contains('view') ? 'view' : 
                      button.classList.contains('edit') ? 'edit' : 'delete';

        const row = button.closest('tr');
        const clientName = row ? row.querySelector('.client-name').textContent : '';

        switch (action) {
            case 'view':
                this.showClientDetails(clientName);
                break;
            case 'edit':
                this.editClient(clientName);
                break;
            case 'delete':
                this.confirmDeleteClient(clientName);
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

    showClientDetails(clientName) {
        this.showNotification(`Mostrando detalles de ${clientName}`, 'info');
    }

    editClient(clientName) {
        this.showNotification(`Editando cliente ${clientName}`, 'warning');
    }

    confirmDeleteClient(clientName) {
        const confirmed = confirm(`¿Estás seguro de que deseas eliminar al cliente ${clientName}?\n\nEsta acción no se puede deshacer.`);
        if (confirmed) {
            this.deleteClient(clientName);
        }
    }

    deleteClient(clientName) {
        // Simular eliminación
        this.showNotification(`Cliente ${clientName} eliminado correctamente`, 'success');
        
        // Aquí harías la petición real al servidor
        // fetch('/api/clients/delete', { method: 'DELETE', ... })
    }

    showNotification(message, type = 'info') {
        // Usar el sistema de notificaciones moderno
        if (window.notifications) {
            window.notifications.show(message, type);
        }
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
}

// Funciones globales para compatibilidad
function clearSearch() {
    const searchInput = document.querySelector('.table-search-input');
    if (searchInput) {
        searchInput.value = '';
        // Enviar formulario para limpiar la búsqueda
        const form = searchInput.closest('form');
        if (form) {
            form.submit();
        } else {
            // Fallback: redirigir a la página sin parámetros
            window.location.href = window.location.pathname;
        }
    }
}

// Variable global para la instancia
let clientManagementInstance = null;

// Función global para notificaciones (usa el sistema moderno)
function showGlobalNotification(message, type = 'info') {
    if (window.notifications) {
        window.notifications.show(message, type);
    } else {
        // Fallback temporal hasta que el sistema se cargue
        setTimeout(() => {
            if (window.notifications) {
                window.notifications.show(message, type);
            }
        }, 100);
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    // Verificar si estamos en la página correcta
    const isClientPage = document.querySelector('.client-management-page') || 
                        (document.querySelector('h1') && document.querySelector('h1').textContent.includes('Gestión de Clientes'));
    
    if (!isClientPage) {
        return;
    }
    
    // Intentar inicializar la clase principal
    try {
        clientManagementInstance = new ClientManagement();
    } catch (error) {
        // Silent fail
    }
    
    // Siempre inicializar búsqueda simple como respaldo
    setTimeout(() => {
        initSimpleSearch();
    }, 200);
});

// Función de búsqueda simple como fallback
function initSimpleSearch() {
    const searchInput = document.querySelector('.table-search-input');
    if (!searchInput) {
        return;
    }
    
    // Verificar si ya tiene event listeners (para evitar duplicados)
    if (searchInput.hasAttribute('data-search-initialized')) {
        return;
    }
    
    // Marcar como inicializado
    searchInput.setAttribute('data-search-initialized', 'true');
    
    // Event listener para búsqueda
    searchInput.addEventListener('input', function(event) {
        const searchTerm = event.target.value.trim();
        const form = event.target.closest('form');
        
        if (!form) {
            return;
        }
        
        // Limpiar timeout anterior
        if (window.clientSearchTimeout) {
            clearTimeout(window.clientSearchTimeout);
        }
        
        // Crear nuevo timeout para debounce
        window.clientSearchTimeout = setTimeout(() => {
            // Mostrar indicador visual (opcional)
            const searchIcon = document.querySelector('.table-search-icon');
            if (searchIcon) {
                searchIcon.className = 'fas fa-spinner fa-spin table-search-icon';
            }
            
            // Enviar formulario
            form.submit();
        }, 500);
    });
    
    // Event listener para tecla Escape
    searchInput.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && this.value) {
            this.value = '';
            const form = this.closest('form');
            if (form) {
                form.submit();
            }
        }
    });
}

// Limpiar al cerrar la página
window.addEventListener('beforeunload', () => {
    if (window.clientSearchTimeout) {
        clearTimeout(window.clientSearchTimeout);
    }
    if (clientManagementInstance) {
        // Limpiar si es necesario
    }
});