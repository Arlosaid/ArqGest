// Filtrado de archivos optimizado con HTMX
document.addEventListener('DOMContentLoaded', function() {
    // Configurar filtros inmediatamente
    setupFileFilters();
    
    // IMPORTANTE: Usar delegación de eventos para el botón de limpiar
    // Esto asegura que funcione incluso si el DOM cambia
    document.body.addEventListener('click', function(e) {
        const clearBtn = e.target.closest('[id^="clearFilters-"]');
        if (clearBtn) {
            e.preventDefault();
            e.stopPropagation();
            const phaseId = clearBtn.id.replace('clearFilters-', '');
            clearFilters(phaseId);
            return false;
        }
    }, true); // Usar capture phase para mayor prioridad
    
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
    
    // NOTA: El botón de limpiar ahora usa delegación de eventos en el body
    // por lo que no necesitamos configurarlo aquí
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
        
        // Reinicializar event listeners en el nuevo contenido
        if (window.htmx) {
            htmx.process(container);
        }
    })
    .catch((error) => {
        hideFilterLoadingIndicator(container);
        
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

function clearFilters(phaseId) {
    const typeFilter = document.getElementById(`fileTypeFilter-${phaseId}`);
    const dateFilter = document.getElementById(`fileDateFilter-${phaseId}`);
    const container = document.getElementById(`files-container-${phaseId}`);
    
    // Resetear valores de los filtros
    if (typeFilter) {
        typeFilter.value = '';
        typeFilter.selectedIndex = 0;
    }
    if (dateFilter) {
        dateFilter.value = '';
        dateFilter.selectedIndex = 0;
    }
    
    // Verificar que el contenedor existe
    if (!container) {
        return;
    }
    
    // Obtener la URL base del contenedor
    const hxGetAttr = container.getAttribute('hx-get');
    if (!hxGetAttr) {
        return;
    }
    
    const baseUrl = hxGetAttr.split('?')[0];
    
    // Construir URL sin filtros
    const url = `${baseUrl}?offset=0&limit=18`;
    
    // Actualizar el atributo hx-get del contenedor
    container.setAttribute('hx-get', url);
    
    // Mostrar indicador de carga
    showFilterLoadingIndicator(container);
    
    // Usar fetch para recargar los archivos sin filtros
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
        
        // Reinicializar event listeners en el nuevo contenido
        if (window.htmx) {
            htmx.process(container);
        }
    })
    .catch((error) => {
        hideFilterLoadingIndicator(container);
        
        // Mostrar notificación de error
        if (window.notifications) {
            window.notifications.error('Error al limpiar filtros');
        }
    });
}

// Funciones globales para compatibilidad
window.applyFileFilters = applyFilters;
window.clearFileFilters = clearFilters;
