/**
 * 📱 Mobile Upload Optimizer
 * Sistema optimizado para subida de múltiples archivos en dispositivos móviles
 * Mejores prácticas: upload secuencial, gestión de memoria, UX adaptativo
 */

class MobileUploadOptimizer {
    constructor() {
        this.isMobile = this.detectMobile();
        this.uploadQueue = [];
        this.isUploading = false;
        this.currentUpload = null;
        
        // Usar configuración centralizada
        const config = window.FILE_UPLOAD_CONFIG || {};
        this.maxConcurrentUploads = this.isMobile 
            ? (config.MOBILE_MAX_CONCURRENT || 1)
            : (config.DESKTOP_MAX_CONCURRENT || 2);
        
        // Usar límite específico para móviles si está disponible
        const maxFileSizeMB = this.isMobile 
            ? (config.MAX_FILE_SIZE_MOBILE_MB || config.MAX_FILE_SIZE_MB || 1500)
            : (config.MAX_FILE_SIZE_MB || 1500);
        
        this.maxMobileFileSize = maxFileSizeMB * 1024 * 1024;
        
        // Solo loguear en modo debug
        if (window.location.search.includes('debug=upload')) {
            console.log(`📱 Upload Optimizer - Límite: ${maxFileSizeMB}MB (${this.isMobile ? 'Mobile' : 'Desktop'})`);
        }
        
        this.mobileChunkSize = this.isMobile 
            ? ((config.MOBILE_CHUNK_SIZE_MB || 1) * 1024 * 1024)
            : ((config.CHUNK_SIZE_MB || 5) * 1024 * 1024);
        
        this.init();
    }

    detectMobile() {
        const userAgent = navigator.userAgent;
        const mobileKeywords = /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i;
        const isSmallScreen = window.innerWidth <= 768;
        const isTouchDevice = 'ontouchstart' in window;
        
        return mobileKeywords.test(userAgent) || (isSmallScreen && isTouchDevice);
    }

    init() {
        if (this.isMobile) {
            this.setupMobileOptimizations();
        }
        
        // Interceptar uploads del upload_progress.js existente
        this.interceptExistingUploads();
        
        // Log solo en modo debug explícito
        if (window.location.search.includes('debug=upload')) {
            console.log(`📱 Mobile Upload Optimizer: ${this.isMobile ? 'ENABLED' : 'DISABLED'}`);
        }
    }

    setupMobileOptimizations() {
        // Reducir límites para mobile
        document.documentElement.style.setProperty('--mobile-file-grid-cols', '2');
        
        // Prevenir zoom en inputs de archivo
        const fileInputs = document.querySelectorAll('input[type="file"]');
        fileInputs.forEach(input => {
            input.addEventListener('click', () => {
                // Pequeña pausa para prevenir zoom automático
                setTimeout(() => {
                    const viewport = document.querySelector('meta[name="viewport"]');
                    if (viewport) {
                        viewport.setAttribute('content', 
                            'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no'
                        );
                    }
                }, 100);
            });
        });

        // Optimizar memoria con cleanup automático
        this.setupMemoryManagement();
    }

    setupMemoryManagement() {
        // Limpiar memoria cada 30 segundos en mobile
        if (this.isMobile) {
            setInterval(() => {
                this.cleanupMemory();
            }, 30000);
        }

        // Advertir sobre batería baja
        if ('getBattery' in navigator) {
            navigator.getBattery().then(battery => {
                if (battery.level < 0.2) {
                    this.showBatteryWarning();
                }
            });
        }
    }

    interceptExistingUploads() {
        // Interceptar el upload_progress.js para optimizar mobile
        const originalProgressManager = window.uploadProgressManager;
        
        if (originalProgressManager) {
            const originalHandleUpload = originalProgressManager.handleUpload;
            
            originalProgressManager.handleUpload = (form, files, phaseId) => {
                if (this.isMobile && files.length > 1) {
                    // En mobile, usar nuestro sistema optimizado
                    this.processMobileMultiUpload(form, files, phaseId);
                    return false; // Cancelar upload original
                } else {
                    // Desktop: usar sistema original
                    return originalHandleUpload.call(originalProgressManager, form, files, phaseId);
                }
            };
        }
    }

    async processMobileMultiUpload(form, files, phaseId) {
        console.log(`📱 Procesando ${files.length} archivos en mobile`);
        
        // Validaciones específicas para mobile
        const validFiles = this.validateMobileFiles(files);
        if (validFiles.length === 0) return;

        // Mostrar UI optimizada para mobile
        this.showMobileUploadProgress(phaseId, validFiles.length);
        
        // Upload secuencial (uno por vez en mobile)
        for (let i = 0; i < validFiles.length; i++) {
            const file = validFiles[i];
            
            try {
                // Actualizar progreso por archivo
                this.updateMobileProgress(phaseId, i + 1, validFiles.length, file.name);
                
                // Upload individual con gestión de memoria
                await this.uploadSingleFileMobile(form, file, phaseId);
                
                // Pequeña pausa para evitar saturar el servidor
                await this.sleep(500);
                
            } catch (error) {
                console.error(`Error uploading ${file.name}:`, error);
                this.showMobileError(phaseId, file.name, error);
            }
        }
        
        // Completar upload
        this.completeMobileUpload(phaseId);
    }

