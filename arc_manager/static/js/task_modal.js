/**
 * Task Modal Manager - Sistema unificado para modales de tareas
 * Maneja: carga de contenido, archivos, notas, eliminación con marcado visual
 * 
 * Patrón: Marcar para eliminar (strikethrough) -> Confirmar al guardar
 * Sin modales anidados para evitar conflictos de z-index y backdrop
 */

class TaskModalManager {
    constructor() {
        this.modal = null;
        this.modalContent = null;
        this.modalTitle = null;
        this.currentTaskId = null;
        this.currentMode = null; // 'detail' or 'edit'
        this.pendingDeletions = {
            files: new Set(),
            notes: new Set()
        };
        this.isLoading = false;
        
        this.init();
    }

    init() {
        // Esperar a que el DOM esté listo
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }

    setup() {
        this.modal = document.getElementById('taskUniversalModal');
        this.modalContent = document.getElementById('taskUniversalContent');
        this.modalTitle = document.getElementById('taskUniversalModalLabel');

        if (!this.modal || !this.modalContent) {
            console.warn('TaskModalManager: Modal elements not found');
            return;
        }

        // Event delegation para todo el modal
        this.modal.addEventListener('click', (e) => this.handleClick(e));
        
        // Limpiar al cerrar el modal
        this.modal.addEventListener('hidden.bs.modal', () => this.cleanup());
        
        // Escuchar evento de carga del modal (desde base.js)
        document.addEventListener('taskModalLoaded', (e) => this.onContentLoaded(e.detail));
        
        // Form submission
        this.modal.addEventListener('submit', (e) => this.handleSubmit(e));
        
        // Input events para contador de caracteres
        this.modal.addEventListener('input', (e) => this.handleInput(e));
    }

    /**
     * Abrir modal de tarea
     */
    open(type, taskId) {
        if (this.isLoading) return;
        
        this.currentTaskId = taskId;
        this.currentMode = type;
        this.pendingDeletions = { files: new Set(), notes: new Set() };
        this.isLoading = true;

        // Actualizar título
        this.modalTitle.textContent = type === 'detail' ? 'Detalles de la Tarea' : 'Editar Tarea';

        // Mostrar loading
        this.modalContent.innerHTML = `
            <div class="text-center p-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
            </div>
        `;

        // Mostrar modal si no está visible
        let modalInstance = bootstrap.Modal.getInstance(this.modal);
        if (!this.modal.classList.contains('show')) {
            this.cleanupBackdrops();
            if (modalInstance) {
                try { modalInstance.dispose(); } catch(e) {}
            }
            modalInstance = new bootstrap.Modal(this.modal, {
                backdrop: true,
                keyboard: true,
                focus: true
            });
            modalInstance.show();
        }

        // Cargar contenido
        const url = type === 'detail' 
            ? (document.body.dataset.taskDetailUrlTemplate || '').replace('0', taskId)
            : `/projects/tasks/${taskId}/edit/`;

        if (!url) {
            this.showError('URL no disponible');
            this.isLoading = false;
            return;
        }

        fetch(url)
            .then(response => {
                if (!response.ok) throw new Error('Error de red');
                return response.text();
            })
            .then(html => {
                this.modalContent.innerHTML = html;
                this.isLoading = false;
                this.onContentLoaded({ type, taskId });
            })
            .catch(error => {
                console.error('Error cargando modal:', error);
                this.showError('Error al cargar el contenido');
                this.isLoading = false;
            });
    }

    /**
     * Cuando el contenido se carga
     */
    onContentLoaded(detail) {
        const { type, taskId } = detail;
        
        // Inicializar componentes específicos
        this.initUploadZone();
        this.initCharCounters();
        
        // Si hay archivos/notas marcados para eliminar previamente, restaurar estado visual
        this.restorePendingDeletionStates();
    }

