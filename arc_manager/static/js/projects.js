/**
 * Projects Module - JavaScript v5.0
 * Funcionalidades profesionales para el módulo de proyectos con filtros de backend
 */

class ProjectsManager {
    constructor() {
        this.init();
    }

    init() {
        this.currentStatusFilter = 'all'; // Filtro actual
        this.searchTimeout = null;
        this.setupSearchAndFilters();
        this.setupStatusFilters();
        this.setupTooltips();
        this.setupActionButtons();
        this.ensureSingleActiveTab();
        this.normalizeInitialActiveTab();
        this.activateTabFromUrl();
    }

    setupActionButtons() {
        // Action buttons
        const actionButtons = document.querySelectorAll('.action-btn');
        actionButtons.forEach(button => {
            button.addEventListener('click', (e) => this.handleActionClick(e));
        });
    }

    setupSearchAndFilters() {
        const searchInput = document.querySelector('.search-input-inline, .table-search-input, .search-input-modern');
        const clearBtn = document.querySelector('.clear-search-btn');
        
        if (searchInput) {
            // Cargar valor de búsqueda desde URL
            const urlParams = new URLSearchParams(window.location.search);
            const searchFromUrl = urlParams.get('search') || '';
            if (searchFromUrl) {
                searchInput.value = searchFromUrl;
                if (clearBtn) clearBtn.style.display = 'flex'; // Changed to flex to center icon
            }
            
            // Solo un event listener para búsqueda
            searchInput.addEventListener('input', (e) => {
                if (this.searchTimeout) {
                    clearTimeout(this.searchTimeout);
                }
                
                const searchTerm = e.target.value.trim();
                
                // Show/hide clear button
                if (clearBtn) {
                    clearBtn.style.display = searchTerm.length > 0 ? 'flex' : 'none';
                }
                
                // Búsqueda con debounce
                this.searchTimeout = setTimeout(() => {
                    this.applyFiltersWithUrl(searchTerm, this.currentStatusFilter);
                }, 400);
            });
        }

        if (clearBtn) {
            clearBtn.addEventListener('click', (e) => {
                e.preventDefault();
                if (searchInput) {
                    searchInput.value = '';
                    this.applyFiltersWithUrl('', this.currentStatusFilter);
                }
                clearBtn.style.display = 'none';
            });
        }
    }

    setupStatusFilters() {
        const filterButtons = document.querySelectorAll('.filter-btn, .filter-btn-compact, .filter-btn-modern');
        
        if (!filterButtons.length) {
            return;
        }
        
        // Cargar filtro de status desde URL
        const urlParams = new URLSearchParams(window.location.search);
        const statusFromUrl = urlParams.get('status') || 'all';
        this.currentStatusFilter = statusFromUrl;
        
        // Marcar el botón activo según la URL
        filterButtons.forEach(btn => {
            if (btn.dataset.filter === statusFromUrl) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
        
        filterButtons.forEach((button, index) => {
            console.log(`✅ Registrando listener para botón ${index + 1}:`, button.dataset.filter);
            
            button.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                console.log('🖱️ CLICK en filtro:', button.dataset.filter);
                
                // Remover clase active de todos los botones
                filterButtons.forEach(btn => btn.classList.remove('active'));
                
                // Agregar clase active al botón clickeado
                button.classList.add('active');
                
                // Obtener el filtro seleccionado
                const filter = button.dataset.filter;
                this.currentStatusFilter = filter;
                
                console.log('📊 Filtro actualizado a:', this.currentStatusFilter);
                
                // Obtener término de búsqueda actual
                const searchInput = document.querySelector('.table-search-input');
                const searchTerm = searchInput ? searchInput.value.trim() : '';
                
                // Aplicar filtros con URL
                this.applyFiltersWithUrl(searchTerm, filter);
            });
        });
        
        console.log('✅ Filtros configurados correctamente');
    }

