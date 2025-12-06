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
                    <div class="progress-bar progress-bar-striped progress-bar-animated bg-primary" 
                         role="progressbar" style="width: 0%"></div>
                </div>
                <div class="upload-status text-muted small"></div>
                <div class="upload-details small text-muted"></div>
            `;
            
            fileInput.parentNode.appendChild(progressContainer);
        }
        
        // Crear área de información del archivo - DESHABILITADO: Ya se muestra en el label
        /*
        let fileInfoContainer = form.querySelector('.file-info-container');
        if (!fileInfoContainer) {
            fileInfoContainer = document.createElement('div');
            fileInfoContainer.className = 'file-info-container mt-2';
            fileInfoContainer.style.display = 'none';
            fileInput.parentNode.appendChild(fileInfoContainer);
        }
        */
    }

    handleFileSelection(fileInput, form) {
        const files = Array.from(fileInput.files);
        
        if (files.length === 0) {
            return;
        }

        const file = files[0];
        
        // Validar archivo
        const validation = this.validateFile(file);
        
        /* DESHABILITADO: El recuadro blanco es redundante
        if (fileInfoContainer) {
            fileInfoContainer.innerHTML = `
                <div class="card border-${validation.isValid ? 'success' : 'danger'}">
                    <div class="card-body p-3">
                        <div class="d-flex align-items-center">
                            <i class="fas fa-file-${this.getFileIcon(extension)} fa-2x text-${validation.isValid ? 'success' : 'danger'} me-3"></i>
                            <div class="flex-grow-1">
                                <h6 class="mb-1">${file.name}</h6>
                                <small class="text-muted">
                                    ${sizeInMB} MB • ${extension}
                                    ${validation.isValid ? '' : ' • ' + validation.error}
                                </small>
                            </div>
                            ${validation.isValid ? '<i class="fas fa-check-circle text-success"></i>' : '<i class="fas fa-exclamation-triangle text-danger"></i>'}
                        </div>
                    </div>
                </div>
            `;
            
            fileInfoContainer.style.display = 'block';
        }
        */
        
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
        
        // Validar espacio de storage disponible PRIMERO
        if (window.STORAGE_INFO) {
            const availableBytes = window.STORAGE_INFO.available_bytes;
            if (file.size > availableBytes) {
                const fileSizeMB = sizeInMB.toFixed(2);
                const availableMB = (availableBytes / (1024 * 1024)).toFixed(2);
                const limitGB = window.STORAGE_INFO.limit_gb;
                return { 
                    isValid: false, 
                    error: `Sin espacio suficiente. Necesitas ${fileSizeMB} MB pero solo tienes ${availableMB} MB disponibles de ${limitGB} GB`,
                    errorType: 'storage'
                };
            }
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
        
        // VALIDACIÓN DE STORAGE - Bloquear ANTES de intentar subir
        const validation = this.validateFile(file);
        
        if (!validation.isValid) {
            // Mostrar error y NO continuar
            this.showNotification(validation.error, 'error');
            
            // Mostrar error en la UI del formulario
            const progressContainer = form.querySelector('.upload-progress-container');
            if (progressContainer) {
                const progressBar = progressContainer.querySelector('.progress-bar');
                const statusDiv = progressContainer.querySelector('.upload-status');
                progressContainer.style.display = 'block';
                progressBar.classList.remove('bg-primary', 'bg-gradient-primary', 'progress-bar-striped', 'progress-bar-animated');
                progressBar.classList.add('bg-danger');
                progressBar.style.width = '100%';
                statusDiv.textContent = validation.error;
            }
            
            return; // NO continuar con el upload
        }
        
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
            
            this.updateProgress(progressBar, statusDiv, 100, '¡Subida completada exitosamente!');
            progressBar.classList.remove('progress-bar-animated', 'bg-primary', 'bg-gradient-primary');
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
            progressBar.classList.remove('bg-primary', 'bg-gradient-primary');
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
        this.updateProgress(progressBar, statusDiv, 0, 'Iniciando subida...');
        
        // Obtener info del archivo para mostrar
        const fileInput = form.querySelector('input[type="file"]');
        if (fileInput && fileInput.files.length > 0) {
            const file = fileInput.files[0];
            const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
            if (detailsDiv) {
                detailsDiv.textContent = `Procesando: ${file.name} (${sizeMB} MB)`;
            }
        }
        
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            const formData = new FormData(form);
            
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    this.updateProgress(progressBar, statusDiv, percentComplete, `Subiendo: ${Math.round(percentComplete)}%`);
                }
            });

            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    this.updateProgress(progressBar, statusDiv, 100, '¡Subida completada!');
                    progressBar.classList.remove('progress-bar-striped', 'progress-bar-animated', 'bg-primary', 'bg-gradient-primary');
                    progressBar.classList.add('bg-success');
                    
                    // Actualizar también el detailsDiv para limpiar "Procesando:"
                    if (detailsDiv) {
                        detailsDiv.textContent = '✓ Archivo procesado correctamente';
                    }
                    
                    this.showNotification('¡Archivo subido exitosamente!', 'success');
                    
                    // Ejecutar cualquier script que venga en la respuesta (para HTMX)
                    try {
                        const responseText = xhr.responseText;
                        if (responseText && responseText.includes('<script>')) {
                            const scriptMatch = responseText.match(/<script>([\s\S]*?)<\/script>/);
                            if (scriptMatch && scriptMatch[1]) {
                                eval(scriptMatch[1]);
                            }
                        }
                    } catch (e) {
                        console.warn('Error ejecutando script de respuesta:', e);
                    }
                    
                    // Refrescar info de storage después de upload exitoso
                    if (window.FILE_VALIDATION && window.FILE_VALIDATION.refreshStorageInfo) {
                        window.FILE_VALIDATION.refreshStorageInfo();
                    }
                    
                    setTimeout(() => {
                        this.reloadFilesList(form);
                        progressContainer.style.display = 'none';
                        
                        // Usar el actualizador global si está disponible
                        if (window.fileListUpdater) {
                            const phaseId = this.extractPhaseId(form.action);
                            window.fileListUpdater.clearFormByPhase(phaseId);
                        } else {
                            form.reset();
                            const fileInfo = form.querySelector('.file-info-container');
                            if (fileInfo) fileInfo.style.display = 'none';
                        }
                        // Reset progress bar
                        progressBar.classList.remove('bg-success');
                        progressBar.classList.add('progress-bar-striped', 'progress-bar-animated');
                        progressBar.style.width = '0%';
                    }, 1500);
                    resolve();
                } else {
                    // Intentar obtener mensaje de error específico del servidor
                    let errorMessage = `Error ${xhr.status}: ${xhr.statusText}`;
                    let isStorageError = false;
                    
                    try {
                        const errorData = JSON.parse(xhr.responseText);
                        if (errorData.error) errorMessage = errorData.error;
                        else if (errorData.detail) errorMessage = errorData.detail;
                        else if (errorData.message) errorMessage = errorData.message;
                        else if (typeof errorData === 'object') {
                            const firstKey = Object.keys(errorData)[0];
                            const firstError = errorData[firstKey];
                            errorMessage = Array.isArray(firstError) ? firstError[0] : firstError;
                        }
                        
                        // Detectar si es error de storage
                        if (errorData.error_type === 'storage_limit' || xhr.status === 413) {
                            isStorageError = true;
                            // Refrescar storage info para actualizar el indicador
                            if (window.FILE_VALIDATION && window.FILE_VALIDATION.refreshStorageInfo) {
                                window.FILE_VALIDATION.refreshStorageInfo();
                            }
                        }
                    } catch (e) {}
                    
                    // Mensaje más claro para error de storage
                    if (xhr.status === 413 && !errorMessage.includes('espacio') && !errorMessage.includes('storage')) {
                        errorMessage = 'No tienes espacio de almacenamiento suficiente. Libera espacio o contacta al administrador para aumentar tu límite.';
                    }
                    
                    reject(new Error(errorMessage));
                }
            });

            xhr.addEventListener('error', () => {
                // Verificar si podría ser un problema de storage
                if (window.STORAGE_INFO && window.STORAGE_INFO.is_over_limit) {
                    reject(new Error('No tienes espacio de almacenamiento disponible. Libera espacio o aumenta tu plan.'));
                } else {
                    reject(new Error('Error de conexión al subir el archivo. Verifica tu conexión a internet e inténtalo de nuevo.'));
                }
            });
            xhr.addEventListener('abort', () => reject(new Error('Subida cancelada')));
            
            xhr.open('POST', form.action);
            xhr.setRequestHeader('X-CSRFToken', this.getCsrfToken());
            xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
            xhr.setRequestHeader('HX-Request', 'true');
            
            xhr.send(formData);
        }).catch(error => {
            progressBar.classList.remove('progress-bar-striped', 'progress-bar-animated', 'bg-primary', 'bg-gradient-primary');
            progressBar.classList.add('bg-danger');
            this.updateProgress(progressBar, statusDiv, 100, 'Error: ' + error.message);
            this.showNotification(error.message, 'error');
        });
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
                    resolve();
                } else {
                    reject(new Error(`Upload failed: ${xhr.status} ${xhr.statusText}`));
                }
            });
            
            xhr.addEventListener('error', (e) => {
                // Mensaje de error más descriptivo para CORS
                let errorMsg = 'Network error during upload';
                if (xhr.status === 0) {
                    errorMsg = 'No se pudo conectar a R2. Verifica:\n' +
                              '1. Configuración CORS en R2\n' +
                              '2. URL presignada válida\n' +
                              '3. Conexión a internet';
                }
                
                reject(new Error(errorMsg));
            });
            
            xhr.addEventListener('timeout', () => {
                reject(new Error('Upload timeout - archivo muy grande o conexión lenta'));
            });
            
            xhr.open('PUT', presignedUrl);
            xhr.setRequestHeader('Content-Type', file.type || 'application/octet-stream');
            xhr.timeout = 600000; // 10 minutos timeout para archivos grandes
            
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
