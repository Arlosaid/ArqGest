// static/js/sidebar.js

class SidebarManager {
    constructor() {
        this.sidebar = document.getElementById('sidebar');
        this.sidebarToggle = document.getElementById('sidebarToggle');
        this.sidebarOverlay = document.getElementById('sidebarOverlay');
        this.navLinks = document.querySelectorAll('.nav-link');
        this.sectionHeaders = document.querySelectorAll('.section-header');
        this.mainContent = document.querySelector('.main-content');
        this.body = document.body;
        this.isOpen = false;
        this.isMobile = window.innerWidth <= 768;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.handleResize();
        this.setActiveLink();
        this.updateLayout();
    }
    
    bindEvents() {
        // Toggle sidebar en móvil
        if (this.sidebarToggle) {
            this.sidebarToggle.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.toggleSidebar();
            });
        }
        
        // Cerrar sidebar al hacer click en overlay
        if (this.sidebarOverlay) {
            this.sidebarOverlay.addEventListener('click', () => this.closeSidebar());
        }
        
        // Cerrar sidebar con tecla Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen && this.isMobile) {
                this.closeSidebar();
            }
        });
        
        // Manejo responsive
        window.addEventListener('resize', () => this.handleResize());
        
        // Efectos de hover para los enlaces
        this.navLinks.forEach(link => {
            link.addEventListener('mouseenter', (e) => this.handleLinkHover(e));
            link.addEventListener('mouseleave', (e) => this.handleLinkLeave(e));
            link.addEventListener('click', (e) => this.handleLinkClick(e));
        });
        
        // Efectos para headers de sección
        this.sectionHeaders.forEach(header => {
            header.addEventListener('click', (e) => this.handleSectionClick(e));
        });
        
        // Prevenir scroll cuando sidebar está abierto en móvil
        document.addEventListener('touchmove', (e) => {
            if (this.isOpen && this.isMobile && !this.sidebar.contains(e.target)) {
                e.preventDefault();
            }
        }, { passive: false });
    }
    
    toggleSidebar() {
        if (this.isOpen) {
            this.closeSidebar();
        } else {
            this.openSidebar();
        }
    }
    
    openSidebar() {
        if (!this.isMobile) return;
        
        this.sidebar.classList.add('sidebar-open');
        this.sidebarOverlay.classList.add('show');
        this.body.classList.add('sidebar-open');
        this.isOpen = true;
        
        // Disparar evento personalizado
        this.dispatchEvent('sidebar:opened');
    }
    
    closeSidebar() {
        if (!this.isMobile) return;
        
        this.sidebar.classList.remove('sidebar-open');
        this.sidebarOverlay.classList.remove('show');
        this.body.classList.remove('sidebar-open');
        this.isOpen = false;
        
        // Disparar evento personalizado
        this.dispatchEvent('sidebar:closed');
    }
    
    handleResize() {
        const wasMobile = this.isMobile;
        this.isMobile = window.innerWidth <= 768;
        
        // Si cambió de móvil a desktop
        if (wasMobile && !this.isMobile) {
            this.closeSidebar();
            this.sidebar.classList.remove('sidebar-open');
            this.sidebarOverlay.classList.remove('show');
            this.body.classList.remove('sidebar-open');
        }
        
        // Actualizar layout
        this.updateLayout();
    }
    
    updateLayout() {
        if (!this.isMobile && this.mainContent) {
            // En desktop, asegurar margen correcto
            this.mainContent.style.marginLeft = 'var(--side-layout-width)';
        } else if (this.mainContent) {
            this.mainContent.style.marginLeft = '0';
        }
    }
    
    handleLinkHover(e) {
        const link = e.currentTarget;
        const icon = link.querySelector('.nav-icon i');
        
        // Efecto de rotación sutil en el icono
        if (icon) {
            icon.style.transform = 'rotate(5deg) scale(1.1)';
            icon.style.transition = 'transform 0.3s ease';
        }
    }
    
    handleLinkLeave(e) {
        const link = e.currentTarget;
        const icon = link.querySelector('.nav-icon i');
        
        if (icon) {
            icon.style.transform = '';
        }
    }
    
    handleLinkClick(e) {
        const link = e.currentTarget;
        
        // Efecto de click simplificado
        link.style.transform = 'scale(0.95)';
        setTimeout(() => {
            link.style.transform = '';
        }, 150);
        
        // En móvil, cerrar sidebar después del click
        if (this.isMobile && this.isOpen) {
            setTimeout(() => this.closeSidebar(), 250);
        }
        
        // Actualizar estado activo
        this.setActiveLink(link);
    }
    
    handleSectionClick(e) {
        const header = e.currentTarget;
        const section = header.closest('.nav-section');
        const navList = section.querySelector('.nav-list');
        
        if (navList) {
            // Toggle collapse de la sección
            section.classList.toggle('collapsed');
            
            // Animar colapso
            if (section.classList.contains('collapsed')) {
                navList.style.maxHeight = '0';
                navList.style.opacity = '0';
            } else {
                navList.style.maxHeight = navList.scrollHeight + 'px';
                navList.style.opacity = '1';
            }
        }
    }
    
    setActiveLink(activeLink = null) {
        // Remover clase activa de todos los enlaces
        this.navLinks.forEach(link => {
            link.classList.remove('active');
        });
        
        if (activeLink) {
            activeLink.classList.add('active');
        } else {
            // Buscar enlace activo basado en la URL actual
            const currentPath = window.location.pathname;
            this.navLinks.forEach(link => {
                const href = link.getAttribute('href');
                if (href && href !== '#' && currentPath.includes(href)) {
                    link.classList.add('active');
                }
            });
        }
    }
    
    addClickEffect(element) {
        element.style.transform = 'scale(0.95)';
        element.style.transition = 'transform 0.15s ease';
        
        setTimeout(() => {
            element.style.transform = '';
        }, 150);
    }

    dispatchEvent(eventName) {
        const event = new CustomEvent(eventName, {
            detail: {
                isOpen: this.isOpen,
                isMobile: this.isMobile
            }
        });
        document.dispatchEvent(event);
    }
    
    // Métodos públicos para control externo
    collapse() {
        this.sidebar.classList.add('sidebar-collapsed');
    }
    
    expand() {
        this.sidebar.classList.remove('sidebar-collapsed');
    }
    
    isCollapsed() {
        return this.sidebar.classList.contains('sidebar-collapsed');
    }
    
    // Método para forzar actualización
    refresh() {
        this.handleResize();
        this.setActiveLink();
        this.updateLayout();
    }
}