    /**
     * Manejar todos los clicks dentro del modal
     */
    handleClick(e) {
        const target = e.target;

        // Botón de eliminar archivo
        const deleteFileBtn = target.closest('[data-action="delete-file"]');
        if (deleteFileBtn) {
            e.preventDefault();
            e.stopPropagation();
            this.toggleFileForDeletion(deleteFileBtn);
            return;
        }

        // Botón de eliminar nota
        const deleteNoteBtn = target.closest('[data-action="delete-note"]');
        if (deleteNoteBtn) {
            e.preventDefault();
            e.stopPropagation();
            this.deleteNote(deleteNoteBtn);
            return;
        }

        // Botón de editar (desde detail -> edit)
        const editBtn = target.closest('[data-action="edit-task"]');
        if (editBtn) {
            e.preventDefault();
            e.stopPropagation();
            const taskId = editBtn.dataset.taskId || this.currentTaskId;
            this.open('edit', taskId);
            return;
        }

        // Botón de ver detalles (desde edit -> detail)
        const detailBtn = target.closest('[data-action="view-task"]');
        if (detailBtn) {
            e.preventDefault();
            e.stopPropagation();
            const taskId = detailBtn.dataset.taskId || this.currentTaskId;
            this.open('detail', taskId);
            return;
        }

        // Upload zone click
        const uploadZone = target.closest('[data-action="upload-zone"]');
        if (uploadZone) {
            e.preventDefault();
            e.stopPropagation();
            const fileInput = this.modalContent.querySelector('[data-upload-input]');
            if (fileInput) fileInput.click();
            return;
        }
    }

    /**
     * Marcar/desmarcar archivo para eliminación (strikethrough visual)
     */
    toggleFileForDeletion(btn) {
        const fileId = btn.dataset.fileId;
        const fileItem = btn.closest('.task-file-item');
        
        if (!fileItem || !fileId) return;

        if (this.pendingDeletions.files.has(fileId)) {
            // Desmarcar
            this.pendingDeletions.files.delete(fileId);
            fileItem.classList.remove('marked-for-deletion');
            fileItem.style.opacity = '';
            fileItem.style.textDecoration = '';
            btn.innerHTML = '<i class="fas fa-trash"></i>';
            btn.title = 'Marcar para eliminar';
            btn.classList.remove('btn-secondary');
            btn.classList.add('btn-outline-danger');
        } else {
            // Marcar para eliminación
            this.pendingDeletions.files.add(fileId);
            fileItem.classList.add('marked-for-deletion');
            fileItem.style.opacity = '0.5';
            fileItem.style.textDecoration = 'line-through';
            btn.innerHTML = '<i class="fas fa-undo"></i>';
            btn.title = 'Deshacer eliminación';
            btn.classList.remove('btn-outline-danger');
            btn.classList.add('btn-secondary');
        }
        
        this.updateDeleteWarning();
    }

