// Filtrado de archivos optimizado con HTMX
document.addEventListener('DOMContentLoaded', function() {
    console.log('🗂️ Filtros de archivos inicializados');
    
    // Configurar filtros para todas las fases
    setupFileFilters();
    
    // Reconfigurar filtros cuando se actualiza contenido dinámico
    document.body.addEventListener('htmx:afterSettle', function(event) {
        if (event.target.id && event.target.id.includes('files-container')) {
            setupFileFilters();
        }
    });
});

function setupFileFilters() {
    // Configurar filtros por tipo
    document.querySelectorAll('[id^="fileTypeFilter-"]').forEach(filter => {
        const phaseId = filter.id.replace('fileTypeFilter-', '');
        
        // Remover listeners anteriores para evitar duplicados
        filter.removeEventListener('change', filter._filterHandler);
        
        // Crear y asignar nuevo handler
        filter._filterHandler = () => applyFilters(phaseId);
        filter.addEventListener('change', filter._filterHandler);
    });
    
    // Configurar filtros por fecha
    document.querySelectorAll('[id^="fileDateFilter-"]').forEach(filter => {
        const phaseId = filter.id.replace('fileDateFilter-', '');
        
        filter.removeEventListener('change', filter._filterHandler);
        filter._filterHandler = () => applyFilters(phaseId);
        filter.addEventListener('change', filter._filterHandler);
    });
    
    // Configurar botones de limpiar
    document.querySelectorAll('[id^="clearFilters-"]').forEach(button => {
        const phaseId = button.id.replace('clearFilters-', '');
        
        button.removeEventListener('click', button._clearHandler);
        button._clearHandler = () => clearFilters(phaseId);
        button.addEventListener('click', button._clearHandler);
    });
}

function applyFilters(phaseId) {
    const typeFilter = document.getElementById(`fileTypeFilter-${phaseId}`);
    const dateFilter = document.getElementById(`fileDateFilter-${phaseId}`);
    const container = document.getElementById(`files-container-${phaseId}`);
    
    if (!typeFilter || !dateFilter || !container) {
        console.warn(`No se encontraron elementos de filtro para fase ${phaseId}`);
        return;
    }
    
    const typeValue = typeFilter.value;
    const dateValue = dateFilter.value;
    
    // Construir URL con filtros
    const baseUrl = container.getAttribute('hx-get').split('?')[0];
    let url = `${baseUrl}?offset=0&limit=20`;
    
    if (typeValue) {
        url += `&type=${encodeURIComponent(typeValue)}`;
    }
    
    if (dateValue) {
        url += `&date=${encodeURIComponent(dateValue)}`;
    }
    
    console.log(`🔍 Aplicando filtros para fase ${phaseId}:`, { type: typeValue, date: dateValue });
    
    // Actualizar el atributo hx-get del contenedor
    container.setAttribute('hx-get', url);
    
    // Trigger HTMX reload
    htmx.trigger(container, 'load');
}

function clearFilters(phaseId) {
    const typeFilter = document.getElementById(`fileTypeFilter-${phaseId}`);
    const dateFilter = document.getElementById(`fileDateFilter-${phaseId}`);
    
    if (typeFilter) typeFilter.value = '';
    if (dateFilter) dateFilter.value = '';
    
    console.log(`🧹 Limpiando filtros para fase ${phaseId}`);
    
    // Aplicar filtros vacíos
    applyFilters(phaseId);
}

// Funciones globales para compatibilidad
window.applyFileFilters = applyFilters;
window.clearFileFilters = clearFilters;
