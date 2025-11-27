(function() {
  function getCsrfToken() {
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

  document.addEventListener('htmx:configRequest', function (event) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      event.detail.headers['X-CSRFToken'] = csrfToken;
    }
  });
})();

