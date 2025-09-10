/**
 * 📊 Sistema de Progreso de Upload de Archivos
 * Maneja el progreso visual durante uploads con HTMX
 */
class UploadProgressManager {
    constructor() {
        this.activeUploads = new Map();
        this.init();
    }

    init() {
        console.log('🚀 Upload Progress Manager initialized');
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Antes de enviar la petición HTMX
        document.addEventListener('htmx:beforeSend', (event) => {
            this.handleBeforeSend(event);
        });

        // Progreso del upload
        document.addEventListener('htmx:xhr:progress', (event) => {
            this.handleProgress(event);
        });

        // Después de la respuesta
        document.addEventListener('htmx:afterRequest', (event) => {
            this.handleAfterRequest(event);
        });

        // En caso de error
        document.addEventListener('htmx:responseError', (event) => {
            this.handleError(event);
        });
    }

    handleBeforeSend(event) {
        const form = event.target;
        
        // Solo manejar formularios de upload de archivos
        if (!form.classList || !form.classList.contains('file-upload-form')) {
            return;
        }

        const phaseId = this.extractPhaseId(form);
        if (!phaseId) return;

        console.log(`📤 Starting upload for phase ${phaseId}`);
        
        // Calcular tamaño total de archivos
        const fileInput = form.querySelector('.file-input');
        const totalSize = this.calculateTotalFileSize(fileInput);
        
        // Iniciar progreso visual
        this.startUploadProgress(phaseId, totalSize);
        
        // Guardar información del upload
        this.activeUploads.set(phaseId, {
            startTime: Date.now(),
            totalSize: totalSize,
            uploadedSize: 0
        });
    }

    handleProgress(event) {
        // HTMX no expone nativamente el progreso de upload
        // Simulamos progreso basado en tiempo para archivos grandes
        const form = event.target;
        if (!form.classList || !form.classList.contains('file-upload-form')) {
            return;
        }

        const phaseId = this.extractPhaseId(form);
        if (!phaseId || !this.activeUploads.has(phaseId)) return;

        // Simular progreso gradual para UX
        this.simulateProgress(phaseId);
    }

    handleAfterRequest(event) {
        const form = event.target;
        
        if (!form.classList || !form.classList.contains('file-upload-form')) {
            return;
        }

        const phaseId = this.extractPhaseId(form);
        if (!phaseId) return;

        if (event.detail.successful) {
            console.log(`✅ Upload completed successfully for phase ${phaseId}`);
            this.completeUploadProgress(phaseId);
        } else {
            console.log(`❌ Upload failed for phase ${phaseId}`);
            this.handleError(event);
        }
    }

    handleError(event) {
        const form = event.target;
        
        if (!form.classList || !form.classList.contains('file-upload-form')) {
            return;
        }

        const phaseId = this.extractPhaseId(form);
        if (!phaseId) return;

        console.log(`🚨 Upload error for phase ${phaseId}`);
        this.showUploadError(phaseId);
    }

    extractPhaseId(form) {
        const fileInput = form.querySelector('.file-input');
        if (!fileInput || !fileInput.id) return null;
        
        return fileInput.id.split('-').pop();
    }

    calculateTotalFileSize(fileInput) {
        if (!fileInput || !fileInput.files) return 0;
        
        let totalSize = 0;
        for (let file of fileInput.files) {
            totalSize += file.size;
        }
        return totalSize;
    }

    startUploadProgress(phaseId, totalSize) {
        const progressContainer = document.getElementById(`upload-progress-${phaseId}`);
        const uploadBtn = document.querySelector(`#file-input-${phaseId}`).closest('form').querySelector('.upload-btn');
        
        if (!progressContainer || !uploadBtn) return;

        // Mostrar contenedor de progreso
        progressContainer.style.display = 'block';
        
        // Cambiar estado del botón
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = `
            <i class="fas fa-spinner fa-spin upload-icon"></i>
            <span class="upload-text ms-1">Subiendo...</span>
        `;

        // Inicializar textos
        const statusText = progressContainer.querySelector('.upload-status-text');
        const sizeText = this.formatFileSize(totalSize);
        
        if (statusText) {
            statusText.textContent = `Subiendo ${sizeText}...`;
        }

        // Comenzar simulación de progreso
        this.updateProgress(phaseId, 5); // Empezar con 5%
    }

