/**
 * PROYECTOS - FUNCIONALIDADES JAVASCRIPT
 * ======================================
 * 
 * Este archivo contiene todas las funcionalidades JavaScript específicas
 * para la gestión de proyectos en ArcManager.
 */

class ProjectsManager {
    constructor() {
        this.init();
    }

    /**
     * Inicializa todas las funcionalidades de proyectos
     */
    init() {
        this.initAnimations();
        this.initDeleteConfirmations();
        this.initFilters();
        this.initSearch();
        this.initTooltips();
        this.initProgressBars();
        this.initFormValidation();
        this.initResponsiveBehavior();
    }

    /**
     * ANIMACIONES DE CARDS
     * ===================
     */
    initAnimations() {
        // Animación de entrada para cards de proyectos
        this.animateProjectCards();
        
        // Animación de hover para cards
        this.initCardHoverEffects();
        
        // Animación de botones
        this.initButtonAnimations();
    }

    /**
     * Anima las cards de proyectos al cargar la página
     */
    animateProjectCards() {
        const projectCards = document.querySelectorAll('.project-card');
        
        if (projectCards.length === 0) return;

        // Configurar observador de intersección para animaciones
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry, index) => {
                if (entry.isIntersecting) {
                    entry.target.style.animationDelay = `${index * 0.1}s`;
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });

