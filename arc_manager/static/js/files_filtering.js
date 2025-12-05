// Filtrado de archivos optimizado con HTMX
document.addEventListener('DOMContentLoaded', function() {
    // Configurar filtros inmediatamente
    setupFileFilters();
    
    // IMPORTANTE: Reconfigurar cuando se carga contenido dinámico (accordions, tabs)
    document.body.addEventListener('htmx:afterSettle', function(event) {
        // Esperar un momento para que el DOM se actualice
        setTimeout(() => {
            setupFileFilters();
        }, 100);
    });
    
    // También configurar cuando se hace swap de contenido
    document.body.addEventListener('htmx:afterSwap', function(event) {
        setTimeout(() => {
            setupFileFilters();
        }, 100);
    });
    
    // Configurar cuando se abre un accordion
    document.addEventListener('shown.bs.collapse', function(event) {
        setTimeout(() => {
            setupFileFilters();
        }, 100);
    });
});

function setupFileFilters() {
    // Configurar filtros por tipo
    const typeFilters = document.querySelectorAll('[id^="fileTypeFilter-"]');
    
    typeFilters.forEach(filter => {
        const phaseId = filter.id.replace('fileTypeFilter-', '');
        
        // Remover listeners anteriores para evitar duplicados
        if (filter._filterHandler) {
            filter.removeEventListener('change', filter._filterHandler);
        }
        
        // Crear y asignar nuevo handler
        filter._filterHandler = () => {
            applyFilters(phaseId);
        };
        filter.addEventListener('change', filter._filterHandler);
    });
    
    // Configurar filtros por fecha
    const dateFilters = document.querySelectorAll('[id^="fileDateFilter-"]');
    
    dateFilters.forEach(filter => {
        const phaseId = filter.id.replace('fileDateFilter-', '');
        
        // Remover listeners anteriores para evitar duplicados
        if (filter._filterHandler) {
            filter.removeEventListener('change', filter._filterHandler);
        }
        
        filter._filterHandler = () => {
            applyFilters(phaseId);
        };
        filter.addEventListener('change', filter._filterHandler);
    });
}

function applyFilters(phaseId) {
    const typeFilter = document.getElementById(`fileTypeFilter-${phaseId}`);
    const dateFilter = document.getElementById(`fileDateFilter-${phaseId}`);
    const container = document.getElementById(`files-container-${phaseId}`);
    
    if (!typeFilter || !dateFilter || !container) {
        return;
    }
    
    const typeValue = typeFilter.value;
    const dateValue = dateFilter.value;
    
    // Obtener la URL base del contenedor
    const hxGetAttr = container.getAttribute('hx-get');
    if (!hxGetAttr) {
        return;
    }
    
    const baseUrl = hxGetAttr.split('?')[0];
    
    // Construir URL con filtros
    let url = `${baseUrl}?offset=0&limit=18`;
    
    if (typeValue) {
        url += `&type=${encodeURIComponent(typeValue)}`;
    }
    
    if (dateValue) {
        url += `&date=${encodeURIComponent(dateValue)}`;
    }
    
    // Actualizar el atributo hx-get del contenedor para futuros reloads
    container.setAttribute('hx-get', url);
    
    // IMPORTANTE: Remover temporalmente el trigger 'load' para evitar re-disparo
    // Guardamos el trigger original y lo reemplazamos con solo 'fileUploaded'
    const originalTrigger = container.getAttribute('hx-trigger');
    container.setAttribute('hx-trigger', 'fileUploaded from:body');
    
    // Mostrar indicador de carga
    showFilterLoadingIndicator(container);
    
    // Usar fetch para cargar los archivos filtrados (compatible con HTMX 1.9.x)
    fetch(url, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'HX-Request': 'true',
            'HX-Target': `files-container-${phaseId}`
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.text();
    })
    .then(html => {
        // Reemplazar contenido del contenedor
        container.innerHTML = html;
        
        hideFilterLoadingIndicator(container);
        
        // Reinicializar HTMX en el nuevo contenido (botones de load more, etc.)
        if (window.htmx) {
            htmx.process(container);
        }
        
        // El trigger ya fue actualizado antes del fetch, no necesita restaurarse
        // porque el nuevo contenido ya tiene el trigger correcto
    })
    .catch((error) => {
        hideFilterLoadingIndicator(container);
        
        // Restaurar trigger original en caso de error
        if (originalTrigger) {
            container.setAttribute('hx-trigger', originalTrigger);
        }
        
        // Mostrar notificación de error
        if (window.notifications) {
            window.notifications.error('Error al aplicar filtros');
        } else {
            alert('Error al aplicar filtros. Por favor, intenta de nuevo.');
        }
    });
}

function showFilterLoadingIndicator(container) {
    // Remover indicador previo si existe
    const existingIndicator = container.querySelector('.filter-loading-indicator');
    if (existingIndicator) {
        existingIndicator.remove();
    }
    
    // Crear indicador de carga
    const indicator = document.createElement('div');
    indicator.className = 'filter-loading-indicator';
    indicator.innerHTML = `
        <div class="d-flex align-items-center justify-content-center py-3">
            <div class="spinner-border spinner-border-sm text-primary me-2" role="status">
                <span class="visually-hidden">Aplicando filtros...</span>
            </div>
            <small class="text-muted">Aplicando filtros...</small>
        </div>
    `;
    
    // Insertar al inicio del contenedor
    const grid = container.querySelector('[id^="files-grid-"]');
    if (grid) {
        grid.insertBefore(indicator, grid.firstChild);
    } else {
        container.insertBefore(indicator, container.firstChild);
    }
}

function hideFilterLoadingIndicator(container) {
    const indicator = container.querySelector('.filter-loading-indicator');
    if (indicator) {
        indicator.remove();
    }
}

// Funciones globales para compatibilidad
window.applyFileFilters = applyFilters;
