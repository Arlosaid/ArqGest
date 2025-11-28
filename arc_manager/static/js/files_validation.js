/**
 * File Validation and Upload Logic
 * Handles client-side validation for file uploads in the files tab.
 * Enhanced with drag & drop support and better UX feedback.
 */

console.log('🚀 Files validation script loaded!');

const FILE_VALIDATION = {
    // Usar configuración centralizada con límites específicos por dispositivo
    MAX_SIZE_MB: window.FILE_UPLOAD_CONFIG?.MAX_FILE_SIZE_MB || 1500,
    MAX_SIZE_MOBILE_MB: window.FILE_UPLOAD_CONFIG?.MAX_FILE_SIZE_MOBILE_MB || 1500,
    ALLOWED_EXTENSIONS: window.FILE_UPLOAD_CONFIG?.ALLOWED_EXTENSIONS || ['PDF', 'JPG', 'JPEG', 'PNG', 'GIF', 'TIFF', 'DWG', 'DXF', 'RVT', 'SKP', 'DOC', 'DOCX', 'XLS', 'XLSX', 'PPT', 'PPTX', 'ZIP', 'RAR', 'TXT', 'MD'],
    
    // Log del límite cargado
    init: function() {
        console.log(`✅ Límites: Desktop=${this.MAX_SIZE_MB}MB, Mobile=${this.MAX_SIZE_MOBILE_MB}MB`);
    },
    
    // Detectar si es dispositivo móvil
    isMobile: function() {
        const userAgent = navigator.userAgent.toLowerCase();
        return /android|iphone|ipad|mobile|tablet/.test(userAgent);
    },
    
    // Obtener extensiones permitidas formateadas
    getAllowedExtensionsText: function() {
        const exts = this.ALLOWED_EXTENSIONS.slice(0, 5);
        return exts.join(', ') + '...';
    },
    
    // Validar un archivo individual
    validateFile: function(file) {
        const errors = [];
        const maxSizeMB = this.isMobile() ? this.MAX_SIZE_MOBILE_MB : this.MAX_SIZE_MB;
        const maxSizeBytes = maxSizeMB * 1024 * 1024;
        
        // Validar tamaño
        if (file.size > maxSizeBytes) {
            const fileSizeMB = (file.size / 1024 / 1024).toFixed(1);
            errors.push({
                type: 'size',
                message: `"${file.name}" es muy grande (${fileSizeMB}MB). Máximo permitido: ${maxSizeMB}MB`
            });
        }
        
        // Validar extensión
        const extension = file.name.split('.').pop().toUpperCase();
        if (!this.ALLOWED_EXTENSIONS.includes(extension)) {
            errors.push({
                type: 'extension',
                message: `"${file.name}" tiene una extensión no permitida (.${extension.toLowerCase()})`
            });
        }
        
        return {
            valid: errors.length === 0,
            errors: errors,
            file: file
        };
    },
    
    // Validar archivo único (simplificado para MVP)
    validateFiles: function(files) {
        const allErrors = [];
        const validFiles = [];
        
        // Solo permitir 1 archivo por vez
        if (files.length > 1) {
            allErrors.push({
                type: 'count',
                message: "Solo se permite subir 1 archivo a la vez"
            });
            return {
                valid: false,
                errors: allErrors,
                validFiles: [],
                hasValidFiles: false
            };
        }
        
        Array.from(files).forEach(file => {
            const validation = this.validateFile(file);
            if (validation.valid) {
                validFiles.push(file);
            } else {
                allErrors.push(...validation.errors);
            }
        });
        
        return {
            valid: allErrors.length === 0,
            errors: allErrors,
            validFiles: validFiles,
            hasValidFiles: validFiles.length > 0
        };
    },
    
    // Formatear tamaño de archivo
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
};

