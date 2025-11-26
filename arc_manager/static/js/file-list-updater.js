/**
 * 🔄 Sistema de Actualización de Lista de Archivos
 * Maneja la actualización inmediata de listas al subir/eliminar archivos
 */

class FileListUpdater {
    constructor() {
        this.pendingUpdates = new Set();
        this.listenersInitialized = false;
        this.init();
    }

    init() {
        // Solo inicializar listeners una vez para evitar duplicados
        if (!this.listenersInitialized) {
            // Escuchar eventos de archivo subido
            document.body.addEventListener('fileUploaded', (e) => {
                this.updateAllFileLists();
                
                // Si el evento incluye phaseId, incrementar el contador
                if (e.detail && e.detail.phaseId) {
                    this.incrementFileCounter(e.detail.phaseId);
                }
            });

            // Escuchar eventos de archivo eliminado
            document.body.addEventListener('fileDeleted', (e) => {
                this.updateAllFileLists();
            });

            // Escuchar respuestas HTMX exitosas
            document.body.addEventListener('htmx:afterRequest', (e) => {
                this.handleHTMXResponse(e);
            });
            
            this.listenersInitialized = true;
        }
    }

    handleHTMXResponse(event) {
        const { xhr, requestConfig } = event.detail;
        
        // Si es un upload exitoso
        if (xhr.status === 200 && requestConfig.path && requestConfig.path.includes('/files/upload/')) {
            // Extraer phaseId de la URL
            const phaseIdMatch = requestConfig.path.match(/\/phases\/(\d+)\//);
            const phaseId = phaseIdMatch ? phaseIdMatch[1] : null;
            
            // Dar un pequeño delay para que el servidor procese
            setTimeout(() => {
                this.updateAllFileLists();
                this.clearFormSelection(event.target);
                
                // Incrementar contador
                if (phaseId) {
                    this.incrementFileCounter(phaseId);
                }
            }, 200);
        }
        
        // Si es una eliminación exitosa
        if (xhr.status === 200 && requestConfig.path && requestConfig.path.includes('/files/delete/')) {
            setTimeout(() => {
                this.updateAllFileLists();
            }, 100);
        }
    }

    updateAllFileLists() {
        // Buscar todos los contenedores de archivos
        const fileContainers = document.querySelectorAll('[id^="files-container-"]');
        
        fileContainers.forEach(container => {
            if (this.pendingUpdates.has(container.id)) {
                return; // Ya hay una actualización pendiente
            }
            
            this.pendingUpdates.add(container.id);
            
            // Mostrar indicador de carga
            this.showLoadingIndicator(container);
            
            // Usar HTMX para recargar el contenedor
            if (window.htmx) {
                htmx.trigger(container, 'fileUploaded');
            }
            
            // Limpiar después de un tiempo
            setTimeout(() => {
                this.pendingUpdates.delete(container.id);
            }, 2000);
        });
    }

    showLoadingIndicator(container) {
        // Crear indicador de carga sutil
        const loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'file-list-updating';
        loadingIndicator.innerHTML = `
            <div class="d-flex align-items-center justify-content-center py-2">
                <div class="spinner-border spinner-border-sm text-primary me-2" role="status">
                    <span class="visually-hidden">Actualizando...</span>
                </div>
                <small class="text-muted">Actualizando lista...</small>
            </div>
        `;
        
        // Insertar al inicio del contenedor
        container.insertBefore(loadingIndicator, container.firstChild);
        
        // Remover después de 3 segundos (por si no se recarga)
        setTimeout(() => {
            if (loadingIndicator.parentNode) {
                loadingIndicator.remove();
            }
        }, 3000);
    }

    clearFormSelection(targetElement) {
        // Buscar el formulario más cercano
        const form = targetElement.closest('form.file-upload-form');
        if (!form) return;

        const fileInput = form.querySelector('input[type="file"]');
        if (!fileInput) return;

        // Resetear input
        fileInput.value = '';
        
        // Obtener phase ID
        const phaseId = fileInput.id.split('-').pop();
        
        // Limpiar UI
        this.clearFileSelectionUI(form, phaseId);
    }

    clearFileSelectionUI(form, phaseId) {
        // Ocultar información de archivos seleccionados
        const fileInfoContainer = form.querySelector('.file-info-container');
        if (fileInfoContainer) {
            fileInfoContainer.style.display = 'none';
        }
        
        // Resetear label del botón
        const fileLabel = form.querySelector('.file-label-text');
        if (fileLabel) {
            fileLabel.textContent = 'Seleccionar archivo';
        }
        
        // Ocultar selected-files
        const selectedFilesDiv = document.getElementById(`selected-files-${phaseId}`);
        if (selectedFilesDiv) {
            selectedFilesDiv.style.display = 'none';
        }
        
        // Deshabilitar botón de submit
        const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
        }
        
        // Limpiar errores de validación
        const errorContainer = document.getElementById(`validation-errors-${phaseId}`);
        if (errorContainer) {
            errorContainer.style.display = 'none';
        }

        // Remover clases de error
        const fileInputContainer = form.querySelector('.file-input-container');
        if (fileInputContainer) {
            fileInputContainer.classList.remove('has-validation-errors');
        }
    }

    // Método público para forzar actualización
    forceUpdate(phaseId = null) {
        if (phaseId) {
            const container = document.getElementById(`files-container-${phaseId}`);
            if (container && window.htmx) {
                htmx.trigger(container, 'fileUploaded');
            }
        } else {
            this.updateAllFileLists();
        }
    }

    // Método público para limpiar selección de un formulario específico
    clearFormByPhase(phaseId) {
        const fileInput = document.getElementById(`file-input-${phaseId}`);
        if (fileInput) {
            const form = fileInput.closest('form');
            if (form) {
                this.clearFileSelectionUI(form, phaseId);
            }
        }
    }

    // Incrementar contador de archivos al subir
    incrementFileCounter(phaseId) {
        const counterBadge = document.getElementById(`file-count-${phaseId}`);
        if (!counterBadge) {
            console.warn('No se encontró el badge del contador para incrementar (Fase:', phaseId, ')');
            return;
        }

        // Extraer el número actual e incrementarlo
        const counterText = counterBadge.textContent.trim();
        const currentCountMatch = counterText.match(/\d+/);
        
        if (!currentCountMatch) {
            console.warn('No se pudo extraer el número del contador:', counterText);
            return;
        }
        
        const currentCount = parseInt(currentCountMatch[0]);
        const newCount = currentCount + 1;
        
        // Actualizar el texto manteniendo la traducción "documentos"
        const documentosText = counterText.includes('documento') ? counterText.match(/\d+\s+(.+)/)[1] : 'documentos';
        counterBadge.textContent = `${newCount} ${documentosText}`;
    }
}

// Patrón singleton para evitar múltiples instancias
if (!window.fileListUpdater) {
    // Instanciar el actualizador cuando el DOM esté listo
    document.addEventListener('DOMContentLoaded', () => {
        if (!window.fileListUpdater) {
            window.fileListUpdater = new FileListUpdater();
        }
    });

    // También inicializar en contenido dinámico si no existe aún
    document.addEventListener('htmx:afterSwap', () => {
        if (!window.fileListUpdater) {
            window.fileListUpdater = new FileListUpdater();
        }
    });
}
