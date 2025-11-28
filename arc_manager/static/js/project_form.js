document.addEventListener('DOMContentLoaded', function() {
  const creationMethodRadios = document.querySelectorAll('input[name="phase_creation_method"]');
  const templateContainer = document.getElementById('phase-template-container');
  const manualContainer = document.getElementById('manual-phases-container');
  function togglePhaseCreationVisibility() {
    const selected = document.querySelector('input[name="phase_creation_method"]:checked');
    if (!selected) return;
    if (selected.value === 'template') {
      if (templateContainer) templateContainer.style.display = 'block';
      if (manualContainer) manualContainer.style.display = 'none';
    } else {
      if (templateContainer) templateContainer.style.display = 'none';
      if (manualContainer) manualContainer.style.display = 'block';
    }
  }
  creationMethodRadios.forEach(radio => radio.addEventListener('change', togglePhaseCreationVisibility));

  const formsetContainer = document.getElementById('phase-forms-container');
  const addButton = document.getElementById('add-form');
  const emptyFormEl = document.getElementById('empty-form');
  const totalForms = document.getElementById('id_phases-TOTAL_FORMS');
  let formNum = totalForms ? parseInt(totalForms.value || '0', 10) : 0;

  function wireDeleteButtons(scope) {
    const container = scope || document;
    container.querySelectorAll('.phase-form').forEach(function(formEl) {
      const btn = formEl.querySelector('.delete-phase-btn, .phase-delete-toggle');
      let checkbox = formEl.querySelector('input[type="checkbox"][name^="phases-"][name$="-DELETE"]');
      const deletedBadge = formEl.querySelector('.phase-badge-deleted');
      if (btn && checkbox && !btn.__wired) {
        btn.__wired = true;
        btn.addEventListener('click', function() {
          // Asegurar que exista el checkbox DELETE
          if (!checkbox) {
            const nameInput = formEl.querySelector('input[name$="-name"]');
            if (nameInput && nameInput.name) {
              const deleteName = nameInput.name.replace(/-name$/, '-DELETE');
              const hidden = document.createElement('input');
              hidden.type = 'checkbox';
              hidden.name = deleteName;
              hidden.className = 'd-none';
              formEl.appendChild(hidden);
              checkbox = hidden;
            }
          }

          if (checkbox) {
            checkbox.checked = !checkbox.checked;
          }
          if (checkbox.checked) {
            formEl.classList.add('deleted', 'removed');
            const nameInput = formEl.querySelector('input[name$="-name"]');
            if (nameInput) { nameInput.required = false; nameInput.disabled = true; }
            if (deletedBadge) deletedBadge.style.display = 'inline-flex';
          } else {
            formEl.classList.remove('deleted', 'removed');
            const nameInput = formEl.querySelector('input[name$="-name"]');
            if (nameInput) { nameInput.required = true; nameInput.disabled = false; }
            if (deletedBadge) deletedBadge.style.display = 'none';
          }
          if (checkbox) {
            const evt = new Event('change', { bubbles: true });
            checkbox.dispatchEvent(evt);
          }
          updateOrder();
        });
      }
      const nameInput = formEl.querySelector('input[name$="-name"]');
      if (nameInput && !nameInput.__wiredEnter) {
        nameInput.__wiredEnter = true;
        nameInput.addEventListener('keydown', function(e) {
          if (e.key === 'Enter') {
            e.preventDefault();
            const forms = Array.from(formsetContainer.querySelectorAll('.phase-form:not(.deleted)'));
            const isLast = forms[forms.length - 1] === formEl;
            if (isLast) { appendNewPhaseAndFocus(''); } else {
              const idx = forms.indexOf(formEl);
              const next = forms[idx + 1];
              if (next) {
                const inputNext = next.querySelector('input[name$="-name"]');
                if (inputNext) inputNext.focus();
              }
            }
          }
        });
      }
    });
  }

  // Delegación global para garantizar funcionamiento del botón eliminar
  if (formsetContainer) {
    formsetContainer.addEventListener('click', function(e) {
      const trigger = e.target.closest('.delete-phase-btn, .phase-delete-toggle');
      if (!trigger) return;
      e.preventDefault();
      const formEl = e.target.closest('.phase-form');
      if (!formEl) return;
      // Si el formulario es "nuevo" (no tiene input -id), eliminar del DOM y ajustar contadores
      const idInput = formEl.querySelector('input[name$="-id"]');
      if (!idInput) {
        formEl.remove();
        if (typeof formNum === 'number' && totalForms) {
          formNum = Math.max(0, formNum - 1);
          totalForms.value = formNum;
        }
        updateOrder();
        return;
      }
      // Si existiera un id (no aplica en creación), marcar DELETE
      let checkbox = formEl.querySelector('input[type="checkbox"][name^="phases-"][name$="-DELETE"]');
      if (!checkbox) {
        const nameInput = formEl.querySelector('input[name^="phases-"][name$="-name"]');
        if (nameInput && nameInput.name) {
          const deleteName = nameInput.name.replace(/-name$/, '-DELETE');
          checkbox = document.createElement('input');
          checkbox.type = 'checkbox';
          checkbox.name = deleteName;
          checkbox.className = 'd-none';
          formEl.appendChild(checkbox);
        }
      }
      if (checkbox) {
        checkbox.checked = !checkbox.checked;
      }
      const nameInput = formEl.querySelector('input[name$="-name"]');
      const deletedBadge = formEl.querySelector('.phase-badge-deleted');
      const isDel = checkbox && checkbox.checked;
      if (isDel) {
        formEl.classList.add('deleted', 'removed');
        if (nameInput) { nameInput.required = false; nameInput.disabled = true; }
        if (deletedBadge) deletedBadge.style.display = 'inline-flex';
      } else {
        formEl.classList.remove('deleted', 'removed');
        if (nameInput) { nameInput.required = true; nameInput.disabled = false; }
        if (deletedBadge) deletedBadge.style.display = 'none';
      }
      updateOrder();
    });
  }

  function updateOrder() {
    if (!formsetContainer) return;
    const forms = formsetContainer.querySelectorAll('.phase-form:not(.deleted)');
    forms.forEach((form, index) => {
      const orderInput = form.querySelector('input[name$="-order"]');
      if (orderInput) orderInput.value = index;
    });
  }

  function appendNewPhaseAndFocus(nameValue) {
    if (!emptyFormEl || !formsetContainer) return;
    const emptyForm = emptyFormEl.innerHTML;
    const newFormHtml = emptyForm.replace(/__prefix__/g, formNum);
    const wrapper = document.createElement('div');
    wrapper.innerHTML = newFormHtml;
    const element = wrapper.firstElementChild;
    formsetContainer.appendChild(element);
    if (nameValue) {
      const input = element.querySelector('input[name$="-name"]');
      if (input) input.value = nameValue;
    }
    wireDeleteButtons(element);
    updateOrder();
    totalForms.value = ++formNum;
    const nextInput = element.querySelector('input[name$="-name"]');
    if (nextInput) nextInput.focus();
  }

  if (addButton) addButton.addEventListener('click', function() { appendNewPhaseAndFocus(''); });

  if (window.Sortable && formsetContainer) {
    new Sortable(formsetContainer, { handle: '.drag-handle', animation: 150, onEnd: updateOrder });
  }

  // Fallback robusto: antes de enviar, garantizar que los eliminados tengan DELETE=on
  const projectForm = document.getElementById('project-form');
  if (projectForm) {
    projectForm.addEventListener('submit', function() {
      document.querySelectorAll('#phase-forms-container .phase-form').forEach(function(formEl) {
        const isDeleted = formEl.classList.contains('deleted') || formEl.classList.contains('removed');
        let del = formEl.querySelector('input[type="checkbox"][name^="phases-"][name$="-DELETE"]');
        if (isDeleted) {
          if (!del) {
            const nameInput = formEl.querySelector('input[name^="phases-"][name$="-name"]');
            if (nameInput && nameInput.name) {
              const deleteName = nameInput.name.replace(/-name$/, '-DELETE');
              del = document.createElement('input');
              del.type = 'checkbox';
              del.name = deleteName;
              del.className = 'd-none';
              projectForm.appendChild(del);
            }
          }
          if (del) del.checked = true;
        }
      });
    });
  }

  togglePhaseCreationVisibility();
  updateOrder();
  wireDeleteButtons(document);

  // ============================================
  // QUICK CLIENT CREATION FUNCTIONALITY
  // ============================================
  const saveQuickClientBtn = document.getElementById('saveQuickClient');
  const quickClientForm = document.getElementById('quickClientForm');
  const quickClientModal = document.getElementById('quickClientModal');
  const clientSelect = document.querySelector('select[name="client"]');
  const quickClientError = document.getElementById('quickClientError');
  const quickClientErrorMessage = document.getElementById('quickClientErrorMessage');

  if (saveQuickClientBtn && quickClientForm) {
    saveQuickClientBtn.addEventListener('click', function() {
      // Reset previous errors
      quickClientError.classList.add('d-none');
      document.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
      
      const formData = new FormData(quickClientForm);
      const name = formData.get('name');
      
      // Simple client-side validation
      if (!name || name.trim() === '') {
        const nameInput = document.getElementById('quick_client_name');
        nameInput.classList.add('is-invalid');
        document.getElementById('quick_client_name_error').textContent = 'Este campo es obligatorio';
        return;
      }
      
      // Check if URL is defined
      if (!window.CLIENT_CREATE_URL) {
        quickClientErrorMessage.textContent = 'Error de configuración. Por favor, recarga la página.';
        quickClientError.classList.remove('d-none');
        return;
      }
      
      // Disable button to prevent double-submission
      saveQuickClientBtn.disabled = true;
      saveQuickClientBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Creando...';
      
      // Send AJAX request to create client
      fetch(window.CLIENT_CREATE_URL, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
        }
      })
      .then(response => {
        return response.json();
      })
      .then(data => {
        if (data.success) {
          // Add new client to select dropdown
          if (clientSelect && data.client) {
            const option = document.createElement('option');
            option.value = data.client.id;
            option.textContent = data.client.name;
            option.selected = true;
            clientSelect.appendChild(option);
            
            // Trigger change event
            clientSelect.dispatchEvent(new Event('change'));
          }
          
          // Close modal
          const modalInstance = bootstrap.Modal.getInstance(quickClientModal);
          if (modalInstance) {
            modalInstance.hide();
          }
          
          // Reset form
          quickClientForm.reset();
          
          // Show success message (optional)
          if (window.showToast) {
            window.showToast('Cliente creado exitosamente', 'success');
          }
        } else {
          // Show error message
          quickClientErrorMessage.textContent = data.error || 'Error al crear el cliente';
          quickClientError.classList.remove('d-none');
        }
      })
      .catch(error => {
        quickClientErrorMessage.textContent = 'Error de conexión. Por favor, intenta nuevamente.';
        quickClientError.classList.remove('d-none');
      })
      .finally(() => {
        // Re-enable button
        saveQuickClientBtn.disabled = false;
        saveQuickClientBtn.innerHTML = '<i class="fas fa-check me-2"></i>Crear Cliente';
      });
    });
  }

  // Reset form when modal is hidden
  if (quickClientModal) {
    quickClientModal.addEventListener('hidden.bs.modal', function() {
      if (quickClientForm) {
        quickClientForm.reset();
        // Clear all input values manually
        document.getElementById('quick_client_name').value = '';
        document.getElementById('quick_client_email').value = '';
        document.getElementById('quick_client_phone').value = '';
      }
      if (quickClientError) quickClientError.classList.add('d-none');
      document.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
    });
    
    // Also reset when modal is shown (to ensure clean state)
    quickClientModal.addEventListener('show.bs.modal', function() {
      if (quickClientForm) {
        quickClientForm.reset();
        document.getElementById('quick_client_name').value = '';
        document.getElementById('quick_client_email').value = '';
        document.getElementById('quick_client_phone').value = '';
      }
      if (quickClientError) quickClientError.classList.add('d-none');
      document.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
    });
  }
});