    /**
     * Eliminar nota directamente
     */
    async deleteNote(btn) {
        const noteId = btn.dataset.noteId;
        const noteItem = btn.closest('.note-item');
        
        if (!noteItem || !noteId) return;

        if (!confirm('¿Estás seguro de que deseas eliminar este comentario?')) {
            return;
        }

        // Deshabilitar botón para evitar doble click
        btn.disabled = true;
        const originalContent = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        try {
            const response = await fetch(`/projects/tasks/notes/${noteId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (data.success) {
                // Eliminar elemento del DOM con animación
                noteItem.style.transition = 'all 0.3s ease';
                noteItem.style.opacity = '0';
                noteItem.style.transform = 'translateX(20px)';
                
                setTimeout(() => {
                    noteItem.remove();
                    
                    // Actualizar contador
                    const counterBadge = this.modalContent.querySelector('[data-notes-count]');
                    if (counterBadge) {
                        const currentCount = parseInt(counterBadge.textContent || '0');
                        counterBadge.textContent = Math.max(0, currentCount - 1);
                    }
                    
                    // Mostrar mensaje si no quedan notas
                    const notesList = this.modalContent.querySelector('[data-notes-list]');
                    if (notesList && !notesList.querySelector('.note-item')) {
                        const emptyState = `
                            <div class="text-muted text-center small py-3" data-notes-empty>
                                <i class="fas fa-comment-slash mb-2" style="font-size: 1.5rem; opacity: 0.5;"></i>
                                <p class="mb-0">No hay notas en esta tarea</p>
                            </div>
                        `;
                        notesList.insertAdjacentHTML('beforeend', emptyState);
                    }
                }, 300);
            } else {
                alert(data.error || 'Error al eliminar la nota');
                btn.disabled = false;
                btn.innerHTML = originalContent;
            }
        } catch (error) {
            console.error('Error deleting note:', error);
            alert('Error de conexión al eliminar la nota');
            btn.disabled = false;
            btn.innerHTML = originalContent;
        }
    }

    /**
     * Mostrar/ocultar advertencia de elementos pendientes de eliminar
     */
    updateDeleteWarning() {
        const warningEl = this.modalContent.querySelector('[data-delete-warning]');
        const totalPending = this.pendingDeletions.files.size; // Solo archivos
        
        if (!warningEl) {
            // Crear elemento de advertencia si no existe
            const footer = this.modalContent.querySelector('.modal-footer-modern, .task-simple-footer');
            if (footer && totalPending > 0) {
                const warning = document.createElement('div');
                warning.setAttribute('data-delete-warning', '');
                warning.className = 'alert alert-warning py-2 px-3 mb-2 small';
                warning.innerHTML = `<i class="fas fa-exclamation-triangle me-1"></i>
                    <span data-delete-count>${totalPending}</span> archivo(s) marcado(s) para eliminar. 
                    Se eliminarán al guardar.`;
                footer.parentNode.insertBefore(warning, footer);
            }
            return;
        }
        
        if (totalPending > 0) {
            warningEl.style.display = '';
            warningEl.querySelector('[data-delete-count]').textContent = totalPending;
        } else {
            warningEl.style.display = 'none';
        }
    }

    /**
     * Manejar envío de formulario
     */
    async handleSubmit(e) {
        const form = e.target.closest('form');
        if (!form) return;

        // Solo manejar el formulario de edición de tarea
        if (!form.id || !form.id.includes('editTaskForm')) return;

        e.preventDefault();

        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn ? submitBtn.innerHTML : '';

        // Verificar si hay elementos pendientes de eliminar
        const totalPending = this.pendingDeletions.files.size;
        
        if (totalPending > 0) {
            const confirmed = await this.confirmDeletions();
            if (!confirmed) return;
        }

        // Mostrar loading
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Guardando...';
        }

        try {
            // Primero eliminar archivos y notas marcados
            await this.processPendingDeletions();

            // Luego guardar el formulario
            const formData = new FormData(form);
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                // Cerrar modal y recargar página
                const modalInstance = bootstrap.Modal.getInstance(this.modal);
                if (modalInstance) modalInstance.hide();
                
                if (window.notifications) {
                    window.notifications.success('Tarea actualizada correctamente');
                }
                
                // Recargar para mostrar cambios
                window.location.reload();
            } else {
                throw new Error('Error al guardar');
            }
        } catch (error) {
            console.error('Error:', error);
            if (window.notifications) {
                window.notifications.error('Error al guardar la tarea');
            }
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }
        }
    }

    /**
     * Confirmar eliminaciones pendientes
     */
    confirmDeletions() {
        const fileCount = this.pendingDeletions.files.size;
        
        let message = 'Se eliminarán permanentemente:\n';
        if (fileCount > 0) message += `• ${fileCount} archivo(s)\n`;
        message += '\n¿Deseas continuar?';
        
        return confirm(message);
    }

    /**
     * Procesar eliminaciones pendientes
     */
    async processPendingDeletions() {
        const csrfToken = this.getCSRFToken();
        const errors = [];

        // Eliminar archivos
        for (const fileId of this.pendingDeletions.files) {
            try {
                const response = await fetch(`/files/${fileId}/delete/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                if (!response.ok) {
                    errors.push(`Error eliminando archivo ${fileId}`);
                }
            } catch (e) {
                errors.push(`Error eliminando archivo ${fileId}`);
            }
        }

        // Eliminar notas - YA NO SE USA (Eliminación directa)
        /*
        for (const noteId of this.pendingDeletions.notes) {
            try {
                const response = await fetch(`/projects/tasks/notes/${noteId}/delete/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                if (!response.ok) {
                    errors.push(`Error eliminando nota ${noteId}`);
                }
            } catch (e) {
                errors.push(`Error eliminando nota ${noteId}`);
            }
        }
        */

        if (errors.length > 0) {
            console.error('Errores durante eliminación:', errors);
        }

        // Limpiar pendientes
        this.pendingDeletions = { files: new Set(), notes: new Set() };
    }