// Función para mostrar errores de validación mejorada
function showValidationErrors(errors, phaseId) {
    const uploadWrapper = document.getElementById('upload-zone-' + phaseId);
    
    // Crear o actualizar el contenedor de errores
    let errorContainer = document.getElementById('validation-errors-' + phaseId);
    if (!errorContainer) {
        errorContainer = document.createElement('div');
        errorContainer.id = 'validation-errors-' + phaseId;
        errorContainer.className = 'validation-error';
        
        const form = document.querySelector('#file-input-' + phaseId).closest('form');
        // Insertar después del upload wrapper
        uploadWrapper.parentNode.insertBefore(errorContainer, uploadWrapper.nextSibling);
    }
    
    // Construir HTML de errores - formato más limpio
    const errorMessages = errors.map(e => {
        if (typeof e === 'string') return e;
        // Simplificar mensaje
        let msg = e.message || '';
        // Remover comillas del nombre de archivo para hacerlo más limpio
        msg = msg.replace(/"/g, '');
        return msg;
    });
    
    // Usar un solo mensaje si hay un solo error
    const errorContent = errorMessages.length === 1 
        ? `<p style="margin: 0; font-size: 0.75rem; color: #991b1b;">${errorMessages[0]}</p>`
        : `<ul class="validation-error-list">${errorMessages.map(error => `<li>${error}</li>`).join('')}</ul>`;
    
    errorContainer.innerHTML = `
        <div class="validation-error-header">
            <i class="fas fa-exclamation-circle"></i>
            <strong>Tipo no permitido</strong>
        </div>
        ${errorContent}
    `;
    errorContainer.style.display = 'block';
    
    // Agregar clase de error al wrapper
    if (uploadWrapper) {
        uploadWrapper.classList.add('has-error');
        uploadWrapper.classList.remove('file-selected');
    }
}

// Función para ocultar errores de validación
function hideValidationErrors(phaseId) {
    const errorContainer = document.getElementById('validation-errors-' + phaseId);
    if (errorContainer) {
        errorContainer.style.display = 'none';
    }
    
    // Remover clase de error del wrapper
    const uploadWrapper = document.getElementById('upload-zone-' + phaseId);
    if (uploadWrapper) {
        uploadWrapper.classList.remove('has-error');
    }
}

// Inicializar drag & drop para las zonas de upload
function initDragAndDrop() {
    document.querySelectorAll('.file-upload-wrapper').forEach(function(wrapper) {
        // Evitar doble binding
        if (wrapper.dataset.dragInitialized) return;
        wrapper.dataset.dragInitialized = "true";
        
        const phaseId = wrapper.id.split('-').pop();
        const fileInput = document.getElementById('file-input-' + phaseId);
        
        // Prevenir comportamiento default del navegador
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            wrapper.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        // Highlight al arrastrar
        ['dragenter', 'dragover'].forEach(eventName => {
            wrapper.addEventListener(eventName, function() {
                wrapper.classList.add('drag-over');
            }, false);
        });
        
        // Remover highlight
        ['dragleave', 'drop'].forEach(eventName => {
            wrapper.addEventListener(eventName, function() {
                wrapper.classList.remove('drag-over');
            }, false);
        });
        
        // Manejar drop
        wrapper.addEventListener('drop', function(e) {
            const files = e.dataTransfer.files;
            if (files.length > 0 && fileInput) {
                // Crear un nuevo DataTransfer para asignar archivos
                const dt = new DataTransfer();
                dt.items.add(files[0]); // Solo el primer archivo
                fileInput.files = dt.files;
                
                // Disparar evento change
                const event = new Event('change', { bubbles: true });
                fileInput.dispatchEvent(event);
            }
        }, false);
    });
}

// Manejar selección de documentos y mostrar información
function initFileInputs() {
    document.querySelectorAll('.file-input').forEach(function(input) {
        // Evitar doble binding
        if (input.dataset.initialized) return;
        input.dataset.initialized = "true";

        input.addEventListener('change', function() {
            const phaseId = this.id.split('-').pop();
            const uploadBtn = this.closest('form').querySelector('.upload-btn');
            const fileLabel = this.closest('.file-input-container').querySelector('.file-label-text');
            const uploadWrapper = document.getElementById('upload-zone-' + phaseId);
            const fileLabelIcon = this.closest('.file-input-container').querySelector('.file-input-label i');
            
            // Ocultar errores previos
            hideValidationErrors(phaseId);
            
            if (this.files.length > 0) {
                // Validar archivo (solo 1 permitido)
                const validation = FILE_VALIDATION.validateFiles(this.files);
                
                if (!validation.valid) {
                    // Mostrar errores de validación
                    showValidationErrors(validation.errors, phaseId);
                    uploadBtn.disabled = true;
                    fileLabel.textContent = 'Selecciona un archivo válido';
                    uploadWrapper.classList.remove('file-selected');
                    
                    // Cambiar icono a error
                    if (fileLabelIcon) {
                        fileLabelIcon.className = 'fas fa-times-circle';
                    }
                } else {
                    // Archivo válido
                    const fileName = this.files[0].name;
                    const fileSize = FILE_VALIDATION.formatFileSize(this.files[0].size);
                    
                    // Truncar nombre si es muy largo
                    const maxLen = 25;
                    const displayName = fileName.length > maxLen 
                        ? fileName.substring(0, maxLen) + '...' 
                        : fileName;
                    
                    // Actualizar texto del label - más compacto
                    fileLabel.innerHTML = `<strong>${displayName}</strong> <span style="color: #64748b;">(${fileSize})</span>`;
                    
                    // Agregar estado de archivo seleccionado
                    uploadWrapper.classList.add('file-selected');
                    
                    // Cambiar icono a check
                    if (fileLabelIcon) {
                        fileLabelIcon.className = 'fas fa-check-circle';
                    }
                    
                    // Habilitar botón de subir
                    uploadBtn.disabled = false;
                }
            } else {
                // Sin archivo seleccionado
                uploadBtn.disabled = true;
                fileLabel.textContent = 'Arrastra o selecciona un archivo';
                uploadWrapper.classList.remove('file-selected');
                
                // Restaurar icono original
                if (fileLabelIcon) {
                    fileLabelIcon.className = 'fas fa-cloud-upload-alt';
                }
            }
        });
    });
}

// Resetear formulario y estado visual
function resetUploadForm(phaseId) {
    const form = document.querySelector(`#file-input-${phaseId}`)?.closest('form');
    if (!form) return;
    
    const uploadWrapper = document.getElementById('upload-zone-' + phaseId);
    const fileLabel = form.querySelector('.file-label-text');
    const fileLabelIcon = form.querySelector('.file-input-label i');
    const uploadBtn = form.querySelector('.upload-btn');
    
    // Resetear formulario
    form.reset();
    
    // Resetear estados visuales
    if (uploadWrapper) {
        uploadWrapper.classList.remove('file-selected', 'has-error', 'drag-over');
    }
    
    if (fileLabel) {
        fileLabel.textContent = 'Arrastra o selecciona un archivo';
    }
    
    if (fileLabelIcon) {
        fileLabelIcon.className = 'fas fa-cloud-upload-alt';
    }
    
    if (uploadBtn) {
        uploadBtn.disabled = true;
    }
    
    hideValidationErrors(phaseId);
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ DOMContentLoaded fired in files tab!');
    initFileInputs();
    initDragAndDrop();
    
    // Inicializar validación y mostrar límite cargado
    FILE_VALIDATION.init();
});

