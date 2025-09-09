/**
 * Dashboard Optimizado - Arc Manager
 * Versión mínima con funcionalidad esencial
 */

// Inicialización simple del dashboard
document.addEventListener('DOMContentLoaded', () => {
    // Configurar contadores (si existen elementos con data-target)
    const counters = document.querySelectorAll('.metric-value[data-target]');
    counters.forEach(counter => {
        const target = parseInt(counter.getAttribute('data-target'));
        counter.textContent = target;
    });

    // Configurar botones de refresh (si existen)
    document.querySelectorAll('[data-action="refresh"]').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            // Recargar la página para obtener datos actualizados
            window.location.reload();
        });
    });
});

// Funciones auxiliares globales
window.dashboardUtils = {
    formatNumber: (number) => number.toLocaleString(),
    formatDate: (date) => new Date(date).toLocaleDateString(),
    
    // Método para actualizar métricas desde el backend
    updateMetric: (metricId, value) => {
        const element = document.querySelector(`[data-metric="${metricId}"]`);
        if (element) {
            element.textContent = value;
        }
    }
}; 