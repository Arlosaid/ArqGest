// static/js/base.js

class BaseAnimation {
    static init() {
        // Animaciones base deshabilitadas
        // this.setupAnimations();
    }

    static setupAnimations() {
        // Configurar animaciones para elementos comunes
        this.animateElements('.page-container, .main-content-grid, .table-container, .info-card-sidebar');
    }

    static animateElements() { /* deshabilitada intencionalmente */ }

    static animateTableRow() { /* deshabilitada intencionalmente */ }

    static animateButton() { /* deshabilitada intencionalmente */ }

    static animateCard() { /* deshabilitada intencionalmente */ }
}

// Inicializar animaciones base cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar animaciones base
    BaseAnimation.init();

    // Activar los tooltips de Bootstrap en toda la aplicación
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Activar los popovers de Bootstrap
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});