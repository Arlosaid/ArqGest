/**
  Sistema de Upload de Archivos Grandes para Cloudflare R2
 * Maneja uploads directos a R2 evitando los límites de Cloudflare proxy
 */

class LargeFileUploader {
    constructor(options = {}) {
        // Usar configuración centralizada
        const config = window.FILE_UPLOAD_CONFIG || {};
        const maxFileSize = config.MAX_FILE_SIZE_MB || 1500;
        
        this.options = {
            maxFileSize: maxFileSize,
            allowedExtensions: config.ALLOWED_EXTENSIONS || [],
            chunkSize: (config.CHUNK_SIZE_MB || 5) * 1024 * 1024,
            maxRetries: config.MAX_RETRIES || 3,
            ...options
        };
        
        // Rastrear formularios ya inicializados para evitar duplicados
        this.initializedForms = new Set();
        
        this.init();
    }

    init() {
        // Buscar formularios de upload
        const uploadForms = document.querySelectorAll('form[data-upload-type="large-file"]');
        uploadForms.forEach(form => this.initializeForm(form));
        
        // También manejar formularios existentes
        const regularForms = document.querySelectorAll('form[enctype="multipart/form-data"]');
        regularForms.forEach(form => {
            const fileInput = form.querySelector('input[type="file"]');
            if (fileInput) {
                this.enhanceFileInput(fileInput, form);
            }
        });
    }

    initializeForm(form) {
        // Evitar inicializar el mismo formulario múltiples veces
        const formId = form.getAttribute('data-phase-id') || form.action;
        if (this.initializedForms.has(formId)) {
            return;
        }
        
        const fileInput = form.querySelector('input[type="file"]');
        if (!fileInput) return;

        this.enhanceFileInput(fileInput, form);
        
        // Remover listener anterior si existe
        if (form._submitHandler) {
            form.removeEventListener('submit', form._submitHandler);
        }
        
        // Crear y asignar nuevo handler
        form._submitHandler = (e) => {
            e.preventDefault();
            e.stopPropagation(); // Evitar propagación del evento
            console.log('📤 Submit interceptado por LargeFileUploader');
            this.handleFormSubmit(form);
        };
        
        form.addEventListener('submit', form._submitHandler);
        
        // Marcar como inicializado
        this.initializedForms.add(formId);
    }

    enhanceFileInput(fileInput, form) {
        // Crear elementos de UI para progreso
        this.createProgressUI(fileInput, form);
        
        fileInput.addEventListener('change', (e) => {
            this.handleFileSelection(e.target, form);
        });
    }

    createProgressUI(fileInput, form) {
        // Crear contenedor de progreso si no existe
        let progressContainer = form.querySelector('.upload-progress-container');
        if (!progressContainer) {
            progressContainer = document.createElement('div');
            progressContainer.className = 'upload-progress-container mt-3';
            progressContainer.style.display = 'none';
            
            progressContainer.innerHTML = `
                <div class="progress mb-2">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" 
                         role="progressbar" style="width: 0%"></div>
                </div>
                <div class="upload-status text-muted small"></div>
                <div class="upload-details small text-muted"></div>
            `;
            
            fileInput.parentNode.appendChild(progressContainer);
        }
        
        // Crear área de información del archivo
        let fileInfoContainer = form.querySelector('.file-info-container');
        if (!fileInfoContainer) {
            fileInfoContainer = document.createElement('div');
            fileInfoContainer.className = 'file-info-container mt-2';
            fileInfoContainer.style.display = 'none';
            fileInput.parentNode.appendChild(fileInfoContainer);
        }
    }