    simulateProgress(phaseId) {
        if (!this.activeUploads.has(phaseId)) return;

        const uploadInfo = this.activeUploads.get(phaseId);
        const elapsed = Date.now() - uploadInfo.startTime;
        
        // Simular progreso basado en tiempo y tamaño
        let progress = Math.min(90, (elapsed / 1000) * 10); // Max 90% hasta completar
        
        // Ajustar por tamaño del archivo
        if (uploadInfo.totalSize > 50 * 1024 * 1024) { // > 50MB
            progress = Math.min(80, progress * 0.7); // Más lento para archivos grandes
        }

        this.updateProgress(phaseId, progress);
    }

    updateProgress(phaseId, percentage) {
        const progressContainer = document.getElementById(`upload-progress-${phaseId}`);
        if (!progressContainer) return;

        const progressBar = progressContainer.querySelector('.progress-bar');
        const percentageSpan = progressContainer.querySelector('.upload-percentage');
        const timeSpan = progressContainer.querySelector('.upload-time');
        const speedSpan = progressContainer.querySelector('.upload-speed');

        if (progressBar) {
            progressBar.style.width = `${percentage}%`;
            progressBar.setAttribute('aria-valuenow', percentage);
        }

        if (percentageSpan) {
            percentageSpan.textContent = `${Math.round(percentage)}%`;
        }

        // Calcular tiempo estimado
        if (this.activeUploads.has(phaseId)) {
            const uploadInfo = this.activeUploads.get(phaseId);
            const elapsed = Date.now() - uploadInfo.startTime;
            const speed = (percentage / 100) * uploadInfo.totalSize / (elapsed / 1000);
            
            if (timeSpan && percentage > 5) {
                const remaining = ((100 - percentage) / percentage) * elapsed;
                timeSpan.textContent = this.formatTime(remaining);
            }

            if (speedSpan && speed > 0) {
                speedSpan.textContent = `(${this.formatSpeed(speed)})`;
            }
        }
    }

    completeUploadProgress(phaseId) {
        const progressContainer = document.getElementById(`upload-progress-${phaseId}`);
        const uploadBtn = document.querySelector(`#file-input-${phaseId}`).closest('form').querySelector('.upload-btn');
        
        if (!progressContainer) return;

        // Completar al 100%
        this.updateProgress(phaseId, 100);

        const statusText = progressContainer.querySelector('.upload-status-text');
        if (statusText) {
            statusText.innerHTML = '<i class="fas fa-check me-1 text-success"></i>¡Upload completado!';
        }

        // Ocultar progreso después de 2 segundos
        setTimeout(() => {
            progressContainer.style.display = 'none';
            
            // Restaurar botón
            if (uploadBtn) {
                uploadBtn.disabled = false;
                uploadBtn.innerHTML = `
                    <i class="fas fa-upload upload-icon"></i>
                    <span class="upload-text ms-1">Subir</span>
                `;
            }
            
            // Limpiar información del upload
            this.activeUploads.delete(phaseId);
        }, 2000);
    }

    showUploadError(phaseId) {
        const progressContainer = document.getElementById(`upload-progress-${phaseId}`);
        const uploadBtn = document.querySelector(`#file-input-${phaseId}`).closest('form').querySelector('.upload-btn');
        
        if (!progressContainer) return;

        const statusText = progressContainer.querySelector('.upload-status-text');
        const progressBar = progressContainer.querySelector('.progress-bar');
        
        if (statusText) {
            statusText.innerHTML = '<i class="fas fa-exclamation-triangle me-1 text-danger"></i>Error en el upload';
        }

        if (progressBar) {
            progressBar.classList.remove('progress-bar-striped', 'progress-bar-animated');
            progressBar.classList.add('bg-danger');
        }

        // Ocultar progreso después de 3 segundos
        setTimeout(() => {
            progressContainer.style.display = 'none';
            
            // Restaurar botón
            if (uploadBtn) {
                uploadBtn.disabled = false;
                uploadBtn.innerHTML = `
                    <i class="fas fa-upload upload-icon"></i>
                    <span class="upload-text ms-1">Subir</span>
                `;
            }
            
            // Limpiar información del upload
            this.activeUploads.delete(phaseId);
        }, 3000);
    }

    // Utilidades de formato
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    formatTime(ms) {
        const seconds = Math.floor(ms / 1000);
        if (seconds < 60) return `${seconds}s restantes`;
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}m ${remainingSeconds}s restantes`;
    }

    formatSpeed(bytesPerSecond) {
        return this.formatFileSize(bytesPerSecond) + '/s';
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    window.uploadProgressManager = new UploadProgressManager();
});