    applyFiltersWithUrl(searchTerm = '', statusFilter = 'all') {
        // Construir nueva URL con filtros
        const url = new URL(window.location);
        
        // Actualizar parámetros
        if (searchTerm) {
            url.searchParams.set('search', searchTerm);
        } else {
            url.searchParams.delete('search');
        }
        
        if (statusFilter && statusFilter !== 'all') {
            url.searchParams.set('status', statusFilter);
        } else {
            url.searchParams.delete('status');
        }
        
        // Resetear página a 1 cuando se cambia el filtro
        url.searchParams.delete('page');
        
        console.log('🔄 Redirigiendo con filtros:', url.toString());
        
        // Redirigir a la nueva URL
        window.location.href = url.toString();
    }

    setupTooltips() {
        // Tooltips simples
        const tooltipElements = document.querySelectorAll('[data-tooltip]');
        tooltipElements.forEach(element => {
            element.addEventListener('mouseenter', (e) => this.showTooltip(e));
            element.addEventListener('mouseleave', () => this.hideTooltip());
        });
    }

    handleActionClick(event) {
        const button = event.currentTarget;
        const action = this.getActionType(button);
        
        // Log de acción
        console.log(`Acción: ${action}`);
    }

    getActionType(button) {
        if (button.classList.contains('view')) return 'view';
        if (button.classList.contains('edit')) return 'edit';
        if (button.classList.contains('delete')) return 'delete';
        return 'unknown';
    }

    showTooltip(event) {
        const tooltip = event.target.dataset.tooltip;
        if (!tooltip) return;

        const tooltipElement = document.createElement('div');
        tooltipElement.className = 'custom-tooltip';
        tooltipElement.textContent = tooltip;
        tooltipElement.style.cssText = `
            position: absolute;
            background: var(--project-text);
            color: white;
            padding: 0.5rem 0.75rem;
            border-radius: var(--project-radius);
            font-size: 0.75rem;
            white-space: nowrap;
            z-index: 1000;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
        `;

        document.body.appendChild(tooltipElement);

        // Posicionar tooltip
        const rect = event.target.getBoundingClientRect();
        tooltipElement.style.top = `${rect.top - tooltipElement.offsetHeight - 8}px`;
        tooltipElement.style.left = `${rect.left + (rect.width / 2) - (tooltipElement.offsetWidth / 2)}px`;

        // Mostrar tooltip
        setTimeout(() => {
            tooltipElement.style.opacity = '1';
        }, 10);

        // Guardar referencia para remover
        event.target._tooltip = tooltipElement;
    }

    hideTooltip() {
        const tooltips = document.querySelectorAll('.custom-tooltip');
        tooltips.forEach(tooltip => {
            tooltip.remove();
        });
    }

