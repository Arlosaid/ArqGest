/**
 * Projects Module - JavaScript v2.5
 * Funcionalidades profesionales para el módulo de proyectos
 */

class ProjectsManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupSearchAndFilters();
        this.setupTooltips();
        this.ensureSingleActiveTab();
        this.normalizeInitialActiveTab();
        this.activateTabFromUrl();
    }

    setupEventListeners() {
        // Búsqueda simplificada
        const searchInput = document.querySelector('.search-input-modern');

        if (searchInput) {
            searchInput.addEventListener('input', (e) => this.handleSearch(e.target.value));
            searchInput.addEventListener('keyup', (e) => this.handleSearch(e.target.value));
        }

        // Botones de acción
        const actionButtons = document.querySelectorAll('.btn-action-modern');
        actionButtons.forEach(button => {
            button.addEventListener('click', (e) => this.handleActionClick(e));
        });
    }

    setupSearchAndFilters() {
        // Búsqueda en tiempo real
        let searchTimeout;
        const searchInput = document.querySelector('.search-input-modern');
        
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                const searchTerm = e.target.value.trim();
                
                // Búsqueda inmediata para términos cortos
                if (searchTerm.length <= 2) {
                    this.performSearch(searchTerm);
                } else {
                    // Debounce para términos más largos
                    searchTimeout = setTimeout(() => {
                        this.performSearch(searchTerm);
                    }, 200);
                }
            });
        }
    }

    setupTooltips() {
        // Tooltips simples
        const tooltipElements = document.querySelectorAll('[data-tooltip]');
        tooltipElements.forEach(element => {
            element.addEventListener('mouseenter', (e) => this.showTooltip(e));
            element.addEventListener('mouseleave', () => this.hideTooltip());
        });
    }

    handleSearch(searchTerm) {
        const cards = document.querySelectorAll('.project-card-modern');
        let visibleCount = 0;

        cards.forEach(card => {
            const title = card.querySelector('.project-card-title-modern').textContent.toLowerCase();
            const searchLower = searchTerm.toLowerCase();

            if (searchLower === '' || title.includes(searchLower)) {
                card.style.display = 'block';
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });

        this.updateResultsCounter(visibleCount, cards.length);
    }

    performSearch(searchTerm) {
        // Búsqueda por nombre de proyecto
        const cards = document.querySelectorAll('.project-card-modern');
        const results = [];

        cards.forEach(card => {
            const title = card.querySelector('.project-card-title-modern').textContent;
            const searchLower = searchTerm.toLowerCase();
            
            if (searchLower === '' || title.toLowerCase().includes(searchLower)) {
                results.push(card);
            }
        });

        this.displaySearchResults(results);
    }

    displaySearchResults(results) {
        const cards = document.querySelectorAll('.project-card-modern');
        
        cards.forEach(card => {
            if (results.includes(card)) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });

        this.updateResultsCounter(results.length, cards.length);
    }

    updateResultsCounter(visible, total) {
        const counter = document.querySelector('.search-results-counter');
        if (counter) {
            if (visible === total) {
                counter.style.display = 'none';
            } else {
                counter.textContent = `${visible} de ${total} proyectos`;
                counter.style.display = 'block';
            }
        }
    }

    handleActionClick(event) {
        const button = event.currentTarget;
        const action = this.getActionType(button);
        
        // Log de acción
        console.log(`Acción: ${action}`);
    }

    getActionType(button) {
        if (button.classList.contains('btn-view-modern')) return 'view';
        if (button.classList.contains('btn-edit-modern')) return 'edit';
        if (button.classList.contains('btn-delete-modern')) return 'delete';
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

// Estilos adicionales para componentes dinámicos
const additionalStyles = `
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

// Inyectar estilos
const styleSheet = document.createElement('style');
styleSheet.textContent = additionalStyles;
document.head.appendChild(styleSheet);

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new ProjectsManager();
});

// Exportar para uso global
window.ProjectsManager = ProjectsManager;
