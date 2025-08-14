// Control robusto de pestañas y utilidades de Project Detail
document.addEventListener('DOMContentLoaded', function () {
  const tabContainer = document.getElementById('projectTab');
  const panes = Array.from(document.querySelectorAll('#projectTabContent .tab-pane'));
  if (!tabContainer || panes.length === 0) return;

  const showTabById = (paneId) => {
    tabContainer.querySelectorAll('.nav-link').forEach(b => b.classList.remove('active'));
    const btn = tabContainer.querySelector(`button[data-bs-target="#${paneId}"]`);
    if (btn) btn.classList.add('active');
    panes.forEach(p => p.classList.remove('show', 'active'));
    const pane = document.getElementById(paneId);
    if (pane) pane.classList.add('show', 'active');
  };

  let initial = 'details';
  try {
    const params = new URLSearchParams(window.location.search);
    const q = (params.get('tab') || '').toLowerCase();
    const h = (window.location.hash || '').replace('#', '').toLowerCase();
    initial = q || h || 'details';
  } catch (_) {}
  if (!['details', 'phases', 'kanban', 'files'].includes(initial)) initial = 'details';
  showTabById(initial);

  tabContainer.addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-bs-target]');
    if (!btn) return;
    const id = btn.getAttribute('data-bs-target').replace('#', '');
    showTabById(id);
  });

  tabContainer.addEventListener('shown.bs.tab', (e) => {
    const id = e.target?.getAttribute('data-bs-target')?.replace('#', '');
    if (id) showTabById(id);
  });

  const kanbanTab = document.getElementById('kanban-tab');
  if (kanbanTab) {
    kanbanTab.addEventListener('click', function () {
      showTabById('kanban');
    });
  }

  document.addEventListener('click', async function (e) {
    const btn = e.target.closest('[data-action="delete-task"][data-task-id]');
    if (!btn) return;
    e.preventDefault();
    const taskId = btn.getAttribute('data-task-id');
    if (!taskId) return;
    if (!confirm('¿Eliminar esta tarea?')) return;
    try {
      const res = await fetch(`/projects/tasks/${taskId}/delete/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': (document.querySelector('[name=csrfmiddlewaretoken]')||{}).value || '' }
      });
      const ok = res.ok;
      if (ok) {
        const row = document.querySelector(`tr[data-task-id="${taskId}"]`);
        if (row) row.remove();
      } else {
        alert('Error al eliminar');
      }
    } catch (err) {
      console.error(err);
      alert('Error al eliminar');
    }
  });

  const phaseFilter = document.getElementById('phaseFilter');
  if (phaseFilter) {
    phaseFilter.addEventListener('change', () => {
      const selected = phaseFilter.value;
      const rows = document.querySelectorAll('#simpleTasksTable tbody tr');
      rows.forEach(row => {
        const phaseId = row.getAttribute('data-phase-id');
        row.style.display = (!selected || selected === phaseId) ? '' : 'none';
      });
    });
  }
});

