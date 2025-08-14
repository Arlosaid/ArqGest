document.addEventListener('DOMContentLoaded', function() {
  document.body.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.target.id === 'notes-form' && evt.detail.successful) {
      const statusEl = document.getElementById('notes-save-status');
      if (statusEl) {
        statusEl.textContent = 'Notas guardadas!';
        setTimeout(() => { statusEl.textContent = ''; }, 3000);
      }
    }
  });

  document.body.addEventListener('htmx:afterOnLoad', function(evt) {
    if (evt.target.id === 'file-upload-form') {
      evt.target.reset();
    }
  });
});

