// Confirmación simple en un solo paso para actualizar plan (migrado)
(function(){
  const form = document.querySelector('form.upgrade-form');
  if (!form) return;
  let confirmed = false;
  form.addEventListener('submit', function(e){
    if (confirmed) { return; }
    e.preventDefault();
    const card = document.getElementById('targetPlanCard');
    const name = card ? (card.querySelector('.plan-name')?.textContent || '') : '';
    const modalId = 'upgradeConfirmModal';
    let modalEl = document.getElementById(modalId);
    if (!modalEl) {
      modalEl = document.createElement('div');
      modalEl.id = modalId;
      modalEl.className = 'modal fade';
      modalEl.tabIndex = -1;
      modalEl.innerHTML = `
      <div class="modal-dialog modal-sm modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Confirmar suscripción</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
          </div>
          <div class="modal-body text-center">
            <p id="upgradeConfirmText" class="mb-0"></p>
          </div>
          <div class="modal-footer">
            <div class="d-flex justify-content-center w-100 gap-2">
              <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Cancelar</button>
              <button type="button" class="btn btn-primary btn-sm" id="upgradeConfirmBtn"><i class="fas fa-check"></i> Confirmar suscripción</button>
            </div>
          </div>
        </div>
      </div>`;
      document.body.appendChild(modalEl);
    }
    const textEl = modalEl.querySelector('#upgradeConfirmText');
    if (textEl) textEl.textContent = `¿Confirmas la suscripción al plan "${name}"?`;
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    const confirmBtn = modalEl.querySelector('#upgradeConfirmBtn');
    const onConfirm = () => { confirmBtn.removeEventListener('click', onConfirm); confirmed = true; modal.hide(); form.submit(); };
    confirmBtn.addEventListener('click', onConfirm);
    modalEl.addEventListener('hidden.bs.modal', function onHide(){
      const submitBtn = form.querySelector('.plan-select-btn, button[type="submit"]');
      if (submitBtn) {
        submitBtn.disabled = false;
        const span = submitBtn.querySelector('span');
        if (span && span.getAttribute('data-original-text')) span.textContent = span.getAttribute('data-original-text');
        const icon = submitBtn.querySelector('i');
        if (icon && icon.getAttribute('data-original-class')) icon.className = icon.getAttribute('data-original-class');
        submitBtn.classList.remove('loading');
      }
      modalEl.removeEventListener('hidden.bs.modal', onHide);
    });
    modal.show();
  });
})();

