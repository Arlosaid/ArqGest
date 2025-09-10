document.addEventListener('DOMContentLoaded', function() {
  document.body.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.target.id === 'notes-form' && evt.detail.successful) {
      const statusEl = document.getElementById('notes-save-status');
      if (statusEl) {
        statusEl.textContent = 'Notas guardadas!';
        setTimeout(() => { statusEl.textContent = ''; }, 3000);
      }
    }
    
    // Manejar subidas de archivos exitosas
    if (evt.target.classList.contains('file-upload-form') && evt.detail.successful) {
      // Mostrar notificación de éxito usando el sistema moderno
      if (window.notifications) {
        window.notifications.success('Archivo(s) subido(s) exitosamente');
      }
    }
  });

  document.body.addEventListener('htmx:afterOnLoad', function(evt) {
    if (evt.target.classList.contains('file-upload-form')) {
      evt.target.reset();
    }
  });

  // Nota: El manejo de errores HTMX ahora está en htmx_error_handler.js
  // que se encarga globalmente de todos los errores HTTP en la aplicación
});

// Phase detail functionality is now minimal - only notes auto-save

