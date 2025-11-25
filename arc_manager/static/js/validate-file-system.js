/**
 * Script de Validación del Sistema de Archivos
 * Verifica que todos los componentes estén cargados correctamente
 * Se ejecuta automáticamente en desarrollo para debugging
 */

(function() {
    'use strict';
    
    // Solo ejecutar en modo desarrollo
    const isDevelopment = window.location.hostname === 'localhost' || 
                          window.location.hostname === '127.0.0.1' ||
                          window.location.search.includes('debug=true');
    
    if (!isDevelopment) {
        return; // No ejecutar en producción
    }
    
    console.log('%c🔍 Validación del Sistema de Archivos', 'color: #3b82f6; font-weight: bold; font-size: 14px;');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    
    let allTestsPassed = true;
    
    // Test 1: FileDeleteManager
    if (typeof FileDeleteManager !== 'undefined') {
        console.log('✅ FileDeleteManager class definida');
    } else {
        console.error('❌ FileDeleteManager class NO definida');
        allTestsPassed = false;
    }
    
    if (window.fileDeleteManager) {
        console.log('✅ window.fileDeleteManager instancia creada');
    } else {
        console.warn('⚠️ window.fileDeleteManager NO instanciado aún');
    }
    
    // Test 2: Funciones de filtros
    if (typeof window.applyFileFilters === 'function') {
        console.log('✅ window.applyFileFilters definida');
    } else {
        console.error('❌ window.applyFileFilters NO definida');
        allTestsPassed = false;
    }
    
    if (typeof window.clearFileFilters === 'function') {
        console.log('✅ window.clearFileFilters definida');
    } else {
        console.error('❌ window.clearFileFilters NO definida');
        allTestsPassed = false;
    }
    
    // Test 3: FileListUpdater
    if (typeof FileListUpdater !== 'undefined') {
        console.log('✅ FileListUpdater class definida');
    } else {
        console.error('❌ FileListUpdater class NO definida');
        allTestsPassed = false;
    }
    
    if (window.fileListUpdater) {
        console.log('✅ window.fileListUpdater instancia creada');
    } else {
        console.warn('⚠️ window.fileListUpdater NO instanciado aún');
    }
    
    // Test 4: LargeFileUploader
    if (typeof LargeFileUploader !== 'undefined') {
        console.log('✅ LargeFileUploader class definida');
    } else {
        console.error('❌ LargeFileUploader class NO definida');
        allTestsPassed = false;
    }
    
    // Test 5: HTMX
    if (typeof htmx !== 'undefined') {
        console.log('✅ HTMX cargado');
        
        if (typeof htmx.ajax === 'function') {
            console.log('✅ htmx.ajax disponible');
        } else {
            console.error('❌ htmx.ajax NO disponible');
            allTestsPassed = false;
        }
    } else {
        console.error('❌ HTMX NO cargado');
        allTestsPassed = false;
    }
    
    // Test 6: Bootstrap
    if (typeof bootstrap !== 'undefined') {
        console.log('✅ Bootstrap cargado');
        
        if (typeof bootstrap.Modal !== 'undefined') {
            console.log('✅ Bootstrap Modal disponible');
        } else {
            console.error('❌ Bootstrap Modal NO disponible');
            allTestsPassed = false;
        }
    } else {
        console.error('❌ Bootstrap NO cargado');
        allTestsPassed = false;
    }
    
    // Test 7: Sistema de notificaciones
    if (window.notifications || window.showGlobalNotification) {
        console.log('✅ Sistema de notificaciones disponible');
    } else {
        console.warn('⚠️ Sistema de notificaciones NO disponible (usará fallback)');
    }
    
    // Test 8: Botones de eliminar en DOM
    const deleteButtons = document.querySelectorAll('.file-delete-btn, button[hx-post*="/files/delete/"]');
    console.log(`📊 Botones de eliminar encontrados: ${deleteButtons.length}`);
    
    // Test 9: Filtros en DOM
    const filterElements = document.querySelectorAll('[id^="fileTypeFilter-"], [id^="fileDateFilter-"]');
    console.log(`📊 Elementos de filtro encontrados: ${filterElements.length}`);
    
    // Test 10: Contenedores de archivos
    const fileContainers = document.querySelectorAll('[id^="files-container-"], [id^="files-grid-"]');
    console.log(`📊 Contenedores de archivos encontrados: ${fileContainers.length}`);
    
    // Test 11: Modal de eliminación
    const deleteModal = document.getElementById('fileDeleteModal');
    if (deleteModal) {
        console.log('✅ Modal de eliminación encontrado en DOM');
    } else {
        console.warn('⚠️ Modal de eliminación NO encontrado en DOM (se creará al cargar FileDeleteManager)');
    }
    
    // Test 12: CSRF Token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfToken && csrfToken.value) {
        console.log('✅ CSRF Token presente');
    } else {
        console.error('❌ CSRF Token NO encontrado');
        allTestsPassed = false;
    }
    
    // Resumen
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    if (allTestsPassed) {
        console.log('%c✅ TODOS LOS TESTS PASARON', 'color: #10b981; font-weight: bold; font-size: 14px;');
        console.log('Sistema de archivos correctamente inicializado');
    } else {
        console.log('%c❌ ALGUNOS TESTS FALLARON', 'color: #ef4444; font-weight: bold; font-size: 14px;');
        console.log('Revisa los errores arriba para más detalles');
    }
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    
    // Agregar helper para testing manual
    window.testFileSystem = function() {
        console.log('🧪 Iniciando test manual...');
        
        // Test de filtros
        const phaseIds = [];
        document.querySelectorAll('[id^="fileTypeFilter-"]').forEach(el => {
            const id = el.id.replace('fileTypeFilter-', '');
            phaseIds.push(id);
        });
        
        if (phaseIds.length > 0) {
            console.log(`Encontradas ${phaseIds.length} fases con filtros`);
            console.log(`Para probar filtros, ejecuta: window.applyFileFilters(${phaseIds[0]})`);
        }
        
        // Test de eliminación
        const deleteBtn = document.querySelector('.file-delete-btn');
        if (deleteBtn) {
            console.log('Para probar eliminación, haz click en cualquier botón de eliminar');
        } else {
            console.log('No se encontraron botones de eliminar en la página actual');
        }
        
        return {
            phaseIds,
            deleteButtonsCount: document.querySelectorAll('.file-delete-btn').length,
            filtersCount: document.querySelectorAll('[id^="fileTypeFilter-"]').length,
            containersCount: document.querySelectorAll('[id^="files-container-"]').length
        };
    };
    
    console.log('💡 Tip: Ejecuta window.testFileSystem() para test manual');
    
})();

