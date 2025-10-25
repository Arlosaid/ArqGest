/**
  Sistema de Upload de Archivos Grandes para Cloudflare R2
 * Maneja uploads directos a R2 evitando los límites de Cloudflare proxy
 */

class LargeFileUploader {
    constructor(options = {}) {
        // Leer el límite desde la variable global (más confiable que meta tag)
        const maxFileSize = window.SYSTEM_CONFIG?.MAX_FILE_SIZE_MB || 1500;
        
        console.log(`Límite de archivo cargado: ${maxFileSize}MB (desde SYSTEM_CONFIG)`);
        
        this.options = {
            maxFileSize: maxFileSize,
            allowedExtensions: (document.querySelector('meta[name="allowed-extensions"]')?.content || '').split(','),
            chunkSize: 5 * 1024 * 1024, // 5MB chunks para uploads grandes
            maxRetries: 3,
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
            console.log(`⚠️ Formulario ${formId} ya inicializado, saltando...`);
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
        console.log(`✅ Formulario ${formId} inicializado`);
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
                    ${validation.isValid && parseFloat(sizeInMB) > 100 ? `
                        <div class="alert alert-info mt-2 mb-0 small">
                            <i class="fas fa-info-circle"></i> 
                            Archivo grande detectado. Se usará upload directo a almacenamiento.
                        </div>
                    ` : ''}
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
        
        // Decidir método de upload basado en tamaño
        if (sizeInMB > 100) {
            await this.handleLargeFileUpload(file, form);
        } else {
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
                this.updateProgress(progressBar, statusDiv, 10, 'Usando método alternativo de upload...');
                
                // Verificar si el archivo es muy grande para upload normal
                const fileSizeMB = file.size / (1024 * 1024);
                const maxSizeMB = window.SYSTEM_CONFIG?.MAX_FILE_SIZE_MB || 1500;
                
                if (fileSizeMB > 500) {
                    this.showNotification(
                        `⚠️ Archivo muy grande (${fileSizeMB.toFixed(0)}MB). En producción se usará R2 para mejor rendimiento.`,
                        'warning'
                    );
                }
                
                await this.handleRegularUpload(form);
                return; // Salir de handleLargeFileUpload
            }
            
            this.updateProgress(progressBar, statusDiv, 10, 'URL de upload obtenida, subiendo archivo...');
            detailsDiv.textContent = `Subiendo directamente a almacenamiento (${(file.size / (1024 * 1024)).toFixed(2)} MB)`;
            
            // Paso 2: Upload directo a R2
            await this.uploadToR2(file, presignedData.url, (progress) => {
                const percentage = 10 + (progress * 0.8); // 10-90%
                this.updateProgress(progressBar, statusDiv, percentage, `Subiendo: ${Math.round(progress)}%`);
            });
            
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
            console.error('Error en upload:', error);
            progressBar.classList.add('bg-danger');
            this.updateProgress(progressBar, statusDiv, 0, 'Error en upload: ' + error.message);
            this.showNotification('Error al subir archivo: ' + error.message, 'error');
        }
    }

    async handleRegularUpload(form) {
        // Para archivos pequeños, usar el método tradicional con HTMX
        const progressContainer = form.querySelector('.upload-progress-container');
        const progressBar = progressContainer.querySelector('.progress-bar');
        const statusDiv = progressContainer.querySelector('.upload-status');
        
        progressContainer.style.display = 'block';
        this.updateProgress(progressBar, statusDiv, 50, 'Subiendo archivo...');
        
        try {
            // Usar fetch para enviar el formulario
            const formData = new FormData(form);
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'X-Requested-With': 'XMLHttpRequest'
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
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
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
            
            xhr.addEventListener('error', () => {
                reject(new Error('Network error during upload'));
            });
            
            xhr.addEventListener('timeout', () => {
                reject(new Error('Upload timeout'));
            });
            
            xhr.open('PUT', presignedUrl);
            xhr.setRequestHeader('Content-Type', file.type);
            xhr.timeout = 300000; // 5 minutos timeout
            xhr.send(file);
        });
    }

    async confirmUpload(key, projectId, phaseId, sizeBytes, contentType) {
        const response = await fetch('/files/confirm-upload/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
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
        // Trigger para recargar archivos usando HTMX
        const event = new CustomEvent('fileUploaded');
        document.body.dispatchEvent(event);
        
        // También intentar recargar contenedores específicos
        const phaseId = this.extractPhaseId(form.action);
        if (phaseId) {
            const container = document.getElementById(`files-container-${phaseId}`);
            if (container && window.htmx) {
                htmx.trigger(container, 'fileUploaded');
            }
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
}

// Patrón singleton para evitar múltiples instancias y event listeners duplicados
let largeFileUploaderInstance = null;

function initializeLargeFileUploader() {
    if (!largeFileUploaderInstance) {
        largeFileUploaderInstance = new LargeFileUploader();
        console.log('✅ LargeFileUploader inicializado (singleton)');
    } else {
        // Solo reinicializar formularios nuevos sin crear nueva instancia
        largeFileUploaderInstance.init();
        console.log('🔄 LargeFileUploader reinicializado (reutilizando instancia)');
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
