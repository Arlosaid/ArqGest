/**
 * Script de Validación del Sistema de Archivos
 * Verifica que todos los componentes estén cargados correctamente
 * Se ejecuta automáticamente en desarrollo para debugging
 */

(function() {
    'use strict';
    
    // Solo ejecutar en modo desarrollo con flag explícito
    const debugEnabled = window.location.search.includes('debug=file-system');
    
    if (!debugEnabled) {
        return; // No ejecutar validaciones
    }
    
    // Validación silenciosa - solo reportar errores críticos
    let criticalErrors = [];
    
    // Verificar dependencias críticas
    if (typeof FileDeleteManager === 'undefined') {
        criticalErrors.push('FileDeleteManager no definida');
    }
    if (typeof FileListUpdater === 'undefined') {
        criticalErrors.push('FileListUpdater no definida');
    }
    if (typeof htmx === 'undefined') {
        criticalErrors.push('HTMX no cargado');
    }
    if (typeof bootstrap === 'undefined') {
        criticalErrors.push('Bootstrap no cargado');
    }
    
    // Solo reportar si hay errores críticos
    if (criticalErrors.length > 0) {
        console.error('❌ Errores críticos del sistema de archivos:', criticalErrors);
    }
    
    // Agregar helper para testing manual (solo si debug está activado)
    window.testFileSystem = function() {
        const phaseIds = [];
        document.querySelectorAll('[id^="fileTypeFilter-"]').forEach(el => {
            phaseIds.push(el.id.replace('fileTypeFilter-', ''));
        });
        
        return {
            phaseIds,
            deleteButtonsCount: document.querySelectorAll('.file-delete-btn').length,
            filtersCount: document.querySelectorAll('[id^="fileTypeFilter-"]').length,
            containersCount: document.querySelectorAll('[id^="files-container-"]').length,
            hasFileDeleteManager: typeof FileDeleteManager !== 'undefined',
            hasFileListUpdater: typeof FileListUpdater !== 'undefined',
            hasHTMX: typeof htmx !== 'undefined',
            hasBootstrap: typeof bootstrap !== 'undefined'
        };
    };
})();