    /**
     * Manejar eventos de input
     */
    handleInput(e) {
        // Contador de caracteres para notas
        if (e.target.matches('[data-char-counter]')) {
            const maxLength = parseInt(e.target.getAttribute('maxlength')) || 2000;
            const counterId = e.target.dataset.charCounter;
            const counter = this.modalContent.querySelector(`[data-counter-display="${counterId}"]`);
            if (counter) {
                counter.textContent = e.target.value.length;
            }
        }

        // Validar título no vacío
        if (e.target.matches('input[name="title"]')) {
            const submitBtn = this.modalContent.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = e.target.value.trim().length === 0;
            }
        }
    }

    /**
     * Inicializar zona de upload
     */
    initUploadZone() {
        const uploadZone = this.modalContent.querySelector('[data-action="upload-zone"]');
        const fileInput = this.modalContent.querySelector('[data-upload-input]');
        
        if (!uploadZone || !fileInput) return;

        // Drag & drop
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('dragover');
            uploadZone.style.borderColor = '#3b82f6';
            uploadZone.style.backgroundColor = '#f0f7ff';
        });

        uploadZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
            uploadZone.style.borderColor = '';
            uploadZone.style.backgroundColor = '';
        });

        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
            uploadZone.style.borderColor = '';
            uploadZone.style.backgroundColor = '';
            if (e.dataTransfer.files.length > 0) {
                this.handleFileUpload(e.dataTransfer.files[0], uploadZone);
            }
        });

        // File input change
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                this.handleFileUpload(fileInput.files[0], uploadZone);
            }
        });
    }

    /**
     * Manejar upload de archivo
     */
    async handleFileUpload(file, uploadZone) {
        const taskId = uploadZone.dataset.taskId;
        const phaseId = uploadZone.dataset.phaseId;
        const projectId = uploadZone.dataset.projectId;
        const currentFiles = parseInt(uploadZone.dataset.currentFiles) || 0;

        if (currentFiles >= 3) {
            if (window.notifications) {
                window.notifications.warning('Límite de 3 archivos por tarea alcanzado');
            }
            return;
        }

        // Mostrar progreso con información detallada
        const progressContainer = this.modalContent.querySelector('[data-upload-progress]');
        const progressBar = progressContainer?.querySelector('.progress-bar');
        const filenameEl = progressContainer?.querySelector('[data-upload-filename]');
        const percentEl = progressContainer?.querySelector('[data-upload-percent]');
        const speedEl = progressContainer?.querySelector('[data-upload-speed]');
        const sizeEl = progressContainer?.querySelector('[data-upload-size]');
        
        // Ocultar zona de upload y mostrar progreso
        if (uploadZone) {
            uploadZone.style.display = 'none';
        }
        if (progressContainer) {
            progressContainer.style.display = 'block';
            // Actualizar nombre del archivo
            if (filenameEl) {
                filenameEl.textContent = file.name.length > 25 ? file.name.substring(0, 22) + '...' : file.name;
                filenameEl.title = file.name;
            }
        }

        const formData = new FormData();
        formData.append('files', file);
        formData.append('csrfmiddlewaretoken', this.getCSRFToken());

        // Variables para calcular velocidad
        let lastLoaded = 0;
        let lastTime = Date.now();

        try {
            const xhr = new XMLHttpRequest();
            
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percent = Math.round((e.loaded / e.total) * 100);
                    
                    // Actualizar barra de progreso
                    if (progressBar) {
                        progressBar.style.width = `${percent}%`;
                    }
                    
                    // Actualizar porcentaje
                    if (percentEl) {
                        percentEl.textContent = `${percent}%`;
                    }
                    
                    // Calcular y mostrar velocidad
                    const now = Date.now();
                    const timeDiff = (now - lastTime) / 1000; // segundos
                    if (timeDiff > 0.5) { // Actualizar cada 500ms
                        const bytesDiff = e.loaded - lastLoaded;
                        const speed = bytesDiff / timeDiff;
                        if (speedEl) {
                            speedEl.textContent = this.formatSpeed(speed);
                        }
                        lastLoaded = e.loaded;
                        lastTime = now;
                    }
                    
                    // Mostrar tamaño subido / total
                    if (sizeEl) {
                        sizeEl.textContent = `${this.formatBytes(e.loaded)} / ${this.formatBytes(e.total)}`;
                    }
                }
            });

            const response = await new Promise((resolve, reject) => {
                xhr.addEventListener('load', () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        resolve(xhr.response);
                    } else {
                        reject(new Error('Upload failed'));
                    }
                });
                xhr.addEventListener('error', () => reject(new Error('Network error')));
                
                xhr.open('POST', `/projects/${projectId}/phases/${phaseId}/tasks/${taskId}/files/upload/`);
                xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
                xhr.send(formData);
            });

            if (window.notifications) {
                window.notifications.success('Archivo subido correctamente');
            }
            
            // Recargar modal para mostrar archivo nuevo
            this.open(this.currentMode, this.currentTaskId);
            
        } catch (error) {
            console.error('Error uploading:', error);
            if (window.notifications) {
                window.notifications.error('Error al subir el archivo');
            }
            
            // Restaurar zona de upload
            if (uploadZone) {
                uploadZone.style.display = '';
            }
            if (progressContainer) {
                progressContainer.style.display = 'none';
                if (progressBar) progressBar.style.width = '0%';
            }
        }
    }

    /**
     * Agregar nota (desde modal de detalle)
     */
    async addNote() {
        const textarea = this.modalContent.querySelector('[data-note-input]');
        const content = textarea?.value?.trim();
        
        if (!content) {
            if (window.notifications) {
                window.notifications.warning('Escribe una nota antes de enviar');
            }
            return;
        }

        const submitBtn = this.modalContent.querySelector('[data-action="add-note"]');
        const originalText = submitBtn?.innerHTML;
        
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        }

        try {
            const response = await fetch(`/projects/tasks/${this.currentTaskId}/notes/create/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `content=${encodeURIComponent(content)}`
            });

            const data = await response.json();

            if (data.success) {
                // Agregar nota al DOM
                this.appendNoteToList(data.note);
                textarea.value = '';
                
                // Actualizar contador
                const counter = this.modalContent.querySelector('[data-counter-display]');
                if (counter) counter.textContent = '0';
                
                if (window.notifications) {
                    window.notifications.success('Nota agregada');
                }
            } else {
                throw new Error(data.error || 'Error al agregar nota');
            }
        } catch (error) {
            console.error('Error:', error);
            if (window.notifications) {
                window.notifications.error(error.message || 'Error al agregar la nota');
            }
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }
        }
    }

    /**
     * Agregar nota al listado
     */
    appendNoteToList(note) {
        const notesList = this.modalContent.querySelector('[data-notes-list]');
        const emptyMsg = this.modalContent.querySelector('[data-notes-empty]');
        
        if (!notesList) return;
        
        if (emptyMsg) emptyMsg.remove();

        const noteHtml = `
            <div class="note-item p-2 rounded mb-2" style="background-color: #fefce8;" id="note-${note.id}">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="d-flex align-items-center gap-2">
                        <div class="note-avatar" style="width: 28px; height: 28px; border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; display: flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: 600;">
                            ${note.author_initials}
                        </div>
                        <div>
                            <span class="fw-semibold small">${this.escapeHtml(note.author_name)}</span>
                            <span class="text-muted small ms-2">${note.created_at}</span>
                        </div>
                    </div>
                    <button type="button" class="btn btn-link btn-sm text-danger p-0" 
                            data-action="delete-note"
                            data-note-id="${note.id}"
                            title="Marcar para eliminar">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="note-content mt-2 small" style="white-space: pre-wrap; word-break: break-word;">${this.escapeHtml(note.content)}</div>
            </div>
        `;

        notesList.insertAdjacentHTML('afterbegin', noteHtml);

        // Actualizar contador de notas
        const countEl = this.modalContent.querySelector('[data-notes-count]');
        if (countEl) {
            const current = parseInt(countEl.textContent) || 0;
            countEl.textContent = current + 1;
        }
    }

    /**
     * Inicializar contadores de caracteres
     */
    initCharCounters() {
        const inputs = this.modalContent.querySelectorAll('[data-char-counter]');
        inputs.forEach(input => {
            const counterId = input.dataset.charCounter;
            const counter = this.modalContent.querySelector(`[data-counter-display="${counterId}"]`);
            if (counter) {
                counter.textContent = input.value.length;
            }
        });
    }

    /**
     * Restaurar estados de elementos marcados para eliminar
     */
    restorePendingDeletionStates() {
        // Archivos
        this.pendingDeletions.files.forEach(fileId => {
            const fileItem = this.modalContent.querySelector(`#task-file-${fileId}, #detail-task-file-${fileId}`);
            const btn = fileItem?.querySelector('[data-action="delete-file"]');
            if (fileItem && btn) {
                fileItem.classList.add('marked-for-deletion');
                fileItem.style.opacity = '0.5';
                fileItem.style.textDecoration = 'line-through';
                btn.innerHTML = '<i class="fas fa-undo"></i>';
                btn.classList.remove('btn-outline-danger');
                btn.classList.add('btn-secondary');
            }
        });

        // Notas - YA NO SE USA (Eliminación directa)
        /*
        this.pendingDeletions.notes.forEach(noteId => {
            const noteItem = this.modalContent.querySelector(`#note-${noteId}`);
            const btn = noteItem?.querySelector('[data-action="delete-note"]');
            if (noteItem && btn) {
                noteItem.classList.add('marked-for-deletion');
                noteItem.style.opacity = '0.5';
                noteItem.style.textDecoration = 'line-through';
                btn.innerHTML = '<i class="fas fa-undo"></i>';
            }
        });
        */

        this.updateDeleteWarning();
    }

    /**
     * Limpiar al cerrar modal
     */
    cleanup() {
        this.pendingDeletions = { files: new Set(), notes: new Set() };
        this.currentTaskId = null;
        this.currentMode = null;
        this.isLoading = false;
        this.cleanupBackdrops();
    }

    /**
     * Limpiar backdrops huérfanos
     */
    cleanupBackdrops() {
        const backdrops = document.querySelectorAll('.modal-backdrop');
        const openModals = document.querySelectorAll('.modal.show');
        
        if (openModals.length === 0) {
            backdrops.forEach(backdrop => backdrop.remove());
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
        }
    }

    /**
     * Mostrar error en el modal
     */
    showError(message) {
        this.modalContent.innerHTML = `
            <div class="text-center p-4 text-danger">
                <i class="fas fa-exclamation-triangle fa-2x mb-3"></i>
                <h5>Error</h5>
                <p class="text-muted">${this.escapeHtml(message)}</p>
            </div>
        `;
    }

    /**
     * Obtener token CSRF
     */
    getCSRFToken() {
        const input = document.querySelector('[name=csrfmiddlewaretoken]');
        if (input) return input.value;
        
        const cookie = document.cookie.match(/csrftoken=([^;]+)/);
        return cookie ? cookie[1] : '';
    }

    /**
     * Escapar HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Formatear bytes a unidad legible
     */
    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    /**
     * Formatear velocidad de upload
     */
    formatSpeed(bytesPerSecond) {
        if (bytesPerSecond === 0) return '0 KB/s';
        const k = 1024;
        if (bytesPerSecond < k) return Math.round(bytesPerSecond) + ' B/s';
        if (bytesPerSecond < k * k) return (bytesPerSecond / k).toFixed(1) + ' KB/s';
        return (bytesPerSecond / (k * k)).toFixed(1) + ' MB/s';
    }
}

// Instancia global
window.taskModalManager = new TaskModalManager();

// Función global para compatibilidad con código existente
window.openTaskModal = function(type, taskId) {
    window.taskModalManager.open(type, taskId);
};

// Función para agregar nota (usada desde botón en template)
window.addTaskNote = function() {
    window.taskModalManager.addNote();
};