    validateMobileFiles(files) {
        const validFiles = [];
        const invalidFiles = [];
        
        for (const file of files) {
            // Validar tamaño específico para mobile
            if (file.size > this.maxMobileFileSize) {
                invalidFiles.push({
                    name: file.name,
                    reason: `Archivo muy grande para mobile (máx ${this.maxMobileFileSize / 1024 / 1024}MB)`
                });
                continue;
            }
            
            // Validar memoria disponible estimada
            if (!this.hasEnoughMobileMemory(file.size)) {
                invalidFiles.push({
                    name: file.name,
                    reason: 'Memoria insuficiente en dispositivo'
                });
                continue;
            }
            
            validFiles.push(file);
        }
        
        if (invalidFiles.length > 0) {
            this.showMobileValidationErrors(invalidFiles);
        }
        
        return validFiles;
    }

    hasEnoughMobileMemory(fileSize) {
        // Estimar memoria disponible (muy básico)
        const estimatedMemoryUsage = fileSize * 2; // Factor de seguridad
        const deviceMemory = navigator.deviceMemory || 4; // GB estimados
        const availableMemory = deviceMemory * 1024 * 1024 * 1024 * 0.3; // 30% disponible
        
        return estimatedMemoryUsage < availableMemory;
    }

    async uploadSingleFileMobile(form, file, phaseId) {
        return new Promise((resolve, reject) => {
            const formData = new FormData(form);
            formData.delete('files'); // Remover archivos múltiples
            formData.append('files', file); // Agregar solo este archivo
            
            const xhr = new XMLHttpRequest();
            
            // Configurar timeouts más largos para mobile
            xhr.timeout = this.isMobile ? 120000 : 60000; // 2 min mobile, 1 min desktop
            
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percent = Math.round((e.loaded / e.total) * 100);
                    this.updateMobileFileProgress(phaseId, file.name, percent);
                }
            });
            
            xhr.addEventListener('load', () => {
                if (xhr.status === 200) {
                    resolve(xhr.response);
                } else {
                    reject(new Error(`HTTP ${xhr.status}: ${xhr.statusText}`));
                }
            });
            
            xhr.addEventListener('error', () => {
                reject(new Error('Error de conexión'));
            });
            
            xhr.addEventListener('timeout', () => {
                reject(new Error('Timeout - conexión lenta'));
            });
            
            xhr.open('POST', form.action);
            
            // Headers optimizados para mobile
            xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
            xhr.setRequestHeader('X-Mobile-Upload', 'true');
            
