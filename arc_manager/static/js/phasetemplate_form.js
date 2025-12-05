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
        const wrapper = btn.closest('.phase-item');
        if (!wrapper) return;
        
        // Para fases nuevas (sin data-is-existing), simplemente eliminar del DOM
        const isExisting = wrapper.dataset.isExisting === 'true';
        
        // Check active phases count before deleting
        const activePhases = Array.from(formsetContainer.querySelectorAll('.phase-item')).filter(item => {
            const delInput = item.querySelector('input[type="checkbox"][name$="-DELETE"]');
            return !delInput || !delInput.checked;
        });

        if (!isExisting) {
            if (activePhases.length <= 1) {
                alert('Debe haber al menos una fase en la plantilla.');
                return;
            }
            // Fase nueva: eliminar completamente del DOM
            wrapper.remove();
            formNum--;
            totalForms.value = formNum;
            updateOrder();
        } else {
            // Fase existente: toggle marcar para eliminar
            const deleteInput = wrapper.querySelector('input[type="checkbox"][name$="-DELETE"]');
            const nameInput = wrapper.querySelector('input[name$="-name"]');
            const icon = btn.querySelector('i');
            
            if (deleteInput) {
                // Toggle estado
                const isDeleting = !deleteInput.checked;
                
                if (isDeleting && activePhases.length <= 1) {
                    alert('Debe haber al menos una fase en la plantilla.');
                    return;
                }

                deleteInput.checked = isDeleting;
                
                if (isDeleting) {
                    wrapper.classList.add('phase-deleted');
                    if (nameInput) nameInput.readOnly = true;
                    if (icon) {
                        icon.classList.remove('fa-trash-alt');
                        icon.classList.add('fa-undo');
                    }
                    btn.title = "Deshacer eliminación";
                    btn.classList.remove('btn-outline-danger');
                    btn.classList.add('btn-outline-secondary');
                } else {
                    wrapper.classList.remove('phase-deleted');
                    if (nameInput) nameInput.readOnly = false;
                    if (icon) {
                        icon.classList.remove('fa-undo');
                        icon.classList.add('fa-trash-alt');
                    }
                    btn.title = "Eliminar fase";
                    btn.classList.remove('btn-outline-secondary');
                    btn.classList.add('btn-outline-danger');
                }
            }
            // No ocultamos ni actualizamos orden para fases existentes
            updateOrder();
        }
    });

    function updateOrder() {
        const forms = formsetContainer.querySelectorAll('.phase-item:not([style*="display: none"])');
        let visibleIndex = 0;
        
        forms.forEach((form) => {
            const deleteInput = form.querySelector('input[type="checkbox"][name$="-DELETE"]');
            const isDeleted = deleteInput && deleteInput.checked;
            const numberBadge = form.querySelector('.phase-number');
            
            if (!isDeleted) {
                const orderInput = form.querySelector('input[name$="-order"]');
                if (orderInput) {
                    orderInput.value = visibleIndex;
                }
                // Actualizar número visual
                if (numberBadge) {
                    numberBadge.textContent = visibleIndex + 1;
                }
                visibleIndex++;
            } else {
                // Para elementos borrados, mostrar icono de basura en lugar de número
                if (numberBadge) {
                    numberBadge.innerHTML = '<i class="fas fa-trash-alt" style="font-size: 0.7rem;"></i>';
                }
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
        // SortableJS no está disponible o falló la inicialización
    }

    // Inicializar estado visual al cargar (por si hay errores de validación y vuelve con datos)
    const existingForms = formsetContainer.querySelectorAll('.phase-item');
    existingForms.forEach(form => {
        const deleteInput = form.querySelector('input[type="checkbox"][name$="-DELETE"]');
        if (deleteInput && deleteInput.checked) {
            form.classList.add('phase-deleted');
            const nameInput = form.querySelector('input[name$="-name"]');
            if (nameInput) nameInput.readOnly = true;
            
            const btn = form.querySelector('.delete-phase-btn');
            if (btn) {
                const icon = btn.querySelector('i');
                if (icon) {
                    icon.classList.remove('fa-trash-alt');
                    icon.classList.add('fa-undo');
                }
                btn.title = "Deshacer eliminación";
                btn.classList.remove('btn-outline-danger');
                btn.classList.add('btn-outline-secondary');
            }
        }
    });

    updateOrder();

    formEl.addEventListener('submit', function(e) {
        const forms = formsetContainer.querySelectorAll('.phase-item:not([style*="display: none"])');
        let activeCount = 0;

        forms.forEach((form) => {
            const nameInput = form.querySelector('input[name$="-name"]');
            const deleteInput = form.querySelector('input[type="checkbox"][name$="-DELETE"]');
            const isExisting = form.dataset.isExisting === 'true';
            
            // Si es una fase existente marcada para borrar, asegurarse que se envíe
            if (isExisting && deleteInput && deleteInput.checked) {
                return; // Ya está marcada, dejarla así
            }

            if (nameInput && !nameInput.value.trim() && deleteInput && isExisting) {
                deleteInput.checked = true;
                form.style.display = 'none';
            } else if (nameInput && !nameInput.value.trim() && !isExisting) {
                // Fases nuevas sin nombre: eliminar del DOM
                form.remove();
            } else {
                activeCount++;
            }
        });

        if (activeCount === 0) {
            e.preventDefault();
            alert('Debe haber al menos una fase en la plantilla.');
            return;
        }
        // No llamamos updateOrder aquí para no reordenar justo antes de enviar si no es necesario
    });
});

