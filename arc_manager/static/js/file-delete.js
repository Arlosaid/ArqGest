/**
 * Sistema de Eliminación de Archivos con Modal de Confirmación
 * Maneja la eliminación segura de archivos con confirmación visual y prevención de bugs
 */

class FileDeleteManager {
    constructor() {
        this.deletingFiles = new Set(); // Prevenir eliminaciones duplicadas
        this.modalInstance = null;
        this.currentFileData = null;
        this.init();
    }

    init() {
        // Crear modal de confirmación una sola vez
        this.createConfirmationModal();
        
        // Configurar event delegation para botones de eliminar
        document.addEventListener('click', (e) => {
            const deleteBtn = e.target.closest('.file-delete-btn');
            if (deleteBtn && !deleteBtn.disabled) {
                e.preventDefault();
                e.stopPropagation();
                this.handleDeleteClick(deleteBtn);
            }
        });
    }

    createConfirmationModal() {
        // Remover modal existente si hay uno
        const existingModal = document.getElementById('fileDeleteModal');
        if (existingModal) {
            existingModal.remove();
        }

        const modalHtml = `
        <div class="modal fade" id="fileDeleteModal" tabindex="-1" aria-labelledby="fileDeleteModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header bg-danger text-white">
                        <h5 class="modal-title" id="fileDeleteModalLabel">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            Confirmar eliminación
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="text-center mb-3">
                            <i class="fas fa-file-alt text-danger" style="font-size: 3rem; opacity: 0.7;"></i>
                        </div>
                        <p class="mb-3">¿Estás seguro de que deseas eliminar el siguiente archivo?</p>
                        <div class="alert alert-light border">
                            <div class="d-flex align-items-center">
                                <i class="fas fa-file me-2" id="fileIconPreview"></i>
                                <div class="flex-grow-1">
                                    <strong id="fileNamePreview"></strong>
                                    <br>
                                    <small class="text-muted" id="fileMetaPreview"></small>
                                </div>
                            </div>
                        </div>
                        <p class="text-muted small mb-0">
                            <i class="fas fa-info-circle me-1"></i>
                            Esta acción no se puede deshacer.
                        </p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            <i class="fas fa-times me-1"></i>
                            Cancelar
                        </button>
                        <button type="button" class="btn btn-danger" id="confirmDeleteFileBtn">
                            <i class="fas fa-trash me-1"></i>
                            Eliminar archivo
                        </button>
                    </div>
                </div>
            </div>
        </div>`;

        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Inicializar modal de Bootstrap
        const modalElement = document.getElementById('fileDeleteModal');
        this.modalInstance = new bootstrap.Modal(modalElement);

        // Configurar botón de confirmación
        document.getElementById('confirmDeleteFileBtn').addEventListener('click', () => {
            this.executeDelete();
        });
    }

    handleDeleteClick(deleteBtn) {
        // Extraer información del archivo
        const fileId = this.extractFileId(deleteBtn);
        const deleteUrl = deleteBtn.dataset.deleteUrl;
        
        if (!fileId || !deleteUrl) {
            console.error('No se pudo extraer file ID o URL de eliminación');
            return;
        }

        // Verificar si ya se está eliminando
        if (this.deletingFiles.has(fileId)) {
            console.warn('Archivo ya en proceso de eliminación:', fileId);
            return;
        }

        // Obtener información del archivo del DOM
        const fileElement = document.getElementById(`file-${fileId}`);
        if (!fileElement) {
            console.error('No se encontró el elemento del archivo:', fileId);
            return;
        }

        const fileName = this.extractFileName(fileElement);
        const fileMeta = this.extractFileMeta(fileElement);
        const fileIcon = this.extractFileIcon(fileElement);

        // Guardar datos del archivo actual
        this.currentFileData = {
            id: fileId,
            url: deleteUrl,
            element: fileElement,
            button: deleteBtn,
            name: fileName,
            meta: fileMeta,
            icon: fileIcon
        };

        // Actualizar modal con información del archivo
        this.updateModalContent(fileName, fileMeta, fileIcon);

        // Mostrar modal
        this.modalInstance.show();
    }