            xhr.send(formData);
        });
    }

    showMobileUploadProgress(phaseId, totalFiles) {
        const progressContainer = document.getElementById(`upload-progress-${phaseId}`);
        if (!progressContainer) return;
        
        progressContainer.style.display = 'block';
        progressContainer.innerHTML = `
            <div class="mobile-upload-progress">
                <div class="mobile-progress-header">
                    <h6><i class="fas fa-mobile-alt me-2"></i>Subiendo archivos (modo móvil)</h6>
                    <small class="text-muted">Optimizado para tu dispositivo</small>
                </div>
                
                <div class="mobile-overall-progress mb-3">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <span class="mobile-overall-text">Progreso general</span>
                        <span class="mobile-overall-count">0 / ${totalFiles}</span>
                    </div>
                    <div class="progress">
                        <div class="progress-bar mobile-overall-bar" style="width: 0%"></div>
                    </div>
                </div>
                
                <div class="mobile-current-file">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <span class="mobile-current-name">Preparando...</span>
                        <span class="mobile-current-percent">0%</span>
                    </div>
                    <div class="progress progress-sm">
                        <div class="progress-bar mobile-current-bar" style="width: 0%"></div>
                    </div>
                </div>
                
                <div class="mobile-upload-tips mt-2">
                    <small class="text-info">
                        <i class="fas fa-lightbulb me-1"></i>
                        Mantén la app abierta para mejor rendimiento
                    </small>
                </div>
            </div>
        `;
    }

    updateMobileProgress(phaseId, currentFile, totalFiles, fileName) {
        const overallPercent = Math.round((currentFile / totalFiles) * 100);
        
        // Actualizar progreso general
        const overallBar = document.querySelector(`#upload-progress-${phaseId} .mobile-overall-bar`);
        const overallCount = document.querySelector(`#upload-progress-${phaseId} .mobile-overall-count`);
        
        if (overallBar) overallBar.style.width = `${overallPercent}%`;
        if (overallCount) overallCount.textContent = `${currentFile} / ${totalFiles}`;
        
        // Actualizar archivo actual
        const currentName = document.querySelector(`#upload-progress-${phaseId} .mobile-current-name`);
        if (currentName) {
            currentName.textContent = fileName.length > 25 
                ? fileName.substring(0, 25) + '...' 
                : fileName;
        }
        
        // Reset progreso del archivo actual
        this.updateMobileFileProgress(phaseId, fileName, 0);
    }

    updateMobileFileProgress(phaseId, fileName, percent) {
        const currentBar = document.querySelector(`#upload-progress-${phaseId} .mobile-current-bar`);
        const currentPercent = document.querySelector(`#upload-progress-${phaseId} .mobile-current-percent`);
        
        if (currentBar) currentBar.style.width = `${percent}%`;
        if (currentPercent) currentPercent.textContent = `${percent}%`;
    }

    completeMobileUpload(phaseId) {
        const progressContainer = document.getElementById(`upload-progress-${phaseId}`);
        if (!progressContainer) return;
        
        progressContainer.innerHTML = `
            <div class="alert alert-success text-center">
                <i class="fas fa-check-circle fa-2x mb-2"></i>
                <h6>¡Archivos subidos exitosamente!</h6>
                <small>Optimizado para móvil completado</small>
            </div>
        `;
        
        // Limpiar después de 3 segundos
        setTimeout(() => {
            progressContainer.style.display = 'none';
            // Trigger recarga de archivos
            document.body.dispatchEvent(new CustomEvent('fileUploaded'));
        }, 3000);
    }

    showMobileError(phaseId, fileName, error) {
        // Mostrar error específico sin interrumpir el flujo
        const errorContainer = document.createElement('div');
        errorContainer.className = 'alert alert-warning alert-dismissible fade show mt-2';
        errorContainer.innerHTML = `
            <small>
                <strong>${fileName}:</strong> ${error.message}
                <button type="button" class="btn-close btn-close-sm" data-bs-dismiss="alert"></button>
            </small>
        `;
        
        const progressContainer = document.getElementById(`upload-progress-${phaseId}`);
        if (progressContainer) {
            progressContainer.appendChild(errorContainer);
        }
    }

    showMobileValidationErrors(invalidFiles) {
        const errorHtml = invalidFiles.map(file => 
            `<li><strong>${file.name}:</strong> ${file.reason}</li>`
        ).join('');
        
        // Mostrar modal o alerta con errores
        const errorAlert = document.createElement('div');
        errorAlert.className = 'alert alert-danger alert-dismissible fade show';
        errorAlert.innerHTML = `
            <h6><i class="fas fa-exclamation-triangle me-2"></i>Archivos no válidos para móvil</h6>
            <ul class="mb-0">${errorHtml}</ul>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(errorAlert);
        
        // Auto-remover después de 8 segundos
        setTimeout(() => {
            if (errorAlert.parentNode) {
                errorAlert.remove();
            }
        }, 8000);
    }

    showBatteryWarning() {
        const warning = document.createElement('div');
        warning.className = 'alert alert-warning alert-dismissible fade show';
        warning.innerHTML = `
            <i class="fas fa-battery-quarter me-2"></i>
            <strong>Batería baja detectada.</strong> 
            Considera conectar el cargador antes de subir archivos grandes.
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(warning);
        
        setTimeout(() => {
            if (warning.parentNode) {
                warning.remove();
            }
        }, 10000);
    }

    cleanupMemory() {
        // Forzar garbage collection si está disponible
        if (window.gc) {
            window.gc();
        }
        
        // Limpiar referencias no utilizadas
        this.uploadQueue = this.uploadQueue.filter(item => item.status !== 'completed');
        
        // Solo loguear en modo debug
        if (window.location.search.includes('debug=true')) {
            console.log('📱 Mobile memory cleanup completed');
        }
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Inicializar automáticamente
document.addEventListener('DOMContentLoaded', function() {
    window.mobileUploadOptimizer = new MobileUploadOptimizer();
});

// CSS adicional para mobile (se puede mover a archivo CSS separado)
const mobileStyles = `
<style>
.mobile-upload-progress {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 1rem;
    border: 1px solid #dee2e6;
}

.mobile-progress-header h6 {
    margin: 0;
    color: #495057;
}

.mobile-overall-progress .progress {
    height: 8px;
}

.mobile-current-file .progress {
    height: 6px;
}

.mobile-upload-tips {
    border-top: 1px solid #dee2e6;
    padding-top: 0.5rem;
}

@media (max-width: 768px) {
    .files-grid {
        grid-template-columns: repeat(var(--mobile-file-grid-cols, 2), 1fr) !important;
        gap: 0.5rem !important;
    }
    
    .file-card {
        padding: 0.5rem !important;
    }
    
    .file-name {
        font-size: 0.8rem !important;
    }
}
</style>
`;

document.head.insertAdjacentHTML('beforeend', mobileStyles);
