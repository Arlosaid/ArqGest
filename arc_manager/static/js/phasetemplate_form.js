document.addEventListener('DOMContentLoaded', function() {
    const formsetContainer = document.getElementById('phase-forms-container');
    const addButton = document.getElementById('add-form');
    const emptyFormTemplate = document.getElementById('empty-form');
    const totalForms = document.getElementById('id_phases-TOTAL_FORMS');
    const formEl = document.getElementById('phase-template-form');

    if (!formsetContainer || !addButton || !emptyFormTemplate || !totalForms || !formEl) {
        return;
    }

    let formNum = parseInt(totalForms.value, 10) || 0;

    addButton.addEventListener('click', function() {
        const emptyFormHtml = emptyFormTemplate.innerHTML;
        const newFormHtml = emptyFormHtml.replace(/__prefix__/g, formNum);
        const newForm = document.createElement('div');
        newForm.innerHTML = newFormHtml;
        formsetContainer.appendChild(newForm.firstElementChild);
        updateOrder();
        totalForms.value = ++formNum;
    });

    formsetContainer.addEventListener('click', function(e) {
        const btn = e.target.closest('.delete-phase-btn');
        if (!btn) return;
        const wrapper = btn.closest('.phase-form');
        if (!wrapper) return;
        const deleteInput = wrapper.querySelector('input[type="checkbox"][name$="-DELETE"]');
        const nameInput = wrapper.querySelector('input[name$="-name"]');
        if (deleteInput) {
            deleteInput.checked = true;
        }
        if (nameInput) {
            nameInput.required = false;
        }
        wrapper.style.display = 'none';
        updateOrder();
    });

    function updateOrder() {
        const forms = formsetContainer.querySelectorAll('.phase-form');
        forms.forEach((form, index) => {
            const orderInput = form.querySelector('input[name$="-order"]');
            if (orderInput) {
                orderInput.value = index;
            }
        });
    }

    try {
        if (window.Sortable && formsetContainer) {
            new Sortable(formsetContainer, {
                handle: '.drag-handle',
                animation: 150,
                onEnd: function() {
                    updateOrder();
                }
            });
        }
    } catch (e) {
        console.warn('SortableJS no está disponible o falló la inicialización:', e);
    }

    updateOrder();

    formEl.addEventListener('submit', function() {
        const forms = formsetContainer.querySelectorAll('.phase-form');
        forms.forEach((form) => {
            const nameInput = form.querySelector('input[name$="-name"]');
            const deleteInput = form.querySelector('input[type="checkbox"][name$="-DELETE"]');
            if (nameInput && !nameInput.value.trim() && deleteInput) {
                deleteInput.checked = true;
                form.style.display = 'none';
            }
        });
        updateOrder();
    });
});