        // Aplicar animación a cada card
        projectCards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            observer.observe(card);
        });
    }

    /**
     * Inicializa efectos hover para las cards
     */
    initCardHoverEffects() {
        const projectCards = document.querySelectorAll('.project-card');
        
        projectCards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-4px)';
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0)';
            });
        });
    }

    /**
     * Inicializa animaciones para botones
     */
    initButtonAnimations() {
        const buttons = document.querySelectorAll('.btn-project-action');
        
        buttons.forEach(button => {
            button.addEventListener('click', (e) => {
                // Efecto de ripple
                const ripple = document.createElement('span');
                const rect = button.getBoundingClientRect();
                const size = Math.max(rect.width, rect.height);
                const x = e.clientX - rect.left - size / 2;
                const y = e.clientY - rect.top - size / 2;
                
                ripple.style.width = ripple.style.height = size + 'px';
                ripple.style.left = x + 'px';
                ripple.style.top = y + 'px';
                ripple.classList.add('ripple');
                
                button.appendChild(ripple);
                
                setTimeout(() => {
                    ripple.remove();
                }, 600);
            });
        });
    }

    /**
     * CONFIRMACIONES DE ELIMINACIÓN
     * =============================
     */
    initDeleteConfirmations() {
        const deleteButtons = document.querySelectorAll('.btn-project-delete');
        
        deleteButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.showDeleteConfirmation(button);
            });
        });
    }

    /**
     * Muestra modal de confirmación de eliminación
     */
    showDeleteConfirmation(button) {
        const projectName = button.closest('.project-card')?.querySelector('.project-card-title')?.textContent || 'este proyecto';
        
        // Crear modal de confirmación
        const modal = document.createElement('div');
        modal.className = 'delete-confirmation-modal';
        modal.innerHTML = `
            <div class="modal-overlay"></div>
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Confirmar Eliminación</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <p>¿Estás seguro de que quieres eliminar <strong>${projectName}</strong>?</p>
                    <p class="text-muted">Esta acción no se puede deshacer.</p>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary cancel-btn">Cancelar</button>
                    <button class="btn btn-danger confirm-btn">Eliminar</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        
        // Mostrar modal con animación
        setTimeout(() => {
            modal.classList.add('show');
        }, 10);

        // Event listeners para el modal
        modal.querySelector('.modal-close').addEventListener('click', () => {
            this.closeModal(modal);
        });

        modal.querySelector('.cancel-btn').addEventListener('click', () => {
            this.closeModal(modal);
        });

        modal.querySelector('.confirm-btn').addEventListener('click', () => {
            this.executeDelete(button, modal);
        });

        // Cerrar al hacer clic fuera del modal
        modal.querySelector('.modal-overlay').addEventListener('click', () => {
            this.closeModal(modal);
        });
    }

    /**
     * Cierra el modal de confirmación
     */
    closeModal(modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.remove();
        }, 300);
    }

    /**
     * Ejecuta la eliminación del proyecto
     */
    executeDelete(button, modal) {
        const projectCard = button.closest('.project-card');
        const deleteUrl = button.getAttribute('href') || button.dataset.deleteUrl;
        
        if (!deleteUrl) {
            console.error('URL de eliminación no encontrada');
            this.closeModal(modal);
            return;
        }

        // Mostrar estado de carga
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Eliminando...';

        // Realizar petición de eliminación
        fetch(deleteUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCSRFToken(),
                'Content-Type': 'application/json',
            },
        })
        .then(response => {
            if (response.ok) {
                // Animación de eliminación
                projectCard.style.transform = 'scale(0.8)';
                projectCard.style.opacity = '0';
                
                setTimeout(() => {
                    projectCard.remove();
                    this.showNotification('Proyecto eliminado correctamente', 'success');
                }, 300);
            } else {
                throw new Error('Error al eliminar el proyecto');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            this.showNotification('Error al eliminar el proyecto', 'error');
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-trash"></i> Eliminar';
        })
        .finally(() => {
            this.closeModal(modal);
        });
    }

    /**
     * FILTROS DINÁMICOS
     * ==================
     */
    initFilters() {
        const filterForm = document.querySelector('.filters-form');
        if (!filterForm) return;

        const filterInputs = filterForm.querySelectorAll('select, input[type="text"], input[type="date"]');
        
        filterInputs.forEach(input => {
            input.addEventListener('change', () => {
                this.applyFilters();
            });
            
            input.addEventListener('input', this.debounce(() => {
                this.applyFilters();
            }, 300));
        });
    }

    /**
     * Aplica los filtros seleccionados
     */
    applyFilters() {
        const projectCards = document.querySelectorAll('.project-card');
        const searchTerm = document.querySelector('.search-input')?.value.toLowerCase() || '';
        const statusFilter = document.querySelector('select[name="status"]')?.value || '';
        const dateFilter = document.querySelector('input[name="date"]')?.value || '';

        projectCards.forEach(card => {
            let showCard = true;

            // Filtro por búsqueda
            if (searchTerm) {
                const title = card.querySelector('.project-card-title')?.textContent.toLowerCase() || '';
                const description = card.querySelector('.project-card-subtitle')?.textContent.toLowerCase() || '';
                
                if (!title.includes(searchTerm) && !description.includes(searchTerm)) {
                    showCard = false;
                }
            }

            // Filtro por estado
            if (statusFilter && showCard) {
                const status = card.querySelector('.project-status')?.textContent.toLowerCase() || '';
                if (status !== statusFilter.toLowerCase()) {
                    showCard = false;
                }
            }

            // Filtro por fecha
            if (dateFilter && showCard) {
                const projectDate = card.dataset.projectDate || '';
                if (projectDate !== dateFilter) {
                    showCard = false;
                }
            }

            // Mostrar/ocultar card
            if (showCard) {
                card.style.display = 'block';
                card.style.animation = 'projectCardFadeIn 0.3s ease-out';
            } else {
                card.style.display = 'none';
            }
        });

        // Mostrar mensaje si no hay resultados
        this.updateEmptyState();
    }

    /**
     * BÚSQUEDA EN TIEMPO REAL
     * =======================
     */
    initSearch() {
        const searchInput = document.querySelector('.search-input');
        if (!searchInput) return;

        // Búsqueda en tiempo real con debounce
        searchInput.addEventListener('input', this.debounce((e) => {
            const searchTerm = e.target.value.toLowerCase();
            this.performSearch(searchTerm);
        }, 300));

        // Limpiar búsqueda
        const clearSearchBtn = document.querySelector('.clear-search');
        if (clearSearchBtn) {
            clearSearchBtn.addEventListener('click', () => {
                searchInput.value = '';
                this.performSearch('');
                searchInput.focus();
            });
        }
    }

    /**
     * Realiza la búsqueda en tiempo real
     */
    performSearch(searchTerm) {
        const projectCards = document.querySelectorAll('.project-card');
        let visibleCount = 0;

        projectCards.forEach(card => {
            const title = card.querySelector('.project-card-title')?.textContent.toLowerCase() || '';
            const description = card.querySelector('.project-card-subtitle')?.textContent.toLowerCase() || '';
            const tags = card.querySelectorAll('.project-tag') || [];
            
            let matches = title.includes(searchTerm) || description.includes(searchTerm);
            
            // Buscar en tags
            tags.forEach(tag => {
                if (tag.textContent.toLowerCase().includes(searchTerm)) {
                    matches = true;
                }
            });

            if (matches || !searchTerm) {
                card.style.display = 'block';
                card.style.opacity = '1';
                visibleCount++;
                
                // Resaltar términos de búsqueda
                if (searchTerm) {
                    this.highlightSearchTerms(card, searchTerm);
                } else {
                    this.removeHighlighting(card);
                }
            } else {
                card.style.display = 'none';
                card.style.opacity = '0';
            }
        });

        // Actualizar contador de resultados
        this.updateSearchResults(visibleCount, projectCards.length);
    }

    /**
     * Resalta los términos de búsqueda
     */
    highlightSearchTerms(card, searchTerm) {
        const title = card.querySelector('.project-card-title');
        const description = card.querySelector('.project-card-subtitle');
        
        if (title) {
            title.innerHTML = title.textContent.replace(
                new RegExp(searchTerm, 'gi'),
                match => `<mark class="search-highlight">${match}</mark>`
            );
        }
        
        if (description) {
            description.innerHTML = description.textContent.replace(
                new RegExp(searchTerm, 'gi'),
                match => `<mark class="search-highlight">${match}</mark>`
            );
        }
    }

    /**
     * Remueve el resaltado de búsqueda
     */
    removeHighlighting(card) {
        const highlights = card.querySelectorAll('.search-highlight');
        highlights.forEach(highlight => {
            highlight.outerHTML = highlight.textContent;
        });
    }

    /**
     * TOOLTIPS INFORMATIVOS
     * =====================
     */
    initTooltips() {
        // Inicializar tooltips de Bootstrap si está disponible
        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
            const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
        }

        // Tooltips personalizados para elementos específicos
        this.initCustomTooltips();
    }

    /**
     * Inicializa tooltips personalizados
     */
    initCustomTooltips() {
        const tooltipElements = document.querySelectorAll('[data-tooltip]');
        
        tooltipElements.forEach(element => {
            element.addEventListener('mouseenter', (e) => {
                this.showCustomTooltip(e.target, e.target.dataset.tooltip);
            });
            
            element.addEventListener('mouseleave', () => {
                this.hideCustomTooltip();
            });
        });
    }

    /**
     * Muestra tooltip personalizado
     */
    showCustomTooltip(element, text) {
        const tooltip = document.createElement('div');
        tooltip.className = 'custom-tooltip';
        tooltip.textContent = text;
        
        document.body.appendChild(tooltip);
        
        const rect = element.getBoundingClientRect();
        tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
        tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
        
        setTimeout(() => {
            tooltip.classList.add('show');
        }, 10);
    }

    /**
     * Oculta tooltip personalizado
     */
    hideCustomTooltip() {
        const tooltip = document.querySelector('.custom-tooltip');
        if (tooltip) {
            tooltip.classList.remove('show');
            setTimeout(() => {
                tooltip.remove();
            }, 200);
        }
    }

    /**
     * INDICADORES DE PROGRESO
     * =======================
     */
    initProgressBars() {
        const progressBars = document.querySelectorAll('.progress-bar');
        
        progressBars.forEach(bar => {
            const percentage = bar.dataset.progress || '0';
            this.animateProgressBar(bar, percentage);
        });
    }

    /**
     * Anima las barras de progreso
     */
    animateProgressBar(bar, targetPercentage) {
        let currentPercentage = 0;
        const increment = targetPercentage / 50; // 50 pasos para la animación
        
        const animation = setInterval(() => {
            currentPercentage += increment;
            
            if (currentPercentage >= targetPercentage) {
                currentPercentage = targetPercentage;
                clearInterval(animation);
            }
            
            bar.style.width = currentPercentage + '%';
        }, 20);
    }

    /**
     * VALIDACIÓN DE FORMULARIOS
     * =========================
     */
    initFormValidation() {
        const projectForm = document.querySelector('.project-form form');
        if (!projectForm) return;

        const requiredFields = projectForm.querySelectorAll('[required]');
        
        requiredFields.forEach(field => {
            field.addEventListener('blur', () => {
                this.validateField(field);
            });
            
            field.addEventListener('input', () => {
                this.clearFieldError(field);
            });
        });

        // Validación al enviar el formulario
        projectForm.addEventListener('submit', (e) => {
            if (!this.validateForm(projectForm)) {
                e.preventDefault();
            }
        });
    }

    /**
     * Valida un campo específico
     */
    validateField(field) {
        const value = field.value.trim();
        const isRequired = field.hasAttribute('required');
        
        if (isRequired && !value) {
            this.showFieldError(field, 'Este campo es obligatorio');
            return false;
        }
        
        // Validaciones específicas por tipo
        if (field.type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                this.showFieldError(field, 'Ingresa un email válido');
                return false;
            }
        }
        
        if (field.type === 'url' && value) {
            const urlRegex = /^https?:\/\/.+/;
            if (!urlRegex.test(value)) {
                this.showFieldError(field, 'Ingresa una URL válida');
                return false;
            }
        }
        
        this.clearFieldError(field);
        return true;
    }

    /**
     * Muestra error en un campo
     */
    showFieldError(field, message) {
        this.clearFieldError(field);
        
        field.classList.add('is-invalid');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        
        field.parentNode.appendChild(errorDiv);
    }

    /**
     * Limpia error de un campo
     */
    clearFieldError(field) {
        field.classList.remove('is-invalid');
        
        const errorDiv = field.parentNode.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    /**
     * Valida todo el formulario
     */
    validateForm(form) {
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });
        
        return isValid;
    }

    /**
     * COMPORTAMIENTO RESPONSIVE
     * =========================
     */
    initResponsiveBehavior() {
        // Ajustar grid en diferentes tamaños de pantalla
        this.adjustGridLayout();
        
        // Event listener para cambios de tamaño de ventana
        window.addEventListener('resize', this.debounce(() => {
            this.adjustGridLayout();
        }, 250));
    }

    /**
     * Ajusta el layout del grid según el tamaño de pantalla
     */
    adjustGridLayout() {
        const projectsGrid = document.querySelector('.projects-grid');
        if (!projectsGrid) return;

        const width = window.innerWidth;
        
        if (width < 768) {
            projectsGrid.style.gridTemplateColumns = '1fr';
        } else if (width < 1200) {
            projectsGrid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(350px, 1fr))';
        } else {
            projectsGrid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(400px, 1fr))';
        }
    }

    /**
     * UTILIDADES
     * ==========
     */
    
    /**
     * Función debounce para optimizar eventos
     */
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

    /**
     * Obtiene el token CSRF
     */
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1] || '';
    }

    /**
     * Muestra notificaciones
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;

        document.body.appendChild(notification);
        
        // Mostrar con animación
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);

        // Auto-ocultar después de 5 segundos
        setTimeout(() => {
            this.hideNotification(notification);
        }, 5000);

        // Cerrar manualmente
        notification.querySelector('.notification-close').addEventListener('click', () => {
            this.hideNotification(notification);
        });
    }

    /**
     * Oculta notificación
     */
    hideNotification(notification) {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }

    /**
     * Actualiza el estado vacío
     */
    updateEmptyState() {
        const projectCards = document.querySelectorAll('.project-card');
        const visibleCards = Array.from(projectCards).filter(card => 
            card.style.display !== 'none'
        );
        
        const emptyState = document.querySelector('.empty-projects');
        
        if (visibleCards.length === 0 && projectCards.length > 0) {
            if (!emptyState) {
                this.showEmptyState();
            }
        } else {
            if (emptyState) {
                emptyState.remove();
            }
        }
    }

    /**
     * Muestra estado vacío
     */
    showEmptyState() {
        const projectsContainer = document.querySelector('.projects-grid')?.parentNode;
        if (!projectsContainer) return;

        const emptyState = document.createElement('div');
        emptyState.className = 'empty-projects';
        emptyState.innerHTML = `
            <div class="empty-projects-icon">
                <i class="fas fa-folder-open"></i>
            </div>
            <h3 class="empty-projects-title">No se encontraron proyectos</h3>
            <p class="empty-projects-text">Intenta ajustar los filtros o crear un nuevo proyecto.</p>
            <a href="/projects/create/" class="btn btn-primary">
                <i class="fas fa-plus"></i> Crear Proyecto
            </a>
        `;

        projectsContainer.appendChild(emptyState);
    }

    /**
     * Actualiza resultados de búsqueda
     */
    updateSearchResults(visibleCount, totalCount) {
        const resultsCounter = document.querySelector('.search-results-counter');
        
        if (resultsCounter) {
            if (visibleCount === totalCount) {
                resultsCounter.style.display = 'none';
            } else {
                resultsCounter.style.display = 'block';
                resultsCounter.textContent = `Mostrando ${visibleCount} de ${totalCount} proyectos`;
            }
        }
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new ProjectsManager();
});

// Exportar para uso global si es necesario
window.ProjectsManager = ProjectsManager;
