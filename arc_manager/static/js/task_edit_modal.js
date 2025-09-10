// ===== TASK EDIT MODAL - FUNCIONALIDADES MEJORADAS =====

// Función global para manejar la eliminación de tareas desde el modal
window.deleteTaskFromModal = function(taskId) {
    if (!confirm('¿Estás seguro de que deseas eliminar esta tarea?')) {
        return;
    }
    
    const deleteBtn = document.getElementById('deleteTaskBtn');
    if (deleteBtn) {
        deleteBtn.disabled = true;
        deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Eliminando...';
    }
    
    // Realizar petición de eliminación
    fetch(`/projects/tasks/${taskId}/delete/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Cerrar modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('taskUniversalModal'));
            if (modal) modal.hide();
            
            // Actualizar UI
            const card = document.querySelector(`.kanban-card[data-task-id="${taskId}"]`);
            if (card) card.remove();
            
            const listItem = document.querySelector(`.task-item[data-task-id="${taskId}"]`);
            if (listItem) listItem.remove();
            
            // Mostrar notificación
            if (window.notifications) {
                window.notifications.success('Tarea eliminada correctamente');
            }
        } else {
            throw new Error(data.error || 'Error al eliminar la tarea');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        if (window.notifications) {
            window.notifications.error('Error al eliminar la tarea');
        }
    })
    .finally(() => {
        if (deleteBtn) {
            deleteBtn.disabled = false;
            deleteBtn.innerHTML = '<i class="fas fa-trash"></i> Eliminar';
        }
    });
};

// Manejo de respuesta HTMX para cerrar el modal universal y refrescar UI
document.addEventListener('htmx:afterRequest', function (e) {
  try {
    const xhr = e.detail.xhr;
    
    // Si la respuesta es exitosa (200) y es un formulario de edición de tarea
    if (xhr.status === 200 && e.target.closest('form') && e.target.closest('form').getAttribute('hx-post') && e.target.closest('form').getAttribute('hx-post').includes('task-edit')) {
      // Cerrar modal universal
      const taskUniversalModal = document.getElementById('taskUniversalModal');
      if (taskUniversalModal && window.bootstrap) {
        const modal = bootstrap.Modal.getInstance(taskUniversalModal);
        if (modal) {
          modal.hide();
        }
      }
      
      // Mostrar notificación de éxito
      if (window.notifications) {
        window.notifications.success('Tarea actualizada correctamente');
      } else {
        console.log('Tarea actualizada correctamente');
      }
      
      // Disparar evento para actualizar la UI dinámicamente
      htmx.trigger(document.body, 'taskUpdated');
    }
    
    // Manejo de respuestas JSON (para compatibilidad)
    const contentType = xhr.getResponseHeader('Content-Type') || '';
    if (contentType.includes('application/json')) {
      const data = JSON.parse(xhr.responseText || '{}');
      if (data && data.success && data.task) {
        // Cerrar modal universal si existe
        const taskUniversalModal = document.getElementById('taskUniversalModal');
        if (taskUniversalModal && window.bootstrap) {
          const modal = bootstrap.Modal.getInstance(taskUniversalModal);
          if (modal) modal.hide();
        }
        
        // Mostrar notificación de éxito
        if (window.notifications) {
          window.notifications.success('Tarea actualizada correctamente');
        }
        
        // Disparar evento para actualizar la UI dinámicamente
        htmx.trigger(document.body, 'taskUpdated');
      }
    }
  } catch (error) {
    console.error('Error processing HTMX response:', error);
  }
});

// Manejo de errores HTMX específicos para tareas solamente
document.addEventListener('htmx:responseError', function (e) {
  // Solo manejar errores que sean específicamente de edición de tareas
  const form = e.target.closest('form');
  if (form && form.getAttribute('hx-post') && form.getAttribute('hx-post').includes('task-edit')) {
    console.error('HTMX Task Edit Error:', e.detail);
    if (window.notifications) {
      window.notifications.error('Error al actualizar la tarea');
    }
  }
  // Para otros errores, dejar que htmx_error_handler.js los maneje
});

// Manejo de envío del formulario con mejor feedback visual
document.addEventListener('htmx:beforeSend', function (e) {
  const form = e.target.closest('form');
  if (form && form.getAttribute('hx-post') && form.getAttribute('hx-post').includes('task-edit')) {
    console.log('HTMX: Enviando formulario de edición de tarea...');
    const submitBtn = form.querySelector('#saveTaskBtn');
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Guardando...';
      submitBtn.style.opacity = '0.7';
    }
  }
});

// Restaurar botón después del envío
document.addEventListener('htmx:afterRequest', function (e) {
  const form = e.target.closest('form');
  if (form && form.getAttribute('hx-post') && form.getAttribute('hx-post').includes('task-edit')) {
    console.log('HTMX: Respuesta recibida para edición de tarea');
    const submitBtn = form.querySelector('#saveTaskBtn');
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<i class="fas fa-save me-2"></i>Guardar Cambios';
      submitBtn.style.opacity = '1';
    }
  }
});

// Debug: Verificar que HTMX está funcionando
document.addEventListener('htmx:configRequest', function(e) {
  if (e.detail.path.includes('task') && e.detail.path.includes('edit')) {
    console.log('HTMX Config Request:', e.detail);
  }
});

// Verificar disponibilidad de HTMX al cargar
document.addEventListener('DOMContentLoaded', function() {
  console.log('HTMX disponible:', typeof htmx !== 'undefined');
  if (typeof htmx === 'undefined') {
    console.error('⚠️ HTMX no está cargado! Los formularios de edición no funcionarán correctamente.');
  } else {
    console.log('✅ HTMX cargado correctamente');
  }
});

// Delegación de eventos para el botón de eliminar
// El botón de cancelar usa el [data-bs-dismiss="modal"] nativo de Bootstrap y no necesita JS adicional.
document.addEventListener('click', function(e) {
  const deleteBtn = e.target.closest('#deleteTaskBtn');
  if (deleteBtn) {
    e.preventDefault();
    const taskId = deleteBtn.getAttribute('data-task-id');
    if (taskId) {
      window.deleteTaskFromModal(taskId);
    }
  }
});

// Mejorar la experiencia de usuario con validación en tiempo real
document.addEventListener('input', function(e) {
  if (e.target.matches('#taskUniversalModal input[name="title"]')) {
    const submitBtn = document.querySelector('#saveTaskBtn');
    if (submitBtn) {
      if (e.target.value.trim().length > 0) {
        submitBtn.disabled = false;
        submitBtn.style.opacity = '1';
      } else {
        submitBtn.disabled = true;
        submitBtn.style.opacity = '0.5';
      }
    }
  }
});

// Inicializar validación cuando se carga el modal
document.addEventListener('DOMContentLoaded', function() {
  const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      if (mutation.type === 'childList') {
        const titleInput = document.querySelector('#taskUniversalModal input[name="title"]');
        const submitBtn = document.querySelector('#saveTaskBtn');
        
        if (titleInput && submitBtn) {
          // Validar estado inicial
          if (titleInput.value.trim().length === 0) {
            submitBtn.disabled = true;
            submitBtn.style.opacity = '0.5';
          }
        }
      }
    });
  });
  
  const modalBody = document.getElementById('taskUniversalContent');
  if (modalBody) {
    observer.observe(modalBody, { childList: true, subtree: true });
  }
});