    handleFileSelection(fileInput, form) {
        const files = Array.from(fileInput.files);
        const fileInfoContainer = form.querySelector('.file-info-container');
        
        if (files.length === 0) {
            fileInfoContainer.style.display = 'none';
            return;
        }

        // Mostrar información del archivo seleccionado
        const file = files[0]; // MVP: solo 1 archivo
        const sizeInMB = (file.size / (1024 * 1024)).toFixed(2);
        const extension = file.name.split('.').pop().toUpperCase();
        
        // Validar archivo
        const validation = this.validateFile(file);
        
        fileInfoContainer.innerHTML = `
            <div class="card border-${validation.isValid ? 'success' : 'danger'}">
                <div class="card-body p-3">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-file-${this.getFileIcon(extension)} fa-2x text-${validation.isValid ? 'success' : 'danger'} me-3"></i>
                        <div class="flex-grow-1">
                            <h6 class="mb-1">${file.name}</h6>
                            <small class="text-muted">
                                ${sizeInMB} MB • ${extension}
                                ${validation.isValid ? '' : ' • ❌ ' + validation.error}
                            </small>
                        </div>
                        ${validation.isValid ? '<i class="fas fa-check-circle text-success"></i>' : '<i class="fas fa-exclamation-triangle text-danger"></i>'}
                    </div>
                </div>
            </div>
        `;
        
        fileInfoContainer.style.display = 'block';
        
        // Habilitar/deshabilitar botón de submit
        const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = !validation.isValid;
        }
    }

    validateFile(file) {
        const sizeInMB = file.size / (1024 * 1024);
        const extension = file.name.split('.').pop().toUpperCase();
        
        if (file.size === 0) {
            return { isValid: false, error: 'Archivo vacío' };
        }
        
        if (sizeInMB > this.options.maxFileSize) {
            return { isValid: false, error: `Muy grande (máx: ${this.options.maxFileSize}MB)` };
        }
        
        if (this.options.allowedExtensions.length > 0 && !this.options.allowedExtensions.includes(extension)) {
            return { isValid: false, error: `Tipo no permitido (.${extension.toLowerCase()})` };
        }
        
        return { isValid: true };
    }

    getFileIcon(extension) {
        const iconMap = {
            'PDF': 'pdf',
            'DOC': 'word', 'DOCX': 'word',
            'XLS': 'excel', 'XLSX': 'excel',
            'PPT': 'powerpoint', 'PPTX': 'powerpoint',
            'ZIP': 'archive', 'RAR': 'archive',
            'JPG': 'image', 'JPEG': 'image', 'PNG': 'image', 'GIF': 'image',
            'DWG': 'drafting-compass', 'DXF': 'drafting-compass',
            'RVT': 'building', 'SKP': 'cube'
        };
        return iconMap[extension] || 'file';
    }

    async handleFormSubmit(form) {
        const fileInput = form.querySelector('input[type="file"]');
        const files = Array.from(fileInput.files);
        
        if (files.length === 0) {
            this.showNotification('Por favor selecciona un archivo', 'warning');
            return;
        }

        const file = files[0];
        const sizeInMB = file.size / (1024 * 1024);
        
        // Verificar si storage externo está habilitado
        const config = window.FILE_UPLOAD_CONFIG || {};
        const storageEnabled = config.ENABLE_STORAGES === true || config.ENABLE_STORAGES === 'true';
        
        // Solo usar upload directo a R2/S3 si está habilitado Y el archivo es grande
        if (storageEnabled && sizeInMB > 100) {
            await this.handleLargeFileUpload(file, form);
        } else {
            // Para archivos pequeños o cuando storage no está habilitado, usar método regular
            await this.handleRegularUpload(form);
        }
    }

    async handleLargeFileUpload(file, form) {
        const progressContainer = form.querySelector('.upload-progress-container');
        const progressBar = progressContainer.querySelector('.progress-bar');
        const statusDiv = progressContainer.querySelector('.upload-status');
        const detailsDiv = progressContainer.querySelector('.upload-details');
        
        try {
            progressContainer.style.display = 'block';
            this.updateProgress(progressBar, statusDiv, 0, 'Preparando upload directo...');
            
            // Paso 1: Obtener URL presignada
            const projectId = form.dataset.projectId || this.extractProjectId(form.action);
            const phaseId = form.dataset.phaseId || this.extractPhaseId(form.action);
            
            let presignedData;
            try {
                presignedData = await this.getPresignedUrl(projectId, phaseId, file);
            } catch (presignError) {
                // 🔥 FALLBACK: Si R2 no está disponible (desarrollo local), usar upload normal
                console.log('⚠️ R2 no disponible, usando upload normal:', presignError.message);
                console.log('💡 Para habilitar R2 en local, configura ENABLE_STORAGES=true en .env');
                this.updateProgress(progressBar, statusDiv, 10, 'Procesando archivo...');
                
                await this.handleRegularUpload(form);
                return; // Salir de handleLargeFileUpload
            }
            
            this.updateProgress(progressBar, statusDiv, 10, 'URL de upload obtenida, subiendo archivo...');
            detailsDiv.textContent = `Subiendo directamente a almacenamiento (${(file.size / (1024 * 1024)).toFixed(2)} MB)`;
            
            // Paso 2: Upload directo a R2 con manejo de errores CORS
            try {
                await this.uploadToR2(file, presignedData.url, (progress) => {
                    const percentage = 10 + (progress * 0.8); // 10-90%
                    this.updateProgress(progressBar, statusDiv, percentage, `Subiendo: ${Math.round(progress)}%`);
                });
            } catch (uploadError) {
                // 🔥 FALLBACK: Si el upload directo falla (CORS), usar upload a través del backend
                if (uploadError.message.includes('Network error') || uploadError.message.includes('CORS')) {
                    console.warn('⚠️ Upload directo a R2 falló (posible problema CORS), usando método alternativo...');
                    console.warn('📖 Para solucionar: ver docs/R2_CORS_CONFIGURATION.md');
                    
                    this.updateProgress(progressBar, statusDiv, 10, 'Cambiando a método alternativo...');
                    detailsDiv.textContent = 'Usando upload a través del servidor...';
                    
                    await this.handleRegularUpload(form);
                    return;
                }
                throw uploadError; // Re-lanzar otros errores
            }
            
            this.updateProgress(progressBar, statusDiv, 90, 'Confirmando upload...');
            
            // Paso 3: Confirmar upload en el backend
            await this.confirmUpload(presignedData.key, projectId, phaseId, file.size, file.type);
            
            this.updateProgress(progressBar, statusDiv, 100, '¡Upload completado exitosamente!');
            progressBar.classList.remove('progress-bar-animated');
            progressBar.classList.add('bg-success');
            
            // Mostrar notificación de éxito
            this.showNotification('¡Archivo subido exitosamente!', 'success');
            
            // Recargar la lista de archivos
            setTimeout(() => {
                this.reloadFilesList(form);
                progressContainer.style.display = 'none';
                
                // Usar el actualizador global si está disponible
                if (window.fileListUpdater) {
                    const phaseId = this.extractPhaseId(form.action);
                    window.fileListUpdater.clearFormByPhase(phaseId);
                } else {
                    form.reset();
                    form.querySelector('.file-info-container').style.display = 'none';
                }
            }, 2000);
            
        } catch (error) {
            console.error('❌ Error en upload:', error);
            progressBar.classList.add('bg-danger');
            
            // Mensaje de error más descriptivo
            let errorMsg = error.message;
            if (error.message.includes('CORS') || error.message.includes('Network error')) {
                errorMsg = 'Error de conexión. Por favor contacta al administrador.';
                detailsDiv.innerHTML = '<small class="text-danger">💡 Problema de configuración CORS detectado</small>';
            }
            
            this.updateProgress(progressBar, statusDiv, 0, 'Error: ' + errorMsg);
            this.showNotification('Error al subir archivo: ' + errorMsg, 'error');
        }
    }

    async handleRegularUpload(form) {
        // Para archivos pequeños o cuando storage no está habilitado, usar el método tradicional
        const progressContainer = form.querySelector('.upload-progress-container');
        const progressBar = progressContainer.querySelector('.progress-bar');
        const statusDiv = progressContainer.querySelector('.upload-status');
        const detailsDiv = progressContainer.querySelector('.upload-details');
        
        progressContainer.style.display = 'block';
        this.updateProgress(progressBar, statusDiv, 10, 'Subiendo archivo al servidor...');
        
        // Obtener info del archivo para mostrar
        const fileInput = form.querySelector('input[type="file"]');
        if (fileInput && fileInput.files.length > 0) {
            const file = fileInput.files[0];
            const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
            if (detailsDiv) {
                detailsDiv.textContent = `Procesando: ${file.name} (${sizeMB} MB)`;
            }
        }
        
        try {
            // Usar fetch para enviar el formulario
            const formData = new FormData(form);
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCsrfToken(),
                    'X-Requested-With': 'XMLHttpRequest',
                    'HX-Request': 'true'  // Marcar como petición HTMX
                }
            });
            
            if (response.ok) {
                this.updateProgress(progressBar, statusDiv, 100, '¡Upload completado!');
                progressBar.classList.add('bg-success');
                
                this.showNotification('¡Archivo subido exitosamente!', 'success');
                
                setTimeout(() => {
                    this.reloadFilesList(form);
                    progressContainer.style.display = 'none';
                    
                    // Usar el actualizador global si está disponible
                    if (window.fileListUpdater) {
                        const phaseId = this.extractPhaseId(form.action);
                        window.fileListUpdater.clearFormByPhase(phaseId);
                    } else {
                        form.reset();
                        form.querySelector('.file-info-container').style.display = 'none';
                    }
                }, 1500);
            } else {
                throw new Error('Error en el servidor');
            }
            
        } catch (error) {
            progressBar.classList.add('bg-danger');
            this.updateProgress(progressBar, statusDiv, 0, 'Error: ' + error.message);
            this.showNotification('Error al subir archivo', 'error');
        }
    }

    async getPresignedUrl(projectId, phaseId, file) {
        const response = await fetch(`/projects/${projectId}/phases/${phaseId}/files/presigned-upload/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken(),
            },
            body: JSON.stringify({
                filename: file.name,
                content_type: file.type,
                file_size: file.size
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Error obteniendo URL de upload');
        }
        
        return await response.json();
    }

    async uploadToR2(file, presignedUrl, progressCallback) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const progress = (e.loaded / e.total) * 100;
                    progressCallback(progress);
                }
            });
            
            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    console.log('✅ Upload a R2 exitoso:', xhr.status);
                    resolve();
                } else {
                    console.error('❌ Upload falló:', xhr.status, xhr.statusText);
                    console.error('Response:', xhr.responseText);
                    reject(new Error(`Upload failed: ${xhr.status} ${xhr.statusText}`));
                }
            });
            
            xhr.addEventListener('error', (e) => {
                console.error('❌ Network error durante upload a R2');
                console.error('Error event:', e);
                console.error('XHR Status:', xhr.status);
                console.error('XHR ReadyState:', xhr.readyState);
                
                // Mensaje de error más descriptivo para CORS
                let errorMsg = 'Network error during upload';
                if (xhr.status === 0) {
                    errorMsg = 'No se pudo conectar a R2. Verifica:\n' +
                              '1. Configuración CORS en R2\n' +
                              '2. URL presignada válida\n' +
                              '3. Conexión a internet';
                    console.error('💡 Tip: Este error suele indicar un problema de CORS.');
                    console.error('📖 Ver docs/R2_CORS_CONFIGURATION.md para solución');
                }
                
                reject(new Error(errorMsg));
            });
            
            xhr.addEventListener('timeout', () => {
                console.error('⏱️ Upload timeout después de 5 minutos');
                reject(new Error('Upload timeout - archivo muy grande o conexión lenta'));
            });
            
            xhr.addEventListener('loadstart', () => {
                console.log('🚀 Iniciando upload directo a R2...');
                console.log('Archivo:', file.name, `(${(file.size / 1024 / 1024).toFixed(2)} MB)`);
            });
            
            xhr.open('PUT', presignedUrl);
            xhr.setRequestHeader('Content-Type', file.type || 'application/octet-stream');
            xhr.timeout = 600000; // 10 minutos timeout para archivos grandes
            
            console.log('📤 Enviando archivo a R2...');
            xhr.send(file);
        });
    }

    async confirmUpload(key, projectId, phaseId, sizeBytes, contentType) {
        const response = await fetch('/files/confirm-upload/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken(),
            },
            body: JSON.stringify({
                key: key,
                project_id: projectId,
                phase_id: phaseId,
                size_bytes: sizeBytes,
                content_type: contentType
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Error confirmando upload');
        }
        
        return await response.json();
    }

    updateProgress(progressBar, statusDiv, percentage, message) {
        progressBar.style.width = `${percentage}%`;
        progressBar.setAttribute('aria-valuenow', percentage);
        statusDiv.textContent = message;
    }

    extractProjectId(url) {
        const match = url.match(/projects\/(\d+)/);
        return match ? match[1] : null;
    }

    extractPhaseId(url) {
        const match = url.match(/phases\/(\d+)/);
        return match ? match[1] : null;
    }

    reloadFilesList(form) {
        // Extraer phaseId
        const phaseId = this.extractPhaseId(form.action) || form.dataset.phaseId;
        
        // Trigger para recargar archivos usando HTMX con phaseId
        const event = new CustomEvent('fileUploaded', { 
            detail: { phaseId: phaseId }
        });
        document.body.dispatchEvent(event);
        
        // También intentar recargar contenedores específicos
        if (phaseId) {
            const container = document.getElementById(`files-container-${phaseId}`);
            if (container && window.htmx) {
                htmx.trigger(container, 'fileUploaded');
            }
            
            // Incrementar contador si el updater está disponible
            // if (window.fileListUpdater) {
            //    window.fileListUpdater.incrementFileCounter(phaseId);
            // }
        }
        
        // Limpiar formulario y selección de archivos
        this.clearFileSelection(form);
    }

    clearFileSelection(form) {
        // Resetear el input de archivos
        const fileInput = form.querySelector('input[type="file"]');
        if (fileInput) {
            fileInput.value = '';
            
            // Obtener el phaseId del input
            const phaseId = fileInput.id.split('-').pop();
            
            // Ocultar información de archivos seleccionados
            const fileInfoContainer = form.querySelector('.file-info-container');
            if (fileInfoContainer) {
                fileInfoContainer.style.display = 'none';
            }
            
            // Resetear el label del botón
            const fileLabel = form.querySelector('.file-label-text');
            if (fileLabel) {
                fileLabel.textContent = 'Seleccionar archivo';
            }
            
            // Ocultar selected-files si existe
            const selectedFilesDiv = document.getElementById(`selected-files-${phaseId}`);
            if (selectedFilesDiv) {
                selectedFilesDiv.style.display = 'none';
            }
            
            // Deshabilitar botón de submit
            const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
            }
            
            // Limpiar errores de validación si existen
            const errorContainer = document.getElementById(`validation-errors-${phaseId}`);
            if (errorContainer) {
                errorContainer.style.display = 'none';
            }
        }
    }

    showNotification(message, type = 'info') {
        // Usar el sistema de notificaciones existente
        if (window.notifications) {
            window.notifications[type](message);
        } else if (window.showGlobalNotification) {
            window.showGlobalNotification(message, type);
        } else {
            // Fallback a alert
            alert(message);
        }
    }

    getCsrfToken() {
        // 1. Try to get from meta tag (most reliable for SPA/AJAX)
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        if (metaToken && metaToken.content) {
            return metaToken.content;
        }
        
        // 2. Try to get from hidden input (standard Django form)
        const inputToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (inputToken && inputToken.value) {
            return inputToken.value;
        }

        // 3. Fallback to cookie (might fail with HttpOnly)
        const value = `; ${document.cookie}`;
        const parts = value.split(`; csrftoken=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        
        return '';
    }
}

// Patrón singleton para evitar múltiples instancias y event listeners duplicados
let largeFileUploaderInstance = null;

function initializeLargeFileUploader() {
    if (!largeFileUploaderInstance) {
        largeFileUploaderInstance = new LargeFileUploader();
    } else {
        // Solo reinicializar formularios nuevos sin crear nueva instancia
        largeFileUploaderInstance.init();
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    initializeLargeFileUploader();
});

// También inicializar en contenido dinámico (HTMX)
document.addEventListener('htmx:afterSwap', () => {
    initializeLargeFileUploader();
});