    // Evitar que dos pestañas queden visibles a la vez
    ensureSingleActiveTab() {
        const tabContainer = document.getElementById('projectTab');
        if (!tabContainer) return;

        const enforce = (btn) => {
            const targetSelector = btn?.getAttribute('data-bs-target');
            const targetPane = targetSelector ? document.querySelector(targetSelector) : null;
            const panes = document.querySelectorAll('#projectTabContent .tab-pane');
            panes.forEach(pane => pane.classList.remove('show', 'active'));
            if (targetPane) targetPane.classList.add('show', 'active');
        };

        tabContainer.addEventListener('shown.bs.tab', (event) => {
            enforce(event.target);
        });

        // Hacer toggle por click SIEMPRE para garantizar consistencia
        tabContainer.addEventListener('click', (e) => {
            const btn = e.target.closest('button[data-bs-target]');
            if (!btn) return;
            enforce(btn);
            // Estado active del botón
            tabContainer.querySelectorAll('.nav-link').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    }

    // Asegura que al cargar solo una pestaña esté visible
    normalizeInitialActiveTab() {
        const tabContainer = document.getElementById('projectTab');
        if (!tabContainer) return;
        let activeBtn = tabContainer.querySelector('.nav-link.active');
        // Si ninguna pestaña está marcada activa, forzar Detalles por defecto
        if (!activeBtn) {
            activeBtn = tabContainer.querySelector('#details-tab') || tabContainer.querySelector('.nav-link');
            if (activeBtn) activeBtn.classList.add('active');
        }
        if (!activeBtn) return;
        const targetSelector = activeBtn.getAttribute('data-bs-target');
        const targetPane = targetSelector ? document.querySelector(targetSelector) : null;
        const panes = document.querySelectorAll('#projectTabContent .tab-pane');
        panes.forEach(pane => pane.classList.remove('show', 'active'));
        if (targetPane) targetPane.classList.add('show', 'active');
        // Reforzar tras breve retraso por si otros scripts alteran el DOM
        setTimeout(() => {
            const currentActiveBtn = tabContainer.querySelector('.nav-link.active') || tabContainer.querySelector('#details-tab');
            const currentTarget = currentActiveBtn?.getAttribute('data-bs-target');
            const currentPane = currentTarget ? document.querySelector(currentTarget) : null;
            if (currentPane && !currentPane.classList.contains('active')) {
                document.querySelectorAll('#projectTabContent .tab-pane').forEach(p => p.classList.remove('show','active'));
                currentPane.classList.add('show','active');
            }
        }, 50);
    }

    // Activa una pestaña si hay ?tab= o #hash en la URL
    activateTabFromUrl() {
        const tabContainer = document.getElementById('projectTab');
        if (!tabContainer) return;
        try {
            const params = new URLSearchParams(window.location.search);
            const tabParam = (params.get('tab') || '').toLowerCase();
            const hash = (window.location.hash || '').replace('#','').toLowerCase();
            const desired = tabParam || hash;
            const idMap = { details: 'details-tab', phases: 'phases-tab', tasks: 'tasks-tab', files: 'files-tab' };
            if (desired && idMap[desired]) {
                const btn = document.getElementById(idMap[desired]);
                if (btn) {
                    if (window.bootstrap && window.bootstrap.Tab) {
                        const tab = new bootstrap.Tab(btn);
                        tab.show();
                    } else {
                        btn.click();
                    }
                }
            }
        } catch (_) { /* noop */ }
    }
}

// Inicialización cuando el DOM esté listo
(function() {
    // Estilos adicionales para componentes dinámicos
    if (!document.getElementById('projects-custom-styles')) {
        const styleSheet = document.createElement('style');
        styleSheet.id = 'projects-custom-styles';
        styleSheet.textContent = `
            .custom-tooltip {
                position: absolute;
                background: var(--project-text);
                color: white;
                padding: 0.5rem 0.75rem;
                border-radius: var(--project-radius);
                font-size: 0.75rem;
                white-space: nowrap;
                z-index: 1000;
                pointer-events: none;
                opacity: 0;
                transition: opacity 0.2s;
            }
        `;
        document.head.appendChild(styleSheet);
    }

    // Función para actualizar círculos de progreso
    function updateProgressCircles() {
        const progressCircles = document.querySelectorAll('.progress-circle');
        
        progressCircles.forEach(circle => {
            const progress = parseInt(circle.dataset.progress) || 0;
            const degrees = (progress / 100) * 360;
            
            circle.style.background = `conic-gradient(#007bff ${degrees}deg, #e9ecef ${degrees}deg)`;
        });
    }

    // Ejecutar cuando el DOM esté listo
    document.addEventListener('DOMContentLoaded', function() {
        console.log('🚀 Inicializando ProjectsManager...');
        updateProgressCircles();
        try {
            if (typeof ProjectsManager === 'function') {
                window.projectsManagerInstance = new ProjectsManager();
                console.log('✅ ProjectsManager inicializado correctamente');
            }
        } catch (e) {
            console.error('❌ Error al inicializar ProjectsManager:', e);
        }
    });

    // Exportar para uso global
    window.ProjectsManager = ProjectsManager;
})();