    updateModalContent(fileName, fileMeta, fileIcon) {
        const fileNameEl = document.getElementById('fileNamePreview');
        const fileMetaEl = document.getElementById('fileMetaPreview');
        const fileIconEl = document.getElementById('fileIconPreview');

        if (fileNameEl) fileNameEl.textContent = fileName;
        if (fileMetaEl) fileMetaEl.textContent = fileMeta;
        if (fileIconEl) {
            fileIconEl.className = fileIcon;
        }
    }

    async executeDelete() {
        if (!this.currentFileData) {
            console.error('No hay datos de archivo para eliminar');
            return;
        }

        const { id, url, element, button } = this.currentFileData;

        // Ensure trailing slash to avoid 301 redirects
        let deleteUrl = url;
        if (!deleteUrl.endsWith('/')) {
            deleteUrl += '/';
        }

        // Marcar como en proceso de eliminación
        this.deletingFiles.add(id);

        // Deshabilitar botón de confirmación
        const confirmBtn = document.getElementById('confirmDeleteFileBtn');
        const originalBtnHtml = confirmBtn.innerHTML;
        confirmBtn.disabled = true;
        confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Eliminando...';

        try {
            // Realizar petición de eliminación
            const response = await fetch(deleteUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'HX-Request': 'true'
                }
            });

            // Check for redirects
            if (response.redirected && response.url.includes('/login/')) {
                window.location.href = response.url;
                return;
            }

            if (!response.ok) {
                throw new Error(`Error del servidor: ${response.status}`);
            }

            // Éxito: cerrar modal
            this.modalInstance.hide();

            // Animación de desaparición suave
            element.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
            element.style.opacity = '0';
            element.style.transform = 'scale(0.95)';

            // Esperar animación y remover elemento
            setTimeout(() => {
                element.remove();
                
                // Verificar si quedan archivos
                this.checkEmptyState(element);
            }, 300);

            // Mostrar notificación de éxito
            this.showNotification('Archivo eliminado exitosamente', 'success');

            // Actualizar contador de archivos
            this.updateFileCounter(element);

