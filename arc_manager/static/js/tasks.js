/**
 * Manejador unificado para creación de tareas desde modales
 * Funciona tanto en Kanban (#addTaskModal) como en Detalle de Proyecto (#createTaskModal)
 */

class TaskCreationManager {
  constructor() {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.init());
    } else {
      this.init();
    }
  }

  init() {
    this.wireModal('#addTaskModal');
    this.wireModal('#createTaskModal');

    // Delegación global por si el wiring específico falla
    document.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-task-create]');
      if (!btn) return;
      const form = btn.closest('form');
      const modal = btn.closest('.modal');
      if (form) {
        this.handleSubmit(e, form, modal || document);
      }
    }, true);

    // Re-cablear cuando se muestran los modales (contenido dinámico o tardío)
    document.addEventListener('show.bs.modal', (event) => {
      const modal = event.target;
      if (modal && (modal.id === 'addTaskModal' || modal.id === 'createTaskModal')) {
        this.wireModal(`#${modal.id}`);
      }
    });
  }

  wireModal(modalSelector) {
    const modal = document.querySelector(modalSelector);
    if (!modal) return;

    // Auto-selección de fase si no hay valor
    modal.addEventListener('show.bs.modal', (event) => {
      const phaseSelect = modal.querySelector('select[name="phase"], #task-phase, #id_phase');
      if (phaseSelect && !phaseSelect.value && phaseSelect.options.length > 0) {
        // Evitar seleccionar placeholder vacío si existe
        const firstValid = Array.from(phaseSelect.options).find(opt => opt.value);
        if (firstValid) {
          phaseSelect.value = firstValid.value;
        }
      }
    });

    const form = modal.querySelector('form');
    if (!form) return;

    // Mitigación: algunos listeners globales podrían interceptar 'submit'.
    // Forzamos manejo por 'click' del botón y cambiamos a type="button".
    const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
    if (submitBtn) {
      try { submitBtn.type = 'button'; } catch (_) {}
      submitBtn.setAttribute('data-task-create', 'true');
      submitBtn.addEventListener('click', (e) => this.handleSubmit(e, form, modal));
    }

    // Aun así, capturamos 'submit' en fase de captura por compatibilidad.
    form.addEventListener('submit', (e) => this.handleSubmit(e, form, modal), { capture: true });
  }

  handleSubmit(event, form, modal) {
    event.preventDefault();

    // Validación mínima
    const title = form.querySelector('input[name="title"], #task-title, #id_title');
    const phase = form.querySelector('select[name="phase"], #task-phase, #id_phase');
    if (!title || !title.value.trim() || !phase || !phase.value) {
      this.notify('Completa Título y Fase', 'error');
      if (title && !title.value.trim()) title.focus();
      return;
    }

    const submitBtn = form.querySelector('button[type="submit"]');
    const originalHTML = submitBtn ? submitBtn.innerHTML : '';
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';
    }

    const formData = new FormData(form);

    fetch(form.action, {
      method: 'POST',
      body: formData,
      headers: {
        'Accept': 'application/json',
        'X-CSRFToken': this.getCSRFToken(),
      },
      credentials: 'same-origin'
    })
      .then((response) => {
        const contentType = response.headers.get('Content-Type') || '';
        if (contentType.includes('application/json')) return response.json();
        if (response.ok) return { success: true };
        throw new Error('Respuesta no válida');
      })
      .then((data) => {
        if (data && data.success) {
          this.notify('Tarea creada correctamente', 'success');
          // Cerrar modal si es Bootstrap
          if (window.bootstrap) {
            const instance = bootstrap.Modal.getInstance(modal) || new bootstrap.Modal(modal);
            instance.hide();
          }
          setTimeout(() => window.location.reload(), 400);
        } else {
          this.notify('Error al crear la tarea', 'error');
        }
      })
      .catch((err) => {
        console.error(err);
        this.notify('Error al crear la tarea', 'error');
      })
      .finally(() => {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = originalHTML;
        }
      });
  }

  getCSRFToken() {
    return (
      document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
      document.cookie.split('; ').find((r) => r.startsWith('csrftoken='))?.split('=')[1] ||
      ''
    );
  }

  notify(message, type = 'info') {
    // Minimalista para no depender de otros módulos
    const n = document.createElement('div');
    n.className = `notification notification-${type}`;
    n.style.cssText = 'position:fixed;right:16px;bottom:16px;background:#333;color:#fff;padding:10px 14px;border-radius:8px;z-index:2000;opacity:0;transition:opacity .2s';
    n.textContent = message;
    document.body.appendChild(n);
    requestAnimationFrame(() => (n.style.opacity = '1'));
    setTimeout(() => {
      n.style.opacity = '0';
      setTimeout(() => n.remove(), 200);
    }, 2200);
  }
}

new TaskCreationManager();


