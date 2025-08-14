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
      const btn = formEl.querySelector('.phase-delete-toggle');
      const checkbox = formEl.querySelector('input[type="checkbox"][name^="phases-"][name$="-DELETE"]');
      const deletedBadge = formEl.querySelector('.phase-badge-deleted');
      if (btn && checkbox && !btn.__wired) {
        btn.__wired = true;
        btn.addEventListener('click', function() {
          checkbox.checked = !checkbox.checked;
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
          const evt = new Event('change', { bubbles: true });
          checkbox.dispatchEvent(evt);
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

  togglePhaseCreationVisibility();
  updateOrder();
  wireDeleteButtons(document);
});