// Re-inicializar cuando HTMX carga contenido nuevo (si fuera necesario)
document.body.addEventListener('htmx:afterSwap', function(evt) {
    initFileInputs();
    initDragAndDrop();
});

// El sistema de actualización ahora se maneja en file-list-updater.js
// Mantener solo compatibilidad básica para casos edge
document.body.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.detail.xhr.status === 200 && evt.detail.requestConfig.path.includes('/files/upload/')) {
        // El FileListUpdater maneja esto automáticamente
        // Solo disparar evento si no está presente
        if (!window.fileListUpdater) {
            document.body.dispatchEvent(new CustomEvent('fileUploaded'));
        }
    }
});

// Función para validar antes del envío del formulario
function validateFormBeforeSubmit(form, phaseId) {
    const fileInput = form.querySelector('.file-input');
    if (!fileInput || !fileInput.files.length) {
        return false; // No hay archivos seleccionados
    }
    
    const validation = FILE_VALIDATION.validateFiles(fileInput.files);
    
    if (!validation.valid) {
        // Mostrar errores si no se habían mostrado ya
        showValidationErrors(validation.errors, phaseId);
        
        if (!validation.hasValidFiles) {
            // No hay archivos válidos, prevenir envío
            return false;
        }
        
        // Si hay archivos válidos, crear una nueva lista de archivos con solo los válidos
        // Nota: No podemos modificar directamente FileList, pero el servidor validará nuevamente
        console.warn('Se enviarán todos los archivos al servidor. El servidor filtrará los inválidos.');
    }
    
    // Ocultar errores previos al enviar
    hideValidationErrors(phaseId);
    
    return true; // Permitir envío
}

// Resetear formulario después de cualquier error (sin notificación duplicada)
document.body.addEventListener('htmx:responseError', function(evt) {
    if (evt.detail.requestConfig.path && evt.detail.requestConfig.path.includes('/files/upload/')) {
        // Encontrar el phaseId desde el formulario
        const form = evt.target.closest('form');
        if (form && form.classList.contains('file-upload-form')) {
            const phaseId = form.dataset.phaseId;
            if (phaseId) {
                resetUploadForm(phaseId);
            } else {
                form.reset();
            }
        }
    }
});

// Exportar funciones para uso externo si es necesario
window.FILE_VALIDATION = FILE_VALIDATION;
window.resetUploadForm = resetUploadForm;