            // Disparar evento para actualizar lista
            this.triggerFileListUpdate();

        } catch (error) {
            console.error('Error al eliminar archivo:', error);
            
            // Mostrar notificación de error
            this.showNotification('Error al eliminar el archivo', 'error');
            
            // Cerrar modal
            this.modalInstance.hide();
        } finally {
            // Limpiar estado
            this.deletingFiles.delete(id);
            this.currentFileData = null;

            // Restaurar botón
            if (confirmBtn) {
                confirmBtn.disabled = false;
                confirmBtn.innerHTML = originalBtnHtml;
            }
        }
    }

    extractFileId(button) {
        // Obtener de data-file-id
        if (button.dataset.fileId) {
            return button.dataset.fileId;
        }

        // Como fallback, intentar extraer de data-delete-url
        const deleteUrl = button.dataset.deleteUrl;
        if (deleteUrl) {
            const match = deleteUrl.match(/\/files\/delete\/(\d+)/);
            if (match) return match[1];
        }

        return null;
    }

    extractFileName(fileElement) {
        // Intentar obtener de varios lugares
        const nameElement = fileElement.querySelector('.file-name, .file-name-full, [title]');
        if (nameElement) {
            // Usar innerText para evitar texto oculto duplicado
            return nameElement.innerText.trim() || nameElement.getAttribute('title');
        }
        return 'Archivo sin nombre';
    }

    extractFileMeta(fileElement) {
        const sizeElement = fileElement.querySelector('.file-size');
        const typeElement = fileElement.querySelector('.file-type');
        const dateElement = fileElement.querySelector('.file-date');

        const parts = [];
        if (sizeElement) parts.push(sizeElement.textContent.trim());
        if (typeElement) parts.push(typeElement.textContent.trim());
        if (dateElement) parts.push(dateElement.textContent.trim());

        return parts.length > 0 ? parts.join(' • ') : 'Sin metadatos';
    }

    extractFileIcon(fileElement) {
        const iconElement = fileElement.querySelector('.file-icon i, .fas, .far');
        if (iconElement) {
            return iconElement.className;
        }
        return 'fas fa-file';
    }

    checkEmptyState(deletedElement) {
        // Encontrar el contenedor de archivos
        const container = deletedElement.closest('[id^="files-container-"], [id^="files-grid-"]');
        if (!container) return;

        // Contar archivos restantes
        const remainingFiles = container.querySelectorAll('.file-item, .file-card').length;
        
        if (remainingFiles === 0) {
            // Mostrar mensaje de "sin archivos"
            const emptyMessage = `
                <div class="no-files-message text-center py-5" style="grid-column: 1 / -1;">
                    <i class="fas fa-folder-open" style="font-size: 3rem; margin-bottom: 1rem; display: block; color: #6b7280;"></i>
                    <p class="text-muted">No se encontraron archivos</p>
                </div>
            `;
            container.innerHTML = emptyMessage;
        }
    }

    updateFileCounter(fileElement) {
        // Buscar el contenedor de la fase para obtener el phaseId
        const filesContainer = fileElement.closest('[id^="files-grid-"], [id^="files-container-"], [id^="files-list-"], [id^="filesTableBody-"]');
        if (!filesContainer) {
            console.warn('No se encontró el contenedor de archivos para actualizar el contador');
            return;
        }

        // Extraer phaseId del ID del contenedor
        // Formatos posibles: files-grid-123, files-container-123, files-list-123, filesTableBody-123
        const containerId = filesContainer.id;
        const phaseIdMatch = containerId.match(/(\d+)$/);
        
        if (!phaseIdMatch) {
            console.warn('No se pudo extraer el phaseId del contenedor:', containerId);
            return;
        }

        const phaseId = phaseIdMatch[1];
        
        // Buscar el badge del contador
        const counterBadge = document.getElementById(`file-count-${phaseId}`);
        if (!counterBadge) {
            console.warn('No se encontró el badge del contador para la fase:', phaseId);
            return;
        }

        // Extraer el número actual y decrementarlo
        const counterText = counterBadge.textContent.trim();
        const currentCount = parseInt(counterText.match(/\d+/)[0]);
        
        if (isNaN(currentCount) || currentCount <= 0) {
            console.warn('Contador inválido o ya es 0:', currentCount);
            return;
        }

        const newCount = currentCount - 1;
        
        // Actualizar el texto manteniendo la traducción "documentos"
        const documentosText = counterText.includes('documento') ? counterText.match(/\d+\s+(.+)/)[1] : 'documentos';
        counterBadge.textContent = `${newCount} ${documentosText}`;
        
        console.log(`✅ Contador actualizado: ${currentCount} → ${newCount} documentos (Fase ${phaseId})`);
    }

    triggerFileListUpdate() {
        // Disparar evento personalizado para actualizar listas
        document.body.dispatchEvent(new CustomEvent('fileDeleted'));
        
        // También disparar evento de fileUploaded (para compatibilidad)
        document.body.dispatchEvent(new CustomEvent('fileUploaded'));
    }

    getCSRFToken() {
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

    showNotification(message, type = 'info') {
        // Usar el sistema de notificaciones global
        if (window.notifications) {
            if (type === 'success') {
                window.notifications.success(message);
            } else if (type === 'error') {
                window.notifications.error(message);
            } else {
                window.notifications.show(message, type);
            }
        } else if (window.showGlobalNotification) {
            window.showGlobalNotification(message, type);
        } else {
            // Fallback: crear notificación simple
            const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
            const alertHtml = `
                <div class="alert ${alertClass} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3" 
                     role="alert" style="z-index: 9999; min-width: 300px;">
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', alertHtml);
            
            // Auto-remover después de 5 segundos
            setTimeout(() => {
                const alert = document.querySelector('.alert');
                if (alert) alert.remove();
            }, 5000);
        }
    }
}

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (!window.fileDeleteManager) {
            window.fileDeleteManager = new FileDeleteManager();
        }
    });
} else {
    // DOM ya está listo
    if (!window.fileDeleteManager) {
        window.fileDeleteManager = new FileDeleteManager();
    }
}

// También inicializar en contenido dinámico
document.addEventListener('htmx:afterSwap', () => {
    if (!window.fileDeleteManager) {
        window.fileDeleteManager = new FileDeleteManager();
    }
});