// Agregar estilos CSS para funcionalidades necesarias
const additionalStyles = `
    .nav-list {
        transition: max-height 0.3s ease, opacity 0.3s ease;
        overflow: hidden;
    }
    
    .nav-section.collapsed .nav-list {
        max-height: 0 !important;
    }
    
    .sidebar-collapsed {
        width: var(--sidebar-collapsed-width) !important;
    }
    
    .sidebar-collapsed .nav-text,
    .sidebar-collapsed .brand-text,
    .sidebar-collapsed .section-title,
    .sidebar-collapsed .user-info {
        opacity: 0;
        visibility: hidden;
    }
    
    .sidebar-collapsed .nav-icon {
        margin-right: 0;
        justify-content: center;
    }
    
    /* Mejoras de performance */
    .sidebar {
        will-change: transform;
    }
    
    .nav-link {
        will-change: transform, background-color;
    }
`;

// Agregar estilos al head
const styleSheet = document.createElement('style');
styleSheet.textContent = additionalStyles;
document.head.appendChild(styleSheet);

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    try {
        window.sidebarManager = new SidebarManager();
        
        // Eventos globales para debugging
        document.addEventListener('sidebar:opened', () => {
            console.log('🎨 Sidebar abierto');
        });
        
        document.addEventListener('sidebar:closed', () => {
            console.log('🎨 Sidebar cerrado');
        });
        
    } catch (error) {
        console.error('❌ Error inicializando Sidebar Manager:', error);
    }
});

// Exportar para uso global
window.SidebarManager = SidebarManager;

