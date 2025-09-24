document.addEventListener('DOMContentLoaded', function() {
  const container = document.getElementById('paymentFormContainer');
  if (!container) return;

  const remaining = parseFloat(container.getAttribute('data-remaining')) || 0;
  const amountInputId = container.getAttribute('data-amount-input-id');
  const dateInputId = container.getAttribute('data-date-input-id');

  const amountInput = amountInputId ? document.getElementById(amountInputId) : null;
  const feedback = document.getElementById('amount-feedback');

  if (amountInput && feedback) {
    // Hints para móviles y evitar formatos localizados
    amountInput.setAttribute('inputmode', 'decimal');
    amountInput.setAttribute('step', '0.01');
    amountInput.setAttribute('autocomplete', 'off');

    amountInput.addEventListener('input', function() {
      // Normalizar: quitar espacios (incl. NBSP) y cambiar coma por punto
      const normalized = (this.value || '')
        .replace(/[\s\u00A0]/g, '')
        .replace(/,/g, '.');
      const amount = parseFloat(normalized) || 0;
      if (amount > remaining) {
        feedback.innerHTML = '<span class="error">Monto excede el máximo disponible</span>';
      } else if (amount > 0) {
        feedback.innerHTML = '<span class="success">✓ Monto válido</span>';
      } else {
        feedback.innerHTML = '';
      }
    });
  }

  const dateInput = dateInputId ? document.getElementById(dateInputId) : null;
  if (dateInput && !dateInput.value) {
    const today = new Date().toISOString().split('T')[0];
    dateInput.value = today;
  }
});


