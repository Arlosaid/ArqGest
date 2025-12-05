/**
 * Finance Module - Unified JavaScript
 * Combina finance_dashboard_bootstrap.js, finance_payment_form.js y finance_dashboard.js
 */

document.addEventListener('DOMContentLoaded', function() {
    'use strict';
    
    // ========================================
    // INICIALIZACIÓN GENERAL
    // ========================================
    
    // Inicializar tooltips de Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // ========================================
    // FUNCIONALIDADES DEL DASHBOARD
    // ========================================
    
    // Auto-submit del formulario de filtros
    const filterForm = document.querySelector('form[method="get"]');
    if (filterForm) {
        const selectElements = filterForm.querySelectorAll('select');
        selectElements.forEach(select => {
            select.addEventListener('change', function() {
                filterForm.submit();
            });
        });
    }
    
    // Búsqueda con debounce
    const searchInput = document.querySelector('.table-search-input, .finance-search-input');
    const searchForm = document.querySelector('.table-search-box, .finance-filters-container');
    
    if (searchInput && searchForm) {
        let searchTimeout;
        let isSearching = false;
        
        searchInput.addEventListener('input', function() {
            if (isSearching) return;
            if (searchTimeout) clearTimeout(searchTimeout);
            searchTimeout = setTimeout(function() {
                isSearching = true;
                const icon = document.querySelector('.table-search-icon, .finance-search-icon');
                if (icon) icon.className = 'fas fa-spinner fa-spin table-search-icon';
                try { 
                    searchForm.submit(); 
                } finally { 
                    isSearching = false; 
                }
            }, 500);
        });
        
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && this.value) {
                this.value = '';
                if (searchTimeout) clearTimeout(searchTimeout);
                searchForm.submit();
            }
        });
    }
    
    // Filtro de estado de presupuesto
    const budgetFilter = document.querySelector('.budget-status-filter');
    if (budgetFilter && searchForm) {
        budgetFilter.addEventListener('change', function() {
            searchForm.submit();
        });
    }
    
    // ========================================
    // ANIMACIONES Y EFECTOS VISUALES
    // ========================================
    
    // Animaciones de entrada para las métricas
    const metricCards = document.querySelectorAll('.finance-metric-card, .summary-item');
    if (metricCards.length > 0) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, { threshold: 0.1 });
        
        metricCards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = `opacity 0.6s ease ${index * 0.1}s, transform 0.6s ease ${index * 0.1}s`;
            observer.observe(card);
        });
    }
    
    // Efectos hover para las cards de métricas
    metricCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-4px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Animación de progreso bars
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(bar => {
        const width = bar.style.width;
        bar.style.width = '0%';
        
        setTimeout(() => {
            bar.style.width = width;
        }, 500);
    });
    
    // ========================================
    // FUNCIONALIDADES DE FORMULARIOS
    // ========================================
    
    // Validación de formulario de pago
    const paymentFormContainer = document.getElementById('paymentFormContainer');
    if (paymentFormContainer) {
        const remaining = parseFloat(paymentFormContainer.getAttribute('data-remaining')) || 0;
        const amountInputId = paymentFormContainer.getAttribute('data-amount-input-id');
        const dateInputId = paymentFormContainer.getAttribute('data-date-input-id');
        
        const amountInput = amountInputId ? document.getElementById(amountInputId) : null;
        const feedback = document.getElementById('amount-feedback');
        
        if (amountInput && feedback) {
            // Hints para móviles y evitar formatos localizados
            amountInput.setAttribute('inputmode', 'decimal');
            amountInput.setAttribute('step', '0.01');
            amountInput.setAttribute('autocomplete', 'off');
            
            amountInput.addEventListener('input', function() {
                // Normalizar: quitar espacios (incl. NBSP) y cambiar coma por punto
                const normalized = (this.value || '')
                    .replace(/[\s\u00A0]/g, '')
                    .replace(/,/g, '.');
                const amount = parseFloat(normalized) || 0;
                if (amount > remaining) {
                    feedback.innerHTML = '<span class="error">Monto excede el máximo disponible</span>';
                } else if (amount > 0) {
                    feedback.innerHTML = '<span class="success">✓ Monto válido</span>';
                } else {
                    feedback.innerHTML = '';
                }
            });
        }
        
        const dateInput = dateInputId ? document.getElementById(dateInputId) : null;
        if (dateInput && !dateInput.value) {
            const today = new Date().toISOString().split('T')[0];
            dateInput.value = today;
        }
    }
    
    // ========================================
    // AUTO-REFRESH Y GESTIÓN DE ESTADO
    // ========================================
    
    // Auto-refresh de métricas (opcional)
    const refreshInterval = 300000; // 5 minutos
    let refreshTimer;
    
    function startAutoRefresh() {
        refreshTimer = setInterval(() => {
            // Solo refrescar si no hay interacción del usuario
            if (!document.hidden) {
                location.reload();
            }
        }, refreshInterval);
    }
    
    function stopAutoRefresh() {
        if (refreshTimer) {
            clearInterval(refreshTimer);
        }
    }
    
    // Controlar auto-refresh basado en visibilidad de la página
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            stopAutoRefresh();
        } else {
            startAutoRefresh();
        }
    });
    
    // Iniciar auto-refresh
    startAutoRefresh();
    
    // Limpiar al salir de la página
    window.addEventListener('beforeunload', stopAutoRefresh);
    
    // ========================================
    // MEJORAS DE ACCESIBILIDAD
    // ========================================
    
    const actionButtons = document.querySelectorAll('.btn[data-bs-toggle="tooltip"]');
    actionButtons.forEach(button => {
        button.addEventListener('focus', function() {
            this.style.outline = '2px solid #4F46E5';
            this.style.outlineOffset = '2px';
        });
        
        button.addEventListener('blur', function() {
            this.style.outline = '';
            this.style.outlineOffset = '';
        });
    });
    
    // ========================================
    // LOADING STATES Y NAVEGACIÓN
    // ========================================
    
    // Loading states para botones de acción
    const actionLinks = document.querySelectorAll('a[href*="payment-create"], a[href*="budget-config"]');
    actionLinks.forEach(link => {
        link.addEventListener('click', function() {
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Cargando...';
            this.style.pointerEvents = 'none';
            
            // Restaurar después de 3 segundos si no hay redirección
            setTimeout(() => {
                this.innerHTML = originalText;
                this.style.pointerEvents = '';
            }, 3000);
        });
    });
    
    // Smooth scroll para paginación
    const paginationLinks = document.querySelectorAll('.pagination a');
    paginationLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const href = this.getAttribute('href');
            
            // Animación de salida
            document.body.style.opacity = '0.8';
            document.body.style.transition = 'opacity 0.3s ease';
            
            setTimeout(() => {
                window.location.href = href;
            }, 300);
        });
    });
    
    // ========================================
    // RESPONSIVE Y TABLAS
    // ========================================
    
    // Responsive table enhancements
    function handleTableResponsive() {
        const tables = document.querySelectorAll('.table-responsive');
        tables.forEach(table => {
            const isOverflowing = table.scrollWidth > table.clientWidth;
            
            if (isOverflowing) {
                table.style.border = '1px solid #dee2e6';
                table.style.borderRadius = '0.375rem';
            }
        });
    }
    
    // Ejecutar al cargar y redimensionar
    handleTableResponsive();
    window.addEventListener('resize', handleTableResponsive);
    
    // ========================================
    // FUNCIONALIDADES ESPECÍFICAS
    // ========================================
    
    // Funcionalidades de filtros ya implementadas en el template
    // Los filtros de búsqueda y estado de presupuesto están funcionando
    
    // ========================================
    // UTILIDADES ADICIONALES
    // ========================================
    
    // Formateo de números para inputs de moneda
    const currencyInputs = document.querySelectorAll('input[type="number"][step="0.01"]');
    currencyInputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value) {
                const value = parseFloat(this.value);
                if (!isNaN(value)) {
                    this.value = value.toFixed(2);
                }
            }
        });
    });
    
    // Validación de archivos
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const maxSize = 5 * 1024 * 1024; // 5MB
                if (file.size > maxSize) {
                    if (window.notifications) {
                        window.notifications.error('El archivo es demasiado grande. Máximo 5MB.');
                    } else {
                        alert('El archivo es demasiado grande. Máximo 5MB.');
                    }
                    this.value = '';
                    return;
                }
                
                // Validar extensión permitida
                const allowedExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx'];
                const fileName = file.name.toLowerCase();
                const hasValidExtension = allowedExtensions.some(ext => fileName.endsWith(ext));
                
                if (!hasValidExtension) {
                    if (window.notifications) {
                        window.notifications.error('Tipo de archivo no permitido. Se permiten: PDF, Imágenes (JPG, PNG) y documentos Word (DOC, DOCX).');
                    } else {
                        alert('Tipo de archivo no permitido. Se permiten: PDF, Imágenes (JPG, PNG) y documentos Word (DOC, DOCX).');
                    }
                    this.value = '';
                    return;
                }
            }
        });
    });
});