// sidebar.js - Funcionalidad para el modal de selección de proyectos
document.addEventListener('DOMContentLoaded', function() {
    const kanbanProjectsBtn = document.getElementById('kanbanProjectsBtn');
    const kanbanProjectsModal = document.getElementById('kanbanProjectsModal');
    const projectSearchInput = document.getElementById('projectSearchInput');
    const statusFilter = document.getElementById('statusFilter');
    const clientFilter = document.getElementById('clientFilter');
    const projectsGrid = document.getElementById('projectsGrid');

    if (!kanbanProjectsBtn) return;

    // Cargar proyectos cuando se abre el modal
    kanbanProjectsModal.addEventListener('show.bs.modal', function() {
        loadProjects();
        loadClientOptions();
    });

    // Búsqueda en tiempo real
    if (projectSearchInput) {
        projectSearchInput.addEventListener('input', debounce(function() {
            filterProjects();
        }, 300));
    }

    // Filtros
    if (statusFilter) {
        statusFilter.addEventListener('change', filterProjects);
    }
    if (clientFilter) {
        clientFilter.addEventListener('change', filterProjects);
    }

    // Cargar proyectos desde la API
    async function loadProjects() {
        try {
            const response = await fetch('/api/projects/');
            if (!response.ok) throw new Error('Error al cargar proyectos');
            
            const projects = await response.json();
            displayProjects(projects);
        } catch (error) {
            console.error('Error:', error);
            displayProjects([]);
        }
    }

    // Cargar opciones de clientes
    async function loadClientOptions() {
        try {
            const response = await fetch('/api/clients/');
            if (!response.ok) throw new Error('Error al cargar clientes');
            
            const clients = await response.json();
            populateClientFilter(clients);
        } catch (error) {
            console.error('Error:', error);
        }
    }

    // Mostrar proyectos en el grid
    function displayProjects(projects) {
        if (!projectsGrid) return;

        projectsGrid.innerHTML = '';
        
        if (projects.length === 0) {
            projectsGrid.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="fas fa-folder-open fa-3x text-muted mb-3"></i>
                    <h5 class="text-muted">No se encontraron proyectos</h5>
                    <p class="text-muted">Intenta ajustar los filtros o crear un nuevo proyecto</p>
                </div>
            `;
            return;
        }

        projects.forEach(project => {
            const projectCard = createProjectCard(project);
            projectsGrid.appendChild(projectCard);
        });
    }

    // Crear tarjeta de proyecto
    function createProjectCard(project) {
        const col = document.createElement('div');
        col.className = 'col-md-6 col-lg-4 mb-3';
        
        const statusClass = getStatusClass(project.status);
        const progress = project.progress_percentage || 0;
        
        col.innerHTML = `
            <div class="project-card-kanban h-100" data-project-id="${project.id}">
                <div class="card h-100 border-0 shadow-sm">
                    <div class="card-body p-3">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="card-title mb-0 text-truncate" title="${project.name}">
                                ${project.name}
                            </h6>
                            <span class="badge ${statusClass}">${getStatusText(project.status)}</span>
                        </div>
                        
                        <p class="text-muted small mb-2">
                            <i class="fas fa-user-tie me-1"></i>
                            ${project.client?.name || 'Sin cliente'}
                        </p>
                        
                        <div class="progress mb-2" style="height: 6px;">
                            <div class="progress-bar bg-primary" style="width: ${progress}%"></div>
                        </div>
                        <small class="text-muted">${progress}% completado</small>
                        
                        <div class="mt-3">
                            <button class="btn btn-primary btn-sm w-100 open-kanban-btn" 
                                    data-project-id="${project.id}" 
                                    data-project-name="${project.name}">
                                <i class="fas fa-columns me-1"></i>
                                Abrir Kanban
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Evento para abrir kanban
        const openBtn = col.querySelector('.open-kanban-btn');
        openBtn.addEventListener('click', function() {
            const projectId = this.dataset.projectId;
            const projectName = this.dataset.projectName;
            openProjectKanban(projectId, projectName);
        });

        return col;
    }

    // Abrir kanban del proyecto
    function openProjectKanban(projectId, projectName) {
        // Cerrar modal
        const modal = bootstrap.Modal.getInstance(kanbanProjectsModal);
        if (modal) modal.hide();
        
        // Redirigir al kanban
        window.location.href = `/projects/${projectId}/kanban/`;
    }

    // Filtrar proyectos
    function filterProjects() {
        const searchTerm = projectSearchInput?.value.toLowerCase() || '';
        const statusFilterValue = statusFilter?.value || '';
        const clientFilterValue = clientFilter?.value || '';

        const projectCards = projectsGrid.querySelectorAll('.project-card-kanban');
        
        projectCards.forEach(card => {
            const projectName = card.querySelector('.card-title').textContent.toLowerCase();
            const projectStatus = card.querySelector('.badge').textContent.toLowerCase();
            const projectClient = card.querySelector('.text-muted small')?.textContent.toLowerCase() || '';

            const matchesSearch = projectName.includes(searchTerm);
            const matchesStatus = !statusFilterValue || projectStatus.includes(statusFilterValue);
            const matchesClient = !clientFilterValue || projectClient.includes(clientFilterValue);

            if (matchesSearch && matchesStatus && matchesClient) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }

    // Poblar filtro de clientes
    function populateClientFilter(clients) {
        if (!clientFilter) return;
        
        clientFilter.innerHTML = '<option value="">Todos los clientes</option>';
        clients.forEach(client => {
            const option = document.createElement('option');
            option.value = client.name.toLowerCase();
            option.textContent = client.name;
            clientFilter.appendChild(option);
        });
    }

    // Utilidades
    function getStatusClass(status) {
        const statusMap = {
            'active': 'bg-success',
            'completed': 'bg-primary',
            'on_hold': 'bg-warning',
            'cancelled': 'bg-danger'
        };
        return statusMap[status] || 'bg-secondary';
    }

    function getStatusText(status) {
        const statusMap = {
            'active': 'Activo',
            'completed': 'Completado',
            'on_hold': 'En Pausa',
            'cancelled': 'Cancelado'
        };
        return statusMap[status] || status;
    }

    function debounce(func, wait) {
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
});